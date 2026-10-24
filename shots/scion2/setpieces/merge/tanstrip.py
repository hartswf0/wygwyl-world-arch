"""Measure 'printed heading on a torn tan paper strip' for every card with aspect >= 2.5.
Writes merge/tanstrip.json {id: {tan, dark, aspect, dark_rows_mid}} (measured). Used by MERGE rule U9."""
import json, os, numpy as np, cv2
cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE); ROOT = os.path.abspath(os.path.join(SP, '../../..'))
H = json.load(open(os.path.join(SP, 'hygiene.json')))['parts']
out = {}
for k, h in H.items():
    if h['kind'] != 'card':
        continue
    w, hh = h['px']
    if w / max(hh, 1) < 2.5:
        continue
    im = cv2.imread(os.path.join(ROOT, 'shots/kits/cut', k + '.webp'), cv2.IMREAD_UNCHANGED)
    if im is None or im.shape[2] < 4:
        continue
    a = im[:, :, 3] > 128
    hsv = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2HSV).astype(float)
    Hh, S, V = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
    n = a.sum() or 1
    tan = ((Hh >= 15) & (Hh <= 50) & (S >= 0.12) & (S <= 0.5) & (V >= 0.65) & a).sum() / n
    dark = ((V < 0.3) & a)
    rows = dark.sum(1); H0 = a.shape[0]
    mid = rows[int(H0 * 0.2):int(H0 * 0.8)].sum() / max(rows.sum(), 1)
    out[k] = {'tan': round(float(tan), 3), 'dark': round(float(dark.sum() / n), 3), 'aspect': round(w / max(hh, 1), 2), 'dark_mid': round(float(mid), 3)}
json.dump(out, open(os.path.join(HERE, 'tanstrip.json'), 'w'), indent=0)
hits = {k: v for k, v in out.items() if v['tan'] >= 0.45 and 0.04 <= v['dark'] <= 0.4 and v['dark_mid'] >= 0.8}
print(len(out), 'measured;', len(hits), 'hits')
for k, v in sorted(hits.items()): print(k, v, H[k]['label'][:30])
