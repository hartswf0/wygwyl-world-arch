#!/usr/bin/env python3
"""Body Lab builder: classify every body piece across all cut-out generations,
solve a common scale (px per cm) per sheet, and flag problems.

    python3 shots/bodylab/build.py            -> shots/bodylab/body.json (+ img/ thumbs for older generations)
    python3 shots/bodylab/build.py --review   -> also writes review contact sheets to shots/bodylab/review/

Generations
    cut       shots/kits/cut/catalog.json           (365 sheets, the current kits)
    tracksuit shots/kits/packs/poet_tracksuit_v1    (31 single-file components)
    arena     shots/arena/parts/library.json        (code-drawn + registered image parts)
    weave     shots/weave/cast/man                  (the older photo-man puppet: parts + library)

Classification = rules over sheet id + OCR label, then size/row propagation for empty or garbled
labels, then OVERRIDES below (each one checked by eye on the review contact sheets).

Scale: every sheet is its own drawing scale.  For each sheet we measure the parts whose true size
we know from anthropometry (limb segments brad-to-brad, hand length, shoe length, head height,
eye/brow/mouth widths) for that character's stature, and take the median px/cm.  `true scale`
then shows every part at cm.  The per-sheet factor relative to the character's reference body
sheet is what a rig must apply; big factors and in-sheet proportion outliers become problems.
"""
import json, re, sys, math, os, hashlib, collections
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]          # shots/
OUT = ROOT / 'bodylab'
CUT = ROOT / 'kits' / 'cut'
REVIEW = '--review' in sys.argv

try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
except ImportError:                                  # still builds body.json without hashes / thumbs
    Image = None

# ───────────────────────── characters ─────────────────────────
# stature in cm; head = crown-to-chin cm (heads stay large in children)
STATURE = {
    'man': (180, 23.5), 'woman': (165, 22.0), 'elder_man': (175, 23.0), 'elder_woman': (160, 21.5),
    'adult': (172, 22.5), 'child6': (115, 20.0), 'child7': (122, 20.5), 'child9': (133, 21.0),
}
CHAR = {   # character -> (body type, display name)
    'poet': ('man', 'Poet'), 'poet_soul': ('man', 'Poet soul'), 'young_poet': ('child7', 'Young poet'),
    'ghost_child': ('child6', 'Ghost child'), 'young_ghost': ('child6', 'Young ghost'),
    'ex': ('man', 'Ex'), 'mother': ('woman', 'Mother'), 'woman': ('woman', 'Woman (13)'),
    'father_02': ('man', 'Father (02)'), 'father_elder': ('elder_man', 'Father elder'), 'parents': ('adult', 'Parents'),
    'brother_1': ('man', 'Brother 1'), 'friend_1': ('man', 'Friend 1'), 'friend_2': ('man', 'Friend 2'),
    'couple_1_a': ('man', 'Couple 1 A'), 'couple_1_b': ('woman', 'Couple 1 B'), 'couple_2_a': ('man', 'Couple 2 A'),
    'couple_2_b': ('woman', 'Couple 2 B'), 'couple_3_a': ('man', 'Couple 3 A'), 'couple_3_b': ('woman', 'Couple 3 B'),
    'elder_man': ('elder_man', 'Elder man'), 'elder_woman': ('elder_woman', 'Elder woman'),
    'family': ('man', 'Family (street clothes)'), 'family_misc': ('adult', 'Family (misc)'), 'fellow_mason': ('man', 'Fellow mason'),
    'dj_cyber': ('man', 'DJ cyber'), 'party_guest': ('man', 'Party guest'), 'dj_guest': ('man', 'DJ + guest shared'),
    'vintage_man': ('man', 'Vintage suit man'), 'vintage_woman': ('woman', 'Vintage gown woman'),
    'vintage_party': ('adult', 'Vintage party (shared)'),
    'angel': ('man', 'Angel'), 'club_dress': ('woman', 'Club dress'), 'club_jacket': ('man', 'Club jacket'),
    'club_shirt': ('man', 'Club shirt'), 'club': ('adult', 'Club (shared)'), 'elders': ('elder_man', 'Elders (12)'),
    'ancestor_elder': ('elder_man', 'Ancestor elder (white)'), 'ancestor_robe': ('man', 'Ancestor robe (indigo)'),
    'ancestors': ('adult', 'Ancestors (identities)'),
    'child_traveler': ('child9', 'Child traveler'), 'citizen_1': ('adult', 'Citizen 1'), 'elder_1': ('elder_man', 'Elder 1'),
    'gatekeeper': ('man', 'Gatekeeper'), 'traveler_1': ('man', 'Traveler 1'), 'atlantis_crowd': ('adult', 'Atlantis crowd'),
}

def char_of(sid, label=''):
    """sheet id (+label) -> (character, costume)"""
    t = sid.split('.')
    L = label.upper()
    if sid.startswith('poet_soul'): return 'poet_soul', 'soul'
    if t[0] == 'poet':
        if 'black_tshirt' in sid or (len(t) > 1 and t[1] in ('01', '02', '03')): return 'poet', 'black_tshirt'
        return 'poet', 'red_black_sunglasses'
    if sid.startswith('02.props.poet-eye-aperture'): return 'poet', 'macro_eye'
    if sid.startswith('04.props.poet-jointed-hands'): return 'poet', 'red_black_sunglasses'
    if t[0] == 'young_poet':
        return 'young_poet', ('pajamas_winter' if ('pajamas' in sid or t[1] == '02') else 'child_clothes')
    if t[0] == 'young_ghost': return 'young_ghost', 'ghost'
    if t[0] == 'ghost_child': return 'ghost_child', 'ghost_nightclothes'
    if t[0] == 'ex': return 'ex', 'ex_jacket'
    if t[0] == 'woman': return ('mother', 'poem09') if 'mother' in sid else ('woman', 'poem13')
    if t[0] == 'parents':
        if 'father_02' in sid: return 'father_02', 'poem02'
        if 'father_elder' in sid: return 'father_elder', 'poem09'
        return 'parents', t[2]
    if t[0] == 'family':
        if 'street_clothes' in sid or t[1] == '14': return 'family', 'street_clothes'
        for k in ('brother_1', 'friend_1', 'friend_2', 'couple_1_a', 'couple_1_b', 'couple_2_a', 'couple_2_b',
                  'couple_3_a', 'couple_3_b', 'elder_man', 'elder_woman'):
            if f'.{k}.' in sid: return k, 'poem' + t[1]
        if 'optional' in sid: return 'fellow_mason', 'poem11'
        return 'family_misc', 'poem' + t[1]
    if t[0] == 'party':
        if 'dj_cyber' in sid: return 'dj_cyber', 'cyber'
        if 'party_guest' in sid: return 'party_guest', 'guest'
        if 'dj-guest' in sid:
            if 'DJ' in L: return 'dj_cyber', 'cyber'
            if 'GUEST' in L: return 'party_guest', 'guest'
            return 'dj_guest', 'shared'
        if 'suit_man' in sid or sid.endswith('.male'): return 'vintage_man', 'suit'
        if 'gown_woman' in sid or sid.endswith('.female'): return 'vintage_woman', 'gown'
        return 'vintage_party', 'vintage'
    if t[0] == '08':
        if t[2] in ('angel',): return 'angel', 'robe'
        if t[2] in ('club_dress', 'club_jacket', 'club_shirt'): return t[2], 'club'
        return 'club', 'shared'
    if t[0] == '12': return 'elders', 'memory'
    if t[0] == 'ancestors':
        if 'elder_white' in sid: return 'ancestor_elder', 'white_silver'
        if 'robe_indigo' in sid: return 'ancestor_robe', 'indigo_gold'
        return 'ancestors', 'identities'
    if t[0] == 'atlantis':
        for k in ('child_traveler', 'citizen_1', 'elder_1', 'gatekeeper', 'traveler_1'):
            if k.replace('_1', '') in sid and (k in sid or k == 'gatekeeper'): return k, 'atlantis'
        if 'atlantis_citizen' in sid: return 'citizen_1', 'atlantis'
        return 'atlantis_crowd', 'atlantis'
    return None, None

