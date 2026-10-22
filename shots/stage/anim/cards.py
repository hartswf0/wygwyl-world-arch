"""What every card IS: the registry the puppet solver draws from and check.py verifies against.

rigs.py resolves the base body cards (torso, limbs, feet, heads) per view. This module adds what the
retarget left out, each mapped by eye from contact sheets of the cut parts (the cutter's part ids are often
shifted against the sheet labels, so ids are listed explicitly, never guessed from names):

  HANDS    hand-shape cards per character: shape x view (back/palm) x intrinsic side, with the sheet's tab
           orientation (where the wrist eyelet is) so wrist, axis, grip point and tip can be resolved.
  FACES    blank head plates plus eye / brow / mouth patches and where each sits on the plate.
  SETS     the poet's replacement sheets (sitting, kneeling, deep crouch, side lying, back lying, falling).
  CAST     extra characters built on the 21-part template sheets (torso front/back/profile, hip bridge,
           seat, limbs L/R, garment overlays, feet front/profile/lifted) plus their heads.
  SHOES    which foot cards belong to which costume (a shoe from another costume is a check failure).

Card meta (CARD[id]) used by check.py:
  role  torso|bridge|seat|skirt|uarm|farm|hand|thigh|shin|foot|head|eyes|brows|mouth|glasses|prop
  side  'L'|'R'|None        intrinsic side as drawn (None: one card serves both sides)
  view  front|profile|back|threequarter|threequarter_back|any
  faces +1/-1/0             which way a profile card points as drawn (toe, nose, chest)
  shape hand shape name     (hands only)
  set   stand|sit|kneel|crouch|lie_side|lie_back|fall   (replacement sheets)
  owner character name(s) the card belongs to (costume)
"""
import os
import rigs

C = 'poet.red_black_sunglasses'
CARD = {}


def reg(pid, **meta):
    m = CARD.setdefault(pid, {})
    m.update({k: v for k, v in meta.items() if v is not None or k not in m})
    return pid


def sheet_ids(sheet):
    return [p['id'] for p in rigs.catalog_sheet(sheet)]


# --------------------------------------------------------------------------------------------- hands
# The poet's hand sheet: 12 shapes, back row and palm row, wrist tab on the LEFT, fingers right, thumb on
# the TOP edge in both rows. With the thumb on top and fingers pointing right, the back row is a RIGHT
# hand seen from the back and the palm row a LEFT hand seen from the palm, so a card's intrinsic side
# follows from its row. The cut ids are shifted against the printed labels; this is the visual mapping.
_PH = sheet_ids(C + '.hands') if rigs.has_sheet(C + '.hands') else []
POET_SHAPES = {  # shape: (back index, palm index)
    'relaxed': (0, 6), 'open': (1, 7), 'fist': (2, 8), 'grip': (3, 9), 'pinch': (4, 10), 'point': (5, 11),
    'peace': (12, 19), 'flat': (13, 23), 'thumb': (14, 18), 'wave': (15, 20), 'claw': (16, 21), 'cup': (17, 22)}


def _poet_hands():
    cards = {}
    for shape, (bi, pi) in POET_SHAPES.items():
        cards[(shape, 'back', 'R')] = reg(_PH[bi], role='hand', side='R', view='back', shape=shape, owner='poet')
        cards[(shape, 'palm', 'L')] = reg(_PH[pi], role='hand', side='L', view='palm', shape=shape, owner='poet')
    return {'tab': 'left', 'ref': _PH[0], 'cards': cards, 'sheet': C + '.hands'}


def _labelled(sheet, table, tab, ref, owner, view='any', tabs=None):
    """A sheet whose cards are drawn as separate L and R hands. table: shape -> (L index, R index)."""
    ids = sheet_ids(sheet)
    cards = {}
    for shape, (li, ri) in table.items():
        v = view if isinstance(view, str) else view.get(shape, 'any')
        for side, i in (('L', li), ('R', ri)):
            if i is None: continue
            cards[(shape, v, side)] = reg(ids[i], role='hand', side=side, view=v, shape=shape, owner=owner)
    out = {'tab': tab, 'ref': ids[ref], 'cards': cards, 'sheet': sheet}
    if tabs:
        out['tabs'] = {ids[i]: t for i, t in tabs.items()}
    return out


