"""Growth assembly: a body grown piece by piece from a seed, every piece joined to the body at a brad.

The rules:
  * Connectivity is structural. Every piece after the seed is attached by snapping one of its own brads onto a FREE
    brad of the body (a brad not yet joined). The assembly is therefore always one connected component; the snapped
    pairs are its skeleton (it is not given, it emerges). A piece may also close a second snap when another of its
    brads lands on another free brad (within SNAP_CM).
  * Brads come from the cards: library.json brads (1-8 listed), else gold rivets detected on the card
    (pieces.piece_brads). Pieces with no brad cannot join and are not used.
  * Reference studs: the painted brads detected on the target painting (assemble.ref_brads) attract: a piece brad
    landing within SNAP_CM of an unused stud earns STUD_B. No pixel of the target is used.
  * Overflow is hard at the work resolution (any cell outside the figure is -1e4). Overlap is charged -OVL per cell,
    except within PIVOT_CM of a free brad: pieces overlapping round a joint is how a joint is built.

Decoding a growth program (genome = list of ranks): at each step, every (free brad, piece variant, piece brad)
attachment is scored (one cv2.matchTemplate per variant against the score map, read at the attachment positions;
an area bound skips most variants); the TOPK best by gain + snap and stud bonuses are ranked, and the genome's rank
at that step picks one (rank 0 = greedy). Growth stops when the best attachment no longer pays the piece cost.
So the program encodes, at each step, which free brad, which piece, which of its brads and which angle / scale.

Fitness (shares of the figure area): coverage - 50 overflow - 10 disconnected - PIECE_C * pieces + SNAP_C * snaps
+ STUD_C * studs hit.

Evolution: islands with distinct seed pieces (the largest pieces that fit the core); mutation = change the rank at
one step and regrow everything after it; crossover = one-point (A's program up to a step, then B's); stall 15
generations -> shake (several ranks changed at once, the weakest island reseeded from the best). Decoded prefixes
are cached, so regrowing after step k costs only the steps after k.

Settle (full resolution, on the best): each piece rotated about its own joint to its parent (+-3, +-6 deg) and
scaled about it (+-4%), carrying its whole subtree; kept if coverage rises with no overflow beyond the 2 px band.
A piece still overflowing is shrunk about its joint; if that fails its subtree is cut (the rest stays connected).
"""
import heapq, json, math, os, random, time
import numpy as np, cv2

from . import fill as FL, pieces as PC

SNAP_CM, PIVOT_CM = 3.0, 4.0
TOPK = 12
PIECE_C, SNAP_C, STUD_C = .006, .004, .003
SNAP_B, STUD_B = .004, .003          # bonus (share of figure) used while ranking attachments
OVL = .12
MAXSTEPS = 45
CUT_SHARE = .001          # settle: a piece overflowing more than this share of the figure loses its subtree
ANG = 30                 # degrees between growth variants (the settle refines by 3 and 6)
KS = (.9, 1.1)           # uniform scales of the growth variants (x target px/cm / card px/cm)
SUBSET = .35             # share of the pieces tried at one growth step (seeded by the program prefix: deterministic)


# ------------------------------------------------------------------ variants with brads
def build(pieces, t):
    V = []
    fig_area = t['inside_w'].sum()
    min_a = max(4, .0015 * fig_area)
    for pi, p in enumerate(pieces):
        if not len(p['brads']):
            continue
        a = p['px'][..., 3] / 255.
        h, w = a.shape
        for k in KS:
            g = t['s'] / p['ppc'] * k * t['r']
            if g * max(h, w) < 3:
                continue
            sw_, sh_ = max(1, int(round(w * g))), max(1, int(round(h * g)))
            small = cv2.resize(a, (sw_, sh_), interpolation=cv2.INTER_AREA)
            if (small > .5).sum() < min_a or (small > .5).sum() > fig_area:
                continue
            bs = p['brads'] * [sw_ / w, sh_ / h]
            D = int(math.ceil(math.hypot(sh_, sw_))) + 2
            for mir in (0, 1):
                for ang in range(0, 360, ANG):
                    M = FL.rot_mat(ang, mir, 1.0, (sw_ / 2, sh_ / 2), (D / 2, D / 2))
                    m = cv2.warpAffine(small, M, (D, D), flags=cv2.INTER_LINEAR) > .5
                    ys, xs = np.nonzero(m)
                    if len(xs) < min_a:
                        continue
                    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
                    b = bs @ M[:, :2].T + M[:, 2] - [x0, y0]
                    mm = m[y0:y1, x0:x1]
                    rad = int(math.ceil(max(np.hypot(*(np.array([[0, 0], [mm.shape[1], 0], [0, mm.shape[0]], [mm.shape[1], mm.shape[0]]])[:, None, :]
                                                       - b[None]).T).max(), 1)))
                    V.append({'pi': pi, 'k': k, 'mir': mir, 'ang': ang, 'm': np.ascontiguousarray(mm, np.float32),
                              'c': (D / 2 - x0, D / 2 - y0), 'area': int(len(xs)), 'b': b, 'rad': rad})
    V.sort(key=lambda v: -v['area'])
    return V


