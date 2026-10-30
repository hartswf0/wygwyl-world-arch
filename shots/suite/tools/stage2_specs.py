# Stage 2 blocking (poems 08-14): one entry per scene, compiled by tools/stage2_stage.py into data/scenes/<id>.json.
#
#   cast   suite cast records; 'place' is the foot point on the set's ground (stage px). Scale is never set here:
#          the set's horizon and px/cm size every puppet by where it stands.
#   beats  (word, who, action, args?, label?)   word = the word as read ('moon', 'go#2' = its 2nd reading) or seconds
#   goals  suite goals (Thistle Gulch style: authored beats + autonomous goals); t0/t1 may be words
#   joins  WEAVE joins; 'query' is searched in the archive by lib/archive_grab.py; 'pane' = a pane cut in a real surface
#   fx     set pieces and code layers (lib/stage2_extra.js: card, glow, smoke, pour, stars; suite: strobe, sunrise, deck, darken)
#   camera keys: t = seconds, a word, or -1 (the end of the scene)
#
# POET is a man (he/his) and is played by his 30 painted replacement cards (play/data.json, the tracksuit with red piping):
# a 'pose' beat swaps the card on a word, the walk alternates his two painted stride cards. EX is played by his back-only
# cards (the EX rule). Everyone else is lane B's jointed puppet in their own costume.
PC = 'card.poet.red_black_sunglasses.'
P = lambda n: PC + n
CAFE, PROPS = 'arena/parts/kit3/release_v2/cuts/13.props.cafe/13.props.cafe__', 'arena/parts/kit3/release_v2/cuts/'

def poet(place, id='POET', stand='09', walk=('05', '16'), **kw):
    c = {'id': id, 'character': 'poet', 'costume': 'red_black_sunglasses', 'mode': 'cards', 'view': 'front', 'side': 'R', 'place': place,
         'cards': {'stand': P(stand), 'walk': [P(w) for w in walk], 'dance': P('11')}}
    c.update(kw); return c
def soul(place, id='POET_SOUL', ghost=0.55, **kw):
    return poet(place, id=id, ghost=ghost, **kw)
def jointed(id, ch, place, view='front', side='R', **kw):
    c = {'id': id, 'character': ch, 'costume': ch, 'view': view, 'side': side, 'place': place}; c.update(kw); return c
def dancer(id, ch, cos, place, view='front', side='R'):
    return {'id': id, 'character': ch, 'costume': cos, 'view': view, 'side': side, 'place': place, 'mode': 'cards'}
def ex(place, **kw):
    c = {'id': 'EX', 'character': 'ex', 'costume': 'ex_jacket', 'mode': 'cards', 'view': 'back', 'side': 'R', 'place': place}; c.update(kw); return c
def angel(id, place, side):
    return {'id': id, 'character': 'angel', 'costume': 'angel', 'mode': 'cards', 'play_key': 'angel/robe', 'view': 'front', 'side': side, 'place': place,
            'cards': {'stand': 'card.angel.robe.00'}}
def cam(z0, x0, y0, z1=None, x1=None, y1=None):
    return {'keys': [{'t': 0, 'zoom': z0, 'x': x0, 'y': y0}, {'t': -1, 'zoom': z1 or z0, 'x': x1 or x0, 'y': y1 or y0}]}
def sway(who, bpm=124, amp=1.0, phase=0.0, t0=None, t1=None):
    g = {'who': who, 'kind': 'sway_to_beat', 'args': {'bpm': bpm, 'amp': amp, 'phase': phase}}
    if t0 is not None: g['t0'] = t0
    if t1 is not None: g['t1'] = t1
    return g
def wander(who, zone, seed, bpm=124, every=2, step=60):
    return {'who': who, 'kind': 'wander', 'args': {'bpm': bpm, 'every_bars': every, 'step_cm': step, 'seed': seed, 'zone': zone}}
def card(file, at, h, **kw):
    f = {'kind': 'card', 'file': file, 'at': at, 'height_cm': h}; f.update(kw); return f

# ── shared set geometry (stage px, read off the plates with a 100 px grid) ──
ROOF_RAIL1 = [[672, 640], [792, 705], [792, 955], [672, 825]]                # railing glass pane, near post pair (08 club walkway)
ROOF_RAIL2 = [[800, 712], [952, 808], [952, 1075], [800, 995]]
ROOF_WALLGLASS = [[215, 265], [298, 372], [298, 690], [215, 790]]            # the glass doors in the left wall
STREET_PANEL = {'A': [[880, 385], [965, 385], [965, 555], [880, 555]], 'B': [[985, 393], [1050, 393], [1050, 550], [985, 550]],
                'C': [[1068, 395], [1150, 395], [1150, 545], [1068, 545]], 'D': [[1183, 400], [1250, 400], [1250, 545], [1183, 545]]}
CHAPEL_DOOR_11_1 = [[1140, 470], [1172, 450], [1205, 470], [1205, 600], [1140, 600]]
CHAPEL_DOOR_11_5 = [[1093, 445], [1120, 425], [1147, 445], [1147, 593], [1093, 593]]
CHAPEL_DOOR_13 = [[1053, 480], [1083, 452], [1113, 480], [1113, 605], [1053, 605]]
CHAPEL_WIN_13 = [[1160, 510], [1172, 490], [1184, 510], [1184, 575], [1160, 575]]
TEMPLE_COLONNADE = [[930, 335], [1010, 335], [1010, 470], [930, 470]]         # between the white columns of the island temple
SHORE_DECK = {'kind': 'deck', 'polygon': [[0, 930], [700, 915], [1920, 905], [1920, 1080], [0, 1080]], 'color': 'rgba(34,32,30,.96)',
              'line': 'rgba(150,140,125,.28)', 'ground_y': 905, 'note': 'a painted shore card: the plate is all mirror water'}
HALL_WINDOWS = [[150, 95], [290, 95], [290, 480], [150, 500]]                 # the left window bank of the temple hall (pane_0)
QUAY_WALL = [[70, 170], [300, 120], [300, 470], [70, 560]]                   # a panel of the quay's stone wall
LAUNDRY_CLOTH = [[1500, 250], [1745, 170], [1810, 470], [1560, 550]]         # the olive sheet on the line

SPECS = {}

