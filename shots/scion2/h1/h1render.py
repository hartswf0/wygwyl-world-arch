"""H1 render: nearest painting -> part masks -> skinned mesh warp toward the target markers."""
import numpy as np, cv2
import h1core as H
import h1warp as W

_cache = {}


def source(pid, targets, mirror):
    key = (pid, mirror)
    if key in _cache:
        return _cache[key]
    rgba = H.load_rgba(pid, key_prop=pid in H.KEYED)
    M = H.markers(targets[pid])
    if mirror:
        rgba = rgba[:, ::-1].copy()
        M = H.mirror_markers(M, rgba.shape[1])
    _cache[key] = (rgba, M)
    return rgba, M


def apply_variant(M, v):
    if v['swap_arm']:
        M = H.swap_side(M, 'arm')
    if v['swap_leg']:
        M = H.swap_side(M, 'leg')
    return M


def pick_donor(M, targets, exclude_family, exclude_pid):
    """another painting of him whose torso is unobstructed, in the nearest view"""
    best = None
    vf = H.view_feat(M)
    for pid in H.CLEAN:
        if pid == exclude_pid or (exclude_family and H.family(pid) == exclude_family):
            continue
        for mir in (False, True):
            DM = H.markers(targets[pid])
            if mir:
                DM = H.mirror_markers(DM, targets[pid]['w'])
            L = np.linalg.norm(DM['neck'] - DM['groin'])
            if not W.donor_is_clean(DM, L):
                continue
            c = np.abs(H.view_feat(DM) - vf).sum()
            if best is None or c < best[0]:
                best = (c, pid, mir)
    if best is None:
        return None, None
    rgba, DM = source(best[1], targets, best[2])
    return (rgba, DM), best[1] + (' (mirrored)' if best[2] else '')


def layer_order(M, F):
    """legs behind the body (higher ankle = farther leg first), arms in front. Legs that
    cross in the painting stay one sheet: which one is in front isn't known from markers,
    so they are not pulled apart."""
    if H.legs_cross(M):
        return ['legs', 'body', 'armL', 'armR']
    legs = sorted(['legL', 'legR'], key=lambda l: F['P']['ankle' + l[-1]][1])
    return legs + ['body', 'armL', 'armR']


def prepare(pid, v, targets, exclude_family):
    key = ('prep', pid, v['mirror'], v['swap_arm'], v['swap_leg'], exclude_family)
    if key in _cache:
        return _cache[key]
    rgba, M0 = source(pid, targets, v['mirror'])
    M = apply_variant(M0, v)
    labels, parts, tmask, radii = W.segment_parts(rgba, M)
    L = float(np.linalg.norm(M['neck'] - M['groin']))
    donor, donor_id = pick_donor(M, targets, exclude_family, pid)
    body_rgba, filled = W.fill_torso(rgba, M, labels, parts, tmask, donor)
    masks = W.layer_masks(labels, parts)
    seg = W.bone_segments(M, L)
    maps = W.blend_maps(labels, parts, filled, L)
    # the painted cut-out rim (light outline round the silhouette): it belongs on the
    # outside. Where a moved part's rim lands inside the figure it is dropped.
    a = (rgba[..., 3] > 128).astype(np.uint8)
    dt = cv2.distanceTransform(a, cv2.DIST_L2, 3)
    gray = rgba[..., :3].astype(float).mean(2)
    rr = max(2.5, .03 * L)
    rim = ((dt < rr) & (gray > 75)).astype(np.float32)
    res = dict(maps=maps, rim=rim, rr=rr, rgba=rgba, M=M, labels=labels, parts=parts, tmask=tmask, body=body_rgba,
               filled=filled, masks=masks, L=L, seg=seg, donor=donor_id)
    _cache[key] = res
    return res


