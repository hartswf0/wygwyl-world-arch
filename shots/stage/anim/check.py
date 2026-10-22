"""Trust the body: per-frame correctness check of puppet clips (sequences and retargeted acts).

    python3 shots/stage/anim/check.py shots/stage/seq/clips/seq.09.phone.profile.json [...] [--json report.json] [-v]

Every drawn body card is checked against what the card IS (cards.CARD, filled by the puppet when it is built)
and what the body is DOING on that frame (the clip's per-frame actor record: view, facing, set, points):

  side     a card drawn for the actor's L/R must be an L/R card after any mirror (hands: palm row = L, back row = R)
  view     body cards must belong to the frame's body view; the head view within one step of the body view
  facing   profile torso/head/foot cards must point the way the actor faces after mirroring (toe, nose, chest)
  shoe     every foot card must belong to the character's costume
  owner    every body card must come from the character's own kit
  planted  a heel or ball resting on the floor on two consecutive frames may move at most 0.6 cm (the arena's tolerance)
  hand     on frames where the clip says what a hand must do (hand_wants), the drawn card's shape must match
  contact  each logged contact (grip, press, pin) must stay within its tolerance on the drawn cards
  set      on sit/kneel/crouch/lie/fall frames, a character with replacement sheets must draw the set's leg cards
  order    in profile the far arm and far leg are drawn behind the torso and shaded; the near arm in front
Retargeted clips without tags are reported as such (their ops carry no roles to check).
"""
import json, math, os, sys
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cards, puppet

TOL_DRIFT = 0.6
ORDER = ['front', 'threequarter', 'profile', 'threequarter_back', 'back']
BODY = ('torso', 'bridge', 'seat', 'uarm', 'farm', 'thigh', 'shin', 'foot', 'skirt')


def owners(character):
    c = puppet.CAST.get(character, {})
    s = {character, c.get('owner', character)}
    if character.startswith('poet'): s.add('poet')
    return s


