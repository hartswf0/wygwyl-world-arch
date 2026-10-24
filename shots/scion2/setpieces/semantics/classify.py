"""SEMANTICS swarm, step 2: name every set piece and say what kind of thing it is; group pieces into scenes.

Inputs (read-only): shots/kits/cut/catalog.json, registry.json, shots/stage/sets/*.json (which parts each staged
location uses), emb_img.npz (embed.py: CLIP ViT-B/32 image embeddings of every card).
Output: shots/scion2/setpieces/semantics.json  {about, taxonomy, rules, summary, parts: {part_id: {...}}, scenes: [...]}

Per part, three independent witnesses, each recorded:
  label  (measured: words read off the catalog label/name, matched to a fixed lexicon; the head noun counts most:
          words before 'with/for/behind/in/on/through...' weigh 1.0, words after weigh 0.35)
  sheet  (measured: words in the sheet id slug + sheet title; a weak prior, weight 0.3)
  clip   (measured: CLIP zero-shot softmax over the 14 classes, several prompts per class averaged)
  knn    (measured: the 7 nearest cards in CLIP image space that HAVE a label class, softmax-weighted vote;
          label propagation, so unlabeled cards borrow the class of look-alikes, usually on the same sheet)
  pixel  (measured: hygiene.pixel_tests; thin strokes / text strip / scattered blobs off fx sheets = +1.0 text-graphic)
Fusion (inferred): score = 1.0*label + 0.3*sheet + 0.7*clip + 0.6*knn + pixel (+ folder/ fx sheet context rules, see CONTEXT below).
conflict = the label had a class and CLIP's top-1 is a different class (CLIP's probability for the label class is
recorded); confidence = fused top share, lowered when the label is missing or witnesses disagree.
"""
import json, os, re, glob
from collections import Counter, defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
OUT = os.path.join(ROOT, 'shots/scion2/setpieces/semantics.json')
TAGS = ('.props.', '.set.', '.hero.', '.fx.')

CLASSES = ['backdrop', 'ground', 'architecture', 'aperture', 'furniture-seat', 'furniture-surface', 'vehicle',
           'handheld-prop', 'wearable', 'plant-nature', 'light-fx', 'text-graphic', 'character-fragment', 'other']

# CLIP prompts (prefixed with PFX). Several per class, averaged in embedding space.
PFX = 'a painted paper cut-out of '
PROMPTS = {
    'backdrop': ['a whole landscape scene', 'a night sky with stars', 'a city skyline seen from far away', 'a wide sea and horizon',
                 'a sky gradient backdrop', 'distant hills and mountains', 'the moon in the sky', 'clouds in the sky'],
    'ground': ['a floor strip', 'a road', 'a strip of ground', 'a sandy shore', 'a stone pavement', 'a patch of water seen from above',
               'wooden floor boards', 'a path'],
    'architecture': ['a building facade', 'a brick wall', 'a stone column', 'a staircase', 'a tower', 'a roof', 'a house',
                     'a bridge', 'a railing or fence', 'a church building'],
    'aperture': ['a door', 'a window', 'a gate', 'an archway', 'a window frame with glass panes', 'an open doorway',
                 'a gothic arched window'],
    'furniture-seat': ['a chair', 'a bench', 'a sofa', 'a bed', 'a stool', 'a church pew', 'an armchair', 'a mattress'],
    'furniture-surface': ['a table', 'a desk', 'a counter', 'a shelf', 'a chest of drawers', 'a cabinet'],
    'vehicle': ['a car', 'a motorcycle', 'a boat', 'a bicycle', 'a ship', 'a wheel of a vehicle'],
    'handheld-prop': ['a cup', 'a mobile phone', 'a book', 'a letter', 'a musical instrument', 'a tambourine', 'a tool',
                      'a bottle', 'a lantern', 'a candle', 'a microphone', 'a suitcase', 'an hourglass', 'a photograph'],
    'wearable': ['a hat', 'a jacket', 'a pair of glasses', 'headphones', 'a ring', 'a necklace', 'a shoe', 'a piece of clothing'],
    'plant-nature': ['a tree', 'a flower', 'a palm tree', 'a bush', 'leaves', 'a tree stump', 'grass', 'a branch', 'rocks'],
    'light-fx': ['a soft glow of light', 'a light beam', 'smoke', 'haze or fog', 'sparks', 'rain', 'fire flames',
                 'a lens flare', 'a reflection shimmer', 'a translucent colour wash'],
    'text-graphic': ['printed text', 'a word written in letters', 'a sign with lettering', 'a label strip with words',
                     'a number', 'a graphic symbol'],
    'character-fragment': ['a hand', 'a person', 'a human figure', 'a face', 'an arm', 'a body part', 'a silhouette of a man',
                           'fingers'],
    'other': ['a mirror', 'a lamp', 'a chandelier', 'a speaker', 'a television', 'a machine', 'a box', 'a ring shaped disc',
              'an abstract shape', 'a piece of blank cardboard'],
}

