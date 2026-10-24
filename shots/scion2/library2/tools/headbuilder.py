"""Head builder: blank face plates + face feature cards -> composed heads with new parts.

    python3 shots/scion2/library2/tools/headbuilder.py poet

A feature layout is defined on the canonical head grid of each blank plate, from the plate's own keypoints:
- H = chin.y - crown.y.
- Front: the eye-pair plate is centred on the eye line. The brow-pair plate sits at eye_y - 0.085 H. The mouth
  plate's lip line is at eye_y + 0.55 (chin_y - eye_y), the same ratio as the painted reference faces (lips at
  0.55-0.61 of eye->chin).
- Profile: the eye at the eye_line keypoint. The lips sit under the nose, at the same mouth ratio.
- Plate widths are fractions of H, measured on the kit's own sheets where a plate and a head were cut together:
  - face.front: eye pair 0.56 H, mouth 0.56 H.
  - face.profile: eye 0.31 H, mouth 0.385 H.
  - Brows take the eye-pair width.
The feature pixels are only scaled and placed, never repainted (their brass eyelets are cut out so they do not read
as pivot holes on the face). The poet kit has no nose card, so front composites
of blank plates have no nose; they are flagged no_nose_card.
Composed heads go into index.json as part 'head' with the flag 'composed' and a 'composed_from' list. They share the
source plate's pivot, transform and keypoints. The sheet is sheets/<char>_head_composed_NN.jpg.
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image
import common as C
import index as IX

FRONT = {   # expression -> (eyes card, brows card, mouth card) by card-id suffix
    'neutral':  ('14.faces-hands/eyes-open', '14.faces-hands/eyebrows-neutral', '12.faces/mouth-only'),
    'smile':    ('14.faces-hands/eyes-smiling', '14.faces-hands/eyebrows-neutral-2', '12.faces/mouth'),
    'surprise': ('14.faces-hands/eyes-open-wider', '12.faces/brows-only-2', 'red_black_sunglasses.face.front/open-a'),
    'sad':      ('14.faces-hands/eyes-down', '14.faces-hands/eyebrows-slight-frown', '13.faces/mouth-only'),
    'talk':     ('red_black_sunglasses.face.front/open', '12.faces/brows-only-3', 'red_black_sunglasses.face.front/open-a-2'),
    'eyes_closed': ('12.faces/eyes-only-4', '12.faces/brows-only-5', '12.faces/mouth-only'),
}
PROFILE = {
    'neutral': ('red_black_sunglasses.face.profile/open', 'red_black_sunglasses.face.profile/smile'),
    'grin': ('red_black_sunglasses.face.profile/open', 'red_black_sunglasses.face.profile/grin-teeth'),
    'strain': ('red_black_sunglasses.face.profile/open', 'red_black_sunglasses.face.profile/strain-teeth'),
    'say_o': ('red_black_sunglasses.face.profile/open', 'red_black_sunglasses.face.profile/open-o'),
    'say_a': ('red_black_sunglasses.face.profile/open', 'red_black_sunglasses.face.profile/open-a'),
}
WIDTH = {'eyes': 0.56, 'brows': 0.56, 'mouth': 0.56, 'p_eye': 0.31, 'p_mouth': 0.385}
# where the anchor sits inside each plate (fraction of the cleaned plate's bbox): front plates are centred, the lips
# at 45 % of a mouth plate's height; profile plates face screen-right with the eye / lips near the front edge
ANCHOR = {'eyes': (0.5, 0.5), 'brows': (0.5, 0.5), 'mouth': (0.5, 0.45), 'p_eye': (0.72, 0.42), 'p_mouth': (0.86, 0.45)}


def card(ch, suffix):
    return next((c for c in C.cards() if c['character'] == ch and c['id'].endswith(suffix)), None)


def plate(c):
    """the cleaned, defringed feature plate, cropped to the plate, with its brass eyelets cut out and then trimmed to
    the painted feature with a feathered edge (feature_only): the plate's outline and card rim do not show on the
    face. Only alpha changes; no pixel is repainted."""
    from brass import brass_blobs
    rgba, _ = C.keep_main(C.load_rgba(c))
    rgba = C.defringe(rgba.copy())
    for b in brass_blobs(rgba):
        cv2.circle(rgba, (int(round(b['c'][0])), int(round(b['c'][1]))), int(round(b['r'] * 1.35 + 2)), (0, 0, 0, 0), -1)
    a = rgba[..., 3] > 40
    ys, xs = np.nonzero(a)
    rgba = rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]      # plate bbox: widths below are plate widths
    return feature_only(rgba)


def feature_only(rgba, de=14.0):
    """trim a feature plate to its painted feature: pixels that differ from the plate's own skin/card colour by more
    than `de` (CIE76), away from the plate's cut rim, cleaned and grown a little, then feathered into the head plate.
    Only alpha changes; the painted pixels are not touched."""
    a = rgba[..., 3] > 128
    if a.sum() < 50:
        return rgba
    lab = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2LAB).astype(np.float32)
    lab[..., 0] *= 100 / 255.0
    lab[..., 1:] -= 128
    w = max(rgba.shape[:2])
    inner = cv2.erode(a.astype(np.uint8), np.ones((max(3, int(0.06 * w)) | 1,) * 2, np.uint8)).astype(bool)
    base = np.median(lab[inner], 0) if inner.sum() > 20 else np.median(lab[a], 0)
    d = np.linalg.norm(lab - base, axis=2)
    f = (d > de) & inner
    f = cv2.morphologyEx(f.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab_, st, _ = cv2.connectedComponentsWithStats(f, 8)
    keep = np.zeros_like(f)
    for i in range(1, n):
        if st[i, 4] >= 0.002 * a.sum():
            keep[lab_ == i] = 1
    g = max(3, int(0.03 * w)) | 1
    keep = cv2.dilate(keep, np.ones((g, g), np.uint8))
    soft = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), max(1.5, 0.02 * w))
    out = rgba.copy()
    out[..., 3] = (rgba[..., 3].astype(np.float32) * np.clip(soft * 1.4, 0, 1)).astype(np.uint8)
    return out


def place(base, pl, width_px, anchor_xy, anchor_frac, flip=False):
    if flip:
        pl = pl[:, ::-1]
    s = width_px / pl.shape[1]
    h, w = pl.shape[:2]
    M = np.array([[s, 0, anchor_xy[0] - anchor_frac[0] * w * s], [0, s, anchor_xy[1] - anchor_frac[1] * h * s]], float)
    lay = C.warp(pl, M, (base.shape[1], base.shape[0]))
    out = base.astype(np.float32)
    a = lay[..., 3:4].astype(np.float32) / 255
    # stay inside the head: features never paint outside the plate's silhouette
    a = a * (base[..., 3:4] > 128)
    out[..., :3] = out[..., :3] * (1 - a) + lay[..., :3] * a
    return out.astype(np.uint8)


def run(ch):
    idx = C.load_json(os.path.join(C.LIB2, 'index.json'))
    P = idx['parts']
    heads = [v for v in P.values() if v['character'] == ch and v['part'] == 'head' and v['status'] == 'ok' and 'composed' not in v['flags']]
    blanks = [v for v in heads if v['classes']['state']['value'] == 'blank_face_plate']
    recs, tiles = [], []
    for b in blanks:
        view, facing = b['classes']['view']['value'], b['classes']['facing']['value']
        if view not in ('front', 'side'):
            continue
        base = np.array(Image.open(os.path.join(C.LIB2, b['image'])).convert('RGBA'))
        k = b['keypoints']['canonical']
        H = k['chin'][1] - k['crown'][1]
        E, K = k['eye_line'], k['chin']
        mouth_y = E[1] + 0.55 * (K[1] - E[1])
        sets = FRONT if view == 'front' else PROFILE
        for expr, cards in sets.items():
            cs = [card(ch, s) for s in cards]
            if any(c is None for c in cs):
                continue
            img = base.copy()
            if view == 'front':
                eyes, brows, mouth = cs
                img = place(img, plate(mouth), WIDTH['mouth'] * H, (E[0], mouth_y), ANCHOR['mouth'])
                img = place(img, plate(eyes), WIDTH['eyes'] * H, (E[0], E[1]), ANCHOR['eyes'])
                img = place(img, plate(brows), WIDTH['brows'] * H, (E[0], E[1] - 0.085 * H), ANCHOR['brows'])
                flags = ['composed', 'painted', 'no_nose_card']
            else:
                eye, mouth = cs
                flip = facing == 'screen-left'
                nose = k.get('nose', [E[0] + 0.1 * H, E[1] + 0.2 * H])
                ax = lambda f: (1 - f[0], f[1]) if flip else f
                img = place(img, plate(mouth), WIDTH['p_mouth'] * H, (nose[0] - 0.03 * H * (-1 if flip else 1), mouth_y), ax(ANCHOR['p_mouth']), flip)
                img = place(img, plate(eye), WIDTH['p_eye'] * H, (E[0], E[1]), ax(ANCHOR['p_eye']), flip)
                flags = ['composed', 'painted'] + (['features_mirrored'] if flip else [])
            key = b['key'] + '+' + expr
            rec = json.loads(json.dumps(b))
            rec.update(key=key, image='%s/head_composed/%s__%s.png' % (ch, C.slug(b['source_card']), expr),
                       composed_from={'plate': b['key'], 'features': [c['id'] for c in cs], 'expression': expr,
                                      'layout': 'eye pair on the eye line; brows at eye-0.085H; lips at eye+0.55(chin-eye); widths %s' % WIDTH},
                       flags=sorted(set([f for f in b['flags'] if f != 'blank'] + flags)))
            rec['classes'] = dict(rec['classes'])
            rec['classes']['state'] = {'value': 'composed_face', 'conf': 0.9, 'source': 'headbuilder: blank plate + feature cards'}
            rec['classes']['expression'] = {'value': expr, 'conf': 0.8, 'source': 'headbuilder feature set'}
            out = os.path.join(C.LIB2, rec['image'])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            Image.fromarray(img).save(out, optimize=True)
            recs.append(rec)
            lines = [b['source_card'].split('/')[-1][:30] + ' + ' + expr, '%s %s  COMPOSED' % (view, facing),
                     'eyes/mouth: ' + cs[0]['id'].split('/')[-1][:14] + ' / ' + cs[-1]['id'].split('/')[-1][:16], ','.join(rec['flags'])[:44]]
            tiles.append(C.draw_tile(img, 'head', {k2: v for k2, v in k.items() if k2 in ('pivot', 'eye_line', 'chin', 'crown')}, [], lines))
    # merge: replace earlier composed records of this character
    idx['parts'] = {kk: v for kk, v in P.items() if not (v['character'] == ch and v['part'] == 'head' and 'composed' in v.get('flags', []))}
    for r in recs:
        idx['parts'][r['key']] = r
    with open(os.path.join(C.LIB2, 'index.json'), 'w') as f:
        json.dump(idx, f, indent=1)
    sheets = C.sheet(tiles, os.path.join(C.LIB2, 'sheets', '%s_head_composed_%%02d.jpg' % ch), cols=6,
                     title='%s composed heads: blank plates + feature cards (head grid; COMPOSED, not painted as one)' % ch)
    print(len(recs), '\n'.join(sheets))


if __name__ == '__main__':
    for ch in sys.argv[1:]:
        run(ch)
