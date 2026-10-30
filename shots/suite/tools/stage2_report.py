#!/usr/bin/env python3
"""Writes shots/suite/STAGED_08-14.md from the staged scene packs (their measured checks and joins) and the eye notes below."""
import os, json
H = os.path.dirname(os.path.abspath(__file__)); SUITE = os.path.dirname(H)
WIN = json.load(open(os.path.join(SUITE, 'data/scenes/stage2_windows.json')))
ARC = json.load(open(os.path.join(SUITE, 'data/archive/index.json')))
# scene: (what's weak, what asset would make it better)
EYE = {
 '08.1': ('A glass walkway, not a club: three dancer cards are a thin "crowded floor". The pane is small.', 'A rooftop-club plate with an empty floor; 6-8 more dancer cards; a back view of the jacket dancer.'),
 '08.2': ('The soul reads as a second POET, not as something leaving him; he does not rise.', 'A vellum soul card with a lift-off pose; a head-down body card.'),
 '08.3': ('"Strangers collide" is two cards walking together; the spark is only a strobe flash.', 'Paired dancer cards at the moment of contact.'),
 '08.4': ('Good read (the sun wipe works). The soul is small and only poses.', 'A heat-haze card over the plain.'),
 '08.5': ('Angels pour from their own card basins to the side; the water on his head comes from a hanging basin, so two pours do not line up.', 'An angel pour card aimed at the centre; a wet POET card (the dossier asks for one); the equator plate for this scene.'),
 '08.6': ('The return is a fade, not a merge; smoke is a code blur.', 'A real smoke plate layer; a lean-back POET card (card 10 stands in).'),
 '08.7': ('The street is a parked car and ad panels; no mountains except in the panel.', 'A street plate with mountains beyond it, as the line asks.'),
 '09.1': ('35 s on one set with a single static crowd; long holds between poses.', 'A cut to a second angle, or a moon card for this arcade; EX packing card in this set.'),
 '09.2': ('35 s, and MOTHER is a tiny jointed figure across a street instead of in her own room; no phone in either hand.', 'A mother_living_room plate (the dossier marks it needed) split-screen in a pane; a POET-on-the-phone card.'),
 '09.3': ('FATHER has one walk card, three-quarter front. The two overlap on screen at the end of the walk (depth is clear on the ground: no body overlap).', 'FATHER back/profile walk cards; a sunrise harbour plate.'),
 '09.4': ('Very small in frame, and FATHER walks away in a card that faces us (view_vs_travel warns). The plate has no quay near the camera.', 'A FATHER back-walk card; lane C\'s harbour plate with a walkable quay in the foreground.'),
 '10.1': ('The road is far from a 5.3 m camera: figures 135 px, plate soft at 2x push. The bike card and card 23\'s bike do not match in position at "hop on".', 'A closer sidewalk plate; POET rub/mount replacement cards with the bike separate.'),
 '10.2': ('Card 23 is POET walking beside the bike, so he never actually rides: it slides with a hop for 27 s, wheels still. The crowd is tiny and the sky wipe barely shows.', 'A jointed rider on the bike-kit parts (10.props.bike-*, already cut) and spinning wheel cards; a street plate with buildings.'),
 '10.3': ('Very large in frame (a 1 m camera and the only floor at the bottom); his feet read as standing on the far buildings.', 'A road-out-of-town plate with a farther floor.'),
 '10.4': ('No road in the plate: he stands on a dark slope on a flat ground plane, feet do not follow the slope.', 'A mountain-road plate with a measured camera (scale here is assumed).'),
 '10.5': ('Almost static: four poses in 12 s. Citizen disc floats in the forest.', 'A walking-on loop for the road; a nest or dawn card.'),
 '10.6': ('He walks beside the bike here too (card 23), though the line is "riding"; the bike crowds the two extras.', 'The jointed rider asked for in 10.2.'),
 '11.1': ('Quiet by design; pane in the chapel door is tiny.', 'A real fog plate layer.'),
 '11.2': ('Plate has no shore: he stands on a code deck strip; the deck reads as a band.', 'A shore foreground card painted for this plate; a flame prop for "diminishing flame".'),
 '11.3': ('"Rebuild" has no building in it: only a pointing pose. The clip in the colonnade is tiny.', 'Temple courses and columns already cut (11.props.temple.arrival.*) as stacking cards.'),
 '11.4': ('The camera looks down at the pool: only a kneeling figure fits, cropped close to the top-left.', 'A journal in his hands; an eye-level pool plate.'),
 '11.5': ('Reads well, but he walks on wet sand rather than water. Card 17 has hands above the head, so its alpha-based size makes the body a few % small.', 'A water-walk plate; body-based sizing for arms-up cards.'),
 '11.6': ('Same deck strip; five poses, no movement in 19 s.', 'A slow walk along the shore; more people from the poem\'s "together".'),
 '12.1': ('The hug is one arm from a jointed brother onto a card that cannot hug back; figures are small behind the plants (a 56 cm camera).', 'A paired hug card; a hall plate with a higher camera.'),
 '12.2': ('23 s; the walk deeper is the only event. Set is not a place for "football".', 'Group laughter cards; replacement mouths driven on the jointed friends.'),
 '12.3': ('Short and clear; the vellum elders are generic extras with no faces of their own.', 'Painted elder heads (lane B flags sixteen extras sharing one head).'),
 '12.4': ('Hourglass props are small at this depth, and POET holds an orb rather than an hourglass.', 'A POET card holding the hourglass.'),
 '12.5': ('No ball: the "football" is a lunge pose. They stand on the bottom step line, and the breakdown\'s parting is not staged.', 'A ball prop card; a kick pair.'),
 '13.1': ('A café made of cards on tidal flats under a storm: lane C marks this set "needs a plate". Table and POET do not share a real seat.', 'The harbour café plate the dossier asks for.'),
 '13.2': ('Couples hold and sway but do not orbit; the jointed arms are thin at this size.', 'A slow-dance pair card; an orbit goal (circle a shared point).'),
 '13.3': ('36 s on one quay, standing in a row; the fire is small and low beside a 700 px POET; the elders\' purple suits are not robes.', 'Three plates (pews, café at dusk, the fire), as the breakdown has; a burning-letters fire card; a kneeling elder group.'),
 '13.4': ('The field is pale canola, not scarlet poppies; figure stands over the flowers with no occlusion.', 'A poppy plate, or poppy cards in a near plane.'),
 '13.5': ('SHE is a small front-only card with no window and no wave: the moment the poem turns on is the weakest beat.', 'A distant-window set card (13.props.distant-window exists) with SHE in it; a working skirt rig or a wave card.'),
 '13.6': ('Same café; the smile is a raised hand, because there are no driven face cards.', 'Face plug-ins (lane A has mouths and eyes) on the POET cards.'),
 '14.1': ('The words the breakdown gives are not in the reading, so this is a held wide over the pause; the haze is a code blur.', 'Dissolve sheets from the plate\'s own layers (fall off plane by plane).'),
 '14.2': ('23 s of poses on the deck strip; the "from the ground up" dissolve is not built.', 'The same dissolve; POET dissolving card.'),
 '14.3': ('Fine and plain; the found clip is a strong image over a figure that is much smaller.', 'None needed.'),
 '14.4': ('Good TV joins; POET is small at the edge, b-roll extras are barely visible inside the screen.', 'A real reel: the motif montage (window, tambourine, field, stars) the breakdown lists, as a clip list.'),
 '14.5': ('"Entwined" is two cards side by side, swaying on a whole-card rotation.', 'A paired dance card of POET with his muse.'),
 '14.6': ('Reading gives 4 s of words; the rest is the walk. Guests stand outside the door because the opening is opaque, not in the party.', 'A vintage party plate through the door; a door-opening animation (14.props.door has the states).'),
}

