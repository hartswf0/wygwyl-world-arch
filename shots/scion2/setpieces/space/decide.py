"""SPACE step 3: how each set piece sits in a stage -> shots/scion2/setpieces/space.json

Inputs (all read-only): shots/kits/cut/catalog.json, registry.json; cache/measure.json (measure.py, pixels);
cache/clip.json (clipview.py); sibling swarm outputs used as evidence when present:
  ../semantics.json  final.category (object class from label words + CLIP + kNN)
  ../hygiene.json    grade / usable (copied through as 'hygiene' so a planner can filter; not decided here)

Per part (kind 'card'; kind 'ref' parts are listed with skip='reference panel' and nothing else):
  plane    far_backdrop | mid_set | ground_plane | near_set | foreground_occluder | overlay_fx
  contact  {type, y_px, x0_px, x1_px}  (px in the part's own webp, origin top-left)
           type: stands (floor contact = lowest opaque row, x extent of the opaque bottom band)
                 rests  (small prop standing on a surface, pickable; same line)
                 lies_flat (a ground piece: y = lowest row; also back_y = top row, where things stand on it)
                 inset  (a pane / window / door leaf that fills an opening of another piece; line = lowest row)
                 hangs  (y = TOP opaque row, x extent of the top band = suspension line)
                 floats (sky bodies, clouds, free fx: no line)
                 full-frame (backdrop scaled to the frame: no line)
                 overlay (fx / graphic laid over the frame: no line)
  view     front | 3/4 | side | top | perspective (one element drawn with convergence: a trapezoid floor, a
           receding wall) | scene (a whole painted picture / backdrop) | flat (fx, text, glow)
  tile     {left, right, repeat, seam, seam_corr}: left/right = that edge is a cut-straight vertical edge;
           repeat = both straight AND left/right strips match (seam <= SEAM_OK Lab units) for a strip piece
  size_cm  {h, w} or null when sized by the frame (scale_src 'frame')
  scale_src  label_cm | registry:dossier | registry:table | prior:<noun> | sheet_median | frame | none
  scale_conflict  null or {own_ppc, sheet_ppc, ratio, sheet_n} when implied size disagrees with the sheet scale by >40%
  evidence  {words, category, measures, clip_view, rules[]}; basis per field: measured | viewed | inferred
"""
import json, math, os, re, sys
from collections import Counter, defaultdict
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
SP = os.path.join(ROOT, 'shots/scion2/setpieces')
TAGS = ('.props.', '.set.', '.hero.', '.fx.')
SEAM_OK = 12.0
CONFLICT = 0.40

