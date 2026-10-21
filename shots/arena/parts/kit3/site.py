"""Build shots/kit3.html: Puppet Kit 3 as a page of the site (GitHub Pages), not an artifact.

    python3 shots/arena/parts/kit3/site.py

Every image is a file in the repository, linked relatively, so the page works from the repo
on GitHub Pages, from a local checkout (python3 serve.py) or straight from a branch.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REL = os.path.relpath(HERE, SHOTS).replace(os.sep, '/')          # arena/parts/kit3
PK = json.load(open(os.path.join(HERE, 'packs.json')))
PO = json.load(open(os.path.join(HERE, 'poison.json')))
STYLE = sorted(os.listdir(os.path.join(HERE, 'style')))
for p in PK:
    p['image'] = f'{REL}/{p["image"]}'
for p in PO:
    p['file'] = f'{REL}/{p["file"]}'
DATA = {'packs': PK, 'poison': PO, 'style': [f'{REL}/style/{n}' for n in STYLE]}

PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Puppet Kit 3 · WYGWYL</title>
<link rel="icon" href="../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
/* the site's arena palette: warm dark bench, kraft card, marker titles */
:root{--bg:#0d0b0a;--panel:#16120f;--line:#2a221c;--ink:#efe6da;--dim:#9a8d7e;--card:#c79a62;--ok:#9fe08a;--bad:#ff7b6b;--acc:#e7a35a;
  --man:#ff7b6b;--poet:#5fc9c9;--dot:#e8c15a;--mono:'JetBrains Mono',ui-monospace,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}
header{display:flex;align-items:center;gap:12px;padding:12px max(18px,env(safe-area-inset-right)) 12px max(18px,env(safe-area-inset-left));border-bottom:1px solid var(--line);flex-wrap:wrap;position:sticky;top:0;background:var(--bg);z-index:5}
header h1{font:400 24px 'Permanent Marker',cursive;margin:0}
header h1 small{font:12px var(--mono);color:var(--dim);margin-left:10px;letter-spacing:.08em}
header a{color:var(--dim);font:12px var(--mono);text-decoration:none;border:1px solid var(--line);padding:4px 10px;border-radius:999px}
header a:hover{color:var(--ink);border-color:var(--card)}
header .sp{flex:1}
main{max-width:1320px;margin:0 auto;padding:24px max(18px,env(safe-area-inset-right)) 80px max(18px,env(safe-area-inset-left));display:grid;gap:48px}
h2{font:400 28px 'Permanent Marker',cursive;margin:0;color:var(--card)}
h3{font:600 16px Inter;margin:0}
p{margin:0;max-width:72ch}
.dim{color:var(--dim)}
section{display:grid;gap:16px;min-width:0}
.lede{font-size:17px;max-width:76ch}
.how{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:0;padding:0;list-style:none;counter-reset:s}
.how li{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px;counter-increment:s;display:grid;gap:4px}
.how li::before{content:counter(s);font:400 26px 'Permanent Marker';color:var(--acc)}
.chips{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.chips span{font:600 10px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--dim)}
.chips button{font:12px var(--mono);color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:5px 12px;cursor:pointer}
.chips button[aria-pressed="true"]{border-color:var(--card);background:#21190f;color:var(--card)}
button:focus-visible,a:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.pack{display:grid;gap:12px;background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--c);border-radius:8px;padding:14px}
.pack[data-c="man"]{--c:var(--man)}.pack[data-c="poet"]{--c:var(--poet)}.pack[data-c="dot"]{--c:var(--dot)}
.pack .top{display:flex;gap:10px 16px;align-items:baseline;flex-wrap:wrap}
.pack .id{font:600 13px var(--mono);color:var(--c)}
.pack img{display:block;width:100%;height:auto;border-radius:4px;background:#fff}
.pack pre{white-space:pre-wrap;word-wrap:break-word;font:12.5px/1.55 var(--mono);color:#e6dccd;background:#0f0c0a;border:1px solid var(--line);border-radius:6px;padding:12px;margin:0;max-height:220px;overflow:auto}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.btn{font:600 13px Inter;color:#1a120a;background:var(--card);border:0;border-radius:999px;padding:7px 16px;cursor:pointer;text-decoration:none}
.btn.ghost{background:none;color:var(--card);border:1px solid var(--card)}
.ok{font:12px var(--mono);color:var(--ok)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.poison{background:var(--panel);border:1px solid #4a201b;border-radius:8px;overflow:hidden;display:grid}
.poison img{width:100%;height:auto;display:block}
.poison div{padding:10px 12px;display:grid;gap:4px}
.poison code{font:12px var(--mono);color:var(--bad)}
.clean img{width:100%;height:auto;display:block;border-radius:4px;background:#fff}
.clean figure{margin:0;display:grid;gap:4px}
.clean figcaption{font:12px var(--mono);color:var(--dim)}
.charts{display:grid;gap:14px}
.charts img{width:100%;height:auto;border-radius:6px;background:#fcfaf5}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font:600 10px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}
td code{font:12px var(--mono);color:var(--acc)}
.proofs{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.proofs figure{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px;display:grid;gap:6px}
.proofs img{width:100%;height:auto;border-radius:4px}
.tag{font:600 10px var(--mono);letter-spacing:.12em;text-transform:uppercase}
.t-gen{color:#8fb0e0}.t-code{color:#c39be6}.t-fuse{color:var(--ok)}
</style>
</head>
<body>
<header>
  <a href="../index.html" id="wy-index">← Index</a>
  <h1>Puppet Kit 3<small>ONE IMAGE · ONE PROMPT · EVERY PART A PLUG</small></h1>
  <span class="sp"></span>
  <a href="arena/puppet/scion.html">Cineosis takes →</a>
  <a href="arena/parts/kit3/registry.json">registry.json</a>
</header>
<main>
  <section>
    <p class="lede">The next puppets for the Acting Arena: the man, the poet and Dot, rebuilt as parts that plug in. For every sheet there is <b>one image</b> and <b>one prompt</b>. Give a generator those two and it paints a full sheet of cards whose brads are already in the right place.</p>
    <ol class="how">
      <li><h3>Open the image</h3><p class="dim">Click it for full size and save it. Panel A is the layout, B is the character, C is the style.</p></li>
      <li><h3>Copy the prompt</h3><p class="dim">One paragraph. It tells the model what each panel is for and what never to draw.</p></li>
      <li><h3>Generate</h3><p class="dim">Paste both into the image model. The output is the painted cards on white, laid out like panel A.</p></li>
      <li><h3>Drop it in</h3><p class="dim">Save the result next to its template. Its sockets are in <code>registry.json</code>, so there is nothing to detect.</p></li>
    </ol>
  </section>

  <section aria-labelledby="packs">
    <h2 id="packs">The sheets</h2>
    <div class="chips" id="chips"><span>Character</span></div>
    <div class="grid" id="plist" style="grid-template-columns:1fr"></div>
  </section>

  <section aria-labelledby="poison">
    <h2 id="poison">Poison: keep these out</h2>
    <p class="dim">These sheets taught the old rig the wrong body, and they teach a generator the same. The worst is the shorts card: a pelvis piece the man does not need. It swung out like an apron and stacked four thighs in side view. Every body sheet is also the front drawing relabelled as profile, back or three-quarter. None of them goes into a pack. The packs use only the clean crops below.</p>
    <div class="grid" id="poisonlist"></div>
  </section>

  <section aria-labelledby="clean">
    <h2 id="clean">Clean references</h2>
    <p class="dim">Cropped from the same sheets, keeping only cards that agree with the new build: segmented trouser legs and Chelsea boots, arm cards, hands on eyelet tabs, the head turnaround and the expression heads.</p>
    <div class="grid clean" id="cleanlist"></div>
  </section>

  <section aria-labelledby="cuts">
    <h2 id="cuts">The cuts</h2>
    <p class="dim">One rest skeleton per character draws the cut charts, every template and the socket registry, so they can't disagree about where a joint is. The man has no pelvis card: his trouser thighs end in a rounded seat that tucks under the jacket hem. The poet's skirt is her only hip card.</p>
    <div class="charts">
      <img src="REL/out/man.cutchart.png" alt="Cut chart of the man, front and profile" loading="lazy">
      <img src="REL/out/poet.cutchart.png" alt="Cut chart of the poet, front and profile" loading="lazy">
      <img src="REL/out/dot.cutchart.png" alt="Cut chart of Dot, front and profile" loading="lazy">
    </div>
  </section>

  <section aria-labelledby="plugs">
    <h2 id="plugs">Plug and play</h2>
    <p class="dim">Any part with a slot's sockets fits that slot: <span class="tag t-gen">generated</span> painted cards, <span class="tag t-code">coded</span> drawings driven by the motion bank, or a <span class="tag t-fuse">fusion</span> of both.</p>
    <div class="tablewrap"><table>
      <thead><tr><th>Slot</th><th>Sockets</th><th>Generated</th><th>Coded</th><th>Fusion</th></tr></thead>
      <tbody>
        <tr><td>Head plate</td><td><code>neck</code> <code>crown</code>, anchors <code>eyes</code> <code>brows</code> <code>mouth</code></td><td>blank plate, five views</td><td>Dot's round head</td><td>the poet's plate with a coded eye</td></tr>
        <tr><td>Eyes · brows · mouth</td><td>their anchors</td><td>8 eyes, 6 brows, 12 mouths, front and profile</td><td>gaze, lids, brow angle, mouth from the bank</td><td>painted shapes, coded pupils and lids</td></tr>
        <tr><td>Glasses</td><td><code>eyes</code></td><td>the man's sunglasses, front and profile</td><td>&ndash;</td><td>on or off per beat</td></tr>
        <tr><td>Hand</td><td>eyelet <code>A</code>, knuckles <code>B</code></td><td>12 shapes &times; back and palm</td><td>Bolas glove port</td><td>painted hand around a coded prop</td></tr>
        <tr><td>Foot</td><td><code>ankle</code> <code>toe</code> <code>heel</code></td><td>flat, heel up, toe up, front, back, 3/4</td><td>&ndash;</td><td>&ndash;</td></tr>
        <tr><td>Body cards</td><td><code>A</code>/<code>B</code>; the torso carries shoulders and hips</td><td>front, 3/4, back, profile</td><td>&ndash;</td><td>&ndash;</td></tr>
        <tr><td>Replacement poses</td><td>one hip brad</td><td>sit, kneel, lie, crouch, fall</td><td>&ndash;</td><td>head and hands plug on</td></tr>
      </tbody>
    </table></div>
    <div class="proofs">
      <figure><img src="REL/demo/poet_fusion.jpg" alt="The poet's head: blank plate, open eye, gaze, half lid, glance up, painted closed eye" loading="lazy"><figcaption class="dim"><span class="tag t-fuse">fusion</span> The poet, awake: her painted plate with the closed eye painted out, a coded eye driven by the bank, and her painted closed eye for blinks.</figcaption></figure>
      <figure><img src="REL/demo/dot_coded.jpg" alt="Dot with her coded face" loading="lazy"><figcaption class="dim"><span class="tag t-code">coded</span> Dot's face, drawn the Crash Lab's way from the bank.</figcaption></figure>
      <figure><img src="REL/demo/man_hands.jpg" alt="The man with his drawn hand cards" loading="lazy"><figcaption class="dim"><span class="tag t-gen">generated</span> The man's hands and legs, cut from his clean sheets.</figcaption></figure>
    </div>
  </section>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const NAMES = {all: 'All', man: 'The man', poet: 'The poet', dot: 'Dot'};
const KIND = {body: 'Body cards', heads: 'Head plates', face: 'Face plug-ins', hands: 'Hands', feet: 'Feet', replacements: 'Replacement poses'};
let cur = 'all';
const g = document.getElementById('chips');
for (const k of Object.keys(NAMES)) { const b = document.createElement('button'); b.textContent = NAMES[k]; b.setAttribute('aria-pressed', String(k === cur));
  b.onclick = () => { cur = k; [...g.querySelectorAll('button')].forEach(x => x.setAttribute('aria-pressed', String(x === b))); render(); }; g.appendChild(b); }
function render() {
  document.getElementById('plist').innerHTML = D.packs.map((s, i) => [s, i]).filter(([s]) => cur === 'all' || s.character === cur).map(([s, i]) => {
    const view = s.sheet.split('.').slice(1).join(' ');
    return `<article class="pack" data-c="${esc(s.character)}" id="${esc(s.id.replace(/\./g, '-'))}">
      <div class="top"><span class="id">${esc(s.id)}</span><h3>${esc(NAMES[s.character])} · ${esc(KIND[s.sheet.split('.')[0]] || s.sheet)}${view ? ' · ' + esc(view) : ''}</h3></div>
      <a href="${esc(s.image)}" target="_blank" rel="noopener"><img src="${esc(s.image)}" alt="${esc(s.id)}: layout, character and style in one image" loading="lazy"></a>
      <pre>${esc(s.prompt)}</pre>
      <div class="row"><button class="btn" data-i="${i}">Copy prompt</button><a class="btn ghost" href="${esc(s.image)}" download>Download image</a><a class="btn ghost" href="${esc(s.image)}" target="_blank" rel="noopener">Open full size</a><span class="ok" aria-live="polite"></span></div>
    </article>`; }).join('');
}
document.getElementById('plist').addEventListener('click', e => {
  const b = e.target.closest('button.btn'); if (!b) return;
  const txt = D.packs[+b.dataset.i].prompt, ok = b.parentElement.querySelector('.ok');
  const done = () => { ok.textContent = 'Copied'; setTimeout(() => ok.textContent = '', 1600); };
  const fallback = () => { const pre = b.closest('.pack').querySelector('pre'); const r = document.createRange(); r.selectNodeContents(pre);
    const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); ok.textContent = 'Selected: press Ctrl+C / Cmd+C'; };
  try { navigator.clipboard.writeText(txt).then(done, fallback); } catch (err) { fallback(); }
});
document.getElementById('poisonlist').innerHTML = D.poison.map(p => `<div class="poison"><img src="${esc(p.file)}" alt="${esc(p.sheet)}, struck out" loading="lazy"><div><code>${esc(p.sheet)}</code><span>${esc(p.why)}</span></div></div>`).join('');
document.getElementById('cleanlist').innerHTML = D.style.map(f => `<figure><a href="${esc(f)}" target="_blank" rel="noopener"><img src="${esc(f)}" alt="${esc(f.split('/').pop())}" loading="lazy"></a><figcaption>${esc(f.split('/').pop().replace('.jpg', ''))}</figcaption></figure>`).join('');
render();
if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
</script>
<script src="../nav.js" defer></script>
</body>
</html>
'''

out = os.path.join(SHOTS, 'kit3.html')
open(out, 'w').write(PAGE.replace('REL/', REL + '/').replace('__DATA__', json.dumps(DATA).replace('</', '<\\/')))
print(out)