# ═══════════════════════ 08 · NEWLY SINGLE ═══════════════════════
SPECS['08.2'] = {
 'set_layers': {'P0': 'back', 'P1': 'back'},
 'cast': [poet([450, 745]), soul([610, 718], view='threequarter', side='L', alpha=0),
          dancer('DANCER_1', 'dancer_dress', 'club_dress', [290, 680]), dancer('DANCER_3', 'dancer_jacket', 'club_jacket', [640, 625], 'threequarter', 'L')],
 'goals': [sway('POET', t1='escaped'), sway('DANCER_1', amp=1.1), sway('DANCER_3', phase=0.3),
           wander('DANCER_1', [[250, 650], [330, 650], [330, 720], [230, 720]], 11), wander('DANCER_3', [[610, 610], [660, 610], [680, 660], [620, 660]], 23)],
 'beats': [('escaped', 'POET', 'pose', {'card': '10'}, 'head back: the soul goes'),
           ('escaped', 'POET_SOUL', 'appear', {'dur': 0.8}, 'the vellum soul steps out of him'),
           ('moment', 'POET_SOUL', 'walk_to', {'to': [440, 600], 'speed': 0.6, 'arrive_word': 'flesh'}),
           ('left', 'POET', 'pose', {'card': '21'}, 'left on the dance floor'),
           ('rejection', 'POET', 'pose', {'card': '28'}, 'flesh and bones: he kneels'),
           ('afloat', 'POET_SOUL', 'turn', {'to': 'camera'}),
           ('imagine', 'POET', 'pose', {'card': '21'})],
 'joins': [{'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': ROOF_WALLGLASS, 'ground_y': 790, 'ground_x': 215,
            'query': 'couples dancing ballroom 1950s', 'word': 'dance', 'end_word': 'afloat', 'mix': 0.85,
            'why': 'the dance floor he was left on plays in the glass door of the walkway'}],
 'fx': [{'kind': 'strobe', 'bpm': 124, 'alpha': 0.10, 'colors': ['#ff4fa8', '#4f8bff'], 't1': 'escaped'}],
 'camera': cam(1.0, 460, 640, 1.07, 470, 660),
 'notes': ['The soul is POET\'s own painted cards drawn as vellum (cast.ghost 0.55), as the dossier asks ("the same cards in vellum").',
           'The reading puts this scene first in poem 08 (the breakdown lists it second); scenes are cut and reeled in reading order.'],
}
SPECS['08.1'] = {
 'set_layers': {'P0': 'back', 'P1': 'back'},
 'cast': [poet([500, 625], stand='21'), dancer('DANCER_1', 'dancer_dress', 'club_dress', [300, 700]),
          dancer('DANCER_2', 'dancer_shirt', 'club_shirt', [640, 690], 'threequarter', 'L'), dancer('DANCER_4', 'dancer_shirt', 'club_shirt', [345, 612])],
 'goals': [sway('DANCER_1', amp=1.1), sway('DANCER_2', phase=0.24), sway('DANCER_4', amp=0.9, phase=0.48),
           wander('DANCER_1', [[230, 660], [350, 660], [330, 760], [200, 760]], 11), wander('DANCER_2', [[610, 650], [660, 650], [700, 760], [630, 760]], 23)],
 'beats': [('pulsing', 'POET', 'walk_to', {'to': [450, 770], 'arrive_word': 'music'}, 'walks onto the floor'),
           ('music', 'POET', 'pose', {'card': '06'}, 'head throbbing: hands up against it'),
           ('empty', 'POET', 'pose', {'card': '21'}, 'empty, standing still'),
           ('temptations', 'POET', 'pose', {'card': '08'}, 'open palms')],
 'joins': [{'kind': 'pane', 'surface': 'wall_1', 'inside': False, 'polygon': ROOF_RAIL1, 'ground_y': 825, 'ground_x': 672,
            'query': 'nightclub dancers 1960s go-go', 'word': 'music', 'mix': 0.8, 'blend': 'screen',
            'why': 'the music\'s dancers play in the railing glass, over the city'}],
 'fx': [{'kind': 'strobe', 'bpm': 124, 'alpha': 0.12, 'colors': ['#ff4fa8', '#4f8bff']}],
 'camera': cam(1.0, 450, 640, 1.05, 450, 660),
 'notes': ['Restaged on lane C\'s rooftop set (a glass walkway above the city, no generated crowd in the plate): the crowd is three painted dancer cards.',
           'Dancers dance in their painted dance cards (replacement), swaying on 124 bpm bars and wandering in zones by goal.'],
}
SPECS['08.3'] = {
 'set_layers': {'P0': 'back', 'P1': 'back'},
 'cast': [poet([440, 780], stand='21'), soul([640, 760], ghost=0.5, stand='09'),
          dancer('DANCER_2', 'dancer_dress', 'club_dress', [330, 650]), dancer('DANCER_4', 'dancer_shirt', 'club_shirt', [560, 640], 'threequarter', 'L'),
          dancer('DANCER_3', 'dancer_jacket', 'club_jacket', [480, 610])],
 'goals': [sway('DANCER_2', t1='leave'), sway('DANCER_4', phase=0.3, t1='leave'), sway('DANCER_3', phase=0.6, t1='leave'),
           {'who': 'POET_SOUL', 'kind': 'face', 'args': {'who': 'POET'}}],
 'beats': [('collide', 'DANCER_2', 'walk_to', {'to': [420, 655], 'speed': 0.8}, 'strangers collide'),
           ('collide', 'DANCER_4', 'walk_to', {'to': [520, 652], 'speed': 0.8}),
           ('watch', 'POET', 'pose', {'card': '09'}),
           ('mood', 'POET', 'pose', {'card': '11'}, 'a good one: he moves'),
           ('last', 'POET', 'pose', {'card': '21'}, 'the last one to leave'),
           ('leave', 'DANCER_2', 'walk_to', {'to': [440, 600], 'speed': 0.8}),
           ('leave', 'DANCER_4', 'walk_to', {'to': [520, 605], 'speed': 0.8}),
           ('leave', 'DANCER_3', 'vanish', {'dur': 1.5}),
           ('refraction', 'DANCER_2', 'vanish', {'dur': 1.4}), ('refraction', 'DANCER_4', 'vanish', {'dur': 1.4}),
           ('escape', 'POET', 'pose', {'card': '15'}, 'an escape few pleasures offer')],
 'joins': [{'kind': 'pane', 'surface': 'wall_1', 'inside': False, 'polygon': ROOF_RAIL2, 'ground_y': 995, 'ground_x': 800,
            'query': 'kaleidoscope refraction lights abstract', 'word': 'bitter', 'mix': 0.85, 'blend': 'screen',
            'why': 'the bitter refraction, in the near railing glass'},
           {'kind': 'citizen', 'query': 'man and woman dancing close', 'at': [600, 615], 'height_cm': 160, 'word': 'strangers', 'end_word': 'mood',
            'why': 'archive strangers collide at the back of the floor'}],
 'fx': [{'kind': 'strobe', 'bpm': 124, 'alpha': 0.16, 'colors': ['#ffffff', '#4f8bff'], 't0': 'spark', 't1': 'mood'}],
 'camera': cam(1.04, 470, 640, 1.0, 470, 640),
}
SPECS['08.4'] = {
 'cast': [soul([1320, 560], ghost=0.6, stand='09', walk=('16', '05'), view='threequarter', side='L')],
 'beats': [('put', 'POET_SOUL', 'walk_to', {'to': [960, 650], 'arrive_word': 'equator'}, 'the soul walks to the middle of the field'),
           ('equator', 'POET_SOUL', 'pose', {'card': '02'}, 'arms open at the equator'),
           ('hotter', 'POET_SOUL', 'pose', {'card': '06'}, 'much hotter')],
 'joins': [{'kind': 'wipe', 'surface': 'haze_1', 'query': 'sun solar flare surface', 'word': 'planet', 'mix': 0.6, 'blend': 'screen', 'wipe_s': 1.0, 'ground_y': 450,
            'why': 'a larger, hotter star wipes down into the sky'}],
 'fx': [{'kind': 'sunrise', 'at': [960, 300], 'r0': 80, 'r1': 900, 't0': 'larger', 'rise': 30}],
 'camera': cam(1.0, 960, 560, 1.08, 960, 600),
 'notes': ['Only the soul is here (vellum POET cards); the body stays on the rooftop.'],
}
SPECS['08.5'] = {
 'set_layers': {'P0': 'back', 'P1': 'back'},
 'cast': [poet([465, 775], stand='21'), angel('ANGEL_1', [290, 690], 'R'), angel('ANGEL_2', [640, 690], 'L')],
 'beats': [('pouring', 'ANGEL_1', 'pose', {'card': 'card.angel.robe.03'}, 'lifts off to tip the ice basin'),
           ('unfiltered', 'ANGEL_2', 'pose', {'card': 'card.angel.robe.03'}),
           ('water', 'POET', 'pose', {'card': '12'}, 'chin high under the water'),
           ('joys', 'POET', 'pose', {'card': '02'}, 'arms open'),
           ('strobe', 'POET', 'pose', {'card': '10'}, 'caught in the flash'),
           ('gracious', 'ANGEL_1', 'pose', {'card': 'card.angel.robe.00'}), ('gracious', 'ANGEL_2', 'pose', {'card': 'card.angel.robe.00'}),
           ('blessed', 'POET', 'pose', {'card': '03'}, 'blessed: hand to heart'),
           ('infinity', 'POET', 'pose', {'card': '09'})],
 'joins': [{'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': ROOF_WALLGLASS, 'ground_y': 790, 'ground_x': 215,
            'query': 'baptism river water poured', 'word': 'water', 'end_word': 'religions', 'mix': 0.85,
            'why': 'a found baptism in the glass door while the angels pour'}],
 'fx': [card(PROPS + '08.props.basins/08.props.basins__p02.png', [465, 785], 26, lift_cm=232, rot=-0.35, t0='pouring', t1='gracious', ground_y=786),
        {'kind': 'pour', 'from': [452, 132], 'to': [470, 200], 'width_cm': 7, 't0': 'water', 't1': 'gracious', 'ground_y': 786},
        {'kind': 'strobe', 'bpm': 124, 'alpha': 0.2, 'colors': ['#ffffff', '#9fd0ff'], 't0': 'flash', 't1': 'gracious'}],
 'camera': cam(1.0, 465, 560, 1.06, 465, 540),
 'notes': ['The breakdown has the pour on the equator plain; lane C put 08.5 on the rooftop, so the angels pour on the walkway.',
           'The ice basin (08.props.basins) hangs over his head as a set card; the water is a code stream.'],
}
SPECS['08.6'] = {
 'set_layers': {'P0': 'back', 'P1': 'back'},
 'cast': [poet([450, 765], stand='21'), soul([495, 625], ghost=0.55, view='front')],
 'beats': [('bring', 'POET_SOUL', 'walk_to', {'to': [470, 712], 'arrive_word': 'body'}, 'the soul comes back'),
           ('body', 'POET_SOUL', 'vanish', {'dur': 0.6}, 'back in his body'),
           ('lean', 'POET', 'pose', {'card': '10'}, 'to lean back'),
           ('breathe', 'POET', 'pose', {'card': '12'}, 'breathe in the smoke'),
           ('tell', 'POET', 'pose', {'card': '03'}),
           ('good', 'POET', 'pose', {'card': '15'}, 'how good it is'),
           ('acquainted', 'POET', 'pose', {'card': '24'}, 'turns to the night')],
 'joins': [{'kind': 'pane', 'surface': 'wall_1', 'inside': False, 'polygon': ROOF_RAIL1, 'ground_y': 825, 'ground_x': 672,
            'query': 'cigarette smoke drifting night', 'word': 'smoke', 'mix': 0.8, 'blend': 'screen', 'why': 'the smoke that fills the room, in the glass'}],
 'fx': [{'kind': 'smoke', 't0': 'smoke', 'alpha': 0.12, 'y0': 0.1, 'y1': 0.9}],
 'camera': cam(1.06, 460, 600, 1.0, 460, 600),
}
SPECS['08.7'] = {
 'cast': [poet([1140, 860], stand='24'), ex([760, 700]),
          dancer('FAN_1', 'dancer_dress', 'club_dress', [1500, 690], 'threequarter', 'L'), dancer('FAN_2', 'dancer_shirt', 'club_shirt', [1640, 720], 'front')],
 'goals': [sway('FAN_1', amp=0.6), sway('FAN_2', amp=0.6, phase=0.3), wander('FAN_1', [[1400, 660], [1650, 660], [1650, 740], [1400, 740]], 7, every=3, step=80)],
 'beats': [('staring', 'POET', 'pose', {'card': '24'}, 'staring at the mountains in the panel'),
           ('wandering', 'EX', 'walk_to', {'to': [700, 620], 'speed': 0.7}, 'EX walks off, back to us'),
           ('eyes', 'POET', 'pose', {'card': '09'}),
           ('thoughts', 'POET', 'pose', {'card': '03'}),
           ('reach', 'POET', 'pose', {'card': '14'}, 'within reach')],
 'joins': [{'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': STREET_PANEL['C'], 'ground_y': 560, 'ground_x': 1068,
            'query': 'mountains in the distance', 'word': 'mountains', 'mix': 0.95, 'why': 'the unfamiliar mountains open in a lit street panel'},
           {'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': STREET_PANEL['A'], 'ground_y': 560, 'ground_x': 880,
            'query': 'eyes looking close-up face woman', 'word': 'eyes', 'mix': 0.9, 'why': 'wandering eyes, in the next panel'}],
 'camera': cam(1.0, 1100, 600, 1.05, 1100, 620),
 'notes': ['EX is played only by his back cards (face never seen); he walks away up the street.'],
}

