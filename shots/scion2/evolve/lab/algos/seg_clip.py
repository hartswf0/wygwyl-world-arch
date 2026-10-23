"""seg_clip (round 03, a new family). Hypothesis (the person): match parts onto the reference by appearance -- split the
reference into part regions with SAM (prompted from the Pose Lab markers), then for each region pick the library card
whose CLIP embedding is closest to the region's, whose shape fits the region once its joint axis lies on the region's
bone, and whose learnt identity agrees with the part; join the cards brad to brad at the joints.

Per region: pool = hygiene-clean cards with >= 1 brad; identity gate: a card the Skin Lab classifier is confident about
(clip.part_p >= .6) must be that part (head / hand / foot regions take only confident cards of that class, heads also
pass grow_clean's face rule); unsure cards (and harvest cards) are allowed on limb and torso regions at -0.1.
Score = z(CLIP region-card) + 1.5 IoU(card placed on the bone, region) - gate penalty - 0.5 per missing joint brad
(a brad within 25% of the card's length from its proximal end, and its distal end for arm and leg segments); top 40
by CLIP are placed.
Placement: card anchors (cards.prep: limb A/B, torso waist->neck, head neck->crown) onto the bone, uniform scale
0.85-1.3 x canonical, mirror and reversed anchors tried. Joints: parents first, each child is turned and moved so its
brad nearest the joint sits on the parent's brad nearest the joint and its far end points along its bone (an edge);
a joint where a card has no brad within 14 cm of it stays unjoined (reported; snapping at any distance collapsed
the body).
No pocket fill (fewest pieces: one card per part)."""
import numpy as np, cv2

from evolve.lab import segclip as SC
from evolve.puzzle import hygiene as HY, pieces as PC
from . import grow_clean as GCL

CLASS = {'head': 'head', 'torso': 'torso', 'uarm': 'upper_arm', 'farm': 'forearm', 'hand': 'hand', 'thigh': 'thigh', 'shin': 'shin', 'foot': 'foot'}
STRICT = {'head', 'hand', 'foot'}
PARENT = {'head': 'torso', 'uarmL': 'torso', 'uarmR': 'torso', 'farmL': 'uarmL', 'farmR': 'uarmR', 'handL': 'farmL', 'handR': 'farmR',
          'thighL': 'torso', 'thighR': 'torso', 'shinL': 'thighL', 'shinR': 'thighR', 'footL': 'shinL', 'footR': 'shinR'}
ORDER = ['thighL', 'thighR', 'shinL', 'shinR', 'footL', 'footR', 'torso', 'head', 'uarmL', 'uarmR', 'farmL', 'farmR', 'handL', 'handR']
TOPN = 40
SNAP_CM = 9.          # a joint whose nearest brads are farther apart than this stays unjoined (was 15: cards flew off)


def part_class(p):
    return CLASS[p.rstrip('LR') if p not in ('head', 'torso') else p]


def prepare(ctx):
    """segmentation, per-card class / anchors / embeddings (cached in ctx)"""
    if 'seg' in ctx:
        return
    import json, os
    from evolve import library as LB, cards as CD
    t = ctx['t']
    L, B = SC.segment(t)
    lib = {c['id']: c for c in LB.cards(ctx['char'], ctx['costume'])}
    Ljs = {c['id']: c for c in json.load(open(os.path.join(LB.SKIN, 'library.json')))}
    C = HY.classify(ctx['pieces'])
    heads_ok = GCL.opts_for(ctx)['heads']
    info = {}
    for i, p in enumerate(ctx['pieces']):
        if HY.junk(C[p['id']]) or not len(p['brads']) or p['id'] not in lib:
            continue
        try:
            k = CD.prep(lib[p['id']])
        except Exception:
            continue
        if not k.ok:
            continue
        off = np.array(PC.card_pixels.offsets.get(p['id'], (0, 0)), float)
        cl = (Ljs.get(p['id']) or {}).get('clip') or {}
        conf = cl.get('part') if cl.get('part_p', 0) >= .6 else None
        if conf == 'head' and i not in heads_ok:
            continue
        A_, B_ = np.asarray(k.A) - off, np.asarray(k.B) - off
        lab_ = np.linalg.norm(B_ - A_) + 1e-6
        dA = np.linalg.norm(p['brads'] - A_, axis=1).min() / lab_
        dB = np.linalg.norm(p['brads'] - B_, axis=1).min() / lab_
        info[i] = {'A': A_, 'B': B_, 'ppc': k.ppc, 'cls': conf, 'slot': p['label'], 'brad_A': dA < .25, 'brad_B': dB < .25}
    E = SC.card_emb([ctx['pieces'][i] for i in info])
    ctx['seg'] = {'L': L, 'B': B, 'info': info, 'E': E}


