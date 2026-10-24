"""colour signature and texture periodicity of a part (measured)."""
import numpy as np, cv2


def sig(im, rows=None):
    """Lab mean / chroma of painted pixels (alpha > 200); rows=(f0, f1) restricts to a band of the alpha bbox"""
    a = im[..., 3] > 200
    if rows:
        ys = np.nonzero(a.any(1))[0]
        y0, y1 = ys.min(), ys.max()
        band = np.zeros_like(a)
        band[int(y0 + rows[0] * (y1 - y0)):int(y0 + rows[1] * (y1 - y0)) + 1] = True
        a = a & band
    lab = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32)[a]
    L = lab[:, 0] * 100 / 255
    A, B = lab[:, 1] - 128, lab[:, 2] - 128
    C = np.hypot(A, B)
    return {'L': round(float(L.mean()), 1), 'a': round(float(A.mean()), 1), 'b': round(float(B.mean()), 1),
            'C_mean': round(float(C.mean()), 1), 'ab_std': round(float(np.hypot(A.std(), B.std())), 1)}


def dist(s1, s2):
    """palette distance: hue/chroma difference of the means plus half the lightness difference, plus the
    difference in colour spread (a multi-hue neon floor under a one-hue wall)"""
    return round(float(np.hypot(s1['a'] - s2['a'], s1['b'] - s2['b']) + 0.5 * abs(s1['L'] - s2['L'])
                       + max(0.0, s1['ab_std'] - s2['ab_std'] - 6)), 1)


def periodicity(img_bgr, axis=1, lo=0.06, hi=0.5):
    """largest local peak of the normalised autocorrelation of the high-passed grey image along an axis,
    over shifts lo..hi of the length: a tiled or machine-repeated texture peaks high (measured)"""
    g = cv2.cvtColor(img_bgr[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = g - cv2.GaussianBlur(g, (0, 0), 6)
    if axis == 0:
        g = g.T
    n = g.shape[1]
    v = float((g * g).mean()) + 1e-6
    sh = list(range(max(2, int(lo * n)), max(3, int(hi * n))))
    c = np.array([float((g[:, :-s] * g[:, s:]).mean()) / v for s in sh])
    peaks = [(c[i], sh[i]) for i in range(1, len(c) - 1) if c[i] >= c[i - 1] and c[i] >= c[i + 1]]
    if not peaks:
        return 0.0, None
    p = max(peaks)
    return round(float(p[0]), 3), int(p[1])
