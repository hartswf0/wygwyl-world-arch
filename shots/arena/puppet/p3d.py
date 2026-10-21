"""The man as the Crash Lab draws its dummy: from 3D joints, through any camera.

The cut-out rig was flat cards in fixed views, so it could only be watched from
the side it was drawn for, and every turn of a hand or a foot was a guess. Bolas
draws its dummy from 3D joints and local frames each frame (lab/crash-lab
drawDummy, gloveDraw, shoe), so it reads from any camera. This draws the man the
same way and paints him as the cardboard puppet on weave/cast/man/sheets/body_profile.jpg:

  limbs, hips, vest   3D volumes in the man's proportions (canon.json), each drawn as
                      one flat card: rim, ink edge, fill; seams inside a part vanish,
                      seams between parts show, as on a real cut-out
  hands               gloveDraw ported: palm normal from the chest frame (in/out/up/
                      down/fwd/back), thumb = fingers x palm, so a hand faces the right
                      way in every direction by construction
  boots               two blocks hinged at the ball, on the bank's heel/ball/toe/ankle,
                      so the boot rolls and creases with the foot
  head                a drawn head (likeness) picked by where the head points relative
                      to the camera, and by the face Bolas asks for

    from p3d import Puppet
    img = Puppet('ACT-010').render(80, yaw=None, elev=None)    # None = the vignette's camera
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ARENA = os.path.normpath(os.path.join(HERE, '..'))
SHOTS = os.path.normpath(os.path.join(ARENA, '..'))
sys.path.insert(0, os.path.join(ARENA, 'parts'))
sys.path.insert(0, os.path.join(ARENA, 'critic'))
import library as LIBR
from kit import vec

CANON = json.load(open(os.path.join(HERE, 'canon.json')))
J = {n: i for i, n in enumerate(['pelvis', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'heelL', 'heelR',
                                 'ballL', 'ballR', 'toeL', 'toeR', 'spineMid', 'neckBase', 'chest', 'shoulderL',
                                 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'headBase', 'head', 'headTop', 'nose'])}
W, H = 1920, 1080
SS = 2                                    # supersampling

C = CANON['colour']


def nrm(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def ellipse(c, ax, bx, a, b, n=20):
    return [c + ax * a * math.cos(2 * math.pi * k / n) + bx * b * math.sin(2 * math.pi * k / n) for k in range(n)]


class Camera:
    def __init__(self, view, yaw=None, elev=None, zoom=None, centre=None):
        v = dict(view or {})
        self.yaw = math.radians(v.get('yaw', -22) if yaw is None else yaw)
        self.elev = math.radians(v.get('elev', 10) if elev is None else elev)
        self.c = centre if centre is not None else [v.get('x', 0), v.get('y', 90), v.get('z', 0)]
        self.s = H * 0.86 / 230 * (v.get('zoom', 1.0) if zoom is None else zoom)

    def cam(self, p):
        """World cm -> camera axes (x right, y up, z away), unscaled."""
        x, y, z = p[0] - self.c[0], p[1] - self.c[1], p[2] - self.c[2]
        cy, sy, ce, se = math.cos(self.yaw), math.sin(self.yaw), math.cos(self.elev), math.sin(self.elev)
        x1, z1 = x * cy - z * sy, x * sy + z * cy
        return np.array([x1, y * ce - z1 * se, y * se + z1 * ce])

    def dir(self, v):
        return self.cam(np.asarray(v, float) + np.array(self.c)) - self.cam(np.array(self.c, float))

    def P(self, p):
        q = self.cam(p)
        return np.array([W / 2 + q[0] * self.s, H * 0.52 - q[1] * self.s, q[2]])


def hull2(pts):
    return vec.hull([[float(p[0]), float(p[1])] for p in pts])


class Painter:
    """Flat cut-out cards on a supersampled canvas. A part is a list of convex polygons
    (screen px) painted as one card: rim, then ink edge, then fill, so its internal
    seams disappear and its outline is one line."""

    def __init__(self, bg=(23, 25, 31), window=None):
        self.x0, self.y0, x1, y1 = window or (0, 0, W, H)
        self.w, self.h = int(x1 - self.x0), int(y1 - self.y0)
        self.im = Image.new('RGBA', (self.w * SS, self.h * SS), bg + (255,))
        self.d = ImageDraw.Draw(self.im)

    def _xy(self, p):
        return ((p[0] - self.x0) * SS, (p[1] - self.y0) * SS)

    def _poly(self, pts, fill, grow=0.0):
        P = [self._xy(p) for p in (vec.offset(pts, grow) if grow else pts)]
        if len(P) >= 3:
            self.d.polygon(P, fill=fill)

    def poly_raw(self, pts, fill, outline=None):
        self.d.polygon([self._xy(p) for p in pts], fill=fill, outline=outline)

    def ellipse_raw(self, c, rx, ry, fill):
        x, y = self._xy(c)
        self.d.ellipse([x - rx * SS, y - ry * SS, x + rx * SS, y + ry * SS], fill=fill)

    def card(self, polys, fill, rim=2.4, ink=1.3, rim_col=None):
        polys = [p for p in polys if len(p) >= 3]
        for p in polys:
            self._poly(p, vec._hex(rim_col or vec.RIM), rim + ink)
        for p in polys:
            self._poly(p, vec._hex(C['ink']), ink)
        for p in polys:
            self._poly(p, vec._hex(fill))

    def line(self, pts, col, w):
        self.d.line([self._xy(p) for p in pts], fill=vec._hex(col), width=max(1, int(w * SS)), joint='curve')

    def disc(self, c, r, col, ink=None):
        x, y = self._xy(c)
        if ink:
            self.d.ellipse([x - (r + 1) * SS, y - (r + 1) * SS, x + (r + 1) * SS, y + (r + 1) * SS], fill=vec._hex(ink))
        self.d.ellipse([x - r * SS, y - r * SS, x + r * SS, y + r * SS], fill=vec._hex(col))

    def brad(self, c, r):
        self.disc(c, r, '#b8902f', ink='#5a4314')
        self.disc((c[0] - r * .25, c[1] - r * .25), r * .35, '#f1d27a')

    def paste(self, img, M, t):
        """Affine-paste an RGBA image: screen = M @ card + t (screen px)."""
        Ms = M * SS
        ts = (np.asarray(t) - np.array([self.x0, self.y0])) * SS
        Mi = np.linalg.inv(Ms)
        ti = -Mi @ ts
        L = img.transform(self.im.size, Image.AFFINE, (Mi[0, 0], Mi[0, 1], ti[0], Mi[1, 0], Mi[1, 1], ti[1]), resample=Image.BICUBIC)
        self.im.alpha_composite(L)
        return np.asarray(L.getchannel('A')) > 128

    def result(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS).convert('RGB')


class Puppet:
    def __init__(self, act):
        n = int(act.split('-')[1])
        self.act, self.tid = act, f'T{n + 100}'
        self.V = json.load(open(os.path.join(ARENA, 'bolas', 'bank', self.tid + '.json')))
        self.parts = LIBR.load()
        self._img = {}

    # ---------------------------------------------------------------- frames
    def actors(self, f):
        return [(aid, a) for aid, a in self.V['frames'][f]['a'].items()]

    @staticmethod
    def frames_of(a):
        j = {k: np.array(a['j'][i], float) for k, i in J.items() if a['j'][i] is not None}
        fwd, up = nrm(a['fwd']), nrm(a['up'])
        x = nrm(np.cross(up, fwd))          # chest x; checked against the shoulders below
        if np.dot(x, j['shoulderL'] - j['shoulderR']) < 0:
            x = -x
        pf = nrm(a['pfwd'])
        up0 = nrm(j['spineMid'] - j['pelvis'])
        x0 = nrm(np.cross(up0, pf))
        if np.dot(x0, j['hipL'] - j['hipR']) < 0:
            x0 = -x0
        pf = nrm(np.cross(x0, up0))
        if np.dot(pf, a['pfwd']) < 0:
            pf = -pf
        return j, {'x': x, 'up': up, 'fwd': fwd}, {'x': x0, 'up': up0, 'fwd': pf}

    # ---------------------------------------------------------------- parts
    def capsule(self, cam, a, b, ra, rb):
        pa, pb = cam.P(a), cam.P(b)
        return hull2(vec.circle_pts(pa[:2], ra * cam.s, 18) + vec.circle_pts(pb[:2], rb * cam.s, 18))

    def facing(self, cam, normal):
        return cam.dir(normal)[2] < 0          # the surface normal points at the camera

    def vest(self, pt, cam, j, Rc, R0):
        K = CANON['vest']
        secs = []
        for name, frame, base, off in (('hem', R0, 'pelvis', 'up0'), ('waist', None, 'spineMid', None),
                                       ('chest', Rc, 'chest', None), ('shoulder', Rc, 'neckBase', 'down'),
                                       ('collar', Rc, 'neckBase', 'up')):
            a, b, dy = K[name]
            fr = frame or {k: nrm(Rc[k] + R0[k]) for k in ('x', 'up', 'fwd')}
            c = j[base] + fr['up'] * dy
            secs.append((c, fr, a, b))
        polys = []
        for (c0, f0, a0, b0), (c1, f1, a1, b1) in zip(secs, secs[1:]):
            P = [cam.P(p)[:2] for p in ellipse(c0, f0['x'], f0['fwd'], a0, b0) + ellipse(c1, f1['x'], f1['fwd'], a1, b1)]
            polys.append(hull2(P))
        pt.card(polys, C['cloth'])
        # piping and zip on the faces that look at the camera
        for side in (-1, 1):
            for face in (1, -1):
                pts, vis = [], []
                for c, fr, a, b in secs[:4]:
                    xo = side * a * 0.55
                    p = c + fr['x'] * xo + fr['fwd'] * face * b * math.sqrt(1 - 0.55 ** 2)
                    pts.append(cam.P(p)[:2])
                    vis.append(self.facing(cam, fr['fwd'] * face + fr['x'] * side * 0.55))
                if sum(vis) >= 3:
                    pt.line(pts, C['piping'], 0.9 * cam.s)
        c, fr, a, b = secs[2]
        if self.facing(cam, fr['fwd']):
            pt.line([cam.P(s[0] + s[1]['fwd'] * s[3])[:2] for s in secs[:5]], C['zip'], 0.35 * cam.s)

    def shorts(self, pt, cam, j, R0):
        K = CANON['shorts']
        top = ellipse(j['pelvis'] + R0['up'] * K['waist'][2], R0['x'], R0['fwd'], K['waist'][0], K['waist'][1])
        polys = []
        for s in 'LR':
            hip, knee = j['hip' + s], j['knee' + s]
            d = nrm(knee - hip)
            hem = hip + d * K['hem']
            ax = nrm(np.cross(d, R0['fwd']))
            bx = nrm(np.cross(d, ax))
            ring = ellipse(hem, ax, bx, K['leg_r'], K['leg_r'])
            seat = ellipse(hip + R0['up'] * 2, R0['x'], R0['fwd'], K['seat'][0], K['seat'][1])
            # each leg of the shorts takes only its own half of the waist and seat, so the
            # crotch shows between them (critic, p3d turn 3: from behind it was a skirt)
            sg = 1 if s == 'L' else -1
            half = [p for p in top + seat if np.dot(p - j['pelvis'], R0['x']) * sg > -1.5]
            polys.append(hull2([cam.P(p)[:2] for p in half + ring]))
        pt.card(polys, C['cloth'])

    def limb(self, pt, cam, a, b, ra, rb, pipe_dir=None, brads=(), cuff=None):
        pt.card([self.capsule(cam, a, b, ra, rb)], C['cloth'])
        if pipe_dir is not None and self.facing(cam, pipe_dir):
            pa, pb = a + pipe_dir * ra * 0.8, b + pipe_dir * rb * 0.8
            pt.line([cam.P(pa)[:2], cam.P(pb)[:2]], C['piping'], 0.9 * cam.s)
        if cuff:
            d = nrm(b - a)
            pt.card([self.capsule(cam, b - d * cuff[1], b, cuff[0], cuff[0])], C['cuff'], rim=0.8)
        for p in brads:
            pt.brad(cam.P(p)[:2], 1.3 * cam.s)

    def boot(self, pt, cam, j, s, shin_dir):
        K = CANON['boot']
        an, he, ba, to = j['ankle' + s], j['heel' + s], j['ball' + s], j['toe' + s]
        up = nrm(an - (he + ba) / 2)
        fr = nrm(ba - he)
        ff = nrm(to - ba)
        side = nrm(np.cross(fr, up))
        upf = nrm(np.cross(side, ff))
        w = K['width'] / 2
        sole = K['sole']
        # rounded blocks: rings across the foot at heel, ball and toe, hulled
        heelc = he - fr * K['heel_back'] * 0.5 + up * (K['heel_h'] - sole) / 2
        ballc = ba + up * (K['ball_h'] - sole) / 2
        tip = to + ff * K['toe_cap']
        toec = tip + upf * (K['toe_h'] - sole) / 2
        instep = (he + ba) / 2 + up * K['instep_h'] / 2
        rear = ellipse(heelc, side, up, w * 0.82, (K['heel_h'] + sole) / 2, 16) + ellipse(ballc, side, up, w, (K['ball_h'] + sole) / 2, 16) + \
            ellipse(instep, side, up, w * 0.95, K['instep_h'] / 2 + sole, 16)
        fore = ellipse(ba + upf * (K['ball_h'] - sole) / 2, side, upf, w, (K['ball_h'] + sole) / 2, 16) + \
            ellipse(toec, side, upf, w * 0.78, (K['toe_h'] + sole) / 2, 16) + [tip + ff * 1.2 + upf * K['toe_h'] * 0.3]
        sx = nrm(np.cross(shin_dir, side))
        shaft = ellipse(an - up * 1.0, side, sx, K['shaft_r'], K['shaft_r'] * 1.1) + \
            ellipse(an + shin_dir * K['shaft_h'], side, sx, K['shaft_r'] * 0.92, K['shaft_r'] * 0.92)
        P2 = lambda L: hull2([cam.P(p)[:2] for p in L])
        pt.card([P2(shaft), P2(rear), P2(fore)], C['leather'])
        # sole as a dark strip, crease at the ball, laces up the front
        sl = [he - fr * K['heel_back'] - up * sole, ba - up * sole, tip - upf * sole, tip + ff * 1.4]
        pt.line([cam.P(p)[:2] for p in sl], C['sole'], 1.6 * cam.s)
        if self.facing(cam, upf + ff * 0.5):
            pt.line([cam.P(ba + upf * K['ball_h'] + side * k * w * 0.7)[:2] for k in (-1, 1)], C['leather_hi'], 0.35 * cam.s)
        front = nrm(fr + ff)
        if self.facing(cam, front):
            lace = [ba + upf * K['ball_h'] * 1.05 - fr * 2, an + front * K['shaft_r'] * 0.9, an + shin_dir * K['shaft_h'] + front * K['shaft_r']]
            pt.line([cam.P(p)[:2] for p in lace], C['laces'], 0.45 * cam.s)

    def hand(self, pt, cam, j, Rc, s, state):
        """Port of bolas lab/crash-lab gloveDraw, painted as a cardboard hand."""
        hs = CANON['hand_scale']
        w, el = j['wrist' + s], j['elbow' + s]
        u = nrm(w - el)
        sg = 1 if s == 'L' else -1
        PALM = {'in': [-sg, 0, 0], 'out': [sg, 0, 0], 'down': [0, -1, 0], 'up': [0, 1, 0], 'fwd': [0, 0, 1], 'back': [0, 0, -1]}
        v = PALM.get(state['palm'], PALM['in'])
        n = Rc['x'] * v[0] + Rc['up'] * v[1] + Rc['fwd'] * v[2]
        n = n - u * np.dot(n, u)
        if np.linalg.norm(n) < .1:
            n = np.cross(u, [0, 1, 0])
        n = nrm(n)
        fdir = u
        thumb = nrm(np.cross(fdir, n) * (-1 if s == 'L' else 1))
        grip, shape = state['grip'], state['shape'] or 'relaxed'
        palmC = w + fdir * 5.5 * hs
        facing = cam.dir(n)[2] < 0
        skin = C['skin_palm'] if facing else C['skin']

        def seg(a, b, wid):
            pt.card([self.capsule(cam, a, b, wid / 2, wid / 2 * 0.92)], C['skin'], rim=1.4, ink=1.1)

        def finger(i, curl):
            across = (i - 1.5) * 2.05 * hs
            base = palmC + fdir * 5.2 * hs - thumb * across
            L1 = (8.5 - abs(i - 1.5) * 1.2) * hs
            k1 = base + fdir * L1 * .55
            tip = k1 + fdir * L1 * .45 * (1 - curl) + n * L1 * .6 * curl
            k1b = base + fdir * L1 * .55 * (1 - curl * .4) + n * L1 * .25 * curl
            seg(base, k1b, 3.2 * hs)
            seg(k1b, tip, 3.0 * hs)

        def palm():
            # a palm, not a disc: longer than wide, squarer at the knuckles (critic, p3d turn 2: mittens)
            ring = [palmC + thumb * (4.3 * hs * math.cos(t)) + fdir * (5.4 * hs * math.sin(t) + (1.2 * hs if math.sin(t) > 0 else 0))
                    for t in np.linspace(0, 2 * math.pi, 28, endpoint=False)]
            pt.card([hull2([cam.P(p)[:2] for p in ring])], skin, rim=1.4, ink=1.1)

        def th(curl):
            base = palmC + thumb * 3.6 * hs - fdir * 1.5 * hs
            tip = base + thumb * 3.4 * (1 - curl) * hs + fdir * 5.0 * hs + n * curl * 3 * hs
            seg(base, tip, 3.4 * hs)
        curls = {'point': (0, .95, .95, .95, .6), 'flat': (0, 0, 0, 0, .2), 'fist': (1, 1, 1, 1, .9),
                 'peace': (0, 0, 1, 1, .8), 'pinch': (.45, .7, .85, .9, .45)}
        if shape == 'hidden':
            return
        if shape == 'fist':
            for i in range(4):
                finger(i, 1)
            palm()
            th(.9)
        elif shape == 'thumb':
            palm()
            for i in range(4):
                finger(i, 1)
            b = palmC + thumb * 4 * hs
            seg(b, b + nrm(Rc['up'] + thumb * .3) * 9 * hs, 3.4 * hs)
        elif shape in curls:
            c = curls[shape]
            palm()
            for i in range(4):
                finger(i, c[i])
            th(c[4])
        else:
            if facing:
                palm()
                for i in range(4):
                    finger(i, grip)
                th(grip)
            else:
                for i in range(4):
                    finger(i, grip)
                th(grip)
                palm()

    def head(self, pt, cam, j, a, face, effort):
        """A drawn head: view from where the head points, expression from the face."""
        hf = nrm(a['hfwd'])
        d = cam.dir(hf)
        ang = math.degrees(math.atan2(d[0], -d[2]))       # 0 = faces the camera, +90 = faces screen right
        expr = face_to_expression(face or {}, effort)
        mirror = ang < 0
        aa = abs(ang)
        if aa < 28:
            # the front bank has no afraid/reluctant/pain/embarrassed: nearest neighbour,
            # never the old sunglasses card (critic, depth turn 1)
            fexpr = {'afraid': 'surprised', 'reluctant': 'strain', 'pain': 'strain', 'embarrassed': 'forced_grin'}.get(expr, expr)
            p, miss = LIBR.pick(self.parts, 'head', view='front', expression=fexpr)
            if miss:
                p, miss = LIBR.pick(self.parts, 'head', view='front', expression='listening')
            mirror = False
        elif aa < 125:
            p, miss = LIBR.pick(self.parts, 'head', view='threequarter_R', expression=expr)
            if miss:
                p, miss = LIBR.pick(self.parts, 'head', view='threequarter_R', expression='listening')
        else:
            p, miss = LIBR.pick(self.parts, 'head', view='back')
            mirror = ang > 0      # the back card faces left-of-screen's opposite
        if p['id'] not in self._img:
            self._img[p['id']] = Image.open(os.path.join(SHOTS, p['file'])).convert('RGBA')
        img = self._img[p['id']]
        sk = p['sockets']
        neck, crown = np.array(sk['neck'], float), np.array(sk['crown'], float)
        if mirror:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
            neck[0] = img.size[0] - neck[0]
            crown[0] = img.size[0] - crown[0]
        A = cam.P(j['neckBase'] + nrm(j['headBase'] - j['neckBase']) * CANON['head']['neck_drop'])[:2]
        B = cam.P(j['headTop'] + nrm(j['headTop'] - j['headBase']) * CANON['head']['crown_lift'])[:2]
        scale = CANON['head']['scale']
        dock = getattr(self, '_head_dock', None)
        if dock is not None:
            # a card rig hangs the head from the torso CARD's drawn collar, not from the
            # skeleton's neck point, so the two never slide apart (critic: the head looked
            # glued on); the neck tab goes down into the collar and is drawn under it
            A, scale = np.asarray(dock['at'], float), dock.get('scale', scale)
        # uniform scale from the head's 3D size, not its foreshortened screen length
        L3 = np.linalg.norm(j['headTop'] - j['neckBase']) * scale * cam.s
        k = L3 / np.linalg.norm(crown - neck)
        v = B - A
        if dock is not None and dock.get('axis') is not None:
            # a cut-out neck turns on one brad: keep the head within MAX_TILT of the torso
            ax = np.asarray(dock['axis'], float)
            d = math.atan2(v[1], v[0]) - math.atan2(ax[1], ax[0])
            d = (d + math.pi) % (2 * math.pi) - math.pi
            lim = math.radians(dock.get('max_tilt', 30))
            d = max(-lim, min(lim, d))
            a0 = math.atan2(ax[1], ax[0]) + d
            v = np.array([math.cos(a0), math.sin(a0)]) * max(np.linalg.norm(v), 1.0)
        th = math.atan2(v[1], v[0]) - math.atan2(crown[1] - neck[1], crown[0] - neck[0])
        if dock is None and np.linalg.norm(v) < 0.35 * L3:     # head pointing at or away from the lens: keep it upright
            th = 0.0
        R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]]) * k
        self._head_mask = pt.paste(img, R, A - R @ neck)
        return {'head': p['id'] + (' (mirrored)' if mirror else ''), 'view_angle': round(ang), 'expression': expr,
                'missing': miss}

    # ---------------------------------------------------------------- frame
    def render(self, f, yaw=None, elev=None, zoom=None, centre=None, props=True, floor=True, window=None):
        """-> (image, notes). window=(x0, y0, x1, y1) in screen px renders only that crop
        (much faster; a take keeps one window so its frames line up)."""
        cam = Camera(self.V['view'], yaw, elev, zoom, centre)
        pt = Painter(window=window)
        notes = []
        if floor:
            fl = [cam.P([cam.c[0] + x, 0, cam.c[2] + z])[:2] for x, z in ((-400, -400), (400, -400), (400, 400), (-400, 400))]
            pt.poly_raw(fl, (31, 34, 41, 255))
        fr = self.V['frames'][f]
        boxes = self.boxes(cam, fr) if props else []
        items, after = [], []          # (key, z, draw); constraints (before, after)
        K = CANON['limbs']
        HEAD_R = CANON['head'].get('front_r', 15.0)
        for aid, a in self.actors(f):
            j, Rc, R0 = self.frames_of(a)
            z = lambda p: cam.P(p)[2]
            near = 'L' if z(j['shoulderL']) < z(j['shoulderR']) else 'R'
            c = cam.P([j['pelvis'][0], 0, j['pelvis'][2]])
            pt.ellipse_raw(c, 26 * cam.s, 5 * cam.s, (12, 13, 16, 255))
            hands = {s: {'shape': a['hand'][s], 'grip': a['hand']['g' + s], 'palm': a['hand']['p' + s] or 'in'} for s in 'LR'}
            info = {'actor': aid, 'near': near, 'hands': hands}
            notes.append(info)

            def add(key, zz, fn):
                items.append([f'{aid}.{key}', zz, fn])

            for s in 'LR':
                out = R0['x'] * (1 if s == 'L' else -1)
                add(f'uarm{s}', z((j['shoulder' + s] + j['elbow' + s]) / 2),
                    lambda s=s, out=out, j=j: self.limb(pt, cam, j['shoulder' + s], j['elbow' + s], *K['uarm'], pipe_dir=out, brads=[j['shoulder' + s], j['elbow' + s]]))
                add(f'farm{s}', z((j['elbow' + s] + j['wrist' + s]) / 2),
                    lambda s=s, out=out, j=j: self.limb(pt, cam, j['elbow' + s], j['wrist' + s], *K['farm'], pipe_dir=out, cuff=K['cuff']))
                add(f'hand{s}', z(j['wrist' + s] + nrm(j['wrist' + s] - j['elbow' + s]) * 8),
                    lambda s=s, j=j, Rc=Rc, hands=hands: self.hand(pt, cam, j, Rc, s, hands[s]))
                add(f'thigh{s}', z((j['hip' + s] + j['knee' + s]) / 2),
                    lambda s=s, out=out, j=j: self.limb(pt, cam, j['hip' + s], j['knee' + s], *K['thigh'], pipe_dir=out))
                add(f'shin{s}', z((j['knee' + s] + j['ankle' + s]) / 2),
                    lambda s=s, out=out, j=j: self.limb(pt, cam, j['knee' + s], j['ankle' + s], *K['shin'], pipe_dir=out, brads=[j['knee' + s]]))
                add(f'boot{s}', z((j['heel' + s] + j['toe' + s]) / 2),
                    lambda s=s, j=j: self.boot(pt, cam, j, s, nrm(j['knee' + s] - j['ankle' + s])))
                P = lambda k: f'{aid}.{k}'
                after += [(P(f'thigh{s}'), P('shorts')), (P(f'shin{s}'), P(f'boot{s}')), (P(f'shin{s}'), P(f'thigh{s}'))]
                # an arm piece hangs over its parent unless it points away from the camera
                if z(j['wrist' + s]) <= z(j['elbow' + s]) + 6:
                    after.append((P(f'uarm{s}'), P(f'farm{s}')))
                if z(j['wrist' + s] + nrm(j['wrist' + s] - j['elbow' + s]) * 8) <= z(j['wrist' + s]) + 4:
                    after.append((P(f'farm{s}'), P(f'hand{s}')))
                # shoulder rule: the upper arm covers the face only when it is in front of the
                # head's surface, not merely nearer than its centre (critic: shoulders over chins)
                if z(j['elbow' + s]) > z(j['head']) - HEAD_R:
                    after.append((P(f'uarm{s}'), P('head')))
            add('shorts', z(j['pelvis']), lambda j=j, R0=R0: self.shorts(pt, cam, j, R0))
            add('vest', z(j['chest']), lambda j=j, Rc=Rc, R0=R0, near=near: (self.vest(pt, cam, j, Rc, R0), pt.brad(cam.P(j['shoulder' + near])[:2], 1.3 * cam.s)))

            def head(a=a, j=j, info=info):
                info.update(self.head(pt, cam, j, a, a.get('face'), a.get('effort', 0)))
                info['_head_snapshot'] = (self._head_mask, np.asarray(pt.im)[self._head_mask].copy())
            # (every queued call binds this actor's joints: a late-bound j drew actor A's
            # body at actor B's joints and left A a floating head; critic, depth turn 1)
            add('head', z(j['head']), head)
            after += [(f'{aid}.shorts', f'{aid}.vest'), (f'{aid}.vest', f'{aid}.head')]
            for p in boxes:
                if p['held'] and p['held'].startswith(aid + '.'):
                    after += [(f'{aid}.vest', 'box.' + p['id'])]
        for p in boxes:
            items.append(['box.' + p['id'], p['z'], lambda p=p: self.draw_box(pt, p)])
        order = depth_order(items, after)
        drawn_after_head = {}
        for n, (key, zz, fn) in enumerate(order):
            fn()
            if key.endswith('.head'):
                drawn_after_head[key.split('.')[0]] = [k for k, _, _ in order[n + 1:]]
        final = np.asarray(pt.im)
        for info in notes:
            snap = info.pop('_head_snapshot', None)
            if snap is None:
                continue
            m, before = snap
            if m.any():
                changed = np.abs(final[m].astype(int) - before.astype(int)).sum(axis=1) > 30
                cov = float(changed.mean())
                info['face_covered'] = round(cov, 3)
                if cov > 0.12:
                    info['face_hidden_by'] = f"{cov:.0%} of the head, under: " + ', '.join(
                        k for k in drawn_after_head.get(info['actor'], []) if not k.startswith(info['actor'] + '.shin'))[:120]
            info['order'] = [k for k, _, _ in order]
        return pt.result(), notes

    def boxes(self, cam, fr):
        """Every prop in the frame as flat-shaded polygons (the name is historical: only
        boxes were drawn at first, which left the ledge, the door, the chair and the balls
        out of half the challenges; critic, study turn 1)."""
        out = []
        for pid, q in fr.get('p', {}).items():
            polys = props_polys(cam, q)
            if not polys:
                continue
            pos = q.get('pos') or [0, 0, 0]
            out.append({'id': pid, 'held': q.get('held'), 'polys': polys, 'z': cam.P(pos)[2], 'type': q.get('type')})
        return out

    def draw_box(self, pt, p):
        for poly, col in p['polys']:
            pt.poly_raw(poly, vec._hex(col), outline=vec._hex('#1a120b'))


def face_to_expression(fc, effort):
    """Crash Lab FACE0 fields -> a head expression name (both head banks use these names)."""
    m, brow, lid, smile = fc.get('mouth'), fc.get('brow', 0), fc.get('lid', 0), fc.get('smile', 0)
    if fc.get('eyes') == 'closed':
        return 'tired'
    if m == 'teeth':
        return 'strain' if brow < -0.3 or effort > 0.5 else 'forced_grin'
    if m in ('O', 'open'):
        return 'surprised' if brow >= -0.1 else 'panting'
    if m == 'wavy':
        return 'afraid'
    if brow < -0.4:
        return 'reluctant'
    if lid > 0.4:
        return 'tired'
    if smile > 0.45:
        return 'recognition'
    if smile < -0.25:
        return 'sad'
    return 'listening'


def _inside(q, poly):
    x, y = q
    n, c = len(poly), False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i][:2], poly[(i + 1) % n][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            c = not c
    return c


def depth_order(items, after):
    """Painter's order: farthest first, but every (a, b) in `after` draws a before b.
    Kahn's algorithm, always taking the farthest part that is free to go."""
    keys = {k for k, _, _ in items}
    after = [(a, b) for a, b in after if a in keys and b in keys and a != b]
    indeg = {k: 0 for k in keys}
    succ = {k: [] for k in keys}
    for a, b in after:
        succ[a].append(b)
        indeg[b] += 1
    by = {k: it for it in items for k in [it[0]]}
    out, free = [], [k for k in keys if indeg[k] == 0]
    while free:
        free.sort(key=lambda k: -by[k][1])
        k = free.pop(0)
        out.append(by[k])
        for b in succ[k]:
            indeg[b] -= 1
            if indeg[b] == 0:
                free.append(b)
    if len(out) < len(items):                      # a cycle: fall back to depth for the rest
        rest = [it for it in items if it[0] not in {o[0] for o in out}]
        out += sorted(rest, key=lambda it: -it[1])
    return out


