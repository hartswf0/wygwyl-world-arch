"""painted card border (cardboard rope / tan trim left by the cutter) on a flat, measured from the alpha
distance to the exterior: the ring colour profile by distance; the border ends at the largest colour
jump between consecutive 2-px rings within 3..18 px (if the jump is big enough). Measured, per part."""
import cv2, numpy as np


def exterior_dist(alpha):
    a = alpha > 40
    h, w = a.shape
    pad = np.pad(~a, 1, constant_values=True).astype(np.uint8)
    n, lab = cv2.connectedComponents(pad, connectivity=4)
    ext = lab == lab[0, 0]
    ext = ext[1:-1, 1:-1]
    return cv2.distanceTransform((~ext).astype(np.uint8), cv2.DIST_L2, 3), a


def border_width(im, max_t=18):
    d, a = exterior_dist(im[..., 3])
    lab = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32)
    prof = []
    for t in range(0, max_t + 12, 2):
        m = a & (d > t) & (d <= t + 2)
        if m.sum() < 50:
            break
        prof.append(lab[m].mean(0))
    prof = np.array(prof)
    if len(prof) < 6:
        return 0, {'profile_L': [], 'jump': 0}
    inner = prof[-3:].mean(0)
    dist_in = np.linalg.norm(prof - inner, axis=1)
    jumps = np.linalg.norm(np.diff(prof, axis=0), axis=1)
    best_i, best = None, 0.
    for i in range(1, min(len(jumps), max_t // 2)):
        if jumps[i] > best:
            best, best_i = jumps[i], i
    ev = {'ring_dist_to_interior': [round(float(x), 1) for x in dist_in], 'jumps': [round(float(x), 1) for x in jumps]}
    # a border: the outer rings differ from the interior and one ring step carries a sharp change
    if best_i is not None and best >= 6 and dist_in[:best_i + 1].mean() >= 10:
        return int(2 * (best_i + 1) + 1), dict(ev, jump=round(float(best), 1))
    return 2, dict(ev, jump=round(float(best), 1))


def trim(im, t):
    d, a = exterior_dist(im[..., 3])
    out = im.copy()
    out[..., 3] = np.where(d <= t, 0, out[..., 3])
    return out