def place_M(ctx, i, part, mir, t, flip=0):
    inf = ctx['seg']['info'][i]
    a, b = ctx['seg']['B'][part]
    A, Bc = inf['A'], inf['B']
    if (part == 'torso') != bool(flip):     # card waist -> neck runs against the bone neck -> mid-hip; flip: anchors reversed
        A, Bc = Bc, A
    v = Bc - A
    lc = np.linalg.norm(v) + 1e-6
    lb = np.linalg.norm(b - a) + 1e-6
    g0 = t['s'] / inf['ppc']
    g = g0 * float(np.clip(lb / (lc * g0), .85, 1.3))
    ang = np.arctan2(*(b - a)[::-1]) - np.arctan2(*v[::-1])
    R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]]) * g
    if mir:                                  # mirror across the card's own axis
        u = v / lc
        Mi = np.eye(2) - 2 * np.outer([-u[1], u[0]], [-u[1], u[0]])
        R = R @ Mi
    tvec = a - R @ A
    return np.hstack([R, tvec[:, None]])


def choose(ctx, t, part, idx, ref_e, k=1, region=None):
    """ranked [(score, piece index, mirror, M)] for one region"""
    seg = ctx['seg']
    cls = part_class(part)
    cand = []
    for i, inf in seg['info'].items():
        if cls in STRICT:
            if inf['cls'] != cls:
                continue
            pen = 0.
        else:
            if inf['cls'] is not None and inf['cls'] != cls:
                continue
            pen = 0. if inf['cls'] == cls else .1
        # joints need brads: a brad at the proximal end (to its parent) and at the distal end (for its children)
        if part != 'torso' and not inf['brad_A']:
            pen += .5
        if part.rstrip('LR') in ('uarm', 'farm', 'thigh', 'shin') and not inf['brad_B']:
            pen += .5
        cand.append((float(seg['E'][ctx['pieces'][i]['id']] @ ref_e), i, pen))
    if not cand:
        return []
    cand.sort(key=lambda x: -x[0])
    cand = cand[:TOPN]
    sims = np.array([c[0] for c in cand])
    z = (sims - sims.mean()) / (sims.std() + 1e-6)
    W, H = t['size']
    out = []
    for (s_, i, pen), zz in zip(cand, z):
        for mir, flip in ((0, 0), (1, 0), (0, 1), (1, 1)):
            M = place_M(ctx, i, part, mir, t, flip)
            m = cv2.warpAffine(ctx['pieces'][i]['px'][..., 3], M, (W, H)) > 128
            inter = (m & region).sum(); uni = (m | region).sum()
            out.append((zz + 1.5 * inter / max(uni, 1) - pen, i, mir, M))
    out.sort(key=lambda x: -x[0])
    return out[:k]


