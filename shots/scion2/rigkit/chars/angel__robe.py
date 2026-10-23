"""The ANGEL of poem 08 (08.3, the angels pouring ice water: one painted angel used three times):
white robe with a rope belt, wide bell sleeves, brass brads, bare feet, great white wings; short
dark hair and beard.

Six whole-figure paintings on 08.cast.angel.main-poses, each its own master (the six are different
drawings of the same angel, from six angles, three of them with the basin: none can be re-posed into
another without inventing what it hides, so each card is only ever posed on its own rig):
  front  : 1-front-arms-lowered-wings-folded          (standing front, arms down, wings folded)
  prof   : float-2-profile-knees-wings-half-open-bent (floating, profile to screen right, knees bent)
  back   : 3-back-view-wings-open                     (from behind, arms out, wings spread)
  tipR   : 4-angel-left-tipping-basin-inward-right    (3/4 to screen right, tipping the basin)
  tipL   : 5-angel-right-tipping-basin-inward-left    (3/4 to screen left, tipping the basin)
  above  : 6-angel-above-tilted-down-tipping-basin    (seen from above, head bowed, pouring down)
Feathers and robe are both white: the wings are told apart by the painted tan outline round them
(chars/_cardrig.py) and are one layer behind the body, riding the chest.  The basin, its ice and the
falling water are cut with the hands holding it, as one hand's part, so they ride the wrist (on the
card seen from above the falling water is painted over the robe, which is not painted behind it: there
it stays with the robe).
The robe hides the legs: knees are guesses (on the knee brads where painted).
Markers: shots/rig/poses/angel__robe.json (MoveNet), corrected below.
"""
import numpy as np, cv2

from . import _cardrig

CHAR = 'angel__robe'
SH = '08.cast.angel.main-poses/'
MARKER_FILES = ['shots/rig/poses/angel__robe.json']

MARKER_FIX = {
    # the legs under the robe: the right knee on its brad, feet on the painted feet
    SH + '1-front-arms-lowered-wings-folded': {'kneeR': (111, 287), 'kneeL': (148, 287), 'ankleR': (113, 372), 'ankleL': (137, 372),
                                               'toeR': (110, 405), 'toeL': (142, 405)},
    SH + 'float-2-profile-knees-wings-half-open-bent': {'toeL': (230, 375)},
    # one foot shows, trailing to the lower left; the knee brad at (187, 241)
    SH + '4-angel-left-tipping-basin-inward-right': {'kneeR': (188, 240), 'kneeL': (198, 248), 'ankleR': (136, 312), 'ankleL': (140, 316),
                                                     'toeR': (120, 356), 'toeL': (126, 362)},
    SH + '5-angel-right-tipping-basin-inward-left': {'kneeL': (289, 245), 'kneeR': (275, 252), 'ankleL': (341, 307), 'ankleR': (335, 305),
                                                     'toeL': (344, 355), 'toeR': (340, 352)},
    # MoveNet put the head and the hips on the basin: head bowed over the chest, hips behind the basin,
    # feet under the robe's hem
    SH + '6-angel-above-tilted-down-tipping-basin': {'head': (233, 20), 'chin': (231, 88), 'neck': (230, 66),
                                                     'hipR': (210, 165), 'hipL': (255, 165), 'kneeR': (205, 215), 'kneeL': (265, 215),
                                                     'ankleR': (200, 265), 'ankleL': (275, 265), 'toeR': (202, 285), 'toeL': (282, 285)},
}


