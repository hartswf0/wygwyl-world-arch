"""gaps.json from out/runs.json: every test pose H1 could not reach within the cap, with
what is missing and a brief for the painting that would close it."""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h1core as H

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {'torso': 'torso lean', 'head': 'head tilt', 'uarmL': 'left upper arm', 'farmL': 'left forearm',
         'uarmR': 'right upper arm', 'farmR': 'right forearm', 'thighL': 'left thigh', 'shinL': 'left shin',
         'thighR': 'right thigh', 'shinR': 'right shin'}


def view_name(M):
    sw, hw, face = H.view_feat(M)
    if abs(sw) < .25:
        v = 'profile'
    elif abs(sw) < .5:
        v = 'three-quarter'
    else:
        v = 'front' if sw > 0 else 'back'
    side = 'facing screen-right' if face > .05 else 'facing screen-left' if face < -.05 else 'facing out'
    return f'{v}, {side}'


def bone_dir(M, b):
    a, c = H.BONES[b]
    v = M[c] - M[a]
    ang = math.degrees(math.atan2(-v[1], v[0]))  # screen angle, 0 = pointing right, 90 = up
    return round(ang)


def main():
    targets = H.load_targets()
    ts = {p['id']: p for p in json.load(open(H.TESTSET))['poses']}
    runs = json.load(open(os.path.join(HERE, 'out', 'runs.json')))
    gaps = []
    for r in runs:
        if r['reached'] and not r['rotation_wanted_beyond_cap']:
            continue
        tid = r['target']
        M = H.markers(targets[tid])
        miss = {NAMES[b]: f'needs {abs(d):.0f} deg turn from the nearest painting (cap {H.HEAD_CAP if b == "head" else H.CAP:.0f})'
                for b, d in r['rotation_wanted_beyond_cap'].items()}
        gaps.append(dict(
            target=tid, kind=ts[tid]['kind'],
            status='rendered at the cap; pose not reached' if not r['reached'] else 'reached within cap+15 deg; some parts short of the target',
            nearest_painting=r['source'] + (' (mirrored)' if r['mirrored'] else ''),
            beyond_cap=miss,
            painting_brief=dict(
                pose=ts[tid]['kind'],
                view=view_name(M),
                screen_angles_deg={NAMES[b]: bone_dir(M, b) for b in NAMES if b not in ('torso', 'head')},
                torso_angle_deg=bone_dir(M, 'torso'),
                note='angles: 0 = pointing screen-right, 90 = up, -90 = down; a painting in another family '
                     'within ~25 deg of every listed part closes this gap for H1',
                reference=ts[tid]['painting'])))
    out = dict(about='H1 gaps: test poses the capped warp could not reach from paintings of other families. '
                     'Each brief describes the painting that would close the gap.',
               cap_deg=H.CAP, head_cap_deg=H.HEAD_CAP, gaps=gaps)
    json.dump(out, open(os.path.join(HERE, 'gaps.json'), 'w'), indent=1)
    print(len(gaps), 'gaps')


if __name__ == '__main__':
    main()
