#!/usr/bin/env python3
"""Post-pass over the cut parts (shots/kits/cut): better labels, canonical names, reference flags and
in-place re-cuts. It never renames or moves a part: every existing id and file path stays.

    python3 shots/kits/fix_cut.py                # every sheet
    python3 shots/kits/fix_cut.py 02.props.car   # just these sheet ids (substring match)
    JOBS=4 ...                                   # worker processes

Per sheet (cut/<sheet id>/sheet.json is rewritten in place, then catalog.json is the merge of them all):
  1. Section boxes: a 'card' that is really a ruled box holding several cards (thin frame, paper inside)
     is marked kind 'ref' (ref_reason 'section box') and what it holds is cut as NEW parts (added: true,
     split_from: <box id>) with the cutter's own section rescue. A framed panel holding ONE figure is
     re-cut in place to that figure (same file).
  2. Unclip: the cutter took the label words out of the picture before finding cards, so a word box that
     overlapped a card bit a notch out of it. The card's full flood component is restored when doing so
     only fills in the bite (the bbox grows by at most a few px and nothing dark and thin joins).
  3. GrabCut edge refinement for pale cards (the flood's weakest case): accepted only when the new outline
     sits on clearly stronger image edges and the masks mostly agree.
  4. Labels: every sheet re-read at 3x (Tesseract psm 11 + psm 3, cached in cut/_ocr), words grouped into
     label blocks (up to three stacked lines), blocks assigned to cards one-to-one by a cost that prefers
     the sheet convention (just under the card, then right, then above); each assigned block re-read on
     its own crop (psm 7 / psm 6 at 3x) and the higher-confidence reading kept. A card's label is replaced
     when it was empty/garbled, when the new block is a re-read of the same text, or when its old text
     belongs to another card.
  5. Names: OCR tokens corrected against the words of the sheet's prompts (prompts.json), then the label
     snapped to the closest phrase of the prompt when it is a near match -> 'name'.
  6. kind 'ref' (so planners skip them): labels saying REFERENCE / PROOF / ASSEMBLED / COMPOSITE / NOT CUT;
     parts under a REFERENCE ONLY / ASSEMBLED / PROOF band heading low on the sheet; label fragments
     (a part that is printed words); section boxes (1.). 'ref_reason' says which.
The originals are kept on each part ('orig': label, kind, bbox, cut, brads, pivot) and every re-cut image's
first version is kept in cut/_orig/, so a re-run starts from the cutter's output and is repeatable.
A log is written to cut/FIXES.md.
"""
import difflib, glob, gzip, json, os, re, shutil, sys
import numpy as np
import cv2
import pytesseract
from PIL import Image
from scipy import ndimage as ndi
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cutter  # noqa: E402

HERE = cutter.HERE
CUT = cutter.OUT
OCR_DIR = os.path.join(CUT, '_ocr')
ORIG_DIR = os.path.join(CUT, '_orig')
ORIG_KEYS = ('label', 'kind', 'bbox', 'cut', 'brads', 'pivot', 'scene')

REF_LABEL = re.compile(r'\bREFERENCES?\b(?<!SEPARATE REFERENCE)|\bREF\b|PROOFS?\b|\bASSEMBLED\b|COMPOSITE|NOT CUT|'
                       r'\bEXAMPLES?\b|\bPREVIEW\b|\bOVERVIEW\b|\bSTATEPROOF', re.I)
SEPARATE_REF = re.compile(r'separate[ ,]*(?:for )?reference', re.I)
BAND_HEAD = re.compile(r'REFERENCE\s*ONLY|\bASSEMBLED\b|\bPROOFS?\b|COMPOSITE|NOT\s*CUT|STATE\s*PROOF', re.I)
CODEISH = re.compile(r'[A-Za-z]{1,3}[.\-_]?\d{1,3}[A-Za-z]?|\d{1,3}[A-Za-z]?')
GARBLED = lambda s: not re.search(r'[A-Za-z]{3}', s or '') and not ((s or '').split() and all(CODEISH.fullmatch(t.strip('.,;:()')) for t in (s or '').split()))


# ---------------------------------------------------------------------------------------------- prompts
def prompt_texts():
    T = {}
    for f in sorted(glob.glob(os.path.join(cutter.PACKS, 'poem_*', 'prompts.json'))):
        for e in json.load(open(f)):
            txt = ' '.join(v for k, v in e.items() if isinstance(v, str) and k not in ('id', 'file', 'note'))
            T.setdefault(e['id'], [])
            if txt not in T[e['id']]:
                T[e['id']].append(txt)
    return {k: ' \n'.join(v) for k, v in T.items()}


def tokens(s):
    return re.findall(r"[A-Za-z][A-Za-z_'\-]*[A-Za-z]|[A-Za-z]", s)


# --------------------------------------------------------------------------------------------- OCR cache
def ocr(sid, rgb):
    """Words on the whole sheet read at 3x, psm 11 (sparse) and psm 3 (blocks); cached."""
    os.makedirs(OCR_DIR, exist_ok=True)
    f = os.path.join(OCR_DIR, sid + '.json.gz')
    if os.path.exists(f):
        return json.load(gzip.open(f, 'rt'))
    g = cv2.cvtColor(cv2.resize(rgb, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC), cv2.COLOR_RGB2GRAY)
    res = {}
    for psm in (11, 3):
        d = pytesseract.image_to_data(g, config=f'--psm {psm}', output_type=pytesseract.Output.DICT)
        res[str(psm)] = [{'t': t.strip(), 'c': float(c), 'x': l / 3, 'y': tp / 3, 'w': w / 3, 'h': h / 3}
                         for t, c, l, tp, w, h in zip(d['text'], d['conf'], d['left'], d['top'], d['width'], d['height']) if t.strip()]
    json.dump(res, gzip.open(f, 'wt'))
    return res