# ------------------------------------------------------------------ state
class State:
    __slots__ = ('placed', 'cov', 'free', 'snaps', 'studs_used', 'done', 'joins', 'ends')

    def __init__(self, shape):
        self.placed, self.cov, self.free, self.snaps, self.studs_used, self.done = [], np.zeros(shape, np.float32), [], [], set(), False
        self.joins, self.ends = {}, False

    def copy(self):
        s = State.__new__(State)
        s.placed = list(self.placed); s.cov = self.cov.copy(); s.free = list(self.free); s.snaps = list(self.snaps)
        s.studs_used = set(self.studs_used); s.done = self.done; s.joins = dict(self.joins); s.ends = self.ends
        return s


class Grower:
    def __init__(self, char, costume, tid, seed=0, prior=None, ctx=None, opts=None):
        self.opts = dict({'max_joins': 1, 'ends': None}, **(opts or {}))
        if ctx is not None:
            self.t = t = ctx['t']
            self.pieces = ctx['pieces']
            if 'V_grow' not in ctx:
                ctx['V_grow'] = build(self.pieces, t)
            self.V = ctx['V_grow']
        else:
            self.t = t = FL.target(char, costume, tid)
            self.pieces, _ = PC.pieces_for(char, costume, tid)
            self.V = build(self.pieces, t)
        self.shape = t['inside_w'].shape
        self.area = float(t['inside_w'].sum())
        self.lam = FL.LAMBDA_SHARE * self.area
        u = t['s'] * t['r']                       # work px per cm
        self.snap_r, self.pivot_r = SNAP_CM * u, PIVOT_CM * u
        self.studs = t['ref_brads'] * t['r'] if len(t['ref_brads']) else np.zeros((0, 2))
        self.rng = random.Random(seed)
        self.cache = {}
        self.prior = prior or {}                  # {(parent piece id, child piece id): count} (learned grammar)
        ids = {p['id']: i for i, p in enumerate(self.pieces)}
        self.prior_piece = {ids[c]: 1 for (_, c) in self.prior if c in ids}   # always tried in prior mode
        yy, xx = np.mgrid[0:self.shape[0], 0:self.shape[1]]
        self.yy, self.xx = yy, xx

    # score map: +1 uncovered figure, -OVL covered (0 near a free brad), -BIG outside
    def score(self, st):
        S = np.zeros(self.shape, np.float32)
        ins = self.t['inside_w']
        S[ins] = 1.
        cov = (st.cov > 0) & ins
        S[cov] = -OVL
        if st.free:
            near = np.zeros(self.shape, bool)
            for f in st.free:
                p = st.placed[f[0]]['bw'][f[1]]
                near |= (self.xx - p[0]) ** 2 + (self.yy - p[1]) ** 2 <= self.pivot_r ** 2
            S[cov & near] = 0.
        S[self.t['outside_w']] = -FL.BIG
        return S

    def seeds(self, n):
        """the largest pieces (>= 2 brads) that fit inside the figure, distinct pieces"""
        S = self.score(State(self.shape))
        out, seen = [], set()
        for vi, v in enumerate(self.V):
            if len(v['b']) < 2 or v['pi'] in seen:
                continue
            m = v['m']
            if m.shape[0] > S.shape[0] or m.shape[1] > S.shape[1]:
                continue
            R = cv2.matchTemplate(S, m, cv2.TM_CCORR)
            _, mx, _, loc = cv2.minMaxLoc(R)
            if mx > .97 * v['area']:              # fits (no outside cell, nearly all on figure)
                out.append((mx, vi, loc)); seen.add(v['pi'])
            if len(out) >= 4 * n:
                break
        out.sort(key=lambda x: -x[0])
        return out[:n]

    def place(self, st, vi, loc, parent=None, pb=None, cb=None):
        v = self.V[vi]
        h, w = v['m'].shape
        st.cov[loc[1]:loc[1] + h, loc[0]:loc[0] + w] += v['m']
        idx = len(st.placed)
        bw = v['b'] + [loc[0], loc[1]]
        st.placed.append({'vi': vi, 'loc': loc, 'bw': bw, 'parent': parent, 'pb': pb, 'cb': cb})
        used = {cb} if cb is not None else set()
        if parent is not None:
            st.joins[(parent, pb)] = st.joins.get((parent, pb), 1) + 1
            if st.joins[(parent, pb)] > self.opts['max_joins']:      # a brad takes max_joins children (1 = a plain pair)
                st.free = [f for f in st.free if f != (parent, pb)]
            st.snaps.append((parent, pb, idx, cb))
        # extra snaps: another of my brads on another free brad
        for j, p in enumerate(bw):
            if j in used:
                continue
            for f in list(st.free):
                q = st.placed[f[0]]['bw'][f[1]]
                if f[0] != idx and np.hypot(*(p - q)) <= self.snap_r:
                    st.free.remove(f); st.snaps.append((f[0], f[1], idx, j)); used.add(j)
                    break
        for j, p in enumerate(bw):
            if len(self.studs):
                d = np.hypot(*(self.studs - p).T)
                i = int(np.argmin(d))
                if d[i] <= self.snap_r and i not in st.studs_used:
                    st.studs_used.add(i)
            if j not in used:
                st.free.append((idx, j))
        return st

    def candidates(self, st, key=()):
        """top attachments: (rank value, vi, loc, free brad, my brad)"""
        if not st.free:
            return []
        rs = random.Random(hash(key) & 0xffffffff)
        tried = {pi for pi in range(len(self.pieces)) if rs.random() < SUBSET}
        S = self.score(st)
        Hs, Ws = S.shape
        F = np.array([st.placed[f[0]]['bw'][f[1]] for f in st.free])
        # live free brads: some uncovered figure within 3 pivot radii (a brad buried inside the body grows nothing)
        I0 = cv2.integral((S > 0).astype(np.uint8))
        rr = int(3 * self.pivot_r) + 1
        Fi0 = np.rint(F).astype(int)
        x0 = np.clip(Fi0[:, 0] - rr, 0, Ws); x1 = np.clip(Fi0[:, 0] + rr + 1, 0, Ws)
        y0 = np.clip(Fi0[:, 1] - rr, 0, Hs); y1 = np.clip(Fi0[:, 1] + rr + 1, 0, Hs)
        live = (I0[y1, x1] - I0[y0, x1] - I0[y1, x0] + I0[y0, x0]) > 0
        if not live.any():
            return []
        fmap = np.nonzero(live)[0]
        Fall = F
        F = F[live]
        Spad = np.pad(S, ((0, 64), (0, 64)), constant_values=-FL.BIG)
        heap = []
        thr = -1e9
        bonus_max = 0.        # prune and keep on raw gain (top TOPK * 3); bonuses re-rank those afterwards
        # bound: a variant attached at a free brad can gain at most the uncovered cells within its reach of that brad
        I = cv2.integral((S > 0).astype(np.uint8))
        Fi = np.rint(F).astype(int)

        def reach(rad):
            x0 = np.clip(Fi[:, 0] - rad, 0, Ws); x1 = np.clip(Fi[:, 0] + rad + 1, 0, Ws)
            y0 = np.clip(Fi[:, 1] - rad, 0, Hs); y1 = np.clip(Fi[:, 1] + rad + 1, 0, Hs)
            return int((I[y1, x1] - I[y0, x1] - I[y1, x0] + I[y0, x0]).max())
        rcache = {}
        for vi, v in enumerate(self.V):
            if v['area'] + bonus_max - self.lam <= thr:
                break                          # variants are sorted by area: nothing later can beat the threshold
            if v['pi'] not in tried and not self.prior_piece.get(v['pi']):
                continue
            rad = v['rad']
            if rad not in rcache:
                rcache[rad] = reach(rad)
            if min(v['area'], rcache[rad]) + bonus_max - self.lam <= thr:
                continue
            m = v['m']
            if m.shape[0] > Hs or m.shape[1] > Ws:
                continue
            L = np.rint(F[:, None, :] - v['b'][None, :, :]).astype(int)       # (free, my brad, xy) top-left
            ok = (L[..., 0] >= 0) & (L[..., 1] >= 0) & (L[..., 0] <= Ws - m.shape[1]) & (L[..., 1] <= Hs - m.shape[0])
            if not ok.any():
                continue
            h_, w_ = m.shape
            if h_ > 64 or w_ > 64:
                R = cv2.matchTemplate(S, m, cv2.TM_CCORR)
                vals = np.where(ok, R[np.minimum(np.maximum(L[..., 1], 0), R.shape[0] - 1), np.minimum(np.maximum(L[..., 0], 0), R.shape[1] - 1)], -1e9)
            else:
                ly, lx = np.nonzero(ok)
                yy = L[ly, lx, 1][:, None, None] + np.arange(h_)[None, :, None]
                xx = L[ly, lx, 0][:, None, None] + np.arange(w_)[None, None, :]
                win = Spad[yy, xx]
                vals = np.full(ok.shape, -1e9)
                vals[ly, lx] = (win * m).sum((1, 2))
            fi, j = np.unravel_index(int(np.argmax(vals)), vals.shape)
            g = vals[fi, j]
            loc = (int(L[fi, j, 0]), int(L[fi, j, 1]))
            fi = int(fmap[fi])
            if g < 0:
                continue
            val = g - self.lam
            pid = self.pieces[v['pi']]['id']
            par = self.pieces[self.V[st.placed[st.free[fi][0]]['vi']]['pi']]['id']
            val += SNAP_B * self.area + self.prior.get((par, pid), 0) * .5 * SNAP_B * self.area
            # extra snap / stud bonus
            bw = v['b'] + loc
            for jj, p in enumerate(bw):
                if jj == j:
                    continue
                if len(Fall) > 1 and (np.hypot(*(Fall - p).T) <= self.snap_r).sum() > (1 if np.hypot(*(Fall[fi] - p)) <= self.snap_r else 0):
                    val += SNAP_B * self.area
                if len(self.studs) and np.min(np.hypot(*(self.studs - p).T)) <= self.snap_r:
                    val += STUD_B * self.area
            if len(heap) < 3 * TOPK:
                heapq.heappush(heap, (g - self.lam, val, vi, loc, fi, int(j), g))
            elif g - self.lam > heap[0][0]:
                heapq.heapreplace(heap, (g - self.lam, val, vi, loc, fi, int(j), g))
            if len(heap) == 3 * TOPK:
                thr = heap[0][0]
        return [h[1:] for h in sorted(heap, key=lambda x: -x[1])[:TOPK]]

    def step(self, st, rank, key=()):
        lam0 = self.lam
        if st.ends:
            self.lam = lam0 * self.opts['ends']                # ends phase: small pieces pay for themselves
        try:
            C = self.candidates(st, key)
            C = [c for c in C if c[5] - self.lam > 0]          # the piece must pay for itself in coverage
        finally:
            self.lam = lam0
        if not C:
            st.done = True
            return st, None
        val, vi, loc, fi, j, g = C[min(rank, len(C) - 1)]
        f = st.free[fi]
        return self.place(st, vi, loc, f[0], f[1], j), C[min(rank, len(C) - 1)]

    def decode(self, seed, prog):
        """seed = (vi, loc); prog = list of ranks. Returns the final state and the program actually used"""
        key = (seed[0], tuple(seed[1]))
        st = None
        k = len(prog)
        while k >= 0:
            if key + tuple(prog[:k]) in self.cache:
                st = self.cache[key + tuple(prog[:k])].copy()
                break
            k -= 1
        if st is None:
            st = self.place(State(self.shape), seed[0], tuple(seed[1]))
            k = 0
            self.cache[key] = st.copy()
        used = list(prog[:k])
        i = k
        while len(st.placed) < MAXSTEPS:
            if st.done:
                if self.opts['ends'] and not st.ends:
                    st.done, st.ends = False, True
                else:
                    break
            r = prog[i] if i < len(prog) else 0
            st, ch = self.step(st, r, key + tuple(used))
            if ch is None:
                continue
            used.append(r)
            i += 1
            if len(self.cache) < 6000:
                self.cache[key + tuple(used)] = st.copy()
        return st, used

    def fitness(self, st):
        ins = self.t['inside_w']
        covd = ((st.cov > 0) & ins).sum() / self.area
        n = len(st.placed)
        return float(covd - PIECE_C * n + SNAP_C * len(st.snaps) + STUD_C * len(st.studs_used)), float(covd)


