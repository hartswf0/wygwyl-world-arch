"""The blind puzzle: cover a silhouette with the fewest library shapes, no overflow.

fill(char, costume, tid, mode='blind'|'prior', zones=None, on_step=callback) -> result dict

Only the target's SILHOUETTE drives the choice (the painting's alpha minus REF_IGNORE props). The skeleton is read
only after the fill, to learn zones, and in 'prior' mode to order which pieces are tried first in a region.

Coarse search (work resolution, target WORK_H px tall):
  score map = +1 uncovered figure cell, -OVL figure cell already covered, 0 edge cell (figure share .15-.6),
              -BIG outside cell (figure share < .15).
  every piece variant (uniform scale k in K_STEPS, mirror, angle every ANG_STEP deg) is correlated with the score map
  (cv2.matchTemplate, TM_CCORR); the best location's value is the piece's gain; any outside cell makes it hugely
  negative, so a placed piece never leaves the figure. A piece costs LAMBDA (fewest pieces).
  greedy: place the best (gain - LAMBDA) until nothing pays; then local search: prune pieces whose unique
  contribution no longer pays, re-place each piece, and try merging two neighbours into one bigger piece.
Refine (full resolution): each piece's position (+-3 px), angle (+-3/6 deg) and scale (+-4%) hill-climbed for
  coverage with overflow (beyond a 2 px anti-alias band) charged 50x; a piece still overflowing after that is
  shrunk, and removed if shrinking cannot clear it.
"""
import math, os, random, time
import numpy as np, cv2

from . import pieces as PC
from evolve import assemble as AS

WORK_H = 128
K_STEPS = (0.85, 1.0, 1.18)
ANG_STEP = 20
OVL = 0.12
BIG = 1e4
LAMBDA_SHARE = 0.005       # piece cost as a share of the figure area
MAX_PIECES = 60
PRIOR_B = .35             # prior mode: bonus per uncovered cell of the zone a piece has learned
TOL_PX = 2                 # anti-alias band outside the figure that does not count as overflow


# ------------------------------------------------------------------ target
def target(char, costume, tid):
    t = AS.target(char, costume, tid)
    fig = t['fig'] & ~t['ignore']
    H, W = fig.shape
    r = WORK_H / H
    Wk = max(8, int(round(W * r)))
    share = cv2.resize(fig.astype(np.float32), (Wk, WORK_H), interpolation=cv2.INTER_AREA)
    ignw = cv2.resize(t['ignore'].astype(np.float32), (Wk, WORK_H), interpolation=cv2.INTER_AREA) > .3
    inside = share >= .6
    outside = (share < .15) & ~ignw
    t.update(fig_t=fig, r=r, inside_w=inside, outside_w=outside, work_size=(Wk, WORK_H),
             fig_dil=cv2.dilate(fig.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * TOL_PX + 1,) * 2)) > 0)
    return t


# ------------------------------------------------------------------ variants
def rot_mat(ang, mir, g, c_src, c_dst):
    """card px -> canvas px: scale g about the card centre, mirror (x), rotate ang deg, centre to c_dst"""
    a = math.radians(ang)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    S = np.diag([-g if mir else g, g])
    M = R @ S
    return np.hstack([M, (np.asarray(c_dst) - M @ np.asarray(c_src))[:, None]])


def build_variants(pieces, t):
    """every (piece, k, mirror, angle) as a binary work-res mask with its centre offset"""
    V = []
    fig_area = t['inside_w'].sum()
    min_a = max(6, LAMBDA_SHARE * fig_area * .8)
    for pi, p in enumerate(pieces):
        a = p['px'][..., 3] / 255.
        h, w = a.shape
        for k in K_STEPS:
            g = t['s'] / p['ppc'] * k * t['r']
            if g * max(h, w) < 3:
                continue
            small = cv2.resize(a, (max(1, int(round(w * g))), max(1, int(round(h * g)))), interpolation=cv2.INTER_AREA)
            if (small > .5).sum() < min_a or (small > .5).sum() > fig_area:
                continue
            sh, sw = small.shape
            D = int(math.ceil(math.hypot(sh, sw))) + 2
            for mir in (0, 1):
                for ang in range(0, 360, ANG_STEP):
                    M = rot_mat(ang, mir, 1.0, (sw / 2, sh / 2), (D / 2, D / 2))
                    m = cv2.warpAffine(small, M, (D, D), flags=cv2.INTER_LINEAR) > .5
                    ys, xs = np.nonzero(m)
                    if len(xs) < min_a:
                        continue
                    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
                    V.append({'pi': pi, 'k': k, 'mir': mir, 'ang': ang, 'm': m[y0:y1, x0:x1].astype(np.float32),
                              'c': (D / 2 - x0, D / 2 - y0), 'area': int(len(xs))})
    return V