def snap(ctx, chosen, t):
    """chain re-placement: each child (parents first) is turned and moved so that its brad nearest the joint sits on the
    parent's brad nearest the joint, and its far end points at the end of its region's bone. Every joint with a brad
    within 14 cm of the joint on both cards is an edge."""
    edges = []
    B = ctx['seg']['B']
    order = ['torso', 'head', 'uarmL', 'uarmR', 'thighL', 'thighR', 'farmL', 'farmR', 'shinL', 'shinR', 'handL', 'handR', 'footL', 'footR']
    for p in order:
        if p not in chosen or p == 'torso' or PARENT[p] not in chosen:
            continue
        J, end = B[p]
        pc, cc = chosen[PARENT[p]], chosen[p]
        bp = ctx['pieces'][pc['pi']]['brads'] @ pc['M'][:, :2].T + pc['M'][:, 2]
        bc = ctx['pieces'][cc['pi']]['brads'] @ cc['M'][:, :2].T + cc['M'][:, 2]
        dp, dc = np.linalg.norm(bp - J, axis=1), np.linalg.norm(bc - J, axis=1)
        if dp.min() > 14 * t['s'] or dc.min() > 14 * t['s']:
            continue                    # always snapping (any distance) collapsed the body: tried, 31% coverage
        ip, ic = int(np.argmin(dp)), int(np.argmin(dc))
        piv, cb = bp[ip], bc[ic]
        inf = ctx['seg']['info'][cc['pi']]
        ends = [cc['M'][:, :2] @ inf['A'] + cc['M'][:, 2], cc['M'][:, :2] @ inf['B'] + cc['M'][:, 2]]
        far = max(ends, key=lambda q: np.linalg.norm(q - cb))
        ang = np.arctan2(*(end - piv)[::-1]) - np.arctan2(*(far - cb)[::-1])
        R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
        cc['M'] = np.hstack([R @ cc['M'][:, :2], (R @ (cc['M'][:, 2] - cb) + piv)[:, None]])
        edges.append((PARENT[p], ip, p, ic))
    return edges


def subtree(p):
    out = [p]
    for c, par in PARENT.items():
        if par == p:
            out += subtree(c)
    return out


def assemble_from(ctx, chosen, t, info=None):
    edges = snap(ctx, chosen, t)
    names = [p for p in ORDER if p in chosen]
    idx = {p: n for n, p in enumerate(names)}
    asm = {'pieces': [{'pi': chosen[p]['pi'], 'M': chosen[p]['M'].tolist()} for p in names],
           'edges': [[idx[a], ia, idx[b], ib] for a, ia, b, ib in edges if a in idx and b in idx],
           'info': dict(info or {}, parts={p: ctx['pieces'][chosen[p]['pi']]['id'] for p in names},
                        unjoined=[p for p in names if p != 'torso' and not any(e[2] == p for e in edges)]),
           '_seg': ctx['seg']['L']}
    return asm


def assemble(target, library, seed, refine=False):
    ctx = target
    t = ctx['t']
    prepare(ctx)
    L = ctx['seg']['L']
    chosen, alts, refs = {}, {}, {}
    for n, p in enumerate(SC.PARTS):
        region = L == n
        if region.sum() < 30:
            continue
        crop = SC.region_crop(t['ref'], L, n)
        e = SC.embed(crop)
        refs[p] = (e, region)
        r = choose(ctx, t, p, n, e, k=5, region=region)
        if r:
            chosen[p] = {'pi': r[0][1], 'M': r[0][3]}
            alts[p] = r
    if refine:
        from evolve.lab import harness as H
        for p in list(chosen):
            best_sim = None
            for sc_, i, mir, M in alts[p]:
                trial = {q: dict(v) for q, v in chosen.items()}
                trial[p] = {'pi': i, 'M': M}
                asm = assemble_from(ctx, {q: dict(v) for q, v in trial.items()}, t)
                ren = H.render(ctx, asm)
                ys, xs = np.nonzero(refs[p][1])
                box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
                sim = float(H.clip_embed(H.on_bg(ren, box)) @ refs[p][0])
                if best_sim is None or sim > best_sim:
                    best_sim, best = sim, {'pi': i, 'M': M}
            chosen[p] = best
    return assemble_from(ctx, chosen, t, {'refine': refine})
