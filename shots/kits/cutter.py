#!/usr/bin/env python3
"""Cut the poem kit sheets apart into named, transparent parts and take stock of them.

STATUS: first pass, masks by colour threshold. Kept for its OCR labelling, ruled-panel and pose-figure naming;
the masks are to be replaced by SAM 2.1 cuts (point prompts) that follow each card's true edge.

    python3 shots/kits/cutter.py                 # every unique sheet in packs/poem_NN -> cut/
    python3 shots/kits/cutter.py SHEET.png ...   # just these (for checking)
    python3 shots/kits/cutter.py poem=04         # every sheet poem 04 uses

Each sheet is white ground with detached cards and a label under every card. Per sheet:
  1. Tesseract reads every word; words are taken out of the picture and kept as labels.
  2. What is left and not white is the cards; holes inside a card are filled (white paint stays).
  3. Each card gets the label line just under it (the sheet convention), else just over it.
  4. Framed panels (pose grids, "reference only" proofs) are recognised by their thin dark frame:
     pose panels yield the figure inside, named by the panel title ("04.2 KNEEL HOLLOW");
     reference panels are kept as references, not parts.
  5. Brass brads / eyelets are found (the pivots); the topmost is the part's suggested pivot.
  6. A sheet that cuts to nothing (every card inside ruled section boxes, so each box read as one framed
     reference panel) is cut box by box (rescue): each box is cropped inside its rule, padded with paper and
     cut as a sheet of its own; boxes inside boxes are opened in turn. Parts from a box titled ASSEMBLED /
     REFERENCE / NOT CUT are kept with kind 'ref'. Sheets that already gave parts are cut exactly as before.
paper_flood(), render() and rescue() are shared with fix_cut.py (the post-pass: labels, names, reference
flags and in-place re-cuts; see cut/FIXES.md).
Parts are written as WebP with alpha to cut/<sheet id>/<slug>.webp; cut/catalog.json lists every
sheet, its poems, its title and its parts (label, code, kind, bbox, size, brads, pivot).
"""
import glob, hashlib, json, os, re, shutil, sys
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
        if xs.start > 2 and ys.start > 2 and xs.stop < W - 2 and ys.stop < H - 2 and w > 110 and h > 110 and w * h < .6 * W * H and (lab[sl] == i).mean() > .9:
            out.append((xs.start, ys.start, w, h))
    return out, grid


