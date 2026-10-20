"""Draw the arena's stand-in cardboard dummy pieces (DRAWN, not generated): one set per performer palette.

Every bone piece is drawn lying along +x: the pivot (proximal brad) at (PAD + r0, CY), the end joint at
(PAD + r0 + LEN, CY). The renderer scales x by the bone's actual length and y by the body scale, so the same
art fits any proportions. Asymmetric pieces (head, foot, hand, side torso) have their front on +y and are
mirrored by the renderer when the puppet faces left.

When the man's library is cut (cast/man/build_cast.py), its pieces replace these by id; nothing else changes.
"""
import json, os
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cast', 'dummy')
LEN = 200  # image px between the two joints of a piece
REF_H = 520  # standing height the widths are drawn for (piece widths are fractions of height)

PALETTES = {
    'bola': dict(card=(92, 140, 196), edge=(52, 84, 126), trim=(48, 86, 220), dark=0.72),   # tan card, red-orange trim (BGR)
    'shim': dict(card=(170, 150, 128), edge=(110, 92, 74), trim=(90, 60, 40), dark=0.72),   # grey-blue card
    'dot': dict(card=(80, 170, 200), edge=(40, 110, 140), trim=(60, 60, 150), dark=0.72),   # ochre card
}

# piece: (bone fraction of height used to scale width, proximal radius, distal radius) radii as fraction of height
PIECES = {
    'thigh': (0.245, 0.052, 0.040), 'shin': (0.245, 0.038, 0.030), 'uarm': (0.165, 0.032, 0.027),
    'farm': (0.145, 0.027, 0.022), 'torso_side': (0.30, 0.085, 0.07), 'torso_front': (0.30, 0.095, 0.11),
}


