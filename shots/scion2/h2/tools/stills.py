"""Reproduce test poses by replacement: pick the nearest painting from another family, place it
(uniform scale + translation, maybe mirror), write RGBA + a painting|pick sheet.
usage: stills.py kill|all"""
import sys, os, json, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import h2
H2 = os.path.join(h2.ROOT, 'shots/scion2/h2')
COVERED, NEAR = 0.65, 1.10    # thresholds on D, set by looking at the picks (see README)

def status(D):
    return 'covered' if D <= COVERED else ('approximate' if D <= NEAR else 'gap')

def run(ids, outdir, sheetname, cols):
    os.makedirs(outdir, exist_ok=True)
    rows = []; picks = {}
    for kind, tid in ids:
        rk = h2.rank(tid, 12)
        r = rk[0]
        fig, off = h2.render_pick(tid, r)
        name = tid.replace('/', '__')
        cv2.imwrite(os.path.join(outdir, name + '.png'), fig)
        st = status(r['D'])
        picks[tid] = dict(kind=kind, pick=r['src'], mirror=r['mirror'], D=round(r['D'], 3), status=st,
                          terms=r['terms'], iou=r['iou'], scale=round(r['s'], 4), offset_in_target_px=[int(off[0]), int(off[1])],
                          runners_up=[dict(src=x['src'], mirror=x['mirror'], D=round(x['D'], 3)) for x in rk[1:5]])
        lab = [f"{kind}: {tid.replace('.main-poses','')}  |  pick: {r['src'].replace('.main-poses','')}{' (mirrored)' if r['mirror'] else ''}",
               f"distance D={r['D']:.2f} (pose {r['terms']['pose']:.2f}, silhouette IoU {r['iou']:.2f})  -> {st.upper()}"]
        rows.append(h2.pair_panel(tid, fig, off, lab, H=560))
    W = max(p.shape[1] for p in rows)
    rows = [np.pad(p, ((0, 0), (0, W - p.shape[1]), (0, 0)), constant_values=255) for p in rows]
    while len(rows) % cols: rows.append(np.full_like(rows[0], 255))
    grid = np.vstack([np.hstack([np.pad(p, ((4,4),(4,4),(0,0)), constant_values=200) for p in rows[i:i+cols]]) for i in range(0, len(rows), cols)])
    cv2.imwrite(os.path.join(outdir, sheetname), grid, [cv2.IMWRITE_JPEG_QUALITY, 86])
    json.dump(picks, open(os.path.join(outdir, 'picks.json'), 'w'), indent=1)
    return picks

if __name__ == '__main__':
    P = [(p['kind'], p['id']) for p in h2.TEST['poses']]
    if sys.argv[1] == 'kill':
        ids = [x for x in P if x[0] in ('front stand', 'crouch', 'seated profile with cup')]
        out = run(ids, os.path.join(H2, 'kill'), 'sheet.jpg', 3)
    else:
        out = run(P, os.path.join(H2, 'out'), 'sheet.jpg', 3)
    for k, v in out.items(): print(v['kind'], '->', v['pick'], v['mirror'], v['D'], v['status'])