# ---- real-size priors: noun -> (cm, axis). axis h = drawn height, w = drawn width, long = longest side.
# Lists are checked in order; the first noun that matches the label wins, so specific nouns come first.
PRIORS = [
    # compound / specific first
    ('light string', 400, 'w'), ('string lights', 400, 'w'), ('string of bulbs', 400, 'w'), ('garland', 400, 'w'),
    ('curtain rod', 200, 'w'), ('door knob', 6, 'w'), ('knob', 6, 'w'), ('lamp shade', 40, 'w'), ('lampshade', 40, 'w'), ('lamp base', 150, 'h'), ('street ?lamp', 450, 'h'), ('lamp ?post', 450, 'h'),
    ('phone ?booth', 230, 'h'), ('phonebooth', 230, 'h'), ('payphone', 60, 'h'), ('wall phone', 60, 'h'),
    ('dj booth', 110, 'h'), ('bell ?tower', 2500, 'h'), ('clock ?tower', 2500, 'h'), ('fire ?escape', 900, 'h'),
    ('stair tread', 120, 'w'), ('tread', 120, 'w'), ('rose window', 400, 'w'), ('door ?post', 220, 'h'), ('door leaf', 205, 'h'), ('door slab', 205, 'h'), ('doorway', 220, 'h'),
    ('wine ?glass', 18, 'h'), ('champagne', 15, 'h'), ('coupe', 15, 'h'), ('table base', 70, 'h'),
    ('palm leaf', 200, 'long'), ('palm tree', 900, 'h'), ('palms', 900, 'h'), ('sofa arm', 65, 'h'), ('pew', 95, 'h'), ('kneeler', 20, 'h'),
    # handheld / small
    ('mug', 10, 'h'), ('cup', 10, 'h'), ('bottle', 30, 'h'), ('glass', 15, 'h'), ('candle', 20, 'h'), ('lantern', 45, 'h'),
    ('bulb', 10, 'h'), ('handset', 22, 'long'), ('receiver', 21, 'long'), ('phone', 22, 'long'), ('microphone', 22, 'long'),
    ('mic', 22, 'long'), ('tambourine', 25, 'w'), ('journal', 22, 'long'), ('book', 24, 'long'), ('envelope', 22, 'w'),
    ('letter', 22, 'w'), ('snapshot', 12, 'long'), ('photo', 12, 'long'), ('coin', 3, 'w'), ('vape', 12, 'long'),
    ('hourglass', 30, 'h'), ('bread', 25, 'w'), ('plate', 25, 'w'), ('dish', 25, 'w'), ('platter', 30, 'w'),
    ('sunglasses', 15, 'w'), ('jacket', 70, 'h'), ('hat', 30, 'w'), ('daisy', 30, 'h'), ('rose', 40, 'h'), ('flower', 40, 'h'),
    ('raven', 35, 'long'), ('guitar', 100, 'long'), ('clock', 40, 'w'), ('cushion', 45, 'w'), ('blanket', 150, 'w'),
    ('mattress', 200, 'long'), ('suitcase', 70, 'w'), ('crate', 50, 'h'), ('basin', 60, 'w'), ('speaker', 110, 'h'),
    ('turntable', 50, 'w'), ('decks', 100, 'w'), ('television', 60, 'w'), ('tv', 60, 'w'), ('mirror', 80, 'h'),
    # furniture
    ('armchair', 95, 'h'), ('chair', 90, 'h'), ('sofa', 200, 'w'), ('couch', 200, 'w'), ('table', 75, 'h'), ('desk', 75, 'h'),
    ('bench', 180, 'w'), ('bed', 200, 'w'), ('dresser', 90, 'h'), ('piano', 130, 'h'), ('counter', 105, 'h'),
    ('curtain', 220, 'h'), ('blinds', 140, 'w'), ('planter', 60, 'h'), ('pot', 40, 'h'), ('plinth', 100, 'h'),
    ('pedestal', 100, 'h'), ('lamp', 160, 'h'), ('chandelier', 90, 'h'),
    # architecture
    ('door', 205, 'h'), ('gate', 400, 'h'), ('window', 140, 'h'), ('shutter', 140, 'h'), ('booth', 230, 'h'),
    ('kiosk', 250, 'h'), ('railing', 100, 'h'), ('rail', 100, 'h'), ('fence', 120, 'h'), ('stair', 250, 'h'),
    ('steps', 200, 'h'), ('column', 450, 'h'), ('pillar', 450, 'h'), ('lancet', 400, 'h'),
    ('niche', 200, 'h'), ('porch', 300, 'h'), ('awning', 300, 'w'), ('canopy', 400, 'w'), ('pediment', 600, 'w'),
    ('arch', 400, 'h'), ('facade', 900, 'h'), ('house', 800, 'h'), ('building', 1200, 'h'), ('chapel', 1400, 'h'),
    ('temple', 1600, 'h'), ('belfry', 600, 'h'), ('spire', 1500, 'h'), ('tower', 2500, 'h'), ('bridge', 3000, 'w'),
    ('viaduct', 4000, 'w'), ('catwalk', 400, 'w'), ('platform', 300, 'w'), ('wall', 300, 'h'), ('sign', 60, 'h'),
    # land / vehicles
    ('tree', 650, 'h'), ('stump', 60, 'h'), ('rock', 100, 'h'), ('boulder', 150, 'h'), ('bush', 120, 'h'),
    ('motorcycle', 110, 'h'), ('motorbike', 110, 'h'), ('bike', 100, 'h'), ('bicycle', 100, 'h'), ('car', 150, 'h'),
    ('boat', 600, 'w'), ('ship', 3000, 'w'),
]
PRIOR_RE = [(re.compile(r'\b' + n.replace(' ?', '\0').replace(' ', '[ .-]?').replace('\0', '[ -]?') + r's?\b'), n, cm, ax)
            for n, cm, ax in PRIORS]
# nouns whose prior is a firm everyday size (used to build the per-sheet scale); the rest only size themselves
TRUSTED = {'mug', 'cup', 'bottle', 'glass', 'wine ?glass', 'coupe', 'champagne', 'candle', 'handset', 'receiver', 'phone',
           'payphone', 'microphone', 'tambourine', 'journal', 'book', 'chair', 'armchair', 'sofa', 'couch', 'table', 'desk',
           'bench', 'pew', 'door', 'door leaf', 'door slab', 'doorway', 'door ?post', 'window', 'phone ?booth', 'phonebooth',
           'car', 'motorcycle', 'motorbike', 'bike', 'bicycle', 'suitcase', 'lamp base', 'lamp', 'speaker', 'dj booth',
           'kneeler', 'mattress', 'bed', 'basin', 'railing', 'rail', 'curtain', 'tv', 'television'}

# words that name a PART of the thing the noun names ("tower cap", "ship mast", "door glass insert"): prior not trusted
PART_WORDS = r'\b(cap|caps|roof|top|trim|hinge|hinges|pivot|insert|inserts|edge|rim|seam|mast|trunk|tab|backing|backer|panel|fragment|half|segment|remnant|remnants|shard|shards|piece|handle|knob|leg|legs|arm|seat|cushion|lid|base|spoke|spokes|finial|pane|glass|glazing|mullion|sill|lintel|strut|bracket|stem|petal|petals|leaf|frame)\b'
# plausible longest side (cm) by semantics category; a size source outside it is rejected
RANGE = {'architecture': (40, 20000), 'aperture': (20, 3000), 'ground': (50, 100000), 'backdrop': (50, 100000),
         'furniture-seat': (30, 350), 'furniture-surface': (30, 400), 'vehicle': (60, 5000), 'handheld-prop': (1, 90),
         'wearable': (3, 150), 'plant-nature': (3, 5000), 'character-fragment': (2, 200), 'light-fx': (1, 100000),
         'text-graphic': (1, 100000), 'other': (1, 100000)}
