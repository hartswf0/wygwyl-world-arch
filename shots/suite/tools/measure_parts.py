"""Measure the registry on the cards themselves (not on the solver).

    python3 shots/suite/tools/measure_parts.py     # writes shots/suite/review/parts_contact.jpg + parts_measure.json

1. Pivot vs brad mark. For 10 random painted cards whose pivot was read off a brad, find the brass brad
   independently with the release cutter's own detector (cut_release_kits.detect_brass_pivots, a different
   colour rule) and report the px distance from the registry pivot to the nearest detection. Also report how far
   kit.py's layout rule (A half a card-width in from the end) lands from the brad, for limb cards.
2. Scale vs the character's height. For 10 random cards with a skeleton span, convert the span to cm with the
   sheet's px/cm computed WITHOUT that card (leave-one-out) and compare with the length the character's
   skeleton (from height_cm) predicts: error in %.
Plus the same two numbers over every eligible card, so the 10 are not cherry-picked.
"""
import json, math, os, random, statistics, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_parts as BP
import cutter

SHOTS = BP.SHOTS
R = json.load(open(os.path.join(SHOTS, 'suite/data/parts.json')))['parts']


def load(p):
    im = cv2.imread(os.path.join(SHOTS, p['file']), cv2.IMREAD_UNCHANGED)
    if im is not None and im.ndim == 3 and im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


def pivot_error(p, im):
    det = cutter.CRK.detect_brass_pivots(im)
    if not det:
        return None, det
    d = min(math.dist(p['pivot'], (q['x'], q['y'])) for q in det)
    return round(d, 1), det


def main():
    random.seed(20261030)
    painted = [p for p in R if p['paint'] == 'painted' and p['label_method'] in ('layout', 'prompt', 'clip', 'layout_partial')]
    brad_piv = [p for p in painted if p['pivot_source'] in ('brad', 'brads', 'brad+layout_rule')]
    # --- all eligible cards: pivot vs independent detector
    allerr, layerr = [], []
    for p in brad_piv:
        im = load(p)
        if im is None:
            continue
        e, _ = pivot_error(p, im)
        if e is not None:
            allerr.append(e)
        if p['part'] in ('upper_arm', 'forearm', 'thigh', 'shin', 'limb') and p['label_method'] == 'layout':
            A = BP.layout_ends(im[:, :, 3] > 128)[0]
            layerr.append(math.dist(A, p['sockets']['A']))
    sample_p = random.sample([p for p in brad_piv if p['part'] in ('upper_arm', 'forearm', 'thigh', 'shin', 'hand', 'foot', 'head', 'torso', 'face_plate', 'limb')], 10)
    # --- scale: leave-one-out per card
    span_ok = []
    for p in painted:
        sc = p.get('scale') or {}
        e = BP.expected_cm(BP.build_of(p['character']), p['part'])
        if not e or not sc.get('loo_px_per_cm') or sc.get('n', 0) < 3 or not BP.trusted_for_scale(p):
            continue
        im = None
        span = BP.measure_span(p['part'], p['sockets'], im)
        if not span:
            continue
        cm = span / sc['loo_px_per_cm']
        span_ok.append((p, round(cm, 1), e, round(100 * (cm - e) / e, 1)))
    sample_s = random.sample(span_ok, 10)
    allpct = [abs(x[3]) for x in span_ok]
    by_part = {}
    for p, cm, e, pct in span_ok:
        by_part.setdefault(p['part'], []).append(abs(pct))
    # --- layout scale agreement: measured sheet px/cm vs layout px/cm x width/2048
    S = json.load(open(os.path.join(SHOTS, 'suite/data/parts_summary.json')))['cut_sheets']
    lay = [100 * (s['px_per_cm'] - s['layout_px_per_cm']) / s['layout_px_per_cm'] for s in S if s.get('px_per_cm') and s.get('layout_px_per_cm') and s['n_scale'] >= 3]
    rows_p, rows_s = [], []
    for p in sample_p:
        im = load(p)
        e, det = pivot_error(p, im)
        rows_p.append({'id': p['id'], 'part': p['part'], 'pivot': p['pivot'], 'pivot_source': p['pivot_source'], 'nearest_independent_brad_px': e,
                       'card_len_px': max(p['w'], p['h']), 'file': p['file']})
    for p, cm, e, pct in sample_s:
        rows_s.append({'id': p['id'], 'part': p['part'], 'character': p['character'], 'height_cm': p['char_height_cm'], 'measured_cm': cm,
                       'skeleton_cm': e, 'error_pct': pct, 'loo_px_per_cm': p['scale']['loo_px_per_cm'], 'file': p['file']})
    out = {
        'about': 'Measured on the card files by shots/suite/tools/measure_parts.py',
        'pivot_vs_brad': {'sample': rows_p, 'all_cards': {'n': len(allerr), 'median_px': round(statistics.median(allerr), 2) if allerr else None,
                                                          'p90_px': round(float(np.percentile(allerr, 90)), 2) if allerr else None,
                                                          'within_3px': round(sum(1 for x in allerr if x <= 3) / max(1, len(allerr)), 3),
                                                          'within_15px': round(sum(1 for x in allerr if x <= 15) / max(1, len(allerr)), 3),
                                                          'median_px_when_both_found_it': round(statistics.median([x for x in allerr if x <= 15]), 2) if allerr else None,
                                                          'note': 'in a visual check of 16 cases over 15 px, 14 were the independent detector missing the pivot brad '
                                                                  '(dark or flat brass) and matching another brad, skin or kraft instead; 2 were bad cards (a merged composite, a long fused card)'},
                          'layout_rule_vs_brad_limbs': {'n': len(layerr), 'median_px': round(statistics.median(layerr), 1) if layerr else None,
                                                        'p90_px': round(float(np.percentile(layerr, 90)), 1) if layerr else None}},
        'scale_vs_height': {'sample': rows_s, 'all_cards': {'n': len(allpct), 'median_abs_pct': round(statistics.median(allpct), 1),
                                                            'p90_abs_pct': round(float(np.percentile(allpct, 90)), 1),
                                                            'by_part_median_abs_pct': {k: round(statistics.median(v), 1) for k, v in sorted(by_part.items())},
                                                            'by_part_n': {k: len(v) for k, v in sorted(by_part.items())}},
                            'sheet_vs_layout_px_per_cm': {'n': len(lay), 'median_pct': round(statistics.median(lay), 1) if lay else None,
                                                          'median_abs_pct': round(statistics.median([abs(x) for x in lay]), 1) if lay else None}},
    }
    json.dump(out, open(os.path.join(SHOTS, 'suite/review/parts_measure.json'), 'w'), indent=1)
    contact(rows_p, rows_s)
    print(json.dumps({k: v.get('all_cards') for k, v in out.items() if isinstance(v, dict)}, indent=1))
    print(json.dumps(out['pivot_vs_brad']['layout_rule_vs_brad_limbs']), json.dumps(out['scale_vs_height']['sheet_vs_layout_px_per_cm']))
    for r in rows_p:
        print('PIV', r['id'][:70], r['part'], r['nearest_independent_brad_px'])
    for r in rows_s:
        print('SCL', r['id'][:70], r['part'], r['measured_cm'], r['skeleton_cm'], r['error_pct'])


