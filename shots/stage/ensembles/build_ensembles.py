"""The ensemble library: reusable, assembled set pieces with a real size, a depth band and slots for actors.

    python3 shots/stage/ensembles/build_ensembles.py      # writes ensembles/ens.*.json + index.json + sets/water/*.webp

Format (FORMATS.md section 2). Units are centimetres around the ensemble's anchor (floor-centre):
  x_cm  centre of the card, right positive          y_cm  bottom edge of the card above the floor (up positive)
  z_cm  depth behind the anchor (farther positive)  w_cm/h_cm  card size (h omitted = the card's own aspect)
Layer kinds (the stage resolves them through the scene's camera, scale.py):
  card               {part, x_cm, y_cm, z_cm, w_cm, h_cm}            a cut card standing in the set
  fill: sky          the backing from the frame top to the horizon
  fill: band         a far strip sitting on the horizon (h_px: it is at infinity, so the same size in every shot)
  fill: far          a far object in screen space (moon, crane on the far shore, a streak in the water)
  fill: water        water from the horizon down to the floor line at z_near (or the frame bottom)
  fill: floor        a floor from the floor line at z_far to z_near (or the frame bottom)
  fill: strip        a full-width card standing at depth z (walls, rails, kerbs), to_top stretches it up out of frame
  in_hole / on       portal content behind a card's opening (window, rose, door, arch) / painted onto a card (TV)
  reflect            a flipped, darkened copy hung under the card's floor line (water, wet stone, mirror floors)
Slots: actor | extras | prop | archive (one tagged still placed in the world) | portal (another world shows through).
"""
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import part, size, aspect, hole, STAGE, SHOTS

LIB = []


# ───────────────────────── layer helpers ─────────────────────────
def _src_or_part(ref):
    return {'src': ref, 'kind': 'plane'} if ref.startswith(('sets/', '../')) else {'part': part(ref)}


def C(ref, x=0, y=0, w=None, h=None, z=0, **kw):
    """A card standing in the set."""
    pid = part(ref)
    a = aspect(pid)
    if w is None and h is None:
        raise ValueError(ref)
    if w is None:
        w = h / a
    nat = h is None
    if h is None:
        h = w * a
    L = {'part': pid, 'x_cm': round(x, 1), 'y_cm': round(y, 1), 'z_cm': round(z, 1), 'w_cm': round(w, 1), 'h_cm': round(h, 1)}
    if not nat and abs(h / w - a) / a > .02:
        L['stretch'] = True
    L.update(kw)
    return L


def Sky(ref, **kw):
    return {'fill': 'sky', **_src_or_part(ref), **kw}


def Band(ref, h_px, y_px=0, w_px=1760, x_px=800, **kw):
    return {'fill': 'band', **_src_or_part(ref), 'h_px': h_px, 'y_px': y_px, 'w_px': w_px, 'x_px': x_px, **kw}


def Far(ref, x_px, y_px, h_px, order='band', **kw):
    """y_px: the card's centre relative to the horizon (negative = above it)."""
    return {'fill': 'far', **_src_or_part(ref), 'x_px': x_px, 'y_px': y_px, 'h_px': h_px, 'order': order, **kw}


def Water(ref, z_near=None, **kw):
    return {'fill': 'water', **_src_or_part(ref), 'z_near': z_near, **kw}


def Floor(ref, z_far, z_near=None, **kw):
    return {'fill': 'floor', **_src_or_part(ref), 'z_far': z_far, 'z_near': z_near, **kw}


def Strip(ref, z, h_cm, y_cm=0, to_top=False, w_px=1760, **kw):
    return {'fill': 'strip', **_src_or_part(ref), 'z_cm': z, 'h_cm': h_cm, 'y_cm': y_cm, 'to_top': to_top, 'w_px': w_px, **kw}


def In(holder, ref, rect=(-.06, -.06, 1.06, 1.06), **kw):
    """Portal content seen through the opening of the card named `holder` (rect in fractions of the opening)."""
    return {'in_hole': holder, **_src_or_part(ref), 'rect': list(rect), **kw}


def On(holder, ref, rect, **kw):
    """Painted onto the card named `holder` (rect in fractions of the card)."""
    return {'on': holder, **_src_or_part(ref), 'rect': list(rect), **kw}


def Slot(name, kind='actor', x=0, z=0, y=0, **kw):
    return {'name': name, 'kind': kind, 'x_cm': x, 'z_cm': z, 'y_cm': y, **kw}


def ens(id, name, poems, depth, layers, slots=(), sfx=(), notes='', reuse_note='', portals=()):
    xs = [L.get('x_cm', 0) + s * L['w_cm'] / 2 for L in layers if L.get('w_cm') for s in (-1, 1)]
    hs = [L['y_cm'] + L['h_cm'] for L in layers if 'h_cm' in L and 'y_cm' in L and 'part' in L]
    E = {'id': id, 'name': name, 'poems': poems, 'depth': depth, 'anchor': 'floor-centre',
         'size_cm': {'w': round(max(xs) - min(xs)) if xs else None, 'h': round(max(hs)) if hs else None},
         'layers': layers, 'slots': list(slots), 'portals': list(portals), 'mechs': [], 'sfx': list(sfx), 'notes': notes}
    LIB.append(E)
    return E


# ───────────────────────── water strips cut from the stills' segmented water planes ─────────────────────────
WATER = {   # name: (still/sheet, what it is)
    'sea_night': ('7a904269_0/S02_P2', 'open sea at night, long dark swell (7a904269 character plane)'),
    'sea_far': ('7a904269_0/S01_P5', 'the far sea band to the horizon (7a904269 distant plane)'),
    'lagoon_lights': ('fc83bfee_0/S07_P1', 'lagoon at night, scattered warm and blue lights in the ripples'),
    'canal_lamps': ('3238a164_1/S08_P2', 'canal at night, lamp streaks broken by ripples'),
    'night_reflections': ('62b9740c_1/S05_P1', 'black water with long lamp reflections'),
    'city_reflections': ('ba11d121_3/S03_P2', 'a city doubled in still black water, vertical light streaks'),
    'star_pool': ('f05c1fa5_1/S01_P2', 'a perfect reflecting pool holding a starry sky'),
    'red_beacons': ('18a6390f_0/S04_P1', 'night water with red beacon reflections'),
    'shallow_street': ('d3d25411_1/S09_P1', 'ankle-deep flood over a street, glints'),
}


def cut_water():
    out = os.path.join(STAGE, 'sets', 'water')
    os.makedirs(out, exist_ok=True)
    meta = {}
    for name, (sheet, what) in WATER.items():
        im = Image.open(os.path.join(SHOTS, 'world', sheet + '.webp')).convert('RGBA')
        a = np.array(im.getchannel('A')) > 128
        rows = np.nonzero(a.mean(1) > .9)[0]
        y0, y1 = int(rows[0]), int(rows[-1]) + 1
        cols = np.nonzero(a[y0:y1].mean(0) > .97)[0]
        x0, x1 = int(cols[0]), int(cols[-1]) + 1
        im.crop((x0, y0, x1, y1)).save(os.path.join(out, name + '.webp'), quality=88)
        meta[name] = {'file': f'sets/water/{name}.webp', 'from': f'../world/{sheet}.webp', 'what': what, 'size': [x1 - x0, y1 - y0]}
    json.dump(meta, open(os.path.join(out, 'index.json'), 'w'), indent=1)
    return meta


W = lambda n: f'sets/water/{n}.webp'


# ═════════════════════════ SKIES AND WATER (back band) ═════════════════════════
ens('ens.sky.harbour_night', 'the harbour at night: navy sky, moon, far shore of sheds with a crane and two masts, black water with lamp streaks',
    ['09', '13', '14'], 'back', [
        Sky('06.set.atlantis_plaza:sky-night-closing-in-around-the-city-outline'),
        Far('09.props.moon-sun:cream-disc-with-three-soft-grey-maria-and-fine-g', 1190, -150, 104, name='moon'),
        Band('09.set.atlantis_harbor_street:town-lamp-1-town-lamp-2-town-lamp-3-town', 70, y_px=3, w_px=820, x_px=420),
        Band('09.set.atlantis_harbor_street:a', 66, y_px=3, w_px=860, x_px=1220),
        Far('09.set.atlantis_harbor_street:town-lamp', 300, -52, 112, name='crane'),
        Far('09.set.atlantis_harbor_street:part-8', 1490, -55, 108),
        Water('09.set.atlantis_harbor_street:09-set-atlantis-harbor-street-all-working-parts-'),
        Far('09.props.moon-sun:road-straight', 1190, 70, 140, order='water', op=.55, blend='screen', name='moon road'),
        Far('09.props.moon-sun:reflections-streak-cards', 470, 34, 64, order='water', op=.75, blend='screen'),
        Far('09.props.moon-sun:four', 690, 34, 64, order='water', op=.7, blend='screen'),
        Far('09.props.moon-sun:harbor-lamp-separate-vertical', 905, 32, 60, order='water', op=.7, blend='screen'),
    ], notes='One tonal engine: the moon lays a road on the water. Pair with ens.harbour.quay (floor) or ens.phone_booth.quay.')

ens('ens.sky.harbour_dusk', 'the bay at dusk: rose sky, far shore with the white temple on its rise, low tide flats and the tide-line water',
    ['13', '14', '11'], 'back', [
        Sky('13.set.harbor_cafe:02-sky-dusk'),
        Band('13.set.harbor_cafe:04-far-shore-silhouette', 22, y_px=2),
        Far('13.set.harbor_cafe:o05-white-temple-on-rise', 1130, -20, 52, name='temple on its rise'),
        Water('13.set.harbor_cafe:08-tide-line-water-edge'),
        Far('13.set.harbor_cafe:09-reflection-strip-subdued-glints', 800, 46, 26, order='water', w_px=1760, op=.8),
    ], notes='Day version: swap the sky for 13.set.harbor_cafe 01-sky-day (scene override).')

ens('ens.sky.harbour_wide_atlantis', 'the harbour wide at dusk: Atlantis spires along the water, the white temple across, the pier arm, all flat bands',
    ['14', '06', '11', '12', '13'], 'back', [
        Sky('14.set.harbor_atlantis_wide:back-01-atlantis-skyline'),
        Far('14.set.harbor_atlantis_wide:part-2', 1290, -230, 70, name='crescent'),
        Band('14.set.harbor_atlantis_wide:mid-01-mid-02-mid-03-white-temple-pier-boat', 150, y_px=6),
        Water('14.set.harbor_atlantis_wide:floor-02-reflectio'),
        Far('14.set.harbor_atlantis_wide:floor-o1-water', 800, 60, 70, order='water', w_px=1760, op=.9),
    ])

