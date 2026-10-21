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
import p3d, propcards, dummyhead, fusion, fx
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

    @staticmethod
    def torso_card(T, vname, ang):
        """Which of the skin's torso cards a view uses (the head follows the same choice)."""
        near = {'threequarter': ('front', 'profile') if abs(ang) < 47 else ('profile', 'front'),
                'threequarter_back': ('profile', 'back') if abs(ang) < 135 else ('back', 'profile'),
                'back': ('back', 'profile'), 'profile': ('profile', 'front'), 'front': ('front',)}
        for n in (vname,) + near.get(vname, ()):
            if n in T and isinstance(T[n], dict):
                return n
        return 'front'

    BOUNDS = (30, 65, 120, 150)

    def body_view(self, cam, Rc, R0, aid):
        """The view a body is seen in, for its torso and head cards: the horizontal facing of
        the chest, or of the pelvis when the chest is bent over (a crouching chest points
        at the floor, and its front/back flipped every frame: critic, T139), with a hold of
        HYST degrees past each boundary so a view can't strobe."""
        f = None
        for v in (Rc['fwd'], R0['fwd'], Rc['up']):
            h = np.array([v[0], 0.0, v[2]])
            if np.linalg.norm(h) > 0.5:
                f = h / np.linalg.norm(h)
                break
        if f is None:
            f = nrm(np.array([Rc['fwd'][0], 0.0, Rc['fwd'][2]]) + 1e-6)
        d = cam.dir(f)
        ang = math.degrees(math.atan2(d[0], -d[2]))
        names = ('front', 'threequarter', 'profile', 'threequarter_back', 'back')
        aa = abs(ang)
        idx = sum(aa >= b for b in self.BOUNDS)
        last = self._views.get(aid) if hasattr(self, '_views') else None
        if last is not None and last != idx:
            # stay in the last view until the angle is HYST past the boundary between them
            b = self.BOUNDS[min(last, idx)]
            if abs(aa - b) < 8:
                idx = last
        self._views = getattr(self, '_views', {})
        self._views[aid] = idx
        return names[idx], ang

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
        # the shadow thins and fades as the body leaves the floor (critic, T160: floor shadows
        # under bodies that are declared to stand on nothing)
        lift = min(j[k][1] for k in ('heelL', 'heelR', 'toeL', 'toeR') if k in j)
        fade = float(np.clip(1 - lift / 45.0, 0, 1))
        if fade > 0.05:
            size = SKINS[skin].get('height_cm', 180) / 180.0 * (0.6 + 0.4 * fade)
            sh = Image.new('RGBA', pt.im.size, (0, 0, 0, 0))
            from PIL import ImageDraw as _D
            x, y = pt._xy(c)
            rx, ry = 26 * cam.s * size * p3d.SS, 5 * cam.s * size * p3d.SS
            _D.Draw(sh).ellipse([x - rx, y - ry, x + rx, y + ry], fill=(40, 34, 28, int(150 * fade)))
            pt.im.alpha_composite(sh)
        P = lambda k: f'{aid}.{k}'

        def limb(kind, s, A3, B3):
            K = S[kind]
            if K.get('hidden'):
                return
            spec = dict(K[s], cm=K['cm'], w=K.get('w')) if s in K else K
            if s in K and left:
                # a per-side card seen from the other side: the other side's drawing, mirrored
                spec = dict(K['R' if s == 'L' else 'L'], cm=K['cm'], w=K.get('w'))
            if 'bent' in K and kind == 'shin':
                # a deep knee bend wears the sheet's bunched-fabric shin (replacement, not a warp)
                th = nrm(j['knee' + s] - j['hip' + s])
                bend = math.degrees(math.acos(float(np.clip(np.dot(th, nrm(B3 - A3)), -1, 1))))
                if bend > K['bent'].get('from_deg', 75):
                    spec = dict(K['bent'], cm=K['cm'], w=K.get('w'))

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
                    # shaft top a little above the ankle brad, sole on the floor under the foot
                    top = an + np.array([0, 3.0, 0])
                    drop = max(6.0, top[1] - min(he[1], to[1]) + 1.0)
                    self.place(pt, cam, spec, top, top - np.array([0, drop, 0]), drop, sockets=('A', 'sole'))
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
                if isinstance(S['hand'], dict) and 'cards' in S['hand']:
                    self.card_hand(pt, cam, j, Rc, s, hands[s], S['hand'])
                elif S['hand'] == 'code':
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
            if isinstance(S['hand'], dict) and 'cards' in S['hand']:
                after.append((P(f'hand{s}'), P(f'farm{s}')))       # the eyelet tab sits under the cuff
            elif z(j['wrist' + s] + nrm(j['wrist' + s] - j['elbow' + s]) * 8) <= z(j['wrist' + s]) + 4:
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
            # and the head follows the torso CARD actually used: a 3/4-back body wears the
            # profile vest, so it gets the side head, not the back of the head (critic, T160/T175)
            tv, tang = self.body_view(cam, Rc, R0, aid)
            card = self.torso_card(S['torso'], tv, tang)
            hv = {'front': 'front' if tv == 'front' else 'threequarter', 'profile': 'profile', 'back': 'back'}.get(card, tv)
            dock['view'] = (hv, tang)

        def torso(j=j, R0=R0, Rc=Rc):
            T = S['torso']
            vname, ang = self.body_view(cam, Rc, R0, aid)
            spec = T[self.torso_card(T, vname, ang)]
            hem = j['pelvis'] + R0['up'] * 6.0
            mirror = (ang < 0) if vname in ('threequarter', 'profile', 'threequarter_back') else False
            width = 1.0
            if T.get('faces') == 'front':
                mirror = left
                # a front-only bodice seen side-on narrows, so the arms do not hang from the
                # middle of a full-width front view (critic: an arm pinned mid-chest)
                if 'profile_width' in T:
                    width = 1.0 - (1.0 - T['profile_width']) * min(1.0, abs(math.sin(math.radians(ang))))
            self.place(pt, cam, spec, hem, j['neckBase'], T['cm'], mirror=mirror, width=width)
            info['torso_view'] = vname
        add('torso', z(j['chest']), torso)

        def head(a=a, j=j):
            Hs = S['head']
            if Hs == 'library':
                self._head_dock = dock
                info.update(self.head(pt, cam, j, a, a.get('face'), a.get('effort', 0)))
                self._head_dock = None
            elif Hs.get('code') == 'dummy':
                dummyhead.draw(pt, cam, j, a, p3d.vec._hex(Hs['colour']), getattr(self, '_f', 0))
                c, r = cam.P(j['head']), np.linalg.norm(j['headTop'] - j['head']) * 1.05 * cam.s
                H_, W_ = pt.im.size[1], pt.im.size[0]
                yy, xx = np.ogrid[:H_, :W_]
                cx, cy = pt._xy(c)
                self._head_mask = (xx - cx) ** 2 + (yy - cy) ** 2 < (r * p3d.SS) ** 2
                info['head'] = 'dummy (Crash Lab face)'
            elif 'bank' in Hs:
                vname, ang = self.body_view(cam, Rc, R0, aid)
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
                if Hs.get('fusion') == 'poet':
                    # the painted plate with her eye plugged in: open, gaze and lid from the bank
                    img, key = fusion.poet_head(a.get('face'))
                    if key not in self._cards:
                        self._cards[key] = kraft_edge(img)
                    spec['file'] = key
                L = np.linalg.norm(j['headTop'] - j['neckBase'])
                self.place_upright(pt, cam, spec, j['neckBase'] - nrm(j['headBase'] - j['neckBase']) * 3, j['headTop'], L, mirror=d[0] < 0)
                info['head'] = Hs['file'] + (' (mirrored)' if d[0] < 0 else '')
            info['_head_snapshot'] = (self._head_mask, np.asarray(pt.im)[self._head_mask].copy())
        add('head', z(j['head']), head)
        # the neck tab tucks under the collar: the head is drawn before the torso card
        # (a real cut-out puts the head's tab behind the vest), the arms still go by depth
        after += [(P('pelvis'), P('torso'))] + ([(P('head'), P('torso'))] if S.get('head_dock', {}).get('under_collar') else [(P('torso'), P('head'))])
        return j

    def card_hand(self, pt, cam, j, Rc, s, state, H):
        """A drawn hand card on its eyelet: the shape from the bank, palm or back by which way
        the palm faces, mirrored so the thumb lands where the 3D hand's thumb is (Bolas
        gloveDraw's frame), scaled at one px-per-cm for every card."""
        if state['shape'] == 'hidden':
            return
        w, el = j['wrist' + s], j['elbow' + s]
        u = nrm(w - el)
        sg = 1 if s == 'L' else -1
        PALM = {'in': [-sg, 0, 0], 'out': [sg, 0, 0], 'down': [0, -1, 0], 'up': [0, 1, 0], 'fwd': [0, 0, 1], 'back': [0, 0, -1]}
        v = PALM.get(state['palm'], PALM['in'])
        n = Rc['x'] * v[0] + Rc['up'] * v[1] + Rc['fwd'] * v[2]
        n = n - u * np.dot(n, u)
        n = nrm(n) if np.linalg.norm(n) > .1 else nrm(np.cross(u, [0, 1, 0]))
        thumb = nrm(np.cross(u, n)) * (-1 if s == 'L' else 1)
        name = H['shape'].get(state['shape'] or '', 'relaxed')
        if name == 'open':
            name = 'open_palm' if cam.dir(n)[2] < 0 else 'open_back'
        spec = H['cards'].get(name) or H['cards']['relaxed']
        a_c, b_c = np.array(spec['A'], float), np.array(spec['B'], float)
        cm = np.linalg.norm(b_c - a_c) / H['px_per_cm']
        # which side of the card's axis the thumb is drawn on, after place()'s rotation to +y
        uc = b_c - a_c
        th0 = math.atan2(uc[0], uc[1])
        R0 = np.array([[math.cos(th0), -math.sin(th0)], [math.sin(th0), math.cos(th0)]])
        side = float(np.sign((R0 @ np.array(spec['thumb'], float))[0]) or 1.0)
        a2, b2 = cam.P(w)[:2], cam.P(w + u * cm)[:2]
        vv = b2 - a2
        th1 = math.atan2(vv[1], vv[0]) - math.pi / 2
        canon_x = np.array([math.cos(th1), math.sin(th1)])
        ts = cam.P(w + thumb * 5)[:2] - a2
        mirror = side * float(np.dot(ts, canon_x)) < 0
        self.place(pt, cam, spec, w, w + u * cm, cm, mirror=mirror)

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
        # sitting: scale about the seat, so the seat stays under the actor and short legs
        # dangle (critic, T166: the little one hovered above the bench)
        for top, (sx, sz), half in getattr(self, '_seats', []):
            if J[0][1] < top + 30 and abs(J[0][0] - sx) < half + 10 and abs(J[0][2] - sz) < 40 and J[0][1] > top - 5:
                base = np.array([J[0][0], top, J[0][2]])
                break
        b = dict(a)
        b['j'] = [None if q is None else list(base + (q - base) * k) for q in J]
        return b, k

    def reflection(self, cam, pt, f, q):
        """What the glass shows: the actors as the mirror sees them (a second camera at the
        mirror, looking along its normal, at the bank's lagged frame), mapped onto the glass by
        its corners. Under an orthographic camera that mapping is exact, and a point in front of
        the mirror lands where its reflection would. Returns an RGBA layer for the main window."""
        st = q.get('state') or {}
        r = q.get('rot') or [0, 0, 0]
        Rm = propcards.rY(r[0]) @ propcards.rX(r[1]) @ propcards.rZ(r[2])
        c = np.array(q['pos'], float)
        n = Rm @ np.array([0, 0, 1.0])
        toward = -np.array([cam.dir(e)[2] for e in np.eye(3)])
        if np.dot(toward, n) <= 0.05:
            return None                                    # we see the back of the mirror
        sz = q.get('size') or [70, 180]
        w, h = sz[0], (sz[1] if len(sz) > 1 else 180)
        corners = [c + Rm @ np.array(v, float) for v in ((-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, h, 0), (-w / 2, h, 0))]
        g = max(0, f - int(st.get('lag', 0) or 0))
        yaw = math.degrees(math.atan2(n[0], n[2]))
        vc = p3d.Camera(self.V['view'], yaw=yaw, elev=0, centre=list(c + Rm @ np.array([0, h / 2, 0])))
        vc.s = cam.s
        V = np.array([vc.P(x)[:2] for x in corners])
        x0, y0 = V.min(0) - 2
        x1, y1 = V.max(0) + 2
        layer = p3d.Painter(bg=(0, 0, 0), window=(int(x0), int(y0), int(x1), int(y1)))
        layer.im = Image.new('RGBA', layer.im.size, (0, 0, 0, 0))
        from PIL import ImageDraw as _D
        layer.d = _D.Draw(layer.im)
        drew = False
        for aid, a in self.V['frames'][g]['a'].items():
            if np.dot(np.array(a['j'][0], float) - c, n) <= 0:
                continue                                   # behind the glass
            b, _ = self.retarget(dict(a, _id=aid), self.cast.get(aid, 'man'))
            items, after, notes = [], [], []
            add = lambda key, zz, fn, items=items: items.append([key, zz, fn])
            self.actor_items(layer, vc, aid, b, add, after, notes, self.cast.get(aid, 'man'))
            for key, zz, fn in p3d.depth_order(items, after):
                fn()
            drew = True
        if not drew:
            return None
        img = layer.im.resize((layer.w, layer.h), Image.LANCZOS)
        A = np.asarray(img).copy()
        tint = np.array([214, 222, 230], float)
        A[..., :3] = (A[..., :3] * 0.78 + tint * 0.22).astype(np.uint8)
        A[..., 3] = (A[..., 3] * 0.82).astype(np.uint8)
        img = Image.fromarray(A)
        # layer px -> main screen, through three of the glass's corners
        Pm = np.array([cam.P(x)[:2] for x in corners])
        Vl = V - np.array([layer.x0, layer.y0])
        M = np.column_stack([Pm[1] - Pm[0], Pm[3] - Pm[0]]) @ np.linalg.inv(np.column_stack([Vl[1] - Vl[0], Vl[3] - Vl[0]]))
        t = Pm[0] - M @ Vl[0]
        out = Image.new('RGBA', pt.im.size, (0, 0, 0, 0))
        tmp = p3d.Painter(bg=(0, 0, 0), window=(pt.x0, pt.y0, pt.x0 + pt.w, pt.y0 + pt.h))
        tmp.im = out
        tmp.paste(img, M, t)
        m = Image.new('L', out.size, 0)
        _D.Draw(m).polygon([tmp._xy(v) for v in Pm], fill=255)
        out.putalpha(Image.fromarray((np.asarray(out.getchannel('A')).astype(float) * np.asarray(m) / 255).astype(np.uint8)))
        return out

    def pool_at(self, j, pools):
        """The pool this actor stands in, if any (pelvis over its footprint)."""
        for q in pools:
            w, dp, d = (q.get('size') or [200, 80, 120]) + [200, 80, 120][len(q.get('size') or []):]
            if abs(j['pelvis'][0] - q['pos'][0]) < w / 2 and abs(j['pelvis'][2] - q['pos'][2]) < d / 2:
                return q
        return None

    def waterline(self, pt, cam, j, q, before):
        """Wading: whatever of the actor is under the surface is seen through the water, tinted
        and faint, cut by a ripple line (critic, T141: he walked on top of a blue slab)."""
        y = q['pos'][1]
        c = cam.P([j['pelvis'][0], y, j['pelvis'][2]])
        wy = int((c[1] - pt.y0) * p3d.SS)
        if wy >= pt.im.size[1]:
            return
        wy = max(0, wy)
        box = (0, wy, pt.im.size[0], pt.im.size[1])
        a = np.asarray(pt.im.crop(box)).astype(float)
        b = np.asarray(before.crop(box)).astype(float)
        tint = np.array([70, 120, 160, 255], float)
        drawn = (np.abs(a - b).sum(axis=2) > 6)[..., None]      # only the actor's own pixels
        under = np.where(drawn, b * 0.7 + (a * 0.55 + tint * 0.45) * 0.3, a)
        pt.im.paste(Image.fromarray(under.astype(np.uint8)), box[:2])
        r = 30 * cam.s
        pt.d.ellipse([pt._xy((c[0] - r, c[1] - r * .18)), pt._xy((c[0] + r, c[1] + r * .18))],
                     outline=(200, 225, 240, 255), width=max(2, int(1.2 * p3d.SS)))

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
        self._seats = []
        for q in fr.get('p', {}).values():
            if q.get('type') in ('bench', 'chair') and q.get('pos') and not q.get('held'):
                sz = q.get('size') if isinstance(q.get('size'), list) else None
                self._seats.append((q['pos'][1] + 46, (q['pos'][0], q['pos'][2]), (sz[0] / 2 if sz else 22)))
        # retarget every actor first, so held props can follow the hand that holds them
        actors, wrists, orig = [], {}, {}
        for aid, a in self.actors(f):
            a = dict(a, _id=aid)
            skin = self.cast.get(aid, 'man')
            b, k = self.retarget(a, skin)
            actors.append((aid, b, skin))
            for s, jn in (('L', 'wristL'), ('R', 'wristR'), ('h', 'headTop')):    # 'h': a hat held on the head
                orig[(aid, s)] = np.array(a['j'][p3d.J[jn]], float)
                wrists[(aid, s)] = np.array(b['j'][p3d.J[jn]], float)
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
        # mirrors reflect: each actor mirrored across the glass (with the bank's lag), painted on
        # its own layer and clipped to the glass (critic, T178: grey slabs with nothing in them)
        for p in boxes:
            q = fr['p'].get(p['id'], {})
            if p['type'] == 'mirror' and (q.get('state') or {}).get('reflect'):
                layer = self.reflection(cam, pt, f, q)
                if layer is not None:
                    p['draw'] = (lambda pt_, d0=p['draw'], L=layer: (d0(pt_), pt_.im.alpha_composite(L)))
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
            groups.append((cam.P(j['pelvis'])[2], p3d.depth_order(items, after), (aid, j)))
        pools = [q for q in fr.get('p', {}).values() if q.get('type') == 'water' and q.get('pos') and not q.get('held')]
        for p in boxes:
            if not p['held']:
                # a pool is the ground the actors stand in: drawn first, under everything
                zz = 1e9 if p['type'] == 'water' else p['z']
                groups.append((zz, [['box.' + p['id'], p['z'], lambda p=p: self.draw_box(pt, p)]], None))
        for zz, order, who in sorted(groups, key=lambda g: -g[0]):
            pool = self.pool_at(who[1], pools) if who and pools else None
            before = pt.im.copy() if pool else None
            for key, z2, fn in order:
                fn()
            if pool:
                self.waterline(pt, cam, who[1], pool, before)
        # the effects track over everything (rain, hearts, sweat, ?, ! ...)
        fx.draw(pt, cam, self.V, f, {aid: {k: np.array(b['j'][i], float) for k, i in p3d.J.items() if b['j'][i] is not None}
                                     for aid, b, skin in actors})
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
