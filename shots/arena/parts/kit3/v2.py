"""Character Kits v2: a Kit 3 pack set for every character of the WYGWYL suite and of Bolas.

    python3 shots/arena/parts/kit3/v2.py        # writes kit3/v2/ (templates, packs, kits.json)

Same paradigm as Kit 3 (kit.py, packs.py), not a rewrite: each character's build is one more
rest skeleton registered beside the man, the poet and Dot, and kit.py's own functions draw its
cut chart and templates; each sheet becomes one image (A layout, B who, C style) and one prompt.

v2 casting, from the assembly treatment (shots/poems/assembly) and the suite's world modules:
  POET       a man: the photos' man. Black t-shirt in 01-03, the red/black outfit with
             sunglasses from 04 Nevermore on.
  EX         a man whose face is never seen: back and three-quarter back only.
  YOUNG_POET the poet at six (a boy); GHOST_CHILD the dead seven-year-old.
  the woman  the puppet the arena called "the poet" until now. She is renamed so that
             "poet" means the man; in the poems she plays the women's parts (MOTHER, SHE).
  extras     parents, ancestors, Atlantis citizens, club crowd, angels, elders, couples ...
  Bolas      Bola, Shim and Dot, the Crash Lab dummies, in cardboard.
Per poem, each character also gets an ACTION sheet: that poem's poses (replacement cards),
special hands (in a pocket, missing, detachable) and the props it holds, each in a cell.
"""
import glob, json, os, sys, textwrap
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit as K
import packs as PKS
from kit import font, FONTB, FONT, MONO, INK, sheet_frame, cross, SOCK_A, SOCK_B, GHOST

SHOTS = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, 'v2')
BD = os.path.join(SHOTS, 'poems', 'breakdown')
SHEETS = os.path.join(SHOTS, 'weave', 'cast', 'man', 'sheets')
DUMMY = os.path.join(SHOTS, 'arena', 'cast', 'dummy')


def scaled(shape, k):
    return [(x * k, y * k) for x, y in shape]