def line(sid, c):
    bad = [k for k in c if isinstance(c[k], dict) and c[k].get('pass') is False]
    v = c.get('view_vs_travel', {})
    return ('PASS' if c.get('pass') else 'FAIL: ' + ', '.join(bad)), v.get('value')

out = ['# Staged: poems 08-14', '',
       'Poems 08 to 14 staged on lane C\'s sets, on the reading\'s clock. All numbers below are measured on the render by `lib/checks.js` (`node shots/suite/render.mjs <id>`) and stored in each `data/scenes/<id>.json`.',
       '', '## How it was built', '',
       '- **Windows on the reading:** `tools/stage2_windows.py` cuts each poem\'s reading into its scenes (word trigrams against the breakdown; hand-set starts for 09, 12, 14, where refrains or abridged lines fool the match). Windows tile the reading, so scenes play in **reading order**, which differs from the breakdown\'s numbering in 08 (08.2 is read first) and 12 (12.2 after 12.4). 14.1 has no words of its own and holds the pause between poems 13 and 14. The reading has "Even here is chilly in the morning" at the head of poem 11, so it sits in 11.1, not 10.6.',
       '- **Blocking:** `tools/stage2_specs.py` (one record per scene), compiled by `tools/stage2_stage.py`. Feet are placed on the ground; no figure is scaled by hand.',
       '- **POET** is played by his 30 painted replacement cards (`pose` beats on words, two stride cards), which answers the review note about segmented tracksuit limbs. **EX** uses back cards only. Angels and SHE use painted play cards because the stager does not draw skirt rigs. Everyone else is lane B jointed.',
       '- **Joins:** panes cut into real surfaces of the plate (railing glass, street ad panels, shop window, chapel door, hanging sheet, hall windows), found by `lib/archive_grab.py`, labelled ARCHIVE as long as they show. Screen, wipe and citizen joins elsewhere.',
       '- **Additions:** `lib/ext.js` (registry), `lib/stage2_extra.js` (actions pose, lean_back, nod, laugh, breathe; fx card, glow, smoke, pour, stars; join pane; held prop cards; cast.ghost; cast.play_key).',
       '',
       '## Limits of this pass', '',
       '- **Archive picks are weak in meaning.** Only 2,292 of the 15,149 clips are cached on this machine and no clip was downloaded, so many picks match by look, not subject (for example, "Moonwalk One" or "Friendship Seven" for skies; "Plant Solutions Video" for a family reunion). Titles are honest on screen, and each scene pack records the pick and its CLIP score. Re-picking by eye, or fetching the best clips, is the cheapest big improvement.',
       '- **The `off_frame` check cannot see a head cut by the frame top** when the camera is not zoomed: the mask canvas clips the silhouette first. Head room was worked out from each set\'s camera height and checked by eye on contact sheets, not by this check.',
       '- **`view_vs_travel` warnings** (warn-only) mostly come from POET\'s and FATHER\'s stride cards when they walk toward or away from the lens; no back stride card exists for either.',
       '- **Cards do not show head beats.** On a card puppet, wince, nod and head moves change nothing visible; POET acts only through card swaps.',
       '- **Set layers.** A plate plane has one depth, so planes can wrongly cover a figure. `set_layers` sends such planes behind the puppets per scene, which loses some true occlusion (the hall\'s planters).',
       '']
