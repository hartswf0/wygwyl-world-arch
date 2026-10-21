"""Poem kits: props, sets and effects for every poem, from its production dossier.

    python3 shots/arena/parts/kit3/poem_kits.py      # shots/poems/dossier/NN.json -> shots/poems/kits/

Per poem, beside the characters' v2 kits (v2.py):
  NN.props.jpg   every hero prop of the poem, each in every state it goes through (whole,
                 flying, shattered ...), at one scale, pivot on green, grip on red
  NN.set.<id>.jpg  one sheet per place, as multiplane layers (sky, back, mid, front, floor)
                 on one horizon and one floor line, so the layers stack in the rig
  NN.fx.jpg      the effects the poem paints rather than codes
each one image (A layout, B the poem's own best stills, C cardboard style) and one prompt,
listed in kits/NN.json for the poem page.
"""
import json, os, sys, textwrap, glob
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit as K
import packs as PKS
from kit import font, FONTB, FONT, MONO, INK, sheet_frame, cross, SOCK_A, SOCK_B, GHOST

SHOTS = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
POEMS = os.path.join(SHOTS, 'poems')
OUT = os.path.join(POEMS, 'kits')
STILLS = os.path.join(POEMS, 'refs', 'stills')
SHEETS = os.path.join(SHOTS, 'weave', 'cast', 'man', 'sheets')
STYLE_PROPS = [os.path.join(SHEETS, 'set_props.jpg'), os.path.join(SHEETS, 'props.jpg'), os.path.join(HERE, 'style', 'craft_grips.jpg')]
STYLE_SET = [os.path.join(SHEETS, 'set_props.jpg'), os.path.join(SHEETS, 'props.jpg')]  # no figures: a set sheet must not seed a body


