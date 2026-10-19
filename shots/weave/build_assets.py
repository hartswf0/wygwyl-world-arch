"""Register the assets for the weave passage (poem 07, "So DJ please turn me up").

Every asset gets: a stable id, its own transparent PNG, a pivot, named sockets, provenance and a ledger column.
Outputs (all under shots/weave/assets/):
  parts/<id>.png      individual cut-outs (kept)
  atlas.png/.json     packed atlas; every packed rect is checked back against its source file
  assets.json         the registry
  debug_*.jpg         overlays used to check pivots by eye

Provenance columns:
  OBSERVED  archive frames (Sound And The Story, 1956), her recorded voice
  INVENTED  the AI world (WYGWYL poem_07 plate), generated puppet art
  RETOUCHED an observed frame changed by us (said what changed)
"""
import json, os
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(ROOT))
OUT = os.path.join(ROOT, 'assets')
os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True)

SHEET = os.path.join(ROOT, 'src', 'poet_parts_sheet.jpg')
ARCH = os.path.join(ROOT, 'archive', 'da69b1ba-1eb8-5072-8cf7-19fc272eba0f.mp4')
PLATE_DIR = os.path.join(REPO, 'shots', 'video', 'poem_07', 'out', 'vid-poem-07-kf00060_0')

REG = {'version': 1, 'about': 'weave assets for p07_turn_me_up', 'assets': []}


def alpha_from_white(bgr, extra_bg=None, max_hole=None):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    bg = (hsv[..., 1] < 28) & (hsv[..., 2] > 200)
    if extra_bg is not None:
        bg |= extra_bg
    fg = (~bg).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, 4]))
        fg = (lab == k).astype(np.uint8)
    if max_hole is None:
        # fill pin holes so a brad hole does not read as a hole through the card
        cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        solid = np.zeros_like(fg)
        cv2.drawContours(solid, cnts, -1, 1, -1)
    else:  # fill only small holes (the brad hole); keep larger openings (a pinch gap) open
        solid = fg.copy()
        n2, l2, s2, _ = cv2.connectedComponentsWithStats(1 - fg)
        for i in range(1, n2):
            x, y, w, h, a = s2[i]
            if a < max_hole and x > 0 and y > 0 and x + w < fg.shape[1] and y + h < fg.shape[0]:
                solid[l2 == i] = 1
    a = cv2.GaussianBlur(solid.astype(np.float32), (3, 3), 0.6)
    return (a * 255).astype(np.uint8)


def cut_part(sheet, pid, box, pivot, sockets, extra_bg_fn=None, note=''):
    x0, y0, x1, y1 = box
    crop = sheet[y0:y1, x0:x1].copy()
    extra = extra_bg_fn(crop) if extra_bg_fn else None
    a = alpha_from_white(crop, extra)
    ys, xs = np.where(a > 8)
    tx0, ty0, tx1, ty1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    crop, a = crop[ty0:ty1, tx0:tx1], a[ty0:ty1, tx0:tx1]
    rgba = np.dstack([crop, a])
    path = os.path.join(OUT, 'parts', pid + '.png')
    cv2.imwrite(path, rgba)
    off = (x0 + tx0, y0 + ty0)
    loc = lambda p: [round(p[0] - off[0], 1), round(p[1] - off[1], 1)]
    REG['assets'].append({
        'id': pid, 'kind': 'puppet_part', 'file': 'assets/parts/%s.png' % pid,
        'size': [int(rgba.shape[1]), int(rgba.shape[0])], 'sheet_rect': [int(off[0]), int(off[1]), int(rgba.shape[1]), int(rgba.shape[0])],
        'pivot': loc(pivot), 'sockets': {k: loc(v) for k, v in sockets.items()},
        'provenance': 'generated image (poet_parts_sheet.jpg), cut by build_assets.py', 'ledger': 'INVENTED',
        'view': 'profile, facing right' if pid != 'torso' else 'front (collage mix of views)',
        'material': 'cardboard, gouache', 'review': 'accepted', 'note': note,
    })
    return rgba, off