def is_body_sheet(sid, s):
    if re.match(r'\d\d\.(fx|hero|props|set)\.', sid) and s['category'] != 'character_special': return False
    if sid.startswith('05.props.fingerprint'): return False
    return True

# ───────────────────────── label rules ─────────────────────────
def norm_label(l):
    u = (l or '').upper().replace('_', ' ').replace('.', ' ').replace('-', ' ').replace('’', "'")
    u = re.sub(r'\b(UARM|FOREARM|SHIN|THIGH|FOOT|HAND|EYE|BROW|UPPERARM|ARM|SHOE|BOOT|FARM)(L|R)\b', r'\1 \2', u)
    u = re.sub(r'\bUPPERARM\b', 'UPPER ARM', u)
    return ' ' + re.sub(r'\s+', ' ', u).strip() + ' '

RULES = [  # (class, regex on normalized label) in priority order
    ('other', r' (REFERENCE|ASSEMBLED|ASSEMBLY|PROOF|POSES?|MAIN POSE|INSTANCES?|CHOREOGRAPHY|PROP|PROPS|VAPE|MICROPHONE|MIC|HEADPHONES?|BAG|STRAP|POCKET|PATCH|WINGS?|FOLDED|DOWNSTROKE|FULLY OPEN|HALF OPEN|LIGHT POINT|NECK CHAIN|TAMBOURINE|STAFF|DISC|HOURGLASS|FOOTBALL|COIN|JOURNAL|LETTER|PHONE|CORD|CURTAIN|SHOULDER PLATE|CUFF|LIPSTICK|ROSARY|PEARLS) '),
    ('hand', r' (HANDS?|PALM|FIST|GRIP|PINCH|POINT|PEACE|WAVE|CLAW|CUPP?ED?|THUMBS?|RELAX(ED)?|FINGERS?|FINGER FAN|PUSH|SHIELDING|GUIDING|REACH|EMBRACE|WRIST TOUCH|SHOULDER REST|SHOULDER TOUCH) '),
    ('glasses', r' (SUNGLASSES|GLASSES|SHADES) '),
    ('eyes', r' (EYES?|EYEL|EYER|EYELIDS?|SCLERA|IRIS|PUPIL|LIDDED|GLANCE|LOOK (LEFT|RIGHT|UP|DOWN)|HAPPY ARC|SQUINT) '),
    ('brows', r' (BROWS?|BROWL|BROWR|EYEBROWS?) '),
    ('mouth', r' (MOUTHS?|LIPS|M B P|F V|OPEN [AO]|SMILE|GRIN|GRIN TEETH|FROWN|WAVY|STRAIN TEETH|LAUGH) '),
    ('nose', r' NOSES? '),
    ('ear', r' EARS? '),
    ('hair', r' (HAIR|CAP|HAT|BRAID|BUN) '),
    ('head', r' (HEADS?|HEAD PLATE|BLANK HEAD|HEAD BLANK|MASKS?|REAR HEAD) '),
    ('neck', r' NECK '),
    ('seat', r' (SEAT|BUTT|SEAT COVER|REAR SEAT) '),
    ('hip', r' (HIP|HIPS|PELVIS|WAIST LINK|HIP BRIDGE|BRIDGE|CONNECTOR|H L H R|GARMENT|OVERLAY|SKIRT|SHORTS|ROBE PANEL|NIGHTGOWN PANEL|LOWER ROBE|COVER) '),
    ('torso', r' (TORSO|BODICE|CHEST|BODY|SLEEVES?) '),
    ('forearm', r' (FOREARM|FARM|FOR|LOWER ARM) '),
    ('upper_arm', r' (UPPER ARM|UARM|ARM|UPPER) '),
    ('thigh', r' (THIGH|THIG|HIGH) '),
    ('shin', r' (SHIN|SHI|CALF|LOWER LEG) '),
    ('shoe', r' (SHOES?|BOOTS?|SNEAKERS?|SANDALS?|FOOTWEAR|HEEL|HEELS) '),
    ('foot', r' (FOOT|FEET|TOE UP|HEEL UP|LIFTED) '),
]
STATES = {
    'hand': ['relaxed', 'open', 'fist', 'grip', 'pinch', 'point', 'thumb', 'peace', 'wave', 'claw', 'cup', 'flat push', 'push',
             'guiding', 'shielding', 'reach', 'embrace', 'support', 'wrist touch', 'shoulder rest', 'shoulder touch', 'elegant',
             'hold', 'partner', 'celebration', 'hang', 'flat', 'speak'],
    'eyes': ['open', 'closed', 'half', 'wide', 'squint', 'sad', 'glance', 'happy arc', 'look left', 'look right', 'look up',
             'look down', 'calm', 'laughing', 'lidded', 'down', 'smiling', 'meeting gaze', 'joy', 'side'],
    'brows': ['rest', 'neutral', 'raised', 'knit', 'sad', 'one up', 'raised one', 'angry', 'anger', 'lowered', 'worried', 'frown',
              'soft raise', 'laughing', 'joy', 'calm'],
    'mouth': ['rest', 'smile', 'grin', 'open o', 'open a', 'm b p', 'f v', 'frown', 'wavy', 'strain', 'laugh', 'closed', 'speak',
              'angry', 'sad', 'calm', 'joy', 'open', 'neutral'],
    'foot': ['flat', 'heel up', 'toe up', 'lifted', 'front', 'back', 'profile', 'threequarter'],
    'head': ['blank', 'calm', 'smile', 'sad', 'strain'],
}
STATES['shoe'] = STATES['foot']
SIDE_RE = [(r' (L|LEFT|EYEL|BROWL|NEAR) ', 'L'), (r' (R|RIGHT|EYER|BROWR|FAR) ', 'R')]
VIEW_RE = [('threequarter_back', r' (THREE ?QUARTER ?BACK|THREE ?QUARTER REAR|3/4 BACK|3Q BACK|REAR THREE ?QUARTER|THREEQUARTER BACK|REAR 3/4) '),
           ('threequarter', r' (THREE ?QUARTER|3/4|3Q|THREEQUARTER) '),
           ('profile', r' (PROFILE|SIDE VIEW|NEAR) '),
           ('back', r' (BACK VIEW|REAR|BACK) '),
           ('front', r' FRONT ')]

