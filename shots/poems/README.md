# Poem production design

One page per poem (`NN.html`, index at `index.html`) that a production designer and an animator can
build the cut-out film from: the poem, its best footage, its world (from the atlas), the cast in costume,
the props in every state, the places as multiplane layers, and every kit to generate as one image plus
one prompt. The production bible's poem pages (`pNN.html`, from `shots/arena/generate_production_pages.py`)
show the finished, sliced parts; each page links to the other.

## What is here

| path | what |
|---|---|
| `dossier/NN.json` | **the source of truth** for a poem's design (schema: `dossier/SCHEMA.md`). Edit this, then rebuild. |
| `atlas/NN.json`, `atlas/world.json` | what butterfly-halfworld's world atlas knows about the poem (scene book, districts, hero buildings, foundry, archive search) and the gazetteer |
| `refs/stills/`, `refs/districts/` | our Midjourney stills (640 px) and district contact sheets |
| `refs/atlas/` | atlas images (≤480 px): `views/` scene-book world views, `heroes/` hero-building photos, `foundry/` and `sets/` foundry frames, `archive/` archive thumbnails |
| `kits/NN.*.jpg`, `kits/NN.json` | the poem's kits: props in every state, a sheet per place, per hero building, painted effects |
| `kits/all.json`, `kits/prompts.md` | every kit of every poem in one file, for batch generation |
| `breakdown/NN.json` | shot breakdowns (used by the production bible) |
| `assembly/` | the treatment PDF and its text |

Character kits (bodies, heads, hands, feet, replacements, per-poem action sheets) are in
`shots/arena/parts/kit3/v2/` and on `shots/kits.html`; poem pages show each character's action sheet.

## Using a kit
1. Download the kit image and copy its prompt. Give the image model exactly those two.
2. Panel A is the layout to paint into. Panel B is what the thing is: our footage and atlas references,
   to copy for content, not photo style. Panel C is the cardboard craft to copy.
3. On the result, a green cross is a card's pivot (a brass brad) and a red cross is where a hand grips.

## Rebuilding
```sh
python3 shots/poems/atlas.py [path/to/butterfly-halfworld]   # atlas/NN.json + refs/atlas/ (needs the butterfly-halfworld clone)
python3 shots/arena/parts/kit3/poem_kits.py                  # kits/ from the dossiers
python3 shots/arena/parts/kit3/poem_pages.py                 # NN.html, index.html, kits/all.json, kits/prompts.md
```
`poem_pages.py` reads the character action sheets from `shots/arena/parts/kit3/v2/kits.json` (built by `v2.py`).
Note that `shots/kits.html` is now hand-extended on top of `v2_page.py`'s output (the parts explorer).
Do not regenerate it with `v2_page.py` without carrying that explorer over.

## Fixed casting
POET is a man: a black t-shirt in 01–03, then a red/black outfit with sunglasses from 04. The EX is a man
whose face is never seen. YOUNG_POET (6) and GHOST_CHILD (7) are children. "The woman" (the old 'poet' puppet)
plays MOTHER and SHE. Extras are grouped by scene. Never draw a pelvis/hip/shorts card, a sleeveless vest,
lace-up boots, or sunglasses painted onto a head.

## Sources and credit
The poems, the treatment (`assembly/`), the reading transcripts, the suite's world modules and the atlas all
come from hartswf0/butterfly-halfworld. The atlas images are thumbnails of its generated stills, MARKOV_POET
clips, halfworld frames and archive footage, used here as production references. Shoot photographs of real
people are never included.
