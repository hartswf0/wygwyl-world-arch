# Epistemic ledger · p04_hands

Five kinds of claim, kept apart. Nothing moves between columns without a note.

## OBSERVED (with a source opened)

| Claim | Source |
| :-- | :-- |
| She reads poem 04 at 362–396 s on the WYGWYL suite recording; "I put them back on with the care of my future at stake" falls at 385.5–389.0 s. | `WYGWYL_Suite_Audio.mp3`; word times in `voice/p04_words.json` (faster-whisper small) |
| *Eagle Has Landed: The Flight of Apollo 11* (1969), clip 6bb6d333, is 10.1 s, 29.97 fps, silent in this library. Frames 256–304 show a man at a ship's rail turning and laughing; frame 305 is a shot change. | [movingimagearchive.com clip 6bb6d333](https://www.movingimagearchive.com/sources/eagle-has-landed-the-flight-of-apollo-11?clip=6bb6d333-facb-5c4e-b540-0c150f87833b), frames extracted and inspected by `build_assets.py` |
| The cineosis cels cut had already matched this clip to poem 04 (patches P04-011, P04-012). | `cineosis-lab/lab/cels/cels.json` |

## CHARACTER BELIEF

| Claim | Status |
| :-- | :-- |
| "They too used to be mine": she believes her hands were hers and can be again. | The passage grants it: she finds them and puts them back on. Her belief made literal, not a fact about the world. |
| The 1969 man is **not** her memory. | He is shown as archive, tagged on screen for every frame he is visible, behind the plate's ledge. He is a citizen of the scene, not a flashback. |

## INVENTED

| Element | Note |
| :-- | :-- |
| The night garden of glass spires. | WYGWYL poem_04 AI plate, keyframe 84, held. The ledge is cut from it. |
| The POET puppet and her second, open hand. | Parts reused from p07; the open hand generated for this passage. Not a likeness of the performer. |
| The rule that her hands come off and go back on with brads. | The poem says "I put them back on"; the brads make it literal in cardboard. |
| That she searches the wrong patch of ground first. | The failure beat, placed on "search the ground". |
| The light that finds the hands. | Drawn, on "two hands". |

## RETOUCHED (observed material we changed)

| Element | Change |
| :-- | :-- |
| The 1969 sky. | A per-pixel median of the clip's own sky pixels over 305 frames; where no frame shows sky, a smooth blur fills it. It is not one frame of the film. The on-screen tag says SKY ASSEMBLED FROM ITS FRAMES. |
| The man at the rail. | One fixed scissor cut around him, scaled 1.32, a paper ring added. His frames inside the cut are untouched. |

## DRAWN

The ground strip, the stick, the dust, the light, the darkening, the labels, and every sound except her voice.
