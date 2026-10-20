// Contact sheet of chosen frames for one passage, drawn by the same page you watch.
// usage: node shots/weave/sheet.mjs <passage_id> <out.jpg> f1 f2 f3 ...   (add DEBUG=1 for contact marks)
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { execFileSync } from 'child_process';

const [pid, out, ...fs_] = process.argv.slice(2);
const frames = fs_.map(Number);
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'weave-sheet-'));
const browser = await puppeteer.launch({ headless: 'new', args: ['--disable-gpu', '--window-size=1920,1080'] });
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080 });
page.on('pageerror', e => console.error('pageerror', e.message));
page.on('console', m => { if (m.type() === 'error') console.error('console', m.text()); });
await page.goto(`http://127.0.0.1:8800/shots/weave.html?capture=1&p=${pid}${process.env.DEBUG ? '&debug=1' : ''}`, { waitUntil: 'networkidle0', timeout: 120000 });
await page.waitForFunction('window.WEAVE_READY === true', { timeout: 120000 });
const files = [];
for (const f of frames) {
  const url = await page.evaluate(n => window.frameJPEG(n, 0.9), f);
  const p = path.join(tmp, String(f).padStart(4, '0') + '.jpg');
  fs.writeFileSync(p, Buffer.from(url.split(',')[1], 'base64'));
  files.push(p);
}
await browser.close();
const cols = Math.min(3, files.length), rows = Math.ceil(files.length / cols);
const args = ['-v', 'error', '-y'];
files.forEach(f => args.push('-i', f));
const scale = files.map((_, i) => `[${i}:v]scale=640:360,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='f${frames[i]}':x=8:y=8:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.5[v${i}]`).join(';');
const pad = files.length < cols * rows ? `;color=black:s=640x360:d=1[blank]` : '';
const inputs = files.map((_, i) => `[v${i}]`).join('') + (files.length < cols * rows ? '[blank]'.repeat(cols * rows - files.length) : '');
const layout = Array.from({ length: cols * rows }, (_, i) => `${(i % cols) * 640}_${Math.floor(i / cols) * 360}`).join('|');
args.push('-filter_complex', `${scale}${pad};${inputs}xstack=inputs=${cols * rows}:layout=${layout}[o]`, '-map', '[o]', '-frames:v', '1', out);
execFileSync('ffmpeg', args, { stdio: 'inherit' });
if (process.env.KEEP) { for (const f of files) fs.copyFileSync(f, path.join(path.dirname(out), path.basename(out, '.jpg') + '_' + path.basename(f))); }
console.log('wrote', out);