def match_class(nl):
    for cls, rx in RULES:
        if re.search(rx, nl): return cls
    return None

def sheet_default(sid):
    """class implied by the sheet type, used when a label says nothing"""
    if re.search(r'main-poses|mainposes|paired-choreography|waltz|procession|plaza-twelve|source-actions|car-argument|'
                 r'couple-orbits|elder-prayer|phone-prayer|hug-restage|muse-dance|memory-drop|watcher-head', sid): return 'other'
    if re.search(r'(\.|-)hands(\b|-|$)|action-hands|jointed-hands', sid) and 'heads-hands' not in sid and 'faces-hands' not in sid: return 'hand'
    if sid.endswith('.feet'): return 'shoe'
    if sid.endswith('.heads') or 'head-variants' in sid: return 'head'
    return None

def view_of(sid, nl, cls):
    m = re.search(r'\.(threequarter_back|threequarter|profile|front|back)\b', sid)
    for v, rx in VIEW_RE:
        if cls == 'hand' and v == 'back': continue          # back of the hand is not a back view
        if re.search(rx, nl): return v
    if m and cls != 'hand': return m.group(1)
    if m and cls == 'hand': return 'profile' if m.group(1) == 'profile' else 'front'
    if sid.endswith('face.profile'): return 'profile'
    return ''

def state_of(cls, nl):
    voc = STATES.get(cls)
    if not voc: return ''
    for w in sorted(voc, key=len, reverse=True):
        if f' {w.upper()} ' in nl: return w.replace(' ', '_')
    return ''

def side_of(nl, sid):
    for rx, s in SIDE_RE:
        if re.search(rx, nl): return s
    return ''

# ───── manual overrides (checked by eye on review/*.png) : part id -> dict of fields ─────
# overrides.json = {"regions": {sheet: [[x0, y0, x1, y1, {fields}], ...]},   (part centre inside box, sheet px; later wins)
#                   "parts": {part id: {fields}}}
OVERRIDES, REGIONS = {}, {}
OV_PATH = OUT / 'overrides.json'
if OV_PATH.exists():
    _ov = json.loads(OV_PATH.read_text())
    OVERRIDES, REGIONS = _ov.get('parts', {}), _ov.get('regions', {})

def apply_regions(r):
    for x0, y0, x1, y1, f in REGIONS.get(r['sheet'], []):
        x, y, w, h = r['bbox']
        cx, cy = x + w / 2, y + h / 2
        if min(w, h) < 22: continue                                    # caption strips stay 'other'
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            if f.get('state') == 'uncut_block':         # only a card that really spans a block (sheets get re-cut)
                SW, SH = cat[r['sheet']]['size']
                if w < 0.4 * SW and h < 0.4 * SH and w * h < 0.12 * SW * SH: continue
            if f.get('_minw') and w < f['_minw']: continue
            if f.get('_maxw') and w > f['_maxw']: continue
            if f.get('_maxh') and h > f['_maxh']: continue
            if f.get('_minh') and h < f['_minh']: continue
            r.update({k: v for k, v in f.items() if not k.startswith('_')}); r['override'] = True

# ───────────────────────── anthropometric scale ─────────────────────────
# expected cm of the measured dimension, as a function of body type
def expected_cm(cls, btype, rec):
    H, head = STATURE[btype]
    w, h = rec['w'], rec['h']
    if cls == 'upper_arm': return 0.186 * H
    if cls == 'forearm': return 0.146 * H
    if cls == 'thigh': return 0.245 * H
    if cls == 'shin': return 0.246 * H
    if cls == 'hand': return 0.108 * H * 1.08            # hand + wrist tab
    if cls in ('shoe', 'foot'): return 0.152 * H * (1.1 if cls == 'shoe' else 1.0)
    if cls == 'head': return head * 1.12                 # crown to chin + neck tab
    if cls == 'eyes': return head * (0.46 if rec['pair'] else 0.17)
    if cls == 'brows': return head * (0.50 if rec['pair'] else 0.22)
    if cls == 'mouth': return head * 0.25
    return None

def measure_px(cls, rec):
    """the px length matching expected_cm, or None if this part can't be measured"""
    w, h, br = rec['w'], rec['h'], rec['brads']
    if cls in ('upper_arm', 'forearm', 'thigh', 'shin'):
        if rec.get('replacement'): return None           # posed replacement limbs are foreshortened
        if 2 <= len(br) <= 3:
            d = max(math.dist(a, b) for i, a in enumerate(br) for b in br[i + 1:])
            if d > 0.45 * max(w, h): return d
        L, S = max(w, h), min(w, h)
        return L - S * 0.9 if L > 1.6 * S else None
    if cls == 'hand':
        if rec['state'] in ('fist', 'cup', 'claw', 'grip', 'pinch'): return None
        return max(w, h)
    if cls in ('shoe', 'foot'):
        return w if (rec['view'] == 'profile' or w > 1.25 * h) else None
    if cls == 'head':
        return h if rec['view'] in ('front', 'threequarter', 'back', 'profile', 'threequarter_back', '') and h > w * 0.95 else None
    if cls in ('eyes', 'brows', 'mouth'):
        if rec['view'] == 'profile': return None
        return w
    return None

# ───────────────────────── image helpers ─────────────────────────
def dhash(path, crop=None):
    try:
        im = Image.open(path).convert('RGBA')
        if crop: im = im.crop(crop)
        bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
        g = np.asarray(bg.convert('L').resize((9, 8), Image.BILINEAR), dtype=np.int16)
        bits = (g[:, 1:] > g[:, :-1]).flatten()
        return int(''.join('1' if b else '0' for b in bits), 2)
    except Exception:
        return None

def thumb(src, dst, maxd=640):
    """trim to alpha, downsize, save webp (older generations ship full-canvas PNGs)"""
    im = Image.open(src).convert('RGBA')
    a = np.asarray(im)[..., 3]
    ys, xs = np.nonzero(a > 16)
    if len(xs):
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    else:
        box = (0, 0) + im.size
    im = im.crop(box)
    s = min(1.0, maxd / max(im.size))
    if s < 1: im = im.resize((max(1, round(im.size[0] * s)), max(1, round(im.size[1] * s))), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, 'WEBP', quality=86)
    return box, s, im.size

