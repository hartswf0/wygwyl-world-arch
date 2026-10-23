"""Parts library: heads (with their expression and gaze), hands and props, cut from a
character's paintings.

Two sources:
  * AUTO   -- every painting with Pose Lab markers gives its own head (cut above the collar
              line, perpendicular to the head axis) and its own two hands (skin-coloured pixels
              beyond the wrist marker).  Part id: '<painting id>#head', '#handR', '#handL'.
  * CURATED -- chars/<char>.py CURATED_PARTS: drawings that need a hand-made cut (a fist from a
              sheet without markers, a hand holding a phone, an empty cuff, the chest emblem).

Every part stores the seat it was cut from, measured in its own painting:
  head : the neck marker and the torso axis (neck - mid-hip) angle
  hand : the wrist marker and the forearm (elbow -> wrist) angle
  prop : an anchor point and an angle
plus the source torso length (for scale) and the painting id (for provenance).
Placement maps the seat onto the rig: the same neck / wrist point, rotated by the difference
between the rig's bone angle and the source's, scaled by torso length.  So a painting's own
head and hands land where that painting drew them.
"""
import json, math, os
import numpy as np, cv2

from . import core

TORSO_CM = 45.0     # fallback torso length (neck -> mid-hip) in cm when markers are unusable


def parts_dir(char):
    return os.path.join(core.BUILD, char, 'parts')


def _P(m, k):
    return np.array(m[k][:2], float)


def torso_len(t, prior=True):
    """neck -> mid-hip in px; with prior, a length outside 36-54 cm of the card's scale prior is
    replaced by 45 cm (a character module sets SCALE_PRIOR = False when its prior is wrong)"""
    m = t['markers']
    mid = (_P(m, 'hipR') + _P(m, 'hipL')) / 2
    T = float(np.linalg.norm(_P(m, 'neck') - mid))
    ppcm = t.get('scale_prior', {}).get('px_per_cm')
    if prior and ppcm and not (36 * ppcm < T < 54 * ppcm):
        T = TORSO_CM * ppcm
    return T


def torso_axis(t):
    m = t['markers']
    mid = (_P(m, 'hipR') + _P(m, 'hipL')) / 2
    v = _P(m, 'neck') - mid
    if np.linalg.norm(v) < 20:
        v = np.array([0., -1.])
    return math.atan2(v[1], v[0])


def skin(rgb):
    b, g, r = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    gold = (g > 0.72 * r) & (r > 170)
    return (r > 70) & (r > g + 12) & (g > b + 20) & (r - b > 40) & ~gold


def fill_holes(m):
    m = m.astype(np.uint8)
    ff = m.copy(); h = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, h, (0, 0), 1)
    return (m | (1 - ff)) > 0


def _save(char, pid, im, mask, seat_ok, meta, index):
    """crop to mask, strip the painting's soft edge, write rgba + edge-class map"""
    ys, xs = np.nonzero(mask)
    if len(ys) < 30:
        return False
    x0, y0, x1, y1 = max(xs.min() - 3, 0), max(ys.min() - 3, 0), min(xs.max() + 4, im.shape[1]), min(ys.max() + 4, im.shape[0])
    fig = im[..., 3] > 127
    border = getattr(core.char_module(char), 'PART_BORDER', 3.0)   # the painting's own paper edge width, stripped
    al = core.strip_edge(mask.astype(np.float32) * (im[..., 3] / 255.), fig, border)[y0:y1, x0:x1]
    crop = im[y0:y1, x0:x1].astype(np.float32).copy()
    crop[..., 3] = al * 255
    T = meta.get('torso', 100.0)
    area = float(mask.sum())
    solid = mask & (im[..., 3] > 200)
    edge_px = int(solid[0].sum() + solid[-1].sum() + solid[:, 0].sum() + solid[:, -1].sum())
    border = edge_px > 5          # the figure is cut by the sheet's straight edge here
    meta = dict(meta, area_T2=area / (T * T), touches_border=border)
    if meta.get('kind') == 'head':
        meta['ok'] = (0.12 < area / (T * T) < 0.62) and not border
    elif meta.get('kind') == 'hand':
        meta['ok'] = (0.015 < area / (T * T) < 0.2) and not border
    else:
        meta['ok'] = True
    fn = pid.replace('/', '__').replace('#', '--')
    d = parts_dir(char)
    cv2.imwrite(os.path.join(d, fn + '.png'), np.clip(crop, 0, 255).astype(np.uint8))
    cv2.imwrite(os.path.join(d, fn + '.edge.png'), (seat_ok[y0:y1, x0:x1].astype(np.float32) * 255).astype(np.uint8))
    meta = dict(meta, file=fn, offset=[int(x0), int(y0)])
    index[pid] = meta
    return True


