"""Render one arena frame from its clip, and measure what is on screen.

No browser: the clip's draw list is composited here with PIL, one layer per
card, so every measurement is about pixels that will actually be seen.

    from frame import load_clip, render, probe, packet

The man's rig draws 15 cards per frame in a fixed order (see draw_man() in
bolas/compile_vignette.py). ROLES names them. The skeleton is recovered from
the bone matrices, because each bone card maps its pivot onto joint A and its
socket onto joint B exactly.
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd

import brads

HERE = os.path.dirname(os.path.abspath(__file__))
ARENA = os.path.normpath(os.path.join(HERE, '..'))
W, H = 1920, 1080
BG = (23, 25, 31)

ROLES = ['uarm.far', 'farm.far', 'hand.far', 'thigh.far', 'shin.far', 'boot.far',
         'pelvis', 'torso', 'head', 'thigh.near', 'shin.near', 'boot.near',
         'uarm.near', 'farm.near', 'hand.near']

# The compiler's own pivots/sockets per card id (card px), used to recover joints.
COMPILER_PINS = {'man.uarm': ((39, 10), (39, 158)), 'man.farm': ((35, 10), (35, 148)),
                 'man.thigh': ((52, 10), (52, 244)), 'man.shin': ((43, 10), (43, 238))}

# parent socket <-> child socket. A joint looks joined when these two land on one point.
JOINTS = [
    ('waist', 'pelvis', 'waist', 'torso', 'hip'),
    ('neck', 'torso', 'neck', 'head', 'neck'),
    ('shoulder.near', 'torso', 'shoulder', 'uarm.near', 'A'),
    ('shoulder.far', 'torso', 'shoulder', 'uarm.far', 'A'),
    ('elbow.near', 'uarm.near', 'B', 'farm.near', 'A'),
    ('elbow.far', 'uarm.far', 'B', 'farm.far', 'A'),
    ('wrist.near', 'farm.near', 'B', 'hand.near', 'wrist'),
    ('wrist.far', 'farm.far', 'B', 'hand.far', 'wrist'),
    ('hip.near', 'pelvis', 'hip', 'thigh.near', 'A'),
    ('hip.far', 'pelvis', 'hip', 'thigh.far', 'A'),
    ('knee.near', 'thigh.near', 'B', 'shin.near', 'A'),
    ('knee.far', 'thigh.far', 'B', 'shin.far', 'A'),
    ('ankle.near', 'shin.near', 'B', 'boot.near', 'ankle'),
    ('ankle.far', 'shin.far', 'B', 'boot.far', 'ankle'),
]


def kind_of(role):
    return role.split('.')[0]


def load_clip(act, skin='man'):
    return json.load(open(os.path.join(ARENA, 'clips', f'{act}__{skin}.json')))


def img_path(clip, iid):
    return os.path.normpath(os.path.join(ARENA, clip['images'][iid]))


def M_of(m):
    return np.array([[m[0], m[2]], [m[1], m[3]]], float), np.array([m[4], m[5]], float)


def apply(m, p):
    M, t = M_of(m)
    return M @ np.asarray(p, float) + t


def actors(clip, f):
    """Number of 15-card man rigs on frame f (0 when a whole-pose picture replaces the rig)."""
    n = sum(1 for o in clip['frames'][f]['draw'] if o['t'] == 'img')
    return n // len(ROLES) if n and n % len(ROLES) == 0 else 0


def pieces(clip, f, actor=0):
    """Card ops of one actor on frame f with roles, or None when it is not the 15-card man rig."""
    ops = [o for o in clip['frames'][f]['draw'] if o['t'] == 'img']
    if actor >= actors(clip, f):
        return None
    ops = ops[actor * len(ROLES):(actor + 1) * len(ROLES)]
    return [dict(o, role=r, actor=actor, path=img_path(clip, o['id'])) for o, r in zip(ops, ROLES)]


def skeleton(cards):
    """Joints in screen px, recovered from the compiler's bone matrices."""
    J = {}
    for c in cards:
        k = kind_of(c['role'])
        side = c['role'].split('.')[-1]
        if c['id'] in COMPILER_PINS:
            a, b = COMPILER_PINS[c['id']]
            names = {'uarm': ('shoulder', 'elbow'), 'farm': ('elbow', 'wrist'),
                     'thigh': ('hip', 'knee'), 'shin': ('knee', 'ankle')}[k]
            J[f'{names[0]}.{side}'] = apply(c['m'], a)
            J[f'{names[1]}.{side}'] = apply(c['m'], b)
        elif k == 'head':
            J['neck'] = apply(c['m'], (107, 257))
        elif k == 'torso':
            J['pelvis'] = apply(c['m'], (110, 308))
    return J


def layer(c):
    im = Image.open(c['path']).convert('RGBA')
    M, t = M_of(c['m'])
    Mi = np.linalg.inv(M)
    ti = -Mi @ t
    return im.transform((W, H), Image.AFFINE, (Mi[0, 0], Mi[0, 1], ti[0], Mi[1, 0], Mi[1, 1], ti[1]),
                        resample=Image.BICUBIC)


