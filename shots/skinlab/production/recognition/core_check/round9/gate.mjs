// gate.mjs OUT ids: render through Builder A's harness (harvest + props + poses_v2) with the working puppet-core; passes the
// Pose Lab target to renderPose (paintedHeadDeg from its markers) by wrapping PuppetCore.renderPose for the run.
import puppeteer from 'puppeteer'; import fs from 'fs';
const out=process.argv[2], ids=new Set(process.argv[3].split(','));
const b=await puppeteer.launch({headless:'new',args:['--no-sandbox'],executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const p=await b.newPage(); p.on('pageerror',e=>console.log('pageerror',e.message));
await p.goto('http://localhost:8811/shots/skinlab/production/recognition/harness.html',{waitUntil:'networkidle0',timeout:120000});
const res=await p.evaluate(async (useTarget)=>{
  const D=await (await fetch('/shots/rig/poses_v2/poet__red_black_sunglasses.json')).json(); const T=Object.fromEntries(D.targets.map(t=>[t.id,t]));
  if (useTarget) { const rp=PuppetCore.renderPose; PuppetCore.renderPose=(ctx,o)=>{ const id=(o.port?.label||'').replace(/^pose\|/,''); return rp(ctx,{...o,target:T[id]}); }; }
  return await harness.run('poet','poet__red_black_sunglasses',720,{harvest:true,props:true,poses:'poses_v2'});
}, !process.env.NOTARGET);
fs.mkdirSync(out,{recursive:true});
for(const r of res){ if(!ids.has(r.id)) continue; if(r.error){console.log(r.id,r.error);continue;}
  fs.writeFileSync(out+'/'+r.id.replace(/\//g,'__')+'.png',Buffer.from(r.png.split(',')[1],'base64'));
  fs.writeFileSync(out+'/'+r.id.replace(/\//g,'__')+'.json',JSON.stringify({frame:r.frame,warnings:r.warnings,chains:r.chains},null,1)); }
console.log('done', res.length); await b.close();