def check_clip(path, verbose=False):
    clip = json.load(open(path))
    cast = {a['id']: a for a in clip.get('cast', [])}
    for a in cast.values():
        if a['character'] in puppet.CAST:
            puppet.Puppet(a['character'], a['id'])           # registers its cards
    k = clip.get('cm_px', 4.038)
    fails = defaultdict(list)          # rule -> [(f, actor, msg)]
    counts = defaultdict(int)
    untagged = 0
    prev_feet = {}
    wants = clip.get('hand_wants', [])
    for fr in clip['frames']:
        f = fr['f']
        acts = fr.get('actors', {})
        draw = fr['draw']
        torso_idx = {}
        for i, op in enumerate(draw):
            tg = op.get('tag')
            if op.get('t') == 'img' and tg and tg.get('r') == 'torso': torso_idx[tg.get('a')] = i
        for i, op in enumerate(draw):
            if op.get('t') != 'img': continue
            tg = op.get('tag')
            if not tg:
                untagged += 1; continue
            role = tg.get('r'); aid = tg.get('a')
            if role == 'prop' or aid not in acts: continue
            A = acts[aid]; ch = cast[aid]['character']
            meta = cards.CARD.get(op['id'], {})
            m = op['m']; det = m[0] * m[3] - m[1] * m[2]; mir = det < 0
            # owner / costume
            if role in BODY + ('hand', 'head') and meta.get('owner') and meta['owner'] not in owners(ch):
                fails['owner'].append((f, aid, '%s %s from %s' % (role, op['id'], meta['owner'])))
            counts['owner'] += 1
            if role == 'foot':
                counts['shoe'] += 1
                if not cards.shoe_ok(ch, op['id']):
                    fails['shoe'].append((f, aid, 'foot card %s is not %s\'s shoe' % (op['id'], ch)))
            # side
            s = tg.get('s')
            if s and meta.get('side'):
                counts['side'] += 1
                eff = meta['side'] if not mir else ('L' if meta['side'] == 'R' else 'R')
                if eff != s:
                    fails['side'].append((f, aid, '%s_%s drawn with a %s card (%s%s)' % (role, s, eff, op['id'].split('/')[-1], ' mirrored' if mir else '')))
            # view
            view = A['view']
            if role in BODY and meta.get('view') not in (None, 'any'):
                counts['view'] += 1
                if meta['view'] != view and not meta.get('set'):
                    fails['view'].append((f, aid, '%s card is %s, body is %s' % (role, meta['view'], view)))
            if role == 'head':
                counts['view'] += 1
                hv = meta.get('view')
                if hv in ORDER and view in ORDER and abs(ORDER.index(hv) - ORDER.index(view)) > 1:
                    fails['view'].append((f, aid, 'head %s on a %s body' % (hv, view)))
            # facing (profile cards that point somewhere)
            if view == 'profile' and role in ('torso', 'head', 'foot') and meta.get('faces'):
                ax = np.array([m[0], m[1]]); n = np.linalg.norm(ax)
                if n > 1e-9 and abs(ax[0]) / n > 0.5:
                    counts['facing'] += 1
                    eff = meta['faces'] * (1 if ax[0] > 0 else -1) * 1
                    want = tg.get('hf', A['face']) if role == 'head' else A['face']
                    if eff != want:
                        fails['facing'].append((f, aid, '%s points %s, actor faces %s' % (role, '+' if eff > 0 else '-', '+' if want > 0 else '-')))
            # draw order in profile
            if view == 'profile' and s and role in ('uarm', 'farm', 'hand', 'thigh', 'shin', 'foot') and aid in torso_idx:
                counts['order'] += 1
                near = 'R' if A['face'] > 0 else 'L'
                ti = torso_idx[aid]
                if s != near and (i > ti or not op.get('shade')):
                    fails['order'].append((f, aid, 'far %s_%s drawn %s torso%s' % (role, s, 'over' if i > ti else 'under', '' if op.get('shade') else ', unshaded')))
                if s == near and role in ('uarm', 'farm', 'hand') and i < ti:
                    fails['order'].append((f, aid, 'near %s_%s drawn under the torso' % (role, s)))
        # hand wants
        for w in wants:
            if w['f'][0] <= f <= w['f'][1]:
                counts['hand'] += 1
                got = [op['tag'].get('sh') for op in draw if op.get('tag', {}).get('a') == w['a'] and op['tag'].get('r') == 'hand' and op['tag'].get('s') == w['s']]
                if not got:
                    fails['hand'].append((f, w['a'], 'no %s hand drawn (%s)' % (w['s'], w['why'])))
                elif not cards.shape_ok(w['shape'], got[0]):
                    fails['hand'].append((f, w['a'], '%s hand is %s, should be %s (%s)' % (w['s'], got[0], w['shape'], w['why'])))
        # planted feet: a heel/ball on the floor on consecutive frames must not slide
        for aid, A in acts.items():
            fl = clip.get('floor_y')
            dep = cast[aid].get('depth', 1.0)
            for s in 'LR':
                for pt in ('heel', 'ball'):
                    p = A['pts'].get('%s_%s' % (pt, s))
                    if p is None: continue
                    key = (aid, s, pt)
                    on = fl is not None and abs(p[1] - A.get('floor', fl)) < 0.8 * k * dep
                    if on and key in prev_feet and prev_feet[key][0] == f - 1 and prev_feet[key][2]:
                        d = math.hypot(p[0] - prev_feet[key][1][0], p[1] - prev_feet[key][1][1]) / (k * dep)
                        counts['planted'] += 1
                        if d > TOL_DRIFT:
                            fails['planted'].append((f, aid, '%s %s slid %.2f cm' % (s, pt, d)))
                    prev_feet[key] = (f, p, on)
        # sets
        for aid, A in acts.items():
            ch = cast[aid]['character']
            if A.get('set', 'stand') != 'stand' and puppet.CAST.get(ch, {}).get('sets'):
                counts['set'] += 1
                th = [op for op in draw if op.get('tag', {}).get('a') == aid and op['tag'].get('r') in ('thigh', 'shin')]
                if not th or any(cards.CARD.get(op['id'], {}).get('set') != A['set'] for op in th):
                    fails['set'].append((f, aid, '%s frame drawn without the %s replacement cards' % (A['set'], A['set'])))
    for c in clip.get('contacts', []):
        counts['contact'] += 1
        if c.get('pass') is False:
            fails['contact'].append((c['f'][0], c['actor'], '%s: %s max %.2f cm > %.1f' % (c['what'], c['point'], c['max_err_cm'], c['tol_cm'])))
    rules = ['side', 'view', 'facing', 'shoe', 'owner', 'planted', 'hand', 'contact', 'set', 'order']
    res = {'clip': os.path.relpath(path), 'id': clip['id'], 'frames': len(clip['frames']), 'untagged_ops': untagged,
           'rules': {r: {'checked': counts[r], 'fail': len(fails[r]), 'pass': len(fails[r]) == 0,
                         'first': ['f%d %s: %s' % x for x in fails[r][:6]]} for r in rules}}
    res['pass'] = all(v['pass'] for v in res['rules'].values()) and untagged == 0
    return res


def main():
    a = sys.argv[1:]
    out = None
    if '--json' in a:
        out = a[a.index('--json') + 1]; del a[a.index('--json'):a.index('--json') + 2]
    verbose = '-v' in a; a = [x for x in a if x != '-v']
    reps = []
    for p in a:
        r = check_clip(p, verbose); reps.append(r)
        print('%-44s %s  (%d frames%s)' % (r['id'], 'PASS' if r['pass'] else 'FAIL', r['frames'],
                                          ', %d untagged ops' % r['untagged_ops'] if r['untagged_ops'] else ''))
        for rule, v in r['rules'].items():
            flag = 'ok ' if v['pass'] else 'BAD'
            print('   %s %-8s checked %6d  fail %4d  %s' % (flag, rule, v['checked'], v['fail'], ('; '.join(v['first'][:3])) if v['first'] else ''))
    if out:
        json.dump(reps, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
