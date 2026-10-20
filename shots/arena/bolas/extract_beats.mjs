import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const src = '/Users/gaia/.gemini/antigravity-ide/brain/23f6b400-2ff0-4dfc-afd4-905e9b68e231/scratch/bolas';
const html = fs.readFileSync(path.resolve(src, '04-crash-lab/index.html'), 'utf8');
const hook = 'window.__cineo=CINEO;';
const tmp = path.resolve(src, '04-crash-lab/__export_beats_all.html');
fs.writeFileSync(tmp, html.replace(hook, hook + '\nwindow.__CL={VIGS,bakeV,frameV};'));

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--allow-file-access-from-files', '--disable-gpu', '--no-sandbox']
});
const page = await browser.newPage();
await page.goto('file://' + tmp, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => window.__CL && window.__CL.VIGS.length > 0);
try { fs.unlinkSync(tmp); } catch (e) {}

const allBeats = await page.evaluate(() => {
  const { VIGS, bakeV } = window.__CL;
  const out = {};
  for (let i = 101; i <= 132; i++) {
    const tid = 'T' + i;
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
});

await browser.close();
const counts = Object.keys(allBeats).map(k => `${k}:${allBeats[k].length}`);
console.log('Extracted beats for', Object.keys(allBeats).length, 'vignettes:');
console.log(counts.join(', '));
fs.writeFileSync('/Users/gaia/Downloads/WYGWYL-WORLD-ARCH/shots/arena/bolas/bank/beats.json', JSON.stringify(allBeats, null, 2));
console.log('Saved to shots/arena/bolas/bank/beats.json');
