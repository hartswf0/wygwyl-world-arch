# Registration: ask the generation to be parsable

After <https://hartswf0.github.io/bolas/this-side-up/>, which solved this for a
physical puppet and shows why ours is harder.

## What This Side Up does

**TSU-01.** *"Parts claim pixels in order: the forearm first, then the upper arm,
then the head. Whatever is left is the body. Pivots go on the visible joint
connectors."*

**TSU-02.** *"The TV behind Boone prints its own frame number on every frame.
Any photograph of the set can be matched to the exact background frame."* Sixteen
bits, white start square, red end square, bottom right.

Both are the same idea: **do not infer what you can read.** Boone's pivots are
not estimated, they are the brass connectors, visible in the photograph. The
frame is not matched by eye, it is printed on the wall.

## Why it does not transfer as-is

Boone is a physical puppet photographed under a light. His brads are metal: they
have a specular highlight and they are not the colour of cardboard. Our figures
are drawn, and the generator drew the brads in the same palette as everything
else. Measured over twelve study sheets:

| hue band | share of saturated pixels |
| :-- | --: |
| red / orange | **99.94%** |
| yellow | 0.00% |
| green | 0.04% |
| cyan, blue, magenta | **0.00%** |

So "warm and saturated" selects 23,077px of skin, cardboard box and salmon
piping, and the brads are inside that, not distinguishable from it. On the
1024px renders brad detection finds three joints of twelve, and on
`slip_recover_f50` it finds none.

The skeleton fit that replaced it is no better: silhouette IoU 0.517, fifteen of
twenty-six joints landing inside the figure, and pieces where the torso is
smaller than an upper arm.

## What to ask the generation for

**1. A registration pass.** Every pose is generated twice from the same prompt
and seed: the finished figure, and the same figure with a flat disc of pure
magenta (`#FF00FF`) centred on every joint — shoulder, elbow, wrist, hip, knee,
ankle, ball, neck, crown. Magenta appears in **zero** pixels of the existing
cast, so the discs segment exactly, with no threshold to tune and no false
positive available. The joints are then read, not fitted.

**2. A frame code**, after TSU-02. Bottom right of every panel: a white start
square, bits for the act and the frame, a red end square. The panel then carries
its own identity and nothing has to be recovered by matching silhouettes — which
is where the current pipeline picks frame 64 for a panel captioned f95.

**3. Claim pixels in order, not by nearest bone.** Nearest-bone gives a
partition with 0.0% overlap, which sounds right and is not: it cannot represent
occlusion, so a forearm crossing the chest takes a bite out of the torso. The
TSU-01 order — hands, forearms, upper arms, head, then whatever is left is the
body — resolves overlap the way the drawing already does, by depth.

## What this costs

One extra generation per pose. 36 cards per character become 36 pairs, and the
pairs make the parsing deterministic instead of approximate. That is a better
trade than any amount of work on the estimator.
