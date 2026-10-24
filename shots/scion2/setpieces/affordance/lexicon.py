"""Label lexicon: which affordance kinds a part's catalog label asks for.

Measured: words read off catalog `label` (+ `name`; the part-id slug only when the label is empty).
Every match returns the words that fired, their position, and the block words that vetoed a kind, so the
decision can be audited from affordance.json alone.
"""
import re

KINDS = ['seat', 'surface', 'grip', 'aperture', 'lean', 'occluder', 'stand_on']


def tokens(text):
    t = (text or '').lower()
    t = t.replace('pewback', 'pew back').replace('countertop', 'counter top').replace('doorpost', 'door post')
    t = t.replace('doorstep', 'door step').replace('streetlamp', 'street lamp').replace('trapdoor', 'trap door')
    t = t.replace('standpole', 'stand pole').replace('street lamp', 'lamppost').replace('streetlamp', 'lamppost').replace('doorway', 'door way').replace('archway', 'arch way')
    t = t.replace('gateway', 'gate way').replace('headboard', 'head board').replace('doorl', 'door l')
    t = t.replace('doorr', 'door r')
    w = re.findall(r'[a-z]+', t)
    out = []
    for x in w:
        if len(x) > 3 and x.endswith('s') and not x.endswith('ss') and x not in ('glass', 'pews', 'stairs', 'steps', 'blinds'):
            x = x[:-1]
        out.append(x)
    # 'stairs'/'steps' -> singular too
    return [{'stairs': 'stair', 'steps': 'step', 'pews': 'pew', 'blinds': 'blind'}.get(x, x) for x in out]


SEAT = {'chair': 1.0, 'armchair': 1.0, 'sofa': 1.0, 'couch': 1.0, 'bench': 1.0, 'pew': 1.0, 'stool': 1.0,
        'seat': 1.0, 'saddle': 0.9, 'mattress': 0.9, 'bed': 0.9, 'cushion': 0.9, 'settee': 1.0, 'throne': 1.0,
        # secondary seats: you can sit on these, but they are not furniture
        'stoop': 0.6, 'step': 0.5, 'kerb': 0.45, 'curb': 0.45}
SURFACE = {'table': 1.0, 'desk': 1.0, 'counter': 1.0, 'shelf': 1.0, 'sill': 0.9, 'ledge': 0.8, 'tray': 0.7,
           'plinth': 0.7, 'pedestal': 0.7, 'drawer': 0.9, 'dresser': 1.0, 'cabinet': 0.9, 'crate': 0.7,
           'mantel': 1.0, 'niche': 0.6, 'altar': 0.9, 'box': 0.45, 'riser': 0.6, 'booth': 0.5,
           'bar': 0.6, 'speaker': 0.45, 'suitcase': 0.35}
GRIP = {'cup': 1.0, 'mug': 1.0, 'coupe': 1.0, 'goblet': 1.0, 'saucer': 0.8, 'bottle': 1.0, 'phone': 0.9,
        'receiver': 1.0, 'handset': 1.0, 'microphone': 1.0, 'mic': 0.9, 'lantern': 1.0, 'candle': 0.9,
        'guitar': 1.0, 'journal': 1.0, 'book': 1.0, 'letter': 0.8, 'paper': 0.7, 'envelope': 1.0, 'snapshot': 1.0,
        'photo': 0.9, 'photograph': 1.0, 'vape': 1.0, 'lighter': 1.0, 'tambourine': 1.0, 'record': 0.7,
        'vinyl': 1.0, 'hourglass': 0.8, 'staff': 0.9, 'coin': 0.8, 'flower': 0.7, 'poppy': 0.8, 'daisy': 0.7,
        'blossom': 0.6, 'rose': 0.5, 'bouquet': 1.0, 'armful': 0.8, 'umbrella': 1.0, 'bag': 0.8, 'key': 0.8,
        'knife': 1.0, 'pen': 0.8, 'rosary': 0.9, 'pearl': 0.7, 'football': 0.9, 'ball': 0.7, 'torch': 1.0,
        'suitcase': 1.0, 'ring': 0.5, 'glasses': 0.7, 'jacket': 0.4, 'remote': 0.8, 'bread': 0.6}
SURF_BLOCK = {'insert', 'overlay', 'light', 'lid', 'glow', 'cord', 'reflection', 'post', 'pole', 'leg', 'cable',
              'screen', 'knob', 'disc', 'platter', 'handle', 'zip', 'cone', 'grille', 'scorched', 'half', 'clip',
              'base', 'round', 'spindle', 'cup', 'espresso', 'saucer', 'step', 'controller', 'inner'}
