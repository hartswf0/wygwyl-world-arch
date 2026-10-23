"""H1 warp: part masks over a painting, per-layer triangle meshes, skinned (linear blend)
deformation with rigid parts and soft joints, hidden-torso fill from another painting."""
import math
import numpy as np, cv2
import h1core as H

LAYER_BONES = {
    'body': ['torso', 'head'],
    'armL': ['uarmL', 'farmL'], 'armR': ['uarmR', 'farmR'],
    'legL': ['thighL', 'shinL', 'footL'], 'legR': ['thighR', 'shinR', 'footR'],
}
PART_LAYER = {b: l for l, bs in LAYER_BONES.items() for b in bs}


def seg_dist(P, a, b):
    """distance from points P (N,2) to segment ab, and the segment parameter."""
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-6), 0, 1)
    q = a + t[:, None] * ab
    return np.linalg.norm(P - q, axis=1), t


def torso_poly(M, L, grow=0.14):
    # the pelvis runs down to the crotch so the legs can open without a gap there
    up = (M['neck'] - M['groin']) / (L + 1e-6)
    g = M['groin'] - up * .1 * L
    # the shoulder slope up to the collar is torso too
    hv = M['hipL'] - M['hipR']; hv = hv / (np.linalg.norm(hv) + 1e-6)
    # the jacket hem runs wider than the hip joints
    pts = np.array([M['shoulderL'] + up * .16 * L, M['neck'] + up * .06 * L, M['shoulderR'] + up * .16 * L,
                    M['hipR'] - hv * .1 * L, g, M['hipL'] + hv * .1 * L], float)
    c = pts.mean(0)
    return c + (pts - c) * (1 + grow)


def poly_dist(P, poly):
    cnt = poly.reshape(-1, 1, 2).astype(np.float32)
    return np.array([-cv2.pointPolygonTest(cnt, (float(x), float(y)), True) for x, y in P])


def bone_segments(M, L):
    """the drawing each bone owns: forearm runs on through the hand, shin to the toe."""
    seg = {}
    for b, (a, c) in H.BONES.items():
        A, C = M[a].copy(), M[c].copy()
        if b.startswith('farm'):
            d = C - A; n = np.linalg.norm(d) + 1e-6
            C = C + d / n * max(.45 * n, .16 * L)
        if b == 'head':
            A = M['neck']; C = (M['head'] + M['chin']) / 2
        seg[b] = (A, C)
    return seg


