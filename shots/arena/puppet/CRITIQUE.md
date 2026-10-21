# Brutal critique of the card-rig takes (2026-10-21)

Four independent critics watched all 64 rendered takes (`study/*.mp4`), 8
challenges each. They had no knowledge of the code, worked from 32-tile contact
sheets (`critique/sheets/`), and pulled close-up frames. I checked the
surprising claims against fresh renders. Below, every pathology names where it
shows, its cause in our code, and the proposed fix.

**Score:** of 32 challenges, **0 read fully, 17 read partly, 15 do not read.**
The best is ACT-007 (slip and recover); ACT-015 is nearly there.

---

## The pathologies, ranked by how badly they break the illusion

### 1. Two actors fuse into one creature
Seen in ACT-002, 018, 022, 023, 026, 030, 031 and 032: every two-hander that
touches.
- The sprinter runs *through* the partner (002).
- An afro profile head sits on the man's back-view vest (023, frame 96).
- His boots stick out from under her skirt (032).
- The door-holder looks headless because the poet's card covers his head (030).
  This was checked against a fresh render: the head is there but buried.

**Cause:** depth is sorted per part across both actors, so their cards
interleave. Bolas's dummies also overlap in space at contacts.

**Fix:** layer each actor as a whole, nearer actor over farther. Interleave only
at real contacts, such as hands in a handshake or arms in a catch, and name
those per beat.

### 2. Each character's height changes from take to take
Whoever is cast as Shim is 1.06×, as Dot 0.72×. In ACT-030 Shim is a giant; in
ACT-032 the man is child-sized. In ACT-029 the man comes up to her shoulder in
one casting and is taller in the other.

**Cause:** we inherit the Bolas actor's scale.

**Fix:** each skin has one height, and the motion is retargeted to it: scale the
actor's joints about its floor point. It's the same person in every shot.

### 3. The man's shorts card (as you said)
Seen in every take with the man.
- It's the **front-view** two-leg shorts card hung below a profile vest.
- Standing side-on, its two lobes sit beside the real thighs: four thighs, a
  padded nappy.
- When he bends or kneels, it swings out behind like a tail or apron (010 frame
  80, 025 frame 56, 003 frame 100).
- Its rivets add stray joint dots halfway down the thigh.
- In front view it shrinks to a brief with bare thigh cards below (004).

**Cause:** the skin uses `pelvis.front.png` in every view, plus separate thigh
cards.

**Fix:** follow the main sheet's own construction. The shorts *are* the thighs.
Cut the shorts card into a left and a right shorts leg, each hinged at the hip
and ending at the knee brad, and hang the shin and boot from its hem. Use no
separate thigh card and no pelvis card in side views. In front view, show only
the waistband strip, under the vest hem.

### 4. Heads change view on their own and come from different drawings
Seen on every sheet.
- A front face on a profile body (001, 003, 007, 014).
- The back-of-head card flickers for single tiles (001 tiles 17→23, 003 tile 19).
- The **front-bank faces are a paler, flatter drawing** than the 3/4 faces, so
  every turn to camera swaps in a washed-out "ghost" man. Checked: it is a
  different drawing, not transparency.
- The back-of-head card fades to nothing at the neck (027).
- The poet has one head: profile, eyes closed. It sits on a front bodice even
  when her body turns away.

**Cause:**
- The head view comes from the head's own yaw, independent of the torso card.
- The two banks came from different generations.
- The poet has no other head.

**Fix:**
- Choose the head view from the torso view, at most one step away, with a hold
  so it can't flicker.
- Generate one head bank in one style: front, 3/4, profile and back, each in 8
  expressions, with no sunglasses.
- Generate a poet bank with open eyes.
- Re-cut the back-of-head card with a hard edge.

### 5. Front cards on side bodies, and the front vest on his back
- The poet's torso and skirt are always front-view rectangles, even with her
  back to camera (025, 018).
- The man's back view shows the zip and piping (011, 016). `torso.back.png` is
  the front drawing; `FAILINGS.md` already measured that.

**Fix:**
- Generate the missing views: the poet's profile bodice and skirt, and the man's
  real back vest.
- Until then, pick each take's camera so the poet stays in profile. A profile
  puppet is a legitimate cut-out convention.

### 6. Hands: a third hand, face-sized mitts, never a grip
- The far hand is drawn *on top of* the skirt or shorts like an appliqué: 012 on
  every tile, 015, 016, 026, 028, 031.
- The man's code hands are flat palm-forward mitts the size of his face, in a
  different drawing style from his cards. They show palms even from behind.
- No hand ever closes on a cup, ledge, racket, box, partner or table.

**Fix:**
- A hard rule: far-side limbs stay behind the torso and pelvis unless the wrist
  is more than 10cm in front of the body.
- Card hands cut from `hands.jpg` and `hands_2.jpg` (which have real left and
  right), at about 70% of the current size.
- A grip shape whenever the bank says a hand holds something.

