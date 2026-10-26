"""Body coverage for every character in the cast plan, and what each poem is blocked by.

    python3 -m studio.body_coverage_all        (run from shots/scion2)
    writes studio/body_coverage_all.json and studio/body_coverage_all.md

Each character in cast_plan.json is measured if it has a rig module (rigkit/chars/<name>__<costume>.py):
the same needs and tests as studio/body_coverage.py, on that character's own costume. A character with no
rig module is listed as NOT MEASURED, with the reason, so no gap is hidden and no coverage is invented.
Then each poem is checked: which of its characters have gaps, and so which poems cannot yet be staged
from paintings alone.
"""
import json, os
from collections import Counter

from studio import select as sel
from studio.body_coverage import NEEDS, RING, raw
from rigkit import core

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
CHARS = os.path.join(ROOT, 'rigkit', 'chars')


def module_for(key):
    ch, _, co = key.partition('/')
    return f'{ch}__{co}'


def costume_of(mod):
    spec = core.char_module(mod)
    cat = spec.catalog() if hasattr(spec, 'catalog') else {}
    MK = core.load_markers(mod)
    cos = Counter((cat.get(t, {}) or {}).get('costume') for t in MK).most_common(1)
    return cos[0][0] if cos and cos[0][0] else None


def measure(mod):
    costume = costume_of(mod)
    lib = sel.library(mod, costume=costume)
    rows, gaps = [], []
    for label, use, test in NEEDS + RING:
        hits = [d.id.split('/')[-1] for d in lib if test(d)]
        rows.append({'need': label, 'uses': use, 'covered_by': hits[:4], 'count': len(hits)})
        if not hits:
            gaps.append({'need': label, 'uses': use})
    return {'module': mod, 'costume': costume, 'drawings': len(lib), 'needs': rows, 'gaps': gaps,
            'covered': sum(1 for r in rows if r['count']), 'total': len(rows)}


def run():
    plan = json.load(open(os.path.join(ROOT, 'cast_plan.json')))
    chars = {}
    for key in plan['characters']:
        mod = module_for(key)
        if os.path.exists(os.path.join(CHARS, mod + '.py')):
            try:
                chars[key] = dict(measure(mod), measured=True)
            except Exception as e:
                chars[key] = {'measured': False, 'reason': f'rig module failed to load: {str(e)[:120]}', 'gaps': []}
        else:
            chars[key] = {'measured': False, 'reason': 'no rig module: its paintings are catalogued, but no layered rig exists yet', 'gaps': []}
    poems = {}
    for pid, p in sorted(plan['poems'].items()):
        members = list(p['cast'].keys())
        blocked = [k for k in members if chars.get(k, {}).get('measured') and chars[k]['gaps']]
        unmeasured = [k for k in members if not chars.get(k, {}).get('measured')]
        poems[pid] = {'title': p['title'], 'cast': members, 'blocked_by': blocked, 'not_measured': unmeasured,
                      'staged_from_paintings_only': not blocked and not unmeasured}
    out = {'characters': chars, 'poems': poems,
           'summary': {'characters': len(chars), 'measured': sum(1 for c in chars.values() if c.get('measured')),
                       'with_gaps': sum(1 for c in chars.values() if c.get('measured') and c['gaps']),
                       'poems': len(poems), 'poems_clear': sum(1 for p in poems.values() if p['staged_from_paintings_only'])}}
    json.dump(out, open(os.path.join(HERE, 'body_coverage_all.json'), 'w'), indent=1)
    L = ['# Body coverage, every character and poem', '',
         f"{out['summary']['measured']} of {out['summary']['characters']} characters measured; "
         f"{out['summary']['with_gaps']} of those have gaps; "
         f"{out['summary']['poems_clear']} of {out['summary']['poems']} poems can be staged from paintings alone.", '']
    L += ['## Poems', '', '| poem | title | blocked by (characters with gaps) | not measured |', '|---|---|---|---|']
    for pid, p in poems.items():
        L.append(f"| {pid} | {p['title']} | {', '.join(p['blocked_by']) or '—'} | {', '.join(p['not_measured']) or '—'} |")
    L += ['', '## Characters', '', '| character | costume | clean drawings | needs covered | gaps (commission) |', '|---|---|---|---|---|']
    for k, c in chars.items():
        if c.get('measured'):
            L.append(f"| {k} | {c['costume']} | {c['drawings']} | {c['covered']} of {c['total']} | {'; '.join(g['need'] for g in c['gaps']) or 'none'} |")
        else:
            L.append(f"| {k} | — | — | NOT MEASURED | {c['reason']} |")
    open(os.path.join(HERE, 'body_coverage_all.md'), 'w').write('\n'.join(L) + '\n')
    print(json.dumps(out['summary']))
    for pid, p in poems.items():
        print(pid, p['title'], 'blocked by', p['blocked_by'], 'unmeasured', len(p['not_measured']))


if __name__ == '__main__':
    run()
