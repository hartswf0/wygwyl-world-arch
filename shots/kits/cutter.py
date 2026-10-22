#!/usr/bin/env python3
"""Cut the poem kit sheets apart into named, transparent parts and take stock of them.

STATUS: first pass, masks by colour threshold. Kept for its OCR labelling, ruled-panel and pose-figure naming;
the masks are to be replaced by SAM 2.1 cuts (point prompts) that follow each card's true edge.

    python3 shots/kits/cutter.py                 # every unique sheet in packs/poem_NN -> cut/
    python3 shots/kits/cutter.py SHEET.png ...   # just these (for checking)

Each sheet is white ground with detached cards and a label under every card. Per sheet:
  1. Tesseract reads every word; words are taken out of the picture and kept as labels.
  2. What is left and not white is the cards; holes inside a card are filled (white paint stays).
  3. Each card gets the label line just under it (the sheet convention), else just over it.
  4. Framed panels (pose grids, "reference only" proofs) are recognised by their thin dark frame:
     pose panels yield the figure inside, named by the panel title ("04.2 KNEEL HOLLOW");
     reference panels are kept as references, not parts.
  5. Brass brads / eyelets are found (the pivots); the topmost is the part's suggested pivot.
Parts are written as WebP with alpha to cut/<sheet id>/<slug>.webp; cut/catalog.json lists every
sheet, its poems, its title and its parts (label, code, kind, bbox, size, brads, pivot).
"""
import glob, hashlib, json, os, re, sys
import numpy as np
import cv2
import pytesseract
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
PACKS = os.path.join(HERE, 'packs')
OUT = os.path.join(HERE, 'cut')
CODE = re.compile(r'\b(\d{2}\.\d)\b')                      # a scene number: 04.2


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:48] or 'part'


def words(rgb):
    """Every confidently read word with its box (Tesseract, sparse text: labels sit anywhere)."""
    big = cv2.resize(rgb, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)   # labels are small: read at 2x
    d = pytesseract.image_to_data(big, config='--psm 11', output_type=pytesseract.Output.DICT)
    out = []
    for i, t in enumerate(d['text']):
        t = t.strip()
        if t and float(d['conf'][i]) > 50 and d['height'][i] < 180 and re.search(r'[A-Za-z0-9]', t):
            out.append({'t': t, 'x': d['left'][i] // 2, 'y': d['top'][i] // 2, 'w': d['width'][i] // 2, 'h': d['height'][i] // 2})
    return out


def lines(ws):
    """Group words into lines (same baseline, close in x)."""
    ws = sorted(ws, key=lambda w: (w['y'] + w['h'] / 2, w['x']))
    L = []
    for w in ws:
        cy = w['y'] + w['h'] / 2
        for ln in L:
            if abs(ln['cy'] - cy) < max(ln['h'], w['h']) * .6 and -ln['h'] < w['x'] - ln['x1'] < 1.4 * ln['h']:
                ln['w'].append(w); ln['x1'] = max(ln['x1'], w['x'] + w['w']); ln['x0'] = min(ln['x0'], w['x'])
                ln['y0'] = min(ln['y0'], w['y']); ln['y1'] = max(ln['y1'], w['y'] + w['h'])
                break
        else:
            L.append({'w': [w], 'cy': cy, 'h': w['h'], 'x0': w['x'], 'x1': w['x'] + w['w'], 'y0': w['y'], 'y1': w['y'] + w['h']})
    for ln in L:
        ln['text'] = ' '.join(w['t'] for w in sorted(ln['w'], key=lambda w: w['x']))
    return L


def brads(rgb):
    """Brass brads and eyelets: small circles with a warm rim."""
    g = cv2.GaussianBlur(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), (5, 5), 1.5)
    c = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, dp=1.2, minDist=14, param1=60, param2=24, minRadius=4, maxRadius=22)
    out = []
    for x, y, r in (np.round(c[0]).astype(int) if c is not None else []):
        ring = rgb[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].reshape(-1, 3).astype(int)
        if len(ring) and (ring[:, 0] - ring[:, 2]).mean() > 25 and ring[:, 0].mean() > 90:
            if all(np.hypot(x - b[0], y - b[1]) > 10 for b in out):
                out.append((int(x), int(y), int(r)))
    return out


