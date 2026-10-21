"""Build one production-design page per poem (shots/poems/NN.html) and the index (shots/poems/index.html).

    python3 shots/arena/parts/kit3/poem_pages.py

Each page reads the poem's dossier (shots/poems/dossier/NN.json), its kits (shots/poems/kits/NN.json)
and the cast's v2 kits (kit3/v2/kits.json): the poem, its arc, the best of our footage, the cast with
their action sheets, props in their states, places as layers, effects, actions, the kits to
generate (one image + one prompt each), and what it gives later poems.
"""
import glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
POEMS = os.path.join(SHOTS, 'poems')
V2 = json.load(open(os.path.join(HERE, 'v2', 'kits.json')))
V2REL = os.path.relpath(HERE, POEMS).replace(os.sep, '/')        # ../arena/parts/kit3

CSS = r'''
:root{--bg:#0d0b0a;--panel:#16120f;--line:#2a221c;--ink:#efe6da;--dim:#9a8d7e;--card:#c79a62;--ok:#9fe08a;--acc:#e7a35a;--mono:'JetBrains Mono',ui-monospace,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 Inter,system-ui,sans-serif}
header.top{display:flex;align-items:center;gap:10px;padding:10px max(18px,env(safe-area-inset-right)) 10px max(18px,env(safe-area-inset-left));border-bottom:1px solid var(--line);flex-wrap:wrap;position:sticky;top:0;background:var(--bg);z-index:5}
header.top a{color:var(--dim);font:12px var(--mono);text-decoration:none;border:1px solid var(--line);padding:4px 10px;border-radius:999px}
header.top a:hover,header.top a[aria-current]{color:var(--card);border-color:var(--card)}
main{max-width:1320px;margin:0 auto;padding:28px max(18px,env(safe-area-inset-right)) 90px max(18px,env(safe-area-inset-left));display:grid;gap:48px}
h1{font:400 clamp(38px,6vw,64px)/1 'Permanent Marker',cursive;margin:0;color:var(--ink)}
h1 span{color:var(--acc)}
h2{font:400 28px 'Permanent Marker',cursive;margin:0;color:var(--card)}
h3{font:600 17px Inter;margin:0}
p{margin:0;max-width:78ch}
.dim{color:var(--dim)}
section{display:grid;gap:16px;min-width:0;scroll-margin-top:70px}
.hero{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:24px;align-items:center}
@media (max-width:860px){.hero{grid-template-columns:1fr}}
.hero img{width:100%;height:auto;border-radius:8px}
.essence{font-size:19px;line-height:1.5}
.swatches{display:flex;gap:6px;flex-wrap:wrap}
.swatches span{width:44px;height:44px;border-radius:6px;border:1px solid var(--line)}
.text{columns:2 340px;column-gap:32px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}
.text div{break-inside:avoid;margin-bottom:6px}
.text code{font:11px var(--mono);color:var(--acc);margin-right:8px}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font:600 10px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;display:grid;gap:8px;align-content:start;min-width:0}
.card img{width:100%;height:auto;border-radius:5px;display:block;background:#fff}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{font:12px var(--mono);color:var(--ink);background:#21190f;border:1px solid var(--line);border-radius:999px;padding:2px 9px}
.chip.hot{border-color:var(--acc);color:var(--acc)}
.refs{display:flex;gap:6px;flex-wrap:wrap}
.refs img{width:120px;height:68px;object-fit:cover;border-radius:4px}
.cast{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:16px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
@media (max-width:860px){.cast{grid-template-columns:1fr}}
.cast img{width:100%;height:auto;border-radius:5px;background:#fff}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:14px}
dt{font:600 11px var(--mono);color:var(--dim);text-transform:uppercase;letter-spacing:.08em;padding-top:3px}
dd{margin:0}
pre{white-space:pre-wrap;word-wrap:break-word;font:12px/1.55 var(--mono);color:#e6dccd;background:#0f0c0a;border:1px solid var(--line);border-radius:6px;padding:10px;margin:0;max-height:180px;overflow:auto}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{font:600 13px Inter;color:#1a120a;background:var(--card);border:0;border-radius:999px;padding:6px 14px;cursor:pointer;text-decoration:none}
.btn.ghost{background:none;color:var(--card);border:1px solid var(--card)}
button:focus-visible,a:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.ok{font:12px var(--mono);color:var(--ok)}
ul.ins{margin:0;padding-left:20px;display:grid;gap:6px;max-width:80ch}
.layers td:first-child{font:600 12px var(--mono);color:var(--acc);text-transform:uppercase}
'''

