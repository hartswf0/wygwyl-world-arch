"""Interaction geometry from a cut-out's alpha (and colour), in the piece's own pixels (x right, y down, origin =
top-left of the .webp). Every function returns (geometry dict, quality 0..1, evidence dict). All numbers measured
from pixels; the interpretation of each number (which row is 'the seat') is a rule, written in the evidence.
"""
import numpy as np, cv2

cv2.setNumThreads(1)


def load(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGRA)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


class Piece:
    def __init__(self, im):
        self.im = im
        self.a = im[..., 3] > 127
        self.L = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
        ys, xs = np.nonzero(self.a)
        self.ok = len(xs) > 30
        if not self.ok:
            return
        self.x0, self.x1, self.y0, self.y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
        self.W, self.H = self.x1 - self.x0 + 1, self.y1 - self.y0 + 1
        self.area = len(xs)
        self.rw = self.a.sum(1)                       # per-row width (count)
        a = self.a
        has = a.any(0)
        self.top = np.where(has, a.argmax(0), -1)     # per-column first alpha row
        self.bot = np.where(has, a.shape[0] - 1 - a[::-1].argmax(0), -1)
        hr = a.any(1)
        self.left = np.where(hr, a.argmax(1), -1)
        self.right = np.where(hr, a.shape[1] - 1 - a[:, ::-1].argmax(1), -1)
        self.cx, self.cy = float(xs.mean()), float(ys.mean())
        self.xs, self.ys = xs, ys

    def core_cols(self, frac=0.1):
        c0 = self.x0 + int(frac * self.W); c1 = self.x1 - int(frac * self.W)
        cols = np.arange(c0, c1 + 1)
        return cols[self.top[cols] >= 0]

    def run_near(self, y, tol, cols=None):
        """longest contiguous run of columns whose top contour is within tol of y -> (x0, x1, frac_of_width)"""
        cols = np.arange(self.x0, self.x1 + 1) if cols is None else cols
        ok = (self.top[cols] >= 0) & (np.abs(self.top[cols] - y) <= tol)
        best, cur, bs = (0, 0), 0, None
        for i, v in enumerate(ok):
            if v:
                if cur == 0: s = i
                cur += 1
                if cur > best[1] - best[0]: best = (s, i + 1)
            else:
                cur = 0
        if best[1] == best[0]:
            return None
        return int(cols[best[0]]), int(cols[best[1] - 1]), (best[1] - best[0]) / self.W

    def hedge(self, ya, yb, xa, xb, gap=3):
        """strongest consistent horizontal colour edge between rows ya..yb over columns xa..xb (alpha both sides).
        -> (row, strength in grey levels) or (None, 0)"""
        best = (None, 0.0)
        xa, xb = max(xa, 0), min(xb, self.a.shape[1] - 1)
        for y in range(max(ya, gap), min(yb, self.a.shape[0] - gap - 1) + 1):
            m = self.a[y - gap, xa:xb + 1] & self.a[y + gap, xa:xb + 1]
            if m.sum() < 0.4 * (xb - xa + 1):
                continue
            d = (self.L[y + gap, xa:xb + 1] - self.L[y - gap, xa:xb + 1])[m]
            s = abs(float(np.median(d)))
            if s > best[1]:
                best = (y, s)
        return best


def _r(v):
    return int(round(float(v)))


