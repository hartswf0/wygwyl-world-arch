"""Measure 'printed lettering / label box' signature on every usable card (measured; used by MERGE rule U10).
achrom = share of opaque px with HSV saturation < 0.12; dark = V < 0.3; pale = V > 0.85; aspect = w/h.
Writes merge/letters.json."""
import json, os, numpy as np, cv2
cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE); ROOT = os.path.abspath(os.path.join(SP, '../../..'))
R = json.load(open(os.path.join(SP, 'registry.json')))['parts']
out = {}
for k, r in R.items():
    if r['kind'] != 'card':
        continue
    im = cv2.imread(os.path.join(ROOT, r['file']), cv2.IMREAD_UNCHANGED)
    if im is None or im.ndim < 3 or im.shape[2] < 4:
        continue
    a = im[:, :, 3] > 128; n = a.sum() or 1
    hsv = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2HSV).astype(float) / 255
    S, V = hsv[..., 1], hsv[..., 2]
    ncc = cv2.connectedComponents(a.astype(np.uint8))[0] - 1
    out[k] = {'achrom': round(float(((S < 0.12) & a).sum() / n), 3), 'dark': round(float(((V < 0.3) & a).sum() / n), 3),
              'pale': round(float(((V > 0.85) & a).sum() / n), 3), 'aspect': round(im.shape[1] / im.shape[0], 2), 'ncc': int(ncc)}
json.dump(out, open(os.path.join(HERE, 'letters.json'), 'w'))
def lettering(v): return v['achrom'] >= 0.85 and v['dark'] >= 0.35 and v['pale'] >= 0.15 and v['aspect'] >= 2
def labelbox(v): return v['achrom'] >= 0.95 and v['pale'] >= 0.4 and 0.01 <= v['dark'] <= 0.3 and v['aspect'] >= 2
for k, v in sorted(out.items()):
    if R[k]['usable'] and (lettering(v) or labelbox(v)):
        print('LET' if lettering(v) else 'BOX', k, v, R[k]['label'][:30], R[k]['category'])