HEAD = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title><link rel="icon" href="../../favicon.svg"><link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>{css}</style></head><body>'''


def esc(s):
    return str(s if s is not None else '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def still(sid, w=None):
    return f'refs/stills/{esc(sid)}.jpg'


def nav(dos, cur):
    links = ''.join(f'<a href="{esc(d["num"])}.html"{" aria-current=\"page\"" if d["num"] == cur else ""}>{esc(d["num"])}</a>' for d in dos)
    return f'''<header class="top"><a href="../../index.html" id="wy-index">← Index</a><a href="index.html">All poems</a>{links}<a href="../kits.html">Character kits</a></header>'''


SCRIPT = '''<script>
const P = JSON.parse(document.getElementById('prompts').textContent);
document.body.addEventListener('click', e => {
  const b = e.target.closest('button.btn[data-i]'); if (!b) return;
  const ok = b.parentElement.querySelector('.ok');
  const done = () => { ok.textContent = 'Copied'; setTimeout(() => ok.textContent = '', 1600); };
  const fallback = () => { const pre = b.closest('.card,.cast')?.querySelector('pre'); if (pre) { const r = document.createRange(); r.selectNodeContents(pre); const s = getSelection(); s.removeAllRanges(); s.addRange(r); } ok.textContent = 'Press Ctrl+C / Cmd+C'; };
  try { navigator.clipboard.writeText(P[+b.dataset.i]).then(done, fallback); } catch (err) { fallback(); }
});
if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
</script><script src="../../nav.js" defer></script></body></html>'''


def page(D, dos):
    n = D['num']
    prompts = []

    def copy(text):
        prompts.append(text)
        return f'<button class="btn" data-i="{len(prompts) - 1}">Copy prompt</button>'
    best = D.get('best_footage') or []
    hero = best[0]['still'] if best else None
    v2p = next((p for p in V2['poems'] if p['num'] == n), {'characters': []})
    acts = {c['id']: c for c in v2p['characters']}
    castv2 = {c['id']: c for c in V2['cast']}
    kits = json.load(open(os.path.join(POEMS, 'kits', f'{n}.json'))) if os.path.exists(os.path.join(POEMS, 'kits', f'{n}.json')) else []
    h = [HEAD.format(title=f"{n} {esc(D.get('title'))} · production design", css=CSS), nav(dos, n), '<main>']
    # hero
    h.append(f'''<section class="hero"><div style="display:grid;gap:14px"><div class="dim" style="font:12px var(--mono);letter-spacing:.12em">POEM {esc(n)} · {esc(D.get('district', ''))}</div>
      <h1>{esc(D.get('title'))}</h1><p class="essence">{esc(D.get('essence'))}</p>
      <div class="swatches">{''.join(f'<span style="background:{esc(c)}" title="{esc(c)}"></span>' for c in D.get('palette') or [])}</div><p class="dim">{esc(D.get('palette_notes'))}</p></div>
      <div>{f'<img src="{still(hero)}" alt="{esc(best[0].get("element"))}">' if hero else ''}</div></section>''')
    # the poem and its arc
    h.append('<section id="poem"><h2>The poem</h2><div class="text">' + ''.join(f'<div><code>{esc(l.get("t"))}</code>{esc(l.get("line"))}</div>' for l in D.get('full_text') or []) + '</div>')
    h.append('<div class="tablewrap"><table><thead><tr><th>Movement</th><th>Beat</th><th>Feeling</th><th>The image</th></tr></thead><tbody>' +
             ''.join(f'<tr><td>{esc(a.get("movement"))}</td><td>{esc(a.get("beat"))}</td><td>{esc(a.get("emotion"))}</td><td>{esc(a.get("image"))}</td></tr>' for a in D.get('arc') or []) + '</tbody></table></div></section>')
    # footage
    h.append('<section id="footage"><h2>From our footage</h2><p class="dim">The strongest elements in what we already have, and what each is for.</p><div class="grid">' +
             ''.join(f'<div class="card"><img src="{still(b["still"])}" alt="{esc(b.get("element"))}" loading="lazy"><div class="chips"><span class="chip hot">{esc(b.get("use_for"))}</span></div><h3>{esc(b.get("element"))}</h3><p class="dim">{esc(b.get("why"))}</p></div>' for b in best) + '</div>')
    if D.get('clips'):
        h.append('<div class="tablewrap"><table><thead><tr><th>Clip</th><th>Use for</th><th>Why</th></tr></thead><tbody>' +
                 ''.join(f'<tr><td style="font:12px var(--mono)">{esc(c.get("file"))}</td><td>{esc(c.get("use_for"))}</td><td>{esc(c.get("why"))}</td></tr>' for c in D['clips']) + '</tbody></table></div>')
    h.append('</section>')
    # cast
    h.append('<section id="cast"><h2>The cast</h2>')
    for c in D.get('characters') or []:
        a = acts.get(c.get('id'))
        img = f'{V2REL}/{a["action"]["image"]}' if a else None
        side = f'<a href="{esc(img)}" target="_blank" rel="noopener"><img src="{esc(img)}" alt="{esc(c.get("id"))} action sheet" loading="lazy"></a>' if img else '<p class="dim">no action sheet yet</p>'
        cv = castv2.get(c.get('id'), {})
        h.append(f'''<div class="cast" id="c-{esc(c.get("id"))}"><div style="display:grid;gap:8px;align-content:start">{side}
          {f'<div class="row">{copy(a["action"]["prompt"])}<a class="btn ghost" href="{esc(img)}" download>Image</a><a class="btn ghost" href="../kits.html#c-{esc(c.get("id"))}">Costume kits</a><span class="ok" aria-live="polite"></span></div>' if a else ''}</div>
          <div style="display:grid;gap:10px;align-content:start"><h3 style="font-size:20px">{esc(cv.get("name", c.get("id")))} <span class="chip hot">{esc(c.get("costume"))}</span></h3>
          <p>{esc(c.get("role_in_poem"))}</p><p class="dim">{esc(c.get("arc"))}</p>
          <dl><dt>Actions</dt><dd>{"<br>".join(esc(x) for x in c.get("signature_actions") or [])}</dd>
          <dt>Faces</dt><dd><div class="chips">{"".join(f'<span class="chip">{esc(x)}</span>' for x in c.get("expressions") or [])}</div></dd>
          <dt>Hands</dt><dd><div class="chips">{"".join(f'<span class="chip">{esc(x)}</span>' for x in c.get("hands") or [])}</div></dd>
          <dt>Props</dt><dd><div class="chips">{"".join(f'<span class="chip">{esc(x)}</span>' for x in c.get("props") or [])}</div></dd>
          <dt>Design</dt><dd>{esc(c.get("design_notes"))}</dd>
          <dt>New parts</dt><dd>{"<br>".join(esc(x) for x in c.get("new_parts") or [])}</dd></dl></div></div>''')
    h.append('</section>')
    # props
    h.append('<section id="props"><h2>Props</h2><div class="grid">' + ''.join(
        f'''<div class="card"><h3>{"★ " if p.get("hero") else ""}{esc(p.get("name") or p.get("id"))} <span class="dim" style="font:12px var(--mono)">{esc(p.get("scale_cm"))} cm</span></h3>
        <p>{esc(p.get("look"))}</p><p class="dim"><b>Build:</b> {esc(p.get("build"))}</p>
        <div class="chips">{"".join(f'<span class="chip hot">{esc(s)}</span>' for s in p.get("states") or [])}{"".join(f'<span class="chip">{esc(w)}</span>' for w in p.get("who") or [])}</div>
        <div class="refs">{"".join(f'<img src="{still(r)}" alt="reference still" loading="lazy">' for r in p.get("refs") or [])}</div></div>''' for p in D.get('props') or []) + '</div></section>')
    # sets
    h.append('<section id="places"><h2>Places</h2><div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(420px,1fr))">' + ''.join(
        f'''<div class="card" id="s-{esc(s.get("id"))}"><div class="refs">{"".join(f'<img src="{still(r)}" alt="reference still" loading="lazy" style="width:190px;height:107px">' for r in s.get("refs") or [])}</div>
        <h3>{esc(s.get("name"))}</h3><p>{esc(s.get("look"))}</p><p class="dim"><b>Light:</b> {esc(s.get("light"))}</p>
        <div class="tablewrap layers"><table><tbody>{"".join(f'<tr><td>{k}</td><td>{esc((s.get("layers") or {}).get(k))}</td></tr>' for k in ("sky", "back", "mid", "front", "floor"))}</tbody></table></div>
        {f'<p class="dim">Also in: {esc(", ".join(s.get("reuse") or []))}</p>' if s.get("reuse") else ''}</div>''' for s in D.get('sets') or []) + '</div></section>')
    # fx and actions
    h.append('<section id="fx"><h2>Effects and actions</h2><div class="tablewrap"><table><thead><tr><th>Effect</th><th>How</th><th>Note</th></tr></thead><tbody>' +
             ''.join(f'<tr><td>{esc(f.get("id"))}</td><td>{esc(f.get("how"))}</td><td>{esc(f.get("note"))}</td></tr>' for f in D.get('fx') or []) + '</tbody></table></div>')
    h.append('<div class="tablewrap"><table><thead><tr><th>Action</th><th>Who</th><th>Move</th><th>Pose kit</th><th>Timing</th></tr></thead><tbody>' +
             ''.join(f'<tr><td>{esc(a.get("id"))}</td><td>{esc(a.get("who"))}</td><td>{esc(a.get("move"))}</td><td style="font:12px var(--mono)">{esc(a.get("pose_kit"))}</td><td>{esc(a.get("timing"))}</td></tr>' for a in D.get('actions') or []) + '</tbody></table></div></section>')
    # kits
    h.append('<section id="kits"><h2>Kits to generate</h2><p class="dim">One image + one prompt each. The characters\' action sheets are in the cast above; their costume kits are on the character kits page.</p><div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(420px,1fr))">' + ''.join(
        f'''<div class="card"><a href="{esc(k["image"])}" target="_blank" rel="noopener"><img src="{esc(k["image"])}" alt="{esc(k["id"])} pack" loading="lazy"></a>
        <h3>{esc(k["title"])} <span class="chip">{esc(k["kind"])}</span></h3><pre>{esc(k["prompt"])}</pre>
        <div class="row">{copy(k["prompt"])}<a class="btn ghost" href="{esc(k["image"])}" download>Image</a><span class="ok" aria-live="polite"></span></div></div>''' for k in kits) + '</div>')
    if D.get('kits_to_build'):
        h.append('<div class="tablewrap"><table><thead><tr><th>Next kit</th><th>Kind</th><th>What</th><th>Why</th></tr></thead><tbody>' +
                 ''.join(f'<tr><td style="font:12px var(--mono)">{esc(k.get("id"))}</td><td>{esc(k.get("kind"))}</td><td>{esc(k.get("what"))}</td><td>{esc(k.get("why"))}</td></tr>' for k in D['kits_to_build']) + '</tbody></table></div>')
    h.append('</section>')
    h.append('<section id="insights"><h2>Insights</h2><ul class="ins">' + ''.join(f'<li>{esc(x)}</li>' for x in D.get('insights') or []) + '</ul>' +
             ('<h3>For later poems</h3><ul class="ins">' + ''.join(f'<li>{esc(x)}</li>' for x in D.get('future') or []) + '</ul>' if D.get('future') else '') + '</section>')
    h.append('</main><script id="prompts" type="application/json">' + json.dumps(prompts).replace('</', '<\\/') + '</script>' + SCRIPT)
    return '\n'.join(h)


def index(dos):
    h = [HEAD.format(title='Poems · production design', css=CSS), nav(dos, None), '<main><section><h1>Where you go <span>when you leave</span></h1>',
         '<p class="essence">Fourteen poems, one page each: the poem, the best of our footage, the cast with their kits, the props in every state, the places as layers, and every kit to generate.</p></section>',
         '<section><div class="grid">']
    for D in dos:
        b = (D.get('best_footage') or [{}])[0].get('still')
        h.append(f'''<a class="card" href="{esc(D["num"])}.html" style="text-decoration:none;color:inherit">{f'<img src="{still(b)}" alt="" loading="lazy">' if b else ''}
          <div class="dim" style="font:12px var(--mono)">{esc(D["num"])} · {esc(D.get("district", ""))}</div><h3 style="font-size:19px">{esc(D.get("title"))}</h3><p class="dim">{esc(D.get("essence"))}</p>
          <div class="chips"><span class="chip">{len(D.get("characters") or [])} characters</span><span class="chip">{len(D.get("props") or [])} props</span><span class="chip">{len(D.get("sets") or [])} places</span></div></a>''')
    h.append('</div></section></main><script id="prompts" type="application/json">[]</script>' + SCRIPT)
    return '\n'.join(h)


def main():
    dos = []
    for f in sorted(glob.glob(os.path.join(POEMS, 'dossier', '[0-9][0-9].json'))):
        D = json.load(open(f))
        D['num'] = D.get('num') or os.path.basename(f)[:2]
        dos.append(D)
    for D in dos:
        open(os.path.join(POEMS, f"{D['num']}.html"), 'w').write(page(D, dos))
    open(os.path.join(POEMS, 'index.html'), 'w').write(index(dos))
    print(len(dos), 'poem pages')


if __name__ == '__main__':
    main()
