# Shot breakdown schema (one JSON per poem: `breakdown/NN.json`)

Sources, both required:
- the assembly treatment `shots/poems/assembly/WYGWYL_Assembly_R6-4-25.pdf` (poem left, staging right; per-page text in `assembly/assembly_pN.txt`, layout text in `assembly/assembly.txt`)
- the suite's world module for the poem (`movements.json` here: each movement's label, seconds and line; source `butterfly-halfworld/wygwyl/worlds/NN-*.mjs`)

Every scene is one movement of the world module, in order; its staging comes from the treatment lines beside those poem lines. Where the treatment is silent, stage from the line itself (the suite's law: every element on screen is in the line).

## Casting (fixed)
| role | puppet | rule |
|---|---|---|
| POET | `poet` | the speaker. Costume by treatment: `black_tshirt` (Out of Life onward) until the treatment changes it; `red_black_sunglasses` from Nevermore ("Red/Black outfit with sunglasses"). |
| EX | `man` | **face never seen**: view is always `back` or `threequarter_back`; head card is the back of the head; expression is `unseen`. |
| YOUNG_POET | `young_poet` (new; `dot` stands in) | the poet at six. |
| GHOST_CHILD | `ghost_child` (new; `dot` stands in, translucent) | the dead seven-year-old. |
| PARENTS, GUESTS, ANCESTORS, ELDERS, CROWD | `extra` | name the role, e.g. `PARENT_1`. |

## Vocabulary (use these words so the sheets can be drawn from the data)
- `view`: front, threequarter, profile, threequarter_back, back
- `pose`: stand, walk, run, sit, kneel, crouch, lie, fall, float, reach, lean, dance, turn, climb
- `expression`: listening, surprised, strain, pain, afraid, tired, sad, recognition, forced_grin, reluctant, panting, embarrassed, awe, joy, calm, unseen
- `eyes`: open, closed, half, wide, down, up, side, unseen
- `hands.L / hands.R` shape: relaxed, open, fist, grip, pinch, point, thumb, peace, wave, claw, cup, flat_push, in_pocket, hidden, missing (Nevermore: the hands are lost and found)
- `framing`: wide, full, medium, close, extreme_close, insert, pov
- `camera`: eye, high, low, top_down, through_window, tracking
- `position`: {"x": 0..1 across the frame, "depth": "near|mid|far", "level": "floor|seat|air|fall"}

## JSON
```json
{
 "num": "01", "title": "Out of Life", "pages": [1,2,3], "style": "photo-realistic",
 "sets": [{"id": "bedroom_highrise", "what": "plain bedroom, high rise, dim; window to a fire escape; TV"}],
 "scenes": [{
   "id": "01.1", "movement": "THE SEARCH", "seconds": 13,
   "lines": "What we've made / we don't want— ...",
   "treatment": "Open on plain bedroom ... POET is reading poem out loud to EX ...",
   "shots": [{
     "id": "01.1a", "framing": "wide", "camera": "eye", "set": "bedroom_highrise",
     "action": "POET reads aloud from a page; EX outside the window on the fire escape, back to us, vaping",
     "bodies": [
       {"role": "POET", "puppet": "poet", "costume": "black_tshirt", "view": "threequarter", "pose": "stand",
        "action": "reads aloud", "expression": "sad", "eyes": "down", "mouth": "speaking",
        "hands": {"L": {"shape": "grip", "holds": "poem_page"}, "R": {"shape": "relaxed", "holds": null}},
        "position": {"x": 0.3, "depth": "mid", "level": "floor"}},
       {"role": "EX", "puppet": "man", "costume": "ex_jacket", "view": "back", "pose": "lean",
        "action": "vapes on the fire escape", "expression": "unseen", "eyes": "unseen", "mouth": "unseen",
        "hands": {"L": {"shape": "relaxed", "holds": null}, "R": {"shape": "pinch", "holds": "vape_pen"}},
        "position": {"x": 0.78, "depth": "far", "level": "floor"}}
     ],
     "props": [{"id": "vape_pen", "held_by": "EX.R"}, {"id": "tv", "state": "showing world chaos", "position": {"x": 0.1, "depth": "mid"}}],
     "fx": ["vape_haze"]
   }]
 }],
 "needs": {
   "bodies": ["poet:black_tshirt", "man:ex_jacket (back only)"],
   "heads": ["poet: sad, listening ...", "man: back only"],
   "hands": ["poet: grip(page), relaxed ...", "man: pinch(vape)"],
   "props": [{"id": "vape_pen", "what": "slim vape pen, glowing tip", "scale_cm": 12}],
   "sets": ["bedroom_highrise"],
   "fx": ["vape_haze", "flashing_lights"],
   "new_parts": ["poet black t-shirt torso cards (4 views)", "..."]
 }
}
```
Two to four shots per scene. Be concrete and physical: what each hand holds, where each body stands, which way it faces. `needs` is the union of everything the shots use, with each prop described once (what it looks like, its size in cm).
