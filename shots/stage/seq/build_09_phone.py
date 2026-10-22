"""Poem 09 "Yet, heard": the POET walks up to the lit phone booth on the quay, lifts the handset, dials,
talks to his mother (head tilt, mouth swaps on a beat, the far palm pressed to the booth wall), hangs up.

    python3 shots/stage/seq/build_09_phone.py          # writes seq/clips/seq.09.phone.{near,far}.json

The booth is assembled here from the cut kit (09.props.phonebooth: back panel with the payphone body,
steel floor, ceiling light, open left door, front mullion frame with glass inserts; 09.props.phones-chair:
the black payphone handset). The mechanisms agent has no phone-booth mech yet (mech/index.json lists none),
so nothing is borrowed from there; the armoured cord is drawn as a sagging steel line between the payphone's
cord port and the handset's mouthpiece (the cord card is a fixed U and cannot stretch).

Two versions: 'near' (cm_px 2.45, the booth fills the frame) and 'far' (the same action at depth 0.55, the
booth small on the quay, more ground). Same keys, same contacts.
"""
import math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from seqlib import Seq, Card, walk, resolve_img
import puppet as PP
from retarget import card_matrix, apply, mlist, unit

BOOTH = '09.props.phonebooth/'
PHONE = '09.props.phones-chair/'


