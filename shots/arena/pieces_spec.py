#!/usr/bin/env python3
"""
THE PIECE SPEC — what a cut-out has to be before it can be hung on this skeleton.

    python3 shots/arena/pieces_spec.py          -> shots/arena/pieces.json

The current library is not a body. Pinning the scale on the thigh, which is the
one piece that fits, every other card is too long for the bone it covers:

    shin +34%   forearm +68%   torso +60%   upper arm +79%   boot +74%   head +84%

Those are not one scale error. A scale error is uniform; these are six different
errors, which means the pieces were drawn independently and then hung on a
skeleton with different proportions. No placement code can fix that, which is
why the arms overlap by 50-68px while the shin gaps by 46px at the same time.

So: lengths come out of the Bolas skeleton, which states them in cm, and nothing
is guessed. Widths cannot come from there - the skeleton is a stick figure and
has no width - so widths are AUTHORED and are labelled as authored.

ONE AXIS RULE, NO EXCEPTIONS. Every card is drawn with joint A at its pivot and
joint B straight down the card. Every placement is then

    angle = atan2(B - A) - 90

for every piece. The thigh and the shin already do this. The boot was the one
exception - it took the raw atan2 of ankle->toe with no correction and no facing
term - and across T102 that puts the foot past vertical in 389 of 520 actor
frames. The foot is upside down for three quarters of the vignette, and because
abs(angle) > 30 selects boot.toe, it is upside down AND wearing the wrong card.
Exceptions to an axis convention are where feet go to die.
"""
import json, os, glob, math, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(HERE, 'bolas', 'bank')
OUT = os.path.join(HERE, 'pieces.json')

# HOW EACH PIECE IS MADE. Measured: tubes are 80% of the figure by card area and
# carry no identity — a sleeve is a sleeve. They should never be generated,
# because a drawn PNG has a fixed length and a bone does not, and that mismatch
# IS the brad gap. Drawn in code at exactly the bone length, the gap is zero by
# construction for half the body and there is nothing to accept or reject.
#
# What must be generated is what a tube cannot be: the head, the hands, the
# boots. 20% of the area and all of the likeness. The torso and pelvis sit
# between — featureless in shape but carrying the garment, so generated once and
# never articulated.
#
#   generate   head, hand, boot      18 cards per character, every view
#   garment    torso, pelvis          generated once, no articulation
#   procedural uarm, farm, thigh, shin  drawn in code, 50% of the figure, 0 cards

# The body has no side view. torso.profile and torso.front are the same picture
# (IoU 0.973, both 220px wide where a real side torso is about 60% the width);
# pelvis the same at 0.983; head.back is head.front at 0.964; and profile_L is
# threequarter_L at 0.917. Of six head 'views' about three are distinct, and the
# torso and pelvis have one each under two names. The renderer drew the fake
# 'profile' torso 7,484 times, more often than the front — so most of the arena
# is a man facing the camera wearing a profile head.
#
# And the hands have neither handedness nor facing: four shapes, one card each,
# so the same palm faces the camera whether the arm reaches toward it or away.
MAKE = {'head': 'generate', 'hand': 'generate', 'boot': 'generate',
        'torso': 'generate', 'pelvis': 'generate',
        'uarm': 'procedural', 'farm': 'procedural',
        'thigh': 'procedural', 'shin': 'procedural'}

# bone = (joint A, joint B). A is the pivot; B is straight down the card.
BONES = [
    ('head',   'headBase', 'headTop',   20.0, 'front|threequarter_L|threequarter_R|profile_L|profile_R|back'),
    ('torso',  'pelvis',   'neckBase',  36.0, 'front|threequarter|profile|back'),   # profile must be ~22cm deep, not 36
    ('pelvis', 'pelvis',   'hipL',      34.0, 'front|threequarter|profile|back'),
    ('uarm',   'shoulderL','elbowL',    11.0, 'profile'),
    ('farm',   'elbowL',   'wristL',     9.0, 'profile'),
    ('hand',   'wristL',   'wristL',     9.0, 'open_palm|open_back|grip|fist|point'),
    ('thigh',  'hipL',     'kneeL',     16.0, 'profile'),
    ('shin',   'kneeL',    'ankleL',    11.0, 'profile'),
    ('boot',   'ankleL',   'ballL',     10.0, 'flat|toe'),
]
HAND_CM = 19.0      # authored: wrist to fingertip

def measure():
    J = None; got = {}
    for f in sorted(glob.glob(os.path.join(BANK, 'T*.json'))):
        d = json.load(open(f))
        if J is None: J = {n: i for i, n in enumerate(d['joints'])}
        for fr in d['frames'][:1]:
            for aid, a in fr['a'].items():
                P = a['j']
                for name, ja, jb, w, views in BONES:
                    if ja == jb: continue
                    pa, pb = P[J[ja]], P[J[jb]]
                    got.setdefault(name, []).append(
                        math.dist(pa[:3], pb[:3]) if len(pa) > 2 else math.dist(pa, pb))
    return {k: round(st.median(v), 1) for k, v in got.items()}, len(got.get('thigh', []))

def main():
    L, n = measure()
    L['hand'] = HAND_CM
    H = 186.0
    pieces = []
    for name, ja, jb, w, views in BONES:
        pieces.append(dict(
            id=name, bone=[ja, jb],
            length_cm=L[name],
            length_source='measured from the Bolas skeleton' if name != 'hand' else 'authored (the skeleton ends at the wrist)',
            width_cm=w, width_source='authored — a stick figure has no width',
            pivot=[0.5, 0.0],      # joint A sits at the top centre of the card
            axis='joint B straight down the card; place at atan2(B-A) - 90',
            make=MAKE[name],
            views=views.split('|'),
            sides=['L', 'R'] if name in ('uarm', 'farm', 'hand', 'thigh', 'shin', 'boot') else ['-'],
        ))
    total_cards = sum(len(p['views']) * len(p['sides']) for p in pieces
                      if p['make'] != 'procedural')
    spec = dict(
        about='PIECE SPEC for the WYGWYL cut-out cast. Lengths measured from the '
              'Bolas skeleton; widths authored. One axis rule for every piece.',
        skeleton=dict(standing_height_cm=H, sampled_from=f'{n} actor-frames across the bank'),
        axis_rule='every card: joint A at the pivot, joint B straight down; '
                  'place at atan2(B-A) - 90. No exceptions — the boot was the '
                  'exception and it is upside down in 389 of 520 frames of T102.',
        cards_per_character=total_cards,
        pieces=pieces,
    )
    json.dump(spec, open(OUT, 'w'), indent=1)
    print(f'skeleton sampled over {n} actor-frames\n')
    print(f'{"piece":8s} {"bone":24s} {"cm":>6s} {"views":>6s} {"sides":>6s} {"cards":>6s}')
    for p in pieces:
        print(f'{p["id"]:8s} {p["bone"][0]+" -> "+p["bone"][1]:24s} {p["length_cm"]:6.1f} '
              f'{len(p["views"]):6d} {len(p["sides"]):6d} {len(p["views"])*len(p["sides"]):6d}')
    import collections
    by = collections.Counter()
    for p in pieces:
        by[p['make']] += len(p['views']) * len(p['sides'])
    print(f'\n{total_cards} cards to generate per character at one camera view.')
    print(f'   {by["generate"]} generated (head, hands, boots) · {by["garment"]} garment '
          f'(torso, pelvis) · {by["procedural"]} would-be cards replaced by code')
    print(f'-> {os.path.relpath(OUT, os.getcwd())}')

if __name__ == '__main__':
    main()
