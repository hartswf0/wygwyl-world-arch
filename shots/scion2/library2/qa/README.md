# library2 QA: part gates and pairwise seam tests

Every regularized part has to pass this stage before an assembler may use it. The stage has two layers:
1. Part gates (`gates.py`) test each part on its own. A part that FAILs is excluded from pairing.
2. Pairwise joint tests (`pairs.py` + `seam.py`) attach each part to the parts beside it, sweep the joint angle,
   and score the seam. The result is a compatibility matrix in `pairs.json`. Assemblers use only CLEAN pairs, and
   only inside their clean range.

## seam.py: the stable interface (the joint lab's fitness)

```python
from seam import score, facing_compatible, TOL
r = score(render_rgba, maskA, maskB, pivot, axisA, axisB, over='A'|'B',
          featuresA=[bool masks], featuresB=[bool masks],
          facingA=(view, facing), facingB=(view, facing), joint='neck'|'wrist'|'ankle'|'elbow'|'knee'|'generic',
          tol={...overrides...})
```

**Inputs.**
- All arrays share one pixel frame, with y pointing down.
- `maskA` and `maskB` are each part's full silhouette as placed, whatever is drawn on top.
- `pivot` is the joint point.
- `axisA` is a unit vector from the joint into A, along A's bone. `axisB` is the same for B.
- `over` names the part drawn on top.
- `features*` are painted features that must stay visible, for example a face oval or an off-joint brad. Only the
  under part's features are tested.

**Output keys.**
- `seam_w`: the unit length, equal to the smaller part's cross-section at the pivot. Every fraction below is
  relative to `seam_w²`.
- `gap_px`, `gap_frac`: background enclosed between the parts. It is computed as the morphological closing of the
  union minus the union, inside a disk of 0.9·seam_w. Holes painted inside one part (eyelet holes, the hollow
  chest) do not count.
- `width_A`, `width_B`, `width_ratio`: each part's own cross-section at the joint, measured across its bone at
  0.1·seam_w inside it. `width_ratio` = B/A, and a step is a ratio outside the joint's tolerance. For the neck, the
  torso's neck end may be 0.9–2.4× the head's neck (a collar wider than the neck); a neck wider than the collar
  fails.
- `exposed_A_frac`, `exposed_B_frac`: pixels of a part that lie beyond the joint, on the other part's side (an
  overlap tab or cut end), and outside the other part's silhouette.
  - When the under part's tab shows, the result is MUTILATED.
  - The over part's beyond-joint pixels, such as a collar rim or cuff, only warn, and only when they are large.
- `covered`: the largest hidden fraction of any under-part feature.
- `colour_dE`: CIE76 ΔE between the median colours either side of the visible seam contour. It only warns at
  joints where the material should continue (elbow and knee).
- `facing_ok`: False when the two (view, facing) tags cannot meet. That happens when the view families differ
  beyond their neighbours (front with three-quarter, three-quarter with side, back with three-quarter-back), or
  when the screen-left/right facings disagree.
- `verdict`: CLEAN, WARN or MUTILATED.
- `why`: the failing terms, the MUTILATED ones listed first.
- `spot`: where to circle the failure on a sheet.

`TOL[joint]` holds the thresholds:
- `gap_warn`, `gap_fail`;
- `exp_warn`, `exp_fail`;
- `cov_warn`, `cov_fail`;
- `ratio` and `ratio_fail`, each a (lo, hi) pair on width_B/width_A;
- `dE_warn`.

The joint lab can pass `tol=` to tune them. Changing a default here changes every verdict.

## gates.py: per-part tests
Each test returns `{result: pass|warn|fail, evidence, why}`. The overall `verdict` is the worst of the four.
- **cutoff**
  - The alpha touches the card border on a side other than the connection end.
  - Long straight outline segments (scissor cuts) run away from the connection end.
  - The part is short against the canonical size, e.g. crown→chin under 0.82× of height/8.
- **contamination**
  - Heads: the outline widens below the chin (shoulders or collar attached); the chin→pivot distance is over 14 cm
    (the pivot sits mid-neck); dark cloth sits in the neck zone.
  - Hands and feet: wrist, sleeve or shin material is present. These tests are added with their part types.
- **connection**
  - The pivot is off the centre-line of the cross-section.
  - No brad was found.
  - There is no overlap tab beyond the pivot.
  - The width at the pivot is recorded, so the neighbour can be matched.
- **view**: the view tag is checked against the pixel test (for heads, the skin/hair centroid offset and the dark
  face box).

## pairs.py: the sweep

```
python3 shots/scion2/library2/qa/pairs.py poet head   # neck: head on torso
python3 shots/scion2/library2/qa/pairs.py poet hand   # wrist: hand on forearm
python3 shots/scion2/library2/qa/pairs.py poet foot   # ankle: foot on shin
```

1. Neighbours: up to 3 per part.
   - They must share the character, a compatible view family and a compatible facing.
   - They rank higher for the same costume, the same cut sheet, a brass-found joint and a neutral pose.
2. Attaching: both parts are canonical, so the neutral pose is the child pivot on the parent's joint keypoint with
   zero rotation.
3. The sweep runs from −60° to +90° in steps of 15°. A positive angle turns the child counter-clockwise on screen.
4. Z-order follows the Skin Lab stack: torso over head, hand over forearm, shin over foot.
5. Outputs:
   - `results/<char>_<part>.json`: the gates, plus every pair-angle score.
   - `pairs.json`: for each child → neighbour pair, `clean_range` and `usable_range` and the failures per angle.
     `clean_range` is the contiguous run of CLEAN steps around 0. `usable_range` is the same with CLEAN or WARN
     steps.
   - `sheets/<char>_<part>_qa_NN.jpg`: one row per part.
     - The canonical part, then 1–3 neighbour strips at −60, −30, −15, 0, +15, +45 and +90.
     - Each tile is outlined green (CLEAN), amber (WARN) or red (MUTILATED), and the failing seam is circled.
     - The four gate results are printed under the row.
   - `sheets/<char>_<part>_qa_worst.jpg`: the worst pair-angles, with the summary counts.
