"""One image + one prompt per sheet: everything a generator needs, ready to paste.

    python3 shots/arena/parts/kit3/packs.py      # writes kit3/packs/<sheet>.jpg and kit3/packs.json

Each pack image has three labelled panels:
  A  LAYOUT   the sheet's template (kit.py): ghosts to paint inside, brads already placed
  B  WHO      the character: the man's photos, the poet's and Dot's current cards
  C  STYLE    cut-out references from our own cardboard sheets, chosen for the sheet's job
and its prompt refers to the panels by letter. So one image and one text go to the model.
"""
import json, os
from PIL import Image, ImageDraw
import kit
from kit import font, FONTB, FONT, MONO, SERIF, INK, PAPER, sheet_frame, cross, SOCK_A
from prompts import prompts, IDENTITY

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUTD = os.path.join(HERE, 'packs')
W, H = 2688, 1560
SHEETS = os.path.join(SHOTS, 'weave', 'cast', 'man', 'sheets')

WHO = {
    'man': [os.path.join(HERE, 'refs', 'man_tracksuit_front.png'), os.path.join(HERE, 'refs', 'man_tracksuit_threequarter.png'),
            os.path.join(SHOTS, 'arena', 'parts', 'cut', 'man_heads_front', 'neutral.png'), 'crop:' + os.path.join(SHEETS, 'heads.jpg') + ':0,10,262,385'],
    'poet': ['fusion:open', os.path.join(SHOTS, 'weave', 'assets', 'parts', 'torso.png'),
             os.path.join(SHOTS, 'weave', 'assets', 'parts', 'skirt.png'), os.path.join(SHOTS, 'weave', 'assets', 'parts', 'upper_arm_near.png')],
    'dot': [os.path.join(HERE, 'demo', 'dot_coded.jpg'), 'rot:' + os.path.join(SHOTS, 'arena', 'cast', 'dummy', 'dot.torso_front.png'),
            'rot:' + os.path.join(SHOTS, 'arena', 'cast', 'dummy', 'dot.thigh.png'), 'rot:' + os.path.join(SHOTS, 'arena', 'cast', 'dummy', 'dot.hand.open.png')],
}
STYLE_DIR = os.path.join(HERE, 'style')
# only clean crops (style/): the full body sheets carry the shorts / hip card, the vest and the
# lace-up boots, and draw every view as the front; they are poison (see POISON)
STYLE = {
    'body': ['craft_legs.jpg', 'craft_arms.jpg', 'craft_head_turn.jpg'],
    'heads': ['craft_head_turn.jpg', 'craft_heads_expr.jpg'],
    'face': ['craft_heads_expr.jpg', 'craft_head_turn.jpg'],
    'hands': ['craft_hands.jpg', 'craft_hands_2.jpg', 'craft_grips.jpg'],
    'feet': ['craft_legs.jpg', 'craft_legs_run.jpg'],
    'replacements': ['craft_seated.jpg', 'craft_legs_run.jpg', 'craft_legs.jpg'],
}
POISON = [
    ('body_front.jpg', 'the shorts card: a pelvis / hip piece the rig does not want (it swung out like an apron and made four thighs)'),
    ('body_profile.jpg', 'labelled profile but it is the front drawing again: front vest, front shorts on a side body'),
    ('body_back.jpg', 'the back view is the front vest with its zip, and the same shorts'),
    ('body_threequarter.jpg', 'a fourth copy of the front sheet: nothing turns'),
    ('draft_profile_unriggable.jpg', 'trousers and hips in one card, bare cardboard arms: cannot be rigged'),
    ('heads_front.jpg', 'sunglasses painted onto two heads: they belong on a plug-in card'),
    ('body_sitting.jpg', 'left figure: shorts, vest and sunglasses (the right figure is kept, cropped)'),
]

TEXT = ("Paint one sheet of cut-out puppet parts for a paper-puppet film, using the attached image. "
        "Panel A is the exact layout, panel B is who the character is, panel C is the style. "
        "STYLE (panel C): flat cards cut from corrugated cardboard, gouache with confident ink linework, the flutes faintly "
        "showing through the paint, a thin raw kraft-brown cut edge round every card, brass split-pin brads; shot flat-on, "
        "even light, no shadows, no perspective. Copy the craft from C, not the clothes in it. ")
RULES = ("LAYOUT (panel A): paint one card inside each grey ghost, in the same place, size and angle, inside its dashed "
         "outline; a brass brad exactly on every green cross; each red cross must fall inside that card's rounded end. "
         "NEVER draw a pelvis, hip, shorts or briefs card (the thighs end in a rounded seat that tucks under the hem), "
         "a sleeveless vest, lace-up boots, or sunglasses painted onto a head. "
         "OUTPUT: only the painted cards on a pure white 2048x1152 sheet laid out as panel A. Leave out panels B and C, "
         "the crosses, labels, ruler, dashed lines and ghosts.")