def PLAIN(rgb, fig, er=5):
    """the white robe: light unsaturated pixels well inside the figure"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    return (mn > 170) & (mx - mn < 30) & e


CARDS = {
    'front': dict(id=SH + '1-front-arms-lowered-wings-folded', view='front', cls='stand', costume='robe',
                  note='standing front, arms down, wings folded',
                  head=[(104, 72), (108, 62), (104, 50), (102, 35), (104, 15), (112, 5), (128, 1), (144, 5), (152, 15), (154, 35), (152, 50),
                        (146, 62), (146, 72)],
                  wings=[(30, 200), (225, 200)], fill=[(110, 220)],
                  flags=['the background removal had punched a hole in the robe (x 98-121, y 201-246); its painted pixels are '
                         'intact and the rig restores them']),
    'prof': dict(id=SH + 'float-2-profile-knees-wings-half-open-bent', view='profR', cls='float', costume='robe',
                 note='floating, profile to screen right, knees bent, one wing half open',
                 head=[(258, 70), (262, 55), (255, 40), (256, 20), (265, 8), (285, 4), (300, 10), (312, 28), (318, 40), (320, 48), (316, 55),
                       (310, 60), (300, 63), (296, 70), (300, 80), (285, 83), (270, 78), (262, 74)],
                 wings=[(100, 150)]),
    'back': dict(id=SH + '3-back-view-wings-open', view='back', cls='stand', costume='robe',
                 note='from behind, arms out, wings spread',
                 head=[(268, 73), (272, 60), (266, 50), (264, 35), (266, 15), (275, 4), (292, 0), (308, 5), (316, 18), (316, 35), (314, 50),
                       (308, 60), (312, 72), (290, 75)],
                 wings=[(100, 150), (470, 150)]),
    'tipR': dict(id=SH + '4-angel-left-tipping-basin-inward-right', view='3qR', cls='float', costume='robe',
                 note='3/4 to screen right, tipping the basin of ice water',
                 head=[(248, 62), (254, 52), (252, 40), (253, 20), (262, 8), (280, 3), (298, 8), (308, 20), (310, 35), (306, 50), (302, 58),
                       (296, 64), (290, 70), (282, 76), (270, 82), (258, 76), (250, 70)],
                 wings=[(100, 120)],
                 prop=dict(side='R', what='basin', front=True, raw_all=True, water=[[(425, 165), (481, 150), (481, 377), (405, 377), (408, 200)]],
                           poly=[(293, 138), (300, 128), (320, 127), (372, 129), (378, 122), (395, 122), (418, 132), (440, 150), (470, 160),
                                 (481, 175), (481, 377), (440, 377), (425, 260), (415, 200), (400, 205), (360, 207), (330, 195), (310, 188),
                                 (296, 184), (292, 170)]),
                 flags=['the basin, its water and both hands on it are one part on his right wrist: the left forearm ends at '
                        'the wrist and the left hand stays on the rim']),
    'tipL': dict(id=SH + '5-angel-right-tipping-basin-inward-left', view='3qL', cls='float', costume='robe',
                 note='3/4 to screen left, tipping the basin of ice water',
                 head=[(182, 52), (185, 42), (184, 30), (188, 15), (198, 6), (215, 3), (232, 6), (240, 15), (237, 30), (236, 45), (240, 55),
                       (242, 68), (236, 76), (225, 82), (214, 76), (208, 68), (200, 65), (192, 58)],
                 wings=[(360, 150)],
                 prop=dict(side='L', what='basin', front=True, raw_all=True, water=[[(0, 150), (62, 150), (66, 200), (60, 368), (0, 368)]],
                           poly=[(0, 368), (0, 250), (20, 190), (45, 160), (60, 150), (70, 138), (82, 128), (100, 126), (112, 120), (119, 128),
                                 (125, 132), (150, 129), (178, 138), (186, 145), (199, 165), (188, 182), (160, 186), (140, 200), (110, 210),
                                 (80, 207), (66, 197), (57, 250), (50, 300), (32, 350), (20, 368)]),
                 flags=['the basin, its water and both hands on it are one part on his left wrist: the right forearm ends at '
                        'the wrist and the right hand stays on the rim']),
    'above': dict(id=SH + '6-angel-above-tilted-down-tipping-basin', view='front', cls='float', costume='robe',
                  note='seen from above, head bowed, pouring the basin straight down',
                  head=[(210, 55), (212, 35), (220, 23), (233, 19), (246, 23), (254, 35), (256, 55), (252, 70), (246, 82), (236, 90), (226, 90),
                        (216, 82), (212, 70)],
                  wings=[(80, 130), (400, 130)],
                  water=[[(205, 200), (292, 200), (292, 376), (205, 376)]],
                  prop=dict(side='R', what='basin', front=True, raw_all=True,
                            poly=[(146, 146), (150, 135), (165, 127), (200, 121), (260, 121), (300, 126), (310, 135), (316, 145), (324, 150),
                                  (326, 185), (306, 192), (285, 200), (268, 206), (220, 206), (208, 205), (180, 200), (160, 190), (148, 186)]),
                  flags=['the basin and both hands on it are one part on his right wrist; the water falling below the basin '
                         'is painted over the robe (the robe behind it is not painted): it stays with the robe and the pelvis, '
                         'so it parts from the basin if the arms move']),
}

_cardrig.setup(globals(), CARDS, PLAIN, {'tip_len': 0.35, 'hand_skin': True, 'torso_over_legs': False, 'limb_r': (0.2, 0.2)},
               view_rigs={'front': ('front', False), '3qR': ('tipR', False), '3qL': ('tipL', False), 'profR': ('prof', False),
                          'profL': ('prof', True), 'back': ('back', False), 'back3qR': ('back', False), 'back3qL': ('back', False)})
# the water drops are small separate pieces: kept by the render's speck filter (see core)
SPECK_MIN_PX = 6
# the falling water reaches well beyond the body mesh: the render window is widened round it (see core)
RENDER_MARGIN = 200
