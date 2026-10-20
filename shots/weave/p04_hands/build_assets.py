"""Assets and set for passage p04_hands (WYGWYL poem 04, "I put them back on").

Reads
  ../assets/assets.json + ../assets/parts/*.png    the POET puppet parts registered for p07 (reused, not re-cut)
  src/poet_open_hand.jpg                           generated: her second hand, open, loose (INVENTED)
  ../archive/6bb6d333-....mp4                      Eagle Has Landed: The Flight of Apollo 11 (1969), 10.1 s, silent (OBSERVED)
  ../../video/poem_04/out/vid-poem-04-kf00084_0    WYGWYL poem 04 AI plate: the night garden of glass spires (INVENTED)
Writes
  assets/parts/hand_open.png, assets/assets.json, assets/atlas.png
  archive/citizen/NNNN.jpg + assets/parts/citizen_mask.png   the 1969 man at the rail, one fixed scissor cut, his film inside it
  archive/sky1969.jpg                                         the 1969 sky, assembled from the clip's own sky pixels (median)
  set/plate.jpg, set/sky_mask.png, set/ledge.png, set/set.json
  debug_*.jpg
"""
import json, os, sys, subprocess
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from weave_lib import WEAVE, REPO, W, H, alpha_from_white, paper_cut, pack_atlas, jdump

ARCH_ID = '6bb6d333-facb-5c4e-b540-0c150f87833b'
ARCH = os.path.join(WEAVE, 'archive', ARCH_ID + '.mp4')
PLATE = os.path.join(REPO, 'shots', 'video', 'poem_04', 'out', 'vid-poem-04-kf00084_0')
RAW = os.path.join(HERE, 'archive', 'raw')
CIT0, CIT1 = 256, 304          # archive frames (1-based, 29.97 fps) of the man turning and laughing; 305 is a shot change
CIT_SCALE = 1.32
rng = np.random.default_rng(1969)
REG = {'version': 1, 'about': 'assets for p04_hands', 'assets': []}


