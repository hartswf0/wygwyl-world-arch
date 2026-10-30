"""Write shots/suite/data/characters.json (lane B contract) from the measured parts, the takes and the drop test.

    python3 shots/suite/lib/build_characters.py

Contract per character: {id, name, height_cm, head_heights, proportions:{...}, views:{view:{parts:[ids], joints:{...}}},
replacement:{heads:[], hands:[]}, walk:{source, cycle_frames, stride_cm}, solve_notes:[...], arena:{challenge: verdict, clip}}
plus the fields the page needs (plays, poems, rig, scale, drop, legacy audit).
Part ids are '<character>.<view>.<part>' and resolve to cast_parts.json; lane A's shots/suite/data/parts.json, when it
lands, is the registry these ids should be re-keyed to (the files are the same v2 cut parts).
"""
import glob, json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import castkit as CK  # noqa: E402

SUITE, SHOTS = CK.SUITE, CK.SHOTS
PARTS = json.load(open(os.path.join(SUITE, 'data', 'cast_parts.json')))['characters']
DROP = json.load(open(os.path.join(SUITE, 'cast', 'drop.json')))
PLAY = json.load(open(os.path.join(SHOTS, 'play', 'data.json')))
RIGS = json.load(open(os.path.join(SHOTS, 'arena', 'parts', 'kit3', 'release_v2', 'character_rigs_library.json')))['rigs']
KITS = {c['id']: c for c in json.load(open(os.path.join(SHOTS, 'arena', 'parts', 'kit3', 'v2', 'kits.json')))['cast']}
RES = json.load(open(os.path.join(SHOTS, 'arena', 'results', 'arena_results.json')))

PLAY_KEY = {'poet_tshirt': 'poet/black_tshirt', 'poet_tracksuit': 'poet/red_black_sunglasses', 'poet_soul': 'poet_soul/soul',
            'ex': 'ex/ex_jacket', 'mother': 'mother/poem09', 'she_window': 'woman/poem13', 'young_poet_pajamas': 'young_poet/pajamas_winter',
            'young_poet_tee': 'young_poet/child_clothes', 'ghost_child': 'ghost_child/ghost_nightclothes', 'father_02': 'father_02/poem02',
            'father_elder': 'father_elder/poem09', 'ancestor_indigo': 'ancestor_robe/indigo_gold', 'ancestor_elder': 'ancestor_elder/white_silver',
            'atlantis_traveler': 'traveler_1/atlantis', 'atlantis_citizen': 'citizen_1/atlantis', 'atlantis_elder': 'elder_1/atlantis',
            'vintage_party': 'vintage_man/suit', 'dj': 'dj_cyber/cyber', 'party_guest': 'party_guest/guest', 'dancer_dress': 'club_dress/club',
            'dancer_shirt': 'club_shirt/club', 'dancer_jacket': 'club_jacket/club', 'angel': 'angel/robe', 'brother': 'brother_1/poem12',
            'friend': 'friend_1/poem12', 'elder_memory': 'elders/memory', 'elder_pearls': 'elder_man/poem13', 'couple_summer': 'couple_1_a/poem13',
            'street_clothes': 'family/street_clothes'}
RIG_OF = {'poet_tshirt': 'poet_black_tshirt', 'poet_tracksuit': 'poet_tracksuit_31', 'poet_soul': 'poet_tracksuit_31', 'ex': 'ex_jacket_back',
          'woman': 'woman_muse_costumes', 'mother': 'mother_ancestors_family', 'she_window': 'woman_muse_costumes',
          'young_poet_pajamas': 'child_traveler_ghost', 'young_poet_tee': 'child_traveler_ghost', 'ghost_child': 'child_traveler_ghost',
          'father_02': 'mother_ancestors_family', 'father_elder': 'mother_ancestors_family', 'ancestor_indigo': 'mother_ancestors_family',
          'ancestor_elder': 'mother_ancestors_family', 'vintage_party': 'vintage_party_couple', 'dj': 'dj_club_citizens', 'angel': 'dj_club_citizens'}
