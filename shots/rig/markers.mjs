// Headless MoveNet over every pose target: node shots/rig/markers.mjs [http://localhost:8791] [only-substring]
// Needs a static server at the repo root (python3 -m http.server 8791) and puppeteer; set PUPPETEER_DIR to the
// folder that holds node_modules/puppeteer and CHROME to a Chromium binary if they are not on the default paths.
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(process.env.PUPPETEER_DIR || here, 'noop.js'));
const puppeteer = require('puppeteer');
const base = process.argv[2] || 'http://localhost:8791', only = process.argv[3] || '';
const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-webgl'], executablePath: process.env.CHROME || undefined, protocolTimeout: 1800000 });
const p = await b.newPage();
p.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
p.on('pageerror', e => console.error('pageerror:', e.message));
await p.goto(base + '/shots/rig/markers.html', { waitUntil: 'networkidle0', timeout: 120000 });
const t0 = Date.now();
const r = await p.evaluate(o => window.runAll(o), only);
const out = path.join(here, 'poses', 'markers.json');
let prev = {}; if (only && fs.existsSync(out)) prev = JSON.parse(fs.readFileSync(out)).targets || {};
r.targets = Object.assign(prev, r.targets);
fs.writeFileSync(out, JSON.stringify(r));
const c = Object.values(r.targets).map(t => t.mean_conf).filter(v => v != null).sort((a, b) => a - b);
console.log(`${Object.keys(r.targets).length} targets, backend ${r.backend}, ${((Date.now() - t0) / 1000).toFixed(0)} s; mean MoveNet confidence median ${c[c.length >> 1]} (min ${c[0]}, max ${c[c.length - 1]}) -> ${out}`);
await b.close();
