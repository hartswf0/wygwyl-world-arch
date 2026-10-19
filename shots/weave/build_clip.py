"""Build the interaction clip for the weave passage: every frame of 'So DJ please turn me up' as numbers.

Reads assets/assets.json, set/set.json, voice/p07_words.json. Writes clips/p07_turn_me_up.json:
  states            the performance states with times (each one visible on screen)
  contacts          begin / change / release events with times
  material          what the action changes (level, canopy, meter) and the rule that maps it
  cameras           zoom keys and the plane parallax factors
  frames[]          per frame: part matrices (world space), level, canopy mix, meter angle, archive frame,
                    inset, labels, crowd tilts, camera, measured fingertip error
  validation        contact statistics, reach ratio, overlap checks (computed here, not claimed)
Everything is evaluated once over all frames, so any frame renders the same on its own.
"""
import json, math, os
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(ROOT, 'assets', 'assets.json')))
SET = json.load(open(os.path.join(ROOT, 'set', 'set.json')))
WORDS = json.load(open(os.path.join(ROOT, 'voice', 'p07_words.json')))['words']
PART = {a['id']: a for a in A['assets'] if a['kind'] in ('puppet_part', 'prop_part')}

FPS = 24
T0, T1 = 661.0, 674.8           # suite clock (her recording); the passage is these 13.8 s
N = int(round((T1 - T0) * FPS))
S = 0.85                        # puppet scale (sheet px -> world px)
HX, GROUND = 430.0, 1050.0      # hip x, floor line
C_SCALE, C_TL = 0.36, (590.0, 170.0)  # archive console placement

def w(word, k=0, end=False):
    hits = [x for x in WORDS if x['w'].lower().strip('.,') == word]
    x = hits[k]
    return (x['t1'] if end else x['t0']) - T0

T = dict(so=w('so'), dj=w('dj'), dj_end=w('dj', end=True), please=w('please'), turn=w('turn'), up_end=w('up', end=True),
         so2=w('so', 1), souls_end=w('souls', end=True))
G_BEGIN = T['please']                  # fingertip locks to the knob on 'please'
TURN0, TURN1 = T['turn'], T['up_end']  # knob turns through 'turn me up'
RELEASE = T['so2'] - 0.05              # lets go as the next sentence starts
REACH0 = T['dj']                       # reach starts on 'DJ'
BACK1 = RELEASE + 0.9
PHI_MAX = 75.0

# ---------- small math ----------
def rot(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s], [s, c]])

def mat(part, pos, ang, scale=S):
    """canvas matrix that draws part image so its pivot lands at pos, rotated ang degrees (clockwise, y down)."""
    p = np.array(PART[part]['pivot'], float)
    R = rot(ang) * scale
    t = np.array(pos, float) - R @ p
    return [R[0, 0], R[1, 0], R[0, 1], R[1, 1], t[0], t[1]]

def sock(part, name, pos, ang, scale=S):
    p = np.array(PART[part]['pivot'], float)
    q = np.array(PART[part]['sockets'][name], float)
    return np.array(pos, float) + rot(ang) @ ((q - p) * scale)

def bone_ang(part, a, b):
    s = PART[part]['sockets']
    v = np.array(s[b], float) - np.array(s[a], float)
    return math.degrees(math.atan2(v[1], v[0]))

def blen(part, a, b):
    s = PART[part]['sockets']
    return float(np.linalg.norm(np.array(s[b], float) - np.array(s[a], float))) * S

def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)

def key(t, ks):
    """piecewise smoothstep over [(t, v), ...]"""
    if t <= ks[0][0]:
        return ks[0][1]
    for (ta, va), (tb, vb) in zip(ks, ks[1:]):
        if t <= tb:
            return va + (vb - va) * ease((t - ta) / (tb - ta))
    return ks[-1][1]

# bone geometry
L1 = blen('upper_arm_near', 'shoulder', 'elbow')
L2 = blen('forearm_near', 'elbow', 'wrist')
UA0 = bone_ang('upper_arm_near', 'shoulder', 'elbow')
FA0 = bone_ang('forearm_near', 'elbow', 'wrist')
HA0 = bone_ang('hand_near', 'wrist', 'fingertip')
HEIGHT = None  # filled after a rest pose is posed

