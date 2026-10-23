// run.mjs: render poses through PuppetCore.renderPose (shots/skinlab/core_check.html) and save PNGs + results.json.
//   python3 -m http.server 8811 (repo root) ; node run.mjs OUT_DIR "id1,id2,..." ; python3 pair.py OUT_PAIRS OUT_DIR
// needs puppeteer (PUPPETEER path via NODE_PATH or a local install) and CHROME (default /opt/pw-browsers/chromium-1194/chrome-linux/chrome)
import puppeteer from 'puppeteer'; import fs from 'fs';
const out=process.argv[2], ids=process.argv[3].split(',');
const b=await puppeteer.launch({headless:'new',args:['--no-sandbox'],executablePath:process.env.CHROME||'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const p=await b.newPage(); await p.setViewport({width:600,height:700});
p.on('pageerror',e=>console.log('pageerror',e.message));
await p.goto('http://localhost:8811/shots/skinlab/core_check.html'+(process.env.HARVEST?'?harvest=1':''),{waitUntil:'networkidle0',timeout:120000});
await p.waitForFunction('window.__ready||window.__error',{timeout:100000});
const err=await p.evaluate(()=>window.__error); if(err){console.log(err);process.exit(1);}
fs.mkdirSync(out,{recursive:true}); const all={};
for(const id of ids){ const [tid,si]=id.split('@'); const r=await p.evaluate((a,b)=>window.__render(a,b),tid,+(si||0)); await new Promise(r=>setTimeout(r,100));
  const el=await p.$('#cv'); const f=out+'/'+tid.split('/').pop()+'.png'; await el.screenshot({path:f}); all[tid]=r; console.log(tid, r.view, r.yaw, (r.warnings||[]).join(' | ').slice(0,300)); }
fs.writeFileSync(out+'/results.json',JSON.stringify(all,null,1)); await b.close();
