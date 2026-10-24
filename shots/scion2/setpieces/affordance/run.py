"""AFFORDANCE & CONTACT swarm: interaction geometry for every set piece.

Inputs (read-only): shots/kits/cut/{catalog,registry}.json, the .webp cut-outs, hygiene.json (other swarm: grade /
usable / defects), semantics.json (other swarm: category), semantics/emb_img.npz (CLIP ViT-B/32 image embeddings of
every card, reused instead of re-embedding). Text prompts are embedded here (cache/txt.npz).
Output: shots/scion2/setpieces/affordance.json
"""
import json, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
SP = os.path.join(ROOT, 'shots/scion2/setpieces')
sys.path.insert(0, HERE)
import lexicon as LX
import geom as G

TAGS = ('.props.', '.set.', '.hero.', '.fx.')
PFX = 'a painted paper cut-out of '
PROMPTS = {
    'seat': ['a chair', 'a sofa', 'a bench', 'a bed', 'a stool', 'an armchair', 'a church pew', 'a seat cushion',
             'stone steps', 'a tree stump'],
    'surface': ['a table', 'a counter', 'a shelf', 'a desk', 'a chest of drawers', 'a bar counter', 'a window sill',
                'a box', 'a plinth'],
    'grip': ['a cup', 'a bottle', 'a mobile phone', 'a microphone', 'a lantern', 'a book', 'a flower', 'a candle',
             'a guitar', 'a letter', 'a ring', 'a coin', 'a small handheld object'],
    'aperture': ['a door', 'a window', 'a gate', 'an archway', 'a doorway', 'a window frame', 'a wall with a door',
                 'a wall with windows'],
    'lean': ['a wall', 'a column', 'a post', 'a railing', 'a fence', 'a tree trunk', 'a lamp post', 'a pillar'],
    'occluder': ['a car', 'a bush', 'a counter', 'a sofa', 'a table', 'a railing', 'a boat', 'a planter',
                 'a church pew'],
    'stand_on': ['a step', 'a stair tread', 'a platform', 'a stone landing', 'a floor', 'a doorstep', 'a road'],
    '_other': ['the sky', 'a cloud', 'a person', 'a face', 'printed text', 'a beam of light', 'a scrap of paper',
               'an abstract shape', 'a flame', 'water', 'a landscape', 'a building far away', 'a hand',
               'a flower petal', 'a mountain'],
}
KORDER = [k for k in PROMPTS]


def txt_emb():
    cache = os.path.join(HERE, 'cache', 'txt.npz')
    key = json.dumps([PFX, PROMPTS], sort_keys=True)
    if os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        if str(z['key']) == key:
            return z['T'].item()
    sys.path.insert(0, os.path.join(ROOT, 'shots/scion2/evolve/puzzle'))
    import hygiene as H
    T = {k: H._txt([PFX + s for s in v]) for k, v in PROMPTS.items()}
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    np.savez(cache, T=np.array(T, dtype=object), key=key)
    return T


def clip_kind_probs(e, T):
    """softmax (T=100) over every prompt; p(kind) = sum over its prompts. Measured."""
    s = []
    lab = []
    for k in KORDER:
        v = T[k] @ e
        s.extend(v.tolist()); lab.extend([k] * len(v))
    s = np.array(s) * 100
    p = np.exp(s - s.max()); p /= p.sum()
    out = {}
    for k in KORDER:
        out[k] = float(sum(pp for pp, l in zip(p, lab) if l == k))
    best = KORDER[int(np.argmax([out[k] for k in KORDER]))]
    top_prompt = PROMPTS[lab[int(np.argmax(s))]][int(np.argmax(s)) - lab.index(lab[int(np.argmax(s))])]
    return out, best, top_prompt


CODEISH = {'front', 'back', 'left', 'right', 'part', 'near', 'mid', 'centre', 'center', 'large', 'small', 'medium',
           'separate', 'blank', 'copy'}
WHOLE_PROPS = {'a cup', 'a bottle', 'a mobile phone', 'a microphone', 'a lantern', 'a book', 'a candle', 'a guitar'}
SEM_TO_KIND = {'furniture-seat': ['seat', 'occluder'], 'furniture-surface': ['surface', 'occluder'],
               'aperture': ['aperture'], 'handheld-prop': ['grip']}