# label lexicon (lower-case words -> class). Ambiguous words resolved by CONTEXT below.
LEX = {
    'backdrop': 'sky skyline skylines horizon backdrop backing backer backers gradient cityscape city view vista sea ocean landscape panorama valley '
                'hill hills mountain mountains treeline moon moons sun sunrise sunset star stars planet planets cloud clouds galaxy universe '
                'town aerial',
    'ground': 'floor floors parquet road roads ground path pavement paving tarmac asphalt sidewalk kerb curb driveway street causeway plaza '
              'carpet rug soil mud mound terrace deck sand shore beach water pool pools puddle ripple ripples wave waves tide quay '
              'field trail footprints footprint boards floorboards slope slopes waterline lake river harbor harbour equator',
    'architecture': 'wall walls building buildings facade tower towers roof column columns pillar pillars pier piers stair stairs '
                    'staircase step steps tread treads riser landing platform catwalk rail rails railing balustrade fence beam '
                    'beams joist ceiling house chapel temple church spire dome pediment portico vault belfry plinth pedestal '
                    'porch awning canopy bridge viaduct slab slabs block blocks course courses brick bricks cinderblock booth '
                    'shaft lightwell corridor hall container shopfront storefront kiosk mast post lamppost streetlamp '
                    'ruin rubble lobby nave choir atrium auditorium forum structure niche finial apse stoop pipework '
                    'escape cafe dam underpass perimeter cornice pole',
    'aperture': 'door doors doorway window windows gate gates arch arches archway portal opening openings aperture hatch '
                'trapdoor lancet lancets pane panes glazing sash mullion casement shutter shutters blinds blind curtain '
                'curtains threshold frame frames gateway doorpost',
    'furniture-seat': 'chair chairs armchair bench benches pew pews sofa couch bed stool seat seats mattress cushion pillow '
                      'kneeler throne headboard blanket',
    'furniture-surface': 'table tables desk counter shelf shelves bar dresser drawers drawer cabinet sideboard altar tray '
                         'nightstand',
    'vehicle': 'car sedan coupe motorcycle motorbike bike bicycle boat boats ship ships hull sail sails wheel wheels chassis '
               'handlebar handlebars headlight headlights axle spoke spokes spoked saddle train tram bus truck van canoe raft',
    'handheld-prop': 'cup cups mug bottle bottles phone phones handset receiver book books journal letter envelope envelopes '
                     'page pages snapshot photo photograph tambourine jingle jingles guitar instrument mic microphone tool key '
                     'keys coin coins vape lighter hourglass lantern candle candles gift gifts bread basket staff umbrella '
                     'controller remote record vinyl suitcase suitcases bag pen notebook map ticket glass glasses wine '
                     'cigarette match matches dish bowl jar can torch',
    'wearable': 'hat cap jacket hoodie coat dress scarf shoe shoes boot boots sunglasses headphones ring rings necklace pearls '
                'rosary mask veil crown glove gloves hem sleeve collar tie belt apron',
    'plant-nature': 'tree trees trunk branch branches leaf leaves palm palms vine vines bush bushes shrub flower flowers '
                    'blossom blossoms petal petals daisy poppy poppies rose roses grass weed weeds stump stumps root roots '
                    'garden planter pine moss bloom blooms stem hedge reeds rock rocks pebble pebbles vineyard grove forest '
                    'raven ravens bird birds cobweb cobwebs web webs',
    'light-fx': 'light lights glow ray rays haze fog mist smoke steam vapour vapor spark sparks ember embers flame flames fire '
                'rain drops droplets dew halo flare flash strobe sweep sweeps streak streaks shadow shadows reflection '
                'reflections sheen highlight glint lens bokeh gobo rainbow comet wisp wisps dust ash splash wavefront iris '
                'pulse gel glare beacon projection lightning storm wash shimmer sparkle neon wind',
    'text-graphic': 'text word words name names nameplate nameplates sign signs signage poster posters notice label glyph '
                    'glyphs digit digits number numeral emblem logo graffiti plaque placard tideboard chalk letters lettering amos otis mae cora ida',
    'character-fragment': 'hand hands arm arms finger fingers thumb head face eye eyes pupil brow mouth lips torso leg '
                          'legs foot feet sole shoulder poet man woman figure figures silhouette silhouettes ghost person '
                          'child brother mother elders ancestors kin wrist knuckle fingerprint marionette',
    'other': 'mirror lamp chandelier chandeliers speaker speakers television decks turntable meter clock bell disc orb cog '
             'cage basin basins laundry box boxes crate crates cord string strings tank fan screen puzzle mechanism bulb bulbs crystal '
             'wire cloth chain hinge handle knob wing wings',
}
WORD2C = {}
for c, ws in LEX.items():
    for w in ws.split():
        WORD2C.setdefault(w, c)

