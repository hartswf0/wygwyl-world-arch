"""Pass 3: rules -> shots/scion2/setpieces/hygiene.json (every set piece, refs included) + audit contact sheets.
Every defect carries {kind, value, evidence, basis: measured|viewed|inferred, severity: C (blocks use) | B (usable, check/fix)}.
Inputs: cache/measure.json (measure.py), cache/clip_scores.json + clip_img.npy (clipscore.py / measure.py),
shots/kits/cut/catalog.json, registry.json. Run: python3 decide.py [--sheets]"""
import json, os, re, sys
from collections import Counter, defaultdict
import numpy as np
from common import setpieces, CACHE, CUT, HERE, contact

OUT = os.path.abspath(os.path.join(HERE, '..', 'hygiene.json'))
AUDIT = os.path.join(HERE, 'audit')
os.makedirs(AUDIT, exist_ok=True)

THIN_OK = r'pulse|ring|circle|hoop|orbit|wire|thread|string|cord|rail|line|beam|ray|streak|crack|horizon|rod|pole|strip|kerb|curb|edge|seam|rope|cable|branch|lightning|ripple|trail|band|stroke|stem|chain|ribbon|lash|needle|stick|bar|beam|spoke|hand|tick|arc|crease|glint|shaft|tail|wisp|sweep|smoke|steam|haze|mist|vapou?r|flare|spark|scratch|mullion|lead|cane|reed|twig|sill|lintel|frame|pipe|cue|wand|track|road|path|shelf|plank|board|leg|bead|filament|glow|light|sheen|heat|air|fog|tread|step|wave|water|tide|surf'
SCATTER = r'dash|dashes|arc\b|ripples|ink\b|fleck|ash|dust|seed|shard|petal|star|rain|spark|letters?|cards|confetti|crumb|leaves|stones|pebbles|drops|droplets|bubbles|embers|flakes|snow|glints|words|birds|moths|pieces|scatter|cluster|\(\d+|\bx\d|\d+ ?x\b|pair|set\b|row|stack|beads|chain|dots|holes|sparks|feathers|coins|keys|books|bottles|cups|mugs|candles|lights|lamps|windows|bulbs|string'
# v3 (viewed audit/defect_body_part_label): arm/body/leg/head/ear/silhouette/poet named furniture & props (couch arm,
# phone body, table leg, headphone ear, skyline silhouette, 'poet' in long ids); keep only unambiguous puppet-joint words
BODY_WORDS = r'\b(fingers?|thumbs?|palm|wrists?|shoulders?|elbows?|knees?|thighs?|forearms?|upper ?arm|lower ?arm|shin|calf|ankle|torso|hips?|brow|lips|mouth|jaw|hand (l|r)|(left|right) hand|hand\.(l|r))\b'
OBJ_HANDWORDS = r'print|glove|statue|sculpture|mannequin|clock|dial|gauge|watch|sign|stamp|mould|mold|cast|carv|icon|emblem|chair|table|leg (of|rest)|table ?leg|chair ?leg|bed|bench|stool|piano|shape|shadow|reflection|outline|window|poster|photo|portrait|painting|picture|mural|statue'
REF_WORDS = r'\b(reference|assembled|assembly|separate|proof|state ?proof|composite|key|legend|notes?|only|example|diagram|layout|arrangement|cards? ?\)|\(\d+ cards|insert|view\)|number strip|label|title|heading)\b'
# v2: matched against the sheet id + the part's own label/name only; 'card' removed (it matched '(3 CARDS)' caption strips)
WORD_SHEET = r'word|letter|journal|poem|text|notice|book|page|plaque|star-names|name\d|names'


def nested_share(p):
    import cv2
    from common import load_rgba
    a = (load_rgba(p)[..., 3] > 128).astype(np.uint8)
    k, lab, st, _ = cv2.connectedComponentsWithStats(a, connectivity=8)
    if k < 3:
        return 0.
    # v4: the container is the component with the largest box (a thin outline loop has little area but the biggest box)
    mi = 1 + int(np.argmax(st[1:, 2] * st[1:, 3]))
    x, y, w, h = st[mi, :4]
    tot = ins = 0
    for j in range(1, k):
        if j == mi:
            continue
        cx, cy = st[j, 0] + st[j, 2] / 2, st[j, 1] + st[j, 3] / 2
        tot += st[j, 4]
        ins += st[j, 4] * (x <= cx <= x + w and y <= cy <= y + h)
    return ins / max(1, tot)


