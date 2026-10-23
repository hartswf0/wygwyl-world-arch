"""The DJ of poem 07 (07.0, 07.6): black cyber tracksuit with violet and blue light piping, black cap,
blue headphones round the neck, black and violet sneakers, brass brads; trimmed beard.

Six whole-figure paintings on party.07.dj_cyber.main-poses, each its own master (six different
drawings: four crouch at the decks, one dances from behind, one stands; none can be re-posed into
another without inventing what it hides, so each is only ever posed on its own rig):
  crouch : 01-crouch-land        (crouching front, one hand on the floor, the other arm out)
  scratch: 02-scratch            (crouching, 3/4 to screen right, a hand on the record)
  listen : 03-listen-lift-earcup (one knee down, 3/4 to screen right, lifting an earcup)
  push   : 04-push-master        (crouching, 3/4 to screen right, a hand on the controller)
  back   : 05-dance-back         (from behind, both arms up, pointing; head turned to screen right)
  front  : 06-stand-front        (standing front, arms down)
The DJ controllers on 02 and 04 are set pieces on the floor (not held): cut away, not in the rig; the
hand that touches each stays his.  No profile painting exists.
Markers: shots/rig/poses/dj_cyber__cyber.json (MoveNet); every card re-marked by hand on its brads
(MoveNet had crossed limbs and hips on most crouches).  Back card: R/L by screen side as MoveNet read
it (his R on screen left).
"""
import numpy as np, cv2

from . import _cardrig

CHAR = 'dj_cyber__cyber'
SH = 'party.07.dj_cyber.main-poses/'
MARKER_FILES = ['shots/rig/poses/dj_cyber__cyber.json']

MARKER_FIX = {
    SH + '01-crouch-land': {'head': (165, 5), 'chin': (170, 113), 'neck': (165, 130),
                            'shoulderR': (98, 108), 'elbowR': (94, 203), 'wristR': (125, 290),
                            'shoulderL': (232, 63), 'elbowL': (308, 72), 'wristL': (380, 92),
                            'hipR': (140, 210), 'hipL': (230, 205), 'kneeR': (23, 198), 'kneeL': (293, 165),
                            'ankleR': (62, 263), 'ankleL': (328, 265), 'toeR': (25, 310), 'toeL': (400, 330)},
    SH + '02-scratch': {'head': (225, 10), 'chin': (215, 118), 'neck': (195, 125),
                        'shoulderR': (121, 85), 'elbowR': (84, 160), 'wristR': (130, 235),
                        'shoulderL': (262, 108), 'elbowL': (299, 190), 'wristL': (330, 265),
                        'hipR': (160, 215), 'hipL': (230, 230), 'kneeR': (48, 168), 'kneeL': (258, 288),
                        'ankleR': (58, 277), 'ankleL': (150, 295), 'toeR': (15, 355), 'toeL': (172, 312)},
    SH + '03-listen-lift-earcup': {'head': (170, 10), 'chin': (195, 105), 'neck': (170, 125),
                                   'shoulderR': (87, 108), 'elbowR': (35, 195), 'wristR': (20, 280),
                                   'shoulderL': (228, 120), 'elbowL': (300, 180), 'wristL': (268, 105),
                                   'hipR': (80, 262), 'hipL': (160, 262), 'kneeR': (60, 345), 'kneeL': (246, 220),
                                   'ankleR': (120, 360), 'ankleL': (265, 327), 'toeR': (110, 385), 'toeL': (325, 395)},
    SH + '04-push-master': {'head': (290, 30), 'chin': (295, 128), 'neck': (255, 140),
                            'shoulderR': (190, 87), 'elbowR': (79, 163), 'wristR': (140, 178),
                            'shoulderL': (342, 124), 'elbowL': (362, 222), 'wristL': (345, 300),
                            'hipR': (220, 230), 'hipL': (290, 250), 'kneeR': (112, 212), 'kneeL': (418, 280),
                            'ankleR': (94, 327), 'ankleL': (295, 320), 'toeR': (15, 405), 'toeL': (285, 335)},
    SH + '05-dance-back': {'head': (165, 15), 'chin': (180, 68), 'neck': (148, 75),
                           'shoulderR': (95, 107), 'elbowR': (32, 157), 'wristR': (15, 110),
                           'shoulderL': (203, 90), 'elbowL': (287, 103), 'wristL': (290, 48),
                           'hipR': (128, 225), 'hipL': (215, 220), 'kneeR': (78, 314), 'kneeL': (248, 313),
                           'ankleR': (77, 397), 'ankleL': (272, 393), 'toeR': (20, 452), 'toeL': (330, 452)},
    SH + '06-stand-front': {'head': (114, 4), 'chin': (114, 72), 'neck': (114, 95),
                            'shoulderR': (56, 103), 'elbowR': (29, 179), 'wristR': (25, 230),
                            'shoulderL': (168, 103), 'elbowL': (191, 179), 'wristL': (200, 230),
                            'hipR': (75, 240), 'hipL': (148, 240), 'kneeR': (66, 328), 'kneeL': (156, 328),
                            'ankleR': (56, 402), 'ankleL': (168, 402), 'toeR': (20, 465), 'toeL': (210, 465)},
}


def PLAIN(rgb, fig, er=7):
    """the black tracksuit: dark pixels well inside the figure, not the light piping, not brass"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    dark = (r < 70) & (g < 70) & (b < 80)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    return dark & e


CARDS = {
    'crouch': dict(id=SH + '01-crouch-land', view='front', cls='crouch', costume='cyber',
                   note='crouching front (landing), one hand on the floor, the other arm out'),
    'scratch': dict(id=SH + '02-scratch', view='3qR', cls='crouch', costume='cyber',
                    note='crouching, 3/4 to screen right, a hand on the record',
                    cut=[[(148, 384), (150, 320), (180, 300), (285, 294), (416, 294), (416, 384)]], cut_keeps_skin=True,
                    flags=['the DJ controller under his hand is a set piece on the floor: cut away (not in the rig); his '
                           'hand on it is kept (skin), the toe of his far sneaker behind it is cut along its edge']),
    'listen': dict(id=SH + '03-listen-lift-earcup', view='3qR', cls='kneel', costume='cyber',
                   note='one knee down, 3/4 to screen right, lifting an earcup'),
    'push': dict(id=SH + '04-push-master', view='3qR', cls='crouch', costume='cyber',
                 note='crouching, 3/4 to screen right, a hand on the controller',
                 cut=[[(158, 438), (158, 388), (165, 355), (200, 345), (290, 342), (442, 345), (442, 438)]], cut_keeps_skin=True,
                 flags=['the DJ controller under his hand is a set piece on the floor: cut away (not in the rig); his '
                        'hand on it is kept (skin), his far foot behind it is cut along its edge']),
    'back': dict(id=SH + '05-dance-back', view='back', cls='dance', costume='cyber',
                 note='from behind, both arms up pointing, head turned to screen right'),
    'front': dict(id=SH + '06-stand-front', view='front', cls='stand', costume='cyber', note='standing front, arms down'),
}

_cardrig.setup(globals(), CARDS, PLAIN, {'tip_len': 0.35, 'hand_skin': True, 'torso_over_legs': False, 'limb_r': (0.2, 0.2)},
               view_rigs={'front': ('front', False), '3qR': ('scratch', False), '3qL': ('scratch', True), 'profR': ('scratch', False),
                          'profL': ('scratch', True), 'back': ('back', False), 'back3qR': ('back', False), 'back3qL': ('back', False)})