# ---------------------------------------------------------------- surface / stand-on (top contour lines)
def top_line(P, label_kind):
    """The resting/standing line = the piece's top contour where it is flat and wide.
    Rule: take core columns (central 80%), the line y = the most common top-contour value among them (5px bins,
    upper quartile preferred only if it is wide); x-range = the longest run of columns whose top is within tol.
    If a consistent colour edge sits just below the top (a painted top face seen from above), report the face band
    and put the rest line in its middle (inferred)."""
    cols = P.core_cols(0.1)
    if len(cols) < 3:
        return None, 0, {'why': 'too narrow'}
    t = P.top[cols]
    tol = max(3, int(0.03 * P.H))
    # candidate levels: histogram of top values
    bins = np.arange(P.y0, P.y1 + 2 * tol, tol)
    h, e = np.histogram(t, bins=bins)
    # prefer the highest (smallest y) level that holds >= 30% of core columns, else the modal level
    order = np.argsort(e[:-1])
    lvl = None
    for i in order:
        if h[i] >= 0.3 * len(cols):
            lvl = i; break
    if lvl is None:
        lvl = int(h.argmax())
    sel = t[(t >= e[lvl] - tol) & (t < e[lvl + 1] + tol)]
    y = float(np.median(sel))
    run = P.run_near(y, tol)
    if run is None:
        return None, 0, {'why': 'no flat run'}
    xa, xb, frac = run
    flat = float(np.std(P.top[xa:xb + 1]))
    ev = {'rule': 'top contour, flattest wide level', 'level_cols_frac': round(len(sel) / len(cols), 2),
          'run_frac_of_width': round(frac, 2), 'top_std_px': round(flat, 1), 'tol_px': tol}
    g = {'y': _r(y), 'x_range': [xa, xb]}
    # painted top face (seen from above): a colour edge within the next 30% of height
    fy, fs = P.hedge(_r(y) + max(3, int(0.03 * P.H)), _r(y + 0.3 * P.H), xa + (xb - xa) // 6, xb - (xb - xa) // 6)
    if fy is not None and fs >= 18 and (fy - y) >= 0.04 * P.H:
        g['top_face'] = [_r(y), int(fy)]
        g['rest_y'] = _r((y + fy) / 2)
        ev['top_face_edge_strength'] = round(fs, 1)
        ev['rest_y_rule'] = 'middle of painted top face (inferred)'
    else:
        g['rest_y'] = _r(y)
        ev['rest_y_rule'] = 'top contour (no painted top face found)'
    q = min(1.0, 0.4 + 0.6 * frac) * (1.0 if flat < 2 * tol else 0.6)
    return g, round(q, 2), ev


# ---------------------------------------------------------------- seat
def seat(P, words, back_expected=True):
    """Seat line, x-range and back side.
    Profile / 3-quarter test (measured): columns whose top is high (within the top 25% of height) form a band at one
    side covering < 45% of width, while >= 35% of width has its top at a lower plateau -> seat = that plateau,
    back = the high side.
    Front view: no such split; seat = strongest horizontal colour edge in 35-70% of height (cushion front / seat edge),
    back = 'behind' (the upper part is the back rest, seen face-on). Fallback: 52% of height (prior)."""
    no_back = bool(set(words) & {'cushion', 'mattress', 'bed', 'stoop', 'step', 'kerb', 'curb', 'stump', 'saddle'}) \
        or ('bench' in words and not back_expected) or 'arm' in words
    flat = P.H < 0.35 * P.W
    if no_back or not back_expected or flat:
        g, q, ev = top_line(P, 'seat')
        if g is None:
            return None, 0, ev
        g = {'seat_y': g['rest_y'], 'x_range': g['x_range'], 'back': 'none', 'top_y': g['y']}
        ev['rule'] = 'backless seat: top contour (' + ev['rule'] + ')'
        return g, q, ev
    cols = np.arange(P.x0, P.x1 + 1)
    t = P.top[cols].astype(float)
    valid = t >= 0
    hi_thr = P.y0 + 0.25 * P.H
    high = valid & (t <= hi_thr)
    hf = high.sum() / max(1, valid.sum())
    ev = {'high_cols_frac': round(float(hf), 2)}
    if 0.05 < hf < 0.45:
        hcols = cols[high]
        # high band must hug one side
        lft = hcols.mean() < P.x0 + 0.5 * P.W
        side = 'left' if lft else 'right'
        rest = valid & ~high & (t > P.y0 + 0.3 * P.H) & (t < P.y0 + 0.8 * P.H)
        if rest.sum() >= 0.3 * valid.sum():
            tr = t[rest]
            tol = max(3, int(0.03 * P.H))
            hist, e = np.histogram(tr, bins=np.arange(tr.min(), tr.max() + 2 * tol, tol))
            k = int(hist.argmax())
            y = float(np.median(tr[(tr >= e[k] - tol) & (tr < e[k + 1] + tol)]))
            run = P.run_near(y, tol)
            if run:
                xa, xb, frac = run
                ev.update({'rule': 'profile/3-quarter: high back band on one side, seat plateau beside it',
                           'plateau_frac': round(frac, 2), 'back_band_x': [int(hcols.min()), int(hcols.max())]})
                return {'seat_y': _r(y), 'x_range': [xa, xb], 'back': side,
                        'back_x': int(hcols.max() if lft else hcols.min()), 'back_top_y': int(t[high].min())}, \
                    round(min(1, 0.5 + frac), 2), ev
    # front view: colour edge in 35..70% height
    xa, xb = P.x0 + P.W // 6, P.x1 - P.W // 6
    fy, fs = P.hedge(_r(P.y0 + 0.35 * P.H), _r(P.y0 + 0.72 * P.H), xa, xb)
    if fy is not None and fs >= 15:
        # the seat top is the UPPER of the strong edges (the strongest is often the seat's front/under edge)
        for yy in range(_r(P.y0 + 0.35 * P.H), int(fy)):
            y2, s2 = P.hedge(yy, yy, xa, xb)
            if y2 is not None and s2 >= 0.6 * fs:
                ev_up = (fy, fs); fy, fs = y2, s2; break
        rows = P.rw[fy]
        l, r = int(P.left[fy]), int(P.right[fy])
        ev.update({'rule': 'front view: topmost horizontal colour edge in 35-72% of height with >=60% of the strongest edge = seat top',
                   'edge_strength': round(fs, 1), 'edge_row_rel': round((fy - P.y0) / P.H, 2)})
        return {'seat_y': int(fy), 'x_range': [l + _r(0.08 * (r - l)), r - _r(0.08 * (r - l))], 'back': 'behind'}, \
            round(min(0.8, 0.35 + fs / 80), 2), ev
    y = _r(P.y0 + 0.52 * P.H)
    l, r = int(P.left[y]), int(P.right[y])
    ev.update({'rule': 'fallback prior: seat at 52% of height (no profile split, no edge)'})
    return {'seat_y': y, 'x_range': [l, r], 'back': 'behind'}, 0.25, ev


# ---------------------------------------------------------------- grip
HANDLE_W = {'lantern', 'suitcase', 'bag', 'bucket', 'basket'}
LONG_W = {'microphone', 'mic', 'bottle', 'candle', 'staff', 'torch', 'flower', 'poppy', 'daisy', 'blossom', 'rose',
          'guitar', 'receiver', 'handset', 'vape', 'pen', 'umbrella', 'knife', 'key', 'hourglass',
          'armful', 'bouquet', 'coupe', 'goblet'}
FLAT_W = {'paper', 'letter', 'envelope', 'snapshot', 'photo', 'photograph', 'journal', 'book', 'record', 'vinyl',
          'tambourine', 'card'}


def holes(P, close_bottom=False, min_frac=0.0):
    """Transparent regions not reachable from the top/left/right border (and bottom too unless close_bottom).
    close_bottom=True treats the bottom edge as a wall: openings that reach the ground (doorways, arches) count."""
    m = P.a.astype(np.uint8)
    h, w = m.shape
    pad = np.zeros((h + 2, w + 2), np.uint8)
    pad[1:-1, 1:-1] = m
    if close_bottom:
        # wall only under the piece's own footprint: from its leftmost to rightmost bottom-row pixel
        yb = P.y1
        xs = np.nonzero(m[max(0, yb - 2):yb + 1].any(0))[0]
        if len(xs):
            pad[yb + 2:, :] = 0
            pad[yb + 1, xs.min() + 1:xs.max() + 2] = 1
    inv = (1 - pad).astype(np.uint8)
    ff = inv.copy()
    msk = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(ff, msk, (0, 0), 0)
    hole = ff[1:-1, 1:-1]
    n, lab, st, cen = cv2.connectedComponentsWithStats(hole, 8)
    out = []
    bb = P.W * P.H
    for i in range(1, n):
        x, y, ww, hh, ar = st[i]
        if ar < max(min_frac * bb, 25):
            continue
        out.append({'rect': [int(x), int(y), int(ww), int(hh)], 'area': int(ar), 'fill': round(ar / (ww * hh), 2),
                    'reaches_bottom': bool(y + hh >= P.y1 - 1), 'mask_id': i})
    return out, lab


def snap(P, pt):
    x, y = int(pt[0]), int(pt[1])
    if 0 <= y < P.a.shape[0] and 0 <= x < P.a.shape[1] and P.a[y, x]:
        return [x, y], 0
    d = (P.xs - x) ** 2 + (P.ys - y) ** 2
    i = int(np.argmin(d))
    return [int(P.xs[i]), int(P.ys[i])], int(np.sqrt(d[i]))


def grip(P, words):
    g, q, ev = _grip(P, words)
    g['point'], moved = snap(P, g['point'])
    if moved:
        ev['snapped_to_alpha_px'] = moved
        q = round(q * (0.8 if moved > 0.1 * max(P.W, P.H) else 1.0), 2)
    return g, q, ev


def _grip(P, words):
    ws = set(words)
    pts = np.stack([P.xs, P.ys], 1).astype(np.float32)
    mu = pts.mean(0)
    cov = np.cov((pts - mu).T)
    ev_, evec = np.linalg.eigh(cov)
    major = evec[:, 1]; elong = float(np.sqrt(ev_[1] / max(ev_[0], 1e-6)))
    ang = float(np.degrees(np.arctan2(major[1], major[0])))
    ev = {'elongation': round(elong, 2), 'major_axis_deg': round(ang, 1)}
    up = [0.0, -1.0]
    mode = None
    hs, _ = holes(P, False, 0.004)
    if ws & HANDLE_W:
        top_holes = [h for h in hs if h['rect'][1] < P.y0 + 0.5 * P.H]
        if top_holes:
            hh = max(top_holes, key=lambda h: h['area'])
            x, y, w, h = hh['rect']
            gx = x + w / 2
            col = P.a[:y, int(gx)]
            bar_top = int(np.nonzero(col)[0].min()) if col.any() else y
            g = {'point': [_r(gx), _r((bar_top + y) / 2)], 'up': up, 'mode': 'handle bar above the hole',
                 'hole': hh['rect']}
            ev['rule'] = 'handle prop: bar above the largest hole in the upper half'
            return g, 0.8, ev
        g = {'point': [_r(P.x0 + P.W / 2), int(P.top[_r(P.x0 + P.W / 2)] if P.top[_r(P.x0 + P.W / 2)] >= 0 else P.y0)],
             'up': up, 'mode': 'top centre (no handle hole found)'}
        ev['rule'] = 'handle prop without a handle hole: top centre'
        return g, 0.45, ev
    if ws & {'cup', 'mug'}:
        side = [h for h in hs if h['rect'][1] > P.y0 + 0.1 * P.H and (h['rect'][0] > P.cx or h['rect'][0] + h['rect'][2] < P.cx)]
        if side:
            hh = max(side, key=lambda h: h['area'])
            x, y, w, h = hh['rect']
            g = {'point': [_r(x + w / 2), _r(y + h / 2)], 'up': up, 'mode': 'cup handle (side hole)', 'hole': hh['rect']}
            ev['rule'] = 'cup: side hole = handle'
            return g, 0.8, ev
        g = {'point': [_r(P.cx), _r(P.cy)], 'up': up, 'mode': 'cup body (wrap), no handle hole'}
        ev['rule'] = 'cup without handle hole: hand wraps the body at its centroid'
        return g, 0.6, ev
    if (ws & LONG_W) or (elong >= 2.2 and not ws & FLAT_W):
        # thinnest cross-section along the major axis, in 15..85% of its length
        proj = (pts - mu) @ major
        perp = (pts - mu) @ np.array([-major[1], major[0]])
        lo, hi = proj.min(), proj.max()
        nb = 40
        edges = np.linspace(lo, hi, nb + 1)
        idx = np.clip(np.digitize(proj, edges) - 1, 0, nb - 1)
        width = np.array([np.ptp(perp[idx == i]) if (idx == i).sum() > 2 else np.inf for i in range(nb)])
        cand = np.arange(int(0.2 * nb), int(0.8 * nb))
        k = cand[np.argmin(width[cand])]
        c = (edges[k] + edges[k + 1]) / 2
        sel = idx == k
        pc = mu + major * c + np.array([-major[1], major[0]]) * float(np.median(perp[sel]))
        # up = the axis end that points up on the sheet (painted upright); for near-horizontal axes, the wider end
        a = major if major[1] < 0 else -major
        if abs(major[1]) < 0.35:
            wa = np.nanmean(np.where(np.isinf(width[:8]), np.nan, width[:8]))
            wb = np.nanmean(np.where(np.isinf(width[-8:]), np.nan, width[-8:]))
            a = -major if wa > wb else major  # head (wider end) is 'up'
            ev['up_rule'] = 'axis near horizontal: up = wider end (head of the prop)'
        else:
            ev['up_rule'] = 'up = major-axis end pointing up the sheet (props are painted upright)'
        g = {'point': [_r(pc[0]), _r(pc[1])], 'up': [round(float(a[0]), 2), round(float(a[1]), 2)],
             'mode': 'thinnest section along the long axis (20-80%)', 'grip_width_px': _r(width[k]),
             'axis_pos': round((c - lo) / (hi - lo), 2)}
        ev['rule'] = 'long prop: hand at the thinnest cross-section in 15-85% of the major axis'
        q = 0.75 if (ws & LONG_W) else 0.5
        return g, q, ev
    if ws & FLAT_W:
        y = _r(P.y0 + 0.55 * P.H)
        x = int(P.left[y]) if P.left[y] >= 0 else P.x0
        g = {'point': [x + max(2, _r(0.08 * P.W)), y], 'up': up, 'mode': 'edge pinch (flat sheet / disc), left edge'}
        ev['rule'] = 'flat prop: pinched at its left edge, just below half height (mirror for right hand)'
        return g, 0.55, ev
    g = {'point': [_r(P.cx), _r(P.cy + 0.1 * P.H)], 'up': up, 'mode': 'compact: palm under the centroid'}
    ev['rule'] = 'compact prop: centroid, nudged 10% down'
    return g, 0.45, ev


# ---------------------------------------------------------------- aperture
def aperture(P, words, role_hint=None, needs_hole=False):
    """Openings from interior transparency (bottom edge treated as a wall, so doorways reaching the ground count),
    else a dark inner panel (painted opening) that does not touch the outline. Door/window from where the opening's
    bottom sits: within 8% of the piece's bottom -> door (stand in / pass through), higher -> window (sill)."""
    ws = set(words)
    if role_hint == 'leaf':
        side = 'left' if ws & {'l', 'left'} else ('right' if ws & {'r', 'right'} else None)
        hs0, _ = holes(P, False, 0.01)
        g = {'role': 'leaf', 'rect': [P.x0, P.y0, P.W, P.H], 'hinge_side': side,
             'hinge_rule': 'label L/left -> hinge on the left edge; None = unknown',
             'glazing_holes': [h['rect'] for h in hs0]}
        return g, 0.65 if side else 0.55, {'rule': 'leaf label (leaf/slab/door L|R): the piece IS the door leaf; '
                                                  'holes inside it are glazing, not passages'}
    hs, lab = holes(P, True, 0.012)
    hs = [h for h in hs if h['rect'][2] >= 0.06 * P.W and h['rect'][3] >= 0.08 * P.H]
    ev = {'holes_found': len(hs)}
    ops = []
    for h in sorted(hs, key=lambda h: -h['area'])[:8]:
        x, y, w, hh = h['rect']
        bottom = y + hh - 1
        gap = P.y1 - bottom
        door = h['reaches_bottom'] or gap <= 0.08 * P.H
        o = {'rect': h['rect'], 'source': 'transparent hole', 'fill': h['fill'],
             'type': 'door' if door else 'window', 'floor_y': int(P.y1 if h['reaches_bottom'] else bottom),
             'open_bottom': h['reaches_bottom'], 'passable': bool(door and hh >= 0.3 * P.H)}
        if not door:
            o['sill_y'] = int(bottom)
        ops.append(o)
    if ops:
        if role_hint == 'floor_opening':
            for o in ops: o['type'] = 'floor_opening'; o['passable'] = False
        g = {'role': 'frame', 'openings': ops}
        ev['rule'] = 'interior transparency (bottom closed under the footprint)'
        return g, 0.85 if ops[0]['fill'] > 0.5 else 0.6, ev
    if needs_hole:
        ev['why'] = 'bare FRAME label and no transparent opening'
        return None, 0, ev
    if role_hint == 'leaf' or (ws & {'door', 'gate'} and not ws & {'wall', 'facade', 'frame', 'way', 'opening',
                                                                      'aperture', 'portal', 'window', 'arch'}):
        side = None
        if ws & {'l', 'left'}: side = 'left'
        if ws & {'r', 'right'}: side = 'right'
        g = {'role': 'leaf', 'rect': [P.x0, P.y0, P.W, P.H], 'hinge_side': side,
             'hinge_rule': 'label L/left -> hinge on left edge (outer edge of a double door); None = unknown'}
        ev['rule'] = 'no opening in the alpha + door/gate/leaf label: the piece IS the leaf that closes an opening'
        return g, 0.6 if side else 0.5, ev
    # dark inner panel
    a = P.a
    inner = cv2.erode(a.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=2).astype(bool)
    med = float(np.median(P.L[a]))
    dark = inner & (P.L < min(0.55 * med, 90))
    dark = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab2, st, _ = cv2.connectedComponentsWithStats(dark, 8)
    cands = []
    for i in range(1, n):
        x, y, w, hh, ar = st[i]
        if ar < 0.02 * P.area or w < 0.06 * P.W or hh < 0.08 * P.H:
            continue
        rect_fill = ar / (w * hh)
        if rect_fill < 0.55:
            continue
        cands.append((ar, [int(x), int(y), int(w), int(hh)], rect_fill))
    ev['median_luma'] = round(med, 1)
    if cands:
        ops = []
        for ar, r, f in sorted(cands, reverse=True)[:6]:
            x, y, w, hh = r
            bottom = y + hh - 1
            door = (P.y1 - bottom) <= 0.1 * P.H
            o = {'rect': r, 'source': 'dark inner panel', 'fill': round(f, 2), 'type': 'door' if door else 'window',
                 'floor_y': int(bottom), 'open_bottom': False, 'passable': bool(door and hh >= 0.3 * P.H)}
            if not door: o['sill_y'] = int(bottom)
            ops.append(o)
        g = {'role': 'painted_opening', 'openings': ops}
        ev['rule'] = 'no transparency; dark (<55% of median luma) rectangular region inside the outline'
        return g, 0.45, ev
    ev['why'] = 'no transparent opening, not a leaf, no dark inner panel'
    return None, 0, ev


# ---------------------------------------------------------------- lean
def lean(P, orient, words):
    ev = {}
    if orient == 'h':
        g, q, e = top_line(P, 'lean')
        if g is None:
            return None, 0, e
        ev.update(e); ev['rule'] = 'railing/counter: lean on the top line (forearms / small of back)'
        return {'edge': 'top', 'y': g['y'], 'x_range': g['x_range'], 'base_y': P.y1}, q, ev
    if set(words) & {'tree', 'trunk', 'palm'}:
        rows = np.arange(_r(P.y0 + 0.55 * P.H), _r(P.y0 + 0.95 * P.H) + 1)
        bx = int(np.median(P.xs[P.ys >= P.y0 + 0.9 * P.H])) if (P.ys >= P.y0 + 0.9 * P.H).any() else int(P.cx)
        L_, R_, Y_ = [], [], []
        for y in rows:
            r = P.a[y]
            if not r[bx]:
                continue
            l = bx
            while l > 0 and r[l - 1]: l -= 1
            rr = bx
            while rr < len(r) - 1 and r[rr + 1]: rr += 1
            if rr - l < 0.35 * P.W:
                L_.append(l); R_.append(rr); Y_.append(y)
        if len(Y_) >= 0.1 * P.H:
            g = {'edges': [{'side': 'left', 'x': int(np.median(L_)), 'y_range': [int(min(Y_)), int(max(Y_))]},
                           {'side': 'right', 'x': int(np.median(R_)), 'y_range': [int(min(Y_)), int(max(Y_))]}],
                 'base_y': P.y1, 'trunk_width_px': int(np.median(np.array(R_) - np.array(L_)))}
            return g, 0.7, {'rule': 'tree: lean on the trunk = rows in the lower 45% where the run through the '
                                    'base column is < 35% of width', 'trunk_rows': len(Y_)}
        return None, 0, {'why': 'tree with no narrow trunk found (canopy to the ground or a tree band)'}
    rows = np.arange(_r(P.y0 + 0.15 * P.H), _r(P.y0 + 0.85 * P.H) + 1)
    rows = rows[P.left[rows] >= 0]
    out = []
    qs = []
    for side, arr in (('left', P.left), ('right', P.right)):
        v = arr[rows].astype(float)
        x = float(np.median(v)); mad = float(np.median(np.abs(v - x)))
        ok = np.abs(v - x) <= max(3, 0.02 * P.W)
        # longest straight vertical run
        best, cur, s0 = (0, 0), 0, 0
        for i, o in enumerate(ok):
            if o:
                if cur == 0: s0 = i
                cur += 1
                if cur > best[1] - best[0]: best = (s0, i + 1)
            else:
                cur = 0
        frac = (best[1] - best[0]) / max(1, len(rows))
        out.append({'side': side, 'x': _r(x), 'y_range': [int(rows[best[0]]), int(rows[best[1] - 1])] if best[1] > best[0] else None,
                    'straight_frac': round(frac, 2), 'mad_px': round(mad, 1)})
        qs.append(frac)
    g = {'edges': out, 'base_y': P.y1}
    if set(words) & {'wall', 'facade'}:
        g['face'] = {'x_range': [P.x0, P.x1], 'base_y': P.y1,
                     'note': 'stand with back to the wall face; feet at base_y if the wall stands on the actor floor'}
    ev['rule'] = 'vertical lean edges: left/right outline at 15-85% height, straight run length'
    return g, round(0.3 + 0.6 * max(qs), 2), ev


# ---------------------------------------------------------------- occluder
def occluder(P, words):
    """hide_y: the row from which the piece is a solid body (row coverage >= 50% of its max, smoothed);
    an actor standing just behind the piece is hidden below hide_y wherever the piece has alpha.
    coverage_below: mean row coverage under hide_y (how much of the lower body it really hides)."""
    rw = P.rw[P.y0:P.y1 + 1].astype(float) / P.W
    k = max(1, int(0.02 * P.H))
    sm = np.convolve(rw, np.ones(k) / k, mode='same')
    mx = sm.max()
    i_half = int(np.argmax(sm >= 0.5 * mx))
    i_solid = int(np.argmax(sm >= 0.8 * mx))
    hide_y = P.y0 + i_half
    cov = float(rw[i_half:].mean())
    kind = 'solid' if cov >= 0.75 else ('partial' if cov >= 0.35 else 'see-through')
    # the occluding x-span at hide_y + a little
    yy = min(P.y1, hide_y + max(2, int(0.05 * P.H)))
    g = {'hide_y': int(hide_y), 'solid_y': int(P.y0 + i_solid), 'x_range': [int(P.left[yy]), int(P.right[yy])],
         'base_y': int(P.y1), 'coverage_below': round(cov, 2), 'hides': kind,
         'top_y': int(P.y0)}
    ev = {'rule': 'row coverage profile: hide_y = first row at >=50% of max coverage; actor behind is hidden below it',
          'max_row_coverage': round(float(mx), 2)}
    q = 0.75 if kind != 'see-through' else 0.5
    return g, q, ev