# ───────────────────────── collect: cut generation ─────────────────────────
cat = json.loads((CUT / 'catalog.json').read_text())['sheets']
parts, sheets = [], {}

def add(rec): parts.append(rec)

def classify(sid, p, sheet):
    nl = norm_label(p['label'])
    d = sheet_default(sid)
    cls = None
    if p.get('kind') == 'pose' or d == 'other': cls = 'other'
    if min(p['bbox'][2], p['bbox'][3]) < 22: cls = 'other'            # caption strips cut as cards
    if not cls: cls = match_class(nl)
    # sheet context beats generic words: a hands sheet's "open palm" is a hand, a feet sheet's "front" a shoe
    if d in ('hand', 'shoe', 'head') and cls in (None, 'other', 'eyes', 'mouth', 'foot', 'torso', 'hip', 'upper_arm'):
        if not (cls == 'other' and re.search(r'REFERENCE|ASSEMBLED|PROP', nl)): cls = d
    if d == 'shoe' and cls == 'foot': cls = 'shoe'
    return cls, nl

for sid, s in cat.items():
    if not is_body_sheet(sid, s): continue
    ch0, co0 = char_of(sid)
    if not ch0: continue
    sheets[sid] = {'id': sid, 'gen': 'cut', 'title': s.get('title', ''), 'category': s['category'], 'size': s['size'],
                   'path': 'kits/' + s['path'], 'poems': s['poems'], 'n': 0}
    for p in s['parts']:
        if not (CUT / p['file']).exists(): continue          # catalog row whose image is not (yet) written
        cls, nl = classify(sid, p, s)
        ch, co = char_of(sid, p['label'])
        x, y, w, h = p['bbox']
        rec = {'id': p['id'], 'gen': 'cut', 'sheet': sid, 'img': 'kits/cut/' + p['file'], 'label': p['label'],
               'nl': nl, 'class': cls, 'character': ch, 'costume': co, 'poems': s['poems'], 'bbox': p['bbox'],
               'w': w, 'h': h, 'brads': p['brads'][:40], 'nbrads': len(p['brads']), 'pivot': p['pivot'],
               'kind': p['kind'], 'replacement': '.replacements.' in sid or '.action' in sid or 'torso-variants' in sid}
        add(rec)

# vintage party sheets hold two actors: male rows on top, female rows below (checked on review sheets)
def vintage_split(r):
    if r['character'] != 'vintage_party': return
    sid, nl = r['sheet'], r['nl']
    if ' FEMALE ' in nl or ' GOWN ' in nl or ' IVORY ' in nl: r['character'], r['costume'] = 'vintage_woman', 'gown'; return
    if ' MALE ' in nl: r['character'], r['costume'] = 'vintage_man', 'suit'; return
    H = cat[sid]['size'][1]
    cy = r['bbox'][1] + r['bbox'][3] / 2
    if re.search(r'body\.(front|back)$|\.hands$|\.heads$|body\.profile$', sid):
        r['character'], r['costume'] = (('vintage_man', 'suit') if cy < H * 0.47 else ('vintage_woman', 'gown'))

# ───────────────────────── propagation for unlabeled parts ─────────────────────────
def propagate():
    by = collections.defaultdict(list)
    for r in parts:
        if r['gen'] == 'cut': by[r['sheet']].append(r)
    for sid, rs in by.items():
        known = [r for r in rs if r['class'] and r['class'] != 'other']
        for r in rs:
            if r['class']: continue
            best, bd = None, 9
            for k in known:
                dw = abs(math.log(r['w'] / k['w'])); dh = abs(math.log(r['h'] / k['h']))
                dy = abs((r['bbox'][1] + r['h'] / 2) - (k['bbox'][1] + k['h'] / 2)) / max(r['h'], k['h'])
                dist = dw + dh + 0.35 * min(dy, 3)
                if dist < bd: best, bd = k, dist
            if best and bd < 0.75:
                r['class'] = best['class']; r['prop_from'] = best['id']
            else:
                r['class'] = 'other'; r['unresolved'] = True

def finish(r):
    nl, cls = r['nl'], r['class']
    ov = OVERRIDES.get(r['id'])
    if ov:
        r.update({k: v for k, v in ov.items() if k != 'note'}); cls = r['class']; r['override'] = True
    r.setdefault('view', view_of(r['sheet'], nl, cls) if r['gen'] == 'cut' else '')
    if not r.get('view') and cls in ('eyes', 'brows', 'mouth', 'nose') and r['gen'] == 'cut':
        r['view'] = 'front'
    r.setdefault('side', side_of(nl, r['sheet']))
    if r['gen'] == 'cut' and cls == 'hand' and not r['side'] and re.search(r'RIGHT[ -]HAND|RIGHT SET|MIRROR FOR LEFT', (' '.join(
            p['label'] for p in cat[r['sheet']]['parts']) + str(cat[r['sheet']].get('notes', '')) + cat[r['sheet']].get('title', '')).upper()):
        r['side'] = 'R'; r['side_note'] = 'sheet says right-hand set'
    st = r.get('state') or state_of(cls, nl)
    r['state'] = st
    if cls in ('shoe', 'foot') and not r['view'] and st in ('flat', 'heel_up', 'toe_up', 'lifted'): r['view'] = 'profile'
    if cls == 'hand':
        r['shows'] = r.get('shows') or ('palm' if ' PALM ' in nl else 'back' if ' BACK ' in nl else '')
    if cls in ('eyes', 'brows'):
        r['pair'] = r.get('pair', not bool(r['side']) and r['w'] > r['h'] * 1.7)
    else:
        r['pair'] = False

def bar(*a): pass