KIT_OF = lambda c: c['dir'].split('.')[0]
CHECK_NAMES = {'foot_slide': 'foot slide', 'brad_gap': 'brad gap / holes', 'contact': 'contact error', 'height_drift': 'height drift',
               'floor': 'floor error', 'balance': 'balance', 'face_never_seen': 'face never seen'}


def thumb(path):
    im = Image.open(os.path.join(SHOTS, path)).convert('LA').resize((24, 32))
    a = np.asarray(im, np.float32)
    g = a[:, :, 0] * (a[:, :, 1] / 255)
    g = g - g.mean()
    return g / (np.linalg.norm(g) + 1e-9)


def shared_heads():
    """Heads that are the same drawing (recoloured or not): correlation of 24x32 luminance thumbnails >= 0.93."""
    th = {c['id']: thumb(PARTS[c['id']]['heads']['profile']['file']) for c in CK.CAST if not c.get('code_head')}
    groups = {}
    for a in th:
        groups[a] = sorted(b for b in th if b != a and float(th[a].ravel() @ th[b].ravel()) >= 0.93)
    return groups


def proportions(c):
    k = c['height_cm'] / CK.K.CHARS[c['build']]['height']
    J = {n: np.array(p, float) * k for n, p in CK.K.CHARS[c['build']]['J'].items()}
    d = lambda a, b: round(float(np.linalg.norm(J[a] - J[b])), 1)
    head = J['crown'][1] - J['chin'][1]
    p = dict(height_cm=c['height_cm'], head_cm=round(head, 1), head_heights=round(c['height_cm'] / head, 2),
             shoulder_height_cm=round(J['shoulderL'][1], 1), shoulder_width_cm=round(2 * abs(J['shoulderL'][0]), 1),
             hip_height_cm=round(J['hipL'][1], 1), leg_cm=round(J['hipL'][1], 1), torso_cm=round(J['neck'][1] - J['hipL'][1], 1),
             upper_arm_cm=d('shoulderL', 'elbowL'), forearm_cm=d('elbowL', 'wristL'), hand_cm=d('wristL', 'tipL'),
             thigh_cm=d('hipL', 'kneeL'), shin_cm=d('kneeL', 'ankleL'), foot_cm=round(J['toeL'][2] - J['heelL'][2], 1),
             build=c['build'], build_height_cm=CK.K.CHARS[c['build']]['height'], k=round(k, 4))
    p['hand_to_height'] = round(p['hand_cm'] / c['height_cm'], 3)
    p['leg_to_height'] = round(p['leg_cm'] / c['height_cm'], 3)
    p['reach_top_cm'] = round(p['shoulder_height_cm'] + 0.92 * (p['upper_arm_cm'] + p['forearm_cm']), 1)
    return p


def heights_seen(c):
    """Every height this character has been given across the repo (they disagree)."""
    out = {'kit_v2': KITS.get(KIT_OF(c), {}).get('height_cm')}
    pk = PLAY_KEY.get(c['id'])
    if pk:
        for ch in PLAY['characters']:
            if ch['key'] == pk:
                out['play_data'] = ch['height_cm']
    rg = RIG_OF.get(c['id'])
    if rg:
        out['rig_library'] = RIGS[rg]['anatomy']['height_cm']
        out['rig_library_head_count'] = RIGS[rg]['anatomy']['head_count']
    return out


def walk_info(c, takes):
    """Cycle and stride as the retargeted walk measured them (Bolas T001 scaled by the leg ratio)."""
    V = json.load(open(BANK_T001))
    A = [list(fr['a'].values())[0] for fr in V['frames']]
    strikes = [f for f in range(1, len(A)) if A[f]['j'][7][1] <= 1.0 and A[f - 1]['j'][7][1] > 1.0]
    cyc = int(np.median(np.diff(strikes))) if len(strikes) > 1 else None
    stride_src = None
    if len(strikes) > 1:
        xs = [A[f]['j'][7][0] for f in strikes]
        stride_src = float(np.median(np.abs(np.diff(xs))))
    p = proportions(c)
    s_leg = (p['thigh_cm'] + p['shin_cm'] + CK.K.CHARS[c['build']]['J']['ankleL'][1] * p['k']) / (44 + 43 + 8)
    pk = PLAY_KEY.get(c['id'])
    play = None
    if pk:
        for ch in PLAY['characters']:
            if ch['key'] == pk:
                play = {'draws': len(ch['draws']), 'clean_walk_indices': ch.get('clean_walk_indices') or [],
                        'stride_cm_painted': [d.get('stride_cm') for d in ch['draws'] if d.get('cls') == 'walk'][:4]}
    return {'source': 'Bolas T001 "Heel, flat, ball, toe" retargeted to this skeleton; planted feet pinned (castrun.py)',
            'cycle_frames': cyc, 'fps': 24, 'stride_cm': round(stride_src * s_leg, 1) if stride_src else None,
            'leg_ratio_to_bolas': round(s_leg, 3), 'play_whole_figure_draws': play}


