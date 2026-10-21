# One rig, two skins: the whole arena

**Study it:** `study.html` (all 32 challenges, the man and the poet, at their
authored beats). Rebuild it with `python3 study.py && python3 study_page.py`.

`cardrig.py` is the rig. The Bolas motion bank, in 3D, decides each part's angle,
which view of it to show, and what goes in front of what (`p3d.depth_order`). The
drawn cards are the look. `skins.json` says which card each bone wears and where
its sockets are, by eye or from the poet's `assets.json`. Each card is:

- scaled so its socket-to-socket length is the 3D bone length, and held to the
  skin's width across the bone (`w`), so cards cut at different scales come out
  on one body: the man's thigh card is a fat oval that would otherwise be 36cm wide;
- turned to the bone on screen, and squashed along it (never across it) when the
  bone points at the camera;
- mirrored when the body faces screen-left.

Both characters run every challenge, and two-actor scenes cast them together:
the poet fights the man in ACT-016, then the cast swaps. Props come from the bank
at real size (boxes, ledges, doors, walls, chairs, balls, water). The stage is
warm paper, because the man's black cards vanished on near-black.

What the earlier code-drawn version (`p3d.py` alone) taught, and what was kept:
- **Kept:** hands use the Crash Lab's own geometry; the man still wears them,
  because his hand cards have no left, right or facing. The boots and the head
  bank follow the bank's foot joints and face fields.
- **Lost:** drawing the parts in code lost the cardboard, and it is not used for
  the look any more.

---

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

## What goes in front of what

The cards used to be drawn in one fixed order. Now every part of every actor is
sorted by its depth from the camera, farthest first, under a few rules that a
cut-out keeps whatever the angle (`depth_order` in `p3d.py`):

- thighs go under the shorts, the shorts under the vest, the vest under the head;
- the shin goes under its boot and its thigh;
- an upper arm goes under its forearm, and the forearm under its hand, unless the
  piece points away from the camera;
- **the shoulder rule:** an upper arm goes over the face only when its elbow is in
  front of the head's surface (15cm in front of its centre). Being nearer than
  the head's centre isn't enough; that is what put shoulders over chins.

Two actors sort together, so whoever is nearer is drawn in front as the camera
goes round (`out/ACT-016/turn_f40.png`). Every render measures, on the pixels,
how much of each drawn head ends up covered by what is painted after it, and
names what covers it. A head seen from behind counts as covered.

A bug that only showed with two actors: the queued drawing calls looked up each
actor's joints when they ran, not when they were queued, so actor A's body was
drawn at actor B's joints and A was left a floating head. Each call now binds its
own actor.

## In-betweens: the exposure sheet

The bank is Bolas's motion on ones: a new, smoothly eased pose 24 times a second.
That is how a 3D rig moves. *This Side Up* times its cut-out the stop-motion way
(TSU-00, the gust test): five keys and four breakdowns, held on twos, switching
to ones only for the two fastest moments, and never a dissolve or a warp passed
off as an in-between. `xsheet.py` does the same on the bank:

| mark | meaning |
| :-- | :-- |
| K key | an authored acting beat, plus the first and last frame |
| B breakdown | in each key interval, the frame that strays furthest from a straight key-to-key move (over 6cm): the arc |
| 1 ones | the take's fastest 8% of frames, and over 5cm a frame |
| 2 twos | every other frame; the next frame repeats the drawing |
| H hold | nothing moves more than 0.25cm: the drawing stays up |

Every drawing is a real pose from the bank. ACT-010 is now 104 drawings for 240
frames: 8 keys and 5 breakdowns, 18 frames on ones, the walk on twos, and holds
on the thinking beats. A flat 3.2cm-a-frame threshold had put the whole walk on
ones, so ones are now relative to each take.

## The whole set

    python3 shots/arena/puppet/batch.py         # all 32, four processes, about 10 minutes

For each challenge, `out/<ACT>/` gets:

- `take.mp4`: the take as exposed on the X-sheet;
- `keys.png`: the cold-read sheet;
- `xsheet.png`: the dope sheet;
- `take.json`: the X-sheet, the face checks, and the camera.

`gallery.html` shows them all (serve the repo and open it). Where the authored
camera hides the faces on the beats, the batch tries the camera at ±30°, ±60° and
±90° around the vertical and keeps the one that shows the most face.

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
