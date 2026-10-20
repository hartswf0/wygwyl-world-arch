#!/usr/bin/env python3
"""
THE GENERATION BRIEF — generate the pieces, don't cut them out of a pose.

    python3 shots/arena/pieces_brief.py [--pxcm 12] [--yaw 4]
        -> shots/arena/pieces_brief.json   (one brief per card)
        -> shots/arena/pieces_brief.md     (the same, readable)

WHY NOT CUT A POSE UP. Because cutting is where it breaks, every time. The four
boxes in pose_decompiler.py share 35-110% of their own area with their
neighbours — man.crouch.legs carries both legs, both boots and a slice of torso
in one card — so compositing them gives you a second arm and a second leg, which
is what you can see on screen. Better segmentation moves that problem; it does
not remove it. There is nothing to segment if the piece was never joined.

SO: SPECIFY THE DISASSEMBLY FIRST. Every card is generated AS a card, alone, on
transparency, at a length taken from the skeleton rather than discovered
afterwards. Its pivot is not found, it is declared: joint A at the top centre,
joint B straight down. Length in centimetres comes out of the Bolas bank, which
states the body in cm and is the only measurement in this pipeline nobody has to
argue about.

THE ACCEPTANCE TEST IS THE POINT. A generated piece is not a piece until it
passes registration, and four checks decide it:

    aspect        the alpha box must be length:width within 12%, or it is not
                  the bone it claims to be — this is the check the current
                  library fails by 34 to 84%
    one piece     98% of the alpha in a single connected component, or the
                  generator has drawn two things
    upright       the long axis within 5 degrees of vertical, so the one axis
                  rule holds and the boot cannot be the exception again
    ends          alpha present at both pivot points, or there is nothing to
                  put a brad through

A piece that fails is regenerated, not placed. That is the whole difference
between this and the library we have: the current cards were never asked to pass
anything.
"""
import json, os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, 'pieces.json')

PXCM = 12.0
YAWS = 4
for i, a in enumerate(sys.argv):
    if a == '--pxcm' and i + 1 < len(sys.argv): PXCM = float(sys.argv[i + 1])
    if a == '--yaw' and i + 1 < len(sys.argv): YAWS = int(sys.argv[i + 1])

STYLE = ('flat cut-out of corrugated cardboard, the kerf and the fluting visible at the '
         'cut edge, painted and inked by hand in the manner of a jointed paper doll, '
         'a brass split-pin brad set through the pivot, soft even studio light, '
         'no cast shadow, pure transparent background, nothing else in frame')

CHARACTER = {
 'man':  'a Black man in his thirties, close-cropped hair and a full beard, a black '
         'sleeveless quilted vest with salmon-pink piping and matching black trousers, '
         'black Chelsea boots',
 'poet': 'a Black woman with a full natural afro, a teal sleeveless dress with gold '
         'filigree print, flat dark shoes',
}

# how each piece should read on its own, so it is a part and not a sliver of a picture
READS = {
 'head':   'the head and neck only, cut at the base of the neck, the brad through the neck',
 'torso':  'the trunk from the hips to the base of the neck, no arms, no head, armholes '
           'closed with cloth so the sleeve card can swing in front of it',
 'pelvis': 'the hips and seat only, cut at the waist and at both hip joints',
 'uarm':   'one upper arm from shoulder to elbow, sleeve only, a brad hole at each end',
 'farm':   'one forearm from elbow to wrist, sleeve and cuff, a brad hole at each end',
 'hand':   'one hand from the wrist, the brad through the wrist',
 'thigh':  'one thigh from hip to knee, trouser only',
 'shin':   'one shin from knee to ankle, trouser only, no foot',
 'boot':   'one boot from the ankle to the ball of the foot, the brad at the ankle, '
           'the sole flat along the bottom edge',
}

def yaw_label(k, n):
    step = 360.0 / n
    a = -180 + step * (k + 0.5)
    return int(round(a)), ('facing the camera' if abs(a) < 25 else
                           'turned three quarters' if abs(a) < 70 else
                           'in profile' if abs(a) < 115 else
                           'turned away three quarters' if abs(a) < 160 else 'from behind')

