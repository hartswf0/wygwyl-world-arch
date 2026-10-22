"""Label every card in the Skin Lab library with CLIP (zero-shot): which way it faces, whether a head already has a
painted face, which feature a face card is, and whether the card even looks like the part it is filed under.

    CLIP_DIR=/path/to/clip python3 shots/skinlab/clip_label.py     # -> shots/skinlab/clip.json

CLIP_DIR holds ViT-B-32 as ONNX (visual.onnx, textual.onnx) from clip-as-service
(https://clip-as-service.s3.us-east-2.amazonaws.com/models/onnx/ViT-B-32/{visual,textual}.onnx), plus OpenAI's
simple_tokenizer.py and bpe_simple_vocab_16e6.txt.gz (MIT; shipped in the clip_server package). Needs onnxruntime,
ftfy, regex. The weights are not committed; clip.json is, and build.py folds it into library.json.

Zero-shot CLIP reads these cut-outs badly (on view it agrees with the labels about half the time on heads and torsos,
13/135 on feet), so the answers that matter are learnt instead: CLIP's image embedding + a logistic regression trained
on the cards that do carry a label (view per part; the part itself, from cards whose file name agrees). Each is scored
by 5-fold cross-validation (printed), then predicts every card; a confident prediction that disagrees with the card's
label is written as a flag, for a person to settle. Zero-shot is kept only where there is nothing to learn from
(painted vs blank face, the kind of eye or mouth, hand pose).
"""
import json, os, re, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CLIP = os.environ.get('CLIP_DIR', '/tmp/claude-0/clip')
sys.path.insert(0, CLIP)
import onnxruntime as ort                      # noqa: E402
from simple_tokenizer import SimpleTokenizer   # noqa: E402

TOK = SimpleTokenizer()
MEAN, STD = np.array([0.48145466, 0.4578275, 0.40821073]), np.array([0.26862954, 0.26130258, 0.27577711])
P = 'a paper cut-out puppet piece: '
# the questions, per slot: name -> {answer: [prompts]}
VIEWS = lambda thing: {
    'front': [f'{P}{thing} seen from the front', f'{P}the front of {thing}, facing the viewer'],
    'side': [f'{P}{thing} seen from the side, in profile', f'{P}a side view of {thing}'],
    'back': [f'{P}{thing} seen from behind', f'{P}the back of {thing}'],
}
Q = {
    'head': {
        'view': {'front': [f'{P}a head facing the viewer, front view', f'{P}a face seen straight on'],
                 'side': [f'{P}a head in profile, side view', f'{P}a side view of a head showing the nose and one ear'],
                 'threequarter': [f'{P}a head turned three-quarters', f'{P}a three-quarter view of a head'],
                 'back': [f'{P}the back of a head, hair only, no face', f'{P}a head seen from behind']},
        'faces': {'L': [f'{P}a head in profile facing left'], 'R': [f'{P}a head in profile facing right']},
        'face': {'painted': [f'{P}a head with painted eyes, nose and mouth', f'{P}a face with eyes and lips'],
                 'blank': [f'{P}a head with a blank face, no eyes, no mouth', f'{P}a featureless blank face']},
    },
    'torso': {'view': VIEWS('a torso')},
    'pelvis': {'view': VIEWS('hips')},
    'thigh': {'view': VIEWS('a thigh')}, 'shin': {'view': VIEWS('a lower leg')},
    'upper_arm': {'view': VIEWS('an upper arm')}, 'forearm': {'view': VIEWS('a forearm')},
    'foot': {'view': {'side': [f'{P}a shoe seen from the side'], 'front': [f'{P}a shoe seen from the front, toe towards the viewer'],
                      'back': [f'{P}a shoe seen from behind, the heel']},
             'faces': {'L': [f'{P}a shoe pointing left'], 'R': [f'{P}a shoe pointing right']}},
    'hand': {'pose': {'open': [f'{P}an open hand'], 'fist': [f'{P}a closed fist'], 'point': [f'{P}a hand pointing a finger'],
                      'relaxed': [f'{P}a relaxed hand'], 'grip': [f'{P}a hand gripping something']}},
    'eye': {'kind': {'one': [f'{P}a single eye'], 'pair': [f'{P}a pair of eyes'], 'closed': [f'{P}a closed eye'], 'plate': [f'{P}a patch of skin with an eye painted on it']}},
    'mouth': {'kind': {'closed': [f'{P}a closed mouth, lips'], 'smile': [f'{P}a smiling mouth'], 'open': [f'{P}an open mouth'], 'teeth': [f'{P}a grin showing teeth']}},
}
SLOTS = {'head': 'a head', 'torso': 'a torso or jacket', 'pelvis': 'hips or a hip bridge', 'thigh': 'a thigh', 'shin': 'a lower leg', 'foot': 'a shoe or foot',
         'upper_arm': 'an upper arm', 'forearm': 'a forearm', 'hand': 'a hand', 'eye': 'an eye', 'brow': 'an eyebrow', 'mouth': 'a mouth', 'nose': 'a nose',
         'other': 'a prop or object, not a body part'}


