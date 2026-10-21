"""Build scion.html: the Cineosis batch (T133-T182) through SCION, from scion/scion.json.

    python3 shots/arena/puppet/scion_page.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, 'scion', 'scion.json')))

PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Cineosis Takes</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="icon" href="../../../favicon.svg">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Saira+Stencil+One&family=IBM+Plex+Sans+Condensed:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* layout: a workbench of shipping labels; each vignette is one label: the take, its beat chain, its stagings, its gate stamps */
:root {
  --paper: #ebe4d8; --card: #f6f1e8; --ink: #2a2520; --dim: #6f6558; --kraft: #a8743f; --rule: #d3c7b4; --stage: #564f47;
  --pass: #3f7a4a; --fail: #b4432f;
  --f-display: 'Saira Stencil One', 'Arial Narrow', sans-serif;
  --f-body: 'IBM Plex Sans Condensed', 'Arial Narrow', system-ui, sans-serif;
  --f-mono: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper: #1f1c18; --card: #2a2621; --ink: #ece4d6; --dim: #a99c88; --kraft: #d39a5c; --rule: #3d372f; --stage: #3a352f; --pass: #7dbb86; --fail: #ec8a74; color-scheme: dark } }
:root[data-theme="dark"] { --paper: #1f1c18; --card: #2a2621; --ink: #ece4d6; --dim: #a99c88; --kraft: #d39a5c; --rule: #3d372f; --stage: #3a352f; --pass: #7dbb86; --fail: #ec8a74; color-scheme: dark }
body { background: var(--paper); color: var(--ink); font: 15px/1.5 var(--f-body); }
.wrap { max-width: 1400px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 24px 64px; display: grid; gap: 22px; }
header { display: grid; gap: 10px; }
h1 { font: 400 clamp(30px, 5vw, 46px)/1 var(--f-display); letter-spacing: .02em; margin: 0; text-wrap: balance; }
h1 span { color: var(--kraft); }
.lede { max-width: 74ch; color: var(--dim); margin: 0; }
.tally { display: flex; flex-wrap: wrap; gap: 6px 18px; font: 500 12px var(--f-mono); color: var(--dim); }
.tally b { color: var(--ink); font-weight: 500; font-variant-numeric: tabular-nums; }
.controls { display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: center; position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; background: var(--paper); padding-block: 10px; border-bottom: 1px solid var(--rule); }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--paper); }
.group { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.group > span { font: 500 11px var(--f-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--dim); margin-right: 2px; }
button { font: 500 13px var(--f-body); color: var(--ink); background: var(--card); border: 1px solid var(--rule); border-radius: 3px; padding: 4px 10px; cursor: pointer; }
button[aria-pressed="true"] { background: var(--ink); color: var(--paper); border-color: var(--ink); }
button:focus-visible, input:focus-visible, summary:focus-visible { outline: 2px solid var(--kraft); outline-offset: 2px; }
input[type="search"] { font: 14px var(--f-body); color: var(--ink); background: var(--card); border: 1px solid var(--rule); border-radius: 3px; padding: 4px 10px; min-width: 0; width: 15em; max-width: 100%; }
.count { font: 12px var(--f-mono); color: var(--dim); }
main { display: grid; gap: 22px; }
article { background: var(--card); border: 1px solid var(--rule); border-radius: 4px; padding: 14px; display: grid; gap: 12px; min-width: 0; }
.label { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 2px 14px; align-items: baseline; }
.id { font: 400 22px/1 var(--f-display); color: var(--kraft); grid-row: span 3; }
.label h2 { margin: 0; font: 600 18px/1.25 var(--f-body); text-wrap: balance; }
.label p { margin: 0; color: var(--dim); max-width: 90ch; }
.cast { font: 500 12px var(--f-mono); color: var(--dim); }
.cast b { color: var(--ink); font-weight: 500; }
.take { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 14px; align-items: start; }
@media (max-width: 860px) { .take { grid-template-columns: 1fr; } }
video { display: block; width: 100%; height: auto; max-height: 460px; object-fit: contain; border-radius: 3px; background: var(--stage); }
.side { display: grid; gap: 12px; min-width: 0; }
.stamps { display: flex; flex-wrap: wrap; gap: 6px; }
.stamp { font: 500 11px var(--f-mono); letter-spacing: .04em; border: 1.5px solid currentColor; border-radius: 2px; padding: 2px 6px; display: inline-flex; gap: 6px; }
.stamp.ok { color: var(--pass); }
.stamp.no { color: var(--fail); }
.stamp i { font-style: normal; color: var(--dim); }
h3 { margin: 0; font: 500 11px var(--f-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--dim); }
ol.chain { margin: 0; padding: 0; list-style: none; display: grid; gap: 3px; font-size: 14px; }
ol.chain li { display: grid; grid-template-columns: 4.2em minmax(0, 1fr); gap: 8px; }
ol.chain code { font: 500 12px var(--f-mono); color: var(--kraft); font-variant-numeric: tabular-nums; }
ol.chain em { font-style: normal; color: var(--dim); }
table { border-collapse: collapse; font: 12px var(--f-mono); font-variant-numeric: tabular-nums; width: 100%; }
th, td { text-align: right; padding: 2px 6px; border-bottom: 1px solid var(--rule); }
th:first-child, td:first-child { text-align: left; }
th { font-weight: 500; color: var(--dim); }
tr.chosen td { color: var(--ink); font-weight: 500; }
tr.chosen td:first-child::before { content: "▸ "; color: var(--kraft); }
.xs { font: 12px var(--f-mono); color: var(--dim); }
.strip { overflow-x: auto; background: var(--stage); border-radius: 3px; }
.strip img { display: block; height: 220px; width: auto; max-width: none; }
details summary { cursor: pointer; font: 500 12px var(--f-mono); color: var(--dim); }
details img { display: block; margin-top: 8px; border-radius: 3px; }
@media (max-width: 600px) { .strip img { height: 150px; } .id { grid-row: auto; } .label { grid-template-columns: 1fr; } }
a#wy-index { font: 500 12px var(--f-mono); color: var(--dim); text-decoration: none; border: 1px solid var(--rule); border-radius: 999px; padding: 4px 10px; justify-self: start; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <a href="../../../index.html" id="wy-index">← Index</a>
    <h1>Cineosis <span>Takes</span></h1>
    <p class="lede">The next fifty Bolas vignettes, T133 to T182, run through the SCION pipeline on the card rig. Each dummy is always the same person: the poet plays Bola, the man plays Shim, Dot is the little one, and extras alternate. For every vignette the authored beats form a chain, three stagings are scored (faces seen, actors kept apart, the action filling the frame) and the best one is shot. The take is timed on the exposure sheet, with dead holds cut to a second, and five gates are measured on it.</p>
    <div class="tally" id="tally"></div>
  </header>
  <div class="controls">
    <div class="group" id="gate"><span>Show</span></div>
    <input id="q" type="search" placeholder="Search title, situation or beat" aria-label="Search vignettes">
    <span class="count" id="count"></span>
  </div>
  <main id="list"></main>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = Object.values(JSON.parse(document.getElementById('data').textContent));
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const GATES = ['G1 silhouette', 'G2 volume', 'G3 contact', 'G4 arcs', 'G5 vitality'];
const st = { gate: 'all', q: '' };
const tally = document.getElementById('tally');
tally.innerHTML = `<span><b>${D.length}</b> vignettes</span><span><b>${D.filter(r => r.passed === 5).length}</b> pass all five gates</span>` +
  GATES.map(g => `<span>${esc(g)} <b>${D.filter(r => r.gates[g].pass).length}/${D.length}</b></span>`).join('');
const g = document.getElementById('gate');
for (const [v, label] of [['all', 'All'], ['fail', 'Any gate failing'], ...GATES.map(x => [x, x.split(' ')[0] + ' failing'])]) {
  const b = document.createElement('button');
  b.textContent = label; b.dataset.v = v; b.setAttribute('aria-pressed', String(st.gate === v));
  b.onclick = () => { st.gate = v; [...g.querySelectorAll('button')].forEach(x => x.setAttribute('aria-pressed', String(x.dataset.v === v))); render(); };
  g.appendChild(b);
}
document.getElementById('q').oninput = e => { st.q = e.target.value.toLowerCase(); render(); };
function detail(name, x) {
  const k = Object.entries(x).filter(([k]) => k !== 'pass').map(([k, v]) => `${k.replace(/_/g, ' ')} ${v}`).join(', ');
  return k;
}
function render() {
  const rows = D.filter(r => (st.gate === 'all' || (st.gate === 'fail' ? r.passed < 5 : !r.gates[st.gate].pass)) &&
    (!st.q || (r.id + ' ' + r.title + ' ' + r.situation + ' ' + r.chain.map(b => b.beat).join(' ')).toLowerCase().includes(st.q)));
  document.getElementById('count').textContent = rows.length + ' of ' + D.length;
  document.getElementById('list').innerHTML = rows.map(r => {
    const cast = Object.entries(r.cast).map(([n, s]) => `${esc(n)} <b>${esc(s)}</b>`).join(' · ');
    const stamps = GATES.map(k => `<span class="stamp ${r.gates[k].pass ? 'ok' : 'no'}" title="${esc(detail(k, r.gates[k]))}">${esc(k.split(' ')[0])} ${r.gates[k].pass ? 'pass' : 'fail'}<i>${esc(detail(k, r.gates[k]))}</i></span>`).join('');
    const chain = r.chain.map(b => `<li><code>f${b.f}</code><span>${esc(b.beat || '(unlabelled beat)')} <em>· ${esc(b.driver)}</em></span></li>`).join('');
    const stg = r.stagings.map(s => `<tr class="${s.name === r.chosen ? 'chosen' : ''}"><td>${esc(s.name)}</td><td>${s.yaw}°</td><td>${s.face.toFixed(2)}</td><td>${s.overlap.toFixed(2)}</td><td>${s.fill.toFixed(2)}</td><td>${s.score.toFixed(3)}</td></tr>`).join('');
    const x = r.xsheet;
    return `<article id="${esc(r.id)}"><div class="label"><span class="id">${esc(r.id)}</span><h2>${esc(r.title)}</h2>
      <p>${esc(r.situation)}</p><div class="cast">${cast}</div></div>
      <div class="take"><video controls loop muted playsinline preload="none" poster="scion/${esc(r.poster)}" src="scion/${esc(r.video)}" aria-label="${esc(r.id)} take"></video>
      <div class="side"><div class="stamps">${stamps}</div>
        <div><h3>Beat chain</h3><ol class="chain">${chain}</ol></div>
        <div><h3>Stagings</h3><div style="overflow-x:auto"><table><thead><tr><th>camera</th><th>yaw</th><th>face hidden</th><th>overlap</th><th>fill</th><th>score</th></tr></thead><tbody>${stg}</tbody></table></div></div>
        <div class="xs">frames ${r.span[0]}–${r.span[1]} of ${r.span[2]} · ${x.drawings} drawings · ${x.keys} keys · ${x.breakdowns} breakdowns · ${x.ones} on ones · ${x.twos} on twos</div>
        <details><summary>The three stagings on the middle beat</summary><img loading="lazy" src="scion/${esc(r.stage)}" alt="${esc(r.id)}, the three stagings tried"></details>
      </div></div>
      <div class="strip"><img loading="lazy" src="scion/${esc(r.strip)}" alt="${esc(r.id)}, key beats on the chosen staging"></div></article>`;
  }).join('');
}
render();
if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
</script>
<script src="../../../nav.js" defer></script>
</body>
</html>
'''

out = os.path.join(HERE, 'scion.html')
open(out, 'w').write(PAGE.replace('__DATA__', json.dumps(DATA).replace('</', '<\\/')))
print(out)