def main():
    spec = json.load(open(SPEC))
    briefs = []
    for char, desc in CHARACTER.items():
        for p in spec['pieces']:
            Lpx = int(round(p['length_cm'] * PXCM))
            Wpx = int(round(p['width_cm'] * PXCM))
            # a head carries its own views; a limb needs the camera's
            views = p['views'] if p['id'] in ('head', 'torso', 'pelvis') else None
            axes = ([(v, None) for v in views] if views else
                    [(v, yaw_label(k, YAWS)) for v in p['views'] for k in range(YAWS)])
            for v, yaw in axes:
                for side in p['sides']:
                    ang = f', seen {yaw[1]} (camera yaw {yaw[0]:+d}°)' if yaw else f', {v} view'
                    sd = '' if side == '-' else f", the figure's {'left' if side=='L' else 'right'} one"
                    briefs.append(dict(
                        card=f"{char}.{p['id']}" + (f'.{v}' if not yaw else '') +
                             (f'.y{yaw[0]:+d}' if yaw else '') + ('' if side == '-' else f'.{side}'),
                        character=char, piece=p['id'], view=v, side=side,
                        yaw_deg=(yaw[0] if yaw else None),
                        length_cm=p['length_cm'], width_cm=p['width_cm'],
                        canvas_px=[Wpx + 24, Lpx + 24],
                        pivot_px=[(Wpx + 24) // 2, 12],
                        far_px=[(Wpx + 24) // 2, Lpx + 12],
                        prompt=(f"{READS[p['id']]}{sd}{ang}. {desc}. {STYLE}. "
                                f"The piece stands upright, its pivot joint at the top centre "
                                f"and its far joint straight below, filling the frame."),
                        accept=dict(aspect=round(p['length_cm'] / p['width_cm'], 2),
                                    aspect_tol=0.12, single_component=0.98,
                                    upright_tol_deg=5.0, ends_must_have_alpha=True),
                    ))
    out = dict(
        about='Generate each card AS a card. Nothing is cut out of a pose, so nothing '
              'overlaps. Lengths from the Bolas skeleton; widths authored.',
        px_per_cm=PXCM, yaw_buckets=YAWS,
        cards=len(briefs),
        acceptance='aspect within 12% · 98% one component · long axis within 5 degrees '
                   'of vertical · alpha at both pivot points',
        briefs=briefs)
    json.dump(out, open(os.path.join(HERE, 'pieces_brief.json'), 'w'), indent=1)

    lines = [f"# Piece briefs — {len(briefs)} cards", '',
             f"{PXCM:.0f} px/cm · {YAWS} yaw buckets · lengths measured from the Bolas skeleton", '',
             '| card | cm | canvas px | accept aspect |', '| :-- | --: | :-- | --: |']
    for b in briefs[:40]:
        lines.append(f"| `{b['card']}` | {b['length_cm']}×{b['width_cm']} | "
                     f"{b['canvas_px'][0]}×{b['canvas_px'][1]} | {b['accept']['aspect']} |")
    lines += ['', f'…and {max(0,len(briefs)-40)} more in pieces_brief.json', '',
              '## Acceptance', '', out['acceptance'], '',
              'A piece that fails is regenerated, not placed.']
    open(os.path.join(HERE, 'pieces_brief.md'), 'w').write('\n'.join(lines))

    import collections
    byc = collections.Counter(b['character'] for b in briefs)
    byp = collections.Counter(b['piece'] for b in briefs)
    print(f"{len(briefs)} cards to generate  ({PXCM:.0f} px/cm, {YAWS} yaw buckets)")
    print('  per character:', dict(byc))
    print('  per piece:')
    for k, v in byp.most_common(): print(f'     {k:8s} {v:4d}')
    print(f"\n-> pieces_brief.json / pieces_brief.md")

if __name__ == '__main__':
    main()
