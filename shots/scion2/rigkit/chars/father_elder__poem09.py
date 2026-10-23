"""The FATHER as an elder (poem 09.4, walking east with the poet): grey herringbone overcoat over a dark
three-piece suit, white shirt, black tie, grey flat cap, grey beard, black boots, brass brads; a wooden
cane with a brass collar in his right hand.

Masters (each card its own master: painted head hand-cut down to the shirt collar, painted brads and
hands kept, scale pinned to 1):
  walk   : parents.09.phone-prayer-walk/walk-east  (standing 3/4 to screen right, cane planted)
  steady : parents.09.phone-prayer-walk/father-elder-poet-steady-shoulder-falter -- a TWO-figure card (the
           father's hand on the poet's shoulder).  The father is split off it (he is drawn wholly in front
           of the poet; nothing of him is hidden): his target is in shots/rig/poses/father_elder__poem09.split.json
           and the poet is cut away.  His left hand rests on the poet's shoulder: it is cut with the hand,
           and on its own it hangs in the air where the shoulder was.
The cane is cut with the right hand (it rides the hand, skinned to one bone from the wrist to its tip);
the coat under it is filled from the coat round it.  The coat skirt rides the torso; the trousers below
it are the legs.  No back view of him exists (cast_plan gap: 09.4 is "two backs walking away").
"""
import sys

from . import _percard as pc

CHAR = 'father_elder__poem09'
PW = 'parents.09.phone-prayer-walk/'
WALK, STEADY = PW + 'walk-east', PW + 'father-elder-poet-steady-shoulder-falter'
MARKER_FILES = ['shots/rig/poses/father_elder__poem09.json', 'shots/rig/poses/father_elder__poem09.split.json']

MARKER_FIX = {
    WALK: dict(shoulderR=(56, 142), shoulderL=(202, 145), elbowR=(24, 242), elbowL=(222, 258), wristR=(48, 300),
               wristL=(226, 330), hipR=(95, 345), hipL=(150, 345), groin=(122, 352), kneeR=(100, 470), kneeL=(159, 483),
               ankleR=(110, 578), ankleL=(146, 610), toeR=(72, 625), toeL=(188, 668), neck=(133, 118), chin=(184, 113),
               head=(150, 2)),
}

_HEAD_W = [(98, 98), (86, 72), (76, 45), (80, 30), (92, 15), (118, 0), (150, -4), (195, 10), (228, 28), (226, 48), (206, 52),
           (208, 80), (202, 100), (194, 118), (178, 122), (160, 113), (140, 121), (106, 101)]
_SEAT_W = [(94, 96), (106, 101), (140, 121), (160, 113), (178, 122), (204, 120)]
CANE_W = [(48, 300), (78, 318), (74, 352), (62, 400), (42, 650), (42, 672), (12, 672), (15, 650), (42, 400), (50, 352)]
# the coat from the waist down (the waist band the legs layer takes, and both skirts) rides the torso;
# the trousers between the skirts are the legs
COAT_W = [(64, 260), (205, 260), (205, 335), (250, 335), (250, 490), (170, 490), (165, 455), (152, 360), (150, 345),
          (103, 345), (100, 360), (80, 470), (78, 490), (0, 490), (0, 350), (84, 350), (84, 290), (64, 280)]
TROUSERS_W = [(100, 343), (152, 343), (165, 470), (80, 470)]

OPTS = {'tip_len': 0.2, 'hand_skin': True, 'torso_over_legs': False, 'limb_r': (0.22, 0.2)}
# the black ferrule at the cane's foot is not warm: given by position
GIVE_W = [('torso', COAT_W), ('legs', TROUSERS_W), ('armR', CANE_W, pc.warm, 'torso'), ('armR', [(10, 640), (46, 640), (46, 690), (10, 690)])]

