"""Card preparation: one library card -> pixels + the measurements the assembler and fitness need.

prep(card) -> Card with
  rgba     BGRA float32, premultiplied=False, the card's own painted border stripped (alpha eroded by `border` px)
  A, B     joints in card px (see anchors(); torso and pelvis anchors are read from the card's alpha)
  ppc      px per cm used for scale (torso: re-derived from its own neck->hem height, see below)
  len_cm   |AB| / ppc
  w0, w1   cloth width (cm) across the A->B axis near A (t=.12) and near B (t=.88): the joint-integrity widths
  lab      median CIE-Lab of the card's pixels (cloth / skin colour for coherence)
  border   px of the painted paper border that was stripped (a crisp edge is drawn back at render time)
  ok/why   False when the card is unusable as its slot (anchors off the card, junk aspect, blank face, ...)

Anchors. The library's A/B are kept for limbs, hands, feet and heads when they pass a check (both on or next to the
card's paint, and spanning >= 45% of the card's long extent); otherwise they are re-read from the alpha's principal axis
(proximal end = the end farther from the library's B). Torso cards carry A/B that are often the two shoulder brads, so
for every torso the waist (hem centre) and neck (collar top centre) come from the alpha, plus two shoulder points.
Pelvis cards: waist = top centre, the two hip points = the two lowest brads (or 70% height, +-30% width).
"""
import functools, math
import numpy as np, cv2

TORSO_CM = 50.0      # neck (collar top) to jacket hem, cm, in the cards' own cm (arm and leg cards: 30 / 27 / 46 / 43 cm)


def read_bgra(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(path)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGRA)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


def lab_of(bgr_u8):
    return cv2.cvtColor(bgr_u8.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32) * [100 / 255., 1, 1] - [0, 128, 128]


def border_width(im, a):
    """px of painted paper border: the ring depth past which the ring colour matches the interior"""
    hard = (a > 128).astype(np.uint8)
    d = cv2.distanceTransform(np.pad(hard, 1), cv2.DIST_L2, 3)[1:-1, 1:-1]
    dmax = d.max()
    if dmax < 6:
        return 0
    deep = d >= min(dmax * .6, 22)
    ref = np.median(lab_of(im[..., :3][deep]), 0)
    bw = 0
    for k in range(1, int(min(16, dmax * .5))):
        ring = (d > k - 1) & (d <= k)
        if ring.sum() < 10:
            break
        c = np.median(lab_of(im[..., :3][ring]), 0)
        if np.linalg.norm(c - ref) > 14:
            bw = k
    return bw


def principal(a):
    ys, xs = np.nonzero(a > 128)
    P = np.stack([xs, ys], 1).astype(np.float64)
    c = P.mean(0)
    u = np.linalg.svd(P - c, full_matrices=False)[2][0]
    t = (P - c) @ u
    return c, u, t.min(), t.max()


def width_at(a, A, B, t, ppc):
    """alpha extent across the A->B axis at fraction t (cm)"""
    A, B = np.asarray(A, float), np.asarray(B, float)
    u = (B - A) / (np.linalg.norm(B - A) + 1e-9)
    n = np.array([-u[1], u[0]])
    p = A + t * (B - A)
    s = np.arange(-a.shape[0] - a.shape[1], a.shape[0] + a.shape[1], 1.0)
    q = p[None] + s[:, None] * n[None]
    ok = (q[:, 0] >= 0) & (q[:, 1] >= 0) & (q[:, 0] < a.shape[1] - 1) & (q[:, 1] < a.shape[0] - 1)
    q, s = q[ok], s[ok]
    v = a[q[:, 1].astype(int), q[:, 0].astype(int)] > 128
    if not v.any():
        return 0.0
    return float(s[v].max() - s[v].min()) / ppc


class Card(dict):
    __getattr__ = dict.get


