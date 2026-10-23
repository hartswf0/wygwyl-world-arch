"""H1 core: pose graph + mesh warp over the painted poses.

Inputs only: the paintings (shots/kits/cut/poet.*.main-poses/*.webp), the Pose Lab
markers (shots/rig/poses_v2/poet__red_black_sunglasses.json, targets[].markers) and the
test set. Nothing from the card-puppet run is used (no solves, no cards, no puppet code).
"""
import json, os, math
import numpy as np, cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MARKERS = os.path.join(ROOT, 'shots/rig/poses_v2/poet__red_black_sunglasses.json')
TESTSET = os.path.join(ROOT, 'shots/scion2/test_set.json')

HEAD_CAP = 20.0  # the head turns less: the neck seam shows first
CAP = 30.0  # max in-plane rotation of any part away from how it was painted (degrees)

# ---------------------------------------------------------------- source curation
# Whole-figure paintings in the red/black suit, not cut at the sheet edge, no held props
# that would travel with the hand. Decided by eye from the contact sheet; reasons kept.
CLEAN = [
    'poet.04.main-poses/04-1-walk-hollow', 'poet.04.main-poses/04-3-walk-the-rows',
    'poet.04.main-poses/04-2-kneel-hollow', 'poet.04.main-poses/04-2-heart-seated',
    'poet.04.main-poses/04-4-empty-cuffs', 'poet.04.main-poses/04-6-rise-flex-reflect',
    'poet.04.main-poses/04-4-sweep-forearms',
    'poet.05.main-poses/q3-restless-lying-1', 'poet.05.main-poses/q3-restless-lying-2',
    'poet.05.main-poses/ask-the-universe-2',
    'poet.07.main-poses/walk-the-room',
    'poet.07.main-poses/push-two-sides-apart', 'poet.07.main-poses/o06-point-at',
    'poet.07.main-poses/chin-up-open-arms',
    'poet.08.main-poses/wince-standing-still-on-with-the-shoulders-beat-',
    'poet.08.main-poses/04-face-head-raised-back-for-slack',
    'poet.08.main-poses/03-gentle-slow-bent-knee-dance-alone',
    'poet.08.main-poses/05-chest-lean-opened-back-head-inhale-back-and-p',
    'poet.08.main-poses/07-push-flat-through-palm-pushes-aside-reach-oth',
    'poet.09.main-poses/falter-at-shoulder-contact',
    'poet.11.main-poses/02-front-guide-stone', 'poet.11.main-poses/03-walk-profile-colonnade',
    'poet.11.main-poses/welcome-new-day',
    'poet.12.main-poses/01', 'poet.12.main-poses/02',
    'poet.13.main-poses/06-refocus', 'poet.13.main-poses/07-hello',
]
# usable after keying out a light, unsaturated prop (bench / envelope); held props remain
KEYED = {
    'poet.13.main-poses/03-letter-fire-crouch': 'envelope keyed out',
}
# tried and dropped: the bench sits in front of his seat, so keying it out cuts the
# figure along the bench edge (08 o06-threequarter-ledge-sit, 11 pool-edge-seated)

EXCLUDED_WHY = {
    'cut at the sheet edge': 'arrive-01, open-arms-02 (hands cut off at the crop), grip-the-mic-stand (arm cut), phone-palm, part-2, 01-cafe-sit, 05/1, 05/2, 07/1, 07/2, 06-walk-to-the-gate, to-one-side, 02-sag, through-06-party-door, most of poet.10',
    'held props / second figure': 'q1-cup-the-star, q2-star-overhead (orb), chin-down-microphone, pluck-the-daisy, 05-fingerprint-palm (stranger hand), set-down-03 (block + hand), 05-read-water x2 (book), 12/03 (hourglass), 13 02-cafe (cup), 04-harvest-reach and 05-becoming-arms (flowers), 08-table-release (table), poet.10 (motorbike), 09 suitcases/phone, 11 01-wall-rear (wall)',
    'other costume': '08-ex-strictly, 09 ex-zips / ex-by-the-cases (olive jacket)',
    'odd projection': 'arms-up-05-with-crowd (seen from below, head small)',
}

BONES = {  # name: (from, to)
    'torso': ('groin', 'neck'), 'head': ('neck', 'head'),
    'uarmL': ('shoulderL', 'elbowL'), 'farmL': ('elbowL', 'wristL'),
    'uarmR': ('shoulderR', 'elbowR'), 'farmR': ('elbowR', 'wristR'),
    'thighL': ('hipL', 'kneeL'), 'shinL': ('kneeL', 'ankleL'), 'footL': ('ankleL', 'toeL'),
    'thighR': ('hipR', 'kneeR'), 'shinR': ('kneeR', 'ankleR'), 'footR': ('ankleR', 'toeR'),
}
CHAINS = {'armL': ['uarmL', 'farmL'], 'armR': ['uarmR', 'farmR'],
          'legL': ['thighL', 'shinL', 'footL'], 'legR': ['thighR', 'shinR', 'footR']}
