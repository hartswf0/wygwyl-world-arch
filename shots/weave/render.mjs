// Render a weave passage from the same page you watch: shots/weave.html?capture=1&p=<id>.
// Every frame is drawn by window.frameJPEG(f), written to <dir>/frames, then muxed with <dir>/passage.wav.
// usage: node shots/weave/render.mjs <passage id> [from] [to]   (frame ranges, so a late fix re-renders only its stretch)
//        the passage id and its dir come from shots/weave/passages.json
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
import { fileURLToPath } from 'url';

const WEAVE = path.dirname(fileURLToPath(import.meta.url));
const index = JSON.parse(fs.readFileSync(path.join(WEAVE, 'passages.json')));
const pid = process.argv[2] ?? index.default;
const P = index.passages.find(p => p.id === pid);
if (!P) { console.error('unknown passage', pid, 'known:', index.passages.map(p => p.id).join(', ')); process.exit(1); }
const DIR = path.join(WEAVE, P.dir);
const OUT = path.join(DIR, 'frames');
fs.mkdirSync(OUT, { recursive: true });
const clip = JSON.parse(fs.readFileSync(path.join(WEAVE, P.clip)));
const N = clip.clock.frames;
const from = +(process.argv[3] ?? 0), to = +(process.argv[4] ?? N - 1);
const browser = await puppeteer.launch({ headless: 'new', args: ['--disable-gpu', '--window-size=1920,1080'] });
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080 });
page.on('pageerror', e => console.error('pageerror', e.message));
await page.goto(`http://127.0.0.1:8800/shots/weave.html?capture=1&p=${pid}`, { waitUntil: 'networkidle0', timeout: 120000 });
await page.waitForFunction('window.WEAVE_READY === true', { timeout: 120000 });
const t0 = Date.now();
for (let f = from; f <= to; f++) {
  const url = await page.evaluate(n => window.frameJPEG(n, 0.93), f);
  fs.writeFileSync(path.join(OUT, String(f).padStart(4, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
  if (f % 48 === 0) console.log(pid, 'frame', f, ((Date.now() - t0) / 1000).toFixed(1) + 's');
}
await browser.close();
const have = fs.readdirSync(OUT).filter(f => f.endsWith('.jpg')).length;
console.log('frames on disk', have, 'of', N);
const wav = path.join(DIR, 'passage.wav');
if (have >= N && fs.existsSync(wav)) {
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(clip.clock.fps || 24), '-i', path.join(OUT, '%04d.jpg'), '-i', wav,
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-c:a', 'aac', '-b:a', '192k',
    '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-shortest', '-movflags', '+faststart', path.join(WEAVE, P.mp4)], { stdio: 'inherit' });
  console.log('wrote', P.mp4);
} else if (!fs.existsSync(wav)) {
  console.log('no passage.wav in', P.dir, '- run its build_sound.py first');
}
