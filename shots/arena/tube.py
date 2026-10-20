#!/usr/bin/env python3
"""
PROCEDURAL TUBES — the half of the body that should never be generated.

    python3 shots/arena/tube.py            -> shots/arena/tube_demo.jpg

A sleeve is a sleeve. Upper arm, forearm, thigh and shin are 50% of the figure
by card area and carry no likeness at all, and every one of them is a PNG with a
fixed length hung on a bone whose length changes every frame. That mismatch IS
the brad gap: the current cards run 34-84% out, the median gap is 11.1cm against
a 2.0 tolerance, and no generator can fix it because the problem is that the
length was ever fixed.

Drawn in code the length is a parameter. Ask for a 44cm thigh and get a 44cm
thigh; ask for the same thigh foreshortened to 31cm two frames later and get
that. The gap is zero by construction, there is nothing to accept or reject, and
the 8 cards per character these replace never need generating.

What is drawn: a tapered capsule in the garment's own colour, the corrugated
fluting running across the piece the way a cut card shows it, a darker cardboard
core at the cut edge, a white paper lip, and a brass brad at each joint.
"""
import os, math
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))

GARMENT = {                       # (BGR) of the cloth, and of its piping
 'man':  ((34, 32, 30), (120, 150, 205)),      # black quilted vest, salmon piping
 'poet': ((104, 86, 42), (120, 185, 215)),     # teal dress, gold filigree
}

def tube(length_px, w_top, w_bot, cloth, piping=None, flute=7, seed=0):
    """one limb card: joint A at the top centre, joint B straight below"""
    pad = 10
    W = int(max(w_top, w_bot)) + pad * 2
    H = int(length_px) + pad * 2
    rgba = np.zeros((H, W, 4), np.uint8)
    cx = W // 2
    # the silhouette: a tapered capsule, rounded at both joints
    poly = []
    N = 48
    for i in range(N + 1):
        t = i / N
        w = (w_top * (1 - t) + w_bot * t) / 2.0
        poly.append((cx - w, pad + t * length_px))
    for i in range(N, -1, -1):
        t = i / N
        w = (w_top * (1 - t) + w_bot * t) / 2.0
        poly.append((cx + w, pad + t * length_px))
    P = np.array([poly], np.int32)
    card = np.zeros((H, W), np.uint8)
    cv2.fillPoly(card, P, 255)
    cv2.circle(card, (cx, pad), int(w_top / 2), 255, -1)
    cv2.circle(card, (cx, pad + int(length_px)), int(w_bot / 2), 255, -1)
    card = cv2.GaussianBlur(card, (0, 0), .6)
    a = (card > 110)

    body = np.zeros((H, W, 3), np.uint8); body[:] = cloth
    # fluting: the corrugation of a cut card, running across the piece
    rs = np.random.RandomState(seed)
    yy = np.arange(H)[:, None]
    rib = (np.sin(yy / float(flute) * math.pi * 2) * .5 + .5)
    rib = (rib * 16 - 8) + rs.normal(0, 1.4, (H, 1))
    body = np.clip(body.astype(np.float32) + rib[:, :, None], 0, 255).astype(np.uint8)
    # the cloth is lit a little from the left, like the rest of the cast
    ramp = np.linspace(-14, 10, W)[None, :, None]
    body = np.clip(body.astype(np.float32) + ramp, 0, 255).astype(np.uint8)
    if piping is not None:            # a seam down the middle, as the trousers have
        cv2.line(body, (cx, pad + 6), (cx, pad + int(length_px) - 6), piping, 2, cv2.LINE_AA)

    # the cut edge: cardboard core, then a white paper lip outside it
    er = cv2.erode(a.astype(np.uint8), np.ones((3, 3)), iterations=2).astype(bool)
    core = a & ~er
    body[core] = (0.55 * body[core] + 0.45 * np.array([60, 82, 112])).astype(np.uint8)
    lip = cv2.dilate(a.astype(np.uint8), np.ones((3, 3)), iterations=1).astype(bool) & ~a

    rgba[..., :3] = body
    rgba[..., 3] = np.where(a, 255, 0)
    rgba[lip] = (238, 240, 243, 255)
    # brass brads, at the two joints, which is where the card is pinned
    for (x, y) in ((cx, pad), (cx, pad + int(length_px))):
        cv2.circle(rgba, (x, y), 7, (40, 62, 92, 255), -1, cv2.LINE_AA)
        cv2.circle(rgba, (x, y), 6, (64, 158, 204, 255), -1, cv2.LINE_AA)
        cv2.circle(rgba, (x - 2, y - 2), 2, (190, 238, 255, 255), -1, cv2.LINE_AA)
    return rgba

PIECES = {'uarm': (28.0, 11.0, 9.5), 'farm': (26.0, 9.5, 8.0),
          'thigh': (44.0, 16.0, 12.5), 'shin': (43.0, 12.5, 9.0)}

def make(piece, char='man', pxcm=12.0, length_cm=None):
    L, wt, wb = PIECES[piece]
    L = length_cm if length_cm else L
    cloth, pip = GARMENT[char]
    return tube(L * pxcm, wt * pxcm, wb * pxcm, cloth,
                pip if piece in ('thigh', 'shin') else None, seed=hash(piece) % 97)

if __name__ == '__main__':
    tiles = []
    for char in ('man', 'poet'):
        for p in PIECES:
            tiles.append((f'{char}.{p}', make(p, char)))
    # and the same thigh at three foreshortenings, which is the whole argument
    for L in (44.0, 36.0, 28.0):
        tiles.append((f'man.thigh @ {L:.0f}cm', make('thigh', 'man', length_cm=L)))
    TH = max(t.shape[0] for _, t in tiles) + 34
    TW = max(t.shape[1] for _, t in tiles) + 16
    canv = np.full((TH + 40, TW * len(tiles), 3), 246, np.uint8)
    cv2.putText(canv, 'procedural tubes - drawn at the bone length, not a fixed PNG',
                (8, 26), cv2.FONT_HERSHEY_DUPLEX, .62, (20, 20, 20), 1, cv2.LINE_AA)
    for i, (nm, t) in enumerate(tiles):
        x = i * TW + 8; y = 40
        al = t[..., 3:4].astype(np.float32) / 255.0
        rgb = (t[..., :3].astype(np.float32) * al + 246 * (1 - al)).astype(np.uint8)
        canv[y:y + t.shape[0], x:x + t.shape[1]] = rgb
        cv2.putText(canv, nm, (x, y + t.shape[0] + 18), cv2.FONT_HERSHEY_SIMPLEX, .38, (40, 40, 40), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(HERE, 'tube_demo.jpg'), canv, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f'{len(tiles)} tubes -> shots/arena/tube_demo.jpg')