ens('ens.sea.open_night', 'open sea at night: the stills\' black swell under a pale dusk-to-night sky, broken crests in three cut bands',
    ['04', '11', '13', '03'], 'back', [
        Sky('04.set.shore_night:sky-04-sky-pale-dusk-to-night'),
        Far('04.fx.moon-reach:7-reach1-small-reach2-small-medium', 1240, -170, 120, name='moon'),
        Band(W('sea_far'), 40, y_px=20),
        Water(W('sea_night')),
        Far('11.set.calm_sea:part-4', 800, 46, 40, order='water', w_px=1760, op=.75),
        Far('04.set.shore_night:2-04-wave-2-wavefront-mid', 520, 110, 46, order='water', w_px=760, op=.9),
        Far('04.set.shore_night:3-04-wave-3-wavefront', 1180, 150, 52, order='water', w_px=820, op=.9),
    ], notes='Footage water (7a904269 sea planes) under cardboard crest strips: the swell reads as card, the depth as film.')

ens('ens.sea.calm_dawn', 'the calm sea off the temple shore at dawn: pale bands, the ridge across the water, a disc of flat bright calm',
    ['11', '13', '12'], 'back', [
        Sky('11.set.calm_sea:poem-11-new-day-calm-sea-separate-layers'),
        Band('11.set.shore_decaying_chapel:ridge-shared-tree-covered-low-hill-ridge-reuse-i', 46, y_px=2),
        Water('11.set.calm_sea:from-11-set-calm-sea-travelling-calm-disc-separa'),
        Far('11.set.calm_sea:part-5', 800, 60, 46, order='water', w_px=1760, op=.85),
        Far('11.fx.fog-halo:halo-large-water-dashes-2-cards', 800, 130, 60, order='water', op=.8, name='calm disc'),
    ])

ens('ens.sky.dawn_shore', 'the shore under a pale cold morning: grey sky, tree-covered ridge, slate sea',
    ['10', '11', '03'], 'back', [
        Sky('11.set.shore_decaying_chapel:01-pale-cold-morning-sky-grey'),
        Band('11.set.shore_decaying_chapel:ridge-shared-tree-covered-low-hill-ridge-reuse-i', 60, y_px=2),
        Water('11.set.shore_decaying_chapel:calm-slate-blue-green-clean-horizon-hill-sky-ref'),
        Far('11.fx.fog-halo:fog-low', 520, -6, 40, op=.75),
    ])

ens('ens.sky.storm', 'storm over the beach: blue-black cloud field, lightning, floodwater',
    ['03'], 'back', [
        Sky('03.set.chapel_storm:cloud-field'),
        Far('03.fx.storm-light:2-center-branch', 1010, -150, 260, op=.9, blend='screen', name='lightning'),
        Far('03.fx.storm-light:1-left-branch-2', 380, -170, 210, op=.75, blend='screen'),
        Water('03.set.chapel_storm:03-floodwater'),
    ], sfx=['sfx.thunder', 'sfx.rain'])

ens('ens.sky.night_stars', 'a dense star sky over a dark field horizon',
    ['04', '05', '06'], 'back', [
        Sky('05.set.night_field_parade:sky-01-sky'),
        Far('04.fx.moon-reach:7-reach1-small-reach2-small-medium', 1230, -200, 110, name='moon'),
        Band('05.set.night_field_parade:horizon-on', 52, y_px=4),
    ])

# ═════════════════════════ THE HARBOUR (09 / 13 / 14) ═════════════════════════
ens('ens.harbour.quay', 'the inner harbour quay: wet stone paving to a lip over black water, two town lamps, bollards, a ladder down the wall',
    ['09', '13', '14'], 'mid', [
        Floor('09.set.harbor_path_east:left-top', z_far=0),
        Strip('09.set.harbor_path_east:part-8', 0, 16, y_cm=-12, name='quay lip'),
        C('09.set.atlantis_harbor_street:town-lamp-2', x=-430, z=-30, h=400, name='lamp L'),
        C('09.set.atlantis_harbor_street:b', x=470, z=-30, h=400, name='lamp R'),
        C('09.set.atlantis_harbor_street:rectangle', x=-170, z=-18, h=55),
        C('09.set.atlantis_harbor_street:bollard-b', x=700, z=-18, h=55),
        C('09.set.atlantis_harbor_street:part-13', x=170, z=1, y=-70, h=92, name='ladder'),
    ], slots=[Slot('walker', x=0, z=-160), Slot('companion', x=70, z=-150), Slot('extras', 'extras', x=-560, z=-60)],
    notes='Anchor = the quay lip at frame centre. The water and the far shore come from a back ensemble (ens.sky.harbour_night).')

ens('ens.harbour.quay_path_east', 'the quay path east at first light: stone kerb with a light strip, worn prints running to the harbour mouth',
    ['09', '11', '13'], 'mid', [
        Floor('09.set.harbor_path_east:left-top', z_far=0),
        Strip('09.set.harbor_path_east:x4', 0, 14, y_cm=-10, name='kerb light strip'),
        C('09.set.harbor_path_east:part-10', x=-60, z=-120, h=28, op=.75),
        C('09.set.harbor_path_east:part-11', x=40, z=-210, h=28, op=.75),
        C('09.set.harbor_path_east:white-gold', x=-30, z=-310, h=28, op=.75),
        C('09.set.atlantis_harbor_street:town-lamp-4', x=-520, z=-20, h=400),
    ], slots=[Slot('walker', x=0, z=-150), Slot('companion', x=80, z=-140)])

ens('ens.harbour.dawn_sky', 'the quay path sky re-banding from navy to apricot, the half sun at the harbour mouth',
    ['09', '11', '13'], 'back', [
        Sky('11.fx.light:ray-07'),
        Band('09.set.harbor_path_east:part-5', 90, y_px=4, op=.9),
        Far('09.props.moon-sun:sun-half-up-larger-half-disc-replacement', 1230, -16, 46, name='half sun'),
        Band('09.set.atlantis_harbor_street:a', 50, y_px=3, w_px=900, x_px=520),
        Water('11.set.shore_decaying_chapel:calm-slate-blue-green-clean-horizon-hill-sky-ref'),
        Far('09.set.harbor_path_east:reflection-white-gold-reflection-strip-separate-', 1230, 40, 50, order='water', w_px=420, op=.85, blend='screen'),
    ])

ens('ens.harbour.moored_boats', 'two small boats moored in the harbour, sails furled half up, their reflections broken in the water',
    ['13', '14', '09'], 'mid', [
        C('13.props.planet-boats:08c', x=-180, z=0, y=-60, w=420, op=.55, name='reflection A'),
        C('13.props.planet-boats:06c-mast-a', x=-180, z=1, y=60, h=430),
        C('13.props.planet-boats:06d-sail-a', x=-150, z=1, y=150, h=300),
        C('13.props.planet-boats:06a-hull-upright', x=-180, z=0, y=-10, w=420),
        C('13.props.planet-boats:08d', x=330, z=160, y=-60, w=380, op=.55),
        C('13.props.planet-boats:07c-mast-b', x=330, z=161, y=55, h=420),
        C('13.props.planet-boats:07d-sail-b', x=360, z=161, y=150, h=280),
        C('13.props.planet-boats:07a-hull-upright', x=330, z=160, y=-10, w=380),
    ], notes='Placed in the water beyond a quay lip (k larger than the quay\'s).')

ens('ens.phone_booth.quay', 'the lit phone booth on the quay: steel frame, glass, the warm roof light, a street lamp, the curb and two suitcases',
    ['09', '10'], 'mid', [
        C('09.props.phonebooth:back-with-payphone-body-no-handset', x=0, z=55, y=10, w=118, h=228, name='booth back'),
        C('09.props.phonebooth:cream-yellow', x=0, z=40, y=226, w=128, name='roof light'),
        C('09.props.phonebooth:steel-mullion', x=0, z=-5, y=8, w=152, h=246, name='booth frame', reflect={'op': .22}),
        C('09.props.phonebooth:front-glass-pane-clear', x=-36, z=-6, y=24, w=58, h=200, op=.28),
        C('09.set.atlantis_harbor_street:town-lamp-4', x=190, z=10, h=410, name='lamp', reflect={'op': .2}),
    ], slots=[Slot('caller', x=-5, z=25, y=10, facing='left', pose='stand', inside=True),
              Slot('waiting', x=-170, z=-70), Slot('cases', 'prop', x=-120, z=-90)],
    portals=[{'name': 'glass', 'kind': 'window', 'card': 'booth frame', 'note': 'the breakup can play as small back cards on the street plate behind'}],
    sfx=['sfx.phone.ring', 'sfx.rain'],
    notes='The caller stands between the back panel and the frame, so the steel mullions and the glass smear cross him.')

ens('ens.props.suitcases', 'two suitcases at the curb: a black hard case standing, a brown leather case lying',
    ['09'], 'front', [
        C('09.props.suitcases-notice:closed-card', x=-30, z=0, h=72),
        C('09.props.suitcases-notice:closed-card-2', x=45, z=-12, h=46),
    ])

ens('ens.quay.night_fire', 'the quay stones at night: a small fire of sticks where five letters burn, the pier with cold cyan lamps behind',
    ['13', '14'], 'mid', [
        Floor('13.set.harbor_quay_night_fire:13-set-harbor-quay-night-fire', z_far=0),
        Strip('13.set.harbor_quay_night_fire:l3-lamp-cyan1-cold-cyan-pier-lamp', 260, 110, y_cm=-20, name='pier'),
        C('13.set.harbor_quay_night_fire:l4-lamp-cyan2-cold-cyan-pier-lamp', x=-380, z=240, y=80, h=380),
        C('13.set.harbor_quay_night_fire:l3-l4-lamp-lamp-cyan1-cyan2-cold-cyan-cold-cyan-', x=420, z=240, y=80, h=360),
        C('13.props.five-letters:hinged-flame-13-22', x=0, z=-80, w=90, name='sticks'),
        C('13.props.five-letters:ash-13-23', x=-8, z=-81, y=8, h=58, name='flame', blend='screen'),
        C('13.props.five-letters:13-23', x=40, z=-95, w=34),
        C('13.props.five-letters:cluster', x=-55, z=-100, w=40),
    ], slots=[Slot('crouch', x=60, z=-60, pose='crouch'), Slot('fire', 'prop', x=0, z=-80)], sfx=['sfx.fire'])

