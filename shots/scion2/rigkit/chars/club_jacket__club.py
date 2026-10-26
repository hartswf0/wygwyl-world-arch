"""CLUB DANCER IN A JACKET (08.1): a club dancer from the 08 sheet, costume 'jacket'.

Two whole-figure dance paintings on 08.cast.club.main-poses, each its own master (the cards are only posed
on their own rig, so nothing is swapped between them):
  front : fast-dance-collision-reach-1-2  (dance, front)
  3/4   : fast-dance-collision-reach-2-2  (dance, reaching, 3/4)
No neutral stand, back or profile painting of this dancer exists; the body coverage page lists the gaps.
Markers: shots/rig/poses/club_jacket__club.json (MoveNet), used as the markers of each card.
"""
import numpy as np

from . import _cardrig

CHAR = 'club_jacket__club'
MARKER_FILES = ['shots/rig/poses/club_jacket__club.json']
S = '08.cast.club.main-poses/'
CARDS = {
    'front': dict(id=S + 'fast-dance-collision-reach-1-2', view='front', cls='dance', costume='jacket',
                  note='dancing, front (08.1): no neutral stand'),
    '3qR': dict(id=S + 'fast-dance-collision-reach-2-2', view='3qR', cls='dance', costume='jacket',
                note='dancing, reaching, 3/4 to screen right (08.1): no profile or back'),
}


def plain_fn(rgb, fig, er=3):
    """the dancer's fabric: figure pixels inside, away from skin and the brass"""
    import cv2
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    gold = (r > 150) & (g > 120) & (b < 120)
    skin = (r > g + 12) & (g > b + 15) & (r > 70) & (r < 200)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    return e & ~skin & ~gold


_cardrig.setup(globals(), CARDS, plain_fn, {'tip_len': 0.35, 'hand_skin': True, 'torso_over_legs': False},
               view_rigs={v: (k, False) for v, k in [('front', 'front'), ('3qR', '3qR')] + [(x, 'front') for x in ('3qL', 'profR', 'profL', 'back', 'back3qR', 'back3qL')]},
               border=2.5)