def load(path, box):
    """An image fitted into box (w, h), on white."""
    if path.startswith('fusion:'):
        import sys
        sys.path.insert(0, os.path.join(SHOTS, 'arena', 'puppet'))
        import fusion
        im = fusion.poet_head({'eyes': 'o'})[0]
    elif path.startswith('crop:'):
        f, cb = path[5:].rsplit(':', 1)
        im = Image.open(f).convert('RGBA').crop(tuple(int(v) for v in cb.split(',')))
    elif path.startswith('rot:'):
        im = Image.open(path[4:]).convert('RGBA').rotate(90, expand=True)
    else:
        im = Image.open(path).convert('RGBA')
    im.thumbnail(box, Image.LANCZOS)
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert('RGB')


def replacement_template(cid):
    """Free poses, but on the same scale and floor: one hip brad per card."""
    C = kit.CHARS[cid]
    pxcm = 4.6 if cid != 'dot' else 7.0
    im, d = sheet_frame(f'{cid}.replacements', f"{C['label']} · whole-body replacement cards, same scale as the body sheets · one brad at the hip (green); no head, no hands (they plug in)", pxcm)
    poses = ['sitting on a chair, side view', 'kneeling on one knee', 'lying on the back', 'lying on the side', 'deep crouch', 'falling backwards']
    cw = (kit.SHEET_W - 120) / 3
    for i, p in enumerate(poses):
        x0, y0 = 60 + cw * (i % 3), 130 + (i // 3) * 500
        floor = y0 + 460
        d.rectangle([x0 + 6, y0 + 6, x0 + cw - 6, floor + 20], outline=(222, 216, 206), width=1)
        d.line([(x0 + 20, floor), (x0 + cw - 20, floor)], fill=(200, 192, 180), width=2)
        hip_y = {'lying on the back': 14, 'lying on the side': 16}.get(p, 50 if 'sitting' in p else 70 if 'kneeling' in p else 45 if 'crouch' in p else 60)
        cross(d, (x0 + cw / 2, floor - hip_y * pxcm), SOCK_A, 'hip')
        d.text((x0 + 20, y0 + 16), p, font=font(FONTB, 18), fill=INK)
    return im


def pack(sheet, cid):
    kind = sheet['sheet'].split('.')[0]
    tpl_path = os.path.join(HERE, sheet['template']) if sheet['template'] else None
    im = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    lab = lambda xy, t: d.text(xy, t, font=font(FONTB, 26), fill=INK)
    # A: the template, full size
    tpl = Image.open(tpl_path).convert('RGB') if tpl_path else replacement_template(cid).convert('RGB')
    im.paste(tpl, (0, 0))
    d.rectangle([0, 0, 2047, 1151], outline=INK, width=3)
    d.rectangle([0, 1152 - 44, 420, 1151], fill=INK)
    d.text((14, 1152 - 38), 'A · LAYOUT: paint into this', font=font(FONTB, 22), fill=(255, 255, 255))
    # B: who
    x0 = 2048 + 20
    lab((x0, 14), 'B · WHO')
    d.text((x0, 48), kit.CHARS[cid]['label'], font=font(FONT, 20), fill=(110, 100, 90))
    cells = [(x0, 86 + k * 266) for k in range(4)]
    for (cx, cy), path in zip(cells, WHO[cid]):
        if path.startswith(('fusion:', 'rot:', 'crop:')) or os.path.exists(path):
            t = load(path, (600, 250))
            im.paste(t, (cx + (600 - t.width) // 2, cy + (250 - t.height) // 2))
    # C: style
    lab((20, 1172), 'C · STYLE: copy the cardboard craft, not these clothes')
    x = 20
    for n in STYLE[kind]:
        p = os.path.join(STYLE_DIR, n)
        t = load(p, (880, 340))
        im.paste(t, (x, 1210))
        x += t.width + 16
    return im


def poison_exhibit():
    """Each poison sheet as a thumbnail stamped with why it is out."""
    os.makedirs(os.path.join(HERE, 'poison'), exist_ok=True)
    out = []
    for n, why in POISON:
        im = Image.open(os.path.join(SHEETS, n)).convert('RGB')
        im.thumbnail((900, 520))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width - 1, im.height - 1], outline=(200, 40, 30), width=8)
        d.line([(0, 0), (im.width, im.height)], fill=(200, 40, 30), width=5)
        d.line([(im.width, 0), (0, im.height)], fill=(200, 40, 30), width=5)
        im.save(os.path.join(HERE, 'poison', n), quality=82)
        out.append({'file': f'poison/{n}', 'sheet': n, 'why': why})
    return out


def main():
    os.makedirs(OUTD, exist_ok=True)
    P = prompts()
    out = []
    for s in P['sheets']:
        cid = s['character']
        img = pack(s, cid)
        path = os.path.join(OUTD, s['id'] + '.jpg')
        img.save(path, quality=88)
        text = TEXT + 'WHO (panel B): ' + IDENTITY[cid] + ' SHEET: ' + s['job'].split(': ', 1)[-1] + ' ' + RULES
        if cid == 'dot' and s['sheet'].startswith('face'):
            text += ' NOTE: Dot\'s features are drawn by code; this sheet is only needed for a painted alternative.'
        out.append({'id': s['id'], 'character': cid, 'sheet': s['sheet'], 'image': f'packs/{s["id"]}.jpg', 'prompt': text})
        print(s['id'])
    json.dump(out, open(os.path.join(HERE, 'packs.json'), 'w'), indent=1)
    json.dump(poison_exhibit(), open(os.path.join(HERE, 'poison.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