def panels(fg):
    """Rectangles ruled by long thin lines (pose grids, reference-only proof boxes)."""
    m = fg.astype(np.uint8)
    H, W = m.shape
    op = lambda k: cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, k))
    # a rule is long one way and thin the other: black fabric is long but also thick, so it drops out
    hl = op((max(60, W // 8), 1)) & (1 - op((1, 9)))
    vl = op((1, max(60, H // 8))) & (1 - op((9, 1)))
    hl = cv2.morphologyEx(hl, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(60, W // 8), 1)))
    vl = cv2.morphologyEx(vl, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(60, H // 8))))
    grid = ndi.binary_dilation((hl | vl) > 0, iterations=2)
    lab, n = ndi.label(~grid)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        ys, xs = sl
        w, h = xs.stop - xs.start, ys.stop - ys.start
        # a cell enclosed by rules: not touching the sheet edge, and big enough to hold a figure
        if xs.start > 2 and ys.start > 2 and xs.stop < W - 2 and ys.stop < H - 2 and w > 110 and h > 110 and (lab[sl] == i).mean() > .9:
            out.append((xs.start, ys.start, w, h))
    return out, grid


def framed(sub_mask, filled, box):
    """A panel: its outline is a thin rectangle and most of its inside was white before filling."""
    x, y, w, h = box
    if w < 120 or h < 120:
        return False
    ink = sub_mask.sum() / max(1, filled.sum())
    edge = np.concatenate([sub_mask[:3].ravel(), sub_mask[-3:].ravel(), sub_mask[:, :3].ravel(), sub_mask[:, -3:].ravel()])
    return ink < .45 and edge.mean() > .55


def cut_sheet(path, sheet_id, outdir):
    im = Image.open(path).convert('RGB')
    rgb = np.array(im)
    H, W = rgb.shape[:2]
    paper = rgb.min(2) > 225
    ws = []
    for w in words(rgb):                                # a label sits on paper: its surround is white
        x0, y0, x1, y1 = max(0, w['x'] - 6), max(0, w['y'] - 6), min(W, w['x'] + w['w'] + 6), min(H, w['y'] + w['h'] + 6)
        ring = np.concatenate([paper[y0:y0 + 3, x0:x1].ravel(), paper[y1 - 3:y1, x0:x1].ravel(), paper[y0:y1, x0:x0 + 3].ravel(), paper[y0:y1, x1 - 3:x1].ravel()])
        if ring.mean() > .85:
            ws.append(w)
    L = lines(ws)
    # foreground: not white-ish paper (allow faint grey shadows to drop out)
    mx, mn = rgb.max(2).astype(int), rgb.min(2).astype(int)
    fg = ~((mn > 232) | ((mn > 200) & (mx - mn < 14)))
    textmask = np.zeros_like(fg)
    for w in ws:
        textmask[max(0, w['y'] - 3):w['y'] + w['h'] + 3, max(0, w['x'] - 3):w['x'] + w['w'] + 3] = True
    fg_parts = fg & ~textmask
    cells, grid = panels(rgb.max(2) < 95)                  # rules are thin and near-black; card edges are kraft brown
    cells = [c for c in cells if fg[c[1]:c[1] + c[3], c[0]:c[0] + c[2]].mean() < .55]   # a panel is mostly white paper
    fg_parts &= ~grid
    fg_parts = ndi.binary_opening(fg_parts, iterations=1)
    pose_sheet = bool(re.search(r'pose', os.path.basename(path)))
    incell = np.zeros_like(fg)
    for (x, y, w, h) in cells:
        incell[y:y + h, x:x + w] = True
    lab, n = ndi.label(ndi.binary_closing(fg_parts & ~incell, iterations=2))
    title = ''
    tops = [ln for ln in L if ln['y0'] < H * .09]
    if tops:
        t = max(tops, key=lambda ln: ln['h'] * len(ln['text']))
        title = t['text']
    parts, refs = [], []
    used_lines = set()
    for (x, y, w, h) in cells:
        top = [o for o in ws if x - 6 < o['x'] < x + w and y - 6 < o['y'] < y + max(44, h * .14)]
        if top:
            y0 = min(o['y'] for o in top)
            top = sorted([o for o in top if o['y'] < y0 + 1.5 * max(o['h'] for o in top)], key=lambda o: o['x'])
        name = ' '.join(o['t'] for o in top)
        inner = fg_parts[y:y + h, x:x + w]
        ilab, k = ndi.label(ndi.binary_closing(inner, iterations=3))
        fig = None
        if k:
            sizes = ndi.sum(np.ones_like(ilab), ilab, range(1, k + 1))
            big = [j + 1 for j, sz in enumerate(sizes) if sz > .08 * sizes.max() and sz > 1500]
            fig = np.isin(ilab, big)
        if pose_sheet and fig is not None and fig.sum() > 3000:
            # each figure in the panel (04.5 shows two): the big blobs, small ones (hands, arrows) join the nearest
            figs = [j + 1 for j, sz in enumerate(sizes) if sz > .35 * sizes.max()]
            for q, fj in enumerate(figs):
                one = ilab == fj
                for j in [j + 1 for j, sz in enumerate(sizes) if .08 * sizes.max() < sz <= .35 * sizes.max() and sz > 1500]:
                    cy, cx = ndi.center_of_mass(ilab == j)
                    near = min(figs, key=lambda f: np.hypot(*(np.array(ndi.center_of_mass(ilab == f)) - (cy, cx))))
                    if near == fj:
                        one |= ilab == j
                fy, fx = np.where(one)
                bx0, by0, bx1, by1 = fx.min(), fy.min(), fx.max() + 1, fy.max() + 1
                m = ndi.binary_fill_holes(ndi.binary_closing(one[by0:by1, bx0:bx1], iterations=2))
                parts.append({'bbox': [int(x + bx0), int(y + by0), int(bx1 - bx0), int(by1 - by0)], 'kind': 'pose',
                              'label': name + (f' ({q + 1})' if len(figs) > 1 else ''), 'mask': m, 'box': (x + bx0, y + by0, bx1 - bx0, by1 - by0)})
        else:
            refs.append({'bbox': [int(x), int(y), int(w), int(h)], 'label': name})
    objs = ndi.find_objects(lab)
    for i, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        ys, xs = sl
        x, y, w, h = xs.start, ys.start, xs.stop - xs.start, ys.stop - ys.start
        comp = lab[sl] == i
        area = int(comp.sum())
        if area < 900 or w < 22 or h < 22:
            continue
        px = rgb[sl][comp]
        if (h < 46 or area < 5000) and (px.max(1) < 70).mean() > .5:
            continue                                  # an unread label: near-black strokes
        filled = ndi.binary_fill_holes(comp)
        is_panel = framed(comp, filled, (x, y, w, h))
        entry = {'bbox': [int(x), int(y), int(w), int(h)]}
        if is_panel:
            # inside the frame: the figure (largest blob), named by the panel's title line
            inner = fg_parts[y + 8:y + h - 8, x + 8:x + w - 8]
            ilab, k = ndi.label(ndi.binary_closing(inner, iterations=2))
            heads = [ln for ln in L if x < ln['x0'] < x + w * .7 and y < ln['y0'] < y + h * .2]
            name = ' / '.join(ln['text'] for ln in sorted(heads, key=lambda ln: ln['y0'])[:2])
            if k:
                sizes = ndi.sum(np.ones_like(ilab), ilab, range(1, k + 1))
                big = [j + 1 for j, s in enumerate(sizes) if s > .12 * sizes.max()]
                fig = np.isin(ilab, big)
                fy, fx = np.where(fig)
                if len(fy) > 2000:
                    bx0, by0, bx1, by1 = fx.min(), fy.min(), fx.max() + 1, fy.max() + 1
                    m = ndi.binary_fill_holes(fig[by0:by1, bx0:bx1])
                    parts.append(dict(entry, kind='pose', label=name, mask=m, box=(x + 8 + bx0, y + 8 + by0, bx1 - bx0, by1 - by0)))
                    continue
            refs.append(dict(entry, label=name))
            continue
        # the label: the words in the strip just under the card (two lines at most), else just over it
        def strip(y0, y1):
            got = [o for o in ws if x - 18 < o['x'] + o['w'] / 2 < x + w + 18 and y0 <= o['y'] <= y1]
            if not got:
                return ''
            first = min(g['y'] for g in got)
            got = [g for g in got if g['y'] < first + 2.4 * max(g['h'] for g in got)]
            got.sort(key=lambda g: (round((g['y'] - first) / max(8, g['h'] * .8)), g['x']))
            return ' '.join(g['t'] for g in got)
        label = strip(y + h - 6, y + h + 64) or strip(y - 64, y - 4)
        parts.append(dict(entry, kind='card', label=label, mask=filled, box=(x, y, w, h)))
    # write
    os.makedirs(outdir, exist_ok=True)
    out, seen = [], {}
    parts.sort(key=lambda p: (p['box'][1] // 120, p['box'][0]))
    for p in parts:
        x, y, w, h = p['box']
        m = p['mask']
        crop = rgb[y:y + h, x:x + w]
        a = (ndi.binary_dilation(m, iterations=1) * 255).astype(np.uint8)
        a = cv2.GaussianBlur(a, (3, 3), 0)
        rgba = np.dstack([crop, a])
        name = p['label'] or f"part {len(out) + 1}"
        code = CODE.search(name)
        s = slug(name)
        seen[s] = seen.get(s, 0) + 1
        if seen[s] > 1:
            s = f'{s}-{seen[s]}'
        Image.fromarray(rgba, 'RGBA').save(os.path.join(outdir, s + '.webp'), quality=86, method=5)
        bs = brads(crop)
        pv = min(bs, key=lambda b: b[1]) if bs else None
        out.append({'id': f'{sheet_id}/{s}', 'file': f'{sheet_id}/{s}.webp', 'label': p['label'], 'kind': p['kind'],
                    'scene': code.group(1) if code else None, 'bbox': [int(x), int(y), int(w), int(h)],
                    'brads': [[b[0], b[1]] for b in bs], 'pivot': [pv[0], pv[1]] if pv else None})
    notes = [ln['text'] for j, ln in enumerate(L) if j not in used_lines and ln['y0'] > H * .09 and len(ln['text']) > 12]
    return {'title': title, 'size': [W, H], 'parts': out, 'refs': [{'bbox': r['bbox'], 'label': r['label']} for r in refs], 'notes': notes[:12]}


def sheets():
    """Unique sheets across the poem packs (by hash), with every poem and folder each appears in."""
    S = {}
    for n in range(1, 15):
        d = os.path.join(PACKS, f'poem_{n:02d}')
        m = json.load(open(os.path.join(d, 'manifest.json')))
        for s in m['sheets']:
            e = S.setdefault(s['sha256'], {'id': s['id'], 'path': os.path.join(d, s['file']), 'poems': [], 'folder': s['file'].split('/')[0],
                                           'category': s.get('category') or s.get('role') or s['file'].split('/')[0]})
            e['poems'].append(f'{n:02d}')
    return list(S.values())


def main():
    args = sys.argv[1:]
    todo = sheets()
    if args:
        todo = [s for s in todo if any(os.path.abspath(a) == os.path.abspath(s['path']) or a in s['id'] for a in args)]
    cat_path = os.path.join(OUT, 'catalog.json')
    cat = json.load(open(cat_path)) if os.path.exists(cat_path) else {'sheets': {}}
    for k, s in enumerate(todo, 1):
        r = cut_sheet(s['path'], s['id'], os.path.join(OUT, s['id']))
        cat['sheets'][s['id']] = {k2: s[k2] for k2 in ('poems', 'folder', 'category')} | {'path': os.path.relpath(s['path'], HERE)} | r
        print(f"[{k}/{len(todo)}] {s['id']}: {len(r['parts'])} parts, {len(r['refs'])} refs · {r['title'][:50]}", flush=True)
    cat['totals'] = {'sheets': len(cat['sheets']), 'parts': sum(len(v['parts']) for v in cat['sheets'].values())}
    json.dump(cat, open(cat_path, 'w'), indent=1)
    print(cat['totals'])


if __name__ == '__main__':
    main()
