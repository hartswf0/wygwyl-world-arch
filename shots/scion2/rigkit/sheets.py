"""Scene sheets: for every key of a poem's scene plan, the REFERENCE painting with its marker skeleton beside the
PUPPET render with the rig skeleton it was posed on, clearly labelled.

    python3 -m rigkit.sheets shots/scion2/poems/09/plan.json      (run from shots/scion2)

Writes shots/scion2/poems/<NN>/sheets/<scene>_<page>.jpg, one set per scene (6 keys per page), plus index.json.
Reads the multi-character scene plan (plan["shots"][].chars[].keys[]); no animation, no video.
"""
import json, os, re, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from . import core, posing

PANEL_H = 560
ROWS = 3                      # keys per page = ROWS * 2 columns
BG = (238, 236, 232)
INK = (28, 32, 38)
MUTED = (95, 101, 112)
REF_C = (30, 110, 200)        # reference skeleton: blue
PUP_C = (215, 60, 40)         # puppet skeleton: red

MK_BONES = [('neck', 'head'), ('shoulderL', 'shoulderR'), ('shoulderL', 'elbowL'), ('elbowL', 'wristL'),
            ('shoulderR', 'elbowR'), ('elbowR', 'wristR'), ('neck', 'groin'), ('hipL', 'hipR'),
            ('hipL', 'kneeL'), ('kneeL', 'ankleL'), ('ankleL', 'toeL'), ('hipR', 'kneeR'), ('kneeR', 'ankleR'),
            ('ankleR', 'toeR')]
RIG_BONES = [('headpiv', 'headtop'), ('neck', 'midhip'), ('shL', 'shR'), ('shL', 'elL'), ('elL', 'wrL'), ('wrL', 'tipL'),
             ('shR', 'elR'), ('elR', 'wrR'), ('wrR', 'tipR'), ('hipL', 'hipR'), ('hipL', 'knL'), ('knL', 'anL'),
             ('anL', 'toL'), ('hipR', 'knR'), ('knR', 'anR'), ('anR', 'toR'), ('neck', 'shL'), ('neck', 'shR')]


def font(sz, bold=False):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else ''),):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


F, FB, FS, FT = font(17), font(19, True), font(14), font(26, True)


def painting_path(pid):
    for e in ('.webp', '.png', '.jpg'):
        p = os.path.join(core.ROOT, 'shots/kits/cut', pid + e)
        if os.path.exists(p):
            return p


def flat(rgba):
    bg = Image.new('RGBA', rgba.size, BG + (255,))
    bg.alpha_composite(rgba)
    return bg.convert('RGB')


def draw_skel(im, pts, bones, color, scale, label_conf=None):
    d = ImageDraw.Draw(im, 'RGBA')
    w = max(2, round(3 * scale))
    for a, b in bones:
        if a in pts and b in pts:
            d.line([tuple(pts[a]), tuple(pts[b])], fill=color + (220,), width=w)
    r = max(3, round(5 * scale))
    for k, p in pts.items():
        x, y = p
        low = label_conf is not None and label_conf.get(k, 1) < .4
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 230) if low else color + (255,), outline=color + (255,), width=2)


def fit(im, pts, h):
    """crop to content (+ the skeleton), scale to height h; returns image and transformed points"""
    a = np.array(im.convert('RGBA'))[:, :, 3]
    ys, xs = np.nonzero(a > 10)
    x0, x1, y0, y1 = (xs.min(), xs.max(), ys.min(), ys.max()) if len(xs) else (0, im.width - 1, 0, im.height - 1)
    if pts:
        P = np.array(list(pts.values()))
        x0, x1 = min(x0, P[:, 0].min()), max(x1, P[:, 0].max())
        y0, y1 = min(y0, P[:, 1].min()), max(y1, P[:, 1].max())
    pad = 12
    x0, y0 = max(0, int(x0) - pad), max(0, int(y0) - pad)
    x1, y1 = min(im.width, int(x1) + pad), min(im.height, int(y1) + pad)
    im = im.crop((x0, y0, x1, y1))
    s = h / im.height
    im = im.resize((max(1, round(im.width * s)), h), Image.LANCZOS)
    return im, {k: ((v[0] - x0) * s, (v[1] - y0) * s) for k, v in pts.items()}, s