# ═══════════════════════ 09 · YET, HEARD ═══════════════════════
ARCADE_SHOP = [[567, 540], [687, 530], [687, 800], [567, 840]]
SPECS['09.1'] = {
 'cast': [poet([820, 880]), ex([1060, 790]),
          dancer('CROWD_1', 'dancer_dress', 'club_dress', [960, 680], 'threequarter', 'R'), dancer('CROWD_2', 'dancer_shirt', 'club_shirt', [1160, 670]),
          dancer('CROWD_3', 'dancer_jacket', 'club_jacket', [1240, 700], 'threequarter', 'L')],
 'goals': [sway('CROWD_1', bpm=110, amp=0.6), sway('CROWD_2', bpm=110, amp=0.6, phase=0.4), sway('CROWD_3', bpm=110, amp=0.6, phase=0.8),
           wander('CROWD_2', [[1100, 650], [1220, 650], [1220, 700], [1100, 700]], 5, bpm=110, every=3, step=50)],
 'beats': [('accepting', 'POET', 'pose', {'card': '21'}, 'accepting'),
           ('real', 'POET', 'pose', {'card': '03'}, 'my love was real'),
           ('give', 'POET', 'pose', {'card': '15'}, 'what isn\'t mine'),
           ('gather', 'POET', 'pose', {'card': '09'}, 'gathers his things'),
           ('moon', 'POET', 'pose', {'card': '24'}, 'we look at the moon'),
           ('moon', 'EX', 'pose', {'card': 'card.ex.ex_jacket.01'}),
           ('talk', 'POET', 'pose', {'card': '09'}),
           ('travel', 'POET', 'pose', {'card': '07'}, 'travel through time'),
           ('good', 'POET', 'pose', {'card': '02'}, 'it feels so good'),
           ('old', 'POET', 'pose', {'card': '21'}),
           ('believe', 'POET', 'pose', {'card': '03'}),
           ('heartbreaks', 'EX', 'walk_to', {'to': [1090, 640], 'speed': 0.6}, 'EX walks into the arcade'),
           ('heartbreaks', 'POET', 'pose', {'card': '28'}),
           ('unchanging', 'POET', 'pose', {'card': '21'})],
 'joins': [{'kind': 'pane', 'surface': 'door_1', 'inside': False, 'polygon': ARCADE_SHOP, 'ground_y': 840, 'ground_x': 567,
            'query': 'full moon night sky clouds', 'word': 'moon', 'end_word': 'old', 'mix': 0.95,
            'why': 'the moon they used to see, in the lit shop window'},
           {'kind': 'citizen', 'query': 'elderly couple walking together', 'at': [1180, 640], 'height_cm': 150, 'word': 'grow', 'end_word': 'all',
            'why': 'we grow old together: an archive couple passes at the back'}],
 'fx': [card(PROPS + '09.props.suitcases-notice/09.props.suitcases-notice__p05.png', [740, 900], 45, t0='gather', ground_y=901)],
 'camera': cam(1.0, 900, 640, 1.08, 920, 660),
 'notes': ['EX keeps his back to us (cards 00/01 and his back walk); he looks at the moon with POET, then walks off.'],
}
SPECS['09.2'] = {
 'cast': [poet([1180, 840]), ex([600, 760], cards={'stand': 'card.ex.ex_jacket.14'}),
          jointed('PARENT_1', 'mother', [1700, 650], 'threequarter', 'L', alpha=0)],
 'beats': [('help', 'POET', 'pose', {'card': '09'}),
           ('mother', 'EX', 'pose', {'card': 'card.ex.ex_jacket.00'}, 'EX stands, his back to us'),
           ('call', 'POET', 'walk_to', {'to': [1420, 760], 'arrive_word': 'mother'}, 'to the phone booth'),
           ('mother', 'POET', 'pose', {'card': '03'}),
           ('mother', 'PARENT_1', 'appear', {'dur': 1.2}, 'MOTHER, far, in her lamplight'),
           ('tears', 'PARENT_1', 'hold_gesture', {'side': 'R', 'name': 'hand_chest'}, 'in tears'),
           ('abyss', 'POET', 'pose', {'card': '06'}, 'an abyss she has never known'),
           ('abyss', 'PARENT_1', 'wince', {}),
           ('talk', 'POET', 'pose', {'card': '09'}),
           ('wounds', 'POET', 'pose', {'card': '03'}),
           ('prayer', 'POET', 'pose', {'card': '20'}, 'even after prayer'),
           ('prayer', 'PARENT_1', 'release', {'side': 'R'}),
           ('give', 'POET', 'pose', {'card': '15'}),
           ('moon', 'POET', 'pose', {'card': '24'}),
           ('dancing', 'POET', 'pose', {'card': '11'}, 'dancing on my own'),
           ('dancing', 'PARENT_1', 'sway', {'bpm': 96, 'amp': 0.8, 'bars': 3}, 'maternal ears in tune')],
 'goals': [{'who': 'PARENT_1', 'kind': 'face', 'args': {'who': 'POET'}, 't0': 'mother'}],
 'joins': [{'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': STREET_PANEL['A'], 'ground_y': 560, 'ground_x': 880,
            'query': 'woman talking on telephone 1950s', 'word': 'mother', 'end_word': 'prayer', 'mix': 0.95, 'why': 'the call, in a lit street panel'},
           {'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': STREET_PANEL['D'], 'ground_y': 560, 'ground_x': 1183,
            'query': 'moon over water night', 'word': 'moon', 'mix': 0.95, 'why': 'the moon looking at us'}],
 'fx': [card(PROPS + '09.props.phonebooth/09.props.phonebooth__p15.png', [1420, 770], 235, ground_y=760),
        card(PROPS + '09.props.suitcases-notice/09.props.suitcases-notice__p06.png', [690, 770], 30, t1='go#2'),
        {'kind': 'glow', 'at': [1700, 470], 'r_cm': 150, 'color': 'rgba(255,190,110,1)', 'alpha': 0.45, 'ground_y': 650, 't0': 'mother'}],
 'camera': cam(1.0, 1150, 600, 1.06, 1250, 600),
 'notes': ['EX packs the suitcase in his crouched back card ("you help me gather my things"), then stands with his back to us.',
           'MOTHER is lane B\'s jointed mother in her cardigan, far across the street in a lamp glow: the other end of the line (the breakdown\'s living room needs its own set).',
           'The phone booth is the painted 09.props.phonebooth card standing on the street at its real height (235 cm).'],
}
SPECS['09.3'] = {
 'cast': [poet([1000, 820], stand='21'), jointed('PARENT_1', 'mother', [1700, 650], 'threequarter', 'L', ghost=0.7),
          {'id': 'ELDER_1', 'character': 'father_elder', 'costume': 'elder_father_coat', 'mode': 'cards', 'view': 'threequarter', 'side': 'R', 'place': [400, 760], 'alpha': 0,
           'cards': {'walk': 'card.father_elder.poem09.00', 'stand': 'card.father_elder.poem09.00'}}],
 'beats': [('watches', 'PARENT_1', 'hold_gesture', {'side': 'R', 'name': 'hand_chest'}, 'she watches us'),
           ('father', 'PARENT_1', 'vanish', {'dur': 1.5}),
           ('father', 'POET', 'pose', {'card': '03'}),
           ('summon', 'ELDER_1', 'appear', {'dur': 1.4}, 'FATHER, summoned from the yonders'),
           ('demeanor', 'POET', 'pose', {'card': '09'}),
           ('walk', 'ELDER_1', 'walk_to', {'to': [1300, 800], 'arrive_word': 'footsteps'}, 'they walk east'),
           ('retrace', 'POET', 'pose', {'card': '21'}),
           ('guiding', 'POET', 'pose', {'card': '07'}, 'guiding a settling moon'),
           ('tears', 'POET', 'pose', {'card': '03'}, 'my tears fall'),
           ('shadows', 'ELDER_1', 'vanish', {'dur': 2.0})],
 'goals': [{'who': 'POET', 'kind': 'walk_with', 'args': {'who': 'ELDER_1', 'side': 'L', 'gap_cm': 70}}],
 'joins': [{'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': STREET_PANEL['B'], 'ground_y': 560, 'ground_x': 985,
            'query': 'sunrise over the sea harbour', 'word': 'east', 'mix': 0.95, 'why': 'east toward the sunrises, in a lit panel'},
           {'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': STREET_PANEL['D'], 'ground_y': 560, 'ground_x': 1183,
            'query': 'father and son walking', 'word': 'walk', 'end_word': 'then', 'mix': 0.95, 'why': 'his footsteps, retraced, in the next panel'}],
 'fx': [{'kind': 'sunrise', 'at': [1500, 420], 'r0': 60, 'r1': 600, 't0': 'east', 'rise': 40}],
 'camera': cam(1.0, 1000, 600, 1.04, 1100, 600),
 'notes': ['FATHER is the painted father_elder walk card (the only FATHER card), summoned with an appear; POET walks with him by goal (walk_with).'],
}
SPECS['09.4'] = {
 'set_layers': {'P0': 'back'},
 'cast': [{'id': 'FATHER', 'character': 'father_elder', 'costume': 'elder_father_coat', 'mode': 'cards', 'view': 'threequarter', 'side': 'L', 'place': [1720, 585],
           'cards': {'walk': 'card.father_elder.poem09.00', 'stand': 'card.father_elder.poem09.00'}},
          poet([1775, 610], stand='24', walk=('24',), view='back')],
 'goals': [{'who': 'POET', 'kind': 'walk_with', 'args': {'who': 'FATHER', 'side': 'R', 'gap_cm': 60}}],
 'beats': [('stroll', 'FATHER', 'walk_to', {'to': [1450, 490], 'arrive_word': 'blew'}, 'they stroll east along the bank'),
           ('hearted', 'POET', 'pose', {'card': '03'}),
           ('broken', 'POET', 'pose', {'card': '21'}),
           ('hurt', 'POET', 'pose', {'card': '24'}, 'yet, heard')],
 'joins': [{'kind': 'screen', 'surface': 'water_0', 'query': 'harbour boats at dawn', 'word': 'stroll', 'mix': 0.45, 'blend': 'screen', 'ground_y': 420,
            'why': 'the inner harbour\'s found film plays in its own water'}],
 'fx': [{'kind': 'sunrise', 'at': [1250, 300], 'r0': 60, 'r1': 520, 't0': 'stroll', 'rise': 30}],
 'camera': cam(1.35, 1560, 470, 1.3, 1480, 460),
 'notes': ['Restaged on lane C\'s harbour canal (stands on water): father and son walk the far bank away from us, east, small in the frame.',
           'The FATHER walk card is three-quarter front; walking away it reads sideways (no back card exists) - his back walk card is the asset to paint.'],
}

