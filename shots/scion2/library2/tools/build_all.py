"""Run every part type for the given characters (automatic pipeline + fixes.json).

    python3 shots/scion2/library2/tools/build_all.py party_guest poet_soul ...
"""
import sys
import heads, hands, feet, segments, headbuilder

for ch in sys.argv[1:]:
    print('==', ch)
    heads.run(ch)
    hands.run(ch)
    feet.run(ch)
    for part in ('torso', 'pelvis', 'upper_arm', 'forearm', 'thigh', 'shin'):
        segments.run(ch, part)
    headbuilder.run(ch)
