"""CAFE COUPLE 1, the man (poem 13.1): short fade, full beard, cream short-sleeved camp shirt, light jeans,
brown sandals, brass brads.  His partner is chars/couple_1_b__poem13.py; the pairing is read from the card
names (1a / 1-b) and the matching clothes on the two-figure cards.

Masters (each card its own master: painted head cut down to the shirt collar, painted brads and hands
kept, scale pinned to 1):
  day  : family.13.couple-orbits/1a-1-b-day                       (seated profile to screen right, both
         arms reaching forward; no chair in the rig)
  lean : family.13.couple_1_a.heads-hands/lean-off-sheet-partner   (seated profile, leaning in, near hand on
         his knee, far hand reaching forward)
  walk : family.13.couple-orbits/harbor-wi-alk-two-by-two          a TWO-figure card (walking hand in hand with
         1B): split.  The bodies are apart; only the joined hands touch.  The clasp (both hands) goes with
         him, so his partner's arm ends at the wrist on her own rig.  Markers: couple_1_a__poem13.split.json.
The dusk turn (both hands held) does not separate cleanly: it is a pair master, chars/couple_1__poem13_pair.py.
Not rendered: the slow-turn 3/4-back card is clipped at the thighs by the sheet cut (no legs to rig).
"""
import sys

from . import _percard as pc

CHAR = 'couple_1_a__poem13'
DAY = 'family.13.couple-orbits/1a-1-b-day'
LEAN = 'family.13.couple_1_a.heads-hands/lean-off-sheet-partner'
TURN = 'family.13.couple_1_a.heads-hands/slow-turn-threequarter-back-both-hands-extended-'
WALK = 'family.13.couple-orbits/harbor-wi-alk-two-by-two'
MARKER_FILES = ['shots/rig/poses/couple_1_a__poem13.json', 'shots/rig/poses/couple_1_a__poem13.split.json']
EXCLUDE_TARGETS = {TURN: 'the card is clipped at the thighs by the sheet cut (cast_plan: poor, legs unmarked); '
                         'it cannot be its own master and no other rig of him is a standing 3/4 back'}

MARKER_FIX = {
    DAY: dict(shoulderR=(65, 87), elbowR=(107, 133), wristR=(172, 124), shoulderL=(100, 80), elbowL=(127, 130),
              wristL=(176, 119), hipR=(29, 175), hipL=(45, 172), groin=(38, 173), kneeR=(115, 156), kneeL=(140, 146),
              ankleR=(124, 222), ankleL=(161, 211), toeR=(162, 262), toeL=(220, 248), neck=(88, 80), chin=(125, 62),
              head=(100, 8)),
    LEAN: dict(shoulderR=(32, 78), elbowR=(56, 116), wristR=(108, 104), shoulderL=(88, 72), elbowL=(104, 92),
               wristL=(160, 94), hipR=(30, 170), hipL=(50, 165), groin=(40, 168), kneeR=(96, 129), kneeL=(127, 123),
               ankleR=(128, 200), ankleL=(178, 176), toeR=(168, 215), toeL=(230, 186), neck=(60, 55), chin=(88, 48),
               head=(75, 2)),
}
OPTS = {'tip_len': 0.35, 'hand_skin': True, 'torso_over_legs': False}

# the man on the harbor-walk card: left of the joined hands; the clasp is his
KEEP_WALK = [(0, 0), (121, 0), (121, 140), (124, 148), (129, 156), (130, 175), (120, 186), (104, 190), (102, 291), (0, 291)]

# his jeans belong to the legs wherever an arm or the torso took them; the cloth under each arm is filled
JEANS = [('legs', [(-5, -5), (300, -5), (300, 300), (-5, 300)], pc.denim)]
day = pc.builder(CHAR, DAY, seat=[(74, 50), (80, 56), (92, 72), (102, 82), (116, 80), (130, 72)], far_hidden='L', opts=OPTS,
                 give_=JEANS, fill_arms=0.2)
lean = pc.builder(CHAR, LEAN, seat=[(42, 45), (50, 58), (62, 66), (76, 62), (90, 52)], opts=OPTS, give_=JEANS, fill_arms=0.2)
walk = pc.builder(CHAR, WALK, keep=KEEP_WALK, seat=[(50, 46), (60, 52), (66, 60), (74, 52), (86, 46)], opts=OPTS, give_=JEANS,
                  fill_arms=0.2)

_NOTES = {'day': 'seated profile, both arms reaching forward; no chair in the rig',
          'lean': 'seated profile leaning in, near hand on his knee, far hand reaching forward; no chair in the rig',
          'walk': 'walking front, hand in hand with 1B; split off the two-figure harbor-walk card'}
pc.finish(sys.modules[__name__],
          {'day': (DAY, day, 'R', 'profR', 'sit'), 'lean': (LEAN, lean, 'R', 'profR', 'sit'), 'walk': (WALK, walk, None, 'front', 'walk')},
          _NOTES, 'cream_shirt', {'day': 'side', 'lean': 'side', 'walk': 'side'},
          {DAY: ['his far arm is behind the near one: its layer is empty (not invented); the near arm carries both hands'],
           WALK: ['split off a two-figure card: the painting column shows the whole card, the rig only him',
                  'his left hand holds 1B\'s right hand: the clasp (both hands, interlocked) is his hand; alone it is still '
                  'a clasp', 'hips, knees under the jeans placed on his brads by eye']})
BRAD_SOURCE = (DAY, 65.0, 87.0, 5.0, 6.5)
