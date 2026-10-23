"""H3 -- one painting made into a layered, mesh-deformed rig (Live2D / Spine style).

Master (front view): shots/kits/cut/poet.11.main-poses/02-front-guide-stone.webp
(family poet.11 is not a target family in shots/scion2/test_set.json).

Layers, back to front:
  legs   : trousers + boots as ONE mesh (both legs, pelvis/waist, crotch).  Hidden
           waist under the jacket hem is completed by inpainting from the trousers.
  torso  : jacket incl. hem, collar, shoulder caps.  The jacket side under each upper
           arm is completed by inpainting; the neck under the beard likewise.
  head   : face + hair above the collar; optional yaw warp (features slide, outline stays).
  armR / armL : sleeve + forearm + hand as ONE mesh per arm, bending at the elbow.
  brads  : the painting's own brass brads (shoulder, elbow, hip, knee) re-placed rigidly
           (never rotated, so their highlight stays lit from the painting's light).

Each layer is a triangle mesh over its alpha.  Every vertex is skinned to the layer's
bones with soft weights (softmax of distance to the bone segments), so a joint bends the
cloth across a band instead of hinging at a cut (linear blend skinning).
Rendering rasterises the deformed mesh into a per-pixel lookup into the master's
texture (bilinear), so the pixels are the painting's pixels, moved.
"""
import json, math, os
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
MASTER_ID = 'poet.11.main-poses/02-front-guide-stone'
MASTER = os.path.join(ROOT, 'shots/kits/cut', MASTER_ID + '.webp')
MARKERS = os.path.join(ROOT, 'shots/rig/poses_v2/poet__red_black_sunglasses.json')
U = 3            # texture upsampling of the master
BORDER = np.array([45, 63, 135], np.float32)       # BGR of the painting's paper edge
BORDER_OUT = np.array([80, 94, 139], np.float32)
DARK = np.array([18, 22, 40], np.float32)


def load_markers():
    d = json.load(open(MARKERS))
    return {t['id']: t for t in d['targets']}


# ----------------------------------------------------------------- rest skeleton (master px)
J = dict(
    neck=(159.5, 80.0), headtop=(161.0, 4.0), headpiv=(159.5, 66.0),
    midhip=(159.0, 190.0), waist=(159.0, 150.0), crotch=(158.5, 212.0),
    shR=(117.0, 87.5), elR=(93.5, 148.5), wrR=(51.0, 151.0), tipR=(10.0, 138.0),
    shL=(203.0, 87.5), elL=(226.0, 148.5), wrL=(269.0, 150.0), tipL=(310.0, 138.0),
    hipR=(129.5, 190.0), knR=(120.5, 288.0), anR=(104.5, 366.0), toR=(70.0, 404.0),
    hipL=(189.0, 190.0), knL=(199.5, 288.0), anL=(214.0, 364.5), toL=(252.0, 402.0),
)
J = {k: np.array(v, np.float64) for k, v in J.items()}

# bones: name -> (joint a, joint b, parent)
BONES = {
    'pelvis': ('midhip', 'waist', None),
    'chest': ('midhip', 'neck', 'pelvis'),
    'head': ('headpiv', 'headtop', 'chest'),
    'uarmR': ('shR', 'elR', 'chest'), 'farmR': ('elR', 'wrR', 'uarmR'), 'handR': ('wrR', 'tipR', 'farmR'),
    'uarmL': ('shL', 'elL', 'chest'), 'farmL': ('elL', 'wrL', 'uarmL'), 'handL': ('wrL', 'tipL', 'farmL'),
    'thighR': ('hipR', 'knR', 'pelvis'), 'shinR': ('knR', 'anR', 'thighR'), 'footR': ('anR', 'toR', 'shinR'),
    'thighL': ('hipL', 'knL', 'pelvis'), 'shinL': ('knL', 'anL', 'thighL'), 'footL': ('anL', 'toL', 'shinL'),
}
BRADS = {  # joint -> (radius px, layer it sits on)
    'shR': 11, 'shL': 11, 'elR': 9.5, 'elL': 9.5, 'hipR': 10.5, 'hipL': 10.5, 'knR': 13, 'knL': 13,
}


def _interp_x(y, pts):
    ys = [p[0] for p in pts]; xs = [p[1] for p in pts]
    return np.interp(y, ys, xs)


DIV_R = [(60, 131), (72, 130), (90, 125), (110, 117), (130, 113), (150, 110), (190, 110)]
DIV_L = [(60, 189), (72, 190), (90, 195), (110, 202), (130, 205), (150, 207), (190, 207)]
HEM_Y = 183.0
FIST_SRC = 'poet.14.muse-dance/cards-2'
# side, crop box (x0,y0,x1,y1), wrist base, knuckle top  (source px)
FISTS = [('R', (5, 0, 50, 44), (23, 42), (25, 0)), ('L', (143, 2, 188, 46), (171, 43), (165, 4))]
FIST_SCALE = 0.85
HAND_CUT = {'R': 50.0, 'L': 270.0}   # x where the painted hand leaves the cuff