def solve_notes(c, P, takes, groups, drop):
    N = []
    ss = P.get('sheet_scale', {})
    if ss:
        N.append({'problem': f"parts painted at different scales: profile cards median {ss['median_px_per_cm']} px/cm, max/min spread "
                             f"{ss['spread']}x" + (f"; outliers (x median) {ss['outliers']}" if ss.get('outliers') else '') +
                             (f"; the head sheet is {ss['head_vs_body']}x the body's px/cm" if ss.get('head_vs_body') else ''),
                  'solution': 'every part gets its own px_per_cm from the Kit 3 ghost it was painted into (cast_parts.json); '
                              'drawn at S*k/px_per_cm, so a card is its template length whatever the sheet did'})
    fid = [(n, p['aspect_fidelity']) for n, p in P['views'].get('profile', {}).items() if 'aspect_fidelity' in p and
           abs(p['aspect_fidelity'] - 1) > 0.35]
    if fid:
        N.append({'problem': 'cards painted off the ghost\'s proportions (width/length vs template, profile): ' +
                             ', '.join(f'{n} {v}' for n, v in fid),
                  'solution': 'scaled by length (limbs, torso) or sole length (feet) only; the width is left as painted and reported'})
    if c.get('head_from'):
        N.append({'problem': f"its own head card is the shared adult man's head (bearded) on a {c['height_cm']} cm child body",
                  'solution': f"borrows the child head from {c['head_from']}" + (' (tinted to the ghost wash)' if c.get('tint') else '') +
                              '; needs its own painted head'})
    if c.get('code_head'):
        N.append({'problem': "the v2 dummy head plates are the man's face recoloured (yellow/teal/coral), not blank dummy heads",
                  'solution': 'heads drawn by code (round plate, crash target, eyes, antenna/fin/bow) as the Crash Lab draws them; '
                              'height measured to the crown, the accessory above it is not height'})
    sh = groups.get(c['id']) or []
    if sh and not c.get('head_from'):
        N.append({'problem': f"head card is the same drawing as {len(sh)} other characters' ({', '.join(sh[:6])}{'...' if len(sh) > 6 else ''})",
                  'solution': 'kept for blocking; identity is carried by costume and colour until a head is painted'})
    rig = P.get('rig')
    if rig == 'skirt':
        N.append({'problem': 'skirt/robe card carries the knees (no thigh cards): planted feet pull against a rigid hem',
                  'solution': 'knee brads ride in a SLOT 4 cm above the hem (best point chosen per frame); if a planted foot is '
                              'still out of reach the whole body is lowered to it (skirt_body_drop), and the cost is reported'})
    if rig == 'legged':
        N.append({'problem': 'the v2 kit painted thighs and a hip-bridge triangle instead of the skirt ghost of its template',
                  'solution': 'rigged as legs: thigh ghosts recomputed from the same skeleton, hip bridge pinned at the waist '
                              'behind the thighs' + ('; the brocade skirt hangs over the thighs as a free overlay '
                                                     '(clamped +-25 deg to the mean thigh, thigh-exit frames counted)' if c.get('skirt_overlay') else '')})
    if c.get('back_only'):
        cut = sum(t.get('face_cut_frames', 0) for t in takes.values())
        N.append({'problem': 'the EX\'s face is never seen: back and three-quarter-back cards only',
                  'solution': f'every take is re-staged by turning the camera so he faces away for as many frames as possible '
                              f'(yaw search, 5 deg); frames that would still show his face are marked CUT and are cut in the edit '
                              f'({cut} of {sum(t["frames"] for t in takes.values())} battery frames). A turn is therefore a cut, not a turn.'})
    if c.get('wings'):
        N.append({'problem': 'wings have no template ghost and no profile card',
                  'solution': 'wings pinned at the shoulder blade (25 % down the torso), 1.35 x torso long (rig library table), '
                              'behind the body except from the back; in profile one wing, mirrored by facing'})
    if c.get('tint') or c.get('alpha', 1) < 1:
        N.append({'problem': 'translucent / pale figure', 'solution': f"cards washed to a tint {c.get('tint')} at alpha {c.get('alpha', 1)} at draw time; "
                                                                      "measurements use alpha > 0.5 so the figure still reads"})
    if c['height_cm'] < 130:
        rt = next((t for t in takes.values() if t['take'] == 'reach'), None)
        note = rt['notes'][0] if rt and rt.get('notes') else ''
        N.append({'problem': f"child scale: {c['height_cm']} cm, {proportions(c)['head_heights']} heads; short limbs cannot reach adult sockets",
                  'solution': 'root travel scaled by leg length (strides shrink), chair sized to the leg (action-owned prop), '
                              'set-owned sockets re-staged to the reach top' + (f' ({note})' if note else '')})
    hs = heights_seen(c)
    vals = {k: v for k, v in hs.items() if k in ('kit_v2', 'play_data', 'rig_library') and v}
    if len(set(vals.values())) > 1:
        N.append({'problem': 'heights disagree across the repo: ' + ', '.join(f'{k} {v} cm' for k, v in vals.items()),
                  'solution': f"canonical height_cm = {c['height_cm']} (the kit's painted build, scaled by k = {proportions(c)['k']})"})
    if 'threequarter' not in P['views'] and not c.get('back_only'):
        N.append({'problem': 'no three-quarter body sheet', 'solution': 'three-quarter frames fall back to front (<45 deg) or profile'})
    # measured failures
    for kind, t in takes.items():
        bad = [k for k, v in t.get('checks', {}).items() if v is False]
        if not bad:
            continue
        nums = []
        for b in bad:
            if b == 'brad_gap':
                nums.append(f"brad gap {t['brad_gap_cm']['worst']} cm, hole frames {t['brad_gap_cm']['hole_frames']} {t['brad_gap_cm'].get('holes_at') or ''}")
            elif b == 'floor':
                nums.append(f"floor error p95 {t['floor_error_cm']['p95_abs']} cm")
            elif b == 'height_drift':
                nums.append(f"height drift mean {t['height_drift_pct']['mean']} %")
            elif b == 'contact':
                nums.append(f"contact median {t['contact_error_cm']['median']} cm")
            elif b == 'balance':
                nums.append(f"balance {t['balance_pct']} %")
            elif b == 'foot_slide':
                nums.append(f"foot slide {t['foot_slide_cm_per_frame']['worst']} cm/f")
        N.append({'problem': f'{kind} ({t["bank"]}) fails: ' + '; '.join(nums), 'solution': 'open (kept as a failed take; see AUDIT_cast.md)',
                  'measured': True})
    return N