# ------------------------------------------------------------------ coarse search
def score_map(t, cov):
    S = np.zeros(t['inside_w'].shape, np.float32)
    S[t['inside_w']] = 1.
    S[t['inside_w'] & (cov > 0)] = -OVL
    S[t['outside_w']] = -BIG
    return S


def best_of(V, idx, S, lam, SZ=None, vz=None):
    """best (net gain, variant index, top-left) over the variants idx. Prior mode: SZ {zone: score map with a bonus
    on that zone's uncovered cells} and vz {variant index: learned zone}; the bonus only reorders, the returned net is
    the blind gain"""
    Hs, Ws = S.shape
    best = (-1e9, None, None)
    for i in idx:
        v = V[i]
        m = v['m']
        if SZ is not None and vz.get(i) in SZ:
            if v['area'] * (1 + PRIOR_B) - lam <= best[0]:
                continue
            R = cv2.matchTemplate(SZ[vz[i]], m, cv2.TM_CCORR)
            _, mx, _, loc = cv2.minMaxLoc(R)
            if mx - lam > best[0]:
                best = (mx - lam, i, loc)
            continue
        if m.shape[0] > Hs or m.shape[1] > Ws:
            continue
        if v['area'] - lam <= best[0]:          # cannot beat the best even if every cell gains
            continue
        R = cv2.matchTemplate(S, m, cv2.TM_CCORR)
        _, mx, _, loc = cv2.minMaxLoc(R)
        if mx - lam > best[0]:
            best = (mx - lam, i, loc)
    return best


def place_mask(v, loc, shape):
    M = np.zeros(shape, np.float32)
    y, x = loc[1], loc[0]
    h, w = v['m'].shape
    M[y:y + h, x:x + w] = v['m']
    return M


def coverage(P, shape):
    cov = np.zeros(shape, np.float32)
    for p in P:
        cov += p['mask']
    return cov


def objective(P, t, lam):
    cov = coverage(P, t['inside_w'].shape)
    ins = t['inside_w']
    covered = ((cov > 0) & ins).sum()
    over = (np.clip(cov - 1, 0, None) * ins).sum()
    return covered - lam * len(P) - OVL * over


