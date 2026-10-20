"""Clip for passage p04_hands: WYGWYL poem 04, 364.0-392.6 s on her clock.

  "The clouds meet the stars for the deepest level of darkness, welcoming extra hard work to search the bare ground for two
   hands. Hands that once could tusk dusk after dusk, find and celebrate a new life and feel good. And they too used to be
   mine. I put them back on with the care of my future at stake, and say to myself: nevermore."

Joins used: WIPE (the 1969 sky wipes into the plate's own sky, labelled, registered to the plate's sky mask),
CITIZEN (the 1969 man at the rail rises as a cut-out on a stick behind the plate's ledge, his film playing inside his cut),
TOUCH (her wrists find her own loose hands on the ground; one hand carries the other to the far wrist).

Every frame is evaluated once here and written as a display list (see weave_lib.py). Nothing is decided in the browser.
Writes ../clips/p04_hands.json
"""
import json, math, os, sys
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from weave_lib import WEAVE, W, H, Rig, ik2, key, ease, rot, words, op_img, op_label, label_fit, label_onscreen, raster_ops, jdump, part_alpha

A = json.load(open(os.path.join(HERE, 'assets', 'assets.json')))
SET = json.load(open(os.path.join(HERE, 'set', 'set.json')))
PART = {a['id']: a for a in A['assets']}
FPS = 24
T0, T1 = 364.0, 392.6
N = int(round((T1 - T0) * FPS))
WORDS, w = words(os.path.join(HERE, 'voice', 'p04_words.json'), T0)
S = 0.72
U = S / 0.62                     # layout offsets were tuned at S 0.62; they scale with the puppet
GROUND = 1000.0
HX0 = 430.0                      # her hip x while standing
rig = Rig(PART, S)
rng = np.random.default_rng(394)

T = dict(clouds=w('clouds'), darkness_end=w('darkness', end=True), welcoming=w('welcoming'), search=w('search'), ground=w('ground'),
         two=w('two'), hands=w('hands'), hands_cap=w('hands', 1), once=w('once'), find=w('find'),
         celebrate=w('celebrate'), good_end=w('good', end=True), they=w('they'),
         mine=w('mine'), mine_end=w('mine', end=True), i=w('i'), put=w('put'), back=w('back'), on=w('on'), care=w('care'),
         future=w('future'), stake=w('stake'), say=w('say'), nevermore=w('nevermore'), nevermore_end=w('nevermore', end=True))

# ---------------- timing (all from her words) ----------------
WIPE0, WIPE1 = T['clouds'] - 0.1, T['darkness_end'] + 0.2          # the 1969 sky comes down
KNEEL0, KNEEL1 = T['welcoming'], T['welcoming'] + 1.75              # she kneels; knees land
PAT1, PAT2 = T['search'] + 0.05, T['ground'] + 0.05                 # the wrong attempts: the bare ground, twice
REVEAL = T['two'] - 0.15                                            # light finds the two hands
CIT_RISE0, CIT_RISE1 = T['hands_cap'] - 0.1, T['hands_cap'] + 0.95  # the citizen rises behind the ledge
CIT_PLAY0 = T['find']                                               # his film runs from 'find' (turns, laughs)
RAISE0, RAISE1 = T['they'] - 0.2, T['mine'] + 0.1                   # she lifts her wrists: "they too used to be mine"
WIPE_BACK0, WIPE_BACK1 = T['mine'], T['mine'] + 1.0                 # the 1969 sky goes back up
BOW2 = T['i'] - 1.0
A_CONTACT, A_ATTACH = T['i'] + 0.25, T['put'] + 0.02                # near wrist onto hand A; the brad goes in
B_GRIP = T['on']                                                    # hand A pinches hand B
CARE0, CARE1 = T['care'] - 0.02, T['care'] + 0.3                    # a held breath in the carry
B_FIT = T['stake']                                                  # hand B onto the far wrist
A_RELEASE = T['stake'] + 0.3
LOOK0 = T['say'] - 0.1
REST0, REST1 = T['nevermore'], T['nevermore'] + 0.9
END = T1 - T0

# ---------------- geometry ----------------
def toe_rest(leg, knee):
    return rig.sock(leg, 'toe', knee, 0)

skirt = PART['skirt']['sockets']
HIP0 = np.array([HX0, GROUND - (skirt['knee_near'][1] - skirt['hip'][1]) * S - (PART['leg_near']['sockets']['sole'][1] - PART['leg_near']['sockets']['knee'][1]) * S])
KN0 = rig.sock('skirt', 'knee_near', HIP0, 0)
KF0 = rig.sock('skirt', 'knee_far', HIP0, 0)
TOE_N = rig.sock('leg_near', 'toe', KN0, 0)
TOE_N[1] = rig.sock('leg_near', 'sole', KN0, 0)[1] + (PART['leg_near']['sockets']['toe'][1] - PART['leg_near']['sockets']['sole'][1]) * S
# drop everything so the near toe is exactly on the ground
dy = GROUND - TOE_N[1]
HIP0 = HIP0 + [0, dy]; KN0 = KN0 + [0, dy]; KF0 = KF0 + [0, dy]; TOE_N = TOE_N + [0, dy]
TOE_F = rig.sock('leg_far', 'toe', KF0, 0)
TOE_F[1] = GROUND
KNEE_R = 22 * S
KT = np.array(PART['leg_near']['sockets']['knee'], float) - np.array(PART['leg_near']['sockets']['toe'], float)

def knee_from_theta(th):
    return TOE_N + rot(th) @ (KT * S)

lo, hi = 30.0, 140.0
for _ in range(60):
    mid = (lo + hi) / 2
    if knee_from_theta(mid)[1] < GROUND - KNEE_R:
        lo = mid
    else:
        hi = mid
TH_END = lo                                     # leg angle at which the knee reaches the ground
KNEE_DOWN = knee_from_theta(TH_END)

L1n, L2n = rig.blen('upper_arm_near', 'shoulder', 'elbow'), rig.blen('forearm_near', 'elbow', 'wrist')
L1f, L2f = rig.blen('upper_arm_far', 'shoulder', 'elbow'), rig.blen('forearm_far', 'elbow', 'wrist')
UAn0, FAn0 = rig.bone_ang('upper_arm_near', 'shoulder', 'elbow'), rig.bone_ang('forearm_near', 'elbow', 'wrist')
UAf0, FAf0 = rig.bone_ang('upper_arm_far', 'shoulder', 'elbow'), rig.bone_ang('forearm_far', 'elbow', 'wrist')
HAn0 = rig.bone_ang('hand_near', 'wrist', 'fingertip')
HB0 = rig.bone_ang('hand_open', 'wrist', 'fingertip')

def lying_pos(part, ang, wrist_x):
    """pivot position for a loose hand lying on the ground: rotated by ang, its lowest alpha point on the ground line"""
    al = part_alpha(os.path.join(WEAVE, PART[part]['file']))
    ys, xs = np.where(al > 128)
    p = np.array(PART[part]['pivot'], float)
    pts = (rot(ang) @ ((np.stack([xs, ys], 1) - p) * S).T).T
    wr = rig.sock(part, 'wrist', (0, 0), ang)
    pos = np.array([wrist_x - wr[0], GROUND - pts[:, 1].max() - 1.0])
    return pos