def main():
    t0 = time.time()
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    reg = json.load(open(os.path.join(CUT, 'registry.json')))['parts']
    hyg = json.load(open(os.path.join(SP, 'hygiene.json')))['parts']
    sem = json.load(open(os.path.join(SP, 'semantics.json')))['parts']
    z = np.load(os.path.join(SP, 'semantics', 'emb_img.npz'), allow_pickle=True)
    EMB = dict(zip(z['ids'].tolist(), z['emb']))
    T = txt_emb()

    parts, checked_none, skipped = {}, {}, {}
    stats = {'sheets': 0, 'parts': 0, 'cards': 0, 'refs_skipped': 0, 'with_affordance': 0, 'checked_none': 0,
             'by_kind': {}, 'dropped_candidates': {}, 'image_missing': 0}
    for sid, S in cat.items():
        if not any(t in sid for t in TAGS):
            continue
        stats['sheets'] += 1
        for p in S['parts']:
            stats['parts'] += 1
            pid = p['id']
            if p['kind'] == 'ref':
                stats['refs_skipped'] += 1
                skipped[pid] = 'kind ref (reference panel): skipped'
                continue
            stats['cards'] += 1
            r = reg.get(pid, {})
            h = hyg.get(pid, {})
            if h and not h.get('usable', True):
                checked_none[pid] = {'sheet': sid, 'label': p.get('label'), 'none_reason':
                                     'hygiene swarm: not usable (%s) - never placed, so no contact geometry' %
                                     ', '.join(d['kind'] for d in h.get('defects', []) if d.get('severity') in ('C', None) or True)}
                stats.setdefault('hygiene_unusable', 0); stats['hygiene_unusable'] += 1
                continue
            sm = sem.get(pid, {}).get('final', {})
            m, info = LX.match(p.get('label'), p.get('name'), pid.split('/')[1], sid, r.get('place'))
            e = EMB.get(pid)
            cp, cbest, ctop = (clip_kind_probs(e, T) if e is not None else ({}, None, None))
            cands = {k: v for k, v in m.items() if not v.get('blocked_by')}
            blocked = {k: v['blocked_by'] for k, v in m.items() if v.get('blocked_by')}
            # unlabelled cards: let CLIP + the semantics swarm's category propose (inferred, low weight)
            # (rule changed after viewing kind_grip_1 / kind_seat_1: the loose version proposed sand inserts, petals,
            # pillows, blankets, glass panes; now CLIP's own top kind must agree, p >= 0.5, no label word blocked)
            nouns = {w for w in (info.get('primary_words') or []) if len(w) >= 4} - CODEISH
            if not cands and not blocked and not nouns and not info.get('note_label') and '.fx.' not in sid \
                    and sm.get('category') in SEM_TO_KIND:
                for k in SEM_TO_KIND[sm['category']]:
                    if k == 'occluder':
                        continue
                    ok = cbest == k and cp.get(k, 0) >= 0.5
                    if k == 'grip':
                        ok = ok and '.props.' in sid and ctop in WHOLE_PROPS and cp.get(k, 0) >= 0.6
                    if ok:
                        cands[k] = {'strength': 0.0, 'words': [ctop.split()[-1]] if k == 'grip' else [],
                                    'from': 'semantics+clip only (no label word)'}
            hdefects = [d['kind'] for d in h.get('defects', [])]
            grade = h.get('grade')
            usable = h.get('usable', True)
            base = {'sheet': sid, 'label': p.get('label'), 'place': r.get('place'), 'registry_q': r.get('q'),
                    'hygiene': {'grade': grade, 'usable': usable, 'defects': hdefects,
                                'duplicate_of': h.get('duplicate_of')},
                    'semantics_category': sm.get('category'),
                    'clip': {'top_kind': cbest, 'top_prompt': ctop,
                             'p': {k: round(v, 3) for k, v in cp.items()}} if cp else None,
                    'label_match': {'primary_words': info.get('primary_words'), 'note_label': info.get('note_label', False),
                                    'blocked': blocked}}
            if not cands:
                why = 'note/heading label' if info.get('note_label') else (
                    'fx sheet' if '.fx.' in sid else ('label words blocked: %s' % blocked if blocked else 'no affordance word in label'))
                base['none_reason'] = why
                checked_none[pid] = base
                continue
            im = G.load(os.path.join(CUT, p['file']))
            if im is None:
                stats['image_missing'] += 1
                base['none_reason'] = 'image missing'
                checked_none[pid] = base
                continue
            P = G.Piece(im)
            if not P.ok:
                base['none_reason'] = 'empty alpha'
                checked_none[pid] = base
                continue
            base['px'] = [int(im.shape[1]), int(im.shape[0])]
            base['alpha_bbox'] = [P.x0, P.y0, P.W, P.H]
            ppcm = r.get('px_per_cm')
            affs, dropped = [], {}
            words_all = info.get('primary_words') or []
            for k, c in cands.items():
                w = c['words'] or words_all
                if k == 'seat':
                    wa = set(words_all) | set(w)
                    furn = wa & {'chair', 'armchair', 'sofa', 'couch', 'pew', 'settee', 'throne', 'seat'}
                    g, q, ev = G.seat(P, sorted(wa), back_expected=bool(furn) and not wa & {'cushion', 'saddle'})
                elif k in ('surface', 'stand_on'):
                    g, q, ev = G.top_line(P, k)
                    if g is not None and k == 'stand_on':
                        g = {'top_y': g['y'], 'foot_y': g['rest_y'], 'x_range': g['x_range'],
                             **({'top_face': g['top_face']} if 'top_face' in g else {})}
                        if c.get('ground'):
                            g['ground'] = True
                            g['walk_band'] = [g['top_y'], P.y1]
                            ev['note'] = 'ground band: whole strip is walkable; feet anywhere in walk_band (depth = y)'
                    elif g is not None:
                        g = {'surface_y': g['y'], 'rest_y': g['rest_y'], 'x_range': g['x_range'],
                             **({'top_face': g['top_face']} if 'top_face' in g else {})}
                elif k == 'grip':
                    g, q, ev = G.grip(P, w)
                elif k == 'aperture':
                    g, q, ev = G.aperture(P, words_all, c.get('role_hint'), c.get('needs_hole', False) or c['strength'] == 0)
                    if g and c['strength'] == 0 and any(o['fill'] < 0.75 for o in g.get('openings', [])):
                        g, ev = None, {'why': 'CLIP-only aperture with ragged holes (broken glass / fragments)'}
                    if g and ppcm:
                        for o in g.get('openings', []):
                            o['h_cm'] = round(o['rect'][3] / ppcm, 1); o['w_cm'] = round(o['rect'][2] / ppcm, 1)
                elif k == 'lean':
                    g, q, ev = G.lean(P, c.get('orient', 'v'), words_all)
                elif k == 'occluder':
                    g, q, ev = G.occluder(P, w)
                if g is None:
                    dropped[k] = {'why': ev.get('why', 'geometry failed'), 'label': c}
                    continue
                # confidence (inferred): label words 0.45, CLIP agreement 0.25, geometry quality 0.30;
                # capped by hygiene (C / unusable -> x0.4) and registry q C (x0.7)
                pk = cp.get(k, 0.0) if cp else 0.0
                clip_term = min(1.0, pk / 0.3)
                # labels on these sheets are often re-assigned to the wrong card (viewed: 'BOAT_A' is a planet,
                # 'TELEVISION PEDESTAL STAND' a television): hygiene's label_mismatch + CLIP near zero -> drop
                if 'label_mismatch' in hdefects and pk < 0.1 and c['strength'] > 0:
                    dropped[k] = {'why': 'label probably belongs to another card (hygiene label_mismatch, CLIP p_%s=%.3f, CLIP top=%s)' % (k, pk, ctop), 'label': c}
                    continue
                conf = 0.45 * c['strength'] + 0.25 * clip_term + 0.30 * q
                caps = []
                if not usable or grade == 'C':
                    conf *= 0.4; caps.append('hygiene C / unusable')
                if r.get('q') == 'C':
                    conf *= 0.7; caps.append('registry q C')
                if 'label_mismatch' in hdefects and c['strength'] > 0:
                    conf = min(conf * 0.8, 0.45); caps.append('hygiene label_mismatch: label may belong to another card; check the image')
                if c['strength'] == 0:
                    conf = min(conf, 0.35); caps.append('no label word: CLIP/semantics only')
                # cap only when CLIP calls it a non-affordance thing (viewed: walls lost to 'a wall with a door',
                # which is another affordance kind, not a disagreement)
                if pk < 0.03 and c['strength'] > 0 and cbest == '_other':
                    conf = min(conf, 0.3); caps.append('CLIP disagrees (p_%s=%.3f, top prompt %r)' % (k, pk, ctop))
                aff = {'kind': k, 'geometry': g, 'confidence': round(conf, 2),
                       'evidence': {'label': {'words': c['words'], 'strength': c['strength'], 'from': c.get('from'),
                                              **({'note': c['note']} if 'note' in c else {})},
                                    'clip_p_kind': round(pk, 3), 'geometry_quality': q, 'geometry': ev,
                                    'basis': {'label': 'measured (words read)', 'clip': 'measured',
                                              'geometry': 'measured from alpha/colour; which line is the seat etc. is a rule (inferred)',
                                              'confidence': 'inferred'},
                                    **({'caps': caps} if caps else {})}}
                if ppcm:
                    aff['evidence']['px_per_cm'] = ppcm
                affs.append(aff)
            if dropped:
                base['dropped_candidates'] = dropped
                for k in dropped:
                    stats['dropped_candidates'][k] = stats['dropped_candidates'].get(k, 0) + 1
            if not affs:
                base['none_reason'] = 'candidates had no usable geometry: %s' % {k: v['why'] for k, v in dropped.items()}
                checked_none[pid] = base
                continue
            affs.sort(key=lambda a: -a['confidence'])
            base['affordances'] = affs
            base['doubt'] = round(1 - max(a['confidence'] for a in affs), 2)
            parts[pid] = base
            for a in affs:
                stats['by_kind'][a['kind']] = stats['by_kind'].get(a['kind'], 0) + 1
    stats['with_affordance'] = len(parts)
    stats['checked_none'] = len(checked_none)
    stats['seconds'] = round(time.time() - t0, 1)
    out = {
        'about': ('AFFORDANCE & CONTACT swarm. Per set-piece part: interaction geometry in the piece\'s own pixels '
                  '(x right, y down, origin = top-left of the part .webp). Kinds: seat {seat_y, x_range, back: left|'
                  'right|behind|none}, surface {surface_y, rest_y, x_range, top_face?}, grip {point, up (unit vector, '
                  'image coords), mode}, aperture {role: frame|painted_opening|leaf, openings: [{rect [x,y,w,h], type '
                  'door|window|floor_opening, floor_y, sill_y?, passable}]} or leaf {rect, hinge_side}, lean {edges '
                  '[{side, x, y_range}], face?} or {edge: top, y, x_range}, occluder {hide_y, solid_y, x_range, base_y, '
                  'coverage_below, hides: solid|partial|see-through}, stand_on {top_y, foot_y, x_range, ground?, '
                  'walk_band?}. Every affordance carries confidence (inferred) and evidence (label words: measured; '
                  'clip_p_kind: measured; geometry rule + numbers: measured). parts = has affordances; checked_none = '
                  'every other set-piece card, with the reason; skipped = reference panels. ALL set-piece sheets '
                  'processed, no sampling.'),
        'code': 'shots/scion2/setpieces/affordance/ (lexicon.py label rules, geom.py geometry, run.py, audit.py)',
        'inputs_reused': ['shots/kits/cut/catalog.json', 'shots/kits/cut/registry.json',
                          'shots/scion2/setpieces/hygiene.json (grade/usable/defects)',
                          'shots/scion2/setpieces/semantics.json (category, only to propose kinds for unlabelled cards)',
                          'shots/scion2/setpieces/semantics/emb_img.npz (CLIP image embeddings, reused)'],
        'clip_prompts': {'prefix': PFX, 'kinds': PROMPTS},
        'summary': stats,
        'parts': parts,
        'checked_none': checked_none,
        'skipped': skipped,
    }
    json.dump(out, open(os.path.join(SP, 'affordance.json'), 'w'), indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main()