ens('ens.cafe.awning', 'the corner café on the quay under its striped awning: teal facade with the bay window, a table with an espresso cup and two bentwood chairs',
    ['13', '14'], 'mid', [
        C('13.hero.cafe:q1-facade-teal-wall', x=0, z=120, w=640, name='facade'),
        In('facade', '13.set.harbor_cafe:01-sky-day', rect=(-.05, -.1, 1.05, .7)),
        In('facade', '13.set.harbor_cafe:08-tide-line-water-edge', rect=(-.05, .55, 1.05, 1.1)),
        C('13.hero.cafe:06-glass-reflection-film', x=-120, z=118, y=140, w=200, op=.25),
        C('13.props.rail-tide-awning:8-awning-fold-valance-flap', x=-40, z=60, y=250, w=520, name='awning'),
        C('13.fx.orbit-harvest:13-fx-orbit-harvest', x=-40, z=55, y=230, w=520, op=.9),
        C('13.props.rail-tide-awning:8-awning-fold-valance', x=300, z=110, y=110, w=90, name='NEXT GATES board'),
        C('13.props.cafe:b-table-with-cup', x=-60, z=0, w=170, name='table and chair'),
        C('13.props.cafe:d-final-empty-chair', x=150, z=-30, w=150),
    ], slots=[Slot('seated', x=-150, z=-10, pose='sit', facing='right'), Slot('couples', 'extras', x=250, z=40),
              Slot('archive', 'archive', on='facade', rect=[.62, .38, .86, .62])],
    portals=[{'name': 'bay window', 'kind': 'window', 'card': 'facade', 'shows': 'the bay by day'}],
    sfx=['sfx.cafe.cups'])

ens('ens.street.club_sidewalk', 'the wet club sidewalk: shopfronts with painted neon, doors in teal and red, wires overhead, gloss floor',
    ['09', '08', '10'], 'mid', [
        Strip('09.set.atlantis_club_sidewalk:01-night-sky-teal-grey', 500, 900, y_cm=150, to_top=True),
        C('09.set.atlantis_club_sidewalk:04-shopfront-a-teal', x=-560, z=120, h=330),
        C('09.set.atlantis_club_sidewalk:05-shopfront-b', x=-60, z=120, h=330),
        C('09.set.atlantis_club_sidewalk:06-shopfront-c', x=420, z=120, h=330, name='shopfront C'),
        C('09.set.atlantis_club_sidewalk:red', x=-60, z=118, h=215, name='pink door'),
        C('09.set.atlantis_club_sidewalk:part-2', x=-300, z=100, y=330, w=500),
        Floor('05.hero.perimeter:floor-wet-floor-no', z_far=120),
        C('09.hero.canopy:q-reflection-strip-right', x=0, z=118, y=-2, w=700, h=40, op=.5, blend='screen'),
    ], slots=[Slot('ex', x=-40, z=80), Slot('crowd', 'extras', x=300, z=40), Slot('poet', x=-300, z=-80),
              Slot('archive', 'archive', on='shopfront C', rect=[.2, .4, .46, .7])])

ens('ens.props.notice_board', 'the harbour notice board on its post: chalk board, the next-gate time chalked on a strip',
    ['09', '13'], 'mid', [
        C('09.props.suitcases-notice:post', x=0, z=2, h=170),
        C('09.props.suitcases-notice:chalk-overlay-with-chalk-overlay', x=0, z=0, y=95, w=96, name='board'),
        C('09.props.suitcases-notice:chalk-overlay-1-with-time', x=0, z=-1, y=78, w=74),
    ], slots=[Slot('archive', 'archive', on='board', rect=[.12, .14, .88, .8])],
    notes='The one archive still of a quay scene is pinned to this board, so it is an object in the world.')

# ═════════════════════════ INTERIORS ═════════════════════════
ens('ens.room.living_1990s', 'the 1990s front room in winter: floral wallpaper wall with the big window (curtains, rod), sofa, standard lamp, the door post with the pencil height marks',
    ['02', '09', '13'], 'mid', [
        Strip('02.set.living_room_1990s:01-window-wall', 260, 260, to_top=True, w_px=None, name='window wall', w_cm=620),
        In('window wall', '02.set.overseer_skyline:01-gradient', rect=(-.1, -.1, 1.1, .8)),
        In('window wall', '02.set.overseer_skyline:left-slab-tower', rect=(.04, .02, .3, .9)),
        In('window wall', '02.set.overseer_skyline:03-right-slab-tower', rect=(.7, 0, .96, .9)),
        In('window wall', '04.fx.moon-reach:7-reach1-small-reach2-small-medium', rect=(.44, .1, .56, .32)),
        In('window wall', '02.set.overseer_skyline:06', rect=(-.05, .62, 1.05, .9)),
        In('window wall', '02.set.overseer_skyline:road-wet-road-backing', rect=(-.05, .82, 1.05, 1.08)),
        On('window wall', '02.props.window:curtain-rod-2', rect=(.2, .12, .82, .2)),
        On('window wall', '02.set.living_room_1990s:05-curtain-l', rect=(.19, .14, .34, .72)),
        On('window wall', '02.set.living_room_1990s:07-curtain-r', rect=(.68, .14, .83, .72)),
        Floor('02.set.living_room_1990s:10-floor', z_far=260),
        C('02.set.living_room_1990s:doorpost', x=-300, z=250, h=215, name='height marks door post'),
        C('02.props.blinds-height:n2-n3-n4-ns-n6-six-seven-n7', x=-300, z=248, y=60, h=110, op=.9),
        C('02.set.living_room_1990s:04-sofa', x=160, z=160, w=230),
        C('02.set.living_room_1990s:lamp-base', x=330, z=200, h=150, name='lamp'),
        C('02.set.living_room_1990s:03-doorpost', x=330, z=199, y=140, w=55, name='lamp shade'),
    ], slots=[Slot('child', x=-40, z=60, facing='away', pose='stand'), Slot('ghost', x=-110, z=70),
              Slot('archive', 'archive', on='window wall', rect=[.86, .3, .98, .5])],
    portals=[{'name': 'front window', 'kind': 'window', 'card': 'window wall', 'shows': 'the rowhouse street, palace and towers under the moon'}],
    notes='The window is a hole in the wallpaper card: the night street stands behind it, so it can be swapped for a portal clip.')

ens('ens.room.mother', "mother's living room: the wall with the big window onto the harbour sidewalk, curtains, the floral armchair, side table with the corded phone, a warm lamp",
    ['09', '02'], 'mid', [
        Strip('09.set.mother_living_room:back-wall-with-window-opening', 240, 265, to_top=True, w_px=None, w_cm=560, name='window wall'),
        In('window wall', '06.set.atlantis_plaza:sky-night-closing-in-around-the-city-outline', rect=(-.1, -.1, 1.1, .7)),
        In('window wall', '09.set.atlantis_harbor_street:town-lamp-1-town-lamp-2-town-lamp-3-town', rect=(-.05, .42, 1.05, .66)),
        In('window wall', '09.set.atlantis_harbor_street:09-set-atlantis-harbor-street-all-working-parts-', rect=(-.05, .62, 1.05, .84)),
        In('window wall', '09.set.harbor_path_east:left-top', rect=(-.05, .8, 1.05, 1.1)),
        In('window wall', '09.props.phonebooth:09-props-phonebooth', rect=(.58, .52, .8, .94), name='booth in the window'),
        On('window wall', '09.set.mother_living_room:left-curtain', rect=(.13, .1, .28, .78)),
        On('window wall', '09.set.mother_living_room:right-curtain', rect=(.72, .1, .87, .78)),
        C('09.set.mother_living_room:with-corner', x=-330, z=120, h=290),
        C('09.set.mother_living_room:with-corner-2', x=330, z=120, h=290),
        Floor('02.set.living_room_1990s:10-floor', z_far=240),
        C('09.props.phones-chair:armchair-body-floral-fabric-cream-one', x=-150, z=90, h=95, name='armchair'),
        C('09.props.phones-chair:side-table-wood', x=0, z=100, h=62, name='side table'),
        C('09.props.phones-chair:phone-base', x=0, z=99, y=60, w=28, name='corded phone'),
        C('09.set.mother_living_room:lamp-base', x=150, z=130, h=130),
        C('09.set.mother_living_room:lamp-shade-light-warm', x=150, z=129, y=122, w=56, name='lamp shade'),
    ], slots=[Slot('seated', x=-150, z=80, pose='sit'), Slot('archive', 'archive', on='window wall', rect=[.88, .26, .97, .42])],
    portals=[{'name': 'the window', 'kind': 'window', 'card': 'window wall', 'shows': 'the harbour sidewalk and the lit booth, where the breakup keeps playing'}],
    sfx=['sfx.phone.ring'])

ens('ens.room.bedroom_highrise', 'the high-rise bedroom: rear wall with the hallway opening and the window onto the fire escape, broken board floor, the dresser, the TV low on the right',
    ['01', '02'], 'mid', [
        Strip('01.hero.severn:02-room-wall-bedroom-rear-wall-hallway-opening-a', 300, 270, to_top=True, w_px=None, w_cm=640, name='rear wall'),
        In('rear wall', '01.hero.severn:15-sky-night-sky-backing', rect=(-.1, -.1, 1.1, 1.1)),
        In('rear wall', '01.hero.severn:14-skyline-distant-tower-strip', rect=(-.1, .45, 1.1, 1.0)),
        Floor('01.hero.severn:03-floor-dark-broken-board-floor', z_far=300),
        C('01.hero.severn:04-hall-1-corridor-frame-1-largest-opening', x=-170, z=310, h=200, op=.95),
        C('01.props.room:dresser-closed', x=-250, z=170, h=88, name='dresser'),
        C('01.props.room:tv-with-screen-static', x=250, z=120, h=62, name='tv'),
        C('01.props.room:television-pedestal-stand-2', x=250, z=121, w=110, y=-4),
    ], slots=[Slot('reader', x=-120, z=-40, pose='stand'), Slot('archive', 'archive', on='tv', rect=[.06, .06, .94, .7])],
    portals=[{'name': 'window', 'kind': 'window', 'card': 'rear wall', 'shows': 'the fire escape and the city falling away'},
             {'name': 'tv', 'kind': 'tv', 'card': 'tv'}])

