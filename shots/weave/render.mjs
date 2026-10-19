// Render the weave passage from the same page you watch: shots/weave.html?capture=1.
// Every frame is drawn by window.frameJPEG(f), written to disk, then muxed with passage.wav.
// usage: node shots/weave/render.mjs [from] [to]     (frame ranges, so a late fix re-renders only its stretch)
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
import { fileURLToPath } from 'url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(ROOT, 'frames');
fs.mkdirSync(OUT, { recursive: true });
const clip = JSON.parse(fs.readFileSync(path.join(ROOT, 'clips', 'p07_turn_me_up.json')));
const N = clip.clock.frames;
const from = +(process.argv[2] ?? 0), to = +(process.argv[3] ?? N - 1);
const browser = await puppeteer.launch({ headless: 'new', args: ['--disable-gpu', '--window-size=1920,1080'] });
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080 });
page.on('pageerror', e => console.error('pageerror', e.message));
await page.goto('http://127.0.0.1:8800/shots/weave.html?capture=1', { waitUntil: 'networkidle0', timeout: 120000 });
await page.waitForFunction('window.WEAVE_READY === true', { timeout: 120000 });
const t0 = Date.now();
for (let f = from; f <= to; f++) {
  const url = await page.evaluate(n => window.frameJPEG(n, 0.93), f);
  fs.writeFileSync(path.join(OUT, String(f).padStart(4, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
  if (f % 48 === 0) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(1) + 's');
}
await browser.close();
const have = fs.readdirSync(OUT).filter(f => f.endsWith('.jpg')).length;
console.log('frames on disk', have, 'of', N);
if (have >= N) {
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '24', '-i', path.join(OUT, '%04d.jpg'), '-i', path.join(ROOT, 'passage.wav'),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-c:a', 'aac', '-b:a', '192k',
    '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-shortest', '-movflags', '+faststart', path.join(ROOT, 'passage.mp4')], { stdio: 'inherit' });
  console.log('wrote passage.mp4');
}
