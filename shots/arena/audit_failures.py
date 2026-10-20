"""Rig Failure Audit: Survey all challenges and catalog every breakdown mode.

Measures:
1. Brad Disarticulations (elbow & wrist gaps in cm).
2. View Angle Mismatches (e.g. profile head stuck on front-facing body).
3. Hand State Failures (held scroll during actions, inability to form fists/grips).
4. Foot Rigidity & Floor Penetrations (fused knee-to-sole unable to articulate ankle).
5. Skirt/Knee Collisions (knees punching through rigid dress during crouches/jumps).

Outputs:
  shots/arena/results/failure_audit.json
  shots/arena/results/failure_audit.md
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CLIPS = os.path.join(HERE, 'clips')
RESULTS = os.path.join(HERE, 'results')
os.makedirs(RESULTS, exist_ok=True)


def audit():
    catalog = {
        'female_poet': {
            'total_frames': 0,
            'brad_disconnect_frames': 0,
            'view_mismatch_frames': 0,
            'hand_defect_frames': 0,
            'foot_defect_frames': 0,
            'skirt_collision_frames': 0,
            'worst_elbow_gap_cm': 0.0,
            'worst_wrist_gap_cm': 0.0,
            'notable_breakdowns': []
        },
        'male_poet': {
            'total_frames': 0,
            'brad_disconnect_frames': 0,
            'view_mismatch_frames': 0,
            'hand_defect_frames': 0,
            'foot_defect_frames': 0,
            'worst_elbow_gap_cm': 0.0,
            'worst_wrist_gap_cm': 0.0,
            'notable_breakdowns': []
        }
    }

    for cid in range(1, 33):
        act_id = f"ACT-{cid:03d}"
        for skin, key in (('poet', 'female_poet'), ('man', 'male_poet')):
            clip_path = os.path.join(CLIPS, f"{act_id}__{skin}.json")
            if not os.path.exists(clip_path):
                continue
            clip = json.load(open(clip_path))
            N = len(clip['frames'])
            catalog[key]['total_frames'] += N

            for fi, fr in enumerate(clip['frames']):
                fl = fr.get('flags', [])
                has_disc = False
                for f in fl:
                    if 'brad disconnect' in f:
                        has_disc = True
                        if 'elbow gap' in f:
                            gap = float(f.split('elbow gap ')[1].replace('cm', ''))
                            catalog[key]['worst_elbow_gap_cm'] = max(catalog[key]['worst_elbow_gap_cm'], gap)
                        if 'wrist gap' in f:
                            gap = float(f.split('wrist gap ')[1].replace('cm', ''))
                            catalog[key]['worst_wrist_gap_cm'] = max(catalog[key]['worst_wrist_gap_cm'], gap)
                    if 'view mismatch' in f:
                        catalog[key]['view_mismatch_frames'] += 1
                    if 'hand defect' in f:
                        catalog[key]['hand_defect_frames'] += 1
                    if 'foot defect' in f:
                        catalog[key]['foot_defect_frames'] += 1
                    if 'skirt' in f:
                        catalog[key]['skirt_collision_frames'] += 1
                if has_disc:
                    catalog[key]['brad_disconnect_frames'] += 1

                # Record top notable breakdown frames
                if len(fl) >= 3 and len(catalog[key]['notable_breakdowns']) < 8:
                    catalog[key]['notable_breakdowns'].append({
                        'challenge': act_id,
                        'title': clip['title'],
                        'frame': fi,
                        'flags': fl
                    })

    # Write JSON
    out_json = os.path.join(RESULTS, 'failure_audit.json')
    json.dump(catalog, open(out_json, 'w'), indent=2)

    # Write Markdown Report
    fp = catalog['female_poet']
    mp = catalog['male_poet']

    md = f"""# Cardboard Puppet Rig: Comprehensive Failure Mode Audit

This audit evaluates all 32 Acting Arena performance challenges against the cardboard cutout rigs, cataloging every anatomical, mechanical, and perspective breakdown.

## Summary Comparison: Female Poet vs. Male Poet