def segment_parts(rgba, M):
    """label every figure pixel with the part that owns it (index into part list)."""
    a = rgba[..., 3] > 20
    L = np.linalg.norm(M['neck'] - M['groin'])
    ys, xs = np.nonzero(a)
    P = np.stack([xs, ys], 1).astype(float)
    dt = cv2.distanceTransform(a.astype(np.uint8), cv2.DIST_L2, 5)
    poly = torso_poly(M, L)
    inpoly = cv2.pointPolygonTest  # noqa
    tmask = np.zeros(a.shape, np.uint8)
    cv2.fillPoly(tmask, [poly.astype(np.int32)], 1)
    tdist = cv2.distanceTransform(1 - tmask, cv2.DIST_L2, 5)
    seg = bone_segments(M, L)
    parts = list(H.BONES)
    costs = []
    radii = {}
    for b in parts:
        A, C = seg[b]
        if b == 'torso':
            costs.append(tdist[ys, xs] - .02 * L)
            radii[b] = 0
            continue
        # radius from the painting's own thickness along the bone, outside the torso
        tt = np.linspace(.25, .75, 9)
        pts = A[None] + tt[:, None] * (C - A)[None]
        r = []
        for x, y in pts:
            xi, yi = int(round(x)), int(round(y))
            if 0 <= yi < a.shape[0] and 0 <= xi < a.shape[1] and tmask[yi, xi] == 0 and dt[yi, xi] > 0:
                r.append(dt[yi, xi])
        dflt = {'h': .32, 'u': .15, 'f': .14, 't': .19, 's': .16}[b[0]] * L
        rr = np.median(r) * 1.25 if len(r) >= 3 else dflt
        lo, hi = {'h': (.22, .45), 'f': (.07, .2), 'u': (.07, .2), 't': (.1, .26), 's': (.08, .22)}[b[0]]
        rr = float(np.clip(rr, lo * L, hi * L))
        radii[b] = rr
        d, t = seg_dist(P, A, C)
        cst = d - rr
        if b == 'head':
            # the head owns what is above the neck point; the collar stays with the torso
            up = (M['neck'] - M['groin']) / (L + 1e-6)
            above = (P - M['neck']) @ up
            lateral = np.linalg.norm((P - M['neck']) - above[:, None] * up[None], axis=1)
            hc = (M['head'] + M['chin']) / 2 - M['neck']
            lat_c = abs(hc[0] * up[1] - hc[1] * up[0])  # the head may lean off the axis
            own = above > .02 * L
            for k in ('shoulderL', 'shoulderR'):   # the shoulder rivets never ride on the head
                own &= np.linalg.norm(P - M[k], axis=1) > .16 * L
            cst = np.where(own, cst, 1e6)
        # the shoulder cap and the hip belong to the torso: a limb owns only what lies
        # past its root joint (and, for a leg inside the torso outline, well past it)
        if b[:-1] in ('uarm', 'thigh'):
            ab = C - A
            traw = ((P - A) @ ab) / max(ab @ ab, 1e-6)
            inside = tmask[ys, xs] > 0
            lim = .05 if b.startswith('uarm') else .25
            cst = np.where(inside & (traw < lim), 1e6, cst)
        costs.append(cst)
    costs = np.stack(costs, 1)
    lab = np.argmin(costs, 1)
    labels = np.full(a.shape, -1, np.int16)
    labels[ys, xs] = lab
    # each part keeps only its component(s) touching its own bone; orphans go to nearest
    for i, b in enumerate(parts):
        m = (labels == i).astype(np.uint8)
        n, cc = cv2.connectedComponents(m)
        if n <= 2:
            continue
        A, C = seg[b]
        keep = set()
        for tt in np.linspace(0, 1, 15):
            x, y = (A + tt * (C - A)).round().astype(int)
            if 0 <= y < a.shape[0] and 0 <= x < a.shape[1] and cc[y, x] > 0:
                keep.add(cc[y, x])
        if not keep:
            sizes = np.bincount(cc.ravel()); sizes[0] = 0; keep = {int(np.argmax(sizes))}
        for j in range(1, n):
            if j not in keep:
                labels[cc == j] = -2
    orphan = labels == -2
    if orphan.any():
        good = labels >= 0
        _, idx = cv2.distanceTransformWithLabels((~good).astype(np.uint8), cv2.DIST_L2, 5,
                                                  labelType=cv2.DIST_LABEL_PIXEL)
        gy, gx = np.nonzero(good)
        lut = np.zeros(idx.max() + 1, np.int16)
        # map label index -> pixel label
        lab_of = labels[gy, gx]
        lut[idx[gy, gx]] = lab_of
        labels[orphan] = lut[idx[orphan]]
    return labels, parts, tmask, radii


def layer_masks(labels, parts):
    out = {}
    for l, bs in LAYER_BONES.items():
        m = np.zeros(labels.shape, bool)
        for b in bs:
            m |= labels == parts.index(b)
        out[l] = m
    return out


# ------------------------------------------------------------------ hidden torso fill
def fill_torso(rgba, M, labels, parts, tmask, donor):
    """Pixels inside the torso that the painting gave to an arm are the torso's hidden
    region. Fill them from another painting of him (donor rgba + markers), registered by
    the shoulders and hips. Returns rgba of the body layer with the hole filled and the
    mask of filled pixels."""
    body = np.isin(labels, [parts.index('torso'), parts.index('head')])
    arms = np.isin(labels, [parts.index(b) for b in ['uarmL', 'farmL', 'uarmR', 'farmR']])
    hole = arms & (tmask > 0)
    out = rgba.copy()
    out[..., 3] = np.where(body, rgba[..., 3], 0)
    if donor is None or hole.sum() == 0:
        return out, hole & False
    drgba, DM = donor
    src = np.array([DM[k] for k in ['shoulderL', 'shoulderR', 'hipL', 'hipR', 'neck', 'groin']], np.float32)
    dst = np.array([M[k] for k in ['shoulderL', 'shoulderR', 'hipL', 'hipR', 'neck', 'groin']], np.float32)
    A, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.LMEDS)  # no shear: rivets stay round
    # the shoulder joint itself stays with the arm's own drawing (no second rivet there)
    L = np.linalg.norm(M['neck'] - M['groin'])
    yy, xx = np.mgrid[0:hole.shape[0], 0:hole.shape[1]]
    for k in ['shoulderL', 'shoulderR']:
        hole &= (xx - M[k][0]) ** 2 + (yy - M[k][1]) ** 2 > (.14 * L) ** 2
    if A is None:
        return out, hole & False
    w = cv2.warpAffine(drgba, A, (rgba.shape[1], rgba.shape[0]), flags=cv2.INTER_LINEAR,
                       borderValue=(0, 0, 0, 0))
    ok = hole & (w[..., 3] > 128)
    # tone match: donor vs painting over the visible torso
    vis = body & (tmask > 0) & (w[..., 3] > 128) & (rgba[..., 3] > 128)
    if vis.sum() > 50:
        for c in range(3):
            ms, ss = rgba[..., c][vis].mean(), rgba[..., c][vis].std() + 1
            md, sd = w[..., c][vis].mean(), w[..., c][vis].std() + 1
            w[..., c] = np.clip((w[..., c].astype(float) - md) * (ss / sd) + ms, 0, 255).astype(np.uint8)
    out[ok, :3] = w[ok, :3]
    out[ok, 3] = 255
    return out, ok


