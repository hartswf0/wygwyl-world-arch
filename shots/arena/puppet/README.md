# The puppet, drawn from 3D: the man and the Bolas dummy as one thing

    python3 shots/arena/puppet/board.py ACT-010 --turn 80             # keys, turnaround, vs main sheet
    python3 shots/arena/puppet/board.py ACT-010 --yaw 30 --elev 8     # the same take, camera steered
    python3 -c "import board; board.closeups('ACT-010', 22)"          # feet and hands, four directions

## What was wrong with building him from cards

| | the Bolas dummy (Crash Lab) | the man as cut cards (before) |
| :-- | :-- | :-- |
| body | 3D joints and local frames; drawn fresh every frame | flat drawings, one per view, stretched joint to joint |
| camera | any; the drawing follows | only the side the card was drawn for |
| hands | `gloveDraw`: palm normal from the chest frame, thumb = fingers × palm, curl per finger | 4 cards with no side and no facing; turned by the forearm angle |
| feet | heel, ball, toe and ankle are joints, so the foot rolls | one rigid boot card, rotated |
| face | 16 numeric fields plus mouth and eyes, every frame | one head per view, sunglasses |
| proportions | thigh 44, shin 43, a 40cm head | cards at six different scales (`FAILINGS.md` §2) |
| props | real size, held by a hand | an 80×70px rectangle |

The dummy has everything except the look. The man has the look and almost
nothing else. Previous attempts tried to force the dummy's motion through the
man's cards. That way round loses every time: each card is a guess about one
view, and the motion asks for all of them.

## The other way round

`p3d.py` keeps everything the dummy has and paints it as the man:

- **Bones, joints, contacts and props** are the bank's, untouched. The hands
  still reach the box.
- **Volumes** come from the main sheet (`weave/cast/man/sheets/body_profile.jpg`)
  and are recorded in `canon.json`. The head share already agreed (sheet 27%,
  Bolas 28%), so the earlier 25–27cm head was the error, not Bolas.
- **Every part is a 3D volume cut as one flat card**: rim, ink edge, fill.
  Seams inside a part vanish and seams between parts show, as on a real cut-out.
  The piping and zip are drawn only on surfaces that face the camera.
- **Hands** are `gloveDraw` ported line for line. In the hanging pose with palms
  in, the palm faces the midline (0.79) and the thumb points forward (0.97) on
  both hands, by construction, from any camera.
- **Boots** are two blocks hinged at the ball, on the bank's heel, ball, toe and
  ankle. At toe-off (T110 f22) the rear boot stands on its forefoot with the
  heel raised.
- **The head** is the one drawn element, because the likeness lives there:
  - The *view* comes from where the head points relative to the camera: front
    under 28°, 3/4 up to 125°, otherwise the back; mirrored for the other side.
  - The *expression* comes from the bank's face fields, through
    `face_to_expression`.
  - It is sized from the 3D head, not from its foreshortened image.

## Steering

The camera is free: `Camera(view, yaw, elev, zoom, centre)`. `board.py --yaw --elev`
renders any take from anywhere, and the turnaround renders one frame from eight
directions. Steering is also a staging tool. On the vignette's own camera the
carried box covers his face at the strain beats (f146, f219, f239: "face hidden
behind a held prop"). At yaw +30, elevation 8, it doesn't. The check is measured
on the pixels of the drawn head, because the skeleton's nose sits behind the
drawn face.

## Open

- **No profile expression heads.** In profile he gets the 3/4 expression head.
  Generate a profile bank without sunglasses, or split brows, lids and mouth
  into replaceable pieces.
- **Boots** read as boots and roll. A drawn boot (a traced card mapped onto the
  two blocks) would read better close up.
- **Wrist bend and gaze.** The Crash Lab has `bend` and `gx`/`gy`; the bank
  exports gaze but not bend, and neither is drawn yet.
- **Shim** is still drawn as the man. The dummy cast (`arena/cast/dummy/`) or a
  second canon would separate them.
- **Not in the browser yet.** This is Python and PIL, at about 0.4s a frame. The
  same code would port to canvas in `arena.html`, the way the Crash Lab draws.