def sheet_words(o, rgb, dE):
    """Confident words that are printed on paper (black on white), psm 11 and psm 3 merged."""
    H, W = rgb.shape[:2]
    mx = rgb.max(2)
    LAB = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    chroma = np.hypot(LAB[..., 1] - 128, LAB[..., 2] - 128)
    cand = []
    for psm in ('11', '3'):
        for w in o.get(psm, []):
            if w['c'] < 45 or not re.search(r'[A-Za-z0-9]', w['t']) or w['h'] > 70 or w['h'] < 5:
                continue
            x0, y0 = int(max(0, w['x'])), int(max(0, w['y']))
            x1, y1 = int(min(W, w['x'] + w['w'])), int(min(H, w['y'] + w['h']))
            if x1 <= x0 or y1 <= y0:
                continue
            box = (dE[y0:y1, x0:x1] < 14) | (mx[y0:y1, x0:x1] < 110)
            grey = (chroma[y0:y1, x0:x1] < 12).mean() > .85 and (dE[y0:y1, x0:x1] < 12).mean() > .25
            Y0, X0, Y1, X1 = max(0, y0 - 4), max(0, x0 - 4), min(H, y1 + 4), min(W, x1 + 4)
            pp = dE[Y0:Y1, X0:X1] < 12
            ring = np.concatenate([pp[:3].ravel(), pp[-3:].ravel(), pp[:, :3].ravel(), pp[:, -3:].ravel()])
            if box.mean() > .65 and grey and ring.mean() > .55:
                cand.append(dict(w, x=x0, y=y0, w=x1 - x0, h=y1 - y0))
    cand.sort(key=lambda w: -w['c'])
    out = []
    for w in cand:                       # psm 11 and psm 3 read the same words: keep the surer one
        if all(iou(w, v) < .4 for v in out):
            out.append(w)
    return out