GRIP_BLOCK = {'insert', 'overlay', 'screen', 'glow', 'reflection', 'shard', 'fragment', 'sand', 'petal', 'jingle',
              'strip', 'motion', 'arc', 'ash', 'cable', 'corona', 'expansion', 'miracle', 'rim', 'water', 'light',
              'beam', 'flash', 'smoke', 'haze', 'remnant', 'tab', 'base', 'backing', 'sky', 'sun', 'band', 'wall',
              'facade', 'floor', 'tower', 'paving', 'trim', 'shelf', 'tray', 'pane', 'road', 'hook', 'dance', 'mask',
              'wash', 'word', 'cave', 'inlay', 'expansion', 'lid', 'stand', 'pole', 'clip', 'support', 'axle'}
APERT = {'door': 1.0, 'window': 1.0, 'gate': 1.0, 'arch': 0.8, 'portal': 1.0, 'opening': 1.0, 'aperture': 1.0,
         'entrance': 1.0, 'exit': 0.8, 'casing': 0.9, 'sash': 0.9, 'lancet': 0.8, 'hatch': 1.0, 'trap': 0.6,
         'belfry': 0.7, 'frame': 0.6, 'way': 0.0}
APERT_BLOCK = {'glass', 'pane', 'glazing', 'insert', 'curtain', 'mullion', 'blind', 'film', 'reflection',
               'backing', 'backer', 'sill', 'rod', 'trim', 'knob', 'hinge', 'tab', 'light', 'sign', 'mask', 'view',
               'meter', 'mirror', 'picture', 'cage', 'overlay', 'sheen', 'lamp', 'valance', 'awning', 'strip',
               'gel', 'portrait', 'nine', 'slot', 'tyre', 'triangulated', 'lit', 'unlit', 'smoked', 'post', 'step',
               'glow', 'water', 'insert', 'remnant', 'leaf_foliage', 'petal', 'rim', 'lantern', 'cage', 'iris'}
APERT_STRONG = {'opening', 'aperture', 'casing', 'empty'}   # override blocks: 'FRONT OPEN FRAME', 'empty aperture'
LEAF = {'leaf', 'slab', 'slider', 'sliding', 'trap'}
LEAN_V = {'wall': 0.9, 'column': 1.0, 'pillar': 1.0, 'pier': 0.9, 'post': 0.9, 'pole': 0.9, 'trunk': 0.9,
          'facade': 0.6, 'strut': 0.6, 'lamppost': 1.0, 'mesh': 0.6, 'tower': 0.4, 'bollard': 0.5, 'tree': 0.5,
          'doorpost': 1.0}
LEAN_H = {'railing': 1.0, 'rail': 0.8, 'fence': 1.0, 'balustrade': 1.0, 'parapet': 1.0, 'counter': 0.8,
          'bar': 0.6, 'sill': 0.6}
LEAN_BLOCK = {'blind', 'curtain', 'lamp', 'overlay', 'sheen', 'reflection', 'card', 'strip', 'line', 'shadow',
              'light', 'water', 'glazing', 'pane', 'insert', 'window', 'floor', 'ceiling', 'plate', 'backing',
              'notch', 'cord', 'stem', 'clip', 'pull', 'top', 'roof', 'cap', 'treeline', 'ridge', 'skyline',
              'silhouette', 'beam', 'canopy', 'dew'}
OCC = {'table': 1.0, 'desk': 1.0, 'counter': 1.0, 'bar': 0.8, 'booth': 0.6, 'sofa': 1.0, 'couch': 1.0,
       'bench': 0.9, 'pew': 1.0, 'armchair': 1.0, 'chair': 0.7, 'bed': 0.8, 'arm': 0.6, 'car': 1.0, 'hull': 0.8,
       'boat': 0.8, 'railing': 0.9, 'rail': 0.6, 'fence': 0.9, 'mesh': 0.7, 'balustrade': 0.9, 'parapet': 1.0,
       'bush': 1.0, 'hedge': 1.0, 'shrub': 1.0, 'weed': 0.8, 'grass': 0.5, 'bloom': 0.6, 'planter': 0.9,
       'stump': 0.7, 'box': 0.5, 'crate': 0.8, 'drawer': 0.8, 'cabinet': 0.8, 'speaker': 0.7, 'plinth': 0.6,
       'kerb': 0.5, 'curb': 0.5, 'stoop': 0.5, 'headboard': 0.5, 'board': 0.0, 'suitcase': 0.4,
       'motorcycle': 0.8, 'chassis': 0.6, 'stall': 0.7, 'pedestal': 0.5, 'stand': 0.4, 'flower': 0.3}
OCC_BLOCK = {'wheel', 'insert', 'light', 'glass', 'pane', 'reflection', 'overlay', 'strip', 'top', 'cushion',
             'pillow', 'blanket', 'curtain', 'blind', 'cord', 'clip', 'line', 'shadow', 'sheen', 'cap', 'lid',
             'knob', 'headlight', 'steering', 'seat', 'view', 'tab', 'lid', 'glow', 'inner', 'raven', 'ash',
             'controller', 'pole', 'clip', 'base', 'marquee', 'floor', 'soil', 'stubble', 'tree', 'cup', 'espresso'}