def compose(a_img, still_ids, b_text, style, b_title):
    Wd, Hd = 2688, 1560
    im = Image.new('RGB', (Wd, Hd), (255, 255, 255))
    d = ImageDraw.Draw(im)
    im.paste(a_img.convert('RGB').resize((2048, 1152)), (0, 0))
    d.rectangle([0, 0, 2047, 1151], outline=INK, width=3)
    d.rectangle([0, 1108, 420, 1151], fill=INK)
    d.text((14, 1114), 'A · LAYOUT: paint into this', font=font(FONTB, 22), fill=(255, 255, 255))
    d.text((2068, 14), 'B · WHAT (footage + atlas references)', font=font(FONTB, 26), fill=INK)
    d.text((2068, 48), b_title[:42], font=font(FONT, 19), fill=(110, 100, 90))
    y = 84
    for sid in still_ids[:3]:
        p = os.path.join(POEMS, sid) if '/' in sid else os.path.join(STILLS, f'{sid}.jpg')  # atlas refs are paths
        if os.path.exists(p):
            t = Image.open(p).convert('RGB')
            t.thumbnail((600, 300))
            im.paste(t, (2068 + (600 - t.width) // 2, y))
            y += t.height + 10
    for ln in textwrap.wrap(b_text, 46):
        if y > 1130:
            break
        d.text((2068, y), ln, font=font(FONT, 16), fill=INK)
        y += 21
    d.text((20, 1172), 'C · STYLE: copy the cardboard craft, not these objects', font=font(FONTB, 26), fill=INK)
    x = 20
    for p in style:
        if os.path.exists(p):
            t = PKS.load(p, (880, 340))
            im.paste(t, (x, 1210))
            x += t.width + 16
    return im


def props_sheet(P):
    """Every hero prop (then the rest) in each of its states, one row per prop."""
    props = sorted(P.get('props') or [], key=lambda p: not p.get('hero'))
    px = 3.0
    im, d = sheet_frame(f"{P['num']}.props", f"{P['title']} · props in every state they go through · one scale · pivot on green, grip on red", px)
    y = 110
    for p in props:
        states = (p.get('states') or ['as seen'])[:6]
        s = float(p.get('scale_cm') or 20)
        cell = max(90, min(250, s * px * 2.2))
        if y + cell + 50 > K.SHEET_H - 30:
            break
        d.text((40, y), f"{'★ ' if p.get('hero') else ''}{p.get('name') or p.get('id')}", font=font(FONTB, 17), fill=INK)
        d.text((40, y + 22), f"{s:g} cm · " + ', '.join(p.get('who') or []), font=font(MONO, 12), fill=(110, 100, 90))
        for k, ln in enumerate(textwrap.wrap(p.get('build', ''), 34)[:4]):
            d.text((40, y + 42 + k * 15), ln, font=font(FONT, 12), fill=(110, 100, 90))
        x = 360
        for st in states:
            if x + cell > K.SHEET_W - 30:
                break
            d.rectangle([x, y, x + cell, y + cell], fill=GHOST)
            for k, ln in enumerate(textwrap.wrap(st, max(12, int(cell / 7.5)))[:3]):
                d.text((x + 6, y + 4 + k * 14), ln, font=font(MONO, 12), fill=INK)
            cross(d, (x + cell / 2, y + cell * .62), SOCK_A, r=7)
            if p.get('who'):
                cross(d, (x + cell * .75, y + cell * .45), SOCK_B, r=6)
            x += cell + 22
        y += cell + 34
    return im, props


LAYERS = ['sky', 'back', 'mid', 'front', 'floor']


def set_sheet(P, s):
    """A place as five stacked layers on one horizon (blue) and one floor line (green)."""
    im, d = sheet_frame(f"{P['num']}.set.{s['id']}", f"{P['title']} · {s.get('name', s['id'])} · multiplane layers, each its own card; horizon on blue, floor line on green", 4.0)
    L = s.get('layers') or {}
    y = 100
    h = 190
    for k in LAYERS:
        d.rectangle([60, y, K.SHEET_W - 60, y + h], fill=GHOST if k != 'sky' else (236, 240, 244))
        d.text((72, y + 8), k.upper(), font=font(FONTB, 18), fill=INK)
        for j, ln in enumerate(textwrap.wrap(str(L.get(k, '')), 150)[:2]):
            d.text((160, y + 10 + j * 18), ln, font=font(FONT, 14), fill=(90, 82, 72))
        hz = y + h * .55
        d.line([(60, hz), (K.SHEET_W - 60, hz)], fill=(80, 110, 170), width=1)
        cross(d, (90, hz), (60, 90, 170), r=8)
        cross(d, (K.SHEET_W - 90, hz), (60, 90, 170), r=8)
        if k in ('front', 'floor', 'mid'):
            fl = y + h - 24
            d.line([(60, fl), (K.SHEET_W - 60, fl)], fill=(60, 140, 80), width=2)
            cross(d, (K.SHEET_W / 2, fl), SOCK_A, r=8)
        y += h + 12
    return im


HERO_BANDS = [('facade', 'the front, openings cut through'), ('openings', 'doors, windows, shutters: each on a brad'),
              ('interior', 'the back wall seen through the openings'), ('floor', 'floor and furniture'), ('broken', 'the changed or ruined state')]


def hero_sheet(P, x):
    """A hero building as cards: facade, openings, interior, floor, broken state, on one ground line."""
    im, d = sheet_frame(f"{P['num']}.hero.{x['id']}", f"{P['title']} · {x.get('name')} · the building as cards; ground on green, swing pivots on green crosses", 4.0)
    y, h = 100, 190
    for k, note in HERO_BANDS:
        d.rectangle([60, y, K.SHEET_W - 60, y + h], fill=GHOST)
        d.text((72, y + 8), k.upper(), font=font(FONTB, 18), fill=INK)
        d.text((190, y + 10), note, font=font(FONT, 14), fill=(90, 82, 72))
        fl = y + h - 24
        d.line([(60, fl), (K.SHEET_W - 60, fl)], fill=(60, 140, 80), width=2)
        if k == 'openings':
            for i in range(4):
                cross(d, (300 + i * 380, y + h * .45), SOCK_A, r=8)
        else:
            cross(d, (K.SHEET_W / 2, fl), SOCK_A, r=8)
        y += h + 12
    return im


def fx_sheet(P):
    fx = [f for f in (P.get('fx') or []) if 'paint' in str(f.get('how', '')) or f.get('how') == 'both']
    im, d = sheet_frame(f"{P['num']}.fx", f"{P['title']} · effects painted as cards (the coded ones are drawn by the rig)", 4.0)
    cw = (K.SHEET_W - 120) / 4
    for i, f in enumerate(fx[:8]):
        x0, y0 = 60 + (i % 4) * cw, 120 + (i // 4) * 500
        d.rectangle([x0 + 6, y0, x0 + cw - 6, y0 + 460], fill=GHOST)
        d.text((x0 + 16, y0 + 10), f.get('id', '?'), font=font(FONTB, 17), fill=INK)
        for k, ln in enumerate(textwrap.wrap(f.get('note', ''), 30)[:5]):
            d.text((x0 + 16, y0 + 36 + k * 17), ln, font=font(FONT, 13), fill=(90, 82, 72))
        cross(d, (x0 + cw / 2, y0 + 300), SOCK_A, r=8)
    return im, fx


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(POEMS, 'dossier', '[0-9][0-9].json'))):
        P = json.load(open(f))
        n = P['num']
        out = []
        best = [b['still'] for b in P.get('best_footage') or []]
        # props
        im, props = props_sheet(P)
        refs = []
        for p in props:  # atlas first: chosen by eye for the object itself
            refs += [r for r in (p.get('atlas_refs') or [])[:1] + (p.get('refs') or []) if r not in refs]
        txt = '; '.join(f"{p.get('name') or p['id']}: {p.get('look', '')} ({', '.join(p.get('states') or [])})" for p in props[:10])
        compose(im, refs or best, txt, STYLE_PROPS, f"{n} {P['title']} · props").save(os.path.join(OUT, f'{n}.props.jpg'), quality=80)
        prompt = (PKS.TEXT.replace('panel B is who the character is', 'panel B is our footage for these props (reference: copy the object, not the photo style)')
                  + f"WHAT (panel B): the props of the poem '{P['title']}', one row each, every state of a prop in its own cell, left to right: " + txt +
                  ". Paint each state as a flat cardboard prop card at the size its cell gives, the same object across its row; a brass brad on the green cross "
                  "(its pivot); where there is a red cross, that is where a hand grips it. " + PKS.RULES)
        out.append({'id': f'{n}.props', 'kind': 'props', 'title': 'Props, every state', 'image': f'kits/{n}.props.jpg', 'prompt': prompt})
        # sets
        for s in P.get('sets') or []:
            im = set_sheet(P, s)
            pid = f"{n}.set.{s['id']}"
            L = s.get('layers') or {}
            txt = f"{s.get('name', s['id'])}: {s.get('look', '')} Light: {s.get('light', '')}"
            compose(im, (s.get('atlas_refs') or [])[:2] + (s.get('refs') or []) or best, txt, STYLE_SET, f"{n} · {s.get('name', s['id'])}").save(os.path.join(OUT, pid + '.jpg'), quality=80)
            prompt = (PKS.TEXT.replace('panel B is who the character is', 'panel B is our footage for this place (reference: copy the place, not the photo style)')
                      + f"WHAT (panel B): {txt}. SHEET: the place as five separate flat cardboard layers, one per band, painted to stack front to back in a "
                      "multiplane rig: " + '; '.join(f"{k.upper()}: {L.get(k, '')}" for k in LAYERS) +
                      ". Each layer is its own card with a clean cut top edge and transparent gaps where the layer behind shows through; keep the "
                      "horizon on the blue line and the floor on the green line in every band so they register. " + PKS.RULES.replace(
                          'NEVER draw a pelvis, hip, shorts or briefs card (the thighs end in a rounded seat that tucks under the hem), '
                          'a sleeveless vest, lace-up boots, or sunglasses painted onto a head. ', ''))
            out.append({'id': pid, 'kind': 'set', 'title': s.get('name', s['id']), 'image': f'kits/{pid}.jpg', 'prompt': prompt})
        # hero buildings: facade, openings, interior, broken states, each its own card
        for x in (P.get('atlas') or {}).get('heroes') or []:
            im = hero_sheet(P, x)
            pid = f"{n}.hero.{x['id']}"
            txt = f"{x.get('name')}: {x.get('in_poem', '')} Build: {x.get('build_as_cards', '')}"
            compose(im, x.get('refs') or best, txt, STYLE_SET, f"{n} · {x.get('name')}").save(os.path.join(OUT, pid + '.jpg'), quality=80)
            prompt = (PKS.TEXT.replace('panel B is who the character is', 'panel B is the atlas reference for this building (copy the building, not the photo style)')
                      + f"WHAT (panel B): {txt}. SHEET: the building as separate flat cardboard cards, one per band: the FACADE with its window and door "
                      "holes cut clean through; the OPENINGS (doors, shutters, windows) as their own cards on a brass brad at the green cross so they swing; "
                      "the INTERIOR back wall seen through the openings; the FLOOR and furniture; and its BROKEN or changed state where the poem has one. "
                      "Keep the ground on the green line in every band so the cards register. " + PKS.RULES.replace(
                          'NEVER draw a pelvis, hip, shorts or briefs card (the thighs end in a rounded seat that tucks under the hem), '
                          'a sleeveless vest, lace-up boots, or sunglasses painted onto a head. ', '') + ' No people on this sheet.')
            out.append({'id': pid, 'kind': 'hero', 'title': x.get('name', x['id']), 'image': f'kits/{pid}.jpg', 'prompt': prompt})
        # painted fx
        im, fx = fx_sheet(P)
        if fx:
            txt = '; '.join(f"{x['id']}: {x.get('note', '')}" for x in fx)
            compose(im, best, txt, STYLE_PROPS, f"{n} · effects").save(os.path.join(OUT, f'{n}.fx.jpg'), quality=80)
            prompt = (PKS.TEXT.replace('panel B is who the character is', 'panel B is our footage for the mood') +
                      f"WHAT: the poem's painted effects, one per cell, as flat cardboard cards that a cut-out film moves in front of the camera: {txt}. "
                      "A brass brad on the green cross of each. " + PKS.RULES)
            out.append({'id': f'{n}.fx', 'kind': 'fx', 'title': 'Painted effects', 'image': f'kits/{n}.fx.jpg', 'prompt': prompt})
        json.dump(out, open(os.path.join(OUT, f'{n}.json'), 'w'), indent=1)
        print(n, P['title'], len(out), 'kits')


if __name__ == '__main__':
    main()