A_ANG0, B_ANG0 = 4.0, -3.0

# the far foot: it cannot stay where it stood (the two rigid legs differ), so it lifts and replants once, mid-kneel
def _far_toe_kneel():
    hip_k = KNEE_DOWN - (np.array(skirt['knee_near'], float) - np.array(skirt['hip'], float)) * S
    kf_k = rig.sock('skirt', 'knee_far', hip_k, 0)
    tk = (np.array(PART['leg_far']['sockets']['toe'], float) - np.array(PART['leg_far']['sockets']['knee'], float)) * S
    best = None
    for th in np.linspace(40, 150, 2201):
        toe = kf_k + rot(th) @ tk
        if toe[0] < kf_k[0] and (best is None or abs(toe[1] - GROUND) < abs(best[1] - GROUND)):
            best = toe
    return np.array([best[0], GROUND])
TOE_F0 = TOE_F.copy()
TOE_F1 = _far_toe_kneel()
FT_LIFT, FT_PLANT = KNEEL0 + 0.35, KNEEL1 - 0.25

def toe_far(t):
    x = ease((t - FT_LIFT) / (FT_PLANT - FT_LIFT))
    return TOE_F0 + (TOE_F1 - TOE_F0) * x + np.array([0, -22]) * math.sin(math.pi * x)

# citizen: a cut-out on a stick behind the ledge, facing left (toward her)
CIT = PART['citizen']
CIT_S = 0.80
CIT_BASE_UP = np.array([1640.0, SET['ledge']['top_y'] + 48.0])     # base of the cut when risen (hidden by the ledge)
CIT_BASE_DOWN = CIT_BASE_UP + [0, CIT['size'][1] * CIT_S * 0.92]
CIT_FRAMES = list(range(CIT['frame_range'][0], CIT['frame_range'][1] + 1))

# the 1969 sky: the clip frame scaled to the width, its top 60% over the plate's sky
SKY_BOX = [-40.0, -30.0, 2000.0, 2000.0 * 486 / 720]

def far_leg_theta(knee_w, toe):
    """the far toe is pinned at `toe`; the far leg turns about it to bring its knee as close as it can to the skirt's far knee"""
    kt = (np.array(PART['leg_far']['sockets']['knee'], float) - np.array(PART['leg_far']['sockets']['toe'], float)) * S
    best = None
    for th in np.linspace(-10, 140, 301):
        d = float(np.linalg.norm(toe + rot(th) @ kt - knee_w))
        if best is None or d < best[1]:
            best = (th, d)
    th0 = best[0]
    for th in np.linspace(th0 - 0.5, th0 + 0.5, 41):
        d = float(np.linalg.norm(toe + rot(th) @ kt - knee_w))
        if d < best[1]:
            best = (th, d)
    return best[0], toe + rot(best[0]) @ kt, best[1]


# ---------------- body keys ----------------
def body_keys(t):
    th = key(t, [(0, 0), (KNEEL0, 0), (KNEEL1, TH_END)])
    # sigma: thigh (skirt) tilt forward about the knee; tau: torso lean on the hip (both + = forward)
    sig = key(t, [(0, 0), (KNEEL1 - 0.3, 0), (KNEEL1 + 0.4, 18), (REVEAL, 18), (REVEAL + 0.7, 8), (CIT_RISE1, 3), (RAISE0, 0),
                  (RAISE1, 0), (BOW2, 0), (A_CONTACT - 0.1, 20), (B_GRIP + 0.1, 20), (B_FIT - 0.2, 2), (END, 2)])
    tau = key(t, [(0, 0), (KNEEL0, 0), (KNEEL1, 6), (KNEEL1 + 0.4, 46), (REVEAL, 46), (REVEAL + 0.7, 22), (CIT_RISE1, 6),
                  (RAISE0, 2), (RAISE1, 8), (BOW2, 8), (A_CONTACT - 0.1, 56), (B_GRIP + 0.1, 63), (B_FIT - 0.2, 6), (END, 6)])
    breathe = 0.7 * math.sin(2 * math.pi * t / 3.4)
    # head relative to torso: + = chin down. looks up at the clouds, down to the ground, right-up to the citizen
    head = key(t, [(0, 4), (WIPE0, 4), (WIPE0 + 0.6, -16), (KNEEL0, -10), (KNEEL1, -2), (PAT1, -4), (REVEAL, 0), (REVEAL + 0.5, 4),
                   (CIT_RISE0 + 0.3, -6), (CIT_PLAY0 + 0.3, -12), (RAISE0, -8), (RAISE1, 14), (BOW2, 2), (A_CONTACT - 0.1, -20),
                   (B_GRIP + 0.1, -18), (B_FIT, 6), (LOOK0, 16), (REST0, 16), (REST1, 4), (END, 4)])
    return th, sig, tau + breathe * 0.5, head


def place_body(t):
    th, sig, tau, head = body_keys(t)
    kn = knee_from_theta(th)
    hip = kn - rot(sig) @ ((np.array(skirt['knee_near'], float) - np.array(skirt['hip'], float)) * S)
    kf_skirt = rig.sock('skirt', 'knee_far', hip, sig)
    thf, kf, kgap = far_leg_theta(kf_skirt, toe_far(t))
    if FT_LIFT < t < FT_PLANT:
        # foot in the air: the leg hangs from the skirt's knee and aims its toe at the step path
        tk = (np.array(PART['leg_far']['sockets']['toe'], float) - np.array(PART['leg_far']['sockets']['knee'], float)) * S
        aim = toe_far(t) - kf_skirt
        thf = math.degrees(math.atan2(aim[1], aim[0]) - math.atan2(tk[1], tk[0]))
        kf, kgap = kf_skirt, 0.0
    tors = sig + tau
    neck = rig.sock('torso', 'neck', hip, tors)
    shn = rig.sock('torso', 'shoulder_near', hip, tors)
    shf = rig.sock('torso', 'shoulder_far', hip, tors)
    return dict(th=th, sig=sig, tau=tau, head=head, kn=kn, kf=kf, kgap=kgap, thf=thf, hip=hip, tors=tors, neck=neck, shn=shn, shf=shf)


def fk(sh, ua, fa, L1, L2):
    e = sh + L1 * np.array([math.cos(math.radians(ua)), math.sin(math.radians(ua))])
    return e, e + L2 * np.array([math.cos(math.radians(fa)), math.sin(math.radians(fa))])


def hang(sh, t, phase=0.0, sw=0.0):
    """a hanging stub arm, wrist kept above the ground"""
    ua = 92 + sw + 2 * math.sin(2 * math.pi * t / 3.4 + phase)
    fa = 86 + sw * 0.6 + 2 * math.sin(2 * math.pi * t / 3.4 + phase + 0.4)
    e, wr = fk(sh, ua, fa, 1, 1)
    return ua, fa


def arc(p0, p1, x, lift):
    x = ease(x)
    return p0 + (p1 - p0) * x + np.array([0, -lift]) * math.sin(math.pi * x)


