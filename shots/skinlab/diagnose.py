"""The evidence pack the experiment agents read: where the pieces, the rigs and the faces go wrong, measured.

    python3 shots/skinlab/diagnose.py            # -> shots/skinlab/state.json (machine) + shots/skinlab/STATE.md (a glance)
    python3 shots/skinlab/diagnose.py --prompt   # also fills AGENT_FOUNDRY_PROMPT.xml with STATE.md -> prompt.rendered.xml

Every number here is recomputed from library.json (+ labels.json when present), so an agent's experiment can be judged
by re-running this and comparing: a proposal names the metric it moves and by how much, and the next run says if it did.
Metrics (lower is better unless noted):
  views.*            per part: cards whose view rests only on a guess (no label, no person), and label-vs-CLIP conflicts.
                     CAUTION: CLIP's view model was trained on these same labels, so few conflicts is expected, not reassuring.
  coverage.*         per character: which part x view slots have no card at all (side/front/back), i.e. forced kitbash
  scale.*            per part: spread of true length (cm) within one character (max/min), and against the Vitruvian canon.
                     CAUTION: arm and leg px/cm were set by normalize.py FROM the skeleton's slot lengths, so their spread is
                     ~1.0 by construction and proves nothing; only head, pelvis and foot spreads are independent evidence.
  misfiled           cards CLIP (learnt) reads confidently as another part, still unsettled by a person
  pelvis.*           hip bridges: how many characters have none (the torso then hangs on nothing), and how many lack 3 brads
  feet.*             shoes: facing unknown, sole length vs the canon (1/7 height), front/back views missing
  faces.*            front heads: painted-vs-blank unsettled, features per character, skin-tone spread of features
  labels             how much of the library a person has settled
"""
import collections, json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
VG = {'profile': 'side', 'side': 'side', 'front': 'front', 'threequarter': 'front', 'back': 'back', 'threequarter_back': 'back'}
H = 184.0   # the poet's rest height in cm (kit.CHARS poetm); canon lengths below are fractions of it
CANON = {'head': H / 8 / .86 * .86, 'torso': .31 * H, 'upper_arm': .165 * H, 'forearm': .15 * H, 'hand': .1 * H, 'thigh': .25 * H, 'shin': .23 * H, 'foot': H / 7, 'pelvis': .11 * H}
BODY = ['head', 'torso', 'pelvis', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot']


def load():
    L = json.load(open(os.path.join(HERE, 'library.json')))
    HL = json.load(open(os.path.join(HERE, 'labels.json'))).get('cards', {}) if os.path.exists(os.path.join(HERE, 'labels.json')) else {}
    for c in L:
        h = HL.get(c['id'], {})
        c['_h'] = h
        c['_slot'] = h.get('slot') or c['slot']
        c['_view'] = VG.get(h.get('view') or c.get('view') or ((c.get('clip') or {}).get('view_l') if (c.get('clip') or {}).get('view_l_p', 0) > .8 else None) or c.get('est_view') or '', None)
        c['_viewsrc'] = 'person' if h.get('view') else 'label' if c.get('view') else 'clip' if (c.get('clip') or {}).get('view_l_p', 0) > .8 else 'pixels' if c.get('est_view') else 'none'
        c['_len'] = ((c['B'][0] - c['A'][0]) ** 2 + (c['B'][1] - c['A'][1]) ** 2) ** .5 / c['px_per_cm'] if c.get('px_per_cm') else None
    return L


def main():
    L = load()
    body = [c for c in L if c['_slot'] in BODY and not c['_h'].get('bad')]
    out = {}
    # views: how each part's view is known, and where the label and CLIP disagree
    out['views'] = {}
    for p in BODY:
        cs = [c for c in body if c['_slot'] == p]
        src = collections.Counter(c['_viewsrc'] for c in cs)
        conflict = [c['id'] for c in cs if c.get('view') and (c.get('clip') or {}).get('view_l') and VG.get(c['view']) != c['clip']['view_l'] and c['clip'].get('view_l_p', 0) > .85]
        out['views'][p] = {'cards': len(cs), 'by_source': dict(src), 'guessed_only': src['pixels'] + src['none'] + src['clip'], 'label_vs_clip_conflicts': len(conflict), 'conflict_ids': conflict[:12]}
    # coverage: per character, the part x view slots with nothing (kitbash forced)
    chars = collections.Counter(c['character'] for c in body if c.get('character'))
    cov = {}
    for ch, n in chars.most_common():
        if n < 12:
            continue
        mine = [c for c in body if c['character'] == ch]
        have = {(c['_slot'], c['_view']) for c in mine}
        absent = [p for p in BODY if not any(c['_slot'] == p for c in mine)]   # no card for the part at all
        unknown = [p for p in BODY if p not in absent and not any(c['_slot'] == p and c['_view'] for c in mine)]   # cards, but no view known
        missing = [f'{p}:{v}' for p in BODY if p not in absent and p not in unknown for v in ('side', 'front', 'back') if (p, v) not in have]
        cov[ch] = {'cards': n, 'absent_parts': absent, 'view_unknown_parts': unknown, 'missing_views': missing, 'missing_n': len(absent) * 3 + len(missing)}
    out['coverage'] = dict(sorted(cov.items(), key=lambda kv: -kv[1]['missing_n']))
    # scale: within one character, the same part should have one true length
    sc = {}
    for p in BODY:
        spreads, vs_canon = [], []
        for ch in chars:
            ls = [c['_len'] for c in body if c['character'] == ch and c['_slot'] == p and c['_len']]
            if len(ls) >= 3:
                spreads.append((max(ls) / max(.1, min(ls)), ch))
            vs_canon += [l / CANON[p] for l in ls]
        spreads.sort(reverse=True)
        sc[p] = {'median_spread': round(st.median([s for s, _ in spreads]), 2) if spreads else None, 'worst': [[round(s, 2), ch] for s, ch in spreads[:4]],
                 'median_vs_canon': round(st.median(vs_canon), 2) if vs_canon else None, 'outside_0.7_1.4_of_canon': sum(1 for r in vs_canon if r < .7 or r > 1.4)}
    out['scale'] = sc
    # misfiled: CLIP reads it as another part, confidently, and no person has said otherwise
    mis = [c for c in L if (c.get('clip') or {}).get('part') and c['clip']['part'] != c['_slot'] and c['clip'].get('part_p', 0) > .8 and not c['_h']]
    out['misfiled'] = {'n': len(mis), 'by_part': dict(collections.Counter(f"{c['_slot']}->{c['clip']['part']}" for c in mis).most_common(12)), 'ids': [c['id'] for c in mis[:20]]}
    # pelvis: the torso and thighs need something to hang on
    pel = [c for c in body if c['_slot'] == 'pelvis']
    pel_chars = collections.Counter(c['character'] for c in pel)
    out['pelvis'] = {'cards': len(pel), 'characters_without': [ch for ch in cov if ch not in pel_chars], 'not_three_brads': sum(1 for c in pel if len(c.get('brads') or []) != 3),
                     'by_view': dict(collections.Counter(c['_view'] for c in pel))}
    # feet
    ft = [c for c in body if c['_slot'] == 'foot']
    out['feet'] = {'cards': len(ft), 'by_view': dict(collections.Counter(c['_view'] for c in ft)), 'facing_unsettled': sum(1 for c in ft if 'left' not in c['_h']),
                   'sole_vs_canon_median': round(st.median([c['_len'] / CANON['foot'] for c in ft if c['_len']]), 2),
                   'no_ankle_brad': sum(1 for c in ft if c.get('pts') == 'guess')}
    # faces
    heads = [c for c in body if c['_slot'] == 'head' and c['_view'] == 'front']
    feats = [c for c in L if c['_slot'] in ('eye', 'brow', 'mouth', 'nose') and not c['_h'].get('bad')]
    tones = [c['tone'] for c in feats if c.get('tone')]
    out['faces'] = {'front_heads': len(heads), 'painted_unsettled': sum(1 for c in heads if 'painted' not in c['_h']),
                    'features': dict(collections.Counter(c['_slot'] for c in feats)), 'features_by_character': dict(collections.Counter(c['character'] for c in feats).most_common(10)),
                    'feature_tone_L_spread': round(max(t[0] for t in tones) - min(t[0] for t in tones), 1) if tones else None,
                    'heads_with_no_feature_kit': sorted({c['character'] for c in heads} - {c['character'] for c in feats})}
    # people
    out['labels'] = {'settled_by_a_person': sum(1 for c in L if c['_h']), 'of': len(L)}
    json.dump(out, open(os.path.join(HERE, 'state.json'), 'w'), indent=1)
    # a glance
    md = ['# Skin Lab state (diagnose.py)', '', 'Recomputed from library.json; agents propose experiments against these numbers.', '',
          '| part | cards | view only guessed | label vs CLIP conflicts | length spread in one character (median, worst) | vs Vitruvian (median) |', '|---|---|---|---|---|---|']
    for p in BODY:
        v, s = out['views'][p], out['scale'][p]
        md.append(f"| {p} | {v['cards']} | {v['guessed_only']} | {v['label_vs_clip_conflicts']} | {s['median_spread']} ({s['worst'][0][0] if s['worst'] else '-'} {s['worst'][0][1] if s['worst'] else ''}) | {s['median_vs_canon']} |")
    md += ['', f"Misfiled (CLIP, unsettled): {out['misfiled']['n']} — {out['misfiled']['by_part']}",
           f"Pelvis: {out['pelvis']['cards']} hip bridges; characters with none: {', '.join(out['pelvis']['characters_without']) or '—'}; not 3 brads: {out['pelvis']['not_three_brads']}; views {out['pelvis']['by_view']}",
           f"Feet: {out['feet']['cards']}; views {out['feet']['by_view']}; facing unsettled {out['feet']['facing_unsettled']}; sole vs canon {out['feet']['sole_vs_canon_median']}",
           f"Faces: {out['faces']['front_heads']} front heads, painted unsettled {out['faces']['painted_unsettled']}; features {out['faces']['features']}; heads with no feature kit: {', '.join(out['faces']['heads_with_no_feature_kit'][:10])}",
           f"Settled by a person: {out['labels']['settled_by_a_person']} of {out['labels']['of']}", '', '## Coverage gaps (forced kitbash), worst first', '']
    for ch, v in list(out['coverage'].items())[:12]:
        md.append(f"- **{ch}** ({v['cards']} cards): no {', '.join(v['absent_parts']) or '—'} at all; views unknown for {', '.join(v['view_unknown_parts']) or '—'}; missing views {', '.join(v['missing_views'][:10]) or '—'}")
    open(os.path.join(HERE, 'STATE.md'), 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md))
    if '--prompt' in __import__('sys').argv:   # the experiment agents' prompt, with this run's evidence in it
        from xml.sax.saxutils import escape
        t = open(os.path.join(HERE, 'AGENT_FOUNDRY_PROMPT.xml')).read().replace('{{STATE_MD}}', escape('\n'.join(md)))
        open(os.path.join(HERE, 'prompt.rendered.xml'), 'w').write(t)


if __name__ == '__main__':
    main()
