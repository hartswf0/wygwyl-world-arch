"""One rig, any skin: the 3D solve places and layers the cards; the cards are the look.

    from cardrig import CardRig
    img, notes = CardRig('ACT-016', cast={'A': 'man', 'B': 'poet'}).render(40)

The rig is the Bolas bank in 3D (p3d.Puppet): joints, local frames, camera, depth
order, hands, heads by view and expression. A SKIN (skins.json) says which drawn
card each bone wears and where its sockets are. Every card is:

  * scaled so its A->B equals that bone's 3D length: cards cut at different
    scales come out on one body, whichever character they belong to;
  * turned to the bone's angle on screen, pinned A on the joint;
  * squashed along the bone (never across it) when the bone points at the camera,
    0.5 to 1.0 of its length: foreshortening without smearing the art;
  * mirrored when the body faces screen-left, so the drawn side faces out;
  * layered by depth with the cut-out rules in p3d.depth_order.

So the man and the poet run the same 32 challenges, and can share a scene.
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3d, propcards
from p3d import nrm

SKINS = json.load(open(os.path.join(HERE, 'skins.json')))
SQUASH_MIN = 0.5


class CardRig(p3d.Puppet):
    def __init__(self, act, cast=None):
        super().__init__(act)
        self.cast = cast or cast_by_name(self.V['actors'])
        self.actor_scale = {a['id']: a.get('scale', 1.0) for a in self.V['actors']}
        self._cards = {}

    def card(self, path):
        if path not in self._cards:
            self._cards[path] = kraft_edge(Image.open(os.path.join(p3d.SHOTS, path)).convert('RGBA'))
        return self._cards[path]

    def place(self, pt, cam, spec, A3, B3, cm, mirror=False, width=1.0, sockets=('A', 'B')):
        """Pin card socket A on A3, its A->B along A3->B3; uniform scale from the 3D length,
        then squash along the bone by the foreshortening."""
        img = self.card(spec['file'])
        a_c = np.array(spec[sockets[0]], float)
        b_c = np.array(spec[sockets[1]], float)
        u = b_c - a_c
        Lc = np.linalg.norm(u)
        a, b = cam.P(A3)[:2], cam.P(B3)[:2]
        v = b - a
        Ls = np.linalg.norm(v)
        k = cm * cam.s / Lc                       # card px -> screen px at full length
        if spec.get('w'):
            # hold the drawn width to the skin's width, measured across this card's own axis
            width = width * spec['w'] * cam.s / max(k * self.ink_width(spec['file'], u), 1e-6)
        sq = float(np.clip(Ls / max(k * Lc, 1e-6), SQUASH_MIN, 1.0))
        # card frame: rotate so u points down (+y), mirror x if asked, scale, rotate to v
        th0 = math.atan2(u[0], u[1])
        R0 = np.array([[math.cos(th0), -math.sin(th0)], [math.sin(th0), math.cos(th0)]])
        F = np.diag([-1.0 if mirror else 1.0, 1.0])
        S = np.diag([k * width, k * sq])
        if Ls < 1e-3:
            v = np.array([0.0, 1.0])
        th1 = math.atan2(v[1], v[0]) - math.pi / 2
        R1 = np.array([[math.cos(th1), -math.sin(th1)], [math.sin(th1), math.cos(th1)]])
        M = R1 @ S @ F @ R0
        pt.paste(img, M, a - M @ a_c)
        return sq

    def ink_width(self, path, u):
        key = (path, round(float(u[0]), 1), round(float(u[1]), 1))
        if key not in self._cards:
            A = np.asarray(self.card(path))[:, :, 3] > 128
            ys, xs = np.nonzero(A)
            n = np.array([-u[1], u[0]]) / np.linalg.norm(u)
            d = xs * n[0] + ys * n[1]
            self._cards[key] = float(np.percentile(d, 99) - np.percentile(d, 1))
        return self._cards[key]

    def facing_left(self, cam, fwd):
        return cam.dir(fwd)[0] < 0

    def view_of(self, cam, fwd):
        d = cam.dir(fwd)
        ang = math.degrees(math.atan2(d[0], -d[2]))
        aa = abs(ang)
        name = 'front' if aa < 30 else 'threequarter' if aa < 65 else 'profile' if aa < 120 else 'threequarter_back' if aa < 150 else 'back'
        return name, ang

    # ------------------------------------------------------------------ actor
    def actor_items(self, pt, cam, aid, a, add, after, notes, skin):
        S = SKINS[skin]
        j, Rc, R0 = self.frames_of(a)
        z = lambda p: cam.P(p)[2]
        near = 'L' if z(j['shoulderL']) < z(j['shoulderR']) else 'R'
        left = self.facing_left(cam, R0['fwd'])
        hands = {s: {'shape': a['hand'][s], 'grip': a['hand']['g' + s], 'palm': a['hand']['p' + s] or 'in'} for s in 'LR'}
        info = {'actor': aid, 'skin': skin, 'near': near, 'hands': hands, 'squash': {}}
        notes.append(info)
        c = cam.P([j['pelvis'][0], 0, j['pelvis'][2]])
        pt.ellipse_raw(c, 26 * cam.s, 5 * cam.s, (70, 63, 55, 255))
        P = lambda k: f'{aid}.{k}'

        def limb(kind, s, A3, B3):
            K = S[kind]
            if K.get('hidden'):
                return
            spec = dict(K[s], cm=K['cm'], w=K.get('w')) if s in K else K
            if s in K and left:
                # a per-side card seen from the other side: the other side's drawing, mirrored
                spec = dict(K['R' if s == 'L' else 'L'], cm=K['cm'], w=K.get('w'))

            def fn(kind=kind, s=s, A3=A3, B3=B3, spec=spec):
                info['squash'][kind + s] = round(self.place(pt, cam, spec, A3, B3, spec['cm'], mirror=left), 2)
            add(f'{kind}{s}', z((A3 + B3) / 2), fn)

        for s in 'LR':
            limb('uarm', s, j['shoulder' + s], j['elbow' + s])
            limb('farm', s, j['elbow' + s], j['wrist' + s])
            limb('thigh', s, j['hip' + s], j['knee' + s])
            limb('shin', s, j['knee' + s], j['ankle' + s])

            def boot(s=s, j=j):
                B = S['boot']
                he, to, an = j['heel' + s], j['toe' + s], j['ankle' + s]
                dsc = cam.P(to)[:2] - cam.P(he)[:2]
                foot3 = np.linalg.norm(to - he) * cam.s
                if np.linalg.norm(dsc) < 0.45 * foot3 and 'front' in B:
                    # the foot points at or away from the camera: the front or back card, upright
                    spec = B['front'] if cam.dir(to - he)[2] < 0 else B['back']
                    self.place(pt, cam, spec, an, an - np.array([0, 8.0, 0]), 8.0 * B['cm'] / 27.0 * 1.0, sockets=('A', 'sole'))
                    return
                raised = (he[1] - to[1]) > 3.0
                spec = B['toe'] if raised and 'toe' in B else B['flat']
                img_left = dsc[0] < 0
                # pin the ankle brad, heel->toe along the projected foot, scale from the 3D foot
                hc, tc, ac = (np.array(spec[k], float) for k in ('heel', 'toe', 'A'))
                u = tc - hc
                k = B['cm'] * cam.s / np.linalg.norm(u)
                v = dsc if np.linalg.norm(dsc) > 1e-3 else np.array([1.0, 0])
                F = np.diag([-1.0, 1.0]) if img_left else np.eye(2)
                uu = F @ u
                th = math.atan2(v[1], v[0]) - math.atan2(uu[1], uu[0])
                R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
                sq = float(np.clip(np.linalg.norm(dsc) / max(foot3, 1e-6), 0.35, 1.0))
                M = R @ np.diag([k * sq, k]) @ F if True else None
                pt.paste(self.card(spec['file']), M, cam.P(an)[:2] - M @ ac)
            add(f'boot{s}', z((j['heel' + s] + j['toe' + s]) / 2), boot)

            def hand(s=s, j=j):
                if S['hand'] == 'code':
                    self.hand(pt, cam, j, Rc, s, hands[s])
                elif 'bank' in S['hand']:
                    H = S['hand']
                    shape = H['shape'].get(hands[s]['shape'] or 'relaxed', 'relaxed')
                    spec = {'file': H['bank'].format(shape=shape), 'A': H['A'], 'B': H['B']}
                    w = j['wrist' + s]
                    self.place(pt, cam, spec, w, w + nrm(w - j['elbow' + s]) * H['cm'], H['cm'], mirror=left)
                else:
                    H = dict(S['hand'])
                    A = json.load(open(os.path.join(p3d.SHOTS, 'weave/assets/assets.json')))
                    sk = next(x for x in A['assets'] if x['file'].endswith(os.path.basename(H['file'])))['sockets']
                    spec = {'file': H['file'], 'A': sk[H['A']], 'B': sk[H['B']]}
                    w = j['wrist' + s]
                    tip = w + nrm(w - j['elbow' + s]) * H['cm']
                    self.place(pt, cam, spec, w, tip, H['cm'], mirror=left)
            add(f'hand{s}', z(j['wrist' + s] + nrm(j['wrist' + s] - j['elbow' + s]) * 8), hand)
            after += [(P(f'thigh{s}'), P('pelvis')), (P(f'shin{s}'), P(f'boot{s}')), (P(f'shin{s}'), P(f'thigh{s}'))]
            if z(j['wrist' + s]) <= z(j['elbow' + s]) + 6:
                after.append((P(f'uarm{s}'), P(f'farm{s}')))
            if z(j['wrist' + s] + nrm(j['wrist' + s] - j['elbow' + s]) * 8) <= z(j['wrist' + s]) + 4:
                after.append((P(f'farm{s}'), P(f'hand{s}')))
            if z(j['elbow' + s]) > z(j['head']) - 15.0:
                after.append((P(f'uarm{s}'), P('head')))
            far = s != near
            if far:
                # the far arm and leg stay behind the body unless the hand really crosses in
                # front of it (critic: a third hand pasted on the hip)
                crosses = z(j['wrist' + s]) < z(j['chest']) - 10.0
                if not crosses:
                    after += [(P(f'{k}{s}'), P('torso')) for k in ('uarm', 'farm', 'hand')]
                after += [(P(f'{k}{s}'), P('torso')) for k in ('thigh', 'shin')]
                if S.get('pelvis'):
                    after += [(P(f'{k}{s}'), P('pelvis')) for k in ('thigh',) + (() if crosses else ('uarm', 'farm', 'hand'))]
            if S.get('pelvis') and S['pelvis'].get('skirt'):
                # under a skirt the thigh only shows below the hem: keep it behind
                after.append((P(f'thigh{s}'), P('pelvis')))

        def pelvis(j=j, R0=R0):
            Pv = S.get('pelvis')
            if not Pv:
                return
            vname, _ = self.view_of(cam, R0['fwd'])
            width = 1.0 if vname in ('front', 'back') else Pv.get('profile_width', 0.7) if vname == 'profile' else 0.85
            top = j['pelvis'] + R0['up'] * (8.0 if Pv.get('skirt') else 4.0)
            if Pv.get('skirt'):
                knees = (j['kneeL'] + j['kneeR']) / 2
                d = nrm(nrm(knees - top) + (-R0['up']))
            else:
                d = -R0['up']
            self.place(pt, cam, Pv, top, top + d * Pv['cm'], Pv['cm'], mirror=left, width=width)
        if S.get('pelvis'):
            add('pelvis', z(j['pelvis']), pelvis)
        else:
            # no pelvis card: the shorts-thighs tuck under the vest hem
            after += [(P(f'thigh{s}'), P('torso')) for s in 'LR']

        # where the torso card's collar lands on screen: the head hangs from it
        hem0 = j['pelvis'] + R0['up'] * 6.0
        hem_s, neck_s = cam.P(hem0)[:2], cam.P(j['neckBase'])[:2]
        axis = neck_s - hem_s
        Ls = np.linalg.norm(axis)
        axis = axis / Ls if Ls > 1e-3 else np.array([0.0, -1.0])
        # the torso card squashes no shorter than SQUASH_MIN of its length, so when he bends
        # toward the camera its collar lands above the skeleton's neck: dock where the card is
        collar = hem_s + axis * max(Ls, SQUASH_MIN * S['torso']['cm'] * cam.s)
        H = S.get('head_dock', {})
        dock = {'at': collar - axis * 0 + axis * (-H.get('tuck_cm', 7.0) * cam.s),
                'axis': axis, 'max_tilt': H.get('max_tilt', 30), 'scale': H.get('scale', 1.0)}
        if H.get('view_from_torso'):
            # the head turns with the torso, one view at a time (critic: a front face on a
            # profile body, the back of the head flickering in for single frames)
            dock['view'] = self.view_of(cam, Rc['fwd'])

        def torso(j=j, R0=R0, Rc=Rc):
            T = S['torso']
            vname, ang = self.view_of(cam, Rc['fwd'])
            near = {'threequarter': ('front', 'profile') if abs(ang) < 47 else ('profile', 'front'),
                    'threequarter_back': ('profile', 'back') if abs(ang) < 135 else ('back', 'profile')}
            spec = T.get(vname) or next((T[n] for n in near.get(vname, ()) if n in T), None) or T.get('profile') or T['front']
            hem = j['pelvis'] + R0['up'] * 6.0
            mirror = (ang < 0) if vname in ('threequarter', 'profile', 'threequarter_back') else False
            if T.get('faces') == 'front':
                mirror = left
            self.place(pt, cam, spec, hem, j['neckBase'], T['cm'], mirror=mirror)
            info['torso_view'] = vname
        add('torso', z(j['chest']), torso)

        def head(a=a, j=j):
            Hs = S['head']
            if Hs == 'library':
                self._head_dock = dock
                info.update(self.head(pt, cam, j, a, a.get('face'), a.get('effort', 0)))
                self._head_dock = None
            elif 'bank' in Hs:
                vname, ang = self.view_of(cam, Rc['fwd'])
                expr = Hs['expr'].get(p3d.face_to_expression(a.get('face') or {}, a.get('effort', 0)), 'neutral')
                view = 'front' if vname == 'front' else 'side'
                spec = {'file': Hs['bank'][view].format(e=expr), 'A': Hs['neck'], 'B': Hs['crown']}
                L = np.linalg.norm(j['headTop'] - j['neckBase']) * Hs.get('size', 1.0)
                self.place_upright(pt, cam, spec, j['neckBase'], j['neckBase'] + nrm(j['headTop'] - j['neckBase']) * L, L,
                                   mirror=(left if view == 'side' else False), upright_axis=axis)
                info['head'] = spec['file']
            else:
                hf = nrm(a['hfwd'])
                d = cam.dir(hf)
                spec = {'file': Hs['file'], 'A': Hs['neck'], 'B': Hs['crown']}
                L = np.linalg.norm(j['headTop'] - j['neckBase'])
                self.place_upright(pt, cam, spec, j['neckBase'] - nrm(j['headBase'] - j['neckBase']) * 3, j['headTop'], L, mirror=d[0] < 0)
                info['head'] = Hs['file'] + (' (mirrored)' if d[0] < 0 else '')
            info['_head_snapshot'] = (self._head_mask, np.asarray(pt.im)[self._head_mask].copy())
        add('head', z(j['head']), head)
        # the neck tab tucks under the collar: the head is drawn before the torso card
        # (a real cut-out puts the head's tab behind the vest), the arms still go by depth
        after += [(P('pelvis'), P('torso'))] + ([(P('head'), P('torso'))] if S.get('head_dock', {}).get('under_collar') else [(P('torso'), P('head'))])
        return j

    def place_upright(self, pt, cam, spec, A3, B3, cm, mirror=False, upright_axis=None):
        """A head: uniform scale (never squashed), turned to the neck->crown direction."""
        img = self.card(spec['file'])
        a_c, b_c = np.array(spec['A'], float), np.array(spec['B'], float)
        if mirror:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
            a_c[0], b_c[0] = img.size[0] - a_c[0], img.size[0] - b_c[0]
        k = cm * cam.s / np.linalg.norm(b_c - a_c)
        a, b = cam.P(A3)[:2], cam.P(B3)[:2]
        v = b - a
        th = math.atan2(v[1], v[0]) - math.atan2(b_c[1] - a_c[1], b_c[0] - a_c[0])
        if np.linalg.norm(v) < 0.35 * k * np.linalg.norm(b_c - a_c):
            v = np.asarray(upright_axis, float) if upright_axis is not None else np.array([0.0, -1.0])
            th = math.atan2(v[1], v[0]) - math.atan2(b_c[1] - a_c[1], b_c[0] - a_c[0])
        R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]]) * k
        self._head_mask = pt.paste(img, R, a - R @ a_c)

    def retarget(self, a, skin):
        """One height per person: scale the actor's joints about the floor point under its
        pelvis so the skin's height holds in every take, whichever Bolas dummy it plays
        (critic: the man was a giant in one take and child-sized in the next)."""
        S = SKINS[skin]
        H = S.get('height_cm')
        if not H:
            return a, 1.0
        J = [np.array(q, float) if q is not None else None for q in a['j']]
        top = J[p3d.J['headTop']]
        heel = min(J[p3d.J['heelL']][1], J[p3d.J['heelR']][1])
        # the actor's standing height, from the bank's own scale (Bola 1, Shim 1.06, Dot .72)
        k = H / (186.0 * self.actor_scale.get(a.get('_id'), 1.0))
        base = np.array([J[0][0], 0.0, J[0][2]])
        b = dict(a)
        b['j'] = [None if q is None else list(base + (q - base) * k) for q in J]
        return b, k

    def boxes(self, cam, fr):
        """Props the Crash Lab's way (propcards.py): its pivots, rotation and states, in the
        cast's cardboard, instead of flat-shaded cuboids."""
        return propcards.prop_items(cam, fr.get('p', {}), getattr(self, '_f', 0))

    def draw_box(self, pt, p):
        p['draw'](pt)

    def render(self, f, yaw=None, elev=None, zoom=None, centre=None, props=True, floor=True, window=None):
        cam = p3d.Camera(self.V['view'], yaw, elev, zoom, centre)
        self._f = f
        # a warm paper stage: the man's black cards vanished on near-black (critic, study turn 2)
        pt = p3d.Painter(bg=(86, 80, 72), window=window)
        notes = []
        if floor:
            fl = [cam.P([cam.c[0] + x, 0, cam.c[2] + zz])[:2] for x, zz in ((-3000, -3000), (3000, -3000), (3000, 3000), (-3000, 3000))]
            pt.poly_raw(fl, (112, 104, 93, 255))
        fr = dict(self.V['frames'][f])
        # retarget every actor first, so held props can follow the hand that holds them
        actors, wrists, orig = [], {}, {}
        for aid, a in self.actors(f):
            a = dict(a, _id=aid)
            skin = self.cast.get(aid, 'man')
            b, k = self.retarget(a, skin)
            actors.append((aid, b, skin))
            for s in 'LR':
                orig[(aid, s)] = np.array(a['j'][p3d.J['wrist' + s]], float)
                wrists[(aid, s)] = np.array(b['j'][p3d.J['wrist' + s]], float)
        # a held prop keeps its offset from the holding hand, after retargeting
        P2 = {}
        for pid, q in fr.get('p', {}).items():
            q = dict(q)
            h = q.get('held')
            if h and q.get('pos'):
                who, side = h.split('.')[0], (h.split('.')[1] if '.' in h else 'R')[:1]
                if (who, side) in wrists:
                    q['pos'] = list(wrists[(who, side)] + (np.array(q['pos'], float) - orig[(who, side)]))
            P2[pid] = q
        fr['p'] = P2
        boxes = self.boxes(cam, fr) if props else []
        groups = []      # each actor is layered as a whole (critic: two actors fused into one creature)
        for aid, a, skin in actors:
            items, after = [], []

            def add(key, zz, fn, aid=aid, items=items):
                items.append([f'{aid}.{key}', zz, fn])
            j = self.actor_items(pt, cam, aid, a, add, after, notes, skin)
            for p in boxes:
                if p['held'] and p['held'].startswith(aid + '.'):
                    items.append(['box.' + p['id'], p['z'], lambda p=p: self.draw_box(pt, p)])
                    after.append((f'{aid}.torso', 'box.' + p['id']))
            groups.append((cam.P(j['pelvis'])[2], p3d.depth_order(items, after)))
        for p in boxes:
            if not p['held']:
                groups.append((p['z'], [['box.' + p['id'], p['z'], lambda p=p: self.draw_box(pt, p)]]))
        for zz, order in sorted(groups, key=lambda g: -g[0]):
            for key, z2, fn in order:
                fn()
        final = np.asarray(pt.im)
        for info in notes:
            snap = info.pop('_head_snapshot', None)
            if snap is not None and snap[0].any():
                m, before = snap
                cov = float((np.abs(final[m].astype(int) - before.astype(int)).sum(axis=1) > 30).mean())
                info['face_covered'] = round(cov, 3)
        return pt.result(), notes