# last-resort size by class when no noun, no registry size and no sheet scale (weak, never trusted for the sheet)
CAT_PRIOR = {'furniture-seat': (90, 'h'), 'furniture-surface': (75, 'h'), 'vehicle': (150, 'h'), 'handheld-prop': (20, 'long'),
             'wearable': (40, 'long')}
W_HANG = r'\b(chandeliers?|hanging|hang|pendant|curtains?|blinds|light[ .-]?string|string lights|garland|cobwebs?|chain|bulbs?|lamp[ .-]?shade|wind ?chime|mobile|cage|swing|banner|bunting|wire|cord|vines?|icicles?)\b'
W_INSET = r'\b(panes?|glazing|glass insert|mullions?|sash|window[ .-]?view|inserts?|inlays?|leaded|stained glass|aperture|iris)\b'
W_SKY = r'\b(corona|sunburst|moon|moons|sun(?!-dried)|suns|clouds?|stars?|sky|comet|planet|galaxy|constellation|aurora|orb|halo)\b'
W_FG = r'\b(foreground|fg|near|framing|occluder|frame[ -]edge|overhang|front layer)\b'
W_FAR = r'\b(far|distant|background|bg|backing|backer|backdrop|horizon|skyline|panorama|silhouette|mountains?|hills?|vista|city)\b'
W_GROUND = r'\b(floor|ground|road|street|pavement|paving|path|sand|shore|beach|water|sea|tide|pool|field|grass|carpet|rug|plaza|quay|kerb|mud|puddle|tiles?|mosaic|deck|driveway|slope|trail|causeway|terrace)\b'
W_PICK = r'\b(cup|mug|glass|bottle|phone|handset|receiver|mic|microphone|book|journal|letter|envelope|snapshot|photo|coin|key|vape|candle|tambourine|hourglass|bread|plate|coupe|lantern|rose|daisy|flower|lighter|cigarette|pen)s?\b'
W_STRIP = r'\b(strip|band|repeatable|tile|tileable|run|frieze|border|fence|railing|rail|kerb|floor|road|sea|water|sky|wall|facade|pavement|paving|shore|horizon|skyline)\b'

V_TOP = r'(top[ -]?down|\bplan view\b|\bplan\b|overhead|from above|aerial|bird.?s.?eye)'
V_SIDE = r'(\bprofile\b|side[ -]?view|side[ -]?elevation|side[ -]?on\b|\(side\)|seen from the side)'
V_34 = r'(3/4|3-4 view|three[ -]?quarter|threequarter)'
V_FRONT = r'(front[ -]?view|front[ -]?elevation|\belevation\b|face[ -]?on|straight[ -]?on|\(front\))'
V_PERSP = r'(\bperspective\b|receding|vanishing)'

CAT2PLANE = {'backdrop': 'far_backdrop', 'ground': 'ground_plane', 'architecture': 'mid_set', 'aperture': 'mid_set',
             'furniture-seat': 'near_set', 'furniture-surface': 'near_set', 'vehicle': 'mid_set', 'handheld-prop': 'near_set',
             'wearable': 'near_set', 'plant-nature': 'mid_set', 'light-fx': 'overlay_fx', 'text-graphic': 'overlay_fx',
             'character-fragment': 'near_set', 'other': None}
PLACE2PLANE = {'sky': 'far_backdrop', 'fx': 'overlay_fx', 'land': 'mid_set', 'arch': 'mid_set', 'floor': 'near_set',
               'held': 'near_set', 'worn': 'near_set', 'band': None, 'body': 'near_set'}