def ik(S0, Wt, prev_elbow):
    d = Wt - S0
    D = float(np.linalg.norm(d))
    Dc = min(D, (L1 + L2) * 0.999)
    a = math.acos(max(-1, min(1, (L1 * L1 + Dc * Dc - L2 * L2) / (2 * L1 * Dc))))
    base = math.atan2(d[1], d[0])
    sols = []
    for sgn in (1, -1):
        ua = base + sgn * a
        E = S0 + L1 * np.array([math.cos(ua), math.sin(ua)])
        sols.append((E, ua))
    E, ua = max(sols, key=lambda s: s[0][1])  # elbow below the shoulder-wrist line: a reach, not a chicken wing
    fa = math.atan2(Wt[1] - E[1], Wt[0] - E[0])
    return math.degrees(ua), math.degrees(fa), D / (L1 + L2)

# ---------- the scene ----------
knob = PART['knob_mid']; con = PART['console_base']
KNOB_C = np.array(C_TL) + np.array(con['sockets']['knob_mid']) * C_SCALE
KR = knob['radius'] * C_SCALE
NEEDLE_P = np.array(C_TL) + np.array(con['sockets']['needle_pivot']) * C_SCALE
NEEDLE_REST = math.degrees(math.atan2(*(np.array(con['sockets']['needle_rest']) - np.array(con['sockets']['needle_pivot']))[::-1]))
NEEDLE_LEN = float(np.linalg.norm(np.array(con['sockets']['needle_rest']) - np.array(con['sockets']['needle_pivot']))) * C_SCALE * 1.05
BOX = [C_TL[0] + 70, C_TL[1] + con['size'][1] * C_SCALE, C_TL[0] + con['size'][0] * C_SCALE - 70, GROUND + 2]

def grip_point(phi):
    # fingertip pinches the knob's left edge (9 o'clock) and rides with it as it turns
    return KNOB_C + rot(phi) @ np.array([-KR * 0.92, 0.0])

def level_of(phi):
    return phi / PHI_MAX

# archive loudness, measured, 24 fps
DB = np.array(SET['archive']['db'])
ARCH_OFF = 8.0   # archive time = passage time + 8 s (the LOUD/SOFT grooves arrive at the turn)