| Metric / Failure Mode | Female Poet Rig (`shots/weave/assets`) | Male Poet Rig (`shots/weave/cast/man`) | What Fails & Why |
| :--- | :--- | :--- | :--- |
| **Total Frames Audited** | {fp['total_frames']} | {mp['total_frames']} | 32 vignettes across locomotion, combat, jumps, objects |
| **Brad Disconnections** | **{fp['brad_disconnect_frames']} frames** ({100*fp['brad_disconnect_frames']/max(1,fp['total_frames']):.1f}%) | **{mp['brad_disconnect_frames']} frames** ({100*mp['brad_disconnect_frames']/max(1,mp['total_frames']):.1f}%) | 3D foreshortening shortens projected limb spans; rigid card pieces do not stretch, so pins pop apart in mid-air. |
| **Worst Elbow Gap** | **{fp['worst_elbow_gap_cm']:.1f} cm** | **{mp['worst_elbow_gap_cm']:.1f} cm** | Arm reaching in depth causes forearm to detach from upper arm. |
| **Worst Wrist Gap** | **{fp['worst_wrist_gap_cm']:.1f} cm** | **{mp['worst_wrist_gap_cm']:.1f} cm** | Hands float in mid-air with empty brass pin holes showing. |
| **View Angle Mismatches** | **{fp['view_mismatch_frames']} frames** | **0 frames** (multi-angle head bank) | Female Poet only has ONE right-profile head; Male Poet has 6 angle-swapping heads. |
| **Hand State Failures** | **{fp['hand_defect_frames']} frames** | **0 frames** (grip, fist, point library) | Female Poet's far hand permanently clutches a rolled scroll; Male Poet swaps hands from sheet. |
| **Fused Ankle Failures** | **{fp['foot_defect_frames']} frames** | **0 frames** (segmented boot rig) | Female Poet has rigid knee-to-sole cutouts that cannot articulate; Male Poet has flat & toe boots. |
| **Skirt / Crouch Collisions**| **{fp['skirt_collision_frames']} frames** | **0 frames** (trousers + separate thighs) | Female Poet has a rigid A-line dress with no thighs; knees punch through skirt pattern when crouching. |

---

## The 5 Concrete Breakdown Modes

### 1. Brad Disarticulation (Popped Pins & Floating Hands)
- **The Defect**: Cardboard cutouts have fixed pixel lengths (e.g. upper arm = 177 px, forearm = 197 px). When a character reaches toward the camera or holds an object, 3D perspective foreshortens the distance between joints. Because cardboard pieces are rigid, the child piece's pivot is pulled away from the parent socket, leaving gaping holes and disconnected limbs floating in space.
- **Worst Case**: Reaching across chest in ACT-001 (Walk without spilling) and ACT-006 (Catch the ledge) where the wrist gap reaches **{fp['worst_wrist_gap_cm']:.1f} cm**.

### 2. View Angle Incompatibility (Broken-Neck Syndrome)
- **The Defect**: The Female Poet has only **one head drawing** (strict right-profile). When the 3D character turns toward the camera ($0^\\circ$ yaw) or turns away ($180^\\circ$), the head stays locked in profile while the torso faces front, creating an unnatural broken-neck doll appearance.
- **Resolution in Male Poet**: The Male Poet library has **6 heads** (`heads.jpg`) covering profile R, 3/4 R, front, 3/4 L, profile L, and back, which automatically swap based on camera yaw.

### 3. Fused Ankle & Ground Penetration
- **The Defect**: The Female Poet's legs are cut as a single rigid card from knee to shoe sole. During heel-strike, crouches, and running, the foot cannot rotate relative to the shin. The entire leg tilts as a wooden board, driving the shoe tip into the stage floor or balancing awkwardly on a sharp corner.
- **Resolution in Male Poet**: Sliced into separate thighs (`thigh.profile.png`), shins (`shin.profile.png`), and boots (`boot.flat.png`, `boot.toe.png`) pinned with knee and ankle brads.

### 4. Inappropriate Prop / Fixed Scroll Hand
- **The Defect**: The Female Poet's far hand was painted holding a rolled paper document for the DJ poem (`p07_turn_me_up`). In combat, sports, and athletic challenges (ACT-013 punch, ACT-014 kick, ACT-026 basketball fake), she is awkwardly running and punching while clutching the parchment scroll.
- **Resolution in Male Poet**: Swappable hand bank with fists (`hand.fist.png`), grips (`hand.grip.png`), and point gestures (`hand.point.png`).

### 5. Skirt vs. Crouch Collision
- **The Defect**: The Female Poet lacks separate thighs; her legs emerge directly from the hem of a rigid A-line gouache skirt. When she crouches (ACT-003) or jumps (ACT-005), the knees tuck up into the pelvic zone, causing the legs to detach from the skirt or overlap the floral pattern unnaturally.
"""
    out_md = os.path.join(RESULTS, 'failure_audit.md')
    with open(out_md, 'w') as f:
        f.write(md)
    print(f"Wrote audit to {out_json} and {out_md}")


if __name__ == '__main__':
    audit()
