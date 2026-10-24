"""Per-part QA gates: cut-off, contamination, connection point, view. A part that FAILs any gate is excluded from
pairing (pairs.py) and from assembly.

    gate(rec) -> {'cutoff': {...}, 'contamination': {...}, 'connection': {...}, 'view': {...}, 'verdict': ...}

Each test gives {'result': pass|warn|fail, 'evidence': {...}, 'why': str}. Measurements are taken on the source card
(border contact, straight cuts) and on the canonical image (lengths in cm at 10 px/cm).
"""
import math, os, sys
import numpy as np
import cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))
import common as C  # noqa: E402

RANK = {'pass': 0, 'warn': 1, 'fail': 2}


def _res(r, ev, why=''):
    return {'result': r, 'evidence': ev, 'why': why}


def worst(*rs):
    return max(rs, key=lambda r: RANK[r])


def load_canon(rec):
    from PIL import Image
    return np.array(Image.open(os.path.join(C.LIB2, rec['image'])).convert('RGBA'))


def card_of(rec):
    return next(c for c in C.cards() if c['id'] == rec['source_card'])


def straight_cuts(mask, min_len, avoid_pt=None, avoid_r=0):
    """long straight runs on the outline (scissor cuts across a limb), excluding those near avoid_pt"""
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return []
    c = max(cs, key=cv2.contourArea)
    poly = cv2.approxPolyDP(c, 1.2, True)[:, 0, :].astype(float)
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        L = float(np.linalg.norm(b - a))
        if L < min_len:
            continue
        mid = (a + b) / 2
        if avoid_pt is not None and np.linalg.norm(mid - np.array(avoid_pt)) < avoid_r:
            continue
        # a straight segment is a cut only if the contour between its ends really follows the chord
        out.append({'a': a.round(1).tolist(), 'b': b.round(1).tolist(), 'len': round(L, 1)})
    return out


def border_contact(alpha, keep_side=None):
    a = alpha > 128
    H, W = a.shape
    sides = {'top': int(a[0].sum()), 'bottom': int(a[-1].sum()), 'left': int(a[:, 0].sum()), 'right': int(a[:, -1].sum())}
    if keep_side:
        sides.pop(keep_side, None)
    return {k: v for k, v in sides.items() if v > 3}


def nearest_side(pt, W, H):
    d = {'left': pt[0], 'right': W - pt[0], 'top': pt[1], 'bottom': H - pt[1]}
    return min(d, key=d.get)