M, W_, D = K.CHARS['man'], K.CHARS['poet'], K.CHARS['dot']
# ------------------------------------------------------------------ builds (one skeleton each)
BUILDS = {
    'poetm': dict(label='The poet', plays='POET', height=184, J=K.humanoid(184, 21, 9.5, 12.0), w=M['w'],
                  torso_front=M['torso_front'], torso_profile=M['torso_profile'], pelvis=None, hair=None,
                  face=['eyes', 'brows', 'mouth', 'glasses'], feet='boot', look=''),
    'ex': dict(label='The ex', plays='EX', height=188, J=K.humanoid(188, 22.5, 10, 12.0),
               w={'uarm': (14, 12), 'farm': (12, 10), 'hand': (9.5, 8.5), 'thigh': (21, 15), 'shin': (15, 11)},
               torso_front=scaled(M['torso_front'], 1.05), torso_profile=scaled(M['torso_profile'], 1.05), pelvis=None, hair=None,
               face=['eyes', 'brows', 'mouth'], feet='boot', look=''),
    'boy': dict(label='The young poet', plays='YOUNG_POET', height=116, J=K.humanoid(116, 12.5, 6.5, 11.0, neck=4.0, arm=(0.15, 0.135, 0.095), leg=(0.22, 0.21), foot=0.15),
                w={'uarm': (8, 7), 'farm': (7, 6), 'hand': (6.5, 6), 'thigh': (12, 9), 'shin': (9, 7)},
                torso_front=scaled(M['torso_front'], .58), torso_profile=scaled(M['torso_profile'], .58), pelvis=None, hair=None,
                face=['eyes', 'brows', 'mouth'], feet='flat', look=''),
    'ghost': dict(label='The ghost child', plays='GHOST_CHILD', height=122, J=K.humanoid(122, 13, 6.8, 11.2, neck=4.0, arm=(0.15, 0.135, 0.095), leg=(0.22, 0.21), foot=0.15),
                  w={'uarm': (8, 7), 'farm': (7, 6), 'hand': (6.5, 6), 'thigh': (12, 9), 'shin': (9, 7)},
                  torso_front=scaled(M['torso_front'], .6), torso_profile=scaled(M['torso_profile'], .6), pelvis=None, hair=None,
                  face=['eyes', 'brows', 'mouth'], feet='flat', look=''),
    'woman': dict(W_, label='The woman', plays='MOTHER / SHE / women'),
    'manx': dict(label='Man (extra)', plays='fathers, ancestors, citizens, crowd', height=180, J=K.humanoid(180, 20, 9.5, 11.8), w=M['w'],
                 torso_front=scaled(M['torso_front'], .97), torso_profile=scaled(M['torso_profile'], .97), pelvis=None, hair=None,
                 face=['eyes', 'brows', 'mouth'], feet='boot', look=''),
    'robed': dict(label='Robed figure', plays='ancestors, angels, elders in robes', height=182, J=K.humanoid(182, 20, 9.5, 11.8), w=M['w'],
                  torso_front=M['torso_front'], torso_profile=M['torso_profile'], pelvis='skirt', hair=None,
                  face=['eyes', 'brows', 'mouth'], feet='flat', look=''),
    'bola': dict(label='Bola', plays='Bola (Crash Lab)', height=172, J=K.humanoid(172, 17, 8.5, 15.5, neck=3.0), w={'uarm': (9, 8), 'farm': (8, 7.5), 'hand': (8.5, 8), 'thigh': (13, 11), 'shin': (11, 9)},
                 torso_front=scaled(D['torso_front'], 1.55), torso_profile=scaled(D['torso_profile'], 1.55), pelvis=None, hair=None,
                 face=['eyes', 'brows', 'mouth'], feet='dummy', look=''),
    'shim': dict(label='Shim', plays='Shim (Crash Lab)', height=182, J=K.humanoid(182, 18, 9.0, 16.0, neck=3.0), w={'uarm': (9.5, 8.5), 'farm': (8.5, 8), 'hand': (9, 8.5), 'thigh': (14, 11.5), 'shin': (11.5, 9.5)},
                 torso_front=scaled(D['torso_front'], 1.65), torso_profile=scaled(D['torso_profile'], 1.65), pelvis=None, hair=None,
                 face=['eyes', 'brows', 'mouth'], feet='dummy', look=''),
    'dotd': dict(D, label='Dot', plays='Dot (Crash Lab)'),
}
for k, v in BUILDS.items():
    K.CHARS.setdefault(k, v)
    K.ACCENT.setdefault(k, {'poetm': (205, 48, 38), 'ex': (70, 70, 80), 'boy': (214, 150, 40), 'ghost': (110, 150, 190), 'woman': (22, 104, 112),
                            'manx': (120, 100, 80), 'robed': (150, 110, 30), 'bola': (225, 180, 30), 'shim': (25, 160, 140), 'dotd': (230, 110, 95)}[k])

STYLE = lambda *n: [os.path.join(HERE, 'style', x) for x in n]
REF = os.path.join(HERE, 'refs')
MANHEAD = os.path.join(SHOTS, 'arena', 'parts', 'cut', 'man_heads_front', 'neutral.png')
WEAVE = os.path.join(SHOTS, 'weave', 'assets', 'parts')