# words after these are modifiers of the head noun ('wall with window-well aperture' is a wall)
MODIFIER_START = {'with', 'for', 'behind', 'through', 'in', 'on', 'under', 'over', 'from', 'of', 'to', 'into', 'beneath', 'above',
                  'against', 'at', 'showing', 'holding', 'without'}
# words that are layout instructions / sheet headings, not content
HEADING = {'separate', 'parts', 'reference', 'only', 'assembled', 'assembly', 'example', 'examples', 'layout', 'sheet', 'cards',
           'card', 'independent', 'replacement', 'replacements', 'states', 'poem', 'layers', 'layer', 'optional', 'copy', 'not',
           'scene', 'insert', 'inserts', 'overlay', 'overlays', 'hang', 'offscreen', 'pcs', 'animation', 'instructions'}
STOP = {'the', 'and', 'a', 'an', 'left', 'right', 'front', 'back', 'rear', 'mid', 'middle', 'centre', 'center', 'top', 'bottom',
        'upper', 'lower', 'near', 'far', 'small', 'large', 'medium', 'tall', 'low', 'long', 'short', 'thin', 'wide', 'dark',
        'pale', 'white', 'black', 'grey', 'gray', 'blue', 'red', 'amber', 'warm', 'cold', 'cool', 'teal', 'cyan', 'gold',
        'cream', 'pink', 'green', 'orange', 'purple', 'violet', 'yellow', 'navy', 'brown', 'silver', 'side', 'one', 'two',
        'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'half', 'full', 'empty', 'open', 'closed', 'broken',
        'blank', 'plain', 'soft', 'dim', 'lit', 'unlit', 'edge', 'end', 'piece', 'part', 'shape', 'strip', 'panel', 'band', 'line',
        'lines', 'plate', 'set', 'base', 'inner', 'outer', 'each', 'same', 'whole', 'new', 'old', 'aged', 'state'}


def words(t):
    return re.findall(r'[a-z]{3,}', (t or '').lower().replace('_', ' '))


def label_text(p):
    lab, nm = p.get('label') or '', p.get('name') or ''
    t = lab if len(words(lab)) >= len(words(nm)) else nm
    return t


ROLE = {'floor', 'floors', 'backer', 'backing', 'backdrop', 'sky', 'road', 'ground'}


def label_vote(text):
    """Returns ({class: weight}, [(word, class, weight)]).
    The label is cut into phrases at modifier prepositions ('with', 'for', 'behind' ...) and '('. The first phrase is
    the head phrase (weight 1.0), later phrases weigh 0.35 ('(' 0.5). Inside a phrase the LAST lexicon word is the
    head noun (English compounds: 'harbor sun' is a sun, 'pier lamp' a lamp) and keeps the full weight; earlier
    lexicon words in the same phrase get half."""
    t = re.sub(r'([A-Za-z])\.([A-Za-z0-9])', r'\1 \2', text or '')
    t = re.sub(r'([a-z])-([a-z])', r'\1 \2', t, flags=re.I)
    toks = re.findall(r'[A-Za-z]+|\(|\)', t)
    phrases, cur, w = [], [], 1.0
    for tok in toks:
        if tok in '()' or tok.lower() in MODIFIER_START:
            if cur: phrases.append((w, cur)); cur = []
            w = min(w, 0.5) if tok == '(' else (w if tok == ')' else 0.35)
            continue
        lw = tok.lower()
        if lw in HEADING or lw in STOP or len(lw) < 3:
            continue
        stem = lw if lw in WORD2C else (lw[:-1] if lw.endswith('s') and lw[:-1] in WORD2C else None)
        if stem:
            cur.append((lw, WORD2C[stem]))
    if cur: phrases.append((w, cur))
    votes, used = Counter(), []
    for w, ph in phrases:
        for i, (lw, c) in enumerate(ph):
            # role words name the piece's job on the stage and keep full weight wherever they sit in the phrase
            ww = w if (i == len(ph) - 1 or lw in ROLE) else w * 0.5
            votes[c] += ww
            used.append((lw, c, ww))
    return votes, used