RULE_CHANGES = [
    'conflict_worst.jpg: priors matched the WHOLE when the label names a part (tower CAP -> 2500 cm, ship MAST, door GLASS INSERT, '
    'tree TRUNK): added PART_WORDS; a part word drops the noun prior, the registry dossier and the registry table for that part.',
    'conflict_worst.jpg: "palm" matched hand palms (puppet hands) -> only "palm tree"/"palms".',
    'conflict_worst.jpg/doubt.jpg: registry dossier sizes often name the wrong prop (lancet window 10x30 cm, facade 100 cm, '
    'railway arch band 10x2 cm): dossier now loses to any noun prior it disagrees with by >40%, and every size source must fall in a '
    'per-category plausible range (RANGE) or the next source is used.',
    'conflict_worst.jpg: skyline / distant pieces were sized by a building prior: far_backdrop is now always frame-sized.',
    'far_backdrop.jpg: a door with "far" on its label became a full-frame backdrop: far words only move other/plant/backdrop '
    'classes (or skyline/horizon/city words); architecture keeps mid_set with a depth hint. Backdrop class on a .props. sheet, small, '
    'no sky word -> near_set (VU meter faces). Horizontal sky bands were "floats": bands (W>=2.5H, straight sides) are full-frame.',
    'fg_occluder.jpg: "close" (close-up photo) made a snapshot a foreground occluder: removed from FG words.',
    'ground.jpg/view_nonfront.jpg: perspective from edge convergence fired on mounds, waves, saddles: ground trapezoid now needs straight '
    'slanted sides (rms < 3% W); receding wall needs one straight top/bottom edge and fill >= 0.5, and only for architecture classes.',
    'view_nonfront.jpg: puppet hands/feet/pivot plates stood on the floor: character-fragment -> contact "attached".',
    'tile_repeat.jpg: framed pictures, label cards and window frames passed the straight-edge + seam test: repeat now also needs W >= 2.5 H.',
    'overlay.jpg: every part on an .fx. sheet was an overlay (a clock, pills, a sign, leaves): when the fx class came only from the sheet '
    '(no label class, no fx word), not translucent, and CLIP depth says object/building/foliage -> near_set with a doubt note.',
    'CLIP view prompts were tested against the 27 labels that state a view: 3/27 correct, so CLIP view is recorded as evidence only, '
    'never used to decide; view comes from label words, then silhouette geometry (edge convergence, mirror symmetry).',
]


def text_of(p):
    return ' '.join([p.get('label') or '', p.get('name') or '', p['id'].split('/')[1].replace('-', ' ')]).lower()


def find(rx, t):
    m = re.search(rx, t)
    return m.group(0) if m else None


def prior_for(t):
    for rx, n, cm, ax in PRIOR_RE:
        if rx.search(t):
            return n, cm, ax
    return None


def label_cm(p):
    t = (p.get('label') or '') + ' ' + (p.get('name') or '')
    m = re.search(r'(\d{1,4}(?:\.\d)?)\s?cm\b', t, re.I)
    if not m:
        return None
    v = float(m.group(1))
    return v if v >= 1 else None


def ppc_from(cm, ax, m):
    h = m['y_low'] - m['y_top'] + 1
    w = m['x_max'] - m['x_min'] + 1
    px = {'h': h, 'w': w, 'long': max(h, w)}[ax]
    return px / cm


