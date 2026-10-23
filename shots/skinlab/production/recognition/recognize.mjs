// Recognition harness: pose a character's puppet (its contract) into every painted pose the Pose Lab solved, in the
// painting's own view and height, and lay puppet and painting side by side (plus a blind set) for a critic.
//
//   node shots/skinlab/production/recognition/recognize.mjs                      # every character in CHARACTERS below
//   node shots/skinlab/production/recognition/recognize.mjs poet                 # one character
//
// Character-agnostic: a contract (shots/skinlab/contracts/<character>.json) and Pose Lab target files
// (shots/rig/poses/<character>__<costume>.json) in; renders + per-pose reports out, then compose.py builds
// pairs/, blind/ (hidden key.json), paintings_contact.jpg, summary.json and ../index.html.
//
// The mechanics are NOT here. Rendering goes through shots/skinlab/puppet-core.js: PuppetCore.renderPose(ctx, {...})
// when it exists (Builder B's general API), otherwise a thin stub over the same file's solve()/drawCard() (the Skin
// Lab's puppet IK on rigid cards). This file only converts the Pose Lab solve into joints (pose-core.js fk) and a port
// that projects exactly as the Pose Lab does, so the puppet lands on the painting's own floor, centre and scale.
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import { fileURLToPath } from 'node:url';
const puppeteer = (await import('/tmp/claude-0/shot/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js')).default;

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../../..');
const CHARACTERS = {   // character -> Pose Lab target files (all costumes the Pose Lab solved)
  poet: ['poet__red_black_sunglasses', 'poet__black_tshirt'],
  angel: ['angel__robe'], dj_cyber: ['dj_cyber__cyber'], party_guest: ['party_guest__guest'],
  poet_soul: ['poet_soul__soul'], young_poet: ['young_poet__child_clothes'],
};
const only = process.argv.slice(2).filter(a => !a.startsWith('--'));
const todo = only.length ? only : Object.keys(CHARACTERS);
const U = 720;   // panel height in px: every puppet is rendered at the painting's own px/cm, scaled so the painting is U tall

const port = await new Promise(r => { const s = net.createServer(); s.listen(0, () => { const p = s.address().port; s.close(() => r(p)); }); });
const srv = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { cwd: ROOT, stdio: 'ignore' });
await new Promise(r => setTimeout(r, 800));
const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'], executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const blocked = {};
try {
  const page = await browser.newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(`http://127.0.0.1:${port}/shots/skinlab/production/recognition/harness.html`, { waitUntil: 'networkidle0' });
  for (const ch of todo) {
    const cpath = path.join(ROOT, 'shots/skinlab/contracts', ch + '.json');
    const out = path.join(HERE, ch), rdir = path.join(out, 'renders');
    if (!fs.existsSync(cpath)) { blocked[ch] = `no character contract (shots/skinlab/contracts/${ch}.json); its ${CHARACTERS[ch].join(', ')} targets cannot be posed`; console.log(ch, 'BLOCKED', blocked[ch]); continue; }
    fs.rmSync(rdir, { recursive: true, force: true }); fs.mkdirSync(rdir, { recursive: true });
    const reports = [];
    for (const file of CHARACTERS[ch]) {
      const res = await page.evaluate(async (ch, file, U) => harness.run(ch, file, U), ch, file, U);
      for (const r of res) {
        if (r.png) { fs.writeFileSync(path.join(rdir, r.safe + '.png'), Buffer.from(r.png.split(',')[1], 'base64')); delete r.png; }
        reports.push(r);
      }
      console.log(ch, file, res.length, 'poses', res.filter(r => r.error).length, 'unrendered');
    }
    fs.writeFileSync(path.join(rdir, 'reports.json'), JSON.stringify({ character: ch, api: await page.evaluate(() => harness.api()), reports }, null, 1));
    execFileSync('python3', [path.join(HERE, 'compose.py'), ch], { stdio: 'inherit' });
  }
  fs.writeFileSync(path.join(HERE, 'blocked.json'), JSON.stringify(blocked, null, 1));
  execFileSync('python3', [path.join(HERE, 'compose.py'), '--index'], { stdio: 'inherit' });
  if (errs.length) console.log('page errors:', errs.slice(0, 5));
} finally { await browser.close(); srv.kill(); }