def ease(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def build(variant='near'):
    depth = 1.0 if variant == 'near' else 0.55
    k = 3.3
    floor_y = 860 if variant == 'near' else 700
    seq = Seq('seq.09.phone.' + variant, 'POET at the lit phone booth: walk up, lift the handset, dial, talk, hang up (%s)' % variant,
              frames=272, cm_px=k * depth, floor_y=floor_y, poem='09', view='profile', variant=variant,
              about='He calls his mother from a lit booth on the quay (poem 09 movement "Tears, an abyss"). '
                    'Profile, facing right; near hand on the handset, far hand dials and then presses flat on the booth wall.')
    seq.origin_x = 560 if variant == 'near' else 760
    K = seq.k
    W = lambda x, y: seq.W(x, y)

    # ---------------- the booth (world cm; centre bx, floor y=0)
    bx = 128.0
    panel = Card(BOOTH + 'back-with-payphone-body-no-handset', hcm=200)
    frame = Card(BOOTH + 'steel-mullion', hcm=240)
    floor = Card(BOOTH + 'steel-grey', wcm=165)
    light = Card(BOOTH + 'cream-yellow', wcm=118)
    door = Card(BOOTH + 'hinge-holes', hcm=228)
    glass = Card(BOOTH + 'front-glass-pane-clear', hcm=150)
    curb = Card(BOOTH + 'pavement-grey', wcm=190)
    hand_set = Card(PHONE + 'a-payphone', {'ear': (0.60, 0.15), 'mouth': (0.60, 0.86), 'grip': (0.20, 0.50),
                                            'cord': (0.56, 0.97)}, hcm=24)
    # panel points (fractions of the panel card), measured on a gridded render of the card
    P_W = 200 * panel.w / panel.h
    pw = lambda fx, fy: (bx + (fx - 0.5) * P_W, 18 + (1 - fy) * 200)
    hook = pw(0.375, 0.255)                 # where the handset's earpiece hangs (top of the cradle side)
    keypad = [pw(0.50, 0.41), pw(0.535, 0.44), pw(0.50, 0.47)]
    cord_port = pw(0.44, 0.60)
    palm_spot = pw(0.31, 0.38)              # the far palm pressed flat on the wall, left of the payphone

    poet = seq.actor('poet', 'poet_tracksuit', z=10.0)
    poet.base = dict(view='profile', face=1, mouth='rest', brows='rest', aL=dict(sh=6.0, el=12.0), aR=dict(sh=6.0, el=12.0),
                     hL='relaxed', hR='relaxed', tilt=0.0, lean=1.5)
    xs = 76.0
    f_walk_end, heels = walk(seq, poet, 6, -150.0, xs, 5, T=12, face=1)

    # ---------------- timeline (frames at 24 fps)
    F = dict(reach0=72, grip=86, lift1=108, dial0=112, dial1=138, palm0=146, palm1=206, talk0=128, talk1=204,
             hang0=210, hang1=230, release=232, rest=248, end=271)

    seq.state(0, f_walk_end, 'S1_walk', 'he walks up the quay into the lit booth; the door stands open')
    seq.state(F['reach0'], F['grip'], 'S2_reach', 'near hand reaches the handset on its cradle; the hand closes on the handle')
    seq.state(F['grip'], F['lift1'], 'S3_lift', 'handset lifted on an arc to his ear; head tips into it')
    seq.state(F['dial0'], F['dial1'], 'S4_dial', 'far hand points and presses three keys')
    seq.state(F['talk0'], F['talk1'], 'S5_talk', 'he talks: mouth swaps on the beat, brows go sad then raised; far palm flat on the wall')
    seq.state(F['hang0'], F['hang1'], 'S6_hang_up', 'handset back onto the cradle; the hand lets go')
    seq.state(F['release'], F['end'], 'S7_after', 'arm down, head drops')

    # head + face keys
    poet.key(F['reach0'], tilt=6.0)
    poet.key(F['lift1'], tilt=11.0, lean=3.0)
    poet.key(F['hang0'], tilt=10.0)
    poet.key(F['hang1'], tilt=4.0)
    poet.key(F['rest'], tilt=15.0, lean=4.0)
    beat = ['A', 'rest', 'E', 'MBP', 'O', 'rest', 'A', 'U', 'rest', 'rest', 'E', 'FV', 'A', 'MBP', 'rest', 'O', 'A', 'rest', 'rest', 'rest']
    f = F['talk0']; i = 0
    while f < F['talk1']:
        m = beat[i % len(beat)]
        poet.key(f, 's', mouth=m)
        f += 4 if m != 'rest' else 6
        i += 1
    poet.key(F['talk1'], 's', mouth='rest')
    poet.key(F['talk0'], 's', brows='rest'); poet.key(150, 's', brows='sad'); poet.key(176, 's', brows='raised')
    poet.key(194, 's', brows='sad'); poet.key(F['rest'], 's', brows='sad')
    # head bobs on the stressed syllables
    for fb in range(F['talk0'], F['talk1'], 16):
        poet.key(fb, tilt=10.0); poet.key(fb + 6, tilt=13.0)

    # hand shapes
    poet.key(0, 's', hR='relaxed', hL='relaxed')
    poet.key(F['reach0'] + 6, 's', hR='open')
    poet.key(F['grip'] - 2, 's', hR='grip')
    poet.key(F['release'], 's', hR='open')
    poet.key(F['rest'], 's', hR='relaxed')
    poet.key(F['dial0'], 's', hL='point')
    poet.key(F['palm0'] - 4, 's', hL='flat', hvL='back')
    poet.key(F['palm1'] + 2, 's', hL='relaxed', hvL='palm')
    seq.want_hand(F['grip'], F['hang1'], 'poet', 'R', 'grip', 'holding the handset')
    seq.want_hand(F['dial0'] + 4, F['dial1'], 'poet', 'L', 'point', 'pressing keys')
    seq.want_hand(F['palm0'], F['palm1'], 'poet', 'L', 'flat', 'palm pressed on the booth wall')

    # ---------------- the handset path (screen), driven by the head on every frame
    cache = {}

    def solve0(f, P):
        Q = dict(P); Q['aR'] = dict(sh=6.0, el=12.0); Q['aL'] = dict(sh=6.0, el=12.0)
        ops, pts, info = poet.p.solve(Q, seq.k * poet.depth, (seq.origin_x, seq.floor_y))
        return pts

    def handset_pose(f, P):
        """(ear point px, axis unit) of the handset for frame f."""
        hk = W(*hook); down = np.array([0.0, 1.0])
        if f < F['grip'] or f > F['hang1']:
            return hk, down
        pts = solve0(f, P)
        ear = pts['ear'] + np.array([-0.5, -1.0]) * K
        d_ear = unit(pts['mouth'] - pts['ear']); a = math.atan2(d_ear[1], d_ear[0]) + math.radians(38)
        d_ear = np.array([math.cos(a), math.sin(a)])
        if f <= F['lift1']:
            u = ease((f - F['grip']) / (F['lift1'] - F['grip']))
        elif f >= F['hang0']:
            u = 1 - ease((f - F['hang0']) / (F['hang1'] - F['hang0']))
        else:
            u = 1.0
        p = hk * (1 - u) + ear * u + np.array([10.0 * K * math.sin(math.pi * u), -4.0 * K * math.sin(math.pi * u)])
        ang0 = math.atan2(down[1], down[0]); ang1 = math.atan2(d_ear[1], d_ear[0])
        an = ang0 + (ang1 - ang0) * u
        return p, np.array([math.cos(an), math.sin(an)])

    def handset_M(p, d):
        s = K / hand_set.px_per_cm()
        return card_matrix(hand_set.pts['ear'], hand_set.pts['mouth'], p, p + d * 100, s, axial=s)

    def to_world(pt):
        return ((pt[0] - seq.origin_x) / K, (seq.floor_y - pt[1]) / K)

    rest_grip = {}

    def armR(f, P):
        if f < F['reach0'] or f > F['rest']:
            return P.get('aR')
        p, d = handset_pose(f, P)
        M, t = handset_M(p, d)
        g = apply(M, t, hand_set.pts['grip'])
        cache[f] = (M, t, g)
        # on the cradle the hand closes across the handle, fingers forward (90); at the ear the fingers wrap
        # the handle pointing up and forward, the wrist under the handset and the elbow down in front of the chest
        u_ear = 0.0 if f <= F['grip'] else min(1.0, max(0.0, (f - F['grip']) / (F['lift1'] - F['grip'])))
        if f >= F['hang0']: u_ear = min(u_ear, 1 - ease((f - F['hang0']) / (F['hang1'] - F['hang0'])))
        ha = 90.0 + 115.0 * ease(u_ear)
        if f < F['grip']:
            if 'r' not in rest_grip:
                Q = dict(P); Q['aR'] = dict(sh=6.0, el=12.0)
                ops, pts, info = poet.p.solve(Q, seq.k, (seq.origin_x, seq.floor_y))
                rest_grip['r'] = pts['grip_R']
            u = ease((f - F['reach0']) / (F['grip'] - F['reach0']))
            tgt = rest_grip['r'] * (1 - u) + g * u
            return dict(ik=to_world(tgt), ha=10 + 80 * u, elbow='down')
        if f > F['release']:
            if 'e' not in rest_grip:
                rest_grip['e'] = g
            Q = dict(P); Q['aR'] = dict(sh=6.0, el=12.0)
            ops, pts, info = poet.p.solve(Q, seq.k, (seq.origin_x, seq.floor_y))
            u = ease((f - F['release']) / (F['rest'] - F['release']))
            tgt = rest_grip['e'] * (1 - u) + pts['grip_R'] * u
            return dict(ik=to_world(tgt), ha=90 - 80 * u, elbow='down')
        return dict(ik=to_world(g), ha=ha, pole=35.0)

    def armL(f, P):
        if f < F['dial0'] - 6 or f > F['palm1'] + 16:
            return P.get('aL')
        Q = dict(P); Q['aL'] = dict(sh=6.0, el=12.0)
        if f < F['dial0']:
            u = ease((f - (F['dial0'] - 6)) / 6.0)
            tgt = np.array(keypad[0]) - np.array([10.0, 14.0]) * (1 - u)
            return dict(ik=tuple(tgt), at='tip', ha=70 + 20 * u, elbow='down')
        if f <= F['dial1']:
            n = (f - F['dial0']) / (F['dial1'] - F['dial0']) * 3
            i = min(2, int(n)); ph = n - i
            press = 1.0 if 0.12 <= ph <= 0.42 else (ph / 0.12 if ph < 0.12 else max(0.0, 1 - (ph - 0.42) / 0.2))
            tgt = np.array(keypad[i]) + np.array([-3.0 * (1 - press), 0.0])
            return dict(ik=tuple(tgt), at='tip', ha=88.0, elbow='down')
        if f < F['palm0']:
            u = ease((f - F['dial1']) / (F['palm0'] - F['dial1']))
            tgt = np.array(keypad[2]) * (1 - u) + np.array(palm_spot) * u
            return dict(ik=tuple(tgt), at='palm', ha=88 + 80 * u, elbow='down')
        if f <= F['palm1']:
            return dict(ik=palm_spot, at='palm', ha=168.0, elbow='down')
        u = ease((f - F['palm1']) / 16.0)
        ops, pts, info = poet.p.solve(Q, seq.k, (seq.origin_x, seq.floor_y))
        rest = np.array(to_world(pts['grip_L']))
        tgt = np.array(palm_spot) * (1 - u) + rest * u
        return dict(ik=tuple(tgt), at='palm', ha=168 - 160 * u, elbow='down')

    poet.poses['aR'] = armR
    poet.poses['aL'] = armL

    # ---------------- props (z: booth back 2, poet 10, handset 10.045 between head and near arm, front frame 20)
    def booth_back(f, s):
        out = []
        out.append(curb.place(s, W(bx, -6), 1.0, pin='c')[0])
        out.append(floor.place(s, W(bx, -2), 1.2, pin='c', sy=0.55)[0])
        out.append(panel.place(s, W(bx, 118), 2.0)[0])
        out.append(frame.place(s, W(bx, 118), 2.05, sx=150.0 / (240 * frame.w / frame.h), a=0.55)[0])
        # the open left door, swung out on its hinge at the frame's left edge (narrowed: seen edge-on)
        out.append(door.place(s, W(bx - 75, 112), 1.5, pin=(door.w, door.h / 2), sx=0.42)[0])
        out.append(light.place(s, W(bx, 228), 2.1)[0])
        out.append((2.2, {'t': 'glow', 'x': round(float(W(bx, 222)[0]), 1), 'y': round(float(W(bx, 222)[1]), 1),
                          'r': round(150 * s.k / 3.3, 1), 'color': '#ffe7a8', 'a': 0.55}))
        return out

    def handset(f, s):
        if f in cache:
            M, t, g = cache[f]
        else:
            p, d = handset_pose(f, poet.pose(f))
            M, t = handset_M(p, d)
        out = [s.img(hand_set.id, M, t, 10.045, tag={'r': 'prop', 'p': 'handset'})]
        a = np.array(W(*cord_port)); b = apply(M, t, hand_set.pts['cord'])
        L = np.linalg.norm(b - a); sag = max(6.0 * s.k, 70.0 * s.k - L * 0.5)
        pts = []
        for i in range(13):
            u = i / 12.0
            q = a * (1 - u) + b * u + np.array([0, sag * 4 * u * (1 - u)])
            pts.append([round(float(q[0]), 1), round(float(q[1]), 1)])
        out.insert(0, (10.044, {'t': 'line', 'pts': pts, 'stroke': '#7d8288', 'w': round(2.6 * s.k / 3.3 + 1, 1)}))
        out.insert(0, (10.0439, {'t': 'line', 'pts': pts, 'stroke': '#2c2f33', 'w': round(4.2 * s.k / 3.3 + 1, 1)}))
        return out

    def booth_front(f, s):
        # cutaway front: the mullion frame stands BEHIND him (it reads as the booth's walls), only the glass
        # is in front of him, faint, so the body stays legible
        out = []
        for gx in (bx - 36, bx + 3, bx + 46):
            out.append(glass.place(s, W(gx, 150), 19.9, sx=0.5, a=0.10)[0])
        return out

    seq.prop('booth_back', booth_back)
    seq.prop('handset', handset)
    seq.prop('booth_front', booth_front)

    # ---------------- events (sfx ids from shots/stage/sfx/index.json)
    seq.event(0, 'sfx.lights.hum', 'booth light hums')
    seq.event(F['grip'], 'sfx.phone.pickup', 'handset off the cradle')
    for j in range(3):
        seq.event(int(F['dial0'] + (j + 0.2) * (F['dial1'] - F['dial0']) / 3), 'sfx.phone.dial', 'key %d' % (j + 1))
    seq.event(F['hang1'] - 2, 'sfx.phone.hangup', 'handset back on the cradle')

    # ---------------- contacts measured on the drawn cards
    seq.contact(F['grip'], F['hang1'], 'poet', 'grip_R', lambda f: cache[f][2] if f in cache else apply(*handset_M(*handset_pose(f, poet.pose(f))), hand_set.pts['grip']),
                'near hand grips the handset handle', tol_cm=1.5)
    for j in range(3):
        fr_ = [f for f in range(F['dial0'], F['dial1'] + 1)
               if min(2, int((f - F['dial0']) / (F['dial1'] - F['dial0']) * 3)) == j and
               0.12 <= (f - F['dial0']) / (F['dial1'] - F['dial0']) * 3 - j <= 0.42]
        seq.contact(fr_[0], fr_[-1], 'poet', 'tip_L', (lambda jj: (lambda f: W(*keypad[jj])))(j), 'fingertip on key %d' % (j + 1), tol_cm=1.5, kind='press')
    seq.contact(F['palm0'], F['palm1'], 'poet', 'grip_L', lambda f: W(*palm_spot), 'far palm pressed flat on the booth wall', tol_cm=1.5, kind='press')

    # anchors other clips can attach to
    seq.anchor('handset_ear', lambda f: (cache[f][2] if f in cache else W(*hook)))
    seq.anchor('mouth', lambda f: seq._fpts.get('poet', {}).get('mouth', W(0, 0)) if False else W(*hook))
    seq.anchor('booth_light', lambda f: W(bx, 222))
    seq.anchor('cord_port', lambda f: W(*cord_port))
    seq.notes += ['booth assembled from 09.props.phonebooth cards here (no booth mech in shots/stage/mech yet)',
                  'armoured cord drawn as a sagging steel line (the cut cord card is a fixed U)',
                  'mouth swaps: poet.red_black_sunglasses.face.profile patches on the blank profile head; eyes hidden by the sunglasses']
    clip = seq.build()
    # the mouth anchor from the drawn head
    clip['anchor_tracks']['mouth'] = [fr['actors']['poet']['pts'].get('mouth') for fr in clip['frames']]
    clip['anchors']['mouth'] = clip['anchor_tracks']['mouth'][0]
    p = seq.write()
    return p


if __name__ == '__main__':
    for v in (sys.argv[1:] or ['near', 'far']):
        print(build(v))