def is_heading_label(text):
    ws = words(text)
    return bool(ws) and sum(x in HEADING for x in ws) >= max(1, 0.5 * len(ws))


def softmax(x, t=100.):
    z = np.exp((x - x.max()) * t)
    return z / z.sum()


# CONTEXT rules (inferred from reading sheets; each one is applied and recorded by name)
def context(sid, title, votes, used):
    notes = []
    fx_sheet = '.fx.' in sid
    # 'beam'/'ring'/'cloud'/'star'/'disc' on an fx sheet are light effects, not structure / jewellery / sky
    if fx_sheet:
        for wd, c, wt in used:
            if c in ('architecture', 'wearable', 'backdrop', 'other', 'aperture') and wd in (
                    'beam', 'beams', 'ring', 'rings', 'cloud', 'clouds', 'star', 'stars', 'disc', 'iris', 'window', 'sky'):
                votes[c] -= wt; votes['light-fx'] += wt
                notes.append(f"fx-sheet: '{wd}' read as light-fx")
    # 'glass' is window glass on aperture-heavy labels, a drinking glass otherwise
    for wd, c, wt in used:
        if wd in ('glass', 'glasses') and (votes.get('aperture', 0) > 0 or 'window' in sid or 'mirror' in ' '.join(x for x, _, _ in used)):
            votes[c] -= wt; votes['aperture' if 'mirror' not in ' '.join(x for x, _, _ in used) else 'other'] += wt
            notes.append(f"'{wd}' with window/mirror context -> pane")
        if wd == 'palm' and any(x in ('finger', 'fingers', 'thumb', 'hand', 'wrist') for x, _, _ in used + [(w, 0, 0) for w in words(sid)]):
            votes[c] -= wt; votes['character-fragment'] += wt
            notes.append("'palm' with hand context -> hand")
        allw = set(x for x, _, _ in used) | set(words(sid)) | set(words(title))
        body_ctx = bool(allw & {'hands', 'hand', 'poet', 'eye', 'jointed', 'fingerprint', 'footprints', 'aperture'}) and \
            not bool(allw & {'clock', 'clocktower', 'hour', 'minute', 'chandeliers', 'chandelier', 'candle', 'road'})
        if c == 'character-fragment' and not body_ctx:
            to = 'other'
            if wd == 'shoulder' and ('road' in allw or '.set.' in sid): to = 'ground'
            if wd in ('poet', 'man', 'woman', 'figure', 'silhouette', 'silhouettes', 'ghost', 'person'): to = None
            votes[c] -= wt
            if to: votes[to] += wt
            notes.append(f"'{wd}' without a body/hand sheet context -> {to or 'no vote (a name, not a class)'}")
        if wd in ('sole', 'foot', 'pad') and 'stamp' in allw:
            votes[c] -= wt; votes['ground'] += wt
            notes.append(f"'{wd} stamp' is a footprint stamp -> ground mark")
        if wd in ('leaf', 'leaves') and (allw & {'door', 'doors', 'gate', 'gates', 'shutter', 'marquee', 'window', 'hinge'}):
            votes[c] -= wt; votes['aperture'] += wt
            notes.append("'leaf' with door/gate context -> door leaf")
        if wd == 'lamp' and allw & {'town', 'street', 'pier', 'post', 'streetlamp', 'quay'}:
            votes[c] -= wt; votes['architecture'] += wt
            notes.append("street/pier/town lamp -> architecture (street furniture)")
        if wd in ('frame', 'frames') and any(x == 'mirror' for x, _, _ in used):
            votes[c] -= wt; votes['other'] += wt
            notes.append("'frame' of a mirror -> other (mirror)")
    return {k: v for k, v in votes.items() if v > 1e-6}, notes