# ═══════════════════════ 10 · MAGIC RIDE ═══════════════════════
BIKE = PROPS + '11.props.parked-motorcycle/11.props.parked-motorcycle__p01.png'
SPECS['10.1'] = {
 'cast': [poet([560, 1048])],
 'beats': [('looking', 'POET', 'walk_to', {'to': [920, 1046], 'arrive_word': 'here'}, 'walks the sidewalk, not looking for a ride'),
           ('here', 'POET', 'pose', {'card': '08'}, 'but here you are'),
           ('blissful', 'POET', 'pose', {'card': '03'}),
           ('withering', 'POET', 'pose', {'card': '21'}),
           ('worlds', 'POET', 'pose', {'card': '07'}, 'the dark and the light worlds'),
           ('rub', 'POET', 'pose', {'card': '06'}, 'rubs his aggressions into the steel'),
           ('hop', 'POET', 'pose', {'card': '23'}, 'hops on')],
 'joins': [{'kind': 'wipe', 'surface': 'haze_0', 'query': 'highway road at night headlights', 'word': 'ride', 'end_word': 'known', 'mix': 0.45, 'blend': 'screen', 'wipe_s': 1.0, 'ground_y': 700,
            'why': 'a found ride wipes into the night sky over the palms'}],
 'fx': [card(BIKE, [1090, 1050], 110, flip=True, t1='hop', fade=0.15, ground_y=1050)],
 'camera': cam(2.0, 900, 1062, 2.0, 980, 1062),
 'notes': ['The set\'s scale puts the road far from a 5.3 m camera (figures 135 px); the camera is pushed in 2x, the figures are not resized.',
           'The motorcycle is the painted 11.props.parked-motorcycle card at its real height (110 cm); POET\'s card 23 "Mounting the Motorcycle" takes over at "hop on".'],
}
SPECS['10.2'] = {
 'cast': [poet([620, 1050], stand='23', walk=('23',)),
          jointed('CROWD_1', 'street_clothes', [850, 960], 'front'), jointed('CROWD_2', 'street_clothes', [1050, 958], 'threequarter', 'L'),
          jointed('CROWD_3', 'street_clothes', [1260, 962], 'profile', 'L')],
 'goals': [{'who': 'CROWD_1', 'kind': 'face', 'args': {'who': 'POET'}}, {'who': 'CROWD_2', 'kind': 'face', 'args': {'who': 'POET'}},
           {'who': 'CROWD_3', 'kind': 'face', 'args': {'who': 'POET'}}],
 'beats': [('loneliness', 'POET', 'walk_to', {'to': [1000, 1052], 'arrive_word': 'end', 'keep_facing': True}, 'rides, slow'),
           ('noise', 'POET', 'walk_to', {'to': [1420, 1052], 'arrive_word': 'exists', 'keep_facing': True}, 'rides on; heads turn'),
           ('eyes', 'CROWD_2', 'head_raises', {}), ('twists', 'CROWD_3', 'nod', {}),
           ('magic', 'CROWD_1', 'hold_gesture', {'side': 'R', 'name': 'page_up'}, 'a wave')],
 'joins': [{'kind': 'wipe', 'surface': 'haze_1', 'query': 'city street lights night traffic', 'word': 'noise', 'mix': 0.65, 'wipe_s': 1.0, 'ground_y': 700,
            'why': 'the noise that blocks the noise, wiped into the sky'}],
 'camera': cam(1.4, 1010, 1062, 1.4, 1010, 1062),
 'notes': ['He rides on his painted card 23 (the motorcycle in it), pinned as his walk card, so the ride is a cut-out slide with the card\'s hop.',
           'The crowd turns to him by goal (face POET), Thistle-Gulch style: no authored turns.'],
}
SPECS['10.3'] = {
 'cast': [poet([450, 1010], stand='24')],
 'beats': [('preparations', 'POET', 'pose', {'card': '24'}, 'his back to us, the moon ahead'),
           ('desire', 'POET', 'pose', {'card': '21'}),
           ('moon', 'POET', 'pose', {'card': '24'}),
           ('morning', 'POET', 'pose', {'card': '02'}, 'a morning ahead')],
 'joins': [{'kind': 'wipe', 'surface': 'wall_1', 'query': 'moon setting night sky', 'word': 'moon', 'end_word': 'subsides', 'mix': 0.55, 'blend': 'screen', 'ground_y': 520,
            'why': 'the moon settling, wiped over the far roofs'},
           {'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': [[655, 650], [730, 650], [730, 770], [655, 770]], 'ground_y': 780, 'ground_x': 655,
            'query': 'sunrise over city rooftops', 'word': 'morning', 'mix': 0.95, 'why': 'a morning, in the one lit window'}],
 'fx': [{'kind': 'sunrise', 'at': [1500, 700], 'r0': 40, 'r1': 700, 't0': 'morning', 'rise': 50}],
 'camera': cam(1.0, 960, 540, 1.05, 900, 560),
 'notes': ['The rooftop is the only floor in view and the camera is 1 m up, so he stands close and big (a back three-quarter medium).'],
}
SPECS['10.4'] = {
 'cast': [poet([760, 1020])],
 'beats': [('looks', 'POET', 'walk_to', {'to': [420, 930], 'arrive_word': 'believe'}, 'walks up the road into the morning'),
           ('believe', 'POET', 'pose', {'card': '09'}),
           ('sunlight', 'POET', 'pose', {'card': '02'}, 'ripe with sunlight'),
           ('warm', 'POET', 'pose', {'card': '03'}),
           ('birds', 'POET', 'pose', {'card': '07'}, 'the birds'),
           ('covered', 'POET', 'pose', {'card': '21'})],
 'joins': [{'kind': 'wipe', 'surface': 'haze_0', 'query': 'birds flying sunrise flock', 'word': 'birds', 'mix': 0.6, 'blend': 'screen', 'wipe_s': 1.0, 'ground_y': 600,
            'why': 'birds out of the night, wiped into the canopy light'}],
 'fx': [{'kind': 'sunrise', 'at': [880, 160], 'r0': 60, 'r1': 600, 't0': 'morning', 'rise': 0}],
 'camera': cam(1.0, 700, 700, 1.06, 560, 700),
}
SPECS['10.5'] = {
 'cast': [poet([470, 960], stand='21')],
 'beats': [('curiosities', 'POET', 'pose', {'card': '15'}),
           ('okay', 'POET', 'pose', {'card': '09'}, 'everything will be okay'),
           ('live', 'POET', 'pose', {'card': '02'}, 'live in this feeling'),
           ('innocent', 'POET', 'pose', {'card': '03'})],
 'joins': [{'kind': 'wipe', 'surface': 'haze_0', 'query': 'sunlight through trees forest morning', 'word': 'feeling', 'mix': 0.55, 'blend': 'screen', 'ground_y': 600,
            'why': 'the feeling, as found morning light'},
           {'kind': 'citizen', 'query': 'children playing laughing', 'at': [1180, 900], 'height_cm': 120, 'word': 'blissful', 'end_word': 'innocent',
            'why': 'blissful and oddly innocent: an archive child on a stick'}],
 'camera': cam(1.0, 600, 680, 1.08, 520, 700),
}
SPECS['10.6'] = {
 'cast': [poet([1180, 1000], stand='23', walk=('23',), view='threequarter', side='L'),
          jointed('CROWD_4', 'street_clothes', [250, 880], 'front'), jointed('CROWD_5', 'street_clothes', [150, 930], 'threequarter', 'R')],
 'goals': [{'who': 'CROWD_4', 'kind': 'face', 'args': {'who': 'POET'}}, {'who': 'CROWD_5', 'kind': 'face', 'args': {'who': 'POET'}}],
 'beats': [('riding', 'POET', 'walk_to', {'to': [700, 930], 'arrive_word': 'magic', 'keep_facing': True}, 'rides up the mountain road'),
           ('click', 'CROWD_4', 'nod', {}), ('magic', 'CROWD_5', 'hold_gesture', {'side': 'R', 'name': 'page_up'})],
 'joins': [{'kind': 'wipe', 'surface': 'haze_0', 'query': 'magician magic trick stage', 'word': 'magic', 'mix': 0.65, 'wipe_s': 0.8, 'ground_y': 600,
            'why': 'the magic still exists'}],
 'camera': cam(1.0, 700, 700, 1.05, 560, 720),
 'notes': ['The breakdown closes 10.6 on "Even here, it\'s chilly in the morning"; the reading speaks that line at the head of poem 11, so it lives in 11.1.'],
}