ens('ens.fire_escape.night', 'the fire escape outside the window: steel landing and rail, the switchback stair, planters, the light-well walls, the city below',
    ['01'], 'mid', [
        Sky('01.hero.severn:15-sky-night-sky-backing'),
        Band('01.hero.severn:14-skyline-distant-tower-strip', 120, y_px=8),
        C('01.hero.severnescape:left-lightwell-wall', x=-420, z=200, y=-500, h=1100),
        C('01.hero.severnescape:right-lightwell-wall', x=430, z=200, y=-500, h=1100),
        C('01.hero.severn:11-escape-steel-switchback-fire-escape', x=260, z=120, y=-160, h=420),
        C('01.hero.severnescape:planter-o1', x=-150, z=10, y=0, h=55),
        C('01.hero.severnescape:planter-o4', x=180, z=10, y=0, h=60),
        Floor('01.props.window:fire-escape-landing-floor', z_far=40, z_near=-90),
        Strip('01.props.window:fire-escape-rail', -60, 100, y_cm=0, w_px=None, w_cm=460, name='rail'),
    ], slots=[Slot('at rail', x=0, z=-20), Slot('ex', x=120, z=0)])

ens('ens.room.vintage_party', 'the old-time party room: damask wallpaper with a dark shut window, panelled door frame, warm parquet, a paper-lantern garland, the gramophone on its side table',
    ['01', '14'], 'mid', [
        Strip('14.set.vintage_party:front-interior-door', 300, 270, to_top=True, w_px=None, w_cm=760, name='party wall'),
        In('party wall', '14.props.party:a-window-assembled'),
        Strip('14.set.vintage_party:front-interior-door-frame', 290, 40, y_cm=270, w_px=None, w_cm=780, name='cornice'),
        Floor('14.set.vintage_party:mid-separate-slow-dancing-puppet-slots-garland-s', z_far=300),
        C('14.set.vintage_party:front-interior-door-frame-2', x=-330, z=295, h=250, name='door frame'),
        C('14.props.party:b-garland-assembled', x=-100, z=150, y=215, w=420, name='garland'),
        C('14.props.party:b-garland-assembled', x=300, z=200, y=225, w=380),
        C('14.props.party:base', x=330, z=130, h=72, name='side table'),
        C('14.props.party:assembled-d-coupes', x=330, z=129, y=70, h=62, name='gramophone'),
        C('01.props.chandeliers:only', x=40, z=200, y=170, h=110),
    ], slots=[Slot('poet', x=-60, z=0), Slot('couples', 'extras', x=0, z=110),
              Slot('archive', 'archive', on='party wall', rect=[.62, .2, .74, .44])],
    portals=[{'name': 'shut window', 'kind': 'window', 'card': 'party wall'}, {'name': 'door', 'kind': 'door', 'card': 'door frame'}],
    sfx=['sfx.gramophone'])

ens('ens.room.container_party', 'the container-built living room: corrugated teal and rust walls, the dark ceiling with LED star holes, magenta and cyan neon strips, haze',
    ['07', '06', '14'], 'mid', [
        Strip('07.hero.house:a2-back-wall-panel-corrugated-container-wall-tea', 360, 280, to_top=True, w_px=None, w_cm=520, x_cm=-300, name='back wall L'),
        Strip('07.hero.house:rusted-container-wall-with-picture-slot-empty', 360, 280, to_top=True, w_px=None, w_cm=560, x_cm=240, name='back wall R'),
        Strip('07.hero.house:b1-ceiling-panel-dark-ceiling-with-holes-12-for-', 300, 90, y_cm=270, w_px=None, w_cm=900, name='ceiling'),
        Floor('08.hero.marquee.interior:lobby-floor-2-corridor', z_far=360),
        C('07.hero.house.furniture:cyan-light-strip-narrow', x=-300, z=355, y=230, w=480, blend='screen'),
        C('07.hero.house.furniture:plinth-l', x=240, z=355, y=20, w=480),
        C('07.fx.party-haze:drifting-haze-band-a', x=-200, z=100, y=120, w=520, op=.35, blend='screen'),
    ], slots=[Slot('crowd', 'extras', x=0, z=120), Slot('archive', 'archive', on='back wall R', rect=[.3, .3, .72, .62])],
    sfx=['sfx.party.room'])

ens('ens.dj_booth', 'the DJ booth on its raised landing: riser with rusted side panels, the booth front with the controller, two tall speakers, the projection wall behind',
    ['07'], 'mid', [
        C('07.props.projection:part-2', x=0, z=120, y=110, w=420, name='projection wall'),
        On('projection wall', '07.props.projection:vineyard', rect=(.12, .12, .88, .86), name='projection'),
        C('07.hero.house.furniture:riser-top', x=0, z=40, y=48, w=380),
        C('07.hero.house.furniture:side-panel-l', x=-150, z=20, w=150),
        C('07.hero.house.furniture:riser-side-panel-r', x=150, z=20, w=150),
        C('07.props.speakers-vu:panel-perforated', x=-250, z=30, y=0, h=170, name='speaker L'),
        C('07.props.speakers-vu:panel-perforated', x=250, z=30, y=0, h=170, flip=True, name='speaker R'),
        C('07.props.dj-decks:dj-booth-front-view-controller', x=0, z=0, y=108, w=120, name='decks'),
        C('07.hero.house.furniture:dj-booth-front', x=0, z=-5, y=60, w=240, name='booth front'),
    ], slots=[Slot('dj', x=0, z=15, y=60, pose='stand'), Slot('archive', 'archive', on='projection wall', rect=[.12, .12, .88, .86])],
    portals=[{'name': 'projection', 'kind': 'screen', 'card': 'projection wall', 'shows': 'vineyard / rings / trucked house / three roads'}],
    sfx=['sfx.vinyl.scratch'])

ens('ens.bar.home', 'the long dark-wood home bar with the magenta underlight, bottles on the counter, the mic stand',
    ['07'], 'mid', [
        C('07.props.bar-handheld:bar-assembly-magenta', x=0, z=0, w=300, name='bar'),
        C('07.props.bar-handheld:bottle-01', x=-90, z=5, y=108, h=30),
        C('07.props.bar-handheld:bottle-04', x=-60, z=5, y=108, h=24),
        C('07.props.bar-handheld:bottle-05', x=95, z=5, y=108, h=30),
    ], slots=[Slot('at bar', x=40, z=-50), Slot('mic', 'prop', x=60, z=-60)])

ens('ens.chapel.nave', 'the chapel nave, decorated: the rose-window end wall over the choir stands, the dry baptism pool, aged pews, cobwebs, the gifts left on the step, a shaft of light',
    ['03', '13'], 'mid', [
        Strip('03.hero.chapel:interior-end-wall-with-rose-window-companions-an', 520, 520, y_cm=-20, to_top=True, w_px=None, w_cm=900, name='end wall'),
        In('end wall', '13.set.church_pews:13-01-sky-night-night-backing-for-windows'),
        In('end wall', '03.props.rose-window:d-centre-glass-disc-tinted-acetate-glass', rect=(.15, .15, .85, .85), op=.85),
        On('end wall', '03.props.rose-window:frame-12-petal-openings', rect=(.415, .2, .585, .455), name='rose window'),
        Floor('03.hero.chapel:1-floor-floor-with-baptism-pool-aperture-nave-st', z_far=520),
        C('03.hero.chapel:03-09-choir-2-choir-stand-step-centre', x=0, z=470, w=420),
        C('03.hero.chapel:03-08-choir-1-choir-left', x=-430, z=440, w=380),
        C('03.hero.chapel:03-10-choir-3-right-choir-stand-step', x=430, z=440, w=380),
        C('03.props.gifts-bread-cups:box-1-body', x=-120, z=455, y=40, w=60),
        C('03.props.gifts-bread-cups:fresh-bread-cup-1-body', x=-60, z=455, y=40, w=40),
        C('03.props.gifts-bread-cups:cup-2-body', x=110, z=455, y=40, w=22),
        C('03.hero.chapel:03-13-baptism-pool-rim', x=0, z=260, w=200, name='pool rim'),
        C('03.hero.chapel.interior-states:pew-2-aged-pane-pew-with-and-kneeler-missing-gla', x=-300, z=180, w=300),
        C('03.hero.chapel.interior-states:pew-2-aged-pane-pew-with-and-kneeler-missing-gla', x=300, z=180, w=300, flip=True),
        C('03.hero.chapel.interior-states:aged-near-pew-back-worn-splintering', x=-380, z=40, w=240),
        C('03.hero.chapel.interior-states:aged-near-pew-back-worn-splintering', x=380, z=40, w=240, flip=True),
        C('03.props.cobwebs:7-near-full', x=-560, z=200, y=200, w=110, op=.85),
        C('03.props.cobwebs:a8', x=560, z=200, y=210, w=110, op=.85, flip=True),
        C('03.fx.storm-light:1-dawn-warm', x=170, z=300, y=0, w=110, h=480, op=.35, blend='screen', rot=-14, name='light shaft'),
    ], slots=[Slot('aisle', x=0, z=120), Slot('archive', 'archive', on='end wall', rect=[.07, .52, .2, .7])],
    portals=[{'name': 'rose window', 'kind': 'window', 'card': 'end wall', 'shows': 'night sky; the tambourine comes through it from 02'}],
    sfx=['sfx.chapel.room'])

ens('ens.chapel.side_doors', 'the chapel side doors: a stone arch with two dark leaves ajar, the wet doorstep, three white gift boxes with their lids off',
    ['03'], 'mid', [
        C('03.set.chapel_side_doors:stone-wall-with-arched-double-door-aperture', x=0, z=60, w=560, name='arch wall'),
        In('arch wall', '02.set.black_void:poem-02-black'),
        C('03.set.chapel_side_doors:left-door-leaf-hinge-edge', x=-120, z=58, y=0, h=280, name='left leaf'),
        C('03.set.chapel_side_doors:right-door-leaf-hinge-edge', x=140, z=58, y=0, h=280, rot=4),
        Strip('03.set.chapel_side_doors:stone-doorstep-wet-dark-light-supplied-separatel', 20, 30, y_cm=-10, w_px=None, w_cm=700, name='step'),
        C('03.props.gifts-bread-cups:box-1-body', x=-110, z=0, y=20, w=62),
        C('03.props.gifts-bread-cups:box-1-light', x=-110, z=1, y=48, w=50, op=.8, blend='screen'),
        C('03.props.gifts-bread-cups:box-2-body', x=10, z=-10, y=20, w=58),
        C('03.props.gifts-bread-cups:box-2-inner-light', x=10, z=-9, y=46, w=46, op=.8, blend='screen'),
        C('03.props.gifts-bread-cups:box-1-lid', x=120, z=-20, y=18, w=62, rot=-8),
    ], slots=[Slot('archive', 'archive', on='arch wall', rect=[.36, .3, .64, .62])],
    portals=[{'name': 'doorway', 'kind': 'door', 'card': 'arch wall'}])