def raw_frames():
    if not os.path.exists(os.path.join(RAW, '0304.png')):
        os.makedirs(RAW, exist_ok=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', ARCH, os.path.join(RAW, '%04d.png')], check=True)
    return lambda n: cv2.imread(os.path.join(RAW, '%04d.png' % n))


def sky_of(im):
    b, g, r = [im[..., i].astype(int) for i in range(3)]
    return (b > r + 18) & (im.max(2) > 55)


def reuse_puppet():
    """the p07 POET parts, by reference: same files, same pivots and sockets"""
    A = json.load(open(os.path.join(WEAVE, 'assets', 'assets.json')))
    keep = ['head', 'torso', 'skirt', 'upper_arm_near', 'forearm_near', 'hand_near', 'upper_arm_far', 'forearm_far', 'leg_near', 'leg_far']
    for a in A['assets']:
        if a['id'] in keep:
            b = dict(a)  # file stays relative to shots/weave/
            b['note'] = (a.get('note', '') + ' · reused from p07').strip(' ·')
            REG['assets'].append(b)
    # toe point of each shoe (front of the sole), measured from the alpha: the kneel pivots about it
    for pid in ('leg_near', 'leg_far'):
        a = next(x for x in REG['assets'] if x['id'] == pid)
        al = cv2.imread(os.path.join(WEAVE, a['file']), cv2.IMREAD_UNCHANGED)[..., 3]
        ys, xs = np.where(al > 128)
        yb = ys.max()
        band = ys > yb - 18
        a['sockets']['toe'] = [float(xs[band].max() - 6), float(yb - 3)]
        a['sockets']['heel'] = [float(xs[band].min() + 6), float(yb - 3)]
        a['sockets']['kneecap'] = [float(a['sockets']['knee'][0] + 14), float(a['sockets']['knee'][1])]


def build_open_hand():
    """her second hand: generated as a companion to the pinch hand, cut and scaled so wrist-to-fingertip matches it"""
    src = cv2.imread(os.path.join(HERE, 'src', 'poet_open_hand.jpg'))
    a = alpha_from_white(src, sat=40, val=190)
    ys, xs = np.where(a > 8)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    pinch = next(x for x in REG['assets'] if x['id'] == 'hand_near')
    L_pinch = np.linalg.norm(np.array(pinch['sockets']['fingertip']) - np.array(pinch['sockets']['wrist']))
    wrist, tip = np.array([272.0, 455.0]), np.array([1072.0, 436.0])  # brad hole centre; middle fingertip (measured on the source)
    f = float(L_pinch * 1.12 / np.linalg.norm(tip - wrist))
    rgba = np.dstack([src[y0:y1, x0:x1], a[y0:y1, x0:x1]])
    rgba = cv2.resize(rgba, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(HERE, 'assets', 'parts', 'hand_open.png'), rgba)
    loc = lambda p: [round((p[0] - x0) * f, 1), round((p[1] - y0) * f, 1)]
    REG['assets'].append({
        'id': 'hand_open', 'kind': 'puppet_part', 'file': 'p04_hands/assets/parts/hand_open.png', 'size': [int(rgba.shape[1]), int(rgba.shape[0])],
        'pivot': loc(wrist), 'sockets': {'wrist': loc(wrist), 'fingertip': loc(tip), 'grip': loc((1000, 440)), 'palm': loc((640, 470))},
        'provenance': 'generated image (src/poet_open_hand.jpg, made with the pinch hand and parts sheet as reference), cut by p04_hands/build_assets.py',
        'ledger': 'INVENTED', 'view': 'profile, fingers right', 'material': 'cardboard, gouache', 'review': 'accepted',
        'note': 'scaled so wrist-to-fingertip is 1.12x the pinch hand (an open hand is longer than a pinch); grip = across the fingers (hand A holds B by its fingers and presents the wrist tab)'})


def build_citizen(frame):
    """One fixed scissor cut around the man, the union of his outline over the frames used; his film plays inside it."""
    masks = []
    for n in range(CIT0, CIT1 + 1):
        im = frame(n)
        sky = sky_of(im)
        h, w = sky.shape
        m = np.zeros((h, w), np.uint8)
        # per row: he is the dark run between the sky gap on his left (behind the other man's head) and the sky on his right
        xl = xr = None
        for y in range(h):
            row = sky[y].astype(np.int8)
            runs = np.flatnonzero(np.diff(np.concatenate([[0], row, [0]]))).reshape(-1, 2)  # [start, end) sky runs
            gaps = [e for s, e in runs if s > w * 0.12 and e < w * 0.8]
            if gaps:
                xl = max(gaps)
            if xl is not None:
                rs = [s for s, e in runs if s > xl + 20]
                if rs:
                    xr = min(rs)
            if xl is None or xr is None:
                continue
            m[y, xl:xr] = 1
        m &= (~sky).astype(np.uint8)
        masks.append(m)
    U = np.zeros_like(masks[0])
    for m in masks:
        U |= m
    U[int(U.shape[0] * 0.97):] = 0          # the bottom of the frame is cut straight off (he is at a rail)
    U = cv2.morphologyEx(U, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(U)
    U = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    U = cv2.dilate(U, np.ones((7, 7), np.uint8))   # a loose cut: a little 1969 sky stays around him
    ys, xs = np.where(U > 0)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    pad = 14
    x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(U.shape[1], x1 + pad), y1
    crop = U[y0:y1, x0:x1]
    big = cv2.resize(crop * 255, None, fx=CIT_SCALE, fy=CIT_SCALE, interpolation=cv2.INTER_LINEAR)
    rgba = np.dstack([np.zeros(big.shape + (3,), np.uint8), big])
    cut = paper_cut(rgba, rng, border=9, jag=(2, 8))
    alpha = cut[..., 3]
    ring = (cut[..., :3].sum(2) > 600) & (alpha > 0)
    cv2.imwrite(os.path.join(HERE, 'assets', 'parts', 'citizen_mask.png'), alpha)
    od = os.path.join(HERE, 'archive', 'citizen')
    os.makedirs(od, exist_ok=True)
    for f in os.listdir(od):
        os.remove(os.path.join(od, f))
    for n in range(CIT0, CIT1 + 1):
        im = frame(n)[y0:y1, x0:x1]
        im = cv2.resize(im, (alpha.shape[1], alpha.shape[0]), interpolation=cv2.INTER_LANCZOS4)
        im[ring] = (226, 232, 236)
        im[alpha == 0] = (0, 0, 0)
        cv2.imwrite(os.path.join(od, '%04d.jpg' % n), im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    # sockets: his face (for eyelines) and the base of the cut (where the stick holds it)
    fm = masks[-1][y0:y1, x0:x1]
    fys, fxs = np.where(fm[: int(fm.shape[0] * 0.6)] > 0)
    face = [float((fxs.min() + 10) * CIT_SCALE), float(np.median(fys) * CIT_SCALE)] if len(fxs) else [0, 0]
    hb, wb = alpha.shape
    REG['assets'].append({
        'id': 'citizen', 'kind': 'archive_cutout', 'file': 'p04_hands/assets/parts/citizen_mask.png',
        'frames': 'p04_hands/archive/citizen/%04d.jpg', 'frame_range': [CIT0, CIT1], 'fps': 29.97, 'size': [wb, hb],
        'pivot': [wb / 2, hb - 4], 'sockets': {'base': [wb / 2, hb - 4], 'face': face},
        'crop_in_source': [int(x0), int(y0), int(x1 - x0), int(y1 - y0)], 'scale': CIT_SCALE,
        'provenance': 'Eagle Has Landed: The Flight of Apollo 11 (1969), clip 6bb6d333, frames %d-%d of the clip (source film %.2f-%.2f s)'
                      % (CIT0, CIT1, 1513.81 + CIT0 / 29.97, 1513.81 + CIT1 / 29.97),
        'ledger': 'OBSERVED', 'treatment': 'one fixed scissor cut (the union of his outline over these frames, dilated), scaled %.2fx, white paper border; the film plays inside it' % CIT_SCALE,
        'view': 'he turns from three-quarter back to profile, facing left, and laughs', 'material': 'photograph cut with a paper border', 'review': 'accepted'})
    dbg = frame(CIT1).copy()
    cv2.rectangle(dbg, (int(x0), int(y0)), (int(x1), int(y1)), (0, 0, 255), 2)
    dbg[U > 0] = (dbg[U > 0] * 0.5 + np.array([0, 160, 0]) * 0.5).astype(np.uint8)
    cv2.imwrite(os.path.join(HERE, 'debug_citizen.jpg'), dbg)


def build_sky(frame):
    """the 1969 sky: for each pixel, the median of the frames in which it is sky (the clip's own pixels, no invented cloud)"""
    stack, ms = [], []
    k = np.ones((9, 9), np.uint8)
    for n in range(1, 305, 2):
        im = frame(n)
        stack.append(im.astype(np.float32)); ms.append(cv2.erode(sky_of(im).astype(np.uint8), k) > 0)
    S = np.array(stack); M = np.array(ms)
    cnt = M.sum(0)
    S[~M] = np.nan
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        med = np.nanmedian(S, axis=0)
    have = (cnt >= 8) & ~np.isnan(med[..., 0])
    med = np.nan_to_num(med)
    # fill where no frame shows sky: normalised blur of the valid pixels (smooth, no streaks), widening until filled
    out = med.copy()
    hv = have.astype(np.float32)
    for sig in (12, 30, 80, 200):
        num = cv2.GaussianBlur(med * hv[..., None], (0, 0), sig)
        den = cv2.GaussianBlur(hv, (0, 0), sig)[..., None]
        fill = num / np.maximum(den, 1e-4)
        miss = (~have) & (den[..., 0] > 0.02)
        out[miss] = fill[miss]
        have = have | miss
        hv = have.astype(np.float32)
        med = out
    out = np.clip(out, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(HERE, 'archive', 'sky1969.jpg'), out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    cov = float(((cnt >= 8)).mean())
    REG['assets'].append({
        'id': 'sky1969', 'kind': 'archive_assembled', 'file': 'p04_hands/archive/sky1969.jpg', 'size': [out.shape[1], out.shape[0]],
        'provenance': 'Eagle Has Landed (1969), clip 6bb6d333: per-pixel median over every second frame, sky pixels only (eroded 4 px, at least 8 samples)', 'ledger': 'RETOUCHED',
        'retouch': 'assembled from the clip\'s own sky pixels; where no frame shows sky (%.0f%% of the frame, mostly the lower half) the gap is filled with a smooth normalised blur of the sky around it' % (100 * (1 - cov)),
        'sky_coverage': round(cov, 3), 'review': 'accepted'})


def build_plate():
    img = cv2.imread(os.path.join(PLATE, 'image.jpg'))
    a = np.load(os.path.join(PLATE, 'arrays.npz'))
    lab = list(a['id2label']); seg = a['seg']
    s = W / img.shape[1]
    ph = int(round(img.shape[0] * s))
    up = lambda m, i=cv2.INTER_LINEAR: cv2.resize(m, (W, ph), interpolation=i)
    big = up(img, cv2.INTER_LANCZOS4)
    oy = (H - ph) // 2
    canvas = np.zeros((H, W, 3), np.uint8); canvas[oy:oy + ph] = big[:H - oy] if ph > H else big
    if ph > H:
        canvas = big[(ph - H) // 2:(ph - H) // 2 + H]; oy = -((ph - H) // 2)
    cv2.imwrite(os.path.join(HERE, 'set', 'plate.jpg'), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])
    place = lambda m: (lambda u: u[-oy:-oy + H] if oy < 0 else np.pad(u, ((oy, H - oy - ph), (0, 0))))(up(m))
    sky = a['sky'].astype(np.uint8) * 255
    sky = cv2.morphologyEx(sky, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    skym = cv2.GaussianBlur(place(sky), (5, 5), 1.4)
    cv2.imwrite(os.path.join(HERE, 'set', 'sky_mask.png'), skym)
    # the ledge at the bottom right (rock + the plants on it): an occluder cut from the plate, drawn in front of the citizen
    occ = np.isin(seg, [lab.index('rock, stone'), lab.index('plant'), lab.index('tree')]).astype(np.uint8)
    occ[: int(seg.shape[0] * 0.80)] = 0
    occ[:, : int(seg.shape[1] * 0.55)] = 0
    occ = cv2.morphologyEx(occ, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    om = cv2.GaussianBlur(place(occ * 255), (3, 3), 0.8)
    ys, xs = np.where(om > 128)
    ledge_top = int(np.percentile(ys[xs > 1300], 8)) if len(ys) else 960
    cv2.imwrite(os.path.join(HERE, 'set', 'ledge.png'), np.dstack([canvas, om]))
    # warm lantern lights in the plate (bright, warm, small): candidates for the light that finds the hands
    hsv = cv2.cvtColor(canvas, cv2.COLOR_BGR2HSV)
    warm = ((hsv[..., 0] < 30) & (hsv[..., 2] > 200) & (hsv[..., 1] > 60)).astype(np.uint8)
    n, l, st, cen = cv2.connectedComponentsWithStats(warm)
    lamps = sorted([[float(cen[i][0]), float(cen[i][1]), int(st[i, 4])] for i in range(1, n) if st[i, 4] > 6], key=lambda v: -v[2])[:12]
    meta = {'size': [W, H], 'plate_rect': [0, oy, W, ph], 'scale_from_plate': s,
            'plate': {'file': 'p04_hands/set/plate.jpg', 'ledger': 'INVENTED', 'provenance': 'WYGWYL poem_04 generated video, keyframe 84 (held), upscaled %.2fx' % s},
            'sky_mask': {'file': 'p04_hands/set/sky_mask.png', 'note': 'the plate\'s own sky mask; spires, trees and palms stay in front'},
            'ledge': {'file': 'p04_hands/set/ledge.png', 'top_y': ledge_top, 'note': 'rock + plants at the bottom right, cut from the plate; the citizen stands behind it'},
            'lamps': lamps}
    jdump(meta, os.path.join(HERE, 'set', 'set.json'))
    REG['assets'].append({'id': 'plate_p04_kf84', 'kind': 'plate', 'file': meta['plate']['file'], 'size': [W, H],
                          'provenance': meta['plate']['provenance'], 'ledger': 'INVENTED'})
    return meta


def atlas():
    items = []
    for a in REG['assets']:
        if a['kind'] == 'puppet_part':
            items.append((a['id'], cv2.imread(os.path.join(WEAVE, a['file']), cv2.IMREAD_UNCHANGED)))
    rects, size = pack_atlas(items, os.path.join(HERE, 'assets', 'atlas.png'))
    for a in REG['assets']:
        if a['id'] in rects:
            a['atlas_rect'] = rects[a['id']]
    REG['atlas'] = {'file': 'p04_hands/assets/atlas.png', 'size': size, 'check': 'every rect equals its source file (max abs diff 0)'}


if __name__ == '__main__':
    frame = raw_frames()
    reuse_puppet()
    build_open_hand()
    build_citizen(frame)
    build_sky(frame)
    meta = build_plate()
    atlas()
    jdump(REG, os.path.join(HERE, 'assets', 'assets.json'))
    print('assets', len(REG['assets']), 'atlas', REG['atlas']['size'], 'ledge top', meta['ledge']['top_y'], 'lamps', meta['lamps'][:4])
