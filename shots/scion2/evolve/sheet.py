"""Review sheet for one pose: REFERENCE (the target painting with its marker skeleton, blue) | CANDIDATE 1..6 (each
render with the skeleton it was posed on, red), fitness terms and the library card per part under each.
Layout, colours and labels follow shots/scion2/rigkit/sheets.py (copied here, rigkit is not imported).

    python3 -m evolve.sheet evolve/kill/candidates.json      (run from shots/scion2) -> evolve/kill/<pose>.jpg
"""
import json, os, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import library, assemble as AS

PANEL_H, PANEL_W = 560, 380
BG = (238, 236, 232)
INK = (28, 32, 38)
MUTED = (95, 101, 112)
REF_C = (30, 110, 200)
PUP_C = (215, 60, 40)
MK_BONES = [('neck', 'head'), ('shoulderL', 'shoulderR'), ('shoulderL', 'elbowL'), ('elbowL', 'wristL'),
            ('shoulderR', 'elbowR'), ('elbowR', 'wristR'), ('neck', 'groin'), ('hipL', 'hipR'),
            ('hipL', 'kneeL'), ('kneeL', 'ankleL'), ('ankleL', 'toeL'), ('hipR', 'kneeR'), ('kneeR', 'ankleR'),
            ('ankleR', 'toeR')]
SHORT = {'torso': 'torso', 'pelvis': 'hips', 'head': 'head', 'uarmL': 'u.arm L', 'uarmR': 'u.arm R', 'farmL': 'forearm L',
         'farmR': 'forearm R', 'handL': 'hand L', 'handR': 'hand R', 'thighL': 'thigh L', 'thighR': 'thigh R',
         'shinL': 'shin L', 'shinR': 'shin R', 'footL': 'foot L', 'footR': 'foot R'}


def font(sz, bold=False):
    p = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else '')
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()


F, FB, FS, FT, FM = font(15), font(19, True), font(12), font(26, True), font(11)


def flat(rgba):
    bg = Image.new('RGBA', rgba.size, BG + (255,))
    bg.alpha_composite(rgba)
    return bg.convert('RGB')


def draw_skel(im, pts, bones, color, scale):
    d = ImageDraw.Draw(im, 'RGBA')
    w = max(2, round(2 * scale))
    for a, b in bones:
        if a in pts and b in pts:
            d.line([tuple(pts[a]), tuple(pts[b])], fill=color + (150,), width=w)
    r = max(3, round(4 * scale))
    for k, (x, y) in pts.items():
        if k.startswith('_'):
            continue
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,), outline=(255, 255, 255, 255), width=1)


def rings(im, pts, color):
    d = ImageDraw.Draw(im, 'RGBA')
    for k, (x, y) in pts.items():
        if k.startswith('_b'):
            d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=color + (255,), width=2)