def reference_panel(char, tid):
    MK = core.load_markers(char)
    t = MK[tid]
    src = painting_path(tid)
    im = Image.open(src).convert('RGBA') if src else Image.new('RGBA', (t['w'], t['h']), (0, 0, 0, 0))
    if src and (im.width, im.height) != (t['w'], t['h']) and t.get('w'):
        im = im.resize((t['w'], t['h']))
    m = t['markers']
    pts = {k: (v[0], v[1]) for k, v in m.items() if isinstance(v, (list, tuple)) and len(v) >= 2}
    conf = {k: (v[4] if len(v) > 4 and isinstance(v[4], (int, float)) else 1) for k, v in m.items() if isinstance(v, (list, tuple))}
    im, pts, s = fit(im, pts, PANEL_H)
    im = flat(im)
    draw_skel(im, pts, MK_BONES, REF_C, PANEL_H / 500, conf)
    return im


def puppet_panel(char, tid, keys):
    pose = posing.pose_from_markers(char, tid, keys)
    R = posing.rig(char, pose['view'])
    W, H = pose['size']
    G = np.array(pose['G'], float)
    img, J = R.render(pose['P'], G, (W, H), ss=2, opts=pose['opts'], lib=posing.parts(char))
    pts = {k: tuple(G[:, :2] @ np.asarray(v, float) + G[:, 2]) for k, v in J.items()}
    if pose['mirror']:
        img = img[:, ::-1].copy()
        pts = {k: (W - 1 - x, y) for k, (x, y) in pts.items()}
    img = np.ascontiguousarray(img[:, :, [2, 1, 0, 3]] if img.shape[2] == 4 else img[:, :, ::-1])   # rigkit renders BGRA (OpenCV order)
    im = Image.fromarray(img)
    im, pts, s = fit(im.convert('RGBA'), pts, PANEL_H)
    im = flat(im)
    draw_skel(im, pts, RIG_BONES, PUP_C, PANEL_H / 500)
    return im, pose


def tag(im, text, color):
    d = ImageDraw.Draw(im)
    w = d.textlength(text, font=FB) + 16
    d.rectangle([0, 0, w, 30], fill=color)
    d.text((8, 4), text, fill=(255, 255, 255), font=FB)


def line_for(tl, t):
    for s in tl['scenes']:
        for l in s.get('lines', []):
            if l['t'] - .3 <= t <= l['e'] + 1.0:
                return l['text']
    ls = [l for s in tl['scenes'] for l in s.get('lines', [])]
    return min(ls, key=lambda l: abs(l['t'] - t))['text'] if ls else ''


def word_time(tl, word, near):
    norm = lambda w: re.sub(r'[^a-z]', '', w.lower())
    c = [w for w in tl['words'] if norm(w['w']) == norm(word)]
    return min(c, key=lambda w: abs(w['s'] - near))['s'] if c else near


def cell(n, scene, who, char, k, tl):
    t = k['t'] if 't' in k else word_time(tl, k.get('word', ''), k.get('near', 0))
    head = '%s · key %02d · %.1fs · "%s"' % (scene, n, t, (k.get('word') or '').upper())
    try:
        ref = reference_panel(char, k['target'])
        tag(ref, 'REFERENCE', REF_C)
    except Exception as e:
        ref = Image.new('RGB', (360, PANEL_H), BG); ImageDraw.Draw(ref).text((10, 40), 'no reference: %s' % e, fill=INK, font=F)
    try:
        pup, pose = puppet_panel(char, k['target'], k.get('keys'))
        tag(pup, 'PUPPET', PUP_C)
        src = pose['sources']
        meta = 'rig %s%s · body %s · head %s' % (pose['view'], ' (mirrored)' if pose['mirror'] else '',
                                                src['body'].split('/')[-1], (src['head'] or '').split('/')[-1])
        flags = '; '.join(f for f in pose['flags'] if 'rig master hand' not in f)[:150]
    except Exception as e:
        pup = Image.new('RGB', (360, PANEL_H), BG); ImageDraw.Draw(pup).text((10, 40), 'puppet failed: %s' % e, fill=INK, font=F)
        meta, flags = '', ''
    W = ref.width + pup.width + 30
    W = max(W, 760)
    txt = [('“' + line_for(tl, t) + '”', F, INK), ('%s (%s) — reference: %s' % (who, char, k['target']), FS, MUTED),
           ('puppet: ' + meta, FS, MUTED)]
    if flags:
        txt.append(('known issues: ' + flags, FS, (170, 40, 40)))
    if k.get('why'):
        txt.append(('why: ' + k['why'], FS, MUTED))
    lines = []
    for s, f, c in txt:
        for w in textwrap.wrap(s, int(W / (f.size * .55))):
            lines.append((w, f, c))
    th = 40 + sum(f.size + 6 for _, f, _ in lines) + 10
    out = Image.new('RGB', (W, PANEL_H + th), (255, 255, 255))
    d = ImageDraw.Draw(out)
    d.text((10, 8), head, fill=INK, font=FB)
    out.paste(ref, (10, 40))
    out.paste(pup, (W - pup.width - 10, 40))
    y = 40 + PANEL_H + 8
    for s, f, c in lines:
        d.text((10, y), s, fill=c, font=f)
        y += f.size + 6
    return out


