"""Compose the recognition test from recognize.mjs's renders (shots/skinlab/production/recognition/<character>/renders).

    python3 compose.py <character>     # pairs/, blind/ (+ key.json, hidden from critics), paintings_contact.jpg, summary.json
    python3 compose.py --index         # ../index.html: every character's summary table and pairs

Pairs: painting | puppet | method, at the same height (the puppet is drawn at the painting's own px/cm, floor and centre).
Method panel colours each segment by the joint atlas's verdict for its view (projected/3D length r):
  green ROTATE (r >= .88), amber SHORTEN12+OVERLAP (.55-.88), red NEEDS-FORESHORTENED-CARD (< .55), blue DEDICATED-CARD (feet);
the line runs from the card's pin to where the card actually ends; a ring marks the joint it should reach.
"""
import json, os, sys, random, hashlib
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
H = 720; BG = (233, 226, 212)
COL = {'ROTATE': (40, 150, 60), 'SHORTEN12+OVERLAP': (225, 140, 20), 'NEEDS-FORESHORTENED-CARD': (210, 30, 30), 'DEDICATED-CARD': (40, 90, 200)}

def font(sz):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()

def painting(r, W):
    im = Image.open(os.path.join(SHOTS, r['img'])).convert('RGBA'); k = H / im.height
    im = im.resize((max(1, round(im.width * k)), H), Image.LANCZOS)
    out = Image.new('RGB', (W, H), BG); out.paste(im, (round(r['dx']), 0), im); return out

def on_bg(im):
    out = Image.new('RGB', im.size, BG); out.paste(im, (0, 0), im); return out

import numpy as np
def cropped(r):   # the cutter cut the painted figure off at a card edge (a long run of opaque pixels on the border)
    a = np.asarray(Image.open(os.path.join(SHOTS, r['img'])).convert('RGBA'))[..., 3] > 128
    runs = {'left': a[:, 0].mean(), 'right': a[:, -1].mean(), 'top': a[0, :].mean()}
    return [k for k, v in runs.items() if v > .25]

NOTES = json.load(open(os.path.join(HERE, 'notes.json'))) if os.path.exists(os.path.join(HERE, 'notes.json')) else {}
def flags_of(r, costume):
    f = []
    if any(r['id'].startswith(o) for o in NOTES.get('other_man', [])): f.append('agent-vision: the painting shows another man (the ex: olive bomber, jeans, white trainers), not the poet')
    cr = cropped(r)
    if cr: f.append('the painting card itself is cut off at its ' + '/'.join(cr) + ' edge (cutter), so part of the figure is missing from the reference')
    tc = r['file'].split('__', 1)[1]
    if costume and tc != costume: f.append(f'painted in the {tc} costume; the puppet wears the contract costume ({costume})')
    need = [s['k'] for s in r['segments'] if s['atlas'] == 'NEEDS-FORESHORTENED-CARD']
    if need: f.append('needs foreshortened cards the kit lacks: ' + ', '.join(need))
    bad = [f"{s['k']} {s['miss_cm']}cm" for s in r['segments'] if s['miss_cm'] > 8 and not s['k'].startswith(('hand', 'foot', 'head'))]
    if bad: f.append('cards miss their joints by > 8 cm: ' + ', '.join(bad))
    wrong = [f"{s['k']} {s['want']}->{s['view']}" for s in r['segments'] if s['view'] != s['want']]
    if wrong: f.append('no card for the wanted view: ' + ', '.join(wrong))
    if (r.get('solve_iou') or 0) < .55: f.append(f"the Pose Lab solve itself is weak (IoU {r.get('solve_iou')})")
    return f