# ------------------------------------------------------------------ characters and costumes
# who: identity text; refs: panel B images; kits: costume -> (description, poems)
CAST = [
    dict(id='poet', name='POET', build='poetm', principal=True,
         who="THE POET, a man: a Black man in his thirties, dark brown skin, short faded haircut, full well-groomed beard, as in "
             "the reference photos. He is the speaker of every poem.",
         refs=[os.path.join(REF, 'man_tracksuit_front.png'), os.path.join(REF, 'man_tracksuit_threequarter.png'), MANHEAD,
               'crop:' + os.path.join(SHEETS, 'heads.jpg') + ':0,10,262,385'],
         kits={'black_tshirt': ("a plain black crew-neck t-shirt, dark trousers, plain dark sneakers; no glasses", '01 02 03'),
               'red_black_sunglasses': ("the red/black outfit: a black track jacket with red piping from the shoulders down the chest, "
                                        "black track trousers, black Chelsea boots, black sunglasses (the sunglasses are their own "
                                        "plug-in card, never painted onto a head)", '04 05 06 07 08 09 10 11 12 13 14')}),
    dict(id='ex', name='EX', build='ex', principal=True, back_only=True,
         who="THE EX, a man the poet loved. His FACE IS NEVER SEEN: paint him only from behind and three-quarter behind; "
             "the head is the back of the head (short dark hair, the nape, one ear at most). Broad shoulders, slightly taller than the poet.",
         refs=['crop:' + os.path.join(SHEETS, 'heads.jpg') + ':1130,10,1376,385'],
         kits={'ex_jacket': ("a dark olive bomber jacket with a ribbed hem, dark jeans, white low sneakers; a vape pen in one hand in 01", '01 02 03 07 08 09')}),
    dict(id='young_poet', name='YOUNG POET', build='boy', principal=True,
         who="THE YOUNG POET, the poet at six: a small Black boy, dark brown skin, short hair, big watchful eyes; child proportions "
             "(a larger head, short limbs). He grows into the poet (panel B describes him in words only).",
         refs=[],
         kits={'pajamas_winter': ("winter pajamas: a long-sleeved flannel top and trousers in faded blue check, thick socks", '02'),
               'child_clothes': ("a striped t-shirt, shorts, small sneakers", '13')}),
    dict(id='ghost_child', name='GHOST CHILD', build='ghost', principal=True,
         who="THE GHOST CHILD, a dead seven-year-old who appears to the young poet: a small Black child, pale grey-blue all over, "
             "painted as if half see-through (a thin wash, the cardboard showing through), calm and sad.",
         refs=[],
         kits={'ghost_nightclothes': ("a long pale nightshirt, bare feet", '02')}),
    dict(id='woman', name='THE WOMAN (was "the poet" puppet)', build='woman', principal=True,
         who="THE WOMAN, the puppet the arena used to call 'the poet' (renamed: the poet is now the man). A Black woman, dark brown "
             "skin, a full rounded afro, eyes OPEN. In the poems she plays the women: the MOTHER (09), SHE in the far window (13).",
         refs=[os.path.join(WEAVE, 'head.png'), os.path.join(WEAVE, 'torso.png'), os.path.join(WEAVE, 'skirt.png')],
         kits={'teal_dress': ("her teal dress with the gold floral print (her current cards, redrawn with open eyes)", 'arena'),
               'mother_cardigan': ("a long grey cardigan over a house dress, slippers", '02 09'),
               'window_woman_dress': ("a red summer dress, seen far off in a lit window", '13')}),
    dict(id='parents', name='PARENTS', build='manx',
         who="THE POET'S PARENTS in 1990s winter clothes, seen arguing in the car at night (02) and in memory (09).",
         refs=[], kits={'parent_coat': ("a heavy 1990s winter coat, scarf; the father bearded, the mother with her hair up", '02'),
                               'elder_father_coat': ("the father older: a long grey overcoat, flat cap, a cane", '09')}),
    dict(id='ancestors', name='ANCESTORS', build='robed',
         who="THE ANCESTORS, an afro-futuristic welcoming parade of Black elders and young people who give the poet stars, galaxies and universes (05).",
         refs=[], kits={'ancestor_robe_indigo_gold': ("a floor-length indigo robe with gold kente-pattern panels, copper shoulder plates, stacked neck rings, a beaded headwrap/crown with thin light filaments, cowrie-shell cuffs", '05'),
                        'ancestor_elder_white_silver': ("a white and silver robe, a silver collar, a tall white headwrap, a carved staff", '05')}),
    dict(id='atlantis', name='ATLANTIS PEOPLE', build='manx',
         who="THE PEOPLE OF RESURRECTED ATLANTIS (06): travellers arriving, citizens in a lit afro-futurist city, a gatekeeper at the admission booth, an old man with a lantern.",
         refs=[], kits={'atlantis_traveler': ("plain travel clothes, long coats, shoulder bags", '06'),
                        'atlantis_citizen': ("light layered linen with neon-thread trim", '06'),
                        'atlantis_gatekeeper': ("a booth uniform with a high collar and a brass badge", '06'),
                        'poet_elder_coat': ("a long patched coat, a scarf, carrying an oil lantern", '06')}),
    dict(id='party', name='PARTY, CLUB AND DJ', build='manx',
         who="THE PARTY AND CLUB PEOPLE: the vintage party guests in romantic slow motion (01, 14), the DJ and the house-party guests (07), the club crowd (08, 09).",
         refs=[], kits={'vintage_party': ("old-time evening wear: a 1940s suit and tie, a satin gown with gloves", '01 14'),
                        'dj_cyber': ("a bomber jacket with LED piping, a cap, headphones round the neck", '07'),
                        'party_guest': ("night-out clothes, several variants", '06 07'),
                        'club_dress': ("a short sequinned club dress", '08 09'), 'club_shirt': ("an open silk shirt", '08 09'),
                        'club_jacket': ("a cropped leather jacket", '08 09')}),
    dict(id='angels', name='ANGELS', build='robed',
         who="THE ANGELS of 08 Newly Single: robed figures with large white wings who float and pour water.",
         refs=[], kits={'angel_white_robe': ("white robes, large white feathered wings on their own cards (pinned at the shoulder blades)", '08')}),
    dict(id='family', name='BROTHER, FRIENDS, ELDERS, COUPLES', build='manx',
         who="THE FAMILY AND FRIENDS of the later poems: the brother and friends at the reunion (12), the remembered elders (12), the elders at prayer and the couples of 13, everyday people (14).",
         refs=[], kits={'brother_casual': ("a hoodie, jeans, sneakers", '12'), 'friend_casual': ("a jacket over a t-shirt, chinos", '12'),
                        'elder_memory_silhouette': ("a pale backlit figure, almost a silhouette", '12'),
                        'elder_robe_pearls': ("a church robe and pearls, kneeling in a pew", '13'),
                        'couple_summer_casual': ("summer clothes: linen shirts, light dresses", '13'), 'street_clothes': ("everyday street clothes", '10 14')}),
    dict(id='bola', name='BOLA (Bolas)', build='bola', principal=True, bolas=True,
         who="BOLA, the Crash Lab's lead crash-test dummy, rebuilt in painted cardboard from the lab drawing in panel B: a "
             "yellow (#ffd23f) round head and rounded torso, a black-and-yellow quartered crash target on each side of the head, "
             "a thin black antenna with a red ball on top, black stick arms and legs, white cartoon gloves, red shoes. Her face "
             "is drawn by code (eyes, brows, mouth), so every head plate stays blank yellow.",
         refs=[os.path.join(REF, 'bolas_bola.png')], kits={'crash_yellow': ("the yellow dummy", 'bolas')}),
    dict(id='shim', name='SHIM (Bolas)', build='shim', principal=True, bolas=True,
         who="SHIM, the Crash Lab's second dummy, a little taller, in painted cardboard from panel B: a teal (#19c9ae) round "
             "head and torso, crash targets on the head, a small blue triangular fin on the crown, black stick arms and legs, "
             "white gloves, blue shoes. His face is drawn by code, so the head plates stay blank teal.",
         refs=[os.path.join(REF, 'bolas_shim.png')], kits={'crash_teal': ("the teal dummy", 'bolas')}),
    dict(id='dot', name='DOT (Bolas)', build='dotd', principal=True, bolas=True,
         who="DOT, the little one: the Crash Lab's child-sized dummy in painted cardboard: a coral (#ff7a6b) round head and "
             "torso, crash targets on the head, a small red bow on top, black stick arms and legs, white gloves, black shoes "
             "(the arena's mustard cardboard Dot is the same character). Her face is drawn by code, so the head plates stay blank.",
         refs=[os.path.join(REF, 'bolas_dot.png'), os.path.join(DUMMY, 'dot.torso_front.png')], kits={'crash_dot': ("the little dummy", 'bolas')}),
]