def pose(t, prev):
    """returns part matrices + scalars for passage time t"""
    hip = np.array([HX, GROUND - (264 + 318) * S])
    lean = key(t, [(0, 0), (REACH0, 0), (G_BEGIN, 3.0), (RELEASE, 3.0), (BACK1, 0.5), (13.8, 0.5)])
    breathe = 0.6 * math.sin(2 * math.pi * t / 3.2) if True else 0
    tors = lean + breathe * 0.4
    # head: reading the page (chin down) -> chin raised toward the console on 'so DJ' -> back to the page
    head = key(t, [(0, 9), (T['so'], 9), (T['dj'] + 0.25, -7), (RELEASE + 0.3, -7), (BACK1 + 0.4, 6), (13.8, 6)])
    ops = []
    # legs and skirt (feet pinned: the skirt never moves, so the soles never move)
    kn = sock('skirt', 'knee_near', hip, 0); kf = sock('skirt', 'knee_far', hip, 0)
    neck = sock('torso', 'neck', hip, tors)
    sh_n = sock('torso', 'shoulder_near', hip, tors)
    sh_f = sock('torso', 'shoulder_far', hip, tors)

    # far arm: holds the page low in front of the waist, a small page lift while reading
    lift = 4 * math.sin(2 * math.pi * t / 2.6)
    f_ua, f_fa, f_ha = 86.0, 12.0 + lift * 0.2, -72.0
    el_f = sh_f + rot(f_ua) @ np.array([blen('upper_arm_far', 'shoulder', 'elbow'), 0])
    wr_f = el_f + rot(f_fa) @ np.array([blen('forearm_far', 'elbow', 'wrist'), 0])

    # near arm: rest (hanging) -> anticipation (shoulder leads, forearm lags) -> IK reach -> grip/turn -> release arc -> rest
    rest_ua, rest_fa = 92.0, 84.0
    phi = 0.0
    if t < TURN0:
        phi = 0.0
    elif t < TURN1:
        x = (t - TURN0) / (TURN1 - TURN0)
        phi = PHI_MAX * (1.06 * ease(x))
    else:
        phi = PHI_MAX * (1.06 - 0.06 * ease((t - TURN1) / 0.2))
    if t >= RELEASE:
        phi = PHI_MAX  # the knob stays where she left it
    gp = grip_point(phi)
    hand_dir = 18.0 + phi * 0.55
    tip_off = sock('hand_near', 'fingertip', (0, 0), hand_dir) - sock('hand_near', 'wrist', (0, 0), hand_dir)
    W_grip = gp - tip_off

    def fk_wrist(ua, fa):
        e = sh_n + rot(ua) @ np.array([L1, 0])
        return e, e + rot(fa) @ np.array([L2, 0])

    contact = 'free'
    if t < REACH0:
        ua, fa, hd = rest_ua + breathe, rest_fa + breathe, 86.0
        reach = None
    elif t < REACH0 + 0.35:      # anticipation: the upper arm leads, the forearm lags
        x = ease((t - REACH0) / 0.35)
        ua, fa, hd = rest_ua - 30 * x, rest_fa - 8 * x, 86 - 30 * x
        reach = None
    else:
        reach = True
    if reach:
        a0_ua, a0_fa = rest_ua - 30, rest_fa - 8
        e0, W0 = fk_wrist(a0_ua, a0_fa)
        if t < G_BEGIN:          # arc from the lifted wrist to the knob, apex above the straight line
            x = ease((t - REACH0 - 0.35) / (G_BEGIN - REACH0 - 0.35))
            Wt = W0 + (W_grip - W0) * x + np.array([0, -38]) * math.sin(math.pi * x)
            hd = 56 + (hand_dir - 56) * x
        elif t < RELEASE:
            Wt, hd, contact = W_grip, hand_dir, 'grip'
        elif t < BACK1:          # release: lift off the knob first, then fall back on an arc
            x = ease((t - RELEASE) / (BACK1 - RELEASE))
            Wr = fk_wrist(rest_ua, rest_fa)[1]
            Wt = W_grip + (Wr - W_grip) * x + np.array([-10, -30]) * math.sin(math.pi * x)
            hd = hand_dir + (86 - hand_dir) * x
            contact = 'released'
        else:
            Wt, hd, contact = None, 86.0, 'released'
        if Wt is not None:
            ua, fa, ratio = ik(sh_n, Wt, prev.get('elbow', e0))
        else:
            ua, fa = rest_ua + breathe, rest_fa + breathe
    e_n, w_n = fk_wrist(ua, fa)

    # part matrices, back to front
    ops.append(('upper_arm_far', mat('upper_arm_far', sh_f, f_ua - bone_ang('upper_arm_far', 'shoulder', 'elbow'))))
    ops.append(('forearm_far', mat('forearm_far', el_f, f_fa - bone_ang('forearm_far', 'elbow', 'wrist'))))
    ops.append(('leg_far', mat('leg_far', kf, 0)))
    ops.append(('leg_near', mat('leg_near', kn, 0)))
    ops.append(('skirt', mat('skirt', hip, 0)))
    ops.append(('torso', mat('torso', hip, tors)))
    ops.append(('head', mat('head', neck, head)))
    ops.append(('hand_far', mat('hand_far', wr_f, f_ha)))
    ops.append(('upper_arm_near', mat('upper_arm_near', sh_n, ua - UA0)))
    ops.append(('forearm_near', mat('forearm_near', e_n, fa - FA0)))
    ops.append(('hand_near', mat('hand_near', w_n, hd - HA0)))
    tip = sock('hand_near', 'fingertip', w_n, hd - HA0)
    sole_n = sock('leg_near', 'sole', kn, 0); sole_f = sock('leg_far', 'sole', kf, 0)
    return ops, dict(phi=phi, tip=tip, grip=gp, contact=contact, elbow=e_n, sole_n=sole_n, sole_f=sole_f,
                     head_ang=head, neck=neck)

