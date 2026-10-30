#!/usr/bin/env python3
"""Write shots/suite/STAGED_01-07.md from the staged scene JSONs and their measured checks (stage lane 1).
Status, checks and joins are read from data/scenes/<id>.json; what's weak and what would help are authored below."""
import json, os, glob, subprocess
SUITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WEAK = {
 '01.1': ('POET and EX read well; the "TV" is a dark framed picture carrying archive; reading gesture is one held page.', 'CRT card with an open screen; head cards for "sad, reading".'),
 '01.2': ('EX is now outside the glass on a code-drawn landing; his retreat is small because the landing is shallow; the window never truly "slides away".', 'A bedroom plate with a real fire escape (lane C flags it); true dolly-zoom planes.'),
 '01.3': ('A 34 s fall on one aerial plate: bodies float, drop and roll, no streaking floors; the jointed tee tumbles stiff. Scale check has no standing frames (air).', 'POET falling/tumbling replacement bodies; a city-streak layer; escape-screen bezels.'),
 '01.4': ('"Needs a plate": a chapel with a giant drum stands in for the ballroom; figures only ~210 px, so the camera is zoomed 1.65-1.9x onto a floor strip. No hole in the floor.', 'A figure-free ballroom plate with parquet; floor-hole card; grey-painted party dancers.'),
 '02.1': ('Works as a void; arms-up scream is one held pose; rings are small code cards. Scale check has no standing frames (float).', 'Scream head card; ring prop cards.'),
 '02.2': ('The window stands in for the mirror (no mirror surface in this plate); he sits on the bed edge rather than tossing in bed.', 'A bedroom plate with a mirror; lying/tossing replacement bodies.'),
 '02.3': ('The pupil push-through is an iris to black, not an eye; POET just stands in the void with two wipes.', 'An eye-macro plate and a real pupil dissolve.'),
 '02.4': ('Lane C uses the high-rise bedroom as the 1990s living room; no car, no door-post height marks; both children wear a borrowed head.', 'A 1990s living-room plate, the driveway view, painted child and ghost heads.'),
 '02.5': ('Blind slats are code-drawn; the amber hazard light is a sweep; the boy barely moves.', 'Blind/curtain card rig; the driveway plate through the window.'),
 '02.6': ('Reads well: hand-off, wind-up, throw, cracks, black. Cracks are code lines, tambourine is a code card; the wind-up is one held arm.', 'Tambourine prop card; a pane-shatter card set.'),
 '03.1': ('No puppet (breakdown): the tambourine crosses a chapel dominated by the plate\'s giant drum. Checks have nothing to measure.', 'A figure-free chapel without the drum: choir stands, prayer lines.'),
 '03.2': ('2.8 s: tambourine enters and hangs; the time-lapse is a light sweep only.', 'Rose-window pass-through card; baptism-pool plate.'),
 '03.3': ('Decay is code cobwebs + darkening on one state of the chapel; the gift boxes are only archive.', 'Three time-lapse states of the chapel; gift-box cards.'),
 '03.4': ('Storm reads (flashes, rain, archive), but no gift/bread/string inserts; no puppet to measure.', 'Broken-gift, bread, marionette-string prop cards.'),
 '03.5': ('Good: two backs walking away; the footprints are small code marks and not read from the soles.', 'Footprint cards; a chapel-remnants plate (this plate\'s chapel is whole).'),
 '03.6': ('The shatter is code shards fading out; pieces do not remain for 04.', 'Tambourine pieces card set that stays on the shore.'),
 '04.1': ('Low camera (53 cm): POET must keep to a far shore strip; hands at the hips stand in for pockets; ravens are code silhouettes.', 'Hands-in-pockets torso/arm cards; raven cards; the hollow-chest card (04.1c).'),
 '04.2': ('Reads well; kneel is a deep squat; the heart is small and code-drawn; 31 s on one set is long for one gesture line.', 'Heart prop card with a beat cycle; kneeling replacement body.'),
 '04.3': ('Back-view walk into the field works; the puzzle pieces are only archive; no incline trail set.', 'Puzzle-piece cards; an incline-trail plate.'),
 '04.4': ('The plants do not actually turn; a glow stands in.', 'Plant/flower cards that turn their faces; weed cards.'),
 '04.5': ('Very dark by design; the hands on the ground are placeholder code cards.', 'Hand-on-ground cards; empty-sleeve arm cards (04.5c).'),
 '04.6': ('50 s on one set; the hands-back-on beat is a reach plus a code card riding up; the puppet shows his own hands throughout.', 'Handless forearm cards and hand-seating cards; a second field plate for the long reflection.'),
 '05.1': ('The parade reads, ancestors walk in and face POET; names on stars (05.1c) not staged; star is a code card.', 'Star prop cards and a name-typing fx; lantern cards.'),
 '05.2': ('"Needs a plate": a flooded underpass stands in for the basement; he sits, cannot lie; the mattress is a code slab.', 'A basement-bedroom plate with joists; lying replacement body; mattress card.'),
 '05.3': ('Works; the universe is a code orb; blessings on nodes are not staged.', 'Universe sphere card; web-of-light fx.'),
 '05.4': ('The chain of hands on shoulders works and is measured, but stays static for 32 s; the insert on the palm (05.4a) is not staged.', 'Palm-insert plate; fingerprint/vein light card; a second blocking for the middle.'),
 '05.5': ('"Needs a plate": a neon alley with a red door stands in for the winged marble gate; no words in this window.', 'A winged marble gate plate (the dossier names it; lane C has none).'),
 '06.1': ('The plate has no causeway: travellers walk on water; comet and soul-light are code cards.', 'A causeway plate; comet card; yellow-brick road.'),
 '06.2': ('The waterline does not actually fall (one plate); only the people move.', 'Two plates (flooded / risen) or a waterline wipe plate.'),
 '06.3': ('Queue and coin hand-offs work; the booth is implied, the door doubles as gate; crowd is shared-head citizens.', 'Booth card; lantern-window faces; painted citizen heads.'),
 '06.4': ('Walk and rainbow sweeps read; door panes are mostly hidden by the plate\'s dark foreground.', 'A real musician card; a narrow-street plate with a clear wall for the archive.'),
 '06.5': ('The reticle is a code overlay; lane C has no plaza plate, the waterfront stands in.', 'A plaza plate; a real scope-reticle card.'),
 '06.6': ('The final arms-up reads; the plate is the waterfront again; wandering to the house (06.6c-d) not staged.', 'A plaza plate and a house-exterior set.'),
 '07.1': ('DJ drops in small and far; no booth or decks in the plate.', 'A DJ booth card with decks; a bar card for POET.'),
 '07.2': ('Ghost EX reads as a translucent back; the vineyard is archive on the wall; guests only lean by a held hand.', 'A couch card; vineyard plate for the projection.'),
 '07.3': ('POET\'s walk and the parting crowd work (keep_distance); only two guests means no "packed" room.', 'More party guests / a crowd layer; ceiling LED stars plate.'),
 '07.4': ('Rings on the wall read; hands-apart gesture is two held arms.', 'Wedding-band cards; truck cards.'),
 '07.5': ('No daisy head is drawn: petals only; a lighter is only a glow.', 'Daisy prop card with separate petals; lighter card.'),
 '07.6': ('Three panels on the wall work; pointing is a held arm (the point hand card is not selected by this gesture).', 'A pointing arm pose; a stronger DJ headphone card.'),
 '07.7': ('Erupting room is three figures; strobe sells it more than the crowd.', 'A crowd layer of hands; phone/lighter cards.'),
}

