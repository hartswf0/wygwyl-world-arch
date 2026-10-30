# Cast audit: what moves, at what size, and what breaks

Lane B of the cut-out suite. This audit covers every character that has to move through the Acting Arena. It records what each one is built from and how big it really is. Each character was run through one standard battery and measured on the render. Every number here comes from `shots/suite/data/characters.json`, `shots/suite/data/cast_parts.json`, `shots/suite/cast/<id>/takes.json` and `shots/suite/cast/drop.json`. The page is `shots/suite/cast.html`.

## 1. What moved before this lane

| source | what it is | how it moves | what was wrong (measured) |
|---|---|---|---|
| `arena/clips/*__{bolas,poet,man}.json` (96 takes) + `results/arena_results.json` | three skins on the 32 Bolas challenges: the cardboard dummy, the **woman** (still called "poet" in the arena code) and the weave **man** | 3D bank joints projected; cards fitted with *axial stretch* | The verdicts belong to the **motion**, not the puppet. Drift and balance are read off the 3D bank joints, and the brad gap is 0 by construction. So all three skins pass or fail the *same* 18/32 challenges (fails: balance 11, planted drift 5, brad 2). The man's torso has no side view (profile = front, IoU 0.973). The woman has one profile head and one hand shape, and her rigid skirt is crossed by her knees. |
| `arena/parts/kit3/release_v2/character_rigs_library.json` | 8 "canonical" rigs, 1,602 resolved parts, posture ratios, a part-scale table | not driven by the arena; it is a table | It claims 7.5 heads for adults and 5.2 for children. The skeletons the parts were *painted to* (`kit.py` / `v2.py` builds) measure **6.93–7.12** heads for adults, **4.79** for the boy, **4.95** for the ghost child and **3.82** for Dot. Its heights disagree with the kit and the play data (below). |
| `play/data.json` + `anim2.js` | 37 walking characters, each a set of whole-figure paintings (4 locked: no clean painting) | 34 of 37 walk by "split-hip scissor" on **one painting**; 3 use a 4-pose stride | No joints, so nothing can reach, sit or touch. POET's stride pair mixes a profile and a three-quarter painting (draws 16 and 5). Heights: every extra is 175 cm, the children 130 cm, the EX 175 cm. |
| `arena/bolas/bank/` (191 vignettes, 3D joints at 24 fps) | the motion | the source for every take below | It is **gitignored**: only `index.json` and `beats.json` are on main. The vignettes were read from the other checkout and copied to a scratch folder to run this lane. Re-running needs `export_bank.mjs` against a bolas checkout. |
| `arena/parts/kit3/v2/parts/<character>.<costume>/` (33 costume dirs) | the v2 Kit 3 cut parts, body cards in 4–5 views, head plates, 12 hand shapes, feet, replacement poses | **nothing drove them as jointed puppets before this lane** | See §2. |

## 2. Scale and proportion problems found in the v2 parts (measured)

Each part was measured against the Kit 3 ghost it was painted into. The ghost's extent in cm comes from `kit.shapes()` and its width/length from the alpha box (`castkit.py`).

