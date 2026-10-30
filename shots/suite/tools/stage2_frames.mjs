// Stage 2 helper: grab single frames of a staged scene as JPEGs (for eye checks), optionally with the debug overlay.
//   node shots/suite/tools/stage2_frames.mjs <scene_id> <outdir> <t1,t2,...> [--debug] [--port 8820]
import puppeteer from 'puppeteer';
import fs from 'fs';
const [id, out, ts] = process.argv.slice(2);
const port = process.argv.includes('--port') ? process.argv[process.argv.indexOf('--port') + 1] : 8820;
const dbg = process.argv.includes('--debug') ? '&debug=1' : '';
const b = await puppeteer.launch({ headless: 'new', args: ['--disable-gpu'] });
const p = await b.newPage(); await p.setViewport({ width: 1920, height: 1080 });
await p.goto(`http://127.0.0.1:${port}/shots/suite/index.html?capture=1&scene=${id}${dbg}`, { waitUntil: 'networkidle0', timeout: 120000 });
await p.waitForFunction('window.SUITE && (window.SUITE.ready || window.SUITE.error)', { timeout: 120000 });
for (const t of ts.split(',').map(Number)) {
  const url = await p.evaluate(f => window.SUITE.frameJPEG(f, 0.85), Math.round(t * 24));
  fs.writeFileSync(`${out}/${id}_${t}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
}
await b.close();
