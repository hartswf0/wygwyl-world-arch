"""rigkit core -- layered, mesh-deformed rigs made from single paintings (the H3 method).
See README.md. A character module in chars/ supplies the masters (layer cuts) and config.

Rendering, per frame, always straight from the master textures (no frame is resampled
from another frame):
  * every layer is a triangle mesh over its alpha, skinned to the layer's bones with soft
    weights (softmax of distance to the bone segments), rasterised into a lookup into the
    master texture (upsampled 3x once, bilinear);
  * the painting's own soft paper edge is stripped from every piece when the rig is built,
    and each piece (layer, head, hand) gets one crisp edge at render time, at output
    resolution: a thin dark-brown line and a hairline of tan, the same everywhere, drawn
    under the piece so it shows only outside it; seams that are meant to be continuous
    (sleeve into shoulder, head into collar, thigh into seat) carry no edge;
  * brads are rigid sprites riding their joints, never rotated.
"""
import json, math, os
import numpy as np, cv2

import importlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
BUILD = os.path.join(HERE, 'build')
U = 3
EDGE_BROWN = np.array([30, 52, 104], np.float32)   # BGR, the paintings' inner edge line
EDGE_TAN = np.array([96, 122, 146], np.float32)    # BGR, the paintings' outer hairline
EDGE_W = (1.6, 1.0)                                # widths in master px (brown, tan)


def char_module(char):
    return importlib.import_module('rigkit.chars.' + char)


def markers_path(char):
    for p in ('shots/rig/poses_v2/%s.json', 'shots/rig/poses/%s.json'):
        f = os.path.join(ROOT, p % char)
        if os.path.exists(f):
            return f
    raise FileNotFoundError(char)


_MK = {}


def load_markers(char='poet__red_black_sunglasses'):
    """{painting id: target}.  A character module may list its own MARKER_FILES (merged in order,
    later files win) and EXCLUDE_TARGETS ({id: reason}: paintings in those files that are not this
    character, e.g. the ex solved on a poet sheet)."""
    if char not in _MK:
        try:
            spec = char_module(char)
        except ImportError:
            spec = None
        files = [os.path.join(ROOT, f) for f in getattr(spec, 'MARKER_FILES', [])] or [markers_path(char)]
        out = {}
        for f in files:
            out.update({t['id']: t for t in json.load(open(f))['targets']})
        for tid in getattr(spec, 'EXCLUDE_TARGETS', {}):
            out.pop(tid, None)
        for tid, fix in getattr(spec, 'MARKER_FIX', {}).items():     # hand corrections {id: {marker: (x, y)}}
            m = dict(out[tid]['markers'])
            for k, (x, y) in fix.items():
                m[k] = [float(x), float(y)] + list(m.get(k, [0, 0, 1.0, 'fix', 1.0])[2:4]) + [1.0]
            out[tid] = dict(out[tid], markers=m)
        _MK[char] = out
    return _MK[char]


