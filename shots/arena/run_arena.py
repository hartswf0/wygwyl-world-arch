"""Compile a solved Scene into a clip (display list per frame) and run challenges.

  python3 shots/arena/run_arena.py                 # every authored challenge
  python3 shots/arena/run_arena.py ACT-001 ACT-006 # some
  python3 shots/arena/run_arena.py ACT-001 --variant short_limbs

Writes, per run:   shots/arena/clips/<ACT>[__variant].json   (drawn by shots/arena.html)
and updates:       shots/arena/results/arena_results.json    (spec-shaped results; failed takes are kept)
"""
import importlib, json, math, os, sys, time, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arena_lib as AL

PARTS = json.load(open(os.path.join(HERE, 'cast', 'dummy', 'parts.json')))
REF_H = PARTS['ref_height']
SPEC = json.load(open(os.path.join(HERE, 'spec', 'acting_arena_v0.2.json')))
CH = {c['id']: c for c in SPEC['challenges']}


def r2(v):
    return [round(float(v[0]), 1), round(float(v[1]), 1)]


def place(pid, A, B, H, flip=False, thick=1.0):
    """matrix for a piece whose bone runs from A to B (stage px)"""
    m = PARTS['parts'][pid]
    A = np.asarray(A, float); B = np.asarray(B, float)
    v = B - A
    Lw = float(np.linalg.norm(v))
    th = math.atan2(v[1], v[0])
    sx = max(Lw, 1e-3) / m['len']
    sy = (H / REF_H) / m['unit'] * thick * (-1 if flip else 1)
    c, s = math.cos(th), math.sin(th)
    M = np.array([[c * sx, -s * sy], [s * sx, c * sy]])
    t = A - M @ np.array(m['pivot'], float)
    return {'t': 'img', 'id': pid, 'm': [round(M[0, 0], 5), round(M[1, 0], 5), round(M[0, 1], 5), round(M[1, 1], 5),
                                          round(t[0], 2), round(t[1], 2)]}


def actor_ops(a, J):
    H, L, look = a.B.H, a.B.L, a.look
    f, view = J['f'], J['view']
    flip = f < 0
    ops = []
    def limb(side, far):
        sfx = '.far' if far else ''
        return [place('%s.uarm%s' % (look, sfx), J['sh' + side], J['elb' + side], H),
                place('%s.farm%s' % (look, sfx), J['elb' + side], J['wri' + side], H),
                place('%s.hand.%s%s' % (look, J['shape' + side], sfx), J['wri' + side], J['tip' + side], H, flip=flip)]
    def leg(side, far):
        sfx = '.far' if far else ''
        A = np.asarray(J['ank' + side]); cc = J['c' + side]
        d = AL.rotv((L['toe'], 0.0), J['pitch' + side])
        Bt = A + np.array([cc * d[0], d[1]])
        if abs(cc) < 0.25:  # end-on (mid-turn): keep a sliver of the foot visible
            Bt = A + np.array([0.25 * (1 if cc >= 0 else -1) * d[0], d[1]])
        return [place('%s.thigh%s' % (look, sfx), J['hip' + side], J['knee' + side], H),
                place('%s.shin%s' % (look, sfx), J['knee' + side], A, H),
                place('%s.foot%s' % (look, sfx), A, Bt, H, flip=cc < 0)]
    hv = J.get('hview') or view
    head = place('%s.head.%s.%s' % (look, 'side' if hv == 'side' else 'front', J['face']), J['N'], J['C'], H,
                 flip=flip and hv == 'side')
    if view == 'side':
        ops += limb('L', True) + leg('L', True)
        ops.append(place('%s.torso_side' % look, J['P'], J['N'], H, flip=flip))
        ops.append(head)
        ops += leg('R', False) + limb('R', False)
    else:
        ops += leg('L', False) + leg('R', False)
        ops.append(place('%s.torso_front' % look, J['P'], J['N'], H))
        ops += limb('L', False) + limb('R', False)
        ops.append(head)
    for o in ops:
        o['k'] = 1
    return ops


def prop_ops(p, pose, owner):
    pts = [r2(c) for c in p.corners(pose)]
    o = {'t': 'poly', 'pts': pts, 'fill': p.fill, 'stroke': '#1a120b', 'w': 2, 'kind': p.kind, 'name': p.name}
    out = [o]
    if p.kind == 'cup':  # the brim of liquid
        c, a = pose
        lvl = [c + AL.rotv((-p.w * 0.42, -p.h * 0.38), a), c + AL.rotv((p.w * 0.42, -p.h * 0.38), a)]
        out.append({'t': 'line', 'pts': [r2(q) for q in lvl], 'w': 4, 'color': '#6b3b1c'})
    if p.kind == 'box':
        c, a = pose
        out.append({'t': 'line', 'pts': [r2(c + AL.rotv((-p.w / 2, -p.h * 0.1), a)), r2(c + AL.rotv((p.w / 2, -p.h * 0.1), a))], 'w': 6, 'color': '#d9c49a'})
    return out