STAND = {'step': 1.0, 'stair': 1.0, 'tread': 1.0, 'stoop': 1.0, 'landing': 1.0, 'platform': 1.0, 'plinth': 0.8,
         'riser': 0.8, 'dais': 1.0, 'stage': 0.9, 'threshold': 0.8, 'kerb': 0.7, 'curb': 0.7, 'catwalk': 0.9,
         'lip': 0.6, 'terrace': 0.7, 'quay': 0.6, 'deck': 0.7,
         # ground bands: standing surface, but their geometry is the space swarm's walk band
         'floor': 0.5, 'road': 0.45, 'path': 0.45, 'trail': 0.45, 'driveway': 0.45, 'pavement': 0.45,
         'paving': 0.45, 'ground': 0.45, 'soil': 0.4, 'tarmac': 0.45, 'sidewalk': 0.45, 'street': 0.4,
         'forecourt': 0.45, 'apron': 0.45, 'shore': 0.3, 'mud': 0.3, 'stubble': 0.3}
STAND_BLOCK = {'lamp', 'reflection', 'water', 'sky', 'line', 'dash', 'tick', 'overlay', 'sheen', 'light', 'flood',
               'glow', 'mirror', 'edge', 'shadow', 'rain', 'fog', 'map', 'lines', 'trim', 'globe', 'cage', 'tab',
               'hinge', 'top', 'emblem', 'recess', 'insert', 'wall', 'end', 'strut', 'parquet', 'splinter', 'clip',
               'controller', 'side', 'rail', 'roof', 'lamppost', 'remnant', 'ring', 'inlay', 'socket',
               'jingle', 'dash', 'reflectio', 'card'}
GROUND_WORDS = {'floor', 'road', 'path', 'trail', 'driveway', 'pavement', 'paving', 'ground', 'soil', 'tarmac',
                'sidewalk', 'street', 'forecourt', 'apron', 'shore', 'mud', 'stubble'}


NOTE_WORDS = {'separate', 'reuse', 'align', 'extraction', 'note', 'asset', 'sheet', 'layer', 'companion',
              'supplied', 'assemble', 'independent', 'working', 'reference', 'slot'}
CONTEXT_CUT = {'behind', 'for', 'to', 'fit', 'fits', 'into', 'under', 'beneath', 'use', 'reuse', 'place', 'sit'}
FAR_WORDS = {'far', 'distant', 'skyline', 'horizon', 'treeline', 'ridge', 'silhouette'}
PROPS_LEAN_OK = {'railing', 'rail', 'fence', 'balustrade', 'wall', 'column', 'counter', 'bar', 'sill', 'doorpost',
                 'parapet', 'pillar'}
FOLIAGE = {'leaf', 'blossom', 'flower', 'close', 'canopy', 'vine'}


def split_label(text):
    """primary = label outside (...) cut at the first context word ('behind the opening', 'fits wall aperture');
    secondary = the rest (modifiers, notes)."""
    t = text or ''
    paren = ' '.join(re.findall(r'\(([^)]*)\)?', t))
    outside = re.sub(r'\([^)]*\)?', ' ', t)
    ws = tokens(outside)
    cut = [i for i, w in enumerate(ws) if w in CONTEXT_CUT and i > 0]
    prim = ws[:cut[0]] if cut else ws
    rest = (ws[cut[0]:] if cut else []) + tokens(paren)
    return prim, rest