def hamming(a, b):
    return int(np.count_nonzero(a != b))


def bits(s):
    return np.frombuffer(s.encode(), np.uint8) - 48


def lab_text(p):
    return ' '.join([p.get('name') or '', p.get('label') or '', p['id'].split('/')[1].replace('-', ' ')]).lower()


def judge(p, m, c, reg):
    D = []                                       # defects
    txt = lab_text(p)
    place = reg.get('place')

    def add(kind, value, evidence, basis, sev):
        D.append({'kind': kind, 'value': value, 'evidence': evidence, 'basis': basis, 'severity': sev})

    if p['kind'] == 'ref':
        add('reference_panel', p.get('ref_reason'), "catalog kind 'ref' (cutter/fix_cut): " + str(p.get('ref_reason')), 'inferred', 'C')
    if m.get('empty') or m['area'] < 400 or min(m['w'], m['h']) < 10:
        add('tiny', m['area'], 'alpha px=%d, box %dx%d' % (m['area'], m['w'], m['h']), 'measured', 'C')
    if m.get('empty'):
        return D
    n, w, h = m['area'], m['w'], m['h']
    # ---- text / label strips -------------------------------------------------------------------------------
    tmarg = c['text'] - c['object']
    # v3 (viewed audit/defect_label_strip): black objects (platters, vinyl, handset, film strip, sunglasses) passed the old
    # test (low chroma + dark ink); printed words are fully achromatic AND carry a white outline/paper (body_pale >= .08)
    lettering = m['low_chroma'] >= .95 and m['ink_dark'] >= .1 and m['body_pale'] >= .08
    refword = re.search(REF_WORDS, (p.get('label') or '').lower())
    word_sheet = re.search(WORD_SHEET, p['sheet'] + ' ' + ((p.get('name') or '') + ' ' + (p.get('label') or '')).lower())
    caption = re.search(r'\(\s*\d+\s*cards?\s*\)|reference only|assembly example|\(\s*\d+\s*parts?\b', (p.get('label') or '').lower())
    # v3: needs CLIP text > objects -- painted haze/water strips whose cutter label read a '(3 cards)' heading are art
    if p['kind'] != 'ref' and caption and tmarg > 0:
        # v2: a printed caption card ('HEADLIGHT STREAKS (3 CARDS)') -- the label the cutter read IS the card's text
        add('label_strip', caption.group(0), "label '%s' is a sheet caption; strip aspect %.1f, CLIP text-object %.3f" % (p.get('label'), max(w, h) / min(w, h), tmarg), 'measured', 'C')
    elif p['kind'] != 'ref':
        if tmarg > 0 and lettering and not word_sheet:
            add('label_strip', round(tmarg, 3), "CLIP '%s' beats best object prompt by %.3f; lettering: %.0f%% low-chroma px, %d blobs >=1%%, %.0f%% near-black"
                % (c['text_best'], tmarg, 100 * m['low_chroma'], m['n_comp_1pct'], 100 * m['ink_dark']), 'measured', 'C')
        elif tmarg > .005 and refword and not word_sheet:
            add('label_strip', round(tmarg, 3), "CLIP '%s' +%.3f over objects and the label says '%s'" % (c['text_best'], tmarg, refword.group(0)), 'measured', 'C')
        elif tmarg > .015 and lettering:
            add('text_card', round(tmarg, 3), "lettering on a words/letters sheet (CLIP text +%.3f); a word card by design, not a set object" % tmarg, 'measured', 'B')
        elif tmarg > .01 and not word_sheet and m['n_comp_1pct'] >= 3 and m['low_chroma'] > .4:
            add('label_strip', round(tmarg, 3), "CLIP text +%.3f, %d separate blobs, %.0f%% low chroma" % (tmarg, m['n_comp_1pct'], 100 * m['low_chroma']), 'measured', 'C')
        if refword and re.search(r'reference|assembled|proof|composite|example|arrangement', refword.group(0)):
            add('reference_label', refword.group(0), "card label '%s' names it a reference/assembly view" % p.get('label'), 'inferred', 'C')
    # ---- components: several objects / satellites ---------------------------------------------------------
    cf = m.get('comp_fracs', [1.])
    second = cf[1] if len(cf) > 1 else 0.
    rest = 1 - cf[0]
    scatter = re.search(SCATTER, txt) or '.fx.' in p['sheet'] and re.search(r'haze|smoke|cloud|mist|fog|glow|ray|light', txt)
    if m['n_comp_5pct'] >= 2 and second >= .12 * cf[0]:
        # v2 (viewed basins water cards): islands that sit inside the main component's box are one drawn object
        nested = nested_share(p)
        kind = 'several_pieces_by_design' if scatter or nested >= .9 else 'several_objects'
        add(kind, m['n_comp_5pct'], '%d components >=5%% of alpha; sizes %s; %.0f%% of the other islands lie inside the main box%s'
            % (m['n_comp_5pct'], cf[:6], 100 * nested, '; label reads as a scatter/set' if scatter else ''), 'measured', 'B' if kind != 'several_objects' else 'C')
    elif rest >= .004:
        ink = m.get('sat_ink', 0)
        if ink > .25 and not scatter:
            add('baked_caption', round(rest, 3), 'separate blobs = %.1f%% of alpha, %.0f%% of them near-black ink (printed label/number beside the object)' % (100 * rest, 100 * ink), 'measured', 'B')
        elif not scatter:
            add('satellites', round(rest, 3), '%d extra blobs = %.1f%% of alpha (keep the main component)' % (m['n_comp'] - 1, 100 * rest), 'measured', 'B')
    # ---- slivers / fragments / paper chunks ----------------------------------------------------------------
    thin = m['erode5'] < .2 or min(w, h) < 14
    thin_ok = re.search(THIN_OK, txt) or place in ('band', 'fx', 'sky')
    if thin and not any(d['kind'] == 'tiny' for d in D):
        if thin_ok:
            add('thin_by_design', m['erode5'], '%.0f%% survives a 5px erosion, min side %d; label/place says a line-like object' % (100 * m['erode5'], min(w, h)), 'measured', 'B' if n < 1500 else 'A')
        else:
            add('sliver', m['erode5'], '%.0f%% survives a 5px erosion, min side %d, alpha %d px, no line-like word in the label' % (100 * m['erode5'], min(w, h), n), 'measured', 'C')
    smarg = c['scrap'] - c['object']
    # v2 (viewed): at > .45 this caught glass panes, marble columns, heat ripples, lightning; only near-all-paper blobs are chunks
    if m['body_pale'] > .9 and smarg > -.01 and not re.search(r'glass|glazing|pane|column|blind|ripple|lightning|paper|page|letter|card|cloud|snow|moon|cloth|sheet|sail|plaster|marble|bone|ghost|steam|mist|fog|haze|light|glow|white|swan|egg|plate', txt):
        add('paper_chunk', round(m['body_pale'], 3), "%.0f%% pale low-saturation px; CLIP '%s' +%.3f over objects" % (100 * m['body_pale'], c['scrap_best'], smarg), 'measured', 'C')
    # ---- straight clipped edges ----------------------------------------------------------------------------
    S = m['sides']
    # v4 (viewed blocked_cards: film frames): a frame's hole lowers plain fill; use the hole-filled silhouette
    sfill = m['fill'] / max(.05, 1 - m['hole_frac'])
    straight = [k for k, s in S.items() if s['run'] >= .6]
    # v2 (after viewing audit/explore_clipped): dE < 9 missed a corner-cut crackle-glass panel at dE 17; 20 still keeps
    # framed/outlined cards out (their border makes dE 30-170). Also: a corner clip = two adjacent sides fully straight while
    # the other two are organic.
    through = [k for k in straight if S[k].get('dE_in', 99) < 20 and S[k].get('edge_dark', 0) < .5 and S[k].get('edge_pale', 0) < .5]
    full = [k for k, s in S.items() if s['run'] >= .9]
    loose = [k for k, s in S.items() if s['run'] < .3]
    corner = len(full) == 2 and len(loose) == 2 and set(full) not in ({'top', 'bottom'}, {'left', 'right'}) and sfill < .75
    if corner:
        through = sorted(set(through) | set(full))
    rect = len(straight) == 4 and sfill > .9
    exempt = place in ('band', 'sky') or re.search(r'sky|sea|strip|band|floor|ground|wall|water|road|street|backdrop|back ?drop|panel|horizon|plane|base|bg|background|curtain|screen|rug|carpet|mat\b', txt)
    sheet_edge = m['touch_sheet']
    if sheet_edge:
        add('sheet_edge', sheet_edge, 'bbox %s touches the sheet border (%s) of a %s sheet' % (p['bbox'], ','.join(sheet_edge), p.get('sheet_size')), 'measured', 'B' if exempt or rect else 'C' if len(sheet_edge) >= 1 and through else 'B')
    if through and not rect:
        ev = '; '.join('%s: %.0f%% straight run, paint continues (dE %.1f between edge and 3-6px in)' % (k, 100 * S[k]['run'], S[k]['dE_in']) for k in through)
        # v2 (viewed): only the corner clip pattern was a real clip at C; other straight painted sides were temple bases,
        # tunnel frames, film frames -> B (check)
        add('clipped_edge', through, ('corner clip; ' if corner else '') + ev, 'measured', 'C' if corner and not exempt else 'B')
    elif rect and through:
        add('rect_panel', len(through), 'full rectangle (fill %.2f) with paint running to %d sides: a painted panel/picture, not a cut-out silhouette' % (m['fill'], len(through)), 'measured', 'B' if not exempt else 'A')
    # ---- holes ----------------------------------------------------------------------------------------------
    if m['hole_frac'] > .25:
        frame_ok = re.search(r'frame|arch|ring|wheel|window|door|hoop|loop|wreath|halo|gate|cog|gear|rim|bracket|hole|opening|lattice|grille|grill|web|net|mesh|cage|fence|rail|railing|chair|stool|ladder|scaffold|truss|tower|pylon|letters?', txt)
        add('big_holes', round(m['hole_frac'], 3), 'enclosed transparent area = %.0f%% of filled silhouette (%d holes >=0.5%%)' % (100 * m['hole_frac'], m['n_holes_big']), 'measured', 'A' if frame_ok else 'B')
    # ---- pale paper fringe ----------------------------------------------------------------------------------
    fx = m['fringe_frac'] - m['inner_pale']
    if m['fringe_frac'] >= .3 and fx >= .2:
        add('pale_fringe', m['fringe_frac'], '%.0f%% of the outer 2px band is light & unsaturated vs %.0f%% 6-12px inside (2-4px band: %.0f%%)'
            % (100 * m['fringe_frac'], 100 * m['inner_pale'], 100 * m['fringe_2_4']), 'measured', 'B')
    # ---- character / body part baked in --------------------------------------------------------------------
    pm = c['person'] - c['object']
    bw = re.search(BODY_WORDS, txt)
    handobj = re.search(OBJ_HANDWORDS, txt)
    # v4 (viewed list): palm trees, road shoulders, 'snap clips' matched; label-only evidence is weak (13.props.harvest/crown is
    # labelled SHOULDER.R but shows flowers) -> C only when CLIP's person/limb score is also within .01 of the best object
    if bw and not handobj and p['kind'] != 'ref' and not re.search(r'palm (tree|row)|strip shoulder|rocky shoulder|clips', txt):
        agree = pm > -.01
        add('body_part_label', bw.group(0), "label/name '%s' names a puppet body part; CLIP person/limb-object = %.3f (%s)"
            % (txt[:50], pm, 'agrees' if agree else 'disagrees'), 'inferred', 'C' if agree else 'B')
    if not thin and m['erode5'] > .3:
        # v3: 'a person sitting in a chair' dropped as a trigger (it fired on an empty folding chair)
        if c['person_best'] in ('a person', 'a man standing', 'a woman', 'a human face', 'a silhouette of a person') and pm > .003:
            add('character_baked', round(pm, 3), "CLIP '%s' beats best object prompt by %.3f" % (c['person_best'], pm), 'measured', 'C' if pm > .012 else 'B')
        elif c['person_best'] in ('a human hand', 'a human arm', 'a puppet body part, a limb with a joint') and pm > .006:
            # v4 (viewed explore_person): alone this mostly fires on cords, cloth, ripples -> info unless a strong hand reading
            add('body_part', round(pm, 3), "CLIP '%s' beats best object prompt by %.3f" % (c['person_best'], pm), 'measured',
                'B' if c['person_best'] == 'a human hand' and pm > .015 else 'A')
    # ---- reference sheet look ------------------------------------------------------------------------------
    rm = c['refsheet'] - c['object']
    if rm > .01 and p['kind'] != 'ref':
        add('refsheet_look', round(rm, 3), "CLIP '%s' beats objects by %.3f" % (c['refsheet_best'], rm), 'measured', 'B')
    # ---- label vs image ------------------------------------------------------------------------------------
    if c['label_pct'] < .5 and len(c['label_text']) > 2:
        add('label_mismatch', c['label_pct'], "image matches its own label '%s' worse than %.0f%% of other set-piece labels" % (c['label_text'], 100 * (1 - c['label_pct'])), 'measured', 'A')
    return D