PROP_COL = {'box': '#c49a6c', 'table': '#7a5232', 'chair': '#8a5a34', 'door': '#6b4a33', 'wall': '#4a4038',
            'beam': '#8b6b4a', 'water': '#2f5d7c', 'puddle': '#33424f', 'ball': '#d9643a', 'cup': '#e8e2d6',
            'coin': '#d8b04a', 'book': '#7a2f2f', 'plate': '#e8e2d6', 'stick': '#9b7b52', 'fence': '#7d6a52',
            'hoop': '#d9643a', 'clock': '#e8e2d6', 'lamp': '#d9c27a', 'candle': '#efe6cf', 'hat': '#2a2a2a',
            'kite': '#c84a3a', 'pie': '#c99a5a', 'bench': '#7a5232', 'stairs': '#6b5a48', 'suitcase': '#5a3a2a'}
# sizes for props the bank gives none (cm): cuboid w,h,d
PROP_DEFAULT = {'cup': [8, 10, 8], 'coin': [3, 0.5, 3], 'book': [16, 3, 22], 'plate': [22, 1.5, 22], 'pie': [22, 5, 22],
                'clock': [30, 30, 4], 'lamp': [30, 150, 30], 'candle': [3, 14, 3], 'hat': [26, 12, 26], 'kite': [50, 60, 2],
                'suitcase': [45, 32, 18], 'key': [6, 1, 2], 'letter': [22, 0.5, 14], 'skull': [16, 18, 18], 'globe': [30, 30, 30],
                'bell': [12, 14, 12], 'broom': [6, 130, 6], 'mirror': [50, 120, 3], 'window': [80, 100, 4], 'screen': [120, 80, 4]}


