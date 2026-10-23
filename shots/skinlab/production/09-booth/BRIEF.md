# 09 — the booth passage: brief, thesis and bar

Run of `shots/skinlab/SCION_PUPPET_FOUNDRY.md`. Owner of the bar: the SCION orchestrator. Builders never award the pass.

## The passage
Poem 09 "Yet, Heard", audio `shots/stage/audio/09.mp3`, **34.79 s → 43.40 s** (8.6 s):
- 35.10–36.80 "You help me gather my things to go."
- 37.98–38.58 "Before I go,"
- 38.74–39.48 "I call on my mother."
- 40.30–43.40 "In tears, speaking of an abyss, she's never known."

**The action:** the poet, carrying a suitcase, walks the quay to the lit phone booth. He sets the case down, turns into the booth, lifts the handset to his ear on "I call on my mother", and holds it through "In tears…". The world: `stage/ensembles/ens.phone_booth.quay.json` and the quay sets, at night. The motion sources are Crash Lab trials T009 (heavy suitcase), T014 (turn) and T025 (phone between ear and shoulder).

## Creative thesis
**Central experience:** a man who is leaving makes one call. The only thing that holds him up is a handset on a cord.

**Distinctive formal choice:** paper that admits it is paper. Brads show, a turn is a card swap that lands on a pose, holds are real holds, and nothing is tweened smooth.

**Defining moment:** the hand meets the handset and lifts it to the ear on "I call on my mother". Then the body settles into the hold, and the weight goes onto the booth or the cord, through "In tears".

**Competent but forgettable:** a smoothly tweened paper doll sliding across a backdrop, with a borrowed face, and feet that skate.

## Quality references (what was reachable)
External film references were **not reachable** from this environment (archive.org and Wikimedia are blocked). That limitation is recorded here. The bar rests on observable tests and on internal references that agents can open:
- **Weight and contact:** Crash Lab trials T009, T014 and T025 played in the Skin Lab, with the Bolas rules. A planted foot slides less than 0.6 cm per frame. The centre of mass stays over the feet unless a fall is the action. A hand lands within 2 cm of its target.
- **Sync to the voice:** `shots/weave.html` (movement cued to the audio). Key poses land within 2 frames of the word they serve.
- **Staging in planes:** `stage/seq/clips/seq.09.phone.near.json` and `seq.09.phone.far.json` and the stage's 09 playthrough. The new passage must read better than these at 1600×900 and normal speed.
- **Cut-out acting (observable tests, no film to compare):**
  - the silhouette alone tells the action at each key;
  - the turn reads as a turn, not a pop;
  - one hold of at least 1 s carries the thought;
  - no idle bobbing;
  - left and right arms are not symmetric at the defining moment.

## The bar (the critic's checklist; all at playback size, normal speed first)
1. **One person drawn by one hand.** Every visible card in a view comes from one sheet or a declared, matched substitute. One head and one face throughout. One scale: parts are within 0.75–1.35 of his canon.
2. **Joints hold.** No card is stretched more than 12% off its true length. No visible gap at a brad (2 cm or more at stage scale). The layer order is right in every view: shoe over calf, near arm over torso, hand over handset where the drawing says so.
3. **Weight.** The suitcase visibly pulls the body. Feet plant and do not skate. The set-down has preparation and settle.
4. **The turn.** The front, side and back card swaps land on poses. None happens mid-tween, and no torso, hip or head shows the wrong view.
5. **Contact.** The hand reaches the handset, and the handset travels with the hand to the ear and stays there through the hold. The cord stays attached.
6. **The face reads** at playback size: painted, or a blank head with a matched feature set. It is not blank, and not a stranger's head.
7. **Sync.** The lift lands on "I call on my mother" (38.74 s ± 2 frames). The hold carries "In tears".
8. **Staging.** The booth light groups the poet. The silhouette reads against the quay, and the planes give depth without clutter.
9. **It is a film moment, not a test.** A fresh viewer would understand who, where and what without any text.

## Character contract format (shared by every builder): `shots/skinlab/contracts/<character>.json`
```json
{
 "character": "poet", "costume": "...", "height_cm": 184,
 "style": "hips",                                   // Skin Lab rig style: classic | hips | mitt | long
 "proportions": {"preset": "cards|vitruvian|custom", "K": {"thigh": 1.0}},
 "bind_frame": 0,
 "stack": {"side": ["far_upper_arm", "..."], "front": [], "back": []},   // Skin Lab roles, back to front
 "limbs": {"torso": {"cards": {"side": "<card id>", "front": "...", "back": "..."}, "src": {"side": "kit|bashed|built"},
           "mode": "true|fit", "scale": 1, "rot": 0, "dx": 0, "dy": 0, "mirror": false, "swap": false}},
 "fix": {"<card id>": {"A": [0, 0], "B": [0, 0], "left": false, "view": "side", "painted": true, "slot": "foot", "bad": false}},
 "face": {"head": "<card id>", "painted": true, "features": {"eye": null, "brow": null, "mouth": null, "nose": null}},
 "claims_by": "agent-vision | person | clip | pixels",   // who settled the claims this contract relies on
 "invariants": {"...measured results...": 0}
}
```
The Skin Lab reads the same data from localStorage (`skinlab.current` = {skin, style, stack, K, preset}; `skinlab.fix` = fix). So a contract can be proven in the real lab, unmodified.