def compose(ch):
    out = os.path.join(HERE, ch); rd = os.path.join(out, 'renders')
    R = json.load(open(os.path.join(rd, 'reports.json')))
    reps = R['reports']
    costume = json.load(open(os.path.join(HERE, '..', '..', 'contracts', ch + '.json'))).get('costume')
    for d in ('pairs', 'blind'):
        os.makedirs(os.path.join(out, d), exist_ok=True)
        for f in os.listdir(os.path.join(out, d)): os.remove(os.path.join(out, d, f))
    ok = [r for r in reps if not r.get('error')]
    rng = random.Random('recognition-' + ch); order = ok[:]; rng.shuffle(order)
    num = {r['id']: i + 1 for i, r in enumerate(order)}
    key = {'about': 'BLIND KEY: critics must not read this file. blind file -> painting number on paintings_contact.jpg and the pose id.', 'blind': {}, 'paintings': {}}
    F, Fs = font(20), font(15)
    summary = []
    for r in reps:
        if r.get('error'):
            summary.append({'id': r['id'], 'rendered': False, 'why': r['error']}); continue
        n = num[r['id']]
        pup = on_bg(Image.open(os.path.join(rd, r['safe'] + '.png')).convert('RGBA'))
        pnt = painting(r, pup.width)
        meth = Image.blend(pup, Image.new('RGB', pup.size, BG), .55); d = ImageDraw.Draw(meth)
        cnt = {}
        for s in r['segments']:
            c = COL[s['atlas']]; cnt[s['atlas']] = cnt.get(s['atlas'], 0) + 1
            d.line([tuple(s['P']), tuple(s['end'])], fill=c, width=4)
            q = s['Q']; d.ellipse([q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5], outline=c, width=2)
        gap, top = 22, 58
        sheet = Image.new('RGB', (max(3 * pup.width + 4 * gap, 900), H + top + 64), BG); dd = ImageDraw.Draw(sheet)
        for i, (im, lab) in enumerate(((pnt, 'painting'), (pup, 'puppet'), (meth, 'method (joint atlas)'))):
            x = gap + i * (pup.width + gap); sheet.paste(im, (x, top)); dd.text((x, top - 22), lab, fill=(60, 50, 40), font=Fs)
        dd.text((gap, 10), f"{n:02d}  {r['id']}   view {r['view']} (psi {r['psi']}), facing {r['facing']}   solve IoU {r.get('solve_iou')}", fill=(30, 25, 20), font=Fs)
        dd.text((gap, top + H + 10), '  '.join(f'{k} {v}' for k, v in sorted(cnt.items())), fill=(60, 50, 40), font=Fs)
        dd.text((gap, top + H + 32), 'green rotate · amber 12% shortening + overlap · red needs a foreshortened card · blue dedicated boot card · ring = joint to reach', fill=(90, 80, 70), font=Fs)
        sheet.save(os.path.join(out, 'pairs', f"{n:02d}_{r['safe']}.jpg"), quality=74)
        tok = hashlib.sha1((r['id'] + '|blind|' + ch).encode()).hexdigest()[:10]
        b = Image.new('RGB', (pup.width + 40, H + 40), BG); b.paste(pup, (20, 20)); b.save(os.path.join(out, 'blind', tok + '.jpg'), quality=80)
        key['blind'][tok + '.jpg'] = {'painting': n, 'id': r['id']}; key['paintings'][str(n)] = r['id']
        fl = flags_of(r, costume)
        summary.append({'n': n, 'id': r['id'], 'rendered': True, 'view': r['view'], 'facing': r['facing'], 'via': r['via'], 'atlas': cnt,
                        'max_miss_cm': max([s['miss_cm'] for s in r['segments']] or [0]), 'flags': fl, 'pair': f"{ch}/pairs/{n:02d}_{r['safe']}.jpg"})
    # numbered paintings (numbers follow the shuffle, so the contact sheet gives no order away)
    cw, chh, cols = 220, 330, 8; cells = sorted(ok, key=lambda r: num[r['id']])
    cs = Image.new('RGB', (cols * cw, max(1, (len(cells) + cols - 1) // cols) * chh), BG); d = ImageDraw.Draw(cs)
    for i, r in enumerate(cells):
        im = Image.open(os.path.join(SHOTS, r['img'])).convert('RGBA'); k = min((cw - 16) / im.width, (chh - 40) / im.height)
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        x0, y0 = (i % cols) * cw, (i // cols) * chh
        cs.paste(im, (x0 + (cw - im.width) // 2, y0 + 34), im); d.text((x0 + 8, y0 + 6), str(num[r['id']]), fill=(20, 15, 10), font=F)
    cs.save(os.path.join(out, 'paintings_contact.jpg'), quality=86)
    json.dump(key, open(os.path.join(out, 'key.json'), 'w'), indent=1)
    json.dump({'character': ch, 'api': R.get('api'), 'poses': summary}, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    print(ch, len(ok), 'rendered,', len(reps) - len(ok), 'not rendered')

def index():
    chars = sorted(d for d in os.listdir(HERE) if os.path.exists(os.path.join(HERE, d, 'summary.json')))
    blocked = json.load(open(os.path.join(HERE, 'blocked.json'))) if os.path.exists(os.path.join(HERE, 'blocked.json')) else {}
    parts = []
    for ch in chars:
        S = json.load(open(os.path.join(HERE, ch, 'summary.json'))); P = S['poses']
        rows = ''.join(
            f"<tr><td>{p.get('n', '')}</td><td>{p['id']}</td><td>{p.get('view', '')}</td><td>{p.get('facing', '')}</td><td>" +
            (', '.join(f'{k} {v}' for k, v in sorted(p['atlas'].items())) if p['rendered'] else 'not rendered') + f"</td><td>{p.get('max_miss_cm', '')}</td><td>" +
            ('; '.join(p.get('flags', [])) if p['rendered'] else p['why']) + '</td></tr>' for p in sorted(P, key=lambda p: p.get('n', 999)))
        figs = ''.join(f"<figure><img loading=\"lazy\" src=\"{p['pair']}\" alt=\"{p['id']}\"><figcaption>{p['n']:02d} · {p['id']}</figcaption></figure>"
                       for p in sorted(P, key=lambda p: p.get('n', 999)) if p['rendered'])
        parts.append(f"<h2>{ch} <small>{sum(p['rendered'] for p in P)} of {len(P)} rendered · via {S.get('api')}</small></h2>"
                     f"<div class=t><table><tr><th>#</th><th>pose</th><th>view</th><th>facing</th><th>atlas verdicts (segments)</th><th>max miss cm</th><th>flags / why not</th></tr>{rows}</table></div>"
                     f"<p>Blind set: <code>{ch}/blind/</code> with <code>{ch}/paintings_contact.jpg</code> (key in <code>{ch}/key.json</code>, not for critics).</p>{figs}")
    bl = ''.join(f'<li><b>{k}</b>: {v}</li>' for k, v in blocked.items())
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recognition test</title><style>
:root{{--bg:#efe7d8;--ink:#2a221c;--dim:#6b5d50;--line:#0002}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#16120f;--ink:#efe6da;--dim:#9a8d7e;--line:#fff2}}}}
:root[data-theme="dark"]{{--bg:#16120f;--ink:#efe6da;--dim:#9a8d7e;--line:#fff2}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,sans-serif;padding:16px}}
h1{{font-size:20px;margin:0 0 6px}} h2{{font-size:17px;margin:28px 0 8px}} small{{color:var(--dim);font-weight:400}} p{{color:var(--dim);max-width:960px}}
.t{{overflow-x:auto}} table{{border-collapse:collapse;font-size:12px}} td,th{{border-bottom:1px solid var(--line);padding:3px 6px;text-align:left;vertical-align:top}}
figure{{margin:0 0 22px}} img{{max-width:100%;height:auto;display:block;border:1px solid var(--line)}} figcaption{{color:var(--dim);font-size:12px}}
</style></head><body>
<h1>Recognition test: painting | puppet | method</h1>
<p>Every painted pose the Pose Lab solved, posed with the character's contract through PuppetCore, in the painting's own view and height. The method panel colours each segment by the joint atlas's verdict for that view: green, rotate a rigid card; amber, 12% shortening plus overlap; red, a foreshortened card is needed and the kit has none; blue, a dedicated boot card. Regenerate: <code>node shots/skinlab/production/recognition/recognize.mjs</code>.</p>
{"<h2>Blocked</h2><ul>" + bl + "</ul>" if bl else ""}
{"".join(parts)}
</body></html>'''
    open(os.path.join(HERE, '..', 'recognition.html') if False else os.path.join(HERE, 'index.html'), 'w').write(html)

if __name__ == '__main__':
    if '--index' in sys.argv: index()
    else: compose(sys.argv[1])