def gate_head(rec):
    c = card_of(rec)
    rgba = C.load_rgba(c)
    kc, kcard = rec['keypoints']['canonical'], rec['keypoints']['card']
    H, W = rgba.shape[:2]
    out = {}
    # --- cut-off: border contact away from the neck end, crown at the very top edge, straight cuts off the neck
    bc = border_contact(rgba[..., 3], keep_side=nearest_side(kcard['pivot'], W, H))
    m = rgba[..., 3] > 128
    hh = math.dist(kcard['crown'], kcard['chin'])
    cuts = straight_cuts(m, 0.28 * hh, avoid_pt=kcard['pivot'], avoid_r=0.75 * math.dist(kcard['pivot'], kcard['chin']) + 0.15 * hh)
    if 'removed_components' in rec:
        cuts = [s for s in cuts if not any(abs(s['a'][1] - r['bbox'][1]) < 3 for r in rec['removed_components'] if r['kind'] == 'caption')]
    crown_cm = math.dist(kc['crown'], kc['chin']) / C.CANON_PPC
    exp = C.height_cm(rec['character']) / 8.0
    r = 'pass'
    why = []
    bc = {k: v for k, v in bc.items() if v > 0.05 * (W if k in ('top', 'bottom') else H)}   # a tangent touch is not a cut
    if bc:
        r = 'fail' if max(bc.values()) > 0.2 * max(W, H) else 'warn'; why.append('alpha runs along the card border: %s px' % bc)
    if cuts:
        r = worst(r, 'warn'); why.append('%d long straight edge(s) away from the neck' % len(cuts))
    if crown_cm < 0.82 * exp:
        r = worst(r, 'fail' if crown_cm < 0.7 * exp else 'warn'); why.append('crown->chin %.1f cm < expected %.1f' % (crown_cm, exp))
    out['cutoff'] = _res(r, {'border_px': bc, 'straight_cuts': cuts, 'crown_chin_cm': round(crown_cm, 1), 'expected_cm': round(exp, 1)}, '; '.join(why))
    # --- contamination: shoulders/collar below the neck (width blows up below the narrowest neck row), neck too long,
    #     dark cloth under the chin
    can = load_canon(rec)
    mc = can[..., 3] > 128
    piv, chin = kc['pivot'], kc['chin']
    wid = rec.get('widths_px', {})
    neck_min = wid.get('neck_min') or 1
    below = [y for y in range(int(chin[1] + 0.4 * (piv[1] - chin[1])), min(mc.shape[0], int(piv[1] + 0.25 * (piv[1] - chin[1])) + 1))]
    wmax = max([np.ptp(np.where(mc[y])[0]) + 1 for y in below if mc[y].any()] or [0])
    neck_cm = (piv[1] - chin[1]) / C.CANON_PPC
    hsv = cv2.cvtColor(can[..., :3], cv2.COLOR_RGB2HSV)
    zone = np.zeros_like(mc); zone[int(chin[1] + 0.25 * (piv[1] - chin[1])):, :] = True
    zone &= mc
    cloth = float(((hsv[..., 2] < 60) & zone).sum() / max(1, zone.sum()))
    r, why = 'pass', []
    if wmax > 1.9 * neck_min:
        r = 'fail'; why.append('outline widens to %.0f px below the chin (neck %.0f): shoulders or collar attached' % (wmax, neck_min))
    elif wmax > 1.5 * neck_min:
        r = 'warn'; why.append('outline widens below the chin (%.0f vs neck %.0f)' % (wmax, neck_min))
    if neck_cm > 14:
        r = worst(r, 'warn'); why.append('chin->pivot %.1f cm: long neck tab, pivot sits mid-neck' % neck_cm)
    if cloth > 0.25 and 'back' not in rec['flags']:
        r = worst(r, 'warn'); why.append('%.0f%% dark cloth-like pixels in the neck zone' % (100 * cloth))
    out['contamination'] = _res(r, {'max_width_below_chin_px': int(wmax), 'neck_min_px': neck_min, 'chin_to_pivot_cm': round(neck_cm, 1),
                                    'dark_in_neck_zone': round(cloth, 3)}, '; '.join(why))
    # --- connection: pivot centred on the neck cross-section, brad found, clean end
    row = int(round(piv[1]))
    xs = np.where(mc[min(max(row, 0), mc.shape[0] - 1)])[0]
    off = abs(piv[0] - (xs[0] + xs[-1]) / 2) / max(1, np.ptp(xs)) if len(xs) else 1
    r, why = 'pass', []
    if off > 0.25:
        r = 'fail'; why.append('pivot %.0f%% off the neck centre-line' % (100 * off))
    elif off > 0.12:
        r = 'warn'; why.append('pivot %.0f%% off the neck centre-line' % (100 * off))
    if 'brass' not in rec.get('pivot_source', ''):
        r = worst(r, 'warn'); why.append('no brad found; pivot = %s' % rec.get('pivot_source'))
    below_piv = mc[int(piv[1]) + 1:].sum() / C.CANON_PPC ** 2
    if below_piv < 0.5:
        r = worst(r, 'warn'); why.append('pivot sits on the bottom edge (%.1f cm^2 below it): no overlap tab' % below_piv)
    out['connection'] = _res(r, {'pivot_offset_frac': round(float(off), 3), 'width_at_pivot_px': rec.get('widths_px', {}).get('neck_at_pivot'),
                                 'tab_below_pivot_cm2': round(float(below_piv), 1), 'pivot_source': rec.get('pivot_source')}, '; '.join(why))
    # --- view: the tag against the pixel test
    px = rec.get('pixel_tests') or {}
    v = rec['classes']['view']['value']
    dx, dbox = px.get('skin_vs_hair_dx', 0), px.get('dark_face_box', 0)
    pv = 'back' if dbox > 0.6 else 'side' if abs(dx) > 0.16 else 'three-quarter' if abs(dx) > 0.06 else 'front'
    fam = lambda x: {'three-quarter-back': 'back', 'three-quarter': 'turned', 'side': 'turned'}.get(x, x)
    r = 'pass' if fam(pv) == fam(v) or 'blank' in rec['flags'] and v != 'back' else 'warn'
    out['view'] = _res(r, {'tag': v, 'pixel_view': pv, 'skin_vs_hair_dx': dx, 'dark_face_box': dbox, 'tag_conf': rec['classes']['view']['conf']},
                       '' if r == 'pass' else 'pixel test reads %s, tag says %s' % (pv, v))
    out['verdict'] = worst(*[out[k]['result'] for k in ('cutoff', 'contamination', 'connection', 'view')])
    return out


