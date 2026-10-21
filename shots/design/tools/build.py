#!/usr/bin/env python3
"""PRODUCTION DESIGN, STEP 3: the pages. From data/NN.json (what we have, gather.py) and data/NN.design.json (the designer's reading,
kit and needs) writes design/index.html, design/NN.html (one per poem) and design/cast/<id>.html (one kit per character, across poems).
  python3 build.py"""
import os, json, glob, html, re
H = os.path.dirname(os.path.abspath(__file__)); DES = os.path.dirname(H); SHOTS = os.path.dirname(DES)
KITS = json.load(open(os.path.join(SHOTS, 'arena/parts/kit3/v2/kits.json'))); CAST = {c['id']: c for c in KITS['cast']}
os.makedirs(os.path.join(DES, 'cast'), exist_ok=True)
e = lambda s: html.escape(str(s if s is not None else ''))
NAME = lambda cid: (CAST.get(cid) or {}).get('name') or str(cid).replace('_', ' ').upper()

CSS = """
:root{--bg:#0d0b0a;--panel:#16120f;--line:#2a221c;--ink:#efe6da;--dim:#9a8d7e;--card:#c79a62;--ok:#9fe08a;--mid:#e7c35a;--bad:#ff7b6b;--acc:#e7a35a;--mono:'JetBrains Mono',ui-monospace,monospace}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}
header.top{display:flex;align-items:center;gap:12px;padding:12px max(16px,env(safe-area-inset-right)) 12px max(16px,env(safe-area-inset-left));border-bottom:1px solid var(--line);flex-wrap:wrap;position:sticky;top:0;background:var(--bg);z-index:5}
header.top h1{font:400 24px 'Permanent Marker',cursive;margin:0}
header.top h1 small{font:12px var(--mono);color:var(--dim);margin-left:10px;letter-spacing:.08em}
header.top a{color:var(--dim);font:12px var(--mono);text-decoration:none;border:1px solid var(--line);padding:4px 10px;border-radius:999px}
header.top a:hover{color:var(--ink);border-color:var(--card)}
header.top .sp{flex:1}
nav.toc{display:flex;gap:6px;flex-wrap:wrap}
nav.toc a{font:12px var(--mono);color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:4px 10px;text-decoration:none}
nav.toc a:hover,nav.toc a.on{border-color:var(--card);color:var(--card)}
main{max-width:1360px;margin:0 auto;padding:22px max(16px,env(safe-area-inset-right)) 80px max(16px,env(safe-area-inset-left));display:grid;gap:40px}
h2{font:400 28px 'Permanent Marker',cursive;margin:0;color:var(--card)}
h3{font:600 16px Inter;margin:0}
p{margin:0;max-width:78ch}
.dim{color:var(--dim)}.mono{font-family:var(--mono);font-size:12px}
section{display:grid;gap:14px;min-width:0;scroll-margin-top:70px}
.lede{font-size:18px;max-width:70ch}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.grid.sm{grid-template-columns:repeat(auto-fill,minmax(170px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;display:grid;gap:8px;align-content:start;min-width:0}
.card img{width:100%;height:auto;display:block;border-radius:4px;background:#000}
.card .t{font:600 13px Inter}
.card p{font-size:13.5px}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{font:11.5px var(--mono);color:var(--ink);background:#21190f;border:1px solid var(--line);border-radius:999px;padding:1px 8px;white-space:normal;max-width:100%}
.chip.have{border-color:var(--ok);color:var(--ok)}.chip.partial{border-color:var(--mid);color:var(--mid)}.chip.need{border-color:var(--bad);color:var(--bad)}
.chip.A{background:#3a2412;border-color:var(--acc);color:var(--acc)}
.sw{display:flex;gap:8px;flex-wrap:wrap}
.sw div{display:grid;gap:3px;width:118px;font-size:12px}
.sw i{display:block;height:46px;border-radius:6px;border:1px solid var(--line)}
.poem-text{font:16px/1.7 Georgia,serif;color:#f3eadc;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 18px;max-height:420px;overflow:auto}
.poem-text span{display:block}.poem-text b{font:11px var(--mono);color:var(--dim);margin-right:10px;font-weight:400}
.two{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:18px}
@media (max-width:880px){.two{grid-template-columns:minmax(0,1fr)}}
section>*,.two>*,.card>*{min-width:0}
p,span,td,li,figcaption,h2,h3{overflow-wrap:anywhere}
.hero img{max-width:100%}
ul.tight{margin:0;padding-left:18px;display:grid;gap:4px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{font:600 12px var(--mono);color:var(--dim)}
.tbl{overflow-x:auto}
details>summary{cursor:pointer;font:600 12.5px var(--mono);color:var(--card);padding:4px 0}
pre{white-space:pre-wrap;word-wrap:break-word;font:12px/1.55 var(--mono);color:#e6dccd;background:#0f0c0a;border:1px solid var(--line);border-radius:6px;padding:10px;margin:0;max-height:220px;overflow:auto}
button.copy{font:600 12px Inter;color:#1a120a;background:var(--card);border:0;border-radius:999px;padding:4px 12px;cursor:pointer;justify-self:start}
button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.layers{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;font-size:13px}
.layers b{font:600 11.5px var(--mono);color:var(--dim)}
.thumbs{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:6px}
.thumbs figure{margin:0;display:grid;gap:2px}.thumbs img{width:100%;border-radius:3px;display:block}
.thumbs figcaption{font:10.5px/1.3 var(--mono);color:var(--dim)}
.pcard{display:grid;grid-template-columns:110px 1fr;gap:10px;align-items:start}
.pcard img{width:110px;border-radius:4px}
.hero{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px}
.hero img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:6px;display:block}
a{color:var(--card)}
"""
JS = """<script>document.addEventListener('click',ev=>{const b=ev.target.closest('button.copy');if(!b)return;const t=document.getElementById(b.dataset.for).innerText;
navigator.clipboard&&navigator.clipboard.writeText(t).then(()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy prompt',1400)})});</script>"""
def page(title, sub, body, root='..', extra_links=''):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title><link rel="icon" href="{root}/../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header class="top"><a href="{root}/../index.html" id="wy-index">← Index</a><h1>{e(title.split(' · ')[0])}<small>{e(sub)}</small></h1><span class="sp"></span>{extra_links}</header>
<main>{body}</main>{JS}<script src="{root}/../nav.js" defer></script></body></html>"""

chip = lambda s, cls=None: f'<span class="chip {e(cls or s)}">{e(s)}</span>' if s else ''
def img(src, alt='', pre=''):
    return f'<img loading="lazy" src="{e(pre + src)}" alt="{e(alt)}">' if src else ''
pid = [0]
def prompt_block(text):
    if not text: return ''
    pid[0] += 1; i = f'pr{pid[0]}'
    return f'<details><summary>Generation prompt</summary><pre id="{i}">{e(text)}</pre><button class="copy" data-for="{i}">Copy prompt</button></details>'

D = {}
for f in sorted(glob.glob(os.path.join(DES, 'data', '[0-9][0-9].json'))):
    n = os.path.basename(f)[:2]; d = json.load(open(f)); df = os.path.join(DES, 'data', f'{n}.design.json')
    d['design'] = json.load(open(df)) if os.path.exists(df) else {}
    D[n] = d
TOC = '<nav class="toc">' + ''.join(f'<a href="{n}.html">{n} {e(D[n]["title"])}</a>' for n in D) + '</nav>'

def poem_page(n):
    d = D[n]; g = d['design']; pre = ''
    secs = []
    secs.append(f"""<section><div class="chips"><span class="chip">poem {n}</span><span class="chip">{e(d.get('style'))}</span><span class="chip">{len(d['lines'])} lines</span>
      <span class="chip">{sum(len(s['shots']) for s in d['scenes'])} shots in the treatment</span></div>
      <p class="lede">{e(g.get('logline', ''))}</p>
      <div class="hero">{''.join(img(b['thumb'], b.get('label')) for b in (g.get('best_elements') or [])[:5])}</div></section>""")
    paras = ''.join(f'<p>{e(p)}</p>' for p in re.split(r'\n\s*\n', g.get('reading', '')) if p.strip())
    secs.append(f"""<section id="poem"><h2>The poem</h2><div class="two"><div class="poem-text">{''.join(f'<span><b>{l["t0"]:.0f}s</b>{e(l["text"])}</span>' for l in d['lines'])}</div>
      <div style="display:grid;gap:12px;align-content:start">{paras}
      <div class="chips">{''.join(chip(m, 'm') for m in g.get('motifs', []))}</div></div></div></section>""")
    if g.get('palette'):
        secs.append(f"""<section id="look"><h2>Look</h2><div class="sw">{''.join(f'<div><i style="background:{e(c["hex"])}"></i><b>{e(c["name"])}</b><span class="dim">{e(c["hex"])} · {e(c.get("where"))}</span></div>' for c in g['palette'])}</div>
          <p>{e(g.get('light_and_texture'))}</p></section>""")
    if g.get('best_elements'):
        secs.append(f"""<section id="best"><h2>Our best elements</h2><p class="dim">The strongest things we already have for this poem: generated footage, Atlantis views, found film and painted kit sheets.</p>
          <div class="grid">{''.join(f'<div class="card">{img(b["thumb"], b.get("label"))}<div class="chips">{chip(b.get("kind"), "m")}</div><div class="t">{e(b.get("label"))}</div><p>{e(b.get("use"))}</p><p class="dim">{e(b.get("why"))}</p></div>' for b in g['best_elements'])}</div></section>""")
    if g.get('gaps'):
        secs.append(f'<section id="gaps"><h2>What we need</h2><ul class="tight">{"".join(f"<li>{e(x)}</li>" for x in g["gaps"])}</ul></section>')
    # characters
    cards = []
    for c in g.get('characters', []):
        kc = next((x for x in d['characters'] if x['id'] == c.get('id')), {})
        acts = ''.join(f'<tr><td><b>{e(a.get("name"))}</b></td><td>{e(a.get("beats"))}</td><td>{e(a.get("cutout"))}</td></tr>' for a in c.get('actions', []))
        cards.append(f"""<div class="card"><div class="two"><div style="display:grid;gap:8px;align-content:start">
          <h3>{e(NAME(c.get('id')))} <a class="mono" href="cast/{e(c.get('id'))}.html">kit →</a></h3>
          <div class="chips">{chip(c.get('status'))}</div><p>{e(c.get('role'))}</p><p><b>Costume.</b> {e(c.get('costume'))}</p>
          <p><b>Expressions.</b> {e(', '.join(c.get('expressions', [])))}</p><p><b>Hands.</b> {e(', '.join(c.get('hands', [])))}</p>
          <p><b>Cards to paint.</b> {e('; '.join(c.get('cards_needed', [])))}</p><p class="dim">{e(c.get('note'))}</p></div>
          <div class="card" style="align-content:center"><p class="dim">{'Its action sheet for this poem is on Character Kits v2.' if kc.get('action_sheet') else 'No action sheet exists for this poem yet.'}</p>{f'<a class="mono" href="../kits.html#{e(n)}">open the action sheet →</a>' if kc.get('action_sheet') else ''}</div></div>
          {f'<div class="tbl"><table><tr><th>action</th><th>beats</th><th>how the card does it</th></tr>{acts}</table></div>' if acts else ''}</div>""")
    if cards: secs.append(f'<section id="cast"><h2>Characters</h2>{"".join(cards)}</section>')
    # props
    if g.get('props'):
        found = {p['id']: p['found'] for p in d.get('props', [])}
        pc = []
        for p in sorted(g['props'], key=lambda p: (p.get('priority') or 'C', p.get('id'))):
            fr = found.get(p.get('id'), {})
            refs = ''.join(f'<figure>{img(a["thumb"])}<figcaption>{e(a["title"])} · {e(a.get("year") or "")}</figcaption></figure>' for a in fr.get('archive', [])[:4])
            refs += ''.join(f'<figure>{img(a["thumb"])}<figcaption>ours · {e(a["name"][:28])}</figcaption></figure>' for a in fr.get('gen', [])[:2])
            pc.append(f"""<div class="card"><div class="pcard">{img(p.get('ref'), p.get('id')) or '<div></div>'}<div style="display:grid;gap:4px">
              <div class="t">{e(p.get('id'))}</div><div class="chips">{chip(p.get('priority'), 'A' if p.get('priority') == 'A' else 'm')}{chip(p.get('status'))}{chip(p.get('build'), 'm')}</div></div></div>
              <p>{e(p.get('what'))}</p><p class="dim">{e(p.get('design'))}</p>{f'<details><summary>References found</summary><div class="thumbs">{refs}</div></details>' if refs else ''}{prompt_block(p.get('prompt'))}</div>""")
        secs.append(f'<section id="props"><h2>Props</h2><p class="dim">Sorted by priority. Each has its design, how to build it, the references found in the archive and our footage, and a prompt for its card sheet.</p><div class="grid">{"".join(pc)}</div></section>')
    # sets
    if g.get('sets'):
        found = {s['id']: s['found'] for s in d.get('sets', [])}
        sc = []
        for s in g['sets']:
            fr = found.get(s.get('id'), {}); L = s.get('layers') or {}
            refs = ''.join(f'<figure>{img(a["thumb"])}<figcaption>ours · {e(a["name"][:30])}</figcaption></figure>' for a in fr.get('gen', [])[:4])
            refs += ''.join(f'<figure>{img(a["thumb"])}<figcaption>view · {e(a["district"])}</figcaption></figure>' for a in fr.get('views', [])[:3])
            refs += ''.join(f'<figure>{img(a["thumb"])}<figcaption>{e(a["title"])} · {e(a.get("year") or "")}</figcaption></figure>' for a in fr.get('archive', [])[:5])
            sc.append(f"""<div class="card"><div class="two"><div>{img(s.get('plate'), s.get('id')) or '<p class="dim">No plate yet.</p>'}</div><div style="display:grid;gap:6px;align-content:start">
              <h3>{e(s.get('id'))}</h3><div class="chips">{chip(s.get('status'))}</div><p>{e(s.get('design'))}</p>
              <div class="layers">{''.join(f'<b>{k}</b><span>{e(L.get(k))}</span>' for k in ('far', 'mid', 'near', 'occluders') if L.get(k))}</div>
              <p><b>Where the archive opens:</b> {e('; '.join(s.get('surfaces', [])))}</p></div></div>
              <details><summary>References: our footage, Atlantis views, found film</summary><div class="thumbs">{refs}</div></details>{prompt_block(s.get('prompt'))}</div>""")
        secs.append(f'<section id="sets"><h2>Places</h2>{"".join(sc)}</section>')
    if g.get('fx'):
        fx_rows = ''.join(f"<tr><td><b>{e(x.get('id'))}</b></td><td>{e(x.get('how'))}</td></tr>" for x in g['fx'])
        secs.append(f'<section id="fx"><h2>Effects</h2><div class="tbl"><table><tr><th>effect</th><th>how, in this cut-out world</th></tr>{fx_rows}</table></div></section>')
    ps = d.get('passage') or {}; a = ps.get('answer') or {}; gp = g.get('passage') or {}
    secs.append(f"""<section id="passage"><h2>The puppet passage</h2><div class="two"><div class="card"><p class="mono dim">his line · {e(ps.get('line_id'))}</p><p style="font:17px Georgia,serif">“{e(ps.get('line'))}”</p>
      <p class="mono dim">the archive answers · {e(a.get('title'))} ({e(a.get('year') or 'n.d.')})</p><p style="font:17px Georgia,serif">“{e(a.get('said'))}”</p>
      <p class="dim">{e(ps.get('gesture'))} · {e(ps.get('surface'))}</p></div>
      <div style="display:grid;gap:8px;align-content:start"><p><b>Keep.</b> {e(gp.get('keep'))}</p><p><b>Better.</b> {e(gp.get('better'))}</p>
      {f'<p><b>Other lines that could carry one:</b></p><ul class="tight">{"".join(f"<li>{e(x)}</li>" for x in gp.get("alt_lines", []))}</ul>' if gp.get('alt_lines') else ''}</div></div></section>""")
    if g.get('ideas'):
        secs.append(f'<section id="ideas"><h2>Scene ideas</h2><ol class="tight">{"".join(f"<li>{e(x)}</li>" for x in g["ideas"])}</ol></section>')
    if g.get('references'):
        ref_rows = ''.join(f"<tr><td>{e(r.get('what'))}</td><td>{e(r.get('look_for'))}</td></tr>" for r in g['references'])
        secs.append(f'<section id="refs"><h2>References to look for</h2><div class="tbl"><table><tr><th>what</th><th>where to look</th></tr>{ref_rows}</table></div></section>')
    secs.append(f"""<section id="footage"><h2>Our footage for this poem</h2><p class="dim">The 20 generated clips and 8 Atlantis views closest to the poem (CLIP, image against its treatment and lines).</p>
      <div class="thumbs">{''.join(f'<figure>{img(x["thumb"])}<figcaption>{e(x["lib"])} · {e(x["name"][:34])}</figcaption></figure>' for x in d.get('poem_gen', []))}
      {''.join(f'<figure>{img(x["thumb"])}<figcaption>Atlantis view</figcaption></figure>' for x in d.get('poem_views', []))}</div></section>""")
    if g.get('kit'):
        order = {'need': 0, 'partial': 1, 'have': 2}
        rows = ''.join(f'<tr><td>{chip(k.get("status"))}</td><td>{e(k.get("category"))}</td><td>{e(k.get("item"))}</td><td class="dim">{e(k.get("source"))}</td></tr>'
                       for k in sorted(g['kit'], key=lambda k: (order.get(k.get('status'), 3), k.get('category') or '')))
        cnt = {s: sum(1 for k in g['kit'] if k.get('status') == s) for s in ('need', 'partial', 'have')}
        counts = chip(f"{cnt['need']} to make", 'need') + chip(f"{cnt['partial']} partial", 'partial') + chip(f"{cnt['have']} have", 'have')
        secs.append(f'<section id="kit"><h2>The kit</h2><div class="chips">{counts}</div><div class="tbl"><table><tr><th>status</th><th>kind</th><th>item</th><th>source</th></tr>{rows}</table></div></section>')
    nav = '<nav class="toc">' + ''.join(f'<a href="#{i}">{t}</a>' for i, t in [('poem', 'Poem'), ('look', 'Look'), ('best', 'Best'), ('gaps', 'Needs'), ('cast', 'Characters'), ('props', 'Props'), ('sets', 'Places'), ('fx', 'Effects'), ('passage', 'Passage'), ('ideas', 'Ideas'), ('refs', 'References'), ('footage', 'Footage'), ('kit', 'Kit')]) + '</nav>'
    prev_ = f'{int(n) - 1:02d}'; next_ = f'{int(n) + 1:02d}'
    links = (f'<a href="{prev_}.html">← {prev_}</a>' if prev_ in D else '') + '<a href="index.html">All poems</a>' + (f'<a href="{next_}.html">{next_} →</a>' if next_ in D else '')
    return page(f'{n} {d["title"]} · Production Design · WYGWYL', 'PRODUCTION DESIGN · KIT · NEEDS', nav + ''.join(secs), '..', links)

for n in D: open(os.path.join(DES, f'{n}.html'), 'w').write(poem_page(n))

# the cast: one kit per character across all poems
chars = {}
for n, d in D.items():
    for c in d['design'].get('characters', []):
        chars.setdefault(c.get('id'), []).append((n, c))
for cid, rows in chars.items():
    k = CAST.get(cid) or {}; name = NAME(cid)
    packs = ''.join(f'<div class="card">{img("../" + "../arena/parts/kit3/" + pk["image"], pk["sheet"])}<div class="t">{e(c["costume"])} · {e(pk["sheet"])}</div></div>' for c in k.get('costumes', []) for pk in c.get('packs', []))
    need = sorted({x for n, c in rows for x in c.get('cards_needed', [])}); npk = sum(len(c.get('packs', [])) for c in k.get('costumes', []))
    per = ''.join(f"""<div class="card"><h3><a href="../{n}.html">{n} {e(D[n]['title'])}</a></h3><div class="chips">{chip(c.get('status'))}</div><p>{e(c.get('role'))}</p>
        <p><b>Costume.</b> {e(c.get('costume'))}</p><p><b>Expressions.</b> {e(', '.join(c.get('expressions', [])))}</p><p><b>Hands.</b> {e(', '.join(c.get('hands', [])))}</p>
        <p><b>Actions.</b> {e('; '.join(a.get('name', '') for a in c.get('actions', [])))}</p><p><b>Cards.</b> {e('; '.join(c.get('cards_needed', [])))}</p></div>""" for n, c in rows)
    acts = ''.join(f'<tr><td>{n}</td><td><b>{e(a.get("name"))}</b></td><td>{e(a.get("beats"))}</td><td>{e(a.get("cutout"))}</td></tr>' for n, c in rows for a in c.get('actions', []))
    body = f"""<section><p class="lede">{e((k.get('who') or '').replace(', as in the reference photos', '') or 'A new character the designers found in the poems: no kit sheets exist yet.')}</p><div class="chips">{''.join(chip(f'{n} {D[n]["title"]}', 'm') for n, _ in rows)}</div></section>
      <section><h2>Across the poems</h2><div class="grid">{per}</div></section>
      <section><h2>Every action</h2><div class="tbl"><table><tr><th>poem</th><th>action</th><th>beats</th><th>how the card does it</th></tr>{acts}</table></div></section>
      <section><h2>Cards to paint</h2><ul class="tight">{''.join(f'<li>{e(x)}</li>' for x in need)}</ul></section>
      {f'<section><h2>Sheets already laid out</h2><p>{npk} sheets on <a href="../../kits.html">Character Kits v2</a>, each one image and one prompt.</p></section>' if npk else ''}"""
    open(os.path.join(DES, 'cast', f'{cid}.html'), 'w').write(page(f'{name} · Character Kit · WYGWYL', 'CHARACTER KIT · EVERY POEM', body, '../..', '<a href="../index.html">All poems</a>'))

# the index
cards = []
for n, d in D.items():
    g = d['design']; kit = g.get('kit', [])
    need = sum(1 for x in kit if x.get('status') == 'need'); have = sum(1 for x in kit if x.get('status') == 'have')
    sw = ''.join(f'<i title="{e(c["name"])}" style="display:inline-block;width:22px;height:14px;border-radius:3px;background:{e(c["hex"])}"></i>' for c in g.get('palette', []))
    th = (g.get('best_elements') or [{}])[0].get('thumb') or (d.get('poem_gen') or [{}])[0].get('thumb')
    cards.append(f"""<a class="card" href="{n}.html" style="text-decoration:none;color:inherit">{img(th)}<h3><span style="font:400 22px 'Permanent Marker';color:var(--acc)">{n}</span> {e(d['title'])}</h3>
      <p>{e(g.get('logline', ''))}</p><div style="display:flex;gap:3px">{sw}</div><div class="chips">{chip(f'{need} to make', 'need')}{chip(f'{have} have', 'have')}{chip(f'{len(g.get("props", []))} props', 'm')}</div></a>""")
castc = ''.join(f'<a class="card" href="cast/{e(cid)}.html" style="text-decoration:none;color:inherit"><h3>{e(NAME(cid))}</h3><p class="dim">{len(rows)} poems · {sum(len(c.get("cards_needed", [])) for _, c in rows)} cards to paint</p></a>' for cid, rows in sorted(chars.items(), key=lambda x: -len(x[1])))
allA = [(n, p) for n, d in D.items() for p in d['design'].get('props', []) if p.get('priority') == 'A' and p.get('status') != 'have']
body = f"""<section><p class="lede">Production design for <i>where you go when you leave</i>: every poem read for what it needs, and matched against what we already have:
  184 generated clips, 100 Atlantis views, 15,149 found-film clips and the painted character sheets. Each poem has a page: its reading, look, best elements, characters, props, places, effects,
  the puppet passage, scene ideas, references to find and a kit checklist. Each character has a kit page across the poems.</p></section>
  <section><h2>Poems</h2><div class="grid">{''.join(cards)}</div></section>
  <section><h2>Character kits</h2><div class="grid sm">{castc}</div></section>
  <section><h2>First props to make</h2><p class="dim">Priority A props across the suite that we don't have yet.</p><div class="tbl"><table><tr><th>poem</th><th>prop</th><th>what</th><th>build</th></tr>
  {''.join(f'<tr><td><a href="{n}.html#props">{n}</a></td><td><b>{e(p.get("id"))}</b></td><td>{e(p.get("what"))}</td><td class="dim">{e(p.get("build"))}</td></tr>' for n, p in allA)}</table></div></section>"""
open(os.path.join(DES, 'index.html'), 'w').write(page('Production Design · WYGWYL', 'EVERY POEM · EVERY CHARACTER · KITS AND NEEDS', body, '..', '<a href="../kits.html">Character Kits v2 →</a>'))
print('pages:', len(D), 'poems,', len(chars), 'characters')
