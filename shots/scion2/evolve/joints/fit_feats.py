import sys, os, json
n = sys.argv[1]
sys.path.insert(0, '/tmp/claude-0/evolve-scratch/fit/jr%s' % n)
sys.path.insert(1, '/home/user/wygwyl-world-arch/shots/scion2')
sys.path.insert(2, '/home/user/wygwyl-world-arch/shots/scion2/library2/qa')
import numpy as np
from evolve.joints import parts as PT, connect as CN, lab as L
import seam
key = json.load(open('/tmp/claude-0/evolve-scratch/fit/key%s.json' % n))
allp = {p['key']: p for p in PT.parts('poet', None)}
out = {}
for sh, k in key.items():
    a, b = allp.get(k['parent']), allp.get(k['child'])
    if a is None or b is None:
        out[sh] = {'error': 'part missing'}; continue
    g = L.load_methods(k['joint'])[k['method']]
    r = CN.connect(a, b, k['joint'], k['angle'], g)
    if r is None:
        out[sh] = {'error': 'no render'}; continue
    img = r['img']
    rgba = np.dstack([img[..., [2, 1, 0]], img[..., 3]]).astype(np.uint8)
    lay = lambda X: np.dstack([X[..., [2, 1, 0]], X[..., 3]]).astype(np.uint8) if X is not None else None
    top = r.get('on_top', g.get('on_top', 'child'))
    mA, mB = r['pm'].copy(), r['cm'].copy()
    if r.get('brad_mask') is not None:
        if top == 'parent': mA |= r['brad_mask']
        else: mB |= r['brad_mask']
    jn = k['joint'] if k['joint'] in seam.ROM else 'generic'
    s = seam.score(rgba, mA, mB, r['pivot'], -r['axis_p'], r['axis_c'], over='A' if top == 'parent' else 'B', joint=jn, angle=None,
                   layerA=lay(r.get('P')), layerB=lay(r.get('C')),
                   bradA=None if r.get('grommet') is None else [float(v) for v in r['grommet']],
                   bradB=None if r.get('child_brad') is None else [float(v) for v in r['child_brad']], px_per_cm=CN.RS,
                   origA=r.get('origP'), origB=r.get('origC'),
                   facingA=(a.get('view'), a.get('facing')) if a.get('view') and a.get('facing') else None,
                   facingB=(b.get('view'), b.get('facing')) if b.get('view') and b.get('facing') else None)
    out[sh] = {kk: (float(v) if isinstance(v, (int, float, np.floating, np.integer, bool)) else v) for kk, v in s.items()
               if kk not in ('spot',) and not isinstance(v, (np.ndarray,))}
json.dump(out, open('/tmp/claude-0/evolve-scratch/fit/feat%s.json' % n, 'w'), indent=1, default=str)
print(n, len(out), sum('error' in v for v in out.values()))
