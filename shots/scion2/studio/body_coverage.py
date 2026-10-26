"""Body coverage: for each actor, which body poses the scenes need, and which clean drawings cover them.

    python3 -m studio.body_coverage        (run from shots/scion2; writes studio/body_coverage.json and .md)

A need is a pose the scenes use (stand, walk, turn ring, sit, reach, lean, kneel, lie). A need is covered
when at least one clean drawing of the actor satisfies its test. Tests read the drawing's own bone angles
(from the markers, mirrored to face right), so a pose is judged by what is drawn, not by its label alone.
Gaps are the commissions: each names the view, the posture and the pose to paint.
"""
import json, math, os
from studio import select as sel

HERE = os.path.dirname(os.path.abspath(__file__))

ACTORS = [('poet', 'poet__red_black_sunglasses', 'track'),
          ('vintage man', 'vintage_man__suit', 'suit'),
          ('vintage woman', 'vintage_woman__gown', 'gown')]


def raw(d):
    """the catalog view as labelled (back3q is kept apart from back)"""
    return d.cat.get('view') or ''


def spread(a, b):
    d = (a - b + 180) % 360 - 180
    return abs(d)


def leg_spread(d):
    return spread(d.ang.get('thighA', 0), d.ang.get('thighB', 0)) if 'thighA' in d.ang and 'thighB' in d.ang else 0


def arm_out(d):
    """how far the more extended arm is from hanging straight down (degrees, 0 = hanging)"""
    best = 0
    for k in ('uarmA', 'uarmB'):
        if k in d.ang:
            best = max(best, spread(d.ang[k], 90))
    return best


# each need: (label, what the scenes use it for, test(drawing) -> bool)
NEEDS = [
    ('stand, front', 'entrances, standing, the spin landing', lambda d: d.view == 'front' and d.cls in ('stand', 'dance', 'walk', '')),
    ('stand, 3/4', 'walks, turns, bar and parlour blocking', lambda d: d.view == 'q3' and d.cls in ('stand', 'dance', 'walk', '')),
    ('stand, profile', 'walking across the frame, turn ring', lambda d: d.view == 'prof' and d.cls in ('stand', 'dance', 'walk', '')),
    ('stand, back', 'turn ring, backs of figures', lambda d: raw(d).startswith('back') and d.cls in ('stand', 'dance', 'walk', '')),
    ('walk stride, 3/4 or profile', 'walk cycles (legs apart, one foot forward)',
     lambda d: d.view in ('q3', 'prof') and leg_spread(d) >= 25),
    ('walk stride, front', 'front walks', lambda d: d.view == 'front' and leg_spread(d) >= 25),
    ('reach or point, arm out', 'grasp, point, offer, open arms', lambda d: arm_out(d) >= 60 and d.view in ('front', 'q3', 'prof', 'back', 'back3q')),
    ('sit', 'armchair, cafe, kitchen seats', lambda d: d.cls == 'sit'),
    ('kneel or crouch', 'low actions, stooping for objects', lambda d: d.cls in ('kneel', 'crouch')),
    ('lean or lunge', 'leaning on the bar, falter, lunge', lambda d: d.cls in ('lean', 'lunge')),
    ('lie or fall', 'falls, lying down, recovery', lambda d: d.cls in ('lie', 'fall')),
]

# the turn ring: a spin needs one drawing in each of these views (the far side is a mirror of a drawing)
RING = [('ring: 3/4', 'the spin, 3/4 slot', lambda d: d.view == 'q3'), ('ring: profile', 'the spin, profile slot', lambda d: d.view == 'prof'),
        ('ring: 3/4 back', 'the spin, 3/4 back slot', lambda d: raw(d).startswith('back3q')), ('ring: back', 'the spin, back slot', lambda d: raw(d) == 'back')]


def run():
    out = {}
    lines = ['# Body coverage per actor', '',
             'Every pose the scenes use, and whether a clean drawing covers it. A gap is a drawing to commission.', '']
    for name, char, costume in ACTORS:
        lib = sel.library(char, costume=costume)
        rows, gaps = [], []
        for label, use, test in NEEDS + RING:
            hits = [d.id.split('/')[-1] for d in lib if test(d)]
            rows.append({'need': label, 'uses': use, 'covered_by': hits[:4], 'count': len(hits)})
            if not hits:
                gaps.append({'need': label, 'uses': use})
        out[name] = {'drawings': len(lib), 'needs': rows, 'gaps': gaps,
                     'covered': sum(1 for r in rows if r['count']), 'total': len(rows)}
        lines += [f'## {name}  ({len(lib)} clean drawings; {out[name]["covered"]} of {out[name]["total"]} needs covered)', '',
                  '| need | used for | covered by | drawings |', '|---|---|---|---|']
        for r in rows:
            cov = ', '.join(r['covered_by']) if r['covered_by'] else '**GAP**'
            lines.append(f"| {r['need']} | {r['uses']} | {cov} | {r['count']} |")
        lines.append('')
        lines.append('**Commission:** ' + ('; '.join(g['need'] for g in gaps) if gaps else 'nothing; every need is covered.'))
        lines.append('')
    json.dump(out, open(os.path.join(HERE, 'body_coverage.json'), 'w'), indent=1)
    open(os.path.join(HERE, 'body_coverage.md'), 'w').write('\n'.join(lines))
    for name in out:
        print('%-14s %2d/%2d needs covered; gaps: %s' % (name, out[name]['covered'], out[name]['total'],
                                                       ', '.join(g['need'] for g in out[name]['gaps']) or 'none'))


if __name__ == '__main__':
    run()