def rng_tex(h, w, seed):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (h // 4 + 1, w // 4 + 1)).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    fib = r.normal(0, 1, (h, w)).astype(np.float32)
    fib = cv2.GaussianBlur(fib, (9, 1), 0)
    return n * 5 + fib * 4


def finish(img, mask, pal, seed, far):
    h, w = mask.shape
    tex = rng_tex(h, w, seed)[..., None]
    col = np.clip(img.astype(np.float32) + tex, 0, 255)
    if far:
        col *= pal['dark']
    # paper border: a thin light rim where scissors cut
    inner = cv2.erode(mask, np.ones((5, 5), np.uint8))
    rim = (mask > 0) & (inner == 0)
    col[rim] = (214, 222, 228) if not far else (150, 156, 160)
    a = cv2.GaussianBlur(mask.astype(np.float32), (3, 3), 0.7)
    return np.dstack([col.astype(np.uint8), a.astype(np.uint8)])


def brad(img, c, r=7):
    cv2.circle(img, c, r, (40, 140, 190, 255), -1, cv2.LINE_AA)
    cv2.circle(img, c, r, (20, 70, 100, 255), 1, cv2.LINE_AA)
    cv2.circle(img, (c[0] - 2, c[1] - 2), 2, (170, 225, 245, 255), -1, cv2.LINE_AA)


def bone_piece(name, pal, far, seed):
    frac, r0f, r1f = PIECES[name]
    s = LEN / (frac * REF_H)  # image px per stage px at reference height
    r0, r1 = int(r0f * REF_H * s), int(r1f * REF_H * s)
    pad = 6
    w = pad * 2 + r0 + LEN + r1
    hh = 2 * max(r0, r1) + pad * 2
    cy = hh // 2
    p0, p1 = (pad + r0, cy), (pad + r0 + LEN, cy)
    mask = np.zeros((hh, w), np.uint8)
    poly = np.array([[p0[0], cy - r0], [p1[0], cy - r1], [p1[0], cy + r1], [p0[0], cy + r0]], np.int32)
    cv2.fillPoly(mask, [poly], 255)
    cv2.circle(mask, p0, r0, 255, -1, cv2.LINE_AA); cv2.circle(mask, p1, r1, 255, -1, cv2.LINE_AA)
    img = np.zeros((hh, w, 3), np.uint8); img[:] = pal['card']
    cv2.polylines(img, [poly], True, pal['edge'], 2, cv2.LINE_AA)
    if name.startswith('torso'):
        # trim: the jacket's piping as two curved stripes (a nod to the man's track jacket)
        for k in (-1, 1) if name == 'torso_front' else (1,):
            pts = np.array([[p1[0] - 10, cy + k * int(r1 * 0.55)], [int(p0[0] + LEN * 0.55), cy + k * int(r0 * 0.25)],
                            [p0[0] + 20, cy + k * int(r0 * 0.15)]], np.int32)
            cv2.polylines(img, [pts], False, pal['trim'], 6, cv2.LINE_AA)
    out = finish(img, mask, pal, seed, far)
    brad(out, p0)
    return out, {'pivot': list(p0), 'end': list(p1), 'len': LEN, 'unit': s}


def foot_piece(pal, far, seed):
    # bone = ankle -> toe at pitch 0; heel behind the ankle, sole along +y
    L = 0.115 * REF_H; s = LEN / L
    ank = 0.04 * REF_H * s; heel = 0.045 * REF_H * s
    pad = 8
    w = int(pad * 2 + heel + LEN + 6); hh = int(ank + pad * 2 + 24)
    p0 = (int(pad + heel), int(pad + 16)); p1 = (int(pad + heel + LEN), p0[1])
    sole = p0[1] + int(ank)
    mask = np.zeros((hh, w), np.uint8)
    poly = np.array([[p0[0] - 14, p0[1] - 16], [p0[0] + 26, p0[1] - 18], [p1[0] - 30, sole - 30], [p1[0], sole - 10],
                     [p1[0] + 2, sole], [pad, sole], [pad - 2, sole - 20]], np.int32)
    cv2.fillPoly(mask, [poly], 255)
    img = np.zeros((hh, w, 3), np.uint8); img[:] = tuple(int(c * 0.55) for c in pal['card'])
    cv2.line(img, (pad, sole - 4), (p1[0], sole - 4), (30, 30, 30), 6)
    out = finish(img, mask, pal, seed, far)
    brad(out, p0, 6)
    return out, {'pivot': list(p0), 'end': list(p1), 'len': LEN, 'unit': s, 'mirror': True}


def head_piece(pal, view, expr, seed):
    # bone = neck -> crown (drawn along +x); the face is on +y
    L = 0.16 * REF_H; s = LEN / L
    R = int(0.062 * REF_H * s)
    pad = 8
    w = pad * 2 + LEN + 10; hh = 2 * R + pad * 2 + 20
    cy = hh // 2
    p0 = (pad + 4, cy); p1 = (pad + 4 + LEN, cy)
    cxh = p0[0] + int(LEN * 0.62)
    mask = np.zeros((hh, w), np.uint8)
    cv2.ellipse(mask, (cxh, cy), (int(R * 1.08), R), 0, 0, 360, 255, -1, cv2.LINE_AA)
    cv2.rectangle(mask, (p0[0], cy - int(R * 0.35)), (cxh, cy + int(R * 0.35)), 255, -1)  # neck
    if view == 'side':
        cv2.circle(mask, (cxh - int(R * 0.15), cy + int(R * 0.95)), int(R * 0.22), 255, -1, cv2.LINE_AA)  # nose
    img = np.zeros((hh, w, 3), np.uint8); img[:] = pal['card']
    # hair: a cropped cap on the crown and the back of the head (+x is up, -y is the back)
    if view == 'side':
        cv2.ellipse(img, (cxh + int(R * 0.42), cy - int(R * 0.28)), (int(R * 0.72), int(R * 0.78)), 0, 0, 360, (40, 40, 44), -1, cv2.LINE_AA)
    else:
        cv2.ellipse(img, (cxh + int(R * 0.62), cy), (int(R * 0.5), int(R * 1.02)), 0, 0, 360, (40, 40, 44), -1, cv2.LINE_AA)
    ink = (25, 20, 18)
    # face features in the head's frame: +x is up (toward the crown), +y is forward
    def P(u, v):  # u up, v forward, in head radii
        return (int(cxh + u * R), int(cy + v * R))
    if view == 'side':
        eye, brow, mouth = P(0.18, 0.62), P(0.42, 0.6), P(-0.42, 0.62)
        cv2.circle(img, eye, 7 if expr != 'closed' else 2, ink, -1, cv2.LINE_AA)
        if expr in ('fear', 'surprise'):
            cv2.circle(img, eye, 11, ink, 2, cv2.LINE_AA)
        bw = {'strain': (0.33, 0.45, 0.42, 0.75), 'fear': (0.5, 0.45, 0.42, 0.75), 'surprise': (0.55, 0.45, 0.55, 0.75),
              'smile': (0.45, 0.45, 0.45, 0.75), 'pain': (0.3, 0.45, 0.46, 0.75), 'impatient': (0.4, 0.45, 0.36, 0.75),
              'listen': (0.48, 0.45, 0.48, 0.75)}.get(expr, (0.42, 0.45, 0.42, 0.75))
        cv2.line(img, P(bw[0], bw[1]), P(bw[2], bw[3]), ink, 4, cv2.LINE_AA)
        m = {'smile': [(-0.38, 0.5), (-0.48, 0.66), (-0.4, 0.8)], 'strain': [(-0.42, 0.52), (-0.42, 0.8)],
             'fear': [(-0.36, 0.6), (-0.5, 0.62), (-0.36, 0.75)], 'surprise': [(-0.34, 0.66), (-0.52, 0.66), (-0.43, 0.8), (-0.34, 0.66)],
             'pain': [(-0.46, 0.5), (-0.4, 0.62), (-0.46, 0.78)], 'impatient': [(-0.44, 0.55), (-0.44, 0.78)],
             'neutral': [(-0.42, 0.55), (-0.44, 0.78)]}.get(expr, [(-0.42, 0.55), (-0.44, 0.78)])
        cv2.polylines(img, [np.array([P(*q) for q in m], np.int32)], False, ink, 4, cv2.LINE_AA)
    else:
        for side in (-1, 1):
            e = P(0.15, side * 0.38)
            cv2.circle(img, e, 7 if expr != 'closed' else 2, ink, -1, cv2.LINE_AA)
            if expr in ('fear', 'surprise'):
                cv2.circle(img, e, 11, ink, 2, cv2.LINE_AA)
            cv2.line(img, P(0.4, side * 0.2), P(0.42 if expr != 'strain' else 0.32, side * 0.55), ink, 4, cv2.LINE_AA)
        mm = {'smile': [(-0.38, -0.3), (-0.5, 0), (-0.38, 0.3)], 'surprise': [(-0.36, -0.12), (-0.55, 0), (-0.36, 0.12), (-0.36, -0.12)],
              'strain': [(-0.45, -0.3), (-0.42, 0.3)], 'fear': [(-0.44, -0.25), (-0.38, 0), (-0.44, 0.25)]}.get(expr, [(-0.44, -0.22), (-0.44, 0.22)])
        cv2.polylines(img, [np.array([P(*q) for q in mm], np.int32)], False, ink, 4, cv2.LINE_AA)
    out = finish(img, mask, pal, seed, False)
    brad(out, p0, 6)
    return out, {'pivot': list(p0), 'end': list(p1), 'len': LEN, 'unit': s, 'mirror': view == 'side'}


def hand_piece(pal, shape, far, seed):
    # bone = wrist -> fingertip; thumb on -y (up when the hand points forward and down), fingers toward +x
    L = 0.095 * REF_H; s = LEN / L
    pad = 10
    w = pad * 2 + LEN + 10; hh = int(0.06 * REF_H * s) + pad * 2
    cy = hh // 2
    p0 = (pad + 4, cy); p1 = (pad + 4 + LEN, cy)
    mask = np.zeros((hh, w), np.uint8)
    pw = int(0.022 * REF_H * s)
    if shape in ('fist', 'grip'):
        cv2.rectangle(mask, (p0[0], cy - pw), (p0[0] + int(LEN * 0.62), cy + pw), 255, -1)
        cv2.circle(mask, (p0[0] + int(LEN * 0.6), cy), int(pw * 1.15), 255, -1, cv2.LINE_AA)
        if shape == 'grip':  # a hook of fingers that closes round a handle at the palm socket
            cv2.ellipse(mask, (p0[0] + int(LEN * 0.55), cy + int(pw * 0.2)), (int(LEN * 0.22), int(pw * 1.3)), 0, -10, 200, 255, int(pw * 0.7))
    else:
        cv2.rectangle(mask, (p0[0], cy - pw), (p0[0] + int(LEN * 0.55), cy + pw), 255, -1)
        for k, dy in enumerate((-0.7, -0.25, 0.2, 0.62)):
            ln = LEN * (0.95 if shape != 'point' or k == 0 else 0.62)
            y = cy + int(dy * pw)
            cv2.line(mask, (p0[0] + int(LEN * 0.5), y), (p0[0] + int(ln), y), 255, int(pw * 0.42), cv2.LINE_AA)
        cv2.line(mask, (p0[0] + int(LEN * 0.3), cy - pw), (p0[0] + int(LEN * 0.62), cy - int(pw * 1.9)), 255, int(pw * 0.45), cv2.LINE_AA)
    img = np.zeros((hh, w, 3), np.uint8); img[:] = tuple(int(c * 0.8) for c in pal['card'])
    cv2.rectangle(img, (p0[0] - 4, 0), (p0[0] + 18, hh), pal['trim'], -1)  # cuff
    out = finish(img, mask, pal, seed, far)
    brad(out, p0, 5)
    return out, {'pivot': list(p0), 'end': list(p1), 'len': LEN, 'unit': s, 'mirror': True}


EXPRS = ['neutral', 'smile', 'strain', 'fear', 'surprise', 'pain', 'impatient', 'listen', 'closed']
SHAPES = ['relaxed', 'open', 'fist', 'grip', 'point']


def main():
    os.makedirs(OUT, exist_ok=True)
    reg = {'about': __doc__.strip().split('\n')[0], 'ledger': 'DRAWN', 'ref_height': REF_H, 'parts': {}}
    seed = 1
    for look, pal in PALETTES.items():
        def put(pid, img_meta):
            nonlocal seed
            img, meta = img_meta
            fn = '%s.png' % pid
            cv2.imwrite(os.path.join(OUT, fn), img)
            meta.update({'file': 'cast/dummy/' + fn, 'size': [img.shape[1], img.shape[0]]})
            reg['parts'][pid] = meta
            seed += 1
        for nm in ('thigh', 'shin', 'uarm', 'farm', 'torso_side', 'torso_front'):
            for far in (False, True):
                if nm.startswith('torso') and far:
                    continue
                pid = '%s.%s%s' % (look, nm, '.far' if far else '')
                put(pid, bone_piece(nm, pal, far, seed))
                if nm == 'torso_side':
                    reg['parts'][pid]['mirror'] = True
        for far in (False, True):
            put('%s.foot%s' % (look, '.far' if far else ''), foot_piece(pal, far, seed))
            for sh in SHAPES:
                put('%s.hand.%s%s' % (look, sh, '.far' if far else ''), hand_piece(pal, sh, far, seed))
        for view in ('side', 'front'):
            for e in EXPRS:
                put('%s.head.%s.%s' % (look, view, e), head_piece(pal, view, e, seed))
    json.dump(reg, open(os.path.join(OUT, 'parts.json'), 'w'), indent=1)
    # a contact sheet of one palette, for review
    ims = [cv2.imread(os.path.join(HERE, reg['parts'][k]['file']), cv2.IMREAD_UNCHANGED) for k in reg['parts'] if k.startswith('bola.')]
    Wd = 1800; x = y = rowh = 0; canvas = np.full((1400, Wd, 3), 245, np.uint8)
    for im in ims:
        h, w = im.shape[:2]
        if x + w > Wd:
            x, y, rowh = 0, y + rowh + 8, 0
        if y + h > canvas.shape[0]:
            break
        a = im[..., 3:4] / 255.0
        canvas[y:y + h, x:x + w] = (canvas[y:y + h, x:x + w] * (1 - a) + im[..., :3] * a).astype(np.uint8)
        x += w + 8; rowh = max(rowh, h)
    cv2.imwrite(os.path.join(OUT, '_sheet_bola.jpg'), canvas[:y + rowh + 8])
    print(len(reg['parts']), 'pieces')


if __name__ == '__main__':
    main()