TORSO_PTS = ['groin', 'neck', 'shoulderL', 'shoulderR', 'hipL', 'hipR']
BONE_W = {'torso': 3, 'head': 2, 'uarmL': 1.5, 'farmL': 1.2, 'uarmR': 1.5, 'farmR': 1.2,
          'thighL': 1.5, 'shinL': 1.2, 'footL': .3, 'thighR': 1.5, 'shinR': 1.2, 'footR': .3}


def load_targets():
    d = json.load(open(MARKERS))
    return {t['id']: t for t in d['targets']}


def family(pid):
    return pid.split('/')[0]


def painting_path(pid):
    return os.path.join(ROOT, 'shots/kits/cut', pid + '.webp')


def load_rgba(pid, key_prop=False):
    im = cv2.imread(painting_path(pid), cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    im = im.copy()
    a = im[..., 3]
    if key_prop:
        hsv = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2HSV)
        light = ((hsv[..., 2] > 150) & (hsv[..., 1] < 90) & (a > 0)).astype(np.uint8)
        light = cv2.morphologyEx(light, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(light)
        kill = np.zeros_like(light)
        for i in range(1, n):
            if st[i, 4] > 0.01 * a.size:  # only big light blobs: zipper highlights stay
                kill[lab == i] = 1
        kill = cv2.dilate(kill, np.ones((7, 7), np.uint8))
        # the prop's thin outline and drop shadow ring
        a[kill > 0] = 0
    # keep the main figure component
    m = (a > 40).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 2:
        big = 1 + np.argmax(st[1:, 4])
        a[lab != big] = 0
    im[..., 3] = a
    return im


def markers(t):
    return {k: np.array(v[:2], float) for k, v in t['markers'].items()}


def conf(t):
    return {k: float(v[-1]) for k, v in t['markers'].items()}


def mirror_markers(M, width):
    out = {}
    for k, p in M.items():
        k2 = k[:-1] + ('R' if k[-1] == 'L' else 'L') if k[-1] in 'LR' else k
        out[k2] = np.array([width - 1 - p[0], p[1]])
    return out


def ang(v):
    return math.degrees(math.atan2(v[1], v[0]))


def wrap(a):
    return (a + 180) % 360 - 180


def blen(M, b):
    a, c = BONES[b]
    return float(np.linalg.norm(M[c] - M[a]))


def view_feat(M):
    L = np.linalg.norm(M['neck'] - M['groin']) + 1e-6
    sw = (M['shoulderL'][0] - M['shoulderR'][0]) / L
    hw = (M['hipL'][0] - M['hipR'][0]) / L
    face = (M['chin'][0] - M['neck'][0]) / L
    return np.array([sw, hw, face])


def swap_side(M, part):
    """swap the L/R labels of one limb chain (arms or legs) of a marker set."""
    keys = {'arm': ['shoulder', 'elbow', 'wrist'], 'leg': ['hip', 'knee', 'ankle', 'toe']}[part]
    M = dict(M)
    for k in keys:
        M[k + 'L'], M[k + 'R'] = M[k + 'R'], M[k + 'L']
    return M


# ---------------------------------------------------------------- pose fit (FK with caps)
def fit(S, T, cap=CAP):
    """Rigidly re-pose source markers S toward target markers T.
    Each part keeps its painted length (global scale only) and turns at most `cap` degrees
    in the picture plane. Returns dict with per-bone transforms and the reached markers."""
    ratios = [blen(T, b) / max(blen(S, b), 1e-3) for b in ['torso', 'uarmL', 'uarmR', 'farmL', 'farmR',
                                                          'thighL', 'thighR', 'shinL', 'shinR']]
    s = float(np.median(ratios))
    want, rot, over = {}, {}, {}
    for b, (a, c) in BONES.items():
        d = wrap(ang(T[c] - T[a]) - ang(S[c] - S[a]))
        want[b] = d
        cb = min(cap, HEAD_CAP) if b == 'head' else cap
        rot[b] = float(np.clip(d, -cb, cb))
        over[b] = max(0.0, abs(d) - cb)
    # boots stay rigid with the shin: the toe markers are silhouette guesses and a boot
    # turned on its own tears at the ankle
    for sd in 'LR':
        rot['foot' + sd] = rot['shin' + sd]
    if legs_cross(S):
        # crossed legs are one sheet of drawing: they ride with the torso, unbent
        for b in ['thighL', 'shinL', 'footL', 'thighR', 'shinR', 'footR']:
            rot[b] = rot['torso']
            over[b] = max(0.0, abs(want[b] - rot[b]) - cap)
    # transforms: p' = s R (p - o) + o'
    X = {}
    P = {}
    def R(deg):
        r = math.radians(deg); return np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
    o = S['groin']; o2 = T['groin']
    X['torso'] = (s * R(rot['torso']), o, o2)
    for k in TORSO_PTS:
        P[k] = o2 + X['torso'][0] @ (S[k] - o)
    X['head'] = (s * R(rot['head']), S['neck'], P['neck'])
    for k in ['head', 'chin']:
        P[k] = P['neck'] + X['head'][0] @ (S[k] - S['neck'])
    for ch, bones in CHAINS.items():
        for b in bones:
            a, c = BONES[b]
            A = s * R(rot[b])
            X[b] = (A, S[a], P[a])
            P[c] = P[a] + A @ (S[c] - S[a])
    return dict(s=s, rot=rot, want=want, over=over, X=X, P=P)


def pose_cost(S, T, Ct, view_w=1.0, emblem=None):
    F = fit(S, T)
    L = np.linalg.norm(T['neck'] - T['groin']) + 1e-6
    err = 0; wsum = 0
    for k in T:
        if k in F['P']:
            w = Ct.get(k, .5)
            err += w * np.linalg.norm(F['P'][k] - T[k]) / L; wsum += w
    err /= wsum
    rotc = sum(BONE_W[b] * (F['rot'][b] / CAP) ** 2 for b in BONES) / sum(BONE_W.values())
    overc = sum(BONE_W[b] * F['over'][b] for b in BONES if b not in ('footL', 'footR'))
    vf = np.abs(view_feat(S) - view_feat(T))
    viewc = vf[0] + .5 * vf[1] + vf[2]
    # foreshortening: the drawing can't change how foreshortened a limb was painted
    fs = 0
    for b in ['uarmL', 'uarmR', 'farmL', 'farmR', 'thighL', 'thighR', 'shinL', 'shinR', 'torso']:
        fs += abs(math.log((blen(T, b) + 2) / (F['s'] * blen(S, b) + 2)))
    fs /= 9
    # crossed legs in one and not the other: the overlap can't be separated cleanly
    cross = abs(legs_cross(S) - legs_cross(T))
    cost = err + .15 * rotc + .5 * viewc + .4 * fs + .002 * overc + .3 * cross
    if emblem is not None:
        cost += .15 * abs(emblem[0] - emblem[1])
    return cost, dict(err=err, rotc=rotc, over=overc, cross=cross, view=viewc, fs=fs, maxover=max(F['over'][b] for b in BONES if b not in ('footL', 'footR')))


def _seg_inter(p1, p2, q1, q2):
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)