def _torso_anchors(a):
    ys, xs = np.nonzero(a > 128)
    y0, y1 = ys.min(), ys.max()
    H = y1 - y0
    def cx_at(y):
        r = np.nonzero(a[int(y)] > 128)[0]
        return (r.min() + r.max()) / 2 if len(r) else xs.mean()
    # collar: the top band's centre; hem: the bottom band's centre
    neck = np.array([cx_at(y0 + .03 * H), y0 + .02 * H])
    waist = np.array([cx_at(y1 - .03 * H), y1 - .02 * H])
    yS = y0 + .16 * H
    r = np.nonzero(a[int(yS)] > 128)[0]
    shL, shR = np.array([r.min() + .07 * (r.max() - r.min()), yS]), np.array([r.max() - .07 * (r.max() - r.min()), yS])
    return waist, neck, shL, shR


def _pelvis_anchors(a, brads):
    ys, xs = np.nonzero(a > 128)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    waist = np.array([(x0 + x1) / 2, y0 + .06 * (y1 - y0)])
    bb = sorted([b for b in brads if b[1] > y0 + .45 * (y1 - y0)], key=lambda b: -b[1])
    if len(bb) >= 2 and abs(bb[0][0] - bb[1][0]) > .3 * (x1 - x0):
        h1, h2 = sorted([np.array(bb[0][:2], float), np.array(bb[1][:2], float)], key=lambda p: p[0])
    else:
        yh = y0 + .70 * (y1 - y0)
        h1, h2 = np.array([(x0 + x1) / 2 - .3 * (x1 - x0), yh]), np.array([(x0 + x1) / 2 + .3 * (x1 - x0), yh])
    crotch = np.array([(x0 + x1) / 2, max(h1[1], h2[1])])
    return waist, crotch, h1, h2


def _limb_check(a, A, B):
    c, u, t0, t1 = principal(a)
    ext = t1 - t0
    ok = np.linalg.norm(np.subtract(B, A)) >= .45 * ext
    H, W = a.shape
    dil = cv2.dilate((a > 128).astype(np.uint8), np.ones((15, 15), np.uint8))
    for p in (A, B):
        x, y = int(round(p[0])), int(round(p[1]))
        if not (0 <= x < W and 0 <= y < H) or not dil[y, x]:
            if not (0 <= x < W and 0 <= y < H):
                ok = ok and False
            else:
                ok = ok and False
    return ok, (c, u, t0, t1)


def _tab_end(im, a, c, u, t0, t1):
    """0 or 1: which principal-axis end carries a wrist tab / eyelet (tan or brass pixels); None if neither clearly"""
    ys, xs = np.nonzero(a > 128)
    t = (np.stack([xs, ys], 1) - c) @ u
    b, g, r = (im[ys, xs, k] for k in range(3))
    tab = ((r > 150) & (g > 105) & (b < 125)) | ((r > 140) & (r - b > 45) & (g > 95) & (r < 225))
    ext = t1 - t0
    s0 = tab[t < t0 + .25 * ext].mean() if (t < t0 + .25 * ext).any() else 0
    s1 = tab[t > t1 - .25 * ext].mean() if (t > t1 - .25 * ext).any() else 0
    if max(s0, s1) < .04 or abs(s0 - s1) < .03:
        return None
    return 0 if s0 > s1 else 1


def _hand_ok(im, a, A, B, c, u, t0, t1):
    """a hand's A must sit in the proximal (wrist) quarter and B in the far quarter"""
    ext = t1 - t0
    ta, tb = (np.subtract(A, c) @ u - t0) / ext, (np.subtract(B, c) @ u - t0) / ext
    if not ((ta < .25 and tb > .75) or (ta > .75 and tb < .25)):
        return False
    te = _tab_end(im, a, c, u, t0, t1)
    return te is None or (te == 0) == (ta < .5)


