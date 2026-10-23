"""Fitness of one candidate against one target. Every term is a proxy, lower is better; score() returns them all.

  joint      mean distance (cm, in the target's own scale) between where the candidate's chain joints landed and the
             Pose Lab markers: elbows, wrists, knees, ankles (shoulders, hips and neck are pinned, so 0 by construction),
             toes (foot card tip vs toe marker, half weight). It measures pose, not looks.
  sil        1 - IoU of the candidate's alpha with the reference painting's alpha (the painting's SHAPE only).
  coh        coherence: colour dE (CIE76, /10) between neighbouring cloth parts and between left/right twins;
             +0.15 per extra kit family among the cloth cards (one costume, one sheet is best); +0.5 if the two hands,
             +0.5 if the two boots come from different families; view mismatch with the genome's view (0.15 unknown,
             0.3 front<->3/4, 0.8 otherwise) per card, /3; the head against the view the target's head shows
             (x3 when a back of head meets a face), each boot against side / front as the target's toe points (x0.5); spread of the per-part scale genes (one scale); +0.1 per
             harvest card (kit sheets preferred); +0.3 for a head from another costume sheet.
  integ      joint integrity: width step at elbow and knee (|w_parent_end - w_child_end| / larger, the cloth width
             across the bone measured on each card); shoulder and hip gap = cm from the joint to the torso / hip
             cloth beyond half the sleeve's / thigh's own root width (0 when the root overlaps the body);
             ankle and wrist gap = cm from the shin's / forearm's end to the boot / hand cloth beyond 1 cm; stretch wanted beyond the 12% limit (shows as joint
             error too, reported separately).
  copy       a penalty for using what the reference painting is: normalised cross-correlation of each placed card's
             grey pixels with the reference painting's grey pixels under it; any part above 0.6 adds (ncc - 0.6).
             Cards cut from the target are already excluded from the pool; this catches a kit card that is the same
             drawing as the painted part.
  total = joint/4 + 2*sil + coh + integ + 2*copy
"""
import math
import numpy as np, cv2

from . import assemble as AS

W_JOINT, W_SIL, W_COPY = 1 / 4., 2.0, 2.0


def dE(a, b):
    return float(np.linalg.norm(np.asarray(a) - np.asarray(b)))


def view_cost(card_view, v):
    if card_view is None:
        return .15
    if card_view == v:
        return 0.
    grp = {'front': 'f', 'threequarter': 'f', 'side': 's', 'back': 'b', 'threequarter_back': 'b'}
    if grp.get(card_view) == grp.get(v):
        return .3
    return .8


