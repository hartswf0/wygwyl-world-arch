"""Piping continuity (round 08, critic r07 s07 / s14: the red stripe on the right of one piece and on the left or
centre of the other).

The red piping's lateral position is measured on each piece's joint end in the straight (rest) render: a band 1-4 cm
from the joint along the limb on each side, the stripe's mean offset from the piece's own centreline across the limb,
as a share of its width (-0.5 .. 0.5). Pieces with no piping in the band put no constraint. A pair is compatible when
the two offsets match within 0.25; when they do not, the child mirrored (its view allowing: not heads, hands or feet)
is tried.
"""
import numpy as np, cv2
from evolve.joints import connect as CN

TOL = .25


def red_mask(bgr):
    hsv = cv2.cvtColor(np.clip(bgr, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    return ((h < 8) | (h > 170)) & (s > 120) & (v > 70)


def offset(L, c, u, d1, d2):
    a = L[..., 3] > 128
    H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W]
    along = (xx - c[0]) * u[0] + (yy - c[1]) * u[1]
    across = (xx - c[0]) * -u[1] + (yy - c[1]) * u[0]
    band = a & (along >= d1) & (along <= d2)
    if band.sum() < 20:
        return None
    t = across[band]
    lo, hi = np.percentile(t, 2), np.percentile(t, 98)
    w = max(hi - lo, 1.)
    red = band & red_mask(L[..., :3])
    if red.sum() < 6:
        return None
    return float((across[red].mean() - (lo + hi) / 2) / w)


def measure(a, b, joint, genes):
    r = CN.connect(a, b, joint, 0, genes)
    if r is None:
        return None, None
    c, u = r['target'], np.asarray(r['axis_c'], float)
    oc = offset(r['C'], c, u, 1 * CN.RS, 4 * CN.RS)
    op = offset(r['P'], c, -u, 1 * CN.RS, 4 * CN.RS)
    # the parent's offset is measured looking back up the limb: flip its sign into the child's frame
    return (None if op is None else -op), oc


def match(a, b, joint, genes):
    """(ok, genes to use, offsets) -- tries the child mirrored when the plain pair does not match"""
    op, oc = measure(a, b, joint, genes)
    if op is None or oc is None:
        return True, genes, (op, oc)
    if abs(op - oc) <= TOL:
        return True, genes, (op, oc)
    if b['part'] in ('head', 'hand', 'foot'):
        return False, genes, (op, oc)
    g2 = dict(genes, mirror=not genes.get('mirror', False))
    op2, oc2 = measure(a, b, joint, g2)
    if op2 is not None and oc2 is not None and abs(op2 - oc2) <= TOL:
        return True, g2, (op2, oc2)
    return False, genes, (op, oc)