GATES = {'head': gate_head}


def gate(rec):
    f = GATES.get(rec['part'])
    return f(rec) if f else None


def _common_cut(rec, rgba, pivot_card):
    H, W = rgba.shape[:2]
    bc = border_contact(rgba[..., 3], keep_side=nearest_side(pivot_card, W, H))
    return {k: v for k, v in bc.items() if v > 0.05 * (W if k in ('top', 'bottom') else H)}


def _cloth(can, zone):
    hsv = cv2.cvtColor(can[..., :3], cv2.COLOR_RGB2HSV)
    S, V = hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    return float((zone & (V < 55)).sum() / max(1, zone.sum())), float((zone & (S < 40) & (V > 170)).sum() / max(1, zone.sum()))


def gate_hand(rec):
    c = card_of(rec)
    rgba = C.load_rgba(c)
    kc, kcard = rec['keypoints']['canonical'], rec['keypoints']['card']
    can = load_canon(rec)
    mc = can[..., 3] > 128
    out = {}
    exp = 0.108 * C.height_cm(rec['character'])            # wrist crease -> middle fingertip
    L = rec['widths_px']['length'] / C.CANON_PPC
    st = rec['classes']['state']['value']
    closed = st in ('fist', 'grip', 'pinch', 'claw', 'cupped', 'point', 'peace') or str(st).startswith('holding')
    lo = 0.45 if closed else 0.65
    bc = _common_cut(rec, rgba, kcard['pivot'])
    r, why = 'pass', []
    if bc:
        r = 'fail' if max(bc.values()) > 0.2 * max(rgba.shape[:2]) else 'warn'; why.append('alpha runs along the card border: %s px' % bc)
    if L < lo * exp:
        r = worst(r, 'fail' if L < (lo - 0.15) * exp else 'warn'); why.append('pivot->tip %.1f cm short for a %s hand (expected >= %.1f)' % (L, st, lo * exp))
    if L > 1.45 * exp:
        r = worst(r, 'warn'); why.append('pivot->tip %.1f cm long (expected about %.1f): wrist/forearm included or scale off' % (L, exp))
    out['cutoff'] = _res(r, {'border_px': bc, 'length_cm': round(L, 1), 'expected_cm': round(exp, 1), 'state': st}, '; '.join(why))
    # contamination: sleeve / cuff (dark or white cloth) past the tab, props, pale skin
    P = kc['pivot']
    zone = mc.copy(); zone[:int(P[1] + 0.12 * rec['widths_px']['length'])] = False
    dark, white = _cloth(can, zone)
    r, why = 'pass', []
    if dark > 0.12:
        r = 'fail'; why.append('%.0f%% dark cloth in the hand (sleeve or cuff attached)' % (100 * dark))
    elif dark > 0.05:
        r = 'warn'; why.append('%.0f%% dark pixels in the hand' % (100 * dark))
    if 'prop' in rec['flags']:
        r = worst(r, 'warn'); why.append('holds a painted prop (%s)' % st)
    if 'pale_skin_off_palette' in rec['flags']:
        r = worst(r, 'warn'); why.append('pale skin, off the poet palette')
    pc = kc.get('palm_centre')
    if pc and (pc[1] - P[1]) > 0.62 * rec['widths_px']['length']:
        r = worst(r, 'warn'); why.append('palm centre far from the wrist pivot: a long wrist/forearm stub')
    out['contamination'] = _res(r, {'dark_cloth': round(dark, 3), 'white_cloth': round(white, 3), 'prop_frac': (rec.get('pixel_tests') or {}).get('prop_frac')}, '; '.join(why))
    # connection
    r, why = 'pass', []
    if 'brass' not in rec.get('pivot_source', ''):
        r = 'warn'; why.append('no wrist brad found; pivot = %s' % rec.get('pivot_source'))
    row = mc[int(P[1])]
    xs = np.where(row)[0]
    off = abs(P[0] - (xs[0] + xs[-1]) / 2) / max(1, np.ptp(xs)) if len(xs) else 1
    if off > 0.25:
        r = 'fail'; why.append('pivot %.0f%% off the wrist tab centre' % (100 * off))
    tab = mc[:int(P[1])].sum() / C.CANON_PPC ** 2
    if tab < 0.3:
        r = worst(r, 'warn'); why.append('nothing beyond the pivot: no overlap tab')
    out['connection'] = _res(r, {'pivot_offset_frac': round(float(off), 3), 'width_at_pivot_px': rec['widths_px'].get('at_pivot'), 'tab_beyond_pivot_cm2': round(float(tab), 1)}, '; '.join(why))
    # view assumptions
    cl = rec['classes']
    r, why = 'pass', []
    if cl['palm_normal']['value'] == 'unknown':
        r = 'warn'; why.append('palm/back facing unknown')
    if cl['side']['value'] == 'unknown':
        r = 'warn'; why.append('his left/right unknown')
    if any(f.startswith('name_') for f in rec['flags']):
        r = 'warn'; why.append('card name contradicts the image (%s)' % ','.join(f for f in rec['flags'] if f.startswith('name_')))
    out['view'] = _res(r, {'view': cl['view']['value'], 'palm_normal': cl['palm_normal']['value'], 'side': cl['side']['value'],
                           'width_over_length': (rec.get('pixel_tests') or {}).get('width_over_length')}, '; '.join(why))
    out['verdict'] = worst(*[out[k]['result'] for k in ('cutoff', 'contamination', 'connection', 'view')])
    return out


