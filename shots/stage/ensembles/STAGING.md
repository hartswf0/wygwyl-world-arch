# Staging rules for the cut-out stage

A scene is a composed shot, not a pile. Each scene in `plans/NN.json` is built from a recipe in `recipes.py`:

```
python3 shots/stage/ensembles/build_ensembles.py   # ensembles/ens.*.json (only those a recipe uses) + sets/water/*.webp
python3 shots/stage/plan_poems.py 09 -f            # restage poem 09 from its recipes (other poems untouched)
python3 shots/stage/build_timeline.py 09           # (lead) re-derive the cues
```

## The rules

1. **One focal action per scene.** One figure (or one pair) doing one thing: reaching through the crowd, zipping the case, walking east. Everyone else is still or is an extras group.
2. **2 to 4 ensembles, placed by depth band.** A back ensemble (sky, far band, water), one or two mid ensembles (the place: quay, booth, room), at most one front/extras group. Each is placed with its anchor at depth k (1 = the subject's distance) and an x; nothing is scattered piece by piece.
3. **Negative space.** The focal action sits on a third (x of about 533 or 1067) with open floor or sky around it. The caption band (bottom 15%) holds no faces or hands.
4. **One coherent background.** Either cardboard (sky card, far strip, water strip) or a footage plate, never both fighting. Footage water strips cut from the stills' segmented planes live in `sets/water/` and are used as cardboard-style bands.
5. **At most one archive still, as an object in the world.** It is pinned to a notice board, hung as a frame on a wall, shown on a shopfront or TV: an ensemble's `archive` slot. It is hidden until its cue wipes it in. Scenes with no surface for it have none.
6. **Extras as a group in their own band, doing something.** Use a crowd ensemble (`ens.crowd.*`), placed behind the focal figure, never between it and the camera.
7. **Props only if the scene uses them, at real size.** Held props go in a hand or on their hook. Floor props stand on the floor line. Sky things (moon, sun) are screen-space `far` items, small and high, always behind the cast.
8. **Scale from the camera.** `scale.py` gives the shot size, camera height, horizon, floor line and px/cm. Every card has a real size in cm, and a thing at depth k is drawn at ppc/k on the floor line `horizon + (foot - horizon)/k`.
9. **Portals.** Windows, doors, arches and screens are holed cards (`hole` is measured from the card's alpha). What lies beyond stands behind the hole (`in_hole`), so a portal clip from `mech/` can replace it.
10. **Water.** The water is a band from the horizon to the shore line. Objects standing in or at the water carry a `reflect`: a flipped, faded copy hung under their floor line. Lamp and moon roads are streak cards in the water band.
11. **Timeline roles.** Each layer carries a `role`: `poet` (the poet's still pose), `action` (the hidden solved clip, at the poet's place and real size), `archive`, `ex`, `woman`, `father`, `prop`, `reflection` or `fx`. The poet's pose is ordered ahead of other characters' cards from poet sheets whenever the draw order allows it.