walk = pc.builder(CHAR, WALK, head=_HEAD_W, seat=_SEAT_W, give_=GIVE_W, opts=OPTS, prop_ends={'R': (28, 668)}, fill_arms='hull', front_arms=True)

_NOTES = {'walk': 'standing 3/4 to screen right, cane planted in his right hand'}
MASTERS_ = {'walk': (WALK, walk, 'R', '3qR', 'walk')}
pc.finish(sys.modules[__name__], MASTERS_, _NOTES, 'overcoat', {'walk': 'side'},
          {WALK: ['the cane rides his right hand (cut with it); the coat behind it is filled from the coat round it',
                  'his left hand is hidden at his side (no hand painted below the cuff)',
                  'no back view of him exists (09.4 wants two backs walking away)']})
BRAD_SOURCE = (WALK, 56.0, 142.0, 6.0, 7.5)

# ---- steady: the father split off the two-figure card (the poet cut away)
_HAND_S = [(244, 178), (258, 163), (270, 152), (285, 148), (306, 148), (311, 154), (306, 160), (304, 165), (296, 170),
           (290, 177), (278, 186), (268, 198), (256, 208), (246, 212), (244, 200)]
KEEP_S = [(0, 0), (200, 0), (200, 150), (230, 178)] + _HAND_S[:-1] + [(248, 222), (200, 240), (178, 240), (176, 430),
                                                                       (170, 682), (0, 682)]
_HEAD_S = [(48, 92), (44, 60), (44, 40), (50, 15), (70, 0), (100, -4), (140, 10), (178, 28), (180, 44), (158, 50), (160, 70),
           (156, 92), (150, 112), (144, 124), (128, 124), (112, 126), (100, 121), (62, 100)]
_SEAT_S = [(50, 95), (62, 100), (100, 121), (112, 126), (128, 124), (150, 124)]
CANE_S = [(96, 362), (132, 362), (130, 682), (104, 682)]
# the coat below the shoulders, less his near sleeve (upper arm down the back, forearm to the cuff)
COAT_S = [(48, 230), (176, 230), (176, 482), (0, 482), (0, 300), (20, 300), (40, 335), (62, 348), (104, 316), (72, 250),
          (48, 240)]
steady = pc.builder(CHAR, STEADY, keep=KEEP_S, cut_pred=[(_HAND_S, pc.very_dark)], head=_HEAD_S, seat=_SEAT_S,
                    give_=[('torso', COAT_S), ('armR', [(20, 248), (72, 248), (105, 316), (62, 350), (38, 337), (18, 300)]),
                           ('armR', CANE_S, pc.warm, 'torso'),
                           ('armR', [(68, 312), (142, 312), (142, 392), (68, 392)], pc.warm, 'torso'),
                           ('armR', [(108, 668), (132, 668), (132, 682), (106, 682)])], opts=OPTS, prop_ends={'R': (118, 678)},
                    fill_arms='hull', front_arms=True)
_NOTES['steady'] = ('profile to screen right, his left hand laid on the poet\'s shoulder, the cane in his right; split off '
                    'the two-figure card father-elder-poet-steady-shoulder-falter (the poet is cut away)')
MASTERS_['steady'] = (STEADY, steady, 'R', 'profR', 'stand')
pc.finish(sys.modules[__name__], MASTERS_, _NOTES, 'overcoat', {'walk': 'side', 'steady': 'side'},
          {WALK: ['the cane rides his right hand (cut with it); the coat behind it is filled from the coat round it',
                  'his left hand is hidden at his side (no hand painted below the cuff)',
                  'no back view of him exists (09.4 wants two backs walking away)'],
           STEADY: ['split off a two-figure card: the painting column shows the whole card, the rig only the father',
                    'his reaching hand was painted on the poet\'s shoulder: the poet\'s dark jacket between its fingers is cut '
                    'away, so a few finger gaps show; alone, the hand rests on air',
                    'his far shoulder, far knee and hips are hidden (placed by eye); the cane rides his near hand']})