SHEET_HINT = {  # sheet slug words that name what the whole sheet is (weak prior)
    'chandeliers': 'other', 'car': 'vehicle', 'bike': 'vehicle', 'motorcycle': 'vehicle', 'boats': 'vehicle',
    'hands': 'character-fragment', 'tambourine': 'handheld-prop', 'phone': 'handheld-prop', 'journal': 'handheld-prop',
    'hourglass': 'handheld-prop', 'letters': 'handheld-prop', 'window': 'aperture', 'door': 'aperture', 'trapdoor': 'aperture',
    'chair': 'furniture-seat', 'pews': 'furniture-seat', 'furniture': 'furniture-seat', 'cafe': 'architecture',
    'words': 'text-graphic', 'names': 'text-graphic', 'notice': 'text-graphic', 'sign': 'text-graphic',
    'cobwebs': 'plant-nature', 'blooms': 'plant-nature', 'tree': 'plant-nature', 'stumps': 'plant-nature',
    'flower': 'plant-nature', 'field': 'ground', 'road': 'ground', 'shore': 'ground', 'skyline': 'backdrop',
    'void': 'backdrop', 'sea': 'backdrop', 'haze': 'light-fx', 'light': 'light-fx', 'lights': 'light-fx',
    'fog': 'light-fx', 'storm': 'light-fx', 'comet': 'light-fx', 'chapel': 'architecture', 'temple': 'architecture',
    'house': 'architecture', 'viaduct': 'architecture', 'steps': 'architecture', 'clocktower': 'architecture',
    'speakers': 'other', 'decks': 'other', 'basins': 'other', 'laundry': 'other', 'suitcases': 'handheld-prop',
    'lantern': 'handheld-prop', 'candle': 'handheld-prop', 'guitar': 'handheld-prop', 'mic': 'handheld-prop',
    'personal': 'wearable', 'gifts': 'handheld-prop', 'bread': 'handheld-prop', 'cups': 'handheld-prop', 'mirror': 'other',
    'phonebooth': 'architecture', 'snapshot': 'handheld-prop', 'reel': 'other', 'party': 'other', 'projection': 'light-fx',
}


def sheet_prior(sid, title):
    v = Counter()
    for w in words(sid.split('.', 2)[-1]):
        if w in SHEET_HINT: v[SHEET_HINT[w]] += 1
    if '.fx.' in sid: v['light-fx'] += 1
    return v


def clean_name(text):
    t = re.sub(r'([A-Za-z])\.([A-Za-z0-9])', r'\1 \2', text or '')
    t = re.sub(r'\(#?[0-9A-Fa-f]{6}\)', '', t)
    toks = re.findall(r"[A-Za-z][A-Za-z'\-]*|\([^)]*\)", t)
    keep = []
    for x in toks:
        lx = x.lower().strip('()')
        if re.fullmatch(r'[a-z]{0,2}\d*', lx) or lx in HEADING:
            continue
        if re.fullmatch(r'[a-z]*\d+[a-z0-9]*', lx):  # codes like w04, co1, c02
            continue
        keep.append(x.lower())
    # drop a repeated code word ('wall l left wall' -> 'left wall'); collapse dups
    out = []
    for x in keep:
        if x in ('l', 'r'):
            continue
        if out and out[-1] == x:
            continue
        out.append(x)
    s = ' '.join(out).strip()
    # many labels are 'CODE descriptive phrase' where the code word repeats in the phrase: keep the phrase
    ws = s.split()
    if len(ws) > 2 and ws[0] in ws[1:]:
        s = ' '.join(ws[1:])
    return s[:90]


RULE_CHANGES = [
    "v1 zero-shot used the normalized mean of each class's prompts; v2 uses the best prompt per class (label agreement 453 -> 505 of 1338 label-classed cards, measured).",
    "added a kNN witness (7 nearest label-classed cards in CLIP image space): leave-one-out agreement with labels 69% vs 38% for zero-shot (measured); cross-sheet only 42%.",
    "viewed contact_charfrag: chandelier 'ARM', clock 'hour/minute hand', road 'shoulder', sign 'leg' were called body parts -> body words only count as character-fragment on hand/poet/eye/footprint sheets; else other (road shoulder -> ground; 'poet'/'silhouette' -> no vote).",
    "viewed contact_conflict: 'harbor sun' voted ground, 'pier lamp' architecture -> head noun is the LAST lexicon word in a phrase (English compounds); role words floor/backer/backing/sky/road keep full weight.",
    "viewed contact_conflict: a door labelled '(separate leaf)' was plant -> 'leaf' with door/gate/marquee/window context is a door leaf (aperture).",
    "viewed contact_nolabel/text: printed sheet words (LAYERS, SURROUND, PARTS, FIELD) cut as cards -> hygiene pixel test (thin strokes / text strip / scattered) adds text-graphic, full weight only if CLIP top-3 also has text-graphic (blue water drips were being called text); such unlabeled/heading lettering is flagged skip.",
    "viewed contact_furniture-seat: 'ARMCHAIR BODY' was pulled to other by 'body' -> 'body' removed from the body lexicon.",
    "viewed contact_other: comet cards on fx sheets called other -> fx sheet with no label class gets +0.5 light-fx; town/pier/street lamp -> architecture.",
    "labels containing reference/assembled/example are flagged and skipped (assembly views cut as cards).",
]