# ───────────────────────── collect: older generations ─────────────────────────
def older():
    if Image is None: return
    # tracksuit pack: one component per file, each blown up to fill its own canvas
    pk = ROOT / 'kits/packs/poet_tracksuit_v1'
    rows = [l.split(',') for l in (pk / 'Component_Index.csv').read_text().splitlines()[1:] if l.strip()]
    TS = {'torso': 'torso', 'waist': 'hip', 'hip': 'hip', 'rear': 'seat', 'pelvis': 'hip', 'upper': 'upper_arm',
          'forearm': 'forearm', 'thigh': 'thigh', 'shin': 'shin', 'hand': 'hand', 'boot': 'shoe', 'head': 'head',
          'eyes': 'eyes', 'brows': 'brows', 'nose': 'nose', 'mouth': 'mouth', 'sunglasses': 'glasses'}
    sheets['tracksuit_v1'] = {'id': 'tracksuit_v1', 'gen': 'tracksuit', 'title': 'Poet tracksuit v1 (pack components)',
                              'category': 'pack', 'size': None, 'path': 'kits/packs/poet_tracksuit_v1/index.html', 'poems': [], 'n': 0,
                              'per_part_scale': True}
    for row in rows:
        pid, name, group, f = row[0], row[1], row[2], row[3]
        key = pid.split('_', 1)[1]
        cls = next((v for k, v in TS.items() if key.startswith(k)), 'other')
        dst = OUT / 'img/tracksuit' / (pid + '.webp')
        box, sc, sz = thumb(pk / f, dst)
        side = 'L' if key.endswith('_L') else 'R' if key.endswith('_R') else ''
        view = 'back' if 'back' in key else 'front'
        st = key.split('_')[1] if cls in ('hand', 'eyes', 'brows', 'mouth') else ''
        if cls == 'mouth': st = '_'.join(key.split('_')[1:])
        add({'id': 'tracksuit/' + pid, 'gen': 'tracksuit', 'sheet': 'tracksuit_v1', 'scale_group': 'tracksuit/' + pid,
             'img': f'bodylab/img/tracksuit/{pid}.webp', 'label': name, 'nl': norm_label(name), 'class': cls,
             'character': 'poet', 'costume': 'tracksuit_v1', 'poems': [], 'bbox': None, 'w': sz[0], 'h': sz[1],
             'src_w': box[2] - box[0], 'src_h': box[3] - box[1], 'brads': [], 'nbrads': int(row[4] or 0), 'pivot': None,
             'kind': 'component', 'side': side, 'view': view, 'state': st, 'src': f'kits/packs/poet_tracksuit_v1/{f}'})
    # arena library: code parts are drawn at a known 12 px/cm; image parts are registered cards
    lib = json.loads((ROOT / 'arena/parts/library.json').read_text())['parts']
    AK = {'hand': 'hand', 'head': 'head', 'boot': 'shoe', 'pelvis': 'hip', 'torso': 'torso', 'uarm': 'upper_arm',
          'farm': 'forearm', 'thigh': 'thigh', 'shin': 'shin'}
    sheets['arena_code'] = {'id': 'arena_code', 'gen': 'arena', 'title': 'Arena code-drawn kit (12 px/cm)', 'category': 'code',
                            'size': None, 'path': 'arena/parts/PARTS.md', 'poems': [], 'n': 0, 'ppc_known': 12}
    sheets['arena_image'] = {'id': 'arena_image', 'gen': 'arena', 'title': 'Arena registered image parts (man)', 'category': 'image',
                             'size': None, 'path': 'arena/parts/PARTS.md', 'poems': [], 'n': 0}
    for p in lib:
        src = ROOT / p['file']
        if not src.exists(): continue
        dst = OUT / 'img/arena' / (p['id'] + '.webp')
        box, sc, sz = thumb(src, dst)
        st = p.get('state') or {}
        state = st.get('shape') or st.get('expression') or (f"roll{st['roll']}" if 'roll' in st else '') or ''
        if not state and '.ie.' in p['id']: state = p['id'].split('.')[-1]
        if not state and p['id'].startswith('man.head.front.'): state = p['id'].split('.')[-1]
        view = p.get('view') or ''
        view = {'threequarter_R': 'threequarter', 'threequarter_L': 'threequarter', 'profile_R': 'profile', 'profile_L': 'profile',
                'flat': 'front'}.get(view, view)
        code = p.get('source') == 'code'
        add({'id': 'arena/' + p['id'], 'gen': 'arena', 'sheet': 'arena_code' if code else 'arena_image',
             'scale_group': 'arena_code' if code else 'arena_image', 'img': f"bodylab/img/arena/{p['id']}.webp",
             'label': p['id'], 'nl': norm_label(p['id']), 'class': AK.get(p['kind'], 'other'), 'character': 'poet',
             'costume': 'arena_man', 'poems': [], 'bbox': None, 'w': sz[0], 'h': sz[1], 'src_w': box[2] - box[0], 'src_h': box[3] - box[1],
             'thumb_scale': sc, 'brads': [], 'nbrads': len(p.get('sockets', {})), 'pivot': None, 'kind': p.get('source'),
             'side': p.get('side', '') or ('L' if view.endswith('_L') else ''), 'view': view, 'state': state,
             'shows': p.get('shows', ''), 'src': p['file']})
    # weave photo-man: parts (rig) + library pieces, grouped by their source sheet
    W = ROOT / 'weave/cast/man'
    cast = json.loads((W / 'cast.json').read_text())['parts']
    lm = json.loads((W / 'library_manifest.json').read_text())['pieces']
    WK = [('hand', r'^hand|^grip|^contact\.clasped'), ('head', r'^head'), ('shoe', r'^boot'), ('hip', r'^pelvis'),
          ('torso', r'^torso|^body_'), ('upper_arm', r'^uarm|arm\.foreshortened|arm\.flared'), ('forearm', r'^farm'),
          ('thigh', r'^thigh|^leg\.thigh'), ('shin', r'^shin|^leg\.shin'), ('other', r'.')]
    items = [(k, v.get('sheet', 'cast'), v['file'], 'rig') for k, v in cast.items()] + \
            [(k, v['source_sheet'], v['file'], v['category']) for k, v in lm.items() if v['category'] in ('hand', 'head', 'leg', 'contact', 'misc')]
    for k, sh, f, catg in items:
        src = ROOT / 'weave' / f
        if not src.exists(): continue
        if catg == 'misc' and not k.startswith('body_'): continue
        if k.startswith('draft_') or re.match(r'^(arms_hands_contact|hands_2|legs_\w+)_\d+$', k): continue
        cls = next(c for c, rx in WK if re.search(rx, k))
        mb = re.match(r'body_(back|front|profile|threequarter|sitting)_(\d+)$', k)
        if mb:   # numbered pieces cut from the photo-man body sheets (checked by eye)
            n = int(mb.group(2))
            cls = {1: 'head', 2: 'torso', 3: 'upper_arm', 4: 'forearm', 5: 'upper_arm', 6: 'forearm', 7: 'forearm', 8: 'hip',
                   9: 'shin', 10: 'shin', 11: 'forearm', 12: 'hand', 13: 'hand'}[n]
            if mb.group(1) == 'sitting': cls = 'shin' if n == 4 else 'other'
        if catg == 'leg' and cls == 'other': cls = 'other'
        gid = 'weave/' + sh
        if gid not in sheets:
            sheets[gid] = {'id': gid, 'gen': 'weave', 'title': f'Photo-man sheet {sh}', 'category': 'weave', 'size': None,
                           'path': 'weave/cast/man/README.md', 'poems': [], 'n': 0}
        dst = OUT / 'img/weave' / (('rig.' if catg == 'rig' else '') + k + '.webp')
        box, sc, sz = thumb(src, dst)
        view = next((v for v in ('threequarter_back', 'threequarter', 'profile', 'front', 'back', 'sitting') if v in k), '')
        if '.3q.' in k: view = 'threequarter'
        state = ''
        if cls == 'hand': state = next((s for s in STATES['hand'] if s.replace(' ', '_') in k or s in k), k.split('.')[-1])
        elif cls == 'head': state = k.split('.')[-1]
        elif cls == 'shoe': state = k.split('.')[-1]
        add({'id': f'weave/{"rig." if catg == "rig" else ""}{k}', 'gen': 'weave', 'sheet': gid, 'scale_group': gid,
             'img': f'bodylab/{dst.relative_to(OUT)}', 'label': k, 'nl': norm_label(k), 'class': cls, 'character': 'poet',
             'costume': 'photo_man', 'poems': [], 'bbox': None, 'w': sz[0], 'h': sz[1], 'src_w': box[2] - box[0], 'src_h': box[3] - box[1],
             'thumb_scale': sc, 'brads': [], 'nbrads': 0, 'pivot': None, 'kind': catg,
             'side': 'L' if '_L' in k or '.L.' in k else 'R' if '_R' in k or '.R.' in k else '', 'view': view, 'state': state,
             'src': 'weave/' + f, 'replacement': cls in ('torso',) and 'body_' in k})