def render(pid, v, T, targets, exclude_family, F=None, cap=H.CAP, pad=None):
    """returns (premultiplied float RGBA canvas, info). Canvas coordinates = target
    marker coordinates + offset."""
    pr = prepare(pid, v, targets, exclude_family)
    M = pr['M']
    if F is None:
        F = H.fit(M, T, cap=cap)
    s = F['s']
    h, w = pr['rgba'].shape[:2]
    # canvas big enough: target extent of markers +- source size * s
    Pm = np.array(list(F['P'].values()))
    span = max(h, w) * s
    x0, y0 = Pm.min(0) - span * 1.2; x1, y1 = Pm.max(0) + span * 1.2
    off = -np.array([x0, y0])
    shape = (int(y1 - y0), int(x1 - x0))
    canvas = np.zeros(shape + (4,), np.float32)
    layers = {}
    # underlay: the root of every limb, carried by the torso only. When a limb turns at
    # the shoulder / hip, the wedge that opens shows the painted joint, not a hole.
    yy, xx = np.mgrid[0:h, 0:w]
    for l in ['legL', 'legR', 'armL', 'armR']:
        root = M[H.BONES[W.LAYER_BONES[l][0]][0]]
        near = (xx - root[0]) ** 2 + (yy - root[1]) ** 2 < (.38 * pr['L']) ** 2
        um = pr['masks'][l] & near
        if um.sum() < 10:
            continue
        out, _ = W.warp_layer(pr['rgba'], um, ['torso'], pr['seg'], F['X'], pr['labels'], pr['parts'],
                              shape, off, pr['L'], rigid=True)
        canvas = W.over(canvas, out)
    under = canvas.copy()
    rims = []
    for l in layer_order(M, F):
        if l == 'legs':
            mask = pr['masks']['legL'] | pr['masks']['legR']
            bones = W.LAYER_BONES['legL'] + W.LAYER_BONES['legR']
        else:
            mask = pr['masks'][l]
            bones = W.LAYER_BONES[l]
        if l == 'body':
            mask = mask | pr['filled']
            img = pr['body']
        else:
            img = pr['rgba']
        if l == 'body':
            bones = ['torso', 'head']
        out, (mx, my) = W.warp_layer(img, mask, bones, pr['seg'], F['X'], pr['labels'], pr['parts'],
                                     shape, off, pr['L'], maps=pr['maps'])
        rimw = cv2.remap(pr['rim'], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        layers[l] = out; rims.append((out, rimw))
        canvas = W.over(canvas, out)
    # second pass: drop rim pixels that ended up inside the figure
    A = (canvas[..., 3] > 128).astype(np.uint8)
    inner = cv2.distanceTransform(A, cv2.DIST_L2, 3) > pr['rr'] * s + 1.5
    # the underlay may only close wedges between parts, never stick out past them
    over_parts = np.zeros(A.shape, np.float32)
    for out, _ in rims:
        over_parts = np.maximum(over_parts, out[..., 3])
    P_ = (over_parts > 128).astype(np.uint8)
    k = max(3, int(.16 * pr['L'] * s)) | 1
    closed = cv2.morphologyEx(P_, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    closed = cv2.GaussianBlur(closed.astype(np.float32), (5, 5), 0)
    canvas = under * closed[..., None]
    for out, rimw in rims:
        k = 1 - np.clip(rimw * 1.5, 0, 1) * inner
        canvas = W.over(canvas, out * k[..., None])
    return canvas, dict(F=F, off=off, donor=pr['donor'], filled=int(pr['filled'].sum()))


def crop_to_height(canvas, height):
    a = canvas[..., 3]
    ys, xs = np.nonzero(a > 8)
    c = canvas[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    k = height / c.shape[0]
    c = cv2.resize(c, (max(1, int(round(c.shape[1] * k))), int(height)), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    c = np.clip(c, 0, 255)
    # un-premultiply
    out = np.zeros(c.shape, np.uint8)
    al = c[..., 3:4]
    rgb = np.where(al > 0, c[..., :3] * 255. / np.maximum(al, 1e-3), 0)
    out[..., :3] = np.clip(rgb, 0, 255)
    out[..., 3] = np.clip(al[..., 0], 0, 255)
    return out


def figure_height(pid):
    im = H.load_rgba(pid)
    ys = np.nonzero(im[..., 3] > 20)[0]
    return ys.max() - ys.min() + 1


def flatten(rgba, bg=(255, 255, 255)):
    a = rgba[..., 3:4] / 255.
    return (rgba[..., :3] * a + np.array(bg) * (1 - a)).astype(np.uint8)


def debug_labels(pid, v, targets, exclude_family):
    pr = prepare(pid, v, targets, exclude_family)
    cols = np.random.RandomState(3).randint(60, 255, (20, 3))
    img = H.load_rgba(pid)
    vis = flatten(pr['rgba']).astype(float)
    lab = pr['labels']
    for i in range(len(pr['parts'])):
        vis[lab == i] = vis[lab == i] * .5 + cols[i] * .5
    vis[pr['filled']] = [255, 0, 255]
    return vis.astype(np.uint8)