def iou(a, b):
    ix = max(0, min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']))
    iy = max(0, min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']))
    i = ix * iy
    return i / max(1, a['w'] * a['h'] + b['w'] * b['h'] - i)


def blocks(ws, H):
    """Label blocks: lines of words, stacked up to three lines when they sit right under each other."""
    L = cutter.lines([{'t': w['t'], 'x': w['x'], 'y': w['y'], 'w': w['w'], 'h': w['h'], 'c': w['c']} for w in ws])
    L = [ln for ln in L if ln['y1'] > H * .075]          # the sheet's title
    for ln in L:
        ln['c'] = float(np.mean([w['c'] for w in ln['w']]))
    # rejoin a line split at a dropped symbol ('(left & right)'): same row, a short gap
    L.sort(key=lambda l: (l['x0']))
    merged = []
    for ln in L:
        for a in merged:
            hh = max(a['h'], ln['h'])
            if abs(a['cy'] - ln['cy']) < .45 * hh and 0 <= ln['x0'] - a['x1'] < 2.6 * hh:
                a['w'] += ln['w']; a['text'] += ' ' + ln['text']; a['x1'] = ln['x1']
                a['y0'], a['y1'] = min(a['y0'], ln['y0']), max(a['y1'], ln['y1'])
                a['c'] = (a['c'] + ln['c']) / 2
                break
        else:
            merged.append(ln)
    L = sorted(merged, key=lambda l: (l['y0'], l['x0']))
    B, used = [], set()
    for i, a in enumerate(L):
        if i in used:
            continue
        blk = {'lines': [a], 'x0': a['x0'], 'x1': a['x1'], 'y0': a['y0'], 'y1': a['y1']}
        used.add(i)
        for j in range(i + 1, len(L)):
            if j in used or len(blk['lines']) >= 3:
                continue
            b = L[j]
            hh = max(b['h'], blk['lines'][-1]['h'])
            gap = b['y0'] - blk['y1']
            ov = min(b['x1'], blk['x1']) - max(b['x0'], blk['x0'])
            cx = abs((b['x0'] + b['x1']) / 2 - (blk['x0'] + blk['x1']) / 2)
            if -hh * .3 < gap < hh * .9 and (ov > .3 * min(b['x1'] - b['x0'], blk['x1'] - blk['x0']) or cx < .25 * (blk['x1'] - blk['x0'])):
                blk['lines'].append(b); used.add(j)
                blk.update(x0=min(blk['x0'], b['x0']), x1=max(blk['x1'], b['x1']), y1=max(blk['y1'], b['y1']))
        blk['text'] = ' '.join(l['text'] for l in blk['lines'])
        blk['c'] = float(np.mean([l['c'] for l in blk['lines']]))
        blk['h'] = float(np.median([l['h'] for l in blk['lines']]))
        B.append(blk)
    return B


def reread(rgb, blk):
    """Read one label block again on its own crop at 3x; keep whichever reading is surer."""
    H, W = rgb.shape[:2]
    p = 6
    x0, y0, x1, y1 = int(max(0, blk['x0'] - p)), int(max(0, blk['y0'] - p)), int(min(W, blk['x1'] + p)), int(min(H, blk['y1'] + p))
    crop = cv2.cvtColor(rgb[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY)
    big = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    big = cv2.copyMakeBorder(big, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    best = (blk['c'], blk['text'])
    for psm in ((7,) if len(blk['lines']) == 1 else (6,)):
        try:
            d = pytesseract.image_to_data(big, config=f'--psm {psm}', output_type=pytesseract.Output.DICT)
        except Exception:
            continue
        ws = [(t.strip(), float(c), b, l) for t, c, b, l in zip(d['text'], d['conf'], d['block_num'], d['line_num']) if t.strip()]
        if not ws:
            continue
        c = float(np.mean([w[1] for w in ws]))
        t = ' '.join(w[0] for w in ws)
        if c > best[0] + 3 and re.search(r'[A-Za-z0-9]', t):
            best = (c, t)
    return best[1], best[0]


# ------------------------------------------------------------------------------------- label assignment
def cost(bb, blk):
    """How far a label block is from a card. The sheet convention is a label just under its card; some
    sheets head their cards instead, so over is barely dearer; then right, left, and inside the card's
    box on paper (a label printed in a notch of the card's outline)."""
    x, y, w, h = bb
    cx, cy = x + w / 2, y + h / 2
    bx0, by0, bx1, by1 = blk['x0'], blk['y0'], blk['x1'], blk['y1']
    bcx, bcy = (bx0 + bx1) / 2, (by0 + by1) / 2
    hov = min(x + w, bx1) - max(x, bx0)                 # horizontal overlap
    vov = min(y + h, by1) - max(y, by0)
    off = abs(bcx - cx)
    out = []
    if by0 >= y + h - 10 and (hov > 0 or off < w / 2 + 40):                    # under
        out.append(max(0, by0 - (y + h)) + .3 * off)
    if by1 <= y + 10 and (hov > 0 or off < w / 2 + 40):                        # over
        out.append(1.15 * max(0, y - by1) + .3 * off + 5)
    if bx0 >= x + w - 10 and vov > 0:                                          # right
        out.append(1.4 * max(0, bx0 - (x + w)) + .3 * abs(bcy - cy) + 18)
    if bx1 <= x + 10 and vov > 0:                                              # left
        out.append(1.6 * max(0, x - bx1) + .3 * abs(bcy - cy) + 30)
    if bx0 >= x - 4 and bx1 <= x + w + 4 and by0 >= y - 4 and by1 <= y + h + 4:  # inside the box, on paper
        out.append(20 + .3 * off + .3 * min(by0 - y, y + h - by1))
    return min(out) if out else 1e9


def assign_labels(cards, B):
    """One block per card, all cards at once (Hungarian): a block under one card and over the next goes
    where it fits the whole sheet best."""
    C = np.array([[cost(p['bbox'], b) for b in B] for p in cards])
    Cc = np.where(C > 120, 1e6, C)
    ri, ci = linear_sum_assignment(Cc)
    return {r: c for r, c in zip(ri, ci) if Cc[r, c] < 1e6}, C


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()


def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# -------------------------------------------------------------------------------------- names / vocab
class Vocab:
    def __init__(self, text, glob_words):
        self.local = {t.lower() for t in tokens(text) if len(t) >= 3}
        self.glob = glob_words
        self.text = text

    def fix_token(self, t):
        if len(t) < 4 or not t.isalpha():
            return t
        lo = t.lower()
        if lo in self.local or lo in self.glob:
            return t
        m = difflib.get_close_matches(lo, list(self.local), n=1, cutoff=.8) or difflib.get_close_matches(lo, list(self.glob), n=1, cutoff=.86)
        if not m:
            return t
        r = m[0]
        return r.upper() if t.isupper() else (r.capitalize() if t[0].isupper() else r)

    def fix(self, label):
        return re.sub(r"[A-Za-z]+", lambda mo: self.fix_token(mo.group(0)), label or '')

    def phrase(self, label):
        """The prompt's own wording when the label is a near copy of a phrase in it."""
        n = norm(label)
        if len(n) < 4:
            return None
        words = re.findall(r"[A-Za-z0-9][A-Za-z0-9_.'\-]*", self.text)
        k = len(n.split())
        best, bs = None, 0.0
        for size in {max(1, k - 1), k, k + 1}:
            for i in range(0, max(0, len(words) - size + 1)):
                cand = ' '.join(words[i:i + size])
                s = difflib.SequenceMatcher(None, n, norm(cand)).ratio()
                if s > bs:
                    best, bs = cand, s
        return best.strip(".,;:'") if bs >= .88 else None


def canonical(label, voc):
    if not label or GARBLED(label):
        return None
    s = voc.fix(label)
    s = re.sub(r'\s+', ' ', s).strip(" .,;:|-_'\"")
    s = re.sub(r'^\(([^)]*)\)$', r'\1', s)
    ph = voc.phrase(s)
    if ph and len(norm(ph)) >= len(norm(s)) * .8:
        s = ph.upper() if s.isupper() else ph
    return s or None


# ------------------------------------------------------------------------------------------- geometry
def part_mask(p):
    a = np.array(Image.open(os.path.join(CUT, p['file'])).convert('RGBA'))[..., 3]
    return ndi.binary_fill_holes(a > 127)


def frame_scores(m):
    """How much of the bbox rim the mask covers, and how much of a band 9..15 px inside it."""
    H, W = m.shape
    rim = np.concatenate([m[:4].any(0), m[-4:].any(0), m[:, :4].any(1), m[:, -4:].any(1)]).mean()
    if H < 40 or W < 40:
        return rim, 1.0
    inner = np.zeros_like(m)
    inner[9:H - 9, 9:W - 9] = True
    inner[15:H - 15, 15:W - 15] = False
    return rim, m[inner].mean()


def rim_thickness(m):
    """Median depth of the mask in from each side of its box: a ruled panel line is a hairline, a painted
    frame (a window sash, an iris plate, a TV) is thick."""
    out = []
    for a in (m, m[::-1], m.T, m.T[::-1]):
        cols = np.where(a[:4].any(0))[0]
        if not len(cols):
            continue
        depth = np.argmin(a[:, cols], axis=0)          # first background row from that side
        depth[a[:, cols].all(0)] = a.shape[0]
        out.append(np.median(depth))
    return float(np.median(out)) if out else 0.0


def save_part(p, rgba, sid):
    f = os.path.join(CUT, p['file'])
    bak = os.path.join(ORIG_DIR, p['file'])
    if not os.path.exists(bak):
        os.makedirs(os.path.dirname(bak), exist_ok=True)
        shutil.copy2(f, bak)
    Image.fromarray(rgba, 'RGBA').save(f, quality=86, method=5)


def describe(p, rgb, dE, LAB, box, m):
    rgba, cut = cutter.render(rgb, dE, LAB, box, m)
    x, y, w, h = box
    bs = cutter.brads(rgb[y:y + h, x:x + w])
    pv = min(bs, key=lambda b: b[1]) if bs else None
    p.update(bbox=[int(x), int(y), int(w), int(h)], cut=cut, brads=[[int(b[0]), int(b[1])] for b in bs], pivot=[int(pv[0]), int(pv[1])] if pv else None)
    return rgba


def grabcut_refine(rgb, box, m):
    """GrabCut around the flood mask: sure fg = mask eroded, sure bg = outside the mask dilated."""
    x, y, w, h = box
    H, W = rgb.shape[:2]
    P = 12
    X0, Y0, X1, Y1 = max(0, x - P), max(0, y - P), min(W, x + w + P), min(H, y + h + P)
    big = np.zeros((Y1 - Y0, X1 - X0), bool)
    big[y - Y0:y - Y0 + h, x - X0:x - X0 + w] = m
    gm = np.full(big.shape, cv2.GC_BGD, np.uint8)
    gm[ndi.binary_dilation(big, iterations=5)] = cv2.GC_PR_BGD
    gm[big] = cv2.GC_PR_FGD
    gm[ndi.binary_erosion(big, iterations=5)] = cv2.GC_FGD
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    img = cv2.cvtColor(rgb[Y0:Y1, X0:X1], cv2.COLOR_RGB2BGR)
    try:
        cv2.grabCut(img, gm, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    except cv2.error:
        return None
    nm = (gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD)
    lab, k = ndi.label(nm)
    if not k:
        return None
    keep = np.unique(lab[big & nm])
    nm = ndi.binary_fill_holes(np.isin(lab, keep[keep > 0]))
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    grad = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    edge = lambda mm: grad[mm & ~ndi.binary_erosion(mm)].mean() if mm.any() else 0
    return nm, big, edge(big), edge(nm), (X0, Y0)


def extend_to_frame(q, fg, box, inset):
    """A figure standing on its cell's rule was trimmed by the rescue's inset: grow it back outward row by
    row (column by column) through the flood's foreground, stopping at the rule itself (a line that is
    mostly ink across the whole box)."""
    x, y, w, h = box
    cv = np.zeros((h, w), bool)
    bx, by, bw, bh = q['box']
    cv[by - y:by - y + bh, bx - x:bx - x + bw] = q['mask']
    f = fg[y:y + h, x:x + w]
    grew = False
    for axis, sign in ((0, 1), (0, -1), (1, 1), (1, -1)):
        a = cv if axis == 0 else cv.T
        g = f if axis == 0 else f.T
        n = a.shape[0]
        idx = np.where(a.any(1))[0]
        if not len(idx):
            continue
        edge = idx.max() if sign > 0 else idx.min()
        if (n - 1 - edge if sign > 0 else edge) > inset + 1:
            continue                                   # not touching the crop's edge on this side
        r = edge
        while 0 <= r + sign < n:
            row = g[r + sign]
            if row.mean() > .7:
                break                                  # the rule
            add = row & ndi.binary_dilation(a[r], iterations=1)
            if not add.any():
                break
            a[r + sign] |= add
            r += sign
            grew = True
    if not grew:
        return q, False
    ys, xs = np.where(cv)
    if ys.min() == 0 or xs.min() == 0 or ys.max() == h - 1 or xs.max() == w - 1:
        return None, False                             # ran into the box edge: not a figure inside a frame
    nb = (int(x + xs.min()), int(y + ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))
    return dict(q, box=nb, mask=cv[ys.min():ys.max() + 1, xs.min():xs.max() + 1]), True


# ----------------------------------------------------------------------------------------------- sheet
def restore(S, sid):
    """Start from the cutter's output: drop parts this pass added, put originals back."""
    keep = []
    for p in S['parts']:
        if p.get('added'):
            f = os.path.join(CUT, p['file'])
            if os.path.exists(f):
                os.remove(f)
            continue
        if 'orig' in p:
            o = p.pop('orig')
            for k in list(p):
                if k not in ('id', 'file') and k not in o:
                    p.pop(k)
            p.update(o)
        for k in ('fix', 'label_conf', 'name', 'ref_reason', 'panel_label'):
            p.pop(k, None)
        bak = os.path.join(ORIG_DIR, p['file'])
        if os.path.exists(bak):
            shutil.copy2(bak, os.path.join(CUT, p['file']))
        keep.append(p)
    S['parts'] = keep
    S.pop('fix', None)
    return S


def fix_sheet(sid, prompts, gwords):
    sj = os.path.join(CUT, sid, 'sheet.json')
    S = restore(json.load(open(sj)), sid)
    rgb = np.array(Image.open(os.path.join(HERE, S['path'])).convert('RGB'))
    H, W = rgb.shape[:2]
    LAB, dE, fg = cutter.paper_flood(rgb)
    pose_sheet = bool(re.search(r'pose', os.path.basename(S['path'])))
    log = {'split': [], 'recut': [], 'unclip': [], 'grabcut': [], 'label': [], 'ref': [], 'added': []}
    for p in S['parts']:
        p['orig'] = {k: p.get(k) for k in ORIG_KEYS}
    existing = {os.path.basename(p['file'])[:-5] for p in S['parts']}
    added = []

    ws = sheet_words(ocr(sid, rgb), rgb, dE)
    B0 = blocks(ws, H)
    # 1. section boxes and framed single-figure panels
    for p in list(S['parts']):
        x, y, w, h = p['bbox']
        if p['kind'] != 'card' or w < 100 or h < 100:
            continue
        m = part_mask(p)
        rim, inner = frame_scores(m)
        paper_in = (dE[y:y + h, x:x + w] < 9).mean()
        if paper_in < .3:
            continue
        raw = np.array(Image.open(os.path.join(CUT, p['file'])).convert('RGBA'))[..., 3] > 127
        framed = rim > .5 and inner < .45 and rim_thickness(raw) <= 5
        backed = (m & (dE[y:y + h, x:x + w] < 9)).sum() > .3 * m.sum()     # opaque over the paper of its cell
        # a ruled cell has plain paper just inside its line; a painted frame (window, rail, TV) has paint there
        pp = dE[y:y + h, x:x + w] < 9
        ring_in = np.concatenate([pp[4:9, 9:-9].ravel(), pp[-9:-4, 9:-9].ravel(), pp[9:-9, 4:9].ravel(), pp[9:-9, -9:-4].ravel()])
        ruled = ring_in.size > 0 and ring_in.mean() > .6
        framed, backed = framed and ruled, backed and ruled
        if not (framed or backed):
            # cards joined into one mask by ruled lines: thin lines open away, the cards fall apart
            ol, k = ndi.label(ndi.binary_opening(m, structure=np.ones((7, 7), bool)))
            if k < 2 or (ndi.sum(np.ones_like(ol), ol, range(1, k + 1)) > 1500).sum() < 2:
                continue
        head = ' '.join(b['text'] for b in B0 if x - 4 <= b['x0'] and b['x1'] <= x + w + 4 and y - 4 <= b['y0'] and b['y1'] <= y + max(60, .25 * h))
        subs, _ = cutter.rescue(rgb, [{'bbox': [x, y, w, h], 'label': (head + ' ' + (p['label'] or '')).strip()}], pose_sheet or bool(re.search(r'orbit|prayer|argument|choreograph', sid)), inset=4)
        subs = [q for q in subs if q['mask'].sum() > 1500 and q['box'][2] >= 22 and q['box'][3] >= 22]
        ext = [extend_to_frame(q, fg, (x, y, w, h), 4)[0] for q in subs]
        if any(e is None for e in ext):
            continue                       # something in it runs out to the box's edge: a card, not a ruled box
        subs = ext
        # a piece cut by the box's own edge was clipped by the inset: never trade a whole card for it
        inside = lambda q, d: q['box'][0] >= x + d and q['box'][1] >= y + d and q['box'][0] + q['box'][2] <= x + w - d and q['box'][1] + q['box'][3] <= y + h - d
        if not subs or (len(subs) == 1 and not inside(subs[0], 1)):
            continue
        if len(subs) == 1 and not backed and subs[0]['mask'].sum() > .97 * raw.sum():
            continue                       # nothing but the object itself: no frame or label to drop
        subs = [q for q in subs if inside(q, 1)]
        if not subs:
            continue
        if len(subs) == 1:
            q = subs[0]
            rgba = describe(p, rgb, dE, LAB, q['box'], q['mask'])
            save_part(p, rgba, sid)
            if q['kind'] == 'pose' and p['kind'] == 'card':
                p['kind'] = 'pose'
            if q['label'] and not GARBLED(q['label']):
                if q['label'] != p['label']:
                    log['label'].append(f"{p['id']}: {p['label']!r} -> {q['label']!r} (printed in its panel)")
                p['label'] = q['label']
                p['panel_label'] = True
            p['fix'] = p.get('fix', []) + ['recut: framed panel -> the figure inside']
            log['recut'].append(f"{p['id']}: framed panel {p['orig']['bbox']} -> figure {p['bbox']}")
            continue
        p['kind'] = 'ref'
        p['ref_reason'] = f'section box: its {len(subs)} contents are cut as separate parts'
        log['split'].append(f"{p['id']} ({w}x{h}) -> {len(subs)} parts")
        for q in subs:
            lab = q['label'] or ''
            s = cutter.slug(lab or 'part')
            base, n = s, 1
            while s in existing:
                n += 1
                s = f'{base}-{n}'
            existing.add(s)
            np_ = {'id': f'{sid}/{s}', 'file': f'{sid}/{s}.webp', 'label': lab, 'kind': 'pose' if q['kind'] == 'pose' else 'card', 'scene': None,
                   'added': True, 'split_from': p['id']}
            if q.get('section'):
                np_['section'] = q['section']
            rgba = describe(np_, rgb, dE, LAB, q['box'], q['mask'])
            Image.fromarray(rgba, 'RGBA').save(os.path.join(CUT, np_['file']), quality=86, method=5)
            code = cutter.CODE.search(lab)
            np_['scene'] = code.group(1) if code else None
            added.append(np_)
            log['added'].append(np_['id'])

    # 2. unclip (words' boxes bit notches out of cards) and 3. GrabCut on pale cards
    chroma = np.hypot(LAB[..., 1] - 128, LAB[..., 2] - 128)
    wordbox = np.zeros((H, W), bool)
    for o in ws:
        wordbox[max(0, o['y'] - 5):o['y'] + o['h'] + 5, max(0, o['x'] - 5):o['x'] + o['w'] + 5] = True
    for p in S['parts']:
        if p['kind'] not in ('card', 'pose') or p.get('fix'):
            continue
        x, y, w, h = p['bbox']
        P = 8
        X0, Y0, X1, Y1 = max(0, x - P), max(0, y - P), min(W, x + w + P), min(H, y + h + P)
        old = np.zeros((Y1 - Y0, X1 - X0), bool)
        try:
            old[y - Y0:y - Y0 + h, x - X0:x - X0 + w] = part_mask(p)
        except ValueError:
            continue
        # the bite: a word box (a rectangle) was taken out of the picture before the cards were found; where it
        # overlapped a card it left a rectangular notch of foreground the mask lacks. Restore notch-shaped,
        # word-sized, ink-free foreground inside the card's own box, joined to the card.
        hull = np.zeros(old.shape, np.uint8)
        cs, _ = cv2.findContours(old.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if cs:
            cv2.fillPoly(hull, [cv2.convexHull(np.vstack(cs))], 1)
        cand = (dE[Y0:Y1, X0:X1] > 12) & (hull > 0) & ~old             # inside the card's own hull: not a label
        cl, k = ndi.label(cand)
        addm = np.zeros_like(old)
        near = ndi.binary_dilation(old, iterations=1)
        for j, sl in enumerate(ndi.find_objects(cl), 1):
            comp = cl[sl] == j
            hh, ww = comp.shape
            if comp.sum() >= 30 and hh <= 40 and ww <= 120 and comp.mean() > .5 and (near[sl] & comp).any():
                addm[sl] |= comp
        changed = False
        if addm.sum() > 40:
            new = ndi.binary_fill_holes(old | addm)
            ys, xs = np.where(new)
            nb = (xs.min() + X0, ys.min() + Y0, xs.max() + 1 + X0, ys.max() + 1 + Y0)
            grow = max(x - nb[0], y - nb[1], nb[2] - (x + w), nb[3] - (y + h))
            thin = ndi.binary_opening(addm, iterations=2).sum() / max(1, addm.sum())
            if grow <= 4 and thin > .3 and addm.sum() < .15 * old.sum():
                box = (int(nb[0]), int(nb[1]), int(nb[2] - nb[0]), int(nb[3] - nb[1]))
                m2 = new[box[1] - Y0:box[1] - Y0 + box[3], box[0] - X0:box[0] - X0 + box[2]]
                rgba = describe(p, rgb, dE, LAB, box, m2)
                a_old = np.array(Image.open(os.path.join(CUT, p['file'])).convert('RGBA'))[..., 3] > 127
                a_new = rgba[..., 3] > 127
                if a_new.sum() - a_old.sum() > 30:
                    save_part(p, rgba, sid)
                    p['fix'] = p.get('fix', []) + [f'unclip: restored {int(a_new.sum() - a_old.sum())} px a label box had cut out']
                    log['unclip'].append(f"{p['id']}: +{int(a_new.sum() - a_old.sum())} px")
                    changed = True
                else:
                    for kk in ('bbox', 'cut', 'brads', 'pivot'):
                        p[kk] = p['orig'][kk]
        if changed or p['kind'] != 'card' or w * h > 600_000:
            continue
        mm = part_mask(p)
        if frame_scores(mm)[0] > .45 or (mm & (dE[y:y + h, x:x + w] < 9)).sum() > .05 * mm.sum():
            continue                       # a frame or paper in the mask: GrabCut would snap to the wrong edge
        band = mm & ~ndi.binary_erosion(mm, iterations=3)
        if not band.any() or dE[y:y + h, x:x + w][band].mean() > 22:
            continue                       # only pale cards: a strong colour edge is already exact
        r = grabcut_refine(rgb, (x, y, w, h), mm)
        if r is None:
            continue
        nm, big, e_old, e_new, (X0, Y0) = r
        inter, union = (nm & big).sum(), (nm | big).sum()
        if union and .9 < inter / union < .995 and e_new > 1.15 * e_old:
            ys, xs = np.where(nm)
            box = (int(xs.min() + X0), int(ys.min() + Y0), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))
            m2 = nm[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            rgba = describe(p, rgb, dE, LAB, box, m2)
            save_part(p, rgba, sid)
            p['fix'] = p.get('fix', []) + [f'grabcut: edge on stronger contrast ({e_old:.0f} -> {e_new:.0f}), IoU {inter / union:.3f}']
            log['grabcut'].append(f"{p['id']}: IoU {inter / union:.3f}, edge {e_old:.0f}->{e_new:.0f}")

    S['parts'] += added

    # 4. labels
    heading = lambda t: re.match(r'^[A-H]\s*[.·:)\-]?\s+[A-Z]{3}', t) or sum(bool(re.fullmatch(r'[A-Z(),&/+\-]{2,}', w)) for w in t.split()) >= 6
    B = [b for b in B0 if not (b['y0'] < H * .09 and b['h'] > 18) and sid not in b['text'].replace(' ', '') and not heading(b['text'])]
    cards = [p for p in S['parts'] if (p['kind'] == 'card' or (p.get('added') and p['kind'] != 'pose')) and not p.get('panel_label')]
    if cards and B:
        assign, C = assign_labels(cards, B)
        owner = {c: r for r, c in assign.items()}
        for r in range(len(cards)):          # shared labels ("CRYSTAL" under ten crystals): nearest unclaimed-or-close block
            if r not in assign:
                c = int(np.argmin(C[r]))
                if C[r, c] < 50:
                    assign[r] = c
        reread_cache = {}
        for r, p in enumerate(cards):
            old = p['label'] or ''
            if r not in assign:
                continue
            c = assign[r]
            if c not in reread_cache:
                reread_cache[c] = reread(rgb, B[c])
            new, conf = reread_cache[c]
            new = re.sub(r'\s+', ' ', new).strip()
            if not new or (GARBLED(new) or not re.search(r'[A-Za-z]{3}', new)) and re.search(r'[A-Za-z]{3}', old):
                continue
            take, why = False, ''
            iscode = lambda t: bool(t.split()) and all(CODEISH.fullmatch(w.strip('.,;:()')) for w in t.split())
            if old and iscode(old) and not iscode(new):
                continue                   # a part code (W07, BO1) is more specific than a group heading
            if norm(new) and norm(old) and (norm(new) in norm(old) or set(norm(new).split()) <= set(norm(old).split())):
                continue                   # the new reading is a piece of the old label
            ob = max(range(len(B)), key=lambda j: sim(old, B[j]['text'])) if old else None
            if ob is not None and sim(old, B[ob]['text']) < .6 and not (norm(old) and norm(old) in norm(B[ob]['text'])):
                ob = None
            if not old or GARBLED(old):
                take, why = True, 'was empty/garbled'
            elif ob == c or norm(old) == norm(new):
                if len(norm(new)) >= len(norm(old)) + 3 and conf >= 60:
                    take, why = True, 're-read, more complete'
            elif ob is None:
                take, why = C[r, c] < 40, f'old text not on the sheet; label {C[r, c]:.0f}px-cost away'
            elif C[r, c] + 5 < C[r, ob]:
                own = owner.get(ob)
                take, why = True, f"closer label (cost {C[r, c]:.0f} vs {C[r, ob]:.0f})" + (f"; old text is {cards[own]['id'].split('/')[-1]}'s" if own is not None and own != r else '')
            if take:
                p['label'] = new
                p['label_conf'] = round(conf, 1)
                log['label'].append(f"{p['id']}: {old!r} -> {new!r} ({why})")

    # 5. names
    voc = Vocab(prompts.get(sid, ''), gwords)
    for p in S['parts']:
        p['name'] = canonical(p['label'], voc)
        code = cutter.CODE.search(p['label'] or '')
        if code and not p.get('scene'):
            p['scene'] = code.group(1)

    # 6. references
    heads = [b for b in B if b['y0'] > H * .5 and BAND_HEAD.search(b['text']) and (b['x0'] < W * .2 or len(b['text']) > 18)]
    for p in S['parts']:
        if p['kind'] == 'ref':
            if p.get('ref_reason', '').startswith('section'):
                log['ref'].append(f"{p['id']}: {p['ref_reason']}")
            elif not p.get('ref_reason'):
                p['ref_reason'] = 'in an ASSEMBLED/REFERENCE section (' + (p.get('section') or '')[:40] + ')'
            continue
        lab = p['label'] or ''
        x, y, w, h = p['bbox']
        why = None
        if REF_LABEL.search(lab) and not SEPARATE_REF.search(lab) and len(lab) <= 60:
            why = f'label says {REF_LABEL.search(lab).group(0)!r}'
        else:
            for b in heads:
                if y >= b['y0'] - 10 and x + w / 2 >= b['x0'] - 30 and not (b['y0'] >= y + h - 12 and b['y0'] <= y + h + 70):
                    why = f"under the band heading {b['text'][:40]!r}"
                    break
        if not why and h < 120 and w * h < 40000:
            # a label fragment: the part is printed words
            m = part_mask(p)
            inw = np.zeros((h, w), bool)
            for o in ws:
                inw[max(0, o['y'] - y - 2):max(0, o['y'] - y + o['h'] + 2), max(0, o['x'] - x - 2):max(0, o['x'] - x + o['w'] + 2)] = True
            crop = rgb[y:y + h, x:x + w]
            dark = (crop.max(2)[m] < 90).mean() if m.any() else 0
            grey = (chroma[y:y + h, x:x + w][m] < 10).mean() if m.any() else 0
            if m.any() and (m & inw).sum() > .6 * m.sum() and (dark > .3 or grey > .9):
                why = 'label fragment (printed words)'
        if why:
            p['kind'] = 'ref'
            p['ref_reason'] = why
            log['ref'].append(f"{p['id']}: {why}")

    for p in S['parts']:
        if p.get('orig') and not p.get('fix') and all(p.get(k) == v for k, v in p['orig'].items()):
            p.pop('orig')               # untouched (only 'name' added)
    S['fix'] = {k: len(v) for k, v in log.items() if v}
    json.dump(S, open(sj, 'w'), indent=1)
    return sid, log


def catalog():
    cat = {'sheets': {}}
    for f in sorted(glob.glob(os.path.join(CUT, '*', 'sheet.json'))):
        e = json.load(open(f))
        cat['sheets'][e.pop('id')] = e
    P = [p for v in cat['sheets'].values() for p in v['parts']]
    cat['totals'] = {'sheets': len(cat['sheets']), 'parts': len(P),
                     'working': sum(p['kind'] != 'ref' for p in P), 'refs': sum(p['kind'] == 'ref' for p in P),
                     'unlabeled': sum(GARBLED(p['label']) for p in P), 'empty_sheets': sum(not v['parts'] for v in cat['sheets'].values()),
                     'added_by_fix': sum(bool(p.get('added')) for p in P), 'recut_by_fix': sum(bool(p.get('fix')) for p in P)}
    json.dump(cat, open(os.path.join(CUT, 'catalog.json'), 'w'), indent=1)
    return cat


def _job(a):
    sid, = a
    try:
        return fix_sheet(sid, PROMPTS, GWORDS)
    except Exception as e:  # one bad sheet must not stop the rest
        import traceback
        traceback.print_exc()
        return sid, {'error': [repr(e)]}


PROMPTS, GWORDS = None, None


def main():
    global PROMPTS, GWORDS
    PROMPTS = prompt_texts()
    from collections import Counter
    cnt = Counter(t.lower() for v in PROMPTS.values() for t in tokens(v) if len(t) >= 3)
    GWORDS = {t for t, n in cnt.items() if n >= 2}
    args = sys.argv[1:]
    ids = sorted(os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(CUT, '*', 'sheet.json')))
    if args:
        ids = [i for i in ids if any(a in i for a in args)]
    os.environ['OMP_THREAD_LIMIT'] = '1'
    import multiprocessing as mp
    logs = {}
    with mp.Pool(int(os.environ.get('JOBS', os.cpu_count() or 2))) as pool:
        for k, (sid, log) in enumerate(pool.imap_unordered(_job, [(i,) for i in ids]), 1):
            logs[sid] = log
            print(f"[{k}/{len(ids)}] {sid}: " + ', '.join(f'{a} {len(b)}' for a, b in log.items() if b), flush=True)
    cat = catalog()
    write_log(logs, cat, full=not args)
    print(cat['totals'])


def write_log(logs, cat, full):
    f = os.path.join(CUT, 'FIXES.md')
    old = {}
    if os.path.exists(f) and not full:            # a partial run keeps the other sheets' entries
        cur = None
        for ln in open(f):
            m = re.match(r'^### (\S+)', ln)
            if m:
                cur = m.group(1); old[cur] = []
            elif cur and ln.startswith('- '):
                old[cur].append(ln)
    T = cat['totals']
    out = ['# Cut fixes (fix_cut.py)', '',
           'Post-pass over the cutter output. No part was renamed or moved; ids and file paths are unchanged.',
           'Each changed part keeps its cutter values under `orig`; the first version of every re-cut image is in `cut/_orig/`.', '',
           'Before (cutter first pass): 365 sheets, 5042 parts, 12 sheets with no parts, 781 parts with an empty or',
           'garbled label (no 3-letter word and not a code like W06), 0 parts marked as references.',
           'The 12 empty sheets were then cut box by box by cutter.py (rescue): +220 parts.', '',
           f"Totals now: {json.dumps(T)}", '',
           'Kinds of fix (a part may have several):',
           '- `split`: a card that was a ruled box holding several cards -> kind `ref` (ref_reason "section box"), its contents added as new parts (`added: true`, `split_from`).',
           '- `recut`: a framed cell holding one figure -> the same file re-cut to the figure (frame, printed label and paper dropped).',
           '- `unclip`: a rectangular bite the cutter took out of a card (a word box removed before finding cards) filled back in.',
           '- `grabcut`: tried on every pale card; the flood edge already sits on stronger contrast than GrabCut finds, so none are accepted.',
           '- `label`: label re-read/re-assigned (old value under `orig.label`).',
           '- `ref`: kind set to `ref` (`ref_reason` says why); planners should skip these.', '',
           '## Per sheet', '']
    for sid in sorted(set(old) | set(logs)):
        if sid in logs:
            lines = [f"- {k}: {e}\n" for k, v in logs[sid].items() for e in v]
        else:
            lines = old[sid]
        if lines:
            out.append(f'### {sid}')
            out += [l.rstrip('\n') for l in lines]
            out.append('')
    open(f, 'w').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
