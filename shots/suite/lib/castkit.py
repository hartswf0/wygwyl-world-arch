"""Cast kit: who is in the cast, which cut parts they are made of, and how big each part really is.

    python3 shots/suite/lib/castkit.py            # measure every part, write shots/suite/data/cast_parts.json

The cut parts live in shots/arena/parts/kit3/v2/parts/<character>.<costume>/ and were painted into
Kit 3 templates (kit.py): one ghost per card, drawn from a rest skeleton in cm at a fixed sheet scale
(body 6 px/cm, heads 12 px/cm). The cutter then trimmed and resized the cards, so a part file's own
pixels no longer say how big it is. This module puts the scale back:

  * the template tells us each card's extent in cm and where its brads sit (A, B, sockets);
  * the part file's ink box (alpha bbox) tells us how many px that extent became;
  * so every part gets its own px_per_cm (and the A/B pivots in its own pixels).

Nothing is guessed from the pixels except the ink box. Every part keeps a record of how far its two
axes disagree (aspect fidelity) so a card painted too fat or too short is visible, not hidden.
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.dirname(HERE)
SHOTS = os.path.dirname(SUITE)
KIT3 = os.path.join(SHOTS, 'arena', 'parts', 'kit3')
PARTS_DIR = os.path.join(KIT3, 'v2', 'parts')
sys.path.insert(0, KIT3)
import v2 as KV2          # noqa: E402  (registers every build's rest skeleton in kit.CHARS)
import kit as K           # noqa: E402

VIEWS = ['profile', 'front', 'threequarter', 'back', 'threequarter_back']

# ------------------------------------------------------------------ the cast
# id, name, parts dir, build (template skeleton), height_cm (real), role, poems, plays, notes for the solver
CAST = [
    dict(id='poet_tshirt', name='POET (black t-shirt)', dir='poet.black_tshirt', build='poetm', height_cm=184,
         plays='POET', poems='01 02 03', pronoun='he'),
    dict(id='poet_tracksuit', name='POET (red/black tracksuit, sunglasses)', dir='poet.red_black_sunglasses', build='poetm',
         height_cm=184, plays='POET', poems='04 05 06 07 08 09 10 11 12 13 14', pronoun='he'),
    dict(id='poet_soul', name="POET's soul (pale acetate double)", dir='poet.red_black_sunglasses', build='poetm', height_cm=184,
         plays='POET (soul)', poems='08', pronoun='he', tint=(170, 205, 235), alpha=0.72),
    dict(id='ex', name='EX (olive bomber)', dir='ex.ex_jacket', build='ex', height_cm=188, plays='EX', poems='01 02 03 07 08 09 12',
         pronoun='he', back_only=True),
    dict(id='woman', name='THE WOMAN (teal dress)', dir='woman.teal_dress', build='woman', height_cm=172, plays='the woman (arena)',
         poems='arena', pronoun='she', rig='legged'),
    dict(id='mother', name='MOTHER (cardigan)', dir='woman.mother_cardigan', build='woman', height_cm=165, plays='MOTHER',
         poems='02 09', pronoun='she', rig='legged', skirt_overlay='body.profile.skirt.brocade.png'),
    dict(id='she_window', name='SHE (red dress, far window)', dir='woman.window_woman_dress', build='woman', height_cm=168,
         plays='SHE', poems='13', pronoun='she'),
    dict(id='young_poet_pajamas', name='YOUNG POET, 6 (winter pajamas)', dir='young_poet.pajamas_winter', build='boy',
         height_cm=116, plays='YOUNG POET', poems='02', pronoun='he', head_from='young_poet.child_clothes'),
    dict(id='young_poet_tee', name='YOUNG POET, 6 (striped tee, shorts)', dir='young_poet.child_clothes', build='boy',
         height_cm=116, plays='YOUNG POET', poems='13', pronoun='he'),
    dict(id='ghost_child', name='GHOST CHILD, 7 (nightshirt)', dir='ghost_child.ghost_nightclothes', build='ghost', height_cm=122,
         plays='GHOST CHILD', poems='02 05 09', pronoun='they', head_from='young_poet.child_clothes', tint=(175, 200, 230), alpha=0.7),
    dict(id='father_02', name='FATHER (1990s winter coat)', dir='parents.parent_coat', build='manx', height_cm=178,
         plays='FATHER', poems='02', pronoun='he'),
    dict(id='father_elder', name='FATHER, elder (overcoat, flat cap)', dir='parents.elder_father_coat', build='manx',
         height_cm=174, plays='FATHER (elder)', poems='09', pronoun='he'),
    dict(id='ancestor_indigo', name='ANCESTOR (indigo & gold robe)', dir='ancestors.ancestor_robe_indigo_gold', build='robed',
         height_cm=180, plays='ANCESTORS', poems='05', pronoun='they', rig='legged'),
    dict(id='ancestor_elder', name='ANCESTOR ELDER (white & silver, staff)', dir='ancestors.ancestor_elder_white_silver',
         build='robed', height_cm=170, plays='ANCESTORS (elder)', poems='05', pronoun='they'),
    dict(id='atlantis_traveler', name='ATLANTIS traveller', dir='atlantis.atlantis_traveler', build='manx', height_cm=178,
         plays='citizens', poems='06', pronoun='they'),
    dict(id='atlantis_citizen', name='ATLANTIS citizen', dir='atlantis.atlantis_citizen', build='manx', height_cm=176,
         plays='citizens', poems='06 10 12', pronoun='they'),
    dict(id='atlantis_gatekeeper', name='ATLANTIS gatekeeper', dir='atlantis.atlantis_gatekeeper', build='manx', height_cm=182,
         plays='gatekeeper', poems='06', pronoun='they'),
    dict(id='atlantis_elder', name='ATLANTIS elder with lantern', dir='atlantis.poet_elder_coat', build='manx', height_cm=168,
         plays='old man with a lantern', poems='06', pronoun='he'),
    dict(id='vintage_party', name='Vintage party guest (1940s suit)', dir='party.vintage_party', build='manx', height_cm=177,
         plays='party', poems='01 14', pronoun='he'),
    dict(id='dj', name='DJ (LED bomber, cap)', dir='party.dj_cyber', build='manx', height_cm=178, plays='DJ', poems='07',
         pronoun='they'),
    dict(id='party_guest', name='Party guest', dir='party.party_guest', build='manx', height_cm=175, plays='party', poems='06 07',
         pronoun='they'),
    dict(id='dancer_dress', name='Club dancer (sequin dress)', dir='party.club_dress', build='manx', height_cm=168,
         plays='club crowd', poems='08 09', pronoun='she'),
    dict(id='dancer_shirt', name='Club dancer (open silk shirt)', dir='party.club_shirt', build='manx', height_cm=178,
         plays='club crowd', poems='08 09', pronoun='he'),
    dict(id='dancer_jacket', name='Club dancer (leather jacket)', dir='party.club_jacket', build='manx', height_cm=176,
         plays='club crowd', poems='08 09', pronoun='they'),
    dict(id='angel', name='ANGEL (white robe, wings)', dir='angels.angel_white_robe', build='robed', height_cm=182,
         plays='ANGELS', poems='08', pronoun='they', wings=True),
    dict(id='brother', name='BROTHER (hoodie)', dir='family.brother_casual', build='manx', height_cm=180, plays='BROTHER',
         poems='12', pronoun='he'),
    dict(id='friend', name='FRIEND (jacket, chinos)', dir='family.friend_casual', build='manx', height_cm=177, plays='friends',
         poems='12', pronoun='they'),
    dict(id='elder_memory', name='Remembered elder (backlit)', dir='family.elder_memory_silhouette', build='manx', height_cm=165,
         plays='elders (memory)', poems='12', pronoun='they', alpha=0.8),
    dict(id='elder_pearls', name='Elder at prayer (robe, pearls)', dir='family.elder_robe_pearls', build='manx', height_cm=160,
         plays='elders', poems='13', pronoun='they'),
    dict(id='couple_summer', name='Summer couple (linen)', dir='family.couple_summer_casual', build='manx', height_cm=175,
         plays='couples', poems='13', pronoun='they'),
    dict(id='street_clothes', name='Family, street clothes (denim)', dir='family.street_clothes', build='manx', height_cm=178,
         plays='family / everyday people', poems='10 14', pronoun='they'),
    dict(id='bola', name='BOLA (Crash Lab dummy)', dir='bola.crash_yellow', build='bola', height_cm=172, plays='Bola',
         poems='bolas', pronoun='she', code_head=dict(color=(255, 210, 63), top='antenna')),
    dict(id='shim', name='SHIM (Crash Lab dummy)', dir='shim.crash_teal', build='shim', height_cm=182, plays='Shim',
         poems='bolas', pronoun='he', code_head=dict(color=(25, 201, 174), top='fin')),
    dict(id='dot', name='DOT (Crash Lab child dummy)', dir='dot.crash_dot', build='dotd', height_cm=105, plays='Dot',
         poems='bolas', pronoun='she', code_head=dict(color=(255, 122, 107), top='bow')),
]
BY_ID = {c['id']: c for c in CAST}

# the arena's older rigs: audited from their existing takes, not re-run (superseded by the v2 kits above)
LEGACY = [
    dict(id='legacy_man', name='POET, legacy weave rig ("man" skin)', skin='man', parts='shots/weave/cast/man/parts',
         height_cm=186, superseded_by='poet_tracksuit'),
    dict(id='legacy_woman', name='THE WOMAN, legacy weave rig ("poet" skin)', skin='poet', parts='shots/weave/assets/parts',
         height_cm=172, superseded_by='woman'),
    dict(id='legacy_dummy', name='Cardboard dummies, legacy (bola/shim/dot)', skin='bolas', parts='shots/arena/cast/dummy',
         height_cm=185, superseded_by='bola'),
]


# ------------------------------------------------------------------ template geometry (cm)
def template_cards(build, view, legged=False):
    """Every body card of one view as kit.body_template draws it: the card upright, its extent in cm,
    and A/B/sockets in card cm measured from the card's top-left. Exactly the same maths as the
    template, so a card painted into the ghost has these brads."""
    C = K.CHARS[build]
    geo = 'profile' if view == 'profile' else 'front'
    saved = C['pelvis']
    if legged:
        C['pelvis'] = None          # the cards were painted with thighs and a hip bridge, not a skirt
    try:
        sh, J = K.shapes(build, geo)
    finally:
        C['pelvis'] = saved
    by = {n: (p, js) for n, p, js in sh}
    out = {}
    for name, (poly, (ja, jb)) in by.items():
        if name in ('neck', 'hair', 'head'):
            continue
        P = np.array(poly, float)
        A = np.array(J[ja]) if ja in J else P.mean(0)
        B = np.array(J[jb]) if jb in J else P.mean(0)
        if name == 'torso':
            A, B = np.array(J['neck']), np.array([J['neck'][0], J['hipL'][1]])
        if name == 'pelvis':
            A = np.array([0.0, C['J']['hipL'][1] + 6])
            B = np.array([0.0, C['J']['kneeL'][1] + 4])
        v = B - A
        th = -math.atan2(v[0], -v[1]) if name not in ('foot.L', 'foot.R', 'torso', 'pelvis') else 0
        R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
        Q = (P - A) @ R.T
        Bq = (B - A) @ R.T
        mn, mx = Q.min(0), Q.max(0)
        card = lambda q: [float(q[0] - mn[0]), float(mx[1] - q[1])]      # cm from the card's top-left, y down
        rec = {'ext_cm': [float(mx[0] - mn[0]), float(mx[1] - mn[1])], 'A': card((0, 0)), 'B': card(Bq),
               'len_cm': float(np.linalg.norm(B - A))}
        if name in ('torso', 'pelvis'):
            socks = {}
            keys = ('shoulderL', 'shoulderR', 'hipL', 'hipR') if name == 'torso' else ('hipL', 'hipR')
            for k in keys:
                socks[k] = card((np.array(J[k]) - A) @ R.T)
            if name == 'pelvis':
                kn = {}
                for s in ('L', 'R'):
                    kn['knee' + s] = card((np.array(J['knee' + s]) + np.array([0, 4.0]) - A) @ R.T)
                socks.update(kn)
            rec['sockets'] = socks
        if name.startswith('foot'):
            s = name[-1]
            rec['toe'] = card((np.array(J['toe' + s]) - A) @ R.T)
            rec['heel'] = card((np.array(J['heel' + s]) - A) @ R.T)
        out[name] = rec
    return out


def template_head(build, view):
    """kit.heads_template: the plate is an ellipse rx, ry with a neck tab 6 cm below it; the cards are
    cut from the ink, so crown (or hair top) is the card top and the neck cross the card bottom."""
    C = K.CHARS[build]
    r = C['J']['crown'][1] - C['J']['head'][1]
    ry = r * 1.08
    rx = r * (0.8 if build != 'dotd' else 1) * (1.05 if 'profile' in view else 1)
    h = 2 * ry + 6.0
    top_extra = 0.0
    if C.get('hair') == 'afro':
        top_extra = ry * 0.3 + 10 / 12.0
    return {'ext_cm': [2 * rx, h + top_extra], 'plate_h_cm': 2 * ry, 'neck_tab_cm': 6.0, 'hair_cm': top_extra,
            'crown_to_chin_cm': float(C['J']['crown'][1] - C['J']['chin'][1])}


def skeleton(build, k=1.0):
    """The build's rest skeleton (cm, y up), scaled to a real height by k."""
    J = K.CHARS[build]['J']
    return {n: (np.array(p, float) * k).tolist() for n, p in J.items()}


