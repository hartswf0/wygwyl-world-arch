// Render the booth passage: every frame of shots/skinlab/passage.html at 1600x900, muxed with the audio window.
//
//   node shots/skinlab/production/09-booth/render.mjs 3            # -> passage_v3.mp4, passage_v3_strip.jpg, v3_key_*.jpg, measures_v3.json
//   node shots/skinlab/production/09-booth/render.mjs --provisional  # -> shots/skinlab/contracts/poet.provisional.json (auto-dress)
//
// Serves the repo root with python3 -m http.server on a free port; puppeteer from /tmp/claude-0/shot/node_modules (or PUPPETEER
// env path), Chromium at /opt/pw-browsers/chromium-1194/chrome-linux/chrome, ffmpeg at /usr/bin/ffmpeg.
import { spawn, execFileSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import net from 'net';
import { fileURLToPath } from 'url';
const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.resolve(HERE, '../../../..');
const { default: puppeteer } = await import(process.env.PUPPETEER || '/tmp/claude-0/shot/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js');
const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', FFMPEG = '/usr/bin/ffmpeg';
const arg = process.argv[2] || '1', provisional = arg === '--provisional', V = provisional ? null : arg.replace(/^v/, '');
const port = await new Promise(r => { const s = net.createServer(); s.listen(0, () => { const p = s.address().port; s.close(() => r(p)); }); });
const srv = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { cwd: ROOT, stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
for (let i = 0; i < 50; i++) { try { await fetch(`http://127.0.0.1:${port}/`); break; } catch { await sleep(100); } }
const browser = await puppeteer.launch({ headless: 'new', executablePath: CHROME, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
const done = async code => { await browser.close(); srv.kill(); process.exit(code); };
try {
  const page = await browser.newPage(); await page.setViewport({ width: 1600, height: 900 });
  page.on('pageerror', e => console.error('pageerror', e.message));
  const q = provisional ? '?render=1&dress=poet' : '?render=1' + (process.env.PASSAGE ? '&p=' + process.env.PASSAGE : '');
  await page.goto(`http://127.0.0.1:${port}/shots/skinlab/passage.html${q}`, { waitUntil: 'networkidle0', timeout: 180000 });
  await page.waitForFunction('window.__ready || window.__error', { timeout: 180000 });
  const err = await page.evaluate(() => window.__error); if (err) { console.error(err); await done(1); }
  if (provisional) {
    const c = await page.evaluate(() => window.__contract);
    fs.writeFileSync(path.join(ROOT, 'shots/skinlab/contracts/poet.provisional.json'), JSON.stringify(c, null, 1));
    console.log('wrote contracts/poet.provisional.json'); await done(0);
  }
  const N = await page.evaluate(() => window.__N), edl = await page.evaluate(() => window.__E.edl);
  const tmp = fs.mkdtempSync('/tmp/booth-frames-');
  const t0 = Date.now();
  for (let f = 0; f < N; f++) {
    const data = await page.evaluate(f => { window.__render(f); return document.getElementById('cv').toDataURL('image/png'); }, f);
    fs.writeFileSync(path.join(tmp, `f${String(f).padStart(4, '0')}.png`), Buffer.from(data.split(',')[1], 'base64'));
    if (f % 40 === 0) console.log('frame', f, '/', N, ((Date.now() - t0) / 1000).toFixed(0) + ' s');
  }
  const measures = await page.evaluate(() => window.__measure());
  measures.rendered = { frames: N, fps: edl.fps, size: [1600, 900], audio: edl.audio, window: [edl.t0, edl.t1], at: new Date().toISOString() };
  fs.writeFileSync(path.join(HERE, `measures_v${V}.json`), JSON.stringify(measures, null, 1));
  // the film: frames + the audio window, H.264, small
  const mp4 = path.join(HERE, `passage_v${V}.mp4`), audio = path.resolve(ROOT, 'shots/skinlab', edl.audio);
  execFileSync(FFMPEG, ['-y', '-loglevel', 'error', '-framerate', String(edl.fps), '-i', path.join(tmp, 'f%04d.png'), '-ss', String(edl.t0), '-t', String(edl.t1 - edl.t0), '-i', audio,
    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '28', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', mp4]);
  // contact strip: every 6th frame, 8 across, 320x180 each, with the frame number and poem time
  const every = 6, cols = 8, picks = []; for (let f = 0; f < N; f += every) picks.push(f);
  const list = path.join(tmp, 'strip.txt');
  fs.writeFileSync(list, picks.map(f => `file '${path.join(tmp, `f${String(f).padStart(4, '0')}.png`)}'`).join('\n'));
  const rows = Math.ceil(picks.length / cols);
  execFileSync(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-vf',
    `scale=320:180,drawtext=text='%{eif\\:n*${every}\\:d}':x=6:y=6:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.5,tile=${cols}x${rows}:padding=2`,
    '-frames:v', '1', '-q:v', '4', path.join(HERE, `passage_v${V}_strip.jpg`)]);
  // key frames, full size
  const keys = { setdown: edl.keys.setdown, turn: edl.keys.turn, lift: edl.keys.lift, hold: edl.keys.hold };
  for (const [k, t] of Object.entries(keys)) {
    const f = Math.min(N - 1, Math.max(0, Math.round((t - edl.t0) * edl.fps)));
    execFileSync(FFMPEG, ['-y', '-loglevel', 'error', '-i', path.join(tmp, `f${String(f).padStart(4, '0')}.png`), '-q:v', '3', path.join(HERE, `v${V}_key_${k}_f${f}.jpg`)]);
  }
  if (process.env.KEEP_FRAMES) { fs.rmSync(process.env.KEEP_FRAMES, { recursive: true, force: true }); fs.renameSync(tmp, process.env.KEEP_FRAMES); } else fs.rmSync(tmp, { recursive: true, force: true });   // KEEP_FRAMES=dir keeps the PNGs (for the image check)
  const sz = fs.statSync(mp4).size;
  console.log(`passage_v${V}.mp4 ${(sz / 1e6).toFixed(2)} MB · ${N} frames · foot slide max ${measures.foot_slide_cm_per_frame.max.toFixed(2)} cm/f · lift sync ${measures.handset_at_ear.sync_offset_frames} frames`);
  await done(0);
} catch (e) { console.error(e); await done(1); }