# ------------------------------------------------------------------ zones (used after the fill, and by the prior)
ZONES = ['head', 'torso', 'hips', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot']


def zone_map(t, shape=None):
    """each figure pixel -> nearest skeleton segment's zone (index into ZONES), -1 outside; from the Pose Lab markers"""
    m = t['markers']
    mid = (m['hipL'] + m['hipR']) / 2
    sp = m['neck'] - mid
    segs = [(0, m['neck'], m['neck'] + 1.3 * (m['head'] - m['neck'])), (1, m['neck'], mid + .3 * sp),
            (2, m['hipL'], m['hipR']), (2, mid + .3 * sp, mid - .12 * sp)]
    for S in 'LR':
        e, w_ = m['elbow' + S], m['wrist' + S]
        segs += [(3, m['shoulder' + S], e), (4, e, w_), (5, w_, w_ + .45 * (w_ - e)), (6, m['hip' + S], m['knee' + S]),
                 (7, m['knee' + S], m['ankle' + S]), (8, m['ankle' + S], m['toe' + S])]
    fig = t['fig_t']
    H, W = fig.shape
    ys, xs = np.nonzero(fig)
    Pt = np.stack([xs, ys], 1).astype(np.float64)
    D = np.stack([AS_seg(Pt, a, b) for _, a, b in segs], 1)
    lab = np.array([z for z, _, _ in segs])[np.argmin(D, 1)]
    Z = np.full((H, W), -1, np.int8)
    Z[ys, xs] = lab
    if shape is not None:
        Z = cv2.resize(Z, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
    return Z


def AS_seg(P, a, b):
    ab = b - a
    tt = np.clip(((P - a) @ ab) / (ab @ ab + 1e-9), 0, 1)
    return np.linalg.norm(P - (a + tt[:, None] * ab), axis=1)


def learned_zone(zones, pid):
    z = (zones or {}).get(pid)
    if not z:
        return None
    k, n = max(z.items(), key=lambda kv: kv[1])
    return k if n >= 2 else None


# ------------------------------------------------------------------ full resolution
def full_M(p, piece, t):
    a = piece['px']
    h, w = a.shape[:2]
    g = t['s'] / piece['ppc'] * p['k']
    return rot_mat(p['ang'], p['mir'], g, (w / 2, h / 2), p['cx'])


def full_mask(p, piece, t):
    W, H = t['size']
    return cv2.warpAffine(piece['px'][..., 3], full_M(p, piece, t), (W, H), flags=cv2.INTER_LINEAR) > 128


def refine(P, pieces, t, deadline):
    fig, fd = t['fig_t'], t['fig_dil']
    ign = t['ignore']
    W, H = t['size']
    masks = [full_mask(p, pieces[p['pi']], t) for p in P]

    def val(i, m):
        others = np.zeros((H, W), bool)
        for j, mm in enumerate(masks):
            if j != i:
                others |= mm
        gain = (m & fig & ~others).sum()
        over = (m & ~fd & ~ign).sum()
        return gain - 50 * over, over
    for it in range(3):
        moved = False
        for i, p in enumerate(P):
            if time.time() > deadline:
                break
            cur, _ = val(i, masks[i])
            for dx, dy, da, dk in [(3, 0, 0, 0), (-3, 0, 0, 0), (0, 3, 0, 0), (0, -3, 0, 0), (1, 0, 0, 0), (-1, 0, 0, 0),
                                   (0, 1, 0, 0), (0, -1, 0, 0), (0, 0, 6, 0), (0, 0, -6, 0), (0, 0, 3, 0), (0, 0, -3, 0),
                                   (0, 0, 0, .04), (0, 0, 0, -.04)]:
                q = dict(p, cx=(p['cx'][0] + dx, p['cx'][1] + dy), ang=p['ang'] + da, k=float(np.clip(p['k'] + dk, .8, 1.25)))
                m = full_mask(q, pieces[q['pi']], t)
                v, _ = val(i, m)
                if v > cur:
                    P[i], masks[i], cur, moved = q, m, v, True
                    p = q
        if not moved:
            break
    # overflow is hard: shrink, then drop
    keep = []
    for i, p in enumerate(P):
        _, over = val(i, masks[i])
        q = p
        while over > 0 and q['k'] > .8:
            q = dict(q, k=q['k'] * .96)
            m = full_mask(q, pieces[q['pi']], t)
            _, over = val(i, m)
            masks[i] = m
        if over == 0:
            P[i] = q
            keep.append(i)
        else:
            masks[i] = np.zeros((H, W), bool)
    return [P[i] for i in keep], [masks[i] for i in keep]


def stats(masks, t):
    fig, fd, ign = t['fig_t'], t['fig_dil'], t['ignore']
    U = np.zeros(fig.shape, bool)
    for m in masks:
        U |= m
    area = max(fig.sum(), 1)
    return {'coverage': float((U & fig).sum() / area), 'overflow': float((U & ~fd & ~ign).sum() / area),
            'overflow_px': int((U & ~fd & ~ign).sum()), 'overflow_in_band': float((U & ~fig & fd & ~ign).sum() / area),
            'union': U}


# ------------------------------------------------------------------ the fill
def fill(char, costume, tid, mode='blind', zones=None, on_step=None, budget_s=420, seed=0, ctx=None):
    rng = random.Random(seed)
    t0 = time.time()
    if ctx is not None:
        t, pieces, V, gone = ctx['t'], ctx['pieces'], ctx['V_fill'], []
    else:
        t = target(char, costume, tid)
        pieces, gone = PC.pieces_for(char, costume, tid)
        V = build_variants(pieces, t)
    shape = t['inside_w'].shape
    lam = LAMBDA_SHARE * t['inside_w'].sum()
    Zw = zone_map(t, shape) if mode == 'prior' else None
    by_piece = {}
    for i, v in enumerate(V):
        by_piece.setdefault(v['pi'], []).append(i)
    lz = {pi: learned_zone(zones, pieces[pi]['id']) for pi in by_piece} if mode == 'prior' else {}
    lz = {k: v for k, v in lz.items() if v}

    vz = {i: lz.get(v['pi']) for i, v in enumerate(V) if lz.get(v['pi'])} if mode == 'prior' else {}

    def search(cov, idx=None):
        """the best placement over every variant (a full pass is ~1 s); prior mode adds the zone bonus"""
        S = score_map(t, cov)
        SZ = None
        if mode == 'prior':
            unc = t['inside_w'] & (cov <= 0)
            SZ = {z: (S + PRIOR_B * (unc & (Zw == ZONES.index(z)))).astype(np.float32) for z in ZONES}
        net, vi, loc = best_of(V, range(len(V)) if idx is None else idx, S, lam, SZ, vz)
        if vi is not None and SZ is not None:       # report the blind gain
            m = V[vi]['m']
            net = float((S[loc[1]:loc[1] + m.shape[0], loc[0]:loc[0] + m.shape[1]] * m).sum()) - lam
        return net, vi, loc

    P = []
    step = 0

    def emit(tag):
        nonlocal step
        step += 1
        if on_step:
            on_step(step, tag, P, pieces, t, None)

    # greedy
    cov = np.zeros(shape, np.float32)
    while len(P) < MAX_PIECES and time.time() - t0 < budget_s * .55:
        net, vi, loc = search(cov)
        if vi is None or net <= 0:
            break
        v = V[vi]
        m = place_mask(v, loc, shape)
        P.append({'vi': vi, 'pi': v['pi'], 'k': v['k'], 'mir': v['mir'], 'ang': v['ang'], 'loc': loc, 'mask': m,
                  'cx': ((loc[0] + v['c'][0]) / t['r'], (loc[1] + v['c'][1]) / t['r'])})
        cov += m
        emit('greedy +%s' % pieces[v['pi']]['id'].split('/')[-1])
    # local search
    J = objective(P, t, lam)
    changed = True
    rounds = 0
    while changed and time.time() - t0 < budget_s * .85 and rounds < 3:
        changed = False
        rounds += 1
        # prune
        for i in sorted(range(len(P)), key=lambda i: P[i]['mask'].sum()):
            if i >= len(P):
                continue
            Q = P[:i] + P[i + 1:]
            Jq = objective(Q, t, lam)
            if Jq > J + 1e-6:
                P, J, changed = Q, Jq, True
                emit('prune')
                break
        # re-place each piece
        for i in range(len(P)):
            if time.time() - t0 > budget_s * .75:
                break
            Q = P[:i] + P[i + 1:]
            covq = coverage(Q, shape)
            net, vi, loc = search(covq)
            if vi is None:
                continue
            v = V[vi]
            cand = {'vi': vi, 'pi': v['pi'], 'k': v['k'], 'mir': v['mir'], 'ang': v['ang'], 'loc': loc,
                    'mask': place_mask(v, loc, shape), 'cx': ((loc[0] + v['c'][0]) / t['r'], (loc[1] + v['c'][1]) / t['r'])}
            Jq = objective(Q + [cand], t, lam)
            if Jq > J + 1:
                P, J, changed = Q + [cand], Jq, True
                emit('replace -> %s' % pieces[v['pi']]['id'].split('/')[-1])
        # merge two neighbours into one
        tries = 0
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                if tries >= 10 or time.time() - t0 > budget_s * .85:
                    break
                a = cv2.dilate(P[i]['mask'], np.ones((3, 3), np.uint8)) > 0
                if not (a & (P[j]['mask'] > 0)).any():
                    continue
                tries += 1
                Q = [p for k_, p in enumerate(P) if k_ not in (i, j)]
                covq = coverage(Q, shape)
                net, vi, loc = search(covq)
                if vi is None:
                    continue
                v = V[vi]
                cand = {'vi': vi, 'pi': v['pi'], 'k': v['k'], 'mir': v['mir'], 'ang': v['ang'], 'loc': loc,
                        'mask': place_mask(v, loc, shape), 'cx': ((loc[0] + v['c'][0]) / t['r'], (loc[1] + v['c'][1]) / t['r'])}
                Jq = objective(Q + [cand], t, lam)
                if Jq > J + 1:
                    P, J, changed = Q + [cand], Jq, True
                    emit('merge 2 -> %s' % pieces[v['pi']]['id'].split('/')[-1])
                    break
    # back to front: bigger pieces behind
    P.sort(key=lambda p: -p['mask'].sum())
    P, masks = refine(P, pieces, t, t0 + budget_s)
    st = stats(masks, t)
    if on_step:
        on_step(step + 1, 'refined at full resolution', P, pieces, t, masks)
    # zones: where each piece landed (read from the skeleton only now)
    Z = zone_map(t)
    landed = []
    for p, m in zip(P, masks):
        zz = Z[m & (Z >= 0)]
        zone = ZONES[int(np.bincount(zz, minlength=len(ZONES)).argmax())] if len(zz) else None
        pc = pieces[p['pi']]
        landed.append({'id': pc['id'], 'label': pc['label'], 'kind': pc['kind'], 'zone': zone, 'k': round(p['k'], 3),
                       'mir': p['mir'], 'ang': p['ang'], 'cx': [round(p['cx'][0], 1), round(p['cx'][1], 1)],
                       'area_share': round(float((m & t['fig_t']).sum() / max(t['fig_t'].sum(), 1)), 4)})
    return {'target': tid, 'char': char, 'costume': costume, 'mode': mode, 'pieces_available': len(pieces),
            'variants': len(V), 'excluded': len(gone), 'coverage': round(st['coverage'], 4), 'overflow': round(st['overflow'], 5),
            'overflow_px': st['overflow_px'], 'overflow_in_band': round(st['overflow_in_band'], 4), 'n_pieces': len(P),
            'seconds': round(time.time() - t0, 1), 'placed': landed, '_P': P, '_masks': masks, '_pieces': pieces, '_t': t}