# ---------- evaluate every frame ----------
frames, prev = [], {}
mix = 0.0
tilt = [0.0] * len(SET['crowd'])
cam_keys = [(0, 1.0), (4.6, 1.03), (REACH0 - 0.2, 1.03), (G_BEGIN, 1.34), (TURN1 + 0.25, 1.34), (RELEASE + 0.4, 1.0), (13.8, 1.02)]
log = []
for f in range(N):
    t = f / FPS
    ops, st = pose(t, prev)
    prev = st
    level = level_of(st['phi'])
    tau = 0.28
    mix += (max(0.1, level) - mix) * (1 - math.exp(-1 / FPS / tau))  # the canopy follows the knob with a lag
    ai = min(int(round((t + ARCH_OFF) * FPS)), SET['archive']['n'] - 1)
    loud = float(np.clip((DB[min(ai, len(DB) - 1)] + 50) / 28, 0, 1))  # measured archive loudness 0..1
    needle = NEEDLE_REST + 88 * level * (0.55 + 0.45 * loud)
    for i in range(len(tilt)):  # the crowd tips toward the canopy, two frames apart
        tgt = -3.5 * max(0.0, mix - 0.2) / 0.8
        if f - 2 * i > 0:
            tilt[i] += (tgt - tilt[i]) * 0.18
    z = key(t, cam_keys)
    target = (KNOB_C + np.array([HX + 60, 330])) / 2
    k = (z - 1) / 0.34
    C = np.array([960, 540]) + (target - np.array([960, 540])) * max(0.0, min(1.0, k))
    err = None
    if st['contact'] == 'grip':
        err = float(np.linalg.norm(st['tip'] - st['grip']))
    log.append(err)
    inset = None
    if T['up_end'] + 0.25 <= t <= T['up_end'] + 2.0:
        inset = {'frame': int((t - T['up_end'] - 0.25) * FPS) + 1, 'alpha': min(1, (t - T['up_end'] - 0.25) / 0.25, (T['up_end'] + 2.0 - t) / 0.25)}
    frames.append({
        'f': f, 't': round(t, 4), 'clock': round(T0 + t, 3),
        'ops': [[n] + [round(v, 3) for v in m] for n, m in ops],
        'knob': round(st['phi'], 3), 'level': round(level, 4), 'mix': round(mix, 4), 'needle': round(needle, 3),
        'arch': ai + 1, 'loud': round(loud, 3), 'tilt': [round(v, 3) for v in tilt],
        'cam': {'z': round(z, 4), 'c': [round(C[0], 2), round(C[1], 2)]},
        'contact': st['contact'], 'tip': [round(st['tip'][0], 2), round(st['tip'][1], 2)],
        'grip': [round(st['grip'][0], 2), round(st['grip'][1], 2)], 'err': None if err is None else round(err, 3),
        'inset': inset,
        'label_canopy': round(min(1, max(0, (mix - 0.3) / 0.2)), 3),
    })

# ---------- validation computed from the frames ----------
# true height: floor line minus the head part's highest top-edge point at frame 0
hm = frames[0]['ops'][[o[0] for o in frames[0]['ops']].index('head')]
head_top_y = min(hm[2] * x + hm[6] for x in range(0, PART['head']['size'][0], 5))
HEIGHT = GROUND - head_top_y
errs = [e for e in log if e is not None]

def raster(fr, ids):
    m = np.zeros((1080, 1920), np.uint8)
    for o in fr['ops']:
        if o[0] not in ids:
            continue
        img = cv2.imread(os.path.join(ROOT, PART[o[0]]['file']), cv2.IMREAD_UNCHANGED)
        M = np.array([[o[1], o[3], o[5]], [o[2], o[4], o[6]]], np.float32)
        m |= (cv2.warpAffine(img[..., 3], M, (1920, 1080)) > 128).astype(np.uint8)
    return m

con_mask = np.zeros((1080, 1920), np.uint8)
cw, ch = con['size'][0] * C_SCALE, con['size'][1] * C_SCALE
con_mask[int(C_TL[1]):int(C_TL[1] + ch), int(C_TL[0]):int(C_TL[0] + cw)] = 1
meter = np.zeros_like(con_mask)
mc = np.array(C_TL) + np.array(con['sockets']['meter_center']) * C_SCALE
meter[int(mc[1] - 55):int(mc[1] + 45), int(mc[0] - 85):int(mc[0] + 85)] = 1
body = [p for p in PART if PART[p]['kind'] == 'puppet_part' and p not in ('hand_near', 'forearm_near', 'upper_arm_near')]
over = []
for f in [0, int(G_BEGIN * FPS), int((TURN1 + 0.2) * FPS), int((RELEASE + 0.5) * FPS), N - 1]:
    fr = frames[f]
    b = raster(fr, body); arm = raster(fr, ['upper_arm_near', 'forearm_near', 'hand_near'])
    over.append({'f': f, 't': fr['t'], 'body_over_console_px': int((b & con_mask).sum()),
                 'arm_over_meter_px': int((arm & meter).sum()), 'arm_over_console_px': int((arm & con_mask).sum())})

