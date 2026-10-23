"""Coverage map over all 130 main-pose paintings, from the hand catalog: coverage.jpg (posture x view
thumbnails of every usable suited painting) and the tables in coverage.md (counts are filled in here)."""
import sys, os, json, collections, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import h2
H2 = os.path.join(h2.ROOT, 'shots/scion2/h2')
VIEWS = [('front', ['front']), ('3/4 to screen-right', ['3qR']), ('3/4 to screen-left', ['3qL']),
         ('profile R', ['profR']), ('profile L', ['profL']), ('back / back-3/4', ['back', 'back3qR', 'back3qL'])]
CLASSES = ['stand', 'walk', 'lunge', 'dance', 'lean', 'crouch', 'kneel', 'sit', 'lie', 'fall', 'ride']

def table(sel):
    cnt = collections.defaultdict(list)
    for pid, c in h2.C.items():
        if not sel(c): continue
        for vn, vs in VIEWS:
            if c[2] in vs: cnt[(c[3], vn)].append(pid)
    lines = ['| posture | ' + ' | '.join(v for v, _ in VIEWS) + ' | total |', '|---|' + '---|'*(len(VIEWS)+1)]
    for cl in CLASSES:
        row = [len(cnt[(cl, v)]) for v, _ in VIEWS]
        lines.append(f'| {cl} | ' + ' | '.join(str(n) if n else '**0**' for n in row) + f' | {sum(row)} |')
    return '\n'.join(lines), cnt

def main():
    use = collections.Counter((c[1]) for c in h2.C.values())
    cos = collections.Counter((c[0], c[1]) for c in h2.C.values())
    suit = lambda c: c[1] == 'ok' and c[0] in ('track', 'track-disc')
    tsh = lambda c: c[1] == 'ok' and c[0] == 'tshirt'
    t_suit, cnt = table(suit); t_tsh, _ = table(tsh)
    # thumbnail map
    TH = 120; cell_w = 6*TH//2
    rows = []
    for cl in CLASSES:
        cells = []
        for vn, _ in VIEWS:
            c = np.full((TH+18, cell_w, 3), 250, np.uint8); x = 2
            for pid in cnt[(cl, vn)]:
                im = h2.img(pid); s = min((TH-4)/im.shape[0], (cell_w/2-6)/im.shape[1]); w = max(1, int(im.shape[1]*s)); hh = max(1, int(im.shape[0]*s))
                if x + w > cell_w: h2.put_text(c, '+more', (cell_w-48, TH+12), 0.35); break
                c[TH-2-hh:TH-2, x:x+w] = cv2.resize(h2.rgba_on(im, 250), (w, hh), interpolation=cv2.INTER_AREA); x += w + 3
            if not cnt[(cl, vn)]: c[:] = (215, 215, 240)
            h2.put_text(c, f'{len(cnt[(cl, vn)])}', (4, TH+12), 0.4)
            cells.append(np.pad(c, ((1, 1), (1, 1), (0, 0)), constant_values=160))
        lab = np.full((TH+20, 90, 3), 255, np.uint8); h2.put_text(lab, cl, (4, TH//2), 0.55)
        rows.append(np.hstack([lab] + cells))
    head = np.full((26, rows[0].shape[1], 3), 255, np.uint8)
    for i, (vn, _) in enumerate(VIEWS): h2.put_text(head, vn, (94 + i*(cell_w+2), 18), 0.45)
    cv2.imwrite(os.path.join(H2, 'coverage.jpg'), np.vstack([head] + rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
    json.dump(dict(use=use, costume_use={f'{a}/{b}': n for (a, b), n in cos.items()},
                   suit_map={f'{a}|{b}': v for (a, b), v in cnt.items()}), open(os.path.join(H2, 'coverage.json'), 'w'), indent=1)
    print(dict(use)); print(t_suit); print(t_tsh)

if __name__ == '__main__':
    main()