def pose_grid(line):
    """Pose sheets: a grid only where rules span it, rows first (a rule across most of the width), then the
    columns inside each row (a rule down most of that row). Figures' own folds and edges never qualify.
    Returns cells and the rule mask; no spanning rules means no grid at all."""
    m = line.astype(np.uint8)
    H, W = m.shape
    hl = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (W // 6, 1))) & (1 - cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 9))))

    def runs(prof, thr):
        idx = np.where(prof > thr)[0]
        if not len(idx):
            return []
        groups, start = [], idx[0]
        for a, b in zip(idx, idx[1:]):
            if b - a > 3:
                groups.append((start + a) // 2); start = b
        groups.append((start + idx[-1]) // 2)
        return groups
    rows = runs(hl.sum(1), .6 * W)
    if len(rows) < 2:
        return [], np.zeros(line.shape, bool)
    grid = np.zeros(line.shape, bool)
    cells = []
    for y0, y1 in zip(rows, rows[1:]):
        if y1 - y0 < 110:
            continue
        band = m[y0 + 4:y1 - 4]
        vl = cv2.morphologyEx(band, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, int((y1 - y0) * .6))))
        cols = runs(vl.sum(0), .8 * (y1 - y0 - 8))
        for x0, x1 in zip(cols, cols[1:]):
            if x1 - x0 > 110:
                cells.append((int(x0) + 4, int(y0) + 4, int(x1 - x0) - 8, int(y1 - y0) - 8))
        for x in cols:
            grid[y0:y1, max(0, x - 3):x + 4] = True
    for y in rows:
        grid[max(0, y - 3):y + 4] = True
    return cells, grid


def framed(sub_mask, filled, box):
    """A panel: its outline is a thin rectangle and most of its inside was white before filling."""
    x, y, w, h = box
    if w < 120 or h < 120:
        return False
    ink = sub_mask.sum() / max(1, filled.sum())
    edge = np.concatenate([sub_mask[:3].ravel(), sub_mask[-3:].ravel(), sub_mask[:, :3].ravel(), sub_mask[:, -3:].ravel()])
    return ink < .45 and edge.mean() > .55


def paper_flood(rgb):
    """Lab image, each pixel's distance from the paper colour, and the foreground (what a flood from the
    sheet's edge through paper-coloured pixels cannot reach)."""
    LAB = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    rim = np.concatenate([LAB[:4].reshape(-1, 3), LAB[-4:].reshape(-1, 3), LAB[:, :4].reshape(-1, 3), LAB[:, -4:].reshape(-1, 3)])
    dE = np.linalg.norm(LAB - np.median(rim, 0), axis=2)
    # seal hairline gaps in a card's outline first (white robes, white paper props): flood an eroded paper,
    # then grow the flood back only into paper-coloured pixels
    cand = dE < 9
    near, _ = ndi.label(ndi.binary_erosion(cand, iterations=2, border_value=1))
    edge_ids = np.unique(np.concatenate([near[0], near[-1], near[:, 0], near[:, -1]]))
    paper_ = ndi.binary_dilation(np.isin(near, edge_ids[edge_ids > 0]), iterations=3) & cand
    fg = ~paper_
    return LAB, dE, fg


def analyse(rgb, pose_sheet, loose=False):
    """Find the parts on a sheet (or on one ruled section of it, cropped and padded with paper)."""
    H, W = rgb.shape[:2]
    paper = rgb.min(2) > 225
    ws = []
    for w in words(rgb):                                # a label sits on paper: its surround is white
        x0, y0, x1, y1 = max(0, w['x'] - 6), max(0, w['y'] - 6), min(W, w['x'] + w['w'] + 6), min(H, w['y'] + w['h'] + 6)
        ring = np.concatenate([paper[y0:y0 + 3, x0:x1].ravel(), paper[y1 - 3:y1, x0:x1].ravel(), paper[y0:y1, x0:x0 + 3].ravel(), paper[y0:y1, x1 - 3:x1].ravel()])
        if ring.mean() > (.5 if loose else .85):              # loose: a section box's labels may touch a figure's feet
            ws.append(w)
    L = lines(ws)
    # foreground: not white-ish paper (allow faint grey shadows to drop out)
    # the paper is what a flood from the sheet's edge reaches through colours close to the paper's own
    # (Lab distance); every card is what it cannot reach, so the cut follows the card's own edge and any
    # white paint inside a card stays (the prompts guarantee: pure white page, no shadows, nothing touches)
    LAB, dE, fg = paper_flood(rgb)
    ref_y = min([o['y'] for o in ws if re.match(r'REFERENCE', o['t']) and o['y'] > H * .55] or [H])   # the REFERENCE ONLY band (low on the sheet)
    textmask = np.zeros_like(fg)
    for w in ws:
        textmask[max(0, w['y'] - 3):w['y'] + w['h'] + 3, max(0, w['x'] - 3):w['x'] + w['w'] + 3] = True
    fg_parts = fg & ~textmask
    # rules are thin lines: near-black on most sheets; on pose grids any thin line darker than the paper (grey rules)
    if pose_sheet:   # three readings of the rules; keep the one that finds the most panels
        dark = panels(rgb.max(2) < 95)
        # a true panel carries its title in its top band: keep the reading with the most titled panels
        # (an untitled panel means the reading split a real one: it counts against)
        titled = lambda c: sum(1 if any(x < o['x'] < x + w and y - 6 < o['y'] < y + max(44, h * .16) for o in ws) else -1 for (x, y, w, h) in c[0])
        cells, grid = max([dark, panels(dE > 28), pose_grid(dE > 28)], key=titled)
        if not cells:
            grid = np.zeros_like(fg)
    else:
        cells, grid = panels(rgb.max(2) < 95)
    cells = [c for c in cells if (dE[c[1]:c[1] + c[3], c[0]:c[0] + c[2]] < 9).mean() > .45]   # a panel is mostly white paper
    fg_parts &= ~grid
    incell = np.zeros_like(fg)
    for (x, y, w, h) in cells:
        incell[y:y + h, x:x + w] = True
    fg_parts[ref_y - 6:] = False
    lab, n = ndi.label(fg_parts & ~incell)
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
        # a ruled panel is walled off from the sheet's edge: flood its paper from the panel's own border
        Lc = LAB[y:y + h, x:x + w]
        shadow = (Lc[..., 0] > 165) & (np.hypot(Lc[..., 1] - 128, Lc[..., 2] - 128) < 9)   # a pale grey floor shadow is paper here
        nl, _ = ndi.label((dE[y:y + h, x:x + w] < 9) | shadow)
        rid = np.unique(np.concatenate([nl[0], nl[-1], nl[:, 0], nl[:, -1]]))
        inner = ~np.isin(nl, rid[rid > 0]) & ~textmask[y:y + h, x:x + w] & ~grid[y:y + h, x:x + w]
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
        def right():
            got = sorted([o for o in ws if x + w - 4 < o['x'] < x + w + 240 and y - 4 < o['y'] + o['h'] / 2 < y + h + 4], key=lambda o: (o['y'], o['x']))
            return ' '.join(o['t'] for o in got)
        label = strip(y + h - 6, y + h + 64) or right() or strip(y - 64, y - 4)
        parts.append(dict(entry, kind='card', label=label, mask=filled, box=(x, y, w, h)))
    return parts, refs, title, L, used_lines, dE, LAB


SECTION_REF = re.compile(r'ASSEMBL|REFERENCE|NOT CUT|PROOF|COMPOSITE|CHOREOGRAPH', re.I)


def rescue(rgb, refs, pose_sheet, depth=0, inset=7):
    """A sheet that cut to nothing: every card sits inside ruled section boxes, so each box was read as one
    framed reference panel. Cut each box as a sheet of its own (inset past its rule, padded with paper);
    a box that again holds only boxes is opened in turn. Parts in a box titled ASSEMBLED / REFERENCE /
    NOT CUT are kept but marked kind 'ref' (a planner skips them); figures in titled pose panels stay 'pose'."""
    H, W = rgb.shape[:2]
    rim = np.concatenate([rgb[:4].reshape(-1, 3), rgb[-4:].reshape(-1, 3), rgb[:, :4].reshape(-1, 3), rgb[:, -4:].reshape(-1, 3)])
    paper = np.median(rim, 0).astype(np.uint8)
    out, left = [], []
    P, I = 30, inset
    for r in refs:
        x, y, w, h = r['bbox']
        if w < 80 or h < 80 or w * h > .97 * W * H:
            left.append(r); continue
        crop = rgb[y + I:y + h - I, x + I:x + w - I]
        pad = np.empty((crop.shape[0] + 2 * P, crop.shape[1] + 2 * P, 3), np.uint8)
        pad[:] = paper
        pad[P:-P, P:-P] = crop
        ps, rs, _, _, _, dEp, _ = analyse(pad, pose_sheet or bool(SECTION_REF.search(r['label'] or '')), loose=True)
        keep = []
        for p in ps:
            bx, by, bw, bh = p['box']
            m = p['mask']
            edge = np.concatenate([m[:3].ravel(), m[-3:].ravel(), m[:, :3].ravel(), m[:, -3:].ravel()]).mean()
            hollow = (dEp[by:by + bh, bx:bx + bw] < 9).mean()
            if p['kind'] == 'card' and edge > .55 and bw > 80 and bh > 80 and depth < 2:
                rs.append({'bbox': [int(bx), int(by), int(bw), int(bh)], 'label': p['label'], 'frame': True})   # a ruled box joined to what it holds
            elif p['kind'] == 'card' and edge > .55 and hollow > .55 and min(bw, bh) < 70:
                continue                                    # a boxed label or a heading strip: the frame round some words
            else:
                keep.append(p)
        ps = keep
        if rs and depth < 2 and (not ps or any(q.get('frame') for q in rs)):
            more, rs = rescue(pad, rs, pose_sheet, depth + 1, inset)
            ps += more
        ref_box = bool(SECTION_REF.search(r['label'] or ''))
        for p in ps:
            bx, by, bw, bh = p['box']
            gx, gy = int(bx + x + I - P), int(by + y + I - P)
            m = p['mask']
            # keep inside the sheet (the pad is not picture)
            cx0, cy0 = max(0, -gx), max(0, -gy)
            cx1, cy1 = min(bw, W - gx), min(bh, H - gy)
            m = m[cy0:cy1, cx0:cx1]
            gx, gy = gx + cx0, gy + cy0
            kind = 'ref' if ref_box and p['kind'] != 'pose' else p['kind']
            if ref_box and p['kind'] == 'pose' and re.search(r'NOT CUT|REFERENCE ONLY', r['label'] or '', re.I):
                kind = 'ref'
            out.append(dict(p, bbox=[gx, gy, int(m.shape[1]), int(m.shape[0])], box=(gx, gy, m.shape[1], m.shape[0]), mask=m, kind=kind,
                            section=r['label'] or ''))
        for q in rs:
            bx, by, bw, bh = q['bbox']
            left.append(dict(q, bbox=[int(bx + x + I - P), int(by + y + I - P), int(bw), int(bh)]))
    return out, left


def render(rgb, dE, LAB, box, m):
    """A part's RGBA crop (edge matte, paper holes cut out) and its outline path."""
    x, y, w, h = box
    crop = rgb[y:y + h, x:x + w]
    # edge matte from colour contrast: on the outer 2 px the alpha is how far a pixel is from the paper
    # holes: paper showing through inside a card (a knot hole, a socket) is cut out too
    d = dE[y:y + h, x:x + w]
    hl, k = ndi.label(m & (d < 9))
    if k:
        sz = ndi.sum(np.ones_like(hl), hl, range(1, k + 1))
        Lw = LAB[y:y + h, x:x + w, 0]
        # an opening is flat paper; white paint (robes, wings, cream) is shaded: keep it
        holes = [j + 1 for j, z in enumerate(sz) if z > 120 and (z < .04 * m.sum() or (Lw[hl == j + 1].std() < 2.5 and d[hl == j + 1].mean() < 4.5))]
        m = m & ~np.isin(hl, holes)
    core = ndi.binary_erosion(m, iterations=3)
    band = ndi.binary_dilation(m, iterations=1) & ~core
    a = np.where(core, 1.0, np.where(band, np.clip((d - 8) / 26, 0, 1), 0.0))
    rgba = np.dstack([crop, (a * 255).astype(np.uint8)])
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cut = ' '.join('M' + ' L'.join(f'{q[0][0]},{q[0][1]}' for q in cv2.approxPolyDP(c, 1.0, True)) + ' Z' for c in cs if len(c) > 8)
    return rgba, cut


def cut_sheet(path, sheet_id, outdir):
    rgb = np.array(Image.open(path).convert('RGB'))
    H, W = rgb.shape[:2]
    pose_sheet = bool(re.search(r'pose', os.path.basename(path)))
    parts, refs, title, L, used_lines, dE, LAB = analyse(rgb, pose_sheet)
    rescued = False
    if not parts and refs:
        parts, refs = rescue(rgb, refs, pose_sheet or bool(re.search(r'orbit|prayer|argument|choreograph', os.path.basename(path))))
        rescued = bool(parts)
    # write (a re-cut replaces the sheet's folder)
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)
    out, seen = [], {}
    parts.sort(key=lambda p: (p['box'][1] // 120, p['box'][0]))
    for p in parts:
        x, y, w, h = p['box']
        rgba, cut = render(rgb, dE, LAB, p['box'], p['mask'])
        crop = rgb[y:y + h, x:x + w]
        name = p['label'] or f"part {len(out) + 1}"
        code = CODE.search(name)
        s = slug(name)
        seen[s] = seen.get(s, 0) + 1
        if seen[s] > 1:
            s = f'{s}-{seen[s]}'
        Image.fromarray(rgba, 'RGBA').save(os.path.join(outdir, s + '.webp'), quality=86, method=5)
        bs = brads(crop)
        pv = min(bs, key=lambda b: b[1]) if bs else None
        out.append({'id': f'{sheet_id}/{s}', 'file': f'{sheet_id}/{s}.webp', 'label': p['label'], 'kind': p['kind'], 'cut': cut,
                    'scene': code.group(1) if code else None, 'bbox': [int(x), int(y), int(w), int(h)],
                    'brads': [[b[0], b[1]] for b in bs], 'pivot': [pv[0], pv[1]] if pv else None})
        if 'section' in p:
            out[-1]['section'] = p['section']
    notes = [ln['text'] for j, ln in enumerate(L) if j not in used_lines and ln['y0'] > H * .09 and len(ln['text']) > 12]
    res = {'title': title, 'size': [W, H], 'parts': out, 'refs': [{'bbox': r['bbox'], 'label': r['label']} for r in refs], 'notes': notes[:12]}
    if rescued:
        res['rescued'] = 'sections'   # cut box by box (see rescue)
    return res


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


def one(s):
    r = cut_sheet(s['path'], s['id'], os.path.join(OUT, s['id']))
    e = {'id': s['id']} | {k2: s[k2] for k2 in ('poems', 'folder', 'category')} | {'path': os.path.relpath(s['path'], HERE)} | r
    json.dump(e, open(os.path.join(OUT, s['id'], 'sheet.json'), 'w'), indent=1)
    return s['id'], len(r['parts']), len(r['refs']), r['title']


def main():
    args = sys.argv[1:]
    todo = sheets()
    if args:
        todo = [s for s in todo if any(a[5:] in s['poems'] if a.startswith('poem=') else (os.path.abspath(a) == os.path.abspath(s['path']) or a in s['id']) for a in args)]
    os.makedirs(OUT, exist_ok=True)
    # each sheet writes its own entry (cut/<id>/sheet.json), so parallel workers and stopped runs lose nothing;
    # the catalog is the merge of every entry on disk
    import multiprocessing as mp
    os.environ['OMP_THREAD_LIMIT'] = '1'
    with mp.Pool(int(os.environ.get('JOBS', os.cpu_count() or 2))) as pool:
        for k, (sid, np_, nr, title) in enumerate(pool.imap_unordered(one, todo), 1):
            print(f"[{k}/{len(todo)}] {sid}: {np_} parts, {nr} refs · {title[:50]}", flush=True)
    cat_path = os.path.join(OUT, 'catalog.json')
    cat = {'sheets': {}}
    for f in sorted(glob.glob(os.path.join(OUT, '*', 'sheet.json'))):
        e = json.load(open(f))
        cat['sheets'][e.pop('id')] = e
    cat['totals'] = {'sheets': len(cat['sheets']), 'parts': sum(len(v['parts']) for v in cat['sheets'].values())}
    json.dump(cat, open(cat_path, 'w'), indent=1)
    print(cat['totals'])


if __name__ == '__main__':
    main()
