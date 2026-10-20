// Run weave.html?selftest=1 for every passage (or the ones named) and print the result.
// usage: node shots/weave/selftest.mjs [id ...]      exit code 1 if any line FAILs
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const WEAVE = path.dirname(fileURLToPath(import.meta.url));
const index = JSON.parse(fs.readFileSync(path.join(WEAVE, 'passages.json')));
const ids = process.argv.length > 2 ? process.argv.slice(2) : index.passages.map(p => p.id);
const browser = await puppeteer.launch({ headless: 'new', args: ['--disable-gpu'] });
let fails = 0;
for (const id of ids) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1000 });
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('response', r => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url()); });
  await page.goto(`http://127.0.0.1:8800/shots/weave.html?p=${id}&selftest=1`, { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForFunction("document.querySelector('#selftest').textContent.includes('DONE')", { timeout: 120000 });
  const txt = await page.$eval('#selftest', e => e.textContent);
  console.log(txt);
  for (const e of errs) console.log('  page:', e);
  fails += (txt.match(/^FAIL/mg) || []).length;
  await page.close();
}
await browser.close();
console.log(fails ? `${fails} FAIL` : 'all PASS');
process.exit(fails ? 1 : 0);