def _poet13():
    # poem 13 gesture hands: L/R pairs, tab on top (hello wave: tab at the bottom, fingers up)
    t = {'pinch_cup': (0, 1), 'pinch_letter': (2, 3), 'grip_stem': (4, 5), 'armful': (6, 7), 'grip_blossom': (8, 9),
         'pinch_glasses': (10, 11), 'hello': (12, 13), 'edge_grip': (14, 15), 'release': (16, 17)}
    return _labelled('poet.13.hands', t, 'top', 16, 'poet', tabs={12: 'bottom', 13: 'bottom'})


def _harvest():
    t = {'stem_grip': (7, 8), 'release_open': (9, 10)}
    return _labelled('poet.13.action.harvest-parts', t, 'top', 9, 'poet')


def _djguest(glow):
    # party.07.dj-guest.action-hands: rows 1-2 carry the DJ's glowing cuffs, rows 3-4 the guest's plain cuffs.
    # L cards: tab left, fingers right. R cards: tab right, fingers left (mapped by eye; cut ids are shifted).
    o = 0 if glow else 12
    t = {'open': (o + 0, o + 1), 'relaxed': (o + 2, o + 3), 'flat': (o + 4, o + 5), 'cup': (o + 6, o + 7),
         'grip': (o + 6, o + 7), 'pinch': (o + 8, o + 9), 'point': (o + 10, o + 11)}
    ids = sheet_ids('party.07.dj-guest.action-hands')
    tabs = {}
    for shape, (li, ri) in t.items():
        tabs[li] = 'left'; tabs[ri] = 'right'
    h = _labelled('party.07.dj-guest.action-hands', t, 'left', o + 2, 'dj' if glow else 'party_guest',
                  view={'open': 'palm'}, tabs=tabs)
    for (shape, v, side), pid in list(h['cards'].items()):
        if v == 'any':
            h['cards'][(shape, 'back', side)] = pid
    return h


def _woman():
    # woman.13.heads-hands: open L/R (palm), relaxed, sill rest. Tab on top.
    t = {'open': (17, 18), 'relaxed': (19, 20), 'rest': (21, 22), 'wave': (17, 18), 'flat': (17, 18)}
    return _labelled('woman.13.heads-hands', t, 'top', 19, 'woman', view={'open': 'palm', 'wave': 'palm', 'flat': 'palm'})


def _child():
    # young_poet.child_clothes.hands: one hand drawn per shape, tab at the bottom (fingers up); the cards
    # read as a RIGHT hand. 0/1 are whole-sheet scraps and are not used.
    ids = sheet_ids('young_poet.child_clothes.hands')
    t = {'grip': 2, 'fist': 3, 'pinch': 4, 'thumb': 5, 'peace': 6, 'wave': 7, 'open': 8, 'flat': 8, 'relaxed': 9,
         'cup': 9, 'claw': 11}
    cards = {}
    for shape, i in t.items():
        cards[(shape, 'any', 'R')] = reg(ids[i], role='hand', side='R', view='any', shape=shape, owner='young_poet')
    return {'tab': 'bottom', 'tabs': {ids[5]: 'left'}, 'ref': ids[9], 'cards': cards,
            'sheet': 'young_poet.child_clothes.hands'}


HANDS = {}


def hands(name):
    if name in HANDS: return HANDS[name]
    if name in ('poet_tracksuit', 'poet_tshirt'):
        h = [_poet_hands(), _poet13(), _harvest()]
    elif name == 'dj':
        h = [_djguest(True)]
    elif name == 'party_guest':
        h = [_djguest(False)]
    elif name == 'woman':
        h = [_woman()]
    elif name == 'young_poet':
        h = [_child()]
    elif name in CROP_HANDS:
        h = [CROP_HANDS[name]()]
    else:
        h = []
    HANDS[name] = h
    return h


