#!/usr/bin/env python3
"""Stage lane 1: poems 01-07 as staged scenes, one spec per breakdown scene.

  /Users/gaia/anaconda3/bin/python3 shots/suite/tools/stage_01_07.py [01 | 01.2 ...]   (no args: every scene)
  node shots/suite/render.mjs <id> --port 8811                                         (measure + film)

Beats are (who, action, word, args, label): the word is a word of the reading in that scene ('the#2' = its 2nd "the"),
so every beat lands on its word. One held gesture per line; goals (keep_distance, face, wander, walk_with,
sway_to_beat) make the rest of the cast act on their own. Joins open archive film in a real surface of the lane-C
set; the query picks the first local clip (lib/archive_grab.py) and the page tags it ARCHIVE while it shows.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stage_build import build_poems, aim, surface_poly

POET_TEE = dict(character='poet', costume='black_tshirt')
POET_TRACK = dict(character='poet', costume='red_black_sunglasses')
EX = dict(character='ex', costume='ex_jacket')
HAZE = lambda t0, n=2, a=0.10: dict(kind='haze', t0=t0, sheets=n, stagger=1.3, slide_s=3.2, reach=1.15, alpha=a, over=True, y0=-0.1, y1=1.1, color='#a7c9cf')

SPECS = {}

# ───────────────────────── 01 · Out of Life ─────────────────────────
# the high-rise bedroom (lane C plate gen_a63bb494b1_10): floor x 1100-1580 between the bed and the dresser; the glass
# wall's foot is at y ~812. The fire-escape landing is OUTSIDE the glass: a code-drawn deck and rail beyond the pane
# (the plate has none; lane C flags the missing escape), same ground plane, so EX is smaller and seen through glass.
BED_ROOM = [[1125, 836], [1568, 830], [1576, 1076], [1092, 1076], [1104, 960], [1112, 880]]
LANDING = [[935, 716], [1405, 716], [1405, 788], [935, 788]]
ESCAPE_FX = [
    dict(kind='deck', ground_y=712, polygon=[[905, 712], [1440, 712], [1440, 792], [905, 792]], color='rgba(14,19,24,.86)'),
    dict(kind='rail', x=[915, 1430], ground_y=794, height_cm=100, color='#11161b'),
    dict(kind='glass', ground_y=812, polygon=[[800, 150], [1540, 95], [1540, 812], [805, 812]], alpha=0.12, color='#a8d6dc'),
]
BED_PATCH = dict(walkable=[BED_ROOM, LANDING],
                 marks={'window': [1290, 838], 'room': [1360, 1040], 'dresser': [1540, 930], 'landing': [1240, 782], 'landing_far': [1010, 736]},
                 surfaces=[{'id': 'pane_0', 'base_y': 812}, {'id': 'pane_1', 'base_y': 812}, {'id': 'pane_2', 'base_y': 1080}, {'id': 'screen_3', 'base_y': 760}],
                 layers=[{'id': 'gen_a63bb494b1_10.P4', 'depth_m': 9.0, 'why': 'P4 holds the room AND the city through the glass; EX stands outside the glass (Z 6.6-8.2 m), so the plane sits behind him. Nothing inside the room stands deeper than 5.8 m.'}],
                 fx=ESCAPE_FX)

SPECS['01.2'] = dict(
    patch=BED_PATCH,
    cast=[dict(id='POET', **POET_TEE, view='threequarter_back', side='L', place=[1380, 1046], hands={'L': 'grip', 'R': 'relaxed'}, props=[{'id': 'poem_page', 'side': 'L'}]),
          dict(id='EX', **EX, view='back', side='R', place=[1150, 766], props=[{'id': 'vape_pen', 'side': 'R'}])],
    beats=[('POET', 'hold_gesture', 0.0, {'side': 'L', 'name': 'page_up', 'dur': 0.01}, 'page held up'),
           ('POET', 'walk_to', 'look', {'to': 'window', 'speed': 0.8}, 'walks to the glass'),
           ('POET', 'turn', 'drawers', {'to': 'right', 'dur': 0.35}, 'glances to the dresser'),
           ('POET', 'turn', 'fire', {'to': -60, 'dur': 0.3}, 'back to the glass')],
    goals=[dict(who='EX', kind='keep_distance', args={'from': 'POET', 'min_cm': 280, 'max_cm': 420, 'zone': LANDING})],
    joins=[dict(kind='screen', surface='pane_2', word='hallways', clip='147f497d-6457-5bcd-a1a1-ed98ff0f2505', mix=0.55, blend='screen',
                tint='sepia(0.3) saturate(0.6)', why='"through the hallways": Alice (1915) runs the locked hallway, in the tall mirror pane'),
           dict(kind='touch', who='POET', side='R', surface='pane_0', at=[1262, 470], word='fire', reach_s=0.3, clip='8b20a7e8-5587-5e18-8553-1c1ec0ff408f',
                mix=0.48, blend='source-over', tint='grayscale(0.4) contrast(1.1)', label='palm on glass',
                why='the palm lands on the glass on "fire escapes"; the pane answers with Under Western Stars while the hand stays')],
    fx=[HAZE(0.3, 3, 0.12), HAZE(2.6, 1, 0.08)],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 1250, 'y': 640}, {'t': 5.4, 'zoom': 1.08, 'x': 1260, 'y': 600}]},
    notes=['Restaged on lane C\'s set (01.2.json): EX stands OUTSIDE the glass on a code-drawn fire-escape landing (deck + rail beyond the pane; the plate has no escape, lane C flags it), POET walks the floor strip between bed and dresser.',
           'EX keeps 2.3-3.8 m from POET by goal: as POET reaches the glass, EX steps back along the landing, back always to camera.'])

SPECS['01.1'] = dict(
    patch=BED_PATCH,
    cast=[dict(id='POET', **POET_TEE, view='threequarter_back', side='L', place=[1400, 1000], hands={'L': 'grip', 'R': 'relaxed'}, props=[{'id': 'poem_page', 'side': 'L'}]),
          dict(id='EX', **EX, view='back', side='R', place=[1180, 772], props=[{'id': 'vape_pen', 'side': 'R'}])],
    beats=[('POET', 'hold_gesture', 'What', {'side': 'L', 'name': 'page_up', 'dur': 0.5}, 'reads the page aloud'),
           ('EX', 'hold_gesture', 'made', {'side': 'R', 'name': 'hand_chest', 'dur': 0.6}, 'vape to his mouth'),
           ('EX', 'release', 'want', {'side': 'R'}),
           ('POET', 'hold_gesture', 'sold', {'side': 'R', 'name': 'palm_out', 'dur': 0.45}, 'palm out to the window'),
           ('POET', 'release', 'ourselves', {'side': 'R'}),
           ('POET', 'head_lowers', 'exist', {'deg': 18}, 'head down to the page')],
    joins=[dict(kind='screen', surface='screen_3', word='world', title='General Strike', query='riot crowd police street', mix=0.85, blend='source-over',
                tint='contrast(1.15) saturate(0.7)', why='"what we\'ve sold to the world": world chaos on the dark frame at left (the TV of the treatment)')],
    fx=[HAZE(4.5, 1, 0.06)],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 1150, 'y': 620}, {'t': 8.4, 'zoom': 1.05, 'x': 1180, 'y': 620}]},
    notes=['POET reads to the glass; EX stays outside on the code-drawn landing, back to us, the vape at his mouth on "made".',
           'The breakdown\'s CRT is not in this plate: the dark framed picture at left (lane C screen_3) carries the world-chaos archive instead.'])

# the fall: lane C city_fall_void (gen_d70a8829a9_50, aerial city at night, no horizon: the default 0.45 H stands).
# Both bodies float over the city (float), drop and tumble on the words; the gap between them never closes.
VOID_FALL = [[0, 640], [1920, 640], [1920, 1076], [0, 1076]]
SPECS['01.3'] = dict(
    patch=dict(walkable=VOID_FALL, marks={}, surfaces=[{'id': 'haze_2', 'base_y': 640}, {'id': 'wall_0', 'base_y': 650}]), all_layers_back=True,
    cast=[dict(id='POET', **POET_TEE, view='threequarter', side='R', place=[640, 860], hands={'L': 'grip', 'R': 'open'}, props=[{'id': 'poem_page', 'side': 'L'}]),
          dict(id='EX', **EX, view='back', side='R', place=[1190, 700])],
    beats=[('POET', 'float', 0.0, {'amp_cm': 7, 'period_s': 2.8}), ('EX', 'float', 0.0, {'amp_cm': 6, 'period_s': 3.3}),
           ('POET', 'falter', 'trip', None, 'trips on his words'),
           ('EX', 'drop', 'falling', {'cm': 110, 'dur': 2.6, 'tumble_deg': 20}, 'EX drops, back to us'),
           ('POET', 'drop', 'find', {'cm': 60, 'dur': 2.0, 'tumble_deg': -12}, 'POET follows him down'),
           ('POET', 'hold_gesture', 'leave', {'side': 'R', 'name': 'reach_out', 'dur': 0.6}, 'reaches back for EX'),
           ('POET', 'release', 'tainted', {'side': 'R'}),
           ('EX', 'drop', 'pit', {'cm': 190, 'dur': 2.4, 'tumble_deg': -15}, 'EX sinks into the pit'),
           ('POET', 'tumble', 'escapism', {'deg': 360, 'dur': 3.0}, 'POET turns over'),
           ('POET', 'drop', 'follow', {'cm': 100, 'dur': 2.2}, '"I\'ll follow"'),
           ('EX', 'rise', 'distance', {'cm': 150, 'dur': 2.0}, 'the gap breathes'),
           ('POET', 'hold_gesture', 'rediscover', {'side': 'R', 'name': 'reach_out', 'dur': 0.7}, 'reaches again'),
           ('POET', 'head_lowers', 'failed', {'deg': 22}),
           ('EX', 'vanish', 'vices', {'dur': 1.0})],
    joins=[dict(kind='screen', surface='haze_2', word='maze', end_word='haven', title='Berlin: Symphony', query='city streets traffic crowd', mix=0.55, blend='screen',
                tint='grayscale(0.5) contrast(1.2)', why='"the maze constructed by a tainted love" opens in the far city'),
           dict(kind='screen', surface='wall_0', word='forest', end_word='you#3', title='Foggy Mountain', query='forest trees fog', mix=0.6, blend='screen',
                tint='grayscale(0.3)', why='"the overnourished forest of escapism that calls for you"'),
           dict(kind='citizen', at=[1560, 760], height_cm=150, word='having', end_word='real', title='Beginning to Date', query='couple dancing', tint='contrast(1.1)',
                why='"almost having it all": a dancing couple from the archive floats past on a stick'),
           dict(kind='screen', surface='haze_2', word='failed', title='Alcohol and the Human Body', query='drinking bottle glass', mix=0.6, blend='screen', tint='contrast(1.2)',
                why='"your own vices": a drug-education film in the city below')],
    fx=[dict(kind='darken', t0=31.0, dur=3.2, alpha=0.82, over=True)],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 540}, {'t': 20, 'zoom': 1.06, 'x': 940, 'y': 600}, {'t': 34.3, 'zoom': 1.12, 'x': 960, 'y': 700}]},
    notes=['A fall staged on the ground solver: both bodies stand on a walkable void plane and float/drop/tumble on the words (lib/actions_extra.js), so scale stays the set\'s at their ground point; the checks skip scale on air frames (no standing frames in this scene).',
           'EX keeps his back to us through the tumble (a roll in the picture plane never shows the face). He vanishes on "vices"; the frame darkens to the black of 01.4d.',
           'Missing: POET falling/tumbling replacement bodies (the dossier lists them as need); the jointed tee puppet tumbles stiff.'])

# the vintage party: lane C gives a chapel plate with a giant drum (01.4 'needs a plate'); horizon 901, ground 1077, so a
# figure at the front is ~210 px. The camera sits low and zoomed 1.7x on the floor strip so the dancers read.
PARTY_FLOOR = [[180, 965], [1740, 965], [1760, 1074], [160, 1074]]
PARTY_SEEN = [[520, 975], [1280, 975], [1290, 1070], [510, 1070]]      # inside the zoomed frame at every camera key
GUEST = dict(character='vintage_party')
SPECS['01.4'] = dict(
    patch=dict(walkable=PARTY_FLOOR, marks={'crash': [760, 1050], 'ex_a': [1200, 990], 'ex_b': [600, 985], 'ex_c': [1060, 995]},
               surfaces=[{'id': 'pane_1', 'base_y': 970}, {'id': 'pane_0', 'base_y': 970}, {'id': 'screen_2', 'base_y': 1240}]),
    cast=[dict(id='POET', **POET_TEE, view='threequarter', side='R', place=[760, 1050], hands={'L': 'open', 'R': 'open'}),
          dict(id='EX', **EX, view='back', side='R', place=[1200, 990]),
          dict(id='GUEST_1', **GUEST, view='threequarter', side='L', place=[980, 1010]),
          dict(id='GUEST_2', **GUEST, view='front', side='R', place=[600, 1020]),
          dict(id='GUEST_3', **GUEST, view='threequarter', side='R', place=[1220, 1040])],
    beats=[('POET', 'drop', 0.0, {'cm': -380, 'dur': 0.01}, 'above the party'),
           ('POET', 'rise', 'crashing', {'cm': 0, 'dur': 0.6, 'ease': 'in'}, 'crashes down'),
           ('POET', 'falter', 'party', None, 'lands hard'),
           ('POET', 'wince', 'instincts'),
           ('EX', 'walk_to', 'silence', {'to': 'ex_c', 'speed': 0.7}, 'EX drifts through the dancers'),
           ('POET', 'walk_to', 'languages', {'to': [930, 1062], 'speed': 0.8}, 'POET follows'),
           ('EX', 'vanish', 'blood', {'dur': 0.8}, 'gone'),
           ('EX', 'walk_to', 'salivating', {'to': 'ex_b', 'speed': 1.2}),
           ('EX', 'appear', 'awakening', {'dur': 0.8}, 'glimpsed again'),
           ('POET', 'turn', 'darkest', {'to': 'left', 'dur': 0.4}),
           ('POET', 'walk_to', 'Pause', {'to': [700, 1045], 'speed': 0.8}),
           ('EX', 'vanish', 'second', {'dur': 0.8}),
           ('EX', 'walk_to', 'garments', {'to': 'ex_a', 'speed': 1.2}),
           ('POET', 'head_lowers', 'empty', {'deg': 20}),
           ('EX', 'appear', 'With', {'dur': 0.8}, '"with your back faced against me"'),
           ('POET', 'head_raises', 'back'),
           ('POET', 'turn', 'faced', {'to': 'right', 'dur': 0.4}),
           ('POET', 'hold_gesture', 'offer', {'side': 'R', 'name': 'reach_out', 'dur': 0.6}, 'reaches toward his back'),
           ('POET', 'falter', 'stumble', None, 'stumbles on his words'),
           ('POET', 'release', 'landing', {'side': 'R'}),
           ('EX', 'vanish', 'secret', {'dur': 1.2}),
           ('POET', 'drop', 'fall', {'cm': 260, 'dur': 1.3, 'tumble_deg': 30}, 'falls through the floor')],
    goals=[dict(who=g, kind='sway_to_beat', args={'bpm': 56, 'amp': 0.8, 'phase': ph}) for g, ph in (('GUEST_1', 0), ('GUEST_2', 0.6), ('GUEST_3', 1.1))] +
          [dict(who=g, kind='wander', args={'bpm': 56, 'every_bars': 3, 'step_cm': 45, 'seed': sd, 'speed': 0.5, 'zone': PARTY_SEEN}) for g, sd in (('GUEST_1', 5), ('GUEST_2', 9), ('GUEST_3', 13))],
    joins=[dict(kind='screen', surface='pane_1', word='spectrum', end_word='empty', title='His Royal Highness', query='dancing couples ballroom', mix=0.62, blend='source-over',
                tint='sepia(0.4) brightness(1.2)', why='"a spectrum of fields… garments made of sweet memories": ballroom dancers fill the tall stained-glass window'),
           dict(kind='screen', surface='screen_2', word='photographs', end_word='empty', title='Colaci Home Movies', query='family home movie', mix=0.75, blend='source-over',
                tint='sepia(0.35)', why='"photographs, film and fiction that leave me empty" on the drum head'),
           dict(kind='screen', surface='pane_0', word='With', title='Under Western Stars', query='man walking away', mix=0.55, blend='source-over', tint='grayscale(0.6)',
                why='"with your back faced against me" in the left window')],
    fx=[dict(kind='darken', t0=38.4, dur=2.4, alpha=0.95, over=True)],
    camera={'keys': [{'t': 0, 'zoom': 1.65, 'x': 960, 'y': 1080}, {'t': 20, 'zoom': 1.75, 'x': 940, 'y': 1080}, {'t': 41.3, 'zoom': 1.9, 'x': 900, 'y': 1080}]},
    notes=['Lane C marks this set "needs a plate": a chapel with a giant drum stands in for the vintage ballroom; horizon 901 and ground 1077 make a front figure ~210 px, so the camera is zoomed 1.65-1.9x on the floor strip (no figure is hand-scaled).',
           'EX vanishes (fade) and walks unseen to his next mark, so he is glimpsed in three places; guests sway at 56 bpm (slow motion) and wander by goal.',
           'POET\'s crash is drop(-380) then rise(0) on "crashing"; the trip through the floor is drop(260)+darken on "fall". No floor-hole card exists yet.'])

# ───────────────────────── 02 · Flashing Lights ─────────────────────────
# the void (lane C code set, no plate): stars on black; bodies float on a ground plane nobody sees.
VOID = [[0, 600], [1920, 600], [1920, 1076], [0, 1076]]
SPECS['02.1'] = dict(
    patch=dict(walkable=VOID),
    cast=[dict(id='POET', **POET_TEE, view='threequarter', side='R', place=[760, 1000], hands={'L': 'open', 'R': 'open'}),
          dict(id='EX', **EX, view='back', side='R', place=[1380, 700])],
    beats=[('POET', 'float', 0.0, {'amp_cm': 6, 'period_s': 3.0}), ('EX', 'float', 0.0, {'amp_cm': 5, 'period_s': 3.6}),
           ('POET', 'wince', 'scream', None, 'hears the scream'),
           ('POET', 'drop', 'falling', {'cm': 45, 'dur': 1.6, 'tumble_deg': 8}, 'falling, headlights off'),
           ('POET', 'hold_gesture', 'silent', {'side': 'L', 'name': 'arms_up', 'hand': 'claw', 'dur': 0.5}, 'the silent scream, hands clawing up'),
           ('POET', 'hold_gesture', 'silent', {'side': 'R', 'name': 'arms_up', 'hand': 'claw', 'dur': 0.5}),
           ('POET', 'head_lowers', 'scream#2', {'deg': -24}, 'head thrown back'),
           ('EX', 'tumble', 'trap', {'deg': -25, 'dur': 2.0}, 'EX in distress, out of reach'),
           ('POET', 'release', 'concussion', {'side': 'L'}), ('POET', 'release', 'concussion', {'side': 'R'}),
           ('POET', 'head_raises', 'concussion'),
           ('POET', 'falter', 'concussion'),
           ('EX', 'drop', 'walls', {'cm': 60, 'dur': 2.5}, 'walls cave in'),
           ('POET', 'hold_gesture', 'seething', {'side': 'R', 'name': 'reach_out', 'dur': 0.7}, 'reaches for EX'),
           ('POET', 'release', 'solitude', {'side': 'R'}),
           ('POET', 'head_lowers', 'smiles', {'deg': 20})],
    joins=[dict(kind='wipe', surface='haze_0', word='walls', end_word='simmering', title='San Francisco Earthquake Aftermath', query='ruined buildings walls collapsed',
                mix=0.5, blend='screen', tint='grayscale(0.6) contrast(1.2)', why='"a set of walls caving inward": 1906 walls in the black'),
           dict(kind='citizen', at=[1560, 860], height_cm=160, word='solitude', title='Coney Island - Boardwalk Crowd', query='crowd smiling people',
                tint='contrast(1.1)', why='"a solitude of crowds and smiles": a boardwalk crowd on a stick, far off')],
    fx=[dict(kind='stars', n=180, seed=21, alpha=0.55),
        dict(kind='sweep', t0=3.4, t1=5.6, period=2.2, width=420, alpha=0.35, color='#fff1c8'),
        dict(kind='flash', times=[11.2], dur=0.5, alpha=0.6),
        dict(kind='prop', prop='ring', size_cm=9, keys=[{'t': 9.2, 'at': [380, 520], 'ground_y': 900}, {'t': 15.5, 'at': [905, 600], 'ground_y': 900}], spin_dps=40),
        dict(kind='prop', prop='ring', size_cm=9, keys=[{'t': 9.2, 'at': [1700, 560], 'ground_y': 900}, {'t': 15.5, 'at': [1015, 600], 'ground_y': 900}], spin_dps=-30),
        dict(kind='strobe', bpm=96, t0=0.2, t1=3.0, alpha=0.12, colors=['#ffffff', '#6f8bff'])],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 600}, {'t': 20.8, 'zoom': 1.08, 'x': 980, 'y': 640}]},
    notes=['The void is lane C\'s code set (black, no plate): both float (lib/actions_extra.js float/drop/tumble); EX floats far off, back to us, tumbling on "trap".',
           'Two engagement rings (lib/fx_extra.js prop) drift toward each other from "marriage" and stop a ring-width apart.'])

BED50 = 'gen_a63bb494b1_50'
ROOM50 = [[1215, 884], [1660, 884], [1666, 1076], [1200, 1076]]
SPECS['02.2'] = dict(
    patch=dict(walkable=ROOM50, marks={'bed_edge': [1250, 1010], 'glass': [1330, 892]},
               surfaces=[{'id': 'pane_0', 'base_y': 868}, {'id': 'pane_1', 'base_y': 868}]),
    cast=[dict(id='POET', **POET_TEE, view='threequarter', side='L', place=[1250, 1010], hands={'L': 'relaxed', 'R': 'relaxed'})],
    beats=[('POET', 'sit', 0.0, {'height_cm': 52}, 'on the edge of the bed'),
           ('POET', 'turn', 'tossing', {'to': 'away', 'dur': 0.5}, 'tossing'),
           ('POET', 'turn', 'turning', {'to': 'camera', 'dur': 0.5}, 'and turning'),
           ('POET', 'head_lowers', 'type', {'deg': 16}),
           ('POET', 'stand', 'silent'),
           ('POET', 'head_raises', 'call#2'),
           ('POET', 'walk_to', 'man', {'to': 'glass', 'speed': 0.9}, 'crosses to the glass'),
           ('POET', 'head_lowers', 'truth', {'deg': 14})],
    joins=[dict(kind='touch', who='POET', side='R', surface='pane_0', at=aim('02.2', 1300, 868, 150), word='midnight', reach_s=0.45,
                title='Speech: Platform Posture', query='man looking in mirror', mix=0.55, blend='source-over', tint='grayscale(0.5) contrast(1.15)', label='hand on the night glass',
                why='"a silent call a man makes to the mirror after midnight": the night window is the mirror; his palm meets it and a 1949 man studies himself in it')],
    fx=[dict(kind='glow', at=[592, 712], ground_y=770, times=[1.1, 1.7, 2.3], r_cm=55, dur=0.45, color='rgba(170,220,255,1)'),
        dict(kind='prop', prop='phone', keys=[{'t': 0, 'at': [592, 712], 'ground_y': 770}]),
        dict(kind='darken', t0=0, dur=0.01, alpha=0.35)],
    camera={'keys': [{'t': 0, 'zoom': 1.12, 'x': 1180, 'y': 760}, {'t': 10.9, 'zoom': 1.2, 'x': 1260, 'y': 700}]},
    notes=['Lane C\'s bedroom_night is the same high-rise bedroom (frame 50). POET sits on the bed edge (the bed is lane C\'s P0 occluder), the phone pulses on the nightstand on "emergency call".',
           'There is no mirror surface in the plate: the night window is the mirror ("a man makes to the mirror after midnight"), so the touch join opens there.'])

SPECS['02.3'] = dict(
    patch=dict(walkable=VOID),
    cast=[dict(id='POET', **POET_TEE, view='front', side='R', place=[960, 1000], hands={'L': 'relaxed', 'R': 'relaxed'})],
    beats=[('POET', 'head_lowers', 'insomnia', {'deg': -8}, 'straining to see'),
           ('POET', 'hold_gesture', 'epiphany', {'side': 'R', 'name': 'hand_chest', 'dur': 0.6}),
           ('POET', 'release', 'After', {'side': 'R'}),
           ('POET', 'head_raises', 'dilated'),
           ('POET', 'hold_gesture', 'sun', {'side': 'L', 'name': 'palm_out', 'dur': 0.6}, 'shades from the sun'),
           ('POET', 'release', 'possible', {'side': 'L'}),
           ('POET', 'head_lowers', 'won\'t', {'deg': 22}, '"we won\'t make it"'),
           ('POET', 'vanish', 'it', {'dur': 1.0})],
    joins=[dict(kind='wipe', surface='haze_0', word='road', end_word='dilated', title='Dusk to Dawn', query='car headlights road night',
                mix=0.6, blend='source-over', tint='contrast(1.1)', why='"a road winding down" seen inside the dark: the childhood road at night'),
           dict(kind='screen', surface='haze_0', word='dilated', end_word='possible', title='Eyes and Their Care', query='eye pupil close up',
                mix=0.55, blend='source-over', tint='grayscale(0.4)', why='"dilated": a 1941 pupil opens in the black (02.3b eye macro)')],
    fx=[dict(kind='stars', n=90, seed=33, alpha=0.4),
        dict(kind='sunrise', t0=8.2, t1=11.2, at=[960, 300], r0=40, r1=420, rise=40, ground_y=700),
        dict(kind='iris', at=[960, 360], t0=11.6, dur=2.6, r0=1500, r1=40)],
    camera={'keys': [{'t': 0, 'zoom': 1.12, 'x': 960, 'y': 600}, {'t': 14.8, 'zoom': 1.24, 'x': 960, 'y': 600}]},
    notes=['POET in the black, whole (camera 1.12-1.24x; a closer push would cut his body and fail off_frame); the road and a 1941 pupil open in the void as wipes; an iris closes on "we won\'t make it" into the flashback.',
           'The pupil push-through (02.3b-c) needs an eye macro plate; the iris to black stands in.'])

YP = dict(character='young_poet_pajamas')
GHOST = dict(character='ghost_child')
WIN50 = [[1225, 884], [1600, 884], [1612, 1000], [1215, 1000]]
SPECS['02.4'] = dict(
    patch=dict(walkable=ROOM50, marks={'window': [1380, 890], 'beside': [1500, 900]},
               surfaces=[{'id': 'pane_0', 'base_y': 868}, {'id': 'pane_1', 'base_y': 868}]),
    cast=[dict(id='YOUNG_POET', **YP, view='back', side='R', place=[1380, 892], hands={'L': 'relaxed', 'R': 'relaxed'}),
          dict(id='GHOST_CHILD', **GHOST, view='threequarter_back', side='L', place=[1560, 930], alpha=0)],
    beats=[('YOUNG_POET', 'hold_gesture', 'recall', {'side': 'R', 'name': 'hand_chest', 'dur': 0.5}),
           ('GHOST_CHILD', 'appear', 'ghost', {'dur': 1.4}, 'the ghost fades in'),
           ('GHOST_CHILD', 'walk_to', 'dead', {'to': [1500, 900], 'speed': 0.6}, 'one notch taller, beside him'),
           ('GHOST_CHILD', 'reach', 'appeared', {'side': 'R', 'target': {'who': 'YOUNG_POET', 'socket': 'shoulder_R'}, 'dur': 0.6}, 'hugs him from the side'),
           ('YOUNG_POET', 'release', 'shared', {'side': 'R'}),
           ('GHOST_CHILD', 'release', 'last', {'side': 'R'}),
           ('GHOST_CHILD', 'vanish', 'It', {'dur': 1.4}, 'gone'),
           ('YOUNG_POET', 'turn', 'winter', {'to': 'threequarter_back', 'side': 'L', 'dur': 0.5}),
           ('YOUNG_POET', 'head_lowers', 'alone', {'deg': 20}, 'left home alone')],
    joins=[dict(kind='screen', surface='pane_1', word='parents', end_word='last', title='Family Life', query='mother father argue',
                mix=0.62, blend='source-over', tint='grayscale(0.3) contrast(1.1)', why='"my parents\' marriage wouldn\'t last": a 1949 family in the window where the car should be'),
           dict(kind='screen', surface='pane_0', word='winter', title='Winter in Den haag', query='snow winter street',
                mix=0.5, blend='source-over', tint='grayscale(0.5)', why='"a warm and heavy breeze in winter"')],
    fx=[dict(kind='sweep', t0=0.4, t1=16.5, period=3.4, width=360, alpha=0.32, color='#fff0c0'),
        dict(kind='darken', t0=0, dur=0.01, alpha=0.25)],
    camera={'keys': [{'t': 0, 'zoom': 1.25, 'x': 1380, 'y': 700}, {'t': 16.9, 'zoom': 1.32, 'x': 1400, 'y': 700}]},
    notes=['Lane C uses the same high-rise bedroom (frame 50) for the 1990s living room: the window stands in for the living-room window. Headlights sweep the room (lib/fx_extra.js sweep).',
           'The ghost child fades in and hugs YOUNG_POET from the side: a reach to his shoulder socket, measured as a contact. The parents argue in the archive in the pane (no car in this plate).',
           'Young poet (pajamas) and ghost child are lane B jointed rigs; both wear the borrowed boy\'s head (lane B flags: needs its own painted heads).'])

SPECS['02.5'] = dict(
    patch=dict(walkable=ROOM50, marks={'window': [1360, 890], 'close': [1330, 886]},
               surfaces=[{'id': 'pane_0', 'base_y': 868}, {'id': 'pane_1', 'base_y': 868}]),
    cast=[dict(id='YOUNG_POET', **YP, view='back', side='R', place=[1420, 940], hands={'L': 'relaxed', 'R': 'relaxed'})],
    beats=[('YOUNG_POET', 'walk_to', 'curtains', {'to': 'window', 'speed': 0.7}, 'to the window'),
           ('YOUNG_POET', 'reach', 'blinds', {'side': 'R', 'target': {'surface': 'pane_1', 'at': aim('02.5', 1385, 868, 98)}, 'dur': 0.5}, 'draws the blind cord'),
           ('YOUNG_POET', 'release', 'as', {'side': 'R'}),
           ('YOUNG_POET', 'head_raises', 'see'),
           ('YOUNG_POET', 'hold_gesture', 'whispering', {'side': 'L', 'name': 'hand_chest', 'dur': 0.5}),
           ('YOUNG_POET', 'head_lowers', 'down', {'deg': 18})],
    joins=[dict(kind='screen', surface='pane_1', word='see', end_word='lights', title='Dusk to Dawn', query='car on road at night headlights',
                mix=0.7, blend='source-over', tint='contrast(1.15)', why='"to see flashing lights": the car below, through the raised blinds'),
           dict(kind='screen', surface='pane_1', word='whispering', title='Have I Told You Lately', query='couple in car talking',
                mix=0.6, blend='source-over', tint='grayscale(0.4)', why='"the whispering screams of two souls on a road winding down"')],
    fx=[dict(kind='blinds', polygon=[[760, 60], [1760, 40], [1760, 862], [760, 866]], t0=2.2, t1=3.4, slats=16),
        dict(kind='sweep', t0=5.8, t1=12.2, period=1.1, width=260, alpha=0.4, color='#ffb347'),
        dict(kind='darken', t0=0, dur=0.01, alpha=0.25)],
    camera={'keys': [{'t': 0, 'zoom': 1.2, 'x': 1380, 'y': 680}, {'t': 12.2, 'zoom': 1.3, 'x': 1380, 'y': 660}]},
    notes=['Blind slats (lib/fx_extra.js blinds) lift from the bottom between "blinds" and "up" while the boy\'s hand is on the cord (a reach to a point 112 cm up the pane: aim()).',
           'Amber hazard flashes sweep the room from "flashing"; the car and the two souls are archive in the raised window.'])

SPECS['02.6'] = dict(
    patch=dict(walkable=ROOM50, marks={'window': [1360, 892]},
               surfaces=[{'id': 'pane_0', 'base_y': 868}, {'id': 'pane_1', 'base_y': 868}]),
    cast=[dict(id='YOUNG_POET', **YP, view='threequarter', side='R', place=[1330, 960], hands={'L': 'relaxed', 'R': 'relaxed'}),
          dict(id='GHOST_CHILD', **GHOST, view='threequarter', side='L', place=[1530, 975], alpha=0)],
    beats=[('GHOST_CHILD', 'appear', 'And', {'dur': 0.4}, 'the ghost again'),
           ('GHOST_CHILD', 'hand_off', 'tears', {'to': 'YOUNG_POET', 'prop': 'tambourine', 'side': 'R', 'to_side': 'R', 'dur': 0.5}, 'holds out a tambourine'),
           ('YOUNG_POET', 'turn', 'no#2', {'to': 'away', 'dur': 0.3}),
           ('YOUNG_POET', 'walk_to', 'fucks', {'to': 'window', 'speed': 1.0}, 'to the window'),
           ('GHOST_CHILD', 'vanish', 'love', {'dur': 1.6}, 'thins away'),
           ('YOUNG_POET', 'hold_gesture', 'love', {'side': 'R', 'name': 'arms_up', 'dur': 0.4}, 'winds up'),
           ('YOUNG_POET', 'release', 'give', {'side': 'R', 'dur': 0.15}, 'throws')],
    joins=[dict(kind='screen', surface='pane_0', word='old', title='Destruction: Fun or Dumb', query='broken window glass',
                mix=0.55, blend='source-over', tint='grayscale(0.3) contrast(1.2)', why='"old to teach": a vandalism-education film in the broken glass')],
    fx=[dict(kind='prop', prop='tambourine', size_cm=25, spin_dps=0, keys=[{'t': 0.0, 'who': 'GHOST_CHILD', 'side': 'R'}, {'t': 1.15, 'who': 'YOUNG_POET', 'side': 'R'},
                                                                           {'t': 4.35, 'who': 'YOUNG_POET', 'side': 'R'}, {'t': 4.8, 'at': [1300, 420], 'ground_y': 868, 'ease': 'linear'},
                                                                           {'t': 5.6, 'at': [1220, 120], 'ground_y': 1600, 'ease': 'linear'}]),
        dict(kind='cracks', ground_y=868, at=[1300, 420], t=4.8, polygon=[[760, 60], [1760, 40], [1760, 862], [760, 866]], black_t=5.3, n=13),
        dict(kind='sweep', t0=0, t1=4.6, period=3.0, width=320, alpha=0.25),
        dict(kind='darken', t0=0, dur=0.01, alpha=0.25)],
    camera={'keys': [{'t': 0, 'zoom': 1.22, 'x': 1400, 'y': 700}, {'t': 7.8, 'zoom': 1.3, 'x': 1360, 'y': 640}]},
    notes=['The tambourine is a prop card (lib/fx_extra.js prop) that rides the ghost\'s hand, changes hands on the hand-off ("tears"), rides YOUNG_POET\'s hand to the window and leaves it on "give"; the pane cracks and goes black behind it.',
           'The ghost thins away (fade) while he winds up. The tambourine leaves the frame into 03.1.'])
# ───────────────────────── 03 · How to break off an engagement ─────────────────────────
# The breakdown puts no body in the chapel: 03.1-03.4 and 03.6 are the tambourine (lib/fx_extra.js prop) and the decay.
# The chapel plate (gen_872d16167d_50) is lane C's: rose/stained windows pane_0 (left) and pane_1 (centre), a giant drum
# head (screen_2) standing in for the empty temple's furniture.
CHAPEL_FLOOR = [[0, 1000], [1920, 1000], [1920, 1078], [0, 1078]]
CHAPEL = dict(walkable=CHAPEL_FLOOR, surfaces=[{'id': 'pane_0', 'base_y': 1000}, {'id': 'pane_1', 'base_y': 1000}, {'id': 'screen_2', 'base_y': 1240}])
SPECS['03.1'] = dict(
    patch=CHAPEL, cast=[],
    beats=[],
    joins=[dict(kind='screen', surface='screen_2', word='tambourine', end_word='temple', title='Sound Waves And Their Sources', query='sound vibration instrument',
                mix=0.6, blend='screen', tint='sepia(0.3)', why='"a tambourine sounds off an empty temple": a 1933 sound film in the drum head'),
           dict(kind='screen', surface='pane_0', word='choir', title='Something to Sing About', query='singers choir stage',
                mix=0.6, blend='source-over', tint='grayscale(0.4)', why='"empty choir stands": a 1937 chorus in the tall left window'),
           dict(kind='screen', surface='pane_1', word='prayer', title='graal pinksterzegen', query='procession people praying',
                mix=0.6, blend='source-over', tint='grayscale(0.4)', why='"empty prayer lines": a 1932 Pentecost procession in the rose window')],
    fx=[dict(kind='darken', t0=0, dur=0.01, alpha=0.2),
        dict(kind='prop', prop='tambourine', size_cm=25, spin_dps=220, over=True, arc_px=0,
             keys=[{'t': 0.0, 'at': [-120, 260], 'ground_y': 1800}, {'t': 3.6, 'at': [700, 520], 'ground_y': 1800, 'ease': 'linear'},
                   {'t': 8.0, 'at': [1300, 380], 'ground_y': 1800, 'ease': 'linear'}, {'t': 12.3, 'at': [2100, 620], 'ground_y': 1800, 'ease': 'linear'}]),
        dict(kind='sweep', t0=0, t1=12.3, period=6.0, width=600, alpha=0.18, color='#ffe2b0')],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 540}, {'t': 12.3, 'zoom': 1.06, 'x': 1000, 'y': 560}]},
    notes=['No puppet: the breakdown has none. The tambourine thrown in 02.6 tumbles end over end across the empty temple (a prop card, 25 cm at the front of the chapel floor).',
           'Checks have no body to measure here; the joins open three archive films in the drum head and the two windows, tagged while they show.'])

SPECS['03.2'] = dict(
    patch=CHAPEL, cast=[],
    beats=[],
    joins=[dict(kind='screen', surface='pane_1', word='abandoned', title='Aqua Frolics', query='swimming pool water',
                mix=0.55, blend='source-over', tint='grayscale(0.5)', why='"abandoned Baptist pools": a water show in the rose window')],
    fx=[dict(kind='darken', t0=0, dur=0.01, alpha=0.25),
        dict(kind='prop', prop='tambourine', size_cm=25, spin_dps=40,
             keys=[{'t': 0.0, 'at': [1010, 160], 'ground_y': 1800}, {'t': 1.4, 'at': [1000, 430], 'ground_y': 1800}]),
        dict(kind='sweep', t0=0, t1=2.8, period=0.9, width=700, alpha=0.22, color='#fff0d0')],
    camera={'keys': [{'t': 0, 'zoom': 1.08, 'x': 1000, 'y': 480}, {'t': 2.8, 'zoom': 1.14, 'x': 1000, 'y': 480}]},
    notes=['The tambourine comes in through the rose window still whole and hangs over the nave; the light races (time-lapse sweeps, 0.9 s a day).'])

SPECS['03.3'] = dict(
    patch=CHAPEL, cast=[],
    beats=[],
    joins=[dict(kind='screen', surface='screen_2', word='cobwebs', end_word='disintegration', title='Spider Engineers', query='spider web',
                mix=0.65, blend='screen', tint='grayscale(0.6) contrast(1.2)', why='"pews taken by cobwebs": a 1956 spider spins on the drum head'),
           dict(kind='screen', surface='pane_0', word='gift', title='Pathe News Christmas', query='presents gifts boxes',
                mix=0.55, blend='source-over', tint='grayscale(0.4)', why='"opened gift boxes placed outside the side doors"')],
    fx=[dict(kind='darken', t0=0, dur=13.5, alpha=0.5),
        dict(kind='cobweb', at=[0, 0], t0=0.6, dur=4.0, r_px=420, spokes=10),
        dict(kind='cobweb', at=[1920, 0], t0=1.6, dur=4.5, r_px=380, spokes=9, flip=True),
        dict(kind='cobweb', at=[1300, 1000], t0=3.4, dur=5.0, r_px=200, spokes=8),
        dict(kind='prop', prop='tambourine', size_cm=25, spin_dps=6, keys=[{'t': 0.0, 'at': [1000, 430], 'ground_y': 1800}, {'t': 13.5, 'at': [990, 445], 'ground_y': 1800}]),
        dict(kind='sweep', t0=0, t1=13.5, period=1.2, width=700, alpha=0.18, color='#fff0d0')],
    camera={'keys': [{'t': 0, 'zoom': 1.14, 'x': 1000, 'y': 480}, {'t': 13.5, 'zoom': 1.0, 'x': 960, 'y': 540}]},
    notes=['Time-lapse decay: cobwebs spin in from the corners (lib/fx_extra.js cobweb), the room darkens over the scene, days race across as light sweeps; the tambourine still hangs.',
           'Needs: the chapel in its three time-lapse states (intact, cobwebbed, rotting) as plates; the dossier asks for them and lane C has one.'])

STORM_FLOOR = [[0, 960], [1920, 960], [1920, 1078], [0, 1078]]
SPECS['03.4'] = dict(
    patch=dict(walkable=STORM_FLOOR, surfaces=[{'id': 'wall_0', 'base_y': 1000}, {'id': 'haze_1', 'base_y': 905}]), cast=[],
    beats=[],
    joins=[dict(kind='screen', surface='haze_1', word='thunders', end_word='remains', title='Lightning', query='lightning storm',
                mix=0.55, blend='screen', tint='grayscale(0.3) contrast(1.3)', why='"it thunders, then it rains until nothing remains"'),
           dict(kind='screen', surface='wall_0', word='broken', end_word='lightning', title='Shock Troops of Disaster', query='hurricane damage wreckage',
                mix=0.55, blend='screen', tint='grayscale(0.5) contrast(1.2)', why='"goods broken and sealed apart by lightning": the 1938 hurricane on the chapel wall'),
           dict(kind='screen', surface='wall_0', word='breads', title='Rain Off Barn Roof', query='rain dripping roof',
                mix=0.6, blend='screen', tint='grayscale(0.3)', why='"daily breads soaked and delivered rotted by rain"')],
    fx=[dict(kind='rain', t0=3.6, t1=21, n=320, alpha=0.32, slant=0.22),
        dict(kind='flash', times=[2.2, 6.9, 15.0, 15.4, 19.3], dur=0.45, alpha=0.7, bolt={'x': 1250, 'y0': 0, 'y1': 600}),
        dict(kind='darken', t0=0, dur=0.01, alpha=0.18)],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 540}, {'t': 20.9, 'zoom': 1.12, 'x': 900, 'y': 620}]},
    notes=['The storm over lane C\'s chapel_storm plate: lightning on "thunders", "lightning", rain from "rains" (lib/fx_extra.js flash, rain).',
           'No puppet (breakdown). Needs: broken wedding-gift, bread and marionette-string prop cards (03.4b-d) to stage the inserts.'])

SHORE = 'gen_e315da34f9_30'
SPECS['03.5'] = dict(
    patch=dict(marks={'trail_far': [760, 690], 'trail_far2': [860, 692]}, surfaces=[{'id': 'water_0', 'base_y': 800}, {'id': 'water_1', 'base_y': 960}]),
    cast=[dict(id='POET', **POET_TEE, view='back', side='R', place=[640, 1010], hands={'L': 'relaxed', 'R': 'relaxed'}),
          dict(id='EX', **EX, view='back', side='R', place=[860, 1018])],
    beats=[('POET', 'walk_to', 'and', {'to': 'trail_far', 'speed': 0.75}, 'walk away up the trail'),
           ('EX', 'walk_to', 'and', {'to': 'trail_far2', 'speed': 0.75}, 'side by side, out of step'),
           ('POET', 'head_lowers', 'footsteps', {'deg': 12})],
    joins=[dict(kind='screen', surface='water_0', word='blankets', end_word='puppeteers', title='Gulliver', query='puppets strings',
                mix=0.55, blend='screen', tint='grayscale(0.4)', why='"blankets soiled by venomous puppeteers"'),
           dict(kind='screen', surface='water_0', word='footsteps', title='Robinson Crusoe', query='footprints in the sand beach',
                mix=0.65, blend='screen', tint='grayscale(0.4) contrast(1.1)', why='"two sets of button-printed footsteps": Crusoe finds the footprint (1927), in the pool that did not drain')],
    fx=[dict(kind='footprints', points=[[650, 1000], [700, 940], [660, 890], [705, 845], [672, 808], [712, 776], [690, 748], [722, 724],
                                        [868, 1006], [835, 950], [880, 900], [845, 856], [888, 818], [856, 786], [892, 757], [866, 733]],
             times=[0.6, 1.3, 2.0, 2.7, 3.4, 4.1, 4.8, 5.5, 0.9, 1.6, 2.3, 3.0, 3.7, 4.4, 5.1, 5.8], alpha=0.55)],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 900, 'y': 600}, {'t': 7.0, 'zoom': 1.08, 'x': 820, 'y': 640}]},
    notes=['The two who made the footprints walk away side by side up the mud shore, both backs to us (EX never turns: back / three-quarter-back only).',
           'Footprints (lib/fx_extra.js footprints) are pressed in one at a time behind them; they are drawn, not read off the puppets\' soles.'])

SPECS['03.6'] = dict(
    patch=dict(surfaces=[{'id': 'water_0', 'base_y': 800}, {'id': 'water_1', 'base_y': 960}]), cast=[],
    beats=[],
    joins=[dict(kind='screen', surface='water_0', word='shattered', title='Explosives', query='explosion debris',
                mix=0.5, blend='screen', tint='grayscale(0.4)', why='"a tambourine shattered into pieces"')],
    fx=[dict(kind='footprints', points=[[650, 1000], [700, 940], [660, 890], [705, 845], [672, 808], [868, 1006], [835, 950], [880, 900], [845, 856], [888, 818]],
             times=[0] * 10, alpha=0.5),
        dict(kind='prop', prop='tambourine', size_cm=25, spin_dps=300,
             keys=[{'t': 0.0, 'at': [1250, -140], 'ground_y': 1000}, {'t': 2.95, 'at': [1180, 930], 'ground_y': 960, 'ease': 'linear'}, {'t': 3.0, 'shatter': True, 'ground_y': 975}],
             pieces=12, fade_s=3.0)],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 540}, {'t': 6.7, 'zoom': 1.1, 'x': 1120, 'y': 760}]},
    notes=['The tambourine falls out of the sky onto the shore and shatters on "shattered" (rim, skin and jingles scatter and fade).',
           'Needs: a tambourine-pieces card set (rim halves, torn skin, loose jingles) to lie on the shore for 04.'])
# ───────────────────────── 04 · Nevermore ─────────────────────────
# POET in red/black with sunglasses (lane B poet_tracksuit). Hands "in pockets": both hands held low at the hips
# (hand_low) until 04.6, when he puts his hands back on. Ravens are prop cards on paths (lib/fx_extra.js raven).
POCKETS = lambda who='POET', w=0.0: [(who, 'hold_gesture', w, {'side': 'L', 'name': 'hand_low', 'dur': 0.3}, 'hands in pockets'), (who, 'hold_gesture', w, {'side': 'R', 'name': 'hand_low', 'dur': 0.3})]
RAVENS = lambda t0, y=180, n=2, dur=7.0, d=-1: [dict(kind='prop', prop='raven', size_cm=70, dir=d, flap_hz=2.0 + 0.3 * i,
                                                      keys=[{'t': t0 + i * 1.1, 'at': [2050 if d < 0 else -130, y + 60 * i], 'ground_y': 760}, {'t': t0 + i * 1.1 + dur, 'at': [-130 if d < 0 else 2050, y - 40 + 50 * i], 'ground_y': 760, 'ease': 'linear'}])
                                                 for i in range(n)]
SHORE_N = dict(marks={'trail_end': [1180, 736], 'rim': [1060, 752]}, surfaces=[{'id': 'water_1', 'base_y': 640}, {'id': 'wall_5', 'base_y': 600}, {'id': 'haze_6', 'base_y': 600}])
SPECS['04.1'] = dict(
    patch=SHORE_N,
    cast=[dict(id='POET', **POET_TRACK, view='profile', side='L', place=[1420, 738])],
    beats=POCKETS() + [
           ('POET', 'walk_to', 'follow', {'to': 'trail_end', 'speed': 0.55}, 'walks the trail of broken pieces'),
           ('POET', 'head_lowers', 'pieces', {'deg': 22}, 'head bowed to read it'),
           ('POET', 'turn', 'ashes', {'to': 'threequarter', 'side': 'L', 'dur': 0.5}),
           ('POET', 'head_raises', 'debris'),
           ('POET', 'turn', 'lift', {'to': 'threequarter_back', 'side': 'R', 'dur': 0.5}, 'looks to the sea')],
    joins=[dict(kind='screen', surface='water_1', word='ashes', end_word='debris', title='Watershed wildfire', query='forest fire smoke ash',
                mix=0.6, blend='screen', tint='contrast(1.15)', why='"the ashes of expired wildfires cover sands" in the far water'),
           dict(kind='screen', surface='water_1', word='lift', title='Wonder of Water', query='sea floor underwater water',
                mix=0.6, blend='screen', tint='grayscale(0.3)', why='"lift it from the night seawater\'s floor"')],
    fx=RAVENS(2.0, 170, 2, 8.0) + RAVENS(9.0, 120, 1, 6.0, 1) +
       [dict(kind='scatter', prop='card', w_cm=4, h_cm=2, color='#c9b08a', n=14, t0=0, spread_s=0.01, x0=1050, x1=1650, y0=725, y1=760, seed=4)],
    camera={'keys': [{'t': 0, 'zoom': 1.05, 'x': 1300, 'y': 560}, {'t': 15.2, 'zoom': 1.12, 'x': 1200, 'y': 580}]},
    notes=['Lane C\'s shore_night: a low camera (53 cm), so POET walks the far shore (y 714-736) to stay 380-450 px tall; hands held at the hips stand in for "in pockets" (no hands-in-pockets torso card exists).',
           'Tambourine pieces lie on the trail (small kraft cards, lib/fx_extra.js scatter, settled from frame 0); ravens cross overhead.'])

SPECS['04.2'] = dict(
    patch=SHORE_N,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter_back', side='L', place=[1180, 736])],
    beats=POCKETS() + [
           ('POET', 'head_lowers', 'whispers', {'deg': 12}),
           ('POET', 'walk_to', 'find', {'to': 'rim', 'speed': 0.5}, 'to the half-buried rim'),
           ('POET', 'turn', 'heart', {'to': 'left', 'dur': 0.4}),
           ('POET', 'sit', 'left', {'height_cm': 34}, 'kneels by the rim'),
           ('POET', 'head_lowers', 'familiar', {'deg': 28}, 'looks at the heart'),
           ('POET', 'head_raises', 'shaken'),
           ('POET', 'head_lowers', 'mine', {'deg': 10}),
           ('POET', 'stand', 'putting', None, 'rises as it re-enters'),
           ('POET', 'head_raises', 'nevermore')],
    joins=[dict(kind='screen', surface='water_1', word='waves', end_word='silence', title='Safe In Port', query='calm sea harbor water',
                mix=0.6, blend='screen', tint='grayscale(0.3)', why='"the waves will calm to folded whispers"'),
           dict(kind='screen', surface='water_1', word='sad', end_word='inspiration', title='Living Stereo', query='orchestra music listening',
                mix=0.6, blend='screen', tint='sepia(0.3)', why='"every sad blue note life can perform"')],
    fx=[dict(kind='prop', prop='heart', size_cm=13, bpm=72, keys=[{'t': 0, 'at': [985, 766], 'ground_y': 766}, {'t': 16.2, 'at': [985, 766], 'ground_y': 766},
                                                                   {'t': 18.0, 'at': [990, 700], 'ground_y': 766}, {'t': 25.7, 'at': [995, 690], 'ground_y': 766},
                                                                   {'t': 27.4, 'who': 'POET', 'joint': 'chest'}, {'t': 27.7, 'hide': True}]),
        dict(kind='glow', at=[985, 760], ground_y=766, times=[8.6, 14.6, 21.0], r_cm=30, dur=0.8, color='rgba(255,90,80,1)'),
        dict(kind='scatter', prop='card', w_cm=4, h_cm=2, color='#c9b08a', n=10, t0=0, spread_s=0.01, x0=900, x1=1300, y0=740, y1=770, seed=4)] + RAVENS(4.0, 150, 1, 8.0),
    camera={'keys': [{'t': 0, 'zoom': 1.12, 'x': 1150, 'y': 600}, {'t': 31.5, 'zoom': 1.25, 'x': 1080, 'y': 620}]},
    notes=['The heart (a beating cut-paper card) lies on the sand from the start, throbs on "throbbing heart", lifts by itself on "shaken off" and floats into his chest on "putting it back in place" (prop keys: ground point -> his chest joint).',
           'He kneels (sit 34 cm) without using his hands; they stay at his hips.'])

FIELD = dict(surfaces=[{'id': 'haze_0', 'base_y': 600}])
SPECS['04.3'] = dict(
    patch=FIELD,
    cast=[dict(id='POET', **POET_TRACK, view='back', side='R', place=[820, 1004])],
    beats=POCKETS() + [
           ('POET', 'walk_to', 'follow', {'to': [1010, 770], 'speed': 0.6}, 'into the vast field'),
           ('POET', 'head_raises', 'faith')],
    joins=[dict(kind='screen', surface='haze_0', word='puzzle', end_word='scrambled', title='Master Hands', query='hands craftsman working',
                mix=0.55, blend='screen', tint='sepia(0.3)', why='"the puzzle pieces of faith are handcrafted"'),
           dict(kind='screen', surface='haze_0', word='mustard', title='Victory Gardens', query='planting seeds garden',
                mix=0.55, blend='screen', tint='grayscale(0.3)', why='"scattered as mustard seeds into the vast moonlight night\'s field"')],
    fx=[dict(kind='scatter', prop='seed', size_cm=1.4, n=70, t0=6.6, spread_s=2.4, x0=200, x1=1700, y0=700, y1=1060, seed=12)] + RAVENS(0.5, 160, 2, 7.0, 1),
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 600}, {'t': 10.3, 'zoom': 1.08, 'x': 980, 'y': 640}]},
    notes=['POET follows the trail up into the moonlit field, back to us, hands at his hips; mustard seeds fall over the rows on "scattered" (lib/fx_extra.js scatter).',
           '04.3a (the incline trail between shore and field) has no set; the scene starts in the field.'])

SPECS['04.4'] = dict(
    patch=FIELD,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter_back', side='R', place=[1010, 772])],
    beats=POCKETS() + [
           ('POET', 'walk_to', 'plants', {'to': [880, 742], 'speed': 0.5}, 'walks the rows'),
           ('POET', 'turn', 'face', {'to': 'camera', 'dur': 0.5}, 'the field faces him'),
           ('POET', 'head_lowers', 'shadows', {'deg': 16}),
           ('POET', 'head_raises', 'called'),
           ('POET', 'turn', 'called', {'to': 'away', 'dur': 0.4}),
           ('POET', 'walk_to', 'forward', {'to': [960, 690], 'speed': 0.6}, 'called forward, steps on')],
    joins=[dict(kind='screen', surface='haze_0', word='golden', end_word='anticipation', title='Spring Comes to a Pond', query='flowers blooming',
                mix=0.55, blend='screen', tint='sepia(0.4) brightness(1.1)', why='"the plants in a golden hue bloom and face toward me"'),
           dict(kind='screen', surface='haze_0', word='memories', end_word='defeat', title='They Grow Up So Fast', query='family memories children',
                mix=0.55, blend='screen', tint='grayscale(0.4)', why='"the shadows where our memories hide"')],
    fx=[dict(kind='sunrise', t0=2.0, t1=6.0, at=[960, 820], r0=60, r1=700, rise=0, ground_y=650),
        dict(kind='darken', t0=7.4, dur=2.0, alpha=0.3)],
    camera={'keys': [{'t': 0, 'zoom': 1.06, 'x': 960, 'y': 620}, {'t': 16.6, 'zoom': 1.14, 'x': 940, 'y': 600}]},
    notes=['A golden glow rises in the rows as they "face toward me" (lane C plate has the flowers; they do not turn: a plant card that turns its face is a needed asset).'])

DARK = dict(surfaces=[{'id': 'haze_0', 'base_y': 600}, {'id': 'floor_1', 'base_y': 878}])
HANDS_AT = [[1186, 878], [1232, 884]]
SPECS['04.5'] = dict(
    patch=DARK,
    cast=[dict(id='POET', **POET_TRACK, view='profile', side='R', place=[860, 862])],
    beats=POCKETS() + [
           ('POET', 'head_lowers', 'deepest', {'deg': 34}, 'bent low, searching the shadows'),
           ('POET', 'walk_to', 'search', {'to': [1010, 870], 'speed': 0.4}, 'searching the bare ground'),
           ('POET', 'head_lowers', 'hands', {'deg': 40})],
    joins=[dict(kind='screen', surface='haze_0', word='clouds', end_word='darkness', title='Cloud Hides Moon', query='clouds covering moon night',
                mix=0.7, blend='screen', tint='grayscale(0.5)', why='"the clouds meet the stars for the deepest level of darkness"')],
    fx=[dict(kind='darken', t0=0.5, dur=3.0, alpha=0.62),
        dict(kind='glow', at=[1208, 872], ground_y=880, times=[7.0], r_cm=90, dur=2.4, alpha=0.5, color='rgba(255,236,190,1)'),
        dict(kind='prop', prop='hand', size_cm=19, keys=[{'t': 7.2, 'at': HANDS_AT[0], 'ground_y': 878}], rot=0.2),
        dict(kind='prop', prop='hand', size_cm=19, keys=[{'t': 7.4, 'at': HANDS_AT[1], 'ground_y': 884}], rot=-0.1)],
    camera={'keys': [{'t': 0, 'zoom': 1.1, 'x': 1000, 'y': 640}, {'t': 9.3, 'zoom': 1.22, 'x': 1060, 'y': 680}]},
    notes=['The darkest frame: the stars go under (darken 0.62). On "two hands" a patch of ground lights and two hands lie palm-down in it (placeholder hand cards: a hand-on-the-ground card set is needed).',
           'His sleeves coming out empty (04.5c) needs a wrists-without-hands arm card: not staged.'])

SPECS['04.6'] = dict(
    patch=DARK,
    cast=[dict(id='POET', **POET_TRACK, view='profile', side='R', place=[1010, 870])],
    beats=POCKETS() + [
           ('POET', 'walk_to', 'Hands', {'to': [1130, 868], 'speed': 0.4}, 'to the two hands'),
           ('POET', 'sit', 'dusk#2', {'height_cm': 26}, 'kneels over them'),
           ('POET', 'release', 'celebrate', {'side': 'L', 'dur': 0.3}),
           ('POET', 'reach', 'celebrate', {'side': 'L', 'target': {'surface': 'floor_1', 'at': aim('04.6', 1185, 876, 52)}, 'dur': 0.6}, 'lowers his left wrist onto the left hand'),
           ('POET', 'release', 'feel', {'side': 'L'}),
           ('POET', 'release', 'they', {'side': 'R', 'dur': 0.3}),
           ('POET', 'reach', 'they', {'side': 'R', 'target': {'surface': 'floor_1', 'at': aim('04.6', 1195, 880, 52)}, 'dur': 0.6}, 'the right hand goes back on'),
           ('POET', 'release', 'mine', {'side': 'R'}),
           ('POET', 'hand_opens', 'put', {'side': 'L'}), ('POET', 'hand_opens', 'put', {'side': 'R'}),
           ('POET', 'stand', 'myself', None, 'rises to full height'),
           ('POET', 'hold_gesture', 'world', {'side': 'L', 'name': 'palm_out', 'dur': 0.6}, 'arms open'),
           ('POET', 'hold_gesture', 'world', {'side': 'R', 'name': 'palm_out', 'dur': 0.6}),
           ('POET', 'release', 'soul', {'side': 'L'}), ('POET', 'release', 'soul', {'side': 'R'}),
           ('POET', 'head_lowers', 'soul', {'deg': 14}),
           ('POET', 'head_raises', 'alright'),
           ('POET', 'turn', 'believe', {'to': 'camera', 'dur': 0.5}),
           ('POET', 'hold_gesture', 'heart', {'side': 'R', 'name': 'hand_chest', 'dur': 0.5}, 'hand on the heart'),
           ('POET', 'release', 'hands#2', {'side': 'R'}),
           ('POET', 'turn', 'still', {'to': 'away', 'dur': 0.6}, 'reflects, facing the field'),
           ('POET', 'walk_to', 'Now', {'to': [1060, 700], 'speed': 0.7}, '"now go"')],
    joins=[dict(kind='screen', surface='haze_0', word='Hands', end_word='mine', title='Master Hands (Part IV)', query='hands working',
                mix=0.55, blend='screen', tint='sepia(0.3)', why='"hands that once could tusk dusk after dusk"'),
           dict(kind='screen', surface='haze_0', word='world', end_word='soul', title='Mirror of America', query='world crowds',
                mix=0.5, blend='screen', tint='grayscale(0.4)', why='"I\'ve wanted the world and lost my soul"'),
           dict(kind='screen', surface='haze_0', word='alright', end_word='alright#2', title='Vivid Sunrise', query='sunrise',
                mix=0.55, blend='screen', tint='sepia(0.2)', why='"I do believe I\'ll be alright"'),
           dict(kind='screen', surface='haze_0', word='tree', end_word='nevermore#2', title='Night Tree', query='tree at night',
                mix=0.6, blend='screen', tint='grayscale(0.3)', why='"this still muted tree in night garden"')],
    fx=[dict(kind='darken', t0=0, dur=0.01, alpha=0.45),
        dict(kind='prop', prop='hand', size_cm=19, rot=0.2, keys=[{'t': 0, 'at': HANDS_AT[0], 'ground_y': 878}, {'t': 4.3, 'at': HANDS_AT[0], 'ground_y': 878}, {'t': 4.9, 'who': 'POET', 'side': 'L'}, {'t': 5.0, 'hide': True}]),
        dict(kind='prop', prop='hand', size_cm=19, rot=-0.1, keys=[{'t': 0, 'at': HANDS_AT[1], 'ground_y': 884}, {'t': 8.8, 'at': HANDS_AT[1], 'ground_y': 884}, {'t': 9.4, 'who': 'POET', 'side': 'R'}, {'t': 9.5, 'hide': True}]),
        dict(kind='glow', at=[1180, 860], ground_y=880, times=[0.0, 2.4, 4.8], r_cm=110, dur=2.6, alpha=0.4, color='rgba(255,236,190,1)'),
        dict(kind='sunrise', t0=12.6, t1=18.0, at=[1130, 820], r0=80, r1=560, rise=0, ground_y=780)],
    camera={'keys': [{'t': 0, 'zoom': 1.22, 'x': 1100, 'y': 700}, {'t': 20, 'zoom': 1.15, 'x': 1060, 'y': 660}, {'t': 49.5, 'zoom': 1.0, 'x': 960, 'y': 560}]},
    notes=['He kneels (sit 26 cm), reaches each wrist to a point 52 cm above its hand (aim()), and the hand card rides up onto that wrist and is gone into it ("I put them back on"); then he stands, opens his arms, and the lit patch widens.',
           'The hands are placeholder code cards; the jointed puppet shows his own hands throughout (no handless forearm card exists): the biggest asset gap in 04.'])
# ───────────────────────── 05 · Bloodlines ─────────────────────────
# Ancestors are lane B rigs: ancestor_indigo (indigo/gold robe, legged) and ancestor_elder (white/silver, skirt card).
A_IND = dict(character='ancestor_indigo')
A_ELD = dict(character='ancestor_elder')
PARADE = dict(walkable=[[0, 560], [1920, 560], [1920, 1076], [0, 1076]], surfaces=[{'id': 'haze_0', 'base_y': 560}])
LANTERN = lambda who, side='R', t=0.0: dict(kind='prop', prop='lantern', keys=[{'t': t, 'who': who, 'side': side}], alpha=0.95)
SPECS['05.1'] = dict(
    patch=PARADE,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter_back', side='R', place=[900, 968]),
          dict(id='ANCESTOR_1', **A_ELD, view='front', side='R', place=[640, 650]),
          dict(id='ANCESTOR_2', **A_IND, view='front', side='R', place=[860, 640]),
          dict(id='ANCESTOR_3', **A_IND, view='front', side='L', place=[1060, 645]),
          dict(id='ANCESTOR_4', **A_IND, view='front', side='L', place=[1260, 655]),
          dict(id='ANCESTOR_5', **A_IND, view='threequarter', side='L', place=[1150, 800]),
          dict(id='ANCESTOR_6', **A_ELD, view='front', side='L', place=[1460, 668])],
    beats=[('POET', 'walk_to', 'They', {'to': [960, 930], 'speed': 0.6}, 'walks out of the field toward the lights'),
           ('ANCESTOR_1', 'walk_to', 'tell', {'to': [700, 770], 'speed': 0.6}, 'the parade comes over the rise'),
           ('ANCESTOR_2', 'walk_to', 'tell', {'to': [840, 745], 'speed': 0.6}),
           ('ANCESTOR_3', 'walk_to', 'ask', {'to': [1100, 748], 'speed': 0.6}),
           ('ANCESTOR_4', 'walk_to', 'ask', {'to': [1280, 772], 'speed': 0.6}),
           ('ANCESTOR_6', 'walk_to', 'inherit', {'to': [1420, 800], 'speed': 0.6}),
           ('ANCESTOR_5', 'walk_to', 'earth', {'to': [1090, 918], 'speed': 0.8}, 'Mae steps out'),
           ('POET', 'hand_opens', 'name', {'side': 'R'}),
           ('ANCESTOR_5', 'hand_off', 'own', {'to': 'POET', 'prop': 'star', 'side': 'R', 'to_side': 'R', 'dur': 0.5}, 'sets the first star in his open hand'),
           ('POET', 'hold_gesture', 'galaxies', {'side': 'R', 'name': 'arms_up', 'dur': 0.6}, 'lifts the star into the sky')],
    goals=[dict(who=a, kind='face', args={'who': 'POET'}) for a in ('ANCESTOR_1', 'ANCESTOR_2', 'ANCESTOR_3', 'ANCESTOR_4', 'ANCESTOR_6')],
    joins=[dict(kind='screen', surface='haze_0', word='inherit', end_word='stars', title='Frederick Douglass', query='portrait man history',
                mix=0.55, blend='screen', tint='grayscale(0.3) sepia(0.2)', why='"to ask if I can inherit the earth": the 1984 Frederick Douglass film in the sky over the parade'),
           dict(kind='screen', surface='haze_0', word='galaxies', title='Heavenly Bodies', query='stars galaxy planets',
                mix=0.65, blend='screen', tint='contrast(1.2)', why='"even galaxies, if I may"')],
    fx=[LANTERN('ANCESTOR_2'), LANTERN('ANCESTOR_4', 'L'), LANTERN('ANCESTOR_6'),
        dict(kind='prop', prop='star', size_cm=9, keys=[{'t': 0, 'who': 'ANCESTOR_5', 'side': 'R'}, {'t': 6.5, 'who': 'POET', 'side': 'R'}, {'t': 7.6, 'who': 'POET', 'side': 'R'},
                                                         {'t': 9.6, 'at': [1010, 120], 'ground_y': 1600, 'ease': 'linear'}])],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 560}, {'t': 9.6, 'zoom': 1.06, 'x': 980, 'y': 600}]},
    notes=['The parade (six lane B ancestor rigs) comes over the rise and faces POET by goal; ANCESTOR_5 (Mae) walks out and hands him the first star (hand_off: both hands meet, measured as a contact); he lifts it and it rises into the sky.',
           'Lanterns ride three ancestors\' hands (prop cards). Naming stars with typed names (05.1c) needs a text/label fx: not staged.'])

BASEMENT_FLOOR = [[700, 640], [1250, 640], [1262, 1076], [690, 1076]]
SPECS['05.2'] = dict(
    patch=dict(walkable=BASEMENT_FLOOR, surfaces=[{'id': 'wall_1', 'base_y': 925}, {'id': 'wall_2', 'base_y': 915}, {'id': 'wall_4', 'base_y': 600}]),
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='R', place=[960, 905])],
    beats=[('POET', 'sit', 0.0, {'height_cm': 24}, 'on a thin mattress pad'),
           ('POET', 'head_lowers', 'past', {'deg': 18}),
           ('POET', 'wince', 'spine', None, 'his spine shifts on the pad'),
           ('POET', 'turn', 'didn\'t', {'to': 'away', 'dur': 0.6}, 'it didn\'t'),
           ('POET', 'head_raises', 'dream'),
           ('POET', 'stand', 'dream'),
           ('POET', 'turn', 'prevail', {'to': 'camera', 'dur': 0.5}, 'to dream was to prevail')],
    joins=[dict(kind='screen', surface='wall_2', word='shared', end_word='bedrooms', title='Inner City', query='crowded apartment room',
                mix=0.5, blend='source-over', tint='grayscale(0.3) contrast(1.15)', why='"the shared rooms of humid basements as bedrooms" on the left column'),
           dict(kind='screen', surface='wall_1', word='wood', end_word='didn\'t', title='Trees to Tribunes', query='pine trees logging timber',
                mix=0.5, blend='source-over', tint='sepia(0.3)', why='"the wood beams of southern pine" on the right column'),
           dict(kind='screen', surface='wall_2', word='mattress', end_word='spine', title='Sleep for Health', query='sleeping bed',
                mix=0.5, blend='source-over', tint='grayscale(0.4)', why='"mattress pads where…"'),
           dict(kind='screen', surface='wall_4', word='dream', title='Sun Emerges', query='sun clouds light',
                mix=0.7, blend='screen', tint='sepia(0.2)', why='"to dream was to prevail": light at the end of the tunnel')],
    fx=[dict(kind='deck', ground_y=870, polygon=[[838, 872], [1092, 872], [1110, 930], [822, 930]], color='rgba(120,112,100,.92)', line='rgba(60,55,50,.5)')],
    camera={'keys': [{'t': 0, 'zoom': 1.15, 'x': 960, 'y': 640}, {'t': 19.3, 'zoom': 1.05, 'x': 960, 'y': 600}]},
    notes=['Lane C marks 05.2 "needs a plate": a flooded concrete underpass stands in for the humid basement. POET sits on a thin mattress pad (code deck card) between the columns; the columns carry the archive (vertical surfaces).',
           'He cannot lie down (no lying replacement body is swapped in yet): the breakdown\'s top-down on the mattress is staged seated.'])

SPECS['05.3'] = dict(
    patch=PARADE,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter_back', side='R', place=[960, 930]),
          dict(id='ANCESTOR_1', **A_ELD, view='front', side='R', place=[700, 770]),
          dict(id='ANCESTOR_2', **A_IND, view='front', side='R', place=[840, 745]),
          dict(id='ANCESTOR_4', **A_IND, view='front', side='L', place=[1100, 748]),
          dict(id='ANCESTOR_7', **A_IND, view='front', side='L', place=[1280, 772]),
          dict(id='ANCESTOR_8', **A_IND, view='threequarter', side='L', place=[1420, 800])],
    beats=[('POET', 'hold_gesture', 'ask', {'side': 'L', 'name': 'arms_up', 'dur': 0.6}, 'asks, palms up'),
           ('POET', 'hold_gesture', 'ask', {'side': 'R', 'name': 'arms_up', 'dur': 0.6}),
           ('ANCESTOR_8', 'walk_to', 'universe', {'to': [1100, 905], 'speed': 0.8}, 'brings the universe'),
           ('POET', 'release', 'God', {'side': 'R', 'dur': 0.4}),
           ('ANCESTOR_8', 'hand_off', 'little', {'to': 'POET', 'prop': 'orb', 'side': 'R', 'to_side': 'R', 'dur': 0.5}, 'hands him the universe'),
           ('POET', 'hold_gesture', 'blessing', {'side': 'R', 'name': 'reach_out', 'dur': 0.5}, 'awards a blessing here'),
           ('POET', 'release', 'there', {'side': 'R'}),
           ('POET', 'release', 'miracles', {'side': 'L'}),
           ('POET', 'hold_gesture', 'miracles', {'side': 'R', 'name': 'arms_up', 'dur': 0.5}, 'raises the universe')],
    goals=[dict(who=a, kind='face', args={'who': 'POET'}) for a in ('ANCESTOR_1', 'ANCESTOR_2', 'ANCESTOR_4', 'ANCESTOR_7')],
    joins=[dict(kind='screen', surface='haze_0', word='universe', end_word='me#2', title='Four in the Cosmos', query='space planets cosmos',
                mix=0.6, blend='screen', tint='contrast(1.2)', why='"to ask if I can invent a new universe"'),
           dict(kind='screen', surface='haze_0', word='miracles', title='VOYAGER', query='saturn planet rings',
                mix=0.65, blend='screen', tint='contrast(1.15)', why='"even grant miracles where the needs of the spoken word exists"')],
    fx=[LANTERN('ANCESTOR_2'), LANTERN('ANCESTOR_7', 'L'),
        dict(kind='prop', prop='orb', size_cm=30, keys=[{'t': 0, 'who': 'ANCESTOR_8', 'side': 'R'}, {'t': 6.4, 'who': 'POET', 'side': 'R'}]),
        dict(kind='flash', times=[9.6], dur=0.6, alpha=0.35, color='#fff2c8')],
    camera={'keys': [{'t': 0, 'zoom': 1.04, 'x': 980, 'y': 600}, {'t': 13.5, 'zoom': 1.12, 'x': 980, 'y': 620}]},
    notes=['The ancestors stand in a half circle behind POET (facing him by goal); he asks with both palms up; ANCESTOR_8 walks in and hands him the universe (an orb card on the hand-off); he raises it on "miracles".'])

CHAIN_Y = [930, 920, 910, 901, 892]
SPECS['05.4'] = dict(
    patch=PARADE,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='L', place=[880, CHAIN_Y[0]]),
          dict(id='ANCESTOR_1', **A_ELD, view='threequarter', side='L', place=[985, CHAIN_Y[1]]),
          dict(id='ANCESTOR_5', **A_IND, view='threequarter', side='L', place=[1070, CHAIN_Y[2]]),
          dict(id='ANCESTOR_6', **A_ELD, view='threequarter', side='L', place=[1150, CHAIN_Y[3]]),
          dict(id='ANCESTOR_9', **A_ELD, view='threequarter', side='L', place=[1225, CHAIN_Y[4]])],
    beats=[('ANCESTOR_9', 'reach', 'times', {'side': 'R', 'target': {'who': 'ANCESTOR_6', 'socket': 'shoulder_L'}, 'dur': 0.7}, 'the bloodline as a chain'),
           ('ANCESTOR_6', 'reach', 'forsaken', {'side': 'R', 'target': {'who': 'ANCESTOR_5', 'socket': 'shoulder_L'}, 'dur': 0.7}),
           ('ANCESTOR_5', 'reach', 'times#2', {'side': 'R', 'target': {'who': 'ANCESTOR_1', 'socket': 'shoulder_L'}, 'dur': 0.7}),
           ('ANCESTOR_1', 'reach', 'tears', {'side': 'R', 'target': {'who': 'POET', 'socket': 'shoulder_L'}, 'dur': 0.7}, 'the nearest on POET\'s shoulder'),
           ('POET', 'head_lowers', 'history', {'deg': 14}),
           ('POET', 'hold_gesture', 'blood', {'side': 'L', 'name': 'hand_chest', 'dur': 0.6}, 'their blood flows through my hands'),
           ('POET', 'hold_gesture', 'blood', {'side': 'R', 'name': 'palm_out', 'dur': 0.6}),
           ('POET', 'release', 'powers', {'side': 'L'}), ('POET', 'release', 'powers', {'side': 'R'}),
           ('POET', 'head_raises', 'sun'),
           ('POET', 'turn', 'baritone', {'to': 'camera', 'dur': 0.5}, 'the voice drops'),
           ('POET', 'head_lowers', 'Beware', {'deg': -8}, '"beware of me"')],
    joins=[dict(kind='screen', surface='haze_0', word='history', end_word='travel', title='Kentucky Pioneers', query='pioneers walking history',
                mix=0.55, blend='screen', tint='sepia(0.4)', why='"a history too battered and bruised to travel"'),
           dict(kind='screen', surface='haze_0', word='blood', end_word='powers', title='Labor of Thy Hands', query='hands working close up',
                mix=0.6, blend='screen', tint='sepia(0.3)', why='"their blood flows through my hands"'),
           dict(kind='screen', surface='haze_0', word='baritone', title='Sound And The Story', query='singer voice microphone',
                mix=0.55, blend='screen', tint='grayscale(0.3)', why='"deepening my voice to a baritone of a million cries"')],
    fx=[dict(kind='prop', prop='star', size_cm=5, keys=[{'t': 16.0, 'who': 'POET', 'side': 'L'}, {'t': 21.0, 'hide': True}]),
        dict(kind='prop', prop='star', size_cm=5, keys=[{'t': 16.0, 'who': 'POET', 'side': 'R'}, {'t': 21.0, 'hide': True}]),
        dict(kind='sunrise', t0=22.4, t1=27.0, at=[700, 640], r0=60, r1=700, rise=30, ground_y=700)],
    camera={'keys': [{'t': 0, 'zoom': 1.1, 'x': 960, 'y': 640}, {'t': 26, 'zoom': 1.2, 'x': 940, 'y': 660}, {'t': 32.3, 'zoom': 1.3, 'x': 920, 'y': 600}],
            'shakes': [{'t': 26.2, 'dur': 0.6, 'amp': 7}, {'t': 30.8, 'dur': 0.8, 'amp': 10}]},
    notes=['The bloodline as a chain: four ancestors in a diagonal line behind POET, each with a hand on the shoulder of the one in front (reaches to shoulder sockets, measured as contacts; overlaps are touch beats).',
           'Light pulses in his hands on "their blood flows through my hands" (star cards on his hands); the ground trembles on "baritone" and "beware of me" (camera shakes).'])

GATE = dict(walkable=[[300, 600], [1650, 600], [1700, 840], [250, 840]], marks={'door': [975, 668]},
            surfaces=[{'id': 'door_1', 'base_y': 655}, {'id': 'pane_0', 'base_y': 640}])
SPECS['05.5'] = dict(
    patch=GATE,
    cast=[dict(id='POET', **POET_TRACK, view='back', side='R', place=[960, 770]),
          dict(id='ANCESTOR_1', **A_ELD, view='threequarter_back', side='L', place=[640, 760]),
          dict(id='ANCESTOR_2', **A_IND, view='threequarter_back', side='R', place=[1300, 765])],
    beats=[('POET', 'walk_to', 1.0, {'to': [975, 700], 'speed': 0.5}, 'before the winged gate'),
           ('ANCESTOR_1', 'walk_to', 1.4, {'to': [760, 700], 'speed': 0.5}),
           ('ANCESTOR_2', 'walk_to', 1.6, {'to': [1190, 702], 'speed': 0.5}),
           ('POET', 'hold_gesture', 4.6, {'side': 'L', 'name': 'palm_out', 'dur': 0.8}, 'the gate opens'),
           ('POET', 'hold_gesture', 4.6, {'side': 'R', 'name': 'palm_out', 'dur': 0.8}),
           ('POET', 'release', 6.6, {'side': 'L'}), ('POET', 'release', 6.6, {'side': 'R'}),
           ('POET', 'walk_to', 6.8, {'to': 'door', 'speed': 0.5}, 'walks between the stone wings')],
    joins=[dict(kind='wipe', surface='door_1', word=2.2, title='A Poem in Marble', query='marble building columns',
                mix=0.85, blend='source-over', tint='sepia(0.2) brightness(1.1)', why='the gate leaves of marble open (no words: the reading is silent here)'),
           dict(kind='screen', surface='pane_0', word=4.0, title="World's Fair Night Aerials", query='city lights at night',
                mix=0.8, blend='source-over', tint='contrast(1.1)', why='beyond, the glow of a city on the water (Atlantis)')],
    fx=[LANTERN('ANCESTOR_1', 'L'), LANTERN('ANCESTOR_2'), dict(kind='sweep', t0=2.0, t1=9.4, period=3.2, width=300, alpha=0.25, color='#e8f0ff')],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 500}, {'t': 9.4, 'zoom': 1.18, 'x': 975, 'y': 460}]},
    notes=['UNREAD: the reading says nothing in this window (the gate lines are spoken at the top of 06.1), so the beats are on seconds, not words.',
           'Lane C marks the winged marble gate "needs a plate": a neon alley with a red double door stands in; the door is the gate (a wipe opens marble archive in it).'])
# ───────────────────────── 06 · Resurrecting Atlantis ─────────────────────────
TRAV = dict(character='atlantis_traveler')
CIT = dict(character='atlantis_citizen')
ELDER = dict(character='atlantis_elder')
KEEPER = dict(character='atlantis_gatekeeper')
SPECS['06.1'] = dict(
    patch=dict(surfaces=[{'id': 'haze_5', 'base_y': 430}, {'id': 'wall_1', 'base_y': 470}]),
    cast=[dict(id='POET', **POET_TRACK, view='back', side='R', place=[860, 652]),
          dict(id='ELDER_1', **ELDER, view='back', side='L', place=[700, 590]),
          dict(id='CROWD_1', **TRAV, view='back', side='R', place=[1000, 560]),
          dict(id='CROWD_2', **TRAV, view='back', side='R', place=[1150, 600])],
    beats=[('CROWD_1', 'walk_to', 'gates', {'to': [1010, 470], 'speed': 0.45}, 'a file of travellers walks out over the water'),
           ('ELDER_1', 'walk_to', 'wings', {'to': [780, 500], 'speed': 0.4}),
           ('CROWD_2', 'walk_to', 'evolution', {'to': [1120, 490], 'speed': 0.45}),
           ('POET', 'walk_to', 'Poets', {'to': [900, 540], 'speed': 0.5}, 'POET walks among them'),
           ('POET', 'head_lowers', 'comets', {'deg': -18}, 'head turned up to the comets'),
           ('POET', 'head_raises', 'consciousness')],
    joins=[dict(kind='screen', surface='haze_5', word='hymns', end_word='us', title='Back of the Mike', query='orchestra musicians playing',
                mix=0.5, blend='screen', tint='sepia(0.3)', why='"the hymns our creator composed with an orchestra of our ancestors\' wildest dreams"'),
           dict(kind='screen', surface='wall_1', word='yellow', end_word='places', title='American Road', query='road highway travel',
                mix=0.45, blend='screen', tint='sepia(0.4)', why='"poets who eased generations down yellow brick roads"'),
           dict(kind='screen', surface='haze_5', word='comets', title='Excursion to the Moon', query='rocket moon stars',
                mix=0.6, blend='screen', tint='sepia(0.3)', why='"to follow comets to the capital city": Excursion to the Moon (1908)')],
    fx=[LANTERN('ELDER_1', 'R'),
        dict(kind='prop', prop='orb', size_cm=10, keys=[{'t': 19.9, 'who': 'CROWD_2', 'joint': 'chest'}, {'t': 23.0, 'at': [1240, 160], 'ground_y': 470, 'ease': 'linear'}, {'t': 23.1, 'hide': True}]),
        dict(kind='prop', prop='star', size_cm=40, keys=[{'t': 23.6, 'at': [1900, 60], 'ground_y': 470}, {'t': 27.6, 'at': [1050, 330], 'ground_y': 470, 'ease': 'linear'}, {'t': 27.8, 'hide': True}]),
        dict(kind='flash', times=[27.6], dur=0.5, alpha=0.3, color='#ffe6b0')],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 900, 'y': 450}, {'t': 28.2, 'zoom': 1.15, 'x': 960, 'y': 440}]},
    notes=['The gate lines open the reading of 06; the causeway plate is lane C\'s (a waterway under a bridge): the travellers walk out over the black water toward the far city (the plate has no causeway: they stand on water, flagged).',
           'A small light lifts out of a traveller\'s chest on "plucked our souls" (orb card on his chest joint), and a comet crosses to the capital on "comets".'])

SPECS['06.2'] = dict(
    patch=dict(surfaces=[{'id': 'water_0', 'base_y': 720}, {'id': 'wall_1', 'base_y': 600}]),
    cast=[dict(id='POET', **POET_TRACK, view='back', side='R', place=[960, 960]),
          dict(id='CROWD_1', **TRAV, view='back', side='R', place=[560, 880]),
          dict(id='CROWD_3', **CIT, view='back', side='L', place=[1380, 900])],
    beats=[('POET', 'hold_gesture', 'Here', {'side': 'L', 'name': 'palm_out', 'dur': 0.7}, 'arms opening: "here we are all one"'),
           ('POET', 'hold_gesture', 'Here', {'side': 'R', 'name': 'palm_out', 'dur': 0.7}),
           ('POET', 'release', 'pack', {'side': 'L'}), ('POET', 'release', 'pack', {'side': 'R'}),
           ('POET', 'walk_to', 'nature', {'to': [940, 900], 'speed': 0.5}, 'the water draws back past his shoes'),
           ('CROWD_1', 'walk_to', 'abandon', {'to': [620, 830], 'speed': 0.5}),
           ('CROWD_3', 'walk_to', 'abandon', {'to': [1320, 840], 'speed': 0.5}),
           ('POET', 'head_lowers', 'best', {'deg': -10})],
    joins=[dict(kind='screen', surface='wall_1', word='Atlantis', end_word='one', title='World of Tomorrow', query='city towers future',
                mix=0.55, blend='screen', tint='grayscale(0.3) contrast(1.1)', why='"resurrecting Atlantis": the city of tomorrow on the risen skyline'),
           dict(kind='screen', surface='water_0', word='pack', end_word='nature', title='Zuyderzee', query='dikes water reclaimed land sea',
                mix=0.5, blend='screen', tint='grayscale(0.4)', why='"the pact we\'ve made here with nature": the sea drawn back (Zuyderzee works, 1930)')],
    fx=[dict(kind='sunrise', t0=5.0, t1=11.8, at=[960, 500], r0=60, r1=500, rise=60, ground_y=700)],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 600}, {'t': 11.8, 'zoom': 1.1, 'x': 960, 'y': 580}]},
    notes=['The waterline falls: the travellers stand along the shore (lane C\'s waterfront plate: the ground plane is the shallow water), POET opens his arms on "here we are all one" and steps forward as the water draws back.'])

QUEUE = [[830, 705], [655, 711], [480, 717], [305, 723], [130, 729]]
SPECS['06.3'] = dict(
    patch=dict(GATE, walkable=[[60, 600], [1650, 600], [1700, 840], [60, 840]], marks={'door': [975, 668], 'booth': [1000, 700]}),
    cast=[dict(id='GATEKEEPER_1', **KEEPER, view='threequarter', side='L', place=[1190, 690]),
          dict(id='POET', **POET_TRACK, view='profile', side='R', place=[1000, 700]),
          dict(id='CROWD_2', **TRAV, view='profile', side='R', place=QUEUE[0]),
          dict(id='CROWD_3', **CIT, view='profile', side='R', place=QUEUE[1]),
          dict(id='CROWD_4', **CIT, view='profile', side='R', place=QUEUE[2]),
          dict(id='CROWD_5', **CIT, view='threequarter_back', side='R', place=QUEUE[3]),
          dict(id='CROWD_6', **CIT, view='threequarter_back', side='R', place=QUEUE[4])],
    beats=[('POET', 'hand_off', 'currency', {'to': 'GATEKEEPER_1', 'prop': 'coin', 'side': 'R', 'to_side': 'R', 'dur': 0.5}, 'sets a glowing coin on the counter'),
           ('GATEKEEPER_1', 'head_lowers', 'mission', {'deg': 14}, 'nods him through'),
           ('GATEKEEPER_1', 'head_raises', 'but'),
           ('POET', 'walk_to', 'safe', {'to': 'door', 'speed': 0.5}, 'walks in'),
           ('POET', 'vanish', 'one', {'dur': 0.8}),
           ('CROWD_2', 'walk_to', 'pack', {'to': 'booth', 'speed': 0.5}, 'the queue moves up'),
           ('CROWD_3', 'walk_to', 'made', {'to': QUEUE[0], 'speed': 0.5}),
           ('CROWD_4', 'walk_to', 'nature', {'to': QUEUE[1], 'speed': 0.5}),
           ('CROWD_5', 'walk_to', 'abandon', {'to': QUEUE[2], 'speed': 0.5}),
           ('CROWD_6', 'walk_to', 'hope', {'to': QUEUE[3], 'speed': 0.5}),
           ('CROWD_2', 'hand_off', 'relearned#2', {'to': 'GATEKEEPER_1', 'prop': 'coin', 'side': 'R', 'to_side': 'R', 'dur': 0.5}),
           ('GATEKEEPER_1', 'head_lowers', 'mission#2', {'deg': 14}),
           ('GATEKEEPER_1', 'head_raises', 'here#4'),
           ('CROWD_2', 'walk_to', 'safe#2', {'to': 'door', 'speed': 0.5}),
           ('CROWD_2', 'vanish', 'flickering', {'dur': 0.8})],
    goals=[dict(who='GATEKEEPER_1', kind='face', args={'who': 'POET'}, t1=8.0)],
    joins=[dict(kind='screen', surface='door_1', word='currency', end_word='mission', title='Banks And Credits', query='money coins bank',
                mix=0.7, blend='source-over', tint='sepia(0.3)', why='"a relearned currency we reassess as a mission"'),
           dict(kind='wipe', surface='door_1', word='safe', end_word='best', title='Gift of Green', query='green nature plants growing',
                mix=0.8, blend='source-over', tint='saturate(1.1)', why='"here we are all safe … the pact we\'ve made here with nature"'),
           dict(kind='screen', surface='pane_0', word='candlelight', title='Coffee House Rendezvous', query='candle light faces smiling',
                mix=0.85, blend='source-over', tint='sepia(0.3) brightness(1.2)', why='"an unfamiliar flickering candlelight illuminating smiles" in the lantern-window')],
    fx=[dict(kind='prop', prop='coin', keys=[{'t': 1.4, 'who': 'POET', 'side': 'R'}, {'t': 2.4, 'who': 'GATEKEEPER_1', 'side': 'R'}, {'t': 3.4, 'hide': True}]),
        dict(kind='prop', prop='coin', keys=[{'t': 16.8, 'who': 'CROWD_2', 'side': 'R'}, {'t': 17.8, 'who': 'GATEKEEPER_1', 'side': 'R'}, {'t': 18.8, 'hide': True}])],
    camera={'keys': [{'t': 0, 'zoom': 1.02, 'x': 800, 'y': 520}, {'t': 29.8, 'zoom': 1.1, 'x': 860, 'y': 500}]},
    notes=['The admission booth is the gate of 05.5\'s alley (lane C uses the same plate): POET pays with a glowing coin (hand_off to the GATEKEEPER, measured), is nodded through and walks in through the door; the queue moves up and the next traveller pays.',
           'The citizens behind the lantern-window are archive (Coffee House Rendezvous, 1969) in the plate\'s one vertical window pane.'])

STREET = dict(surfaces=[{'id': 'door_0', 'base_y': 1080}])
SPECS['06.4'] = dict(
    patch=STREET,
    cast=[dict(id='POET', **POET_TRACK, view='back', side='R', place=[985, 905]),
          dict(id='CROWD_7', **CIT, view='front', side='R', place=[1148, 720]),
          dict(id='CROWD_8', **CIT, view='threequarter', side='L', place=[905, 760]),
          dict(id='MUSICIAN_1', **CIT, view='threequarter', side='R', place=[856, 822])],
    beats=[('POET', 'walk_to', 'where', {'to': [1020, 745], 'speed': 0.5}, 'down the narrow street'),
           ('CROWD_7', 'walk_to', 'night', {'to': [1165, 880], 'speed': 0.5}, 'a citizen walks the other way'),
           ('MUSICIAN_1', 'hold_gesture', 0.0, {'side': 'R', 'name': 'hand_chest', 'dur': 0.3}, 'plays'),
           ('MUSICIAN_1', 'hold_gesture', 0.0, {'side': 'L', 'name': 'hand_low', 'dur': 0.3}),
           ('POET', 'turn', 'joyful', {'to': 'left', 'dur': 0.5}, 'to the musician'),
           ('POET', 'head_lowers', 'heal', {'deg': -12}),
           ('POET', 'turn', 'clouds', {'to': 'away', 'dur': 0.5})],
    goals=[dict(who='MUSICIAN_1', kind='sway_to_beat', args={'bpm': 100, 'amp': 0.8}), dict(who='CROWD_8', kind='sway_to_beat', args={'bpm': 100, 'amp': 0.5})],
    joins=[dict(kind='screen', surface='door_0', word='shadows', end_word='love', title='Third Avenue El', query='shadows street elevated train',
                mix=0.65, blend='screen', tint='grayscale(0.3) contrast(1.2)', why='"where shadows cast from narrow streets"'),
           dict(kind='screen', surface='door_0', word='joyful', end_word='rainbows', title='Coney Island At Night', query='lights rides night',
                mix=0.7, blend='screen', tint='saturate(1.3)', why='"the joyful noises that color rainbows"'),
           dict(kind='screen', surface='door_0', word='clouds', title='Moon And Cloud', query='clouds moving moon',
                mix=0.65, blend='screen', tint='grayscale(0.3)', why='"and set clouds free"')],
    fx=[dict(kind='sweep', t0=5.4, t1=9.2, period=1.3, width=220, alpha=0.35, color='#ff6a6a'),
        dict(kind='sweep', t0=5.8, t1=9.2, period=1.5, width=220, alpha=0.35, color='#6aff9a', dir=-1),
        dict(kind='sweep', t0=6.2, t1=9.2, period=1.7, width=220, alpha=0.35, color='#6a9aff')],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 560}, {'t': 13.8, 'zoom': 1.12, 'x': 980, 'y': 520}]},
    notes=['Lane C\'s narrow_streets is an Atlantis view (view_007); only that plate is used.',
           'A street musician sways at 100 bpm; the joyful noise throws rainbow light (three coloured sweeps) on "rainbows".'])

PLAZA = dict(surfaces=[{'id': 'water_0', 'base_y': 720}, {'id': 'wall_1', 'base_y': 600}])
SPECS['06.5'] = dict(
    patch=PLAZA,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='R', place=[960, 940]),
          dict(id='CROWD_3', **CIT, view='threequarter', side='L', place=[520, 760]),
          dict(id='CROWD_7', **CIT, view='profile', side='L', place=[1440, 780])],
    beats=[('POET', 'hold_gesture', 0.0, {'side': 'R', 'name': 'hand_chest', 'dur': 0.2}, 'braced: hand at his chest'),
           ('POET', 'head_lowers', 0.0, {'deg': 18}, 'chin down'),
           ('POET', 'head_raises', 'stay', None, 'head up'),
           ('POET', 'release', 'leaving', {'side': 'R'}, 'unclenches'),
           ('POET', 'hold_gesture', 'continuums', {'side': 'R', 'name': 'palm_out', 'dur': 0.6}, 'hand open'),
           ('POET', 'head_lowers', 'serendipity', {'deg': -14}, 'face lifts: "it could stay here forever"')],
    goals=[dict(who='CROWD_3', kind='wander', args={'bpm': 90, 'every_bars': 2, 'step_cm': 60, 'seed': 3, 'zone': [[380, 740], [760, 740], [760, 800], [380, 800]]}),
           dict(who='CROWD_7', kind='wander', args={'bpm': 90, 'every_bars': 2, 'step_cm': 60, 'seed': 8, 'zone': [[1260, 750], [1600, 750], [1600, 810], [1260, 810]]})],
    joins=[dict(kind='screen', surface='wall_1', word='crosshairs', end_word='continuums', title='Space Navigation', query='target navigation instruments',
                mix=0.5, blend='screen', tint='grayscale(0.4)', why='"leaving behind crosshairs for continuums"'),
           dict(kind='screen', surface='water_0', word='serendipity', title='Sun Peeks', query='sun behind clouds',
                mix=0.5, blend='screen', tint='sepia(0.2)', why='"strains for serendipity"')],
    fx=[dict(kind='reticle', at=[960, 570], t0=0.0, t_open=5.4, dur=2.6, r_px=230)],
    camera={'keys': [{'t': 0, 'zoom': 1.15, 'x': 960, 'y': 640}, {'t': 10.5, 'zoom': 1.0, 'x': 960, 'y': 560}]},
    notes=['A scope reticle sits on POET (lib/fx_extra.js reticle); on "crosshairs" its arms dissolve into rings that widen off the frame while he unclenches: hand off the chest, head up, palm open.',
           'Lane C uses the waterfront plate for the plaza (no plaza plate): he stands in the shallows before the city.'])

SPECS['06.6'] = dict(
    patch=PLAZA,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter_back', side='R', place=[960, 920]),
          dict(id='CROWD_1', **TRAV, view='threequarter', side='R', place=[380, 860]),
          dict(id='CROWD_3', **CIT, view='threequarter', side='L', place=[1560, 870]),
          dict(id='CROWD_7', **CIT, view='threequarter', side='R', place=[600, 760]),
          dict(id='ELDER_1', **ELDER, view='threequarter', side='L', place=[1360, 765]),
          dict(id='GUEST_1', character='party_guest', view='threequarter', side='L', place=[1660, 800])],
    beats=[('CROWD_1', 'walk_to', 'A', {'to': [700, 875], 'speed': 0.7}, 'citizens walk in'),
           ('CROWD_3', 'walk_to', 'city', {'to': [1230, 880], 'speed': 0.7}),
           ('CROWD_7', 'walk_to', 'born', {'to': [800, 780], 'speed': 0.7}),
           ('ELDER_1', 'walk_to', 'in', {'to': [1160, 778], 'speed': 0.6}),
           ('GUEST_1', 'walk_to', 'unison', {'to': [1420, 820], 'speed': 0.7}),
           ('POET', 'turn', 'welcoming', {'to': 'camera', 'dur': 0.5}, 'met at the middle')] +
          [(w, 'hold_gesture', 'all', {'side': s, 'name': 'arms_up', 'dur': 0.5}, 'everyone raises their arms' if (w, s) == ('POET', 'L') else None)
           for w in ('POET', 'CROWD_1', 'CROWD_3', 'CROWD_7', 'ELDER_1', 'GUEST_1') for s in ('L', 'R')],
    joins=[dict(kind='screen', surface='wall_1', word='city', title="World's Fair Night Aerials", query='city lights night aerial',
                mix=0.6, blend='screen', tint='saturate(1.2)', why='"a city born in unison": every window lights at once')],
    fx=[dict(kind='flash', times=[0.6], dur=1.2, alpha=0.3, color='#ffd9a0'), LANTERN('ELDER_1', 'L')],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 960, 'y': 560}, {'t': 8.1, 'zoom': 1.06, 'x': 960, 'y': 600}]},
    notes=['The plaza fills: five citizens walk in to meet POET at the middle; on the last word "all" everyone raises both arms together.',
           '06.6c-d (wandering to the house where people go in) are not staged: the next scene opens inside the party.'])
# ───────────────────────── 07 · DJ Turn Me Up ─────────────────────────
# lane C house_party (gen_9c5f9c7c4a_70): a long concrete room; the right wall (wall_0) is the party's projection wall.
DJ = dict(character='dj')
PG = dict(character='party_guest')
MIC = lambda t=0.0: dict(kind='prop', prop='mic', keys=[{'t': t, 'who': 'POET', 'side': 'R'}])
FLOOR_07 = surface_poly('07.1', 'floor_4'), surface_poly('07.1', 'floor_5')
PARTY = dict(walkable=list(FLOOR_07), marks={'bar': [330, 960], 'stand': [820, 780], 'booth': [620, 745]},
             surfaces=[{'id': 'wall_0', 'base_y': 1000}, {'id': 'wall_0a', 'kind': 'pane', 'polygon': [[1290, 140], [1460, 150], [1460, 840], [1290, 860]], 'base_y': 1000},
                       {'id': 'wall_0b', 'kind': 'pane', 'polygon': [[1490, 150], [1660, 160], [1660, 820], [1490, 838]], 'base_y': 1000},
                       {'id': 'wall_0c', 'kind': 'pane', 'polygon': [[1690, 160], [1880, 170], [1880, 800], [1690, 816]], 'base_y': 1000},
                       {'id': 'micstand', 'kind': 'screen', 'polygon': [[858, 560], [874, 560], [874, 780], [858, 780]], 'base_y': 780}])
STAND = dict(kind='prop', prop='micstand', h_cm=150, keys=[{'t': 0, 'at': [866, 780], 'ground_y': 780}])
GROOVE = lambda ids, bpm=96: [dict(who=g, kind='sway_to_beat', args={'bpm': bpm, 'amp': 0.8, 'phase': 0.2 * i}) for i, g in enumerate(ids)]
SPECS['07.1'] = dict(
    patch=PARTY,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='R', place=[330, 960]),
          dict(id='DJ', **DJ, view='front', side='R', place=[620, 745]),
          dict(id='GUEST_1', **PG, view='threequarter_back', side='L', place=[880, 820]),
          dict(id='GUEST_2', **PG, view='threequarter_back', side='R', place=[220, 1010])],
    beats=[('DJ', 'drop', 0.0, {'cm': -260, 'dur': 0.01}, 'above the booth'),
           ('DJ', 'rise', 'DJ', {'cm': 0, 'dur': 0.5, 'ease': 'in'}, 'drops into the house'),
           ('DJ', 'hold_gesture', 'please', {'side': 'R', 'name': 'hand_low', 'hand': 'pinch', 'dur': 0.3}, 'spins / scratches'),
           ('DJ', 'hold_gesture', 'please', {'side': 'L', 'name': 'hand_low', 'dur': 0.3}),
           ('POET', 'hold_gesture', 'eyes', {'side': 'R', 'name': 'hand_chest', 'dur': 0.5}, 'mic up, eyes shut'),
           ('POET', 'head_lowers', 'chin', {'deg': 22}, 'chin nested'),
           ('POET', 'wince', 'weight', {'amp': 0.6}, 'pressed lower by the weight')],
    goals=GROOVE(['DJ', 'GUEST_1', 'GUEST_2']) + [dict(who='GUEST_1', kind='face', args={'who': 'DJ'}), dict(who='GUEST_2', kind='face', args={'who': 'DJ'})],
    joins=[dict(kind='screen', surface='wall_0', word='turn', title='Chevrolet Sales Convention Musical', query='stage show dancers band',
                mix=0.6, blend='screen', tint='saturate(1.2)', why='"DJ turn me up please" on the projection wall')],
    fx=[MIC(), dict(kind='strobe', bpm=96, t0=1.0, t1=8.7, alpha=0.1, colors=['#ff4fa8', '#4f8bff'])],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 900, 'y': 640}, {'t': 8.7, 'zoom': 1.08, 'x': 760, 'y': 700}]},
    notes=['The DJ drops into the house onto the booth spot (drop/rise) and goes into the groove; guests sway at 96 bpm and face the booth by goal; POET at the bar, mic up (a mic card on his hand), chin tucked.'])

SPECS['07.2'] = dict(
    patch=PARTY,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='R', place=[330, 960]),
          dict(id='EX', **EX, view='back', side='R', place=[720, 775], alpha=0.5),
          dict(id='GUEST_3', **PG, view='threequarter', side='L', place=[900, 860]),
          dict(id='GUEST_4', **PG, view='threequarter', side='L', place=[1010, 905])],
    beats=[('POET', 'hold_gesture', 0.0, {'side': 'R', 'name': 'hand_chest', 'dur': 0.2}, 'mic up'),
           ('POET', 'head_lowers', 0.0, {'deg': 16}),
           ('POET', 'hold_gesture', 'story', {'side': 'L', 'name': 'palm_out', 'dur': 0.6}, 'other hand opens outward'),
           ('EX', 'walk_to', 'ghosts', {'to': [640, 668], 'speed': 0.35, 'keep_facing': True}, 'a translucent ghost walks away, back to us'),
           ('GUEST_3', 'hold_gesture', 'ghosts', {'side': 'R', 'name': 'hand_chest', 'dur': 0.6}, 'leans in, hand on her chest'),
           ('EX', 'vanish', 'dying', {'dur': 1.4}),
           ('POET', 'release', 'veneers', {'side': 'L'})],
    goals=[dict(who='GUEST_3', kind='face', args={'who': 'POET'}), dict(who='GUEST_4', kind='face', args={'who': 'POET'})],
    joins=[dict(kind='screen', surface='wall_0', word='ghosts', end_word='nourished', title='Golden Harvest', query='orchard fields sun rows',
                mix=0.6, blend='screen', tint='sepia(0.4) brightness(1.1)', why='"the veneers of sun-soaked evergreen fields": the rows on the projection wall')],
    fx=[MIC()],
    camera={'keys': [{'t': 0, 'zoom': 1.06, 'x': 760, 'y': 700}, {'t': 13.8, 'zoom': 1.12, 'x': 700, 'y': 680}]},
    notes=['EX walks away down the room, half transparent (alpha 0.5), back to us, and fades on "dying": the ghost of the story; guests lean in and face POET by goal.'])

SPECS['07.3'] = dict(
    patch=PARTY,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='R', place=[330, 960]),
          dict(id='DJ', **DJ, view='front', side='R', place=[620, 745]),
          dict(id='GUEST_1', **PG, view='threequarter', side='L', place=[700, 975]),
          dict(id='GUEST_5', **PG, view='threequarter', side='L', place=[600, 830])],
    beats=[('POET', 'walk_to', 'love', {'to': 'stand', 'speed': 0.45}, 'walks the length of the room to the mic stand'),
           ('POET', 'turn', 'walked', {'to': 'camera', 'dur': 0.4}),
           ('POET', 'reach', 'So', {'side': 'R', 'target': {'surface': 'micstand', 'at': aim('07.3', 862, 780, 135)}, 'dur': 0.3}, 'his hand closes on the stand on the beat'),
           ('POET', 'head_lowers', 'DJ', {'deg': -12}, 'head lifts to the booth'),
           ('DJ', 'head_lowers', 'turn', {'deg': 14}, 'nods'),
           ('DJ', 'head_raises', 'up')],
    goals=GROOVE(['DJ']) + [dict(who=g, kind='keep_distance', args={'from': 'POET', 'min_cm': 170, 'max_cm': 260, 'speed': 1.0, 'zone': z})
                            for g, z in (('GUEST_1', [[640, 960], [1040, 960], [1040, 1060], [640, 1060]]), ('GUEST_5', [[440, 800], [640, 800], [640, 880], [440, 880]]))],
    joins=[dict(kind='screen', surface='wall_0', word='stars', end_word='glares', title='Moonwalk One', query='stars space',
                mix=0.55, blend='screen', tint='contrast(1.1)', why='"defamed unsalted stars diminish their glares"'),
           dict(kind='screen', surface='wall_0', word='thousand', end_word='heard', title="Who's Out There", query='galaxy telescope stars',
                mix=0.55, blend='screen', tint='contrast(1.1)', why='"I\'ve walked a thousand light years across the greatest divide"')],
    fx=[MIC(), STAND, dict(kind='darken', t0=7.8, dur=1.6, alpha=0.25)],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 760, 'y': 640}, {'t': 19.4, 'zoom': 1.15, 'x': 800, 'y': 600}]},
    notes=['POET leaves the bar and walks through the crowd to the mic stand; the guests part for him by goal (keep_distance 170-260 cm); his hand lands on the stand on "So" (a reach to the stand, measured as a contact).'])

AT_STAND = [820, 780]
SPECS['07.4'] = dict(
    patch=PARTY,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='L', place=AT_STAND),
          dict(id='GUEST_2', **PG, view='threequarter_back', side='L', place=[1000, 900]),
          dict(id='GUEST_6', **PG, view='threequarter_back', side='R', place=[560, 880])],
    beats=[('POET', 'hold_gesture', 'diverging', {'side': 'L', 'name': 'palm_out', 'dur': 0.5}, 'pushes two invisible things apart'),
           ('POET', 'hold_gesture', 'diverging', {'side': 'R', 'name': 'reach_out', 'dur': 0.5}),
           ('POET', 'release', 'souls', {'side': 'L'}), ('POET', 'release', 'souls', {'side': 'R'}),
           ('POET', 'head_lowers', 'home', {'deg': 14}),
           ('POET', 'head_raises', 'Maybe')],
    goals=GROOVE(['GUEST_2', 'GUEST_6'], 88),
    joins=[dict(kind='screen', surface='wall_0', word='shared', end_word='streets', title='Transportation: Bus, Truck', query='moving truck street',
                mix=0.6, blend='screen', tint='grayscale(0.3)', why='"a shared home boxed in truck on separate one-way streets"'),
           dict(kind='screen', surface='wall_0', word='u', end_word='signs', title="Show 'Em the Road", query='road signs traffic',
                mix=0.6, blend='screen', tint='grayscale(0.3)', why='"not built with u-turns or stop signs"')],
    fx=[STAND, dict(kind='prop', prop='ring', size_cm=60, spin_dps=20, keys=[{'t': 1.0, 'at': [1560, 430], 'ground_y': 1000}, {'t': 5.2, 'at': [1400, 240], 'ground_y': 1000}]),
        dict(kind='prop', prop='ring', size_cm=60, spin_dps=-20, keys=[{'t': 1.0, 'at': [1600, 450], 'ground_y': 1000}, {'t': 5.2, 'at': [1780, 650], 'ground_y': 1000}, {'t': 6.6, 'hide': True}])],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 1000, 'y': 600}, {'t': 16.8, 'zoom': 1.06, 'x': 1040, 'y': 600}]},
    notes=['Two wedding bands slide apart across the projection wall (ring cards on "wedding bands diverging") while POET pushes two invisible things apart; the trucks and one-way streets are archive on the same wall.'])

SPECS['07.5'] = dict(
    patch=PARTY,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='L', place=AT_STAND),
          dict(id='GUEST_3', **PG, view='threequarter', side='L', place=[980, 880]),
          dict(id='GUEST_4', **PG, view='threequarter', side='R', place=[600, 900])],
    beats=[('POET', 'hold_gesture', 'daisy', {'side': 'L', 'name': 'page_up', 'dur': 0.5}, 'holds a daisy up to the mic'),
           ('GUEST_3', 'hold_gesture', 'love', {'side': 'R', 'name': 'arms_up', 'hand': 'fist', 'dur': 0.5}, 'holds up a lighter'),
           ('GUEST_4', 'hold_gesture', 'love', {'side': 'L', 'name': 'hand_chest', 'dur': 0.5}, '"we love, we not"'),
           ('POET', 'release', 'future', {'side': 'L'}),
           ('POET', 'hold_gesture', 'empty', {'side': 'L', 'name': 'palm_out', 'dur': 0.4}, 'the empty hand stays open')],
    goals=[dict(who=g, kind='face', args={'who': 'POET'}) for g in ('GUEST_3', 'GUEST_4')],
    joins=[dict(kind='screen', surface='wall_0', word='daisy', end_word='not', title='Spring Comes to a Pond', query='flower petals',
                mix=0.55, blend='screen', tint='saturate(1.1)', why='"each plucked off as daisy petals, we love, we not"'),
           dict(kind='screen', surface='wall_0', word='future', title='They Grow Up So Fast', query='children growing family',
                mix=0.55, blend='screen', tint='grayscale(0.4)', why='"of a future gone swiftly and a past left empty"')],
    fx=[STAND] + [dict(kind='prop', prop='petal', size_cm=3, color='#f4f1e6', keys=[{'t': 4.1, 'who': 'POET', 'side': 'L'}, {'t': 3.1 + 0.6 * i + 1.0, 'who': 'POET', 'side': 'L'},
                                                                                   {'t': 3.1 + 0.6 * i + 2.2, 'at': [780 + 18 * i, 780], 'ground_y': 780}]) for i in range(5)]
       + [dict(kind='glow', at=[980, 600], ground_y=880, times=[5.8, 6.4], r_cm=40, dur=0.8, color='rgba(255,180,90,1)')],
    camera={'keys': [{'t': 0, 'zoom': 1.12, 'x': 820, 'y': 600}, {'t': 10.4, 'zoom': 1.2, 'x': 820, 'y': 580}]},
    notes=['POET holds a daisy to the mic and petals fall from his hand to the floor one by one (petal cards); a guest raises a lighter on "we love".',
           'Needs: a daisy prop card with petals as separate brads (here the petals are code cards and the daisy head is not drawn).'])

SPECS['07.6'] = dict(
    patch=PARTY,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='R', place=AT_STAND),
          dict(id='DJ', **DJ, view='front', side='R', place=[640, 700])],
    beats=[('POET', 'turn', 'pick', {'to': 'right', 'dur': 0.4}, 'to the wall'),
           ('POET', 'hold_gesture', 'road', {'side': 'R', 'name': 'reach_out', 'hand': 'point', 'dur': 0.4}, 'points to each road'),
           ('POET', 'release', 'night', {'side': 'R'}),
           ('POET', 'hold_gesture', 'cloud', {'side': 'R', 'name': 'reach_out', 'hand': 'point', 'dur': 0.4}, 'lingers on the third'),
           ('DJ', 'hold_gesture', 'silver', {'side': 'R', 'name': 'hand_chest', 'dur': 0.4}, 'lifts his headphones off one ear')],
    goals=GROOVE(['DJ'], 88),
    joins=[dict(kind='screen', surface='wall_0a', word='rain', title='Rain On Budded Tree', query='heavy rain', mix=0.7, blend='screen', tint='grayscale(0.3)', why='"a road of heavy rain"'),
           dict(kind='screen', surface='wall_0b', word='fog', title='Low-Lying Fog', query='fog', mix=0.7, blend='screen', tint='grayscale(0.3)', why='"or a frontal fog"'),
           dict(kind='screen', surface='wall_0c', word='lights', title='Small Town Intersection', query='street lights night', mix=0.7, blend='screen', tint='contrast(1.1)',
                why='"or of dim night lights under a cloud with the silver lining"')],
    fx=[STAND],
    camera={'keys': [{'t': 0, 'zoom': 1.0, 'x': 1100, 'y': 560}, {'t': 10.2, 'zoom': 1.05, 'x': 1150, 'y': 540}]},
    notes=['The projection wall splits into three vertical panels (scene surfaces cut from lane C\'s wall_0): rain, fog, night lights, each opening on its word; POET points to them.'])

SPECS['07.7'] = dict(
    patch=PARTY,
    cast=[dict(id='POET', **POET_TRACK, view='threequarter', side='L', place=AT_STAND),
          dict(id='DJ', **DJ, view='front', side='R', place=[620, 745]),
          dict(id='GUEST_1', **PG, view='threequarter_back', side='R', place=[560, 880]),
          dict(id='GUEST_5', **PG, view='threequarter_back', side='L', place=[1000, 900])],
    beats=[('POET', 'turn', 'turning', {'to': 'camera', 'dur': 0.6}, 'turns to face the room'),
           ('POET', 'hold_gesture', 'face', {'side': 'L', 'name': 'palm_out', 'dur': 0.6}, 'free arm open'),
           ('POET', 'release', 'tear', {'side': 'L'}),
           ('POET', 'head_lowers', 'Chin', {'deg': -14}, 'chin high'),
           ('DJ', 'hold_gesture', 'volume', {'side': 'R', 'name': 'reach_out', 'dur': 0.4}, 'pushes the master all the way up')] +
          [(w, 'hold_gesture', 'up', {'side': s, 'name': 'arms_up', 'dur': 0.5}, 'the house erupts' if (w, s) == ('GUEST_1', 'L') else None) for w in ('GUEST_1', 'GUEST_5', 'POET') for s in ('L', 'R')],
    goals=GROOVE(['DJ', 'GUEST_1', 'GUEST_5'], 96),
    joins=[dict(kind='screen', surface='wall_0', word='open', end_word='time#4', title='Walk In - Coming Soon', query='theater audience',
                mix=0.6, blend='screen', tint='contrast(1.1)', why='"one open mic at a time"'),
           dict(kind='screen', surface='wall_0', word='volume', title='Coney Island At Night', query='crowd lights rides night',
                mix=0.65, blend='screen', tint='saturate(1.3)', why='"volume turned up"')],
    fx=[STAND, dict(kind='strobe', bpm=96, t0=16.8, t1=21.4, alpha=0.16, colors=['#ff4fa8', '#4f8bff', '#ffe14f'])],
    camera={'keys': [{'t': 0, 'zoom': 1.08, 'x': 820, 'y': 600}, {'t': 21.4, 'zoom': 1.0, 'x': 900, 'y': 600}]},
    notes=['POET turns to the room, arm open, chin high; on "volume turned up" the DJ pushes the master and everyone\'s hands go up with the strobe.'])

if __name__ == '__main__':
    build_poems(SPECS, set(sys.argv[1:]) or None)
