# Cast · the man (cardboard cut-out)

A **library**, not one sheet per scene. That is how cut-out studios have always worked (and how *TROUTTOWN* is built): a few body sets by view, plus big banks of replacement heads and hands. A scene picks from the library; it only gets its own new sheet when it needs something the library does not have (a new costume, a prop, an unusual pose).

All images here are generated (INVENTED). His look was described in words from the user's reference photos; the photos themselves are not in the repo. Put them in `ref/` and future sheets can use them directly as image references, which will hold the likeness much better than a description.

## What is here (`sheets/`)

| Sheet | Holds | Use | Notes |
| :-- | :-- | :-- | :-- |
| `body_profile.jpg` | profile head (sunglasses), sleeveless torso, hips, 8 sleeve pieces, open + pinch hands, 2 legs | walking across frame, kneeling, reaching (like the POET) | extra arm pieces; pick the two clearest pairs |
| `body_threequarter.jpg` | head, torso, hips, sleeves, 2 hands, 2 legs | turning, standing at an angle, walking diagonally | its head came out in profile, not 3/4: use the 3/4 head from `heads.jpg` |
| `body_front.jpg` | front head, torso, hips, sleeves, 2 hands, 2 legs | walking toward camera, standing facing us, addressing the viewer | |
| `body_back.jpg` | back of head, torso, hips, sleeves, 2 hands, 2 legs | walking away down a path | |
| `heads.jpg` | 12 heads: 6 angles (profile R, 3/4 R, front, 3/4 L, profile L, back) + 6 expressions (smile, eyes closed, looking up, looking down, sunglasses, speaking) | replacement heads, swapped on the neck brad | the main acting tool |
| `hands.jpg` | 15 hands: open, palm down, palm up, loose fist, fist, pinch, point, thumb up, holding sunglasses, adjusting sunglasses, knob grip, notebook, pen, wave, curled | replacement hands, swapped on the wrist brad | the sunglasses pair is one two-hand piece |
| `draft_profile_unriggable.jpg` | first try | reference only | sleeves fused to the jacket, hands fused to the arms |
| `heads_front.jpg` | 12 front-facing heads: neutral, big smile, small smile, eyes closed, looking up, looking down, sunglasses, sunglasses + smile, speaking, singing, surprised, frowning | acting to camera; lip shapes (speaking / singing / closed) for her words | strongest likeness consistency so far |
| `legs_walk.jpg` | profile walk legs (flat, toe-off, passing, heel strike, step), a bent-knee leg, 2 thigh lengths + 1 full trouser leg, 2 loose boots, 2 front/back legs | walk cycles: alternate these on the knee brad | thigh and shin are fused in the bent pieces, which is fine for replacement walks |
| `body_sitting.jpg` | front sitting (wide thighs, legs down, sunglasses head, arm adjusting glasses, arm on knee) and profile sitting (torso, horizontal thigh, two shins) | sitting on a bench or ledge (from the reference photo) | the front arms have their hands fused on: pose pieces, not general arms |
| `hands_2.jpg` | 15 more: front hanging L/R, curled L/R, edge-on, back of hand L/R, palm out, peace, cupped ear, microphone, phone, record, on a turntable, in a pocket | front/back views, DJ and listening gestures (poem 07) | the pocket is khaki, not black: recolour or regenerate |
| `props.jpg` | sunglasses (front, profile, folded), notebook closed/open, pen, phone, microphone (in hand), record, turntable + separate tone-arm, headphones, lamp, folded note, bench | props that hands hold or that sit in a set | the microphone came with a hand attached |
| `legs_segmented.jpg` | separate thighs (2 long, 3 short/foreshortened), shins (one with a bunched deep-bend knee), 4 plain chelsea boots (flat, on toe, pointed, front), example crouch and kneel | the arena rig: knee placement for crouch, kneel, mantle, lift | replaces the lace-up boots; the first two thighs touch their shins on the sheet |
| `legs_run_stairs.jpg` | run legs, stair step up/down, jump tucks, two lying legs | run, stairs (poems 09, 11, 13), falls | most pieces are two legs fused together: cut apart or regenerate one leg per piece |
| `heads_intent_effort.jpg` | 12 heads: strain, pain, panting, tired, afraid, surprised; reluctant, embarrassed, forced grin, recognition, listening, sad | effort and intent (arena challenges, poems 02, 03, 05, 08, 12) | the bottom row is good 3/4; the top row came out front-ish, not the profile asked for |
| `heads_effort_threequarter.jpg` | 12 more effort/intent heads | a second 3/4 bank | asked for strict profile; came out 3/4, two facing left. Strict profiles are still a gap |
| `arms_hands_contact.jpg` | foreshortened upper arms and forearms, a flared elbow pair, two overhead sleeves; bar grips, edge hook, flat palm, spread catch, ball pinch; cupped pair, box lift, hand on shoulder, clasped hands, cup from below | contact: ledges, railings, doors, catching, carrying, touching another person | bar grips have the bar fused on; the box lift has the box; the shoulder hand has a jacket piece |
| `set_props.jpg` | railing (x2, both side view), stairs with handrail, door leaf + separate frame, car door with window, box, table, two cups + lid, baseball x2, basketball, soccer ball, racket, street sign | set pieces for the arena and the poems (railing, stairs, door, vehicle, sign) | the balls overlap: cut with care |

The last six sheets were generated on 2026-10-20 from the ranked gap list in [arena_requirements.md](../../../arena/requirements/arena_requirements.md), with the earlier sheets as style references.

Known drift between sheets: the torso shape is almost the same in front, 3/4 and back (the generator reused the layout); the boots are lace-ups, the photos show plainer ankle boots; the piping reads orange-brown, the photos show red-orange.

## Views, and how a shot picks one

A cut-out figure faces one way per set. Turning is a **replacement**, not a rotation: profile -> 3/4 -> front, swapped on a held frame or behind a hand or an occluder.

| What he does | Body set | Head |
| :-- | :-- | :-- |
| walks across frame | profile | profile (flip the whole set for the other direction) |
| walks toward camera | front, scaled up over the walk | front |
| walks away | back, scaled down over the walk | back |
| walks diagonally | 3/4 | 3/4 |
| turns to us | profile -> 3/4 -> front, one swap per beat | matching angle |
| speaks, reacts | any | expression heads |

Walking toward or away is done by **scale and ground line** in the clip (the plate's perspective sets the scale per metre). Legs alternate on the same set; no new drawing is needed for each step.

## How a scene uses this

For each passage, list in its `build_clip.py`:

1. which body set(s) and which heads/hands it uses, by id;
2. the swap times (on her words, like every other state);
3. anything it needs that the library lacks. Generate only that, as a small extra sheet in `shots/weave/<passage>/src/`, with this library's sheets as the style reference.

Next step to make this usable: a `cast/man/build_cast.py` that cuts every piece out of every sheet, names it (`head.front`, `head.smile`, `hand.point`, `body.back.torso` ...), sets its pivot and sockets, and writes one `cast/man/cast.json` that any passage can reference, the way `p04_hands` reuses the POET parts.
