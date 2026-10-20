# Cardboard Puppet Rig: Comprehensive Failure Mode Audit

This audit evaluates all 32 Acting Arena performance challenges against the cardboard cutout rigs, cataloging every anatomical, mechanical, and perspective breakdown.

## Summary Comparison: Female Poet vs. Male Poet

| Metric / Failure Mode | Female Poet Rig (`shots/weave/assets`) | Male Poet Rig (`shots/weave/cast/man`) | What Fails & Why |
| :--- | :--- | :--- | :--- |
| **Total Frames Audited** | 7160 | 7160 | 32 vignettes across locomotion, combat, jumps, objects |
| **Brad Disconnections** | **7160 frames** (100.0%) | **7154 frames** (99.9%) | 3D foreshortening shortens projected limb spans; rigid card pieces do not stretch, so pins pop apart in mid-air. |
| **Worst Elbow Gap** | **26.9 cm** | **30.3 cm** | Arm reaching in depth causes forearm to detach from upper arm. |
| **Worst Wrist Gap** | **29.3 cm** | **25.6 cm** | Hands float in mid-air with empty brass pin holes showing. |
| **View Angle Mismatches** | **4323 frames** | **0 frames** (multi-angle head bank) | Female Poet only has ONE right-profile head; Male Poet has 6 angle-swapping heads. |
| **Hand State Failures** | **1787 frames** | **0 frames** (grip, fist, point library) | Female Poet's far hand permanently clutches a rolled scroll; Male Poet swaps hands from sheet. |
| **Fused Ankle Failures** | **11820 frames** | **0 frames** (segmented boot rig) | Female Poet has rigid knee-to-sole cutouts that cannot articulate; Male Poet has flat & toe boots. |
| **Skirt / Crouch Collisions**| **798 frames** | **0 frames** (trousers + separate thighs) | Female Poet has a rigid A-line dress with no thighs; knees punch through skirt pattern when crouching. |

---

## The 5 Concrete Breakdown Modes

### 1. Brad Disarticulation (Popped Pins & Floating Hands)
- **The Defect**: Cardboard cutouts have fixed pixel lengths (e.g. upper arm = 177 px, forearm = 197 px). When a character reaches toward the camera or holds an object, 3D perspective foreshortens the distance between joints. Because cardboard pieces are rigid, the child piece's pivot is pulled away from the parent socket, leaving gaping holes and disconnected limbs floating in space.
- **Worst Case**: Reaching across chest in ACT-001 (Walk without spilling) and ACT-006 (Catch the ledge) where the wrist gap reaches **29.3 cm**.

### 2. View Angle Incompatibility (Broken-Neck Syndrome)
- **The Defect**: The Female Poet has only **one head drawing** (strict right-profile). When the 3D character turns toward the camera ($0^\circ$ yaw) or turns away ($180^\circ$), the head stays locked in profile while the torso faces front, creating an unnatural broken-neck doll appearance.
- **Resolution in Male Poet**: The Male Poet library has **6 heads** (`heads.jpg`) covering profile R, 3/4 R, front, 3/4 L, profile L, and back, which automatically swap based on camera yaw.

### 3. Fused Ankle & Ground Penetration
- **The Defect**: The Female Poet's legs are cut as a single rigid card from knee to shoe sole. During heel-strike, crouches, and running, the foot cannot rotate relative to the shin. The entire leg tilts as a wooden board, driving the shoe tip into the stage floor or balancing awkwardly on a sharp corner.
- **Resolution in Male Poet**: Sliced into separate thighs (`thigh.profile.png`), shins (`shin.profile.png`), and boots (`boot.flat.png`, `boot.toe.png`) pinned with knee and ankle brads.

### 4. Inappropriate Prop / Fixed Scroll Hand
- **The Defect**: The Female Poet's far hand was painted holding a rolled paper document for the DJ poem (`p07_turn_me_up`). In combat, sports, and athletic challenges (ACT-013 punch, ACT-014 kick, ACT-026 basketball fake), she is awkwardly running and punching while clutching the parchment scroll.
- **Resolution in Male Poet**: Swappable hand bank with fists (`hand.fist.png`), grips (`hand.grip.png`), and point gestures (`hand.point.png`).

### 5. Skirt vs. Crouch Collision
- **The Defect**: The Female Poet lacks separate thighs; her legs emerge directly from the hem of a rigid A-line gouache skirt. When she crouches (ACT-003) or jumps (ACT-005), the knees tuck up into the pelvic zone, causing the legs to detach from the skirt or overlap the floral pattern unnaturally.
