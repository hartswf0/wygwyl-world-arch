"""Find brass brads / eyelets (the kit's real pivots) by colour + roundness."""
import numpy as np, cv2


def brass_blobs(rgba, min_r_frac=0.012):
    rgb = rgba[..., :3]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    m = ((h >= 17) & (h <= 32) & (s >= 90) & (v >= 105) & (rgba[..., 3] > 128)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    H, W = m.shape
    rmin = max(3, min_r_frac * max(H, W))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n):
        x, y, w, hh, a = st[i]
        r = (w + hh) / 4
        if r < rmin or r > 0.12 * max(H, W):
            continue
        aspect = min(w, hh) / max(w, hh)
        if aspect < 0.7:
            continue
        # filled disc (brad) has fill ~0.78; ring (eyelet) less; reject sprawling shapes
        fill = a / (w * hh)
        if fill < 0.35:
            continue
        out.append(dict(c=[float(x + w / 2), float(y + hh / 2)], r=float(r), fill=float(fill), aspect=float(aspect)))
    return out
