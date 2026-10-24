"""Heads: clean, classify, sub-skeleton, regularize onto the head grid, review sheet.

    python3 shots/scion2/library2/tools/heads.py poet [ex ...]

Writes library2/<char>/head/*.png, merges records into library2/index.json, sheets into library2/sheets/.
Head grid: 512x512 canvas, neck pivot at (256,448), head 'up' (neck->crown) = canvas up, CANON_PPC px/cm with the
crown->chin height scaled to the character's head height (height/8, Vitruvian canon).
"""
import math, os, sys
import numpy as np, cv2
from PIL import Image
import common as C
from brass import brass_blobs
import index as IX

PART = 'head'
G = C.GRID[PART]
YAW = {'front': 0, 'three-quarter': 45, 'side': 90, 'three-quarter-back': 135, 'back': 180}
BONES = [('pivot', 'chin'), ('chin', 'eye_line'), ('eye_line', 'crown'), ('ear_l', 'ear_r'), ('eye_line', 'nose'), ('ear', 'eye_line')]


def rows_profile(m):
    ys = np.where(m.any(1))[0]
    L = np.full(m.shape[0], -1); R = np.full(m.shape[0], -1)
    for y in ys:
        xs = np.where(m[y])[0]
        L[y], R[y] = xs[0], xs[-1]
    return L, R


