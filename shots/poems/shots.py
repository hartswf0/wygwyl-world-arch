"""Render every shot of every poem with the card rig: the real puppets, posed from the bank.

    python3 shots/poems/shots.py [NN ...]    # breakdown/NN.json -> out/NN/<shot>.jpg + out/NN.board.jpg

A shot's bodies come from the pose library (poses.json: real Crash Lab poses by class),
turned to the view the breakdown asks for (the EX always from behind), placed by its
position (x across, depth, level), with its expression, its hands (shape, what they hold,
in a pocket, or missing) and its props, and drawn by cardrig.CardRig like any take.
Casting: POET -> the poet, EX -> the man, YOUNG_POET and GHOST_CHILD -> Dot (stand-in
until their own cards exist), everyone else alternates man and poet.
"""
import json, math, os, sys, textwrap, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'arena', 'puppet'))
import p3d, cardrig, propcards

POSES = json.load(open(os.path.join(HERE, 'poses.json')))
BD = os.path.join(HERE, 'breakdown')
OUT = os.path.join(HERE, 'out')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FM = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
PAPER = (250, 247, 240)
INK = (26, 23, 20)
DIM = (120, 110, 98)

VIEW_DEG = {'front': 0, 'threequarter': 40, 'profile': 90, 'threequarter_back': 140, 'back': 180}
POSE_ALIAS = {'turn': 'stand', 'climb': 'reach', 'point': 'reach', 'hug': 'reach', 'throw': 'reach', 'step': 'walk',
              'jump': 'float', 'tumble': 'fall', 'drift': 'float', 'search': 'walk', 'read': 'stand', 'look': 'stand'}
HANDS = {'relaxed': '', 'open': 'flat', 'flat_push': 'flat', 'wave': 'flat', 'fist': 'fist', 'grip': 'grip', 'cup': 'grip',
         'pinch': 'pinch', 'point': 'point', 'thumb': 'thumb', 'peace': 'peace', 'claw': 'grip', 'hidden': 'hidden',
         'missing': 'hidden', 'in_pocket': 'hidden'}
FACE = {'listening': {}, 'calm': {'smile': .1}, 'surprised': {'mouth': 'O', 'brow': .3}, 'awe': {'mouth': 'O', 'brow': .4},
        'strain': {'mouth': 'teeth', '_effort': .8, 'brow': -.4}, 'pain': {'mouth': 'teeth', '_effort': 1, 'brow': -.6},
        'afraid': {'mouth': 'wavy', 'brow': .5}, 'tired': {'lid': .6}, 'sad': {'smile': -.55, 'brow': .5},
        'recognition': {'smile': .6}, 'joy': {'smile': .85}, 'forced_grin': {'mouth': 'teeth', 'smile': .6},
        'reluctant': {'brow': -.6}, 'embarrassed': {'brow': -.5, 'smile': -.2}, 'panting': {'mouth': 'O', 'brow': -.2}}
PROP = {'tv': 'screen', 'screen': 'screen', 'television': 'screen', 'projection': 'screen', 'phone': 'phone', 'receiver': 'phone',
        'handset': 'phone', 'vape': 'vape', 'tambourine_piece': 'shard', 'shard': 'shard', 'piece': 'shard', 'tambourine': 'tambourine',
        'heart': 'heart', 'raven': 'raven', 'bird': 'raven', 'star': 'star', 'orb': 'star', 'galaxy': 'star', 'universe': 'star',
        'moon': 'moon', 'mic': 'mic', 'ring': 'ring', 'band': 'ring', 'cup': 'cup', 'glass': 'cup', 'coupe': 'cup', 'chair': 'chair',
        'table': 'table', 'bed': 'bench', 'mattress': 'bench', 'pew': 'bench', 'bench': 'bench', 'door': 'door', 'window': 'window',
        'mirror': 'mirror', 'letter': 'letter', 'page': 'letter', 'poem': 'letter', 'journal': 'book', 'book': 'book', 'photo': 'letter',
        'box': 'box', 'gift': 'box', 'crate': 'box', 'lamp': 'lamp', 'lantern': 'lamp', 'candle': 'candle', 'clock': 'clock', 'hourglass': 'clock',
        'coin': 'coin', 'key': 'key', 'globe': 'globe', 'hat': 'hat', 'suitcase': 'suitcase', 'bag': 'suitcase', 'fence': 'fence',
        'railing': 'fence', 'rail': 'fence', 'fire_escape': 'fence', 'stairs': 'stairs', 'bottle': 'cup', 'skull': 'skull', 'broom': 'broom'}
