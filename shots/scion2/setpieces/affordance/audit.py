"""Contact sheets for auditing affordance.json: each tile = the part on a checkerboard with its geometry drawn.
Colours: seat green (back side arrow), surface blue (rest line dashed), grip red dot + up arrow, aperture magenta
rects (leaf: magenta outline + hinge bar), lean orange, occluder cyan line + hatched hidden zone, stand-on yellow.
usage: python3 audit.py [kind|doubtful|all] ...
"""
import json, os, sys
import numpy as np, cv2

cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
OUT = os.path.join(HERE, 'audit')
COL = {'seat': (60, 200, 60), 'surface': (230, 120, 30), 'grip': (40, 40, 230), 'aperture': (220, 40, 220),
       'lean': (0, 140, 255), 'occluder': (220, 220, 0), 'stand_on': (0, 220, 255)}
TILE = 300


def checker(h, w):
    y, x = np.mgrid[0:h, 0:w]
    c = (((x // 12) + (y // 12)) % 2).astype(np.uint8)
    return np.where(c[..., None] == 1, 205, 235).astype(np.uint8).repeat(3, 2)


def draw(pid, rec, kinds=None):
    p = CUT + '/' + pid.split('/')[0] + '/' + pid.split('/')[1] + '.webp'
    cat_file = rec.get('_file')
    im = cv2.imread(os.path.join(CUT, cat_file) if cat_file else p, cv2.IMREAD_UNCHANGED)
    h, w = im.shape[:2]
    k = (TILE - 50) / max(h, w)
    sw, sh = max(1, int(w * k)), max(1, int(h * k))
    im = cv2.resize(im, (sw, sh), interpolation=cv2.INTER_AREA)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    a = im[..., 3:] / 255.
    bg = checker(sh, sw)
    comp = (im[..., :3] * a + bg * (1 - a)).astype(np.uint8)
    tile = np.full((TILE, TILE, 3), 250, np.uint8)
    ox, oy = (TILE - sw) // 2, 8
    tile[oy:oy + sh, ox:ox + sw] = comp

    def P(x, y):
        return int(ox + x * k), int(oy + y * k)
    for af in rec.get('affordances', []):
        kd = af['kind']
        if kinds and kd not in kinds:
            continue
        g, c = af['geometry'], COL[kd]
        if kd == 'seat':
            x0, x1 = g['x_range']
            cv2.line(tile, P(x0, g['seat_y']), P(x1, g['seat_y']), c, 3)
            b = g.get('back')
            mx = (x0 + x1) / 2
            if b in ('left', 'right'):
                bx = g.get('back_x', x0 if b == 'left' else x1)
                cv2.arrowedLine(tile, P(mx, g['seat_y'] - 4 / k), P(bx, g['seat_y'] - 4 / k), c, 2, tipLength=0.25)
            elif b == 'behind':
                cv2.putText(tile, 'B', P(mx, g['seat_y'] - 8 / k), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        elif kd in ('surface', 'stand_on'):
            y = g.get('surface_y', g.get('top_y'))
            ry = g.get('rest_y', g.get('foot_y'))
            x0, x1 = g['x_range']
            cv2.line(tile, P(x0, y), P(x1, y), c, 2)
            if ry != y:
                for xx in range(int(P(x0, 0)[0]), int(P(x1, 0)[0]), 10):
                    cv2.line(tile, (xx, P(0, ry)[1]), (xx + 5, P(0, ry)[1]), c, 2)
        elif kd == 'grip':
            x, y = g['point']
            cv2.circle(tile, P(x, y), 6, c, -1)
            ux, uy = g['up']
            px, py = P(x, y)
            cv2.arrowedLine(tile, (px, py), (int(px + ux * 40), int(py + uy * 40)), c, 2, tipLength=0.3)
        elif kd == 'aperture':
            if g['role'] == 'leaf':
                x, y, ww, hh = g['rect']
                cv2.rectangle(tile, P(x, y), P(x + ww, y + hh), c, 2)
                if g.get('hinge_side'):
                    hx = x if g['hinge_side'] == 'left' else x + ww
                    cv2.line(tile, P(hx, y), P(hx, y + hh), c, 6)
            else:
                for o in g['openings']:
                    x, y, ww, hh = o['rect']
                    cv2.rectangle(tile, P(x, y), P(x + ww, y + hh), c, 2 if o['type'] == 'door' else 1)
                    cv2.putText(tile, 'D' if o['type'] == 'door' else ('W' if o['type'] == 'window' else 'F'),
                                P(x + 2, y + hh / 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 2)
        elif kd == 'lean':
            if g.get('edge') == 'top':
                x0, x1 = g['x_range']
                cv2.line(tile, P(x0, g['y']), P(x1, g['y']), c, 3)
            else:
                for e in g['edges']:
                    if e['y_range']:
                        cv2.line(tile, P(e['x'], e['y_range'][0]), P(e['x'], e['y_range'][1]), c, 3)
        elif kd == 'occluder':
            x0, x1 = g['x_range']
            yy = g['hide_y']
            cv2.line(tile, P(x0, yy), P(x1, yy), c, 2)
            for t in range(int(P(0, yy)[1]), int(P(0, g['base_y'])[1]), 8):
                cv2.line(tile, (P(x0, 0)[0], t), (P(x0, 0)[0] + 12, t + 6), c, 1)
    # caption
    cap1 = pid.split('/')[1][:38]
    cap2 = ' '.join('%s%.2f' % (a['kind'][:4], a['confidence']) for a in rec.get('affordances', []))
    cap3 = (rec.get('label') or '')[:40]
    cv2.putText(tile, cap1, (3, TILE - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 0, 0), 1)
    cv2.putText(tile, cap3, (3, TILE - 17), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (90, 30, 30), 1)
    cv2.putText(tile, cap2[:48], (3, TILE - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 0, 160), 1)
    cv2.rectangle(tile, (0, 0), (TILE - 1, TILE - 1), (180, 180, 180), 1)
    return tile


def sheet(items, name, kinds=None, cols=6, maxn=48):
    items = items[:maxn]
    if not items:
        return None
    rows = (len(items) + cols - 1) // cols
    S = np.full((rows * TILE, cols * TILE, 3), 255, np.uint8)
    for i, (pid, rec) in enumerate(items):
        t = draw(pid, rec, kinds)
        r, c = divmod(i, cols)
        S[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE] = t
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + '.jpg')
    cv2.imwrite(path, S, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return path


def main():
    A = json.load(open(os.path.join(ROOT, 'shots/scion2/setpieces/affordance.json')))
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    files = {p['id']: p['file'] for S in cat.values() for p in S['parts']}
    parts = A['parts']
    for pid, r in parts.items():
        r['_file'] = files[pid]
    which = sys.argv[1:] or ['all']
    made = []
    kinds = ['seat', 'surface', 'grip', 'aperture', 'lean', 'occluder', 'stand_on']
    for kd in kinds:
        if 'all' in which or kd in which:
            it = [(pid, r) for pid, r in parts.items() if any(a['kind'] == kd for a in r['affordances'])]
            it.sort(key=lambda x: min(a['confidence'] for a in x[1]['affordances'] if a['kind'] == kd))
            for i in range(0, len(it), 48):
                made.append(sheet(it[i:i + 48], 'kind_%s_%d' % (kd, i // 48 + 1), [kd]))
    if 'all' in which or 'doubtful' in which:
        it = sorted(parts.items(), key=lambda x: -x[1]['doubt'])
        made.append(sheet(it[:48], 'doubtful_top48'))
    print('\n'.join(m for m in made if m))


if __name__ == '__main__':
    main()