# ------------------------------------------------------------------ measuring the cut parts
def ink_box(path, thr=128):
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im)[:, :, 3]
    ys, xs = np.where(a > thr)
    if not len(xs):
        return None, im.size
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1], im.size


def neck_tab_x(path, box):
    a = np.asarray(Image.open(path).convert('RGBA'))[:, :, 3]
    y0 = box[3] - max(3, int((box[3] - box[1]) * 0.06))
    xs = np.where(a[y0:box[3]].max(0) > 24)[0]
    return float(xs.mean()) if len(xs) else (box[0] + box[2]) / 2


def file_for(d, view, name):
    """body.<view>.<name>.png in the character's dir; profile far-side cards fall back to the near ones."""
    p = os.path.join(PARTS_DIR, d, f'body.{view}.{name}.png')
    if os.path.exists(p):
        return p, False
    if name.endswith('.R'):
        q = os.path.join(PARTS_DIR, d, f'body.{view}.{name[:-2]}.L.png')
        if os.path.exists(q):
            return q, True
    return None, False


def measure_character(c):
    build = c['build']
    k = c['height_cm'] / K.CHARS[build]['height']
    rec = {'id': c['id'], 'dir': c['dir'], 'build': build, 'build_height_cm': K.CHARS[build]['height'], 'k': round(k, 4),
           'views': {}, 'heads': {}}
    legged = c.get('rig') == 'legged'
    rec['rig'] = 'legged' if legged else ('skirt' if K.CHARS[build]['pelvis'] == 'skirt' else 'jointed')
    for view in VIEWS:
        tc = template_cards(build, view, legged)
        parts = {}
        for name, t in tc.items():
            p, mirrored = file_for(c['dir'], view, name)
            if not p:
                continue
            box, size = ink_box(p)
            if not box:
                continue
            w, h = box[2] - box[0], box[3] - box[1]
            ppc_w, ppc_h = w / t['ext_cm'][0], h / t['ext_cm'][1]
            # limbs and the torso are scaled by their length (the axis the brads sit on), feet by their length too
            ppc = ppc_w if name.startswith('foot') else ppc_h
            P = lambda q: [round(box[0] + q[0] * ppc_w, 1), round(box[1] + q[1] * ppc_h, 1)]
            if name.startswith('foot'):
                # a shoe is painted taller than its ghost (the boot shaft): keep ONE scale (along the sole) and
                # hang the ankle brad its real height above the sole line, which is the card's bottom edge
                e_h = t['ext_cm'][1]
                P = lambda q, e_h=e_h: [round(box[0] + q[0] * ppc_w, 1), round(box[3] - (e_h - q[1]) * ppc_w, 1)]
            pr = {'file': os.path.relpath(p, SHOTS), 'size': list(size), 'ink': box, 'px_per_cm': round(ppc, 3),
                  'aspect_fidelity': round(ppc_w / ppc_h, 3), 'A': P(t['A']), 'B': P(t['B']), 'len_cm': round(t['len_cm'], 1),
                  'far_from_near': mirrored}
            if 'sockets' in t:
                pr['sockets'] = {s: P(q) for s, q in t['sockets'].items()}
            if 'toe' in t:
                pr['toe'], pr['heel'] = P(t['toe']), P(t['heel'])
            parts[name] = pr
        if legged:
            # the painted hip bridge (a triangle: waist brad on top, hip brads at the corners) sits behind the thighs
            p = os.path.join(PARTS_DIR, c['dir'], f'body.{view}.pelvis.png')
            if os.path.exists(p):
                box, size = ink_box(p)
                C = K.CHARS[build]
                w_cm = 2 * abs(C['J']['hipL'][0]) + C['w']['thigh'][0]
                ppc = (box[2] - box[0]) / w_cm
                parts['bridge'] = {'file': os.path.relpath(p, SHOTS), 'size': list(size), 'ink': box, 'px_per_cm': round(ppc, 3),
                                   'A': [round((box[0] + box[2]) / 2, 1), round(box[1] + 0.12 * (box[3] - box[1]), 1)],
                                   'B': [round((box[0] + box[2]) / 2, 1), float(box[3])], 'len_cm': round((box[3] - box[1]) / ppc, 1)}
        ov = c.get('skirt_overlay')
        if ov and view == 'profile':
            p = os.path.join(PARTS_DIR, c['dir'], ov)
            box, size = ink_box(p)
            C = K.CHARS[build]
            h_cm = (C['J']['hipL'][1] + 6) - (C['J']['kneeL'][1] + 4)
            ppc = (box[3] - box[1]) / h_cm
            parts['overlay_skirt'] = {'file': os.path.relpath(p, SHOTS), 'size': list(size), 'ink': box, 'px_per_cm': round(ppc, 3),
                                      'A': [round((box[0] + box[2]) / 2, 1), float(box[1] + 0.02 * (box[3] - box[1]))],
                                      'B': [round((box[0] + box[2]) / 2, 1), float(box[3])], 'len_cm': round(h_cm, 1)}
        if parts:
            rec['views'][view] = parts
        # head for this view
        hd = c.get('head_from') or c['dir']
        hp = os.path.join(PARTS_DIR, hd, f'head.{view}.png')
        if not os.path.exists(hp) and view == 'threequarter_back':
            hp = os.path.join(PARTS_DIR, hd, 'head.back.png')
        if os.path.exists(hp):
            box, size = ink_box(hp)
            th = template_head(build, view)
            w, h = box[2] - box[0], box[3] - box[1]
            ppc_h, ppc_w = h / th['ext_cm'][1], w / th['ext_cm'][0]
            ppc = ppc_h      # heads by height: the plate plus its neck tab (headwear is counted, and reported)
            nx = neck_tab_x(hp, box)
            # the heads sheet paints a 6 cm neck tab for everyone; a build with a shorter neck (children, dummies)
            # needs less, so its brad goes further up the tab and the rest tucks under the collar
            J = K.CHARS[build]['J']
            tab_needed = (J['head'][1] - (J['crown'][1] - J['head'][1]) * 1.08) - J['neck'][1]
            up = max(0.04 * h, (6.0 - tab_needed) * ppc)
            rec['heads'][view] = {'file': os.path.relpath(hp, SHOTS), 'size': list(size), 'ink': box, 'px_per_cm': round(ppc, 3),
                                  'aspect_fidelity': round(ppc_w / ppc_h, 3), 'neck': [round(nx, 1), round(box[3] - up, 1)], 'neck_tab_needed_cm': round(tab_needed, 1),
                                  'crown': [round(nx, 1), float(box[1])], 'borrowed_from': c.get('head_from'),
                                  'plate_h_cm': round(th['plate_h_cm'], 1), 'crown_to_chin_cm': round(th['crown_to_chin_cm'], 1)}
    # wings (angels): no template ghost, scaled to the canonical 1.35 x torso length (rig library table)
    if c.get('wings'):
        rec['wings'] = {}
        for view in ('back', 'front'):
            for s in ('L', 'R'):
                p = os.path.join(PARTS_DIR, c['dir'], f'body.{view}.wing.{s}.png')
                if os.path.exists(p):
                    box, size = ink_box(p)
                    rec['wings'][f'{view}.{s}'] = {'file': os.path.relpath(p, SHOTS), 'ink': box, 'size': list(size)}
    return rec


