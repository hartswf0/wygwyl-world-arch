import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

// node shots/arena/bolas/extract_beats.mjs <bolas checkout> [first] [last]   (default T001..T191)
import { fileURLToPath } from 'url';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const src = process.argv[2];
if (!src) { console.error('usage: node extract_beats.mjs <bolas checkout> [first] [last]'); process.exit(1); }
const first = +(process.argv[3] || 1), last = +(process.argv[4] || 191);
const LAB = ['lab/crash-lab', '04-crash-lab'].find(d => fs.existsSync(path.resolve(src, d, 'index.html')));
const html = fs.readFileSync(path.resolve(src, LAB, 'index.html'), 'utf8');
const hook = 'window.__cineo=CINEO;';
const tmp = path.resolve(src, LAB, '__export_beats_all.html');
fs.writeFileSync(tmp, html.replace(hook, hook + '\nwindow.__CL={VIGS,bakeV,frameV};'));

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--allow-file-access-from-files', '--disable-gpu', '--no-sandbox'],
  executablePath: process.env.CHROME || undefined
});
const page = await browser.newPage();
await page.goto('file://' + tmp, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => window.__CL && window.__CL.VIGS.length > 0);
try { fs.unlinkSync(tmp); } catch (e) {}

const allBeats = await page.evaluate((first, last) => {
  const { VIGS, bakeV } = window.__CL;
  const out = {};
  for (let i = first; i <= last; i++) {
    const tid = 'T' + String(i).padStart(3, '0');
    const v = VIGS.find(q => q.id === tid);
    if (!v) continue;
    bakeV(v);
    const beats = [];
    for (const a of v.actors) {
      for (const k of (a.keys || [])) {
        if (k.note) {
          beats.push({ f: k.f, who: a.name, beat: k.note });
        }
      }
    }
    beats.sort((a, b) => a.f - b.f);
    out[tid] = beats;
  }
  return out;
}, first, last);

await browser.close();
const counts = Object.keys(allBeats).map(k => `${k}:${allBeats[k].length}`);
console.log('Extracted beats for', Object.keys(allBeats).length, 'vignettes:');
console.log(counts.join(', '));
const OUT = path.join(HERE, 'bank', 'beats.json');
const old = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : {};
fs.writeFileSync(OUT, JSON.stringify(Object.assign(old, allBeats), null, 2));
console.log('Saved to shots/arena/bolas/bank/beats.json');