def cut_auto(char, tid, t, catalog, index):
    im = core.read_rgba(os.path.join(core.CUT, tid + '.webp'))
    H, W = im.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    m = t['markers']
    T = torso_len(t, getattr(core.char_module(char), 'SCALE_PRIOR', True))
    th = torso_axis(t)
    fig = im[..., 3] > 127
    sk = skin(im[..., :3]) & fig
    attrs = catalog.get(tid, {})
    handmask = np.zeros((H, W), bool)
    got = []
    for S in 'RL':
        wr, el = _P(m, 'wrist' + S), _P(m, 'elbow' + S)
        f = wr - el
        if np.linalg.norm(f) < 3:
            continue
        f /= np.linalg.norm(f)
        rel = np.stack([xx - wr[0], yy - wr[1]], -1)
        along = rel @ f
        dist = np.hypot(rel[..., 0], rel[..., 1])
        zone = (dist < 0.42 * T) & (along > -0.06 * T)
        s = sk & zone
        s = cv2.morphologyEx(s.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
        n, lab, st, _ = cv2.connectedComponentsWithStats(s.astype(np.uint8))
        keep = np.zeros_like(s)
        for i in range(1, n):
            comp = lab == i
            if st[i, cv2.CC_STAT_AREA] < 0.004 * T * T:
                continue
            if dist[comp].min() < 0.16 * T:
                keep |= comp
        if keep.sum() < 0.02 * T * T:
            continue
        keep = fill_holes(keep)
        keep = cv2.dilate(keep.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
        keep &= fig
        # the cuff side (behind the wrist) is the seat: no edge there
        seat_ok = ~((along < 0.06 * T) & (dist < 0.16 * T))
        handmask |= keep
        pid = tid + '#hand' + S
        if _save(char, pid, im, keep, seat_ok, dict(kind='hand', side=S, painting=tid, family=tid.split('/')[0],
                 wr=wr.tolist(), farm=math.atan2(f[1], f[0]), torso=T, attrs=attrs, conf=float(min(m['wrist' + S][4], m['elbow' + S][4]))), index):
            got.append(pid)
    # head: above the collar line, inside a head-sized disc, not the hands
    n_, ch = _P(m, 'neck'), _P(m, 'chin')
    a = ch - n_
    up = np.array([math.cos(th), math.sin(th)])
    if np.linalg.norm(a) > 4:
        a = a / np.linalg.norm(a)
        ax = up * 0.5 + a * 0.5; ax /= np.linalg.norm(ax)
    else:
        ax = up
    rel = np.stack([xx - n_[0], yy - n_[1]], -1)
    h = rel @ ax
    nrm = np.array([-ax[1], ax[0]])
    perp = rel @ nrm - float((ch - n_) @ nrm)          # across the head, centred on the chin
    s0 = 0.20 * T
    # a head-shaped window: wide at the skull, narrowing to the neck so no shoulder/collar is taken
    half = np.clip(0.18 * T + (h - s0) * 0.9, 0.18 * T, 0.42 * T)
    b_, g_, r_ = [im[..., i].astype(int) for i in range(3)]
    gold = (r_ > 140) & (g_ > 95) & (b_ < 130) & (r_ - b_ > 60)
    zone = (h > s0) & (h < s0 + 0.85 * T) & (np.abs(perp) < half) & fig
    zone &= ~cv2.dilate(handmask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    n, lab, st, _ = cv2.connectedComponentsWithStats(zone.astype(np.uint8))
    if n > 1:
        # the component nearest the chin
        best, bd = 0, 1e9
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < 0.02 * T * T:
                continue
            ys, xs = np.nonzero(lab == i)
            d = np.min(np.hypot(xs - ch[0], ys - ch[1]))
            if d < bd:
                best, bd = i, d
        if best:
            hm = lab == best
            seat_ok = h > s0 + 4
            pid = tid + '#head'
            if _save(char, pid, im, hm, seat_ok, dict(kind='head', painting=tid, family=tid.split('/')[0], neck=n_.tolist(),
                     axis=th, torso=T, attrs=attrs, seat=s0, ax=ax.tolist()), index):
                got.append(pid)
    return got


def cut_curated(char, pid, c, index, MK):
    im = core.read_rgba(os.path.join(core.CUT, c['src'] + '.webp'))
    H, W = im.shape[:2]
    mask = np.zeros((H, W), np.uint8)
    cv2.fillPoly(mask, [np.array(c['poly'], np.int32)], 1)
    mask = (mask > 0) & (im[..., 3] > 127)
    yy0, xx0 = np.mgrid[0:H, 0:W]
    if 'circle' in c:
        cx, cy, r = c['circle']
        mask = (((xx0 - cx) ** 2 + (yy0 - cy) ** 2) <= r * r) & (im[..., 3] > 127)
    if c.get('skin_only'):
        mask &= fill_holes(cv2.morphologyEx((skin(im[..., :3]) & mask).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0)
        mask = cv2.dilate(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
        mask &= im[..., 3] > 127
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    seat_ok = np.zeros((H, W), bool) if c.get('no_edge') else np.ones((H, W), bool)
    if 'wr' in c:
        seat_ok = np.hypot(xx - c['wr'][0], yy - c['wr'][1]) > c.get('seat_r', 9)
    if 'seat_line' in c:
        (ax_, ay), (bx, by) = c['seat_line']
        seat_ok &= ((xx - ax_) * (by - ay) - (yy - ay) * (bx - ax_)) * c.get('seat_sign', 1) > 4 * math.hypot(bx - ax_, by - ay)
    if c['src'] in MK:
        T = torso_len(MK[c['src']], getattr(core.char_module(char), 'SCALE_PRIOR', True))
    else:
        T = c['torso']
    meta = dict(kind=c['kind'], painting=c['src'], family=c['src'].split('/')[0], torso=T, attrs=c.get('attrs', {}), curated=True)
    if c['kind'] == 'hand':
        f = np.array(c['wr'], float) - np.array(c['el'], float)
        meta.update(side=c['side'], wr=list(c['wr']), farm=math.atan2(f[1], f[0]))
    elif c['kind'] == 'head':
        meta.update(neck=list(c['neck']), axis=c.get('axis', -math.pi / 2))
    else:
        meta.update(anchor=list(c['anchor']), angle=c.get('angle', -math.pi / 2), bone=c.get('bone', 'chest'))
    return _save(char, pid, im, mask, seat_ok, meta, index)


def build_parts(char, only=None):
    """Cut every painting's own head and hands, plus the character's curated parts."""
    os.makedirs(parts_dir(char), exist_ok=True)
    spec = core.char_module(char)
    MK = core.load_markers(char)
    catalog = spec.catalog() if hasattr(spec, 'catalog') else {}
    index = {}
    for tid, t in MK.items():
        if only and tid not in only:
            continue
        if spec.is_character_painting(tid, catalog):
            cut_auto(char, tid, t, catalog, index)
    for pid, c in getattr(spec, 'CURATED_PARTS', {}).items():
        cut_curated(char, pid, c, index, MK)
    json.dump(index, open(os.path.join(parts_dir(char), 'index.json'), 'w'), indent=1)
    return index


# ------------------------------------------------------------------ placement at render time
class Parts:
    def __init__(self, char):
        self.char = char
        self.index = json.load(open(os.path.join(parts_dir(char), 'index.json')))
        self.tex = {}

    def has(self, pid):
        return pid in self.index

    def _tex(self, pid, mirror):
        key = (pid, mirror)
        if key not in self.tex:
            p = self.index[pid]
            d = parts_dir(self.char)
            im = cv2.imread(os.path.join(d, p['file'] + '.png'), cv2.IMREAD_UNCHANGED)
            e = cv2.imread(os.path.join(d, p['file'] + '.edge.png'), 0).astype(np.float32) / 255.
            if mirror:
                im = im[:, ::-1].copy(); e = e[:, ::-1].copy()
            self.tex[key] = (core.premul_up(im), cv2.resize(e, None, fx=core.U, fy=core.U, interpolation=cv2.INTER_LINEAR), im.shape[1])
        return self.tex[key]

    def _place(self, acc, pid, mirror, src_pt, src_ang, dst_pt, dst_ang, k, Gs, piece, sc_o, extra_rot=0.0):
        p = self.index[pid]
        tex, E, w = self._tex(pid, mirror)
        ox, oy = p['offset']
        sp = np.array([src_pt[0] - ox, src_pt[1] - oy], float)
        sa = src_ang
        if mirror:
            sp[0] = w - sp[0]
            sa = math.pi - sa
        rot = dst_ang - sa + extra_rot
        c, s = math.cos(rot), math.sin(rot)
        M = k * np.array([[c, -s], [s, c]])
        t = dst_pt - M @ sp
        Mo = np.hstack([Gs[:, :2] @ M, (Gs[:, :2] @ t + Gs[:, 2])[:, None]])
        Mu = Mo.copy(); Mu[:, :2] = Mo[:, :2] / core.U
        lay = cv2.warpAffine(tex, Mu.astype(np.float32), (acc.shape[1], acc.shape[0]), flags=cv2.INTER_LINEAR)
        e = cv2.warpAffine(E, Mu.astype(np.float32), (acc.shape[1], acc.shape[0]), flags=cv2.INTER_LINEAR)
        return piece(acc, lay, e, sc_o)

    @staticmethod
    def _spec(spec):
        return (spec[0], bool(spec[1])) if isinstance(spec, (list, tuple)) else (spec, False)

    def place_head(self, acc, spec, R, A, Gs, opts, piece, sc_o):
        pid, mirror = self._spec(spec)
        p = self.index[pid]
        J = R.J
        Mc = A['chest']
        neck = Mc[:, :2] @ J.get('mkneck', J['neck']) + Mc[:, 2]
        tv = Mc[:, :2] @ (J['neck'] - J['midhip'])
        rig_T = np.linalg.norm(J['neck'] - J['midhip'])
        k = rig_T / p['torso'] * opts.get('head_scale', 1.0)
        head_rot = opts.get('_head_rot', 0.0)
        off = np.array(opts.get('head_off', (0, 0)), float)
        return self._place(acc, pid, mirror, p['neck'], p['axis'], neck + off, math.atan2(tv[1], tv[0]), k, Gs, piece, sc_o,
                           extra_rot=head_rot)

    def place_hand(self, acc, spec, side, R, A, Gs, opts, piece, sc_o):
        pid, mirror = self._spec(spec)
        p = self.index[pid]
        J = R.J
        Mf = A['farm' + side]
        Mh = A['hand' + side]
        wr = Mh[:, :2] @ J['wr' + side] + Mh[:, 2]
        fv = Mf[:, :2] @ (J['wr' + side] - J['el' + side])
        rig_T = np.linalg.norm(J['neck'] - J['midhip'])
        k = rig_T / p['torso'] * opts.get('hand_scale', 1.0)
        extra = math.atan2(*(Mh[:, :2] @ np.array([1.0, 0.0]))[::-1]) - math.atan2(*(Mf[:, :2] @ np.array([1.0, 0.0]))[::-1])
        fu = fv / (np.linalg.norm(fv) + 1e-9)
        return self._place(acc, pid, mirror, p['wr'], p['farm'], wr - fu * 1.5, math.atan2(fv[1], fv[0]), k, Gs, piece, sc_o,
                           extra_rot=extra)

    def place_prop(self, acc, spec, R, A, Gs, opts, piece, sc_o):
        pid, mirror = self._spec(spec)
        p = self.index[pid]
        J = R.J
        Mb = A[p.get('bone', 'chest')]
        nk = np.array(J.get('mkneck', J['neck']), float)
        frac = getattr(R.specs, 'PROP_SPINE_FRAC', {}).get(pid, 0.33)   # down the spine from the neck
        anchor_rig = np.array(opts.get('prop_at', {}).get(pid, nk + frac * (J['midhip'] - nk)), float)
        dst = Mb[:, :2] @ anchor_rig + Mb[:, 2]
        tv = Mb[:, :2] @ np.array([0.0, -1.0])
        rig_T = np.linalg.norm(J['neck'] - J['midhip'])
        k = rig_T / p['torso']
        return self._place(acc, pid, mirror, p['anchor'], p['angle'], dst, math.atan2(tv[1], tv[0]), k, Gs, piece, sc_o)

    def place_cuff(self, acc, side, R, A, Gs, sc_o):
        return None


if __name__ == '__main__':
    import sys
    idx = build_parts(sys.argv[1])
    print(len(idx), 'parts')