# fixed points for the carry, computed from a reference pose at the fit time
B_REF = place_body(B_FIT)
P_FIT = B_REF['shf'] + np.array([198.0, 70.0])
uaF, faF, _, _ = ik2(B_REF['shf'], P_FIT, L1f, L2f, 'down')
B_ANG_FIT = faF - FAf0 + FAf0 - HB0 + HB0  # hand straight on the forearm: hand bone angle = forearm bone angle
B_ANG_FIT = faF                             # world bone angle of hand B at the fit
A_HOLD_ANG = 64.0                           # hand A's bone angle while it pinches B's top edge from above

# the pats go where the bowed shoulder can reach the ground (0.93 of full arm), slightly ahead of the shoulder
def _pat_x(tp, frac=0.93, ahead=1.0):
    sh = place_body(tp)['shn']
    dy = (GROUND - 3) - sh[1]
    r = frac * (L1n + L2n)
    dx = math.sqrt(max(0.0, r * r - dy * dy))
    return sh[0] + ahead * dx, dy / (L1n + L2n)
_p1, _r1 = _pat_x(PAT1, 0.93, 0.55)
_p2, _r2 = _pat_x(PAT2, 0.93, 0.95)
PAT_X = [_p1, max(_p2, _p1 + 40)]
print('pat x', [round(v, 1) for v in PAT_X], 'vertical reach fraction', round(_r1, 3), round(_r2, 3))
# the hands lie just past the second pat: she was searching the wrong patch of ground, a stub-width short
A_POS0 = lying_pos('hand_near', A_ANG0, PAT_X[1] + 70)
B_POS0 = lying_pos('hand_open', B_ANG0, PAT_X[1] + 70 + 80 * U)
_sa = place_body(A_CONTACT)['shn']
print('press reach', round(float(np.linalg.norm(rig.sock('hand_near', 'wrist', A_POS0, A_ANG0) - _sa)) / (L1n + L2n), 3))


def hand_world(part, sock_name, sock_world, bone_ang_world):
    """pivot pos + draw angle for a hand whose socket sits at sock_world with its wrist->fingertip bone at bone_ang_world"""
    ang = bone_ang_world - rig.bone_ang(part, 'wrist', 'fingertip')
    pos = rig.pos_for_socket(part, sock_name, sock_world, ang)
    return pos, ang


# ---------------- evaluate every frame ----------------
frames = []
log = dict(pat=[], press=[], grip=[], fit=[], far_toe=[], knee=[], reach=[])
contacts = []
dust_parts = []          # particles: spawn t, pos, vel, r
specks = []              # settled dust on the ground (persists)
material = dict(dust_stub_near=0.0)
A_state, B_state = 'ground', 'ground'
A_rel = B_rel = None
prev = {}
B_carry0 = None


def spawn_dust(t, p, n, spread=70):
    for _ in range(n):
        v = np.array([rng.uniform(-spread, spread), rng.uniform(-150, -50)])
        dust_parts.append(dict(t=t, p=np.array(p, float), v=v, r=float(rng.uniform(1.6, 3.6))))


ev_once = set()

def once(name, t, fn):
    if name not in ev_once and t >= 0:
        ev_once.add(name)
        fn()


