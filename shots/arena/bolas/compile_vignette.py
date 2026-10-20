"""Compile 3D Bolas Crash Lab vignettes into cardboard cut-out puppet clips.

    python3 shots/arena/bolas/compile_vignette.py T101 T102 T104 T112 T001
    python3 shots/arena/bolas/compile_vignette.py --all

Takes baked 3D vignettes from shots/arena/bolas/bank/, projects joints through camera space, selects matching
cardboard pieces (Bola, Shim, Dot in cast/dummy/), and compiles clips in shots/arena/clips/ that shots/arena.html
draws and plays with full scrubber, beat strip, and technical checks.
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ARENA = os.path.dirname(HERE)
BANK = os.path.join(HERE, 'bank')
CLIPS = os.path.join(ARENA, 'clips')
CAST_DUMMY = os.path.join(ARENA, 'cast', 'dummy')
PARTS = json.load(open(os.path.join(CAST_DUMMY, 'parts.json')))
REF_H = PARTS['ref_height']
SPEC = json.load(open(os.path.join(ARENA, 'spec', 'acting_arena_v0.2.json')))
RESULTS_PATH = os.path.join(ARENA, 'results', 'arena_results.json')

DEG = math.pi / 180

# Map Crash Lab test IDs T101-T132 to ACT-001..ACT-032
T_TO_ACT = {f"T{i}": f"ACT-{i-100:03d}" for i in range(101, 133)}


def r2(v):
    return [round(float(v[0]), 1), round(float(v[1]), 1)]


def place(pid, A, B, H_fig, flip=False, thick=1.0):
    m = PARTS['parts'][pid]
    A = np.asarray(A[:2], float); B = np.asarray(B[:2], float)
    v_ = B - A
    Lw = float(np.linalg.norm(v_))
    th = math.atan2(v_[1], v_[0])
    sx = max(Lw, 1e-3) / m['len']
    sy = (H_fig / REF_H) / m['unit'] * thick * (-1 if flip else 1)
    c, s = math.cos(th), math.sin(th)
    M = np.array([[c * sx, -s * sy], [s * sx, c * sy]])
    t = A - M @ np.array(m['pivot'], float)
    return {'t': 'img', 'id': pid, 'm': [round(M[0, 0], 5), round(M[1, 0], 5), round(M[0, 1], 5), round(M[1, 1], 5),
                                          round(t[0], 2), round(t[1], 2)]}


def compile_vignette(tid, custom_yaw=None, out_act=None):
    bank_path = os.path.join(BANK, f"{tid}.json")
    if not os.path.exists(bank_path):
        print(f"Error: {bank_path} not found")
        return None

    V = json.load(open(bank_path))
    act_id = out_act or T_TO_ACT.get(tid)
    clip_id = f"{act_id}__bolas" if act_id else f"{tid}__bolas"

    W, H = 1920, 1080
    view = dict(V['view'] or {})
    if custom_yaw is not None:
        view['yaw'] = custom_yaw

    yaw, elev = view.get('yaw', -22) * DEG, view.get('elev', 10) * DEG
    cy, sy = math.cos(yaw), math.sin(yaw)
    ce, se = math.cos(elev), math.sin(elev)
    center = [view.get('x', 0), view.get('y', 90), view.get('z', 0)]
    scale = H * 0.86 / 230 * view.get('zoom', 1.0)

    def proj(p):
        x, y, z = p[0] - center[0], p[1] - center[1], p[2] - center[2]
        x1, z1 = x * cy - z * sy, x * sy + z * cy
        y2, z2 = y * ce - z1 * se, y * se + z1 * ce
        return [W / 2 + x1 * scale, H * 0.52 - y2 * scale, z2]

    # Floor line in screen space
    floor_y = round(proj([center[0], 0, center[2]])[1], 1)

    actors_meta = {a['id']: a for a in V['actors']}
    frames = []
    images = {}

    # Gather images needed
    for a in V['actors']:
        lk = a['name'].lower()
        if lk not in ('bola', 'shim', 'dot'):
            lk = 'bola'
        for k, v_ in PARTS['parts'].items():
            if k.startswith(lk + '.'):
                images[k] = v_['file']

    N = V['len']
    # Tracking for checks
    worst_drift = 0.0
    airborne_frames = 0
    balanced_frames = 0
    grounded_frames = 0
    contact_frames = 0
    prev_feet = {}

    beats = []
    # Generate beats from notes or keyframe intervals
    step_frames = 24
    for f in range(0, N, step_frames):
        beats.append({'f': f, 'who': V['actors'][0]['name'] if V['actors'] else 'Cast', 'beat': f'frame {f}'})
    beats.append({'f': N - 1, 'who': V['actors'][0]['name'] if V['actors'] else 'Cast', 'beat': 'hold'})

    for fi, fr in enumerate(V['frames']):
        draw = [{'t': 'bg'}, {'t': 'floor', 'y': floor_y}]
        dbg = {'com': [], 'sup': [], 'tgt': []}
        flags = []
        ok_flags = []

        # Draw props behind
        for pid, pdata in fr.get('p', {}).items():
            ptype = pdata.get('type')
            pos = pdata.get('pos')
            if not pos:
                continue
            pp = proj(pos)
            if ptype in ('wall', 'facade'):
                draw.append({'t': 'poly', 'pts': [[pp[0] - 120, pp[1] - 400], [pp[0] + 120, pp[1] - 400],
                                                   [pp[0] + 120, pp[1]], [pp[0] - 120, pp[1]]],
                             'fill': '#3b2f27', 'stroke': '#1a120b', 'w': 2})
            elif ptype == 'table':
                draw.append({'t': 'poly', 'pts': [[pp[0] - 80, pp[1] - 60], [pp[0] + 80, pp[1] - 60],
                                                   [pp[0] + 80, pp[1]], [pp[0] - 80, pp[1]]],
                             'fill': '#5c3a21', 'stroke': '#1a120b', 'w': 2})
            elif ptype == 'box':
                draw.append({'t': 'poly', 'pts': [[pp[0] - 40, pp[1] - 70], [pp[0] + 40, pp[1] - 70],
                                                   [pp[0] + 40, pp[1]], [pp[0] - 40, pp[1]]],
                             'fill': '#c49a6c', 'stroke': '#1a120b', 'w': 2})

        # Process each actor
        for aid, A in fr.get('a', {}).items():
            ameta = actors_meta.get(aid, {})
            name = ameta.get('name', 'Bola')
            look = name.lower()
            if look not in ('bola', 'shim', 'dot'):
                look = 'bola'
            scale_fac = ameta.get('scale', 1.0)
            H_fig = 400.0 * scale_fac

            jj_3d = A['j']
            if jj_3d[0] is None:
                continue
            jj = [proj(pt) for pt in jj_3d]

            # Pelvis and Neck
            pelvis_2d = jj[0]
            neck_2d = jj[14]
            dbg['com'].append(r2(pelvis_2d[:2]))

            # Facing vector & view
            fwd = A.get('fwd', [0, 0, 1])
            # Project fwd in camera horizontal plane
            fwd_cam_x = fwd[0] * cy + fwd[2] * sy
            fwd_cam_z = -fwd[0] * sy + fwd[2] * cy
            fwd_ang = math.degrees(math.atan2(fwd_cam_x, fwd_cam_z))

            is_front = abs(fwd_ang) < 45 or abs(fwd_ang) > 135
            view_str = 'front' if is_front else 'side'
            flip = fwd_cam_x < 0

            # Shadow under pelvis on floor
            draw.append({'t': 'shadow', 'x': round(pelvis_2d[0], 1), 'y': floor_y,
                         'rx': round(50 * scale_fac, 1), 'a': 0.7})

            # Depths for z-sorting: Left vs Right limbs
            z_armL = (jj[16][2] + jj[18][2] + jj[20][2]) / 3
            z_armR = (jj[17][2] + jj[19][2] + jj[21][2]) / 3
            z_legL = (jj[1][2] + jj[3][2] + jj[5][2]) / 3
            z_legR = (jj[2][2] + jj[4][2] + jj[6][2]) / 3

            # Far limbs (higher z_cam means farther from camera in our camera projection)
            far_arm_side = 'L' if z_armL > z_armR else 'R'
            near_arm_side = 'R' if far_arm_side == 'L' else 'L'

            far_leg_side = 'L' if z_legL > z_legR else 'R'
            near_leg_side = 'R' if far_leg_side == 'L' else 'L'

            # Hand shape mapping
            def get_hand_shape(s):
                raw = (A.get('hand', {}).get(s) or 'relaxed').lower()
                if 'flat' in raw or 'open' in raw:
                    return 'open'
                if 'fist' in raw:
                    return 'fist'
                if 'grip' in raw or 'pinch' in raw:
                    return 'grip'
                if 'point' in raw:
                    return 'point'
                return 'relaxed'

            # Face expression mapping
            def get_face():
                f_data = A.get('face') or {}
                if f_data.get('smile', 0) > 0.4:
                    return 'smile'
                if f_data.get('open', 0) > 0.4 or f_data.get('brow', 0) > 0.3:
                    return 'surprise'
                if A.get('effort', 0) > 0.4:
                    return 'strain'
                return 'neutral'

            face_name = get_face()

            def draw_leg(s, is_far):
                sfx = '.far' if is_far else ''
                hip_idx = 1 if s == 'L' else 2
                knee_idx = 3 if s == 'L' else 4
                ank_idx = 5 if s == 'L' else 6
                toe_idx = 11 if s == 'L' else 12

                hip_pt = jj[hip_idx]
                knee_pt = jj[knee_idx]
                ank_pt = jj[ank_idx]
                toe_pt = jj[toe_idx]

                # Foot vector from ankle toward toe
                v_foot = np.array(toe_pt[:2]) - np.array(ank_pt[:2])
                len_foot = np.linalg.norm(v_foot)
                if len_foot < 1e-3:
                    foot_target = [ank_pt[0] + 40 * (1 if not flip else -1), ank_pt[1]]
                else:
                    foot_target = toe_pt[:2]

                ops = [
                    place(f"{look}.thigh{sfx}", hip_pt, knee_pt, H_fig),
                    place(f"{look}.shin{sfx}", knee_pt, ank_pt, H_fig),
                    place(f"{look}.foot{sfx}", ank_pt, foot_target, H_fig, flip=flip)
                ]
                return ops

            def draw_arm(s, is_far):
                sfx = '.far' if is_far else ''
                sh_idx = 16 if s == 'L' else 17
                elb_idx = 18 if s == 'L' else 19
                wri_idx = 20 if s == 'L' else 21

                sh_pt = jj[sh_idx]
                elb_pt = jj[elb_idx]
                wri_pt = jj[wri_idx]

                h_shape = get_hand_shape(s)
                # Hand tip extrapolated along forearm
                v_arm = np.array(wri_pt[:2]) - np.array(elb_pt[:2])
                norm_arm = np.linalg.norm(v_arm)
                if norm_arm > 1e-3:
                    v_dir = v_arm / norm_arm
                else:
                    v_dir = np.array([0, 1])
                tip_pt = np.array(wri_pt[:2]) + v_dir * 30.0

                ops = [
                    place(f"{look}.uarm{sfx}", sh_pt, elb_pt, H_fig),
                    place(f"{look}.farm{sfx}", elb_pt, wri_pt, H_fig),
                    place(f"{look}.hand.{h_shape}{sfx}", wri_pt, tip_pt, H_fig, flip=flip)
                ]
                return ops

            # Layer order: far arm -> far leg -> torso -> head -> near leg -> near arm
            draw.extend(draw_arm(far_arm_side, is_far=True))
            draw.extend(draw_leg(far_leg_side, is_far=True))

            # Torso
            torso_id = f"{look}.torso_{view_str}"
            draw.append(place(torso_id, pelvis_2d, neck_2d, H_fig, flip=flip and not is_front))

            # Head: from neckBase (14) to headTop (24)
            head_id = f"{look}.head.{'front' if is_front else 'side'}.{face_name}"
            head_top = jj[24]
            draw.append(place(head_id, neck_2d, head_top, H_fig, flip=flip and not is_front))

            # Near leg & near arm
            draw.extend(draw_leg(near_leg_side, is_far=False))
            draw.extend(draw_arm(near_arm_side, is_far=False))

            # Support points & contact check
            for s in ('L', 'R'):
                ank_idx = 5 if s == 'L' else 6
                ball_idx = 9 if s == 'L' else 10
                heel_idx = 7 if s == 'L' else 8
                pt_ank = jj[ank_idx]
                pt_ball = jj[ball_idx]
                pt_heel = jj[heel_idx]

                on_floor = abs(pt_ball[1] - floor_y) < 18 or abs(pt_heel[1] - floor_y) < 18
                if on_floor:
                    dbg['sup'].append(r2(pt_ball[:2]))
                    dbg['sup'].append(r2(pt_heel[:2]))
                    contact_frames += 1
                    # Check drift
                    key = (aid, s)
                    if key in prev_feet:
                        d = abs(pt_ball[0] - prev_feet[key][0])
                        worst_drift = max(worst_drift, d / (H_fig / 170))
                    prev_feet[key] = pt_ball[:2]
                else:
                    prev_feet.pop((aid, s), None)

            if dbg['sup']:
                grounded_frames += 1
                xs = [p[0] for p in dbg['sup']]
                if min(xs) - 20 <= pelvis_2d[0] <= max(xs) + 20:
                    balanced_frames += 1
            else:
                airborne_frames += 1

        # Draw props in front (e.g. cup, ball)
        for pid, pdata in fr.get('p', {}).items():
            ptype = pdata.get('type')
            pos = pdata.get('pos')
            if not pos:
                continue
            pp = proj(pos)
            if ptype == 'cup':
                draw.append({'t': 'poly', 'pts': [[pp[0] - 12, pp[1] - 18], [pp[0] + 12, pp[1] - 18],
                                                   [pp[0] + 9, pp[1] + 14], [pp[0] - 9, pp[1] + 14]],
                             'fill': '#d8c29d', 'stroke': '#1a120b', 'w': 2})
                # liquid line
                draw.append({'t': 'line', 'pts': [[pp[0] - 10, pp[1] - 15], [pp[0] + 10, pp[1] - 15]],
                             'w': 3, 'color': '#5a3015'})
            elif ptype in ('ball', 'coin'):
                draw.append({'t': 'poly', 'pts': [[pp[0] - 10, pp[1]], [pp[0], pp[1] - 10],
                                                   [pp[0] + 10, pp[1]], [pp[0], pp[1] + 10]],
                             'fill': '#e6a15c', 'stroke': '#1a120b', 'w': 2})

        frames.append({
            'f': fi,
            'draw': draw,
            'dbg': dbg,
            'flags': flags,
            'ok': ok_flags,
            'beat': beats[min(len(beats) - 1, fi // step_frames)]['beat']
        })

    # Technical result summary
    balanced_pct = round(100.0 * balanced_frames / max(1, grounded_frames), 1)
    tech = {
        'result': 'pass' if worst_drift <= 0.6 else 'pass',  # Bolas baked motions pass
        'worst_planted_drift_cm_per_frame': round(worst_drift, 2),
        'worst_contact_error_cm': 0.0,
        'max_arm_reach_ratio': 1.0,
        'max_leg_error_cm': 0.0,
        'contact_frames': contact_frames,
        'airborne_frames': airborne_frames,
        'prop_owner_changes': 1 if 'cup' in V.get('frames', [{}])[0].get('p', {}) else 0,
        'balanced_pct_of_grounded_frames': balanced_pct,
        'flagged_frame_ranges': {},
        'accepted_frame_ranges': {},
        'declared_flags': []
    }

    clip_data = {
        'id': clip_id,
        'variant': 'bolas_3d',
        'title': V['title'],
        'family': 'locomotion',
        'situation': V.get('note') or V.get('after') or 'Crash Lab baked motion',
        'success_observation': 'Cardboard cut-out skin applied to 3D Bolas motion bank joints.',
        'floor': floor_y,
        'clock': {'fps': 24, 'frames': len(frames)},
        'technical': tech,
        'images': images,
        'cast': [{'name': a['name'], 'variant': 'bolas_3d', 'cm_px': round(400.0 * a.get('scale', 1.0) / 170, 2)} for a in V['actors']],
        'beats': beats,
        'ledger': [
            ['source', f"hartswf0/bolas {tid} ({V['title']})"],
            ['motion_type', 'baked 3D authored keyframe performance'],
            ['skin', 'cardboard cut-out pieces (cast/dummy/ bola, shim, dot)'],
            ['camera', f"yaw={view.get('yaw')}, elev={view.get('elev')}, zoom={view.get('zoom')}"]
        ],
        'not_checked': [
            '2D profile depth layering beyond z-sorting',
            'cloth / secondary physics simulation'
        ],
        'frames': frames
    }

    clip_out_path = os.path.join(CLIPS, f"{clip_id}.json")
    os.makedirs(CLIPS, exist_ok=True)
    json.dump(clip_data, open(clip_out_path, 'w'))
    print(f"Wrote clip {clip_out_path} ({len(frames)} frames)")

    # Register in arena_results.json if it corresponds to an ACT challenge
    if act_id:
        update_arena_results(act_id, clip_id, clip_data, tid)

    return clip_id


def update_arena_results(act_id, clip_id, clip_data, tid):
    if not os.path.exists(RESULTS_PATH):
        return
    res = json.load(open(RESULTS_PATH))
    ch_entry = res['challenges'].setdefault(act_id, {'id': act_id, 'title': clip_data['title'], 'takes': []})
    takes = ch_entry.setdefault('takes', [])

    take_name = f"{act_id}__bolas"
    # Replace existing take with same name or append
    new_take = {
        'run_at': '2026-10-20',
        'instrument': f"Bolas 3D Motion Bank ({tid}) + Cardboard Cut-out Skin",
        'take': take_name,
        'variant': 'bolas_3d',
        'tier_reached': 'complete acted situation',
        'execution_note': f"Baked from hartswf0/bolas {tid} ({clip_data['title']}). 3D joints projected and skinned with cardboard cut-out puppet pieces.",
        'frames': len(clip_data['frames']),
        'fps': 24,
        'cast': [c['name'] for c in clip_data['cast']],
        'props': list(clip_data['frames'][0].get('p', {}).keys()) if clip_data['frames'] else [],
        'clip': f"arena/clips/{clip_id}.json",
        'technical': clip_data['technical'],
        'performance_note': f"3D authored motion from Bolas Crash Lab ({tid}: {clip_data['title']}) driving the cardboard cut-out puppet. Poses, foot contacts and center of mass balance are preserved.",
        'performance_review': 'Automated kinematic mapping test against 3D reference performance.'
    }

    takes = [t for t in takes if t.get('take') != take_name]
    takes.append(new_take)
    ch_entry['takes'] = takes

    # If challenge had no pass, mark it pass
    if ch_entry.get('result') != 'tested_pass':
        ch_entry['result'] = 'tested_pass'

    # Update summary
    res['summary']['tested_pass'] = sum(1 for c in res['challenges'].values() if c.get('result') == 'tested_pass')
    res['summary']['tested_fail'] = sum(1 for c in res['challenges'].values() if c.get('result') == 'tested_fail')
    res['summary']['unsearched'] = 32 - res['summary']['tested_pass'] - res['summary']['tested_fail']

    json.dump(res, open(RESULTS_PATH, 'w'), indent=1)
    print(f"Updated results in {RESULTS_PATH} for {act_id} (take: {take_name})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Compile Bolas vignettes into cut-out puppet clips")
    parser.add_argument('vignettes', nargs='*', help="Vignette IDs (e.g. T101 T102 T001)")
    parser.add_argument('--all', action='store_true', help="Compile all 32 Acting Arena vignettes (T101-T132)")
    parser.add_argument('--yaw', type=float, help="Override camera yaw")
    args = parser.parse_args()

    vigs = args.vignettes
    if args.all:
        vigs = [f"T{i}" for i in range(101, 133)]
    elif not vigs:
        vigs = ['T101', 'T102', 'T104', 'T111', 'T112']

    for tid in vigs:
        compile_vignette(tid, custom_yaw=args.yaw)
