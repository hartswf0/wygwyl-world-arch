"""Library hygiene for shape-picking: which cards are single painted body parts, and which are junk for this job.

junk(record) -> reason or None. A piece is junk when it is NOT one body part:
  * CLIP zero-shot (ViT-B/32, the Skin Lab's prompts style): the best of the junk prompts beats the best body-part
    prompt by MARGIN (caption / text strip, a whole small figure, a single eye / mouth / brow feature, a prop object, a blank
    plate);
  * pixel tests: a large flat near-white area (a blank plate: > 45% of the piece's pixels light and low-texture);
    many disconnected blobs (text, a scatter: > 6 alpha components of >= 1% each).
is_head(record): the best body prompt is a head (face or back of head); face_p: CLIP's painted-face vs blank / back
probability (for heads).
Results are cached in lab/hygiene.json (id -> {'junk': reason|None, 'face': p, 'scores': ...}) so a person can audit
every exclusion.
"""
import json, os, sys
import numpy as np, cv2

CLIP_DIR = '/tmp/claude-0/clip'
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.abspath(os.path.join(HERE, '..', 'lab', 'hygiene.json'))
P = 'a paper cut-out puppet piece: '
BODY = ['a head with a face', 'the back of a head', 'a torso or jacket', 'hips', 'a thigh', 'a lower leg', 'a leg in trousers',
        'an upper arm in a sleeve', 'a forearm in a sleeve', 'a hand', 'a fist', 'a shoe or boot', 'a foot']
JUNK = {'text': ['printed text, a caption label with words', 'a strip of printed letters'],
        'figure': ['a small complete figure of a whole person', 'a full body puppet of a man, head to feet'],
        'feature': ['a single eye', 'a mouth with lips', 'an eyebrow', 'a nose'],
        'prop': ['a flower', 'a microphone', 'a wine glass', 'a mobile phone', 'a pen', 'a letter or envelope', 'a suitcase'],
        'blank': ['a blank white paper plate', 'a plain empty piece of paper'],
        'wire': ['a grey wireframe rectangle outline', 'a thin line drawing of a box', 'a diagram with thin lines']}
FACE = {'painted': ['a head with painted eyes, nose and mouth', 'a face with eyes and lips'],
        'blank': ['a head with a blank face, no eyes, no mouth', 'the back of a head, hair only, no face']}
MEAN, STD = np.array([0.48145466, 0.4578275, 0.40821073]), np.array([0.26862954, 0.26130258, 0.27577711])
_S = {}


def _sess():
    if 'v' not in _S:
        import onnxruntime as ort
        sys.path.insert(0, CLIP_DIR)
        from simple_tokenizer import SimpleTokenizer
        so = ort.SessionOptions(); so.intra_op_num_threads = 1
        _S['v'] = ort.InferenceSession(os.path.join(CLIP_DIR, 'visual.onnx'), so, providers=['CPUExecutionProvider'])
        _S['t'] = ort.InferenceSession(os.path.join(CLIP_DIR, 'textual.onnx'), so, providers=['CPUExecutionProvider'])
        _S['tok'] = SimpleTokenizer()
    return _S


def _txt(texts):
    s = _sess()
    out = np.zeros((len(texts), 77), np.int64)
    for i, t in enumerate(texts):
        ids = [49406] + s['tok'].encode(t)[:75] + [49407]
        out[i, :len(ids)] = ids
    e = s['t'].run(None, {s['t'].get_inputs()[0].name: out})[0]
    return e / np.linalg.norm(e, axis=1, keepdims=True)