ens('ens.chapel.exterior', 'the chapel small on the flat beach: facade, slate roof planes, the bell tower',
    ['03', '10', '11'], 'mid', [
        C('03.hero.chapel:roof-l-left-roof-plane-slate', x=-120, z=20, y=430, w=520),
        C('03.hero.chapel:roof-r-right-roof-plane-slate', x=260, z=20, y=430, w=520),
        C('03.hero.chapel:03-04-tower-base-square-bell-tower-shaft', x=330, z=10, y=0, h=900),
        C('03.hero.chapel:03-05-tower-cap-bell-tower-roof-top', x=330, z=10, y=880, w=300),
        C('03.hero.chapel:front-front-facade-with-arched-doorway', x=-100, z=0, h=700, name='facade'),
    ])

ens('ens.shore.remnants', 'chapel remnants on the mud shore: the ruined west wall and side wall, the floor with the pool that did not drain, stones in the wet sand',
    ['03', '04', '10', '11'], 'mid', [
        Floor('03.set.remnants_shore:mud-dark-wet-sand-mud-shore-dark-tone', z_far=500, z_near=200),
        Floor('03.set.remnants_shore:mud-mid-wet-sand-mud-shore-mid-tone', z_far=200, z_near=0),
        Floor('03.set.remnants_shore:mud-light-wet-sand-mud-shore-light-tone', z_far=0),
        C('03.hero.chapel.ruin:03-14-west-wall-ruined-end-wall-with-partial-win', x=-260, z=420, h=520, name='west wall'),
        C('03.hero.chapel.ruin:03-06-side-l-left-side-wall-ruined-three-lancets', x=330, z=360, w=900),
        C('03.hero.chapel.ruin:03-11-floor-empty-ruined-floor-with-pool-apertur', x=0, z=200, w=640),
        C('03.set.remnants_shore:pool-water-pale-blue-green-water-plate-blank', x=0, z=199, y=6, w=300, h=40, op=.85),
        C('11.props.ruin:sto', x=-420, z=60, h=60),
        C('11.props.ruin:part-9', x=470, z=20, h=55),
    ], slots=[Slot('walker', x=0, z=80), Slot('prints', 'prop', x=120, z=40)])

ens('ens.shore.steps_lanterns', 'the wet stone steps from the old station down to the water: two landings, the shore wall, lanterns on the landings',
    ['04', '11'], 'mid', [
        C('11.hero.steps:wall-left-shore-wall-left', x=-380, z=60, h=330),
        C('11.hero.steps:landing-o1-stone-landing-upper', x=-200, z=40, y=180, w=420),
        C('11.hero.steps:stair-tread', x=-60, z=30, y=140, w=210),
        C('11.hero.steps:tread-o3-stair-tread', x=-30, z=20, y=100, w=210),
        C('11.hero.steps:stair-tread-2', x=0, z=10, y=60, w=205),
        C('11.hero.steps:landing-o2-stone-landing-lower', x=60, z=0, y=0, w=420, h=70),
        C('11.props.inlays-lantern:lantern-lit-faint-glow-warm', x=-300, z=38, y=200, h=60, name='upper lantern'),
        C('11.props.inlays-lantern:lantern-lit-faint-glow-warm', x=230, z=-2, y=60, h=55, name='lower lantern'),
    ], slots=[Slot('on steps', x=-20, z=5, y=70)], sfx=['sfx.sea.lap'])

ens('ens.shoreline.waves', 'the night shoreline: three wave fronts folding in, foam lines, wet ash over sand, charred stumps',
    ['04', '03', '11'], 'mid', [
        C('04.set.shore_night:wave-1-04-wave-1-wavefront-outer', x=-250, z=600, y=-10, w=900),
        C('04.set.shore_night:2-04-wave-2-wavefront-mid', x=300, z=420, y=-10, w=800),
        C('08.fx.soul-weather:wet-highlight-overlays-3-2', x=-100, z=300, y=-6, w=700, op=.7, name='foam'),
        C('04.set.shore_night:3-04-wave-3-wavefront', x=0, z=280, y=-12, w=760),
        Floor('04.set.shore_night:ash-dark-ash-sand-dark-04-set-shore-night', z_far=270, z_near=80),
        Floor('04.set.shore_night:ash-mid-ash-sand-mid', z_far=80),
        C('04.set.shore_night:stump-2-04-stump-2-charred-stump', x=-520, z=120, h=110),
        C('04.set.shore_night:tree-2-04-tree-2-still-tree', x=620, z=320, h=330),
    ], slots=[Slot('walker', x=0, z=40), Slot('heart', 'prop', x=60, z=-40)], sfx=['sfx.sea.waves'])

ens('ens.pool.infinity', "the temple's edgeless pool between white walls: niche wall, the pool lip, the surface an exact mirror of sky and wall",
    ['11', '12'], 'mid', [
        Sky('11.set.temple_infinity_pool:sky-01-clean-pale-blue-sky'),
        Far('11.set.temple_infinity_pool:long-low-cloud-streak', 520, -120, 40),
        Strip('11.set.temple_infinity_pool:01-temple-niche', 500, 300, y_cm=0, name='niche wall'),
        Floor('11.set.temple_infinity_pool:01', z_far=500, z_near=60, name='pool'),
        Strip('11.set.temple_infinity_pool:reflection-of-wall', 470, 200, y_cm=-200, op=.55, name='wall reflection'),
        Strip('11.set.temple_infinity_pool:mirror-sky', 300, 90, y_cm=-140, op=.5),
        Strip('11.set.temple_infinity_pool:pool-lip-strip-note-sea-side-edge-has-layer-card', 60, 20, y_cm=-10, name='lip'),
        Floor('11.hero.pools:lip-land-pool-lip-chalk-white-with-seam-cyan', z_far=59),
    ], slots=[Slot('seated at lip', x=-60, z=50, pose='sit', reflect=True), Slot('archive', 'archive', on='niche wall', rect=[.46, .2, .54, .7])])

ens('ens.mirror_hall', 'the mirror hall: white piers in two rows standing in black still water, every pier doubled, the far arch open onto distant lights',
    ['11', '12'], 'mid', [
        Strip('11.set.mirror_hall:06-07-r2-08-l3-09-r3-rear-left-pier-rear-right-p', 900, 380, y_cm=0, to_top=True, name='rear wall'),
        C('11.set.mirror_hall:right-pi', x=0, z=880, h=330, name='far arch'),
        Floor('11.set.mirror_hall:11-set-mirror-hall-same-hall-poem12-flip-dark-mi', z_far=900),
        C('11.set.mirror_hall:14-ml3-mirror-flip-vertically-source', x=-330, z=600, h=420, reflect={'op': .4}),
        C('11.set.mirror_hall:15-mr3-mirror-flip-vertically-source', x=330, z=600, h=420, reflect={'op': .4}),
        C('11.set.mirror_hall:12-ml2-mirror-flip-vertically-source', x=-360, z=330, h=420, reflect={'op': .4}),
        C('11.set.mirror_hall:13-mr2-mirror-flip-vertically-source', x=360, z=330, h=420, reflect={'op': .4}),
        C('11.set.mirror_hall:10-ml1-mirror-flip-vertically-source', x=-400, z=60, h=420, reflect={'op': .4}),
        C('11.set.mirror_hall:11-mr1-mirror-flip-vertically-source', x=400, z=60, h=420, reflect={'op': .4}),
    ], slots=[Slot('at edge', x=0, z=150, reflect=True), Slot('archive', 'archive', on='far arch', rect=[.2, .25, .8, .85])],
    portals=[{'name': 'far arch', 'kind': 'arch', 'card': 'far arch', 'shows': 'distant lights over water'}])

ens('ens.temple.hall', "inside the temple: the bone-white niche wall, three pairs of piers stepping toward camera, long dark-wood benches, the black gloss floor doubling everyone",
    ['12', '11', '13', '14'], 'mid', [
        Strip('12.set.temple_hall:01-sky-13-vault', 700, 330, y_cm=0, to_top=True, name='niche wall'),
        Floor('11.set.mirror_hall:11-set-mirror-hall-same-hall-poem12-flip-dark-mi', z_far=700),
        C('12.set.temple_hall:07-l3', x=-330, z=520, h=360, reflect={'op': .35}),
        C('12.set.temple_hall:08-r3', x=330, z=520, h=360, reflect={'op': .35}),
        C('12.set.temple_hall:05-l2', x=-380, z=300, h=360, reflect={'op': .35}),
        C('12.set.temple_hall:06-r2', x=380, z=300, h=360, reflect={'op': .35}),
        C('12.set.temple_hall:09-bench-left', x=-170, z=180, w=300, reflect={'op': .3}),
        C('12.set.temple_hall:10-bench-right', x=200, z=200, w=420, reflect={'op': .3}),
        C('12.set.temple_hall:03-l1', x=-470, z=40, h=360),
        C('12.set.temple_hall:04-r1', x=470, z=40, h=360),
    ], slots=[Slot('centre', x=0, z=100, reflect=True), Slot('friends', 'extras', x=-120, z=260),
              Slot('archive', 'archive', on='niche wall', rect=[.47, .25, .53, .75])])

ens('ens.temple.shore', 'the white temple assembled on the old chapel footprint: stylobate courses, six columns, beams, pediment and finial, on the wet stone foundation',
    ['11', '12', '14'], 'mid', [
        Floor('11.set.temple_shore:ground-o1-wet-old-stone-foundation-ground-strip', z_far=400),
        C('11.props.temple.states:1-only-2', x=0, z=300, h=520, name='temple'),
    ], slots=[Slot('on stylobate', x=-140, z=200, y=0), Slot('before', x=0, z=40)])