# ------------------------------------------------------------------ full resolution
def full_affines(G, st):
    t = G.t
    out = []
    for p in st.placed:
        v = G.V[p['vi']]
        pc = G.pieces[v['pi']]
        h, w = pc['px'].shape[:2]
        g = t['s'] / pc['ppc'] * v['k']
        c = ((p['loc'][0] + v['c'][0]) / t['r'], (p['loc'][1] + v['c'][1]) / t['r'])
        out.append(FL.rot_mat(v['ang'], v['mir'], g, (w / 2, h / 2), c))
    return out


def brads_full(G, st, Ms):
    return [G.pieces[G.V[p['vi']]['pi']]['brads'] @ M[:, :2].T + M[:, 2] for p, M in zip(st.placed, Ms)]


def children(st):
    ch = {i: [] for i in range(len(st.placed))}
    for i, p in enumerate(st.placed):
        if p['parent'] is not None:
            ch[p['parent']].append(i)
    return ch


def subtree(ch, i):
    out, todo = [], [i]
    while todo:
        k = todo.pop()
        out.append(k); todo += ch[k]
    return out


def settle(G, st, deadline, on_tick=None):
    """rotate / scale each piece about its joint to its parent, carrying its subtree; coverage up, no overflow"""
    t = G.t
    W, H = t['size']
    fig, fd, ign = t['fig_t'], t['fig_dil'], t['ignore']
    Ms = full_affines(G, st)
    px = [G.pieces[G.V[p['vi']]['pi']]['px'] for p in st.placed]
    ch = children(st)

    def masks_of(Ms_):
        return [cv2.warpAffine(px[i][..., 3], Ms_[i], (W, H), flags=cv2.INTER_LINEAR) > 128 for i in range(len(Ms_))]

    def evalm(ms):
        U = np.zeros((H, W), bool)
        for m in ms:
            U |= m
        return (U & fig).sum(), (U & ~fd & ~ign).sum()
    masks = masks_of(Ms)
    cov, over = evalm(masks)
    tick = 0
    for rnd in range(3):
        improved = False
        for i in range(0, len(st.placed)):
            if time.time() > deadline:
                break
            p = st.placed[i]
            if p['parent'] is None:          # the seed turns about its own centre
                piv = Ms[0][:, :2] @ (np.array(G.pieces[G.V[p['vi']]['pi']]['px'].shape[1::-1]) / 2.) + Ms[0][:, 2]
            else:
                piv = (G.pieces[G.V[st.placed[p['parent']]['vi']]['pi']]['brads'][p['pb']] @ Ms[p['parent']][:, :2].T + Ms[p['parent']][:, 2])
            sub = subtree(ch, i)
            for da, ds in ((3, 1), (-3, 1), (6, 1), (-6, 1), (0, 1.04), (0, .96)):
                a = math.radians(da)
                R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]) * ds
                T = np.hstack([R, (piv - R @ piv)[:, None]])
                Ms2 = list(Ms)
                for k in sub:
                    Ms2[k] = T[:, :2] @ Ms[k] + np.hstack([np.zeros((2, 2)), T[:, 2:]])
                m2 = list(masks)
                for k in sub:
                    m2[k] = cv2.warpAffine(px[k][..., 3], Ms2[k], (W, H), flags=cv2.INTER_LINEAR) > 128
                c2, o2 = evalm(m2)
                if c2 - 50 * o2 > cov - 50 * over:
                    Ms, masks, cov, over, improved = Ms2, m2, c2, o2, True
                    tick += 1
                    if on_tick:
                        on_tick(tick, Ms, masks)
                    break
        if not improved:
            break
    # overflow is hard: cut the subtree of any piece still overflowing (the rest stays one component)
    alive = set(range(len(st.placed)))
    for i in sorted(range(1, len(st.placed)), key=lambda i: -len(subtree(ch, i))):
        if i not in alive:
            continue
        if (masks[i] & ~fd & ~ign).sum() > CUT_SHARE * fig.sum():
            for k in subtree(ch, i):
                alive.discard(k)
    if 0 in alive and (masks[0] & ~fd & ~ign).any():
        pass                                                   # the seed fitted at work resolution; reported below
    return Ms, masks, alive


def components(st, alive):
    """connected components of the snapped graph over the alive pieces"""
    par = {i: i for i in alive}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for a, _, b, _ in st.snaps:
        if a in alive and b in alive:
            par[find(a)] = find(b)
    return len({find(i) for i in alive})