def compile_clip(sc, ch, tech, failing, accepted, variant, wall):
    fr_flags = {}
    for k, fr, msg in failing:
        fr_flags.setdefault(fr, []).append(msg.replace('#', '').replace('  ', ' '))
    fr_ok = {}
    for k, fr, msg in accepted:
        fr_ok.setdefault(fr, []).append(msg.replace('#', '').replace('  ', ' '))
    images = {}
    frames = []
    beats = sorted(sc.beats, key=lambda b: b['f'])
    order = sorted(sc.actors.values(), key=lambda a: -a.lane)  # far lanes first
    for fr in range(sc.N):
        draw = [{'t': 'bg'}, {'t': 'floor', 'y': sc.floor}]
        if sc.water:
            draw.append({'t': 'water', 'x0': sc.water[0], 'x1': sc.water[1], 'y': sc.water[2], 'under': True})
        back = [p for p in sc.props.values() if p.kind in ('wall', 'ledge', 'box', 'door') and not sc.owners[p.name][fr]]
        for p in back:
            draw += prop_ops(p, sc.prop_track[p.name][fr], None)
        for a in order:
            J = sc.poses[a.name][fr]
            lowest = max(J['heelL'][1], J['heelR'][1], J['toeL'][1], J['toeR'][1])
            draw.append({'t': 'shadow', 'x': round(float(J['P'][0]), 1), 'y': sc.floor, 'rx': round(a.B.H * 0.16, 1),
                         'a': round(max(0.15, 0.55 - (sc.floor - lowest) / a.B.H), 2)})
            ops = actor_ops(a, J)
            for o in ops:
                images[o['id']] = PARTS['parts'][o['id']]['file']
            draw += ops
            # props carried by this actor are drawn with them (in front)
            for p in sc.props.values():
                if sc.owners[p.name][fr] and sc.owners[p.name][fr].startswith(a.name + '.'):
                    draw += prop_ops(p, sc.prop_track[p.name][fr], sc.owners[p.name][fr])
        for p in sc.props.values():
            if p not in back and not sc.owners[p.name][fr]:
                draw += prop_ops(p, sc.prop_track[p.name][fr], None)
        if sc.water:
            draw.append({'t': 'water', 'x0': sc.water[0], 'x1': sc.water[1], 'y': sc.water[2]})
        dbg = {'com': [], 'sup': [], 'tgt': []}
        for a in sc.actors.values():
            J = sc.poses[a.name][fr]
            carried = [(sc.prop_track[p.name][fr][0], p.mass) for p in sc.props.values()
                       if sc.owners[p.name][fr] and sc.owners[p.name][fr].startswith(a.name + '.')]
            dbg['com'].append(r2(AL.com(a, J, carried)))
            for k in ('heelL', 'ballL', 'toeL', 'heelR', 'ballR', 'toeR', 'kneeL', 'kneeR', 'P'):
                p = J[k]
                if abs(sc.ground_y(p[0]) - p[1]) < a.B.cm * 1.5 or (k.startswith(('knee', 'P')) and abs(sc.ground_y(p[0]) - p[1]) < a.B.R['shin'] + a.B.cm):
                    dbg['sup'].append(r2(p))
        for (an, k), (e, spec) in sc.hand_err[fr].items():
            J = sc.poses[an][fr]
            dbg['tgt'].append(r2(J['palm' + k[-1]]) + [round(e, 2)])
        now = [b for b in beats if b['f'] <= fr]
        frames.append({'f': fr, 'draw': draw, 'dbg': dbg, 'flags': fr_flags.get(fr, []), 'ok': fr_ok.get(fr, []),
                       'beat': (now[-1]['who'] + ': ' + now[-1]['beat']) if now else ''})
    clip = {
        'id': sc.id, 'variant': variant, 'title': '%s · %s' % (ch['id'], ch['title']), 'situation': ch['situation'],
        'success_observation': ch['success_observation'], 'clock': {'fps': sc.fps, 'frames': sc.N},
        'floor': sc.floor, 'images': images, 'beats': beats, 'technical': tech,
        'cast': [{'name': a.name, 'height_px': a.B.H, 'cm_px': round(a.B.cm, 3), 'variant': a.B.variant, 'look': a.look}
                 for a in sc.actors.values()],
        'props': [{'name': p.name, 'kind': p.kind, 'solid': p.solid, 'mass': p.mass} for p in sc.props.values()],
        'notes': sc.notes[:40], 'not_checked': AL.CHECKS_NOT_MEASURED, 'solve_seconds': round(wall, 2),
        'ledger': [['DRAWN', 'Stand-in cardboard dummy pieces drawn by build_dummy.py; the man\'s cut pieces replace them by id.'],
                   ['INVENTED', 'The performance is authored in the challenge script (keys and motion generators); nothing is captured or retargeted.']],
        'frames': frames,
    }
    return clip