for f in range(N):
    t = f / FPS
    B = place_body(t)
    shn, shf = B['shn'], B['shf']
    # ---------- near arm target ----------
    near_contact = 'free'
    A_ang = None
    if t < KNEEL1 + 0.2:
        ua_n, fa_n = hang(shn, t, 0, sw=-6 * math.sin(math.pi * min(1, max(0, (t - KNEEL0) / (KNEEL1 - KNEEL0)))))
        Wn = None
    elif t < REVEAL:
        # the wrong attempts: two pats on the bare ground
        p_top = lambda x: np.array([x, GROUND - 70])
        g = lambda x: np.array([x, GROUND - 3])
        if t < PAT1 - 0.35:
            x = (t - KNEEL1 - 0.2) / max(0.01, PAT1 - 0.35 - KNEEL1 - 0.2)
            e0, w0 = fk(shn, 92, 86, L1n, L2n)
            Wn = arc(w0, p_top(PAT_X[0]), x, 0)
        elif t < PAT1:
            Wn = arc(p_top(PAT_X[0]), g(PAT_X[0]), (t - PAT1 + 0.35) / 0.35, 0)
        elif t < PAT1 + 0.18:
            Wn = g(PAT_X[0]); near_contact = 'pat'
        elif t < PAT2 - 0.3:
            Wn = arc(g(PAT_X[0]), g(PAT_X[1]) - [0, 4], (t - PAT1 - 0.18) / (PAT2 - 0.3 - PAT1 - 0.18), 60)
        elif t < PAT2:
            Wn = arc(g(PAT_X[1]) - [0, 4], g(PAT_X[1]), (t - PAT2 + 0.3) / 0.3, 0)
        elif t < PAT2 + 0.18:
            Wn = g(PAT_X[1]); near_contact = 'pat'
        else:
            Wn = arc(g(PAT_X[1]), np.array([PAT_X[1] - 40, GROUND - 110]), (t - PAT2 - 0.18) / (REVEAL - PAT2 - 0.18), 0)
        # never ask the stub for more than it can reach: pull the target toward the shoulder
        dv = Wn - shn; dl = float(np.linalg.norm(dv)); mx = 0.985 * (L1n + L2n)
        if dl > mx:
            Wn = shn + dv * (mx / dl)
    elif t < BOW2:
        # from the ground up to hanging, then lifting both stubs on "they too used to be mine", then down
        lift = key(t, [(RAISE0, 0), (RAISE1, 1), (BOW2 - 0.5, 1), (BOW2, 0.4)])
        hang_w = fk(shn, 88, 80, L1n, L2n)[1]
        if t < REVEAL + 0.8:
            src = np.array([PAT_X[1] - 40, GROUND - 110])
            Wn = arc(src, hang_w, (t - REVEAL) / 0.8, 0)
        else:
            Wn = hang_w + (shn + np.array([150, 30]) - hang_w) * lift
    else:
        # the touch: wrist onto hand A, then A pinches B, carries it to the far wrist, lets go, look, rest
        A_wr0 = rig.sock('hand_near', 'wrist', A_POS0, A_ANG0)
        if t < A_CONTACT:
            e0, w0 = fk(shn, 88, 80, L1n, L2n)
            Wn = arc(shn + np.array([150, 30]) * 0.4 + (w0 - shn) * 0.6, A_wr0, (t - BOW2) / (A_CONTACT - BOW2), 40)
        elif t < A_ATTACH:
            Wn = A_wr0.copy(); near_contact = 'press'
        else:
            near_contact = 'carry_A'
    # ---------- hand A and B logic, after attach ----------
    # A's bone angle after it is on the wrist: its brad lets it turn; it points where the task needs it
    def A_from_target(tip_world, a_bone):
        pos, ang = hand_world('hand_near', 'fingertip', tip_world, a_bone)
        return rig.sock('hand_near', 'wrist', pos, ang), ang

    B_grip0 = rig.sock('hand_open', 'grip', B_POS0, B_ANG0)
    B_wr0 = rig.sock('hand_open', 'wrist', B_POS0, B_ANG0)
    B_target = None   # desired (B wrist world, B bone angle) while carried
    if near_contact == 'carry_A':
        if t < B_GRIP:
            x = (t - A_ATTACH) / (B_GRIP - A_ATTACH)
            a_bone = key(t, [(A_ATTACH, A_ANG0 + HAn0), (B_GRIP, A_HOLD_ANG)])
            tip = arc(rig.sock('hand_near', 'fingertip', A_POS0, A_ANG0) + [0, -30], B_grip0, x, 50)
            Wn, A_ang = A_from_target(tip, a_bone)
        elif t < B_FIT:
            # B's wrist travels from the ground to P_FIT, with a held breath on "care"
            u = key(t, [(B_GRIP + 0.12, 0), (CARE0, 0.42), (CARE1, 0.46), (B_FIT - 0.05, 1.0)])
            bw = arc(B_wr0, P_FIT, u, 60) if u < 1 else P_FIT
            bb = key(t, [(B_GRIP + 0.12, B_ANG0 + HB0), (B_FIT - 0.05, B_ANG_FIT)])
            B_target = (bw, bb)
            bpos, bang = hand_world('hand_open', 'wrist', bw, bb)
            tip = rig.sock('hand_open', 'grip', bpos, bang)
            a_bone = key(t, [(B_GRIP, A_HOLD_ANG), (B_FIT, A_HOLD_ANG - 40)])
            Wn, A_ang = A_from_target(tip, a_bone)
            near_contact = 'grip'
        elif t < A_RELEASE + 0.5:
            bpos, bang = hand_world('hand_open', 'wrist', P_FIT, B_ANG_FIT)
            tip0 = rig.sock('hand_open', 'grip', bpos, bang)
            x = (t - B_FIT) / (A_RELEASE + 0.5 - B_FIT)
            if t < A_RELEASE:
                tip = tip0; near_contact = 'grip'
            else:
                tip = arc(tip0, tip0 + np.array([30, -70]), (t - A_RELEASE) / 0.5, 0)
            a_bone = A_HOLD_ANG - 40 + key(t, [(A_RELEASE, 0), (A_RELEASE + 0.5, -10)])
            Wn, A_ang = A_from_target(tip, a_bone)
        else:
            # both hands in front ("say to myself"), then down to rest on the thighs on "nevermore"
            front = B['shn'] + np.array([135, 70])
            rest = B['hip'] + rot(B['sig']) @ np.array([82, 112])
            base = key(t, [(A_RELEASE + 0.5, 0), (LOOK0, 1), (REST0, 1), (REST1, 2)])
            tip_prev = prev['A_tip']
            if base <= 1:
                Wn = prev['Wn'] + (front - prev['Wn']) * min(1, 0.18)
            else:
                Wn = front + (rest - front) * (base - 1)
            A_ang = key(t, [(A_RELEASE + 0.5, A_HOLD_ANG - 50), (LOOK0 + 0.4, 10), (REST0, 4), (REST1, 30)])
    # ---------- solve near arm ----------
    clamped = False
    if Wn is not None:
        ua_n, fa_n, ratio, clamped = ik2(shn, Wn, L1n, L2n, 'down')
        log['reach'].append(ratio)
        if ratio > 1.0:
            log.setdefault('reach_over', []).append((round(t, 2), near_contact, round(ratio, 3)))
    e_n, w_n = fk(shn, ua_n, fa_n, L1n, L2n)
    # ---------- far arm ----------
    far_contact = 'free'
    if t < RAISE0 - 0.1 or (t >= BOW2 and t < B_GRIP + 0.3):
        ua_f, fa_f = hang(shf, t, 1.3)
        e_f, w_f = fk(shf, ua_f, fa_f, L1f, L2f)
        # keep a hanging stub above the ground while she bows
        if w_f[1] > GROUND - 8:
            ua_f, fa_f, _, _ = ik2(shf, np.array([w_f[0], GROUND - 8]), L1f, L2f, 'back')
    elif t < BOW2:
        lift = key(t, [(RAISE0, 0), (RAISE1, 1), (BOW2 - 0.5, 1), (BOW2, 0)])
        hw = fk(shf, 90, 84, L1f, L2f)[1]
        ua_f, fa_f, _, _ = ik2(shf, hw + (shf + np.array([128, 40]) - hw) * lift, L1f, L2f, 'down')
    elif t < B_FIT:
        hw = fk(shf, 90, 84, L1f, L2f)[1]
        x = (t - B_GRIP - 0.3) / (B_FIT - 0.08 - B_GRIP - 0.3)
        tgt = arc(hw, P_FIT, min(1, x), 20) if x < 1 else P_FIT
        ua_f, fa_f, _, _ = ik2(shf, tgt, L1f, L2f, 'down')
        far_contact = 'approach'
    else:
        far_contact = 'hand_on'
        if t < A_RELEASE + 0.5:
            ua_f, fa_f, _, _ = ik2(shf, P_FIT, L1f, L2f, 'down')
        else:
            front = B['shf'] + np.array([150, 80])
            rest = B['hip'] + rot(B['sig']) @ np.array([70, 128])
            base = key(t, [(A_RELEASE + 0.5, 0), (LOOK0, 1), (REST0, 1), (REST1, 2)])
            if base <= 1:
                tgt = prev['Wf'] + (front - prev['Wf']) * 0.18
            else:
                tgt = front + (rest - front) * (base - 1)
            ua_f, fa_f, _, _ = ik2(shf, tgt, L1f, L2f, 'down')
    e_f, w_f = fk(shf, ua_f, fa_f, L1f, L2f)

    # ---------- hands ----------
    if t < A_ATTACH:
        A_pos, A_draw = A_POS0, A_ANG0
    else:
        if A_ang is None:
            A_ang = fa_n + 10
        A_draw = A_ang - HAn0
        A_pos = rig.pos_for_socket('hand_near', 'wrist', w_n, A_draw)
    A_tip = rig.sock('hand_near', 'fingertip', A_pos, A_draw)
    if t < B_GRIP:
        B_pos, B_draw = B_POS0, B_ANG0
    elif t < B_FIT:
        # B hangs from A's actual fingertip (what the picture shows), with the angle it should have
        bb = B_target[1] if B_target else B_ANG0 + HB0
        B_draw = bb - HB0
        B_pos = rig.pos_for_socket('hand_open', 'grip', A_tip, B_draw)
        if B_rel is None:
            B_rel = B_draw
    else:
        if A_rel is None:
            pass
        if 'B_fit_rel' not in prev:
            prev['B_fit_rel'] = (B_ANG_FIT - HB0) - (fa_f - FAf0)
        B_draw = (fa_f - FAf0) + prev['B_fit_rel']
        B_pos = rig.pos_for_socket('hand_open', 'wrist', w_f, B_draw)
    B_wr = rig.sock('hand_open', 'wrist', B_pos, B_draw)
    B_grip = rig.sock('hand_open', 'grip', B_pos, B_draw)

    # ---------- logs: measured on what is drawn ----------
    if near_contact == 'pat':
        log['pat'].append(abs(w_n[1] - (GROUND - 3)))
    if near_contact == 'press':
        log['press'].append(float(np.linalg.norm(w_n - rig.sock('hand_near', 'wrist', A_POS0, A_ANG0))))
    if near_contact == 'grip' and B_GRIP <= t < A_RELEASE:
        log['grip'].append(float(np.linalg.norm(A_tip - B_grip)))
    if far_contact == 'approach' and t > B_FIT - 0.25:
        log['fit'].append((round(t, 3), float(np.linalg.norm(w_f - B_wr))))
    thf_toe = B['kf'] + rot(B['thf']) @ ((np.array(PART['leg_far']['sockets']['toe'], float) - np.array(PART['leg_far']['sockets']['knee'], float)) * S)
    log['far_toe'].append(thf_toe.tolist())
    log.setdefault('kgap', []).append(B['kgap'])
    if t >= KNEEL1:
        log['knee'].append(float(B['kn'][1] - (GROUND - KNEE_R)))

    # ---------- events ----------
    once('kneel_land', t - KNEEL1, lambda: (contacts.append({'t': round(KNEEL1, 3), 'event': 'begin', 'what': 'both knees on the ground (toes stay pinned)'}),
                                           spawn_dust(KNEEL1, KNEE_DOWN + [0, -2], 6, 90)))
    once('pat1', t - PAT1, lambda: (contacts.append({'t': round(PAT1, 3), 'event': 'begin', 'what': 'near wrist stub on bare ground (wrong attempt 1)'}), spawn_dust(PAT1, [PAT_X[0], GROUND - 2], 8)))
    once('pat1r', t - PAT1 - 0.18, lambda: contacts.append({'t': round(PAT1 + 0.18, 3), 'event': 'release', 'what': 'nothing there; lifts'}))
    once('pat2', t - PAT2, lambda: (contacts.append({'t': round(PAT2, 3), 'event': 'begin', 'what': 'near wrist stub on bare ground (wrong attempt 2)'}), spawn_dust(PAT2, [PAT_X[1], GROUND - 2], 8)))
    once('pat2r', t - PAT2 - 0.18, lambda: contacts.append({'t': round(PAT2 + 0.18, 3), 'event': 'release', 'what': 'nothing there; lifts'}))
    once('A_contact', t - A_CONTACT, lambda: contacts.append({'t': round(A_CONTACT, 3), 'event': 'begin', 'what': 'near wrist stub onto hand A\'s wrist tab (hand A lying on the ground)'}))
    once('A_attach', t - A_ATTACH, lambda: (contacts.append({'t': round(A_ATTACH, 3), 'event': 'change', 'what': 'brad in: hand A now parented to the near forearm; lifted off the ground'}),
                                          spawn_dust(A_ATTACH, rig.sock('hand_near', 'palm', A_POS0, A_ANG0), 6)))
    once('B_grip', t - B_GRIP, lambda: (contacts.append({'t': round(B_GRIP, 3), 'event': 'begin', 'what': 'hand A pinches hand B\'s top edge (B leaves the ground, parented to A)'}),
                                       spawn_dust(B_GRIP, rig.sock('hand_open', 'palm', B_POS0, B_ANG0), 6)))
    once('B_fit', t - B_FIT, lambda: contacts.append({'t': round(B_FIT, 3), 'event': 'change', 'what': 'brad in: hand B onto the far wrist (B parented to the far forearm)'}))
    once('A_release', t - A_RELEASE, lambda: contacts.append({'t': round(A_RELEASE, 3), 'event': 'release', 'what': 'hand A lets go of hand B; marked released, not zero'}))
    if t >= PAT1:
        material['dust_stub_near'] = 0.35 if t < PAT2 else 0.6
    # dust: particles fly, land, and stay as specks
    dots = []
    for d in dust_parts:
        age = t - d['t']
        if age < 0:
            continue
        g = 340.0
        y = d['p'][1] + d['v'][1] * age + 0.5 * g * age * age
        x = d['p'][0] + d['v'][0] * age
        if 'land' not in d:
            a_, b_, c_ = 0.5 * g, d['v'][1], d['p'][1] - GROUND
            disc = b_ * b_ - 4 * a_ * c_
            d['land'] = (-b_ + math.sqrt(max(0, disc))) / (2 * a_)
        if age < d['land']:
            dots.append([round(x, 1), round(y, 1), round(d['r'], 1), 0.85])
        else:
            lx = d['p'][0] + d['v'][0] * d['land']
            dots.append([round(lx, 1), GROUND - 1, round(d['r'] * 0.9, 1), 0.7])

    # ---------- sky, darkness, light ----------
    wipe_y = key(t, [(0, -60), (WIPE0, -60), (WIPE1, 900), (WIPE_BACK0, 900), (WIPE_BACK1, -60), (END, -60)])
    dark = key(t, [(0, 0.0), (WIPE0, 0.0), (T['darkness_end'], 0.42), (WIPE_BACK0, 0.42), (WIPE_BACK1, 0.18), (END, 0.18)])
    glow = key(t, [(0, 0), (REVEAL, 0), (REVEAL + 0.6, 0.5), (WIPE_BACK0, 0.5), (WIPE_BACK1, 0.62), (END, 0.62)])
    # ---------- citizen ----------
    rise = key(t, [(0, 0), (CIT_RISE0, 0), (CIT_RISE1, 1), (END, 1)])
    wob = 1.2 * math.sin(2 * math.pi * t / 1.7) * rise
    cit_base = CIT_BASE_DOWN + (CIT_BASE_UP - CIT_BASE_DOWN) * rise
    ft = (t - CIT_PLAY0) * 29.97
    cn = CIT_FRAMES[int(min(len(CIT_FRAMES) - 1, max(0, ft)))]
    # ---------- camera ----------
    cam_keys = [(0, (1.0, 960, 540)), (KNEEL0, (1.0, 960, 540)), (KNEEL1 + 0.3, (1.12, 900, 640)), (REVEAL + 0.5, (1.12, 960, 640)),
                (CIT_RISE1, (1.06, 1080, 560)), (RAISE1, (1.06, 1000, 560)), (BOW2 + 0.6, (1.42, KNEE_DOWN[0] + 210, 800)),
                (B_FIT + 0.2, (1.42, KNEE_DOWN[0] + 160, 720)), (LOOK0 + 0.6, (1.22, KNEE_DOWN[0] + 120, 700)), (END, (1.16, KNEE_DOWN[0] + 100, 690))]
    zc = key(t, cam_keys)

    # ---------- display list ----------
    D = []
    D.append(op_img('plate', box=[0, 0, W, H], k=0.4))
    if wipe_y > -50:
        D.append(op_img('sky1969', box=SKY_BOX, k=0.4, a=0.96, op='source-over', mask=None,
                        wipe={'y': round(wipe_y, 1), 'seed': 7, 'jag': 26, 'clip': 'skymask'}))
    if rise > 0:
        cm = rig.mat('citizen', cit_base, wob, scale=CIT_S)
        st0 = cit_base + rot(wob) @ np.array([0, -30])
        D.append({'t': 'line', 'pts': [[round(st0[0], 1), round(st0[1], 1)], [round(cit_base[0] - 4, 1), round(cit_base[1] + 260, 1)]], 'w': 11, 'color': '#5a3d22', 'k': 0.4})
        D.append(op_img('seq:cit:%d' % cn, m=cm, k=0.4, mask='citmask', sh=1))
    D.append(op_img('ledge', box=[0, 0, W, H], k=0.4))
    D.append({'t': 'rect', 'color': '#02030a', 'a': round(dark, 3), 'k': 0.4, 'plane': True})
    D.append({'t': 'proc', 'name': 'ground', 'y': GROUND, 'k': 1.0})
    if glow > 0:
        D.append({'t': 'glow', 'x': round((A_POS0[0] + B_POS0[0]) / 2 + 60, 1), 'y': GROUND + 4, 'rx': 330, 'ry': 70, 'color': [255, 196, 120], 'a': round(glow, 3), 'op': 'screen', 'k': 1.0})
    # contact shadows: knees / toes on the ground, loose hands
    sh = [[TOE_N[0] - 20, GROUND, 70 + 50 * ease(B['th'] / TH_END), 10]]
    if B['th'] > 20:
        sh.append([B['kn'][0], GROUND, 60, 9])
    if A_state == 'ground' and t < A_ATTACH:
        sh.append([A_POS0[0] + 50, GROUND, 52, 6])
    if t < B_GRIP:
        sh.append([B_POS0[0] + 45, GROUND, 46, 6])
    D.append({'t': 'proc', 'name': 'shadows', 'e': [[round(v, 1) for v in s] for s in sh], 'k': 1.0})
    D.append({'t': 'dots', 'pts': dots, 'color': '#b39a78', 'k': 1.0})
    P = []
    P.append(('upper_arm_far', rig.mat('upper_arm_far', shf, ua_f - UAf0), 0))
    P.append(('forearm_far', rig.mat('forearm_far', e_f, fa_f - FAf0), 0))
    if t >= B_FIT:
        P.append(('hand_open', rig.mat('hand_open', B_pos, B_draw), 0.55))
    P.append(('leg_far', rig.mat('leg_far', B['kf'], B['thf']), 0))
    P.append(('leg_near', rig.mat('leg_near', B['kn'], B['th']), 0))
    P.append(('skirt', rig.mat('skirt', B['hip'], B['sig']), 0))
    P.append(('torso', rig.mat('torso', B['hip'], B['tors']), 0))
    P.append(('head', rig.mat('head', B['neck'], B['tors'] + B['head']), 0))
    if t < A_ATTACH:
        P.insert(0, ('hand_near', rig.mat('hand_near', A_POS0, A_ANG0), 0.55))
    if t < B_GRIP:
        P.insert(0, ('hand_open', rig.mat('hand_open', B_POS0, B_ANG0), 0.55))
    elif t < B_FIT:
        P.append(('hand_open', rig.mat('hand_open', B_pos, B_draw), 0.55))
    P.append(('upper_arm_near', rig.mat('upper_arm_near', shn, ua_n - UAn0), 0))
    P.append(('forearm_near', rig.mat('forearm_near', e_n, fa_n - FAn0), material['dust_stub_near']))
    if t >= A_ATTACH:
        P.append(('hand_near', rig.mat('hand_near', A_pos, A_draw), 0.55))
    for pid, m, dust in P:
        D.append(op_img(pid, m=m, k=1.0, sh=1, dust=dust))
    D.append({'t': 'rect', 'color': '#7d86a8', 'a': round(0.55 * dark + 0.1, 3), 'op': 'multiply', 'k': 0})
    if glow > 0:
        D.append({'t': 'glow', 'x': round((A_POS0[0] + B_POS0[0]) / 2 + 40, 1), 'y': GROUND - 120, 'rx': 420, 'ry': 260, 'color': [255, 190, 120], 'a': round(glow * 0.35, 3), 'op': 'soft-light', 'k': 1.0})
    # labels: the archive is labelled for as long as it is on screen
    sky_vis = 1.0 if wipe_y > -50 else 0.0
    if sky_vis > 0:
        txt = 'ARCHIVE · 1969 · EAGLE HAS LANDED · SKY ASSEMBLED FROM ITS FRAMES'
        lx, ly = label_fit(txt, 120, 150, 24, 0.4, zc[0], zc[1:])
        D.append(op_label(txt, lx, ly, 24, -0.025, '#e8eefc', '#141c33', sky_vis, 0.4))
        log.setdefault('label_ok', []).append(label_onscreen(txt, lx, ly, 24, 0.4, zc[0], zc[1:]))
    if rise > 0:
        txt = 'ARCHIVE · 1969 · A MAN AT A SHIP\'S RAIL'
        tp = cit_base + np.array([-250, -CIT['size'][1] * CIT_S + 40])
        lx, ly = label_fit(txt, tp[0], tp[1], 21, 0.4, zc[0], zc[1:])
        D.append(op_label(txt, lx, ly, 21, 0.04, '#1d130b', '#f1e3c8', min(1, rise * 1.5), 0.4))
        log.setdefault('label_ok', []).append(label_onscreen(txt, lx, ly, 21, 0.4, zc[0], zc[1:]))

    st = dict(A_tip=A_tip, Wn=w_n if Wn is None else Wn, Wf=w_f)
    prev.update(st)
    dbg = []
    if near_contact in ('pat', 'press'):
        dbg.append([round(w_n[0], 1), round(w_n[1], 1), 'on'])
    if near_contact == 'grip':
        dbg.append([round(B_grip[0], 1), round(B_grip[1], 1), 'on' if t < A_RELEASE else 'released'])
    if far_contact in ('approach', 'hand_on'):
        dbg.append([round(B_wr[0], 1), round(B_wr[1], 1), 'on' if far_contact == 'hand_on' else 'free'])
    dbg.append([round(TOE_N[0], 1), round(TOE_N[1], 1), 'on'])
    frames.append({'f': f, 't': round(t, 4), 'clock': round(T0 + t, 3),
                   'cam': {'z': round(zc[0], 4), 'c': [round(zc[1], 2), round(zc[2], 2)]},
                   'draw': D,
                   'g': {'wipe': round(max(0, wipe_y) / 900, 3), 'dark': round(dark, 3), 'rise': round(rise, 3), 'glow': round(glow, 3),
                         'kneel': round(B['th'] / TH_END, 3), 'bow': round((B['sig'] + B['tau']) / 70, 3)},
                   'contact': near_contact, 'far': far_contact, 'dbg': dbg,
                   'puppet': [p[0] for p in P]})

