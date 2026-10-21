# Production-design dossier schema (one JSON per poem: `dossier/NN.json`)

The film is a cut-out (cardboard puppet) film. These dossiers drive one page per poem and the kits we
generate (one image + one prompt per sheet). Write for a production designer and an animator.

## Read, all of it
- the full poem: `butterfly-halfworld/wygwyl/descriptions/NN.md` (timestamped transcript of the reading)
- the treatment: `shots/poems/assembly/WYGWYL_Assembly_R6-4-25.pdf` (Read with pages; text in `assembly/assembly_pN.txt`)
- the suite's world module: `butterfly-halfworld/wygwyl/worlds/NN-*.mjs` (how the poem is staged: every mechanism is a line)
- our shot breakdown: `shots/poems/breakdown/NN.json`
- our footage:
  - stills: `shots/poems/refs/stills_index.json` (id, district, prompt, detected objects); the images are `shots/poems/refs/stills/<id>.jpg`;
    contact sheet per district `shots/poems/refs/districts/<district>.jpg` (LOOK at them with Read)
  - the poem's film cut: `shots/film/poems.json` (entry for the poem: its district and the still ids it uses)
  - archive and generated clips: `shots/atlas_footage.json` → `by_poem[NN]` (file, source, tags)
- the cast and kits we already have: `shots/arena/parts/kit3/v2/kits.json` (characters, costumes, per-poem action sheets)

## Casting (fixed)
POET is a man (black t-shirt in 01-03, red/black outfit + sunglasses from 04). EX is a man whose face is never seen.
YOUNG_POET (6) and GHOST_CHILD (7) are new children. "The woman" (the old 'poet' puppet) plays MOTHER and SHE.
Extras by group. Character ids: poet, ex, young_poet, ghost_child, woman, parents, ancestors, atlantis, party, angels, family.

## JSON
```json
{
 "num": "04", "title": "Nevermore", "district": "Mirror Thread Bay",
 "essence": "2-3 sentences: what this poem is, in images",
 "palette": ["#0b1a2a", "#c23a2c", "..."],
 "palette_notes": "where the colours come from (stills, accent)",
 "full_text": [{"t": "00:00.1", "line": "What if I follow this trail ..."}],
 "arc": [{"movement": "WASHED ASHORE", "beat": "he finds the trail", "emotion": "numb", "image": "the one image that carries it"}],
 "best_footage": [{"still": "<still id>", "element": "what in it we take", "use_for": "set|prop|light|texture|mood|blocking", "why": "..."}],
 "clips": [{"file": "<atlas file>", "use_for": "...", "why": "..."}],
 "characters": [{"id": "poet", "costume": "red_black_sunglasses", "role_in_poem": "...", "arc": "...",
                 "signature_actions": ["kneels at the pile, hands still in pockets"], "expressions": ["..."],
                 "hands": ["in_pocket", "missing", "hand_L detachable"], "props": ["heart"],
                 "design_notes": "...", "new_parts": ["chest-hollow torso card", "..."]}],
 "props": [{"id": "heart", "name": "the heart", "hero": true, "look": "...", "build": "how to make it as cut-out cards (single card, jointed, replacement states, coded glow)",
            "scale_cm": 14, "states": ["beating", "dusted", "floating", "seated in the chest"], "who": ["poet"], "refs": ["<still id>"]}],
 "sets": [{"id": "night_shore", "name": "the night shore", "look": "...", "light": "...",
           "layers": {"sky": "...", "back": "...", "mid": "...", "front": "...", "floor": "..."},
           "refs": ["<still id>"], "reuse": ["13"]}],
 "fx": [{"id": "ravens", "how": "coded|painted cards|both", "note": "..."}],
 "actions": [{"id": "find_heart", "who": "poet", "move": "kneel, hands in pockets; heart floats up and re-enters the chest", "pose_kit": "poet.04.action", "timing": "4 s, holds on the float"}],
 "kits_to_build": [{"id": "04.props.hero", "kind": "props|set|fx|character", "what": "...", "why": "..."}],
 "insights": ["production insights: what makes this poem work in cut-out, what to reuse, what to avoid"],
 "future": ["what this poem gives to later poems (assets, motifs)"]
}
```
Be specific and visual. 6-12 best_footage entries, every hero prop and every set with at least one still ref
where one fits (or say none fits). Every still id must exist in stills_index.json.