@functools.lru_cache(maxsize=4000)
def _prep(cid, img, slot, A, B, ppc, erase, trim, pts, brads, kind='kit', ppc_fixed=False):
    im = read_bgra(img).astype(np.float32)
    a = im[..., 3].copy()
    for x0, y0, x1, y1 in erase:
        a[int(y0):int(y1), int(x0):int(x1)] = 0
    if trim:
        a = cv2.erode(a, np.ones((2 * trim + 1, 2 * trim + 1), np.uint8))
    if 'hollow' not in cid:
        # holes the cutter keyed out of white paint (sneakers, cuffs): enclosed transparent areas are filled back,
        # otherwise each gets its own paper edge. Cards drawn with a hole on purpose ('hollow' chest) keep theirs.
        hard = (a > 128).astype(np.uint8)
        ff = np.pad(1 - hard, 1, constant_values=1)
        mask = np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8)
        cv2.floodFill(ff, mask, (0, 0), 2)
        holes = (ff[1:-1, 1:-1] == 1)
        if holes.any():
            a = np.where(holes, 255., a).astype(np.float32)
    u8 = np.dstack([im[..., :3], a]).astype(np.uint8)
    out = Card(id=cid, slot=slot, ok=True, why=[])
    if (a > 128).sum() < 200:
        return Card(id=cid, ok=False, why=['too few pixels'])
    bw = border_width(u8, a)
    if slot in ('torso', 'pelvis'):
        bw = min(bw, 8)
    out['border'] = bw
    A, B = np.array(A, float), np.array(B, float)
    extra = {}
    if slot == 'torso':
        waist, neck, shL, shR = _torso_anchors(a)
        A, B = waist, neck
        ppc = np.linalg.norm(B - A) / TORSO_CM
        extra = {'shL': shL, 'shR': shR}
    elif slot == 'pelvis':
        waist, crotch, h1, h2 = _pelvis_anchors(a, brads)
        A, B = waist, crotch
        extra = {'hip1': h1, 'hip2': h2}
        hw = np.linalg.norm(h2 - h1)
        ppc = hw / 26.0        # painted hip brad to hip brad ~26 cm
    else:
        ok, (c, u, t0, t1) = _limb_check(a, A, B)
        if slot == 'hand':
            ok = ok and _hand_ok(im, a, A, B, c, u, t0, t1)
        if not ok:
            e0, e1 = c + t0 * u, c + t1 * u
            # proximal = the end farther from the library's B (B is usually right even when A is not);
            # for a hand, the end carrying the wrist tab / eyelet (tan leather, brass) when one end has it
            if slot == 'hand' and _tab_end(im, a, c, u, t0, t1) is not None:
                if _tab_end(im, a, c, u, t0, t1) == 1:
                    e0, e1 = e1, e0
            elif np.linalg.norm(e0 - B) < np.linalg.norm(e1 - B):
                e0, e1 = e1, e0
            k = .08 if slot in ('hand', 'head', 'foot') else .1
            L0 = np.linalg.norm(B - A)
            A2, B2 = e0 + k * (e1 - e0), e1 - .03 * (e1 - e0)
            if L0 > 1:
                ppc = ppc * np.linalg.norm(B2 - A2) / L0
            A, B = A2, B2
            out['why'].append('anchors re-read from the alpha axis')
    L = np.linalg.norm(B - A)
    # kit hands and boots: library px/cm was normalised on anchors that are often wrong; size them by the drawing
    # (hand: wrist eyelet to fingertip 19 cm; boot: 26 cm heel to toe in profile, 11 cm across from the front/back).
    # Harvest cards keep their painting's px/cm (they are drawn at the size the painter drew them).
    if kind == 'kit' and not ppc_fixed and slot in ('hand', 'foot'):
        if slot == 'hand' and L > 8:
            # by the hand's width across the axis at 45% (palm or fist ~10 cm): a fist's wrist-to-knuckle axis is
            # short, so sizing by A-B (19 cm) blew fists up to twice a hand
            wpx = width_at(a, A, B, .45, 1.0)
            ppc = wpx / 10.0 if wpx > 5 else L / 19.0
        elif slot == 'foot':
            ys_, xs_ = np.nonzero(a > 128)
            bw_, bh_ = xs_.max() - xs_.min(), ys_.max() - ys_.min()
            ppc = bw_ / 26.0 if bw_ > .8 * bh_ else bw_ / 11.0     # side-on boots are wider than tall, front ones narrow
    if L < 8:
        return Card(id=cid, ok=False, why=['anchors collapse'])
    out.update(A=A, B=B, ppc=float(ppc), len_cm=float(L / ppc), **extra)
    out['w0'] = width_at(a, A, B, .12, ppc)
    out['w1'] = width_at(a, A, B, .88, ppc)
    out['wmid'] = width_at(a, A, B, .5, ppc)
    hard = a > 200
    er = cv2.erode(hard.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    px = im[..., :3][er if er.sum() > 50 else hard].astype(np.uint8)
    lab = lab_of(px)
    out['lab'] = np.median(lab, 0)
    # skin share: warm mid-luminance pixels
    out['skin'] = float(((lab[:, 0] > 25) & (lab[:, 0] < 75) & (lab[:, 1] > 8) & (lab[:, 2] > 12)).mean())
    out['tan'] = float(((lab[:, 0] > 45) & (lab[:, 1] > 5) & (lab[:, 2] > 20)).mean())
    if slot == 'head' and kind == 'harvest':
        # a harvest head is a window cut from a painting: it carries collar, shoulders and sometimes a jacket brad.
        # Keep the head only: above a line just below the neck point, within a radius of the head's centre.
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
        u = (B - A) / (np.linalg.norm(B - A) + 1e-9)
        t_ = (xx - A[0]) * u[0] + (yy - A[1]) * u[1]
        Lh = np.linalg.norm(B - A)
        cen = A + .5 * (B - A)
        rr = np.hypot(xx - cen[0], yy - cen[1])
        keep = np.clip((t_ + .12 * Lh) / (.06 * Lh), 0, 1) * np.clip((1.0 * Lh - rr) / (.06 * Lh), 0, 1)
        a = a * keep
        out['why'] = out['why'] + ['harvest head clipped to the head (no collar / shoulders)']
    ys_, xs_ = np.nonzero(a > 128)
    out['bbox'] = (int(xs_.min()), int(ys_.min()), int(xs_.max()), int(ys_.max()))
    # painted lean of the axis from card-vertical (heads: a head drawn bent over; feet: not used)
    out['lean'] = float(abs(math.degrees(math.atan2(B[0] - A[0], -(B[1] - A[1])))))
    if slot == 'foot':
        # how far the paint rises above the ankle, in units of ankle->toe: a boot with a trouser stub on it rises far
        out['rise'] = float((A[1] - ys_.min()) / (np.linalg.norm(B - A) + 1e-6))
    out['bgra'] = np.dstack([im[..., :3], a]).astype(np.float32)
    out['size'] = (a.shape[1], a.shape[0])
    if slot == 'head':
        # a painted face has dark features (eyes, brows, beard, glasses) inside the lower 60% of the head
        ys, xs = np.nonzero(a > 128)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        reg = (slice(int(y0 + .3 * (y1 - y0)), int(y0 + .75 * (y1 - y0))), slice(int(x0 + .2 * (x1 - x0)), int(x1 - .2 * (x1 - x0))))
        g = cv2.cvtColor(im[..., :3].astype(np.uint8), cv2.COLOR_BGR2GRAY)[reg]
        m = a[reg] > 128
        out['face_std'] = float(g[m].std()) if m.sum() > 50 else 0.
        # eyes band (35-55% of the head's height, middle half): a painted face has dark eyes / brows / glasses there,
        # a blank kit head is plain skin
        reg2 = (slice(int(y0 + .33 * (y1 - y0)), int(y0 + .55 * (y1 - y0))), slice(int(x0 + .25 * (x1 - x0)), int(x1 - .25 * (x1 - x0))))
        g2 = cv2.cvtColor(im[..., :3].astype(np.uint8), cv2.COLOR_BGR2GRAY)[reg2]
        m2 = a[reg2] > 128
        out['eyes_dark'] = float((g2[m2] < 55).mean()) if m2.sum() > 30 else 0.
    return out


def prep(c):
    return _prep(c['id'], c['img'], c['slot'], tuple(c['A']), tuple(c['B']), c['ppc'], tuple(tuple(e) for e in c.get('erase') or ()),
                 int(c.get('trim') or 0), c.get('pts'), tuple(tuple(b[:2]) for b in c.get('brads') or ()), c.get('kind', 'kit'),
                 bool(c.get('ppc_fixed')))
