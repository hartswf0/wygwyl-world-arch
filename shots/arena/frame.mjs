// One frame of an arena take as a JPEG: node shots/arena/frame.mjs ACT-001 120 out.jpg [take] [dbg=1]
import puppeteer from 'puppeteer';
import fs from 'fs';
const [id, f, out, take = '', dbg = '1'] = process.argv.slice(2);
const b = await puppeteer.launch({headless: 'new'});
const p = await b.newPage();
await p.setViewport({width: 1920, height: 1080});
await p.goto(`http://localhost:8800/shots/arena.html?capture=1&a=${id}&f=${f}&dbg=${dbg}${take ? '&take=' + take : ''}`, {waitUntil: 'networkidle0'});
await p.waitForFunction('window.ARENA_READY === true');
const url = await p.evaluate(() => document.querySelector('#c').toDataURL('image/jpeg', 0.9));
fs.writeFileSync(out, Buffer.from(url.split(',')[1], 'base64'));
await b.close();