def run(cid, variant='standard'):
    mod = importlib.import_module('challenges.' + cid.replace('-', '_').lower())
    t0 = time.time()
    sc = mod.build(variant=variant)
    sc.solve()
    tech, failing, accepted = AL.check(sc)
    wall = time.time() - t0
    ch = CH[cid]
    clip = compile_clip(sc, ch, tech, failing, accepted, variant, wall)
    os.makedirs(os.path.join(HERE, 'clips'), exist_ok=True)
    name = cid + ('' if variant == 'standard' else '__' + variant)
    with open(os.path.join(HERE, 'clips', name + '.json'), 'w') as fh:
        json.dump(clip, fh, separators=(',', ':'))
    run_rec = {
        'run_at': time.strftime('%Y-%m-%d'), 'instrument': 'WYGWYL Acting Arena (2D cut-out solver, shots/arena)',
        'take': name, 'variant': variant,
        'tier_reached': getattr(mod, 'TIER', 'complete acted situation'),
        'execution_note': 'Authored with motion generators and keys on the arena card dummy (thigh, shin and foot are separate pieces). '
                          'No Mixamo clip was searched, imported or retargeted.',
        'frames': sc.N, 'fps': sc.fps, 'cast': list(sc.actors), 'props': ['%s%s' % (p.kind, ' (solid)' if p.solid else '') for p in sc.props.values()],
        'beats': sorted([b for b in sc.beats if b['beat'] not in ('passing', 'heel strike')], key=lambda b: b['f']),
        'technical': tech,
        'performance_note': getattr(mod, 'PERFORMANCE_NOTE', {}).get(variant, 'not reviewed yet'),
        'performance_review': 'Single reviewer (the coding agent), from the contact sheet; not a panel review.' if getattr(mod, 'PERFORMANCE_NOTE', {}).get(variant) else 'none',
        'clip': 'arena/clips/%s.json' % name,
    }
    return run_rec, tech


def save_results(recs):
    path = os.path.join(HERE, 'results', 'arena_results.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old = json.load(open(path)) if os.path.exists(path) else {'challenges': {}}
    for cid, rec in recs:
        ent = old['challenges'].setdefault(cid, {'id': cid, 'title': CH[cid]['title'], 'takes': []})
        ent['takes'] = [t for t in ent['takes'] if not (t['take'] == rec['take'] and t['run_at'] == rec['run_at'])]
        ent['takes'].append(rec)  # earlier takes, including failed ones, are kept
        std = [t for t in ent['takes'] if t['variant'] == 'standard']
        if std:
            ent['result'] = 'tested_pass' if std[-1]['technical']['result'] == 'pass' else 'tested_fail'
        ent['stress_variations_run'] = sorted({t['variant'] for t in ent['takes'] if t['variant'] != 'standard'})
    authored = set(old['challenges'])
    for cid in CH:
        if cid not in authored:
            old['challenges'][cid] = {'id': cid, 'title': CH[cid]['title'], 'result': 'unsearched', 'takes': [],
                                      'why': 'not authored in the arena yet'}
    old['challenges'] = dict(sorted(old['challenges'].items()))
    old['about'] = ('Arena results in the spec\'s coverage states. Technical results come from arena_lib.check(); '
                    'performance notes are separate and come from a single reviewer looking at contact sheets.')
    old['updated'] = time.strftime('%Y-%m-%d %H:%M')
    old['summary'] = {s: sum(1 for c in old['challenges'].values() if c.get('result') == s) for s in SPEC['coverage_states']}
    json.dump(old, open(path, 'w'), indent=1)
    return old


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    variant = 'standard'
    if '--variant' in sys.argv:
        variant = sys.argv[sys.argv.index('--variant') + 1]
        args = [a for a in args if a != variant]
    if not args:
        args = sorted(f[:-3].upper().replace('_', '-') for f in os.listdir(os.path.join(HERE, 'challenges'))
                      if f.startswith('act_') and f.endswith('.py'))
    recs = []
    for cid in args:
        rec, tech = run(cid, variant)
        recs.append((cid, rec))
        print('%-8s %-22s %-4s drift %.2f  contact %.2f cm  reach %.3f  leg %.2f cm  balanced %.1f%%  flags %s' % (
            cid, variant, tech['result'], tech['worst_planted_drift_cm_per_frame'], tech['worst_contact_error_cm'],
            tech['max_arm_reach_ratio'], tech['max_leg_error_cm'], tech['balanced_pct_of_grounded_frames'],
            json.dumps(tech['flagged_frame_ranges'])[:400]))
    res = save_results(recs)
    print('summary', res['summary'])