def seg_dist(P, a, b):
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    q = a + t[:, None] * ab
    return np.linalg.norm(P - q, axis=1), t


# ----------------------------------------------------------------- build the layered rig
def build(out_dir=None):
    out_dir = out_dir or os.path.join(HERE, 'rig')
    os.makedirs(out_dir, exist_ok=True)
    im = cv2.imread(MASTER, cv2.IMREAD_UNCHANGED).astype(np.float32)
    H, W = im.shape[:2]
    rgb, a = im[:, :, :3], im[:, :, 3] / 255.
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    fig = a > 0.5
    xr = _interp_x(yy, DIV_R); xl = _interp_x(yy, DIV_L)

    def circ(c, r):
        return (xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= r * r

    # head: above the collar line
    head = fig & (yy < 64) & (xx > 128) & (xx < 194)
    # arms: outside the dividers, above the hem
    armR = fig & (xx < xr) & (yy < HEM_Y + 2) & (yy > 62)
    armL = fig & (xx > xl) & (yy < HEM_Y + 2) & (yy > 62)
    # torso: between the dividers, plus shoulder caps
    torso_vis = fig & (yy >= 60) & (yy < HEM_Y + 1) & (~armR | circ(J['shR'], 14)) & (~armL | circ(J['shL'], 14))
    for sh in (J['shR'], J['shL']):   # the shoulder top (collar to brad) stays on the jacket
        torso_vis |= fig & (yy < sh[1] + 2) & (yy >= 60) & (np.abs(xx - 159.5) < abs(sh[0] - 159.5) + 4) & ~head
    legs_vis = fig & (yy >= HEM_Y - 4)

    # ---- hidden-area completion -------------------------------------------------
    # torso side under each arm: the jacket continues straight down from the shoulder cap
    side = np.zeros_like(fig)
    for y in range(80, int(HEM_Y) + 1):
        xo = np.interp(y, [80, 100, 130, 160, HEM_Y], [104, 104, 108, 110, 110])
        xo2 = np.interp(y, [80, 100, 130, 160, HEM_Y], [216, 216, 211, 208, 208])
        side[y, int(xo):int(_interp_x(y, DIV_R)) + 1] = True
        side[y, int(_interp_x(y, DIV_L)):int(xo2) + 1] = True
    side &= fig | (yy < 152)   # the jacket side runs straight down under the arm to the elbow gap
    neck = (yy >= 44) & (yy < 66) & (xx > 140) & (xx < 180)
    torso_m = torso_vis | side | neck
    fill = (torso_m & ~torso_vis) | neck & head
    plain = plain_fabric(rgb, fig)
    known = torso_vis & ~fill & plain
    torso_rgb = inpaint(rgb, fill, known, 9)
    # neck under the jaw: the face's own skin, in shadow (only seen when the head tilts)
    skin = rgb[40:50, 147:152].reshape(-1, 3)
    neck_col = np.median(skin, 0) * 0.55
    neck_m = neck & head
    torso_rgb[neck_m] = neck_col
    torso_m = torso_m & ~(neck & ~((xx > 145) & (xx < 175)) & (yy < 63))

    # legs: waist of the trousers continues up under the hem
    # the trouser waist under the hem: as wide as the hips, rounded at the top corners
    waist = (yy >= 150) & (yy < HEM_Y + 2) & (np.abs(xx - 159.5) <= 40 - np.clip(170 - yy, 0, 20) * 0.8)
    legs_m = legs_vis | waist
    lfill = legs_m & ~(legs_vis & (yy > HEM_Y + 3))
    lknown = legs_vis & (yy > HEM_Y + 3) & (yy < 240) & plain
    legs_rgb = inpaint(rgb, lfill, lknown, 9)

    # arms: the shoulder top (towards the collar) is shared with the torso, fade it in the arm
    def arm_alpha(m, sh):
        d = np.sqrt((xx - J['neck'][0]) ** 2 * 1.0 + 0 * yy)
        al = m.astype(np.float32)
        # fade the part of the arm that lies inward of the shoulder brad and above it
        inward = np.abs(xx - J['neck'][0]) < np.abs(sh[0] - J['neck'][0])
        up = yy < sh[1]
        f = np.clip((np.abs(xx - J['neck'][0]) - (abs(sh[0] - J['neck'][0]) - 10)) / 10, 0, 1)
        al = np.where(inward & up, al * f, al)
        return al

    aR = arm_alpha(armR, J['shR']); aL = arm_alpha(armL, J['shL'])
    head_a = soft_bottom(head.astype(np.float32), 61, 65)
    layers = {
        'legs': (legs_rgb, legs_m.astype(np.float32)),
        'torso': (torso_rgb, torso_m.astype(np.float32)),
        'head': (rgb.copy(), head_a),
        'armR': (rgb.copy(), aR),
        'armL': (rgb.copy(), aL),
    }
    # brads sprites (taken from the master, soft round mask)
    brad_meta = {}
    for j, r in BRADS.items():
        c = refine_brad(rgb, a, J[j], 5)
        brad_meta[j] = [float(c[0]), float(c[1]), r]
    # hand swap drawings: fists from another painting of him (poet.14.muse-dance/cards-2)
    src = cv2.imread(os.path.join(ROOT, 'shots/kits/cut', FIST_SRC + '.webp'), cv2.IMREAD_UNCHANGED)
    for side, (x0, y0, x1, y1), base, top in FISTS:
        crop = src[y0:y1, x0:x1].copy()
        cv2.imwrite(os.path.join(out_dir, f'fist_{side}.png'), crop)
        brad_meta['fist' + side] = [base[0] - x0, base[1] - y0, top[0] - x0, top[1] - y0]
    for name, (c, al) in layers.items():
        rgba = np.dstack([np.clip(c, 0, 255), np.clip(al * 255, 0, 255)]).astype(np.uint8)
        cv2.imwrite(os.path.join(out_dir, f'layer_{name}.png'), rgba)
        # cut edges: where this layer ends inside the painted figure (not on its paper edge)
        lm = (al > 0.5).astype(np.uint8)
        dL = cv2.distanceTransform(np.pad(lm, 1), cv2.DIST_L2, 3)[1:-1, 1:-1]
        dM = cv2.distanceTransform(np.pad(fig.astype(np.uint8), 1), cv2.DIST_L2, 3)[1:-1, 1:-1]
        cut = (lm > 0) & (dL < 2.6) & (dM > dL + 2.0)
        cutf = cv2.GaussianBlur(cut.astype(np.float32), (0, 0), 0.45)
        cv2.imwrite(os.path.join(out_dir, f'cut_{name}.png'), np.clip(cutf * 255, 0, 255).astype(np.uint8))
    cv2.imwrite(os.path.join(out_dir, 'master.png'), im.astype(np.uint8))
    json.dump({'master': MASTER_ID, 'brads': brad_meta, 'joints': {k: v.tolist() for k, v in J.items()}},
              open(os.path.join(out_dir, 'rig.json'), 'w'), indent=1)
    return out_dir


def plain_fabric(rgb, fig):
    """Pixels usable as a source for completing hidden fabric: dark cloth, not piping,
    brass, skin or the paper edge."""
    b, g, r = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    dark = (r < 70) & (g < 70) & (b < 70) & (r < g + 25)
    er = cv2.erode(fig.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    return dark & er


def soft_bottom(al, y0, y1):
    H = al.shape[0]
    f = np.clip((y1 - np.arange(H)) / (y1 - y0), 0, 1)[:, None]
    return al * f


def inpaint(rgb, fill, known, r):
    """Fill `fill` from `known` pixels only (others are treated as unknown too)."""
    img = rgb.copy()
    m = (~known).astype(np.uint8)
    src = np.clip(img, 0, 255).astype(np.uint8)
    src[m.astype(bool)] = 0
    out = cv2.inpaint(src, m * 255, r, cv2.INPAINT_TELEA).astype(np.float32)
    img[fill] = out[fill]
    return img


def refine_brad(rgb, a, c, win):
    x0, y0 = int(c[0]) - 12, int(c[1]) - 12
    patch = rgb[y0:y0 + 25, x0:x0 + 25]
    b, g, r = patch[..., 0], patch[..., 1], patch[..., 2]
    gold = ((r > 150) & (g > 110) & (b < 120)).astype(np.float32)
    if gold.sum() < 10:
        return c
    ys, xs = np.nonzero(gold)
    return np.array([x0 + xs.mean(), y0 + ys.mean()])


# ----------------------------------------------------------------- runtime rig
class Rig:
    LAYER_BONES = {
        'legs': {'pelvis': [('waist', 'crotch'), ('hipR', 'hipL')],
                 'thighR': [('hipR', 'knR')], 'shinR': [('knR', 'anR')], 'footR': [('anR', 'toR')],
                 'thighL': [('hipL', 'knL')], 'shinL': [('knL', 'anL')], 'footL': [('anL', 'toL')]},
        'torso': None,  # weights by height (pelvis at the hem, chest above)
        'head': {'head': [('headpiv', 'headtop')]},
        'armR': {'chest': [('neck', 'shR')], 'uarmR': [('shR', 'elR')], 'farmR': [('elR', 'wrR')], 'handR': [('wrR', 'tipR')]},
        'armL': {'chest': [('neck', 'shL')], 'uarmL': [('shL', 'elL')], 'farmL': [('elL', 'wrL')], 'handL': [('wrL', 'tipL')]},
    }
    TAU = {'legs': 3.2, 'armR': 2.6, 'armL': 2.6, 'head': 1.0}
    ORDER = ['legs', 'torso', 'head', 'armR', 'armL']
    DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
             'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}

    def __init__(self, rig_dir=None, step=2.0):
        rig_dir = rig_dir or os.path.join(HERE, 'rig')
        meta = json.load(open(os.path.join(rig_dir, 'rig.json')))
        self.brads = {k: v for k, v in meta['brads'].items() if not k.startswith('fist')}
        self.fist_meta = {k[-1]: v for k, v in meta['brads'].items() if k.startswith('fist')}
        self.fist = {}
        for side in 'RL':
            f = cv2.imread(os.path.join(rig_dir, f'fist_{side}.png'), cv2.IMREAD_UNCHANGED).astype(np.float32)
            f[..., :3] *= f[..., 3:] / 255.
            self.fist[side] = f
        self.master = cv2.imread(os.path.join(rig_dir, 'master.png'), cv2.IMREAD_UNCHANGED)
        self.tex = {}
        self.cut = {}
        self.mesh = {}
        for name in self.ORDER:
            L = cv2.imread(os.path.join(rig_dir, f'layer_{name}.png'), cv2.IMREAD_UNCHANGED).astype(np.float32)
            Lu = cv2.resize(L, None, fx=U, fy=U, interpolation=cv2.INTER_CUBIC)
            Lu = np.clip(Lu, 0, 255)
            pm = Lu.copy(); pm[..., :3] *= pm[..., 3:] / 255.   # premultiplied
            self.tex[name] = pm
            if name.startswith('arm'):
                side = name[-1]
                xx = np.arange(pm.shape[1]) / U
                keep = np.clip((xx - HAND_CUT['R']) / 1.5, 0, 1) if side == 'R' else np.clip((HAND_CUT['L'] - xx) / 1.5, 0, 1)
                self.tex[name + '_nohand'] = pm * keep[None, :, None]
            cut = cv2.imread(os.path.join(rig_dir, f'cut_{name}.png'), 0).astype(np.float32) / 255.
            self.cut[name] = cv2.resize(cut, None, fx=U, fy=U, interpolation=cv2.INTER_LINEAR)
            self.mesh[name] = self._mesh(name, L[..., 3] > 8, step)
        # brad sprites
        mu = cv2.resize(self.master.astype(np.float32), None, fx=U, fy=U, interpolation=cv2.INTER_CUBIC)
        self.brad_tex = {}
        for j, (x, y, r) in self.brads.items():
            R = int(math.ceil(r * U)) + 2
            cx, cy = x * U, y * U
            M = np.float32([[1, 0, -(cx - R)], [0, 1, -(cy - R)]])
            spr = cv2.warpAffine(mu, M, (2 * R + 1, 2 * R + 1), flags=cv2.INTER_LINEAR)
            yy, xx = np.mgrid[0:2 * R + 1, 0:2 * R + 1]
            d = np.sqrt((xx - R) ** 2 + (yy - R) ** 2) / U
            m = np.clip((r - d) / 1.5 + 0.5, 0, 1)
            spr[..., 3] = np.clip(spr[..., 3], 0, 255) * m
            spr[..., :3] *= spr[..., 3:] / 255.
            self.brad_tex[j] = (spr, R)

    # mesh: grid vertices over the layer alpha, weights per bone
    def _mesh(self, name, mask, step):
        H, W = mask.shape
        md = cv2.dilate(mask.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        xs = np.arange(0, W + step, step); ys = np.arange(0, H + step, step)
        gx, gy = np.meshgrid(xs, ys)
        V = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float64)
        nx = len(xs)
        tris = []
        for j in range(len(ys) - 1):
            for i in range(len(xs) - 1):
                x0, y0 = xs[i], ys[j]
                sub = md[int(y0):int(min(H, y0 + step + 1)), int(x0):int(min(W, x0 + step + 1))]
                if sub.size and sub.any():
                    a = j * nx + i; b = a + 1; c = a + nx; d = c + 1
                    tris.append((a, b, d)); tris.append((a, d, c))
        tris = np.array(tris)
        used = np.unique(tris)
        remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
        V = V[used]; tris = remap[tris]
        # weights
        if name == 'torso':
            t = np.clip((V[:, 1] - 128) / (176 - 128), 0, 1)
            t = t * t * (3 - 2 * t)
            # the shoulder cap partly follows the upper arm, so a raised arm lifts the deltoid
            # instead of leaving a fixed shoulder pad under it
            wa = []
            for sd in 'RL':
                d = np.linalg.norm(V - J['sh' + sd], axis=1)
                lat = np.clip((np.abs(V[:, 0] - 159.5) - (abs(J['sh' + sd][0] - 159.5) - 12)) / 12, 0, 1)
                wa.append(0.6 * np.clip(1 - d / 20, 0, 1) * lat)
            wa = np.stack(wa, 1)
            rest = 1 - wa.sum(1, keepdims=True)
            names = ['chest', 'pelvis', 'uarmR', 'uarmL']
            Wt = np.hstack([rest * (1 - t)[:, None], rest * t[:, None], wa])
        else:
            spec = self.LAYER_BONES[name]
            names = list(spec)
            D = []
            for b in names:
                d = np.min([seg_dist(V, J[p], J[q])[0] for p, q in spec[b]], axis=0)
                D.append(d)
            D = np.stack(D, 1)
            tau = self.TAU[name]
            Wt = np.exp(-(D - D.min(1, keepdims=True)) / tau)
            Wt /= Wt.sum(1, keepdims=True)
        # draw order: proximal first, distal last (the forearm folds over the upper arm)
        depth = (Wt @ np.array([self.DEPTH[b] for b in names], float))
        tdepth = depth[tris].mean(1)
        order = np.argsort(tdepth, kind='stable')
        Tt = tris[order]
        av = mask[np.clip(V[:, 1].astype(int), 0, H - 1), np.clip(V[:, 0].astype(int), 0, W - 1)]
        opaque = av[Tt].all(1)
        return {'V': V, 'T': Tt, 'W': Wt, 'names': names, 'G': np.round(tdepth[order] * 2).astype(int), 'opaque': opaque}

    # ------------------------------------------------------------ posing
    def transforms(self, P):
        """P: dict of params (see pose.py).  Returns bone -> 2x3 affine in master px."""
        A = {}
        posed = {}

        def aff(pivot_rest, pivot_new, rot, ax_dir=None, sa=1.0, sp=1.0):
            c, s = math.cos(rot), math.sin(rot)
            R = np.array([[c, -s], [s, c]])
            S = np.eye(2)
            if ax_dir is not None:
                u = ax_dir / np.linalg.norm(ax_dir); n = np.array([-u[1], u[0]])
                S = sa * np.outer(u, u) + sp * np.outer(n, n)
            M = R @ S
            t = pivot_new - M @ pivot_rest
            return np.hstack([M, t[:, None]])

        def app(M, p):
            return M[:, :2] @ p + M[:, 2]

        root = J['midhip'] + np.array(P.get('root_off', (0., 0.)))
        A['pelvis'] = aff(J['midhip'], root, P.get('pelvis', 0.), np.array([1., 0.]), P.get('hipw', 1.), 1.)
        sp = J['neck'] - J['midhip']
        A['chest'] = aff(J['midhip'], root, P.get('chest', 0.), sp, P.get('torso_len', 1.), P.get('shw', 1.))
        hp = app(A['chest'], J['headpiv'])
        A['head'] = aff(J['headpiv'], hp, P.get('head', 0.) + P.get('chest', 0.))
        for side in 'RL':
            sh = app(A['chest'], J['sh' + side])
            ua = J['el' + side] - J['sh' + side]
            A['uarm' + side] = aff(J['sh' + side], sh, P.get('uarm' + side, 0.), ua, P.get('luarm' + side, 1.))
            el = app(A['uarm' + side], J['el' + side])
            fa = J['wr' + side] - J['el' + side]
            A['farm' + side] = aff(J['el' + side], el, P.get('farm' + side, 0.), fa, P.get('lfarm' + side, 1.))
            wr = app(A['farm' + side], J['wr' + side])
            A['hand' + side] = aff(J['wr' + side], wr, P.get('hand' + side, P.get('farm' + side, 0.)))
            hip = app(A['pelvis'], J['hip' + side])
            th = J['kn' + side] - J['hip' + side]
            A['thigh' + side] = aff(J['hip' + side], hip, P.get('thigh' + side, 0.), th, P.get('lthigh' + side, 1.))
            kn = app(A['thigh' + side], J['kn' + side])
            sn = J['an' + side] - J['kn' + side]
            A['shin' + side] = aff(J['kn' + side], kn, P.get('shin' + side, 0.), sn, P.get('lshin' + side, 1.))
            an = app(A['shin' + side], J['an' + side])
            A['foot' + side] = aff(J['an' + side], an, P.get('foot' + side, P.get('shin' + side, 0.)))
        return A

    def joint_pos(self, A):
        app = lambda M, p: M[:, :2] @ p + M[:, 2]
        out = {}
        for j, b in [('shR', 'uarmR'), ('shL', 'uarmL'), ('elR', 'farmR'), ('elL', 'farmL'), ('hipR', 'thighR'),
                     ('hipL', 'thighL'), ('knR', 'shinR'), ('knL', 'shinL'), ('anR', 'footR'), ('anL', 'footL'),
                     ('wrR', 'handR'), ('wrL', 'handL'), ('headpiv', 'head'), ('neck', 'chest'), ('midhip', 'pelvis'),
                     ('headtop', 'head'), ('toR', 'footR'), ('toL', 'footL'), ('tipR', 'handR'), ('tipL', 'handL')]:
            out[j] = app(A[b], J[j])
        return out

    def render(self, P, G, size, ss=2, border=True, head_yaw=0.0, hands=None):
        """Render only the figure's bounding window, then place it on the full canvas."""
        Wo, Ho = size
        A = self.transforms(P)
        pts = []
        for name in self.ORDER:
            m = self.mesh[name]; V = m['V']
            Vp = np.zeros_like(V)
            for k, b in enumerate(m['names']):
                Mb = A[b]; Vp += m['W'][:, k:k + 1] * (V @ Mb[:, :2].T + Mb[:, 2])
            pts.append(Vp @ G[:, :2].T + G[:, 2])
        pts = np.vstack(pts)
        sc = math.sqrt(abs(np.linalg.det(G[:, :2])))
        mg = int(30 * sc) + 8
        x0 = max(0, int(pts[:, 0].min()) - mg); y0 = max(0, int(pts[:, 1].min()) - mg)
        x1 = min(Wo, int(pts[:, 0].max()) + mg); y1 = min(Ho, int(pts[:, 1].max()) + mg)
        out = np.zeros((Ho, Wo, 4), np.uint8)
        if x1 <= x0 or y1 <= y0:
            return out, self.joint_pos(A)
        G2 = G.copy(); G2[:, 2] -= (x0, y0)
        img, jp = self._render(P, G2, (x1 - x0, y1 - y0), ss, border, head_yaw, hands)
        out[y0:y1, x0:x1] = img
        return out, jp

    def _render(self, P, G, size, ss=2, border=True, head_yaw=0.0, hands=None):
        """G: global 2x3 similarity master px -> output px.  size=(W,H).  Returns RGBA uint8."""
        Wo, Ho = size
        A = self.transforms(P)
        G2 = np.vstack([G, [0, 0, 1]]); S2 = np.diag([ss, ss, 1.])
        Gs = (S2 @ G2)[:2]
        acc = np.zeros((Ho * ss, Wo * ss, 4), np.float32)
        tanned = np.zeros((Ho * ss, Wo * ss), np.float32)
        jp = self.joint_pos(A)
        for name in self.ORDER:
            m = self.mesh[name]
            V = m['V']
            Vr = V
            if name == 'head' and abs(head_yaw) > 1e-3:
                Vr = V  # warp applies to texture lookup: see below
            Vp = np.zeros_like(V)
            for k, b in enumerate(m['names']):
                Mb = A[b]
                Vp += m['W'][:, k:k + 1] * (V @ Mb[:, :2].T + Mb[:, 2])
            Vo = Vp @ Gs[:, :2].T + Gs[:, 2]
            UV = V * U
            if name == 'head' and abs(head_yaw) > 1e-3:
                UV = yaw_lookup(V, head_yaw) * U
            # triangles stretched far past their painted size (the empty wedge of the crotch when
            # the legs spread) would smear the paper edge across the gap: they are dropped
            T = m['T']
            sc_o = math.sqrt(abs(np.linalg.det(Gs[:, :2])))
            er = np.stack([np.linalg.norm(V[T[:, i]] - V[T[:, (i + 1) % 3]], axis=1) for i in range(3)], 1)
            eo = np.stack([np.linalg.norm(Vo[T[:, i]] - Vo[T[:, (i + 1) % 3]], axis=1) for i in range(3)], 1)
            stretched = (eo.max(1) / (sc_o * er.max(1) + 1e-6)) > 1.8
            keep = ~(stretched & ~m['opaque'])
            mx, my, cov = raster_fast(Vo, UV, T[keep], m['G'][keep], Wo * ss, Ho * ss, self.tex[name][..., 3])
            hands = hands or {}
            texname = name
            if name.startswith('arm') and hands.get(name[-1]) in ('fist', 'none'):
                texname = name + '_nohand'
                if hands.get(name[-1]) == 'fist':
                    acc = over(acc, self._fist(name[-1], A, Gs, Wo * ss, Ho * ss))
            lay = cv2.remap(self.tex[texname], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            lay *= cov[..., None]
            if border:
                # a cut edge that ends up on the silhouette (nothing behind it) gets the paper edge
                cutr = cv2.remap(self.cut[name], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) * cov
                t = np.clip(cutr * (1 - acc[..., 3] / 255.) * 1.2, 0, 1)[..., None]
                la = lay[..., 3:] / 255.
                lay[..., :3] = lay[..., :3] * (1 - t) + BORDER * la * t
                tanned = np.maximum(tanned, t[..., 0] * la[..., 0])
            if name.startswith('arm'):
                # the painting draws a dark contour where a sleeve lies over the jacket
                al = lay[..., 3] / 255.
                rim = cv2.dilate(al, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ss + 1, 2 * ss + 1))) - al
                rim = np.clip(rim, 0, 1) * (acc[..., 3] / 255.) * 0.85
                acc = over(acc, np.dstack([DARK[None, None] * rim[..., None], rim * 255]))
            acc = over(acc, lay)
            # brads that belong on this layer
            for j in {'legs': ['hipR', 'hipL', 'knR', 'knL'], 'armR': ['shR', 'elR'], 'armL': ['shL', 'elL']}.get(name, []):
                spr, R = self.brad_tex[j]
                bx, by, _ = self.brads[j]
                off = np.array([bx, by]) - J[j]
                # brad follows its joint (the offset rides with the distal bone)
                b = {'hipR': 'thighR', 'hipL': 'thighL', 'knR': 'shinR', 'knL': 'shinL', 'shR': 'uarmR', 'shL': 'uarmL',
                     'elR': 'farmR', 'elL': 'farmL'}[j]
                Mb = A[b]
                p = Mb[:, :2] @ np.array([bx, by]) + Mb[:, 2]
                po = Gs[:, :2] @ p + Gs[:, 2]
                sc = math.sqrt(abs(np.linalg.det(Gs[:, :2]))) / U
                # composite in a local window only
                half = int(math.ceil(sc * R)) + 3
                x0, y0 = int(po[0]) - half, int(po[1]) - half
                x1, y1 = x0 + 2 * half + 1, y0 + 2 * half + 1
                cx0, cy0, cx1, cy1 = max(x0, 0), max(y0, 0), min(x1, Wo * ss), min(y1, Ho * ss)
                if cx1 <= cx0 or cy1 <= cy0:
                    continue
                M = np.float32([[sc, 0, po[0] - sc * R - cx0], [0, sc, po[1] - sc * R - cy0]])
                spr_o = cv2.warpAffine(spr, M, (cx1 - cx0, cy1 - cy0), flags=cv2.INTER_LINEAR)
                acc[cy0:cy1, cx0:cx1] = over(acc[cy0:cy1, cx0:cx1], spr_o)
        if border:
            # thin outer lip outside the tanned cut edges, like the painting's outermost light line
            fa = acc[..., 3] / 255.
            lip = cv2.dilate((tanned > 0.3).astype(np.uint8), np.ones((2 * ss + 1, 2 * ss + 1), np.uint8)).astype(np.float32)
            lip = cv2.GaussianBlur(lip, (0, 0), 0.6 * ss) * (1 - fa) * 0.9
            acc[..., :3] += BORDER_OUT * lip[..., None]; acc[..., 3] += 255 * lip
        out = cv2.resize(acc, (Wo, Ho), interpolation=cv2.INTER_AREA)
        rgb = np.where(out[..., 3:] > 0, out[..., :3] / np.maximum(out[..., 3:], 1e-3) * 255., 0)
        return np.dstack([np.clip(rgb, 0, 255), np.clip(out[..., 3], 0, 255)]).astype(np.uint8), jp


def _fist(self, side, A, Gs, W, H):
    """A fist drawing riding the hand bone: wrist base on the wrist, knuckles along the hand."""
    bx, by, tx, ty = self.fist_meta[side]
    Mh = A['hand' + side]
    wr = Mh[:, :2] @ J['wr' + side] + Mh[:, 2]
    tip = Mh[:, :2] @ J['tip' + side] + Mh[:, 2]
    d = tip - wr; d /= np.linalg.norm(d)
    u = np.array([tx - bx, ty - by], float); u /= np.linalg.norm(u)
    rot = math.atan2(d[1], d[0]) - math.atan2(u[1], u[0])
    c, s_ = math.cos(rot), math.sin(rot)
    M = FIST_SCALE * np.array([[c, -s_], [s_, c]])
    base = wr - d * 3.0          # tuck the wrist into the cuff
    t = base - M @ np.array([bx, by])
    Mo = Gs[:, :2] @ M; to = Gs[:, :2] @ t + Gs[:, 2]
    return cv2.warpAffine(self.fist[side], np.hstack([Mo, to[:, None]]).astype(np.float32), (W, H),
                          flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


Rig._fist = _fist


def yaw_lookup(V, yaw):
    """Head turn by sliding the face features inside a fixed head outline (Live2D 'angle X').
    yaw in [-1,1]: positive = face turns to image-right.  Returns source coords for each vertex."""
    cx, cy, rx, ry = 161.0, 34.0, 27.0, 34.0
    dx = (V[:, 0] - cx) / rx; dy = (V[:, 1] - cy) / ry
    r2 = np.clip(1 - dx * dx - dy * dy, 0, 1)
    shift = yaw * 10.0 * r2      # px in master space at the face centre
    S = V.copy(); S[:, 0] = V[:, 0] - shift
    return S


def over(dst, src):
    a = src[..., 3:] / 255.
    return src + dst * (1 - a)


def raster(Vo, UV, T, W, H, alpha=None):
    """Rasterise a deformed mesh into a lookup map.  Where triangles overlap (a fold), a later
    triangle only wins on pixels where its own texel is painted, so the transparent margin
    of the mesh never punches a hole through cloth drawn before it."""
    mx = np.full((H, W), -10, np.float32); my = np.full((H, W), -10, np.float32)
    cov = np.zeros((H, W), np.float32)
    P = Vo[T]; Q = UV[T]
    x0 = np.floor(P[..., 0].min(1)).astype(int); x1 = np.ceil(P[..., 0].max(1)).astype(int)
    y0 = np.floor(P[..., 1].min(1)).astype(int); y1 = np.ceil(P[..., 1].max(1)).astype(int)
    ok = (x1 >= 0) & (y1 >= 0) & (x0 < W) & (y0 < H)
    for i in np.nonzero(ok)[0]:
        a, b, c = P[i]
        xa, xb = max(x0[i], 0), min(x1[i], W - 1); ya, yb = max(y0[i], 0), min(y1[i], H - 1)
        if xb < xa or yb < ya:
            continue
        gx, gy = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        e = -1e-4
        ins = (l1 >= e) & (l2 >= e) & (l3 >= e)
        if not ins.any():
            continue
        q = Q[i]
        u = l1 * q[0, 0] + l2 * q[1, 0] + l3 * q[2, 0]
        v = l1 * q[0, 1] + l2 * q[1, 1] + l3 * q[2, 1]
        sl = (slice(ya, yb + 1), slice(xa, xb + 1))
        if alpha is not None:
            ai = alpha[np.clip(v.astype(int), 0, alpha.shape[0] - 1), np.clip(u.astype(int), 0, alpha.shape[1] - 1)]
            ins &= (ai > 60) | (cov[sl] == 0)
        mx[sl][ins] = u[ins]; my[sl][ins] = v[ins]; cov[sl][ins] = 1
    return mx, my, cov


def raster_fast(Vo, UV, T, groups, W, H, alpha):
    """Same result as raster(), done per depth group with an ID buffer: each group's
    triangles are filled (OpenCV) with their index, the texture coordinate of every pixel
    comes from its triangle's affine map, and a later group only replaces pixels where its
    own texel is painted (or nothing was there)."""
    mx = np.full((H, W), -10, np.float32); my = np.full((H, W), -10, np.float32)
    cov = np.zeros((H, W), np.float32)
    P = Vo[T]; Q = UV[T]
    # per-triangle affine out(x,y,1) -> uv
    X = np.concatenate([P, np.ones(P.shape[:2] + (1,))], 2)       # N,3,3
    det = np.linalg.det(X)
    good = np.abs(det) > 1e-9
    Minv = np.zeros_like(X); Minv[good] = np.linalg.inv(X[good])
    Mu = np.einsum('nij,njk->nik', Minv, Q)                          # N,3,2 : [x y 1] @ Mu = uv
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


def paper_edge(out, scale):
    """Give every silhouette edge the painting's paper edge, but only where the
    figure's own pixels don't already carry it (new edges made by moving parts)."""
    a = out[..., 3] / 255.
    rgb = out[..., :3] / np.maximum(a[..., None], 1e-3)
    w = max(1, int(round(1.1 * scale)))
    fig = a > 0.5
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * w + 1, 2 * w + 1))
    inner = fig & ~cv2.erode(fig.astype(np.uint8), k).astype(bool)
    tanlike = inner & (np.linalg.norm(rgb - BORDER, axis=2) < 55)
    has = cv2.dilate(tanlike.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4 * w + 1, 4 * w + 1))) > 0
    ring_w = max(1, int(round(1.6 * scale)))
    kr = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ring_w + 1, 2 * ring_w + 1))
    grown = cv2.dilate(fig.astype(np.uint8), kr) > 0
    need = inner & ~has   # figure edge pixels lacking the paper edge
    near_need = cv2.dilate(need.astype(np.uint8), kr) > 0
    ring = grown & ~fig & near_need
    # also paint the edge band itself (the cut fabric gets a tan rim like the painting)
    band = need
    col = np.zeros_like(out)
    col[..., :3] = BORDER; col[..., 3] = 255
    res = out.copy()
    ring_f = cv2.GaussianBlur(ring.astype(np.float32), (0, 0), 0.6)
    ring_f = np.clip(ring_f * (1 - a), 0, 1)
    res = res + col * ring_f[..., None]
    bf = band.astype(np.float32) * 0.8
    res[..., :3] = res[..., :3] * (1 - bf[..., None]) + BORDER * (res[..., 3:] / 255.) * bf[..., None]
    res[..., 3] = np.clip(res[..., 3], 0, 255)
    return res


if __name__ == '__main__':
    print(build())