def reconcile(reg, D, m):
    """registry q/why: confirm or overturn each reason with this pass's measurements"""
    kinds = {d['kind'] for d in D}
    out = []
    for w in reg.get('why', []):
        if w.startswith('clipped'):
            ok = bool(kinds & {'clipped_edge', 'sheet_edge', 'rect_panel'})
        elif w.startswith('pale fringe'):
            ok = 'pale_fringe' in kinds
        elif w.startswith('big holes'):
            ok = 'big_holes' in kinds
        elif w.startswith('fragments'):
            ok = bool(kinds & {'several_objects', 'several_pieces_by_design', 'satellites', 'baked_caption', 'label_strip'})
        elif w.startswith('mostly paper'):
            ok = bool(kinds & {'paper_chunk', 'label_strip', 'text_card'}) or m.get('body_pale', 0) > .45
        elif w.startswith('tiny'):
            ok = bool(kinds & {'tiny', 'sliver'})
        elif w.startswith('printed lettering'):
            ok = bool(kinds & {'label_strip', 'text_card', 'baked_caption'})
        elif w.startswith(('reference panel', 'assembled')):
            ok = 'reference_panel' in kinds
        else:
            ok = None                                         # 'no label': not a pixel claim
        out.append({'why': w, 'confirmed': ok})
    return out


