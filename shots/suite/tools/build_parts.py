"""One registry of every cut puppet part: shots/suite/data/parts.json (+ parts_summary.json).

    python3 shots/suite/tools/cut_all.py  <work>     # 1. cut every painted part sheet (cached)
    python3 shots/suite/tools/clip_tag.py <work>     # 2. zero-shot tags for cards the layout cannot name (cached)
    python3 shots/suite/tools/build_parts.py <work>  # 3. name, pivot, socket, scale; write the registry

Naming, in order of trust:
  layout   the sheet's kit layout knows the cell order (kit.py / v2.py / packs.py): body 13/14, profile 7/8,
           hands 24, heads 5/10, feet 6, face 27, replacements 6, hipcore 5. Cards are read in rows (cards
           whose heights overlap share a row) and must match the layout's count exactly, and agree with
           CLIP on the coarse kind for at least 60% of cards, or the layout is refused for that sheet.
  prompt   the sheet's own generation prompt lists its cards ("01 torso FRONT, 02 torso BACK ...") and the
           count matches.
  clip     otherwise: zero-shot OpenCLIP tag (coarse kind only; limbs stay 'limb', state 'unassigned').
Pivots are the brass brads read off each card (cutter.brads); when a card has no readable brad the pivot is
constructed and flagged. Scale (px per cm) is per sheet: the median of every card that can be measured
against the character's skeleton (kit.py humanoid from height_cm): limb brad spans, torso neck-hip, hand
wrist-tip, head crown-neck, foot heel-toe. Existing cut libraries are registered as they are, with their own
sockets where they were placed by hand (arena/parts/registered.json, weave cast.json) and provenance.
"""
import csv, glob, json, math, os, re, statistics, sys
from collections import Counter, defaultdict
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cutter
import sheets as SH

SHOTS = SH.SHOTS
SUITE = os.path.join(SHOTS, 'suite')
CUT_OUT = os.path.join(SUITE, 'parts', 'cut')
rel = lambda p: os.path.relpath(p, SHOTS)
KL = json.load(open(os.path.join(SUITE, 'data', 'kit_layouts.json')))
KITS = SH.KITS
CAST = {c['id']: c for c in KITS['cast']}
COSTUME_POEMS = {(c['id'], k['costume']): k['poems'] for c in KITS['cast'] for k in c['costumes']}
VIEWS = ('front', 'threequarter', 'profile', 'threequarter_back', 'back')
PARENT = {'head': 'torso', 'torso': 'pelvis', 'pelvis': None, 'upper_arm': 'torso', 'forearm': 'upper_arm', 'hand': 'forearm',
          'thigh': 'pelvis', 'shin': 'thigh', 'foot': 'shin', 'eye': 'head', 'mouth': 'head', 'brow': 'head', 'nose': 'head',
          'glasses': 'head', 'face_plate': 'torso', 'limb': None, 'replacement': None, 'prop': 'hand', 'wing': 'torso', 'accessory': 'head'}
CATEGORY = {'hand': 'hands', 'foot': 'feet', 'head': 'heads', 'face_plate': 'heads', 'eye': 'face', 'mouth': 'face', 'brow': 'face',
            'nose': 'face', 'glasses': 'face', 'accessory': 'face', 'upper_arm': 'limbs', 'forearm': 'limbs', 'thigh': 'limbs',
            'shin': 'limbs', 'limb': 'limbs', 'torso': 'body', 'pelvis': 'body', 'wing': 'body', 'replacement': 'replacement', 'prop': 'prop'}
COARSE = {'upper_arm': 'limb', 'forearm': 'limb', 'thigh': 'limb', 'shin': 'limb', 'face_plate': 'head', 'pelvis': 'torso'}

# --------------------------------------------------------------- characters, builds, skeleton expectations
EXTRA_BUILD = {'-': None}


def build_of(char):
    c = CAST.get(char)
    return c['build'] if c else None


def height_of(char):
    c = CAST.get(char)
    return c['height_cm'] if c else None


def expected_cm(build, part, side='L'):
    """The layout's length for a measurable span of this part, in cm (from the build's skeleton/templates)."""
    if not build:
        return None
    B = KL['builds'][build]
    sk = B['skeleton_cm']
    L = B['layouts']
    if part in ('upper_arm', 'forearm', 'thigh', 'shin'):
        return sk[{'upper_arm': 'uarm', 'forearm': 'farm', 'thigh': 'thigh', 'shin': 'shin'}[part]]
    if part == 'torso':
        return sk['torso']
    if part == 'hand':
        return sk['hand']
    if part == 'head':
        h = L['heads.blank']
        return round((h['front']['neck'][1] - h['front']['crown'][1]) / h['px_per_cm'], 2)
    if part == 'face_plate':
        f = L['face.front']
        return round((f['plate']['neck'][1] - f['plate']['crown'][1]) / f['px_per_cm'], 2)
    if part == 'foot':
        f = L['feet.R']['flat']
        return round((f['toe'][0] - f['heel'][0]) / f['px_per_cm'], 2)
    return None


# --------------------------------------------------------------- layout orders
BODY13 = [('torso', '-'), ('upper_arm', 'L'), ('forearm', 'L'), ('hand', 'L'), ('upper_arm', 'R'), ('forearm', 'R'), ('hand', 'R'),
          ('thigh', 'L'), ('shin', 'L'), ('foot', 'L'), ('thigh', 'R'), ('shin', 'R'), ('foot', 'R')]
BODY14 = BODY13[:1] + [('pelvis', '-')] + BODY13[1:]
PROF7 = [('torso', '-'), ('upper_arm', 'L'), ('forearm', 'L'), ('hand', 'L'), ('thigh', 'L'), ('shin', 'L'), ('foot', 'L')]
PROF8 = PROF7[:1] + [('pelvis', '-')] + PROF7[1:]
HS = ['relaxed', 'open', 'fist', 'grip', 'pinch', 'point', 'thumb', 'peace', 'wave', 'claw', 'cup', 'flat_push']
HANDS24 = [('hand', 'R', f'{s}.{f}') for half in (HS[:6], HS[6:]) for f in ('back', 'palm') for s in half]
HEADS = ['front', 'threequarter', 'profile', 'threequarter_back', 'back']
FEET6 = [('profile', 'flat'), ('profile', 'heel_up'), ('profile', 'toe_up'), ('front', 'flat'), ('back', 'flat'), ('threequarter', 'flat')]
EYES = ['open', 'wide', 'half', 'closed', 'squint', 'happy_arc', 'sad', 'glance_side']
BROWS = ['rest', 'raised', 'knit', 'sad', 'one_up', 'angry']
MOUTHS = ['rest', 'smile', 'grin_teeth', 'open_O', 'open_A', 'E', 'U', 'M_B_P', 'F_V', 'frown', 'strain_teeth', 'wavy']
REPL6 = ['sit', 'kneel', 'lie_back', 'lie_side', 'deep_crouch', 'fall']
HIPCORE5 = [('torso', '-', 'front'), ('torso', '-', 'back'), ('pelvis', '-', 'waist_link'), ('pelvis', '-', 'hip_bridge'), ('pelvis', '-', 'rear_seat')]


def rows(cards):
    """Reading order: cards whose vertical extents overlap by >=35% of the shorter one share a row."""
    rs = []
    for c in sorted(cards, key=lambda c: c['bbox_sheet'][1] + c['bbox_sheet'][3] / 2):
        x, y, w, h = c['bbox_sheet']
        for r in rs:
            ov = min(r['y1'], y + h) - max(r['y0'], y)
            if ov >= 0.35 * min(h, r['y1'] - r['y0']):
                r['c'].append(c); r['y0'] = min(r['y0'], y); r['y1'] = max(r['y1'], y + h)
                break
        else:
            rs.append({'y0': y, 'y1': y + h, 'c': [c]})
    rs.sort(key=lambda r: r['y0'])
    return [c for r in rs for c in sorted(r['c'], key=lambda c: c['bbox_sheet'][0])], len(rs)


def layout_labels(kind, view, cards):
    """[(part, side, view, state)] in reading order, or None if the count does not fit the layout."""
    n = len(cards)
    k = kind
    if k == 'body':
        v = view
        if v == 'profile':
            L = PROF7 if n == 7 else PROF8 if n == 8 else None
        else:
            L = BODY13 if n == 13 else BODY14 if n == 14 else None
        return None if L is None else (rows(cards)[0], [(p, s, v, 'rest') for p, s in L])
    if k == 'hands' and n == 24:
        return rows(cards)[0], [(p, s, 'flat', st) for p, s, st in HANDS24]
    if k == 'heads' and n in (5, 10):
        order, nr = rows(cards)
        lab = [('head', '-', HEADS[i % 5], 'blank' + ('' if n == 5 else ('.row1' if i < 5 else '.row2'))) for i in range(n)]
        return order, lab
    if k == 'feet' and n == 6:
        return rows(cards)[0], [('foot', 'R', v, st) for v, st in FEET6]
    if k == 'face' and n == 27:
        plate = max(cards, key=lambda c: c['alpha_px'])
        rest, _ = rows([c for c in cards if c is not plate])
        lab = [('face_plate', '-', view, 'blank')] + [('eye', '-', view, e) for e in EYES] + [('brow', '-', view, b) for b in BROWS] + \
              [('mouth', '-', view, m) for m in MOUTHS]
        return [plate] + rest, lab
    if k == 'replacements' and n == 6 and view is None:
        return rows(cards)[0], [('replacement', '-', 'profile' if r in ('sit', 'lie_side') else 'threequarter', r) for r in REPL6]
    if k == 'hipcore' and n == 5:
        return rows(cards)[0], [(p, s, 'back' if st == 'back' or st == 'rear_seat' else 'front', st) for p, s, st in HIPCORE5]
    return None


