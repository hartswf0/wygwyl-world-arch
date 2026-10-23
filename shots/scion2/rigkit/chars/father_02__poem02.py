"""The FATHER of poem 02 (02.4, driving): short fade, full beard, olive quilted jacket, red-and-black plaid
scarf, dark jeans, black lace-up boots, brass brads.

Two whole-figure paintings exist, both SEATED profiles to screen right with both fists on an (unpainted)
steering wheel, and nearly identical (the second has the hips a little higher).  Each is its own master
(rig 'drive' and 'drive2'), keeps its painted head (hand-cut down to the scarf) and its painted hand.
His far arm is hidden behind the near arm in both: the far-arm layer is empty (no arm is invented), so
only the near arm moves.  No standing, front or back painting of him exists (cast_plan: none needed).
Markers: shots/rig/poses/father_02__poem02.json (MoveNet, "medium"): every joint re-placed below on his
brads (near side = 'R').
"""
import sys

from . import _percard as pc

CHAR = 'father_02__poem02'
CA = 'parents.02.car-argument/'
D1, D2 = CA + 'father-driver-profile', CA + 'father-driver-profile-2'
MARKER_FILES = ['shots/rig/poses/father_02__poem02.json']

MARKER_FIX = {
    D1: dict(shoulderR=(46, 98), elbowR=(113, 138), wristR=(209, 121), shoulderL=(98, 94), elbowL=(140, 132), wristL=(205, 120),
             hipR=(44, 214), hipL=(66, 208), groin=(56, 220), kneeR=(154, 196), ankleR=(186, 276), toeR=(245, 296),
             kneeL=(192, 185), ankleL=(237, 266), toeL=(318, 290), neck=(84, 76), chin=(136, 84), head=(110, 1)),
    D2: dict(shoulderR=(49, 98), elbowR=(113, 141), wristR=(208, 122), shoulderL=(98, 94), elbowL=(140, 132), wristL=(205, 121),
             hipR=(43, 206), hipL=(66, 200), groin=(56, 212), kneeR=(153, 191), ankleR=(186, 270), toeR=(245, 290),
             kneeL=(195, 176), ankleL=(238, 256), toeL=(318, 284), neck=(85, 77), chin=(137, 85), head=(111, 2)),
}

# his head down to the plaid scarf (card px, card 1; card 2 is the same drawing 1 px lower and right)
_HEAD = [(60, 38), (62, 18), (72, 4), (88, -6), (104, -8), (124, -6), (142, 2), (150, 16), (152, 30), (156, 44), (160, 54),
         (154, 64), (148, 72), (146, 82), (142, 88), (118, 88), (103, 79), (78, 57), (62, 49)]
_SEAT = [(64, 49), (78, 57), (103, 79), (118, 88), (140, 88)]
_sh = lambda pts, d: [(x + d, y + d) for x, y in pts]

OPTS = {'tip_len': 0.35, 'hand_skin': True, 'torso_over_legs': False, 'limb_r': (0.26, 0.2)}


def _b(pid, d):
    return pc.builder(CHAR, pid, head=_sh(_HEAD, d), seat=_sh(_SEAT, d), far_hidden='L', opts=OPTS)


_NOTE = 'seated driver profile, both fists on an unpainted steering wheel; no car seat or wheel in the rig'
pc.finish(sys.modules[__name__],
          {'drive': (D1, _b(D1, 0), 'R', 'profR', 'sit'), 'drive2': (D2, _b(D2, 1), 'R', 'profR', 'sit')},
          {'drive': _NOTE, 'drive2': _NOTE}, 'quilted_jacket', {'drive': 'side', 'drive2': 'side'},
          {pid: ['his far arm is hidden behind the near arm: the far-arm layer is empty (not invented); only the near '
                 'arm can move', 'seated only: no standing, walking or back painting of him exists'] for pid in (D1, D2)})
# required by the rig builder; never drawn (his brads stay painted)
BRAD_SOURCE = (D1, 46.5, 98.0, 6.0, 7.5)