ens('ens.room.temple_backroom', 'the side room of the temple: bare boards, grey folding chairs facing nothing, one chair turned away at the foot of a lit stair, a sagging wire of bulbs',
    ['12', '14'], 'mid', [
        Strip('12.set.temple_backroom:back-wall-doorway', 400, 290, to_top=True, w_px=None, w_cm=760, name='back wall'),
        In('back wall', '12.set.temple_backroom:doorway-light-insert'),
        Floor('12.set.temple_backroom:01-floor-bare-board-strip-interior', z_far=400),
        C('12.set.temple_backroom:stairs-short-flight', x=180, z=380, h=150),
        C('12.set.temple_backroom:12-mid-01-mid-chair-front', x=-300, z=200, h=85),
        C('12.set.temple_backroom:12-mid-01-mid-chair-front', x=-180, z=200, h=85),
        C('12.set.temple_backroom:12-mid-02-mid-chair-three-quarter', x=-60, z=200, h=85),
        C('12.set.temple_backroom:12-mid-03-mid-chair-profile', x=-250, z=120, h=85),
        C('12.set.temple_backroom:12-mid-01-mid-chair-front', x=-120, z=120, h=85),
        C('12.set.temple_backroom:1-1-front-chair-turned-away', x=200, z=300, h=85, name='the chair turned away'),
        C('12.set.temple_backroom:12-fix-01-hanging-wire-sagging', x=0, z=150, y=220, w=500),
        C('12.set.temple_backroom:bare-bulb', x=-120, z=150, y=190, h=26),
        C('12.set.temple_backroom:12-fix-02-bare-bulb', x=80, z=150, y=195, h=26),
    ], slots=[Slot('archive', 'archive', on='back wall', rect=[.12, .25, .26, .5])],
    portals=[{'name': 'lit doorway', 'kind': 'door', 'card': 'back wall'}])

ens('ens.grove.temple', 'the temple grove at the forest edge: three thick trunks, a dark canopy, picnic bulbs strung between, a fog bank behind',
    ['12'], 'mid', [
        Sky('12.set.temple_grove:12-sky-dusk-sky-gradient'),
        Band('12.set.temple_grove:fog-screen-blank', 220, y_px=60, op=.75, name='fog screen'),
        Floor('12.set.temple_grove:grass-strip-front', z_far=500),
        C('12.set.temple_grove:tree-trunk-1', x=-380, z=300, h=520),
        C('12.set.temple_grove:12-mid-3-tree-trunk-3', x=60, z=360, h=520),
        C('12.set.temple_grove:tree-trunk-2', x=460, z=260, h=520),
        C('12.set.temple_grove:12-fix-wire-picnic-wire-loop', x=40, z=320, y=300, w=900),
        C('12.set.temple_grove:12-fix-bulb-1-bulb-1', x=-200, z=320, y=280, h=26),
        C('12.set.temple_grove:12-fix-bulb-2-bulb-2', x=150, z=320, y=275, h=26),
        C('12.set.temple_grove:12-fix-bulb-3-bulb-3', x=330, z=320, y=285, h=26),
        Strip('12.set.temple_grove:canopy-front', 250, 260, y_cm=380, to_top=True),
    ], slots=[Slot('at trunk', x=-300, z=260), Slot('friends', 'extras', x=200, z=200),
              Slot('archive', 'archive', on='fog screen', rect=[.35, .15, .65, .85])])

ens('ens.terrace.temple_shore', 'the broad wet terrace on the shore below the temple: stone floor, low steps, two wall lamps, cloths on a line, the water and far hills',
    ['12', '13', '14'], 'mid', [
        Sky('12.set.temple_shore_terrace:01-indigo-dusk-first-stars-milky-way'),
        Band('12.set.temple_shore_terrace:02-back-far-shore-hills-distant-lights', 70, y_px=3),
        Water('12.set.temple_shore_terrace:04-blue-grey-water'),
        Far('12.set.temple_shore_terrace:04-blue-grey-water-reflection-strip', 800, 40, 22, order='water', w_px=1760, op=.8),
        Floor('12.set.temple_shore_terrace:06-floor-stone-e', z_far=200),
        C('12.set.temple_shore_terrace:06-floor-stone', x=-420, z=230, h=160),
        C('12.set.temple_shore_terrace:07-wall-lamp', x=-520, z=230, y=170, h=60),
        C('12.set.temple_shore_terrace:09-clothes-line-line-rope', x=380, z=260, y=170, w=300),
        C('12.set.temple_shore_terrace:hanging-cloth-wind-1', x=330, z=259, y=95, h=80),
        C('12.set.temple_shore_terrace:11-cloth2-hanging-cloth-wind-2', x=460, z=259, y=100, h=70),
    ], slots=[Slot('chain', 'extras', x=0, z=60), Slot('poet', x=-80, z=40)])

ens('ens.field.night_rows', 'the night garden field: red soil in deep rows of golden blooms, weeds at the edges, a muted treeline',
    ['04', '05'], 'mid', [
        Band('04.set.night_garden_field:treeline-one-muted-dark-green-tree-silhouette', 60, y_px=4),
        Floor('04.set.night_garden_field:deeper-dark-reddish-brown-grit-04-set-night-gard', z_far=1500),
        C('04.set.night_garden_field:er-row-smallest', x=0, z=1100, w=4000, h=40),
        C('04.set.night_garden_field:flower-smaller-row', x=0, z=700, w=2800, h=45),
        C('04.set.night_garden_field:second-flower-slightly-smaller-row', x=0, z=380, w=1900, h=55),
        C('04.set.night_garden_field:bloom-1-front-flower-row', x=0, z=160, w=1300, h=70),
        C('04.set.night_garden_field:left-weeds-grass', x=-420, z=-80, w=420),
        C('04.set.night_garden_field:weed-r-right-strip', x=440, z=-90, w=420),
    ], slots=[Slot('in the rows', x=0, z=100)])

ens('ens.field.rise', "the field opened into a wide grass rise: the convex horizon, the gate ring small on it, grass clumps in front",
    ['05', '06'], 'mid', [
        C('05.set.night_field_parade:rise-04-rise', x=0, z=900, y=-40, w=3400, h=300),
        C('05.set.night_field_parade:03-gate', x=380, z=1100, y=150, h=180),
        Floor('05.set.night_field_parade:globe-floor-07-globe-floor', z_far=700),
        C('05.set.night_field_parade:grass-l-05-grass-l', x=-520, z=-60, h=130),
        C('05.set.night_field_parade:grass-r-06-grass-r', x=560, z=-60, h=130),
    ], slots=[Slot('on the rise', x=-80, z=200), Slot('ancestors', 'extras', x=250, z=500)])

ens('ens.gate.winged', 'the colossal winged marble gate in the night field: the gateway frame, two leaves carved as folded wings',
    ['05', '06'], 'mid', [
        C('05.set.winged_marble_gate:colossal-marble-gateway-frame', x=0, z=0, h=900, name='gateway'),
        In('gateway', '06.set.crystal_tree_hall:opening-crystal-distant-arch-opening', rect=(.05, .3, .95, 1.0)),
        C('05.set.winged_marble_gate:left-gate-leaf-folded-wing', x=-150, z=-5, h=760),
        C('05.set.winged_marble_gate:right-gate-leaf-folded-wing', x=150, z=-5, h=760),
    ], slots=[Slot('before the gate', x=0, z=-300)], portals=[{'name': 'gateway', 'kind': 'arch', 'card': 'gateway', 'shows': 'the crystal tree hall of Atlantis'}])

ens('ens.fence.perimeter', 'the perimeter fence: chain-link panels between end posts, cold cyan light strip and hot lamps behind the mesh, wet ground reflecting it',
    ['05', '06'], 'mid', [
        Strip('05.hero.perimeter:back-light-strip-0-0', 30, 20, y_cm=80, blend='screen'),
        C('05.hero.perimeter:lamp-2-lamp-2', x=-300, z=25, y=180, h=40, blend='screen'),
        C('05.hero.perimeter:lamp-3-lamp-3', x=60, z=25, y=180, h=40, blend='screen'),
        C('05.hero.perimeter:lamp-5-lamp-5', x=400, z=25, y=180, h=40, blend='screen'),
        C('05.hero.perimeter:mesh-l-wire-mesh-panel-left', x=-330, z=0, w=660, h=260),
        C('05.hero.perimeter:mesh-r-wire-mesh-panel-right', x=330, z=0, w=660, h=260),
        C('05.hero.perimeter:post-l-end-post-left', x=-670, z=0, h=300),
        C('05.hero.perimeter:post-r-end-post-right', x=670, z=0, h=300),
        Floor('05.hero.perimeter:floor-wet-floor-no', z_far=0),
    ])

ens('ens.room.basement', 'the low humid basement: two courses of damp cinderblock, the narrow window well cold blue, Southern-pine joists overhead, the blue mattress pad on the concrete',
    ['05'], 'mid', [
        Strip('05.set.humid_basement:05-wall-of-two-of-grey-with-empty-window-well-ap', 300, 230, w_px=None, w_cm=900, name='block wall'),
        In('block wall', '05.set.humid_basement:05-window-well-narrow-cold-blue-night-backing-fo'),
        Strip('05.set.humid_basement:05-joist-beam', 200, 30, y_cm=230, w_px=None, w_cm=900),
        Strip('05.set.humid_basement:05-joist-beam', 120, 30, y_cm=230, w_px=None, w_cm=900),
        Floor('05.props.staff-mattress-emblem:paving-card-rectangular-stone-floor-with-shallow', z_far=300),
        C('05.props.staff-mattress-emblem:view-thin-rigid-tufted-stained', x=0, z=60, w=200, h=40, name='mattress'),
        C('12.props.niche-porch:on', x=-60, z=100, y=180, h=40, name='bulb'),
    ], slots=[Slot('lying', x=0, z=60, y=20, pose='lie'), Slot('archive', 'archive', on='block wall', rect=[.66, .3, .8, .62])],
    portals=[{'name': 'window well', 'kind': 'window', 'card': 'block wall', 'shows': 'cold blue night'}])

# ═════════════════════════ STREETS, ROADS, ATLANTIS ═════════════════════════
ens('ens.motorcycle.curb', 'the motorcycle parked at the curb under one street lamp: the bike side-on, the lamp post with its cone, the kerb and wet sidewalk',
    ['10', '09', '11'], 'mid', [
        Floor('13.set.harbor_cafe:12-floor-wet-quay-13-set-harbor-cafe', z_far=60),
        Strip('09.hero.canopy:n-curb-strip-1', 60, 16, y_cm=0, name='kerb'),
        C('07.set.projection_three_roads:streetlamp-a-dim-warm', x=170, z=40, h=430, name='lamp', reflect={'op': .2}),
        C('11.props.parked-motorcycle:part-1', x=0, z=0, w=210, name='bike', reflect={'op': .22}),
    ], slots=[Slot('rider', x=-160, z=-20), Slot('mounted', x=0, z=0, pose='ride')], sfx=['sfx.engine.start'])