# ═══════════════════════ 11 · NEW DAY ═══════════════════════
SPECS['11.1'] = {
 'set_layers': {'P4': 'back'},
 'cast': [poet([700, 880], stand='24')],
 'beats': [('chilly', 'POET', 'pose', {'card': '06'}, 'chilly'),
           ('river', 'POET', 'pose', {'card': '24'}, 'looks out at the fog on the sea'),
           ('hills', 'POET', 'pose', {'card': '21'}),
           ('peace', 'POET', 'pose', {'card': '09'}, 'this world is at peace')],
 'joins': [{'kind': 'pane', 'surface': 'wall_2', 'inside': False, 'polygon': CHAPEL_DOOR_11_1, 'ground_y': 605, 'ground_x': 1140,
            'query': 'river rafting fog hills', 'word': 'river', 'mix': 0.95, 'why': 'the river-rafting fog, through the chapel door'}],
 'fx': [{'kind': 'smoke', 'alpha': 0.1, 'color': '#dfe4e6', 'y0': 0.45, 'y1': 0.75, 'n': 7}],
 'camera': cam(1.0, 900, 600, 1.06, 900, 620),
}
SPECS['11.2'] = {
 'cast': [poet([760, 1000], stand='21')],
 'beats': [('silent', 'POET', 'pose', {'card': '21'}),
           ('choir', 'POET', 'pose', {'card': '03'}, 'choir chords'),
           ('calm', 'POET', 'pose', {'card': '09'}),
           ('offer', 'POET', 'pose', {'card': '02'}, 'offers them back to the higher powers'),
           ('exhausted', 'POET', 'pose', {'card': '28'}, 'exhausted'),
           ('jazz', 'POET', 'pose', {'card': '29'}, 'a diminishing flame'),
           ('remnants', 'POET', 'pose', {'card': '21'})],
 'joins': [{'kind': 'pane', 'surface': 'wall_1', 'inside': False, 'polygon': TEMPLE_COLONNADE, 'ground_y': 520, 'ground_x': 930,
            'query': 'church choir singing', 'word': 'choir', 'end_word': 'powers', 'mix': 0.9, 'why': 'the choir, between the temple columns'},
           {'kind': 'citizen', 'query': 'jazz trumpet player', 'at': [1560, 915], 'height_cm': 150, 'word': 'jazz', 'end_word': 'dew',
            'why': 'jazz-tuned lyrics: an archive player on a stick'}],
 'fx': [SHORE_DECK, {'kind': 'sunrise', 'at': [1370, 330], 'r0': 50, 'r1': 500, 't0': 'sunlight', 'rise': 20}],
 'camera': cam(1.0, 960, 560, 1.05, 900, 600),
 'notes': ['The plate is mirror water to the frame edge; POET stands on a painted shore card (a code deck), sized by the set\'s scale at its line.'],
}
SPECS['11.3'] = {
 'cast': [poet([1060, 990], stand='09')],
 'beats': [('rebuild', 'POET', 'pose', {'card': '07'}, 'points at the temple'),
           ('new', 'POET', 'pose', {'card': '02'}, 'a new day'),
           ('catharsis', 'POET', 'pose', {'card': '06'}),
           ('crawl', 'POET', 'pose', {'card': '28'}, 'the painful crawl'),
           ('broken', 'POET', 'pose', {'card': '13'}, 'boulevards of broken dreams')],
 'joins': [{'kind': 'pane', 'surface': 'wall_1', 'inside': False, 'polygon': TEMPLE_COLONNADE, 'ground_y': 520, 'ground_x': 930,
            'query': 'workers building construction scaffolding', 'word': 'rebuild', 'end_word': 'day', 'mix': 0.9, 'why': 'rebuilding, in the colonnade'},
           {'kind': 'wipe', 'surface': 'water_0', 'query': 'cobblestone street rain night', 'word': 'cobblestone', 'mix': 0.5, 'blend': 'screen', 'wipe_s': 0.9, 'ground_y': 600,
            'why': 'the cobblestone boulevards, wiped across the mirror sea'}],
 'fx': [SHORE_DECK],
 'camera': cam(1.0, 960, 600, 1.06, 1000, 620),
}
SPECS['11.4'] = {
 'cast': [poet([210, 575], stand='28')],
 'beats': [('close', 'POET', 'pose', {'card': '28'}, 'kneels at the pool'),
           ('words', 'POET', 'pose', {'card': '29'}, 'holds the universe up'),
           ('majestic', 'POET', 'pose', {'card': '29'})],
 'joins': [{'kind': 'screen', 'surface': 'water_0', 'query': 'galaxy stars night sky', 'word': 'journal', 'mix': 0.5, 'blend': 'screen', 'ground_y': 200,
            'why': 'the journal of great clarity opens in the infinity pool'}],
 'fx': [card(PROPS + '11.props.journal/11.props.journal__p11.png', [340, 610], 14, ground_y=610)],
 'camera': cam(1.0, 600, 500, 1.06, 500, 520),
 'notes': ['The camera looks down on the pool (horizon at y 80): a standing 184 cm figure fits only far away, so he is staged kneeling (cards 28, 29).'],
}
SPECS['11.5'] = {
 'set_layers': {'P4': 'back'},
 'cast': [poet([1500, 760], walk=('16', '05'))],
 'beats': [('words', 'POET', 'walk_to', {'to': [620, 900], 'arrive_word': 'drying', 'speed': 0.8}, 'walks on the water of the flats'),
           ('drying', 'POET', 'pose', {'card': '21'}),
           ('embrace', 'POET', 'pose', {'card': '02'}, 'embrace a new day'),
           ('receive', 'POET', 'pose', {'card': '15'}, 'receive'),
           ('welcome', 'POET', 'pose', {'card': '17'}, 'welcome')],
 'joins': [{'kind': 'pane', 'surface': 'wall_2', 'inside': False, 'polygon': CHAPEL_DOOR_11_5, 'ground_y': 600, 'ground_x': 1093,
            'query': 'gospel choir singing', 'word': 'sung', 'end_word': 'past', 'mix': 0.95, 'why': 'gospels to the lonely, through the chapel door'}],
 'fx': [{'kind': 'sunrise', 'at': [400, 560], 'r0': 60, 'r1': 800, 't0': 'embrace', 'rise': 40}],
 'camera': cam(1.0, 1000, 600, 1.05, 760, 640),
}
SPECS['11.6'] = {
 'cast': [poet([900, 1000])],
 'beats': [('everything', 'POET', 'pose', {'card': '09'}),
           ('circumference', 'POET', 'pose', {'card': '02'}, 'every circumference of life'),
           ('celebrating', 'POET', 'pose', {'card': '20'}),
           ('sacred', 'POET', 'pose', {'card': '03'}, 'this sacred place'),
           ('sunlight', 'POET', 'pose', {'card': '17'}, 'reveling in the sunlight'),
           ('peace', 'POET', 'pose', {'card': '09'}, 'a heart at peace')],
 'joins': [{'kind': 'pane', 'surface': 'wall_1', 'inside': False, 'polygon': TEMPLE_COLONNADE, 'ground_y': 520, 'ground_x': 930,
            'query': 'crowd celebrating festival', 'word': 'celebrating', 'end_word': 'place', 'mix': 0.9, 'why': 'the celebration, in the temple'}],
 'fx': [SHORE_DECK, {'kind': 'sunrise', 'at': [1370, 330], 'r0': 60, 'r1': 760, 't0': 'sunlight', 'rise': 30}],
 'camera': cam(1.05, 900, 600, 1.0, 960, 560),
}