def sheet_scale_report(rec):
    """How consistent is each character's own painting scale? (px_per_cm per part, profile view)."""
    pv = rec['views'].get('profile', {})
    vals = {n: p['px_per_cm'] for n, p in pv.items() if not p.get('far_from_near') and n not in ('bridge', 'overlay_skirt')}
    if not vals:
        return {}
    med = float(np.median(list(vals.values())))
    out = {'median_px_per_cm': round(med, 2), 'spread': round(max(vals.values()) / min(vals.values()), 2),
           'outliers': {n: round(v / med, 2) for n, v in vals.items() if abs(v / med - 1) > 0.2}}
    hd = rec['heads'].get('profile')
    if hd:
        out['head_vs_body'] = round(hd['px_per_cm'] / med, 2)
    return out


def main():
    out = {'about': 'Every cut part of the cast measured against its Kit 3 template: px_per_cm per part, A/B pivots and sockets in '
                    'the part file\'s own pixels. Written by shots/suite/lib/castkit.py.', 'characters': {}}
    for c in CAST:
        rec = measure_character(c)
        rec['sheet_scale'] = sheet_scale_report(rec)
        out['characters'][c['id']] = rec
        print(c['id'], {v: len(p) for v, p in rec['views'].items()}, 'heads', list(rec['heads']), rec['sheet_scale'])
    json.dump(out, open(os.path.join(SUITE, 'data', 'cast_parts.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