# props that live in the sky or the air rather than on the floor
SKY = ('raven', 'star', 'moon', 'kite', 'clock')
FX = {'rain': 'rain', 'storm': 'rain', 'wind': 'wind', 'hearts': 'hearts', 'stars': 'stars', 'galaxies': 'stars',
      'flashing_lights': 'glow', 'headlights': 'glow', 'glow': 'glow', 'tears': 'tear', 'sweat': 'sweat', 'dust': 'dust'}


def puppet_for(role, k):
    r = (role or '').upper()
    if r == 'POET' or r.startswith('POET'):
        return 'poet'
    if r == 'EX':
        return 'man'
    if r in ('YOUNG_POET', 'GHOST_CHILD') or 'CHILD' in r or 'YOUNG' in r or 'KID' in r:
        return 'dot'
    return ('man', 'poet')[k % 2]


def rotY(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def place(b, k):
    """A body from the breakdown -> a bank actor record in world cm."""
    pose = (b.get('pose') or 'stand').lower()
    pose = POSE_ALIAS.get(pose, pose)
    lib = POSES.get(pose) or POSES['stand']
    a = json.loads(json.dumps(lib['actor']))
    view = b.get('view') or 'front'
    if (b.get('role') or '').upper() == 'EX' and view not in ('back', 'threequarter_back'):
        view = 'back'                                         # the EX's face is never seen
    pos = b.get('position') or {}
    x = pos.get('x', .5)
    x = float(x) if isinstance(x, (int, float)) else .5
    sign = -1 if x > .55 else 1                               # turn toward the middle of the frame
    deg = VIEW_DEG.get(view, 0) * sign
    R = rotY(deg)
    off = np.array([(x - .5) * 320, {'air': 45, 'fall': 70}.get(pos.get('level'), 0),
                    {'near': 70, 'mid': 0, 'far': -110}.get(pos.get('depth'), 0)])
    a['j'] = [None if q is None else (R @ np.array(q) + off).tolist() for q in a['j']]
    for kk in ('fwd', 'up', 'hfwd', 'pfwd'):
        a[kk] = (R @ np.array(a[kk])).tolist()
    # hands
    hs = b.get('hands') or {}
    hand = dict(a.get('hand') or {})
    J = p3d.J
    for s in 'LR':
        h = hs.get(s) or {}
        shape = h.get('shape') or 'relaxed'
        hand[s] = HANDS.get(shape, '')
        hand['g' + s] = .8 if shape in ('grip', 'fist', 'cup') else 0
        if shape == 'in_pocket':
            sh, hip = np.array(a['j'][J['shoulder' + s]]), np.array(a['j'][J['hip' + s]])
            fw = np.array(a['pfwd'])
            side = hip - np.array(a['j'][J['pelvis']])
            wr = hip + side * .25 + fw * 4 + np.array([0, -4, 0])
            el = (sh + wr) / 2 + side * .6 - fw * 5
            a['j'][J['wrist' + s]], a['j'][J['elbow' + s]] = wr.tolist(), el.tolist()
    a['hand'] = hand
    # face
    face = {'mouth': 'line', 'eyes': 'o', 'smile': 0, 'open': 0, 'lid': 0, 'brow': 0, 'gx': 0, 'gy': 0}
    fx = dict(FACE.get(b.get('expression') or 'listening', {}))
    eff = fx.pop('_effort', 0)
    face.update(fx)
    e = b.get('eyes') or 'open'
    face.update({'closed': {'eyes': 'closed'}, 'half': {'lid': .55}, 'down': {'gy': -1, 'lid': .3}, 'up': {'gy': 1},
                 'side': {'gx': 1}}.get(e, {}))
    a['face'] = face
    a['effort'] = eff
    return a, lib['scale']


def build(shot):
    bodies = shot.get('bodies') or []
    actors, frame, cast, costumes = [], {'a': {}, 'p': {}}, {}, {}
    ids = {}
    for k, b in enumerate(bodies):
        aid = chr(65 + k)
        a, sc = place(b, k)
        actors.append({'id': aid, 'name': b.get('role') or aid, 'scale': sc})
        frame['a'][aid] = a
        cast[aid] = puppet_for(b.get('role'), k)
        costumes[aid] = str(b.get('costume') or '')
        ids[(b.get('role') or '').upper()] = aid
    for i, p in enumerate(shot.get('props') or []):
        pid = str(p.get('id', f'p{i}'))
        t = next((v for kk, v in PROP.items() if kk in pid.lower()), 'tag')
        q = {'type': t, 'pos': None, 'rot': [0, 0, 0], 'held': None, 'size': None, 'id': pid}
        hb = str(p.get('held_by') or '')
        if '.' in hb and hb.split('.')[0].upper() in ids:
            who = ids[hb.split('.')[0].upper()]
            side = hb.split('.')[1][:1].upper()
            w = frame['a'][who]['j'][p3d.J['wrist' + (side if side in 'LR' else 'R')]]
            q['pos'] = [w[0], w[1] - 4, w[2] + 2]
            q['held'] = f'{who}.{side}'
        else:
            pos = p.get('position') or {}
            x = pos.get('x', .15 + .7 * (i % 3) / 2)
            x = float(x) if isinstance(x, (int, float)) else .5
            lvl = pos.get('level')
            y = 0 if t in ('chair', 'table', 'bench', 'door', 'window', 'fence', 'stairs', 'lamp', 'screen', 'mirror') else \
                (170 + 20 * (i % 3) if t in SKY or lvl == 'air' else 95 if t == 'tag' and bodies else 4)
            q['pos'] = [(x - .5) * 320, y, {'near': 70, 'mid': 0, 'far': -110}.get(pos.get('depth'), -60)]
            if t == 'window':
                q['pos'][1] = 80
        frame['p'][pid] = q
    fx = []
    for name in shot.get('fx') or []:
        k = next((v for kk, v in FX.items() if kk in str(name).lower()), None)
        if k:
            fx.append({'k': k, 'a': 0, 'b': 10, 'who': None, 'p': [0, 120, -60] if k == 'glow' else None})
    V = {'actors': actors, 'frames': [frame], 'view': {'yaw': 0, 'elev': 8, 'zoom': 1.0, 'x': 0, 'y': 90, 'z': 0}, 'fx': fx}
    return V, cast, costumes


def recolour(img, costume):
    """A costume as a recolour of the poet's dress cards: the teal ground and the gold print
    are re-dyed, the drawing (shading, ink, cardboard) is kept."""
    import colorsys
    a = np.asarray(img).astype(float) / 255
    rgb = a[..., :3]
    mx, mn = rgb.max(2), rgb.min(2)
    lum = rgb.mean(2)
    sat = (mx - mn) / (mx + 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    teal = (g > r * 1.05) & (b > r * .95) & (sat > .18)
    gold = (r > b * 1.25) & (g > b * 1.05) & (sat > .22) & ~teal
    if costume.startswith('red_black'):
        ground, print_ = np.array([.09, .08, .08]), np.array([.80, .14, .12])
    elif 'black' in costume:
        ground, print_ = np.array([.10, .10, .11]), np.array([.30, .30, .32])
    else:
        return img
    out = rgb.copy()
    out[teal] = np.clip(ground * (0.55 + lum[teal][:, None] * 1.4), 0, 1)
    out[gold] = np.clip(print_ * (0.6 + lum[gold][:, None] * 0.8), 0, 1)
    a[..., :3] = out
    return Image.fromarray((a * 255).astype(np.uint8))


class ShotRig(cardrig.CardRig):
    """The card rig on a one-frame scene built from a shot, with costumes per actor."""
    def __init__(self, V, cast, costumes=None):
        self.act, self.tid, self.V = 'shot', 'shot', V
        self.parts = p3d.LIBR.load()
        self._img, self._cards = {}, {}
        self.cast = cast
        self.costumes = costumes or {}
        self.actor_scale = {a['id']: a.get('scale', 1.0) for a in V['actors']}

    def actor_items(self, pt, cam, aid, a, add, after, notes, skin):
        """Bind this actor's costume into each of its draw calls (they run after every actor is
        queued, so a shared 'current costume' would dress everyone as the last actor)."""
        cos = self.costumes.get(aid.rstrip('~'), '')

        def add2(key, zz, fn, cos=cos):
            add(key, zz, lambda fn=fn, cos=cos: (setattr(self, '_cur_costume', cos), fn())[-1])
        self._cur_costume = cos
        return super().actor_items(pt, cam, aid, a, add2, after, notes, skin)

    def card(self, path):
        cos = getattr(self, '_cur_costume', '') or ''
        if cos and path.startswith('weave/assets/parts/') and any(k in path for k in ('torso', 'skirt')):
            key = (path, cos)
            if key not in self._cards:
                self._cards[key] = recolour(super().card(path), cos)
            return self._cards[key]
        return super().card(path)


def framing_window(R, cam, shot):
    pts, heads = [], []
    fr = R.V['frames'][0]
    for aid, a in fr['a'].items():
        b, _ = R.retarget(dict(a, _id=aid), R.cast[aid])
        pts += [cam.P(q)[:2] for q in b['j'] if q is not None]
        heads.append((cam.P(b['j'][p3d.J['head']])[:2], cam.P(b['j'][p3d.J['pelvis']])[:2]))
    if not pts:
        # an insert with no bodies: frame the props
        for q in fr.get('p', {}).values():
            if q.get('pos'):
                c = cam.P(q['pos'])[:2]
                pts += [c - 30 * cam.s, c + 30 * cam.s]
    pts = np.array(pts) if pts else np.array([[900, 500], [1000, 700]])
    m = 40 * cam.s
    fr_ = shot.get('framing') or 'wide'
    x0, y0 = pts.min(0) - m
    x1, y1 = pts.max(0) + m
    floor = cam.P([0, 0, 0])[1]
    if fr_ in ('wide', 'pov'):
        x0, x1 = x0 - 120 * cam.s, x1 + 120 * cam.s
        y0, y1 = y0 - 40 * cam.s, max(y1, floor + 25 * cam.s)
    elif fr_ in ('full',):
        y1 = max(y1, floor + 15 * cam.s)
    elif fr_ == 'medium' and heads:
        y1 = max(h[1][1] for h in heads) + 10 * cam.s
    elif fr_ in ('close', 'extreme_close', 'insert') and heads:
        (hx, hy), _ = heads[0]
        r = (34 if fr_ == 'close' else 20) * cam.s
        x0, x1, y0, y1 = hx - r * 1.5, hx + r * 1.5, hy - r, hy + r * 1.2
    w, h = x1 - x0, y1 - y0
    if w < h * 1.4:                                     # boards are wide: 1.4:1 at least
        cx = (x0 + x1) / 2
        x0, x1 = cx - h * .7, cx + h * .7
    return (int(x0), int(y0), int(x0) + 2 * int((x1 - x0) / 2), int(y0) + 2 * int((y1 - y0) / 2))


def render_shot(shot, size=(700, 500)):
    V, cast, costumes = build(shot)
    R = ShotRig(V, cast, costumes)
    cam = p3d.Camera(V['view'])
    win = framing_window(R, cam, shot)
    img, notes = R.render(0, window=win)
    # a ghost is see-through: redraw the frame without it and blend (cut-out double exposure)
    ghosts = [a['id'] for a, b in zip(V['actors'], shot.get('bodies') or []) if 'GHOST' in (b.get('role') or '').upper()]
    if ghosts:
        V2 = json.loads(json.dumps(V))
        for g in ghosts:
            V2['frames'][0]['a'].pop(g, None)
            V2['actors'] = [a for a in V2['actors'] if a['id'] != g]
        bg, _ = ShotRig(V2, {k: v for k, v in cast.items() if k not in ghosts}, costumes).render(0, window=win)
        img = Image.blend(bg.convert('RGB'), img.convert('RGB'), .45)
    img = img.convert('RGB')
    img.thumbnail(size, Image.LANCZOS)
    return img


def board(P, cells):
    cols = 3
    cw, ch, cap = 700, 500, 170
    shots = [(sc, sh) for sc in P.get('scenes', []) for sh in sc.get('shots', [])]
    rows = max(1, math.ceil(len(shots) / cols))
    W = 50 + cols * (cw + 24)
    Hh = 170 + rows * (ch + cap + 26)
    im = Image.new('RGB', (W, Hh), PAPER)
    d = ImageDraw.Draw(im)
    d.text((50, 34), f"{P.get('num')}  {P.get('title', '').upper()}", font=ImageFont.truetype(SERIF, 44), fill=INK)
    d.text((50, 96), f"{len(P.get('scenes', []))} scenes · {len(shots)} shots · treatment pp. {P.get('pages')} · {P.get('style', '')} · rendered with the card rig, poses from the Crash Lab bank",
           font=ImageFont.truetype(FR, 20), fill=DIM)
    for i, (sc, sh) in enumerate(shots):
        x, y = 50 + (i % cols) * (cw + 24), 160 + (i // cols) * (ch + cap + 26)
        c = cells.get(sh.get('id'))
        if c is not None:
            im.paste(c, (x + (cw - c.width) // 2, y + (ch - c.height) // 2))
        d.rectangle([x, y, x + cw - 1, y + ch - 1], outline=(214, 206, 192))
        d.text((x, y + ch + 8), f"{sh.get('id', '')} · {sh.get('framing', '')} · {sh.get('camera', '')} · {sc.get('movement', '')}", font=ImageFont.truetype(FB, 16), fill=INK)
        yy = y + ch + 32
        for ln in textwrap.wrap(sh.get('action', ''), 80)[:3]:
            d.text((x, yy), ln, font=ImageFont.truetype(FR, 15), fill=INK)
            yy += 19
        for b in (sh.get('bodies') or [])[:3]:
            hs = b.get('hands') or {}
            hand = ' / '.join(f"{(hs.get(k) or {}).get('shape', '-')}" + (f"({(hs.get(k) or {}).get('holds')})" if (hs.get(k) or {}).get('holds') else '') for k in 'LR')
            d.text((x, yy), f"{b.get('role')}: {b.get('view')} · {b.get('pose')} · {b.get('expression')} · {hand}"[:92], font=ImageFont.truetype(FM, 13), fill=DIM)
            yy += 17
    return im


def run(n):
    P = json.load(open(os.path.join(BD, f'{n}.json')))
    od = os.path.join(OUT, n)
    os.makedirs(od, exist_ok=True)
    cells = {}
    for sc in P.get('scenes', []):
        for sh in sc.get('shots', []):
            try:
                img = render_shot(sh)
            except Exception as e:
                img = Image.new('RGB', (700, 500), (240, 230, 225))
                ImageDraw.Draw(img).text((20, 20), f'render failed: {e}'[:80], font=ImageFont.truetype(FR, 16), fill=(180, 40, 30))
            img.save(os.path.join(od, f"{sh.get('id')}.jpg"), quality=86)
            cells[sh.get('id')] = img
    board(P, cells).save(os.path.join(OUT, f'{n}.board.jpg'), quality=84)
    print(n, P.get('title'), len(cells), 'shots')


if __name__ == '__main__':
    ns = sys.argv[1:] or [os.path.basename(f)[:2] for f in sorted(glob.glob(os.path.join(BD, '[0-9][0-9].json')))]
    for n in ns:
        run(n)