# ───────────────────────── run ─────────────────────────
for r in parts: vintage_split(r)
for r in parts:
    if r['gen'] == 'cut': apply_regions(r)
propagate()
older()
for r in parts:
    if r['gen'] == 'cut': finish(r)
    else:
        r.setdefault('pair', r['class'] in ('eyes', 'brows') and not r['side'])
        r['nl'] = r.get('nl', '')
        ov = OVERRIDES.get(r['id'])
        if ov: r.update({k: v for k, v in ov.items() if k != 'note'}); r['override'] = True

# cell frames: a card that wholly contains another substantial card on the same sheet is the grid cell, not the part
_bys = collections.defaultdict(list)
for r in parts:
    if r['gen'] == 'cut' and r['class'] != 'other': _bys[r['sheet']].append(r)
for sid, rs in _bys.items():
    for a in rs:
        ax, ay, aw, ah = a['bbox']
        for b in rs:
            if b is a: continue
            bx, by_, bw, bh = b['bbox']
            if bx >= ax - 3 and by_ >= ay - 3 and bx + bw <= ax + aw + 3 and by_ + bh <= ay + ah + 3 and bw * bh > 0.03 * aw * ah and bw * bh < 0.8 * aw * ah and b['class'] != 'other':
                a['class'] = 'other'; a['state'] = 'cell_frame'
                a['problem'] = 'cut as a whole grid cell around ' + b['id'].split('/')[-1] + ' (duplicate of the inner card)'
                break

# lettering cut as cards: very flat strips that are not face features
for r in parts:
    if r['gen'] == 'cut' and r['class'] not in ('other', 'eyes', 'brows', 'mouth', 'glasses', 'hip', 'seat'):
        if r['w'] > 4.2 * r['h'] or (r['h'] < 48 and r['w'] > 2.5 * r['h']):
            r['class'] = 'other'; r['state'] = 'text'

# barefoot characters: their "foot" cards are feet, everyone else wears shoes
BARE = {'angel', 'ghost_child', 'young_ghost'}
for r in parts:
    if r['class'] in ('foot', 'shoe') and r.get('state') != 'sock':
        r['class'] = 'foot' if r['character'] in BARE else 'shoe'

# ───────── scale per group ─────────
for r in parts:
    r.setdefault('scale_group', r['sheet'])
    btype = CHAR.get(r['character'], ('adult',))[0]
    r['btype'] = btype
    if r['class'] == 'other' or r['costume'] == 'macro_eye': continue
    m = measure_px(r['class'], r)
    e = expected_cm(r['class'], btype, r)
    if m and e:
        # older generations: measure in source px (thumbs were downsized)
        k = (r.get('src_w', r['w']) / r['w']) if r['gen'] != 'cut' else 1
        r['_ppc'] = m * k / e

groups = collections.defaultdict(list)
for r in parts:
    if '_ppc' in r: groups[r['scale_group']].append(r)
gscale = {}
PRIMARY = {'upper_arm', 'forearm', 'thigh', 'shin', 'hand', 'shoe', 'foot', 'head'}
for g, rs in list(groups.items()):
    prim = [r for r in rs if r['class'] in PRIMARY]
    if prim: groups[g] = rs = prim          # face-feature cards carry wide skin margins: use them only when nothing else is measurable
    vals = sorted(r['_ppc'] for r in rs)
    gscale[g] = {'ppc': round(median(vals), 3), 'n': len(vals),
                 'by': dict(collections.Counter(r['class'] for r in rs)),
                 'spread': round(vals[int(len(vals) * .8) - 1 if len(vals) > 4 else -1] / vals[int(len(vals) * .2)], 2) if len(vals) > 1 else 1}
if 'arena_code' in sheets: gscale['arena_code'] = {'ppc': 12.0, 'n': 0, 'by': {}, 'spread': 1, 'known': True}

# fallback: a group with nothing measurable borrows the character's body-sheet scale (or the character median)
char_ppc = collections.defaultdict(list)
for g, v in gscale.items():
    rs = groups.get(g, [])
    if rs: char_ppc[(rs[0]['character'], rs[0]['costume'])].append(v['ppc'])

def ref_sheet(ch, co):
    """the character's reference body sheet (front body, else compact core, else any .body)"""
    cands = [sid for sid, s in sheets.items() if s['gen'] == 'cut' and sid in gscale and
             any(r['character'] == ch and r['costume'] == co for r in groups.get(sid, []))]
    for pat in (r'\.body\.front$', r'compact-core$|\.core$', r'\.body$', r'\.body\.', r'hipcore$'):
        hit = [s for s in cands if re.search(pat, s)]
        if hit:
            # prefer the sheet with the most limb measurements
            return max(hit, key=lambda s: sum(1 for r in groups[s] if r['class'] in ('upper_arm', 'forearm', 'thigh', 'shin') and r['character'] == ch))
    return None

for r in parts:
    g = r['scale_group']
    if g in gscale:
        r['scale_px_per_cm'] = gscale[g]['ppc']; r['scale_source'] = 'sheet'
    else:
        v = char_ppc.get((r['character'], r['costume']))
        r['scale_px_per_cm'] = round(median(v), 3) if v else None; r['scale_source'] = 'character median' if v else 'none'
    if r['gen'] != 'cut' and r['scale_px_per_cm']:
        # thumbs are downsized; store display scale in the thumb's own px
        r['scale_px_per_cm'] = round(r['scale_px_per_cm'] * r['w'] / r.get('src_w', r['w']), 4)

# ───────────────────────── problems ─────────────────────────
problems = []          # page-level list
def prob(kind, sev, msg, **kw):
    d = {'kind': kind, 'sev': sev, 'msg': msg}; d.update(kw); problems.append(d); return d

for r in parts: r['problems'] = []