def _img(px):
    rgb = px[..., [2, 1, 0]].astype(np.float32)
    a = px[..., 3:] / 255.
    o = rgb * a + np.array([235, 232, 226], np.float32) * (1 - a)
    h, w = o.shape[:2]
    k = 224 / max(h, w)
    o = cv2.resize(o, (max(1, round(w * k)), max(1, round(h * k))), interpolation=cv2.INTER_CUBIC)
    c = np.full((224, 224, 3), (235, 232, 226), np.float32)
    y0, x0 = (224 - o.shape[0]) // 2, (224 - o.shape[1]) // 2
    c[y0:y0 + o.shape[0], x0:x0 + o.shape[1]] = o
    x = ((c / 255. - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)
    s = _sess()['v']
    e = s.run(None, {s.get_inputs()[0].name: x})[0][0]
    return e / np.linalg.norm(e)


_T = {}


def _texts():
    if not _T:
        _T['body'] = _txt([P + b for b in BODY])
        _T['junk'] = {k: _txt([P + v for v in vs]) for k, vs in JUNK.items()}
        _T['face'] = {k: _txt([P + v for v in vs]).mean(0) for k, vs in FACE.items()}
    return _T


def pixel_tests(px):
    a = px[..., 3] > 128
    n = a.sum()
    if n < 50:
        return 'too few pixels'
    bgr = px[..., :3].astype(np.uint8)
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    tex = cv2.blur(np.abs(cv2.Laplacian(g, cv2.CV_32F)), (5, 5))
    light = (g > 205) & (tex < 6) & a
    if light.sum() > .45 * n:
        return 'blank plate (%.0f%% flat near-white)' % (100 * light.sum() / n)
    # thin strokes (wireframes, text, outlines): most of the alpha disappears under a 7 px erosion
    er = cv2.erode(a.astype(np.uint8), np.ones((7, 7), np.uint8))
    if er.sum() < .35 * n:
        return 'thin strokes (%.0f%% survives a 7 px erosion: wireframe / text)' % (100 * er.sum() / n)
    # a text strip: a long thin band (aspect > 5) with many dark marks
    ys, xs = np.nonzero(a)
    hh, ww = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
    if max(hh, ww) > 5 * min(hh, ww) and ((g < 80) & a).sum() > .08 * n and ((g > 200) & a).sum() > .3 * n:
        return 'text strip (aspect %.1f, dark marks on light)' % (max(hh, ww) / min(hh, ww))
    k, lab, st, _ = cv2.connectedComponentsWithStats(a.astype(np.uint8))
    big = (st[1:, cv2.CC_STAT_AREA] >= .01 * n).sum()
    if big > 6:
        return 'scattered (%d separate blobs: text or a scatter)' % big
    return None


def load():
    return json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def classify(pieces):
    """{id: record} for every piece (cached)"""
    C = load()
    T = None
    changed = False
    for p in pieces:
        if p['id'] in C:
            continue
        T = T or _texts()
        e = _img(p['px'])
        bs = T['body'] @ e
        body = float(bs.max())
        js = {k: float((v @ e).max()) for k, v in T['junk'].items()}
        jk = max(js, key=js.get)
        fp = float(np.exp(100 * (T['face']['painted'] @ e)) / (np.exp(100 * (T['face']['painted'] @ e)) + np.exp(100 * (T['face']['blank'] @ e))))
        why = pixel_tests(p['px'])
        C[p['id']] = {'pixel': why, 'face_p': round(fp, 3), 'body': round(body, 3), 'body_best': BODY[int(bs.argmax())],
                      'junk_scores': {k: round(v, 3) for k, v in js.items()}, 'label': p.get('label')}
        changed = True
    if changed:
        tmp = CACHE + '.%d.tmp' % os.getpid()
        json.dump(C, open(tmp, 'w'), indent=0)
        os.replace(tmp, CACHE)
    return C


MARGIN = {'text': 0., 'figure': 0., 'wire': 0., 'blank': .01, 'feature': .02, 'prop': .02}
# a junk prompt must beat the best body-part prompt by this much (0.005 everywhere threw out sleeves as 'props');
# round 03: text, whole figures and wireframes at 0 (the round 02 critic still found label strips and wireframes)


def junk(r):
    if r.get('pixel'):
        return r['pixel']
    for jk, v in sorted(r['junk_scores'].items(), key=lambda kv: -kv[1]):
        if v > r['body'] + MARGIN.get(jk, .02):
            return 'CLIP reads %s (%.3f) over a body part (%.3f)' % (jk, v, r['body'])
    return None


def is_head(r):
    return r.get('body_best') in ('a head with a face', 'the back of a head')


def clean(pieces):
    """the pieces that pass, and the excluded [(id, reason)]"""
    C = classify(pieces)
    keep, gone = [], []
    for p in pieces:
        why = junk(C.get(p['id'], {}))
        if why:
            gone.append((p['id'], why))
        else:
            keep.append(p)
    return keep, gone
