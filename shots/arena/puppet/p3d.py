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

    def __init__(self, bg=(23, 25, 31)):
        self.im = Image.new('RGBA', (W * SS, H * SS), bg + (255,))
        self.d = ImageDraw.Draw(self.im)

    def _poly(self, pts, fill, grow=0.0):
        P = [(p[0] * SS, p[1] * SS) for p in (vec.offset(pts, grow) if grow else pts)]
        if len(P) >= 3:
            self.d.polygon(P, fill=fill)

    def card(self, polys, fill, rim=2.4, ink=1.3, rim_col=None):
        polys = [p for p in polys if len(p) >= 3]
        for p in polys:
            self._poly(p, vec._hex(rim_col or vec.RIM), rim + ink)
        for p in polys:
            self._poly(p, vec._hex(C['ink']), ink)
        for p in polys:
            self._poly(p, vec._hex(fill))

    def line(self, pts, col, w):
        self.d.line([(p[0] * SS, p[1] * SS) for p in pts], fill=vec._hex(col), width=max(1, int(w * SS)), joint='curve')

    def disc(self, c, r, col, ink=None):
        x, y = c[0] * SS, c[1] * SS
        if ink:
            self.d.ellipse([x - (r + 1) * SS, y - (r + 1) * SS, x + (r + 1) * SS, y + (r + 1) * SS], fill=vec._hex(ink))
        self.d.ellipse([x - r * SS, y - r * SS, x + r * SS, y + r * SS], fill=vec._hex(col))

    def brad(self, c, r):
        self.disc(c, r, '#b8902f', ink='#5a4314')
        self.disc((c[0] - r * .25, c[1] - r * .25), r * .35, '#f1d27a')

    def paste(self, img, M, t):
        """Affine-paste an RGBA image: screen = M @ card + t (screen px)."""
        Ms = M * SS
        ts = np.asarray(t) * SS
        Mi = np.linalg.inv(Ms)
        ti = -Mi @ ts
        L = img.transform(self.im.size, Image.AFFINE, (Mi[0, 0], Mi[0, 1], ti[0], Mi[1, 0], Mi[1, 1], ti[1]), resample=Image.BICUBIC)
        self.im.alpha_composite(L)
        return np.asarray(L.getchannel('A')) > 128

    def result(self):
        return self.im.resize((W, H), Image.LANCZOS).convert('RGB')


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
            p, miss = LIBR.pick(self.parts, 'head', view='front', expression=expr)
            mirror = False
        elif aa < 125:
            p, miss = LIBR.pick(self.parts, 'head', view='threequarter_R', expression=expr)
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
        # uniform scale from the head's 3D size, not its foreshortened screen length
        L3 = np.linalg.norm(j['headTop'] - j['neckBase']) * CANON['head']['scale'] * cam.s
        k = L3 / np.linalg.norm(crown - neck)
        v = B - A
        th = math.atan2(v[1], v[0]) - math.atan2(crown[1] - neck[1], crown[0] - neck[0])
        if np.linalg.norm(v) < 0.35 * L3:            # head pointing at or away from the lens: keep it upright
            th = 0.0
        R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]]) * k
        self._head_mask = pt.paste(img, R, A - R @ neck)
        return {'head': p['id'] + (' (mirrored)' if mirror else ''), 'view_angle': round(ang), 'expression': expr,
                'missing': miss}

    # ---------------------------------------------------------------- frame
    def render(self, f, yaw=None, elev=None, zoom=None, centre=None, props=True, floor=True):
        cam = Camera(self.V['view'], yaw, elev, zoom, centre)
        pt = Painter()
        notes = []
        if floor:
            y0 = cam.P([cam.c[0], 0, cam.c[2]])[1]
            fl = [cam.P([cam.c[0] + x, 0, cam.c[2] + z])[:2] for x, z in ((-400, -400), (400, -400), (400, 400), (-400, 400))]
            pt.d.polygon([(p[0] * SS, p[1] * SS) for p in fl], fill=(31, 34, 41, 255))
        fr = self.V['frames'][f]
        boxes = self.boxes(cam, fr) if props else []
        for p in boxes:
            if not p['held']:
                self.draw_box(pt, p)
        for aid, a in self.actors(f):
            j, Rc, R0 = self.frames_of(a)
            near = 'L' if cam.P(j['shoulderL'])[2] < cam.P(j['shoulderR'])[2] else 'R'
            far = 'R' if near == 'L' else 'L'
            # floor shadow
            c = cam.P([j['pelvis'][0], 0, j['pelvis'][2]])
            pt.d.ellipse([(c[0] - 26 * cam.s) * SS, (c[1] - 5 * cam.s) * SS, (c[0] + 26 * cam.s) * SS, (c[1] + 5 * cam.s) * SS], fill=(12, 13, 16, 255))
            hands = {'L': {'shape': a['hand']['L'], 'grip': a['hand']['gL'], 'palm': a['hand']['pL'] or 'in'},
                     'R': {'shape': a['hand']['R'], 'grip': a['hand']['gR'], 'palm': a['hand']['pR'] or 'in'}}
            K = CANON['limbs']

            def arm(s):
                out = R0['x'] * (1 if s == 'L' else -1)
                self.limb(pt, cam, j['shoulder' + s], j['elbow' + s], *K['uarm'], pipe_dir=out, brads=[j['shoulder' + s], j['elbow' + s]])
                self.limb(pt, cam, j['elbow' + s], j['wrist' + s], *K['farm'], pipe_dir=out, cuff=K['cuff'])
                self.hand(pt, cam, j, Rc, s, hands[s])

            def leg(s):
                out = R0['x'] * (1 if s == 'L' else -1)
                self.limb(pt, cam, j['knee' + s], j['ankle' + s], *K['shin'], pipe_dir=out, brads=[j['knee' + s]])
                self.boot(pt, cam, j, s, nrm(j['knee' + s] - j['ankle' + s]))
                self.limb(pt, cam, j['hip' + s], j['knee' + s], *K['thigh'], pipe_dir=out)

            arm(far)
            leg(far)
            leg(near)
            self.shorts(pt, cam, j, R0)
            self.vest(pt, cam, j, Rc, R0)
            pt.brad(cam.P(j['shoulder' + near])[:2], 1.3 * cam.s)
            info = self.head(pt, cam, j, a, a.get('face'), a.get('effort', 0))
            for p in boxes:
                if p['held'] and p['held'].startswith(aid + '.'):
                    self.draw_box(pt, p)
                    # staging check on the pixels: how much of the drawn head does the
                    # carried box cover? The skeleton's nose sits behind the drawn face,
                    # so testing joints missed it (critic, p3d turn 4).
                    bm = Image.new('L', pt.im.size, 0)
                    dd = ImageDraw.Draw(bm)
                    for poly, _ in p['polys']:
                        dd.polygon([(q[0] * SS, q[1] * SS) for q in poly], fill=255)
                    hm = self._head_mask
                    cover = float((np.asarray(bm) > 0)[hm].mean()) if hm.any() else 0.0
                    if cover > 0.15:
                        info['face_hidden_by'] = f"{p['id']} ({cover:.0%} of the head)"
            arm(near)
            notes.append(dict(info, actor=aid, near=near, hands=hands))
        return pt.result(), notes

    def boxes(self, cam, fr):
        out = []
        for pid, q in fr.get('p', {}).items():
            if q.get('type') != 'box' or not q.get('pos') or not q.get('size'):
                continue
            (sx, sy, sz), (cx, cy, cz) = q['size'], q['pos']
            Pt = {(i, k, l): cam.P([cx + i * sx / 2, cy + k * sy / 2, cz + l * sz / 2]) for i in (-1, 1) for k in (-1, 1) for l in (-1, 1)}
            faces = {'top': ([(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)], [0, 1, 0]),
                     'bottom': ([(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], [0, -1, 0]),
                     'a': ([(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)], [0, 0, -1]),
                     'b': ([(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [0, 0, 1]),
                     'c': ([(1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)], [1, 0, 0]),
                     'd': ([(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)], [-1, 0, 0])}
            shade = {'top': '#d9b483', 'bottom': '#8a6a46', 'a': '#c49a6c', 'b': '#b88e60', 'c': '#a77f55', 'd': '#a77f55'}
            polys = [([Pt[i][:2] for i in idx], shade[k]) for k, (idx, nv) in faces.items() if cam.dir(nv)[2] < 0]
            out.append({'id': pid, 'held': q.get('held'), 'polys': polys})
        return out

    def draw_box(self, pt, p):
        for poly, col in p['polys']:
            pt.d.polygon([(q[0] * SS, q[1] * SS) for q in poly], fill=vec._hex(col), outline=vec._hex('#1a120b'))


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
