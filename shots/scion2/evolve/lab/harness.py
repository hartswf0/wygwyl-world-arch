"""The algorithm lab's shared harness: one target context, any algorithm, one scorer, one renderer.

An algorithm is evolve/lab/algos/<name>.py with
    assemble(target, library, seed) -> {'pieces': [{'pi': int, 'M': 2x3 card px -> target px}], 'edges': [[i, bi, j, bj]],
                                        'info': {...}}
where `target` is the context dict (t: the target from puzzle.fill.target, i.e. the reference silhouette and, for
algorithms that ask for it, the markers / studs) and `library` is the list of pieces (puzzle.pieces.pieces_for: every
card of the character as pixels + brads, minus anything cut from the target painting). An edge is a snapped brad pair:
piece i's brad bi on piece j's brad bj.

Scores (score()):
  coverage    share of the reference figure covered
  overflow    share (of the figure area) covered OUTSIDE the figure, beyond a 2 px anti-alias band
  components  connected components of the snapped graph (pieces with no edge are their own component); a body is 1
  pieces, snaps
  clip        cosine of CLIP ViT-B/32 image embeddings, render vs reference, same crop, same neutral background
  segments_missing  skeleton segments (head, torso, hips, each upper arm / forearm / hand / thigh / shin / foot) whose
              region of the figure is less than 50% covered (round 02)
  Q           coverage - 10 overflow - 0.05 (components - 1) - 0.003 pieces + 0.5 clip - 0.05 segments_missing
              (the selection proxy; the blind critic's verdicts outrank it)
"""
import importlib, json, math, os, sys, time
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..')))
from evolve.puzzle import fill as FL, pieces as PC  # noqa: E402

BG = (226, 232, 235)          # BGR of the neutral background (235, 232, 226 RGB, as clip_label.py)
CLIP = '/tmp/claude-0/clip/visual.onnx'
MEAN, STD = np.array([0.48145466, 0.4578275, 0.40821073]), np.array([0.26862954, 0.26130258, 0.27577711])


def context(char, costume, tid):
    t = FL.target(char, costume, tid)
    # other figures: keep the largest alpha component and any component >= 20% of it
    fig = t['fig_t'].astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(fig)
    if n > 2:
        big = st[1:, cv2.CC_STAT_AREA].max()
        keep = np.zeros(n, bool)
        keep[1:] = st[1:, cv2.CC_STAT_AREA] >= .2 * big
        drop = (~keep[lab]) & (lab > 0)
        t['ignore'] = t['ignore'] | drop
        t['fig_t'] = t['fig_t'] & ~drop
        FL_resample(t)
    # props merged with the figure (a door frame, a table, a window): alpha farther than PROP_CM from every segment
    # of the Pose Lab skeleton is not the figure (round 02)
    Z = skeleton_distance(t)
    prop = t['fig_t'] & (Z > PROP_CM * t['s'])
    if prop.any():
        n, lab, st, _ = cv2.connectedComponentsWithStats(prop.astype(np.uint8))
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] >= 40:          # specks at the outline stay figure
                t['ignore'] = t['ignore'] | (lab == i)
                t['fig_t'] = t['fig_t'] & ~(lab == i)
        FL_resample(t)
    pieces, gone = PC.pieces_for(char, costume, tid)
    return {'t': t, 'pieces': pieces, 'excluded': gone, 'char': char, 'costume': costume, 'id': tid}


PROP_CM = 20.0


def skeleton_distance(t):
    m = t['markers']
    mid = (m['hipL'] + m['hipR']) / 2
    sp = m['neck'] - mid
    # the head marker sits on the face, the toe marker inside the shoe: both segments are extended past them
    segs = [(m['neck'], m['neck'] + 2.2 * (m['head'] - m['neck'])), (m['neck'], mid), (m['hipL'], m['hipR'])]
    for S in 'LR':
        e, w_ = m['elbow' + S], m['wrist' + S]
        segs += [(m['neck'], m['shoulder' + S]), (m['shoulder' + S], e), (e, w_), (w_, w_ + .8 * (w_ - e)),
                 (m['hip' + S], m['knee' + S]), (m['knee' + S], m['ankle' + S]), (m['ankle' + S], m['toe' + S] + .6 * (m['toe' + S] - m['ankle' + S]))]
    H, W = t['fig_t'].shape
    ys, xs = np.nonzero(t['fig_t'])
    P = np.stack([xs, ys], 1).astype(np.float64)
    D = np.min(np.stack([FL.AS_seg(P, a, b) for a, b in segs], 1), 1)
    Z = np.zeros((H, W), np.float32)
    Z[ys, xs] = D
    return Z


def segment_coverage(t, U):
    """share of each skeleton segment's region of the figure (pixels nearest that segment) that the assembly covers"""
    m = t['markers']
    mid = (m['hipL'] + m['hipR']) / 2
    segs = {'head': (m['neck'], m['neck'] + 1.3 * (m['head'] - m['neck'])), 'torso': (m['neck'], mid), 'hips': (m['hipL'], m['hipR'])}
    for S in 'LR':
        e, w_ = m['elbow' + S], m['wrist' + S]
        segs.update({'upper_arm' + S: (m['shoulder' + S], e), 'forearm' + S: (e, w_), 'hand' + S: (w_, w_ + .6 * (w_ - e)),
                     'thigh' + S: (m['hip' + S], m['knee' + S]), 'shin' + S: (m['knee' + S], m['ankle' + S]), 'foot' + S: (m['ankle' + S], m['toe' + S])})
    ys, xs = np.nonzero(t['fig_t'])
    P = np.stack([xs, ys], 1).astype(np.float64)
    names = list(segs)
    lab = np.argmin(np.stack([FL.AS_seg(P, a, b) for a, b in segs.values()], 1), 1)
    cov = U[ys, xs]
    out = {}
    for i, nm in enumerate(names):
        sel = lab == i
        if sel.sum() >= 20:
            out[nm] = float(cov[sel].mean())
    return out


