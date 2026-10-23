"""diagnostic: target | top-k picks at the same scale (for my own eyes, not a deliverable)"""
import sys, os, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import h2
tid = sys.argv[1]; out = sys.argv[2]; k = int(sys.argv[3]) if len(sys.argv) > 3 else 4
rs = h2.rank(tid, 40)
seen=set(); picks=[]
for r in rs:
    if r['src'] in seen: continue
    seen.add(r['src']); picks.append(r)
    if len(picks)==k: break
panels=[]
for r in picks:
    fig, off = h2.render_pick(tid, r)
    panels.append(h2.pair_panel(tid, fig, off, [f"{r['src'].replace('.main-poses','')[:40]}{' (mirror)' if r['mirror'] else ''}", f"D={r['D']:.2f} pose={r['terms']['pose']:.2f} iou={r['iou']}"], H=420))
W=max(p.shape[1] for p in panels)
cv2.imwrite(out, np.vstack([np.pad(p,((0,0),(0,W-p.shape[1]),(0,0)),constant_values=255) for p in panels]) if len(panels)<3 else np.hstack([np.pad(p,((0,0),(0,0),(0,0))) for p in panels]))