def donor_is_clean(M, L):
    """arms clear of the torso: wrists and elbows outside the torso polygon"""
    poly = torso_poly(M, L, 0.0).astype(np.float32).reshape(-1, 1, 2)
    for k in ['wristL', 'wristR', 'elbowL', 'elbowR']:
        if cv2.pointPolygonTest(poly, tuple(map(float, M[k])), False) >= 0:
            return False
    return True


# ------------------------------------------------------------------ mesh + skinning
def build_mesh(mask, step):
    h, w = mask.shape
    m = cv2.dilate(mask.astype(np.uint8), np.ones((5, 5), np.uint8))
    gx = np.arange(-step, w + 2 * step, step); gy = np.arange(-step, h + 2 * step, step)
    nx, ny = len(gx), len(gy)
    X, Y = np.meshgrid(gx, gy)
    V = np.stack([X.ravel(), Y.ravel()], 1).astype(float)
    # cell is used if any pixel of the dilated mask is inside it
    cell_used = np.zeros((ny - 1, nx - 1), bool)
    ii = np.clip(((np.arange(h) + step) // step), 0, ny - 2)
    jj = np.clip(((np.arange(w) + step) // step), 0, nx - 2)
    ys, xs = np.nonzero(m)
    cell_used[ii[ys], jj[xs]] = True
    tris = []
    for i, j in zip(*np.nonzero(cell_used)):
        v00 = i * nx + j; v01 = v00 + 1; v10 = v00 + nx; v11 = v10 + 1
        tris.append((v00, v01, v11)); tris.append((v00, v11, v10))
    tris = np.array(tris, int).reshape(-1, 3)
    used = np.unique(tris)
    remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    return V[used], remap[tris]


def skin_weights(V, bones, seg, labels_near, sigma):
    """linear-blend weights: each vertex belongs to its own part, blending into the
    neighbouring part only near the joint (soft bend, no hinge seam)."""
    D = []
    for b in bones:
        A, C = seg[b]
        d, _ = seg_dist(V, A, C)
        D.append(d)
    D = np.stack(D, 1)
    D = D - D.min(1, keepdims=True)
    sig = np.array([sigma * (1.8 if (b == 'torso' and len(bones) > 2 and bones[0] == 'torso' and 'head' not in bones) else 1.0) for b in bones])
    W = np.exp(-(D / sig[None]) ** 2)
    # sharpen ownership by the painted label
    if labels_near is not None:
        for k, b in enumerate(bones):
            W[labels_near == b, k] += 1.5
    W /= W.sum(1, keepdims=True)
    return W


def transform_points(V, W, bones, X):
    out = np.zeros_like(V)
    for k, b in enumerate(bones):
        A, o, o2 = X[b]
        out += W[:, k:k + 1] * ((V - o) @ A.T + o2)
    return out


def raster_backmap(Vs, Vd, tris, shape):
    """for each destination pixel inside a warped triangle, the source coordinate"""
    h, w = shape
    mapx = np.full((h, w), -1e4, np.float32); mapy = np.full((h, w), -1e4, np.float32)
    for t in tris:
        d = Vd[t]; s = Vs[t]
        x0, y0 = np.floor(d.min(0)).astype(int); x1, y1 = np.ceil(d.max(0)).astype(int)
        x0 = max(x0, 0); y0 = max(y0, 0); x1 = min(x1, w - 1); y1 = min(y1, h - 1)
        if x1 < x0 or y1 < y0:
            continue
        T = np.array([[d[1, 0] - d[0, 0], d[2, 0] - d[0, 0]], [d[1, 1] - d[0, 1], d[2, 1] - d[0, 1]]])
        det = T[0, 0] * T[1, 1] - T[0, 1] * T[1, 0]
        if abs(det) < 1e-6:
            continue
        Ti = np.array([[T[1, 1], -T[0, 1]], [-T[1, 0], T[0, 0]]]) / det
        yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        px = xx - d[0, 0]; py = yy - d[0, 1]
        u = Ti[0, 0] * px + Ti[0, 1] * py; v = Ti[1, 0] * px + Ti[1, 1] * py
        inside = (u >= -1e-3) & (v >= -1e-3) & (u + v <= 1 + 1e-3)
        if not inside.any():
            continue
        sx = s[0, 0] + u * (s[1, 0] - s[0, 0]) + v * (s[2, 0] - s[0, 0])
        sy = s[0, 1] + u * (s[1, 1] - s[0, 1]) + v * (s[2, 1] - s[0, 1])
        mapx[yy[inside], xx[inside]] = sx[inside]
        mapy[yy[inside], xx[inside]] = sy[inside]
    return mapx, mapy


JOINTS = [('torso', 'head', .14), ('torso', 'uarmL', .18), ('uarmL', 'farmL', .13),
          ('torso', 'uarmR', .18), ('uarmR', 'farmR', .13), ('torso', 'thighL', .22),
          ('thighL', 'shinL', .14), ('shinL', 'footL', .08), ('torso', 'thighR', .22),
          ('thighR', 'shinR', .14), ('shinR', 'footR', .08)]
ALL = list(H.BONES)


def blend_maps(labels, parts, filled, L):
    """smoothed ownership of each bone over the painting. Weights read from these maps are
    continuous across the cut between two layers, so a joint bends, it doesn't tear."""
    lab = labels.copy()
    lab[filled] = parts.index('torso')
    sig = .07 * L
    maps = []
    for b in ALL:
        m = (lab == parts.index(b)).astype(np.float32)
        maps.append(cv2.GaussianBlur(m, (0, 0), sig))
    return np.stack(maps, 0)


def skin(V, prim, seg, maps, L):
    """per-vertex weights over all bones: own part only, except near a joint, where the
    two parts that meet there share the smoothed ownership (tapered with distance)."""
    h, w = maps.shape[1:]
    vi = np.clip(V.round().astype(int), [0, 0], [w - 1, h - 1])
    Wt = np.zeros((len(V), len(ALL)), np.float32)
    samp = maps[:, vi[:, 1], vi[:, 0]].T  # (N, bones)
    pi = np.array([ALL.index(p) for p in prim])
    Wt[np.arange(len(V)), pi] = np.maximum(samp[np.arange(len(V)), pi], .05)
    for P, C, rho in JOINTS:
        J = seg[C][0]
        d = np.linalg.norm(V - J, axis=1)
        r = rho * L
        taper = np.clip((1.6 * r - d) / (.6 * r), 0, 1)
        taper = taper * taper * (3 - 2 * taper)
        for a, b in ((P, C), (C, P)):
            sel = (pi == ALL.index(a)) & (taper > 0)
            k = ALL.index(b)
            Wt[sel, k] = np.maximum(Wt[sel, k], samp[sel, k] * taper[sel])
    Wt /= Wt.sum(1, keepdims=True)
    return Wt


def warp_layer(rgba_layer, mask, bones, seg, X, labels, parts, out_shape, offset, L, maps=None, rigid=False):
    step = max(3, int(round(L / 22)))
    V, tris = build_mesh(mask, step)
    if len(tris) == 0:
        z = np.full(out_shape, -1e4, np.float32)
        return np.zeros(out_shape + (4,), np.float32), (z, z)
    # label of the nearest figure pixel of this layer at each vertex
    h, w = labels.shape
    lb = labels.copy(); lb[~mask] = -1
    _, idx = cv2.distanceTransformWithLabels((lb < 0).astype(np.uint8), cv2.DIST_L2, 5,
                                              labelType=cv2.DIST_LABEL_PIXEL)
    gy, gx = np.nonzero(lb >= 0)
    lut = np.full(idx.max() + 1, -1, int); lut[idx[gy, gx]] = lb[gy, gx]
    vi = np.clip(V.round().astype(int), [0, 0], [w - 1, h - 1])
    vlab = lut[idx[vi[:, 1], vi[:, 0]]]
    prim = []
    for i in vlab:
        nm = parts[i] if i >= 0 else bones[0]
        prim.append(nm if nm in bones else bones[0])
    if rigid:
        Wt = np.zeros((len(V), len(ALL)), np.float32); Wt[:, ALL.index(bones[0])] = 1
    else:
        Wt = skin(V, prim, seg, maps, L)
    Vd = transform_points(V, Wt, ALL, X) + offset
    mx, my = raster_backmap(V, Vd, tris, out_shape)
    pre = rgba_layer.astype(np.float32)
    pre[..., 3] = np.where(mask, pre[..., 3], 0)
    pre[..., :3] *= pre[..., 3:4] / 255.
    out = cv2.remap(pre, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return out, (mx, my)


def over(dst, src):
    a = src[..., 3:4] / 255.
    dst[..., :3] = src[..., :3] + dst[..., :3] * (1 - a)
    dst[..., 3:4] = src[..., 3:4] + dst[..., 3:4] * (1 - a)
    return dst
