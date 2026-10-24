# Joint critic v2 (style-anchored)

From round 07 onward this is the judge. The v1 rubric failed 3 of 4 unaltered-painting controls. v2 scored the controls at a mean of 5.5 and our joints at 3.8 on the same pack, so it separates the two.

## Step 1: learn the style
Open these unaltered poet paintings and zoom into their joints:
- shots/kits/cut/poet.05.main-poses/06-walk-to-the-gate-2.webp
- shots/kits/cut/poet.05.main-poses/ask-the-universe-2.webp
- shots/kits/cut/poet.06.main-poses/open-arms-02-at-shore.webp
- shots/kits/cut/poet.06.main-poses/arms-up-05-with-crowd.webp
- shots/kits/cut/poet.04.main-poses/04-1-walk-hollow.webp
- any 2 from shots/kits/cut/poet.13.main-poses

(06-walk-to-the-gate-threequarter-step.webp and ask-the-universe.webp are about 600-byte placeholders with no picture.)

The following belong to the style and are not defects:
- brass grommets with a dark hole on a dark pad;
- a 1–2 px tan/copper rim on every edge;
- rounded ends overlapping, with the rim visible inside the figure;
- piping that stays on one edge across a joint;
- spare grommets;
- mild softness.

## Step 2: judge
Open only round NN/critic/sXX.jpg, and nothing else in the joints tree. Mark a joint MUTILATED for anything the paintings don't have:
- a background gap;
- a notch, wedge or straight cut;
- a foreign tab or plate;
- a halo unlike the paintings' rim;
- a misregistered fastener or a white hole;
- a width step or costume mismatch;
- an impossible angle;
- pieces that don't read as one body.

Score each joint 0–10, where 10 is indistinguishable from the paintings. CLEAN needs a score of 5 or more and no glaring defect.

## Calibration
Each pack hides at least 4 controls: unaltered painting crops, cut only by the field edge. A critic run counts only if the controls score clearly above our joints.