def font(n):
    for f in ('/System/Library/Fonts/Menlo.ttc', '/Library/Fonts/Arial.ttf'):
        try:
            return ImageFont.truetype(f, n)
        except OSError:
            pass
    return ImageFont.load_default()


def contact(rows_p, rows_s):
    W, cell = 2000, 200
    im = Image.new('RGB', (W, 1060), (34, 30, 27))
    d = ImageDraw.Draw(im)
    F, f = font(22), font(14)
    d.text((20, 14), 'PIVOT vs BRAD  green = registry pivot, red = sockets, blue ring = brad found by the release detector (independent)', font=F, fill=(240, 230, 210))
    for i, r in enumerate(rows_p):
        x0 = 20 + i * cell
        card = Image.open(os.path.join(SHOTS, r['file'])).convert('RGBA')
        p = next(q for q in R if q['id'] == r['id'])
        k = min((cell - 20) / card.width, 330 / card.height)
        card = card.resize((max(1, int(card.width * k)), max(1, int(card.height * k))))
        y0 = 60
        im.paste(card, (x0, y0), card)
        cv = cv2.imread(os.path.join(SHOTS, r['file']), cv2.IMREAD_UNCHANGED)
        if cv.ndim == 3 and cv.shape[2] == 3:
            cv = np.dstack([cv, np.full(cv.shape[:2], 255, np.uint8)])
        for q in cutter.CRK.detect_brass_pivots(cv):
            c = (x0 + q['x'] * k, y0 + q['y'] * k)
            d.ellipse([c[0] - 9, c[1] - 9, c[0] + 9, c[1] + 9], outline=(80, 160, 255), width=2)
        for nm, s in p['sockets'].items():
            c = (x0 + s[0] * k, y0 + s[1] * k)
            d.line([c[0] - 5, c[1], c[0] + 5, c[1]], fill=(230, 60, 50), width=2)
            d.line([c[0], c[1] - 5, c[0], c[1] + 5], fill=(230, 60, 50), width=2)
        c = (x0 + p['pivot'][0] * k, y0 + p['pivot'][1] * k)
        d.ellipse([c[0] - 4, c[1] - 4, c[0] + 4, c[1] + 4], fill=(60, 220, 90))
        d.text((x0, 400), f"{r['part']}", font=F, fill=(255, 220, 120))
        d.text((x0, 428), f"err {r['nearest_independent_brad_px']} px", font=f, fill=(240, 230, 210))
        d.text((x0, 446), r['id'].split('/')[0][-26:], font=f, fill=(170, 160, 150))
    d.text((20, 490), 'SCALE vs HEIGHT  each card drawn at true size on one cm grid (1 cm = 5 px, grid every 10 cm); its skeleton span measured with the sheet scale computed without it', font=F, fill=(240, 230, 210))
    G = 5.0
    base = 990
    for yy in range(0, 90, 10):
        d.line([0, base - yy * G, W, base - yy * G], fill=(60, 54, 48) if yy % 50 else (100, 90, 80), width=1)
    x = 30
    for r in rows_s:
        p = next(q for q in R if q['id'] == r['id'])
        card = Image.open(os.path.join(SHOTS, r['file'])).convert('RGBA')
        k = G / r['loo_px_per_cm']
        card = card.resize((max(1, int(card.width * k)), max(1, int(card.height * k))))
        im.paste(card, (x, int(base - card.height)), card)
        d.text((x, base + 8), f"{r['part']} {r['character']}", font=f, fill=(255, 220, 120))
        d.text((x, base + 26), f"{r['measured_cm']} vs {r['skeleton_cm']} cm ({r['error_pct']:+}%)", font=f, fill=(240, 230, 210))
        x += max(card.width, 150) + 40
    im.save(os.path.join(SHOTS, 'suite/review/parts_contact.jpg'), quality=86)


if __name__ == '__main__':
    main()