# 1) in-sheet proportion outliers (a part far off the norm at its own sheet's scale)
for r in parts:
    if '_ppc' in r and r['scale_source'] == 'sheet' and gscale[r['scale_group']]['n'] >= 3 and r['gen'] == 'cut':
        f = r['_ppc'] / gscale[r['scale_group']]['ppc']
        if f > 1.4 or f < 1 / 1.4:
            r['problems'].append(f"proportion: {r['class'].replace('_', ' ')} is {f:.2f}× its sheet's norm for a {STATURE[r['btype']][0]} cm figure")

# 2) cross-sheet scale: each sheet vs the character's reference body sheet
chars = sorted({(r['character'], r['costume']) for r in parts if r['gen'] == 'cut'})
REF = {}
for ch, co in chars:
    REF[(ch, co)] = ref_sheet(ch, co)

def med_len(rs):
    v = [measure_px(r['class'], r) for r in rs]
    v = [x for x in v if x]
    return median(v) if v else None

sheet_rel = {}
for sid, s in sheets.items():
    if s['gen'] != 'cut' or sid not in gscale: continue
    rs = [r for r in parts if r['sheet'] == sid]
    cc = collections.Counter((r['character'], r['costume']) for r in rs if r['class'] != 'other')
    if not cc: continue
    ch, co = cc.most_common(1)[0][0]
    ref = REF.get((ch, co))
    s['character'], s['costume'], s['ref'] = ch, co, ref
    if not ref or ref == sid: s['rel'] = 1.0; continue
    rel = gscale[sid]['ppc'] / gscale[ref]['ppc']
    s['rel'] = round(rel, 3)
    # direct comparison per class where both sheets have that class
    direct = {}
    for cls in ('hand', 'shoe', 'foot', 'head', 'upper_arm', 'forearm', 'thigh', 'shin'):
        a = med_len([r for r in rs if r['class'] == cls and r['character'] == ch])
        b = med_len([r for r in parts if r['sheet'] == ref and r['class'] == cls and r['character'] == ch])
        if a and b: direct[cls] = round(a / b, 2)
    s['direct'] = direct
    if rel > 1.25 or rel < 0.8:
        what = '; as drawn: ' + ', '.join(f"{k.replace('_', ' ')} {v:.2f}× the body-sheet {k.replace('_', ' ')}" for k, v in direct.items()) if direct else ''
        sev = 'high' if (rel > 1.6 or rel < 1 / 1.6) else 'mid'
        prob('scale', sev, f"{sid}: drawn at {rel:.2f}× the body sheet's scale — rescale ×{1 / rel:.2f} to match {ref}{what}",
             sheet=sid, ref=ref, rel=round(rel, 3), character=ch, costume=co, direct=direct)

# 3) body-sheet internal consistency: hand vs forearm, foot vs shin, head vs torso on reference sheets
for (ch, co), ref in REF.items():
    if not ref: continue
    rs = [r for r in parts if r['sheet'] == ref and r['character'] == ch]
    def mcm(cls):
        v = [measure_px(cls, r) for r in rs if r['class'] == cls]
        v = [x for x in v if x]
        return median(v) / gscale[ref]['ppc'] if v else None
    H = STATURE[CHAR[ch][0]][0]
    for a, b, norm in (('hand', 'forearm', 0.108 * 1.08 / 0.146), ('shoe', 'shin', 0.152 * 1.1 / 0.246),
                       ('forearm', 'upper_arm', 0.146 / 0.186), ('shin', 'thigh', 1.0)):
        x, y = mcm(a), mcm(b)
        if x and y:
            f = (x / y) / norm
            if f > 1.3 or f < 1 / 1.3:
                prob('proportion', 'high' if (f > 1.6 or f < 1 / 1.6) else 'mid',
                     f"{ref}: {a.replace('_', ' ')} is {f:.2f}× the expected size relative to the {b.replace('_', ' ')} ({ch})",
                     sheet=ref, character=ch, costume=co, rel=round(f, 2))

# 4) missing parts per character
NEED = [('head', 'front'), ('head', 'profile'), ('head', 'threequarter'), ('head', 'back'), ('eyes', None), ('brows', None),
        ('mouth', None), ('torso', 'front'), ('torso', 'back'), ('torso', 'profile'), ('hip', None), ('seat', None),
        ('upper_arm', 'L'), ('upper_arm', 'R'), ('forearm', 'L'), ('forearm', 'R'), ('hand', 'L'), ('hand', 'R'),
        ('hand', 'profile'), ('thigh', 'L'), ('thigh', 'R'), ('shin', 'L'), ('shin', 'R'), ('feet', 'L'), ('feet', 'R'),
        ('feet', 'profile')]
missing = {}
for ch, co in chars:
    rs = [r for r in parts if r['character'] == ch and r['costume'] == co and r['class'] != 'other']
    if len(rs) < 6 or not REF.get((ch, co)): continue      # only characters with a body sheet
    miss = []
    for cls, q in NEED:
        cs = ('foot', 'shoe') if cls == 'feet' else (cls,)
        pool = [r for r in rs if r['class'] in cs]
        if q in ('L', 'R'):
            ok = any(r['side'] == q for r in pool)
            if not ok and pool and any(not r['side'] for r in pool): miss.append(f"{cls.replace('_', ' ')} {q} (unlabeled sides only)")
            elif not ok: miss.append(f"{cls.replace('_', ' ')} {q}")
        elif q:
            if not any(r['view'] == q for r in pool): miss.append(f"{cls.replace('_', ' ')} {q}")
        elif not pool: miss.append(cls)
    if miss:
        missing[f'{ch}/{co}'] = miss
        prob('missing', 'mid' if len(miss) < 8 else 'high', f"{CHAR[ch][1]} · {co}: no " + ', '.join(miss), character=ch, costume=co, items=miss)

# 5) duplicates (perceptual hash, same class, same character)
if Image is not None:
    for r in parts:
        r['_h'] = dhash(ROOT / r['img'])
    by = collections.defaultdict(list)
    for r in parts:
        if r['class'] != 'other' and r['_h'] is not None: by[(r['class'], r['character'])].append(r)
    for (cls, ch), rs in by.items():
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                if a['gen'] != b['gen']: continue
                if abs(math.log(a['w'] / b['w'])) > .12 or abs(math.log(a['h'] / b['h'])) > .12: continue
                if bin(a['_h'] ^ b['_h']).count('1') <= 3:
                    a.setdefault('dups', []).append(b['id']); b.setdefault('dups', []).append(a['id'])
    seen = set()
    for r in parts:
        if r.get('dups'):
            grp = tuple(sorted([r['id']] + r['dups']))
            if grp in seen: continue
            seen.add(grp)
            r['problems'].append('possible duplicate of ' + ', '.join(r['dups'][:4]))
            prob('duplicate', 'low', f"{len(grp)} near-identical {r['class'].replace('_', ' ')} cards ({CHAR[r['character']][1]}): " + ', '.join(grp[:5]) + (' …' if len(grp) > 5 else ''),
                 character=r['character'], parts=list(grp))