def checks(d):
    c = d.get('checks') or {}
    items = c.get('items', [])
    fails = [i['id'] for i in items if not i['pass'] and not i.get('warnOnly')]
    warns = [i['id'] for i in items if not i['pass'] and i.get('warnOnly')]
    get = lambda k: next((i for i in items if i['id'] == k), {})
    return c, fails, warns, get

def main():
    rows, detail = [], []
    n = ok = 0; total = 0.0
    cast_n = 0
    for f in sorted(glob.glob(os.path.join(SUITE, 'data/scenes/0[1-7].*.json'))):
        if f.endswith('.words.json'): continue
        d = json.load(open(f)); sid = d['scene_id']; n += 1; total += d['duration']
        c, fails, warns, get = checks(d)
        cast = [x['id'] for x in d.get('cast', [])]; cast_n += bool(cast)
        passed = bool(c) and not fails
        ok += passed
        sc = get('scale_vs_set'); fs = get('foot_slide'); co = get('contact_error'); oc = get('occlusion'); gr = get('ground'); of = get('off_frame'); ws = get('word_sync')
        status = ('PASS' if passed else 'FAIL ' + ', '.join(fails)) if c else 'NOT RENDERED'
        if not cast: status += ' (no puppet: checks have no body to measure)' if passed else ''
        rows.append(f"| {sid} | {d.get('movement','')} | {d['duration']:.1f} | {', '.join(cast) or '—'} | {len(d['beats'])} / {len(d.get('joins', []))} | {status} |")
        joins = '; '.join(f"{j['kind']} on {j.get('surface') or 'stage'} @ {j.get('word_anchor') or round(j['t'],2)}: {j.get('archive','').split(' · ')[0]}" for j in d.get('joins', []))
        weak, asset = WEAK.get(sid, ('', ''))
        m = lambda it, k='value': ('—' if not it or it.get(k) is None else it[k])
        sc_per = sc.get('per', {}) if sc else {}
        detail.append(f"### {sid} · {d.get('movement','')} ({d['duration']:.1f} s, suite {d['audio']['suite_in']:.2f}–{d['audio']['suite_out']:.2f})\n"
                      f"- **Status:** {status}{'; warn: ' + ', '.join(warns) if warns else ''}. Set: {d.get('set')} (lane C {sid}).\n"
                      f"- **Checks:** foot slide {m(fs)} cm/f · reach {m(get('reach'))} · contact {m(co)} % · scale {m(sc)} % · occlusion {m(oc)} f · bodies {m(get('bodies'))} cm · ground {m(gr)} f · off-frame {m(of)} f · word sync {m(ws)} off.\n"
                      f"- **Joins:** {joins or 'none'}.\n"
                      f"- **Weak:** {weak}\n- **Would help:** {asset}\n")
    head = f"""# Staged scenes, poems 01–07 (stage lane 1)

{n} scenes, {total/60:.1f} minutes of reading, {ok} pass every hard check measured on the render. {n - cast_n} scenes have no puppet (the breakdown puts no body in them), so their checks have nothing to measure; say so rather than read those passes as evidence.

Every scene is built by `tools/stage_01_07.py` (compact spec) + `tools/stage_build.py` (windows, audio, walkable, archive strips, word anchors) and rendered by `node shots/suite/render.mjs <id>`.
Scene windows tile each poem's reading end to end (`tools/stage_windows.py`), so a poem's reel plays its reading through. Figure size always comes from lane C's horizon + px/cm: nothing is hand-scaled.

What the numbers do not say: `occlusion` is 0 by construction where lane C gives no footprint (it has none), so it only counts feet inside a footprint the scene authored; `off_frame` under-reads when no camera zoom is active (the mask is clipped to the frame); `scale_vs_set` skips air and sit frames, so a floating scene reports "no standing frames".

Reels: `renders/poem_NN.mp4` (`tools/stage_reels.py`).

New modules: `lib/set_patch.js` (scene-side walkable, marks, surface depths, plane re-seating), `lib/actions_extra.js` (drop, rise, float, tumble), `lib/fx_extra.js` (props that ride hands and fly; sweep, flash, rain, footprints, blinds, cracks, glow, iris, cobweb, stars, scatter, reticle), `lib/hands_extra.js` + `data/hand_cards.json` (replacement hand shapes).
Shared-file edits, all small: `index.html` (imports; applySetPatch after loadSet; applyExtras after compileScene; comp/set/cam on window.SUITE), `lib/adapters.js` (every lane-B character gets parts; pelvis/bridge cards; replacement hands), `lib/draw.js` (FX_EXTRA hook; lane-B pelvis card sized by its own px/cm), `lib/solver.js` (a held gesture is kept inside the arm), `lib/checks.js` (a vanished body re-plants where it reappears, so foot slide is not read across a vanish), `render.mjs` (protocolTimeout 30 min: long crowd scenes outlast the 3 min default).

## Scenes

| scene | movement | s | cast | beats / joins | status |
|---|---|---|---|---|---|
"""
    open(os.path.join(SUITE, 'STAGED_01-07.md'), 'w').write(head + '\n'.join(rows) + '\n\n## Per scene\n\n' + '\n'.join(detail))
    print(n, 'scenes', ok, 'pass', f'{total/60:.1f} min')

if __name__ == '__main__':
    main()