# shapes that may stand in for one another when a sheet lacks the asked one (check.py accepts these)
SHAPE_ALIAS = {
    'grip': ['grip', 'cup', 'fist', 'grip_stem', 'stem_grip', 'grip_blossom', 'edge_grip', 'receiver'],
    'cup': ['cup', 'grip', 'armful'], 'flat': ['flat', 'open', 'release', 'release_open', 'wave'],
    'open': ['open', 'wave', 'release', 'release_open', 'flat', 'hello', 'argue'], 'point': ['point'],
    'pinch': ['pinch', 'pinch_cup', 'pinch_letter', 'pinch_glasses'], 'fist': ['fist', 'grip'],
    'relaxed': ['relaxed', 'rest', 'open'], 'wave': ['wave', 'hello', 'open'], 'hello': ['hello', 'wave', 'open'],
    'argue': ['argue', 'open', 'wave'], 'pray': ['pray', 'cup', 'flat'], 'receiver': ['receiver', 'grip'],
}


def shape_ok(want, got):
    if want is None or got is None: return True
    return got == want or got in SHAPE_ALIAS.get(want, [want]) or want in SHAPE_ALIAS.get(got, [])


# --------------------------------------------------------------------------------------------- crops
# Some template sheets were never cut into separate hands / features (the cutter merged the whole panel
# into one part). Those are cropped from the PACK sheet into shots/stage/anim/parts/crop/ by crops.py, with
# the white ground keyed out. Boxes are in pack-sheet pixels.
CROPS = {
    # father_02 action hands (parents.02.father_02.heads-hands, 1536x1024)
    'father.open_L': ('parents.02.father_02.heads-hands', (20, 590, 250, 760)),
    'father.open_R': ('parents.02.father_02.heads-hands', (280, 590, 500, 760)),
    'father.grip_L': ('parents.02.father_02.heads-hands', (560, 590, 760, 760)),
    'father.grip_R': ('parents.02.father_02.heads-hands', (830, 590, 1030, 760)),
    'father.fist_L': ('parents.02.father_02.heads-hands', (1060, 590, 1250, 760)),
    'father.fist_R': ('parents.02.father_02.heads-hands', (1320, 590, 1500, 760)),
    'father.eyes_strain': ('parents.02.father_02.heads-hands', (880, 105, 1100, 175)),
    'father.brows_strain': ('parents.02.father_02.heads-hands', (1115, 105, 1340, 165)),
    'father.mouth_strain': ('parents.02.father_02.heads-hands', (1350, 90, 1490, 180)),
    'father.eyes_pain': ('parents.02.father_02.heads-hands', (880, 280, 1100, 350)),
    'father.brows_pain': ('parents.02.father_02.heads-hands', (1115, 275, 1340, 335)),
    'father.mouth_pain': ('parents.02.father_02.heads-hands', (1350, 260, 1490, 350)),
}

CROP_HANDS = {}


def _father_hands():
    cards = {}
    for shape, nm in (('argue', 'open'), ('open', 'open'), ('wave', 'open'), ('grip', 'grip'), ('fist', 'fist'), ('relaxed', 'grip')):
        for side in 'LR':
            pid = 'crop:father.%s_%s' % (nm, side)
            cards[(shape, 'any', side)] = reg(pid, role='hand', side=side, view='any', shape=shape if nm != 'grip' or shape == 'grip' else shape, owner='father')
    tabs = {'crop:father.open_L': 'right', 'crop:father.open_R': 'left', 'crop:father.grip_L': 'left',
            'crop:father.grip_R': 'right', 'crop:father.fist_L': 'left', 'crop:father.fist_R': 'right'}
    return {'tab': 'left', 'tabs': tabs, 'ref': 'crop:father.open_R', 'cards': cards, 'sheet': 'parents.02.father_02.heads-hands'}


CROP_HANDS['father'] = _father_hands


# --------------------------------------------------------------------------------------------- faces
# Feature patches sit on a blank head plate. 'at' = centre of the patch as a fraction of the PLATE card
# (x from the card's left, y from its top), 'w' = patch width as a fraction of the plate width. Placed by
# eye on rendered test sheets (frames/face_*.png). Profile plates face screen-right as drawn.
def _ids(sheet, names):
    ids = {p.split('/')[-1]: p for p in sheet_ids(sheet)}
    return {k: ids[v] for k, v in names.items()}