def score(G, t, lib, PL=None, prep_ref=None):
    PL = PL or AS.place(G, t, lib)
    pts, s = t['pts'], t['s']
    terms = {}
    # joint
    errs = []
    for S in 'LR':
        errs += [np.linalg.norm(PL['uarm' + S].Q - pts['elbow' + S]), np.linalg.norm(PL['farm' + S].Q - pts['wrist' + S]),
                 np.linalg.norm(PL['thigh' + S].Q - pts['knee' + S]), np.linalg.norm(PL['shin' + S].Q - pts['ankle' + S]),
                 .5 * np.linalg.norm(PL['foot' + S].Q - pts['toe' + S])]
    terms['joint'] = float(np.mean(errs) / s)
    # silhouette
    acc, masks = AS.render_fast(PL, G['view'], t)
    if prep_ref is None:
        prep_ref = prep_reference(t)
    ra, rg = prep_ref
    ca = acc[..., 3] > 128
    inter = (ca & ra).sum(); uni = (ca | ra).sum()
    terms['sil'] = float(1 - inter / max(uni, 1))
    # coherence
    coh = 0.
    cloth_pairs = [('torso', 'uarmL'), ('torso', 'uarmR'), ('uarmL', 'farmL'), ('uarmR', 'farmR'), ('thighL', 'shinL'),
                   ('thighR', 'shinR'), ('uarmL', 'uarmR'), ('farmL', 'farmR'), ('thighL', 'thighR'), ('shinL', 'shinR'),
                   ('handL', 'handR'), ('footL', 'footR'), ('pelvis', 'thighL'), ('pelvis', 'thighR'), ('torso', 'thighL')]
    des = [dE(PL[a].card.lab, PL[b].card.lab) for a, b in cloth_pairs if a in PL and b in PL]
    coh += np.mean(des) / 10.
    fam = lambda k: lib[G['parts'][k]['id']]['family']
    cloth = ['torso', 'uarmL', 'uarmR', 'farmL', 'farmR', 'thighL', 'thighR', 'shinL', 'shinR']
    coh += .15 * (len({fam(k) for k in cloth}) - 1)
    coh += .5 * (fam('handL') != fam('handR')) + .5 * (fam('footL') != fam('footR'))
    vc = sum(view_cost(lib[g['id']]['view'], G['view']) for k, g in G['parts'].items() if g and k not in ('handL', 'handR', 'head', 'footL', 'footR'))
    coh += vc / 3.
    # head and feet follow what the target shows, not the body's view: a head turned to profile, boots seen side-on
    hv, want_h = lib[G['parts']['head']['id']]['view'], t.get('head_view') or [G['view']]
    hc = min(view_cost(hv, w) for w in want_h)
    coh += 3 * hc if hc >= .8 else hc          # a back of head on a front body costs most
    for S in 'LR':
        fv, want_f = lib[G['parts']['foot' + S]['id']]['view'], t.get('foot_view_' + S) or [G['view']]
        coh += .5 * min(view_cost(fv, w) for w in want_f)
    coh += float(np.std([g['k'] for g in G['parts'].values() if g])) * 3
    coh += .1 * sum(lib[g['id']]['kind'] == 'harvest' for g in G['parts'].values() if g)
    coh += .3 * bool(lib[G['parts']['head']['id']].get('other_costume'))
    terms['coh'] = float(coh)
    # integrity
    steps = []
    for S in 'LR':
        for a, b in (('uarm' + S, 'farm' + S), ('thigh' + S, 'shin' + S)):
            w1, w0 = PL[a].card.w1 * PL[a].g['k'], PL[b].card.w0 * PL[b].g['k']
            steps.append(abs(w1 - w0) / max(w1, w0, 1e-3))
    body = masks['torso'] > .5
    hipc = body | (masks['pelvis'] > .5) if 'pelvis' in masks else body
    dt_t = cv2.distanceTransform((~body).astype(np.uint8), cv2.DIST_L2, 3)
    dt_h = cv2.distanceTransform((~hipc).astype(np.uint8), cv2.DIST_L2, 3)
    gaps = []
    H, W = body.shape
    for S in 'LR':
        # the sleeve / thigh root reaches the body cloth when the cloth is within half the root's own width
        for dt, p, pl in ((dt_t, pts['shoulder' + S], PL['uarm' + S]), (dt_h, pts['hip' + S], PL['thigh' + S])):
            x, y = int(np.clip(p[0], 0, W - 1)), int(np.clip(p[1], 0, H - 1))
            gaps.append(max(0., dt[y, x] / s - .5 * pl.card.w0 * pl.g['k']))
    for S in 'LR':
        # a boot / hand must touch the end of its trouser leg / sleeve: cm from the shin's (forearm's) end point to
        # the foot (hand) cloth, beyond 1 cm
        for part, end in (('foot' + S, PL['shin' + S].Q), ('hand' + S, PL['farm' + S].Q)):
            m = masks[part] > .5
            if not m.any():
                gaps.append(5.)
                continue
            dt = cv2.distanceTransform((~m).astype(np.uint8), cv2.DIST_L2, 3)
            x, y = int(np.clip(end[0], 0, W - 1)), int(np.clip(end[1], 0, H - 1))
            gaps.append(max(0., dt[y, x] / s - 1.))
    over = [max(0., abs(p.want - 1) - .12) for p in PL.values() if p.key[:-1] in ('uarm', 'farm', 'thigh', 'shin') or p.key == 'torso']
    terms['width_step'] = float(np.mean(steps))
    terms['gap_cm'] = float(np.mean(gaps))
    terms['overstretch'] = float(np.mean(over))
    terms['integ'] = float(2 * np.mean(steps) + .3 * np.mean(gaps) + 2 * np.mean(over))
    # copy check
    gray = cv2.cvtColor(np.clip(acc[..., :3], 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    cp, worst = 0., (0., None)
    for k, m in masks.items():
        mm = (m > .9) & ra
        if mm.sum() < 60:
            continue
        a_, b_ = gray[mm], rg[mm]
        a_ = a_ - a_.mean(); b_ = b_ - b_.mean()
        ncc = float((a_ * b_).sum() / (np.sqrt((a_ * a_).sum() * (b_ * b_).sum()) + 1e-6))
        cp += max(0., ncc - .6)
        if ncc > worst[0]:
            worst = (ncc, k)
    terms['copy'] = float(cp)
    terms['max_ncc'] = [round(worst[0], 3), worst[1]]
    terms['total'] = float(W_JOINT * terms['joint'] + W_SIL * terms['sil'] + terms['coh'] + terms['integ'] + W_COPY * terms['copy'])
    return terms


def prep_reference(t):
    ref = t['ref']
    ra = ref[..., 3] > 128
    rg = cv2.cvtColor(ref[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
    return ra, rg
