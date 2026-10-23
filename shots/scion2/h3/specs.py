"""Masters and their layer cuts (H3 round 2).

FRONT : poet.11.main-poses/02-front-guide-stone   (front, standing, palms up)
Q3R   : poet.10.main-poses/q1-approach-bike        (3/4 to screen right, walking; bike cut away)

Neither family (poet.11, poet.10) is a test-target family.

Each builder returns, in master pixels:
  joints  : name -> (x, y)
  layers  : ordered back->front list of dicts
            {name, rgb, alpha, edgeok, bones:{bone:[(ja,jb),...]} | 'torso', tau, brads:[(joint,bone,r)],
             hand:{side: (x0,y0,nx,ny)}  (half-plane that is the painted hand, removed on a swap)}
  border  : width (px) of the painting's own paper edge, stripped and redrawn crisply at render
Bone names are shared by all masters; R/L follow the Pose Lab marker labels
(R = the arm/leg on screen-left in both of these views).
"""
import numpy as np, cv2

BONES = {
    'pelvis': ('midhip', 'waist', None),
    'chest': ('midhip', 'neck', 'pelvis'),
    'head': ('headpiv', 'headtop', 'chest'),
    'uarmR': ('shR', 'elR', 'chest'), 'farmR': ('elR', 'wrR', 'uarmR'), 'handR': ('wrR', 'tipR', 'farmR'),
    'uarmL': ('shL', 'elL', 'chest'), 'farmL': ('elL', 'wrL', 'uarmL'), 'handL': ('wrL', 'tipL', 'farmL'),
    'thighR': ('hipR', 'knR', 'pelvis'), 'shinR': ('knR', 'anR', 'thighR'), 'footR': ('anR', 'toR', 'shinR'),
    'thighL': ('hipL', 'knL', 'pelvis'), 'shinL': ('knL', 'anL', 'thighL'), 'footL': ('anL', 'toL', 'shinL'),
}
DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def grid(H, W):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return yy, xx


def poly(H, W, pts):
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    return m > 0


def interp_x(y, pts):
    return np.interp(y, [p[0] for p in pts], [p[1] for p in pts])


def plain_fabric(rgb, fig, er=9):
    b, g, r = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    dark = (r < 70) & (g < 70) & (b < 70) & (r < g + 25)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    return dark & e


def inpaint(rgb, fill, known, r=9):
    img = rgb.copy()
    m = (~known).astype(np.uint8)
    src = np.clip(img, 0, 255).astype(np.uint8)
    src[m.astype(bool)] = 0
    out = cv2.inpaint(src, m * 255, r, cv2.INPAINT_TELEA).astype(np.float32)
    img[fill] = out[fill]
    return img


def fade(al, region, ramp):
    """multiply alpha by ramp inside region (seam fade)"""
    return np.where(region, al * ramp, al)