FACES = {}


def faces(name):
    if name in FACES: return FACES[name]
    F = {}
    if name in ('poet_tracksuit', 'poet_tshirt'):
        sp = C + '.face.profile'
        prof = {
            'eyes': _ids(sp, {'open': 'open', 'wide': 'wide', 'half': 'half', 'closed': 'closed', 'squint': 'squint',
                              'happy': 'happy-arc', 'sad': 'sad', 'glance': 'glance-side'}),
            'brows': _ids(sp, {'rest': 'rest', 'raised': 'raised', 'knit': 'knit', 'sad': 'sad-2', 'one_up': 'one-up',
                               'angry': 'angry'}),
            'mouth': _ids(sp, {'rest': 'rest-2', 'smile': 'smile', 'grin': 'grin-teeth', 'O': 'open-o', 'A': 'open-a',
                               'E': 'angry-2', 'U': 'rest-3', 'MBP': 'm-b-p', 'FV': 'f-v', 'frown': 'frown',
                               'strain': 'strain-teeth', 'wavy': 'wavy'}),
            # head plate is the .heads profile card (same art as the face sheet's blank plate, already rigged)
            'at': {'eyes': (0.735, 0.43, 0.27), 'brows': (0.71, 0.305, 0.33), 'mouth': (0.755, 0.605, 0.30)},
        }
        sf = C + '.face.front'
        front = {
            'eyes': _ids(sf, {'open': 'open', 'wide': 'wide', 'half': 'half', 'closed': 'closed', 'squint': 'squint',
                              'happy': 'part-8', 'sad': 'sad', 'glance': 'wide-2'}),
            'brows': _ids(sf, {'rest': 'rest', 'raised': 'part-14', 'knit': 'knit', 'sad': 'sad-3', 'one_up': 'one-up',
                               'angry': 'part-18'}),
            'mouth': _ids(sf, {'rest': 'rest-2', 'smile': 'part-22', 'grin': 'part-23', 'O': 'open-a', 'A': 'open-a-2',
                               'E': 'part-26', 'U': 'rest-3', 'MBP': 'm-b-p', 'FV': 'f-v', 'frown': 'frown',
                               'strain': 'open-a-3', 'wavy': 'wavy'}),
            'at': {'eyes': (0.5, 0.45, 0.70), 'brows': (0.5, 0.36, 0.72), 'mouth': (0.5, 0.70, 0.46)},
        }
        F = {'profile': prof, 'front': front, 'glasses_hide_eyes': name == 'poet_tracksuit'}
    elif name == 'woman':
        s = 'woman.13.heads-hands'
        front = {'eyes': _ids(s, {'open': '6-eyes-calm-open', 'gaze': '7-eyes-meeting-gaze', 'down': '8-eyes-looking-down'}),
                 'brows': _ids(s, {'rest': '9-brows-neutral', 'raised': '10-soft-raise', 'tender': 'tender'}),
                 'mouth': _ids(s, {'rest': '12-calm', 'smile': '13-small-smile', 'A': '14-mouth-recognition',
                                   'O': '14-mouth-recognition', 'E': '13-small-smile', 'MBP': '12-calm'}),
                 'at': {'eyes': (0.5, 0.56, 0.44), 'brows': (0.5, 0.49, 0.44), 'mouth': (0.5, 0.74, 0.30)}}
        F = {'front': front}
    elif name == 'father':
        front = {'eyes': {'strain': 'crop:father.eyes_strain', 'pain': 'crop:father.eyes_pain'},
                 'brows': {'strain': 'crop:father.brows_strain', 'pain': 'crop:father.brows_pain'},
                 'mouth': {'strain': 'crop:father.mouth_strain', 'pain': 'crop:father.mouth_pain'},
                 'at': {'eyes': (0.5, 0.45, 0.62), 'brows': (0.5, 0.37, 0.64), 'mouth': (0.5, 0.67, 0.38)}}
        F = {'front': front}
    for v, d in F.items():
        if not isinstance(d, dict): continue
        for part in ('eyes', 'brows', 'mouth'):
            for st, pid in d.get(part, {}).items():
                reg(pid, role=part, view=v, state=st, owner=name)
    FACES[name] = F
    return F