def tokens(texts):
    out = np.zeros((len(texts), 77), np.int64)
    for i, t in enumerate(texts):
        ids = [49406] + TOK.encode(t)[:75] + [49407]
        out[i, :len(ids)] = ids
    return out


def prep(path):
    im = Image.open(path).convert('RGBA')
    bg = Image.new('RGBA', im.size, (235, 232, 226, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
    w, h = im.size; s = 224 / max(w, h)                     # fit whole card (a crop would cut feet and hands off)
    im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.BICUBIC)
    c = Image.new('RGB', (224, 224), (235, 232, 226)); c.paste(im, ((224 - im.width) // 2, (224 - im.height) // 2))
    return ((np.asarray(c) / 255.0 - MEAN) / STD).transpose(2, 0, 1).astype(np.float32)


def norm(x):
    return x / np.linalg.norm(x, axis=-1, keepdims=True)


VIEWG = {'profile': 'side', 'front': 'front', 'threequarter': 'front', 'back': 'back', 'threequarter_back': 'back'}
NAMEOK = {'upper_arm': r'upper|uarm|bicep|arm-a\b|^arm', 'forearm': r'fore|farm', 'hand': r'hand|palm|fist|grip|point|pinch|relax|open|thumb|wave|cup|claw',
          'thigh': r'thigh', 'shin': r'shin|calf', 'foot': r'foot|shoe|boot|sneak|heel|toe', 'head': r'head|face', 'torso': r'torso|chest|jacket|shirt|vest|bodice',
          'pelvis': r'hip|pelvis|waist', 'eye': r'eye', 'brow': r'brow', 'mouth': r'mouth|lip|smile|grin|teeth', 'nose': r'nose'}


def learn(L, E, out):
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict
    def fit(idx, y, name, field, min_n=20):
        y = np.array(y); keep = [i for i, v in zip(idx, y)]
        if len(set(y)) < 2 or len(y) < min_n:
            return
        X = E[idx]; clf = LogisticRegression(max_iter=2000, C=2.0, class_weight='balanced')
        cv = cross_val_predict(clf, X, y, cv=min(5, min(np.unique(y, return_counts=True)[1])))
        acc = (cv == y).mean(); clf.fit(X, y)
        print(f'  {name}: {len(y)} labelled, {len(set(y))} classes, cross-validated accuracy {acc:.0%}')
        P = clf.predict_proba(E); cls = list(clf.classes_)
        for c, p in zip(L, P):
            if field == 'part' or c['slot'] in name.split('+'):
                out[c['id']][field] = cls[int(p.argmax())]; out[c['id']][field + '_p'] = round(float(p.max()), 3)
        return acc
    HL = json.load(open(os.path.join(HERE, 'labels.json'))).get('cards', {}) if os.path.exists(os.path.join(HERE, 'labels.json')) else {}
    for c in L:   # a person's answers (exported from the Skin Lab) are labels too, and win
        h = HL.get(c['id'], {})
        if h.get('view'): c['view'] = {'side': 'profile'}.get(h['view'], h['view'])
        if h.get('slot'): c['slot'] = h['slot']
    print('learnt from the labels:')
    # view, per family of parts that look alike
    for fam in (['head'], ['torso', 'pelvis'], ['thigh', 'shin', 'upper_arm', 'forearm'], ['foot'], ['hand']):
        idx = [i for i, c in enumerate(L) if c['slot'] in fam and VIEWG.get(c.get('view'))]
        fit(idx, [VIEWG[L[i]['view']] for i in idx], '+'.join(fam), 'view_l')
    # the part itself, trained on cards whose file name agrees with their slot
    idx = [i for i, c in enumerate(L) if re.search(NAMEOK.get(c['slot'], '^$'), c['id'].split('/')[-1].lower())]
    fit(idx, [L[i]['slot'] for i in idx], 'part', 'part')
    # flags: a confident learnt answer that contradicts the card
    for c in L:
        r = out[c['id']]; f = []
        if r.get('part') and r['part'] != c['slot'] and r['part_p'] > .8: f.append(f"looks like a {r['part']}")
        if r.get('view_l') and c.get('view') and VIEWG.get(c['view']) != r['view_l'] and r['view_l_p'] > .85: f.append(f"looks {r['view_l']}, labelled {c['view']}")
        if f: r['flags'] = f


def main():
    vis, txt = ort.InferenceSession(os.path.join(CLIP, 'visual.onnx')), ort.InferenceSession(os.path.join(CLIP, 'textual.onnx'))
    T = lambda texts: norm(txt.run(None, {'input': tokens(texts)})[0])
    L = json.load(open(os.path.join(HERE, 'library.json')))
    E = []
    for i in range(0, len(L), 32):
        batch = np.stack([prep(os.path.join(HERE, c['img'])) for c in L[i:i + 32]])
        E.append(vis.run(None, {'input': batch})[0])
        print(f'\r{i + len(batch)}/{len(L)}', end='', flush=True)
    E = norm(np.concatenate(E)); print()
    np.save(os.path.join(CLIP, 'emb.npy'), E.astype(np.float16))
    slot_names = list(SLOTS); slot_txt = T([f'{P}{v}' for v in SLOTS.values()])
    qtxt = {s: {q: (list(a), np.stack([T(p).mean(0) for p in a.values()])) for q, a in qs.items()} for s, qs in Q.items()}
    out = {}
    for c, e in zip(L, E):
        r = {}
        p = np.exp(100 * e @ slot_txt.T); p /= p.sum()
        r['slot'] = slot_names[int(p.argmax())]; r['slot_p'] = round(float(p[slot_names.index(c['slot'])]), 3) if c['slot'] in slot_names else None
        for q, (names, tv) in qtxt.get(c['slot'], {}).items():
            tv = norm(tv); p = np.exp(100 * e @ tv.T); p /= p.sum()
            r[q] = names[int(p.argmax())]; r[q + '_p'] = round(float(p.max()), 3)
        out[c['id']] = r
    learn(L, E, out)
    json.dump(out, open(os.path.join(HERE, 'clip.json'), 'w'), separators=(',', ':'))
    # how CLIP's view compares with the cards that carry a view label
    G = lambda v: {'profile': 'side', 'side': 'side', 'front': 'front', 'threequarter': 'front' if True else v, 'back': 'back', 'threequarter_back': 'back'}.get(v)
    from collections import Counter, defaultdict
    agree = defaultdict(Counter)
    for c in L:
        r = out[c['id']]
        if c.get('view') and 'view' in r:
            agree[c['slot']][G(c['view']) == G(r['view'])] += 1
    print('view: CLIP agrees with the label', {s: f'{a[True]}/{a[True] + a[False]}' for s, a in agree.items()})
    print('slot: CLIP thinks it is something else', Counter(c['slot'] for c in L if out[c['id']]['slot'] != c['slot']))


if __name__ == '__main__':
    main()
