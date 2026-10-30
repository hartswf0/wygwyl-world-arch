// Headless renderer for the Cut-Out Suite: a staged scene JSON -> mp4 with the reading, contact sheet, measured checks.
// The frames are drawn by the same page you edit (shots/suite/index.html?capture=1), so the film is the staging.
//
// usage: node shots/suite/render.mjs <scene_id ...> | --all   [--port 8800] [--no-video] [--no-checks] [--w 1920]
//   writes shots/suite/renders/<id>.mp4, shots/suite/data/scenes/<id>.sheet.jpg, and the measured checks into
//   shots/suite/data/scenes/<id>.json (the scene pack). Serves the repo root itself if nothing answers on the port.
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import http from 'http';
import { spawn, execFileSync } from 'child_process';
import { fileURLToPath } from 'url';

const SUITE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(SUITE, '../..');
const argv = process.argv.slice(2);
const flag = (k, d) => { const i = argv.indexOf(k); return i < 0 ? d : (argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : true); };
const PORT = +flag('--port', process.env.SUITE_PORT || 8800);
const index = JSON.parse(fs.readFileSync(path.join(SUITE, 'data/scenes/index.json')));
let ids = argv.filter((a, i) => !a.startsWith('--') && !(i > 0 && ['--port', '--w'].includes(argv[i - 1])));
if (argv.includes('--all') || !ids.length) ids = index.scenes.map(s => s.id);

const up = () => new Promise(res => http.get(`http://127.0.0.1:${PORT}/shots/suite/index.html`, r => { r.resume(); res(r.statusCode === 200); }).on('error', () => res(false)));
let server = null;
if (!(await up())) {
  server = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1', '--directory', ROOT], { stdio: 'ignore' });
  for (let i = 0; i < 50 && !(await up()); i++) await new Promise(r => setTimeout(r, 200));
  console.log('serving', ROOT, 'on', PORT);
}

const browser = await puppeteer.launch({ headless: 'new', args: ['--disable-gpu', '--window-size=1920,1080', '--autoplay-policy=no-user-gesture-required'] });
let failed = 0;
for (const id of ids) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  page.on('pageerror', e => { console.error(id, 'pageerror', e.message); failed++; });
  await page.goto(`http://127.0.0.1:${PORT}/shots/suite/index.html?capture=1&scene=${encodeURIComponent(id)}`, { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForFunction('window.SUITE && (window.SUITE.ready || window.SUITE.error)', { timeout: 120000 });
  const err = await page.evaluate(() => window.SUITE.error);
  if (err) { console.error(id, 'failed to open:', err); failed++; await page.close(); continue; }
  const { frames, fps } = await page.evaluate(() => ({ frames: window.SUITE.frames, fps: window.SUITE.fps }));
  const t0 = Date.now();
  // 1. checks, measured on the render
  if (!argv.includes('--no-checks')) {
    const q = await page.evaluate(() => window.SUITE.runChecks().then(r => r.items.map(i => ({ id: i.id, value: i.value, unit: i.unit, pass: i.pass, warnOnly: i.warnOnly, frames: i.frame_ranges }))));
    for (const i of q) console.log(`${id}  ${i.pass ? 'PASS' : i.warnOnly ? 'WARN' : 'FAIL'}  ${i.id.padEnd(15)} ${i.value ?? '—'} ${i.unit}${i.frames ? '  frames ' + i.frames.slice(0, 70) : ''}`);
    const pack = await page.evaluate(() => window.SUITE.sceneJSON());
    fs.writeFileSync(path.join(SUITE, 'data/scenes', id + '.json'), JSON.stringify(pack, null, 1));
    console.log(id, 'checks written into data/scenes/' + id + '.json', ((Date.now() - t0) / 1000).toFixed(1) + 's');
  }
  // 2. contact sheet
  const sheet = await page.evaluate(() => window.SUITE.contactSheet(4, 12));
  fs.writeFileSync(path.join(SUITE, 'data/scenes', id + '.sheet.jpg'), Buffer.from(sheet.split(',')[1], 'base64'));
  // 3. the film
  if (!argv.includes('--no-video')) {
    const dir = path.join(SUITE, 'renders', id + '_frames');
    fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
    for (let f = 0; f < frames; f++) {
      const url = await page.evaluate(n => window.SUITE.frameJPEG(n, 0.92), f);
      fs.writeFileSync(path.join(dir, String(f).padStart(4, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
    }
    const scene = JSON.parse(fs.readFileSync(path.join(SUITE, 'data/scenes', id + '.json')));
    const audio = path.join(SUITE, scene.audio.file.replace(/^suite\//, ''));
    const out = path.join(SUITE, 'renders', id + '.mp4');
    const W = +flag('--w', 1920);
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(fps), '-i', path.join(dir, '%04d.jpg'), '-i', audio,
      '-vf', `scale=${W}:-2`, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'slow',
      '-c:a', 'aac', '-b:a', '160k', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-shortest', '-movflags', '+faststart', out], { stdio: 'inherit' });
    fs.rmSync(dir, { recursive: true, force: true });
    console.log(id, 'wrote', path.relative(ROOT, out), frames, 'frames', ((Date.now() - t0) / 1000).toFixed(1) + 's');
  }
  await page.close();
}
await browser.close();
if (server) server.kill();
process.exit(failed ? 1 : 0);
