"""Requirements matrix: which cut-out pieces each Acting Arena challenge and each poem needs, what the cast
already has, and which missing pieces unlock the most.

    python3 shots/arena/requirements/requirements.py      (writes arena_requirements.json and .md next to this file)

Coverage states for a piece (per cast):
    missing            nothing usable exists
    generated_uncut    on a generated sheet, not yet cut out, pivoted or named (cast/man/build_cast.py does not exist yet)
    generated_fix      on a sheet but with a known fault (wrong colour, fused piece, wrong angle)
    rigged             cut out, pivoted and used by a rig (POET parts in weave/assets; arena dummy pieces)
    engine             not art: a rig or renderer feature (a mask, a shadow, an IK mode)
    n/a                does not apply to this cast

Poem actions are BELIEF: proposed from the environment labels in shots/cartoon_sequences.json, not from reading the
poems or from the user. Correct them in POEMS below and re-run.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# id: (group, description, {cast: state}, sheet or note)
E = {
    # ---- body sets by view
    'body.profile':        ('body', 'profile torso + hips + sleeves', {'man': 'generated_uncut', 'poet': 'rigged', 'dummy': 'rigged'}, 'man/body_profile.jpg'),
    'body.front':          ('body', 'front torso + hips + sleeves', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'rigged'}, 'man/body_front.jpg'),
    'body.threequarter':   ('body', '3/4 torso + hips + sleeves', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'missing'}, 'man/body_threequarter.jpg: head came out in profile'),
    'body.back':           ('body', 'back torso + hips + sleeves', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man/body_back.jpg'),
    'torso.bend':          ('body', 'chest and hips as separate pieces so the spine can bend (hunch, lift, bow)', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man sheets show torso and hips separately'),
    # ---- legs
    'legs.walk_profile':   ('legs', 'profile walk replacement legs (contact, passing, toe-off)', {'man': 'generated_uncut', 'poet': 'rigged', 'dummy': 'rigged'}, 'man/legs_walk.jpg'),
    'legs.segmented':      ('legs', 'separate thigh, shin and foot (profile) so the knee can be placed: crouch, kneel, mantle, lift', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'rigged'}, 'man/legs_segmented.jpg (2026-10-20); the arena dummy proves the need (ACT-006)'),
    'legs.run_profile':    ('legs', 'run legs with a flight phase: drive knee, extended push, recovery', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'engine'}, 'man/legs_run_stairs.jpg top row: most pieces are two legs fused together; cut apart or regenerate one leg per piece'),
    'legs.front_back':     ('legs', 'legs for front and back views (walking toward or away)', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'legs_walk.jpg has 2'),
    'legs.threequarter':   ('legs', 'legs for 3/4 view (diagonal walks, turns)', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'body_threequarter.jpg'),
    'legs.sit':            ('legs', 'sitting: horizontal thigh, hanging shin, front and profile', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man/body_sitting.jpg'),
    'legs.kneel':          ('legs', 'kneeling and half-kneeling (knee on the ground, foot flat behind)', {'man': 'generated_uncut', 'poet': 'rigged', 'dummy': 'rigged'}, 'POET skirt has knee sockets; man/legs_segmented.jpg example kneel'),
    'legs.stairs':         ('legs', 'stepping up and down: high knee, foot flat on a tread', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'engine'}, 'man/legs_run_stairs.jpg middle row: two legs fused per piece'),
    'legs.lie':            ('legs', 'lying on the side and back, legs relaxed (falls, getting up)', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'engine'}, 'man/legs_run_stairs.jpg bottom row'),
    'legs.jump_tuck':      ('legs', 'airborne tuck and reach-down legs', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'engine'}, 'man/legs_run_stairs.jpg middle right: pair fused'),
    'feet.loose':          ('legs', 'boots as separate pieces with heel/ball/toe pivots', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'rigged'}, 'man/legs_segmented.jpg: plain chelsea boots, flat / on toe / pointed / front'),
    # ---- arms
    'arms.profile':        ('arms', 'upper arm and forearm sleeves, near and far', {'man': 'generated_uncut', 'poet': 'rigged', 'dummy': 'rigged'}, 'man/body_profile.jpg'),
    'arms.foreshortened':  ('arms', 'short and flared arm pieces: reaching toward or away from camera, elbows out on an overhead pull', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man/arms_hands_contact.jpg top row; ACT-006 elbows hit the wall in pure profile'),
    'arms.overhead':       ('arms', 'arms raised overhead (hang, celebrate, stretch)', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'engine'}, 'man/arms_hands_contact.jpg long straight sleeves'),
    'thigh.foreshortened': ('legs', 'short thigh for a knee coming toward camera (kneel-up, step onto a ledge, sit seen from front)', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man/legs_segmented.jpg short thighs'),
    # ---- heads
    'heads.angles':        ('heads', 'six angles: profile L/R, 3/4 L/R, front, back', {'man': 'generated_uncut', 'poet': 'rigged', 'dummy': 'rigged'}, 'man/heads.jpg'),
    'heads.basic':         ('heads', 'neutral, smile, eyes closed, look up/down, speaking', {'man': 'generated_uncut', 'poet': 'rigged', 'dummy': 'rigged'}, 'man/heads.jpg, heads_front.jpg'),
    'heads.effort':        ('heads', 'strain, pain, out of breath, tired (profile and front)', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'rigged'}, 'heads_intent_effort.jpg top row came out front/3/4, not profile; heads_effort_threequarter.jpg is 3/4 too'),
    'heads.intent':        ('heads', 'fear, surprise, reluctance, embarrassment, false confidence, recognition (profile and 3/4)', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'rigged'}, 'heads_intent_effort.jpg bottom row is good 3/4; no strict profile came out of three tries'),
    'heads.visemes':       ('heads', 'mouth shapes for her words (A/I, E, O, U, M/B/P, F/V, rest) in front and 3/4', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'n/a'}, 'only speaking / singing / closed exist'),
    # ---- hands
    'hands.basic':         ('hands', 'open, relaxed, fist, point, palm up/down', {'man': 'generated_uncut', 'poet': 'rigged', 'dummy': 'rigged'}, 'man/hands.jpg'),
    'hands.grip_bar':      ('hands', 'closed round a bar or edge (ledge, railing, handrail, door handle), seen from both sides', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'rigged'}, 'arms_hands_contact.jpg: bar grips have the bar fused on; edge hook is clean'),
    'hands.carry':         ('hands', 'two-hand carry under a box or table edge; cup held from below', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'rigged'}, 'arms_hands_contact.jpg: cupped pair is clean; the box-lift hand has the box fused on'),
    'hands.catch':         ('hands', 'spread to catch, closing on an object; glove-like cupped pair', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'arms_hands_contact.jpg spread hand and ball pinch'),
    'hands.flat_push':     ('hands', 'palm flat on a surface (push a door, brace on a wall, press a ceiling)', {'man': 'generated_uncut', 'poet': 'rigged', 'dummy': 'rigged'}, 'hands_2.jpg palm out'),
    'hands.offer':         ('hands', 'offering and receiving: palm up holding, hand closing on an offered object', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'rigged'}, 'hands.jpg palm up'),
    'hands.touch_person':  ('hands', 'hand on a shoulder, a back, holding another hand', {'man': 'generated_fix', 'poet': 'missing', 'dummy': 'engine'}, 'arms_hands_contact.jpg: shoulder hand has a jacket piece fused on; clasped pair is clean'),
    'hands.gesture_dj':    ('hands', 'DJ and listening gestures: cupped ear, on a turntable, microphone', {'man': 'generated_uncut', 'poet': 'n/a', 'dummy': 'n/a'}, 'man/hands_2.jpg'),
    'hands.pocket':        ('hands', 'hand in pocket', {'man': 'generated_fix', 'poet': 'n/a', 'dummy': 'n/a'}, 'pocket came out khaki'),
    # ---- props
    'prop.cup':            ('props', 'cup, full and empty, with a liquid surface that can tilt', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'rigged'}, 'man/set_props.jpg'),
    'prop.box':            ('props', 'cardboard box, light and heavy dressing', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'rigged'}, 'man/set_props.jpg'),
    'prop.door':           ('props', 'door with frame, hinge pivot and handle socket', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'rigged'}, 'man/set_props.jpg'),
    'prop.chair':          ('props', 'chair or bench seat', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'props.jpg bench'),
    'prop.book':           ('props', 'notebook / book, open and closed', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'rigged'}, 'props.jpg'),
    'prop.ball':           ('props', 'balls (baseball, basketball, football, tennis) and a racket', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man/set_props.jpg'),
    'prop.table':          ('props', 'table, carried by two', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man/set_props.jpg'),
    'prop.ledge':          ('props', 'ledge, beam, wall top: a solid with a grip lip', {'man': 'n/a', 'poet': 'n/a', 'dummy': 'rigged'}, 'set piece'),
    'prop.railing':        ('props', 'railing section with a grip bar at hand height, front and profile', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man/set_props.jpg'),
    'prop.stairs':         ('props', 'stair flight with treads at a known rise/run (profile and 3/4)', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man/set_props.jpg'),
    'prop.vehicle_window': ('props', 'car door/window frame to sit behind (occluder with a seat line)', {'man': 'generated_uncut', 'poet': 'missing', 'dummy': 'missing'}, 'man/set_props.jpg'),
    'prop.sunglasses':     ('props', 'sunglasses on, off, folded', {'man': 'generated_uncut', 'poet': 'n/a', 'dummy': 'n/a'}, 'props.jpg'),
    'prop.dj':             ('props', 'record, turntable, tone-arm, headphones, microphone', {'man': 'generated_fix', 'poet': 'n/a', 'dummy': 'n/a'}, 'microphone came with a hand attached'),
    # ---- engine features (not art)
    'fx.waterline':        ('engine', 'cut the figure at a water surface and ripple the line (wading, swimming, standing in water)', {'man': 'engine', 'poet': 'engine', 'dummy': 'engine'}, 'arena draws water as a volume; no cut line yet'),
    'fx.contact_shadow':   ('engine', 'contact shadow under feet and props', {'man': 'engine', 'poet': 'engine', 'dummy': 'rigged'}, 'arena has it'),
    'fx.depth_scale':      ('engine', 'scale along a ground line for walking toward or away', {'man': 'engine', 'poet': 'engine', 'dummy': 'missing'}, 'arena is profile-only'),
    'fx.view_swap':        ('engine', 'replacement turn profile -> 3/4 -> front on a held frame', {'man': 'engine', 'poet': 'engine', 'dummy': 'rigged'}, 'arena swaps side/front only'),
}

# ---- Acting Arena challenges -> pieces (figure: who performs in the arena; all are biped)
COMMON = ['body.profile', 'legs.walk_profile', 'arms.profile', 'heads.angles', 'heads.basic', 'hands.basic', 'feet.loose', 'fx.contact_shadow']
ACT = {
    'ACT-001': ('Walk without spilling', ['prop.cup', 'hands.carry', 'fx.view_swap']),
    'ACT-002': ('Sprint and reconsider', ['legs.run_profile', 'heads.intent', 'fx.view_swap']),
    'ACT-003': ('Crouch under trouble', ['legs.segmented', 'torso.bend', 'prop.ledge']),
    'ACT-004': ('Spin and find the target', ['body.front', 'body.threequarter', 'body.back', 'legs.front_back', 'legs.threequarter', 'fx.view_swap']),
    'ACT-005': ('Jump into water', ['legs.jump_tuck', 'arms.overhead', 'heads.intent', 'fx.waterline', 'prop.ledge']),
    'ACT-006': ('Overshoot the ledge', ['legs.run_profile', 'legs.jump_tuck', 'legs.segmented', 'arms.overhead', 'arms.foreshortened', 'thigh.foreshortened', 'hands.grip_bar', 'heads.effort', 'prop.ledge']),
    'ACT-007': ('Slip and recover', ['arms.overhead', 'heads.intent', 'legs.segmented']),
    'ACT-008': ('Stand after a fall', ['legs.lie', 'legs.kneel', 'legs.segmented', 'heads.effort', 'torso.bend']),
    'ACT-009': ('Door opens the wrong way', ['prop.door', 'hands.grip_bar', 'hands.flat_push', 'heads.intent']),
    'ACT-010': ('The unexpectedly heavy box', ['prop.box', 'hands.carry', 'legs.segmented', 'torso.bend', 'heads.effort']),
    'ACT-011': ('Chair moved away', ['prop.chair', 'legs.sit', 'legs.segmented', 'heads.intent']),
    'ACT-012': ('Hand over reluctantly', ['prop.book', 'hands.offer', 'heads.intent']),
    'ACT-013': ('Punch that misses', ['hands.basic', 'arms.foreshortened', 'heads.effort']),
    'ACT-014': ('Kick and keep balance', ['legs.segmented', 'heads.effort']),
    'ACT-015': ('Block into retreat', ['arms.foreshortened', 'legs.segmented', 'heads.intent']),
    'ACT-016': ('Fight becomes apology', ['hands.offer', 'hands.touch_person', 'heads.intent']),
    'ACT-017': ('Dance through a missed beat', ['legs.segmented', 'heads.intent']),
    'ACT-018': ('Spin with a partner', ['hands.touch_person', 'body.front', 'fx.view_swap']),
    'ACT-019': ('Celebration interrupted', ['arms.overhead', 'legs.jump_tuck', 'heads.intent']),
    'ACT-020': ('Too big for the stage', ['arms.overhead', 'hands.flat_push', 'body.front']),
    'ACT-021': ('Cower then help', ['legs.segmented', 'torso.bend', 'hands.touch_person', 'heads.intent']),
    'ACT-022': ('Pretend the box is light', ['prop.box', 'hands.carry', 'heads.effort', 'heads.intent']),
    'ACT-023': ('The false confident entrance', ['heads.intent', 'prop.door', 'fx.view_swap']),
    'ACT-024': ('Wait without becoming inert', ['heads.intent', 'fx.view_swap']),
    'ACT-025': ('Baseball grounder', ['prop.ball', 'hands.catch', 'legs.segmented', 'legs.run_profile']),
    'ACT-026': ('Basketball fake', ['prop.ball', 'hands.catch', 'legs.jump_tuck', 'arms.overhead']),
    'ACT-027': ('Soccer whiff', ['prop.ball', 'legs.run_profile', 'legs.segmented']),
    'ACT-028': ('Tennis late return', ['prop.ball', 'legs.run_profile', 'legs.segmented', 'arms.foreshortened']),
    'ACT-029': ('Carry a table through a door', ['prop.table', 'prop.door', 'hands.carry']),
    'ACT-030': ('Crowded doorway', ['prop.door', 'hands.flat_push', 'hands.grip_bar']),
    'ACT-031': ('Catch a falling friend', ['hands.touch_person', 'arms.foreshortened', 'heads.intent']),
    'ACT-032': ('Chain reaction', ['prop.cup', 'hands.catch', 'heads.intent']),
}

# ---- poems: labels from cartoon_sequences.json; actions are BELIEF (proposed, not read from the poems)
POEMS = {
    '01': ('OUT OF LIFE', 'building, cloud, floor, sky, street lamp, wall, window',
           ['walks along the street under the lamp', 'stops at a window and looks in', 'looks up at the sky', 'walks away'],
           ['legs.front_back', 'body.back', 'fx.depth_scale', 'hands.pocket', 'fx.view_swap']),
    '02': ('FLASHING LIGHTS', 'building, sky, street lamp, wall, window, person',
           ['stands among people', 'turns toward the lights', 'shields the eyes'],
           ['body.front', 'body.threequarter', 'heads.intent', 'hands.flat_push', 'fx.view_swap']),
    '03': ('HOW TO BREAK OFF AN ENGAGEMENT', 'water, wall',
           ['leans on a wall by the water', 'sits on the wall', 'lets something go into the water'],
           ['legs.sit', 'prop.chair', 'hands.offer', 'heads.intent', 'torso.bend']),
    '04': ('NEVERMORE', 'person, vehicle, water',
           ['walks past a car', 'reaches toward another person', 'hands speak (p04_hands exists)'],
           ['arms.foreshortened', 'hands.touch_person', 'prop.vehicle_window', 'heads.visemes']),
    '05': ('BLOODLINES', 'person, wall',
           ['faces another person', 'hand on a shoulder', 'embrace'],
           ['hands.touch_person', 'body.front', 'body.threequarter', 'heads.intent']),
    '06': ('RESURRECTING ATLANTIS', 'railing, vehicle, water',
           ['leans on a railing over the water', 'grips the rail', 'looks down into the water'],
           ['prop.railing', 'hands.grip_bar', 'torso.bend', 'body.back', 'fx.waterline']),
    '07': ('DJ TURN ME UP', 'person, wall',
           ['DJ at a turntable', 'nods and bounces on the beat', 'sings to camera'],
           ['hands.gesture_dj', 'prop.dj', 'legs.segmented', 'heads.visemes', 'body.front']),
    '08': ('NEWLY SINGLE', 'railing, vehicle, water',
           ['walks along a railing', 'sits in a car and looks out the window'],
           ['prop.railing', 'prop.vehicle_window', 'legs.sit', 'heads.intent']),
    '09': ('YET, HEARD', 'sign, stairs, street, water, window',
           ['climbs stairs', 'reads a sign', 'cups an ear to listen'],
           ['legs.stairs', 'prop.stairs', 'legs.segmented', 'hands.gesture_dj', 'body.threequarter']),
    '10': ('MAGIC RIDE', 'railing',
           ['rides standing, holding a rail', 'sways with the motion'],
           ['prop.railing', 'hands.grip_bar', 'body.front', 'arms.overhead']),
    '11': ('NEW DAY', 'door, stairs, water, window',
           ['opens a door', 'goes down stairs', 'looks out a window at the water'],
           ['prop.door', 'hands.grip_bar', 'legs.stairs', 'prop.stairs', 'body.back']),
    '12': ('REUNION', 'water, window',
           ['sees someone', 'walks toward camera', 'embrace'],
           ['fx.depth_scale', 'legs.front_back', 'arms.foreshortened', 'hands.touch_person', 'heads.intent']),
    '13': ('HOW TO WIN MY HEART', 'stairs, vehicle, water',
           ['climbs stairs', 'kneels', 'offers something'],
           ['legs.stairs', 'prop.stairs', 'legs.kneel', 'legs.segmented', 'thigh.foreshortened', 'hands.offer']),
    '14': ('HOT MINUTE', 'person, water',
           ['runs along the water with someone', 'wades in'],
           ['legs.run_profile', 'fx.waterline', 'hands.touch_person', 'heads.basic']),
}

ORDER = ['missing', 'generated_fix', 'generated_uncut', 'rigged', 'engine', 'n/a']


def build():
    uses = {k: {'challenges': [], 'poems': []} for k in E}
    for a, (title, els) in ACT.items():
        for e in COMMON + els:
            uses[e]['challenges'].append(a)
    for p, (title, labels, actions, els) in POEMS.items():
        for e in COMMON + els:
            uses[e]['poems'].append(p)
    elements = []
    for k, (grp, desc, cov, note) in E.items():
        u = uses[k]
        elements.append({'id': k, 'group': grp, 'description': desc, 'coverage': cov, 'note': note,
                         'challenges': sorted(set(u['challenges'])), 'poems': sorted(set(u['poems']))})
    # gaps: art the man needs to generate (or regenerate), ranked by what it unlocks
    gaps = []
    for el in elements:
        st = el['coverage'].get('man')
        if st in ('missing', 'generated_fix'):
            n = len(el['challenges']) + 2 * len(el['poems'])  # a poem counts double: the poems are the film
            gaps.append({'id': el['id'], 'man': st, 'score': n, 'challenges': len(el['challenges']), 'poems': len(el['poems']),
                         'kind': 'engine' if el['group'] == 'engine' else 'art'})
    gaps.sort(key=lambda g: (-g['score'], g['id']))
    return {
        'about': __doc__.strip().splitlines()[0],
        'coverage_states': ORDER,
        'poem_actions_status': 'BELIEF: proposed from environment labels, not read from the poems',
        'common': COMMON,
        'elements': elements,
        'challenges': {a: {'title': t, 'needs': sorted(set(COMMON + els))} for a, (t, els) in ACT.items()},
        'poems': {p: {'title': t, 'labels': lab, 'proposed_actions': act, 'needs': sorted(set(COMMON + els))}
                  for p, (t, lab, act, els) in POEMS.items()},
        'gaps_ranked': gaps,
    }


def to_md(R):
    L = ['# Acting Arena: requirements matrix', '',
         'Generated by [requirements.py](requirements.py). Which cut-out pieces each challenge and each poem needs, what exists, and what to generate next.', '',
         '> Poem actions are **BELIEF**: proposed from the environment labels in `shots/cartoon_sequences.json`, not from the poem texts. Correct them in `POEMS` and re-run.', '',
         'Coverage states: `missing`, `generated_fix` (sheet exists with a known fault), `generated_uncut` (on a sheet, not cut out), `rigged`, `engine` (a renderer feature, not art), `n/a`.', '',
         '## Gaps for the man, ranked', '',
         'Score = challenges that need it + 2 x poems that need it.', '',
         '| Rank | Piece | Kind | Man | Challenges | Poems | Score |', '| --: | :-- | :-- | :-- | --: | --: | --: |']
    for i, g in enumerate(R['gaps_ranked'], 1):
        L.append('| %d | `%s` | %s | %s | %d | %d | %d |' % (i, g['id'], g['kind'], g['man'], g['challenges'], g['poems'], g['score']))
    L += ['', '## Pieces', '', '| Piece | What | Man | POET | Dummy | Note |', '| :-- | :-- | :-- | :-- | :-- | :-- |']
    for el in R['elements']:
        c = el['coverage']
        L.append('| `%s` | %s | %s | %s | %s | %s |' % (el['id'], el['description'], c.get('man'), c.get('poet'), c.get('dummy'), el['note']))
    L += ['', '## Poems (BELIEF)', '', '| Poem | Labels | Proposed actions | Extra pieces |', '| :-- | :-- | :-- | :-- |']
    for p, v in R['poems'].items():
        extra = [e for e in v['needs'] if e not in R['common']]
        L.append('| %s %s | %s | %s | %s |' % (p, v['title'], v['labels'], '; '.join(v['proposed_actions']), ', '.join('`%s`' % e for e in extra)))
    L += ['', '## Challenges', '', 'Every challenge also needs the common set: ' + ', '.join('`%s`' % e for e in R['common']) + '.', '',
          '| Challenge | Extra pieces |', '| :-- | :-- |']
    for a, v in R['challenges'].items():
        extra = [e for e in v['needs'] if e not in R['common']]
        L.append('| %s %s | %s |' % (a, v['title'], ', '.join('`%s`' % e for e in extra)))
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    R = build()
    json.dump(R, open(os.path.join(HERE, 'arena_requirements.json'), 'w'), indent=1)
    open(os.path.join(HERE, 'arena_requirements.md'), 'w').write(to_md(R))
    for i, g in enumerate(R['gaps_ranked'][:15], 1):
        print(i, g['id'], g['kind'], g['man'], g['score'])