BY_NAME = {'Bola': 'poet', 'Shim': 'man', 'Dot': 'dot'}


def cast_by_name(actors):
    """Each Bolas dummy is always played by the same person: Bola (she) by the poet, Shim
    (he) by the man, Dot by the little one; extras alternate man and poet. Casting went by
    actor id before, and Dot (id C) fell back to the man (rig v2 test, ACT-019)."""
    out, n = {}, 0
    for a in actors:
        if a['name'] in BY_NAME:
            out[a['id']] = BY_NAME[a['name']]
        else:
            out[a['id']] = ('man', 'poet')[n % 2]
            n += 1
    return out


def kraft_edge(img, band=3):
    """The cut edge of a card is kraft cardboard, not a white glow (critic: pale seams and
    white bolts made the man read as a glowing Tron suit). Light, unsaturated pixels within
    `band` px of the cut become kraft brown; a fully white fringe is dropped."""
    from scipy import ndimage as nd
    a = np.asarray(img).copy()
    A = a[..., 3] > 40
    edge = A & ~nd.binary_erosion(A, iterations=band)
    rgb = a[..., :3].astype(int)
    light = (rgb.max(axis=2) > 150) & (np.ptp(rgb, axis=2) < 70)
    white = (rgb.min(axis=2) > 215)
    outer = A & ~nd.binary_erosion(A, iterations=1)
    a[..., 3] = np.where(outer & white, 0, a[..., 3])
    fix = edge & light & ~(outer & white)
    a[fix, 0], a[fix, 1], a[fix, 2] = 132, 98, 62
    return Image.fromarray(a)
