"""SPACE audit sheets: render chosen parts with their stage decision drawn on them.

  red line    contact line (stands / rests / inset / lies_flat: lowest opaque row, x extent of the base band)
  blue line   hang line (top opaque row)
  green bar   an edge marked tileable-straight (left / right); thick green frame = repeat
  text        plane / contact / view / size (scale_src) / conflict ratio / doubt
python3 contact.py            -> audit/*.jpg
"""
import json, os, sys
import numpy as np, cv2
cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
SP = os.path.join(ROOT, 'shots/scion2/setpieces')
CELL, TXT, COLS = 230, 66, 7


def cell(pid, v, files):
    px = cv2.imread(os.path.join(CUT, files[pid]), cv2.IMREAD_UNCHANGED)
    c = np.full((CELL + TXT, CELL, 3), (226, 232, 235), np.uint8)
    if px is None:
        return c
    if px.shape[2] == 3:
        px = np.dstack([px, np.full(px.shape[:2], 255, np.uint8)])
    H, W = px.shape[:2]
    k = (CELL - 10) / max(H, W)
    nw, nh = max(1, int(W * k)), max(1, int(H * k))
    im = cv2.resize(px, (nw, nh), interpolation=cv2.INTER_AREA).astype(np.float32)
    a = im[:, :, 3:] / 255.
    ox, oy = (CELL - nw) // 2, (CELL - nh) // 2
    bg = c[oy:oy + nh, ox:ox + nw].astype(np.float32)
    # checker under transparent area so holes show
    yy, xx = np.mgrid[0:nh, 0:nw]
    chk = ((yy // 8 + xx // 8) % 2 == 0)[..., None]
    bg = np.where(chk, bg, bg * 0.88)
    c[oy:oy + nh, ox:ox + nw] = (im[:, :, :3] * a + bg * (1 - a)).astype(np.uint8)
    ct = v['contact']
    def X(x): return int(ox + x * k)
    def Y(y): return int(oy + y * k)
    if 'y_px' in ct:
        col = (200, 60, 30) if ct['type'] == 'hangs' else (30, 30, 220)
        cv2.line(c, (X(ct['x0_px']), Y(ct['y_px'])), (X(ct['x1_px']), Y(ct['y_px'])), col, 3)
    tl = v['tile']
    if tl['left']:
        cv2.line(c, (ox - 3, oy), (ox - 3, oy + nh), (40, 170, 40), 3)
    if tl['right']:
        cv2.line(c, (ox + nw + 2, oy), (ox + nw + 2, oy + nh), (40, 170, 40), 3)
    if tl['repeat']:
        cv2.rectangle(c, (1, 1), (CELL - 2, CELL - 2), (40, 170, 40), 2)
    sz = v['size_cm']
    s = '%sx%s' % (int(sz['w']), int(sz['h'])) if sz else '-'
    lines = [pid.split('/')[1][:34],
             '%s | %s | %s' % (v['plane'].replace('_', ' ').replace('foreground occluder', 'FG occl'), ct['type'], v['view']),
             'wxh %s cm (%s)' % (s, v['scale_src'].replace('registry:', 'reg:')[:16]),
             ('CONFLICT x%.2f ' % v['scale_conflict']['ratio'] if v.get('scale_conflict') else '') + (v['doubt'][0][:30] if v.get('doubt') else '')]
    for i, l in enumerate(lines):
        cv2.putText(c, l, (3, CELL + 13 + i * 14), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (20, 20, 20) if i != 3 else (0, 0, 190), 1, cv2.LINE_AA)
    return c


def sheet(ids, parts, files, path, title):
    ids = ids[:COLS * 8]
    if not ids:
        return
    cells = [cell(i, parts[i], files) for i in ids]
    while len(cells) % COLS:
        cells.append(np.full_like(cells[0], 255))
    rows = [np.hstack(cells[i:i + COLS]) for i in range(0, len(cells), COLS)]
    img = np.vstack(rows)
    head = np.full((28, img.shape[1], 3), 255, np.uint8)
    cv2.putText(head, title, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.imwrite(path, np.vstack([head, img]), [cv2.IMWRITE_JPEG_QUALITY, 82])
    print(path, len(ids))


if __name__ == '__main__':
    D = json.load(open(os.path.join(SP, 'space.json')))['parts']
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    files = {p['id']: p['file'] for s in cat.values() for p in s['parts']}
    P = {k: v for k, v in D.items() if 'plane' in v}
    od = os.path.join(HERE, 'audit'); os.makedirs(od, exist_ok=True)
    rng = np.random.default_rng(7)
    def pick(f, n=56, key=None, rand=False):
        ids = [k for k, v in P.items() if f(v)]
        if key:
            ids.sort(key=lambda k: key(P[k]))
        elif rand:
            rng.shuffle(ids)
        return ids[:n], len(ids)
    sets = {
        'conflict_worst': (lambda v: v.get('scale_conflict'), lambda v: -abs(np.log(v['scale_conflict']['ratio'])), 'scale conflicts, largest first'),
        'doubt': (lambda v: v.get('doubt'), None, 'parts with a doubt note'),
        'fg_occluder': (lambda v: v['plane'] == 'foreground_occluder', None, 'foreground occluders (all)'),
        'far_backdrop': (lambda v: v['plane'] == 'far_backdrop', None, 'far backdrop (random)'),
        'ground': (lambda v: v['plane'] == 'ground_plane', None, 'ground plane (random)'),
        'hangs_inset': (lambda v: v['contact']['type'] in ('hangs', 'inset'), None, 'hangs / inset'),
        'view_nonfront': (lambda v: v['view'] in ('3/4', 'side', 'perspective', 'top'), None, 'view 3/4 / side / perspective / top (random)'),
        'tile_repeat': (lambda v: v['tile']['repeat'], None, 'tile repeat (random)'),
        'near_rests': (lambda v: v['contact']['type'] == 'rests', None, 'rests / pickable props (random)'),
        'mid_stands': (lambda v: v['plane'] == 'mid_set' and v['contact']['type'] == 'stands', None, 'mid set standing (random)'),
        'overlay': (lambda v: v['plane'] == 'overlay_fx', None, 'overlay fx (random)'),
        'sheet_median': (lambda v: v['scale_src'] == 'sheet_median', None, 'sized by the sheet median only (random)'),
    }
    only = sys.argv[1:] or list(sets)
    for name in only:
        f, key, title = sets[name]
        ids, n = pick(f, key=key, rand=key is None)
        sheet(ids, P, files, os.path.join(od, name + '.jpg'), '%s: showing %d of %d' % (title, len(ids), n))
