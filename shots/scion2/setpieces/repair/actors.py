"""Per-drawing measurements the stage needs to keep an actor continuous across swaps (measured, cached):
  glasses   CLIP on the head crop (head..chin markers, padded): sim('wearing dark sunglasses') minus
            sim('bare eyes, no glasses'); > 0 = glasses on. Cross-checked against the cast note ('glasses off').
  halo_px   width of a light sticker border around the silhouette: the outer rings (by distance from the
            exterior) that are near-white (L > 190 and chroma < 22) in >= 70% of their pixels
  lead      how far the silhouette reaches ahead of the torso (max of neck/groin x) in the facing
            direction, as a fraction of painted height (an outstretched arm reads as a floating limb
            when the body is still hidden behind a jamb)
  hip_ratio pelvis height above the lowest painted row / painted height (low = crouched)"""
import json, os, sys
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache', 'actor_meas.json')
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'evolve', 'puzzle')))
_C = None


def _cache():
    global _C
    if _C is None:
        _C = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    return _C


def save():
    json.dump(_cache(), open(CACHE, 'w'), indent=1)


def light_mask(img):
    lab = cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0] * 100 / 255
    ch = np.hypot(lab[..., 1] - 128, lab[..., 2] - 128)
    return (L > 75) & (ch < 22)


def halo_px(img):
    """consecutive 1-px rings from the 2nd one inwards in which >= 15% of pixels are near-white (ring 0 is
    the anti-aliased edge and is always light-ish), capped at 6"""
    from border import exterior_dist
    d, a = exterior_dist(img[..., 3])
    light = light_mask(img)
    w = 0
    fr = []
    for t in range(0, 10):
        m = a & (d > t) & (d <= t + 1)
        if m.sum() < 30:
            break
        f = float(light[m].mean())
        fr.append(round(f, 2))
    for t in range(1, len(fr)):
        if fr[t] >= 0.15:
            w = t
        else:
            break
    return min(w, 6), fr


def strip_halo(img, w):
    """remove near-white pixels within w+1 px of the exterior (the sticker halo), nothing else"""
    from border import exterior_dist
    d, a = exterior_dist(img[..., 3])
    out = img.copy()
    kill = (d <= w + 1.5) & light_mask(img)
    out[..., 3] = np.where(kill, 0, out[..., 3])
    return out


def measure(d):
    c = _cache()
    if d.id in c:
        return c[d.id]
    import hygiene
    img = d.image()
    a = img[..., 3] > 40
    ys, xs = np.nonzero(a)
    top, low = ys.min(), ys.max()
    hgt = low - top
    m = d.m
    out = {'id': d.id}
    if 'head' in m and 'chin' in m:
        hx, hy = m['head']
        cy = m['chin'][1]
        r = max(20, abs(cy - hy) * 1.1)
        x0, x1 = int(max(0, hx - r)), int(min(img.shape[1], hx + r))
        y0, y1 = int(max(0, min(hy, cy) - r * 0.9)), int(min(img.shape[0], max(hy, cy) + r * 0.3))
        crop = img[y0:y1, x0:x1]
        e = hygiene._img(crop)
        t = hygiene._txt(['a painted portrait of a man wearing dark sunglasses over his eyes',
                          'a painted portrait of a man with bare visible eyes, no glasses'])
        s = t @ e
        out['glasses'] = {'score': round(float(s[0] - s[1]), 4), 'sims': [round(float(x), 4) for x in s],
                          'crop': [x0, y0, x1, y1]}
    tx = max(m[k][0] for k in ('neck', 'groin') if k in m)
    out['lead'] = round(float((xs.max() - tx) / hgt), 3)
    out['hip_ratio'] = round(float((low - m['groin'][1]) / hgt), 3)
    c[d.id] = out
    return out


def halo(d):
    w, fr = halo_px(d.image())
    return {'halo_px': w, 'ring_light_frac': fr}


def glasses_on(d):
    g = measure(d).get('glasses')
    return None if g is None else g['score'] > 0