def _poly(d, pts, fill, stroke='#1a120b'):
    d.polygon([tuple(p) for p in pts], fill=fill, outline=stroke)


def render(clip, f, cards=None, props=None):
    """props: replaces the clip's own prop rectangles (see bank.Bank.props). A held prop
    is drawn in front of the torso and behind the near arm, as a carried box is."""
    """-> (RGB image, {role: alpha mask}, floor_y)"""
    frame = clip['frames'][f]
    canvas = Image.new('RGBA', (W, H), BG + (255,))
    d = ImageDraw.Draw(canvas)
    floor = None
    masks = {}
    cards = cards if cards is not None else pieces(clip, f)
    roles = {id(o): None for o in frame['draw']}
    queue = list(cards or [])
    for o in frame['draw']:
        if o['t'] == 'floor':
            floor = o['y']
            d.line([0, o['y'], W, o['y']], fill=(120, 130, 145), width=2)
        elif o['t'] == 'poly':
            if props is None:
                d.polygon([tuple(p) for p in o['pts']], fill=o.get('fill', '#888'), outline=o.get('stroke'))
            else:
                for pr in props:
                    if not pr.get('held'):
                        for q in pr['polys']:
                            _poly(d, q['pts'], q['fill'])
        elif o['t'] == 'shadow':
            sh = Image.new('L', (W, H), 0)
            ImageDraw.Draw(sh).ellipse([o['x'] - o['rx'], o['y'] - o['rx'] * 0.18, o['x'] + o['rx'], o['y'] + o['rx'] * 0.18], fill=int(255 * o['a'] * 0.6))
            sh = sh.filter(__import__('PIL.ImageFilter', fromlist=['GaussianBlur']).GaussianBlur(6))
            canvas.paste((0, 0, 0, 255), (0, 0), sh)
        elif o['t'] == 'img' and queue:
            c = queue.pop(0)
            if props and c['role'] == 'uarm.near' and c.get('actor', 0) == 0:
                dd = ImageDraw.Draw(canvas)
                for pr in props:
                    if pr.get('held'):
                        for q in pr['polys']:
                            _poly(dd, q['pts'], q['fill'])
            L = layer(c)
            canvas.alpha_composite(L)
            masks[(c.get('actor', 0), c['role'])] = np.asarray(L)[:, :, 3] > 100
    return canvas.convert('RGB'), masks, floor


ALIAS = {'waist': 'A', 'wrist': 'A', 'ankle': 'A'}


def sockets_on_screen(cards):
    S = {}
    for c in cards:
        if 'part' in c:
            # a library part: sockets from its contract, constructed or registered
            sk = dict(c['part']['sockets'])
            for k, v in ALIAS.items():
                if k not in sk and v in sk:
                    sk[k] = sk[v]
            for name, p in sk.items():
                S[(c['role'], name)] = (apply(c['m'], p), False)
            continue
        r = brads.read(c['path'], kind_of(c['role']))
        for name, p in r['sockets'].items():
            S[(c['role'], name)] = (apply(c['m'], p), name in r['guessed'])
    return S


def _sock(S, role, name):
    if name == 'hip' and role == 'pelvis':
        return None
    return S.get((role, name))


_PXCM = {}


def px_per_cm(clip):
    """Screen px per cm, from the skeleton itself: the longest the leg gets over the
    clip (foreshortening only shortens) against the model sheet's thigh + shin, 87cm.
    The clip's own `cast.cm_px` is not used: it is 400/170 whatever the camera, and
    on ACT-010 it is 2.35 where the skeleton is drawn at about 4.4."""
    key = clip['id']
    if key not in _PXCM:
        L = []
        for f in range(0, len(clip['frames']), 4):
            cs = pieces(clip, f)
            if not cs:
                continue
            J = skeleton(cs)
            for s in ('near', 'far'):
                L.append(np.linalg.norm(J[f'hip.{s}'] - J[f'knee.{s}']) + np.linalg.norm(J[f'knee.{s}'] - J[f'ankle.{s}']))
        _PXCM[key] = float(np.percentile(L, 95)) / 87.0 if L else 4.0
    return _PXCM[key]