def overlay(cand_rgba, t, F2, box, h=150):
    """reference figure grey, candidate holes blue, spill red"""
    import cv2
    W, H = t['size']
    ca = np.asarray(cand_rgba)[..., 3] > 128
    ca = cv2.resize(ca.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    fig, ign = t['fig'], t['ignore']
    o = np.full((H, W, 3), 255, np.uint8)
    o[fig & ca] = (170, 170, 170)
    o[fig & ~ca & ~ign] = (30, 110, 220)
    o[ca & ~fig & ~ign] = (220, 40, 40)
    o[ign] = (255, 230, 120)
    im = Image.fromarray(o)
    x0, y0, x1, y1 = [int(v / F2) for v in box]
    im = im.crop((max(0, x0), max(0, y0), min(W, x1), min(H, y1)))
    k = h / im.height
    im = im.resize((max(1, int(im.width * k)), h), Image.NEAREST)
    ImageDraw.Draw(im).rectangle([0, 0, im.width - 1, im.height - 1], outline=(90, 90, 90))
    return im


def fit_panel(im, pts, box):
    """crop to the union of content and both skeletons' box, scale into PANEL_W x PANEL_H"""
    x0, y0, x1, y1 = box
    im = im.crop((x0, y0, x1, y1))
    s = min(PANEL_H / im.height, PANEL_W / im.width)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    out = Image.new('RGBA', (PANEL_W, PANEL_H), (0, 0, 0, 0))
    ox, oy = (PANEL_W - im.width) // 2, (PANEL_H - im.height) // 2
    out.paste(im, (ox, oy))
    return out, {k: ((v[0] - x0) * s + ox, (v[1] - y0) * s + oy) for k, v in pts.items()}


def tag(im, text, color):
    d = ImageDraw.Draw(im)
    w = d.textlength(text, font=FB) + 16
    d.rectangle([0, 0, w, 30], fill=color)
    d.text((8, 4), text, fill=(255, 255, 255), font=FB)


def bgra_to_pil(a):
    return Image.fromarray(np.dstack([a[..., 2], a[..., 1], a[..., 0], a[..., 3]]).astype(np.uint8), 'RGBA')


def make(res, outdir, F2=2.0):
    char, costume, tid = res['char'], res['costume'], res['target']
    t = AS.target(char, costume, tid)
    lib = {c['id']: c for c in library.cards(char, costume)}
    W, H = t['size']
    renders = []
    for c in res['candidates']:
        G = c['genome']
        PL = AS.place(G, t, lib)
        img, _ = AS.render_full(PL, G['view'], t, F=F2)
        J = {k: v * F2 for k, v in AS.joints_out(PL).items()}
        n_ = 0
        for k_, arr in AS.card_brads(PL).items():
            for b_ in arr:
                J['_b%d' % n_] = b_ * F2; n_ += 1
        renders.append((bgra_to_pil(img), J, c))
    ref = bgra_to_pil(np.asarray(__import__('cv2').resize(t['ref'], (int(W * F2), int(H * F2)))))
    rp = {k: t['pts'][k] * F2 for k in ('neck', 'head', 'shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR',
                                         'groin', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'toeL', 'toeR') if k in t['markers']}
    rp = {k: t['markers'][k] * F2 for k in rp}
    for i, b in enumerate(t['ref_brads']):
        rp['_b%d' % i] = b * F2
    # one crop box for every panel of the row (same scale, so the reader can compare sizes)
    xs, ys = [], []
    for im, J, _ in renders + [(ref, rp, None)]:
        a = np.asarray(im)[..., 3]
        yy, xx = np.nonzero(a > 10)
        if len(xx):
            xs += [xx.min(), xx.max()]; ys += [yy.min(), yy.max()]
        P = np.array(list(J.values()))
        xs += [P[:, 0].min(), P[:, 0].max()]; ys += [P[:, 1].min(), P[:, 1].max()]
    pad = 14
    box = (max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad), int(max(xs)) + pad, int(max(ys)) + pad)
    sc = 1.0
    panels = []
    im, pts = fit_panel(ref, rp, box)
    im = flat(im)
    draw_skel(im, pts, MK_BONES, REF_C, sc)
    rings(im, pts, REF_C)
    tag(im, 'REFERENCE', REF_C)
    lines = [('target painting (reference only,', FS, MUTED), ('never a source of pixels):', FS, MUTED), (tid, FS, INK),
             ('blue dots = Pose Lab markers', FS, REF_C), ('blue rings = painted brads found (%d);' % len(t['ref_brads']), FS, REF_C),
             ('%d used as joint targets' % len(t['brad_joints']), FS, REF_C), ('scale %.2f px per card-cm' % t['s'], FS, MUTED),
             ('thumbnails: grey = filled, blue = HOLE,', FS, MUTED), ('red = SPILL, yellow = prop ignored', FS, MUTED),
             ('facing: %s' % (t['facing'] or ('back' if t['back'] else 'camera')), FS, MUTED)]
    panels.append((im, lines))
    for n, (im, J, c) in enumerate(renders, 1):
        pim, pts = fit_panel(im, J, box)
        pim = flat(pim)
        draw_skel(pim, pts, AS.SKEL, PUP_C, sc)
        rings(pim, pts, PUP_C)
        tag(pim, 'CANDIDATE %d' % n, PUP_C)
        ov = overlay(im, t, F2, box)
        pim.paste(ov, (PANEL_W - ov.width - 4, PANEL_H - ov.height - 4))
        s = c['scores']
        G = c['genome']
        lines = [('HOLE %.1f%%   SPILL %.1f%%' % (100 * s['hole'], 100 * s['spill']), FB, (200, 30, 30) if max(s['hole'], s['spill']) > .1 else INK),
                 ('hips covered %.0f%%%s · brad %.1f cm' % (100 * s['hip_cov'], '' if s['valid'] else ' INVALID', s['brad']), FS, INK),
                 ('view %s · total %.2f' % (G['view'], s['total']), F, INK),
                 ('joint %.1f cm · 1-IoU %.2f' % (s['joint'], s['sil']), FS, INK),
                 ('coh %.2f · integ %.2f · copy %.2f' % (s['coh'], s['integ'], s['copy']), FS, INK),
                 ('width step %.2f · gap %.1f cm · overstretch %.2f' % (s['width_step'], s['gap_cm'], s['overstretch']), FS, MUTED),
                 ('max ncc vs reference %.2f (%s)' % (s['max_ncc'][0], s['max_ncc'][1]), FS, MUTED)]
        for k in AS.KEYS:
            g = G['parts'][k]
            if not g:
                lines.append(('%s: none' % SHORT[k], FM, MUTED))
                continue
            cid = g['id'].replace('poet.red_black_sunglasses.', 'rb.').replace('ex.ex_jacket.', 'ex.')
            extra = ' x%.2f' % g['k'] + (' %+.0f°' % g['rot'] if g['rot'] else '') + (' mirr' if g['mir'] else '')
            for i, w in enumerate(textwrap.wrap('%s: %s%s' % (SHORT[k], cid, extra), 58)):
                lines.append((('   ' if i else '') + w, FM, INK if not g['id'].startswith('harvest') else (120, 70, 20)))
        panels.append((pim, lines))
    th = max(sum(f.size + 4 for _, f, _ in L) for _, L in panels) + 16
    Wr = len(panels) * (PANEL_W + 12) + 12
    out = Image.new('RGB', (Wr, 100 + PANEL_H + th), (255, 255, 255))
    d = ImageDraw.Draw(out)
    d.text((12, 10), '%s — %s (%s)' % (t['label'] or '', tid, char), fill=INK, font=FT)
    d.text((12, 46), 'REFERENCE: the target painting + its marker skeleton (blue).  CANDIDATE n: library cards evolved onto those '
                      'markers / brads (red; red rings = the cards\' own brads). Brown text = a harvest card (cut from ANOTHER painting).',
           fill=MUTED, font=F)
    d.text((12, 68), 'Lower is better for every term; they are proxies (joint = pose, sil = painting shape, coh = one costume, '
                      'integ = joints hold, copy = looks like the painting\'s own pixels).', fill=MUTED, font=F)
    for i, (im, L) in enumerate(panels):
        x = 12 + i * (PANEL_W + 12)
        out.paste(im, (x, 96))
        y = 96 + PANEL_H + 8
        for s_, f, col in L:
            d.text((x, y), s_, fill=col, font=f)
            y += f.size + 4
    fn = os.path.join(outdir, tid.split('/')[0].replace('.main-poses', '') + '__' + tid.split('/')[1] + '.jpg')
    out.save(fn, quality=88)
    return fn


if __name__ == '__main__':
    path = sys.argv[1]
    D = json.load(open(path))
    for r in D.values():
        print(make(r, os.path.dirname(os.path.abspath(path))))