def page(cells, title, sub):
    cw = max(c.width for c in cells)
    cols = 2
    rows = (len(cells) + 1) // 2
    rh = [max(c.height for c in cells[r * 2:r * 2 + 2]) for r in range(rows)]
    W = cols * cw + 3 * 16
    H = 90 + sum(rh) + (rows + 1) * 16
    P = Image.new('RGB', (W, H), (214, 218, 223))
    d = ImageDraw.Draw(P)
    d.text((16, 14), title, fill=INK, font=FT)
    d.text((16, 52), sub, fill=MUTED, font=F)
    y = 90
    for r in range(rows):
        for c in range(cols):
            i = r * 2 + c
            if i < len(cells):
                P.paste(cells[i], (16 + c * (cw + 16), y))
        y += rh[r] + 16
    return P


def main(path):
    plan = json.load(open(path))
    poem = plan['poem']
    tl = json.load(open(os.path.join(core.ROOT, 'shots/stage/timeline/%s.json' % poem)))
    names = {s['key']: s['name'] for s in tl['scenes']}
    cast = plan.get('cast', {})
    od = os.path.join(os.path.dirname(os.path.abspath(path)), 'sheets')
    os.makedirs(od, exist_ok=True)
    index = []
    by_scene = {}
    for sh in plan['shots']:
        by_scene.setdefault(sh['scene'], []).append(sh)
    for scene, shots in by_scene.items():
        items = []
        for sh in shots:
            for ch in sh.get('chars', []):
                char = (cast.get(ch['who']) or {}).get('char')
                if not char:
                    continue
                for k in ch.get('keys', []):
                    if k.get('target'):
                        items.append((ch['who'], char, k))
        items.sort(key=lambda it: it[2].get('t', word_time(tl, it[2].get('word', ''), it[2].get('near', 0))))
        cells = [cell(i + 1, scene, who, char, k, tl) for i, (who, char, k) in enumerate(items)]
        per = ROWS * 2
        npg = max(1, (len(cells) + per - 1) // per)
        for p in range(npg):
            chunk = cells[p * per:(p + 1) * per]
            if not chunk:
                continue
            title = 'Poem %s · scene %s · %s  (sheet %d of %d)' % (poem, scene, names.get(scene, ''), p + 1, npg)
            sub = 'Each key: REFERENCE painting with its marker skeleton (blue; hollow dot = low-confidence marker) | PUPPET render with the rig skeleton it was posed on (red).'
            fn = '%s_%d.jpg' % (scene, p + 1)
            page(chunk, title, sub).save(os.path.join(od, fn), quality=86)
            index.append({'scene': scene, 'name': names.get(scene, ''), 'sheet': fn, 'keys': len(chunk)})
        if not items:
            index.append({'scene': scene, 'name': names.get(scene, ''), 'sheet': None, 'keys': 0,
                          'note': 'no rigged character keys in this scene'})
    json.dump(index, open(os.path.join(od, 'index.json'), 'w'), indent=1)
    print(json.dumps(index, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