def duplicates(ids, M, P, E, eidx):
    """near-duplicate groups: pHash(RGB on paper) <= 10/63, alpha 16x16 <= 26/256, aspect within 20%, CLIP cos >= .93"""
    ok = [i for i in ids if not M[i].get('empty') and i in eidx]
    ph = np.array([bits(M[i]['phash']) for i in ok]); ah = np.array([bits(M[i]['ahash']) for i in ok])
    asp = np.array([np.log(M[i]['w'] / M[i]['h']) for i in ok])
    Ev = np.array([E[eidx[i]] for i in ok])
    par = list(range(len(ok)))

    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    pairs = {}
    for a in range(len(ok)):
        dp = (ph[a + 1:] != ph[a]).sum(1); da = (ah[a + 1:] != ah[a]).sum(1)
        cos = Ev[a + 1:] @ Ev[a]
        hit = np.nonzero((dp <= 10) & (da <= 26) & (np.abs(asp[a + 1:] - asp[a]) < .2) & (cos >= .93))[0]
        for j in hit:
            b = a + 1 + j
            pairs[(ok[a], ok[b])] = (int(dp[j]), int(da[j]), round(float(cos[j]), 3))
            par[f(a)] = f(b)
    groups = defaultdict(list)
    for k, i in enumerate(ok):
        groups[f(k)].append(i)
    return [g for g in groups.values() if len(g) > 1], pairs