def views_block(cid, P):
    out = {}
    for v, parts in P['views'].items():
        ids = [f'{cid}.{v}.{n}' for n in parts]
        hd = P['heads'].get(v)
        if hd:
            ids.append(f'{cid}.{v}.head')
        t = parts.get('torso', {})
        joints = {'neck': {'torso': t.get('A'), 'head': hd['neck'] if hd else None, 'tuck_cm': 0.8}}
        for s, p in (t.get('sockets') or {}).items():
            joints[s] = {'torso': p}
        for n, p in parts.items():
            if 'A' in p and n not in ('torso',):
                joints.setdefault(n + '.A', {})[n] = p['A']
        out[v] = {'parts': ids, 'joints': joints}
    return out


def replacement_block(c):
    d = os.path.join(CK.PARTS_DIR, c['dir'])
    rel = lambda f: os.path.relpath(os.path.join(d, f), SHOTS)
    fs = sorted(os.listdir(d))
    return {'heads': [rel(f) for f in fs if f.startswith('head.')],
            'hands': [rel(f) for f in fs if f.startswith('hand.')],
            'feet': [rel(f) for f in fs if f.startswith('foot.')],
            'poses': [rel(f) for f in fs if f.startswith('replacement.')],
            'faces': len([f for f in fs if f.startswith('face.')])}