def main():
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    reg = json.load(open(os.path.join(CUT, 'registry.json')))['parts']
    M = json.load(open(os.path.join(HERE, 'cache', 'measure.json')))
    CL = json.load(open(os.path.join(HERE, 'cache', 'clip.json')))['parts']
    sem = {}
    if os.path.exists(os.path.join(SP, 'semantics.json')):
        sem = json.load(open(os.path.join(SP, 'semantics.json')))['parts']
    hyg = {}
    if os.path.exists(os.path.join(SP, 'hygiene.json')):
        hyg = json.load(open(os.path.join(SP, 'hygiene.json')))['parts']

    out, stats = {}, Counter()
    sheets = [sid for sid in cat if any(t in sid for t in TAGS)]
    for sid in sheets:
        S = cat[sid]
        sw, sh = S.get('size') or [1646, 956]
        rows = []
        for p in S['parts']:
            pid = p['id']
            if p['kind'] == 'ref':
                out[pid] = {'sheet': sid, 'skip': 'reference panel (kind ref)', 'label': p.get('label')}
                stats['ref'] += 1
                continue
            m = M.get(pid)
            if not m or m.get('empty'):
                out[pid] = {'sheet': sid, 'skip': 'unreadable or empty alpha', 'label': p.get('label')}
                stats['empty'] += 1
                continue
            t = text_of(p)
            r = reg.get(pid, {})
            se = (sem.get(pid) or {}).get('final') or {}
            category = se.get('category')
            rules = []
            doubt = []
            ev = {'label': p.get('label'), 'category': category, 'category_conf': se.get('confidence'),
                  'registry_place': r.get('place')}
            w_hang, w_inset, w_sky = find(W_HANG, t), find(W_INSET, t), find(W_SKY, t)
            w_fg, w_far, w_ground = find(W_FG, t), find(W_FAR, t), find(W_GROUND, t)
            w_pick, w_strip = find(W_PICK, t), find(W_STRIP, t)
            ev['words'] = {k: v for k, v in dict(hang=w_hang, inset=w_inset, sky=w_sky, fg=w_fg, far=w_far, ground=w_ground,
                                                  pick=w_pick, strip=w_strip).items() if v}
            W, H = m['W'], m['H']
            rect = m['fill'] >= 0.9 and min(m['straight_l'], m['straight_r'], m['straight_b'], m['straight_t']) >= 0.85
            big = W >= 0.45 * sw or H >= 0.6 * sh
            wide = W >= 3 * H
            fxsheet = '.fx.' in sid
            soft = m['soft'] >= 0.35

            # ---------------- plane ----------------
            plane, pb = None, None
            if category in ('light-fx', 'text-graphic') or (fxsheet and category in (None, 'other', 'backdrop')):
                plane, pb = 'overlay_fx', 'category %s%s' % (category, ' on .fx. sheet' if fxsheet else '')
                if w_sky and category != 'text-graphic':
                    plane, pb = 'far_backdrop', 'sky word %r on an fx/light piece' % w_sky
            elif w_sky and (category in ('backdrop', 'other', None, 'light-fx') or r.get('place') == 'sky'):
                plane, pb = 'far_backdrop', 'sky word %r' % w_sky
            elif category == 'ground' or (category in ('other', None, 'backdrop') and w_ground and wide):
                plane, pb = 'ground_plane', 'category ground' if category == 'ground' else 'ground word %r + wide strip' % w_ground
            elif category == 'backdrop':
                plane, pb = 'far_backdrop', 'category backdrop'
            elif category in CAT2PLANE and CAT2PLANE[category]:
                plane, pb = CAT2PLANE[category], 'category %s' % category
            else:
                pl = PLACE2PLANE.get(r.get('place'))
                if pl:
                    plane, pb = pl, 'registry place %s (category %s)' % (r.get('place'), category)
                elif w_ground:
                    plane, pb = 'ground_plane', 'band + ground word %r' % w_ground
                elif w_far or (rect and big):
                    plane, pb = 'far_backdrop', 'band + far word/rectangle'
                else:
                    plane, pb = 'mid_set', 'fallback (band, no words)'
            rules.append('plane: ' + pb)
            # fx-sheet pieces whose fx class came only from the sheet (no fx word on the label) and that CLIP sees as an
            # object or building, and that are not soft/translucent: an object drawn on an fx sheet (clock, sign, leaf)
            dep = (CL.get(pid) or {}).get('depth') or {}
            if plane == 'overlay_fx' and category == 'light-fx' and not se.get('label_class') and not soft and dep \
                    and max(dep, key=dep.get) in ('object', 'building', 'foliage') and not find(r'\b(haze|glow|light|beam|ray|flare|smoke|fog|mist|streak|spark|shimmer|dew|rain|drop|ripple|reflection|shadow|flash|halo|sheen|neon)', t):
                plane = 'near_set'
                doubt.append('fx sheet, no fx word, CLIP depth %s %.2f: treated as an object' % (max(dep, key=dep.get), max(dep.values())))
                rules.append('plane -> near_set: object-looking piece on an fx sheet (CLIP depth %s)' % max(dep, key=dep.get))
            # depth words on the label override the class default (the sheet author placed it)
            if plane in ('mid_set', 'near_set') and w_fg and not re.search(r'\bfront (view|elevation|wheel|fork|door|panel)', t):
                plane = 'foreground_occluder'; rules.append('plane -> foreground_occluder: label word %r' % w_fg)
            elif plane in ('mid_set', 'near_set') and w_far and not w_ground and category not in ('handheld-prop', 'furniture-seat', 'furniture-surface', 'wearable') \
                    and (category in ('other', 'plant-nature', 'backdrop', None) or w_far not in ('far', 'backing', 'backer', 'bg')):
                plane = 'far_backdrop'; rules.append('plane -> far_backdrop: label word %r' % w_far)
            elif plane in ('mid_set', 'near_set') and w_far:
                rules.append('depth hint: label word %r kept on %s (a %s piece set deep in the scene, not a backdrop)' % (w_far, plane, category))
            if plane == 'far_backdrop' and '.props.' in sid and not (big or w_sky):
                plane = 'near_set'; rules.append('plane -> near_set: backdrop class on a .props. sheet, small, no sky word')
            if plane == 'mid_set' and category == 'plant-nature' and re.search(r'\b(branch|branches|vines?|fronds?|leaves|foliage|canopy)\b', t) \
                    and m['edge_touch'][0] > 0.2:
                plane = 'foreground_occluder'; rules.append('plane -> foreground_occluder: hanging foliage cut flat at top edge')
            if plane in ('near_set',) and category == 'plant-nature':
                pass
            if plane == 'mid_set' and category == 'plant-nature' and not re.search(r'\b(tree|palm|trunk|bush|hedge|stump|rock)\b', t):
                plane = 'near_set'; rules.append('plane -> near_set: small plant (no tree/bush word)')
            prn = prior_for(t)
            if plane == 'far_backdrop' and category == 'backdrop' and prn and prn[1] <= 300 and not (w_sky or w_far):
                plane = 'near_set' if prn[1] <= 150 else 'mid_set'
                rules.append('plane -> %s: class says backdrop but label names a %d cm %r' % (plane, prn[1], prn[0]))
            if plane == 'far_backdrop' and not (rect or big or w_sky or w_far) and category not in ('backdrop',):
                rules.append('note: far_backdrop but small and not a rectangle')

            # ---------------- contact ----------------
            if plane == 'overlay_fx':
                ctype = 'overlay'
            elif plane == 'far_backdrop':
                bandlike = rect or (W >= 2.5 * H and m['fill'] >= 0.75 and m['straight_l'] >= 0.8 and m['straight_r'] >= 0.8)
                ctype = 'full-frame' if bandlike else 'floats' if w_sky else 'full-frame' if (big or category == 'backdrop') else 'floats'
                if not w_sky and not rect and m['straight_b'] >= 0.8 and m['base_frac'] >= 0.6:
                    ctype = 'stands'  # a skyline / distant building silhouette standing on the horizon line
                    rules.append('contact: far piece with a flat cut base -> stands on the horizon')
            elif plane == 'ground_plane':
                ctype = 'lies_flat'
            elif w_hang and not re.search(r'\b(lamp base|stand|post|floor lamp)\b', t):
                ctype = 'hangs'
            elif w_inset and category in ('aperture', 'architecture', 'other', None, 'light-fx', 'backdrop'):
                ctype = 'inset'
            elif category == 'wearable':
                ctype = 'worn'
            elif category == 'character-fragment':
                ctype = 'attached'  # a puppet part (hand, foot, pivot plate): joins a body, no stage contact
            elif plane == 'near_set' and (w_pick or category == 'handheld-prop'):
                ctype = 'rests'
            else:
                ctype = 'stands'
            contact = {'type': ctype}
            if ctype in ('stands', 'rests', 'inset', 'lies_flat'):
                contact.update(y_px=m['y_low'], x0_px=m['base_x0'], x1_px=m['base_x1'], base_runs=m['base_runs'],
                               flat_base=m['straight_b'] >= 0.8)
                if ctype == 'lies_flat':
                    contact['back_y_px'] = m['y_top']
            elif ctype == 'hangs':
                contact.update(y_px=m['y_top'], x0_px=m['top_x0'], x1_px=m['top_x1'])
            if ctype == 'rests':
                contact['pickable'] = True
            # a 'stands' piece whose bottom is ragged (no flat cut, base narrow) is more doubtful
            if ctype == 'stands' and m['straight_b'] < 0.3 and m['base_frac'] < 0.1 and m['base_runs'] <= 1 and category not in ('furniture-seat', 'furniture-surface', 'vehicle'):
                doubt.append('stands on a point (narrow single base)')
            rules.append('contact: %s' % ctype)

            # ---------------- view ----------------
            vb = None
            lv = None
            for name, rx in (('top', V_TOP), ('side', V_SIDE), ('3/4', V_34), ('front', V_FRONT), ('perspective', V_PERSP)):
                if re.search(rx, t):
                    lv = name; break
            if lv:
                view, vb = lv, 'label words'
            elif plane == 'overlay_fx':
                view, vb = 'flat', 'fx/graphic overlay'
            elif plane == 'ground_plane':
                trap = m['straight_b'] >= 0.5 and m['left_rms'] < 0.03 * W + 2 and m['right_rms'] < 0.03 * W + 2
                if m['conv_lr'] >= 0.25 and trap:
                    view, vb = 'perspective', 'trapezoid widening downward (conv_lr %.2f)' % m['conv_lr']
                elif m['conv_lr'] <= -0.25 and trap:
                    view, vb = 'perspective', 'trapezoid narrowing downward (conv_lr %.2f): seen from below / ceiling' % m['conv_lr']
                elif m['fill'] >= 0.75 and H > 0.6 * W and not wide:
                    view, vb = 'top', 'deep rectangular ground piece (H/W %.2f)' % (H / W)
                else:
                    view, vb = 'front', 'ground strip seen at grazing angle (paper-theatre floor band)'
            elif plane == 'far_backdrop':
                view, vb = ('scene', 'backdrop picture') if (rect or ctype == 'full-frame') else ('front', 'far silhouette / sky body')
            else:
                persp = abs(m['conv_tb']) >= 0.15 and min(m['top_rms'], m['bot_rms']) < 0.04 * H + 2 \
                    and max(m['top_rms'], m['bot_rms']) < 0.06 * H + 2 and m['fill'] >= 0.5
                if category in ('architecture', 'aperture', 'backdrop') or (category in (None, 'other') and r.get('place') in ('arch', 'band')):
                    if persp:
                        view, vb = 'perspective', 'top/bottom edges converge (conv_tb %.2f): receding wall' % m['conv_tb']
                    else:
                        view, vb = 'front', 'architecture default (edges parallel, conv_tb %.2f)' % m['conv_tb']
                else:
                    sym = m['sym']
                    if sym >= 0.88:
                        view, vb = 'front', 'symmetric silhouette (sym %.2f)' % sym
                    elif category == 'vehicle':
                        view, vb = 'side', 'vehicle, asymmetric silhouette (sym %.2f)' % sym
                    elif sym < 0.75:
                        view, vb = '3/4', 'asymmetric silhouette (sym %.2f)' % sym
                    else:
                        view, vb = 'front', 'weakly symmetric (sym %.2f): front, low confidence' % sym
                        doubt.append('view uncertain (sym %.2f)' % sym)
            vconf = 'high' if vb == 'label words' else 'low' if ('sym' in vb or 'default' in vb or 'grazing' in vb) else 'medium'
            rules.append('view: %s (%s, confidence %s)' % (view, vb, vconf))
            cv = (CL.get(pid) or {}).get('view') or {}

            # ---------------- tile ----------------
            seam, sc = m.get('seam'), m.get('seam_corr')
            tl, tr = m['straight_l'] >= 0.9, m['straight_r'] >= 0.9
            stripish = plane in ('ground_plane', 'far_backdrop') or bool(w_strip) or wide
            # a repeat needs a band (W >= 2.5 H): squarer straight-edged cards were mostly framed pictures, label
            # cards and window frames when viewed (audit/tile_repeat.jpg, first pass)
            rep = bool(tl and tr and stripish and W >= 2.5 * H and seam is not None and seam <= SEAM_OK)
            if re.search(r'\b(repeatable|tileable|tile)\b', t) and tl and tr:
                rep = True; rules.append('tile: label says repeatable')
            tile = {'left': bool(tl), 'right': bool(tr), 'repeat': rep, 'seam': seam, 'seam_corr': sc,
                    'border': [m.get('border_l'), m.get('border_r')],
                    'straight': [m['straight_l'], m['straight_r']]}

            rows.append(dict(pid=pid, semskip=bool(se.get('skip')), p=p, m=m, r=r, t=t, plane=plane, contact=contact, view=view, vconf=vconf, tile=tile, ev=ev,
                             rules=rules, doubt=doubt, category=category, cv=cv, w_sky=w_sky, rect=rect, big=big,
                             hyg=hyg.get(pid)))

        # ---------------- size: own estimate per part ----------------
        for x in rows:
            m, r, t = x['m'], x['r'], x['t']
            x['own'] = None
            if (x['plane'] in ('overlay_fx', 'far_backdrop') or x['contact']['type'] in ('full-frame', 'floats')) and not label_cm(x['p']):
                x['frame'] = True
                continue
            x['frame'] = False
            lc = label_cm(x['p'])
            pr = prior_for(t)
            partw = find(PART_WORDS, t)
            if partw and pr and partw in pr[0]:
                partw = None  # the part word is the noun itself ('lamp base', 'glass')
            hpx_ = m['y_low'] - m['y_top'] + 1
            wpx_ = m['x_max'] - m['x_min'] + 1
            cands = []   # (ppc, src, note, trusted)
            if lc:
                ax = 'w' if 'square' in t else 'long'
                cands.append((ppc_from(lc, ax, m), 'label_cm', '%g cm (%s) from label' % (lc, ax), True))
            prc = None
            if pr and partw:
                x['rules'].append('size: prior %r names the whole, label has part word %r -> prior not used' % (pr[0], partw))
                pr = None
            if pr:
                prc = (ppc_from(pr[1], pr[2], m), 'prior:' + pr[0], '%s ~%d cm (%s)' % (pr[0], pr[1], pr[2]),
                       pr[0] in TRUSTED and not partw)
                if partw:
                    x['rules'].append('size: prior %r names the whole, label has part word %r -> prior not trusted' % (pr[0], partw))
            if r.get('scale_src') == 'dossier' and r.get('px_per_cm') and partw:
                x['rules'].append('size: registry dossier size skipped (part word %r: dossier names the whole prop)' % partw)
            if r.get('scale_src') == 'dossier' and r.get('px_per_cm') and not partw:
                dc = (r['px_per_cm'] * (max(wpx_, hpx_) / max(r['px'])), 'registry:dossier', 'poem dossier scale_cm, longest side', True)
                if prc:
                    rat = dc[0] / prc[0]
                    if rat > 1 + CONFLICT or rat < 1 / (1 + CONFLICT):
                        x['doubt'].append('dossier size disagrees with prior %s %dcm (ratio %.2f): prior used' % (pr[0], pr[1], rat))
                        dc = None
                if dc:
                    cands.append(dc)
            if prc:
                cands.append(prc)
            if r.get('scale_src') == 'table' and r.get('px_per_cm') and not partw:
                cands.append((r['px_per_cm'], 'registry:table', 'registry size table (longest side)', False))
            lo, hi = RANGE.get(x['category'] or 'other', RANGE['other'])
            for c in cands:
                longest = max(hpx_, wpx_) / c[0]
                if lo <= longest <= hi:
                    x['own'] = c
                    break
                x['rules'].append('size: %s rejected, longest side %.0f cm outside %s range %g-%g cm' % (c[1], longest, x['category'], lo, hi))
        trusted = [x['own'][0] for x in rows if x['own'] and x['own'][3] and x['plane'] != 'ground_plane']
        sheet_ppc = float(np.exp(np.median(np.log(trusted)))) if trusted else None
        spread = float(np.exp(np.std(np.log(trusted)))) if len(trusted) >= 2 else None
        for x in rows:
            m = x['m']
            hpx = m['y_low'] - m['y_top'] + 1
            wpx = m['x_max'] - m['x_min'] + 1
            conflict = None
            if x['frame']:
                size, src = None, 'frame'
            elif x['own']:
                ppc, src = x['own'][0], x['own'][1]
                size = {'h': round(hpx / ppc, 1), 'w': round(wpx / ppc, 1)}
                if sheet_ppc and len(trusted) >= 2:
                    rat = ppc / sheet_ppc
                    others = [v for v in trusted if v != ppc] if x['own'][3] else trusted
                    if others:
                        sp2 = float(np.exp(np.median(np.log(others))))
                        rat = ppc / sp2
                        if rat > 1 + CONFLICT or rat < 1 / (1 + CONFLICT):
                            conflict = {'own_ppc': round(ppc, 3), 'sheet_ppc': round(sp2, 3), 'ratio': round(rat, 2),
                                        'sheet_n': len(others),
                                        'size_at_sheet_scale': {'h': round(hpx / sp2, 1), 'w': round(wpx / sp2, 1)}}
            elif sheet_ppc:
                ppc, src = sheet_ppc, 'sheet_median'
                size = {'h': round(hpx / ppc, 1), 'w': round(wpx / ppc, 1)}
            elif x['plane'] == 'ground_plane':
                size, src = None, 'frame'
            elif x['category'] in CAT_PRIOR:
                cm_, ax_ = CAT_PRIOR[x['category']]
                ppc, src = ppc_from(cm_, ax_, m), 'prior:category:' + x['category']
                size = {'h': round(hpx / ppc, 1), 'w': round(wpx / ppc, 1)}
            else:
                size, src = None, 'none'
            x['size'], x['src'], x['conflict'] = size, src, conflict
            x['sheet_ppc'] = sheet_ppc
            mm = {k: m[k] for k in ('W', 'H', 'fill', 'soft', 'y_top', 'y_low', 'base_frac', 'base_runs', 'straight_l',
                                     'straight_r', 'straight_b', 'straight_t', 'conv_tb', 'conv_lr', 'sym', 'seam', 'seam_corr')}
            ev = dict(x['ev'])
            ev['measures'] = mm
            ev['clip_view'] = x['cv']
            ev['size_note'] = x['own'][2] if x['own'] else ('sheet log-median of %d trusted parts' % len(trusted) if src == 'sheet_median' else src)
            ev['rules'] = x['rules']
            basis = {'plane': 'inferred', 'contact': 'measured' if 'y_px' in x['contact'] else 'inferred',
                     'view': 'inferred (label words)' if x['rules'] and 'label words' in [r for r in x['rules'] if r.startswith('view')][0] else 'inferred (pixel geometry)' if x['view'] not in ('flat',) else 'inferred',
                     'tile': 'measured', 'size': {'label_cm': 'measured (label text)', 'frame': 'inferred', 'none': 'none'}.get(src, 'inferred')}
            hg = x['hyg'] or {}
            out[x['pid']] = {
                'sheet': sid, 'label': x['p'].get('label'), 'category': x['category'],
                'plane': x['plane'], 'contact': x['contact'], 'view': x['view'], 'view_conf': x['vconf'], 'tile': x['tile'],
                'size_cm': size, 'scale_src': src, 'scale_conflict': conflict,
                'sheet_px_per_cm': round(sheet_ppc, 3) if sheet_ppc else None, 'sheet_scale_n': len(trusted),
                'sheet_scale_spread': round(spread, 2) if spread else None,
                'placeable': bool(hg.get('usable', True)) and not (x['category'] in ('character-fragment', 'text-graphic') and x['plane'] != 'overlay_fx')
                             and not x['semskip'] and not re.search(r'\b(reference|assembled|assembly|example|do not)\b', x['t']),
                'doubt': x['doubt'], 'hygiene': {'grade': hg.get('grade'), 'usable': hg.get('usable')} if hg else None,
                'basis': basis, 'evidence': ev}
            stats['card'] += 1
    summ = {
        'parts': len(out), 'cards': stats['card'], 'refs_skipped': stats['ref'], 'empty': stats['empty'],
        'plane': Counter(v['plane'] for v in out.values() if 'plane' in v),
        'contact': Counter(v['contact']['type'] for v in out.values() if 'plane' in v),
        'view': Counter(v['view'] for v in out.values() if 'plane' in v),
        'tile_repeat': sum(1 for v in out.values() if 'plane' in v and v['tile']['repeat']),
        'scale_src': Counter(v['scale_src'].split(':')[0] for v in out.values() if 'plane' in v),
        'scale_conflict': sum(1 for v in out.values() if v.get('scale_conflict')),
        'doubt': sum(1 for v in out.values() if v.get('doubt')),
        'placeable': sum(1 for v in out.values() if v.get('placeable')),
    }
    doc = {'about': __doc__ + '''
placeable = hygiene usable (../hygiene.json) AND not a character fragment / text graphic outside the fx plane AND
semantics final.skip false AND no reference/assembled/assembly/example/do-not word in the label (inferred).''',
           'rule_changes_after_viewing': RULE_CHANGES, 'summary': summ, 'priors': {n: [cm, ax] for n, cm, ax in PRIORS},
           'thresholds': {'SEAM_OK_lab': SEAM_OK, 'conflict': CONFLICT}, 'parts': out}
    json.dump(doc, open(os.path.join(SP, 'space.json'), 'w'), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
