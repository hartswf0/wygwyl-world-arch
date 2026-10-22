"""Sequence builder: several puppets + props on one clock, written in the FORMATS.md clip format.

    seq = Seq('seq.09.phone.profile', 'POET at the lit booth', frames=192, cm_px=3.4, floor_y=780)
    poet = seq.actor('poet', 'poet_tracksuit', x0=..., depth=1.0)       # depth scales cm_px (near/far)
    poet.key(0, x=-120, fL=..., ...)                                       # puppet.Track keys
    seq.prop('booth', draw_fn)                                             # draw_fn(f, seq) -> [(z, op)]
    seq.event(40, 'sfx.phone.pickup', 'handset lifted')
    seq.contact(48, 120, 'poet', 'grip_R', lambda f: handset_anchor(f), 'grip handset')
    clip = seq.build(); seq.write()

World units are cm (x right, y up from the floor); screen is the 1600x900 stage. Each frame's ops are
sorted by z (actor z + the puppet's own layer: far arm 1, far leg 2, near leg 3, torso 4, near arm 5),
so a prop can slot between an actor's far leg and body (a motorcycle) or in front of everything (booth
glass). Every contact is measured on the DRAWN cards each frame and logged with its worst error.
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.dirname(HERE)
SHOTS = os.path.dirname(STAGE)
sys.path.insert(0, os.path.join(STAGE, 'anim'))
import puppet as PP
import rigs
from retarget import card_matrix, apply, mlist, unit

W_STAGE, H_STAGE = 1600, 900
OUT = os.path.join(HERE, 'clips')


def resolve_img(pid):
    """Relative-to-shots path for a cut part id (or crop:/pack:)."""
    rel, ab = rigs._img_path(pid)
    if not pid.startswith(('pack:', 'crop:')):
        rel, ab = rigs._cleaned(pid, rel, ab)
    return rel.replace(os.sep, '/'), ab


class Actor:
    def __init__(self, seq, aid, character, z=10.0, depth=1.0, x0=0.0):
        self.seq = seq; self.id = aid; self.character = character
        self.p = PP.Puppet(character, actor=aid)
        self.tr = PP.Track(); self.z = z; self.depth = depth; self.x0 = x0
        self.layers = {}
        self.poses = {}
        self.hidden = set()
        self.base = {}

    def key(self, f, ease='io', **ch):
        self.tr.key(f, ease, **ch); return self

    def hold(self, f0, f1, **ch):
        self.tr.key(f0, 'io', **ch); self.tr.key(f1, 's', **ch); return self

    def pose(self, f):
        P = dict(self.base); P.update(self.tr.value(f))
        for k_, fn in self.poses.items():
            P[k_] = fn(f, P)
        return P


class Seq:
    def __init__(self, sid, title, frames, cm_px=3.0, floor_y=760, fps=24, loop=False, poem=None, view=None,
                 variant=None, about=None, bg=None):
        self.id = sid; self.title = title; self.N = frames; self.k = cm_px; self.floor_y = floor_y
        self.fps = fps; self.loop = loop; self.poem = poem; self.view = view; self.variant = variant; self.about = about
        self.actors = []; self.props = []; self.events = []; self.contacts = []; self.anchors = {}; self.anchor_fns = {}
        self.images = {}; self.notes = []; self.bg = bg; self.states = []; self.mech = []; self.wants = []
        self.origin_x = W_STAGE / 2

    # ------------------------------------------------------------- authoring
    def actor(self, aid, character, z=10.0, depth=1.0, x0=0.0, floor_y=None):
        a = Actor(self, aid, character, z, depth, x0)
        a.floor_y = floor_y
        self.actors.append(a); return a

    def prop(self, name, fn, z=0.0):
        self.props.append((name, fn, z)); return fn

    def event(self, f, sfx, label):
        self.events.append({'f': int(f), 'sfx': sfx, 'label': label})

    def state(self, f0, f1, sid, visible):
        self.states.append({'id': sid, 'f': [int(f0), int(f1)], 'visible': visible})

    def contact(self, f0, f1, aid, point, target, what, tol_cm=2.0, kind='grip'):
        """target: fn(f) -> screen px, or the name of another tracked point 'actor:point'."""
        self.contacts.append(dict(f0=int(f0), f1=int(f1), a=aid, pt=point, target=target, what=what, tol=tol_cm, kind=kind))

    def want_hand(self, f0, f1, aid, side, shape, why):
        """What the hand must be doing (check.py compares the drawn card's shape on these frames)."""
        self.wants.append({'f': [int(f0), int(f1)], 'a': aid, 's': side, 'shape': shape, 'why': why})

    def plant(self, f0, f1, aid, side, what='foot planted'):
        self.contact(f0, f1, aid, 'ball_' + side, None, what, tol_cm=0.6, kind='plant')

    def anchor(self, name, fn):
        """A socket other clips can attach to: fn(f) -> screen px."""
        self.anchor_fns[name] = fn

    def W(self, x, y, depth=1.0, floor_y=None):
        fy = self.floor_y if floor_y is None else floor_y
        return np.array([self.origin_x + x * self.k * depth, fy - y * self.k * depth])

    def img(self, pid, M, t, z, tag=None, a=None, shade=None, blend=None):
        rel, _ = resolve_img(pid) if not pid.startswith('file:') else (pid[5:], None)
        op = {'t': 'img', 'id': pid, 'm': mlist(M, t), '_img': rel}
        if a is not None and a < 0.999: op['a'] = round(float(a), 3)
        if shade: op['shade'] = round(shade, 2)
        if blend: op['blend'] = blend
        if tag: op['tag'] = tag
        return (z, op)

    # ------------------------------------------------------------- build
    def frame_actor(self, a, f):
        P = a.pose(f)
        k = self.k * a.depth
        fy = self.floor_y if a.floor_y is None else a.floor_y
        O = (self.origin_x + a.x0 * self.k, fy)
        ops, pts, info = a.p.solve(P, k, O)
        return [(a.z + z * 0.01, op) for z, op in ops], pts, info, P

    def build(self):
        frames = []; images = {}
        cerr = [dict(c, err=[], frames=0) for c in self.contacts]
        self._pts = []
        for f in range(self.N):
            allops = []; fpts = {}; finfo = {}
            for a in self.actors:
                if f in a.hidden: continue
                ops, pts, info, P = self.frame_actor(a, f)
                allops += ops
                fpts[a.id] = pts; finfo[a.id] = dict(info, pose={k_: v for k_, v in P.items() if isinstance(v, (int, float, str))})
            self._fpts = fpts; self._f = f
            for name, fn, z in self.props:
                for z_, op in fn(f, self):
                    allops.append((z_, op))
            allops.sort(key=lambda x: x[0])
            draw = []
            for z, op in allops:
                if op.get('t') == 'img' and '_img' in op:
                    images[op['id']] = op.pop('_img')
                draw.append(op)
            # contacts measured on the drawn points
            dbg = {}
            for c in cerr:
                if c['f0'] <= f <= c['f1'] and c['a'] in fpts:
                    p = fpts[c['a']].get(c['pt'])
                    if p is None: continue
                    if c['kind'] == 'plant':
                        prev = c.get('_prev')
                        if prev is not None:
                            c['err'].append(float(np.linalg.norm(p - prev)) / self.k)
                        c['_prev'] = p.copy()
                    else:
                        tg = c['target'](f) if callable(c['target']) else fpts[c['target'].split(':')[0]][c['target'].split(':')[1]]
                        c['err'].append(float(np.linalg.norm(p - np.asarray(tg))) / self.k)
                    c['frames'] += 1
                    dbg.setdefault('contacts', []).append([c['a'], c['pt'], round(float(p[0]), 1), round(float(p[1]), 1)])
            fr = {'f': f, 'draw': draw,
                  'actors': {aid: {'view': i['view'], 'face': i['face'], 'set': i['set'], 'head': i.get('head_view'),
                                   'pts': {k_: v for k_, v in i['pts'].items() if k_.split('_')[0] in ('pelvis', 'neck', 'head', 'grip', 'tip', 'heel', 'ball', 'toe', 'wr', 'mouth', 'knee', 'hip', 'ank', 'sole')},
                                   **({'reach': i['reach']} if 'reach' in i else {}),
                                   **({'foot_miss': i['foot_miss']} if 'foot_miss' in i else {})}
                             for aid, i in finfo.items()}}
            if dbg: fr['dbg'] = dbg
            frames.append(fr)
        anchors = {}; tracks = {}
        for name, fn in self.anchor_fns.items():
            tr = [[round(float(v), 1) for v in fn(f)] for f in range(self.N)]
            anchors[name] = tr[0]; tracks[name] = tr
        contacts = []
        for c in cerr:
            e = c['err']
            contacts.append({'f': [c['f0'], c['f1']], 'actor': c['a'], 'point': c['pt'], 'what': c['what'], 'kind': c['kind'],
                             'max_err_cm': round(max(e), 2) if e else None, 'mean_err_cm': round(float(np.mean(e)), 2) if e else None,
                             'tol_cm': c['tol'], 'frames': c['frames'], 'pass': (max(e) <= c['tol']) if e else None})
        rel = os.path.relpath(SHOTS, OUT).replace(os.sep, '/')
        clip = {
            'id': self.id, 'title': self.title, 'kind': 'sequence', 'poem': self.poem, 'view': self.view, 'variant': self.variant,
            'about': self.about,
            'clock': {'fps': self.fps, 'frames': self.N}, 'loop': self.loop,
            'size': {'w': W_STAGE, 'h': H_STAGE}, 'cm_px': self.k, 'floor_y': self.floor_y,
            'image_root': rel + '/', 'image_paths': 'relative to this clip file (%s/ == shots/)' % rel,
            'images': {k_: rel + '/' + v for k_, v in images.items()},
            'cast': [{'id': a.id, 'character': a.character, 'height_cm': a.p.body.H, 'depth': a.depth, 'z': a.z} for a in self.actors],
            'anchors': anchors, 'anchor_tracks': tracks,
            'events': sorted(self.events, key=lambda e: e['f']),
            'states': self.states, 'contacts': contacts, 'hand_wants': self.wants, 'mech': self.mech,
            'notes': self.notes,
            'frames': frames,
        }
        self.clip = clip
        return clip

    def write(self, name=None):
        os.makedirs(OUT, exist_ok=True)
        p = os.path.join(OUT, (name or self.id) + '.json')
        json.dump(self.clip, open(p, 'w'), separators=(',', ':'))
        return p


# ------------------------------------------------------------- prop helpers
class Card:
    """A prop card from the cut kit with named points (fractions of its width/height, or px)."""

    def __init__(self, pid, pts=None, hcm=None, wcm=None):
        self.id = pid
        rel, ab = resolve_img(pid)
        from PIL import Image
        im = Image.open(ab)
        self.w, self.h = im.size
        self.rel = rel
        self.pts = {}
        for k_, v in (pts or {}).items():
            self.pts[k_] = np.array([v[0] * self.w if abs(v[0]) <= 1.5 else v[0], v[1] * self.h if abs(v[1]) <= 1.5 else v[1]], float)
        self.hcm = hcm; self.wcm = wcm

    def px_per_cm(self):
        if self.wcm: return self.w / self.wcm
        return self.h / self.hcm

    def place(self, seq, at, z, pin='c', rot=0.0, scale=1.0, flip=False, a=None, depth=1.0, tag=None, sx=1.0, sy=1.0):
        """Draw with card point `pin` at screen `at`, rotated rot deg (screen, clockwise +), scaled to its cm size."""
        s = seq.k * depth * scale / self.px_per_cm()
        c = self.pts.get(pin, np.array([self.w / 2, self.h / 2])) if isinstance(pin, str) else np.asarray(pin, float)
        r = math.radians(rot)
        R = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
        M = R @ np.diag([s * sx * (-1 if flip else 1), s * sy])
        t = np.asarray(at, float) - M @ c
        return seq.img(self.id, M, t, z, tag=tag or {'r': 'prop', 'p': self.id.split('/')[-1]}, a=a), (M, t)

    def pt(self, name, M, t):
        return apply(M, t, self.pts[name])


# ------------------------------------------------------------- locomotion
def walk(seq, a, f0, x0, x1, steps, T=12, face=1, lift=7.0, first=None, sfx='sfx.footsteps', swing=15.0, lean=4.0):
    """Key a profile walk: the swing foot rolls heel->ball, pivots on the planted ball (heel-up), swings,
       strikes heel first and flattens; the stance foot never moves (its keys hold), so planted drift is zero
       by construction and check.py verifies it on the drawn cards. Returns the frame the walk ends."""
    B = a.p.body.foot * 0.773
    first = first or ('R' if face > 0 else 'L')
    other = 'L' if first == 'R' else 'R'
    heel = {first: x0 - face * 3.0, other: x0 + face * 3.0}
    d = (x1 - x0) / steps
    a.key(f0, 'l', x=x0)
    a.key(f0 + steps * T + 2, 'l', x=x1)
    for s in 'LR':
        a.key(f0, **{'f' + s: dict(x=heel[s], y=0.0, p=0.0, c='heel')})
    for i in range(steps):
        s = first if i % 2 == 0 else other
        o = other if s == first else first
        st = f0 + i * T
        hs = heel[s]
        land = x0 + (i + 1) * d + (d / 2 if i < steps - 1 else 0.0) + (-face * 3.0 if s == first else face * 3.0)
        bx = hs + face * B
        r = math.radians(28)
        if st - 1 > f0:
            a.key(st - 1, **{'f' + s: dict(x=hs, y=0.0, p=0.0, c='heel')})
        a.key(st, **{'f' + s: dict(x=bx, y=0.0, p=0.0, c='ball')})
        a.key(st + 3, **{'f' + s: dict(x=bx, y=0.0, p=-28.0, c='ball')})
        a.key(st + 4, **{'f' + s: dict(x=bx - face * B * math.cos(r) + face * 4, y=B * math.sin(r) + 2.5, p=-22.0, c='heel')})
        a.key(st + 7, **{'f' + s: dict(x=(hs + land) / 2, y=lift, p=-4.0, c='heel')})
        a.key(st + T - 1, **{'f' + s: dict(x=land - face * 1.5, y=1.2, p=10.0, c='heel')})
        a.key(st + T, **{'f' + s: dict(x=land, y=0.0, p=8.0, c='heel')})
        a.key(st + T + 2, **{'f' + s: dict(x=land, y=0.0, p=0.0, c='heel')})
        heel[s] = land
        # arms swing against the legs
        a.key(st + T // 2, **{'a' + s: dict(sh=-swing, el=14.0), 'a' + o: dict(sh=swing, el=22.0)})
        a.key(st, lean=lean)
        if sfx: seq.event(st + T, sfx, 'heel strike %s' % s)
    end = f0 + steps * T + 2
    a.key(end + 4, aL=dict(sh=6.0, el=12.0), aR=dict(sh=6.0, el=12.0), lean=1.5)
    return end, heel