ens('ens.avenue.neon', 'the neon Atlantis avenue: night sky with a nebula, rooftop rows in magenta and blue, an industrial stack, dark asphalt with the dashed line',
    ['10', '06', '08'], 'back', [
        Sky('10.set.atlantis_streets:sky-night'),
        Band('10.set.atlantis_streets:rooftop-layer-1-far-low', 120, y_px=6, w_px=900, x_px=420),
        Band('10.set.atlantis_streets:rooftop-layer-2-mid-low', 130, y_px=8, w_px=900, x_px=1220),
        Far('10.set.atlantis_streets:stack-2-industrial', 1450, -100, 200),
        Water('10.set.atlantis_streets:road-dark-asphalt-plain'),
        Far('10.set.atlantis_streets:road-dash-white-repeatable-empty-street-assemble', 800, 90, 14, order='water', w_px=1760),
    ], notes='The street plays the water band role: a gloss floor from the horizon down.')

ens('ens.road.mountain', 'the switchbacks around Atlantis at first light: receding ridges, the road forking ahead, the nest tree at the roadside',
    ['10', '11'], 'back', [
        Sky('10.set.mountain_road:far-ridge-back-layer-lighter-distant-mountains'),
        Band('10.set.mountain_road:y-fork-road-ground-base-asphalt-surface', 120, y_px=4),
        Band('10.set.mountain_road:road-lines-2-separate-strips-rocky-shoulders-2-s', 90, y_px=14),
        Water('10.set.mountain_road:10-set-mountain-road'),
        Far('10.props.tree-dawn-sign:a1-tree-main', 1320, -120, 330, name='nest tree'),
        Far('10.props.tree-dawn-sign:a3-nest', 1300, -205, 40),
        Far('10.props.tree-dawn-sign:di-sun-disc', 420, -150, 80, name='sun'),
    ])

ens('ens.viaduct.arches', 'the old elevated rail: a band of gothic pointed arches, rusted railing, names carved under the salt line',
    ['04', '10', '11'], 'mid', [
        C('04.hero.viaduct:01-d-gothic-railway-archband-with-4-pointed-arch', x=0, z=0, w=2400, name='arch band'),
        C('04.hero.viaduct:06-rail-rusted-thin-railing', x=0, z=-1, y=600, w=2400, h=70),
        C('04.hero.viaduct:08-name-band-inscription-strip', x=-300, z=-2, y=180, w=900, op=.9),
    ])

ens('ens.viaduct.frame', 'the near viaduct arch framing the road out of the city (a foreground portal)',
    ['10', '04'], 'front', [
        C('04.hero.viaduct:03-larger-arch-framing-cutout-near', x=0, z=0, w=1500, name='arch'),
    ], portals=[{'name': 'arch', 'kind': 'arch', 'card': 'arch'}])

ens('ens.sign.new_dawn', 'the NEW DAWN roadside sign on two legs, digits waiting',
    ['10'], 'mid', [
        C('10.props.tree-dawn-sign:c6-leg-left', x=-60, z=0, h=260),
        C('10.props.tree-dawn-sign:c7-leg-right', x=60, z=0, h=260),
        C('10.props.tree-dawn-sign:c1-sign-panel', x=0, z=-1, y=170, w=200),
    ])

ens('ens.street.narrow', 'the narrow colonial street by candlelight: painted facades either side, string lights overhead, the end arch, stone floor',
    ['06', '07', '08', '09', '10'], 'mid', [
        Sky('06.set.narrow_streets:sky-thin-sky-strip'),
        C('06.set.narrow_streets:far-arch-street-end-arch', x=0, z=1500, h=520, name='end arch'),
        In('end arch', '06.set.atlantis_plaza:sky-night-closing-in-around-the-city-outline'),
        Floor('06.set.narrow_streets:floor-alley-floor-stone', z_far=1500),
        C('06.set.narrow_streets:wall-l-left-facade-street', x=-330, z=500, h=1100),
        C('06.set.narrow_streets:wall-r-right-facade-street', x=340, z=500, h=1100),
        C('06.set.narrow_streets:light-string-string-lights', x=0, z=600, y=520, w=700),
        C('06.set.narrow_streets:light-string-string-lights', x=0, z=250, y=480, w=700),
        C('06.props.lantern-candle-guitar:lantern-body-open-frame', x=-200, z=200, h=55),
    ], slots=[Slot('walker', x=0, z=150), Slot('archive', 'archive', on='end arch', rect=[.25, .3, .75, .9])],
    portals=[{'name': 'end arch', 'kind': 'arch', 'card': 'end arch'}])

ens('ens.house.containers', 'the House: stacked shipping containers, teal below and pink above, a door spilling warm light, a string of bulbs, the concrete apron',
    ['06', '07'], 'mid', [
        C('06.hero.house:upper-pink-stacked-container-front-two-windows', x=0, z=40, y=290, w=900),
        C('06.hero.house:lower-teal-broad-shipping-container-front-large-', x=0, z=40, y=0, w=900, h=300, name='lower container'),
        In('lower container', '06.hero.house:warm-back-interior-backing-muted-amber'),
        C('06.hero.house:light-string-string-of-bulbs-warm', x=-60, z=10, y=280, w=600),
        Floor('06.hero.house:floor-slab-concrete-apron', z_far=40),
    ], slots=[Slot('at the door', x=-20, z=-20), Slot('guests', 'extras', x=80, z=10)],
    portals=[{'name': 'door', 'kind': 'door', 'card': 'lower container', 'shows': 'the warm party inside'}])

ens('ens.atlantis.gate', 'the Atlantis light gate: the marble portal with gold inlay, the admission booth on its platform, the black mirror pool',
    ['06', '05'], 'mid', [
        Floor('06.set.atlantis_gate:floor-06-a-floor', z_far=500),
        C('06.set.atlantis_gate:portal-06-a-portal', x=0, z=420, h=620, name='portal'),
        In('portal', '06.set.crystal_tree_hall:opening-crystal-distant-arch-opening', rect=(-.1, .2, 1.1, 1.0)),
        In('portal', '06.set.crystal_tree_hall:canopy-l2-crystal-canopy-left-2-middle', rect=(-.1, 0, .6, .45)),
        In('portal', '06.set.crystal_tree_hall:canopy-r2-crystal-canopy-right-2-middle', rect=(.4, 0, 1.1, .45)),
        C('06.set.atlantis_gate:06-a-pool-rim', x=0, z=200, w=420),
        C('06.set.atlantis_gate:06-a-pool-water-mirror-black', x=0, z=199, y=4, w=380, h=40),
        C('06.set.atlantis_gate:booth-platform-06-a-booth-platform', x=-380, z=150, w=240),
        C('06.props.coin-booth:wet-ivory-marble-card-with-brass-details', x=-380, z=149, y=30, h=250, name='admission booth'),
        C('06.props.coin-booth:rim-card-pink-slim-card-teal', x=-380, z=148, y=200, w=160, blend='screen'),
    ], slots=[Slot('arriving', x=120, z=0), Slot('at booth', x=-260, z=110)],
    portals=[{'name': 'portal', 'kind': 'arch', 'card': 'portal', 'shows': 'the crystal tree hall'}])

ens('ens.atlantis.plaza', 'the rose stone plaza under the capital dome: three palace facades with lit windows, the dome rising behind',
    ['06', '08', '14'], 'mid', [
        Sky('06.set.atlantis_plaza:sky-night-closing-in-around-the-city-outline'),
        Far('06.set.atlantis_waterfront.skyline:city-01-capital-dome', 800, -150, 300, name='capital dome'),
        C('06.set.atlantis_plaza:facade-c-plaza-building-front-centre', x=0, z=900, h=900),
        C('06.set.atlantis_plaza:facade-l-left-plaza-building-front', x=-1100, z=700, h=900),
        C('06.set.atlantis_plaza:facade-r-right-plaza-building-front', x=1100, z=700, h=900),
        Floor('06.set.atlantis_plaza:ringed-mosaic-paving-top-down-06-set-atlantis-pl', z_far=900),
    ], slots=[Slot('centre', x=0, z=150), Slot('crowd', 'extras', x=350, z=400)])

ens('ens.atlantis.waterfront', 'the Atlantis waterfront: marble domes and towers surfacing with neon, water streaming off, vines on the terraces',
    ['06', '08', '14', '10'], 'back', [
        Sky('06.set.causeway_road:06-sky-sky-night'),
        Far('06.set.atlantis_waterfront.skyline:city-02-north-spire', 300, -110, 230),
        Far('06.set.atlantis_waterfront.skyline:city-07-central-rotunda', 560, -64, 140),
        Far('06.set.atlantis_waterfront.skyline:city-01-capital-dome', 850, -96, 210, name='capital dome'),
        Far('06.set.atlantis_waterfront.skyline:city-09-garden-dome', 1130, -62, 130),
        Far('06.set.atlantis_waterfront.skyline:city-03-south-spire', 1370, -105, 220),
        Water('06.set.atlantis_waterfront:strip'),
        Far('06.set.atlantis_waterfront.skyline:reflected-skyline-are-separate-exact-assembly', 850, 70, 140, order='water', op=.35, flip_v=True),
        Far('06.set.atlantis_waterfront:06-vine-l-left-vines', 420, 20, 70, order='water', op=.95),
    ])

ens('ens.causeway', 'the yellow-brick causeway laid over black water to the domes and spire tips at the vanishing point',
    ['06', '05', '10'], 'back', [
        Sky('06.set.causeway_road:06-sky-sky-night'),
        Band('06.set.causeway_road:06-set-causeway-road-dome-and-two-spire-tips-cit', 70, y_px=3),
        Water('06.set.causeway_road:06-water-plane-water-no-reflections'),
        Far('06.set.causeway_road:06-road-yellow-brick-road-full-length', 800, 250, 500, order='water', w_px=1500, name='causeway'),
    ])

ens('ens.rooftop.club', "the open-air rooftop over Atlantis: purple night, the disc-spire skyline, two lattice strobe towers, the railing ledge, the tile dance floor",
    ['08', '09', '14'], 'mid', [
        Sky('08.set.rooftop_club:part-1'),
        Band('08.set.rooftop_club:far-b', 60, y_px=-6),
        Band('08.set.rooftop_club:part-7', 110, y_px=4),
        Strip('08.set.rooftop_club:ledge', 700, 90, y_cm=0),
        Strip('08.set.rooftop_club:part-9', 690, 70, y_cm=60, name='railing'),
        Floor('08.set.rooftop_club:tile-floor', z_far=700),
        C('08.set.rooftop_club:part-4', x=-650, z=500, h=900, name='strobe tower L'),
        C('08.set.rooftop_club:part-5', x=650, z=500, h=900, name='strobe tower R'),
        C('08.fx.soul-weather:club-haze-bands-3', x=0, z=300, y=60, w=900, op=.45, blend='screen'),
    ], slots=[Slot('dancer', x=0, z=150), Slot('crowd', 'extras', x=0, z=380), Slot('at parapet', x=-200, z=640)],
    sfx=['sfx.party.room'])