def gate_foot(rec):
    c = card_of(rec)
    rgba = C.load_rgba(c)
    kc, kcard = rec['keypoints']['canonical'], rec['keypoints']['card']
    can = load_canon(rec)
    mc = can[..., 3] > 128
    out = {}
    exp = 0.165 * C.height_cm(rec['character'])            # boot length heel->toe
    L = rec['widths_px']['length'] / C.CANON_PPC
    side = rec['classes']['view']['value'] in ('side', 'three-quarter')
    bc = _common_cut(rec, rgba, kcard['pivot'])
    r, why = 'pass', []
    if bc:
        r = 'fail' if max(bc.values()) > 0.2 * max(rgba.shape[:2]) else 'warn'; why.append('alpha runs along the card border: %s px' % bc)
    edge = mc[:, 0].any() or mc[:, -1].any() or mc[-1].any()
    if edge:
        r = worst(r, 'warn'); why.append('the foot reaches the canonical canvas edge')
    if side and L < 0.75 * exp:
        r = worst(r, 'fail' if L < 0.6 * exp else 'warn'); why.append('heel->toe %.1f cm short (expected about %.1f)' % (L, exp))
    if side and L > 1.35 * exp:
        r = worst(r, 'warn'); why.append('heel->toe %.1f cm long (expected about %.1f)' % (L, exp))
    out['cutoff'] = _res(r, {'border_px': bc, 'length_cm': round(L, 1), 'expected_cm': round(exp, 1)}, '; '.join(why))
    hp = rec['widths_px']['height_pivot_to_sole'] / C.CANON_PPC
    P = kc['pivot']
    zone = mc.copy(); zone[int(P[1]):] = False
    hsv = cv2.cvtColor(can[..., :3], cv2.COLOR_RGB2HSV)
    red = float((zone & ((hsv[..., 0] < 8) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 120) & (hsv[..., 2] > 80)).sum() / max(1, zone.sum()))
    r, why = 'pass', []
    if hp > 24:
        r = 'warn'; why.append('ankle pivot %.1f cm above the sole: shaft/shin included?' % hp)
    if red > 0.03:
        r = 'fail'; why.append('trouser stripe (red) above the ankle: shin attached')
    if 'off_palette_white' in rec['flags']:
        r = worst(r, 'warn'); why.append('white boot, off the costume palette')
    out['contamination'] = _res(r, {'pivot_to_sole_cm': round(hp, 1), 'red_above_pivot': round(red, 3)}, '; '.join(why))
    r, why = 'pass', []
    if 'brass' not in rec.get('pivot_source', ''):
        r = 'warn'; why.append('no ankle brad found; pivot = %s' % rec.get('pivot_source'))
    row = mc[int(P[1])]
    xs = np.where(row)[0]
    off = abs(P[0] - (xs[0] + xs[-1]) / 2) / max(1, np.ptp(xs)) if len(xs) else 1
    if off > 0.3:
        r = worst(r, 'fail'); why.append('pivot %.0f%% off the ankle tab centre' % (100 * off))
    out['connection'] = _res(r, {'pivot_offset_frac': round(float(off), 3), 'width_at_pivot_px': rec['widths_px'].get('ankle_tab_at_pivot')}, '; '.join(why))
    cl = rec['classes']
    asym = (rec.get('pixel_tests') or {}).get('toe_asym', 0)
    r, why = 'pass', []
    if cl['view']['value'] == 'side' and abs(asym) < 0.12:
        r = 'warn'; why.append('tagged side but symmetric about the ankle (asym %.2f)' % asym)
    if cl['view']['value'] in ('front', 'back') and abs(asym) > 0.25:
        r = 'warn'; why.append('tagged %s but reads as a side view (asym %.2f)' % (cl['view']['value'], asym))
    if cl['side']['value'] == 'unknown':
        r = worst(r, 'warn'); why.append('his left/right unknown')
    out['view'] = _res(r, {'view': cl['view']['value'], 'facing': cl['facing']['value'], 'toe_asym': asym}, '; '.join(why))
    out['verdict'] = worst(*[out[k]['result'] for k in ('cutoff', 'contamination', 'connection', 'view')])
    return out


