// run.mjs OUT_DIR [ids,comma,separated]: re-solves every target through shots/skinlab/resolve.html (serve the repo root on :8811). PICS=1 saves before/after PNGs; FORCE=1 redoes done ids. Needs puppeteer.
import puppeteer from 'puppeteer'; import fs from 'fs';
const out=process.argv[2], ids=process.argv[3]?process.argv[3].split(','):null, pics=!!process.env.PICS;
const b=await puppeteer.launch({headless:'new',args:['--no-sandbox'],executablePath:process.env.CHROME||'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const p=await b.newPage(); p.on('pageerror',e=>console.log('pageerror',e.message));
await p.goto('http://localhost:8811/shots/skinlab/resolve.html',{waitUntil:'networkidle0',timeout:120000});
await p.waitForFunction('window.__ready||window.__error',{timeout:120000});
const err=await p.evaluate(()=>window.__error); if(err){console.log(err);process.exit(1);}
const all=ids||(await p.evaluate(()=>window.__doc.ids)); fs.mkdirSync(out,{recursive:true});
const res=fs.existsSync(out+'/resolve.json')?JSON.parse(fs.readFileSync(out+'/resolve.json')):{};
for(const id of all){ if(res[id]&&!process.env.FORCE) continue;
  const r=await p.evaluate((id,pics)=>window.__resolve(id,{pics}),id,pics);
  for(const k of ['png_before','png_after']) if(r[k]){ fs.writeFileSync(out+'/'+id.replace(/\//g,'__')+'.'+k.slice(4)+'.png', Buffer.from(r[k].split(',')[1],'base64')); delete r[k]; }
  res[id]=r; fs.writeFileSync(out+'/resolve.json',JSON.stringify(res,null,1));
  console.log(id, r.error||'', r.ms, r.evals, r.before&&JSON.stringify([r.before.iou,r.before.marker_err_cm,r.before.obj]), '->', r.after&&JSON.stringify([r.after.iou,r.after.marker_err_cm,r.after.obj, r.after.from])); }
await b.close();