ens('ens.plain.equator', 'the endless red plain at the equator: air bands, heat ripples, equator ticks nailed into the ground, a gas-giant moon',
    ['08'], 'back', [
        Sky('08.set.equator_plain:air-band-x1'),
        Far('13.props.planet-boats:02-moon1', 1180, -190, 220, name='gas giant'),
        Band('08.set.equator_plain:heat-ripple-a-x1', 40, y_px=-30, op=.7),
        Water('08.set.equator_plain:08-set-equator-plain-all-working-parts'),
        Far('08.set.equator_plain:equator-ticks-x6', 800, 60, 60, order='water', op=.9),
    ])

ens('ens.field.poppies', 'the poppy field under a smoky sky: scarlet poppies and purple spikes in rows, the near half cut to stubble',
    ['13', '14'], 'mid', [
        Sky('13.set.flower_field:poem-blossom-separate-layers'),
        Band('13.set.flower_field:back-p-horizon', 30, y_px=2),
        Floor('13.set.flower_field:13-04-mid-to-cut-stalks', z_far=1200, z_near=300),
        Floor('13.set.flower_field:13-09-stubble-ground-poet-handheld-flowe', z_far=300),
        C('13.set.flower_field:part-6', x=-500, z=500, w=1400),
        C('13.set.flower_field:13-05-frame-close', x=500, z=420, w=1300),
        C('13.set.flower_field:13-07-cut-stalk-1-medium', x=0, z=120, w=1200),
    ], slots=[Slot('harvester', x=0, z=150, pose='crouch')])

ens('ens.void.black', 'the black: no room, no floor, one faint open horizon of light; a faint dance ring can appear',
    ['01', '02', '03', '14'], 'back', [
        Sky('14.set.black_void:back-open-horizon'),
        Water('02.set.black_void:poem-02-black'),
    ], slots=[Slot('floating', x=0, z=0)])

ens('ens.door.vintage', 'the old panelled door alone in the black, warm light under it, the faint floor ring around it',
    ['14'], 'mid', [
        C('14.set.black_void:optional-dance-ring', x=0, z=0, y=-20, w=520, op=.6),
        C('14.props.door:d-opening', x=0, z=10, h=230, name='door'),
    ], slots=[Slot('approaching', x=-40, z=-200)], portals=[{'name': 'door', 'kind': 'door', 'card': 'door', 'shows': 'the amber party room'}])

ens('ens.eye.macro', "the poet's eye card filling the frame, the iris an aperture onto the night road winding to one far light",
    ['02'], 'front', [
        C('02.set.eye_macro.road:night', x=0, z=10, y=-20, w=600, h=180),
        C('02.set.eye_macro.road:winding', x=0, z=9, y=-10, w=560, h=90),
        C('02.props.poet-eye-aperture:large', x=0, z=5, y=10, w=150, name='iris'),
        C('02.props.poet-eye-aperture:eye-plate-brow-skin-no', x=0, z=0, y=-40, w=520, name='eye plate'),
    ], portals=[{'name': 'pupil', 'kind': 'aperture', 'card': 'iris', 'shows': 'the night road with two headlight beams'}])

ens('ens.car.driveway_night', 'the car at the top of the winding downhill road at night: the sedan side-on with warm windows and amber hazards, the road, two slab towers and the moon between',
    ['02'], 'mid', [
        Sky('02.set.overseer_skyline:01-gradient'),
        Far('04.fx.moon-reach:7-reach1-small-reach2-small-medium', 800, -230, 120, name='moon'),
        Far('02.set.overseer_skyline:left-slab-tower', 470, -170, 330),
        Far('02.set.overseer_skyline:03-right-slab-tower', 1130, -175, 340),
        Band('02.set.overseer_skyline:06', 70, y_px=4),
        Water('02.set.driveway_road_night:02-driveway-downhill-road-separate-layers'),
        Floor('02.set.driveway_road_night:part-3', z_far=60),
        C('02.props.car:dome-light-insert', x=-20, z=1, y=95, w=120, op=.8, blend='screen'),
        C('02.props.car:car', x=0, z=0, y=0, w=440, name='car'),
        C('02.props.car:hazard-light-left', x=-205, z=-1, y=70, w=20, blend='screen'),
        C('02.props.car:inserts-right-2', x=205, z=-1, y=70, w=20, blend='screen'),
    ], slots=[Slot('watching', x=-400, z=-300)], sfx=['sfx.car.idle'])

ens('ens.reel.filmstrip', 'the reel: framed inserts sliding on a black film strip with sprocket holes',
    ['14'], 'mid', [
        Sky('14.set.broll_life:1-sky-black-backing'),
        Water('14.set.broll_life:1-sky-black-backing'),
        C('14.set.broll_life:2-back-nine-frame-film-strip', x=0, z=200, y=40, w=1600),
        C('14.fx.filmframe:03-16-9-frame', x=0, z=0, y=60, w=360, name='insert frame'),
    ], slots=[Slot('archive', 'archive', on='insert frame', rect=[.1, .1, .9, .9])])

# ═════════════════════════ EXTRAS (groups in their own band, doing something) ═════════════════════════
ens('ens.crowd.club', 'club dancers in a loose ring, colliding and closing gaps', ['08', '09', '07'], 'front', [
    C('08.cast.club.main-poses:fast-dance-collision-reach-1', x=-220, z=0, h=165, name='dancer 1'),
    C('08.cast.club.main-poses:fast-dance', x=-60, z=40, h=172),
    C('08.cast.club.main-poses:street-fan-2', x=150, z=10, h=170, flip=True),
    C('08.cast.club.main-poses:close-the-gap', x=300, z=50, h=165, flip=True),
], notes='Extras: placed as one group in its own depth band behind the focal figure.')

ens('ens.crowd.party_guests', 'party guests at the House: words, lighters up', ['07', '06'], 'front', [
    C('party.07.party_guest.main-poses:02-mouth-words-we-love', x=-200, z=0, h=176),
    C('party.07.party_guest.main-poses:04-lighter-up-2', x=0, z=40, h=180),
    C('party.07.party_guest.main-poses:03-mouth-words-we-not', x=200, z=10, h=176, flip=True),
])

ens('ens.crowd.vintage_couples', 'vintage couples dancing cheek to cheek in slow motion', ['01', '14'], 'front', [
    C('party.vintage_party.main-poses:dance-threequarter', x=-260, z=0, h=178),
    C('party.vintage_party.main-poses:dance-threequarter-2', x=-180, z=8, h=165),
    C('party.vintage_party.main-poses:dance-back', x=160, z=30, h=178, flip=True),
    C('party.vintage_party.main-poses:dance-profile-2', x=240, z=36, h=165, flip=True),
])

ens('ens.crowd.harbour_couples', 'couples on the harbour: seated leaning in, walking two by two', ['13', '14'], 'front', [
    C('family.13.couple-orbits:1a-1-b-day', x=-120, z=0, h=125),
    C('family.13.couple-orbits:seated-lean', x=-20, z=0, h=118),
    C('family.13.couple-orbits:harbor-wi-alk-two-by-two', x=220, z=60, h=172),
])

ens('ens.crowd.angels', 'three angels on the rail above, basins tipping', ['08'], 'front', [
    C('08.cast.angel.main-poses:4-angel-left-tipping-basin-inward-right', x=-260, z=0, y=0, h=200),
    C('08.cast.angel.main-poses:6-angel-above-tilted-down-tipping-basin', x=0, z=20, y=40, h=200),
    C('08.cast.angel.main-poses:5-angel-right-tipping-basin-inward-left', x=260, z=0, y=0, h=200),
])


def main():
    meta = cut_water()
    os.makedirs(HERE, exist_ok=True)
    for f in os.listdir(HERE):
        if f.startswith('ens.') and f.endswith('.json'):
            os.remove(os.path.join(HERE, f))
    mech_idx = os.path.join(STAGE, 'mech', 'index.json')
    mechs = json.load(open(mech_idx)) if os.path.exists(mech_idx) else None
    from recipes import SCENES
    used = {e for R in SCENES.values() for e, _ in R['ens']} | {c['slot'].split(':')[0] for R in SCENES.values() for c in R.get('cast', []) if c.get('slot')}
    index = []
    for E in [E for E in LIB if E['id'] in used]:   # only ensembles a staged scene uses are published; the rest are drafts in this file
        for L in E['layers']:   # record each holed card's opening, so portals and portal clips can register to it
            if L.get('part') and L.get('name') and any(M.get('in_hole') == L['name'] for M in E['layers']):
                L['hole'] = hole(L['part'])
        if mechs:   # portal clips from the mechanisms agent, by the portal's kind
            items = mechs if isinstance(mechs, list) else mechs.get('clips', [])
            for P in E['portals']:
                hit = [m for m in items if isinstance(m, dict) and P['kind'] in (m.get('id', '') + ' ' + ' '.join(m.get('tags', [])))]
                if hit:
                    P['clip'] = hit[0].get('file') or hit[0].get('src') or hit[0]['id']
                    E['mechs'].append({'clip': P['clip'], 'slot': P['name'], 'trigger': 'portal opens'})
        json.dump(E, open(os.path.join(HERE, E['id'] + '.json'), 'w'), indent=1)
        index.append({'id': E['id'], 'name': E['name'], 'poems': E['poems'], 'depth': E['depth'], 'size_cm': E['size_cm'],
                      'layers': len(E['layers']), 'slots': [s['name'] for s in E['slots']], 'portals': [p['name'] for p in E['portals']]})
    json.dump({'about': 'Reusable set pieces for the cut-out stage (FORMATS.md section 2). Built by build_ensembles.py.',
               'water': meta, 'ensembles': index}, open(os.path.join(HERE, 'index.json'), 'w'), indent=1)
    print(len(index), 'of', len(LIB), 'ensembles published,', sum(i['layers'] for i in index), 'layers,', len(meta), 'water strips')


if __name__ == '__main__':
    main()