def main():
    global BANK_T001
    BANK_T001 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SHOTS, 'arena', 'bolas', 'bank', 'T001.json')
    groups = shared_heads()
    chars = []
    for c in CK.CAST:
        cid = c['id']
        P = PARTS[cid]
        tk = json.load(open(os.path.join(SUITE, 'cast', cid, 'takes.json')))['takes']
        prop = proportions(c)
        chars.append({
            'id': cid, 'name': c['name'], 'plays': c['plays'], 'poems': c['poems'].split(), 'pronoun': c['pronoun'],
            'height_cm': c['height_cm'], 'head_heights': prop['head_heights'], 'proportions': prop,
            'heights_seen': heights_seen(c), 'rig': P.get('rig'), 'parts_dir': os.path.relpath(os.path.join(CK.PARTS_DIR, c['dir']), SHOTS),
            'scale': {'k': P['k'], 'build': c['build'], 'sheet': P.get('sheet_scale'), 'rule': 'draw scale = px_per_cm(set, foot y) * k / part.px_per_cm (scale.js)'},
            'views': views_block(cid, P), 'replacement': replacement_block(c), 'walk': walk_info(c, tk),
            'solve_notes': solve_notes(c, P, tk, groups, DROP['characters'].get(cid)),
            'arena': {k: {'verdict': t['verdict'], 'bank': t['bank'], 'clip': f'cast/{cid}/{k}.mp4', 'sheet': f'cast/{cid}/{k}.jpg',
                          'checks': t['checks']} for k, t in tk.items()},
            'drop': DROP['characters'].get(cid),
        })
    legacy = []
    for L in CK.LEGACY:
        variant = {'man': 'man', 'poet': 'poet', 'bolas': 'bolas_3d'}[L['skin']]
        rows = []
        for ch in RES['challenges'].values():
            for t in ch.get('takes', []):
                if t.get('variant') == variant:
                    rows.append((ch['id'], t['technical'].get('result'), list(t['technical'].get('failed_checks', {}).keys()), t.get('clip')))
        legacy.append({'id': L['id'], 'name': L['name'], 'height_cm': L['height_cm'], 'parts': L['parts'], 'superseded_by': L['superseded_by'],
                       'arena': {r[0]: {'verdict': r[1], 'failed': r[2], 'clip': r[3]} for r in sorted(rows)},
                       'pass': sum(r[1] == 'pass' for r in rows), 'takes': len(rows),
                       'audit': 'verdicts are the MOTION\'s: drift and balance are read from the 3D bank joints, brad gap is 0 by '
                                'construction (axial stretch), so the dummy, woman and man skins pass/fail the same 18/32 challenges'})
    out = {'about': 'WYGWYL cast: every character that moves through the Acting Arena, with proportions, scale, the standard battery '
                    'measured on the render, and how each was solved. Built by shots/suite/lib/build_characters.py.',
           'contract': 'lane B (SUITE_BRIEF.md)', 'units': 'cm; px only where named', 'battery': [{'take': k, 'bank': t} for k, t in
                                                                                                    __import__('castrun').BATTERY],
           'tolerances': __import__('castrun').TOL, 'scale_lib': ['shots/suite/lib/scale.js', 'shots/suite/lib/scale.py'],
           'parts_registry': {'used': 'shots/suite/data/cast_parts.json (measured here from arena/parts/kit3/v2/parts)',
                              'pending': 'lane A shots/suite/data/parts.json was not available when this was built'},
           'characters': chars, 'legacy_rigs': legacy}
    json.dump(out, open(os.path.join(SUITE, 'data', 'characters.json'), 'w'), indent=1)
    print(len(chars), 'characters,', len(legacy), 'legacy rigs')


if __name__ == '__main__':
    main()