SHEETS_FULL = ['body.front', 'body.threequarter', 'body.back', 'body.profile', 'heads', 'face.front', 'face.profile', 'hands', 'feet', 'replacements']
SHEETS_BACK = ['body.back', 'body.threequarter_back', 'heads', 'hands', 'feet']
SHEETS_EXTRA = ['body.front', 'body.back', 'body.profile', 'heads', 'hands']
SHEET_STYLE = {'body': ('craft_legs.jpg', 'craft_arms.jpg', 'craft_head_turn.jpg'), 'heads': ('craft_head_turn.jpg', 'craft_heads_expr.jpg'),
               'face': ('craft_heads_expr.jpg', 'craft_head_turn.jpg'), 'hands': ('craft_hands.jpg', 'craft_hands_2.jpg', 'craft_grips.jpg'),
               'feet': ('craft_legs.jpg', 'craft_legs_run.jpg'), 'replacements': ('craft_seated.jpg', 'craft_legs_run.jpg', 'craft_legs.jpg'),
               'action': ('craft_seated.jpg', 'craft_grips.jpg', 'craft_legs_run.jpg')}
JOBS = {
    'body.front': "the body cards facing the viewer", 'body.threequarter': "the body cards turned three-quarters to screen right",
    'body.back': "the body cards seen from directly behind (the back of the clothes: no face, no zip, no buttons)",
    'body.threequarter_back': "the body cards turned three-quarters AWAY from the viewer (we see the back and one shoulder, never the face)",
    'body.profile': "the body cards in strict profile facing screen right",
    'heads': "BLANK head plates in five views (front, three-quarter, profile, three-quarter back, back) with their neck tabs: no eyes, no brows, no mouth, no glasses; keep skin, hair, ears, nose and beard",
    'face.front': "the face plug-ins, front: a blank plate, 8 pairs of eyes, 6 pairs of brows, 12 mouths, each centred on its cross",
    'face.profile': "the face plug-ins, profile: a blank plate, eyes, brows and mouths for the side view",
    'hands': "the RIGHT hand only (the left is its mirror), 12 shapes from the back and the palm, each on a cardboard tab with a brass eyelet on the green cross",
    'feet': "the RIGHT shoe/boot in six states (flat, heel up, toe up, front, back, three-quarter), the ankle brad on the green cross",
    'replacements': "whole-body replacement cards for poses a jointed puppet cannot hold (sitting, kneeling, lying on the back and side, deep crouch, falling), one brass brad at the hip, head and hands left off",
}


