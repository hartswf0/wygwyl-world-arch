// Export the Bolas Crash Lab vignettes as a motion bank: 3D joints, face and hand states, props and camera per frame.
//
//   node shots/arena/bolas/export_bank.mjs <path to a bolas checkout> [T001 T002 ...]
//
// Loads lab/crash-lab/index.html (or the older 04-crash-lab/) headless, bakes each vignette with the page's own bakeV()/frameV() (nothing is
// re-implemented here, so the motion is exactly what the Crash Lab draws), and writes
//   shots/arena/bolas/bank/<T###>.json   one vignette
//   shots/arena/bolas/bank/index.json    titles, categories, lengths, cast
// Units are the Crash Lab's (cm, y up, floor at y = 0). The source is https://github.com/hartswf0/bolas.
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const src = process.argv[2];
if (!src) { console.error('usage: node export_bank.mjs <bolas checkout> [T001 ...]'); process.exit(1); }
const only = new Set(process.argv.slice(3));
const OUT = path.join(HERE, 'bank');
fs.mkdirSync(OUT, { recursive: true });

const JOINTS = ['pelvis', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'heelL', 'heelR', 'ballL', 'ballR', 'toeL', 'toeR',
  'spineMid', 'neckBase', 'chest', 'shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'headBase', 'head', 'headTop', 'nose'];

const browser = await puppeteer.launch({ headless: 'new', args: ['--allow-file-access-from-files', ...(process.getuid && process.getuid() === 0 ? ['--no-sandbox'] : [])],
  executablePath: process.env.CHROME || undefined });
const page = await browser.newPage();
page.on('pageerror', e => console.error('page error:', e.message));
// the page keeps everything inside one IIFE; a temporary copy exposes the three functions we need on window
// the Crash Lab moved from 04-crash-lab/ to lab/crash-lab/; take whichever this checkout has
const LAB = ['lab/crash-lab', '04-crash-lab'].find(d => fs.existsSync(path.resolve(src, d, 'index.html')));
if (!LAB) { console.error('no Crash Lab in', src); process.exit(1); }
const html = fs.readFileSync(path.resolve(src, LAB, 'index.html'), 'utf8');
const hook = 'window.__cineo=CINEO;';
if (!html.includes(hook)) { console.error('hook not found: the Crash Lab page has changed'); process.exit(1); }
const tmp = path.resolve(src, LAB, '__export_bank.html');
fs.writeFileSync(tmp, html.replace(hook, hook + '\nwindow.__CL={VIGS,bakeV,frameV};'));
await page.goto('file://' + tmp, { waitUntil: 'domcontentloaded', timeout: 120000 });
await page.waitForFunction(() => window.__CL && window.__CL.VIGS.length > 0, { timeout: 120000 });
fs.unlinkSync(tmp);
const ids = await page.evaluate(() => window.__CL.VIGS.map(v => v.id));
console.log(ids.length, 'vignettes');
const index = [];
for (const id of ids) {
  if (only.size && !only.has(id)) continue;
  const v = await page.evaluate((id, JOINTS) => {
    const r1 = x => Math.round(x * 10) / 10, r3 = x => Math.round(x * 1000) / 1000;
    const { VIGS, bakeV, frameV } = window.__CL;
    const v = VIGS.find(q => q.id === id); bakeV(v); frameV(v);
    const col = (R, c) => [r3(R[0][c]), r3(R[1][c]), r3(R[2][c])];
    const actors = v.actors.map(a => ({ id: a.id, name: a.name, scale: a.scale || 1 }));
    const frames = v.F.map(R => {
      const A = {};
      for (const a of v.actors) {
        const rec = R.actors[a.id]; if (!rec) continue; const J = rec.J, p = rec.p || {};
        A[a.id] = {
          j: JOINTS.map(k => J[k] ? J[k].map(r1) : null),
          fwd: col(J._Rc, 2), up: col(J._Rc, 1), hfwd: col(J._Rh, 2), pfwd: col(J._R0, 2),
          hand: { L: p.shapeL || '', R: p.shapeR || '', gL: r3(p.gripL ?? 0), gR: r3(p.gripR ?? 0), pL: p.palmL || '', pR: p.palmR || '' },
          face: p.face ? { mouth: p.face.mouth, eyes: p.face.eyes, smile: r3(p.face.smile), open: r3(p.face.open), lid: r3(p.face.lid), brow: r3(p.face.browA), gx: r3(p.face.gx), gy: r3(p.face.gy) } : null,
          effort: r3(p.effort || 0),
        };
      }
      const P = {};
      for (const id in (R.props || {})) { const q = R.props[id]; P[id] = { type: q.type, pos: q.pos ? q.pos.map(r1) : null, rot: q.rot || null, held: q.held || null, size: q.size || null };
        // the prop's state drives how it is drawn: a door's open angle, a clock's hand, a letter opened, a hidden prop
        const st = {}; for (const k in (q.state || {})) { const x = q.state[k]; if (typeof x === 'number') st[k] = r3(x); else if (typeof x === 'boolean' || typeof x === 'string') st[k] = x; }
        if (Object.keys(st).length) P[id].state = st; }
      return { a: A, p: P };
    });
    return { id: v.id, title: v.title, cat: v.cat, after: v.after || '', note: v.note || '', len: v.len, set: v.set, view: v.view, actors, frames };
  }, id, JOINTS);
  v.joints = JOINTS; v.units = 'cm, y up, floor y=0'; v.source = 'hartswf0/bolas 04-crash-lab/index.html, baked by its own bakeV()';
  fs.writeFileSync(path.join(OUT, id + '.json'), JSON.stringify(v));
  index.push({ id: v.id, title: v.title, cat: v.cat, len: v.len, cast: v.actors.map(a => a.name), view: v.view });
  process.stdout.write(id + ' ');
}
if (!only.size) fs.writeFileSync(path.join(OUT, 'index.json'), JSON.stringify({ joints: JOINTS, vignettes: index }, null, 1));
await browser.close();
console.log('\ndone');