# --------------------------------------------------------------------------------------------- replacement sets
# The poet's six replacement sheets, mapped part by part (the cutter's ids are shifted on several sheets).
def _set(sheet, order):
    ids = sheet_ids(sheet)
    return {role: ids[i] for role, i in order.items()}


SETS = {}


def sets():
    if SETS: return SETS
    P = C + '.replacements.'
    std = dict(torso=0, uarm_L=1, uarm_R=2, farm_L=3, farm_R=4, bridge=5, seat=6, thigh_L=7, thigh_R=8, shin_L=9,
               shin_R=10, hand_L=11, hand_R=12, foot_L=13, foot_R=14)
    SETS['sit'] = _set(P + 'sitting', std)
    SETS['kneel'] = _set(P + 'kneeling', dict(torso=0, bridge=1, seat=2, uarm_L=3, uarm_R=4, farm_L=5, farm_R=6, hand_L=7,
                                              hand_R=8, shin_L=9, shin_R=10, thigh_L=11, thigh_R=12, foot_L=13, foot_R=14))
    SETS['crouch'] = _set(P + 'deep_crouch', dict(torso=0, seat=1, uarm_L=2, uarm_R=3, farm_L=4, farm_R=5, hand_L=6, hand_R=7,
                                                  bridge=8, thigh_L=9, thigh_R=10, shin_L=11, shin_R=12, foot_L=13, foot_R=14))
    lie = dict(torso=0, bridge=1, seat=2, uarm_L=3, uarm_R=4, farm_L=5, farm_R=6, hand_L=7, hand_R=8, thigh_L=9, thigh_R=10,
               shin_L=11, shin_R=12, foot_L=13, foot_R=14)
    SETS['lie_side'] = _set(P + 'side_lying', lie)
    SETS['lie_back'] = _set(P + 'back_lying', lie)
    SETS['fall'] = _set(P + 'falling', dict(uarm_L=0, uarm_R=1, torso=2, bridge=3, seat=4, farm_L=5, farm_R=6, hand_L=7, hand_R=8,
                                            thigh_L=9, thigh_R=10, shin_L=11, shin_R=12, foot_L=13, foot_R=14))
    for s, d in SETS.items():
        for role, pid in d.items():
            r = role.split('_')
            reg(pid, role=r[0], side=r[1] if len(r) > 1 else None, set=s, owner='poet',
                view='front' if r[0] in ('torso', 'bridge', 'seat') else 'any')
    return SETS


# --------------------------------------------------------------------------------------------- shoes
SHOES = {
    'poet_tracksuit': ['poet.red_black_sunglasses.feet/', 'pack:poet_tracksuit_v1/01_COMPONENTS/19_boot', 'pack:poet_tracksuit_v1/01_COMPONENTS/20_boot',
                       'poet.red_black_sunglasses.replacements.'],
    'poet_tshirt': ['poet.black_tshirt.compact-core/13-foot', 'poet.black_tshirt.compact-core/14-foot', 'poet.red_black_sunglasses.feet/'],
    'young_poet': ['young_poet.child_clothes.feet/'],
    'woman': ['woman.13.body/16-shoe', 'woman.13.body/17-shoe'],
    'ex': ['ex.ex_jacket.feet/'],
    'party_guest': ['party.party_guest.body.profile/14', 'party.party_guest.face-feet/'],
    'dj': ['party.dj_cyber.body.profile/foot', 'party.dj_cyber.compact-core/13', 'party.dj_cyber.compact-core/14', 'party.dj_cyber.face-feet/'],
    'father': ['parents.02.father_02.body/1', 'parents.02.father_02.body/2', 'parents.02.father_02.body/foot'],
    'mother': ['woman.09.mother.body/1', 'woman.09.mother.body/2'],
    'elder_man': ['family.13.elder_man.body/'],
    'elder_woman': ['family.13.elder_woman.body/'],
}


def shoe_ok(character, pid):
    allowed = SHOES.get(character)
    if not allowed: return True
    return any(pid.startswith(a) for a in allowed)