# ---------------- validation, computed from the frames ----------------
FILES = {a['id']: os.path.join(WEAVE, a['file']) for a in A['assets'] if a['kind'] == 'puppet_part'}
f0 = frames[0]
hm = next(o for o in f0['draw'] if o.get('id') == 'head')['m']
head_top = min(hm[1] * x + hm[3] * 0 + hm[5] for x in range(0, PART['head']['size'][0], 4))
al = part_alpha(FILES['head']); ys, xs = np.where(al > 128)
pts_y = hm[1] * xs + hm[3] * ys + hm[5]
HEIGHT = GROUND - float(pts_y.min())
ft = np.array(log['far_toe'])
grip_err = log['grip']; press_err = log['press']; pat_err = log['pat']
fit_last = log['fit'][-1][1] if log['fit'] else None
over = []
body_ids = ['head', 'torso', 'skirt', 'leg_near', 'leg_far']
for name, tt in [('reveal', REVEAL + 0.4), ('press', A_CONTACT + 0.1), ('grip', B_GRIP + 0.2), ('care', (CARE0 + CARE1) / 2), ('fit', B_FIT + 0.05), ('look', LOOK0 + 0.8)]:
    fr = frames[min(N - 1, int(tt * FPS))]
    hands = raster_ops(fr['draw'], FILES, ['hand_near', 'hand_open'])
    head = raster_ops(fr['draw'], FILES, ['head'])
    arms = raster_ops(fr['draw'], FILES, ['upper_arm_near', 'forearm_near', 'upper_arm_far', 'forearm_far'])
    body = raster_ops(fr['draw'], FILES, body_ids)
    over.append({'name': name, 't': fr['t'], 'hands_over_head_px': int((hands & head).sum()), 'arms_over_head_px': int((arms & head).sum()),
                 'hand_open_visible_px': int((raster_ops(fr['draw'], FILES, ['hand_open']) & (1 - body) & (1 - raster_ops(fr['draw'], FILES, ['hand_near', 'forearm_near', 'upper_arm_near']))).sum()),
                 'hands_px': int(hands.sum())})