# ═══════════════════════ 12 · REUNION ═══════════════════════
SPECS['12.1'] = {
 'set_layers': {'P0': 'back', 'P1': 'back', 'P4': 'back'},
 'cast': [poet([1010, 565]), jointed('BROTHER_1', 'brother', [1290, 548], 'threequarter', 'L'),
          jointed('FRIEND_1', 'friend', [1420, 520], 'front'), jointed('FRIEND_2', 'friend', [860, 522], 'threequarter', 'R')],
 'beats': [('decades', 'BROTHER_1', 'walk_to', {'to': [1160, 560], 'arrive_word': 'laughter'}, 'his brother crosses to him'),
           ('laughter', 'FRIEND_1', 'laugh', {'dur': 1.6}), ('laughter', 'FRIEND_2', 'laugh', {'dur': 1.6}),
           ('hugs', 'BROTHER_1', 'reach', {'side': 'R', 'target': {'who': 'POET', 'socket': 'shoulder_L'}, 'hand': 'open', 'dur': 0.5}, 'hugs with no reason'),
           ('hugs', 'POET', 'pose', {'card': '02'}, 'arms open'),
           ('loud', 'FRIEND_1', 'laugh', {'dur': 1.4}), ('voices', 'FRIEND_2', 'nod', {}),
           ('overheard', 'BROTHER_1', 'release', {'side': 'R'}),
           ('overheard', 'POET', 'pose', {'card': '03'}, 'our hearts overheard')],
 'joins': [{'kind': 'pane', 'surface': 'pane_0', 'inside': False, 'polygon': HALL_WINDOWS, 'ground_y': 500, 'ground_x': 150,
            'query': 'family reunion hugging home movie', 'word': 'hugs', 'mix': 0.9, 'why': 'a found reunion in the hall windows'}],
 'camera': cam(1.0, 1130, 480, 1.12, 1130, 470),
 'notes': ['The hall\'s camera is low (56 cm): everyone stands far, beyond the planters, so their whole figures fit (y <= 609).'],
}
SPECS['12.3'] = {
 'set_layers': {'P0': 'back', 'P1': 'back', 'P4': 'back'},
 'cast': [poet([1050, 560], stand='21'), jointed('BROTHER_1', 'brother', [1220, 552], 'threequarter', 'L'),
          jointed('ELDER_1', 'elder_memory', [880, 515], 'front', ghost=0.5), jointed('ELDER_2', 'elder_memory', [1360, 510], 'front', ghost=0.5),
          jointed('ELDER_3', 'elder_memory', [1140, 500], 'front', ghost=0.45)],
 'beats': [('drifts', 'POET', 'pose', {'card': '24'}, 'his mind drifts'),
           ('afterlives', 'ELDER_1', 'head_lowers', {'deg': 10}), ('afterlives', 'ELDER_2', 'head_lowers', {'deg': 10}),
           ('rooms', 'ELDER_1', 'vanish', {'dur': 1.0}), ('rooms', 'ELDER_2', 'vanish', {'dur': 1.2}), ('rooms', 'ELDER_3', 'vanish', {'dur': 1.4}),
           ('empty', 'POET', 'pose', {'card': '21'}, 'and those rooms are empty'),
           ('empty', 'BROTHER_1', 'head_lowers', {'deg': 14})],
 'joins': [{'kind': 'pane', 'surface': 'pane_0', 'inside': False, 'polygon': HALL_WINDOWS, 'ground_y': 500, 'ground_x': 150,
            'query': 'empty room old house', 'word': 'rooms', 'mix': 0.9, 'why': 'the empty rooms, in the windows'}],
 'fx': [{'kind': 'darken', 't0': 'darkness', 'dur': 1.5, 'alpha': 0.4}],
 'camera': cam(1.08, 1120, 470, 1.15, 1120, 470),
 'notes': ['The elders of memory are lane B\'s elder_memory puppets drawn as vellum (cast.ghost); they fade at "rooms".'],
}
GLASS = PROPS + '12.props.last-hourglass/12.props.last-hourglass__p23.png'
SPECS['12.4'] = {
 'set_layers': {'P0': 'back', 'P1': 'back', 'P4': 'back'},
 'cast': [poet([1010, 568]), jointed('BROTHER_1', 'brother', [1240, 552], 'threequarter', 'L', props=[{'kind': 'card', 'side': 'R', 'file': GLASS, 'h_cm': 24}]),
          jointed('FRIEND_1', 'friend', [1420, 522], 'front', props=[{'kind': 'card', 'side': 'R', 'file': GLASS, 'h_cm': 24}]),
          jointed('FRIEND_2', 'friend', [860, 524], 'threequarter', 'R', props=[{'kind': 'card', 'side': 'R', 'file': GLASS, 'h_cm': 24}])],
 'beats': [('all', 'POET', 'pose', {'card': '20'}, 'we are all here'),
           ('holding', 'BROTHER_1', 'hold_gesture', {'side': 'R', 'name': 'page_up'}, 'each holding an hourglass of burning sand'),
           ('holding', 'FRIEND_1', 'hold_gesture', {'side': 'R', 'name': 'page_up'}),
           ('holding', 'FRIEND_2', 'hold_gesture', {'side': 'R', 'name': 'page_up'}),
           ('holding', 'POET', 'pose', {'card': '29'}, 'he holds his, kneeling'),
           ('grateful', 'POET', 'pose', {'card': '03'}),
           ('forest', 'FRIEND_1', 'head_raises', {}),
           ('memories', 'POET', 'pose', {'card': '09'}),
           ('memories', 'BROTHER_1', 'nod', {})],
 'joins': [{'kind': 'pane', 'surface': 'pane_0', 'inside': False, 'polygon': HALL_WINDOWS, 'ground_y': 500, 'ground_x': 150,
            'query': 'forest trees sunlight', 'word': 'tree', 'mix': 0.9, 'why': 'every living tree in the forest, in the windows'}],
 'fx': [{'kind': 'glow', 'at': [1240, 400], 'r_cm': 60, 'alpha': 0.5, 'flicker': True, 'ground_y': 552, 't0': 'burning'}],
 'camera': cam(1.0, 1130, 480, 1.1, 1130, 470),
 'notes': ['The burning hourglass is the painted 12.props.last-hourglass card (p23) held in each jointed hand as a prop card.'],
}
SPECS['12.2'] = {
 'set_layers': {'P0': 'back', 'P1': 'back', 'P4': 'back'},
 'cast': [poet([1060, 565]), jointed('BROTHER_1', 'brother', [1195, 562], 'threequarter', 'L'), jointed('FRIEND_1', 'friend', [880, 522], 'threequarter', 'R')],
 'goals': [{'who': 'BROTHER_1', 'kind': 'walk_with', 'args': {'who': 'POET', 'side': 'L', 'gap_cm': 65}}],
 'beats': [('brotherhood', 'BROTHER_1', 'reach', {'side': 'R', 'target': {'who': 'POET', 'socket': 'shoulder_L'}, 'hand': 'open', 'dur': 0.5}, 'an arm round him: brotherhood'),
           ('brotherhood', 'POET', 'pose', {'card': '20'}),
           ('smiles', 'FRIEND_1', 'laugh', {'dur': 1.8}, 'smiles with no reason'),
           ('differences', 'BROTHER_1', 'release', {'side': 'R'}),
           ('overheard', 'POET', 'pose', {'card': '03'}),
           ('ears', 'BROTHER_1', 'head_lowers', {'deg': 12}, 'an ear to his brother\'s soul'),
           ('follow', 'POET', 'walk_to', {'to': [1180, 505], 'arrive_word': 'nights', 'speed': 0.7}, 'they follow the paths, deeper into the hall'),
           ('lights', 'FRIEND_1', 'turn', {'to': 'away'}),
           ('familiar', 'POET', 'pose', {'card': '24'})],
 'joins': [{'kind': 'pane', 'surface': 'pane_0', 'inside': False, 'polygon': HALL_WINDOWS, 'ground_y': 500, 'ground_x': 150,
            'query': 'hiking mountains canyon', 'word': 'hilltops', 'end_word': 'nights', 'mix': 0.9, 'why': 'paths of hilltops and canyons, in the windows'}],
 'fx': [{'kind': 'darken', 't0': 'infinite', 'dur': 1.2, 'alpha': 0.25}],
 'camera': cam(1.0, 1100, 480, 1.12, 1150, 460),
 'notes': ['Reading order: "This is brotherhood ... all too familiar" is read here, after 12.4; the reel follows the reading.'],
}
SPECS['12.5'] = {
 'set_layers': {'P0': 'back', 'P1': 'back', 'P4': 'back'},
 'cast': [poet([560, 790]), jointed('BROTHER_1', 'brother', [800, 785], 'threequarter', 'L')],
 'beats': [('create', 'BROTHER_1', 'laugh', {'dur': 1.5}, 'laughter'),
           ('laughter', 'POET', 'pose', {'card': '11'}, 'a little dance of it'),
           ('football', 'POET', 'pose', {'card': '18'}, 'football: a lunge for the ball'),
           ('recollections', 'POET', 'pose', {'card': '09'}),
           ('home', 'BROTHER_1', 'walk_to', {'to': [700, 735], 'speed': 0.7}, 'home, every time'),
           ('home', 'POET', 'walk_to', {'to': [520, 740], 'speed': 0.7})],
 'joins': [{'kind': 'pane', 'surface': 'wall_4', 'inside': False, 'polygon': QUAY_WALL, 'ground_y': 800, 'ground_x': 70,
            'query': 'football match players kicking', 'word': 'football', 'mix': 0.9, 'why': 'football and recollections, on the quay wall'}],
 'camera': cam(1.0, 640, 560, 1.05, 620, 560),
}

# ═══════════════════════ 13 · HOW TO WIN MY HEART ═══════════════════════
TABLE, CHAIR = CAFE + 'p14.png', CAFE + 'p04.png'
CAFE_SET = [card(TABLE, [880, 850], 76, ground_y=851), card(TABLE, [1460, 760], 76, ground_y=761), card(CHAIR, [1380, 758], 90, ground_y=757),
            card(CHAIR, [1545, 758], 90, flip=True, ground_y=757)]