def main():
    P = {p['id']: p for p in setpieces()}
    M = json.load(open(os.path.join(CACHE, 'measure.json')))
    C = json.load(open(os.path.join(CACHE, 'clip_scores.json')))
    R = json.load(open(os.path.join(CUT, 'registry.json')))['parts']
    E = np.load(os.path.join(CACHE, 'clip_img.npy')); eidx = {i: k for k, i in enumerate(json.load(open(os.path.join(CACHE, 'clip_ids.json'))))}
    out = {}
    for i, p in P.items():
        m, c, reg = M[i], C.get(i, {}), R.get(i, {})
        D = judge(p, m, c, reg) if c else [{'kind': 'unreadable', 'value': None, 'evidence': 'no CLIP embedding (empty alpha)', 'basis': 'measured', 'severity': 'C'}]
        out[i] = {'sheet': p['sheet'], 'label': p.get('label'), 'kind': p['kind'], 'place': reg.get('place'),
                  'defects': D, 'components': m.get('n_comp', 0), 'comp_fracs': m.get('comp_fracs', [])[:6],
                  'fringe_frac': m.get('fringe_frac'), 'fringe_inner_pale': m.get('inner_pale'), 'hole_frac': m.get('hole_frac'),
                  'px': [m['w'], m['h']], 'alpha_px': m['area'],
                  'clip': {k: c.get(k) for k in ('text', 'person', 'scrap', 'refsheet', 'object', 'object_best', 'label_text', 'label_pct')},
                  'registry': {'q': reg.get('q'), 'why': reg.get('why', []), 'check': reconcile(reg, D, m)}}
    # duplicates
    groups, pairs = duplicates(list(P), M, P, E, eidx)
    sev = {'C': 2, 'B': 1, 'A': 0}

    def score(i):
        o = out[i]; worst = max([sev[d['severity']] for d in o['defects']] + [0])
        return (-worst, -sum(sev[d['severity']] for d in o['defects']), o['alpha_px'], -(o['fringe_frac'] or 0))
    for g in groups:
        best = max(g, key=score)
        cross = len({P[i]['sheet'] for i in g}) > 1
        for i in g:
            out[i]['dup_group'] = sorted(g)
            out[i]['duplicate_of'] = None if i == best else best
            if i != best:
                pr = pairs.get((i, best)) or pairs.get((best, i))
                # v3 (viewed audit/dup_groups): same-sheet look-alikes are animation states / repeat cards by design -> info only
                xs = P[i]['sheet'] != P[best]['sheet']
                out[i]['defects'].append({'kind': 'near_duplicate' if xs else 'variant', 'value': best,
                                          'evidence': ('pHash %d/63, alpha %d/256, CLIP cos %.3f to the best copy' % pr) if pr else 'same group (linked through another copy)',
                                          'basis': 'measured', 'severity': 'B' if xs else 'A', 'cross_sheet': xs})
    for i, o in out.items():
        o.setdefault('duplicate_of', None)
        worst = max([sev[d['severity']] for d in o['defects']] + [0])
        o['grade'] = {2: 'C', 1: 'B', 0: 'A'}[worst]
        o['usable'] = worst < 2
        o['fix'] = [f for f, k in [('erode alpha 2px (fringe)', 'pale_fringe'), ('keep largest component', 'satellites'), ('keep largest component (drops printed caption)', 'baked_caption')]
                    if any(d['kind'] == k for d in o['defects'])]
        rq = o['registry']['q']
        o['registry']['agree'] = (rq == 'C') == (o['grade'] == 'C')
    meta = {'about': 'Set-piece hygiene: one record per part on .props./.set./.hero./.fx. sheets (all %d, refs included and marked unusable). '
                     'grade A clean, B usable with care (see defects/fix), C do not place. severity per defect; basis measured|viewed|inferred. '
                     'duplicate_of = id of the best copy in its near-duplicate group (null when this is the best or unique). Code: shots/scion2/setpieces/hygiene/.' % len(out),
            'summary': {'parts': len(out), 'grade': Counter(o['grade'] for o in out.values()), 'usable': sum(o['usable'] for o in out.values()),
                        'defects': Counter(d['kind'] for o in out.values() for d in o['defects']),
                        'defects_blocking': Counter(d['kind'] for o in out.values() for d in o['defects'] if d['severity'] == 'C'),
                        'dup_groups': len(groups), 'dup_cross_sheet_groups': sum(len({P[i]['sheet'] for i in g}) > 1 for g in groups),
                        'dup_non_best': sum(1 for o in out.values() if o['duplicate_of']),
                        'registry_vs_ours': Counter('%s->%s' % (o['registry']['q'], o['grade']) for o in out.values()),
                        'registry_reasons_confirmed': Counter('%s:%s' % (c['why'].split(' (')[0].split(':')[0], c['confirmed']) for o in out.values() for c in o['registry']['check'])}}
    json.dump({'meta': meta, 'parts': out}, open(OUT, 'w'), indent=0)
    print(json.dumps(meta['summary'], indent=1))
    if '--sheets' in sys.argv:
        sheets(out, P, groups)