def _shade(hexcol, f):
    c = [int(hexcol[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(v * f))) for v in c)


def _cuboid(cam, c, size, yaw, col):
    sx, sy, sz = size
    cy, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    def W(i, k, l):
        x, y, z = i * sx / 2, k * sy / 2, l * sz / 2
        return [c[0] + x * cy + z * sn, c[1] + y, c[2] - x * sn + z * cy]
    P = {(i, k, l): cam.P(W(i, k, l)) for i in (-1, 1) for k in (-1, 1) for l in (-1, 1)}
    faces = [([(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)], [0, 1, 0], 1.1),
             ([(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], [0, -1, 0], 0.6),
             ([(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)], [-sn, 0, -cy], 1.0),
             ([(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [sn, 0, cy], 0.92),
             ([(1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)], [cy, 0, -sn], 0.82),
             ([(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)], [-cy, 0, sn], 0.82)]
    return [([P[i][:2] for i in idx], _shade(col, f)) for idx, nv, f in faces if cam.dir(nv)[2] < 0]


def _disc(cam, c, r, normal, col, n=28):
    normal = nrm(normal)
    a = nrm(np.cross(normal, [0, 0, 1] if abs(normal[2]) < .9 else [1, 0, 0]))
    b = np.cross(normal, a)
    return [([cam.P(np.asarray(c) + a * r * math.cos(t) + b * r * math.sin(t))[:2] for t in np.linspace(0, 2 * math.pi, n, endpoint=False)], col)]


def props_polys(cam, q):
    t = q.get('type')
    pos = q.get('pos')
    if not pos:
        return []
    size = q.get('size')
    size = size if isinstance(size, list) else ([size] if size else None)
    rot = q.get('rot') or [0, 0, 0]
    col = PROP_COL.get(t, '#9a8a70')
    if t == 'ball':
        r = (size or [11])[0]
        c = cam.P(pos)
        return [([[c[0] + r * cam.s * math.cos(a), c[1] + r * cam.s * math.sin(a)] for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)], col)]
    if t == 'puddle':
        return _disc(cam, [pos[0], 0.2, pos[2]], (size or [30])[0], [0, 1, 0], col)
    if t == 'hoop':
        return _disc(cam, pos, 23, [0, 1, 0], col)
    if t in ('door', 'wall', 'fence', 'window', 'mirror', 'screen') and size and len(size) <= 2:
        w = size[0]
        h = size[1] if len(size) > 1 else 100
        yaw = rot[1] + (90 if abs(rot[0]) == 90 and t == 'wall' else 0)
        return _cuboid(cam, [pos[0], pos[1] + h / 2, pos[2]], [w, h, 4], yaw, col)
    if t == 'chair':
        y = pos[1]
        c = [pos[0], y + 45, pos[2]]
        out = _cuboid(cam, c, [44, 4, 44], rot[1], col)
        for dx in (-19, 19):
            for dz in (-19, 19):
                out += _cuboid(cam, [pos[0] + dx, y + 22, pos[2] + dz], [3, 44, 3], rot[1], _shade(col, .8))
        out += _cuboid(cam, [pos[0], y + 70, pos[2] - 20], [44, 46, 3], rot[1], col)
        return out
    if t == 'bench':
        return _cuboid(cam, [pos[0], pos[1] + 45, pos[2]], (size if size and len(size) == 3 else [120, 6, 40]), rot[1], col)
    if size and len(size) == 3:
        c = list(pos)
        if c[1] - size[1] / 2 < 0 and not q.get('held'):
            c[1] = size[1] / 2               # some props give their base, not their centre
        return _cuboid(cam, c, size, rot[1], col)
    d = PROP_DEFAULT.get(t)
    if d:
        return _cuboid(cam, pos, d, rot[1], col)
    return []