# 6) labels: unreadable or unresolved; reviewer notes from overrides
for r in parts:
    if r.get('problem'): r['problems'].append(r['problem'])
    if r['gen'] == 'cut' and r.get('unresolved'):
        r['problems'].append('unclassified: empty/garbled label and no look-alike on the sheet')
    if r['gen'] == 'cut' and not r['label'].strip() and r['class'] != 'other':
        r['problems'].append('no label on the card (class inferred from the sheet)')

# attach sheet-level scale problems to parts
for p in problems:
    if p['kind'] == 'scale':
        for r in parts:
            if r['sheet'] == p['sheet'] and r['character'] == p['character']:
                r['problems'].append(f"sheet scale ×{p['rel']:.2f} vs body sheet {p['ref']} (rescale ×{1 / p['rel']:.2f})")

# ───────────────────────── write ─────────────────────────
KEEP = ['id', 'gen', 'sheet', 'img', 'label', 'class', 'side', 'view', 'state', 'shows', 'character', 'costume', 'poems',
        'w', 'h', 'bbox', 'brads', 'nbrads', 'pivot', 'scale_px_per_cm', 'scale_source', 'problems', 'pair', 'dups', 'src',
        'override', 'prop_from', 'src_w', 'src_h']
out_parts = []
for r in parts:
    d = {k: r[k] for k in KEEP if k in r and r[k] not in (None, '', [], False)}
    if r.get('_ppc'): d['own_ppc'] = round(r['_ppc'], 3)
    out_parts.append(d)
for sid, s in sheets.items():
    s['n'] = sum(1 for r in parts if r['sheet'] == sid)
    if sid in gscale: s['scale'] = gscale[sid]
counts = collections.defaultdict(collections.Counter)
for r in parts: counts[r['class']][f"{r['character']}/{r['costume']}"] += 1
chars_out = {}
for r in parts:
    k = f"{r['character']}/{r['costume']}"
    c = chars_out.setdefault(k, {'character': r['character'], 'costume': r['costume'], 'name': CHAR[r['character']][1],
                                  'body': CHAR[r['character']][0], 'stature_cm': STATURE[CHAR[r['character']][0]][0],
                                  'gen': r['gen'], 'n': 0, 'ref_sheet': REF.get((r['character'], r['costume']))})
    c['n'] += 1
doc = {'about': 'Body Lab: every body piece across all cut-out generations, classified, with a solved px/cm scale per sheet. Built by shots/bodylab/build.py.',
       'stature': {k: {'cm': v[0], 'head_cm': v[1]} for k, v in STATURE.items()},
       'characters': chars_out, 'sheets': sheets, 'parts': out_parts, 'problems': problems, 'missing': missing,
       'counts': {k: dict(v) for k, v in counts.items()}}
(OUT / 'body.json').write_text(json.dumps(doc, separators=(',', ':')))
print('parts', len(out_parts), 'sheets', len(sheets), 'problems', len(problems))
print(collections.Counter(r['class'] for r in parts).most_common())
print('scale problems', sum(1 for p in problems if p['kind'] == 'scale'), 'missing', len(missing))

# ───────────────────────── review contact sheets ─────────────────────────
COL = {'hand': '#ff4d4d', 'foot': '#ff9f1a', 'shoe': '#ff9f1a', 'head': '#4dd2ff', 'face': '#4dd2ff', 'eyes': '#3cff7a',
       'brows': '#b8ff3c', 'mouth': '#ff5ce1', 'nose': '#ffe14d', 'ear': '#ffe14d', 'hair': '#9a7bff', 'torso': '#2f7bff',
       'upper_arm': '#00e0b0', 'forearm': '#00a888', 'thigh': '#c06cff', 'shin': '#8a3cff', 'hip': '#ffb38a',
       'seat': '#d9a066', 'neck': '#aaaaaa', 'glasses': '#ffffff', 'other': '#666666'}
AB = {'hand': 'HND', 'foot': 'FT', 'shoe': 'SHO', 'head': 'HEAD', 'eyes': 'EYE', 'brows': 'BRW', 'mouth': 'MTH', 'nose': 'NOS',
      'ear': 'EAR', 'hair': 'HAIR', 'torso': 'TOR', 'upper_arm': 'UA', 'forearm': 'FA', 'thigh': 'TH', 'shin': 'SH',
      'hip': 'HIP', 'seat': 'SEAT', 'neck': 'NECK', 'glasses': 'GLS', 'other': '--'}
if REVIEW and Image is not None:
    rv = Path(os.environ.get('BODYLAB_REVIEW', OUT / 'review')); rv.mkdir(parents=True, exist_ok=True)
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    except Exception: font = ImageFont.load_default()
    cut_sheets = [sid for sid, s in sheets.items() if s['gen'] == 'cut']
    if os.environ.get('BODYLAB_ONLY'):
        only = set(Path(os.environ['BODYLAB_ONLY']).read_text().split())
        cut_sheets = [s for s in cut_sheets if s in only]
        for f in rv.glob('sheets_*.jpg'): f.unlink()
    for i in range(0, len(cut_sheets), 4):
        tiles = []
        for sid in cut_sheets[i:i + 4]:
            im = Image.open(ROOT / sheets[sid]['path']).convert('RGB')
            im = Image.blend(im, Image.new('RGB', im.size, 'black'), .45)
            d = ImageDraw.Draw(im)
            for gy in range(100, im.size[1], 100):
                d.line([0, gy, im.size[0], gy], fill=(90, 90, 0), width=1); d.text((2, gy - 24), str(gy), fill='yellow', font=font)
            for gx in range(100, im.size[0], 100):
                d.line([gx, 0, gx, 14], fill='yellow', width=2); d.text((gx + 2, im.size[1] - 26), str(gx // 100), fill='yellow', font=font)
            for r in parts:
                if r['sheet'] != sid: continue
                x, y, w, h = r['bbox']; c = COL[r['class']]
                d.rectangle([x, y, x + w, y + h], outline=c, width=4)
                t = AB[r['class']] + (r['side'] or '') + ('*' if r.get('override') else '')
                d.rectangle([x, y, x + 13 * len(t) + 8, y + 26], fill='black')
                d.text((x + 4, y + 1), t, fill=c, font=font)
            d.rectangle([0, 0, 14 * len(sid) + 10, 30], fill='black'); d.text((5, 3), sid, fill='yellow', font=font)
            im.thumbnail((1100, 1100)); tiles.append(im)
        Wt = 1100; Ht = max(t.size[1] for t in tiles)
        M = Image.new('RGB', (Wt * 2, Ht * ((len(tiles) + 1) // 2)), 'black')
        for k, t in enumerate(tiles): M.paste(t, ((k % 2) * Wt, (k // 2) * Ht))
        M.save(rv / f'sheets_{i // 4:03d}.jpg', quality=80)
    print('review sheets in', rv)