def cap(i, o, k=None):
    ds = [d for d in o['defects'] if k is None or d['kind'] == k] or o['defects']
    return [i[-36:], '%s %s %s' % (o['grade'], (ds[0]['kind'] if ds else '-'), (str(ds[0]['value'])[:12] if ds else '')),
            ','.join(sorted({d['kind'][:8] for d in o['defects']}))[:36]]


def sheets(out, P, groups):
    by = defaultdict(list)
    for i, o in out.items():
        for d in o['defects']:
            by[d['kind']].append(i)
    rnd = np.random.RandomState(0)
    for k, L in by.items():
        L = sorted(L)
        if len(L) > 48:
            L = list(rnd.choice(L, 48, replace=False))
        contact([(P[i], cap(i, out[i], k)) for i in L], os.path.join(AUDIT, 'defect_%s.jpg' % k), title='%s (%d parts; %s)' % (k, len(by[k]), 'random 48' if len(by[k]) > 48 else 'all'))
    # hardest: grade disagrees with registry, and borderline clean
    dis = [i for i, o in out.items() if not o['registry']['agree'] and o['kind'] == 'card']
    L = sorted(dis)
    sel = list(rnd.choice(L, 60, replace=False)) if len(L) > 60 else L
    contact([(P[i], cap(i, out[i]) + ['reg %s %s' % (out[i]['registry']['q'], ';'.join(out[i]['registry']['why'])[:30])]) for i in sel],
            os.path.join(AUDIT, 'hard_registry_disagree.jpg'), title='grade C vs registry disagree (%d cards)' % len(L))
    A = sorted(i for i, o in out.items() if o['grade'] == 'A')
    contact([(P[i], cap(i, out[i])) for i in rnd.choice(A, 48, replace=False)], os.path.join(AUDIT, 'grade_A_random.jpg'), title='grade A random 48 of %d' % len(A))
    Cc = sorted(i for i, o in out.items() if o['grade'] == 'C' and o['kind'] == 'card')
    contact([(P[i], cap(i, out[i])) for i in Cc[:90]], os.path.join(AUDIT, 'blocked_cards.jpg'), cols=9, cell=170,
            title='every grade-C card that is NOT a catalogued ref (%d, first 90 by id)' % len(Cc))
    G = sorted(groups, key=lambda g: -len(g))[:12]
    items = []
    for g in G:
        for i in sorted(g, key=lambda i: out[i]['duplicate_of'] is not None)[:6]:
            items.append((P[i], [i[-36:], 'BEST' if out[i]['duplicate_of'] is None else 'dup', '%s' % out[i]['grade']]))
        while len(items) % 6:
            items.append((P[G[0][0]], ['(pad)', '', '']))
    contact(items, os.path.join(AUDIT, 'dup_groups.jpg'), title='12 biggest near-duplicate groups (best first per row)')


if __name__ == '__main__':
    main()
