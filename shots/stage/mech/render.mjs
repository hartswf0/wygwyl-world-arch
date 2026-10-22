// node render.mjs <clip.json> [<clip.json> ...] [--frames 0,6,12] [--n 8] [--h 260] [--anchors]
// writes frames/<clip basename>.png  (needs: python3 -m http.server 8781 from the repo root)
import puppeteer from '/tmp/claude-0/shot/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js';
import fs from 'fs'; import path from 'path';
const a = process.argv.slice(2), opt = {n: 8, h: 260};
const clips = [];
for (let i = 0; i < a.length; i++) { if (a[i] === '--frames') opt.frames = a[++i]; else if (a[i] === '--n') opt.n = +a[++i]; else if (a[i] === '--h') opt.h = +a[++i];
  else if (a[i] === '--anchors') opt.anchors = 1; else if (a[i] === '--cols') opt.cols = +a[++i]; else if (a[i] === '--out') opt.out = a[++i]; else clips.push(a[i]); }
const here = path.dirname(new URL(import.meta.url).pathname);
const b = await puppeteer.launch({headless: 'new', args: ['--no-sandbox'], executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const p = await b.newPage(); p.on('pageerror', e => console.log('pageerror', e.message)); p.on('console', m => { if (m.type() === 'warning' || m.type() === 'error') console.log(m.text()); });
for (const c of clips) {
  const j = JSON.parse(fs.readFileSync(path.resolve(c)));
  const n = j.frames.length;
  const frames = opt.frames || Array.from({length: opt.n}, (_, i) => Math.round(i * (n - 1) / Math.max(1, opt.n - 1))).join(',');
  const rel = path.relative(here, path.resolve(c));
  const url = `http://127.0.0.1:8781/shots/stage/mech/strip.html?clip=${encodeURIComponent(rel)}&frames=${frames}&h=${opt.h}` + (opt.anchors ? '&anchors' : '') + (opt.cols ? '&cols=' + opt.cols : '');
  await p.goto(url, {waitUntil: 'load', timeout: 60000});
  await p.waitForFunction('window.DONE', {timeout: 60000});
  const d = await p.evaluate('window.DONE');
  if (d.startsWith('ERR')) { console.log(c, d); continue; }
  const out = opt.out || path.join(here, 'frames', path.basename(c).replace(/\.json$/, '.png'));
  fs.writeFileSync(out, Buffer.from(d.split(',')[1], 'base64')); console.log('wrote', out);
}
await b.close();