1. **Parts are painted at different scales.** Within one profile sheet, px/cm varies **1.5–2.8×** between cards. The 16 generic extras share a 2.6× spread: upper arm 1.47×, forearm 1.37×, hand 0.57× the median. POET in the t-shirt has hands at **2.1×**, so they would be twice too big if pasted at body scale. The young poet's tee kit is painted at 12.5 px/cm, his pajama kit at 5.6 px/cm, and an adult extra's at 4.2 px/cm. A naive paste makes the child as big as an adult.
2. **Heads are on a different sheet.** Measured against the body median, the head plates run from **0.94×** (POET tracksuit) to **3.1×** (generic extras, Shim). Pasting them at body scale gives heads up to three times too big.
3. **Card shape is not the ghost's shape.** Many feet are painted shorter than the ghost relative to their height (aspect 0.48 on the extras' shoe). Boots are painted with a shaft above the ghost. Hung by the template ankle, that put the sole **8 cm under the floor** (first POET walk: floor p50 −8.4 cm).
4. **The neck brad sits on the edge of both cards.** The torso ghost starts at the neck line and the head's neck cross is the tab's bottom edge. As built, the neck showed a **hole in 80 of 110 walk frames**.
5. **Short-necked builds.** The heads sheet paints the same 6 cm neck tab for everyone. The boy's neck needs 3 cm and Bola's 1.6 cm. Pinned at the tab bottom, the children stood **+2 %** and Bola **+3.3 %** too tall.
6. **One head, sixteen characters.** One painted man's head is shared, sometimes recoloured, by the parents, Atlantis people, party guests, club dancers (shirt and jacket), brother, friend and elders. The **young poet in pajamas** and the **ghost child** were given that adult, bearded head. **Bola, Shim and Dot** got the same face recoloured yellow, teal and coral, not blank dummy heads.
7. **Wrong pelvis for the template.** The woman (teal dress), the mother (cardigan) and the indigo ancestor are built on skirt/robe templates with no thigh ghost. Their kits painted **thighs and a hip-bridge triangle** instead. The teal-dress "dress" is a red bodice with no skirt card at all.
8. **Heights disagree across the repo.** EX: 188 (kit) / 175 (play) / 188 (rig library). Young poet: 116 / 130 / 122. Mother: 172 (woman build) / 163 / 174. Every extra in play is 175. Canonical here: the kit's painted build height, scaled per character by `k = height_cm / build height` (§4).
9. **The EX kit** has front/profile/three-quarter files. They are copies of the back cards and the back of his head (checked by eye), so no face exists anywhere. Only back and three-quarter-back are used.
10. **Wings** (angel) are flat panel cards with no ghost and no profile view.

## 3. The battery

| take | Bolas | tests |
|---|---|---|
| walk | T001 Heel, flat, ball, toe | planted feet, stride by leg length |
| turn | T014 Quarter, half, whole turn | every body view in one take; the pop when views swap |
| sit | T006 Sitting down, standing up | a chair sized to the sitter |
| reach | T080 Hanging a picture | two hands to sockets the set owns (frame at 140 cm) |
| handoff | T046 The letter changes hands | hand meets a partner's hand (partner: POET ↔ woman, child ↔ mother, Bola ↔ Shim, others ↔ POET) |
| fall | T108 Stand after a fall | down to the floor and back up |

Pipeline (`lib/castrun.py`):
1. Retarget the 3D joints to the character's own skeleton: directions from the motion, lengths from the build × k.
2. Pin planted feet in 3D.
3. IK the hands to their sockets.
4. Project with the vignette camera.
5. Build the rigid card chain: torso first, then limbs hung from the **torso card's own sockets**, with 2D two-bone IK on card lengths. A planted foot is the **root** of its leg.
6. Composite.
7. Measure on the render, at 640×360 and about 1.39 px/cm (1 px ≈ 0.7 cm).

Checks and tolerances:
- **foot slide**: the rendered sole contact point moving while planted, ≤ 0.6 cm/frame (spec).
- **brad gap**: card-to-card distance at every brad, ≤ 2 cm, **and** no frame where a brad point is transparent (a hole).
- **contact**: socket to hand-card segment, or hand segment to hand segment; median ≤ 3 cm.
- **height drift**: rendered top against the motion's own head top, in standing frames; |mean| ≤ 3 %.
- **floor**: lowest rendered pixel against the projected floor under the planted contact; p95 ≤ 2 cm.
- **balance**: pelvis over the rendered soles in ≥ 95 % of grounded frames.
- **face never seen**: EX only.

**Result: 34 characters × 6 takes = 204 takes rendered, 36,720 frames measured, 175 pass, 29 fail.**

| check | failing takes / takes where it applies |
|---|---|
| foot slide | 0 / 204 |
| brad gap / holes | 14 / 204 |
| contact | 4 / 68 |
| height drift | 8 / 204 |
| floor | 8 / 204 |
| balance | 2 / 204 |
| face never seen | 0 / 6 |

Foot slide is 0 because the planted foot is the root of the leg: the cost moves to the ankle brad, where it is measured as brad gap. The free arms hang from the torso card's own shoulder, which sits higher than the motion's shoulder, so they miss their free target by 2–9 cm. This is reported as `ik_unreached_cm` and is not a check.