def main():
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    reg = json.load(open(os.path.join(CUT, 'registry.json')))['parts']
    z = np.load(os.path.join(HERE, 'emb_img.npz'), allow_pickle=True)
    emb = dict(zip(z['ids'].tolist(), z['emb']))

    import sys
    sys.path.insert(0, os.path.join(ROOT, 'shots/scion2/evolve/puzzle'))
    tcache = os.path.join(HERE, 'emb_txt.npz')
    key = json.dumps(PROMPTS, sort_keys=True)
    T = None
    if os.path.exists(tcache):
        zt = np.load(tcache, allow_pickle=True)
        if str(zt['key']) == key: T = zt['T']
    if T is None:
        import hygiene as H
        T = np.stack([H._txt([PFX + s for s in PROMPTS[c]]) for c in CLASSES], 0) if False else \
            np.array([H._txt([PFX + s for s in PROMPTS[c]]) for c in CLASSES], dtype=object)
        np.savez(tcache, T=T, key=key)
    # zero-shot score per class = best prompt of that class (max beat a normalized prompt mean: 505 vs 453 of 1338
    # label-classed cards agree with CLIP top-1; measured in the step-2 experiment, see README in summary)
    def zs(e):
        return np.array([float((t @ e).max()) for t in T])

    # pixel tests (measured; hygiene.pixel_tests: blank plate / thin strokes / text strip / scattered blobs), cached
    import cv2
    cv2.setNumThreads(1)
    import hygiene as HY
    pcache = os.path.join(HERE, 'pixel_tests.json')
    PX = json.load(open(pcache)) if os.path.exists(pcache) else {}
    for sid, S in cat.items():
        if not any(t in sid for t in TAGS): continue
        for p in S['parts']:
            if p['kind'] == 'card' and p['id'] not in PX:
                im = cv2.imread(os.path.join(CUT, p['file']), cv2.IMREAD_UNCHANGED)
                if im is not None and im.ndim == 3 and im.shape[2] == 4:
                    PX[p['id']] = HY.pixel_tests(im)
                else:
                    PX[p['id']] = None
    json.dump(PX, open(pcache, 'w'), indent=0)

    # pre-pass: label class of every card, for the kNN witness (label propagation over CLIP image space)
    pre = {}
    for sid, S in cat.items():
        if not any(t in sid for t in TAGS): continue
        for p in S['parts']:
            if p['kind'] != 'card' or p['id'] not in emb: continue
            v, u = label_vote(label_text(p)); v, _ = context(sid, S.get('title') or '', Counter(v), u)
            if v: pre[p['id']] = max(v, key=v.get)
    kid = list(pre); KE = np.stack([emb[k] for k in kid]); KL = np.array([CLASSES.index(pre[k]) for k in kid])

    def knn(pid, e, k=7):
        g = KE @ e
        if pid in pre: g[kid.index(pid)] = -9
        nn = np.argsort(-g)[:k]
        v = np.zeros(len(CLASSES))
        for j in nn: v[KL[j]] += np.exp(20 * g[j])
        v /= v.sum()
        return v, [[kid[j], pre[kid[j]], round(float(g[j]), 3)] for j in nn[:3]]

    # scenes from shots/stage/sets (measured: which parts each staged location references / which sheets it cuts from)
    stage = {}
    part_scenes = defaultdict(set)
    for f in sorted(glob.glob(os.path.join(ROOT, 'shots/stage/sets/*.json'))):
        d = json.load(open(f))
        sidk = os.path.basename(f)[:-5]
        refs = set()
        def walk(o):
            if isinstance(o, dict):
                if o.get('kind') == 'part' and o.get('part'): refs.add(o['part'])
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk({k: d.get(k) for k in ('bands', 'pieces', 'fx', 'reuse')})
        stage[sidk] = {'id': sidk, 'poem': d.get('poem'), 'name': d.get('name'), 'look': d.get('look'),
                       'interior': d.get('interior'), 'void': d.get('void'), 'cut_sheets': d.get('cut_sheets') or [],
                       'staged_parts': sorted(refs)}

    sheets_in_stage = defaultdict(list)
    for k, s in stage.items():
        for sh in s['cut_sheets']: sheets_in_stage[sh].append(k)
        for pid in s['staged_parts']: part_scenes[pid].add(k)

    parts = {}
    for sid, S in cat.items():
        if not any(t in sid for t in TAGS):
            continue
        title = S.get('title') or ''
        sp = sheet_prior(sid, title)
        for p in S['parts']:
            pid = p['id']
            r = reg.get(pid, {})
            rec = {'sheet': sid, 'poems': S.get('poems'), 'folder': S.get('folder'), 'sheet_title': title,
                   'label': p.get('label'), 'catalog_name': p.get('name'), 'kind': p['kind'],
                   'registry': {'place': r.get('place'), 'q': r.get('q'), 'why': r.get('why')}}
            for sh_scene in sheets_in_stage.get(sid, []):
                part_scenes[pid].add(sh_scene)
            if p['kind'] == 'ref':
                rec.update({'final': {'category': 'reference-panel', 'name': clean_name(label_text(p)) or 'reference panel',
                                      'confidence': 1.0, 'conflict': False, 'skip': True,
                                      'why': 'catalog kind=ref (measured): an assembly/reference panel, never place'}})
                parts[pid] = rec
                continue
            text = label_text(p)
            votes, used = label_vote(text)
            votes, cnotes = context(sid, title, Counter(votes), used)
            pxt = PX.get(pid)
            if pxt and pxt.split()[0] in ('thin', 'scattered', 'text') and '.fx.' not in sid:
                pix_tg = 1.0  # scaled below by whether CLIP also sees text
                cnotes.append(f'pixel test: {pxt} -> text-graphic +1.0 in fusion (+0.3 if CLIP top-3 lacks text-graphic)')
            else:
                pix_tg = 0.0
            e = emb.get(pid)
            if e is not None:
                sims = zs(e)
                prob = softmax(sims)
                kv, kn = knn(pid, e)
                order = np.argsort(-prob)
                top3 = [[CLASSES[i], round(float(prob[i]), 3)] for i in order[:3]]
                clip_top = CLASSES[order[0]]
            else:
                prob = np.full(len(CLASSES), 1 / len(CLASSES)); top3 = []; clip_top = None
                kv, kn = np.zeros(len(CLASSES)), []
            if '.fx.' in sid and not votes:
                snorm_fx = 0.5
                cnotes.append('fx sheet, no label class: +0.5 light-fx')
            else:
                snorm_fx = 0.0
            if pix_tg and not any(c == 'text-graphic' for c, _ in top3):
                pix_tg = 0.3
            lsum = sum(votes.values())
            lnorm = {c: v / lsum for c, v in votes.items()} if lsum else {}
            ssum = sum(sp.values())
            snorm = {c: v / ssum for c, v in sp.items()} if ssum else {}
            fused = np.array([1.0 * lnorm.get(c, 0) + 0.3 * snorm.get(c, 0) + 0.7 * prob[i] + 0.6 * kv[i] + (pix_tg if c == 'text-graphic' else 0) + (snorm_fx if c == 'light-fx' else 0) for i, c in enumerate(CLASSES)])
            fo = np.argsort(-fused)
            cat_final = CLASSES[fo[0]]
            share = float(fused[fo[0]] / fused.sum())
            label_top = max(lnorm, key=lnorm.get) if lnorm else None
            conflict = bool(label_top and clip_top and label_top != clip_top)
            heading = is_heading_label(text)
            conf = share
            if not label_top: conf *= 0.7
            if conflict: conf *= 0.8
            if heading: conf *= 0.6
            flags = []
            if pxt: flags.append('pixel test: ' + pxt)
            if heading: flags.append('label reads like a sheet heading/instruction, not a part name')
            refword = bool(set(words(text)) & {'reference', 'assembled', 'example', 'examples'})
            lettering = cat_final == 'text-graphic' and bool(pxt) and pxt.split()[0] in ('thin', 'scattered', 'text') and \
                (not label_top or heading)
            if lettering: flags.append('sheet lettering cut as a card (printed heading word), not a prop sign')
            if refword: flags.append('label says reference/assembled/example: likely an assembly view cut as a card')
            if not words(text): flags.append('no readable label')
            if cat_final == 'character-fragment': flags.append('person/body part: not a set piece')
            if cat_final == 'text-graphic': flags.append('text/graphic: check it is a real prop sign, not a label strip')
            if r.get('q') == 'C': flags.append('registry grade C (do not place): ' + ', '.join(r.get('why') or []))
            nm = clean_name(text)
            name_src = 'label'
            if len(words(nm)) == 0:
                nm = clean_name(p.get('name') or '')
                name_src = 'catalog name'
            if len(words(nm)) == 0:
                nm = f"{cat_final} ({title.lower() or sid})"
                name_src = 'category + sheet title (no readable label)'
            rec.update({
                'pixel_test': pxt,
                'label_words': [[w, c, round(wt, 2)] for w, c, wt in used],
                'label_votes': {c: round(v, 2) for c, v in sorted(votes.items(), key=lambda x: -x[1])},
                'context_rules': cnotes,
                'sheet_prior': dict(sp),
                'clip_top3': top3,
                'knn_label_vote': {CLASSES[i]: round(float(kv[i]), 2) for i in np.argsort(-kv)[:3] if kv[i] > 0.01},
                'knn_nearest_labelled': kn,
                'clip_p_label_class': round(float(prob[CLASSES.index(label_top)]), 3) if label_top else None,
                'fused_top3': [[CLASSES[i], round(float(fused[i]), 3)] for i in fo[:3]],
                'final': {'category': cat_final, 'name': nm, 'name_src': name_src, 'confidence': round(conf, 3),
                          'conflict': conflict, 'label_class': label_top, 'clip_class': clip_top,
                          'skip': cat_final in ('character-fragment',) or (heading and cat_final == 'text-graphic') or refword or lettering,
                          'review': conf < 0.3 or (conflict and conf < 0.4),
                          'flags': flags},
            })
            parts[pid] = rec

    # scenes list: staged locations (measured from shots/stage/sets) + per-sheet pools for sheets no stage set uses
    scenes = []
    for k, s in stage.items():
        members = set(pid for pid in s['staged_parts'] if pid in parts)
        for sh in s['cut_sheets']:
            members |= {pid for pid, r in parts.items() if r['sheet'] == sh and r['kind'] == 'card'}
        if not members:
            continue
        scenes.append({'id': 'stage:' + k, 'kind': 'staged location', 'poem': s['poem'], 'name': s['name'], 'look': s['look'],
                       'interior': s['interior'], 'cut_sheets': s['cut_sheets'],
                       'source': 'shots/stage/sets/%s.json (cut_sheets + every part referenced in bands/pieces/fx) [measured]' % k,
                       'by_category': dict(Counter(parts[m]['final']['category'] for m in members)),
                       'parts': sorted(members)})
    for sid, S in cat.items():
        if not any(t in sid for t in TAGS):
            continue
        pids = sorted(pid for pid, r in parts.items() if r['sheet'] == sid and r['kind'] == 'card')
        staged = sorted({sc for pid in pids for sc in part_scenes.get(pid, ())})
        scenes.append({'id': 'sheet:' + sid, 'kind': 'sheet group (same sheet = same poem, same location/prop family)',
                       'poem': (S.get('poems') or [None])[0], 'poems': S.get('poems'), 'name': S.get('title'),
                       'location_slug': sid.split('.', 2)[-1], 'staged_in': staged,
                       'source': 'catalog sheet + title [measured]; catalog scene field is null for every set piece [measured]',
                       'by_category': dict(Counter(parts[m]['final']['category'] for m in pids)), 'parts': pids})
    for pid, r in parts.items():
        r['scenes'] = sorted(part_scenes.get(pid, ()))

    cards = [r for r in parts.values() if r['kind'] == 'card']
    summary = {
        'set_piece_sheets': len({r['sheet'] for r in parts.values()}), 'parts': len(parts), 'cards': len(cards),
        'refs_skipped': len(parts) - len(cards),
        'clip_embedded': sum(1 for r in cards if r['clip_top3']),
        'category': dict(Counter(r['final']['category'] for r in cards).most_common()),
        'conflicts': sum(r['final']['conflict'] for r in cards),
        'no_label_class': sum(1 for r in cards if not r['final']['label_class']),
        'label_clip_agree': sum(1 for r in cards if r['final']['label_class'] and r['final']['label_class'] == r['final']['clip_class']),
        'low_confidence_lt_0.35': sum(1 for r in cards if r['final']['confidence'] < 0.35),
        'review': sum(1 for r in cards if r['final']['review']),
        'skip': sum(1 for r in cards if r['final']['skip']),
        'heading_labels': sum(1 for r in cards if any('heading' in f for f in r['final']['flags'])),
        'staged_scenes': sum(1 for s in scenes if s['kind'] == 'staged location'),
        'parts_in_a_staged_scene': sum(1 for r in cards if r['scenes']),
    }
    out = {'about': __doc__, 'taxonomy': CLASSES, 'clip_prompts': PROMPTS, 'clip_prompt_prefix': PFX,
           'evidence_levels': {'label_words/label_votes/sheet_prior/clip_top3/registry/scenes': 'measured',
                               'final.category/name/confidence/conflict/skip': 'inferred (fusion rule in about)'},
           'rule_changes_after_viewing': RULE_CHANGES,
           'summary': summary, 'parts': parts, 'scenes': scenes}
    json.dump(out, open(OUT, 'w'), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