def build_puppet():
    sheet = cv2.imread(SHEET)

    def no_paper(crop):  # the notepad and pencil beside the open hand are not part of the hand
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        paper = (hsv[..., 1] < 70) & (hsv[..., 2] > 170)
        h, w = crop.shape[:2]
        right = np.zeros_like(paper)
        right[:, int(w * 0.62):] = True
        return paper | (right & (hsv[..., 2] < 120))

    # pivots and sockets are in SHEET pixels, measured on debug_sheet.jpg
    P = [
        ('head', (100, 30, 405, 400), (272, 352), {'neck': (272, 352), 'eye': (345, 222), 'mouth': (378, 285)}),
        ('torso', (505, 68, 740, 362), (622, 335), {'neck': (622, 90), 'shoulder_near': (690, 112), 'shoulder_far': (556, 112), 'hip': (622, 335)}),
        ('skirt', (468, 352, 795, 738), (630, 372), {'hip': (630, 372), 'knee_near': (668, 690), 'knee_far': (590, 690)}),
        ('upper_arm_near', (112, 410, 323, 500), (137, 447), {'shoulder': (137, 447), 'elbow': (314, 457)}),
        ('forearm_near', (822, 230, 1070, 306), (849, 266), {'elbow': (849, 266), 'wrist': (1046, 266)}),
        ('hand_near', (1064, 208, 1278, 334), (1086, 262), {'wrist': (1086, 262), 'palm': (1150, 262), 'fingertip': (1208, 255)}),
        ('upper_arm_far', (820, 88, 1019, 182), (850, 126), {'shoulder': (850, 126), 'elbow': (1012, 134)}),
        ('forearm_far', (104, 530, 310, 610), (127, 570), {'elbow': (127, 570), 'wrist': (285, 572)}),
        ('hand_far', (288, 545, 436, 732), (318, 598), {'wrist': (318, 598), 'palm': (350, 640)}),
        ('leg_near', (836, 405, 1010, 726), (885, 436), {'knee': (885, 436), 'sole': (930, 700)}),
        ('leg_far', (1085, 402, 1252, 726), (1202, 434), {'knee': (1202, 434), 'sole': (1168, 700)}),
    ]
    dbg = sheet.copy()
    for pid, box, piv, socks in P:
        if pid == 'hand_near':
            continue
        cut_part(sheet, pid, box, piv, socks)
        cv2.rectangle(dbg, box[:2], box[2:], (200, 200, 200), 1)
        cv2.circle(dbg, piv, 7, (0, 0, 255), 2)
        for k, v in socks.items():
            cv2.circle(dbg, v, 4, (255, 0, 0), -1)
            cv2.putText(dbg, k, (v[0] + 5, v[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 0, 0), 1)
        cv2.putText(dbg, pid, (box[0] + 2, box[1] + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 120, 0), 1)
    cv2.imwrite(os.path.join(OUT, 'debug_sheet.jpg'), dbg)
    build_pinch_hand()


def build_pinch_hand(f=0.2):
    """The near hand: a separate generated piece (poet_pinch_hand.jpg), scaled to the sheet. Its pinch gap stays open:
    the knob's edge sits in it, so the knob face stays readable while she turns it."""
    src = cv2.imread(os.path.join(ROOT, 'src', 'poet_pinch_hand.jpg'))
    a = alpha_from_white(src, max_hole=2000)
    ys, xs = np.where(a > 8)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    rgba = np.dstack([src[y0:y1, x0:x1], a[y0:y1, x0:x1]])
    rgba = cv2.resize(rgba, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(OUT, 'parts', 'hand_near.png'), rgba)
    loc = lambda p: [round((p[0] - x0) * f, 1), round((p[1] - y0) * f, 1)]
    REG['assets'].append({
        'id': 'hand_near', 'kind': 'puppet_part', 'file': 'assets/parts/hand_near.png', 'size': [int(rgba.shape[1]), int(rgba.shape[0])],
        'pivot': loc((270, 516)), 'sockets': {'wrist': loc((270, 516)), 'palm': loc((560, 430)), 'fingertip': loc((770, 501))},
        'provenance': 'generated image (poet_pinch_hand.jpg, made with the parts sheet as reference), cut by build_assets.py',
        'ledger': 'INVENTED', 'view': 'profile, facing right', 'material': 'cardboard, gouache', 'review': 'accepted',
        'note': 'replaces the sheet hand, which was painted over a notepad; fingertip socket = centre of the pinch gap'})


def build_console():
    """The console is cut from the archive itself: frame 3.75 s, cropped above the chrome strip so the 1956 hand is out of it."""
    cap = cv2.VideoCapture(ARCH)
    cap.set(cv2.CAP_PROP_POS_MSEC, 3750)
    ok, fr = cap.read()
    assert ok
    S = 4  # 320x240 -> 1280x960, Lanczos; the film grain is kept, not invented away
    big = cv2.resize(fr, None, fx=S, fy=S, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(os.path.join(OUT, 'debug_console_frame.jpg'), big)
    H = 204 * S  # above the chrome strip; the hand is below it at this time
    base = big[:H].copy()

    # middle knob: find its circle
    g = cv2.medianBlur(cv2.cvtColor(base, cv2.COLOR_BGR2GRAY), 5)
    roi = g[560:H, 480:840]
    c = cv2.HoughCircles(roi, cv2.HOUGH_GRADIENT, 1.2, 200, param1=80, param2=25, minRadius=55, maxRadius=95)
    if c is not None:
        kx, ky, kr = c[0][0]
        kx, ky, kr = float(kx + 480), float(ky + 560), float(kr)
    else:
        kx, ky, kr = 658.0, 705.0, 75.0
    kr += 6
    yy, xx = np.mgrid[:base.shape[0], :base.shape[1]]
    disc = (((xx - kx) ** 2 + (yy - ky) ** 2) <= kr ** 2).astype(np.uint8) * 255
    x0, y0 = int(kx - kr - 2), int(ky - kr - 2)
    x1, y1 = int(kx + kr + 3), int(ky + kr + 3)
    knob = np.dstack([base[y0:y1, x0:x1], disc[y0:y1, x0:x1]])
    cv2.imwrite(os.path.join(OUT, 'parts', 'knob_mid.png'), knob)

    # meter needle: retouch it out of the observed frame so a drawn needle can read the measured level
    needle = np.zeros(base.shape[:2], np.uint8)
    cv2.line(needle, (556, 258), (486, 170), 255, 17)
    retouched = cv2.inpaint(base, needle, 5, cv2.INPAINT_TELEA)

    # the cut: a photograph trimmed with scissors, a thin white paper border, slightly irregular
    h, w = retouched.shape[:2]
    rng = np.random.default_rng(56)
    pts = []
    for t in np.linspace(0, 1, 40, endpoint=False):
        pts.append((int(t * w), int(rng.uniform(4, 14))))
    for t in np.linspace(0, 1, 30, endpoint=False):
        pts.append((w - int(rng.uniform(4, 14)), int(t * h)))
    for t in np.linspace(1, 0, 40, endpoint=False):
        pts.append((int(t * w), h - int(rng.uniform(4, 14))))
    for t in np.linspace(1, 0, 30, endpoint=False):
        pts.append((int(rng.uniform(4, 14)), int(t * h)))
    outer = np.zeros((h, w), np.uint8)
    cv2.fillPoly(outer, [np.array(pts)], 255)
    inner = cv2.erode(outer, np.ones((15, 15), np.uint8))
    rgba = np.dstack([retouched, outer])
    rgba[(outer > 0) & (inner == 0), :3] = (226, 232, 236)  # paper border
    cv2.imwrite(os.path.join(OUT, 'parts', 'console_base.png'), rgba)

    REG['archive_frame'] = {'clip': 'da69b1ba-1eb8-5072-8cf7-19fc272eba0f', 't': 3.75, 'scale': S,
                            'title': 'Sound And The Story', 'year': 1956,
                            'page': 'https://www.movingimagearchive.com/sources/sound-and-the-story-331f8150?clip=da69b1ba-1eb8-5072-8cf7-19fc272eba0f'}
    REG['assets'].append({
        'id': 'console_base', 'kind': 'prop_part', 'file': 'assets/parts/console_base.png', 'size': [w, h],
        'pivot': [w / 2, h], 'sockets': {'knob_mid': [round(kx, 1), round(ky, 1)], 'needle_pivot': [548, 248],
                                          'needle_rest': [494, 182], 'meter_center': [652, 150], 'base_contact': [w / 2, h]},
        'provenance': 'Sound And The Story (1956), clip da69b1ba, frame 3.75 s, upscaled 4x', 'ledger': 'RETOUCHED',
        'retouch': 'meter needle painted out (cv2.inpaint) so a drawn needle can show the measured level; cropped above the chrome strip',
        'view': 'front', 'material': 'photograph cut with a paper border', 'review': 'accepted'})
    REG['assets'].append({
        'id': 'knob_mid', 'kind': 'prop_part', 'file': 'assets/parts/knob_mid.png', 'size': [x1 - x0, y1 - y0],
        'pivot': [round(kx - x0, 1), round(ky - y0, 1)], 'sockets': {'grip': [round(kx - x0, 1), round(ky - y0 - kr * 0.55, 1)]},
        'radius': round(kr, 1), 'provenance': 'Sound And The Story (1956), same frame, the middle knob cut as a disc', 'ledger': 'OBSERVED',
        'view': 'front', 'material': 'photograph', 'review': 'accepted'})
    dbg = base.copy()
    cv2.circle(dbg, (int(kx), int(ky)), int(kr), (0, 0, 255), 2)
    cv2.line(dbg, (548, 248), (494, 182), (0, 255, 0), 2)
    cv2.imwrite(os.path.join(OUT, 'debug_console.jpg'), np.hstack([dbg, retouched]))
    return big


def build_plate():
    img = cv2.imread(os.path.join(PLATE_DIR, 'image.jpg'))
    REG['assets'].append({'id': 'plate_p07_kf60', 'kind': 'plate', 'file': os.path.relpath(os.path.join(PLATE_DIR, 'image.jpg'), ROOT),
                          'size': [img.shape[1], img.shape[0]], 'provenance': 'WYGWYL poem_07 generated video, keyframe 60', 'ledger': 'INVENTED'})


def pack_atlas():
    parts = [a for a in REG['assets'] if a['kind'] in ('puppet_part', 'prop_part')]
    imgs = [cv2.imread(os.path.join(ROOT, a['file']), cv2.IMREAD_UNCHANGED) for a in parts]
    order = sorted(range(len(parts)), key=lambda i: -imgs[i].shape[0])
    W, pad = 2048, 4
    x = y = rowh = 0
    rects = {}
    for i in order:
        h, w = imgs[i].shape[:2]
        if x + w + pad > W:
            x, y, rowh = 0, y + rowh + pad, 0
        rects[i] = (x, y, w, h)
        x += w + pad
        rowh = max(rowh, h)
    H = y + rowh
    atlas = np.zeros((H, W, 4), np.uint8)
    for i, (x, y, w, h) in rects.items():
        atlas[y:y + h, x:x + w] = imgs[i]
    cv2.imwrite(os.path.join(OUT, 'atlas.png'), atlas)
    worst = 0
    for i, (x, y, w, h) in rects.items():  # check every packed rect against its source
        worst = max(worst, int(np.abs(atlas[y:y + h, x:x + w].astype(int) - imgs[i].astype(int)).max()))
        parts[i]['atlas_rect'] = [x, y, w, h]
    assert worst == 0, 'atlas mismatch %d' % worst
    REG['atlas'] = {'file': 'assets/atlas.png', 'size': [W, H], 'check': 'every rect equals its source file (max abs diff 0)'}


if __name__ == '__main__':
    build_puppet()
    build_console()
    build_plate()
    pack_atlas()
    json.dump(REG, open(os.path.join(OUT, 'assets.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    print('parts', len([a for a in REG['assets'] if a['kind'] == 'puppet_part']), 'atlas', REG['atlas']['size'])
