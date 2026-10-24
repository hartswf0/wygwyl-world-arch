"""repair audit: v1 vs v2 measurements on the rendered stills + contact sheets of the doubtful cases.
    python3 repair/audit.py   -> proof/repair_audit.json, proof/repair_compare.jpg, proof/repair_hard_cases.jpg"""
import json, os, subprocess, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import palette
P = os.path.join(os.path.dirname(HERE), 'proof')
SC = ['p07_bar', 'p09_parlour', 'p01_doorway']
FONT = cv2.FONT_HERSHEY_SIMPLEX


def frame(mp4, f):
    out = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', mp4, '-vf', f'select=eq(n\\,{f})', '-vframes', '1', '-f', 'image2pipe',
                          '-vcodec', 'png', '-'], capture_output=True).stdout
    return cv2.imdecode(np.frombuffer(out, np.uint8), cv2.IMREAD_COLOR)


def edge_bands(im):
    """mean |gradient| in the 15 px bands at the left/right frame edges vs the frame mean (a card border shows as a high-contrast strip)"""
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0)) + np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1))
    m = gx[:560].mean()
    return {'left_15px_over_mean': round(float(gx[:560, :15].mean() / m), 2), 'right_15px_over_mean': round(float(gx[:560, -15:].mean() / m), 2)}


res = {}
for s in SC:
    r = {}
    for v, suf in (('v1', '_v1'), ('v2', '')):
        im = cv2.imread(os.path.join(P, s + suf + '.jpg'))
        band = im[604:718]
        r[v] = {'floor_band_periodicity_x_still': palette.periodicity(band, 1, 20 / 1280, 0.5), **edge_bands(im)}
    res[s] = r
json.dump(res, open(os.path.join(P, 'repair_audit.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))

# side by side stills
rows = []
for s in SC:
    a = cv2.resize(cv2.imread(os.path.join(P, s + '_v1.jpg')), (640, 360))
    b = cv2.resize(cv2.imread(os.path.join(P, s + '.jpg')), (640, 360))
    for im, t in ((a, s + ' v1'), (b, s + ' v2 (repair)')):
        cv2.rectangle(im, (0, 0), (260, 24), (255, 255, 255), -1)
        cv2.putText(im, t, (6, 17), FONT, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    rows.append(np.hstack([a, b]))
cv2.imwrite(os.path.join(P, 'repair_compare.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 86])

# hard cases: crops at full res
cases = [('p01_doorway', [18, 20, 22, 24, 26, 30], (380, 60, 360, 560), 'p01 entrance frames (v2)'),
         ('p01_doorway_v1', [18, 20, 22, 24, 26, 30], (380, 60, 360, 560), 'p01 entrance frames (v1)'),
         ('p09_parlour', [54, 56, 57, 58, 59, 60], (560, 150, 520, 520), 'p09 stand->sit (v2)'),
         ('p07_bar', [40, 44, 46, 74, 76, 80], (700, 120, 400, 300), 'p07 bartender pose swaps (v2, halo)')]
sheet = []
for name, fr, (x, y, w, h), title in cases:
    mp4 = os.path.join(P, name + '.mp4')
    th = []
    for f in fr:
        im = frame(mp4, f)
        c = cv2.resize(im[y:y + h, x:x + w], (240, int(240 * h / w)))
        cv2.putText(c, f'f{f}', (4, 16), FONT, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        th.append(c)
    hh = max(t.shape[0] for t in th)
    th = [cv2.copyMakeBorder(t, 0, hh - t.shape[0], 0, 2, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in th]
    row = np.hstack(th)
    head = np.full((26, row.shape[1], 3), 255, np.uint8)
    cv2.putText(head, title, (6, 18), FONT, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
    sheet.append(np.vstack([head, row]))
wmax = max(r.shape[1] for r in sheet)
sheet = [cv2.copyMakeBorder(r, 0, 0, 0, wmax - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in sheet]
cv2.imwrite(os.path.join(P, 'repair_hard_cases.jpg'), np.vstack(sheet), [cv2.IMWRITE_JPEG_QUALITY, 86])