## 4. Scale: the rule (lib/scale.js, lib/scale.py, tests in lib/tests)

* **Unit:** the real cm. Each character has `height_cm`. Each part has its own measured `px_per_cm` (cast_parts.json). The scale factor is `k = height_cm / build height`.
* **Into a set:** use the lane-C contract `ground.y_px`, `ground.horizon_y_px` and `scale.px_per_cm_at_ground_line`. Then `ppc(y) = ppc_ground · (y − horizon)/(ground − horizon)`, and the camera height is `(ground − horizon)/ppc_ground`. The test: a figure as tall as the camera has its head on the horizon at every depth. Depth: `y(d) = horizon + (ground − horizon) · d_ground / d`.
* **Drawing a part:** `s = ppc(y) · k / part.px_per_cm`. This one line fixes problems 1–2 above. Every card is drawn at its template length whatever the sheet did.
* **Corrections are constants or data, not per-shot tweaks:**
  - collar tuck 0.8 cm
  - head brad 4 % up the tab, or `6 − needed neck` cm up for short necks
  - ankle brad = the template ankle height above the sole line (scale along the sole only)
  - skirt knees in a slot 4 cm above the hem
  - wings 1.35 × torso
  - action-owned props scale with the leg; set-owned sockets are re-staged to the character's reach top, `shoulder + 0.92 × arm`
* **Drop test:** every character was placed in the poem-07 plaza plate at y 1040 (24 m) and y 935 (62 m). The calibration is in `data/sample_set_p07_plaza.json`: horizon = canopy vanishing point; scale = the plate's own person cut, 112 px, taken as 170 cm; camera 2.53 m up. Heights were measured on the composite:
  - near: **29 / 34 within 3 %** of the rule;
  - far (about 50 px tall, so 1 px ≈ 2 %): 19 / 34.
  - Every figure stands 1–1.5 % under `height_cm` in the Bolas rest stance (knees soft). Against its own stance the near error is −1.75 % to +1.15 %.
* **A finding about the existing weave scene:** in `weave/clips/p07_turn_me_up.json` the woman is 991 px tall with her feet at y 1050. On this plate's floor, perspective says 172 cm at y 1050 is about 124 px. She reads as standing about 8× nearer than the floor line she is drawn on. That is fine if the ground line is understood as hidden below the frame (a foreground plane), but it is not a placement on that floor.

