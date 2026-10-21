"""Build study.html: the whole arena on one page, from study/study.json.

    python3 shots/arena/puppet/study_page.py

The data is written into the page, so it opens straight from disk, on GitHub
Pages, or as an artifact with the study/*.jpg files beside it.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, 'study', 'study.json')))

PAGE = r'''<title>Acting Arena Study</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Saira+Stencil+One&family=IBM+Plex+Sans+Condensed:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* layout: a long workbench of rows; each challenge is a shipping label (id, title, situation) over its two casts */
:root {
  --paper: #ebe4d8; --card: #f6f1e8; --ink: #2a2520; --dim: #6f6558; --kraft: #a8743f; --rule: #d3c7b4; --stage: #564f47;
  --f-display: 'Saira Stencil One', 'Arial Narrow', sans-serif;
  --f-body: 'IBM Plex Sans Condensed', 'Arial Narrow', system-ui, sans-serif;
  --f-mono: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper: #1f1c18; --card: #2a2621; --ink: #ece4d6; --dim: #a99c88; --kraft: #d39a5c; --rule: #3d372f; --stage: #3a352f; color-scheme: dark } }
:root[data-theme="dark"] { --paper: #1f1c18; --card: #2a2621; --ink: #ece4d6; --dim: #a99c88; --kraft: #d39a5c; --rule: #3d372f; --stage: #3a352f; color-scheme: dark }
body { background: var(--paper); color: var(--ink); font: 15px/1.5 var(--f-body); }
.wrap { max-width: 1400px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 24px 64px; display: grid; gap: 22px; }
header { display: grid; gap: 8px; }
h1 { font: 400 clamp(30px, 5vw, 46px)/1 var(--f-display); letter-spacing: .02em; margin: 0; text-wrap: balance; }
h1 span { color: var(--kraft); }
.lede { max-width: 72ch; color: var(--dim); margin: 0; }
.controls { display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: center; position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; background: var(--paper); padding-block: 10px; border-bottom: 1px solid var(--rule); }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--paper); }
.group { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.group > span { font: 500 11px var(--f-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--dim); margin-right: 2px; }
button { font: 500 13px var(--f-body); color: var(--ink); background: var(--card); border: 1px solid var(--rule); border-radius: 3px; padding: 4px 10px; cursor: pointer; }
button[aria-pressed="true"] { background: var(--ink); color: var(--paper); border-color: var(--ink); }
button:focus-visible, input:focus-visible { outline: 2px solid var(--kraft); outline-offset: 2px; }
input[type="search"] { font: 14px var(--f-body); color: var(--ink); background: var(--card); border: 1px solid var(--rule); border-radius: 3px; padding: 4px 10px; min-width: 0; width: 15em; max-width: 100%; }
.count { font: 12px var(--f-mono); color: var(--dim); }
article { background: var(--card); border: 1px solid var(--rule); border-radius: 4px; padding: 14px; display: grid; gap: 10px; min-width: 0; }
.label { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 2px 14px; align-items: baseline; }
.id { font: 400 22px/1 var(--f-display); color: var(--kraft); grid-row: span 2; }
.label h2 { margin: 0; font: 600 18px/1.25 var(--f-body); text-wrap: balance; }
.label p { margin: 0; color: var(--dim); }
.fam { font: 500 11px var(--f-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--dim); }
.row { display: grid; gap: 4px; min-width: 0; }
.pair { display: grid; grid-template-columns: minmax(0, auto) minmax(0, 1fr); gap: 8px; align-items: start; }
.pair video { display: block; height: 200px; width: auto; max-width: 100%; border-radius: 3px; background: var(--stage); }
@media (max-width: 760px) { .pair { grid-template-columns: 1fr; } .pair video { height: auto; width: 100%; } }
.cast { font: 500 12px var(--f-mono); color: var(--dim); }
.cast b { color: var(--ink); font-weight: 500; }
.strip { overflow-x: auto; background: var(--stage); border-radius: 3px; }
.strip img { display: block; height: 200px; width: auto; max-width: none; }
.beats { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 13px; color: var(--dim); }
.beats code { font: 500 12px var(--f-mono); color: var(--kraft); margin-right: 4px; }
.flag { font: 12px var(--f-mono); color: var(--kraft); }
@media (max-width: 600px) { .strip img { height: 140px; } .id { grid-row: auto; } .label { grid-template-columns: 1fr; } }
</style>
<div class="wrap">
  <header>
    <h1>Acting Arena <span>Study</span></h1>
    <p class="lede">All 32 challenges, each played by the man and by the poet on the same rig. The Bolas Crash Lab motion places and layers every card, and the drawn cards are the look. Each row has the take as a video, timed the cut-out way (poses held on twos, ones only for the fastest moments), beside a strip of the authored acting beats. Two-actor scenes put them together, then swap the cast.</p>
  </header>
  <div class="controls">
    <div class="group" id="fam"><span>Family</span></div>
    <div class="group" id="who"><span>Show</span></div>
    <input id="q" type="search" placeholder="Search title or beat" aria-label="Search challenges">
    <span class="count" id="count"></span>
  </div>
  <main id="list" class="wrap" style="padding:0"></main>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = Object.values(JSON.parse(document.getElementById('data').textContent));
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const st = { fam: 'all', who: 'both', q: '' };
function chips(id, key, opts) {
  const g = document.getElementById(id);
  for (const [v, label] of opts) {
    const b = document.createElement('button');
    b.textContent = label; b.dataset.v = v; b.setAttribute('aria-pressed', String(st[key] === v));
    b.onclick = () => { st[key] = v; [...g.querySelectorAll('button')].forEach(x => x.setAttribute('aria-pressed', String(x.dataset.v === v))); render(); };
    g.appendChild(b);
  }
}
const fams = [...new Set(D.map(r => r.family))].sort();
chips('fam', 'fam', [['all', 'All'], ...fams.map(f => [f, f.replace('_', ' & ')])]);
chips('who', 'who', [['both', 'Both'], ['man', 'Man first'], ['poet', 'Poet first']]);
document.getElementById('q').oninput = e => { st.q = e.target.value.toLowerCase(); render(); };
function render() {
  const L = document.getElementById('list');
  const rows = D.filter(r => (st.fam === 'all' || r.family === st.fam) &&
    (!st.q || (r.title + ' ' + r.situation + ' ' + r.beats.map(b => b[1]).join(' ')).toLowerCase().includes(st.q)));
  document.getElementById('count').textContent = rows.length + ' of ' + D.length;
  L.innerHTML = rows.map(r => {
    const strips = r.rows.filter((x, i) => st.who === 'both' || Object.values(x.cast)[0] === st.who).map(x => {
      const cast = Object.entries(x.cast).map(([n, s]) => `${esc(n)} <b>${esc(s)}</b>`).join(' · ');
      const hid = x.face_covered.filter(v => v > .12).length;
      return `<div class="row"><div class="cast">${cast}${hid ? ` <span class="flag">face covered on ${hid} beat${hid > 1 ? 's' : ''}</span>` : ''}</div>
        <div class="pair">${x.video ? `<video controls loop muted playsinline preload="none" poster="study/${esc(x.poster)}" src="study/${esc(x.video)}" aria-label="${esc(r.id)} take, ${esc(Object.values(x.cast).join(' and '))}"></video>` : ''}
        <div class="strip"><img loading="lazy" src="study/${esc(x.file)}" alt="${esc(r.id)}, ${esc(Object.values(x.cast).join(' and '))}, key beats"></div></div></div>`;
    }).join('');
    return `<article id="${esc(r.id)}"><div class="label"><span class="id">${esc(r.id)}</span><h2>${esc(r.title)}</h2>
      <p><span class="fam">${esc(r.family.replace('_', ' & '))}</span> · ${esc(r.situation)}</p>
      ${r.xsheet ? `<p class="fam">${r.xsheet.frames} frames · ${r.xsheet.drawings} drawings · ${r.xsheet.keys} keys · ${r.xsheet.breakdowns} breakdowns · ${r.xsheet.ones} on ones</p>` : ''}</div>
      ${strips}<div class="beats">${r.beats.map(b => `<span><code>f${b[0]}</code>${esc(b[1] || '—')}</span>`).join('')}</div></article>`;
  }).join('');
}
render();
if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
</script>
'''

out = os.path.join(HERE, 'study.html')
open(out, 'w').write(PAGE.replace('__DATA__', json.dumps(DATA).replace('</', '<\\/')))
print(out)