def legs_cross(M):
    for a in ['thighL', 'shinL']:
        for b in ['thighR', 'shinR']:
            if _seg_inter(M[BONES[a][0]], M[BONES[a][1]], M[BONES[b][0]], M[BONES[b][1]]):
                return 1
    return 0


_emb = {}


def has_emblem(pid):
    """the glowing blue chest emblem some sheets painted on the jacket (costume variant)"""
    if pid not in _emb:
        im = cv2.imread(painting_path(pid), cv2.IMREAD_UNCHANGED)
        hsv = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2HSV)
        blue = (hsv[..., 0] > 95) & (hsv[..., 0] < 125) & (hsv[..., 1] > 120) & (hsv[..., 2] > 150) & (im[..., 3] > 128)
        _emb[pid] = int(blue.sum() > 30)
    return _emb[pid]


def candidates(exclude_family=None, allow=None):
    ids = CLEAN + list(KEYED)
    out = []
    for pid in ids:
        if exclude_family and family(pid) == exclude_family:
            continue
        if allow is not None and pid not in allow:
            continue
        out.append(pid)
    return out


def variants(t):
    """marker variants of a source painting: as painted / mirrored, and the free pairing of
    which painted arm (leg) plays which target arm (leg)."""
    M = markers(t)
    W = t['w']
    for mir in (False, True):
        B = mirror_markers(M, W) if mir else M
        for sa in (False, True):
            for sl in (False, True):
                X = B
                if sa: X = swap_side(X, 'arm')
                if sl: X = swap_side(X, 'leg')
                yield dict(mirror=mir, swap_arm=sa, swap_leg=sl), X


def rank_sources(tid, targets, exclude_family=True, allow=None, T=None, Ct=None, costume=True):
    t = targets[tid]
    if T is None:
        T = markers(t); Ct = conf(t)
    res = []
    for pid in candidates(family(tid) if exclude_family else None, allow):
        best = None
        for v, S in variants(targets[pid]):
            c, info = pose_cost(S, T, Ct, emblem=(has_emblem(pid), has_emblem(tid)) if costume else None)
            # the swapped pairings are only for markers mislabelled L/R; small penalty
            c += .05 * (v['swap_arm'] + v['swap_leg']) + .02 * v['mirror']
            if best is None or c < best[0]:
                best = (c, pid, v, info)
        res.append(best)
    res.sort(key=lambda r: r[0])
    return res