def probe(clip, f, cards, masks, floor):
    """Measurements on the rendered frame for the actor `cards` belong to."""
    px_cm = px_per_cm(clip)
    who = cards[0].get('actor', 0)
    masks = {r: m for (a, r), m in masks.items() if a == who}
    S = sockets_on_screen(cards)
    out = {'frame': f, 'beat': clip['frames'][f].get('beat'), 'joints': {}, 'cards': {}, 'figure': {}}
    for name, pr, pn, cr, cn in JOINTS:
        child = S.get((cr, cn))
        if pr == 'pelvis' and pn == 'hip':
            cands = [S.get(('pelvis', 'hip_L')), S.get(('pelvis', 'hip_R'))]
            cands = [c for c in cands if c]
            if len(cands) == 2:
                # In profile both thighs hang from between the two drawn hip brads.
                cands.append(((cands[0][0] + cands[1][0]) / 2, cands[0][1] or cands[1][1]))
            parent = min(cands, key=lambda c: np.linalg.norm(c[0] - child[0])) if cands and child else None
        else:
            parent = S.get((pr, pn))
        if not parent or not child:
            continue
        gap = float(np.linalg.norm(parent[0] - child[0]))
        touching = bool((nd.binary_dilation(masks[pr], iterations=2) & masks[cr]).any()) if pr in masks and cr in masks else None
        out['joints'][name] = {'brad_gap_px': round(gap, 1), 'brad_gap_cm': round(gap / px_cm, 1),
                               'parent': [round(v, 1) for v in parent[0]], 'child': [round(v, 1) for v in child[0]],
                               'guessed': bool(parent[1] or child[1]), 'cards_touch': touching}
    for c in cards:
        M, _ = M_of(c['m'])
        sv = np.linalg.svd(M, compute_uv=False)
        out['cards'][c['role']] = {'id': c['id'], 'scale': round(float(math.sqrt(abs(np.linalg.det(M)))), 3),
                                   'anisotropy': round(float(sv[0] / max(sv[1], 1e-6)), 2)}
    union = np.zeros((H, W), bool)
    for m in masks.values():
        union |= m
    lab, n = nd.label(nd.binary_dilation(union, iterations=1))
    sizes = sorted(np.bincount(lab.ravel())[1:], reverse=True)
    ys, xs = np.nonzero(union)
    fig_h = int(ys.max() - ys.min()) if len(ys) else 0
    head = masks.get('head')
    head_h = int(np.ptp(np.nonzero(head)[0])) if head is not None and head.any() else 0
    boots = [masks[r] for r in ('boot.near', 'boot.far') if r in masks]
    low = [int(np.nonzero(b)[0].max()) for b in boots if b.any()]
    torso_id, head_id = cards[ROLES.index('torso')]['id'], cards[ROLES.index('head')]['id']
    out['figure'] = {
        'pieces_detached': int(sum(1 for s in sizes[1:] if s > 200)),
        'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
        'head_to_figure_height': round(head_h / max(fig_h, 1), 2),
        'boot_lowest_minus_floor_px': [lo - floor for lo in low] if floor is not None else None,
        'views': {'torso': torso_id.split('.')[-1], 'head': head_id.split('.')[-1]},
        'view_mismatch': ('front' in torso_id) != ('front' in head_id),
    }
    return out, S


def _font(n):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, n)
    return ImageFont.load_default()


def packet(img, masks, report, S, out_dir, tag, J=None, tol_cm=2.0):
    """Write the four images a critic looks at: plain, overlay, joint loupes, silhouette."""
    os.makedirs(out_dir, exist_ok=True)
    every = np.zeros((H, W), bool)
    for m in masks.values():
        every |= m
    ys, xs = np.nonzero(every)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    pad = 60
    box = (max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad))
    plain = img.crop(box)
    plain.save(os.path.join(out_dir, f'{tag}_plain.png'))

    ov = img.copy().convert('RGB')
    d = ImageDraw.Draw(ov)
    for name, j in report['joints'].items():
        p, c = j['parent'], j['child']
        bad = j['brad_gap_cm'] > tol_cm
        d.line([tuple(p), tuple(c)], fill=(255, 40, 40) if bad else (80, 255, 80), width=3)
        for q, col in ((p, (0, 220, 255)), (c, (255, 0, 255))):
            r = 7
            if j['guessed']:
                d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], outline=col, width=2)
            else:
                d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)
        if bad:
            d.text((c[0] + 9, c[1] - 7), f"{name} {j['brad_gap_cm']}cm", fill=(255, 230, 0), font=_font(16))
    for name, q in (J or {}).items():
        d.rectangle([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], outline=(120, 255, 120))
    ov.crop(box).save(os.path.join(out_dir, f'{tag}_overlay.png'))

    names = list(report['joints'])
    cell, cols = 220, 7
    rows = (len(names) + cols - 1) // cols
    L = Image.new('RGB', (cols * cell, rows * (cell + 24)), (40, 40, 40))
    dl = ImageDraw.Draw(L)
    for i, name in enumerate(names):
        c = report['joints'][name]['child']
        crop = img.crop((int(c[0]) - 55, int(c[1]) - 55, int(c[0]) + 55, int(c[1]) + 55)).resize((cell, cell), Image.LANCZOS)
        cx, cy = (i % cols) * cell, (i // cols) * (cell + 24)
        L.paste(crop, (cx, cy + 24))
        j = report['joints'][name]
        dl.text((cx + 4, cy + 4), f"{name} {j['brad_gap_cm']}cm{' ?' if j['guessed'] else ''}", fill=(255, 230, 0) if j['brad_gap_cm'] > tol_cm else (200, 255, 200), font=_font(14))
    L.save(os.path.join(out_dir, f'{tag}_loupes.png'))

    union = np.zeros((H, W), bool)
    for (a, r), m in masks.items():
        union |= m
    sil = Image.fromarray(np.where(union, 0, 255).astype(np.uint8)).crop(box)
    sil.save(os.path.join(out_dir, f'{tag}_silhouette.png'))
    return box
