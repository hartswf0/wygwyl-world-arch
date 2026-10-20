// Contact sheet of an arena take: node shots/arena/sheet.mjs ACT-001 [take] [n=16] [out.jpg]
// Needs the repo served at :8800 (python3 -m http.server 8800 from the repo root).
import puppeteer from 'puppeteer';
const [id, take = '', n = '16', out = `shots/arena/sheets/${id}${take ? '__' + take : ''}.jpg`] = process.argv.slice(2);
const b = await puppeteer.launch({headless: 'new'});
const p = await b.newPage();
await p.setViewport({width: 2600, height: 2000});
p.on('pageerror', e => console.error('page', e.message));
await p.goto(`http://localhost:8800/shots/arena.html?capture=1&a=${id}${take ? '&take=' + take : ''}&sheet=${n}`, {waitUntil: 'networkidle0'});
await p.waitForFunction('window.SHEET_DONE === true', {timeout: 60000});
const url = await p.evaluate(() => document.querySelector('#c').toDataURL('image/jpeg', 0.85));
const fs = await import('fs');
fs.mkdirSync('shots/arena/sheets', {recursive: true});
fs.writeFileSync(out, Buffer.from(url.split(',')[1], 'base64'));
console.log('wrote', out);
await b.close();
