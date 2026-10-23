# Blind recognition test 2: renderPose + harvested cards + framing + set pieces

**Setup.**
- The same 30 poses as test 1, under a new shuffle and new names.
- A fresh critic matched them blind against the same 108 paintings.
- Renders now go through Builder B's renderPose, which applies the per-view mechanics. Builder A's harvested foreshortened cards were used leave-one-family-out.
- Whole figures are in frame. 10 of the 30 renders also carry a flat set-piece silhouette cut from their own painting.

**Result** (top-1 = the critic's first pick is the right painting):

| Subset | Test 1 top-1 | Test 2 top-1 | Test 2 top-2 |
|---|---|---|---|
| All 30 | 7 | **10** | 11 |
| The 20 poses with no set piece (the fair comparison) | 6 | **7** | 8 |
| The 10 with a set piece | 1 | **3** | 3 |

The set pieces come from the very painting being matched, so the critic could partly match on them (it flagged 2 as prop-led and 3 as partly prop-led). Treat that row as leak-assisted.

**Honest read.** On the fair subset the gain is one pose, which is within noise. The renders look better pose by pose, but recognisability has barely moved yet.

**New on the recognised list:** lying (q3-restless-lying-2), phone-palm (high confidence for profile hand-to-ear), gentle-slow-bent-knee-dance, push (12/03), falter-at-shoulder-contact-2, empty-cuffs, rise-flex-reflect, welcome-new-day. Daisy and coil-to-mount were also matched, but with their set pieces.

**Failure causes now (the critic's words), each with its owner:**
1. **Seated and crouched poses collapse in profile:** the seat is a detached black disc, and thighs and shins pile up as cards (c02 cafe-sit, c04, c05 heart-seated, c24, c28). → renderPose seat and sitting mechanics (B).
2. **Knee seams:** gaps and width steps between thigh and shin, and shins detached from boots (c03, c06, c18, c19, c20, c21). These come from mixing harvested and contract cards on one leg. → take whole limb chains from one source (A), and match widths at the joint (B).
3. **Far limbs over the face or torso, and rotated torso cards that shear** (c02, c08, c13, c25). → layering and torso (B).
4. **Head direction doesn't match the body:** a profile head on a frontal torso (c01, c22, c29), and over-stretched necks (c23). → head view and neck (B).
5. **Neutral standing poses are near-identical across paintings** (#15/26/28/52/81). This is a ceiling no puppet can beat without the props. Abstract grey blobs confused more than they helped. → kit prop cards instead of painting blobs (A).