## 5. Every character
| id | plays | rig | height cm (kit / play / rig lib) | heads | views painted | sheet px/cm median · spread · head× | walk | turn | sit | reach | handoff | fall | drop near / far % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| poet_tshirt | POET | jointed | 184 (184 / 183 / 184) | 6.97 | P F 3q B | 4.61 · 2.77× · 1.85× | pass | pass | pass | pass | **FAIL** contact | pass | -2.85 / -2.76 |
| poet_tracksuit | POET | jointed | 184 (184 / 183 / 184) | 6.97 | P F 3q B | 9.02 · 1.58× · 0.94× | pass | pass | pass | pass | **FAIL** contact | pass | -2.85 / -2.76 |
| poet_soul | POET (soul) | jointed | 184 (184 / 175 / 184) | 6.97 | P F 3q B | 9.02 · 1.58× · 0.94× | pass | pass | pass | pass | pass | pass | -2.85 / -2.76 |
| ex | EX | jointed | 188 (188 / 175 / 188) | 7.12 | P F 3q B 3qB | 6.31 · 1.54× · 2.21× | **FAIL** brad gap | **FAIL** brad gap, balance | pass | **FAIL** contact | pass | **FAIL** brad gap, balance | -2.58 / -2.84 |
| woman | the woman (arena) | legged | 172 (172 / – / 174) | 7.11 | P F 3q B | 6.16 · 1.82× · 1.05× | pass | pass | pass | pass | **FAIL** height drift | **FAIL** height drift | -0.33 / -0.31 |
| mother | MOTHER | legged | 165 (172 / 163 / 179) | 7.11 | P F 3q B | 5.11 · 2.04× · 1.21× | pass | pass | pass | pass | **FAIL** height drift | **FAIL** height drift, floor | -1.43 / -2.85 |
| she_window | SHE | skirt | 168 (172 / 165 / 174) | 7.11 | P F 3q B | 4.98 · 2.44× · 1.96× | pass | pass | **FAIL** brad gap, floor | pass | **FAIL** height drift | **FAIL** brad gap, height drift | -0.57 / -0.15 |
| young_poet_pajamas | YOUNG POET | jointed | 116 (116 / 130 / 122) | 4.79 | P F 3q B | 5.55 · 2.19× · 2.36× | pass | pass | pass | pass | pass | pass | -1.48 / -3.59 |
| young_poet_tee | YOUNG POET | jointed | 116 (116 / 130 / 122) | 4.79 | P F 3q B | 12.49 · 1.82× · 1.05× | pass | pass | pass | pass | pass | pass | -1.48 / -3.59 |
| ghost_child | GHOST CHILD | jointed | 122 (122 / 125 / 122) | 4.95 | P F 3q B | 5.34 · 2.26× · 2.42× | pass | pass | pass | pass | pass | pass | -1.52 / -2.22 |
| father_02 | FATHER | jointed | 178 (180 / 175 / 179) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.87 / -3.67 |
| father_elder | FATHER (elder) | jointed | 174 (180 / 175 / 179) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -3.16 / -3.59 |
| ancestor_indigo | ANCESTORS | legged | 180 (182 / 175 / 179) | 7.01 | P F 3q B | 5.1 · 1.51× · 1.6× | **FAIL** brad gap | **FAIL** brad gap | **FAIL** brad gap | pass | pass | **FAIL** brad gap | -2.32 / -2.67 |
| ancestor_elder | ANCESTORS (elder) | skirt | 170 (182 / 165 / 179) | 7.01 | P F B | 4.88 · 2.62× · 2.51× | pass | pass | **FAIL** brad gap, height drift | pass | pass | **FAIL** brad gap | -2.61 / -3.52 |
| atlantis_traveler | citizens | jointed | 178 (180 / 175 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.87 / -3.67 |
| atlantis_citizen | citizens | jointed | 176 (180 / 175 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.6 / -2.57 |
| atlantis_gatekeeper | gatekeeper | jointed | 182 (180 / – / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.59 / -3.74 |
| atlantis_elder | old man with a lantern | jointed | 168 (180 / 160 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.32 / -2.37 |
| vintage_party | party | jointed | 177 (180 / 177 / 181) | 6.93 | P F 3q B | 6.39 · 1.56× · 1.5× | pass | pass | pass | pass | pass | pass | -2.32 / -3.12 |
| dj | DJ | jointed | 178 (180 / 175 / 182) | 6.93 | P F 3q B | 8.96 · 1.51× · 1.61× | **FAIL** floor | **FAIL** brad gap | pass | pass | pass | **FAIL** floor | -2.87 / -3.67 |
| party_guest | party | jointed | 175 (180 / 175 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.88 / -4.14 |
| dancer_dress | club crowd | jointed | 168 (180 / 175 / –) | 6.93 | P F B | 4.0 · 2.59× · 2.82× | **FAIL** floor | pass | **FAIL** floor | pass | **FAIL** floor | **FAIL** floor | -3.19 / -2.37 |
| dancer_shirt | club crowd | jointed | 178 (180 / 175 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.87 / -3.67 |
| dancer_jacket | club crowd | jointed | 176 (180 / 175 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.6 / -2.57 |
| angel | ANGELS | skirt | 182 (182 / 175 / 182) | 7.01 | P F B | 4.88 · 2.62× · 2.51× | pass | pass | **FAIL** brad gap, height drift | pass | pass | **FAIL** brad gap | -2.59 / -3.74 |
| brother | BROTHER | jointed | 180 (180 / 175 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -3.13 / -2.67 |
| friend | friends | jointed | 177 (180 / 175 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -3.15 / -3.12 |
| elder_memory | elders (memory) | jointed | 165 (180 / 160 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -3.21 / -2.85 |
| elder_pearls | elders | jointed | 160 (180 / 165 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.93 / -2.15 |
| couple_summer | couples | jointed | 175 (180 / 175 / –) | 6.93 | P F B | 4.24 · 2.59× · 2.89× | pass | pass | pass | pass | pass | pass | -2.88 / -4.14 |
| street_clothes | family / everyday people | jointed | 178 (180 / 175 / –) | 6.93 | P F 3q B | 10.02 · 1.6× · 1.47× | pass | pass | pass | pass | pass | pass | -2.87 / -3.67 |
| bola | Bola | jointed | 172 (172 / – / –) | 5.04 | P F 3q B | 4.67 · 2.6× · 2.74× | pass | pass | pass | pass | pass | pass | -1.18 / -2.47 |
| shim | Shim | jointed | 182 (182 / – / –) | 5.17 | P F 3q B | 4.39 · 2.63× · 2.92× | pass | pass | pass | pass | **FAIL** contact | pass | -1.78 / -1.69 |
| dot | Dot | jointed | 105 (105 / – / –) | 3.82 | P F 3q B | 8.76 · 2.18× · 1.45× | pass | pass | pass | pass | pass | pass | -0.92 / -0.59 |

`rig`: jointed = thighs from torso sockets; legged = thighs + painted hip bridge (the kit did not follow the skirt template); skirt = skirt/robe card carries the knees in a slot. Heights are canonical / (kit / play / rig library). The sheet column is that character's profile cards: median px/cm, max/min spread, head plate vs body.

## 6. Problems and the solution chosen, by kind of body

| body | problem (measured) | solution | result |
|---|---|---|---|
| **every character** | parts painted 1.5–2.8× apart, heads 0.9–3.1× the body | per-part px/cm from the Kit 3 ghost; draw at `ppc·k/part_ppc` | line-up at one px/cm reads correctly (`cast/lineup.jpg`); drop test near: 29/34 within 3 % |
| every character | boot shafts painted above the ghost: sole 8 cm under the floor | foot scaled along the sole only; ankle brad hung at the template ankle height above the card's bottom edge | POET walk floor p50 −8.4 → +0.5 cm |
| every character | neck brad on both cards' edges: hole in 80/110 frames | collar tuck: brad 0.8 cm into the collar and 4 % up the tab | 0 neck holes in 204 takes |
| every character | rigid foot cards driven by the *projected* ankle→toe dive through the floor when the foot points at the camera (turn: floor p95 11 cm); a mirrored card turned 180° lands upside down (the old boot bug) | foot oriented by its true 3D pitch, its left/right taken from where the foot points, the card mirrored by the foot, not the body | turn floor p95 11 → 0.4 cm |
| every character | planted feet slid 2 cm/frame when the card's ball differed from the skeleton's | the planted foot is the root of the leg (card contact point pinned, leg IK'd up to it); the residual is an ankle brad gap | foot slide 0 in 204/204 takes; gap reported |
| every character | three-quarter cards were treated as side views | 3/4 cards were painted into FRONT ghosts: their feet stand upright | 17 turn failures → 3 |
| **children** (young poet ×2, ghost child, Dot) | 4.8–5.0 heads (3.8 Dot); short limbs; adult sockets out of reach; adult chair | root travel × leg ratio (strides 0.57–0.67× an adult's: Dot 0.57, boy 0.63, ghost 0.67); chair sized to the leg; set sockets re-staged to the reach top (frame 140 → 108 cm for the boy, 93 cm for Dot); short neck tab | all six takes pass for both young poets, the ghost child and Dot |
| children (pajamas), ghost child | given the adult bearded head | borrow the boy's head (ghost: tinted, 70 % alpha) | flagged: needs its own painted head |
| **EX** | face never seen | camera yaw searched per take (5° steps) so he faces away; any frame that would show the face is marked CUT and is cut in the edit; only back / 3/4-back cards and the back of his head | walk/sit/reach/handoff need **no** cuts; turn: 61 of 150 frames are CUT (a turn becomes two shots); fall: 0 cuts but 11 view swaps. Fails: brad gap 2.1–3.4 cm (3/4-back ankle), contact 9.9 cm on the frame (he reaches with his back to us: the hand is behind the body card), balance 77–83 % in turn/fall |
| **skirt / robe** (SHE, angel, elder ancestor) | knees fused into the skirt card | knee brads in a 4 cm-above-hem slot; if a planted foot is still out of reach the whole body drops to it (`skirt_body_drop`) | walk passes (drop ≤ 6 cm); sit and fall fail: ankle gap 3.5–4.3 cm seated, **14.6–16.5 cm on the floor** (a skirt card cannot lie down: needs the replacement poses) |
| **legged women** (THE WOMAN, MOTHER), indigo ancestor | template wanted a skirt, kit painted thighs + hip bridge | rigged as legs with recomputed thigh ghosts; bridge pinned at the waist; MOTHER's brocade skirt as a free overlay (±25° on the mean thigh) | walk/sit/reach pass; the overlay skirt is crossed by a thigh in 30/110 walk frames (counted); the afro is counted in height (+3.6 %: fails height drift in handoff and fall); the indigo ancestor's far shoulder brad shows a hole in 6–7 frames (the torso card is narrower than its socket) |
| **angel** | wings with no ghost | pinned at the shoulder blade, 1.35 × torso, behind except from the back | wings visible in profile and from the back; the robe fails sit/fall like the other skirts |
| **Bola, Shim, Dot** | v2 heads are the man's face recoloured | heads drawn by code (plate, crash target, eyes, antenna/fin/bow); height measured to the crown | Bola 6/6, Dot 6/6, Shim 5/6 (hand-off contact 5.8 cm with Bola) |
| **adult-adult hand-off** (POET ×2 ↔ woman, Shim ↔ Bola) | the midpoint of two retargeted wrists is out of one rigid arm's reach | 3D two-bone IK to the midpoint, then 2D IK on card lengths | contact median 5.1–5.8 cm (fail). Next: move the socket toward the shorter reach, or step the partner in |
| **DJ, club dancer (dress)** | shoes painted off the ghost (aspect 0.5) | scaled along the sole | floor p95 2.4–2.5 cm in walk (fail by 0.5 cm, about 1 px) |

## 7. What is not solved

* Lying, kneeling and sitting deep are still jointed cards. The kits have replacement poses (`replacement.sit/kneel/fall/lie_*`, listed per character in characters.json) that are not yet swapped in. Skirted bodies need them.
* No face plug-ins or expressions are driven. The painted heads are used as they are.
* The EX's turn is cut, not solved. A three-quarter-back head turn is the only motion his cards allow.
* Heads normalise by plate plus hair/headwear height. An afro or turban makes the face slightly smaller and counts toward height (woman +3.6 %).
* Sixteen generic extras share one head drawing. Identity rests on costume until heads are painted.
* Lane A's `shots/suite/data/parts.json` was not available. characters.json points to `cast_parts.json` (the same v2 files) and part ids are `<character>.<view>.<part>`. Re-key the ids when lane A lands.
* Privacy: nothing here uses or derives from private photography. One open question, not checked by this lane: the POET kit prompts say "as in the reference photos" (`arena/parts/kit3/refs/man_tracksuit_*.png`, committed on main). Their provenance should be confirmed.

## 8. Files

* `lib/castkit.py`: the cast list, template geometry, part measurement → `data/cast_parts.json`
* `lib/castrun.py`: retarget, pin, cut-out solve, render, measure → `cast/<id>/{walk,turn,sit,reach,handoff,fall}.{mp4,jpg}` + `takes.json`
* `lib/castdrop.py`: drop at scale + line-up → `cast/<id>/drop.jpg`, `cast/lineup.jpg`, `cast/drop.json`, `data/sample_set_p07_plaza.json`
* `lib/build_characters.py`: `data/characters.json`
* `lib/scale.js`, `lib/scale.py`, `lib/tests/` (node --test, unittest; shared cases)
* `cast.html`: the page

Re-run: `python3 shots/suite/lib/castkit.py && python3 shots/suite/lib/castrun.py --bank <bank dir> --jobs 12 && python3 shots/suite/lib/castdrop.py --bank <bank dir> && python3 shots/suite/lib/build_characters.py <bank dir>/T001.json`