def match(label, name, slug, sheet, place=None):
    """-> ({kind: {strength, words, blocked_by?, ...}}, info). Words outside parentheses (before any context word)
    decide; parenthetical words only count when the primary words name no kind at all."""
    info = {'src': 'label'}
    text = label or ''
    if len(re.findall(r'[A-Za-z]{3,}', text)) == 0:
        text = name or ''
    if len(re.findall(r'[A-Za-z]{3,}', text)) == 0:
        text = slug.replace('-', ' '); info['src'] = 'slug'
    prim, rest = split_label(text)
    allw = prim + rest
    S = set(allw)
    info['primary_words'] = prim
    nn = len(S & NOTE_WORDS) + (2 if ':' in text and len(allw) > 6 else 0)
    if 'reference' in S and ('only' in S or 'assembled' in S):
        nn = 2
    if nn >= 2:
        info['note_label'] = True
        return {}, info
    props = '.props.' in sheet
    setlike = ('.set.' in sheet or '.hero.' in sheet)
    lexes = {'seat': SEAT, 'surface': SURFACE, 'grip': GRIP, 'aperture': APERT,
             'lean': {**LEAN_V, **LEAN_H}, 'occluder': OCC, 'stand_on': STAND}
    blocks = {'seat': set(), 'surface': SURF_BLOCK, 'grip': GRIP_BLOCK, 'aperture': APERT_BLOCK, 'lean': LEAN_BLOCK,
              'occluder': OCC_BLOCK, 'stand_on': STAND_BLOCK}
    out = {}
    prim_any = any(w in lx and lx[w] > 0 for w in prim for lx in lexes.values())
    for kind, lx in lexes.items():
        hits = [(i, w) for i, w in enumerate(prim) if w in lx and lx[w] > 0]
        from_paren = False
        if not hits and not prim_any:
            hits = [(i + 100, w) for i, w in enumerate(rest) if w in lx and lx[w] > 0]
            from_paren = bool(hits)
        if not hits:
            continue
        i0 = hits[0][0]
        st = max(lx[w] for _, w in hits) * (1.0 if i0 <= 3 else 0.8) * (0.6 if from_paren else 1.0)
        rec = {'strength': round(st, 2), 'words': sorted({w for _, w in hits}), 'from': 'parenthetical' if from_paren else 'primary'}
        blk = set(S & blocks[kind])
        if kind == 'seat':
            for i, w in enumerate(allw):
                if w == 'back' and i > 0 and allw[i - 1] in ('pew', 'couch', 'sofa', 'chair', 'bench', 'seat') and \
                        not (i + 1 < len(allw) and allw[i + 1] == 'view'):
                    blk.add('back')
                if w == 'arm' and 'sit' not in S:
                    blk.add('arm')
            blk |= S & {'pillow', 'blanket', 'leg', 'ash', 'raven', 'light'}
            if setlike is False and not props:
                blk.add('fx-sheet')
        if kind == 'surface' and 'side' in S and 'panel' in S:
            blk.add('side panel')
        if kind == 'surface' and 'top' in S and S & {'booth', 'riser', 'counter'}:
            rec['strength'] = max(rec['strength'], 0.9)
        if kind == 'grip':
            if not props:
                blk.add('not-a-props-sheet')
        if kind == 'aperture':
            if rec['words'] == ['frame']:
                if not setlike or S & ({'picture', 'photo', 'meter', 'film', 'mirror', 'portrait'} | SEAT.keys() | {'bed'}):
                    blk.add('bare-frame-off-architecture')
                rec['strength'] = min(rec['strength'], 0.5)
                rec['needs_hole'] = True
            if 'leaf' in S and not S & {'door', 'gate'}:
                blk.add('foliage-leaf')
            if S & FOLIAGE - {'leaf'}:
                blk |= S & (FOLIAGE - {'leaf'})
            if blk and S & APERT_STRONG and not S & {'glass', 'pane', 'glazing', 'backer', 'backing', 'glow'}:
                rec['note'] = 'strong opening word overrides %s' % sorted(blk); blk = set()
            if S & LEAF or (S & {'door', 'gate'} and S & {'l', 'r', 'left', 'right'} and
                            not S & {'frame', 'wall', 'way', 'opening', 'aperture', 'interior', 'facade'}):
                rec['role_hint'] = 'leaf'
            if S & {'floor', 'slab', 'paving', 'forecourt', 'ground'}:
                rec['role_hint'] = 'floor_opening'
        if kind == 'lean':
            rec['orient'] = 'h' if any(w in LEAN_H for w in rec['words']) and not any(w in LEAN_V for w in rec['words']) else 'v'
            if props and not set(rec['words']) & PROPS_LEAN_OK:
                blk.add('small-prop-post')
            blk |= S & FAR_WORDS
            if set(rec['words']) <= {'tree', 'trunk'} and place in ('band', 'sky'):
                blk.add('tree in a distant band')
        if kind == 'occluder':
            if rec['words'] == ['arm'] and not S & {'couch', 'sofa', 'chair', 'armchair', 'overlay', 'front'}:
                blk.add('arm-not-furniture')
            if not setlike and not props:
                blk.add('fx-sheet')
        if kind == 'stand_on':
            ground = all(w in GROUND_WORDS for w in rec['words'])
            rec['ground'] = ground
            if ground and not setlike:
                blk.add('ground-word-off-set-sheet')
            if S & {'bed', 'sofa', 'couch'}:
                blk.add('furniture-platform')
            blk |= S & FAR_WORDS
        if 'skyline' in sheet or place == 'sky':
            blk.add('skyline/sky: too far for contact')
        if '.fx.' in sheet:
            blk.add('fx sheet')
        if S & {'far', 'distant'} and kind in ('aperture',):
            rec['strength'] = round(rec['strength'] * 0.6, 2); rec['note'] = 'far/distant: small in frame'
        if blk:
            rec['blocked_by'] = sorted(blk)
        out[kind] = rec
    return out, info
