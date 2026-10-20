"""Keyframe-Budget Lab: Quantifies how fast rigid cut-out brad gaps reopen
between generated keyframes under 3D camera projection, establishing the minimum
image generation budget per challenge.

    python3 shots/arena/bolas/keyframe_budget.py T102
    python3 shots/arena/bolas/keyframe_budget.py --all
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(HERE, 'bank')
BEATS_PATH = os.path.join(BANK, 'beats.json')
DEG = math.pi / 180

TOL_TIGHT = 0.6  # cm: tight Crash Lab tolerance
TOL_DISC  = 2.0  # cm: structural brad disconnect limit


def analyze_vignette(tid):
    vpath = os.path.join(BANK, f"{tid}.json")
    if not os.path.exists(vpath):
        print(f"Error: {vpath} not found")
        return None

    V = json.load(open(vpath))
    beats_all = json.load(open(BEATS_PATH)) if os.path.exists(BEATS_PATH) else {}
    beats = beats_all.get(tid, [])

    view = dict(V.get('view') or {})
    yaw, elev = view.get('yaw', -22) * DEG, view.get('elev', 10) * DEG
    cy, sy = math.cos(yaw), math.sin(yaw)
    ce, se = math.cos(elev), math.sin(elev)
    center = [view.get('x', 0), view.get('y', 90), view.get('z', 0)]
    scale = 1080 * 0.86 / 230 * view.get('zoom', 1.0)

    def proj(p):
        x, y, z = p[0] - center[0], p[1] - center[1], p[2] - center[2]
        x1, z1 = x * cy - z * sy, x * sy + z * cy
        y2, z2 = y * ce - z1 * se, y * se + z1 * ce
        return np.array([1920 / 2 + x1 * scale, 1080 * 0.52 - y2 * scale, z2])

    N = V['len']
    actors = V.get('actors', [])
    if not actors:
        return None

    # Pick actor with highest motion displacement
    hero = actors[0]['id']
    max_motion = -1
    for a in actors:
        aid = a['id']
        pts = [fr['a'][aid]['j'][0] for fr in V['frames'] if aid in fr.get('a', {}) and fr['a'][aid].get('j') and fr['a'][aid]['j'][0]]
        if len(pts) > 1:
            tot = float(np.sum(np.linalg.norm(np.diff(np.array(pts), axis=0), axis=1)))
            if tot > max_motion:
                max_motion = tot
                hero = aid

    hero_actor = next(a for a in actors if a['id'] == hero)
    hero_scale = hero_actor.get('scale', 1.0)
    H_fig = 185.0 * hero_scale * scale
    cm_px = H_fig / 170.0

    # Segments to track: (jointA_idx, jointB_idx, name)
    BONES = [
        (16, 18, 'uarm_L'), (18, 20, 'farm_L'),
        (17, 19, 'uarm_R'), (19, 21, 'farm_R'),
        (1, 3, 'thigh_L'),  (3, 5, 'shin_L'),
        (2, 4, 'thigh_R'),  (4, 6, 'shin_R'),
    ]

    # Compute projected bone lengths per frame
    frame_bones = []
    for fi, fr in enumerate(V['frames']):
        arec = fr.get('a', {}).get(hero)
        if not arec or not arec.get('j') or arec['j'][0] is None:
            frame_bones.append({})
            continue
        jj_2d = [proj(p) for p in arec['j']]
        lens = {}
        for ja, jb, bname in BONES:
            d = np.linalg.norm(jj_2d[jb][:2] - jj_2d[ja][:2]) / cm_px
            lens[bname] = d
        frame_bones.append(lens)

    # Keyframe placement: greedily step forward until max gap > TOL_TIGHT
    budget_tight = []
    cur_f = 0
    budget_tight.append(cur_f)

    while cur_f < N - 1:
        ref_lens = frame_bones[cur_f]
        next_f = cur_f + 1
        while next_f < N:
            target_lens = frame_bones[next_f]
            if not target_lens:
                break
            max_gap = max(abs(target_lens[b] - ref_lens.get(b, target_lens[b])) for b in target_lens)
            if max_gap > TOL_TIGHT:
                break
            next_f += 1
        # Place keyframe at break or next_f
        key_placed = max(cur_f + 1, next_f - 1) if next_f < N else N - 1
        budget_tight.append(key_placed)
        cur_f = key_placed

    # Keyframe placement for structural limit (TOL_DISC = 2.0 cm)
    budget_disc = []
    cur_f = 0
    budget_disc.append(cur_f)
    while cur_f < N - 1:
        ref_lens = frame_bones[cur_f]
        next_f = cur_f + 1
        while next_f < N:
            target_lens = frame_bones[next_f]
            if not target_lens:
                break
            max_gap = max(abs(target_lens[b] - ref_lens.get(b, target_lens[b])) for b in target_lens)
            if max_gap > TOL_DISC:
                break
            next_f += 1
        key_placed = max(cur_f + 1, next_f - 1) if next_f < N else N - 1
        budget_disc.append(key_placed)
        cur_f = key_placed

    # Match against Bolas named beats
    beat_frames = [b['f'] for b in beats if not any(x in b['beat'] for x in ('passing', 'heel strike'))]
    unique_beats = sorted(set(beat_frames))

    return {
        'tid': tid,
        'title': V['title'],
        'frames': N,
        'camera': {'yaw': view.get('yaw', -22), 'elev': view.get('elev', 10), 'zoom': view.get('zoom', 1.0)},
        'named_beats_count': len(beats),
        'acting_beats_count': len(unique_beats),
        'tight_budget_0_6cm': len(budget_tight),
        'structural_budget_2_0cm': len(budget_disc),
        'tight_keyframe_indices': budget_tight,
        'structural_keyframe_indices': budget_disc,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Keyframe Budget Lab")
    parser.add_argument('vignette', nargs='?', default='T102', help="Vignette ID (e.g. T102)")
    parser.add_argument('--all', action='store_true', help="Run budget lab across all 32 challenges")
    args = parser.parse_args()

    if args.all:
        print(f"{'Vignette':<8} {'Title':<28} {'Frames':<7} {'Beats':<6} {'Budget ≤0.6cm':<14} {'Budget ≤2.0cm':<14}")
        print("-" * 80)
        tot_tight, tot_disc, tot_frames = 0, 0, 0
        for i in range(101, 133):
            tid = f"T{i}"
            res = analyze_vignette(tid)
            if not res:
                continue
            tot_tight += res['tight_budget_0_6cm']
            tot_disc += res['structural_budget_2_0cm']
            tot_frames += res['frames']
            print(f"{res['tid']:<8} {res['title'][:26]:<28} {res['frames']:<7} {res['acting_beats_count']:<6} {res['tight_budget_0_6cm']:<14} {res['structural_budget_2_0cm']:<14}")
        print("-" * 80)
        print(f"TOTALS: {tot_frames} frames | {tot_tight} images (≤0.6cm tolerance) | {tot_disc} images (≤2.0cm disconnect)")
    else:
        res = analyze_vignette(args.vignette)
        if res:
            print(f"=== KEYFRAME BUDGET LAB: {res['tid']} ({res['title']}) ===")
            print(f"Total Frames: {res['frames']} | Camera: yaw={res['camera']['yaw']}°, elev={res['camera']['elev']}°, zoom={res['camera']['zoom']}")
            print(f"Named Dramaturgical Beats: {res['named_beats_count']} total ({res['acting_beats_count']} acting beats)")
            print(f"\nImage Generation Budget:")
            print(f"  - Strict 0.6 cm tolerance: {res['tight_budget_0_6cm']} keyframes")
            print(f"    Keyframe list: {res['tight_keyframe_indices']}")
            print(f"  - Structural 2.0 cm limit: {res['structural_budget_2_0cm']} keyframes")
            print(f"    Keyframe list: {res['structural_keyframe_indices']}")