WORDS = [('upper ?arm', 'upper_arm'), ('forearm', 'forearm'), ('thigh', 'thigh'), ('shin', 'shin'), ('hand', 'hand'), ('torso', 'torso'),
         ('hip bridge|waist link|rear seat|pelvis|hip', 'pelvis'), ('foot|shoe|boot', 'foot'), ('brow', 'brow'), ('eye', 'eye'),
         ('mouth', 'mouth'), ('nose', 'nose'), ('glasses', 'glasses'), ('head', 'head'), ('wing', 'wing')]


def parse_label(t):
    s = t.lower()
    part = next((p for pat, p in WORDS if re.search(r'\b(' + pat + r')', s)), None)
    side = 'L' if re.search(r'\bl\b', s) else 'R' if re.search(r'\br\b', s) else '-'
    view = next((v for v in ('threequarter_back', 'threequarter', 'profile', 'front', 'back') if v.replace('_', ' ') in s.replace('-', ' ') or v in s), None)
    if 'rear' in s and not view:
        view = 'back'
    st = re.sub(r'\b(l|r|front|back|profile|threequarter)\b', '', s).strip(' -/')
    if part is None:
        return ('replacement', '-', view or 'unknown', re.sub(r'\s+', '_', s.strip())[:40])
    return (part, side, view or 'unknown', re.sub(r'\s+', '_', st)[:40] or 'rest')


def prompt_runs(t):
    items = [(int(m.group(1)), m.group(2).strip()) for m in
             re.finditer(r'\b(\d{2})[\s.:)-]+([A-Za-z][A-Za-z _/\-]{1,40}?)(?=\s*(?:[,;(]|\d{2}\b|$|\.))', t or '')]
    best, cur = [], []
    for n, l in items:
        if n == len(cur) + 1:
            cur.append(l)
        elif n == 1:
            cur = [l]
        if len(cur) > len(best):
            best = list(cur)
    return best


# --------------------------------------------------------------- pivots and sockets from brads
def axis_end(alpha, p, far=True):
    ys, xs = np.nonzero(alpha)
    if len(xs) == 0:
        return p
    d = (xs - p[0]) ** 2 + (ys - p[1]) ** 2
    i = int(np.argmax(d)) if far else int(np.argmin(d))
    return [float(xs[i]), float(ys[i])]


def layout_ends(a):
    """kit.py draws a limb card as a capsule with brad A half a card-width in from the top end and B half a
    width in from the bottom end. Returns [A, B] by that rule for an upright (or lying) card."""
    ys, xs = np.nonzero(a)
    h, w = a.shape
    if h >= w:
        y0, y1 = ys.min(), ys.max()
        width = np.median([np.ptp(xs[ys == y]) + 1 for y in range(int(y0 + 0.3 * (y1 - y0)), int(y0 + 0.7 * (y1 - y0)), 4) if (ys == y).any()] or [w])
        top_x = xs[ys <= y0 + width / 2].mean()
        bot_x = xs[ys >= y1 - width / 2].mean()
        return [[float(top_x), float(y0 + width / 2)], [float(bot_x), float(y1 - width / 2)]]
    x0, x1 = xs.min(), xs.max()
    width = np.median([np.ptp(ys[xs == x]) + 1 for x in range(int(x0 + 0.3 * (x1 - x0)), int(x0 + 0.7 * (x1 - x0)), 4) if (xs == x).any()] or [h])
    return [[float(x0 + width / 2), float(ys[xs <= x0 + width / 2].mean())], [float(x1 - width / 2), float(ys[xs >= x1 - width / 2].mean())]]


def sockets_for(part, side, view, rgba, br):
    """pivot, sockets, how. Coordinates are card px."""
    a = rgba[:, :, 3] > 128
    h, w = a.shape
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return [w / 2, h / 2], {}, 'empty'
    cx, cy = float(xs.mean()), float(ys.mean())
    top = [float(xs[ys == ys.min()].mean()), float(ys.min())]
    bot = [float(xs[ys == ys.max()].mean()), float(ys.max())]
    B = sorted(([b['x'], b['y']] for b in br), key=lambda q: q[1])
    r1 = lambda q: [round(q[0], 1), round(q[1], 1)]
    if part in ('upper_arm', 'forearm', 'thigh', 'shin', 'limb'):
        ends = layout_ends(a)
        if len(B) >= 2:
            A, Bq = B[0], B[-1]
            if h < w:  # lying card: proximal brad is the left one
                A, Bq = sorted([B[0], B[-1]], key=lambda q: q[0])
            return r1(A), {'A': r1(A), 'B': r1(Bq)}, 'brads'
        if len(B) == 1:
            far = max(ends, key=lambda q: math.dist(q, B[0]))
            return r1(B[0]), {'A': r1(B[0]), 'B': r1(far)}, 'brad+layout_rule'
        return r1(ends[0]), {'A': r1(ends[0]), 'B': r1(ends[1])}, 'layout_rule'
    if part == 'torso':
        S = {}
        if B:
            upper = [q for q in B if q[1] < cy]
            lower = [q for q in B if q[1] >= cy]
            mid = [q for q in upper if abs(q[0] - cx) < 0.18 * w]
            sides = [q for q in upper if abs(q[0] - cx) >= 0.18 * w]
            S['neck'] = r1(min(mid, key=lambda q: q[1])) if mid else r1(top)
            for q in sides:
                # actor L is viewer right in front view
                S['shoulder_' + ('L' if (q[0] > cx) == (view != 'back') else 'R')] = r1(q)
            lm = [q for q in lower if abs(q[0] - cx) < 0.18 * w]
            ls = [q for q in lower if abs(q[0] - cx) >= 0.18 * w]
            if lm:
                S['waist'] = r1(max(lm, key=lambda q: q[1]))
            for q in ls:
                S['hip_' + ('L' if (q[0] > cx) == (view != 'back') else 'R')] = r1(q)
            piv = S.get('waist') or S.get('neck')
            return piv, S, 'brads'
        return r1(bot), {'neck': r1(top), 'waist': r1(bot)}, 'constructed_ends'
    if part == 'pelvis':
        if B:
            S = {'waist': r1(B[0])}
            for q in B[1:]:
                S['hip_' + ('L' if q[0] > cx else 'R')] = r1(q)
            return r1(B[0]), S, 'brads'
        return r1(top), {'waist': r1(top)}, 'constructed_ends'
    if part == 'hand':
        wrist = B[0] if B else None
        if wrist is None:
            # the tab end: the alpha extreme nearest the card's narrow end (top for upright cards, left for lying)
            wrist = top if h >= w else [float(xs.min()), float(ys[xs == xs.min()].mean())]
            how = 'constructed_tab'
        else:
            how = 'brad'
        tip = axis_end(a, wrist)
        lerp = lambda t: [wrist[0] + t * (tip[0] - wrist[0]), wrist[1] + t * (tip[1] - wrist[1])]
        return r1(wrist), {'wrist': r1(wrist), 'palm': r1(lerp(0.5)), 'grip': r1(lerp(0.62)), 'tip': r1(tip)}, how
    if part == 'foot':
        ank = B[0] if B else top
        band = ys >= ys.max() - max(2, 0.06 * h)
        bx = xs[band]
        lo, hi = float(bx.min()), float(bx.max())
        sole = float(ys.max())
        if view in ('front', 'back'):
            heel, toe = [cx, sole], [cx, sole]
        elif abs(ank[0] - lo) < abs(ank[0] - hi):
            heel, toe = [lo, sole], [hi, sole]
        else:
            heel, toe = [hi, sole], [lo, sole]
        return r1(ank), {'ankle': r1(ank), 'heel': r1(heel), 'toe': r1(toe)}, 'brad' if B else 'constructed_top'
    if part in ('head', 'face_plate'):
        neck = B[-1] if B else bot
        crown = top
        # the layout's own ratios (kit.py heads/face templates): eyes 0.356, mouth 0.585 of crown->neck; chin just below the mouth
        lerp = lambda t: [crown[0] + t * (neck[0] - crown[0]), crown[1] + t * (neck[1] - crown[1])]
        S = {'neck': r1(neck), 'crown': r1(crown)}
        if view not in ('back',):
            S.update(eyes=r1(lerp(0.356)), mouth=r1(lerp(0.585)), chin=r1(lerp(0.70)))
        return r1(neck), S, 'brad' if B else 'constructed_bottom'
    if part == 'replacement':
        if B:
            hip = min(B, key=lambda q: abs(q[1] - cy))
            return r1(hip), {'hip': r1(hip), **{f'brad{i}': r1(q) for i, q in enumerate(B)}}, 'brads'
        return r1([cx, cy]), {'hip': r1([cx, cy])}, 'constructed_centroid'
    if part == 'prop':
        if B:
            return r1(B[0]), {'grip': r1(B[0])}, 'brad'
        return r1([cx, cy]), {'grip': r1([cx, cy])}, 'constructed_centroid'
    return r1([cx, cy]), {'center': r1([cx, cy])}, 'centroid'