def read_rgba(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


def strip_edge(alpha, fig, border):
    """remove the painting's own paper edge along the original silhouette"""
    dM = cv2.distanceTransform(np.pad(fig.astype(np.uint8), 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
    return alpha * np.clip(dM - border + 0.5, 0, 1)


def refine_brad(rgb, c):
    x0, y0 = int(c[0]) - 12, int(c[1]) - 12
    patch = rgb[max(0, y0):y0 + 25, max(0, x0):x0 + 25]
    b, g, r = patch[..., 0], patch[..., 1], patch[..., 2]
    gold = ((r > 150) & (g > 110) & (b < 120)).astype(np.float32)
    if gold.sum() < 10:
        return np.array(c, float)
    ys, xs = np.nonzero(gold)
    return np.array([max(0, x0) + xs.mean(), max(0, y0) + ys.mean()])


# ------------------------------------------------------------------ build
def build_rig(char, view, master_painting=None):
    """Build one view rig of a character: layers, meshes' source textures, edge classes, brads.
    The layer cuts come from chars/<char>.py MASTERS[view] = (painting id, builder fn)."""
    specs = char_module(char)
    mid, fn = specs.MASTERS.get(view, (master_painting, 'auto'))
    if master_painting:
        mid = master_painting
    if fn == 'auto':
        from . import auto
        mk = load_markers(char)[mid]['markers']
        fn = lambda rgb, a: auto.build_auto(rgb, a, mk, plain_fn=getattr(specs, 'PLAIN_FABRIC', None),
                                              **getattr(specs, 'AUTO_OPTS', {}))
    out = os.path.join(BUILD, char, 'rig', view)
    os.makedirs(out, exist_ok=True)
    im = read_rgba(os.path.join(CUT, mid + '.webp')).astype(np.float32)
    rgb, a = im[..., :3], im[..., 3] / 255.
    S = fn(rgb, a)
    J = S['joints']
    try:
        mk = load_markers(char)[mid]['markers']
        J = dict(J, mkneck=tuple(mk['neck'][:2]))
    except KeyError:
        J = dict(J, mkneck=J['neck'])
    meta = {'master': mid, 'view': view, 'joints': {k: list(v) for k, v in J.items()}, 'layers': [],
            'brads': [list(b) for b in S.get('brads', [])]}
    # every painted brad is removed from every layer (filled from the surrounding cloth/leather);
    # each is drawn back once at render time from one clean source brad
    b_, g_, r_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    goldish = (r_ > 110) & (r_ - b_ > 40)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
    for L in S['layers']:
        img = np.clip(L['rgb'], 0, 255).astype(np.uint8)
        for (_, _, _, bx, by, br, rr) in S.get('brads', []):
            circ = (xx - bx) ** 2 + (yy - by) ** 2 <= rr * rr
            if not (circ & (L['alpha'] > 0.5)).any():
                continue
            ring = ((xx - bx) ** 2 + (yy - by) ** 2 <= (rr + 6) ** 2) & ~circ & ~goldish & (a > 0.5)
            m = (~ring).astype(np.uint8) * 255
            src = img.copy(); src[~ring] = 0
            filled = cv2.inpaint(src, m, 6, cv2.INPAINT_TELEA)
            img[circ] = filled[circ]
        L['rgb'] = img.astype(np.float32)
    # the one clean source brad: the front master's right-shoulder brad, 6x, round soft edge
    bsrc = specs.BRAD_SOURCE   # (painting, cx, cy, brass radius, sprite radius)
    fm = read_rgba(os.path.join(CUT, bsrc[0] + '.webp')).astype(np.float32)
    K, cx, cy, R0 = 6, bsrc[1], bsrc[2], bsrc[4]
    big = cv2.resize(fm[int(cy) - 12:int(cy) + 13, int(cx) - 12:int(cx) + 13], None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
    gy, gx = np.mgrid[0:big.shape[0], 0:big.shape[1]].astype(np.float32)
    ox, oy = (cx - (int(cx) - 12)) * K, (cy - (int(cy) - 12)) * K
    d = np.hypot(gx - ox, gy - oy) / K
    big[..., 3] = 255 * np.clip((R0 - d) * 2.0 + 0.5, 0, 1)
    cv2.imwrite(os.path.join(out, 'brad.png'), np.clip(big, 0, 255).astype(np.uint8))
    meta['brad_src'] = {'painting': bsrc[0], 'center': [ox / K, oy / K], 'K': K, 'brass_r': bsrc[3], 'R0': R0}
    for L in S['layers']:
        al = strip_edge(L['alpha'], S['fig'], S['border'])
        rgba = np.dstack([np.clip(L['rgb'], 0, 255), np.clip(al * 255, 0, 255)]).astype(np.uint8)
        cv2.imwrite(os.path.join(out, f"layer_{L['name']}.png"), rgba)
        # edge class: 1 = the painting's own outline (always edged), 0.5 = a cut (edged only where it
        # ends up on the silhouette), 0 = a seam meant to read as continuous cloth (never edged)
        dM = cv2.distanceTransform(np.pad(S['fig'].astype(np.uint8), 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
        E = np.where(L['edgeok'] < 0.5, 0.0, np.where(dM < S['border'] + 2.5, 1.0, 0.5))
        cv2.imwrite(os.path.join(out, f"edge_{L['name']}.png"), (E * 255).astype(np.uint8))
        m = {k: L[k] for k in ('name', 'bones', 'tau', 'torso', 'hand', 'is_head', 'side') if k in L}
        meta['layers'].append(m)
    cv2.imwrite(os.path.join(out, 'master.png'), im.astype(np.uint8))
    json.dump(meta, open(os.path.join(out, 'rig.json'), 'w'), indent=1)
    return out


def seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def premul_up(rgba):
    L = cv2.resize(rgba.astype(np.float32), None, fx=U, fy=U, interpolation=cv2.INTER_CUBIC)
    L = np.clip(L, 0, 255)
    L[..., :3] *= L[..., 3:] / 255.
    return L


def over(dst, src):
    return src + dst * (1 - src[..., 3:] / 255.)


# ------------------------------------------------------------------ runtime
class Rig:
    def __init__(self, char, view, step=2.0):
        d = os.path.join(BUILD, char, 'rig', view)
        self.char = char
        self.specs = char_module(char)
        self.meta = json.load(open(os.path.join(d, 'rig.json')))
        self.view = view
        self.J = {k: np.array(v, float) for k, v in self.meta['joints'].items()}
        self.layers = self.meta['layers']
        self.order = [L['name'] for L in self.layers]
        self.tex, self.edge, self.mesh, self.nohand = {}, {}, {}, {}
        master = read_rgba(os.path.join(d, 'master.png'))
        mu = cv2.resize(master.astype(np.float32), None, fx=U, fy=U, interpolation=cv2.INTER_CUBIC)
        self.brads = self.meta.get('brads', [])
        bs = cv2.imread(os.path.join(d, 'brad.png'), cv2.IMREAD_UNCHANGED).astype(np.float32)
        bs[..., :3] *= bs[..., 3:] / 255.
        self.brad_spr = (bs, self.meta['brad_src'])
        for L in self.layers:
            n = L['name']
            rgba = cv2.imread(os.path.join(d, f'layer_{n}.png'), cv2.IMREAD_UNCHANGED)
            self.tex[n] = premul_up(rgba)
            e = cv2.imread(os.path.join(d, f'edge_{n}.png'), 0).astype(np.float32) / 255.
            self.edge[n] = cv2.resize(e, None, fx=U, fy=U, interpolation=cv2.INTER_LINEAR)
            self.mesh[n] = self._mesh(L, rgba[..., 3] > 8, step)
            if 'hand' in L:
                (side, (x0, y0, nx, ny)), = L['hand'].items()
                H, W = self.tex[n].shape[:2]
                yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) / U
                keep = np.clip(((xx - x0) * nx + (yy - y0) * ny) / 1.5, 0, 1)
                self.nohand[n] = self.tex[n] * keep[..., None]

    def _mesh(self, L, mask, step):
        H, W = mask.shape
        md = cv2.dilate(mask.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        xs = np.arange(0, W + step, step); ys = np.arange(0, H + step, step)
        gx, gy = np.meshgrid(xs, ys)
        V = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float64)
        nx = len(xs)
        # cells touching the mask
        cell = np.zeros((len(ys) - 1, len(xs) - 1), bool)
        for j in range(len(ys) - 1):
            r0, r1 = int(ys[j]), int(min(H, ys[j] + step + 1))
            row = md[r0:r1].any(0) if r1 > r0 else np.zeros(W, bool)
            for i in range(len(xs) - 1):
                c0, c1 = int(xs[i]), int(min(W, xs[i] + step + 1))
                cell[j, i] = row[c0:c1].any() if c1 > c0 else False
        jj, ii = np.nonzero(cell)
        a = jj * nx + ii; b = a + 1; c = a + nx; d = c + 1
        tris = np.concatenate([np.stack([a, b, d], 1), np.stack([a, d, c], 1)])
        used = np.unique(tris)
        remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
        V = V[used]; tris = remap[tris]
        J = self.J
        if L['bones'] == 'torso':
            T = L['torso']
            if 'p0' in T:      # blend along the spine: p1 = all chest, p0 = all pelvis
                p0, p1 = np.array(T['p0']), np.array(T['p1'])
                dv = p0 - p1
                t = np.clip(((V - p1) @ dv) / (dv @ dv), 0, 1)
            else:
                t = np.clip((V[:, 1] - T['y0']) / (T['y1'] - T['y0']), 0, 1)
            t = t * t * (3 - 2 * t)
            wa = []
            names = ['chest', 'pelvis']
            for sj, bone in T['caps']:
                dd = np.linalg.norm(V - J[sj], axis=1)
                lat = np.clip((np.abs(V[:, 0] - T['cx']) - (abs(J[sj][0] - T['cx']) - 12)) / 12, 0, 1)
                wa.append(0.6 * np.clip(1 - dd / 20, 0, 1) * lat); names.append(bone)
            wa = np.stack(wa, 1)
            rest = 1 - wa.sum(1, keepdims=True)
            Wt = np.hstack([rest * (1 - t)[:, None], rest * t[:, None], wa])
        else:
            names = list(L['bones'])
            D = np.stack([np.min([seg_dist(V, J[p], J[q]) for p, q in L['bones'][b]], axis=0) for b in names], 1)
            Wt = np.exp(-(D - D.min(1, keepdims=True)) / L['tau'])
            Wt /= Wt.sum(1, keepdims=True)
        depth = Wt @ np.array([self.specs.DEPTH[b] for b in names], float)
        td = depth[tris].mean(1)
        order = np.argsort(td, kind='stable')
        tris = tris[order]
        av = mask[np.clip(V[:, 1].astype(int), 0, H - 1), np.clip(V[:, 0].astype(int), 0, W - 1)]
        return {'V': V, 'T': tris, 'W': Wt, 'names': names, 'G': np.round(td[order] * 2).astype(int), 'opaque': av[tris].all(1)}

    # -------------------------------------------------------------- posing
    def transforms(self, P):
        J = self.J
        A = {}

        def aff(pr, pn, rot, ax=None, sa=1.0, sp=1.0):
            c, s = math.cos(rot), math.sin(rot)
            R = np.array([[c, -s], [s, c]])
            S = np.eye(2)
            if ax is not None:
                u = ax / np.linalg.norm(ax); n = np.array([-u[1], u[0]])
                S = sa * np.outer(u, u) + sp * np.outer(n, n)
            M = R @ S
            return np.hstack([M, (pn - M @ pr)[:, None]])

        app = lambda M, p: M[:, :2] @ p + M[:, 2]
        root = J['midhip'] + np.array(P.get('root_off', (0., 0.)))
        A['pelvis'] = aff(J['midhip'], root, P.get('pelvis', 0.), np.array([1., 0.]), P.get('hipw', 1.), 1.)
        A['chest'] = aff(J['midhip'], root, P.get('chest', 0.), J['neck'] - J['midhip'], P.get('torso_len', 1.), P.get('shw', 1.))
        A['head'] = aff(J['headpiv'], app(A['chest'], J['headpiv']), P.get('head', 0.) + P.get('chest', 0.))
        for S in 'RL':
            sh = app(A['chest'], J['sh' + S])
            A['uarm' + S] = aff(J['sh' + S], sh, P.get('uarm' + S, 0.), J['el' + S] - J['sh' + S], P.get('luarm' + S, 1.))
            el = app(A['uarm' + S], J['el' + S])
            A['farm' + S] = aff(J['el' + S], el, P.get('farm' + S, 0.), J['wr' + S] - J['el' + S], P.get('lfarm' + S, 1.))
            wr = app(A['farm' + S], J['wr' + S])
            A['hand' + S] = aff(J['wr' + S], wr, P.get('hand' + S, P.get('farm' + S, 0.)))
            hip = app(A['pelvis'], J['hip' + S])
            A['thigh' + S] = aff(J['hip' + S], hip, P.get('thigh' + S, 0.), J['kn' + S] - J['hip' + S], P.get('lthigh' + S, 1.))
            kn = app(A['thigh' + S], J['kn' + S])
            A['shin' + S] = aff(J['kn' + S], kn, P.get('shin' + S, 0.), J['an' + S] - J['kn' + S], P.get('lshin' + S, 1.))
            an = app(A['shin' + S], J['an' + S])
            A['foot' + S] = aff(J['an' + S], an, P.get('foot' + S, 0.))
        return A

    def joint_pos(self, A):
        J = self.J
        app = lambda M, p: M[:, :2] @ p + M[:, 2]
        m = {'shR': 'uarmR', 'shL': 'uarmL', 'elR': 'farmR', 'elL': 'farmL', 'wrR': 'handR', 'wrL': 'handL',
             'tipR': 'handR', 'tipL': 'handL', 'hipR': 'thighR', 'hipL': 'thighL', 'knR': 'shinR', 'knL': 'shinL',
             'anR': 'footR', 'anL': 'footL', 'toR': 'footR', 'toL': 'footL', 'headpiv': 'head', 'headtop': 'head',
             'neck': 'chest', 'collar': 'chest', 'midhip': 'pelvis'}
        return {j: app(A[b], J[j]) for j, b in m.items()}

    def deform(self, name, A):
        m = self.mesh[name]
        V = m['V']
        Vp = np.zeros_like(V)
        for k, b in enumerate(m['names']):
            Mb = A[b]
            Vp += m['W'][:, k:k + 1] * (V @ Mb[:, :2].T + Mb[:, 2])
        return Vp

    # -------------------------------------------------------------- render
    def render(self, P, G, size, ss=2, opts=None, lib=None):
        """Render only the figure's window, then place it on the full canvas."""
        Wo, Ho = size
        A = self.transforms(P)
        pts = np.vstack([self.deform(n, A) for n in self.order]) @ G[:, :2].T + G[:, 2]
        sc = math.sqrt(abs(np.linalg.det(G[:, :2])))
        mg = int(70 * sc) + 8
        x0 = max(0, int(pts[:, 0].min()) - mg); y0 = max(0, int(pts[:, 1].min()) - mg)
        x1 = min(Wo, int(pts[:, 0].max()) + mg); y1 = min(Ho, int(pts[:, 1].max()) + mg)
        out = np.zeros((Ho, Wo, 4), np.uint8)
        if x1 > x0 and y1 > y0:
            G2 = G.copy(); G2[:, 2] -= (x0, y0)
            out[y0:y1, x0:x1] = self._render(A, G2, (x1 - x0, y1 - y0), ss, opts or {}, lib)
        return out, self.joint_pos(A)

    def _ring(self, lay, E, sc_o, bg_a):
        """crisp paper edge for one piece: brown line + tan hairline, outside the piece only"""
        al = lay[..., 3] / 255.
        hard = (al > 0.5).astype(np.uint8)
        if not hard.any():
            return None
        wb, wt = EDGE_W[0] * sc_o, EDGE_W[1] * sc_o
        d = cv2.distanceTransform(1 - hard, cv2.DIST_L2, 5)
        r = int(math.ceil(wb + wt)) + 1
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        e1 = cv2.dilate(((E > 0.75) * hard).astype(np.float32), k)
        e2 = cv2.dilate((((E > 0.25) & (E <= 0.75)) * hard).astype(np.float32), k)
        Eo = np.clip(e1 + e2 * (1 - bg_a), 0, 1)
        a_out = np.clip(wb + wt - d + 0.5, 0, 1) * (d > 0) * Eo
        tmix = np.clip(d - wb + 0.5, 0, 1)[..., None]
        col = EDGE_BROWN * (1 - tmix) + EDGE_TAN * tmix
        ring = np.dstack([col * a_out[..., None], a_out * 255])
        return ring.astype(np.float32)

    def _piece(self, acc, lay, E, sc_o, edge=True):
        if edge:
            ring = self._ring(lay, E, sc_o, acc[..., 3] / 255.)
            if ring is not None:
                acc = over(acc, ring)
        return over(acc, lay)

    def _render(self, A, Gs0, size, ss, opts, lib):
        Wo, Ho = size
        S2 = np.diag([ss, ss, 1.])
        Gs = (S2 @ np.vstack([Gs0, [0, 0, 1]]))[:2]
        sc_o = math.sqrt(abs(np.linalg.det(Gs[:, :2])))
        W2, H2 = Wo * ss, Ho * ss
        acc = np.zeros((H2, W2, 4), np.float32)
        hands = opts.get('hands', {})
        for L in self.layers:
            n = L['name']
            if L.get('is_head') and opts.get('head'):
                acc = lib.place_head(acc, opts['head'], self, A, Gs, opts, self._piece, sc_o)
                continue
            m = self.mesh[n]
            V = m['V']
            Vp = self.deform(n, A)
            Vo = Vp @ Gs[:, :2].T + Gs[:, 2]
            T = m['T']
            er = np.stack([np.linalg.norm(V[T[:, i]] - V[T[:, (i + 1) % 3]], axis=1) for i in range(3)], 1)
            eo = np.stack([np.linalg.norm(Vo[T[:, i]] - Vo[T[:, (i + 1) % 3]], axis=1) for i in range(3)], 1)
            keep = ~(((eo.max(1) / (sc_o * er.max(1) + 1e-6)) > 1.8) & ~m['opaque'])
            tex = self.tex[n]
            side = L.get('side')
            hsw = hands.get(side) if side else None
            if hsw and n in self.nohand:
                tex = self.nohand[n]
            mx, my, cov = raster_fast(Vo, V * U, T[keep], m['G'][keep], W2, H2, self.tex[n][..., 3])
            cuff = None
            if hsw and hsw not in ('none',):
                if hsw == 'cuff':
                    cuff = lib.place_cuff(acc, side, self, A, Gs, sc_o)
                else:
                    acc = lib.place_hand(acc, hsw, side, self, A, Gs, opts, self._piece, sc_o)
            lay = cv2.remap(tex, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) * cov[..., None]
            E = cv2.remap(self.edge[n], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            acc = self._piece(acc, lay, E, sc_o)
            if cuff is not None:
                acc = over(acc, cuff)
            for pid, after in opts.get('props', []):
                if after == n:
                    acc = lib.place_prop(acc, pid, self, A, Gs, opts, self._piece, sc_o)
            for (bn, bl, b, bx, by, br, rr) in self.brads:
                if bl != n:
                    continue
                spr, meta = self.brad_spr
                Mb = A[b]
                p = Mb[:, :2] @ np.array([bx, by]) + Mb[:, 2]
                po = Gs[:, :2] @ p + Gs[:, 2]
                k = sc_o * br / meta['brass_r'] / meta['K']        # sprite px -> output px
                ox, oy = meta['center'][0] * meta['K'], meta['center'][1] * meta['K']
                half = int(math.ceil(k * spr.shape[0])) + 3
                cx0, cy0 = max(int(po[0]) - half, 0), max(int(po[1]) - half, 0)
                cx1, cy1 = min(int(po[0]) + half + 1, W2), min(int(po[1]) + half + 1, H2)
                if cx1 <= cx0 or cy1 <= cy0:
                    continue
                M = np.float32([[k, 0, po[0] - k * ox - cx0], [0, k, po[1] - k * oy - cy0]])
                so = cv2.warpAffine(spr, M, (cx1 - cx0, cy1 - cy0), flags=cv2.INTER_AREA)
                acc[cy0:cy1, cx0:cx1] = over(acc[cy0:cy1, cx0:cx1], so)
        out = cv2.resize(acc, (Wo, Ho), interpolation=cv2.INTER_AREA)
        # drop detached specks (stray texels from a part's margin): keep components >= 2% of the figure
        n, lab, st, _ = cv2.connectedComponentsWithStats((out[..., 3] > 20).astype(np.uint8))
        if n > 2:
            big = st[1:, cv2.CC_STAT_AREA].max()
            for i in range(1, n):
                if st[i, cv2.CC_STAT_AREA] < 0.02 * big:
                    out[lab == i] = 0
        a = out[..., 3:]
        rgb = np.where(a > 0, out[..., :3] / np.maximum(a, 1e-3) * 255., 0)
        return np.dstack([np.clip(rgb, 0, 255), np.clip(a, 0, 255)]).astype(np.uint8)


def raster_fast(Vo, UV, T, groups, W, H, alpha):
    """ID-buffer rasteriser: each depth group's triangles are filled with their index; texture
    coordinates come from each triangle's affine map; a later group replaces earlier cloth
    only where its own texel is painted."""
    mx = np.full((H, W), -10, np.float32); my = np.full((H, W), -10, np.float32)
    cov = np.zeros((H, W), np.float32)
    P = Vo[T]; Q = UV[T]
    X = np.concatenate([P, np.ones(P.shape[:2] + (1,))], 2)
    det = np.linalg.det(X)
    good = np.abs(det) > 1e-9
    Minv = np.zeros_like(X); Minv[good] = np.linalg.inv(X[good])
    Mu = np.einsum('nij,njk->nik', Minv, Q)
    SH = 4
    for g in np.unique(groups):
        idx = np.nonzero((groups == g) & good)[0]
        if not len(idx):
            continue
        ids = np.zeros((H, W), np.int32)
        pts = np.round(P[idx] * (1 << SH) - (1 << (SH - 1))).astype(np.int32)
        for k, i in enumerate(idx):
            cv2.fillConvexPoly(ids, pts[k], int(i) + 1, lineType=cv2.LINE_8, shift=SH)
        ys, xs = np.nonzero(ids)
        if not len(ys):
            continue
        t = ids[ys, xs] - 1
        px = xs + 0.5; py = ys + 0.5
        u = px * Mu[t, 0, 0] + py * Mu[t, 1, 0] + Mu[t, 2, 0]
        v = px * Mu[t, 0, 1] + py * Mu[t, 1, 1] + Mu[t, 2, 1]
        ai = alpha[np.clip(v.astype(int), 0, alpha.shape[0] - 1), np.clip(u.astype(int), 0, alpha.shape[1] - 1)]
        ok = (ai > 60) | (cov[ys, xs] == 0)
        ys, xs, u, v = ys[ok], xs[ok], u[ok], v[ok]
        mx[ys, xs] = u; my[ys, xs] = v; cov[ys, xs] = 1
    return mx, my, cov


if __name__ == '__main__':
    import sys
    ch = sys.argv[1]
    for v in (sys.argv[2:] or list(char_module(ch).MASTERS)):
        print(build_rig(ch, v))
