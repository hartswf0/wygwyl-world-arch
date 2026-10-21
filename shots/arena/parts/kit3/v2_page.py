"""Build shots/kits.html: Character Kits v2, by poem and by character (a site page, not an artifact).

    python3 shots/arena/parts/kit3/v2_page.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REL = os.path.relpath(HERE, SHOTS).replace(os.sep, '/')
D = json.load(open(os.path.join(HERE, 'v2', 'kits.json')))
for c in D['cast']:
    c['chart'] = f"{REL}/v2/templates/{c['build']}.cutchart.png"
    for k in c['costumes']:
        for p in k['packs']:
            p['image'] = f"{REL}/{p['image']}"
for P in D['poems']:
    for c in P['characters']:
        c['action']['image'] = f"{REL}/{c['action']['image']}"

PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Character Kits v2 · WYGWYL</title>
<link rel="icon" href="../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
/* the site's arena palette: warm dark bench, kraft card, marker titles */
:root{--bg:#0d0b0a;--panel:#16120f;--line:#2a221c;--ink:#efe6da;--dim:#9a8d7e;--card:#c79a62;--ok:#9fe08a;--bad:#ff7b6b;--acc:#e7a35a;--mono:'JetBrains Mono',ui-monospace,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}
header{display:flex;align-items:center;gap:12px;padding:12px max(18px,env(safe-area-inset-right)) 12px max(18px,env(safe-area-inset-left));border-bottom:1px solid var(--line);flex-wrap:wrap;position:sticky;top:0;background:var(--bg);z-index:5}
header h1{font:400 24px 'Permanent Marker',cursive;margin:0}
header h1 small{font:12px var(--mono);color:var(--dim);margin-left:10px;letter-spacing:.08em}
header a{color:var(--dim);font:12px var(--mono);text-decoration:none;border:1px solid var(--line);padding:4px 10px;border-radius:999px}
header a:hover{color:var(--ink);border-color:var(--card)}
header .sp{flex:1}
nav.toc{display:flex;gap:6px;flex-wrap:wrap}
nav.toc a{font:12px var(--mono);color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:4px 10px;text-decoration:none}
nav.toc a:hover{border-color:var(--card);color:var(--card)}
main{max-width:1360px;margin:0 auto;padding:24px max(18px,env(safe-area-inset-right)) 80px max(18px,env(safe-area-inset-left));display:grid;gap:44px}
h2{font:400 30px 'Permanent Marker',cursive;margin:0;color:var(--card)}
h3{font:600 17px Inter;margin:0}
p{margin:0;max-width:76ch}
.dim{color:var(--dim)}
section{display:grid;gap:16px;min-width:0}
.cast-note{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}
.cast-note div{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}
.cast-note b{color:var(--card)}
.poem,.who{scroll-margin-top:72px}
.poem{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;display:grid;gap:14px}
.poem>header{position:static;padding:0;border:0;background:none;gap:12px}
.poem>header .n{font:400 30px 'Permanent Marker';color:var(--acc)}
.char{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:14px;border-top:1px solid var(--line);padding-top:14px}
@media (max-width:880px){.char{grid-template-columns:1fr}}
.char img{width:100%;height:auto;display:block;border-radius:4px;background:#fff}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{font:12px var(--mono);color:var(--ink);background:#21190f;border:1px solid var(--line);border-radius:999px;padding:2px 9px}
.chip.cos{border-color:var(--card);color:var(--card)}
pre{white-space:pre-wrap;word-wrap:break-word;font:12px/1.55 var(--mono);color:#e6dccd;background:#0f0c0a;border:1px solid var(--line);border-radius:6px;padding:10px;margin:0;max-height:200px;overflow:auto}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{font:600 13px Inter;color:#1a120a;background:var(--card);border:0;border-radius:999px;padding:6px 14px;cursor:pointer;text-decoration:none}
.btn.ghost{background:none;color:var(--card);border:1px solid var(--card)}
button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.ok{font:12px var(--mono);color:var(--ok)}
details>summary{cursor:pointer;font:600 13px var(--mono);color:var(--card);padding:6px 0}
.packs{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:8px}
.pk{background:#120f0c;border:1px solid var(--line);border-radius:8px;padding:8px;display:grid;gap:6px;align-content:start}
.pk img{width:100%;height:auto;border-radius:3px;background:#fff}
.pk .t{font:600 12px var(--mono);color:var(--ink)}
.who{display:grid;grid-template-columns:minmax(0,280px) minmax(0,1fr);gap:16px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px}
@media (max-width:760px){.who{grid-template-columns:1fr}}
.who img{width:100%;height:auto;border-radius:4px;background:#fcfaf5}
</style>
</head>
<body>
<header>
  <a href="../index.html" id="wy-index">← Index</a>
  <h1>Character Kits v2<small>EVERY CHARACTER · EVERY POEM · ONE IMAGE + ONE PROMPT PER SHEET</small></h1>
  <span class="sp"></span>
  <a href="kit3.html">Puppet Kit 3 →</a>
  <a href="poems/index.html">Poem pages →</a>
  <a href="arena/parts/kit3/v2/kits.json">kits.json</a>
</header>
<main>
  <section>
    <p style="font-size:17px">The kits to generate the cast of <i>where you go when you leave</i> and the Crash Lab, in the Kit 3 way. Each sheet is <b>one image</b> (A: the layout with the brads already placed, B: who, C: the cardboard style) and <b>one prompt</b>. Pick a poem, pick a character, then generate their action sheet for that poem and the costume kit it wears.</p>
    <div class="cast-note">
      <div><b>POET is a man</b>, the man in the photos. Black t-shirt in 01–03; the red/black outfit and sunglasses from 04 Nevermore on.</div>
      <div><b>EX</b> is a man whose face is never seen. His kit has only back and three-quarter-back sheets.</div>
      <div><b>The woman</b> is the puppet the arena called "the poet". She is renamed so that "poet" means the man; in the poems she plays MOTHER and SHE.</div>
      <div><b>YOUNG POET</b> (6) and the <b>GHOST CHILD</b> (7) are new children; <b>Bola, Shim and Dot</b> are the Crash Lab dummies in cardboard.</div>
    </div>
    <nav class="toc" id="toc"></nav>
  </section>
  <section aria-labelledby="bypoem"><h2 id="bypoem">By poem</h2><div id="poems" style="display:grid;gap:18px"></div></section>
  <section aria-labelledby="bychar"><h2 id="bychar">By character</h2><div id="cast" style="display:grid;gap:18px"></div></section>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const PROMPTS = [];
const reg = t => { PROMPTS.push(t); return PROMPTS.length - 1; };
const castById = Object.fromEntries(D.cast.map(c => [c.id, c]));
const packCard = p => `<div class="pk"><a href="${esc(p.image)}" target="_blank" rel="noopener"><img src="${esc(p.image)}" alt="${esc(p.id)} pack" loading="lazy"></a>
  <span class="t">${esc(p.sheet || p.id)}</span><div class="row"><button class="btn" data-i="${reg(p.prompt)}">Copy prompt</button><a class="btn ghost" href="${esc(p.image)}" download>Image</a><span class="ok" aria-live="polite"></span></div></div>`;
const kitBlock = (c, cos) => {
  const k = c.costumes.find(x => x.costume === cos);
  if (!k) return `<p class="dim">${esc(cos)}: no kit yet (covered by the character's other costume)</p>`;
  return `<details><summary>${esc(c.name)} · ${esc(cos.replace(/_/g, ' '))} kit · ${k.packs.length} sheets</summary><p class="dim">${esc(k.what)}</p><div class="packs">${k.packs.map(packCard).join('')}</div></details>`;
};
document.getElementById('toc').innerHTML = D.poems.map(p => `<a href="#p${esc(p.num)}">${esc(p.num)} ${esc(p.title)}</a>`).join('') + '<a href="#bychar">Cast</a>' + '<a href="#c-bola">Bolas</a>';
document.getElementById('poems').innerHTML = D.poems.map(P => `<article class="poem" id="p${esc(P.num)}">
  <header><span class="n">${esc(P.num)}</span><h3 style="font-size:20px">${esc(P.title)}</h3><span class="dim">${esc(P.style || '')} · ${P.characters.length} characters</span></header>
  ${P.characters.map(ch => { const c = castById[ch.id] || {costumes: []}; return `<div class="char">
    <div><a href="${esc(ch.action.image)}" target="_blank" rel="noopener"><img src="${esc(ch.action.image)}" alt="${esc(ch.name)} action sheet for ${esc(P.title)}" loading="lazy"></a></div>
    <div style="display:grid;gap:8px;align-content:start"><h3>${esc(ch.name)}</h3>
      <div class="chips">${ch.costumes.map(x => `<span class="chip cos">${esc(x.replace(/_/g, ' '))}</span>`).join('')}</div>
      <div class="chips">${ch.poses.slice(0, 6).map(x => `<span class="chip">${esc(x)}</span>`).join('')}${ch.hands.slice(0, 6).map(x => `<span class="chip">hand: ${esc(x)}</span>`).join('')}${ch.props.slice(0, 6).map(x => `<span class="chip">prop: ${esc(x)}</span>`).join('')}</div>
      <pre>${esc(ch.action.prompt)}</pre>
      <div class="row"><button class="btn" data-i="${reg(ch.action.prompt)}">Copy action-sheet prompt</button><a class="btn ghost" href="${esc(ch.action.image)}" download>Image</a><span class="ok" aria-live="polite"></span></div>
      ${ch.costumes.map(cos => kitBlock(c, cos)).join('')}
    </div></div>`; }).join('')}
</article>`).join('');
document.getElementById('cast').innerHTML = D.cast.map(c => `<article class="who" id="c-${esc(c.id)}">
  <div><img src="${esc(c.chart)}" alt="${esc(c.name)} cut chart" loading="lazy"></div>
  <div style="display:grid;gap:10px;align-content:start"><h3 style="font-size:20px">${esc(c.name)} <span class="dim" style="font:12px var(--mono)">${esc(c.height_cm)} cm · build ${esc(c.build)}</span></h3>
  <p class="dim">${esc(c.who)}</p>${c.costumes.map(k => kitBlock(c, k.costume)).join('')}</div></article>`).join('');
document.body.addEventListener('click', e => {
  const b = e.target.closest('button.btn[data-i]'); if (!b) return;
  const txt = PROMPTS[+b.dataset.i], ok = b.parentElement.querySelector('.ok');
  const done = () => { ok.textContent = 'Copied'; setTimeout(() => ok.textContent = '', 1600); };
  const fallback = () => { const pre = b.closest('.char, .pk, details')?.querySelector('pre'); if (pre) { const r = document.createRange(); r.selectNodeContents(pre); const s = getSelection(); s.removeAllRanges(); s.addRange(r); } ok.textContent = 'Press Ctrl+C / Cmd+C'; };
  try { navigator.clipboard.writeText(txt).then(done, fallback); } catch (err) { fallback(); }
});
if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
</script>
<script src="../nav.js" defer></script>
</body>
</html>
'''
out = os.path.join(SHOTS, 'kits.html')
open(out, 'w').write(PAGE.replace('__DATA__', json.dumps(D).replace('</', '<\\/')))
print(out)
