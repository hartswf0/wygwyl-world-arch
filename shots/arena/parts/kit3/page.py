"""Build kit3.html: the Kit 3 plan, sketches, templates, plug-ins and every generation prompt.

    python3 shots/arena/parts/kit3/page.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'prompts.json')))
PK = json.load(open(os.path.join(HERE, 'packs.json')))
R = json.load(open(os.path.join(HERE, 'registry.json')))
SNIP = json.dumps({'man.body.front.torso': R['man']['body.front']['torso'], 'man.hands.R.point.back': R['man']['hands.R']['point.back'],
                   'poet.face.profile.plate': R['poet']['face.profile']['plate']}, indent=1)
DATA = {'packs': PK}

PAGE = r'''<title>Puppet Kit 3</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Saira+Stencil+One&family=IBM+Plex+Sans+Condensed:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* layout: a cutting-room spec sheet. The butcher's charts lead; then the rules (skeleton first, brads before paint),
   the plug-ins with working proofs, the templates, and every prompt ready to copy */
:root {
  --paper: #efe9de; --card: #f8f4ec; --ink: #26221e; --dim: #6d6356; --rule: #d6cbb8; --kraft: #a5703c;
  --man: #c23a2c; --poet: #186c72; --dot: #b8891c; --gen: #4a6fa5; --code: #7a4fa0; --fuse: #3d8a55;
  --f-display: 'Saira Stencil One', 'Arial Narrow', sans-serif;
  --f-body: 'IBM Plex Sans Condensed', 'Arial Narrow', system-ui, sans-serif;
  --f-mono: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper: #1e1b17; --card: #29251f; --ink: #ede5d7; --dim: #a99c87; --rule: #3e372e; --kraft: #d49b5d;
  --man: #ee7564; --poet: #5cc0c4; --dot: #e3b84a; --gen: #8fb0e0; --code: #c39be6; --fuse: #7fcf96; color-scheme: dark } }
:root[data-theme="dark"] { --paper: #1e1b17; --card: #29251f; --ink: #ede5d7; --dim: #a99c87; --rule: #3e372e; --kraft: #d49b5d;
  --man: #ee7564; --poet: #5cc0c4; --dot: #e3b84a; --gen: #8fb0e0; --code: #c39be6; --fuse: #7fcf96; color-scheme: dark }
body { background: var(--paper); color: var(--ink); font: 16px/1.55 var(--f-body); }
.wrap { max-width: 1240px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 28px 80px; display: grid; gap: 44px; }
h1 { font: 400 clamp(36px, 6.5vw, 64px)/0.95 var(--f-display); margin: 0; letter-spacing: .01em; text-wrap: balance; }
h1 span { color: var(--kraft); }
h2 { font: 400 clamp(24px, 3.4vw, 32px)/1.1 var(--f-display); margin: 0; text-wrap: balance; }
h3 { font: 600 17px/1.3 var(--f-body); margin: 0; }
p { margin: 0; max-width: 68ch; }
.lede { font-size: 18px; max-width: 70ch; }
.dim { color: var(--dim); }
.eyebrow { font: 500 12px var(--f-mono); letter-spacing: .1em; text-transform: uppercase; color: var(--dim); }
section { display: grid; gap: 16px; min-width: 0; }
header { display: grid; gap: 14px; }
.steps { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; counter-reset: s; }
.steps li { background: var(--card); border: 1px solid var(--rule); border-radius: 4px; padding: 14px; display: grid; gap: 6px; counter-increment: s; align-content: start; }
.steps li::before { content: counter(s); font: 400 30px/1 var(--f-display); color: var(--kraft); }
.charts { display: grid; gap: 18px; }
figure { margin: 0; display: grid; gap: 6px; min-width: 0; }
figure img { width: 100%; height: auto; border: 1px solid var(--rule); border-radius: 3px; background: #fcfaf5; }
figcaption { font-size: 14px; color: var(--dim); }
.tag { font: 500 11px var(--f-mono); letter-spacing: .06em; text-transform: uppercase; padding: 2px 7px; border-radius: 2px; border: 1.5px solid currentColor; white-space: nowrap; }
.t-gen { color: var(--gen); } .t-code { color: var(--code); } .t-fuse { color: var(--fuse); }
.tablewrap { overflow-x: auto; border: 1px solid var(--rule); border-radius: 4px; background: var(--card); }
table { border-collapse: collapse; width: 100%; font-size: 14.5px; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { font: 500 12px var(--f-mono); letter-spacing: .06em; text-transform: uppercase; color: var(--dim); }
td code, p code, li code { font: 13px var(--f-mono); color: var(--kraft); }
tr:last-child td { border-bottom: 0; }
.proofs { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
.proof { background: var(--card); border: 1px solid var(--rule); border-radius: 4px; padding: 12px; display: grid; gap: 8px; align-content: start; min-width: 0; }
.proof img { width: 100%; height: auto; border-radius: 2px; }
.proof .head { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; position: sticky; top: env(safe-area-inset-top, 0px); background: var(--paper); padding-block: 10px; z-index: 4; border-bottom: 1px solid var(--rule); }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--paper); }
button { font: 500 14px var(--f-body); color: var(--ink); background: var(--card); border: 1px solid var(--rule); border-radius: 3px; padding: 5px 12px; cursor: pointer; }
button[aria-pressed="true"] { background: var(--ink); color: var(--paper); border-color: var(--ink); }
button:focus-visible, a:focus-visible { outline: 2px solid var(--kraft); outline-offset: 2px; }
.sheets { display: grid; gap: 14px; }
.sheet { background: var(--card); border: 1px solid var(--rule); border-left: 4px solid var(--c, var(--kraft)); border-radius: 4px; padding: 14px; display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 16px; align-items: start; }
.row { display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center; }
.open { font: 500 14px var(--f-body); color: var(--kraft); }
.sheet[data-c="man"] { --c: var(--man); } .sheet[data-c="poet"] { --c: var(--poet); } .sheet[data-c="dot"] { --c: var(--dot); }
@media (max-width: 760px) { .sheet { grid-template-columns: 1fr; } }
.sheet img { width: 100%; height: auto; border: 1px solid var(--rule); border-radius: 2px; background: #fcfaf5; }
.sheet .noimg { font: 13px var(--f-mono); color: var(--dim); border: 1px dashed var(--rule); border-radius: 2px; padding: 24px 12px; text-align: center; }
.sheet .body { display: grid; gap: 8px; min-width: 0; }
.sheet .id { font: 500 14px var(--f-mono); color: var(--c); }
.sheet .job { font-size: 15px; }
details summary { cursor: pointer; font: 500 13px var(--f-mono); color: var(--dim); }
pre { white-space: pre-wrap; word-wrap: break-word; font: 12.5px/1.5 var(--f-mono); background: var(--paper); border: 1px solid var(--rule); border-radius: 3px; padding: 10px; margin: 0; max-height: 260px; overflow: auto; }
.copy { justify-self: start; }
.ok { color: var(--fuse); font: 13px var(--f-mono); }
.grid-t { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; }
.grid-t a { display: grid; gap: 4px; text-decoration: none; color: var(--dim); font: 12px var(--f-mono); }
.grid-t img { width: 100%; height: auto; border: 1px solid var(--rule); border-radius: 2px; background: #fcfaf5; }
ul.plain { margin: 0; padding-left: 20px; display: grid; gap: 6px; max-width: 72ch; }
</style>
<div class="wrap">
  <header>
    <div class="eyebrow">Acting arena · the next version of the puppets</div>
    <h1>Puppet Kit <span>3</span></h1>
    <p class="lede">Every part becomes a plug: a hand, an eye, a mouth, a boot, a whole head. A part can be <span class="tag t-gen">generated</span> (a painted card from an image model), <span class="tag t-code">coded</span> (drawn by the rig from the motion bank) or a <span class="tag t-fuse">fusion</span> of both (a painted plate with coded features riding on it). Anything that fits a slot's sockets can replace anything else in that slot.</p>
    <p class="dim">The old parts were made the other way round: a model painted a card, then we guessed where its brads were, and the guesses were off by up to 30 pixels. Here the skeleton comes first. The cut charts, the templates and the socket registry are all drawn from one rest skeleton per character, so the brads are placed before anything is painted.</p>
  </header>

  <section aria-labelledby="packs">
    <h2 id="packs">One image, one prompt</h2>
    <p class="dim">Thirty sheets, ten per character. For each: open the image and save it, copy the prompt, and give the generator just those two. The image carries everything in three panels: <b>A</b> the layout to paint into (brads already placed), <b>B</b> who the character is, <b>C</b> cut-out style references from our own cardboard sheets.</p>
    <div class="controls" id="pchips"><span class="eyebrow">Character</span></div>
    <div class="sheets" id="plist"></div>
  </section>

  <section aria-labelledby="how">
    <h2 id="how">How a part is made</h2>
    <ol class="steps">
      <li><h3>Skeleton in centimetres</h3><p class="dim">One rest pose per character (the man 186 cm, the poet 172, Dot 105): every joint, every card's width.</p></li>
      <li><h3>Cut chart and templates</h3><p class="dim">The body cut into numbered cards like a butcher's chart. Each sheet is a template at one scale, with every brad already on a cross.</p></li>
      <li><h3>Paint into the template</h3><p class="dim">An image model, or an artist, paints each card inside its ghost, from the prompt and the references. Nothing is detected afterwards.</p></li>
      <li><h3>Plug into the rig</h3><p class="dim">The registry says where each socket is in the sheet. The rig pins A on the joint, scales by centimetres and plugs features onto their anchors.</p></li>
    </ol>
  </section>

  <section aria-labelledby="charts">
    <h2 id="charts">The cuts</h2>
    <p class="dim">One outline per view. A dashed line is a cut, where one card tucks under the next; a brass dot is a brad. The coloured marks are the face plug-ins. The man has no pelvis card: his trouser thighs end in a rounded seat that tucks under the jacket hem, as the critics asked. The poet's skirt is her only hip card.</p>
    <div class="charts">
      <figure><img src="out/man.cutchart.png" alt="Cut chart of the man, front and profile, pieces 1 to 19" loading="lazy"><figcaption>The man: track jacket with the red piping, track trousers, Chelsea boots; the sunglasses are plug-in 19.</figcaption></figure>
      <figure><img src="out/poet.cutchart.png" alt="Cut chart of the poet, front and profile" loading="lazy"><figcaption>The poet: bodice, skirt (3), the afro as its own layer (20) so her head can turn without the hair jumping.</figcaption></figure>
      <figure><img src="out/dot.cutchart.png" alt="Cut chart of Dot, front and profile" loading="lazy"><figcaption>Dot: a crash dummy at 105 cm with a head that is all face.</figcaption></figure>
    </div>
  </section>

  <section aria-labelledby="plugs">
    <h2 id="plugs">Plug and play</h2>
    <p class="dim">Each slot takes any part with its sockets. These rows show what can fill each slot today and what the generation runs add.</p>
    <div class="tablewrap"><table>
      <thead><tr><th>Slot</th><th>Sockets</th><th>Generated</th><th>Coded</th><th>Fusion</th></tr></thead>
      <tbody>
        <tr><td>Head plate</td><td><code>neck</code> <code>crown</code> + <code>eyes</code> <code>brows</code> <code>mouth</code> anchors</td><td>painted blank plate, five views</td><td>Dot's round head</td><td>the poet's plate with a coded eye</td></tr>
        <tr><td>Eyes</td><td>centred on <code>eyes</code></td><td>painted pairs: open, wide, half, closed, squint, happy, sad, side glance</td><td>whites, iris, gaze and lids from the bank</td><td>painted whites, coded pupils that follow gaze</td></tr>
        <tr><td>Brows</td><td>centred on <code>brows</code></td><td>rest, raised, knit, sad, one up, angry</td><td>a stroke turned by the bank's brow angle</td><td>painted brow, turned and lifted by code</td></tr>
        <tr><td>Mouth</td><td>centred on <code>mouth</code></td><td>rest, smile, grin, O, A, E, U, M/B/P, F/V, frown, strain, wavy</td><td>line, O, open, teeth, wavy from the bank</td><td>painted shape chosen by code, opened by the bank's <code>open</code></td></tr>
        <tr><td>Glasses</td><td>on <code>eyes</code></td><td>the man's sunglasses, front and profile</td><td>&ndash;</td><td>on or off per beat</td></tr>
        <tr><td>Hand</td><td>eyelet <code>A</code> on the wrist, <code>B</code> on the knuckles</td><td>12 shapes &times; back and palm, right hand (the left is its mirror)</td><td>Bolas glove port</td><td>painted hand closed around a coded prop grip</td></tr>
        <tr><td>Foot</td><td><code>ankle</code>, <code>toe</code>, <code>heel</code></td><td>flat, heel up, toe up, front, back, 3/4</td><td>&ndash;</td><td>&ndash;</td></tr>
        <tr><td>Body cards</td><td><code>A</code>/<code>B</code> per limb; the torso carries shoulders and hips</td><td>front, 3/4, back and profile sheets</td><td>&ndash;</td><td>&ndash;</td></tr>
        <tr><td>Replacement</td><td>one brad at the hip</td><td>sit, kneel, lie, crouch, fall</td><td>&ndash;</td><td>head and hands plug onto it</td></tr>
      </tbody>
    </table></div>
    <h3>Working now</h3>
    <div class="proofs">
      <div class="proof"><div class="head"><span class="tag t-fuse">fusion</span><h3>The poet, awake</h3></div><img src="demo/poet_fusion.jpg" alt="The poet's head: blank plate, open eye, gaze forward, half lid, glance up, her painted closed eye" loading="lazy"><p class="dim">Her only head had its eyes painted shut, so every critic said she looked asleep. The eye is painted out to make a plate. A coded eye in her style plugs in, with gaze and lids from the bank, and her own painted closed eye stays as the closed state.</p></div>
      <div class="proof"><div class="head"><span class="tag t-fuse">fusion</span><h3>In the rig</h3></div><img src="demo/poet_awake.jpg" alt="Four renders of the poet with open eyes" loading="lazy"><p class="dim">The same head in four takes, mirrored whichever way she faces.</p></div>
      <div class="proof"><div class="head"><span class="tag t-code">coded</span><h3>Dot's face</h3></div><img src="demo/dot_coded.jpg" alt="Dot with her coded crash-dummy face in several takes" loading="lazy"><p class="dim">Dot's head is drawn the way Bolas draws it: eyes, brows and mouth from the bank, crash targets and her bow. In profile the face turns a little toward camera so it still reads.</p></div>
      <div class="proof"><div class="head"><span class="tag t-gen">generated</span><h3>The man's hands and legs</h3></div><img src="demo/man_hands.jpg" alt="The man in several poses with his drawn hand cards" loading="lazy"><p class="dim">The hands are cut from his hand sheets, each on its eyelet tab. The legs come from his segmented leg sheet. These are the generated parts Kit 3 makes properly, from templates instead of found sheets.</p></div>
    </div>
  </section>

  <section aria-labelledby="drive">
    <h2 id="drive">What drives the face</h2>
    <p class="dim">The Crash Lab bank already carries a face on every frame. Each field maps onto a plug-in, so a painted set and a coded set answer to the same data.</p>
    <div class="tablewrap"><table>
      <thead><tr><th>Bank field</th><th>Values</th><th>What it changes</th></tr></thead>
      <tbody>
        <tr><td><code>eyes</code></td><td>o, closed, heart</td><td>which eye card (or coded eye) is on; heart becomes a coded overlay</td></tr>
        <tr><td><code>lid</code></td><td>0 to 1</td><td>coded upper lid over any open eye; past 0.85 the closed card</td></tr>
        <tr><td><code>gx</code>, <code>gy</code></td><td>-1 to 1</td><td>coded pupils move inside the painted whites</td></tr>
        <tr><td><code>brow</code></td><td>-1 to 1</td><td>picks rest / raised / knit / sad, then turns it by the angle</td></tr>
        <tr><td><code>mouth</code></td><td>line, O, teeth, wavy</td><td>picks the mouth family</td></tr>
        <tr><td><code>smile</code>, <code>open</code></td><td>-1 to 1, 0 to 1</td><td>picks within the family (smile, frown, grin) and stretches it open</td></tr>
        <tr><td><code>effort</code></td><td>0 to 1</td><td>teeth with effort is strain, never a grin</td></tr>
        <tr><td>hand <code>shape</code>, <code>palm</code></td><td>relaxed, flat, pinch, fist, grip, point &hellip;; in, out, up, down</td><td>which hand card, back or palm by which way the palm faces, the thumb side from the 3D hand</td></tr>
      </tbody>
    </table></div>
  </section>

  <section aria-labelledby="reg">
    <h2 id="reg">The registry</h2>
    <p class="dim"><code>kit3/registry.json</code> is written by <code>kit3/kit.py</code> from the same skeleton that draws the templates. A card painted into a template keeps these sockets, in sheet pixels. A few entries:</p>
    <pre id="snip"></pre>
    <ul class="plain">
      <li>Generate a sheet, then cut it by its template cells (the cells are in the registry). There is no socket detection step.</li>
      <li>Hands and feet: paint the right one only. The left is its mirror, and the rig mirrors it so the thumb lands on the 3D hand's thumb side.</li>
      <li>Heads: paint blank plates. Eyes, brows and mouth plug in from a painted sheet, from code, or both.</li>
      <li>Replacement cards (sitting, lying, crouching) carry one hip brad. The head and hands plug onto them.</li>
    </ul>
  </section>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const SNIP = __SNIP__;
document.getElementById('snip').textContent = JSON.stringify(SNIP, null, 1);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const NAMES = {all: 'All', man: 'The man', poet: 'The poet', dot: 'Dot'};
const KIND = {body: 'Body cards', heads: 'Head plates', face: 'Face plug-ins', hands: 'Hands', feet: 'Feet', replacements: 'Replacement poses'};
let cur = 'all';
const g = document.getElementById('pchips');
for (const k of Object.keys(NAMES)) { const b = document.createElement('button'); b.textContent = NAMES[k]; b.setAttribute('aria-pressed', String(k === cur));
  b.onclick = () => { cur = k; [...g.querySelectorAll('button')].forEach(x => x.setAttribute('aria-pressed', String(x === b))); plist(); }; g.appendChild(b); }
function plist() { document.getElementById('plist').innerHTML = D.packs.map((s, i) => [s, i]).filter(([s]) => cur === 'all' || s.character === cur).map(([s, i]) =>
  `<article class="sheet" data-c="${esc(s.character)}" id="${esc(s.id.replace(/\./g, '-'))}">
   <a href="${esc(s.image)}" target="_blank" rel="noopener"><img src="${esc(s.image)}" alt="pack image for ${esc(s.id)}: layout, character and style panels" loading="lazy"></a>
   <div class="body"><span class="id">${esc(s.id)}</span><h3>${esc(NAMES[s.character])} · ${esc(KIND[s.sheet.split('.')[0]] || s.sheet)}${s.sheet.includes('.') ? ' · ' + esc(s.sheet.split('.').slice(1).join(' ')) : ''}</h3>
   <pre>${esc(s.prompt)}</pre>
   <div class="row"><button class="copy" data-i="${i}">Copy prompt</button><a class="open" href="${esc(s.image)}" target="_blank" rel="noopener">Open image</a><span class="ok" aria-live="polite"></span></div></div></article>`).join(''); }
document.getElementById('plist').addEventListener('click', e => {
  const b = e.target.closest('button.copy'); if (!b) return;
  const txt = D.packs[+b.dataset.i].prompt, ok = b.parentElement.querySelector('.ok');
  const done = () => { ok.textContent = 'Copied'; setTimeout(() => ok.textContent = '', 1600); };
  const fallback = () => { const pre = b.closest('.body').querySelector('pre');
    const r = document.createRange(); r.selectNodeContents(pre); const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); ok.textContent = 'Selected: copy with your keyboard'; };
  try { navigator.clipboard.writeText(txt).then(done, fallback); } catch (err) { fallback(); }
});
plist();
</script>
'''

out = os.path.join(HERE, 'kit3.html')
open(out, 'w').write(PAGE.replace('__DATA__', json.dumps(DATA).replace('</', '<\\/')).replace('__SNIP__', SNIP.replace('</', '<\\/')))
print(out)
