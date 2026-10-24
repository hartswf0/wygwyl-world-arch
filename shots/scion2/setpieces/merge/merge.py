"""MERGE swarm: fuse hygiene / semantics / space / affordance into one registry of set pieces.

Reads   shots/kits/cut/catalog.json (read-only), shots/scion2/setpieces/{hygiene,semantics,space,affordance}.json
Writes  shots/scion2/setpieces/registry.json   one record per set piece (all 2,227 parts incl. refs)
        shots/scion2/setpieces/conflicts.json  every cross-swarm disagreement and how it was resolved

Field ownership (who decides what; every record's `provenance` repeats this with the evidence):
  name, category, scene ......... semantics (category may be corrected by a MERGE misfile rule, recorded)
  grade, defects, duplicate_of .. hygiene
  usable ........................ AND of hygiene.usable, not semantics.skip, not character-fragment, space.placeable;
                                  any one swarm saying "do not place" wins (conservative)
  plane, contact, view, tile, size_cm, scale_src .. space (plane may be corrected by a MERGE rule, recorded)
  affordances ................... affordance (dropped when unusable; confidence capped when category disagrees)
Every MERGE rule is listed in RULES below with its id; records cite the ids that fired.
"""
import json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)                                   # shots/scion2/setpieces
ROOT = os.path.abspath(os.path.join(SP, '../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')

RULES = {
    # usability
    'U1': 'hygiene grade C / usable=false -> unusable (hygiene owns pixel cleanliness)',
    'U2': 'semantics skip=true (character fragment, sheet lettering, reference/assembled/example label) -> unusable even when hygiene passed it',
    'U3': 'semantics category character-fragment -> unusable (a body part is not a set piece)',
    'U4': 'space placeable=false (reference/assembly wording on the label) -> unusable',
    'U5': 'unusable parts get grade C (grade_hygiene keeps the hygiene grade) and lose their affordances (kept under affordances_dropped)',
    'U6': 'semantics flag "registry grade C" is NOT used: hygiene re-measured the registry reasons and owns the call',
    'U7': 'MERGE: label contains "reference only" / "assembled" / "assembly" / "example" / "states assembled" / "poses reference" -> unusable (viewed: assembly views)',
    'U8': 'MERGE: text-graphic with an EMPTY label AND (semantics pixel test thin strokes/text strip OR hygiene CLIP text > object) -> unusable (unnamed lettering). v1 fired on any text-graphic without a label class and killed the TIDE OFFICE plate, a blank number strip, a marquee poster frame and a thread (viewed) -> now needs an empty label.',
    'U9': 'MERGE: printed heading on a torn tan paper strip (measured merge/tanstrip.json: tan>=0.7, dark 0.04-0.4 in the middle 60% of rows, aspect>=5) -> unusable label_strip. Viewed: 7 "(N CARDS)" / "REFERENCE ONLY" strips on 10.fx.ride-light that hygiene and semantics passed.',
    'U10': 'MERGE: measured lettering signature (merge/letters.json): achromatic>=0.85, dark>=0.30 (was 0.35; missed WHEEL SPOKE INSERT at 0.32-0.33), white outline pale>=0.15, aspect>=2 (black capitals with a white rim), OR a label box: achromatic>=0.95, pale>=0.4, dark 0.01-0.3, aspect>=2 -> unusable label_strip. Viewed: "LIGHTS", "PARTS", "FRONT WHEEL RING", "8 wide light pool" box. Black objects (platters, screens) fail on achromatic/aspect.',
    'P3': 'MERGE: usable text-graphic not on an .fx. sheet and without overlay/reflect/chalk/flood/line words -> plane near_set, flag contact_doubt (name plaques, EXIT sign, TIDE OFFICE plate are physical signs, not overlays; viewed).',
    'U11': 'MERGE: hygiene baked_caption AND hygiene CLIP text beats object by >=0.015 AND >=15 alpha components -> unusable (an "ASSEMBLED REFERENCE" scene image with its heading baked in; viewed 2 hits; the projection frame at +0.012 stays usable).',
    'C4b': 'MERGE: C4 is skipped when semantics CLIP zero-shot is >=0.9 sure of the furniture class: the tableware label belongs to a neighbouring card (viewed: "7 ESPRESSO CUP (TABLE)" and "8 SAUCER" are bentwood chairs). Category kept, grip dropped, label_doubt.',
    'C5': 'MERGE: every part on 02.props.poet-eye-aperture is the poet\'s eye (iris, sclera, lids, light point) -> character-fragment, unusable (viewed: "LOWER LID", iris rings were filed as ground/light-fx).',
    'U4o': 'MERGE overturn: space placeable=false or U7 came only from reference/assembled wording in the label/id, but hygiene passed the pixels and CLIP sees an object more than text or a reference sheet (text<=object, refsheet<=object, no refsheet_look/reference_label defect) -> usable, flag label_doubt. Viewed: lantern, gold rim, terraces, hanging foliage, pearl bracelet, door frame, VU backing were all clean pieces carrying a mis-attached heading.',
    'U2o': 'MERGE overturn: semantics skip came only from a heading-like label or "sheet lettering" pixel test, but hygiene passed it with no label_strip, CLIP text < object and the pixel test is not "text strip" -> usable, flag label_doubt. Viewed: a thread (T5), the marquee front.',
    'H1': 'MERGE overturn: hygiene\'s ONLY blocking defect is clipped_edge (corner clip) and category is aperture/architecture/light-fx -> usable grade B, flag hygiene_overturned. Viewed: shadowpool tunnel frames, temple "4. COMPLETE", temple shadow wedge are intact (hygiene itself listed them as doubtful). The cage front (other) keeps C: it has a baked caption and border line.',
    'C2': 'MERGE: character-fragment whose label names furniture/an object (sofa/couch/chair arm, marionette control, glass/acetate panel) or is only the caption "Poet" -> category from that noun or semantics\' next fused class; U2/U3/U4 lifted. Viewed: sofa arm, marionette crossbar, handprint glass panel, a quay ground strip labelled "Poet".',
    'C3': 'MERGE: affordance grip (confidence>=0.62 from a label word) on architecture/backdrop/aperture/ground/furniture -> handheld-prop. Viewed: folded paper, poem paper, staff shaft.',
    'C4': 'MERGE: label noun cup/saucer/coupe/mug/espresso on furniture/vehicle/ground -> handheld-prop (coupe is a champagne glass, not a car; viewed). label "facade" on handheld-prop -> architecture.',
    # category / plane fixes (misfiles)
    'C1': 'MERGE: semantics light-fx, but space found an opaque object on an fx sheet with an object-noun label (pills, heart, clock ...) -> category taken from the noun',
    'P1': 'MERGE: category light-fx and space plane near_set with a code-only/empty label (C07, G01, BO1, w04) -> plane overlay_fx (viewed: comet swirls, glints, smudge words, flames). Exception after viewing: hygiene CLIP object_best is a plant -> category plant-nature, plane near_set (orbit-harvest tulips/stems); a building/wall -> architecture, plane mid_set (BO1-3 lit tower strips).',
    'P2': 'MERGE: category backdrop on far_backdrop is fine; handheld-prop / furniture / wearable on far_backdrop or overlay_fx -> plane near_set, flagged',
    # flags
    'F1': 'space scale_conflict (own size vs sheet scale > 40%) -> flag size_doubt',
    'F2': 'size_cm outside the plausible range for the category -> flag size_doubt',
    'F3': 'affordance kind incompatible with category -> confidence capped at 0.35, flagged',
    'F4': 'semantics conflict (label class != CLIP class) and hygiene label_mismatch -> flag label_doubt',
    'F5': 'category light-fx but plane not overlay_fx (after P1) -> flag plane_doubt',
    'F6': 'duplicate_of set -> not best copy; query() hides it unless include_dups=True',
}

# plausible longest side in cm per category (F2)
CAT_RANGE = {'handheld-prop': (1, 150), 'wearable': (2, 220), 'furniture-seat': (30, 320),
             'furniture-surface': (25, 400), 'vehicle': (60, 4000), 'aperture': (20, 3000),
             'architecture': (10, 20000), 'plant-nature': (1, 4000)}
# which categories each affordance kind makes sense on (F3)
AFF_OK = {
    'seat': {'furniture-seat', 'furniture-surface', 'architecture', 'ground', 'vehicle', 'plant-nature', 'other'},
    'surface': {'furniture-surface', 'furniture-seat', 'architecture', 'ground', 'aperture', 'other', 'vehicle'},
    'grip': {'handheld-prop', 'wearable', 'other', 'plant-nature'},
    'aperture': {'aperture', 'architecture', 'vehicle', 'backdrop', 'other', 'ground'},
    'lean': {'architecture', 'aperture', 'plant-nature', 'ground', 'furniture-seat', 'furniture-surface', 'other', 'vehicle', 'backdrop'},
    'occluder': {'architecture', 'aperture', 'plant-nature', 'ground', 'furniture-seat', 'furniture-surface', 'other', 'vehicle', 'backdrop', 'handheld-prop'},
    'stand_on': {'ground', 'architecture', 'furniture-surface', 'other', 'vehicle', 'backdrop', 'aperture'},
}
REF_WORDS = re.compile(r'reference only|reference[- ]only|\bassembled\b|\bassembly\b|\bexample\b|poses reference|reference prop', re.I)
CODE_LABEL = re.compile(r'^\s*\(?[a-z]{0,3}\s?-?\d{0,3}[a-z]?\)?\s*$', re.I)   # C07, G01, BO1, w04, COPY) handled below
# C1: object nouns that are not fx even on an fx sheet  -> category
NOUN_CAT = [(r'\bpills?\b|\bbottle|\bcup\b|\bmug\b|\bclock\b|\bphone\b|\bcandle\b|\bbook\b|\bkey\b|\bcoin\b', 'handheld-prop'),
            (r'\bheart\b|\blub\b|\bdub\b', 'other')]


def L(name):
    return json.load(open(os.path.join(SP, name)))


def main():
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    H = L('hygiene.json')['parts']; S = L('semantics.json')['parts']; X = L('space.json')['parts']
    A = L('affordance.json'); AP = A['parts']; ANONE = A['checked_none']
    global TAN
    TAN = json.load(open(os.path.join(HERE, 'tanstrip.json')))
    global LET
    lp = os.path.join(HERE, 'letters.json')
    LET = json.load(open(lp)) if os.path.exists(lp) else {}
    cparts = {}
    for sid, sh in cat.items():
        if not re.search(r'\.(props|set|hero|fx)\.', sid):
            continue
        for p in sh['parts']:
            cparts[p['id']] = (sid, sh, p)
    reg, conflicts = {}, []

    def conflict(pid, kind, a, b, resolution, rule, basis='inferred'):
        conflicts.append({'id': pid, 'kind': kind, 'a': a, 'b': b, 'resolution': resolution, 'rule': rule, 'basis': basis})

    for pid, (sid, sh, p) in sorted(cparts.items()):
        h, s, x = H[pid], S[pid], X[pid]
        sf = s['final']
        fired, flags = [], []
        label = p.get('label') or ''
        is_ref = p.get('kind') == 'ref'
        category = sf['category']
        cat_src = 'semantics'
        plane = x.get('plane'); plane_src = 'space'
        hc = h.get('clip', {}) or {}
        hdefs = [d['kind'] for d in h['defects']]
        hblock = [d['kind'] for d in h['defects'] if d.get('severity') == 'C']
        pt = s.get('pixel_test') or ''
        aff_in = AP.get(pid, {}).get('affordances') or []
        lw = set(re.findall(r'[a-z]+', label.lower()))

        def recat(c2, rule, why, plane2=None):
            nonlocal category, cat_src, plane, plane_src
            conflict(pid, 'category', f'semantics: {category}', why, f'category {c2}' + (f', plane {plane2}' if plane2 else ''), rule)
            category, cat_src = c2, 'merge:' + rule; fired.append(rule)
            if plane2 and plane2 != plane:
                plane, plane_src = plane2, 'merge:' + rule

        # ---------- category misfiles (C1-C4, P1 exceptions), decided before usability ----------
        if not is_ref and category == 'light-fx' and x.get('plane') == 'near_set':
            for rx, c2 in NOUN_CAT:
                if re.search(rx, label, re.I):
                    recat(c2, 'C1', f'space: opaque object on fx sheet; label noun -> {c2}')
                    break
        if not is_ref and sid == '02.props.poet-eye-aperture' and category != 'character-fragment':
            recat('character-fragment', 'C5', "sheet is the poet's eye")
        if not is_ref and category == 'character-fragment' and 'C5' not in fired:
            if lw & {'sofa', 'couch', 'chair', 'armchair'}:
                recat('furniture-seat', 'C2', 'label names furniture: ' + label[:40], 'near_set')
            elif 'marionette' in lw:
                recat('handheld-prop', 'C2', 'label names a marionette control (prop): ' + label[:40], 'near_set')
            elif lw & {'glass', 'acetate'} or lw == {'poet'}:
                c2 = next(c for c, _ in s['fused_top3'] if c != 'character-fragment')
                recat(c2, 'C2', f'label "{label[:30]}" is an object/caption; semantics next fused class {c2}',
                      {'ground': 'ground_plane', 'light-fx': 'overlay_fx'}.get(c2, 'near_set'))
            if 'C2' in fired:
                flags.append('contact_doubt')
        grip_strong = [a for a in aff_in if a['kind'] == 'grip' and a['confidence'] >= 0.62
                       and (a.get('evidence', {}).get('label') or {}).get('strength', 0) > 0]
        drop_kinds = set(); name_override = None
        if not is_ref and category in ('furniture-seat', 'furniture-surface', 'vehicle', 'ground') and lw & {'cup', 'saucer', 'coupe', 'mug', 'espresso'}:
            ct = s.get('clip_top3') or [[None, 0]]
            if ct[0][0] == category and ct[0][1] >= 0.9:
                # C4b: CLIP is sure it is furniture; the tableware label belongs to a neighbouring card
                fired.append('C4b'); flags += ['label_doubt', 'contact_doubt', 'size_doubt']; drop_kinds.add('grip')
                name_override = f"{category} (label doubtful: {label[:30]})"
                conflict(pid, 'category', f'label noun tableware: {label[:40]}', f'CLIP {ct[0][0]} {ct[0][1]}',
                         f'keep {category}, drop grip, flag label_doubt', 'C4b', 'viewed')
            else:
                recat('handheld-prop', 'C4', 'label noun is a tableware item: ' + label[:40], 'near_set')
        elif not is_ref and category in ('architecture', 'backdrop', 'aperture', 'ground', 'furniture-seat', 'furniture-surface') and grip_strong:
            recat('handheld-prop', 'C3', f"affordance grip {grip_strong[0]['confidence']} from label word", 'near_set')
        if not is_ref and category == 'handheld-prop' and 'facade' in lw:
            recat('architecture', 'C4', 'label names a facade', 'mid_set')
        if not is_ref and category == 'light-fx' and plane == 'near_set':
            ob = (hc.get('object_best') or '').lower() + ' ' + ' '.join(d for d in x.get('doubt', []) if re.search(r'CLIP depth (building|foliage) 0\.[5-9]', d))
            lab = re.sub(r'[^a-z0-9 ]', '', label.lower()).strip()
            if lab == '' or re.fullmatch(r'[a-z]{1,3}\s?\d{1,3}[a-z]?(\s?\d)?|copy|part\s?\d*', lab):
                if re.search(r'plant|flower|tree|leaves|bush|foliage', ob):
                    recat('plant-nature', 'P1', f'fx-sheet card, code label; hygiene CLIP object_best "{ob}"', 'near_set')
                elif re.search(r'building|wall|tower|facade', ob):
                    recat('architecture', 'P1', f'fx-sheet card, code label; hygiene CLIP object_best "{ob}"', 'mid_set')
                else:
                    conflict(pid, 'plane', 'space: near_set (fx-sheet card that CLIP called an object)',
                             'semantics: light-fx with code-only label', 'overlay_fx', 'P1')
                    plane, plane_src = 'overlay_fx', 'merge:P1'; fired.append('P1')
        # ---------- usability ----------
        text_le_obj = hc.get('text', 1) <= hc.get('object', 0) and hc.get('refsheet', 1) <= hc.get('object', 0) \
            and not ({'refsheet_look', 'reference_label', 'label_strip'} & set(hdefs))
        why_not = []
        if not h['usable']:
            if hblock == ['clipped_edge'] and category in ('aperture', 'architecture', 'light-fx'):
                fired.append('H1'); flags.append('hygiene_overturned')
                conflict(pid, 'usable', 'hygiene: C clipped_edge (corner clip)', f'category {category}; viewed intact portal/temple shapes',
                         'usable, grade B', 'H1', 'viewed')
            else:
                why_not.append({'by': 'hygiene', 'rule': 'U1', 'reason': hblock or ['grade C']})
        sem_skip = bool(sf.get('skip')) and not is_ref and 'C2' not in fired
        if sem_skip:
            sflags = sf.get('flags', [])
            heading_only = not any('person' in f for f in sflags) and category != 'character-fragment'
            if heading_only and h['usable'] and 'label_strip' not in hdefs and hc.get('text', 1) < hc.get('object', 0) and not pt.startswith('text strip') \
                    and not re.search(r'abstract|reference', label, re.I):
                fired.append('U2o'); flags.append('label_doubt')
                conflict(pid, 'usable', 'semantics: skip (heading-like label / lettering test)', 'hygiene usable, CLIP text<object',
                         'usable, flag label_doubt', 'U2o')
            else:
                why_not.append({'by': 'semantics', 'rule': 'U2', 'reason': [f for f in sflags if 'label' in f or 'person' in f or 'lettering' in f or 'reference' in f][:3] or [sf.get('why') or 'skip']})
        if category == 'character-fragment':
            why_not.append({'by': 'semantics', 'rule': 'U3', 'reason': ['character-fragment']})
        refword = []
        if not is_ref and x.get('placeable') is False and 'C2' not in fired and h['usable'] and not sem_skip:
            # space.placeable already ANDs hygiene.usable and character-fragment; count U4 only when it adds information
            refword.append({'by': 'space', 'rule': 'U4', 'reason': ['placeable=false (reference/assembly wording)']})
        if not is_ref and REF_WORDS.search(label):
            refword.append({'by': 'merge', 'rule': 'U7', 'reason': ['label names a reference/assembly view: ' + label[:60]]})
        if refword:
            if h['usable'] and text_le_obj and not sem_skip and not re.search(r'abstract|reference for', label, re.I):
                fired.append('U4o'); flags.append('label_doubt')
                conflict(pid, 'usable', 'space placeable=false / reference wording: ' + label[:40], 'hygiene usable; CLIP object > text, refsheet',
                         'usable, flag label_doubt', 'U4o')
            else:
                why_not += refword
        if (not is_ref and category == 'text-graphic' and not label.strip()
                and (pt.startswith('thin strokes') or pt.startswith('text strip') or hc.get('text', 0) > hc.get('object', 1))):
            why_not.append({'by': 'merge', 'rule': 'U8', 'reason': ['unnamed lettering (empty label, text evidence: ' + (pt[:30] or 'CLIP text>object') + ')']})
        ts = TAN.get(pid)
        if not is_ref and ts and ts['tan'] >= 0.7 and 0.04 <= ts['dark'] <= 0.4 and ts['dark_mid'] >= 0.8 and ts['aspect'] >= 5:
            why_not.append({'by': 'merge', 'rule': 'U9', 'reason': [f"label_strip: printed heading on tan strip (tan {ts['tan']}, dark {ts['dark']}, aspect {ts['aspect']})"]})
        lt = LET.get(pid)
        if not is_ref and lt and lt['aspect'] >= 2 and (
                (lt['achrom'] >= 0.85 and lt['dark'] >= 0.30 and lt['pale'] >= 0.15) or
                (lt['achrom'] >= 0.95 and lt['pale'] >= 0.4 and 0.01 <= lt['dark'] <= 0.3)):
            why_not.append({'by': 'merge', 'rule': 'U10', 'reason': [f"label_strip: printed lettering/label box (achrom {lt['achrom']}, dark {lt['dark']}, pale {lt['pale']})"]})
        if (not is_ref and 'baked_caption' in hdefs and hc.get('text', 0) - hc.get('object', 0) >= 0.015
                and (h.get('components') or 0) >= 15):
            why_not.append({'by': 'merge', 'rule': 'U11', 'reason': [f"captioned reference image (text-object {hc.get('text', 0) - hc.get('object', 0):.3f}, {h.get('components')} components)"]})
        if is_ref:
            why_not = [{'by': 'catalog', 'rule': 'U1', 'reason': ['reference_panel (catalog kind=ref)']}]
        usable = not why_not
        # cross-swarm disagreements about usability
        if not is_ref:
            votes = {'hygiene': h['usable'], 'semantics': not sf.get('skip') and sf['category'] != 'character-fragment',
                     'space': bool(x.get('placeable'))}
            if len(set(votes.values())) > 1:
                conflict(pid, 'usable', {k: v for k, v in votes.items() if v}, {k: v for k, v in votes.items() if not v},
                         ('usable' if usable else 'unusable') + ' after merge rules', [w['rule'] for w in why_not] + [r for r in fired if r in ('U2o', 'U4o', 'H1', 'C2')])
            if h['usable'] and any('registry grade C' in f for f in sf.get('flags', [])):
                conflict(pid, 'registry_q', 'semantics echoes registry q=C', 'hygiene re-measured: usable grade ' + h['grade'],
                         'hygiene wins', 'U6')
        # ---------- plane ----------
        if not is_ref and category in ('handheld-prop', 'furniture-seat', 'furniture-surface', 'wearable') and plane in ('far_backdrop', 'overlay_fx'):
            conflict(pid, 'plane', f'space: {plane}', f'semantics: {category}', 'near_set (flagged)', 'P2')
            plane, plane_src = 'near_set', 'merge:P2'; fired.append('P2'); flags.append('plane_doubt')
        if (not is_ref and category == 'text-graphic' and plane == 'overlay_fx' and '.fx.' not in sid
                and not re.search(r'overlay|reflect|chalk|flood|line|falling', label, re.I)):
            conflict(pid, 'plane', 'space: overlay_fx', 'text-graphic plate/sign on a props/set sheet', 'near_set (flag contact_doubt)', 'P3')
            plane, plane_src = 'near_set', 'merge:P3'; fired.append('P3'); flags.append('contact_doubt')
        if not is_ref and category == 'light-fx' and plane != 'overlay_fx':
            flags.append('plane_doubt'); fired.append('F5')
        # ---------- size ----------
        size = x.get('size_cm')
        if x.get('scale_conflict'):
            flags.append('size_doubt'); fired.append('F1')
            conflict(pid, 'size', f"space own size {size} ({x.get('scale_src')})",
                     f"sheet scale gives {x['scale_conflict'].get('size_at_sheet_scale')} (ratio {x['scale_conflict'].get('ratio')})",
                     'keep own size, flag size_doubt', 'F1', 'measured')
        if size and category in CAT_RANGE:
            lo, hi = CAT_RANGE[category]; m = max(size.get('h') or 0, size.get('w') or 0)
            if m and not (lo <= m <= hi):
                flags.append('size_doubt'); fired.append('F2')
                conflict(pid, 'size_vs_category', f'space size {m:.0f} cm ({x.get("scale_src")})', f'category {category} range {lo}-{hi} cm',
                         'keep size, flag size_doubt', 'F2')
        # ---------- label doubt ----------
        if not is_ref and sf.get('conflict') and 'label_mismatch' in hdefs:
            flags.append('label_doubt'); fired.append('F4')
        # ---------- affordances ----------
        affs, dropped = [], []
        for a in aff_in:
            a2 = {'kind': a['kind'], 'confidence': a['confidence'], 'geometry': a['geometry']}
            if a['kind'] not in AFF_OK or category not in AFF_OK[a['kind']]:
                a2['confidence'] = min(a2['confidence'], 0.35); a2['capped'] = 'F3'
                flags.append('affordance_doubt'); fired.append('F3')
                conflict(pid, 'affordance_vs_category', f"affordance: {a['kind']} {a['confidence']}", f'category {category}',
                         'kept, confidence capped 0.35', 'F3')
            if a['kind'] in drop_kinds:
                a2['dropped_by'] = 'C4b'; dropped.append(a2); continue
            (affs if usable else dropped).append(a2)
        if dropped:
            fired.append('U5')
        if h.get('duplicate_of'):
            fired.append('F6')
        grade = ('B' if 'H1' in fired else h['grade']) if usable else 'C'
        if why_not and not is_ref:
            fired += [w['rule'] for w in why_not]
        if 'C2' in fired and usable:
            flags.append('contact_doubt')
        # ---------- rank (best-first ordering inside a query; inferred) ----------
        rank = {'A': 3, 'B': 2, 'C': 0}[grade] + (0 if h.get('duplicate_of') else 1) + sf.get('confidence', 0) \
            - 0.3 * len(set(flags)) + (0.2 if size else 0) - 0.1 * sum(1 for d in h['defects'] if d.get('severity') == 'B')
        scenes = sorted(set(([p['scene']] if p.get('scene') else []) + (s.get('scenes') or [])))
        rec = {
            'id': pid, 'file': f'shots/kits/cut/{p["file"]}', 'sheet': sid, 'poems': sh.get('poems', []),
            'scene': scenes, 'label': label, 'kind': p.get('kind'),
            'name': name_override or sf.get('name'), 'category': category,
            'usable': usable, 'grade': grade, 'grade_hygiene': h['grade'],
            'unusable_reasons': why_not,
            'defects': [{k: d[k] for k in ('kind', 'severity', 'basis', 'evidence') if k in d} for d in h['defects']],
            'fix': h.get('fix', []),
            'duplicate_of': h.get('duplicate_of'),
            'plane': plane if not is_ref else None, 'contact': x.get('contact'), 'view': x.get('view'),
            'view_conf': x.get('view_conf'), 'tile': x.get('tile'),
            'size_cm': size, 'scale_src': x.get('scale_src'), 'px': h.get('px'),
            'affordances': affs, 'affordances_dropped': dropped,
            'flags': sorted(set(flags)), 'rank': round(rank, 3), 'merge_rules': sorted(set(fired)),
            'provenance': {
                'name': {'by': 'merge:C4b' if name_override else 'semantics', 'basis': 'inferred', 'src': sf.get('name_src'), 'semantics_name': sf.get('name')},
                'category': {'by': cat_src, 'basis': 'inferred',
                             'evidence': {'label_class': sf.get('label_class'), 'clip_class': sf.get('clip_class'),
                                          'knn': s.get('knn_label_vote'), 'fused_top3': s.get('fused_top3'),
                                          'confidence': sf.get('confidence'), 'conflict': sf.get('conflict'),
                                          'semantics_category': sf['category']}},
                'scene': {'by': 'semantics', 'basis': 'measured (stage set files)', 'catalog_scene': p.get('scene')},
                'grade': {'by': 'hygiene', 'basis': 'measured+viewed', 'evidence': {'components': h.get('components'),
                          'fringe_frac': h.get('fringe_frac'), 'hole_frac': h.get('hole_frac'), 'clip': h.get('clip')}},
                'usable': {'by': [w['by'] for w in why_not] or ['hygiene', 'semantics', 'space'], 'basis': 'inferred (AND of swarms)',
                           'hygiene': h['usable'], 'semantics_skip': sf.get('skip'), 'space_placeable': x.get('placeable')},
                'duplicate_of': {'by': 'hygiene', 'basis': 'measured (perceptual hash + CLIP)'},
                'plane': {'by': plane_src, 'basis': (x.get('basis') or {}).get('plane'), 'space_plane': x.get('plane')},
                'contact': {'by': 'space', 'basis': (x.get('basis') or {}).get('contact')},
                'view': {'by': 'space', 'basis': (x.get('basis') or {}).get('view'), 'conf': x.get('view_conf')},
                'tile': {'by': 'space', 'basis': (x.get('basis') or {}).get('tile')},
                'size_cm': {'by': 'space', 'basis': (x.get('basis') or {}).get('size'), 'scale_src': x.get('scale_src'),
                            'scale_conflict': x.get('scale_conflict'), 'doubt': x.get('doubt', [])},
                'space_rules': (x.get('evidence') or {}).get('rules', []),
                'affordances': {'by': 'affordance', 'basis': 'label words measured, geometry measured, confidence inferred',
                                'evidence': [a.get('evidence') for a in (AP.get(pid, {}).get('affordances') or [])],
                                'checked_none': (ANONE.get(pid) or {}).get('reason') if pid in ANONE else None},
            },
        }
        reg[pid] = rec

    # ---------- summary ----------
    U = [r for r in reg.values() if r['usable']]
    summ = {
        'parts': len(reg), 'cards': sum(1 for r in reg.values() if r['kind'] == 'card'),
        'usable': len(U), 'unusable': len(reg) - len(U),
        'usable_best_copies': sum(1 for r in U if not r['duplicate_of']),
        'grade': dict(collections.Counter(r['grade'] for r in reg.values())),
        'usable_by_category': dict(collections.Counter(r['category'] for r in U).most_common()),
        'all_by_category': dict(collections.Counter(r['category'] for r in reg.values()).most_common()),
        'usable_by_plane': dict(collections.Counter(r['plane'] for r in U).most_common()),
        'unusable_by_rule': dict(collections.Counter(w['rule'] for r in reg.values() for w in r['unusable_reasons']).most_common()),
        'affordances_usable': dict(collections.Counter(a['kind'] for r in U for a in r['affordances']).most_common()),
        'flags': dict(collections.Counter(f for r in reg.values() for f in r['flags']).most_common()),
        'merge_rules_fired': dict(collections.Counter(f for r in reg.values() for f in r['merge_rules']).most_common()),
        'conflicts': dict(collections.Counter(c['kind'] for c in conflicts).most_common()),
    }
    out = {'about': __doc__, 'rules': RULES, 'cat_range_cm': CAT_RANGE, 'affordance_category_ok': {k: sorted(v) for k, v in AFF_OK.items()},
           'summary': summ, 'parts': reg}
    json.dump(out, open(os.path.join(SP, 'registry.json'), 'w'), indent=1)
    json.dump({'about': 'Cross-swarm disagreements and their resolution. a/b are the two sides; rule refers to registry.json rules.',
               'summary': summ['conflicts'], 'conflicts': conflicts}, open(os.path.join(SP, 'conflicts.json'), 'w'), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