n = ok = 0
for p in sorted(WIN):
    bd = json.load(open(os.path.join(os.path.dirname(SUITE), f'poems/breakdown/{p}.json')))
    out += [f"## {p} · {bd['title']}", '', f"Reel: `renders/poem_{p}.mp4`", '',
            '| scene | s | status | foot slide cm/f | contact % | scale % | bodies cm | card/travel warn f | joins (ARCHIVE) |', '| :-- | --: | :-- | --: | --: | --: | --: | --: | :-- |']
    notes = []
    for s in sorted(WIN[p]['scenes'], key=lambda s: s['in']):
        d = json.load(open(os.path.join(SUITE, f"data/scenes/{s['id']}.json"))); c = d.get('checks', {})
        st, warn = line(s['id'], c); n += 1; ok += st == 'PASS'
        js = '; '.join(f"{j['kind']} {j.get('surface') or ''} {ARC.get(j['clip'], {}).get('title', j['clip'])}".replace('|', '/') for j in d['joins'])
        g = lambda k: c.get(k, {}).get('value')
        out.append(f"| {s['id']} {d['movement']} | {d['duration']:.1f} | {st} | {g('foot_slide')} | {g('contact_error') if g('contact_error') is not None else '–'} | {g('scale_vs_set')} | {g('bodies') if g('bodies') is not None else '–'} | {warn} | {js} |")
        w = EYE[s['id']]
        notes.append(f"- **{s['id']}** Weak: {w[0]} Would help: {w[1]}" + (f" Staging notes: {' '.join(d['notes'])}" if d.get('notes') else ''))
    out += [''] + notes + ['']
out.insert(2, f'**{ok} of {n} scenes pass every hard check.** Passing means the measurements hold (feet, scale, contact, overlaps, word sync); it does not mean the scene is good. The weak points below are from reading contact sheets.')
out.insert(3, '')
open(os.path.join(SUITE, 'STAGED_08-14.md'), 'w').write('\n'.join(out))
print(ok, 'of', n, 'pass')