### 7. Props: floating, unheld, opaque, and they eat bodies
- The cup is a white cube beside the hip (001, 032).
- The racket is a vertical dowel floating by the hand (028).
- The table is a legless crate nobody touches (029).
- The box sits flat on one palm (022).
- The ball freezes mid-air (028); he ends standing on the ball (027).
- Water is an opaque blue box: he kneels *in front of* it in the air (005), and
  the man loses his head behind it.
- Walls and boxes cover the whole body but leave the feet showing (021, 023, 024,
  030).

**Cause:**
- A prop is one flat item with one depth.
- Held props aren't attached to a hand.
- Default prop sizes are invented.

**Fix:**
- Sort props face by face, together with body parts.
- Pin a held prop to the hand socket and give the hand a grip.
- Draw water as a translucent surface plane, with everything below the
  waterline tinted and cut.
- Use prop cards from `props.jpg` and `set_props.jpg` (door, table, cup,
  racket, balls) instead of cuboids.

### 8. Bodies collapse into a heap on the floor
In ACT-008 tiles 8–11 the fall becomes a knot of cards, with the head upside down
by the boots.

**Fix:** lying and kneeling poses use replacement whole-body cards, the
cut-out convention. Some already exist: `man.crouch.*` and
`poet.floor_recovery.*`.

### 9. Expressions contradict the beat
He grins while hauling himself up (006 frame 150), grins for pain (008), and looks
shocked during a calm carry (001). The poet's eyes are closed on every beat that
needs a look.

**Cause:** `face_to_expression` turns Bolas's `mouth: teeth` into a grin when
effort is low.

**Fix:** read effort and the beat text together: teeth with effort is a strain,
never a grin. Pain beats map to pain. The poet needs her own bank (see 4).

### 10. Dead holds
About half of many clips is a frozen pose (014, 015, 016, 025, 027, 028, 031,
032).

**Fix:** end each take 12–18 frames after its last authored beat, and keep
holds alive with a 2-frame breath on twos.

### 11. The Tron look
Every card has a pale seam and white bolts, so the man reads as glowing outlines
on black rather than painted cardboard. At 344–416px wide, faces and piping turn
to mush.

**Fix:** defringe every card (as the heads already are), use a kraft-coloured
cut edge instead of grey-white, and render the study at 720p.

### 12. The poet's skirt
- It's a rigid board that tilts like a sail in the kick and lies flat like a rug
  in the squat.
- A blue thigh card pokes out under the hem (027, 014, 003).

**Fix:**
- Thighs under a skirt are never drawn; only the shin shows below the hem.
- The skirt hangs from the hip, turns with the pelvis, and flares at most 10°.

---

## Does each situation read? (the critics' verdicts)

| | reads | | reads |
| :-- | :-- | :-- | :-- |
| 001 carry a full cup | partly: a cube, not a cup | 017 dance, missed beat | no: back to camera |
| 002 sprint, recognise | no: runs through the partner | 018 spin with partner | partly: bodies merge |
| 003 crouch under trouble | partly | 019 celebration interrupted | partly: frozen arms |
| 004 spin to the target | no: heads flip, no turn | 020 too big for the stage | no: tiny, hidden |
| 005 jump into water | no: opaque water, no head | 021 cower then help | no: floats on the box |
| 006 catch the ledge | partly: the hang is hidden | 022 pretend the box is light | partly: one-palm box |
| 007 slip and recover | **best**: partly | 023 false confident entrance | no: fused at the door |
| 008 stand after a fall | partly: heap, grin for pain | 024 wait, not inert | partly: wall eats him |
| 009 door the wrong way | no: the door never moves | 025 grounder | partly |
| 010 heavy box | partly: tug reads, no grip | 026 basketball fake | no: fused |
| 011 chair moved away | no: the chair never moves | 027 soccer whiff | partly: ends on the ball |
| 012 hand over reluctantly | partly: no hold or release | 028 tennis | no: racket floats |
| 013 punch that misses | no: it hits the face | 029 table through a door | no: crate, unheld |
| 014 kick, keep balance | partly: never reaches | 030 holding the door | no: buried, giant |
| 015 block into retreat | partly/yes | 031 catch a friend | partly: no hands |
| 016 fight to apology | partly: no recognition | 032 chain reaction | no: fused, T-pose |

## Order of work (most leverage first)

1. **Actors layered as wholes, and one height per character** (pathologies 1
   and 2). This fixes the chimeras and the headless door-holder in eight takes.
2. **Shorts become the thighs** (3). This fixes every take with the man.
3. **Far limbs behind the body, card hands, grips on held props** (6, part of 7).
4. **Head view tied to the torso view** (4, the part that needs no new art).
5. **Props sorted face by face, translucent water, prop cards** (7).
6. **Defringe, kraft edges, 720p, trimmed holds** (10, 11).
7. **New art:**
   - one consistent head bank for the man, with a back view;
   - a poet head bank with open eyes;
   - the poet's profile bodice and skirt;
   - the man's real back vest;
   - lying replacement cards (4, 5, 8, 12).

Items 1–6 are code. Item 7 is generation, briefed per card with
`parts/cut_sheet.py` and `registered.json` waiting for the results.