SPECS['13.1'] = {
 'set_layers': {'P4': 'back'},
 'cast': [poet([1000, 860], stand='27'), jointed('COUPLE_1_A', 'couple_summer', [1385, 762], 'profile', 'R', alpha=0),
          jointed('COUPLE_1_B', 'couple_summer', [1540, 762], 'profile', 'L', alpha=0)],
 'beats': [(0.0, 'COUPLE_1_A', 'sit', {'height_cm': 46}), (0.0, 'COUPLE_1_B', 'sit', {'height_cm': 46}),
           (0.75, 'COUPLE_1_A', 'appear', {'dur': 0.5}, 'they are already seated'), (0.75, 'COUPLE_1_B', 'appear', {'dur': 0.5}),
           ('notice', 'POET', 'pose', {'card': '27'}, 'at the small table, watching'),
           ('cafe', 'COUPLE_1_B', 'nod', {}),
           ('heavens', 'COUPLE_1_A', 'laugh', {'dur': 1.2}),
           ('thought', 'POET', 'pose', {'card': '27'})],
 'joins': [{'kind': 'pane', 'surface': 'wall_2', 'inside': False, 'polygon': CHAPEL_DOOR_13, 'ground_y': 610, 'ground_x': 1053,
            'query': 'harbour cafe people sitting tables', 'word': 'cafe', 'mix': 0.95, 'why': 'a found harbour café through the chapel door'}],
 'fx': CAFE_SET,
 'camera': cam(1.0, 1100, 640, 1.06, 1150, 660),
 'notes': ['Lane C has no café plate (status "needs a plate"): the café is built on the tidal flats with the painted 13.props.cafe tables and chairs at their real heights.'],
}
SPECS['13.2'] = {
 'set_layers': {'P0': 'back', 'P4': 'back'},
 'cast': [poet([380, 980], stand='09'), jointed('COUPLE_1_A', 'couple_summer', [700, 905], 'profile', 'R'), jointed('COUPLE_1_B', 'couple_summer', [785, 905], 'profile', 'L'),
          jointed('COUPLE_2_A', 'couple_summer', [1180, 880], 'profile', 'R'), jointed('COUPLE_2_B', 'couple_summer', [1250, 880], 'profile', 'L')],
 'goals': [sway('COUPLE_1_A', bpm=84, amp=0.7), sway('COUPLE_1_B', bpm=84, amp=0.7), sway('COUPLE_2_A', bpm=84, amp=0.7, phase=0.5), sway('COUPLE_2_B', bpm=84, amp=0.7, phase=0.5)],
 'beats': [('discovering', 'COUPLE_1_A', 'reach', {'side': 'R', 'target': {'who': 'COUPLE_1_B', 'socket': 'shoulder_L'}, 'hand': 'open'}, 'couples hold each other, slow-dancing'),
           ('discovering', 'COUPLE_1_B', 'reach', {'side': 'L', 'target': {'who': 'COUPLE_1_A', 'socket': 'shoulder_R'}, 'hand': 'open'}),
           ('water', 'COUPLE_2_A', 'reach', {'side': 'R', 'target': {'who': 'COUPLE_2_B', 'socket': 'shoulder_L'}, 'hand': 'open'}),
           ('water', 'COUPLE_2_B', 'reach', {'side': 'L', 'target': {'who': 'COUPLE_2_A', 'socket': 'shoulder_R'}, 'hand': 'open'}),
           ('healing', 'POET', 'pose', {'card': '03'}),
           ('molding', 'POET', 'pose', {'card': '09'}),
           ('walking', 'POET', 'walk_to', {'to': [470, 940], 'speed': 0.6}, 'walking alone'),
           ('really', 'POET', 'pose', {'card': '08'}, 'really notice me'),
           ('avoid', 'POET', 'pose', {'card': '21'})],
 'joins': [{'kind': 'pane', 'surface': 'wall_0', 'inside': False, 'polygon': LAUNDRY_CLOTH, 'ground_y': 900, 'ground_x': 1560,
            'query': 'planet saturn rings moons astronomy animation', 'word': 'Jupiter', 'end_word': 'alone', 'mix': 0.9,
            'why': 'Jupiter\'s moons, on a sheet hung on the line (a vertical pane)'}],
 'camera': cam(1.0, 860, 760, 1.06, 820, 780),
 'notes': ['Each couple holds by two reaches (hand to the partner\'s shoulder) and sways together; their overlap is an exempt touch beat.'],
}
FIRE_LOGS, FIRE_BOOK = PROPS + '13.props.five-letters/13.props.five-letters__p21.png', PROPS + '13.props.five-letters/13.props.five-letters__p02.png'
SPECS['13.3'] = {
 'set_layers': {'P0': 'back', 'P1': 'back', 'P4': 'back'},
 'cast': [poet([620, 795], stand='21'), jointed('YOUNG_POET', 'young_poet_tee', [260, 770], 'threequarter', 'R'),
          jointed('ELDER_1', 'elder_pearls', [1080, 762], 'threequarter', 'L'), jointed('ELDER_2', 'elder_pearls', [1230, 758], 'front')],
 'beats': [('younger', 'YOUNG_POET', 'turn', {'to': 'camera'}, 'our younger selves, watching'),
           ('dreaming', 'YOUNG_POET', 'head_raises', {}),
           ('clutch', 'ELDER_1', 'hold_gesture', {'side': 'R', 'name': 'hand_chest'}, 'the elders clutch their pearls'),
           ('clutch', 'ELDER_2', 'hold_gesture', {'side': 'L', 'name': 'hand_chest'}),
           ('breath', 'ELDER_1', 'head_lowers', {'deg': 12}),
           ('freeing', 'ELDER_1', 'release', {'side': 'R'}), ('freeing', 'ELDER_2', 'release', {'side': 'L'}),
           ('freeing', 'ELDER_1', 'head_raises', {}),
           ('journeyed', 'POET', 'walk_to', {'to': [760, 805], 'arrive_word': 'conceivably'}, 'to the fire'),
           ('burned', 'POET', 'pose', {'card': '28'}, 'life has burned all my love stories'),
           ('losses', 'POET', 'pose', {'card': '21'}),
           ('win', 'POET', 'pose', {'card': '08'}, 'just one win'),
           ('celebrate', 'POET', 'pose', {'card': '02'}),
           ('ice', 'POET', 'pose', {'card': '21'}),
           ('death', 'ELDER_1', 'vanish', {'dur': 1.4}), ('death', 'ELDER_2', 'vanish', {'dur': 1.6}),
           ('departure', 'YOUNG_POET', 'vanish', {'dur': 1.4})],
 'joins': [{'kind': 'pane', 'surface': 'wall_4', 'inside': False, 'polygon': QUAY_WALL, 'ground_y': 800, 'ground_x': 70,
            'query': 'love letters burning fire', 'word': 'burned', 'end_word': 'seasons', 'mix': 0.9, 'why': 'the burned love stories, on the quay wall'},
           {'kind': 'citizen', 'query': 'old woman pearls necklace', 'at': [1380, 750], 'height_cm': 150, 'word': 'pearls', 'end_word': 'peacefully',
            'why': 'an archive elder clutches her pearls beside ours'}],
 'fx': [card(FIRE_LOGS, [900, 815], 18, ground_y=816), card(FIRE_BOOK, [905, 812], 9, t0='burned', ground_y=813),
        {'kind': 'glow', 'at': [900, 790], 'r_cm': 110, 'flicker': True, 'alpha': 0.6, 'ground_y': 815},
        {'kind': 'darken', 't0': 'ice', 'dur': 1.5, 'alpha': 0.3}],
 'camera': cam(1.0, 760, 560, 1.06, 800, 560),
 'notes': ['The breakdown spans three sets (church pews, café at dusk, the quay fire); lane C gives 13.3 the quay, so the younger self and the elders stand on the quay as memory.'],
}
SPECS['13.4'] = {
 'cast': [poet([900, 800], stand='21')],
 'beats': [('love', 'POET', 'pose', {'card': '03'}, 'to love myself more'),
           ('loss', 'POET', 'pose', {'card': '15'}),
           ('wizardry', 'POET', 'pose', {'card': '29'}, 'harvest a wizardry'),
           ('blossoms', 'POET', 'pose', {'card': '02'}),
           ('claimed', 'POET', 'pose', {'card': '21'})],
 'joins': [{'kind': 'wipe', 'surface': 'haze_0', 'query': 'poppies field flowers blooming', 'word': 'scarlet', 'mix': 0.6, 'blend': 'screen', 'wipe_s': 1.0, 'ground_y': 560,
            'why': 'scarlet poppies wipe into the night sky over the field'}],
 'fx': [{'kind': 'stars', 'n': 120, 'alpha': 0.5, 'y1': 0.5}],
 'camera': cam(1.0, 920, 600, 1.1, 900, 640),
 'notes': ['The plate\'s field is pale canola, not scarlet poppies: the poppies arrive as found film (asset wanted: a poppy-field plate or a poppy card).'],
}
SPECS['13.5'] = {
 'set_layers': {'P4': 'back'},
 'cast': [poet([1000, 860], stand='27'), jointed('COUPLE_1_A', 'couple_summer', [1385, 762], 'profile', 'R', alpha=0),
          jointed('COUPLE_1_B', 'couple_summer', [1540, 762], 'profile', 'L', alpha=0), jointed('SHE', 'she_window', [1280, 690], 'front', mode='cards', play_key='woman/poem13')],
 'beats': [(0.0, 'COUPLE_1_A', 'sit', {'height_cm': 46}), (0.0, 'COUPLE_1_B', 'sit', {'height_cm': 46}),
           (0.75, 'COUPLE_1_A', 'appear', {'dur': 0.5}, 'they are already seated'), (0.75, 'COUPLE_1_B', 'appear', {'dur': 0.5}),
           ('hope', 'POET', 'pose', {'card': '27'}),
           ('eyes', 'POET', 'pose', {'card': '03'}, 'capture my eyes'),
           ('stepping', 'SHE', 'walk_to', {'to': [1330, 670], 'speed': 0.5}, 'stepping back'),
           ('hello', 'POET', 'pose', {'card': '20'}, 'hello back')],
 'joins': [{'kind': 'pane', 'surface': 'wall_2', 'inside': False, 'polygon': CHAPEL_WIN_13, 'ground_y': 610, 'ground_x': 1160,
            'query': 'woman at window looking out', 'word': 'window', 'end_word': 'refocus', 'mix': 0.95, 'why': 'a distant window, in the chapel\'s'}],
 'fx': CAFE_SET,
 'camera': cam(1.0, 1150, 640, 1.08, 1200, 640),
 'notes': ['SHE is the painted woman card (front stand only: lane B\'s skirt rig does not draw in the stager, so she has no wave), far across the flats; the couple sits at the second café table.'],
}
SPECS['13.6'] = {
 'set_layers': {'P4': 'back'},
 'cast': [poet([1000, 860], stand='27')],
 'beats': [('fatigue', 'POET', 'pose', {'card': '27'}, 'alone at the small table'),
           ('smile', 'POET', 'pose', {'card': '20'}, 'a smile worth the promise of my heart'),
           ('heart', 'POET', 'pose', {'card': '03'})],
 'joins': [{'kind': 'pane', 'surface': 'wall_2', 'inside': False, 'polygon': CHAPEL_DOOR_13, 'ground_y': 610, 'ground_x': 1053,
            'query': 'man smiling close-up', 'word': 'smile', 'mix': 0.95, 'why': 'a found smile, in the chapel door'}],
 'fx': CAFE_SET[:1],
 'camera': cam(1.0, 1000, 640, 1.1, 980, 680),
}