def FL_resample(t):
    H, W = t['fig_t'].shape
    Wk, Hk = t['work_size']
    share = cv2.resize(t['fig_t'].astype(np.float32), (Wk, Hk), interpolation=cv2.INTER_AREA)
    ignw = cv2.resize(t['ignore'].astype(np.float32), (Wk, Hk), interpolation=cv2.INTER_AREA) > .3
    t['inside_w'] = share >= .6
    t['outside_w'] = (share < .15) & ~ignw
    t['fig_dil'] = cv2.dilate(t['fig_t'].astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * FL.TOL_PX + 1,) * 2)) > 0


def load_algo(name):
    return importlib.import_module('evolve.lab.algos.' + name)


def masks(ctx, asm):
    t = ctx['t']
    W, H = t['size']
    return [cv2.warpAffine(ctx['pieces'][p['pi']]['px'][..., 3], np.asarray(p['M'], float), (W, H), flags=cv2.INTER_LINEAR) > 128
            for p in asm['pieces']]


def render(ctx, asm):
    t = ctx['t']
    W, H = t['size']
    acc = np.zeros((H, W, 4), np.float32)
    for p in asm['pieces']:
        lay = cv2.warpAffine(ctx['pieces'][p['pi']]['px'], np.asarray(p['M'], float), (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        a = lay[..., 3:] / 255.
        acc[..., :3] = lay[..., :3] * a + acc[..., :3] * (1 - a)
        acc[..., 3:] = 255 * a + acc[..., 3:] * (1 - a)
    return acc


def components(n, edges):
    par = list(range(n))

    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for e in edges:
        if e[0] < n and e[2] < n:
            par[f(e[0])] = f(e[2])
    roots = [f(i) for i in range(n)]
    return len(set(roots)), roots


def on_bg(bgra, box):
    x0, y0, x1, y1 = box
    a = bgra[y0:y1, x0:x1, 3:] / 255.
    return (bgra[y0:y1, x0:x1, :3] * a + np.array(BG, np.float32) * (1 - a)).astype(np.uint8)


def crop_box(t, extra=None):
    ys, xs = np.nonzero(t['fig_t'] | (extra if extra is not None else False))
    p = 6
    H, W = t['fig_t'].shape
    return max(0, xs.min() - p), max(0, ys.min() - p), min(W, xs.max() + p + 1), min(H, ys.max() + p + 1)


_SESS = {}


def clip_embed(bgr):
    import onnxruntime as ort
    if 'v' not in _SESS:
        so = ort.SessionOptions(); so.intra_op_num_threads = 1
        _SESS['v'] = ort.InferenceSession(CLIP, so, providers=['CPUExecutionProvider'])
    s = _SESS['v']
    rgb = bgr[..., ::-1]
    h, w = rgb.shape[:2]
    k = 224 / max(w, h)
    im = cv2.resize(rgb, (max(1, round(w * k)), max(1, round(h * k))), interpolation=cv2.INTER_CUBIC)
    c = np.full((224, 224, 3), (235, 232, 226), np.uint8)
    y0, x0 = (224 - im.shape[0]) // 2, (224 - im.shape[1]) // 2
    c[y0:y0 + im.shape[0], x0:x0 + im.shape[1]] = im
    x = ((c / 255.0 - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)
    e = s.run(None, {s.get_inputs()[0].name: x})[0][0]
    return e / (np.linalg.norm(e) + 1e-9)


def score(ctx, asm):
    t = ctx['t']
    ms = masks(ctx, asm)
    fig, fd, ign = t['fig_t'], t['fig_dil'], t['ignore']
    U = np.zeros(fig.shape, bool)
    for m in ms:
        U |= m
    area = max(fig.sum(), 1)
    n = len(asm['pieces'])
    comp, _ = components(n, asm.get('edges', []))
    ren = render(ctx, asm)
    box = crop_box(t, U)
    ref = t['ref'].astype(np.float32).copy()
    ref[..., 3] *= ~ign                      # props / other figures off the reference too
    try:
        clip = float(clip_embed(on_bg(ren, box)) @ clip_embed(on_bg(ref, box)))
    except Exception as e:
        clip = float('nan')
    s = {'coverage': float((U & fig).sum() / area), 'overflow': float((U & ~fd & ~ign).sum() / area),
         'components': int(comp) if n else 0, 'pieces': n, 'snaps': len(asm.get('edges', [])), 'clip': clip}
    seg = segment_coverage(t, U)
    s['segments_missing'] = int(sum(1 for v in seg.values() if v < .5))
    s['segment_coverage'] = {k: round(v, 3) for k, v in seg.items()}
    s['Q'] = float(s['coverage'] - 10 * s['overflow'] - .05 * max(0, s['components'] - 1) - .003 * n + .5 * (0 if math.isnan(clip) else clip)
                   - .05 * s['segments_missing'])
    return s, ms, ren


def run(algo, ctx, seed=0):
    t0 = time.time()
    asm = load_algo(algo).assemble(ctx, ctx['pieces'], seed)
    asm['seconds'] = round(time.time() - t0, 1)
    return asm