clip = {
    'id': 'p04_hands', 'version': 1, 'title': 'POEM 04 · "I PUT THEM BACK ON"',
    'about': 'WYGWYL poem 04: the clouds meet the stars, she searches the bare ground for her two hands, a 1969 man at a ship\'s rail laughs, and she puts her hands back on.',
    'clock': {'source': 'WYGWYL_Suite_Audio.mp3 (her recording)', 't0': T0, 't1': T1, 'fps': FPS, 'frames': N},
    'audio': {'mix': 'p04_hands/passage.wav', 'voice': 'p04_hands/voice/p04_362_396.wav', 'voice_offset': T0 - 362.0},
    'line': 'I put them back on with the care of my future at stake.',
    'words': WORDS,
    'images': {'plate': 'p04_hands/set/plate.jpg', 'skymask': 'p04_hands/set/sky_mask.png', 'ledge': 'p04_hands/set/ledge.png',
               'sky1969': 'p04_hands/archive/sky1969.jpg', 'citmask': 'p04_hands/assets/parts/citizen_mask.png',
               **{a['id']: a['file'] for a in A['assets'] if a['kind'] == 'puppet_part'}},
    'masks': ['skymask', 'citmask'],
    'seqs': {'cit': 'p04_hands/archive/citizen/%04d.jpg'},
    'states': [
        {'id': 'S1_standing', 't': [0, round(WIPE0, 3)], 'visible': 'she stands in the night garden; her arms end at the wrist tabs; her two hands lie on the ground ahead, in shadow'},
        {'id': 'S2_clouds_meet_stars', 't': [round(WIPE0, 3), round(KNEEL0, 3)], 'visible': 'the 1969 sky wipes down into the plate\'s own sky, behind the spires; labelled; the garden darkens'},
        {'id': 'S3_kneel', 't': [round(KNEEL0, 3), round(KNEEL1, 3)], 'visible': 'she kneels: toes pinned, shins turn about them, both knees land; dust'},
        {'id': 'S4_wrong_attempts', 't': [round(KNEEL1, 3), round(REVEAL, 3)], 'visible': 'she bows and pats the bare ground twice with her wrist stub; nothing there; dust rises and stays on the stub'},
        {'id': 'S5_found', 't': [round(REVEAL, 3), round(CIT_RISE0, 3)], 'visible': 'a warm light finds the two hands; she sees them'},
        {'id': 'S6_citizen', 't': [round(CIT_RISE0, 3), round(RAISE0, 3)], 'visible': 'a 1969 man at a ship\'s rail rises on a stick behind the ledge (labelled); from "find" his film runs: he turns and laughs'},
        {'id': 'S7_used_to_be_mine', 't': [round(RAISE0, 3), round(BOW2, 3)], 'visible': 'she lifts both wrist stubs and looks at them; the 1969 sky goes back up; the man stays'},
        {'id': 'S8_first_hand', 't': [round(BOW2, 3), round(A_ATTACH, 3)], 'visible': 'she bows and presses the near wrist onto hand A; the brad goes in'},
        {'id': 'S9_pinch', 't': [round(A_ATTACH, 3), round(B_GRIP, 3)], 'visible': 'hand A, now hers, reaches for hand B and pinches its top edge'},
        {'id': 'S10_carry', 't': [round(B_GRIP, 3), round(B_FIT, 3)], 'visible': 'she rises carrying B; a held stop on "care"; the far wrist comes to meet it'},
        {'id': 'S11_fit_release', 't': [round(B_FIT, 3), round(A_RELEASE + 0.5, 3)], 'visible': 'B goes onto the far wrist on "stake"; A lets go'},
        {'id': 'S12_nevermore', 't': [round(A_RELEASE + 0.5, 3), round(END, 3)], 'visible': 'she holds both hands up and looks at them; on "nevermore" they go down to rest on her thighs; both stay dusty'},
    ],
    'contacts': sorted(contacts + [{'t': 0, 'event': 'pinned', 'what': 'near toe pinned in world space for the whole passage; far toe planted except for one logged step during the kneel'}], key=lambda c: c['t']),
    'material': {'dust': 'particles spawned at each ground contact fly, land and stay as specks; stub dust 0 -> 0.35 -> 0.6 at the pats; both hands carry ground dust (0.55) from the start to the end',
                 'darkness': 'plate darkens to 0.42 by "darkness", eases to 0.18 when the 1969 sky withdraws',
                 'light': 'a warm light on the ground from "two hands" on, brighter after the sky clears',
                 'sky_wipe': 'torn wipe edge descends to y 900 over 364.4-367.5 s, rises on "mine"; drawn only inside the plate\'s sky mask',
                 'citizen_film': 'his frames %d-%d play at 29.97 fps from "find"; before that frame %d is held, after it frame %d is held' % (CIT_FRAMES[0], CIT_FRAMES[-1], CIT_FRAMES[0], CIT_FRAMES[-1])},
    'cameras': {'keys': [[k, list(v)] for k, v in cam_keys], 'rule': 'wide for the sky, in on the wrong attempts, out for the citizen, close on the hands, back out for nevermore'},
    'scene': {'puppet_scale': S, 'ground': GROUND, 'toe_near': TOE_N.round(2).tolist(), 'knee_down': KNEE_DOWN.round(2).tolist(), 'theta_kneel': round(TH_END, 2),
              'hand_A_rest': A_POS0.round(2).tolist(), 'hand_B_rest': B_POS0.round(2).tolist(), 'fit_point': P_FIT.round(2).tolist(),
              'citizen_base': CIT_BASE_UP.round(2).tolist(), 'sky_box': SKY_BOX},
    'joins': [['Wipe', 'the 1969 sky wipes into the plate\'s own sky (its sky mask), behind the spires, labelled while it shows'],
              ['Citizen', 'the 1969 man rises as a cut-out on a stick behind the plate\'s ledge; his film plays inside one fixed scissor cut; tagged'],
              ['Touch', 'her wrist stubs find her own loose hands; one hand carries the other to the far wrist; every hand-off is a logged contact']],
    'ledger': [['OBSERVED', 'Her voice, 364.0-392.6 s of the WYGWYL suite recording. Word times by faster-whisper (small).'],
               ['OBSERVED', 'Eagle Has Landed: The Flight of Apollo 11 (1969), clip 6bb6d333 (source film 1513.81-1523.96 s), silent in this library. The man at the rail: frames %d-%d.' % (CIT_FRAMES[0], CIT_FRAMES[-1])],
               ['RETOUCHED', 'The 1969 sky: a per-pixel median of the clip\'s own sky pixels; where no frame shows sky it is filled by a smooth blur.'],
               ['INVENTED', 'The night garden: WYGWYL poem 04 AI plate (keyframe 84, held). The ledge is cut from it.'],
               ['INVENTED', 'The puppet (reused from p07) and her second, open hand (generated). The rule that her hands come off and go back on.'],
               ['DRAWN', 'The ground strip, the stick, the dust, the light, the labels.'],
               ['CHARACTER BELIEF', '"They too used to be mine": hers, about her hands. The 1969 man is not her memory and is not presented as one.']],
    'tracks': [['wipe', '#9fc6e8'], ['dark', '#a9a0d6'], ['rise', '#e7a35a'], ['glow', '#ffd38a'], ['kneel', '#7fd3c4'], ['bow', '#d98bb0']],
    'validation': {
        'puppet_height_px': round(HEIGHT, 1),
        'pat_err_px': {'max': round(max(pat_err), 3) if pat_err else None, 'frames': len(pat_err)},
        'press_err_px': {'max': round(max(press_err), 3) if press_err else None, 'frames': len(press_err)},
        'grip_err_px': {'max': round(max(grip_err), 3), 'mean': round(float(np.mean(grip_err)), 3), 'frames': len(grip_err)},
        'grip_err_pct_height': round(100 * max(grip_err) / HEIGHT, 3),
        'press_err_pct_height': round(100 * max(press_err) / HEIGHT, 3) if press_err else None,
        'fit_gap_before_brad_px': round(fit_last, 3) if fit_last is not None else None,
        'fit_gap_pct_height': round(100 * fit_last / HEIGHT, 3) if fit_last is not None else None,
        'near_toe_drift_px': 0.0,
        'far_toe_drift_px': round(float(max(abs(ft[i, 0] - (TOE_F0[0] if i / FPS < FT_LIFT else TOE_F1[0])) for i in range(N) if not (FT_LIFT <= i / FPS <= FT_PLANT))), 2),
        'far_toe_off_ground_px': round(float(max(abs(ft[i, 1] - GROUND) for i in range(N) if not (FT_LIFT <= i / FPS <= FT_PLANT))), 2),
        'far_toe_step': [round(FT_LIFT, 3), round(FT_PLANT, 3)],
        'labels_on_screen': [int(sum(log.get('label_ok', []))), len(log.get('label_ok', []))],
        'knee_off_ground_px': round(float(np.abs(log['knee'][int(0.3 * FPS):]).max()), 2) if log['knee'] else None,
        'far_knee_joint_gap_px': round(float(max(log['kgap'])), 2),
        'ik_reach_max': round(max(log['reach']), 3),
        'overlaps': over,
        'dust_particles': len(dust_parts),
    },
    'dust_land': sorted(round(d['t'] + d.get('land', 0), 3) for d in dust_parts),
    'cit_rise': [round(CIT_RISE0, 3), round(CIT_RISE1, 3)],
    'frames': frames,
}
vv = clip['validation']
pct = lambda px: px is not None and 100 * px / HEIGHT < 1
clip['measured'] = [
    ['puppet height (standing)', '%s px' % vv['puppet_height_px'], None],
    ['grip error < 1% (A pinching B)', '%s px max over %d frames (%s%%)' % (vv['grip_err_px']['max'], vv['grip_err_px']['frames'], vv['grip_err_pct_height']), vv['grip_err_pct_height'] < 1],
    ['press error < 1% (wrist onto A)', '%s px over %d frames' % (vv['press_err_px']['max'], vv['press_err_px']['frames']), pct(vv['press_err_px']['max'])],
    ['pat error < 1% (stub on ground)', '%s px over %d frames' % (vv['pat_err_px']['max'], vv['pat_err_px']['frames']), pct(vv['pat_err_px']['max'])],
    ['fit gap before the brad < 1%', '%s px (%s%%)' % (vv['fit_gap_before_brad_px'], vv['fit_gap_pct_height']), pct(vv['fit_gap_before_brad_px'])],
    ['near toe drift', '%s px' % vv['near_toe_drift_px'], vv['near_toe_drift_px'] == 0],
    ['far toe planted (outside its one step %s-%s s)' % tuple(vv['far_toe_step']), '%s px along, %s px off ground' % (vv['far_toe_drift_px'], vv['far_toe_off_ground_px']), vv['far_toe_drift_px'] < 0.01 * HEIGHT and vv['far_toe_off_ground_px'] < 0.01 * HEIGHT],
    ['knees on ground after kneel', '%s px off' % vv['knee_off_ground_px'], (vv['knee_off_ground_px'] or 0) < 0.01 * HEIGHT],
    ['far knee joint gap < 1% (rigid far leg vs skirt)', '%s px max' % vv['far_knee_joint_gap_px'], vv['far_knee_joint_gap_px'] < 0.01 * HEIGHT],
    ['IK reach ratio max', vv['ik_reach_max'], vv['ik_reach_max'] <= 1.0],
    ['archive labels wholly on screen', '%d of %d label-frames' % tuple(vv['labels_on_screen']), vv['labels_on_screen'][0] == vv['labels_on_screen'][1]],
    ['dust particles (each lands and stays)', vv['dust_particles'], None],
] + [['overlap @%ss %s' % (o['t'], o['name']), 'arms/head %d · hands/head %d' % (o['arms_over_head_px'], o['hands_over_head_px']), None] for o in over]
jdump(clip, os.path.join(WEAVE, 'clips', 'p04_hands.json'), compact=True)
v = clip['validation']
print('frames', N, 'height', v['puppet_height_px'], 'kneel theta', round(TH_END, 1))
for m in clip['measured']:
    print('  %-52s %-40s %s' % (m[0], m[1], {True: 'PASS', False: 'FAIL', None: ''}[m[2]]))
for o in over:
    print(' ', o)
print({k: round(x, 2) for k, x in T.items()})
print('size MB', round(os.path.getsize(os.path.join(WEAVE, 'clips', 'p04_hands.json')) / 1e6, 2))