# ═══════════════════════ 14 · HOT MINUTE ═══════════════════════
VOID_FX = [{'kind': 'stars', 'n': 260, 'alpha': 0.7}]
SPECS['14.1'] = {
 'cast': [poet([900, 1000], stand='24')],
 'beats': [(1.0, 'POET', 'pose', {'card': '24'}, 'his back to us: everything he built, on the water'),
           (6.5, 'POET', 'pose', {'card': '21'})],
 'joins': [{'kind': 'pane', 'surface': 'wall_1', 'inside': False, 'polygon': TEMPLE_COLONNADE, 'ground_y': 520, 'ground_x': 930,
            'query': 'city in fog smog 1940s', 'word': 1.2, 'mix': 0.85, 'why': 'the city learning to be weather, between the columns'}],
 'fx': [SHORE_DECK, {'kind': 'smoke', 't0': 0.5, 'alpha': 0.16, 'color': '#d8dadb', 'y0': 0.3, 'y1': 0.8, 'rise_s': 6}],
 'camera': cam(1.0, 960, 560, 1.08, 960, 580),
 'notes': ['No words: the reading pauses between poems 13 and 14 here, and the scene holds that pause (beats on seconds, not words).'],
}
SPECS['14.2'] = {
 'cast': [poet([960, 1000])],
 'beats': [('leave', 'POET', 'pose', {'card': '06'}, 'don\'t make me leave'),
           ('constellations', 'POET', 'pose', {'card': '04'}),
           ('broken', 'POET', 'pose', {'card': '28'}, 'broken'),
           ('escaped', 'POET', 'pose', {'card': '21'}),
           ('key', 'POET', 'pose', {'card': '07'}, 'a sharpened key of answers'),
           ('bravado', 'POET', 'pose', {'card': '02'}),
           ('safe', 'POET', 'pose', {'card': '03'}),
           ('timeless', 'POET', 'pose', {'card': '24'})],
 'joins': [{'kind': 'pane', 'surface': 'wall_1', 'inside': False, 'polygon': TEMPLE_COLONNADE, 'ground_y': 520, 'ground_x': 930,
            'query': 'stars constellations planetarium', 'word': 'spectrums', 'end_word': 'broken', 'mix': 0.9, 'why': 'light-filled constellations, in the colonnade'}],
 'fx': [SHORE_DECK, {'kind': 'smoke', 'alpha': 0.14, 'color': '#d8dadb', 'y0': 0.5, 'y1': 0.95, 'n': 8},
        {'kind': 'darken', 't0': 'escaped', 'dur': 4.0, 'alpha': 0.35}],
 'camera': cam(1.0, 960, 600, 1.12, 960, 640),
}
SPECS['14.3'] = {
 'cast': [poet([960, 880], stand='21')],
 'beats': [('whatever', 'POET', 'pose', {'card': '21'}),
           ('damn', 'POET', 'pose', {'card': '06'}, 'damn you'),
           ('love', 'POET', 'pose', {'card': '03'}),
           ('endure', 'POET', 'pose', {'card': '28'}, 'as we must endure')],
 'joins': [{'kind': 'wipe', 'surface': 'haze_0', 'query': 'ballroom dancing couples', 'word': 'love', 'mix': 0.55, 'wipe_s': 0.8, 'ground_y': 500,
            'why': 'all black again, but no walls: a ballroom wipes down behind him'}],
 'fx': VOID_FX,
 'camera': cam(1.0, 960, 560, 1.06, 960, 580),
}
SPECS['14.4'] = {
 'cast': [poet([1700, 1050], stand='24'), jointed('BROLL_1', 'street_clothes', [560, 640], 'profile', 'R'), jointed('BROLL_2', 'atlantis_citizen', [880, 650], 'front')],
 'beats': [('absent', 'POET', 'pose', {'card': '24'}, 'watching the reel'),
           ('absent', 'BROLL_1', 'walk_to', {'to': [760, 650], 'speed': 0.6}),
           ('highs', 'POET', 'pose', {'card': '02'}),
           ('lows', 'POET', 'pose', {'card': '28'}),
           ('impulse', 'POET', 'pose', {'card': '21'}),
           ('battle', 'POET', 'pose', {'card': '06'}, 'battle scars'),
           ('wisdom', 'POET', 'pose', {'card': '03'}),
           ('defeats', 'POET', 'pose', {'card': '15'})],
 'joins': [{'kind': 'screen', 'surface': 'screen_0', 'query': 'home movie family picnic 1950s', 'word': 'highs', 'end_word': 'materials', 'mix': 0.85,
            'why': 'the reel: a life\'s highs and lows on the set\'s own screen'},
           {'kind': 'screen', 'surface': 'screen_1', 'query': 'soldiers battle war', 'word': 'battle', 'end_word': 'defeats', 'mix': 0.85,
            'why': 'battle scars, on the same screen'}],
 'camera': cam(1.0, 1100, 600, 1.05, 1200, 620),
 'notes': ['Two b-roll extras walk inside the screen\'s street (tiny, at the plate\'s own scale); POET watches from the dark in front of it.'],
}
SPECS['14.5'] = {
 'cast': [poet([820, 900], stand='21'), soul([1100, 900], id='POET_MUSE', ghost=0.6, stand='21', view='front')],
 'goals': [sway('POET', bpm=96, amp=0.8, t0='dance', t1='minute'), sway('POET_MUSE', bpm=96, amp=0.8, phase=0.5, t0='dance', t1='minute')],
 'beats': [('trust', 'POET', 'pose', {'card': '03'}, 'I trust that you\'ll be fine'),
           ('fine', 'POET_MUSE', 'pose', {'card': '15'}),
           ('escaped', 'POET', 'pose', {'card': '21'}),
           ('victory', 'POET_MUSE', 'pose', {'card': '20'}),
           ('minute', 'POET_MUSE', 'vanish', {'dur': 1.5}, 'for a hot minute')],
 'joins': [{'kind': 'wipe', 'surface': 'haze_0', 'query': 'tango couple dancing 1930s', 'word': 'dance', 'mix': 0.55, 'wipe_s': 0.8, 'ground_y': 500,
            'why': 'our dance together, as found film behind the two of him'}],
 'fx': VOID_FX,
 'camera': cam(1.0, 960, 580, 1.08, 960, 600),
 'notes': ['The muse is POET\'s own cards in vellum (cast.ghost 0.6): two entwined muses, one man.'],
}
DOOR = PROPS + '14.props.door/14.props.door__p13.png'
SPECS['14.6'] = {
 'cast': [poet([500, 900], walk=('05', '16')), jointed('GUEST_1', 'vintage_party', [1600, 860], 'threequarter', 'L', ghost=0.8, alpha=0),
          jointed('GUEST_2', 'vintage_party', [1790, 850], 'threequarter', 'L', ghost=0.8, alpha=0)],
 'beats': [('genesis', 'POET', 'walk_to', {'to': [1030, 885], 'arrive_word': 'ends'}, 'he chooses the door'),
           ('testament', 'GUEST_1', 'appear', {'dur': 1.2}), ('testament', 'GUEST_2', 'appear', {'dur': 1.4}),
           ('ends', 'POET', 'pose', {'card': '20'}, 'a greeting at the door'),
           (7.0, 'POET', 'walk_to', {'to': [1180, 882], 'speed': 0.7}, 'this time, he chooses the door'),
           (8.6, 'POET', 'vanish', {'dur': 1.0}),
           ('ends', 'GUEST_1', 'sway', {'bpm': 80, 'amp': 0.6, 'bars': 4}), ('ends', 'GUEST_2', 'sway', {'bpm': 80, 'amp': 0.6, 'bars': 4})],
 'joins': [{'kind': 'pane', 'surface': 'haze_0', 'inside': False, 'polygon': [[1085, 330], [1300, 330], [1300, 875], [1085, 875]], 'ground_y': 884, 'ground_x': 1085,
            'query': 'party 1930s amateur film', 'word': 'genesis', 'mix': 0.85, 'why': 'the slow party, through the open door'}],
 'fx': VOID_FX + [card(DOOR, [1250, 880], 210, ground_y=880)],
 'camera': cam(1.0, 900, 580, 1.08, 1100, 600),
 'notes': ['The door is the painted 14.props.door card (p13, open, cream light) at 210 cm; the party is seen through it as found film, the guests as vellum.'],
}