def measure_span(part, sockets, rgba):
    """Pixel length of the span that expected_cm() describes, or None."""
    d = lambda p, q: math.dist(p, q)
    if part in ('upper_arm', 'forearm', 'thigh', 'shin') and 'A' in sockets and 'B' in sockets:
        return d(sockets['A'], sockets['B'])
    if part == 'torso' and 'neck' in sockets and 'waist' in sockets:
        return d(sockets['neck'], sockets['waist'])
    if part == 'hand' and 'wrist' in sockets and 'tip' in sockets:
        return d(sockets['wrist'], sockets['tip'])
    if part in ('head', 'face_plate') and 'neck' in sockets and 'crown' in sockets:
        return d(sockets['neck'], sockets['crown'])
    if part == 'foot' and 'heel' in sockets and 'toe' in sockets and sockets['heel'] != sockets['toe']:
        return d(sockets['heel'], sockets['toe'])
    return None


# --------------------------------------------------------------- writing cards
def save_card(src_png, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im = cv2.imread(src_png, cv2.IMREAD_UNCHANGED)
    cv2.imwrite(out_path, im, [cv2.IMWRITE_WEBP_QUALITY, 86])
    return im


def poems_for(char, costume, sheet_poems):
    if sheet_poems:
        return sorted(sheet_poems)
    return COSTUME_POEMS.get((char, costume), [])


def costume_of(sid, char):
    t = sid.split('.')
    if char in CAST:
        names = {k['costume'] for k in CAST[char]['costumes']}
        for x in t:
            if x in names:
                return x
    if len(t) > 2 and re.match(r'\d\d$', t[1]):
        return t[2] if len(t) > 3 and t[2] not in ('action', 'main-poses') else 'poem' + t[1]
    return t[1] if len(t) > 1 else '-'


def register_cut_sheets(work, parts, sheets_out, stats):
    C = json.load(open(os.path.join(work, 'cuts.json')))
    CL = json.load(open(os.path.join(work, 'clip.json')))
    P = {}
    for f in glob.glob(os.path.join(SHOTS, 'kits/packs/poem_*/prompts.json')):
        for x in json.load(open(f)):
            P.setdefault(x['id'], x.get('final_revision_prompt') or x.get('generation_prompt') or '')
    rel_cat = json.load(open(os.path.join(SHOTS, 'arena/parts/kit3/release_v2/release_catalog.json')))
    REL = {s['id']: s for s in rel_cat['sheets']}
    inv = {s['id']: s for s in SH.inventory()}
    for sid, res in sorted(C.items()):
        S = inv[sid]
        bare = sid.split(':')[-1]
        char = S.get('character') or '-'
        kind, view = S['kind'] if isinstance(S['kind'], (list, tuple)) else (S['kind'], None)
        cards = [p for p in res.get('parts', []) if p['role'] == 'working_part']
        refs = [p for p in res.get('parts', []) if p['role'] != 'working_part']
        # drop printed text / ruler / title cards
        junk = [p for p in cards if CL.get(p['abs'], {}).get('text', 0) > 0.6 or
                (CL.get(p['abs'], {}).get('wordness', 0) >= 0.78 and not p['brads'])]
        cards = [p for p in cards if p not in junk]
        stats['dropped_text'] += len(junk)
        stats['dropped_reference_proofs'] += len(refs)
        method, labels = 'clip', None
        if S['subfolder'] if 'subfolder' in S else False:
            pass
        ll = layout_labels(kind, view, cards) if kind and kind != 'body' else None
        if kind == 'body' and cards:
            lab, typed = typed_body(view, cards, CL)
            method, labels = ('layout' if typed else 'layout_partial'), lab
            stats['body_typed' if typed else 'body_partial'] += 1
        if ll:
            order, lab = ll
            agree = sum(1 for c, l in zip(order, lab) if coarse_ok(l[0], CL.get(c['abs'], {})))
            if agree >= 0.6 * len(order):
                method, labels = 'layout', list(zip(order, lab))
                stats['layout_agree'].append(agree / len(order))
            else:
                stats['layout_refused'].append((sid, round(agree / len(order), 2)))
        if labels is None:
            L = prompt_runs(P.get(bare, ''))
            if L and len(L) == len(cards):
                order, _ = rows(cards)
                method, labels = 'prompt', [(c, parse_label(t)) for c, t in zip(order, L)]
        if labels is None:
            labels = []
            for c in rows(cards)[0]:
                tag = CL.get(c['abs'], {})
                k = clip_kind(c, tag, res.get('height') or 1000)
                if S.get('subfolder') == '03_PROPS' and k not in ('hand',):
                    k = 'prop'
                v = view or guess_view(bare)
                labels.append((c, (k, '-', v, 'unassigned' if k == 'limb' else 'rest')))
        build = build_of(char)
        cos = 'soul' if S.get('role') == 'soul' else costume_of(bare, char)
        poems = poems_for(char, cos, S.get('poems'))
        rel_parts = {}
        rs = REL.get(bare)
        if rs:
            for rp in rs['parts']:
                rel_parts[tuple(rp['bbox_sheet'])] = rp
        built = []
        seen = Counter()
        for c, (part, side, v, st) in labels:
            rgba = cv2.imread(c['abs'], cv2.IMREAD_UNCHANGED)
            br = c['brads']
            piv, sock, how = sockets_for(part, side, v, rgba, br)
            base = f"{part}.{side}.{v}.{st}".replace('-.', '').replace('..', '.')
            seen[base] += 1
            name = base + (f'.{seen[base]}' if seen[base] > 1 else '')
            pid = f"{sid}/{name}"
            existing = rel_parts.get(tuple(c['bbox_sheet']))
            ex_file = existing and os.path.join(SHOTS, existing['file'])
            if ex_file and os.path.exists(ex_file):
                im = cv2.imread(ex_file, cv2.IMREAD_UNCHANGED)
                if im is not None and im.shape[:2] == rgba.shape[:2]:
                    f, prov = existing['file'], f"cut earlier by arena/parts/kit3/cut_release_kits.py ({existing['id']}); named, pivoted, scaled here"
                    stats['reused_release_files'] += 1
                else:
                    ex_file = None
            if not (ex_file and os.path.exists(ex_file)):
                out = os.path.join(CUT_OUT, sid.replace(':', '__'), name + '.webp')
                save_card(c['abs'], out)
                f, prov = rel(out), 'cut here by shots/suite/tools/cut_all.py (release cutter on a flattened ground)'
                stats['new_cut_files'] += 1
            tag = CL.get(c['abs'], {})
            built.append(dict(id=pid, character=char, costume=cos, role=S.get('role'), part=part, side=side, view=v, state=st,
                              category=CATEGORY.get(part, 'other'), file=f, w=int(rgba.shape[1]), h=int(rgba.shape[0]), pivot=piv,
                              parent_part=PARENT.get(part), sockets=sock, pivot_source=how, brads=len(br),
                              sheet=S['file'], sheet_id=bare, bbox_sheet=c['bbox_sheet'], poems=poems, painted=True, paint='painted',
                              label_method=method, clip=round(tag.get(COARSE.get(part, part), 0), 2) if tag else None,
                              provenance=prov, _rgba_span=measure_span(part, sock, rgba)))
        # sheet scale: median of measurable cards against the skeleton
        est = []
        for p in built:
            e = expected_cm(build, p['part'])
            # trust: hands and heads are recognisable whatever named them; limbs, torsos and feet only when the
            # layout or the prompt named them (CLIP cannot tell a thigh from a forearm, or a profile foot from a front one)
            trusted = trusted_for_scale(p)
            if e and p['_rgba_span'] and trusted:
                est.append((p['id'], p['_rgba_span'] / e))
        ppc = statistics.median([x for _, x in est]) if est else None
        lay_ppc = None
        if kind in ('body', 'hands', 'heads', 'feet', 'face', 'replacements') and S['group'] in ('poem_kit', 'kit3_v2_render'):
            base_ppc = {'body': 6.0, 'hands': 11.0, 'heads': 12.0, 'feet': 11.0, 'face': 14.0, 'replacements': 4.6}[kind]
            if build == 'dotd' and kind == 'body':
                base_ppc = 9.0
            lay_ppc = round(base_ppc * res['width'] / 2048.0, 3)
        for p in built:
            if ppc:
                loo = [x for i, x in est if i != p['id']]
                p['scale'] = {'px_per_cm': round(ppc, 3), 'source': f"sheet median of {len(est)} cards measured against {build} skeleton "
                                                                   f"({CAST[char]['height_cm'] if char in CAST else '?'} cm)",
                              'n': len(est), 'layout_px_per_cm': lay_ppc,
                              'loo_px_per_cm': round(statistics.median(loo), 3) if loo else None}

            else:
                p['scale'] = {'px_per_cm': None, 'source': 'unmeasured: no card on this sheet has a trusted skeleton span (the layout px/cm '
                                                           'is not used: painters did not keep the layout scale)', 'n': 0, 'layout_px_per_cm': lay_ppc}
            p['height_cm_real'] = round(p['h'] / p['scale']['px_per_cm'], 1) if p['scale']['px_per_cm'] else None
            p['char_height_cm'] = height_of(char)
        parts.extend(built)
        sheets_out.append(dict(id=sid, file=S['file'], group=S['group'], character=char, kind=[kind, view], cards=len(cards),
                               dropped_text=len(junk), reference_proofs=len(refs), label_method=method,
                               px_per_cm=round(ppc, 3) if ppc else None, layout_px_per_cm=lay_ppc, n_scale=len(est),
                               cards_with_brads=sum(1 for p in built if p['brads']), previously_cut=S.get('previously_cut')))


def trusted_for_scale(p):
    """Cards whose skeleton span can be trusted: hands and heads (recognisable whatever named them); limbs, torsos
    and flat profile feet only when the layout or the prompt named them."""
    if p['pivot_source'] in ('constructed_tab', 'constructed_bottom'):
        return False
    if p['part'] in ('hand', 'head', 'face_plate'):
        return True
    if p['label_method'] not in ('layout', 'prompt', 'manifest', 'filename', 'assets.json', 'library.json') or p['view'] == 'unknown':
        return False
    if p['part'] == 'foot':
        return p['view'] == 'profile' and p['state'] in ('flat', 'rest')
    return p['part'] in ('upper_arm', 'forearm', 'thigh', 'shin', 'torso')


def clip_kind(c, tag, sheet_h):
    """CLIP's top kind, corrected by two shape facts CLIP gets wrong: a long capsule with a brad at each end is a
    limb segment (CLIP often calls it a foot); a face feature is small (a card taller than 22% of the sheet that
    CLIP calls an eye/mouth/nose/brow is a head in profile)."""
    if not tag:
        return 'prop'
    rank = sorted((x for x in tag if x not in ('text', 'wordness')), key=lambda x: -tag[x])
    k = rank[0]
    x, y, w, h = c['bbox_sheet']
    el = max(w, h) / max(1, min(w, h))
    if k in ('foot', 'torso', 'pelvis', 'prop') and el >= 2.3 and len(c['brads']) >= 2:
        return 'limb'
    if k in ('eye', 'mouth', 'nose', 'brow', 'glasses') and h > 0.22 * sheet_h:
        return next((r for r in rank if r not in ('eye', 'mouth', 'nose', 'brow', 'glasses')), 'head')
    return k


def coarse_ok(part, tag):
    if not tag:
        return True
    want = COARSE.get(part, part)
    top = sorted(((v, k) for k, v in tag.items() if k not in ('text', 'wordness')), reverse=True)[:2]
    ok = {k for _, k in top}
    if want == 'limb':
        return bool(ok & {'limb', 'torso', 'pelvis', 'prop', 'foot', 'wing'})
    if want == 'replacement':
        return bool(ok & {'replacement', 'torso', 'pelvis', 'limb', 'prop', 'wing', 'foot'})
    if want == 'face_plate':
        want = 'head'
    return want in ok


def typed_body(view, cards, CL):
    """Body sheets: the layout's slots, filled by kind rather than by strict reading order (painters keep the
    slots but not always the order: some put both hands after the four arm segments). torso = the largest card;
    hands / feet = the cards CLIP is surest are hands / feet (two each, one in profile), left to right = L, R;
    the elongated rest are limb segments, read in rows in the layout's own sequence (upper arm, forearm, [upper arm,
    forearm,] thigh, shin, [thigh, shin]). Anything left over is named by CLIP."""
    tag = lambda c: CL.get(c['abs'], {})
    rem = list(cards)
    out = []
    nside = 1 if view == 'profile' else 2
    sides = ['L', 'R'][:nside]
    torso = max(rem, key=lambda c: c['alpha_px'] * (1.0 if tag(c).get('torso', 0) > 0.2 else 0.4))
    rem.remove(torso)
    out.append((torso, ('torso', '-', view, 'rest')))
    for kind in ('hand', 'foot'):
        cand = sorted([c for c in rem if tag(c).get(kind, 0) > 0.5], key=lambda c: -tag(c)[kind])[:nside]
        cand.sort(key=lambda c: c['bbox_sheet'][0])
        for c, sd in zip(cand, sides):
            out.append((c, (kind, sd, view, 'rest')))
            rem.remove(c)
    for c in [c for c in rem if tag(c) and max((k for k in tag(c) if k != 'wordness'), key=tag(c).get) == 'head']:
        out.append((c, ('head', '-', view, 'painted')))
        rem.remove(c)
    elong = lambda c: max(c['bbox_sheet'][2], c['bbox_sheet'][3]) / max(1, min(c['bbox_sheet'][2], c['bbox_sheet'][3])) >= 1.8
    limbs = sorted([c for c in rem if elong(c)], key=lambda c: -c['alpha_px'])[:4 * nside]
    rest = [c for c in rem if c not in limbs]
    pel = [c for c in rest if tag(c).get('pelvis', 0) > 0.4]
    if pel:
        c = max(pel, key=lambda c: c['alpha_px'])
        out.append((c, ('pelvis', '-', view, 'rest')))
        rest.remove(c)
    if len(limbs) == 4 * nside:
        # the layout's sequence, read in rows: uarm, farm, (uarm, farm,) thigh, shin, (thigh, shin)
        seq = [('upper_arm', 'L'), ('forearm', 'L')] + ([('upper_arm', 'R'), ('forearm', 'R')] if nside == 2 else []) + \
              [('thigh', 'L'), ('shin', 'L')] + ([('thigh', 'R'), ('shin', 'R')] if nside == 2 else [])
        for c, (pt, sd) in zip(rows(limbs)[0], seq):
            out.append((c, (pt, sd, view, 'rest')))
        typed = True
    else:
        rest += limbs
        typed = False
    for c in rest:
        t = tag(c)
        k = clip_kind(c, t, 1000)
        out.append((c, (k, '-', view, 'unassigned' if k == 'limb' else 'rest')))
    return out, typed


def guess_view(sid):
    for v in ('threequarter_back', 'threequarter', 'profile', 'front', 'back'):
        if v in sid:
            return v
    return 'unknown'


# --------------------------------------------------------------- existing libraries (registered as they are)
def card_info(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None, []
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGRA)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im, cutter.brads(im)


V2NAME = [(r'^body\.(\w+)\.(torso|pelvis)(\.true)?$', lambda m: (m.group(2), '-', m.group(1), 'true' if m.group(3) else 'rest')),
          (r'^body\.(\w+)\.(uarm|farm|thigh|shin|hand|foot)\.([LR])$', lambda m: ({'uarm': 'upper_arm', 'farm': 'forearm'}.get(m.group(2), m.group(2)), m.group(3), m.group(1), 'rest')),
          (r'^face\.(\w+)\.(eyes|brows|mouth)\.(\w+)$', lambda m: ({'eyes': 'eye', 'brows': 'brow'}.get(m.group(2), m.group(2)), '-', m.group(1), m.group(3))),
          (r'^face\.(\w+)\.plate$', lambda m: ('face_plate', '-', m.group(1), 'blank')),
          (r'^face\.(\w+)\.glasses$', lambda m: ('glasses', '-', m.group(1), 'sunglasses')),
          (r'^hand\.([LR])\.(\w+)\.(back|palm)$', lambda m: ('hand', m.group(1), 'flat', f'{m.group(2)}.{m.group(3)}')),
          (r'^foot\.([LR])\.(\w+)$', lambda m: ('foot', m.group(1), m.group(2) if m.group(2) in VIEWS else 'profile', m.group(2) if m.group(2) not in VIEWS else 'flat')),
          (r'^head\.(\w+?)(\.blank|_B)?$', lambda m: ('head', '-', m.group(1), 'blank' if m.group(2) == '.blank' else 'painted' + ('_B' if m.group(2) == '_B' else ''))),
          (r'^replacement\.(\w+)$', lambda m: ('replacement', '-', 'unknown', m.group(1))),
          (r'^hand\.\d+_(.+)$', lambda m: ('hand', '-', 'flat', m.group(1))),
          (r'^pose\.\d+_(\w+?)_(front|threequarter_back|threequarter|profile|back)$', lambda m: ('replacement', '-', m.group(2), m.group(1))),
          (r'^prop\.(.+)$', lambda m: ('prop', '-', '-', m.group(1)))]
V2PPC = {'body': 6.0, 'face': 14.0, 'hand': 11.0, 'foot': 11.0, 'head': 12.0, 'replacement': 4.6}


def register_v2_parts(parts, stats):
    root = os.path.join(SHOTS, 'arena/parts/kit3/v2/parts')
    for d in sorted(glob.glob(os.path.join(root, '*'))):
        kid = os.path.basename(d)
        t = kid.split('.')
        char = t[0] if t[0] in CAST else '-'
        cos = t[1] if len(t) > 1 else '-'
        build = build_of(char)
        action = len(t) > 2 and t[2] == 'action'
        for f in sorted(glob.glob(os.path.join(d, '*.png'))):
            nm = os.path.basename(f)[:-4]
            lab = None
            for pat, fn in V2NAME:
                m = re.match(pat, nm)
                if m:
                    lab = fn(m); break
            if lab is None:
                stats['v2_unparsed'] += 1
                continue
            part, side, view, st = lab
            im, br = card_info(f)
            if im is None:
                continue
            piv, sock, how = sockets_for(part, side, view, im, br)
            key = nm.split('.')[0]
            ppc = None if action else V2PPC.get(key)
            if build == 'dotd' and key == 'body':
                ppc = 9.0
            poems = [t[1]] if action else COSTUME_POEMS.get((char, cos), [])
            parts.append(dict(id=f'v2parts:{kid}/{nm}', character=char, costume=('poem' + t[1]) if action else cos, part=part, side=side, view=view,
                              state=st, category=CATEGORY.get(part, 'other'), file=rel(f), w=int(im.shape[1]), h=int(im.shape[0]),
                              pivot=piv, parent_part=PARENT.get(part), sockets=sock, pivot_source=how, brads=len(br),
                              scale={'px_per_cm': ppc, 'source': 'kit layout px/cm (pasted into the template cell at template scale)' if ppc else
                                     'unmeasured (action-sheet card, free scale)'},
                              height_cm_real=round(im.shape[0] / ppc, 1) if ppc else None, char_height_cm=height_of(char),
                              sheet='arena/parts/kit3/v2/packs/' + kid + '.*', sheet_id=kid, poems=poems, painted=False, paint='composited',
                              label_method='filename', provenance='arena/parts/kit3/generate_v2_kits.py: painted_bank recolour/composite of '
                                                                  'existing painted cards into the kit template (not painted for this character)'))
            stats['v2_parts'] += 1


def register_tracksuit(parts, stats):
    root = os.path.join(SHOTS, 'kits/packs/poet_tracksuit_v1')
    man = json.load(open(os.path.join(root, 'manifest.json')))
    MAP = [('torso_front', ('torso', '-', 'front', 'rest')), ('torso_back', ('torso', '-', 'back', 'rest')), ('waist_link', ('pelvis', '-', 'front', 'waist_link')),
           ('hip_bridge', ('pelvis', '-', 'front', 'hip_bridge')), ('rear_seat', ('pelvis', '-', 'back', 'rear_seat')), ('pelvis_front', ('pelvis', '-', 'front', 'front_cover')),
           ('upper_arm', ('upper_arm',)), ('forearm', ('forearm',)), ('thigh', ('thigh',)), ('shin', ('shin',)), ('hand_', ('hand',)), ('boot', ('foot',)),
           ('head', ('head', '-', 'front', 'blank')), ('eyes', ('eye',)), ('brows', ('brow',)), ('nose', ('nose',)), ('mouth', ('mouth',)), ('sunglasses', ('glasses',))]
    items = []
    for c in man['components']:
        items.append((os.path.join(root, c['file']), c['id']))
    for sub in ('profile_face_clean',):
        for f in sorted(glob.glob(os.path.join(root, '01_COMPONENTS', sub, '*.png'))):
            items.append((f, 'profile.' + os.path.basename(f)[:-4]))
    for f in sorted(glob.glob(os.path.join(SHOTS, 'kits/packs/young_poet_v1/01_COMPONENTS/profile_face_clean/*.png'))):
        items.append((f, 'young.profile.' + os.path.basename(f)[:-4]))
    built = []
    for f, cid in items:
        young = cid.startswith('young.')
        lab = None
        for k, v in MAP:
            if k in cid:
                lab = v; break
        if lab is None and 'base_profile_head' in cid:
            lab = ('face_plate', '-', 'profile', 'blank')
        if lab is None:
            continue
        if len(lab) == 1:
            side = 'L' if cid.endswith('_L') else 'R' if cid.endswith('_R') else '-'
            view = 'profile' if 'profile' in cid else 'front'
            st = re.sub(r'^(\d+_|profile\.|young\.profile\.)', '', cid)
            lab = (lab[0], side, view, st)
        part, side, view, st = lab
        im, br = card_info(f)
        if im is None:
            continue
        piv, sock, how = sockets_for(part, side, view, im, br)
        char = 'young_poet' if young else 'poet'
        built.append(dict(id=('young_poet_v1:' if young else 'tracksuit31:') + cid, character=char, costume='child_clothes' if young else 'red_black_sunglasses',
                          part=part, side=side, view=view, state=st, category=CATEGORY.get(part, 'other'), file=rel(f), w=int(im.shape[1]), h=int(im.shape[0]),
                          pivot=piv, parent_part=PARENT.get(part), sockets=sock, pivot_source=how, brads=len(br),
                          sheet='kits/packs/poet_tracksuit_v1/03_SOURCE_SHEETS' if not young else 'kits/packs/young_poet_v1', sheet_id='tracksuit31',
                          poems=COSTUME_POEMS.get((char, 'red_black_sunglasses'), []) if not young else ['13'], painted=True, paint='painted',
                          label_method='manifest', provenance=('kits/packs/poet_tracksuit_v1 (31 individual parts, separated by the kit author)' if not young
                                                               else 'kits/packs/young_poet_v1 profile face set'),
                          _span=measure_span(part, sock, im)))
    # each component of the 31-part set was rendered to fill its own canvas (limbs 1024x1536, the rest ~1280x1230),
    # so there is no shared sheet scale: each card is scaled by its own skeleton span, or left unmeasured
    for p in built:
        char = p['character']
        e = expected_cm(build_of(char), p['part'])
        sp = p.pop('_span', None)
        ok = e and sp and p['pivot_source'] not in ('constructed_tab', 'constructed_bottom', 'constructed_top', 'constructed_ends')
        ppc = sp / e if ok else None
        p['scale'] = {'px_per_cm': round(ppc, 3) if ppc else None, 'n': 1 if ppc else 0,
                      'source': (f"own span vs {build_of(char)} skeleton (each component has its own canvas; no shared sheet scale)" if ppc
                                 else 'unmeasured: own canvas, no brad span to measure')}
        p['height_cm_real'] = round(p['h'] / ppc, 1) if ppc else None
        p['char_height_cm'] = height_of(char)
    parts.extend(built)
    stats['tracksuit_parts'] += len(built)


def register_weave_man(parts, stats):
    cast = json.load(open(os.path.join(SHOTS, 'weave/cast/man/cast.json')))['parts']
    reg = json.load(open(os.path.join(SHOTS, 'arena/parts/registered.json')))['parts']
    regby = {v['file']: (k, v) for k, v in reg.items()}
    lib = json.load(open(os.path.join(SHOTS, 'weave/cast/man/library_manifest.json')))['pieces']
    PM = {'torso': 'torso', 'pelvis': 'pelvis', 'uarm': 'upper_arm', 'farm': 'forearm', 'thigh': 'thigh', 'shin': 'shin', 'hand': 'hand',
          'boot': 'foot', 'head': 'head', 'leg': 'limb', 'arm': 'limb', 'shoe': 'foot', 'foot': 'foot', 'eyes': 'eye', 'mouth': 'mouth', 'brow': 'brow'}
    items = [(os.path.join(SHOTS, 'weave', v['file']), k, v, 'weave/cast/man/cast.json') for k, v in cast.items()]
    seen = {os.path.normpath(i[0]) for i in items}
    for k, v in lib.items():
        f = os.path.join(SHOTS, 'weave', v['file'])
        if os.path.normpath(f) in seen:
            continue
        items.append((f, k, v, 'weave/cast/man/library_manifest.json'))
    for f in sorted(glob.glob(os.path.join(SHOTS, 'weave/cast/man/parts/*.png'))):
        if os.path.normpath(f) not in {os.path.normpath(i[0]) for i in items}:
            items.append((f, os.path.basename(f)[:-4], {}, 'weave/cast/man/parts'))
    built = []
    for f, k, v, src in items:
        if not os.path.exists(f):
            stats['missing_files'] += 1
            continue
        t = k.split('.')
        if k.startswith('proc.') or k.startswith('man.crouch.'):
            t = t[1:] if k.startswith('proc.') else ['crouch_' + t[-1]]
        part = PM.get(t[0], 'prop' if v.get('category') == 'prop' else ('replacement' if v.get('category') == 'contact' else None))
        if part is None and t[0].startswith('crouch_'):
            part = {'crouch_arm': 'limb', 'crouch_legs': 'limb', 'crouch_head': 'head', 'crouch_torso': 'torso'}.get(t[0], 'replacement')
        if part is None and re.match(r'(body_|draft_)', k):
            part = 'clip?'
        if part is None:
            part = {'hand': 'hand', 'head': 'head', 'leg': 'limb'}.get(v.get('category'), 'accessory')
        view = next((x for x in VIEWS if x in k), 'threequarter' if '.3q' in k or '3q.' in k else 'unknown')
        side = 'L' if k.endswith('.L') or '.near' in k else 'R' if k.endswith('.R') or '.far' in k else '-'
        st = re.sub(r'^(torso|pelvis|uarm|farm|thigh|shin|hand|boot|head|leg|arm|shoe|foot)\.?', '', k) or 'rest'
        im, br = card_info(f)
        if im is None:
            continue
        rk = regby.get(rel(f))
        if rk:
            sock = {kk: [float(x) for x in vv] for kk, vv in rk[1]['sockets'].items()}
            piv = sock.get('A') or next(iter(sock.values()))
            how = 'placed by hand (arena/parts/registered.json)'
        elif v.get('sockets'):
            sock = {kk: [float(x) for x in vv] for kk, vv in v['sockets'].items()}
            piv = [float(x) for x in v.get('pivot', next(iter(sock.values())))]
            how = 'weave cast.json'
        else:
            piv, sock, how = sockets_for(part, side, view, im, br)
        built.append(dict(id='weave_man:' + k, character='poet', costume='red_black_sunglasses', part=part, side=side, view=view, state=st,
                          category=CATEGORY.get(part, 'other'), file=rel(f), w=int(im.shape[1]), h=int(im.shape[0]), pivot=[round(x, 1) for x in piv],
                          parent_part=PARENT.get(part), sockets=sock, pivot_source=how, brads=len(br),
                          sheet='weave/cast/man/sheets/' + (v.get('source_sheet') or v.get('sheet') or '?'), sheet_id='weave_man',
                          poems=COSTUME_POEMS.get(('poet', 'red_black_sunglasses'), []), painted=not k.startswith('proc.'),
                          paint='coded' if k.startswith('proc.') else 'painted', label_method='filename',
                          provenance=src, _span=measure_span(part, sock, im) if part != 'limb' else None))
    # library pieces numbered off a body sheet (body_front_01 ...) are named by CLIP, as the cut sheets are
    need = [p for p in built if p['part'] == 'clip?']
    if need:
        import clip_tag
        tags = clip_tag.tag_files([os.path.join(SHOTS, p['file']) for p in need], os.path.join(WORK, 'clip_extra.json'))
        for p in need:
            im, br = card_info(os.path.join(SHOTS, p['file']))
            tg = tags.get(os.path.join(SHOTS, p['file']), {})
            c = {'bbox_sheet': [0, 0, im.shape[1], im.shape[0]], 'brads': br}
            p['part'] = clip_kind(c, tg, 10 ** 6)
            p['category'] = CATEGORY.get(p['part'], 'other')
            p['parent_part'] = PARENT.get(p['part'])
            p['label_method'] = 'clip'
            if 'draft' in p['id']:
                p['state'] = 'draft_unriggable'
            p['pivot'], p['sockets'], p['pivot_source'] = sockets_for(p['part'], '-', p['view'], im, br)
            p['_span'] = measure_span(p['part'], p['sockets'], im)
    # the library's pieces come from different sheets painted at different scales: one px/cm per source sheet
    est_all = [p['_span'] / expected_cm('poetm', p['part']) for p in built if p['_span'] and expected_cm('poetm', p['part'])]
    by_sheet = defaultdict(list)
    for p in built:
        if p['_span'] and expected_cm('poetm', p['part']):
            by_sheet[p['sheet']].append(p['_span'] / expected_cm('poetm', p['part']))
    for p in built:
        p.pop('_span', None)
        est = by_sheet.get(p['sheet'], [])
        if len(est) >= 2:
            ppc, src = statistics.median(est), f"median of {len(est)} cards of {p['sheet'].split('/')[-1]} vs poetm skeleton (184 cm)"
        else:
            ppc, src = None, 'unmeasured: fewer than 2 measurable cards on its source sheet'
        p['scale'] = {'px_per_cm': round(ppc, 3) if ppc else None, 'n': len(est), 'source': src}
        p['height_cm_real'] = round(p['h'] / ppc, 1) if ppc else None
        p['char_height_cm'] = 184
    parts.extend(built)
    stats['weave_man_parts'] += len(built)


def role_char(role):
    """play/data.json roles -> kits.json cast ids (the role stays in 'costume')."""
    if role in CAST:
        return role
    for pre, cid in (('poet_soul', 'poet'), ('angel', 'angels'), ('dj', 'party'), ('party', 'party'), ('club', 'party'), ('vintage', 'party'),
                     ('father', 'parents'), ('parent', 'parents'), ('mother', 'woman'), ('she', 'woman'), ('window_woman', 'woman'),
                     ('brother', 'family'), ('friend', 'family'), ('couple', 'family'), ('elder_man', 'family'), ('elder_woman', 'family'),
                     ('elders', 'family'), ('watcher', 'family'), ('traveler', 'atlantis'), ('citizen', 'atlantis'), ('child_traveler', 'atlantis'),
                     ('gatekeeper', 'atlantis'), ('elder_1', 'atlantis'), ('ancestor', 'ancestors'), ('young_ghost', 'ghost_child'), ('ghost', 'ghost_child'),
                     ('young', 'young_poet'), ('boy', 'young_poet')):
        if role.startswith(pre):
            return cid
    return role


def register_misc(parts, stats):
    # the woman's weave parts (p07)
    A = json.load(open(os.path.join(SHOTS, 'weave/assets/assets.json')))['assets']
    PM = {'head': 'head', 'torso': 'torso', 'skirt': 'pelvis', 'upper_arm': 'upper_arm', 'forearm': 'forearm', 'hand': 'hand', 'leg': 'limb',
          'proc.uarm': 'upper_arm', 'proc.farm': 'forearm', 'proc.thigh': 'thigh', 'proc.shin': 'shin', 'proc.boot': 'foot'}
    W = []
    for a in A:
        if a.get('kind') != 'puppet_part':
            continue
        f = os.path.join(SHOTS, 'weave', a['file'])
        im, br = card_info(f)
        if im is None:
            continue
        part = next((v for k, v in sorted(PM.items(), key=lambda kv: -len(kv[0])) if a['id'].startswith(k)), 'accessory')
        side = 'L' if 'near' in a['id'] else 'R' if 'far' in a['id'] else '-'
        coded = a['id'].startswith('proc.')
        sock = {k: [float(x) for x in v] for k, v in (a.get('sockets') or {}).items()}
        W.append(dict(id='weave_woman:' + a['id'], character='woman', costume='teal_dress', part=part, side=side, view='profile', state='rest',
                      category=CATEGORY.get(part, 'other'), file=rel(f), w=int(im.shape[1]), h=int(im.shape[0]),
                      pivot=[float(x) for x in a.get('pivot', [im.shape[1] / 2, im.shape[0] / 2])], parent_part=PARENT.get(part), sockets=sock,
                      pivot_source='weave assets.json', brads=len(br), sheet='weave/src (poet_parts_sheet.jpg)', sheet_id='weave_woman',
                      poems=['07'], painted=not coded, paint='coded' if coded else 'painted', label_method='assets.json',
                      provenance=a.get('provenance', 'weave/assets/assets.json'), scale={'px_per_cm': None, 'source': 'unmeasured', 'n': 0},
                      height_cm_real=None, char_height_cm=height_of('woman')))
    # scale from the head (crown-neck) vs the woman's layout head
    heads = [p for p in W if p['part'] == 'head']
    if heads:
        h = heads[0]
        span = h['pivot'][1]  # crown at y~0 of the card
        ppc = span / expected_cm('woman', 'head')
        for p in W:
            p['scale'] = {'px_per_cm': round(ppc, 3), 'n': 1, 'source': 'head neck pivot to card top vs woman layout head (one card)'}
            p['height_cm_real'] = round(p['h'] / ppc, 1)
    parts.extend(W)
    stats['weave_woman_parts'] += len(W)
    # code-drawn kit parts (arena/parts/library.json)
    L = json.load(open(os.path.join(SHOTS, 'arena/parts/library.json')))['parts']
    for q in L:
        f = os.path.join(SHOTS, q['file'])
        if not os.path.exists(f):
            stats['missing_files'] += 1
            continue
        kind = q.get('kind')
        part = {'hand': 'hand', 'boot': 'foot', 'farm': 'forearm', 'uarm': 'upper_arm', 'thigh': 'thigh', 'shin': 'shin', 'head': 'head',
                'torso': 'torso', 'foot': 'foot'}.get(kind, kind or 'accessory')
        sock = {k: [float(x) for x in v] for k, v in (q.get('sockets') or {}).items()}
        ppc = q.get('ppc')
        st = q.get('state')
        parts.append(dict(id='lib:' + q['id'], character='poet' if q['id'].startswith('kit.') or q['id'].startswith('man.') else q['id'].split('.')[0],
                          costume='kit_code' if q.get('source') == 'code' else '-', part=part, side=q.get('side', '-'), view=q.get('view', 'unknown'),
                          state='.'.join(str(v) for v in st.values()) if isinstance(st, dict) else (st or 'rest'), category=CATEGORY.get(part, 'other'), file=q['file'],
                          w=q['size'][0], h=q['size'][1], pivot=sock.get('A') or [q['size'][0] / 2, q['size'][1] / 2], parent_part=PARENT.get(part),
                          sockets=sock, pivot_source=q.get('socket_source', 'library.json'), brads=0, sheet='arena/parts/library.json', sheet_id='lib',
                          poems=[], painted=q.get('source') != 'code', paint='coded' if q.get('source') == 'code' else 'painted', label_method='library.json',
                          provenance=f"arena/parts/library.json ({q.get('source')})",
                          scale={'px_per_cm': ppc, 'n': 0, 'source': 'library ppc' if ppc else 'unmeasured'},
                          height_cm_real=round(q['size'][1] / ppc, 1) if ppc else None, char_height_cm=184))
        stats['library_parts'] += 1
    # arena/parts/cut (man hands/heads/legs, cut by hand from the weave sheets)
    for f in sorted(glob.glob(os.path.join(SHOTS, 'arena/parts/cut/man_*/*.png'))):
        grp = f.split('/')[-2]
        part = {'man_hands': 'hand', 'man_heads_front': 'head', 'man_heads_ie': 'head', 'man_legs': 'foot', 'man_shorts': 'pelvis', 'man_torso': 'torso'}[grp]
        nm = os.path.basename(f)[:-4]
        if grp == 'man_legs' and not nm.startswith('boot'):
            part = 'limb'
        im, br = card_info(f)
        view = 'front' if 'front' in grp or 'front' in nm else 'profile' if 'profile' in nm else 'threequarter' if grp == 'man_heads_ie' else 'unknown'
        piv, sock, how = sockets_for(part, '-', view, im, br)
        hj = os.path.join(os.path.dirname(f), 'hands.json')
        if grp == 'man_hands' and os.path.exists(hj):
            H = json.load(open(hj))
            e = next((v for k, v in H.items() if k == nm), None)
            if e:
                piv = [float(x) for x in e['A']]
                sock = {'wrist': piv, 'B': [float(x) for x in e['B']]}
                how = 'hands.json (A/B placed)'
        parts.append(dict(id=f'arena_cut:{grp}/{nm}', character='poet', costume='red_black_sunglasses', part=part, side='-', view=view, state=nm,
                          category=CATEGORY.get(part, 'other'), file=rel(f), w=int(im.shape[1]), h=int(im.shape[0]), pivot=piv, parent_part=PARENT.get(part),
                          sockets=sock, pivot_source=how, brads=len(br), sheet='weave/cast/man/sheets', sheet_id='arena_cut', poems=[], painted=True,
                          paint='painted', label_method='filename', provenance='arena/parts/cut (hand cuts of the weave man sheets)',
                          scale={'px_per_cm': None, 'n': 0, 'source': 'unmeasured'}, height_cm_real=None, char_height_cm=184))
        stats['arena_cut_parts'] += 1
    # Bolas dummies (drawn in code)
    D = json.load(open(os.path.join(SHOTS, 'arena/cast/dummy/parts.json')))
    ref_h = D.get('ref_height')
    for k, q in (D['parts'].items() if isinstance(D['parts'], dict) else enumerate(D['parts'])):
        f = q.get('file') if isinstance(q, dict) else None
        if not f:
            continue
        fp = os.path.join(SHOTS, 'arena', f)
        if not os.path.exists(fp):
            fp = os.path.join(SHOTS, 'arena/cast/dummy', os.path.basename(f))
        if not os.path.exists(fp):
            stats['missing_files'] += 1
            continue
        nm = os.path.basename(fp)[:-4]
        t = nm.split('.')
        who = t[0]
        part = {'farm': 'forearm', 'uarm': 'upper_arm', 'foot': 'foot', 'hand': 'hand', 'head': 'head', 'torso': 'torso', 'thigh': 'thigh',
                'shin': 'shin', 'pelvis': 'pelvis'}.get(t[1] if len(t) > 1 else '', 'accessory')
        im, br = card_info(fp)
        sock = {'A': [float(x) for x in q['pivot']], 'B': [float(x) for x in q['end']]} if q.get('pivot') and q.get('end') else {}
        piv = [float(x) for x in q.get('pivot', [])] if isinstance(q, dict) and q.get('pivot') else None
        if not piv:
            piv, s2, how = sockets_for(part, '-', 'profile', im, br)
            sock = sock or s2
        else:
            how = 'dummy parts.json'
        ppc = round(ref_h / height_of(who), 3) if ref_h and height_of(who) else None
        parts.append(dict(id=f'dummy:{nm}', character={'bola': 'bola', 'shim': 'shim', 'dot': 'dot'}.get(who, who), costume='dummy', part=part,
                          side='R' if 'far' in nm else 'L', view='profile', state='.'.join(t[2:]) or 'rest', category=CATEGORY.get(part, 'other'),
                          file=rel(fp), w=int(im.shape[1]), h=int(im.shape[0]), pivot=piv, parent_part=PARENT.get(part), sockets=sock, pivot_source=how,
                          brads=len(br), sheet='arena/cast/dummy', sheet_id='dummy', poems=[], painted=False, paint='coded', label_method='filename',
                          provenance='arena/cast/dummy (drawn in code, Bolas stand-in dummies)',
                          scale={'px_per_cm': ppc, 'n': 0, 'source': f'dummy ref_height {ref_h}px / {height_of(who)} cm' if ppc else 'unmeasured'},
                          height_cm_real=round(im.shape[0] / ppc, 1) if ppc else None, char_height_cm=height_of(who)))
        stats['dummy_parts'] += 1
    # body lab crops (hands/heads/shoes/noses/accessories) — catalogued by body_lab_catalog.json
    BC = json.load(open(os.path.join(SHOTS, 'arena/parts/body_lab/body_lab_catalog.json')))
    PMAP = {'hands': 'hand', 'shoes': 'foot', 'heads': 'head', 'eyes': 'eye', 'noses': 'nose', 'mouths': 'mouth', 'accessories': 'accessory', 'torsos': 'torso'}
    have = {p['file'] for p in parts}
    for cat, L in BC.items():
        for q in L:
            f = q['path'][len('shots/'):] if q['path'].startswith('shots/') else q['path']
            if f in have or not os.path.exists(os.path.join(SHOTS, f)):
                continue
            if not f.startswith('arena/parts/body_lab/'):
                continue  # the catalogue also lists weave/tracksuit files registered above
            part = PMAP.get(cat, 'accessory')
            im, br = card_info(os.path.join(SHOTS, f))
            if im is None:
                continue
            piv, sock, how = sockets_for(part, '-', 'unknown', im, br)
            ch = (q.get('character') or '').lower()
            char = 'poet' if 'poet' in ch else 'party' if 'party' in ch or 'guest' in ch or 'club' in ch else 'woman' if 'woman' in ch else \
                'young_poet' if 'young' in ch or 'child' in ch else 'ex' if ch.startswith('ex') else 'family' if 'family' in ch or 'ancest' in ch else '-'
            parts.append(dict(id='body_lab:' + q['id'], character=char, costume='-', part=part, side='-', view='unknown', state=q.get('name', 'rest'),
                              category=CATEGORY.get(part, 'other'), file=f, w=int(im.shape[1]), h=int(im.shape[0]), pivot=piv, parent_part=PARENT.get(part),
                              sockets=sock, pivot_source=how, brads=len(br), sheet=q.get('source', '?'), sheet_id='body_lab', poems=[], painted=True,
                              paint='painted', label_method='body_lab_catalog.json', provenance='arena/parts/body_lab (crops catalogued by body_lab_catalog.json)',
                              scale={'px_per_cm': None, 'n': 0, 'source': 'unmeasured'}, height_cm_real=None, char_height_cm=height_of(char)))
            have.add(f)
            stats['body_lab_parts'] += 1
    # play/data.json whole-figure draws (replacement cards with a measured body height)
    PD = json.load(open(os.path.join(SHOTS, 'play/data.json')))['characters']
    for c in PD:
        key = c['key']
        role = key.split('/')[0]
        char = role_char(role)
        d = os.path.join(SHOTS, 'play/assets', key.replace('/', '__'))
        if not os.path.isdir(d):
            cand = [x for x in glob.glob(os.path.join(SHOTS, 'play/assets', key.split('/')[0] + '*'))]
            d = cand[0] if cand else d
        for q in c['draws']:
            fp = os.path.join(d, q['f'])
            if not os.path.exists(fp):
                stats['missing_files'] += 1
                continue
            hc = c.get('height_cm')
            ppc = (q['body_px'] / hc) if q.get('body_px') and hc else None
            parts.append(dict(id=f"play:{key}/{q['f']}", character=char, costume=key.split('/')[-1], part='replacement', side='-',
                              view={'prof': 'profile', 'front': 'front', 'back': 'back', '3q': 'threequarter'}.get(q.get('view'), q.get('view') or 'unknown'),
                              state=q.get('sem_id') or q.get('cls') or 'pose', category='replacement', file=rel(fp), w=q['w'], h=q['h'],
                              pivot=[round(q.get('ax', q['w'] / 2), 1), round(q['h'] * q.get('hip_y_ratio', 0.5), 1)], parent_part=None,
                              sockets={'hip': [round(q.get('ax', q['w'] / 2), 1), round(q['h'] * q.get('hip_y_ratio', 0.5), 1)]},
                              pivot_source='play/data.json ax + hip_y_ratio', brads=0, sheet=q.get('id', '?'), sheet_id='play', poems=c.get('poems', []),
                              painted=True, paint='painted', label_method='play/data.json', provenance='shots/play/data.json draws (whole-figure cards)',
                              scale={'px_per_cm': round(ppc, 3) if ppc else None, 'n': 1, 'source': 'play body_px / height_cm' if ppc else 'unmeasured'},
                              height_cm_real=round(q['h'] / ppc, 1) if ppc else None, char_height_cm=hc))
            stats['play_draws'] += 1


# --------------------------------------------------------------- expected cells, summary
def expected_cells():
    """The kit's own cell list per character (v2.py SHEETS_FULL / SHEETS_BACK / SHEETS_EXTRA)."""
    out = {}
    for c in KITS['cast']:
        cid = c['id']
        V2 = __import__('importlib').import_module('kit_registry').V2
        src = next(x for x in V2.CAST if x['id'] == cid)
        sheets = V2.SHEETS_BACK if src.get('back_only') else (V2.SHEETS_FULL if src.get('principal') else V2.SHEETS_EXTRA)
        cells = []
        for sh in sheets:
            k = sh.split('.')
            if k[0] == 'body':
                L = PROF7 if k[1] == 'profile' else BODY13
                cells += [(p, s, k[1], 'rest') for p, s in L]
            elif k[0] == 'hands':
                cells += [(p, s, 'flat', st) for p, s, st in HANDS24]
            elif k[0] == 'heads':
                cells += [('head', '-', v, 'blank') for v in (HEADS if not src.get('back_only') else ('threequarter_back', 'back'))]
            elif k[0] == 'feet':
                cells += [('foot', 'R', v, st) for v, st in FEET6]
            elif k[0] == 'face':
                cells += [('face_plate', '-', k[1], 'blank')] + [('eye', '-', k[1], e) for e in EYES] + [('brow', '-', k[1], b) for b in BROWS] + \
                         [('mouth', '-', k[1], m) for m in MOUTHS]
            elif k[0] == 'replacements':
                cells += [('replacement', '-', '*', r) for r in REPL6]
        out[cid] = cells
    return out


def summarize(parts, sheets_out, stats):
    exp = expected_cells()
    by = defaultdict(lambda: Counter())
    for p in parts:
        by[(p['character'], p['paint'])][(p['part'], p['view'])] += 1
    missing = {}
    for cid, cells in exp.items():
        have_p = {(p['part'], p['side'] if p['side'] != '-' else '-', p['view'], p['state']) for p in parts if p['character'] == cid and p['paint'] == 'painted'}
        have_any = {(p['part'], p['side'] if p['side'] != '-' else '-', p['view'], p['state']) for p in parts if p['character'] == cid}
        def has(cell, H):
            part, side, view, st = cell
            for q in H:
                if q[0] != part:
                    continue
                if view != '*' and q[2] != view and not (part == 'hand' and q[2] in ('flat', 'unknown')):
                    continue
                if part in ('hand', 'eye', 'brow', 'mouth', 'replacement', 'foot') and st not in ('rest', 'blank') and not q[3].startswith(st):
                    continue
                if side not in ('-',) and q[1] not in (side, '-') and part not in ('hand', 'foot'):
                    continue
                return True
            return False
        miss_p = [list(c) for c in cells if not has(c, have_p)]
        miss_a = [list(c) for c in cells if not has(c, have_any)]
        missing[cid] = {'cells': len(cells), 'missing_painted': len(miss_p), 'missing_any': len(miss_a), 'missing_painted_cells': miss_p,
                        'missing_even_composited': miss_a}
    counts = {f'{c}|{paint}': {f'{k[0]}|{k[1]}': v for k, v in sorted(cnt.items())} for (c, paint), cnt in sorted(by.items())}
    return {'about': 'Counts of shots/suite/data/parts.json by character x paint x (part|view), and the kit cells each character lacks. '
                     'Expected cells are the v2 kit layout for that character (v2.py: principal / back-only / extra sheet lists).',
            'totals': {'parts': len(parts), 'by_category': Counter(p['category'] for p in parts), 'by_paint': Counter(p['paint'] for p in parts),
                       'by_label_method': Counter(p['label_method'] for p in parts), 'by_pivot_source': Counter(p['pivot_source'] for p in parts),
                       'with_scale': sum(1 for p in parts if p['scale'].get('px_per_cm')), 'by_character': Counter(p['character'] for p in parts)},
            'stats': {k: (v if not isinstance(v, list) else (v if k == 'layout_refused' else {'n': len(v), 'median': round(statistics.median(v), 3) if v else None}))
                      for k, v in stats.items()},
            'counts': counts, 'missing': missing, 'cut_sheets': sheets_out}


WORK = None


def main(work):
    global WORK
    WORK = work
    stats = defaultdict(int)
    stats['layout_agree'] = []
    stats['layout_refused'] = []
    parts, sheets_out = [], []
    register_cut_sheets(work, parts, sheets_out, stats)
    register_v2_parts(parts, stats)
    register_tracksuit(parts, stats)
    register_weave_man(parts, stats)
    register_misc(parts, stats)
    # per-card proportion check: the painters did not keep the skeleton's proportions (arms drawn long, legs and
    # torsos short), so each measurable card also carries its own px/cm and its error against the skeleton
    for p in parts:
        sc = p['scale']
        e = expected_cm(build_of(p['character']), p['part'])
        sp = measure_span(p['part'], p['sockets'], None)
        if e and sp and sc.get('px_per_cm') and trusted_for_scale(p):
            sc['own_px_per_cm'] = round(sp / e, 3)
            sc['vs_skeleton_pct'] = round(100 * (sp / sc['px_per_cm'] - e) / e, 1)
    for p in parts:
        p.pop('_rgba_span', None)
        p.pop('_span', None)
        p.setdefault('height_cm_real', None)
        p['scale'].setdefault('n', 0)
    ids = Counter(p['id'] for p in parts)
    for p in parts:
        if ids[p['id']] > 1:
            ids[p['id']] -= 1
            p['id'] += f'#{ids[p["id"]] + 1}'
    reg = {'about': 'One registry of every cut puppet part in the suite (lane A). Coordinates are px in the part file; pivot is the brad '
                    'the part turns on; sockets are where children pin; scale.px_per_cm turns px into cm. paint: painted (a painting of this '
                    'character), composited (recoloured/pasted from other paintings by generate_v2_kits.py) or coded (drawn by a program). '
                    'Written by shots/suite/tools/build_parts.py; see shots/suite/AUDIT_parts.md.',
           'schema': 'id, character, costume, part, side, view, state, file, w, h, pivot, parent_part, sockets, scale{px_per_cm,source}, '
                     'height_cm_real (part file height in cm), char_height_cm, sheet, provenance, painted, paint, category, poems, '
                     'label_method, pivot_source, brads',
           'count': len(parts), 'parts': parts}
    json.dump(reg, open(os.path.join(SUITE, 'data', 'parts.json'), 'w'), separators=(',', ':'))
    summ = summarize(parts, sheets_out, stats)
    json.dump(summ, open(os.path.join(SUITE, 'data', 'parts_summary.json'), 'w'), indent=1)
    print(json.dumps(summ['totals'], indent=1, default=str))
    print(json.dumps(summ['stats'], default=str)[:2000])


if __name__ == '__main__':
    main(sys.argv[1])