def geometry(m, pivot):
    """auto estimates in card px: crown, chin, eye line, ears, extents"""
    L, R = rows_profile(m)
    ys = np.where(L >= 0)[0]
    top, bot = int(ys[0]), int(ys[-1])
    W = np.where(L >= 0, R - L + 1, 0)
    band = slice(top, top + max(2, (bot - top) // 30))
    crown = [float(np.mean([(L[y] + R[y]) / 2 for y in range(band.start, band.stop) if L[y] >= 0])), float(top)]
    py = int(round(pivot[1]))
    # neck: narrowest row between 55% height and the pivot
    lo = top + int(0.55 * (py - top))
    seg = [(W[y], y) for y in range(lo, max(lo + 1, py)) if W[y] > 0]
    neck_w, neck_y = min(seg) if seg else (W[py], py)
    # chin: scanning up from the neck, first row clearly wider than the neck
    chin_y = neck_y
    for y in range(neck_y, top, -1):
        if W[y] > 1.28 * neck_w:
            chin_y = y
            break
    hh = chin_y - top
    eye_y = top + 0.56 * hh
    return dict(top=top, bot=bot, L=L, R=R, W=W, crown=crown, neck_y=int(neck_y), neck_w=float(neck_w),
                chin_y=float(chin_y), eye_y=float(eye_y), head_h=float(hh))


def pixel_tests(rgba, m, g):
    hsv = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2HSV)
    V = hsv[..., 2].astype(int)
    top, ch = g['top'], int(g['chin_y'])
    region = np.zeros_like(m); region[top:ch] = m[top:ch]
    dark = region & (V < 70)
    light = region & (V >= 70)
    yy, xx = np.nonzero(region)
    width = max(1, xx.max() - xx.min())
    dx = 0.0
    if dark.sum() > 50 and light.sum() > 50:
        dx = (np.nonzero(light)[1].mean() - np.nonzero(dark)[1].mean()) / width
    # face box: middle rows, central 50 % (front-ish) -> how much is dark (back of head = hair everywhere)
    y0, y1 = int(top + 0.35 * g['head_h']), int(top + 0.75 * g['head_h'])
    x0, x1 = int(xx.min() + 0.25 * width), int(xx.max() - 0.25 * width)
    box = m[y0:y1, x0:x1]
    dark_box = float(((V[y0:y1, x0:x1] < 70) & box).sum() / max(1, box.sum()))
    # eye band texture: painted eyes/sunglasses -> dark specks inside the light face; blank plate -> smooth cardboard
    e0, e1 = int(top + 0.42 * g['head_h']), int(top + 0.66 * g['head_h'])
    eb = m[e0:e1, x0:x1] & (V[e0:e1, x0:x1] >= 0)
    vv = V[e0:e1, x0:x1][eb]
    eye_dark = float((vv < 60).mean()) if vv.size else 0.0
    eye_std = float(vv.std()) if vv.size else 0.0
    return dict(skin_vs_hair_dx=round(float(dx), 3), dark_face_box=round(dark_box, 3), eye_band_dark=round(eye_dark, 3),
                eye_band_std=round(eye_std, 1))


def auto_classify(c, px):
    """view / facing / face state from pixel tests, the library view, labels.json and CLIP. Returns {field: (value, conf, source)}"""
    lab = C.labels().get(c['id'], {})
    clip = c.get('clip', {})
    out = {}
    dx, dbox = px['skin_vs_hair_dx'], px['dark_face_box']
    if dbox > 0.6:
        pv = 'back'
    elif abs(dx) > 0.16:
        pv = 'side'
    elif abs(dx) > 0.06:
        pv = 'three-quarter'
    else:
        pv = 'front'
    libv = {'threequarter': 'three-quarter', 'profile': 'side', 'threequarter_back': 'three-quarter-back'}.get(c.get('view'), c.get('view'))
    if libv:
        out['view'] = (libv, 0.8, 'library.view (filed by sheet caption)')
    elif lab.get('view'):
        out['view'] = ({'side': 'side'}.get(lab['view'], lab['view']), 0.75, 'labels.json (agent-vision)')
    else:
        out['view'] = (pv, 0.55, 'pixel: skin/hair centroid dx=%.2f, dark face box=%.2f' % (dx, dbox))
    v = out['view'][0]
    if v in ('front', 'back'):
        out['facing'] = ('camera' if v == 'front' else 'away', 0.8, 'follows view')
    else:
        f = 'screen-right' if dx > 0 else 'screen-left'
        # three-quarter-back: the jaw/cheek skin shows on the side the face is turned to (same sign as the 3/4 front)
        out['facing'] = (f, min(0.95, 0.5 + abs(dx) * 2), 'pixel: skin centroid is %s of hair centroid (dx=%.2f)' % ('right' if dx > 0 else 'left', dx))
    if v in ('back', 'three-quarter-back'):
        st = ('back_of_head', 0.85, 'view')
    else:
        painted = px['eye_band_dark'] > 0.03 or px['eye_band_std'] > 38
        st = ('painted_face' if painted else 'blank_face_plate', 0.7,
              'pixel: eye band dark=%.3f std=%.0f' % (px['eye_band_dark'], px['eye_band_std']))
        if clip.get('face'):
            agree = (clip['face'] == 'painted') == painted
            st = (st[0], 0.85 if agree else 0.5, st[2] + '; CLIP face=%s (%s)' % (clip['face'], 'agrees' if agree else 'disagrees'))
        if 'painted' in lab:
            st = ('painted_face' if lab['painted'] else 'blank_face_plate', 0.9, 'labels.json (agent-vision); ' + st[2])
    out['state'] = st
    return out


def process(c, fx, s_override=None):
    rgba0 = C.load_rgba(c)
    rgba, removed = C.keep_main(rgba0)
    m = C.mask_of(rgba)
    flags = []
    if removed:
        flags.append('cleaned')
        if any(r['kind'] == 'caption' for r in removed):
            flags.append('caption_removed')
    # neck pivot: a brass brad/eyelet in the lower third, else the card's A point, else bottom centre
    H, W = m.shape
    bl = [b for b in brass_blobs(rgba) if b['c'][1] > 0.6 * H]
    if fx.get('pivot'):
        pivot, psrc = list(map(float, fx['pivot'])), 'fixes.json'
    elif bl:
        b = min(bl, key=lambda b: abs(b['c'][0] - W / 2) + 0.3 * (H - b['c'][1]))
        pivot, psrc = b['c'], 'brass eyelet/brad (colour+roundness detector)'
    elif c.get('A') and c['A'][1] > 0.6 * H:
        pivot, psrc = list(map(float, c['A'])), 'library A point'
    else:
        ys = np.where(m.any(1))[0]
        pivot, psrc = [W / 2, float(ys[-1]) - 0.05 * H], 'bottom centre'
    rgba, cap = C.cut_bottom_caption(rgba, pivot[1] + 0.02 * H)
    if cap:
        removed.append(cap); flags += ['cleaned', 'caption_removed']
        m = C.mask_of(rgba)
    g = geometry(m, pivot)
    px = pixel_tests(rgba, m, g)
    cls = auto_classify(c, px)
    for k in ('view', 'facing', 'state'):
        if k in fx:
            cls[k] = (fx[k], 0.95, 'fixes.json (agent-vision, card looked at)')
    if cls['view'][0] in ('three-quarter', 'three-quarter-back', 'side') and cls['facing'][0] in ('camera', 'away') and 'facing' not in fx:
        dx = px['skin_vs_hair_dx']
        cls['facing'] = ('screen-right' if dx > 0 else 'screen-left', min(0.95, 0.5 + abs(dx) * 2),
                         'pixel: skin centroid is %s of hair centroid (dx=%.2f)' % ('right' if dx > 0 else 'left', dx))
    view, facing = cls['view'][0], cls['facing'][0]
    kp = {}
    kp['pivot'] = pivot
    kp['crown'] = list(fx.get('crown', g['crown']))
    cy = fx.get('chin', [None, g['chin_y']])[1]
    L, R = g['L'], g['R']
    def row_mid(y):
        y = int(round(min(max(y, g['top']), g['bot'])))
        return (L[y] + R[y]) / 2.0, L[y], R[y]
    mid, l, r = row_mid(cy)
    if 'chin' in fx:
        kp['chin'] = list(fx['chin'])
    elif view == 'side':
        kp['chin'] = [float(r - 0.08 * (r - l)) if facing == 'screen-right' else float(l + 0.08 * (r - l)), float(cy)]
    else:
        kp['chin'] = [float(mid), float(cy)]
    hh = math.dist(kp['crown'], kp['chin'])
    ey = fx.get('eye_line', [None, kp['crown'][1] + 0.56 * (kp['chin'][1] - kp['crown'][1])])[1]
    emid, el, er = row_mid(ey)
    if 'eye_line' in fx:
        kp['eye_line'] = list(fx['eye_line'])
    elif view == 'side':
        kp['eye_line'] = [float(er - 0.15 * (er - el)) if facing == 'screen-right' else float(el + 0.15 * (er - el)), float(ey)]
    elif view == 'three-quarter':
        kp['eye_line'] = [float(emid + (0.12 if facing == 'screen-right' else -0.12) * (er - el)), float(ey)]
    else:
        kp['eye_line'] = [float(emid), float(ey)]
    # ears: extreme points in the band just below the eye line
    y0, y1 = int(ey - 0.05 * hh), int(ey + 0.22 * hh)
    sub = [(L[y], y) for y in range(max(y0, g['top']), min(y1, g['bot'])) if L[y] >= 0]
    subr = [(R[y], y) for y in range(max(y0, g['top']), min(y1, g['bot'])) if R[y] >= 0]
    ear_l = [float(min(sub)[0]), float(min(sub)[1])] if sub else None
    ear_r = [float(max(subr)[0]), float(max(subr)[1])] if subr else None
    if view in ('front', 'back'):
        kp['ear_l'], kp['ear_r'] = ear_l, ear_r      # screen-left / screen-right ear (outer edge)
    elif view in ('three-quarter', 'three-quarter-back'):
        if facing == 'screen-right':
            kp['ear_l'] = ear_l
        else:
            kp['ear_r'] = ear_r
    for k in ('ear_l', 'ear_r', 'nose', 'ear'):
        if k in fx:
            kp[k] = fx[k]
    # face direction (where the nose points): yaw about the head's up axis, +x = screen right, z = toward camera
    yaw = YAW.get(view, 0) * (1 if facing in ('screen-right', 'camera', 'away') else -1)
    if view == 'back':
        yaw = 180
    t = math.radians(yaw)
    face_dir3 = [round(math.sin(t), 3), 0.0, round(math.cos(t), 3)]
    # transform: card upright (rotation from fixes only), scale crown->chin to the character's head height
    head_cm = C.height_cm(c['character']) / 8.0
    rot = float(fx.get('rot', 0.0))
    s = head_cm * C.CANON_PPC / max(8.0, hh)
    s_own = s
    ssrc = 'own crown->chin = %.1f cm (height/8, Vitruvian canon)' % head_cm
    if fx.get('scale'):
        s, ssrc = float(fx['scale']), 'fixes.json'
    elif s_override:
        s, ssrc = s_override
    M = C.similarity(kp['pivot'], G['pivot'], rot, s)
    can = C.warp(rgba, M, G['canvas'])
    kc = {k: C.apply(M, v) for k, v in kp.items() if v is not None}
    # neck width at the pivot and at the chin (cloth/skin outline widths), canonical px
    widths = {'neck_at_pivot': round(float(g['W'][int(min(max(pivot[1], g['top']), g['bot']))]) * s, 1),
              'neck_min': round(g['neck_w'] * s, 1), 'chin_row': round(float(R[int(cy)] - L[int(cy)]) * s, 1)}
    if fx.get('flags'):
        flags += fx['flags']
    if view in ('back', 'three-quarter-back') and 'chin' not in fx:
        flags.append('chin_estimated_from_outline')
    st = cls['state'][0]
    flags.append({'painted_face': 'painted', 'blank_face_plate': 'blank', 'back_of_head': 'back', 'bare_backing_plate': 'blank'}.get(st, st))
    if max(H, W) < 180:
        flags.append('low_res')
    return dict(rgba=can, M=M, kp=kp, kc=kc, cls=cls, px=px, flags=sorted(set(flags)), removed=removed, scale=s,
                rot=rot, psrc=psrc, s_own=s_own, ssrc=ssrc, sheet_measurable=(view in ('front', 'three-quarter', 'side') and 'chin_estimated_from_ear_line' not in flags and 'chin' in fx or view == 'front'), face_dir3=face_dir3, widths=widths, yaw=yaw)


def candidates(ch):
    lab, fxs = C.labels(), C.fixes()
    out = []
    for c in C.cards():
        if c['character'] != ch:
            continue
        slot = fxs.get(c['id'], {}).get('part') or lab.get(c['id'], {}).get('slot') or c['slot']
        if c['slot'] == 'head' or slot == 'head':
            out.append(c)
    return out


def run(ch):
    fxs = C.fixes()
    recs, tiles, bad_tiles = [], [], []
    for c in candidates(ch):
        fx = fxs.get(c['id'], {})
        lab = C.labels().get(c['id'], {})
        refiled = fx.get('part') or lab.get('slot')
        if fx.get('reject') or (refiled and refiled != 'head') or lab.get('bad'):
            why = fx.get('reject') or ('misfiled: this card is a %s, not a head' % (refiled or '?')) + ('' if not lab.get('note') else ' (%s)' % lab['note'])
            rgba = C.load_rgba(c)
            rec = IX.reject_record(c, PART, why, refiled if refiled and refiled != 'head' else None)
            recs.append(rec)
            bad_tiles.append(IX.reject_tile(rgba, c, why))
            continue
        r = process(c, fx)
        sk = c['id'].split('/')[0]
        peers = [p for p in candidates(ch) if p['id'].split('/')[0] == sk and p['id'] != c['id'] and not fxs.get(p['id'], {}).get('reject')
                 and not fxs.get(p['id'], {}).get('part')]
        if peers:
            ss = [r['s_own']] if r['sheet_measurable'] else []
            for p in peers:
                rp = process(p, fxs.get(p['id'], {}))
                if rp['sheet_measurable']:
                    ss.append(rp['s_own'])
            if not ss:      # no member with a visible chin (all back views): the sheet still shares one scale
                ss = [r['s_own']] + [process(p, fxs.get(p['id'], {}))['s_own'] for p in peers]
            if ss:
                med = float(np.median(ss))
                r = process(c, fx, (med, 'shared by the %d heads of sheet %s (median of %d measured crown->chin; this card alone: x%.2f)'
                                    % (len(peers) + 1, sk, len(ss), r['s_own'] / med)))
        rec = IX.part_record(c, PART, r, C.CANON_PPC)
        rec['face_dir'] = {'yaw_deg': r['yaw'], 'vec3': r['face_dir3'],
                           'about': 'nose direction: x screen-right, y down (0 = level), z toward camera; yaw about the head up axis'}
        rec['widths_px'] = r['widths']
        recs.append(rec)
        path = os.path.join(C.LIB2, rec['image'])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(r['rgba']).save(path, optimize=True)
        cls = rec['classes']
        lines = [c['id'].split('/')[-1][:44] + '  ' + c['id'].split('.')[1],
                 '%s  %s  yaw %d' % (cls['view']['value'], cls['facing']['value'], r['yaw']),
                 '%s (%.2f)  view %.2f' % (cls['state']['value'], cls['state']['conf'], cls['view']['conf']),
                 'pivot: ' + r['psrc'][:36],
                 ','.join(rec['flags'])[:44]]
        dirs = []
        if r['yaw'] not in (0, 180) and rec['keypoints']['canonical'].get('eye_line'):
            dirs = [(rec['keypoints']['canonical']['eye_line'], [math.sin(math.radians(r['yaw'])), 0])]
        elif r['yaw'] == 0 and rec['keypoints']['canonical'].get('eye_line'):
            dirs = [(rec['keypoints']['canonical']['eye_line'], [0, 0])]
        tiles.append(IX.tile(r['rgba'], PART, rec['keypoints']['canonical'], BONES, lines, dirs=dirs))
    order = {'front': 0, 'three-quarter': 1, 'side': 2, 'three-quarter-back': 3, 'back': 4}
    good = [i for i, rec in enumerate(recs) if rec['status'] == 'ok']
    good.sort(key=lambda i: (order.get(recs[i]['classes']['view']['value'], 9), recs[i]['classes']['facing']['value']))
    tiles = [tiles[[j for j in range(len(recs)) if recs[j]['status'] == 'ok'].index(i)] for i in good]
    IX.merge(recs, ch, PART)
    sheets = C.sheet(tiles, os.path.join(C.LIB2, 'sheets', '%s_head_%%02d.jpg' % ch), cols=6,
                     title='%s heads on the head grid (512x512, neck pivot red cross at 256,448; grid 5 cm; %g px/cm)' % (ch, C.CANON_PPC))
    sheets += C.sheet(bad_tiles, os.path.join(C.LIB2, 'sheets', '%s_head_rejected_%%02d.jpg' % ch), cols=6,
                      title='%s head cards rejected / re-filed (reason under each)' % ch)
    print('\n'.join(sheets))
    return recs, sheets


if __name__ == '__main__':
    for ch in sys.argv[1:]:
        run(ch)
