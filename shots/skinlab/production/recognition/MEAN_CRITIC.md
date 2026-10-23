# The mean critic: when is the puppet good enough?

The person's instruction: "hone and evolve till a mean critic satisfied". Recognition alone is not enough: a render can be matched to its painting and still be ugly. So there are two independent, fresh-context judges each round, and the run stops only when **both** pass.

## Judge 1: blind recognition (unchanged)
The same 30 poses, freshly shuffled, matched blind against all 108 paintings.
**Pass:**
- ≥ 25/30 top-1 overall, and ≥ 16/20 on test 2's fair subset;
- every high-confidence pick right;
- no pose recognised in the previous test lost.

## Judge 2: the mean critic (side by side, kill, don't grade)
The critic sees each of the 30 poses as **painting | puppet** at the same height and answers one question per pose:
*"Would I accept this puppet as this painting's pose, done in cut-out, in a finished film?"*

**Instant FAIL on sight** (BRIEF.md critic protocol v2):
- no seat in profile;
- a leg that breaks into cards at the knee;
- a wrong-way knee;
- a width step or seam at a joint;
- converging shins;
- a boot not ~1/7 of his height, or the two boots at different scales;
- a wrist past ~90°;
- a far limb over the face;
- a hand not reached by its arm;
- a head of the wrong size, roll or view;
- a blurred or holed card;
- a prop that floats instead of being held or sat on;
- a different face from the rest of the set;
- a key gesture of the painting missing: the hand's shape, the arm straight vs bent, the head's direction, the emblem.

There is no "narrowly met". Each FAIL names the one worst defect, so it can be routed.

**Pass:** ≥ 24/30 accepted, and no instant-fail category on more than 2 poses.

## Ceilings
A pose may be declared a ceiling only with:
- the reason (for example: the painting shows less than 60% of the figure; a rigid card can't fold; an outfit with no cards);
- the critic's agreement that the painting itself is the limit.

Ceilings are listed in the results and excluded from the thresholds' denominators. No more than 4 may be declared.

## Loop
1. Render.
2. Judge 1 and judge 2, both fresh, both blind to builder notes.
3. Route the failures to Builders A and B.
4. Gate on every pose ever recognised or accepted.
5. Repeat until both pass.