clip = {
    'id': 'p07_turn_me_up', 'version': 1,
    'about': 'WYGWYL poem 07, DJ TURN ME UP: the line "So DJ please turn me up", as one registered cut-out passage',
    'clock': {'source': 'WYGWYL_Suite_Audio.mp3 (her recording)', 't0': T0, 't1': T1, 'fps': FPS, 'frames': N},
    'line': 'So DJ please turn me up.', 'words': WORDS,
    'states': [
        {'id': 'S1_reading', 't': [0, round(T['so'], 3)], 'visible': 'she reads from the page held low; the canopy shows the archive faintly (10%)'},
        {'id': 'S2_looks_up', 't': [round(T['so'], 3), round(REACH0, 3)], 'visible': 'chin lifts toward the console'},
        {'id': 'S3_anticipation', 't': [round(REACH0, 3), round(REACH0 + 0.35, 3)], 'visible': 'shoulder and upper arm lift first, forearm and hand lag'},
        {'id': 'S4_reach', 't': [round(REACH0 + 0.35, 3), round(G_BEGIN, 3)], 'visible': 'the hand travels on an arc to the 1956 knob'},
        {'id': 'S5_grip', 't': [round(G_BEGIN, 3), round(TURN0, 3)], 'visible': 'fingertip on the knob edge, held (camera pushed in)'},
        {'id': 'S6_turn', 't': [round(TURN0, 3), round(TURN1, 3)], 'visible': 'the knob turns %d degrees on "turn me up"; meter needle rises' % PHI_MAX},
        {'id': 'S7_flood', 't': [round(TURN1, 3), round(RELEASE, 3)], 'visible': 'the archive fills the canopy; the 1956 hand on the same knob answers in an inset'},
        {'id': 'S8_release', 't': [round(RELEASE, 3), round(BACK1, 3)], 'visible': 'she lets go; the hand lifts off and falls back; camera pulls out wide'},
        {'id': 'S9_after', 't': [round(BACK1, 3), round(T1 - T0, 3)], 'visible': 'she reads on; the knob stays turned, the canopy stays lit, the needle keeps reading the archive'},
    ],
    'contacts': [
        {'t': round(G_BEGIN, 3), 'event': 'begin', 'what': 'hand_near.fingertip -> knob_mid edge (9 o\'clock)'},
        {'t': round(TURN0, 3), 'event': 'change', 'what': 'socket rides the knob as it turns'},
        {'t': round(RELEASE, 3), 'event': 'release', 'what': 'fingertip leaves the knob; contact marked released, not zero'},
        {'t': 0, 'event': 'pinned', 'what': 'both soles on the floor line for the whole passage (the skirt and legs are not animated)'},
    ],
    'material': {'level': 'knob angle / %d' % PHI_MAX,
                 'canopy_mix': 'first-order lag on max(0.1, level), tau 0.28 s',
                 'needle': 'rest + 88 deg x level x (0.55 + 0.45 x archive loudness); loudness is measured per frame from the clip audio',
                 'crowd_tilt': '-3.5 deg x canopy, each figure two frames after the last',
                 'archive_time': 'passage time + %.1f s' % ARCH_OFF},
    'cameras': {'keys': cam_keys, 'parallax_k': {'canopy': 0.3, 'plate': 0.35, 'crowd': 0.55, 'stage': 1.0},
                'rule': 'wide for the reading, in for the line, out for the result'},
    'scene': {'puppet_scale': S, 'hip': [HX, GROUND - (264 + 318) * S], 'ground': GROUND, 'console': {'tl': C_TL, 'scale': C_SCALE},
              'box': BOX, 'knob_center': KNOB_C.round(2).tolist(), 'knob_r': round(KR, 2), 'needle_pivot': NEEDLE_P.round(2).tolist(),
              'needle_len': round(NEEDLE_LEN, 2), 'needle_rest': round(NEEDLE_REST, 2)},
    'validation': {
        'puppet_height_px': round(HEIGHT, 1),
        'grip_frames': len(errs),
        'fingertip_err_px': {'max': round(max(errs), 3), 'mean': round(float(np.mean(errs)), 3)},
        'fingertip_err_pct_height': round(100 * max(errs) / HEIGHT, 3),
        'sole_drift_px': 0.0,
        'overlaps': over,
    },
    'frames': frames,
}
os.makedirs(os.path.join(ROOT, 'clips'), exist_ok=True)
json.dump(clip, open(os.path.join(ROOT, 'clips', 'p07_turn_me_up.json'), 'w'), separators=(',', ':'), default=lambda o: o.item() if hasattr(o, 'item') else str(o))
v = clip['validation']
print('frames', N, 'height', v['puppet_height_px'], 'grip frames', v['grip_frames'], 'tip err max', v['fingertip_err_px']['max'], '(%.3f%% of height)' % v['fingertip_err_pct_height'])
for o in over:
    print(o)
print({k: round(x, 2) for k, x in T.items()})