# ---------------------------------------------------------------- FRONT
def build_front(rgb, a):
    H, W = a.shape
    yy, xx = grid(H, W)
    fig = a > 0.5
    J = dict(neck=(159.5, 80.0), headtop=(161.0, 4.0), headpiv=(159.5, 64.0), collar=(159.5, 63.0),
             midhip=(159.0, 190.0), waist=(159.0, 150.0), crotch=(158.5, 212.0),
             shR=(117.0, 87.5), elR=(93.5, 148.5), wrR=(51.0, 151.0), tipR=(10.0, 138.0),
             shL=(203.0, 87.5), elL=(226.0, 148.5), wrL=(269.0, 150.0), tipL=(310.0, 138.0),
             hipR=(129.5, 190.0), knR=(120.5, 288.0), anR=(104.5, 366.0), toR=(70.0, 404.0),
             hipL=(189.0, 190.0), knL=(199.5, 288.0), anL=(214.0, 364.5), toL=(252.0, 402.0))
    DIV_R = [(60, 131), (72, 130), (90, 125), (110, 117), (130, 113), (150, 110), (190, 110)]
    DIV_L = [(60, 189), (72, 190), (90, 195), (110, 202), (130, 205), (150, 207), (190, 207)]
    HEM = 183.0
    xr = interp_x(yy, DIV_R); xl = interp_x(yy, DIV_L)
    circ = lambda c, r: (xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= r * r
    head = fig & (yy < 64) & (xx > 128) & (xx < 194)
    armR = fig & (xx < xr) & (yy < HEM + 2) & (yy > 62)
    armL = fig & (xx > xl) & (yy < HEM + 2) & (yy > 62)
    torso_vis = fig & (yy >= 60) & (yy < HEM + 1) & (~armR | circ(J['shR'], 14)) & (~armL | circ(J['shL'], 14))
    for sh in (J['shR'], J['shL']):
        torso_vis |= fig & (yy < sh[1] + 2) & (yy >= 60) & (np.abs(xx - 159.5) < abs(sh[0] - 159.5) + 4) & ~head
    legs_vis = fig & (yy >= HEM - 4)
    side = np.zeros_like(fig)
    for y in range(80, int(HEM) + 1):
        xo = np.interp(y, [80, 100, 130, 160, HEM], [104, 104, 108, 110, 110])
        xo2 = np.interp(y, [80, 100, 130, 160, HEM], [216, 216, 211, 208, 208])
        side[y, int(xo):int(interp_x(y, DIV_R)) + 1] = True
        side[y, int(interp_x(y, DIV_L)):int(xo2) + 1] = True
    side &= fig | (yy < 160)
    # the jacket body with rounded shoulders: no square tab beyond the deltoid
    halfR = [(140, 58), (128, 64), (118, 70), (110, 77), (106, 86), (105, 96), (107, 120), (110, 150), (110, HEM + 1)]
    body = poly(H, W, halfR + [(319 - x, y) for x, y in halfR[::-1]])
    torso_vis &= body
    side &= body
    neck = (yy >= 44) & (yy < 66) & (xx > 145) & (xx < 175)
    torso_m = ((torso_vis | side | (neck & head)) & (body | (neck & head))) | (body & (yy > 60))
    plain = plain_fabric(rgb, fig)
    fill = torso_m & ~torso_vis
    torso_rgb = inpaint(rgb, fill, torso_vis & plain)
    torso_rgb[neck & head] = np.median(rgb[40:50, 147:152].reshape(-1, 3), 0) * 0.55
    waist = (yy >= 150) & (yy < HEM + 2) & (np.abs(xx - 159.5) <= 40 - np.clip(170 - yy, 0, 20) * 0.8)
    legs_m = legs_vis | waist
    legs_rgb = inpaint(rgb, legs_m & ~(legs_vis & (yy > HEM + 3)), legs_vis & (yy > HEM + 3) & (yy < 240) & plain)

    def arm_alpha(m, sh):
        al = m.astype(np.float32)
        inward = np.abs(xx - 159.5) < abs(sh[0] - 159.5)
        f = np.clip((np.abs(xx - 159.5) - (abs(sh[0] - 159.5) - 10)) / 10, 0, 1)
        seam = inward & (yy < sh[1])
        return fade(al, seam, f), seam & m

    aR, seamR = arm_alpha(armR, J['shR']); aL, seamL = arm_alpha(armL, J['shL'])
    head_a = head.astype(np.float32) * np.clip((65 - yy) / 4, 0, 1)
    ones = lambda m: np.ones(m.shape, np.float32)
    head_ok = (yy < 58).astype(np.float32)          # no edge line along the collar seat
    legs_ok = (yy > HEM - 2).astype(np.float32)      # hidden waist: no edge
    layers = [
        dict(name='legs', rgb=legs_rgb, alpha=legs_m.astype(np.float32), edgeok=legs_ok,
             bones={'pelvis': [('waist', 'crotch'), ('hipR', 'hipL')], 'thighR': [('hipR', 'knR')], 'shinR': [('knR', 'anR')],
                    'footR': [('anR', 'toR')], 'thighL': [('hipL', 'knL')], 'shinL': [('knL', 'anL')], 'footL': [('anL', 'toL')]},
             tau=3.2),
        dict(name='torso', rgb=torso_rgb, alpha=torso_m.astype(np.float32), edgeok=ones(a),
             bones='torso', torso=dict(y0=128, y1=176, caps=[('shR', 'uarmR'), ('shL', 'uarmL')], cx=159.5)),
        dict(name='head', rgb=rgb.copy(), alpha=head_a, edgeok=head_ok, bones={'head': [('headpiv', 'headtop')]}, tau=1.0,
             is_head=True),
        dict(name='armR', rgb=rgb.copy(), alpha=aR, edgeok=(~seamR).astype(np.float32),
             bones={'chest': [('neck', 'shR')], 'uarmR': [('shR', 'elR')], 'farmR': [('elR', 'wrR')], 'handR': [('wrR', 'tipR')]},
             tau=2.6, hand={'R': (50.0, 0, 1.0, 0.0)}, side='R'),
        dict(name='armL', rgb=rgb.copy(), alpha=aL, edgeok=(~seamL).astype(np.float32),
             bones={'chest': [('neck', 'shL')], 'uarmL': [('shL', 'elL')], 'farmL': [('elL', 'wrL')], 'handL': [('wrL', 'tipL')]},
             tau=2.6, hand={'L': (270.0, 0, -1.0, 0.0)}, side='L'),
    ]
    # brads: (name, layer drawn after, bone, x, y, brass radius, removal radius)
    brads = [('shR', 'armR', 'uarmR', 116.3, 86.0, 6.5, 10), ('elR', 'armR', 'farmR', 94.0, 147.0, 6.0, 9),
             ('shL', 'armL', 'uarmL', 203.0, 86.0, 6.5, 10), ('elL', 'armL', 'farmL', 226.0, 146.0, 6.0, 9),
             ('hipR', 'legs', 'thighR', 129.0, 190.0, 6.5, 10), ('hipL', 'legs', 'thighL', 189.0, 190.0, 6.5, 10),
             ('knR', 'legs', 'shinR', 120.0, 287.0, 6.5, 11), ('knL', 'legs', 'shinL', 198.0, 287.0, 6.5, 11),
             ('anR', 'legs', 'footR', 105.0, 363.0, 6.0, 12), ('anL', 'legs', 'footL', 214.0, 362.0, 6.0, 12)]
    return dict(joints=J, layers=layers, border=3.5, fig=fig, brads=brads)


# ---------------------------------------------------------------- 3/4 to screen right
def build_q3(rgb, a):
    H, W = a.shape
    yy, xx = grid(H, W)
    bike = ((xx >= 205) & (yy < 342)) | ((xx >= 196) & (yy >= 240) & (yy <= 342)) | (xx >= 234)
    fig = (a > 0.5) & ~bike
    n, lab, st, _ = cv2.connectedComponentsWithStats(fig.astype(np.uint8))
    fig = lab == (1 + np.argmax(st[1:, cv2.CC_STAT_AREA]))   # drop the bike's leftovers
    J = dict(neck=(118.0, 75.0), headtop=(146.0, 2.0), headpiv=(128.0, 62.0), collar=(128.0, 62.0),
             midhip=(97.0, 173.5), waist=(100.0, 140.0), crotch=(106.0, 215.0),
             shR=(97.5, 70.0), elR=(57.0, 124.0), wrR=(45.0, 174.0), tipR=(38.0, 222.0),
             shL=(146.0, 86.0), elL=(156.0, 140.0), wrL=(176.0, 182.0), tipL=(193.0, 216.0),
             hipR=(87.0, 176.0), knR=(68.0, 262.0), anR=(30.0, 330.0), toR=(66.0, 362.0),
             hipL=(107.0, 171.0), knL=(145.0, 252.0), anL=(167.0, 334.0), toL=(212.0, 362.0))
    HEM = 166.0
    # head above the collar
    cy = np.interp(xx, [100, 112, 125, 140, 160, 180], [40, 44, 58, 64, 68, 68])
    head = fig & (yy < cy) & (xx > 104) & (xx < 180) & (yy < 70)
    # near arm (R, screen-left, in front of the torso)
    armN_poly = [(122, 66), (110, 56), (90, 54), (66, 66), (48, 95), (36, 130), (24, 172), (15, 228), (62, 228), (66, 182),
                 (72, 166), (76, 140), (80, 116), (92, 98), (112, 84), (124, 76)]
    armN = fig & poly(H, W, armN_poly) & ~head
    # far arm (L, screen-right, behind the torso)
    armF_poly = [(140, 66), (152, 70), (160, 95), (166, 130), (178, 162), (206, 186), (206, 224), (166, 224), (158, 186),
                 (152, 168), (150, 140), (148, 110), (144, 88)]
    armF = fig & poly(H, W, armF_poly) & ~head
    torso_vis = fig & (yy < HEM + 2) & ~armN & ~armF & ~head & (yy > 40)
    # jacket behind the near arm: back contour runs down from the shoulder to the hem
    back = poly(H, W, [(104, 60), (84, 62), (70, 80), (66, 110), (64, 140), (66, HEM + 2), (80, HEM + 2), (78, 130), (84, 104),
                       (100, 86), (118, 78)])
    front = poly(H, W, [(140, 66), (146, 90), (149, 115), (150, 140), (146, 140), (143, 100), (138, 70)])
    neck = poly(H, W, [(118, 44), (140, 50), (146, 66), (124, 68)])
    body = poly(H, W, [(112, 52), (100, 57), (86, 62), (75, 74), (68, 94), (65, 125), (66, HEM + 2), (153, HEM + 2),
                       (152, 140), (149, 110), (145, 86), (140, 66), (128, 58)])
    torso_m = (torso_vis | (back & (armN | ~fig) & (yy > 58)) | (front & (armF | fig)) | (neck & head) |
               (armN & (yy < 96) & (xx > 66)) | body) & (body | (neck & head))
    torso_vis &= body
    plain = plain_fabric(rgb, fig, 7)
    torso_rgb = inpaint(rgb, torso_m & ~torso_vis, torso_vis & plain)
    torso_rgb[neck & head] = np.median(rgb[40:50, 150:156].reshape(-1, 3), 0) * 0.55
    # legs: near (R, back leg, screen-left) in front of far (L, forward) + pelvis
    legs_vis = fig & (yy >= HEM - 6) & ~armN & ~armF
    near = legs_vis & poly(H, W, [(60, 160), (100, 172), (104, 200), (108, 232), (100, 300), (70, 384), (0, 384), (0, 160)])
    farp = legs_vis & ~near
    waist = (yy >= 148) & (yy < HEM + 4) & poly(H, W, [(74, 148), (148, 148), (152, HEM + 4), (70, HEM + 4)])
    hipc = (xx - J['hipR'][0]) ** 2 + (yy - J['hipR'][1]) ** 2 <= 16 ** 2
    farp_m = farp | waist | (near & hipc & (yy < 200))   # the seat continues under the near hip only
    lrgb = inpaint(rgb, farp_m & ~(farp & (yy > HEM + 2)), legs_vis & (yy > HEM + 2) & (yy < 230) & plain, 7)
    # near leg's top fades into the seat around the hip
    near_a = near.astype(np.float32)
    seam_n = near & (yy < 202) & (xx > 62)
    near_a = fade(near_a, seam_n, np.clip((yy - 178) / 24, 0, 1))
    nrgb = rgb.copy()
    # near arm top fades into the jacket's shoulder
    sh = J['shR']
    seamA = armN & (((xx - sh[0]) * 0.8 + (yy - sh[1]) * -0.6) > 4) & (yy < 82)
    aN = fade(armN.astype(np.float32), seamA, np.clip(1 - (((xx - sh[0]) * 0.8 - (yy - sh[1]) * 0.6) - 4) / 12, 0, 1))
    head_a = head.astype(np.float32) * np.clip((cy + 2 - yy) / 4, 0, 1)
    ones = lambda: np.ones((H, W), np.float32)
    layers = [
        dict(name='armL', rgb=rgb.copy(), alpha=armF.astype(np.float32), edgeok=ones(),
             bones={'chest': [('neck', 'shL')], 'uarmL': [('shL', 'elL')], 'farmL': [('elL', 'wrL')], 'handL': [('wrL', 'tipL')]},
             tau=2.4, hand={'L': (0, 184.0, 0.0, -1.0)}, side='L'),
        dict(name='legs', rgb=lrgb, alpha=farp_m.astype(np.float32), edgeok=(yy > HEM - 2).astype(np.float32),
             bones={'pelvis': [('waist', 'crotch'), ('hipR', 'hipL')], 'thighL': [('hipL', 'knL')], 'shinL': [('knL', 'anL')],
                    'footL': [('anL', 'toL')]},
             tau=3.0),
        dict(name='legN', rgb=nrgb, alpha=near_a, edgeok=(~seam_n).astype(np.float32),
             bones={'pelvis': [('waist', 'midhip')], 'thighR': [('hipR', 'knR')], 'shinR': [('knR', 'anR')], 'footR': [('anR', 'toR')]},
             tau=3.0),
        dict(name='torso', rgb=torso_rgb, alpha=torso_m.astype(np.float32), edgeok=ones(),
             bones='torso', torso=dict(y0=115, y1=160, caps=[('shR', 'uarmR')], cx=118.0)),
        dict(name='head', rgb=rgb.copy(), alpha=head_a, edgeok=(yy < cy - 4).astype(np.float32),
             bones={'head': [('headpiv', 'headtop')]}, tau=1.0, is_head=True),
        dict(name='armR', rgb=rgb.copy(), alpha=aN, edgeok=(~seamA).astype(np.float32),
             bones={'chest': [('neck', 'shR')], 'uarmR': [('shR', 'elR')], 'farmR': [('elR', 'wrR')], 'handR': [('wrR', 'tipR')]},
             tau=2.6, hand={'R': (0, 176.0, 0.0, -1.0)}, side='R'),
    ]
    brads = [('shR', 'armR', 'uarmR', 98.0, 70.0, 5.5, 9), ('elR', 'armR', 'farmR', 58.0, 123.0, 5.7, 9),
             ('shL', 'torso', 'chest', 147.0, 82.0, 5.0, 8), ('elL', 'armL', 'farmL', 155.0, 139.0, 4.5, 7),
             ('hipL', 'legs', 'thighL', 105.0, 169.0, 5.7, 9), ('knL', 'legs', 'shinL', 145.0, 253.0, 6.0, 10),
             ('anL', 'legs', 'footL', 167.0, 334.0, 6.0, 11), ('knR', 'legN', 'shinR', 74.0, 262.0, 6.0, 10),
             ('anR', 'legN', 'footR', 32.0, 324.0, 5.7, 11)]
    return dict(joints=J, layers=layers, border=3.5, fig=fig, brads=brads)


MASTERS = {
    'front': ('poet.11.main-poses/02-front-guide-stone', build_front),
    'q3r': ('poet.10.main-poses/q1-approach-bike', build_q3),
}