def gate_limb(rec):
    """forearm / shin / upper arm / thigh: border cut, two segments, both joint brads"""
    c = card_of(rec)
    rgba = C.load_rgba(c)
    kcard = rec['keypoints']['card']
    out = {}
    bc = _common_cut(rec, rgba, kcard['pivot'])
    out['cutoff'] = _res('warn' if bc else 'pass', {'border_px': bc}, 'alpha runs along the card border' if bc else '')
    bad = 'extra_brads_mid_segment' in rec['flags']
    out['contamination'] = _res('fail' if bad else 'pass', {'flags': rec['flags']}, 'brads mid-segment: two segments on one card' if bad else '')
    est = [f for f in rec['flags'] if f.endswith('_pivot_estimated')]
    out['connection'] = _res('warn' if est else 'pass', {'pivot_source': rec.get('pivot_source'), 'widths_px': rec.get('widths_px')}, ', '.join(est))
    out['view'] = _res('pass', {'view': rec['classes']['view']['value']}, '')
    out['verdict'] = worst(*[out[k]['result'] for k in ('cutoff', 'contamination', 'connection', 'view')])
    return out


GATES.update({'hand': gate_hand, 'foot': gate_foot, 'forearm': gate_limb, 'shin': gate_limb, 'upper_arm': gate_limb, 'thigh': gate_limb})