def template_for(build, sheet):
    """kit.py's own template for this build and sheet (drawn once, cached in v2/templates)."""
    td = os.path.join(OUT, 'templates')
    os.makedirs(td, exist_ok=True)
    p = os.path.join(td, f'{build}.{sheet}.png')
    if not os.path.exists(p):
        reg = {}
        kind = sheet.split('.')[0]
        if kind == 'body':
            view = sheet.split('.')[1]
            geo = 'profile' if view == 'profile' else 'front'
            K.body_template(build, geo, reg, view).save(p)
        elif kind == 'heads':
            K.heads_template(build, reg).save(p)
        elif kind == 'face':
            K.face_template(build, sheet.split('.')[1], reg).save(p)
        elif kind == 'hands':
            K.hands_template(build, reg).save(p)
        elif kind == 'feet':
            K.feet_template(build, reg).save(p)
        elif kind == 'replacements':
            PKS.replacement_template(build).save(p)
    return Image.open(p)


def compose(a_img, refs, b_text, style, b_title):
    """One pack image: A the template, B who (images + text), C style crops."""
    Wd, Hd = 2688, 1560
    im = Image.new('RGB', (Wd, Hd), (255, 255, 255))
    d = ImageDraw.Draw(im)
    im.paste(a_img.convert('RGB').resize((2048, 1152)), (0, 0))
    d.rectangle([0, 0, 2047, 1151], outline=INK, width=3)
    d.rectangle([0, 1108, 420, 1151], fill=INK)
    d.text((14, 1114), 'A · LAYOUT: paint into this', font=font(FONTB, 22), fill=(255, 255, 255))
    d.text((2068, 14), 'B · WHO', font=font(FONTB, 26), fill=INK)
    d.text((2068, 48), b_title[:42], font=font(FONT, 19), fill=(110, 100, 90))
    y = 84
    for r in refs[:3]:
        try:
            t = PKS.load(r, (600, 250))
        except Exception:
            continue
        im.paste(t, (2068 + (600 - t.width) // 2, y))
        y += t.height + 10
    for ln in textwrap.wrap(b_text, 46):
        if y > 1130:
            break
        d.text((2068, y), ln, font=font(FONT, 17), fill=INK)
        y += 22
    d.text((20, 1172), 'C · STYLE: copy the cardboard craft, not these clothes', font=font(FONTB, 26), fill=INK)
    x = 20
    for p in style:
        t = PKS.load(p, (880, 340))
        im.paste(t, (x, 1210))
        x += t.width + 16
    return im


def prompt(c, costume, desc, sheet, poems):
    job = JOBS.get(sheet, sheet)
    back = (" HIS FACE IS NEVER SEEN: no front view of the head, no face anywhere on the sheet." if c.get('back_only') else '')
    return (PKS.TEXT.replace('panel B is who the character is', 'panel B is who the character is (reference only: copy the person, '
                             'not the photo style)') + f"WHO (panel B): {c['who']} COSTUME: {desc}." + back +
            f" SHEET: {job}." + (" This is a v2 kit for the WYGWYL film, poems " + poems + "." if poems not in ('arena', 'bolas') else
                                 " This is a v2 kit for the " + ("Crash Lab (Bolas) dummies." if poems == 'bolas' else "acting arena.")) +
            " " + PKS.RULES)


# ------------------------------------------------------------------ per-poem action sheets
POSE_HIP = {'lie': 14, 'fall': 60, 'float': 70, 'sit': 50, 'kneel': 62, 'crouch': 45}


def action_template(c, poem, uses):
    """One poem's sheet for one character: its poses there (replacement cells with a hip brad),
    its special hands, the props it holds (grip on red)."""
    b = K.CHARS[c['build']]
    px = 3.6 if b['height'] > 140 else 5.0
    im, d = sheet_frame(f"{c['id']}.{poem['num']}.action", f"{c['name']} in {poem['num']} {poem['title']} · this poem's poses, hands and held props · hip brad on green, grips on red", px)
    poses = uses['poses'][:6]
    cw = (K.SHEET_W - 120) / max(1, min(6, len(poses)))
    for i, (pose, view, line) in enumerate(poses):
        x0, y0 = 60 + cw * i, 120
        floor = y0 + 560
        d.rectangle([x0 + 6, y0, x0 + cw - 6, floor + 18], outline=(222, 216, 206), width=1)
        d.line([(x0 + 14, floor), (x0 + cw - 14, floor)], fill=(200, 192, 180), width=2)
        hip = POSE_HIP.get(pose, 95 if b['height'] > 140 else 60)
        cross(d, (x0 + cw / 2, floor - hip * px), SOCK_A, 'hip')
        d.text((x0 + 14, y0 + 10), f"{pose} · {view}", font=font(FONTB, 17), fill=INK)
        for k, ln in enumerate(textwrap.wrap(line, int(cw / 9))[:3]):
            d.text((x0 + 14, y0 + 34 + k * 18), ln, font=font(FONT, 14), fill=(110, 100, 90))
    # hands and props row
    y = 740
    d.text((60, y), 'HANDS IN THIS POEM', font=font(FONTB, 18), fill=INK)
    x = 60
    for shape, holds in uses['hands'][:8]:
        d.rectangle([x, y + 30, x + 210, y + 170], outline=(222, 216, 206))
        cross(d, (x + 30, y + 100), SOCK_A)
        if holds:
            cross(d, (x + 140, y + 100), SOCK_B, r=7)
        d.text((x + 8, y + 36), f"{shape}" + (f" · {holds}" if holds else ''), font=font(MONO, 13), fill=INK)
        x += 225
    y = 930
    d.text((60, y), 'PROPS THIS CHARACTER HOLDS OR TOUCHES', font=font(FONTB, 18), fill=INK)
    x = 60
    for pid, what, sc in uses['props'][:9]:
        s = max(50, min(170, float(sc or 20) * 3))
        d.rectangle([x, y + 30, x + s, y + 30 + s * .7], fill=GHOST)
        cross(d, (x + s / 2, y + 30 + s * .35), SOCK_B, r=6)
        d.text((x, y + 36 + s * .7), pid[:22], font=font(MONO, 12), fill=INK)
        x += s + 40
    return im


def poem_uses(P, role_test):
    poses, hands, props, seen = [], [], [], set()
    pmap = {p['id']: p for p in (P.get('needs') or {}).get('props') or [] if isinstance(p, dict) and p.get('id')}
    for sc in P.get('scenes') or []:
        for sh in sc.get('shots') or []:
            for b in sh.get('bodies') or []:
                if not role_test(b):
                    continue
                k = (b.get('pose'), b.get('view'))
                if k not in seen and b.get('pose') not in (None, 'stand', 'walk'):
                    seen.add(k)
                    poses.append((b.get('pose'), b.get('view'), b.get('action') or sh.get('action', '')))
                for s in 'LR':
                    h = (b.get('hands') or {}).get(s) or {}
                    t = (h.get('shape') or 'relaxed', h.get('holds'))
                    if t[0] not in ('relaxed',) and t not in hands:
                        hands.append(t)
                    if h.get('holds') and h['holds'] not in [p[0] for p in props]:
                        e = pmap.get(h['holds'], {})
                        props.append((h['holds'], e.get('what', ''), e.get('scale_cm')))
    if not poses:
        poses = [('stand', 'front', 'stands and walks only in this poem')]
    return {'poses': poses, 'hands': hands, 'props': props}


def costume_of(b):
    return (b.get('costume') or '').strip()


def main():
    os.makedirs(os.path.join(OUT, 'packs'), exist_ok=True)
    kits, out = [], {'about': __doc__.strip().split('\n')[0], 'cast': [], 'poems': []}
    for c in CAST:
        sheets = SHEETS_BACK if c.get('back_only') else (SHEETS_FULL if c.get('principal') else SHEETS_EXTRA)
        entry = {'id': c['id'], 'name': c['name'], 'build': c['build'], 'height_cm': K.CHARS[c['build']]['height'], 'who': c['who'], 'costumes': []}
        for cos, (desc, poems) in c['kits'].items():
            packs = []
            for sh in sheets:
                kind = sh.split('.')[0]
                tpl = template_for(c['build'], sh)
                pid = f"{c['id']}.{cos}.{sh}"
                sty = STYLE('craft_dummy.jpg', *SHEET_STYLE[kind][:2]) if c.get('bolas') else STYLE(*SHEET_STYLE[kind])
                img = compose(tpl, c['refs'], f"{desc}.", sty, f"{c['name']} · {cos.replace('_', ' ')}")
                img.save(os.path.join(OUT, 'packs', pid + '.jpg'), quality=80)
                packs.append({'id': pid, 'sheet': sh, 'image': f'v2/packs/{pid}.jpg', 'prompt': prompt(c, cos, desc, sh, poems)})
            entry['costumes'].append({'costume': cos, 'what': desc, 'poems': poems.split(), 'packs': packs})
            print(c['id'], cos, len(packs))
        out['cast'].append(entry)
    # per poem: who is in it, in which costume, and each character's action sheet
    roles = {'POET': 'poet', 'EX': 'ex', 'YOUNG_POET': 'young_poet', 'GHOST_CHILD': 'ghost_child', 'MOTHER': 'woman', 'SHE': 'woman'}
    bycos = {cos: c for c in CAST for cos in c['kits']}
    for f in sorted(glob.glob(os.path.join(BD, '[0-9][0-9].json'))):
        P = json.load(open(f))
        P['num'] = P.get('num') or os.path.basename(f)[:2]
        present = {}
        for sc in P.get('scenes') or []:
            for sh in sc.get('shots') or []:
                for b in sh.get('bodies') or []:
                    cos = costume_of(b)
                    role = (b.get('role') or '').upper()
                    cid = roles.get(role) or roles.get(role.rsplit('_', 1)[0])
                    c = next((x for x in CAST if x['id'] == cid), None) or bycos.get(cos)
                    if c is None:
                        continue
                    present.setdefault(c['id'], set()).add(cos)
        chars = []
        for cid, coss in present.items():
            c = next(x for x in CAST if x['id'] == cid)
            if cid in ('poet', 'ex', 'young_poet', 'ghost_child'):
                test = lambda b, cid=cid: roles.get(b.get('role')) == cid
            else:
                test = lambda b, coss=coss: costume_of(b) in coss
            uses = poem_uses(P, test)
            tpl = action_template(c, P, uses)
            pid = f"{cid}.{P['num']}.action"
            lines = [f"{p}: {w}" for p, w, s in uses['props']]
            desc = '; '.join(f"{a} ({v}): {l}" for a, v, l in uses['poses'][:6])
            img = compose(tpl, c['refs'], f"In {P['title']}: " + desc[:500], STYLE(*SHEET_STYLE['action']), f"{c['name']} · {P['num']} {P['title']}")
            img.save(os.path.join(OUT, 'packs', pid + '.jpg'), quality=80)
            pr = (PKS.TEXT + f"WHO (panel B): {c['who']} COSTUME in this poem: " + ', '.join(c['kits'].get(x, (x,))[0] for x in sorted(coss) if x) + ". " +
                  f"SHEET: {c['name']}'s action sheet for the poem '{P['title']}': one whole-body replacement card per cell for these poses, "
                  f"each with a brass brad at the hip on the green cross, head and hands left off: {desc}. "
                  + (f"Below them, the hands this poem needs ({', '.join(h + (' holding ' + str(o) if o else '') for h, o in uses['hands'][:8])}) "
                     "on eyelet tabs, " if uses['hands'] else '')
                  + (f"and the props this character holds, each in its own cell with its grip on the red cross: {'; '.join(lines)}. " if lines else '')
                  + ("HIS FACE IS NEVER SEEN. " if c.get('back_only') else '') + PKS.RULES)
            chars.append({'id': cid, 'name': c['name'], 'costumes': sorted(x for x in coss if x), 'action': {'id': pid, 'image': f'v2/packs/{pid}.jpg', 'prompt': pr},
                          'poses': [p[0] + ' · ' + p[1] for p in uses['poses']], 'hands': [h + (f'({o})' if o else '') for h, o in uses['hands']], 'props': [p[0] for p in uses['props']]})
        out['poems'].append({'num': P['num'], 'title': P.get('title'), 'style': P.get('style'), 'characters': chars})
        print(P['num'], P.get('title'), [x['id'] for x in chars])
    # cut charts for every build
    for b in BUILDS:
        p = os.path.join(OUT, 'templates', f'{b}.cutchart.png')
        if not os.path.exists(p):
            K.cut_chart(b).save(p)
    json.dump(out, open(os.path.join(OUT, 'kits.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
