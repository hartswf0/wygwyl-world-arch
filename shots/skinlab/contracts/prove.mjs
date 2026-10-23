// Prove a character contract in the real Skin Lab, unmodified.
// usage: node shots/skinlab/contracts/prove.mjs [character=poet] [--probe] [--no-video]
// It serves the repo root, loads shots/skinlab/index.html with the contract injected into localStorage
// (skinlab.current = {skin, style, stack, K, preset}; skinlab.fix = fix), plays Crash Lab trials through the page's own
// solve(), and writes strips, short mp4s and per-frame invariants into contracts/proof/<character>/.
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import { fileURLToPath } from 'node:url';
const puppeteer = (await import('/tmp/claude-0/shot/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js')).default;

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../..');
const CH = process.argv.slice(2).find(a => !a.startsWith('--')) || 'poet';
const PROBE = process.argv.includes('--probe'), NOVIDEO = process.argv.includes('--no-video');
const C = JSON.parse(fs.readFileSync(path.join(HERE, CH + '.json'), 'utf8'));
const OUT = path.join(HERE, 'proof', CH);
fs.mkdirSync(OUT, { recursive: true });
const TMP = fs.mkdtempSync('/tmp/prove-');
const t0 = Date.now(), log = (...a) => console.log(((Date.now() - t0) / 1000).toFixed(1) + 's', ...a);

const port = await new Promise(r => { const s = net.createServer(); s.listen(0, () => { const p = s.address().port; s.close(() => r(p)); }); });
const srv = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { cwd: ROOT, stdio: 'ignore' });
await new Promise(r => setTimeout(r, 800));
const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'], executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const done = async code => { await browser.close().catch(() => {}); srv.kill(); fs.rmSync(TMP, { recursive: true, force: true }); process.exit(code); };
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: 1 });
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  const url = `http://127.0.0.1:${port}/shots/skinlab/index.html`;
  await page.goto(url + '#T014', { waitUntil: 'networkidle0' });
  const skin = Object.fromEntries(Object.entries(C.limbs).map(([k, l]) => [k, { cards: l.cards, src: l.src, mode: l.mode || 'fit', scale: l.scale ?? 1, rot: l.rot || 0, dx: l.dx || 0, dy: l.dy || 0, mirror: !!l.mirror, swap: !!l.swap }]));
  await page.evaluate((cur, fix) => { localStorage.clear(); localStorage.setItem('skinlab.current', JSON.stringify(cur)); localStorage.setItem('skinlab.fix', JSON.stringify(fix)); },
    { skin, style: C.style, stack: C.stack, K: C.proportions.K || {}, preset: C.proportions.preset }, C.fix);
  await page.reload({ waitUntil: 'networkidle0' });
  await page.waitForFunction(() => typeof S !== 'undefined' && S.data && S.lib.length > 0, { timeout: 30000 });
  // the stage alone, 1600x900; no skeleton overlay; puppet IK; bound at the contract's frame
  await page.addStyleTag({ content: '#cv{position:fixed!important;left:0;top:0;width:1600px!important;height:900px!important;z-index:50}' });
  await page.evaluate((sk) => { S.skel = sk; S.puppet = true; S.follow = true; S.view = 'cam'; S.playing = false; layout(); draw(); }, !!process.env.SKEL);

  // in-page helpers: wait for card images, measure a frame, grab the canvas
  await page.evaluate((C) => {
    window.__C = C;
    // ---- contract fields the lab's index.html does not read yet. They are interpreted here, at run time, without editing
    // the page (Builder B implements the same fields in puppet-core.js):
    //   fix[id].erase   [[x0,y0,x1,y1],...] card-px rectangles made transparent (printed sheet labels: TORSO, THIGH, HEAD)
    //   fix[id].trim    erode the card's alpha by n px (a light cut fringe)
    //   fix[id].sockets {group: [x,y]} where a child of that group hangs on this card, instead of the lab's snapped brad
    //   fix[id].hold    [x,y] where a held prop's handle sits on a grip card
    //   limbs.hand_*.states {open:{view:id}, grip:{view:id}}: grip while the trial's bank props say this hand holds a prop
    window.__prep = async () => {
      for (const [id, f] of Object.entries(C.fix)) { if (!f.erase && !f.trim) continue; const c = S.byId[id]; if (!c) continue;
        const im = img(c); if (!(im.complete && im.naturalWidth)) await new Promise(r => { im.onload = im.onerror = r; });
        const o = document.createElement('canvas'); o.width = c.w; o.height = c.h; const g = o.getContext('2d'); g.drawImage(im, 0, 0, c.w, c.h);
        for (const [x0, y0, x1, y1] of f.erase || []) g.clearRect(x0, y0, x1 - x0, y1 - y0);
        if (f.trim) { const d = g.getImageData(0, 0, c.w, c.h), a = new Uint8Array(c.w * c.h), r = f.trim; for (let i = 0; i < a.length; i++) a[i] = d.data[i * 4 + 3];
          for (let y = 0; y < c.h; y++) for (let x = 0; x < c.w; x++) { let m = a[y * c.w + x]; if (!m) continue;
            for (let dy = -r; dy <= r && m; dy++) for (let dx = -r; dx <= r; dx++) { if (dx * dx + dy * dy > r * r) continue; const X = x + dx, Y = y + dy;
              const v = X < 0 || Y < 0 || X >= c.w || Y >= c.h ? 0 : a[Y * c.w + X]; if (v < m) m = v; if (!m) break; }
            d.data[(y * c.w + x) * 4 + 3] = m; }
          g.putImageData(d, 0, 0); }
        const ni = new Image(); ni.src = o.toDataURL(); await new Promise(r => { ni.onload = r; }); IMG[id] = ni; delete ALPHA[id];
      }
    };
    const sock0 = socket;
    window.socket = function (k, px, port, puppet) { const site = C.fix[px.c.id]?.sockets?.[SEG[k].g]; if (site) return { p: fwd(px, site), how: 'site' }; return sock0(k, px, port, puppet); };
    window.__props = () => { const out = []; for (const [name, p] of Object.entries(S.data.props || {})) { const per = p.per_frame, cur = new Array(per).fill(0), fr = [];
      for (let f = 0; f < S.data.n; f++) { for (let i = 0; i < per; i++) cur[i] += p.f[f * per + i]; fr.push({ pos: [cur[0] / 2, cur[1] / 2, cur[2] / 2], held: cur[6] >= 0 ? p.held[cur[6]] : 'absent' }); }
      out.push({ name, type: p.type, size: p.size, fr }); } return out; };
    window.__TP = [];
    const HOLD = { 'A.R': 'hand_R', 'A.L': 'hand_L' };
    window.__state = (f) => { const held = {}; for (const p of __TP) { const h = HOLD[p.fr[f]?.held]; if (h) held[h] = p; }
      for (const k of ['hand_L', 'hand_R']) { const st = C.limbs[k]?.states; if (st && S.skin[k]) S.skin[k].cards = { ...(held[k] ? st.grip : st.open) }; }
      window.__held = held; };
    // a plain paper prop at the hand's hold point (suitcase: hangs from its handle; handset: across the fist), or at the
    // trial's own prop position when no hand holds it (the phone clamped at the ear)
    window.__drawProp = (g, p, at, x) => { const k = S.ports[0].k; g.save(); g.lineJoin = 'round';
      const paper = (path, fill) => { g.fillStyle = fill; path(); g.fill(); g.lineWidth = 3; g.strokeStyle = '#c9a26b'; path(); g.stroke(); g.lineWidth = 1; g.strokeStyle = '#6b4a2a'; path(); g.stroke(); };
      const brad = (q, r) => { const rg = g.createRadialGradient(q[0] - 1, q[1] - 1, 1, q[0], q[1], r); rg.addColorStop(0, '#fff3c0'); rg.addColorStop(.5, '#d9a640'); rg.addColorStop(1, '#7a5410'); g.fillStyle = rg; g.beginPath(); g.arc(q[0], q[1], r, 0, 7); g.fill(); };
      if (p.type === 'suitcase') { const w = 46 * k, h = 34 * k, top = at[1] + 5 * k;
        const handle = () => { g.beginPath(); g.moveTo(at[0] - 6 * k, top); g.quadraticCurveTo(at[0], at[1] - 4 * k, at[0] + 6 * k, top); }; g.lineCap = 'round'; g.lineWidth = 3.4 * k; g.strokeStyle = '#c9a26b'; handle(); g.stroke(); g.lineWidth = 2.2 * k; g.strokeStyle = '#7a4a28'; handle(); g.stroke();
        paper(() => { g.beginPath(); g.roundRect(at[0] - w / 2, top, w, h, 2 * k); }, '#6a4428');
        g.strokeStyle = '#3d2614'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(at[0] - w / 2 + 3 * k, top + 6 * k); g.lineTo(at[0] + w / 2 - 3 * k, top + 6 * k); g.stroke();
        brad([at[0] - 6 * k, top + 1.5 * k], .9 * k); brad([at[0] + 6 * k, top + 1.5 * k], .9 * k); }
      else if (p.type === 'phone') { const ang = x ? x.ang + Math.PI / 2 : -Math.PI / 2 + .25, L = 21 * k;
        g.translate(at[0], at[1]); g.rotate(ang);
        paper(() => { g.beginPath(); g.roundRect(-L / 2, -1.6 * k, L, 3.2 * k, 1.6 * k); g.moveTo(-L / 2 + 3.4 * k, 0); g.arc(-L / 2 + 3 * k, 0, 3.4 * k, 0, 7); g.moveTo(L / 2 - 2.6 * k, 0); g.arc(L / 2 - 3 * k, 0, 3.4 * k, 0, 7); }, '#1d1916');
        brad([0, 0], .8 * k); }
      g.restore(); };
    const dc0 = drawCard;
    window.drawCard = function (g, x, alpha) { const after = [];
      if (S.data && !S.grid) for (const p of __TP) { const h = p.fr[S.f]?.held;
        if (HOLD[h] === x.k) { const hp = C.fix[x.c.id]?.hold; if (hp) __drawProp(g, p, fwd(x, hp), x); }
        if (/^A\.ear/.test(h || '') && x.k === 'head') after.push([p, h.slice(-1)]); }
      dc0(g, x, alpha);
      for (const [p, side] of after) { const e = C.fix[x.c.id]?.ears?.[side]; __drawProp(g, p, e ? fwd(x, e) : S.ports[0].p(p.fr[S.f].pos), null); } };
    window.__imgs = async () => { const ids = new Set(); for (const sk of Object.values(S.skin)) for (const id of Object.values(sk.cards)) ids.add(id); for (const l of Object.values(C.limbs)) for (const st of Object.values(l.states || {})) for (const id of Object.values(st)) ids.add(id);
      await Promise.all([...ids].map(id => { const im = img(S.byId[id]); return im.complete && im.naturalWidth ? 0 : new Promise(r => { im.onload = im.onerror = r; }); })); };
    const sheet = id => id.split('/')[0];
    const ppcOf = c => C.fix[c.id]?.px_per_cm || c.px_per_cm;
    // a fixed world camera (no follow) to measure how far planted cards slide on the floor
    window.__measure = (f) => {
      __bind(f); const port = S.ports[0], fr = S.data.frames[f]; centre(port, fr);
      const sol = solve(fr, port); if (!sol) return null;
      const out = { f, view: sol.view, cards: {}, sheets: [...new Set(sol.order.map(x => sheet(x.c.id)))], order: sol.order.map(x => x.role) };
      for (const x of sol.order) {
        const g = SEG[x.k].g, trueCm = x.lab / ppcOf(x.c), shownCm = x.lab * x.s / port.k;
        out.cards[x.k] = { id: x.c.id, view: x.view, want: x.want, miss: +x.miss.toFixed(2), gap: +x.gap.toFixed(2), sock: x.sockHow || null,
          sockOff: x.sockP && (x.sockHow === 'brad' || x.sockHow === 'bound' || x.sockHow === 'site') ? +(hyp(x.sockP, sol.pj[ji[SEG[x.k].from]]) / port.k).toFixed(2) : 0,
          facesLeft: x.view === 'side' ? (x.mir !== cardLeft(x.c)) : null,
          stretch: +(shownCm / trueCm).toFixed(3), canon: +(trueCm / (VIT[g] * S.H)).toFixed(3), shownCanon: +(shownCm / (VIT[g] * S.H)).toFixed(3) };
      }
      // the painted armhole of the side torso: the share of the oval not covered by a card drawn after the torso
      const T = sol.X.torso, hole = T && C.fix[T.c.id]?.hole;
      if (T && hole && T.view === 'side') { const [cx, cy, rx, ry] = hole, later = sol.order.slice(sol.order.indexOf(T) + 1); let n = 0, open = 0;
        for (let i = -5; i <= 5; i++) for (let j = -5; j <= 5; j++) { const u = i / 5, v = j / 5; if (u * u + v * v > 1) continue; n++;
          const p = fwd(T, [cx + u * rx, cy + v * ry]);
          if (!later.some(y => { const q = inv(y, p), a = alphaOf(y.c), X = Math.round(q[0]), Y = Math.round(q[1]); return a && X >= 0 && Y >= 0 && X < y.c.w && Y < y.c.h && a[Y * y.c.w + X] > 128; })) open++; }
        out.hole = +(open / n).toFixed(3); }
      // a handset clamped at the ear: drawn at the head card's ear site; how far that is from the trial's own prop position
      for (const p of __TP) { const h = p.fr[f]?.held; if (/^A\.ear/.test(h || '') && sol.X.head) { const e = C.fix[sol.X.head.c.id]?.ears?.[h.slice(-1)];
        out.ear = { card: sol.X.head.c.id, view: sol.X.head.view, earToPropCm: e ? +(hyp(fwd(sol.X.head, e), port.p(p.fr[f].pos)) / port.k).toFixed(1) : null }; } }
      // held props: which hand grips, and how far the grip's hold point is from the trial's prop position
      out.held = {}; for (const [k, p] of Object.entries(__held || {})) { const x = sol.X[k], hp = x && C.fix[x.c.id]?.hold;
        out.held[k] = { prop: p.type, card: x?.c.id, view: x?.view, holdToPropCm: hp ? +(hyp(fwd(x, hp), port.p(p.fr[f].pos)) / port.k).toFixed(1) : null }; }
      // feet on the floor, in world cm: the foot card's toe end, read through the inverse of the stage projection
      const rk = port.k, J = sol.j;
      out.world = {};
      for (const s of ['L', 'R']) { const x = sol.X['foot_' + s]; if (!x) continue; const b = fwd(x, x.B), a = fwd(x, x.A);
        out.world['foot_' + s] = { toe: [(b[0] - port.x - port.w / 2) / rk + 0, (port.y + port.h - 22 - b[1]) / rk], ank: [(a[0] - port.x - port.w / 2) / rk, (port.y + port.h - 22 - a[1]) / rk],
          skelToe: J[ji['toe' + s]].slice(), skelAnk: J[ji['ankle' + s]].slice(), cx: port.cx, cz: port.cz }; }
      return out;
    };
    // sockets: the lab binds every view's sockets at one frame (S.bindF). A back or side card bound on a front-facing frame
    // takes its shoulder/hip sockets mirrored or collapsed, so (contract: bind_per_view) each view is bound at the first
    // frame of the trial whose torso wants that view and faces that way — the lab's own "bind here", pressed once per view.
    // the pose key of a frame: which view the torso wants, and (side view) which way its card is mirrored
    window.__key = (f) => { const port = S.ports[0], fr = S.data.frames[f]; centre(port, fr); const sol = solve(fr, port), t = sol?.X?.torso; return t ? t.want + (t.view === 'side' ? (t.mir ? '<' : '>') : '') : null; };
    window.__bind = (f) => { __state(f); S.bindF = __B.front; if (__B.per) { const k = __key(f); if (k && __B.per[k] != null) S.bindF = __B.per[k]; } };
    window.__goto = (f) => { __bind(f); S.f = f; draw(); };
    window.__setTrialBind = (front, perView) => { window.__B = { front, per: null }; if (!perView) return __B; __B.per = {};
      for (let f = 0; f < S.data.frames.length; f++) { const k = __key(f); if (k && __B.per[k] == null) __B.per[k] = f; }
      const fk = __key(front); if (fk) __B.per[fk] = front;   // the contract frame wins for its own view
      return __B; };
    window.__shot = (q) => cv.toDataURL('image/jpeg', q || 0.82);
    // a strip of tiles cropped around the figure, labelled with frame and the torso's view
    window.__strip = (frames, cols, label) => {
      const tw = 1600 / cols, th = Math.round(tw * 1.55), rows = Math.ceil(frames.length / cols);
      const o = document.createElement('canvas'); o.width = 1600; o.height = rows * th + 34; const g = o.getContext('2d');
      g.fillStyle = '#0d0b0a'; g.fillRect(0, 0, o.width, o.height); g.fillStyle = '#efe6da'; g.font = '600 16px Inter, sans-serif'; g.fillText(label, 10, 22);
      const cw = 900 / 1.55;
      frames.forEach((f, i) => { __goto(f); const sol = S.ports[0].sol;
        const x0 = (i % cols) * tw, y0 = 34 + Math.floor(i / cols) * th;
        g.drawImage(cv, 800 - cw / 2, 0, cw, 900, x0, y0, tw, th);
        const tv = sol?.X?.torso, wrong = sol ? sol.order.filter(x => x.view !== x.want).length : 0;
        g.fillStyle = wrong ? '#ef6a5a' : '#9a8d7e'; g.font = '11px monospace'; g.fillText(`f${f} ${tv ? tv.view : ''}${wrong ? ' !' + wrong : ''}`, x0 + 4, y0 + 13);
        g.strokeStyle = '#2a221c'; g.strokeRect(x0, y0, tw, th); });
      return o.toDataURL('image/webp', 0.8);
    };
  }, C);
  await page.evaluate(async () => { await __imgs(); await __prep(); });
  const save = (file, dataUrl) => fs.writeFileSync(path.join(OUT, file), Buffer.from(dataUrl.split(',')[1], 'base64'));
  // load a trial, bind sockets at the contract frame, set the camera (trial camera, or side/front of the actor)
  const trial = async (id, view) => {
    await page.evaluate(async (id, view, bind, backRule) => {
      await loadTrial(id); S.bindF = bind; S.sock = {};
      S.view = view || 'cam'; const fy = trialFacing();
      S.yaw = view === 'side' ? fy + 90 : view === 'front' ? fy : (S.data.view?.yaw ?? -22); S.yaw = ((S.yaw + 540) % 360) - 180;
      layout(); await __imgs(); window.__TP = __props(); __setTrialBind(bind, backRule); draw();
    }, id, view, C.bind_frame || 0, C.bind_per_view === true);
    await new Promise(r => setTimeout(r, 150));
    return page.evaluate(() => ({ n: S.data.frames.length, K: S.K, rec: S.rec, H: S.H, yaw: S.yaw, preset: S.preset, bind: __B }));
  };

  const TRIALS = [['T014', 'turn'], ['T009', 'suitcase'], ['T025', 'phone'], ['T006', 'sit'], ['T016', 'kneel'], ['T020', 'coin']];
  const inv = { character: CH, contract: CH + '.json', mode: 'puppet IK (rigid cards pinned at brads), cards fit to the retargeted bones', trials: {} };
  for (const [id, name] of TRIALS) {
    const info = await trial(id);
    const per = await page.evaluate(n => { const out = []; for (let f = 0; f < n; f++) out.push(__measure(f)); return out; }, info.n);
    if (process.env.DUMP) fs.writeFileSync(path.join(process.env.DUMP, id + '.json'), JSON.stringify(per));
    // summarise
    const parts = {}, sheetsPerView = {}, wrong = []; let maxMiss = 0, maxMissAt = null;
    for (const m of per) { if (!m) continue;
      (sheetsPerView[m.view] ||= new Set()); m.sheets.forEach(s => sheetsPerView[m.view].add(s));
      const w = Object.entries(m.cards).filter(([, c]) => c.view !== c.want).map(([k, c]) => `${k}:${c.want}->${c.view}`); if (w.length) wrong.push({ f: m.f, w });
      for (const [k, c] of Object.entries(m.cards)) { const p = parts[k] ||= { sockOffMax: 0, stretchMin: 9, stretchMax: 0, canon: c.canon, shownCanonMin: 9, shownCanonMax: 0, missMax: 0, missMean: 0, n: 0, socket: c.sock, ids: new Set() };
        p.stretchMin = Math.min(p.stretchMin, c.stretch); p.stretchMax = Math.max(p.stretchMax, c.stretch); p.shownCanonMin = Math.min(p.shownCanonMin, c.shownCanon); p.shownCanonMax = Math.max(p.shownCanonMax, c.shownCanon);
        p.sockOffMax = Math.max(p.sockOffMax, c.sockOff); p.missMax = Math.max(p.missMax, c.miss); p.missMean += c.miss; p.n++; p.ids.add(c.view + ':' + c.id.split('/').slice(-1)[0]);
        if (c.miss > maxMiss) { maxMiss = c.miss; maxMissAt = { f: m.f, k }; } } }
    for (const p of Object.values(parts)) { p.missMean = +(p.missMean / p.n).toFixed(2); p.ids = [...p.ids]; delete p.n; }
    // facing: in side view every profile card should face the way the torso faces
    const facing = []; for (const m of per) { if (!m || m.view !== 'side') continue; const t = m.cards.torso?.facesLeft; if (t == null) continue;
      const odd = Object.entries(m.cards).filter(([k, c]) => c.facesLeft != null && c.facesLeft !== t).map(([k]) => k); if (odd.length) facing.push({ f: m.f, odd }); }
    // layer order: shoe over calf, near arm over torso, in every frame
    let layerBad = 0; for (const m of per) { if (!m) continue; const r = q => m.order.indexOf(q);
      if (r('near_foot') < r('near_shin') || r('far_foot') < r('far_shin') || r('near_upper_arm') < r('torso') || r('near_forearm') < r('near_upper_arm')) layerBad++; }
    // view swaps: the frames at which the torso card changes view
    const swaps = []; for (let i = 1; i < per.length; i++) if (per[i]?.cards.torso?.view !== per[i - 1]?.cards.torso?.view) swaps.push({ f: i, from: per[i - 1]?.cards.torso?.view, to: per[i]?.cards.torso?.view });
    // planted feet: frames where the skeleton's toe stays put (< 0.3 cm), how far the drawn toe moves (cm, screen plane)
    let slideMax = 0, slideN = 0;
    for (let i = 1; i < per.length; i++) for (const s of ['foot_L', 'foot_R']) { const a = per[i - 1]?.world?.[s], b = per[i]?.world?.[s]; if (!a || !b) continue;
      const sk = Math.hypot(b.skelToe[0] - a.skelToe[0], b.skelToe[1] - a.skelToe[1], b.skelToe[2] - a.skelToe[2]);
      if (sk < 0.3 && b.skelToe[1] < 6) { slideN++; const dx = (b.toe[0] - a.toe[0]), dy = b.toe[1] - a.toe[1];
        // the camera follows the pelvis: add back the follow shift projected on the screen's right axis
        const yawR = info.yaw * Math.PI / 180, shift = (b.cx - a.cx) * Math.cos(yawR) - (b.cz - a.cz) * Math.sin(yawR);
        slideMax = Math.max(slideMax, Math.hypot(dx + shift, dy)); } }
    const holes = per.filter(m => m?.hole != null).map(m => m.hole), med = a => a.length ? +[...a].sort((x, y) => x - y)[Math.floor(a.length / 2)].toFixed(1) : null;
    const grips = per.flatMap(m => Object.entries(m?.held || {}).map(([k, h]) => ({ f: m.f, k, ...h })));
    const ears = per.filter(m => m?.ear).map(m => m.ear);
    const extra = { armhole_exposed_share: holes.length ? { frames: holes.length, max: Math.max(...holes), mean: +(holes.reduce((a, b) => a + b, 0) / holes.length).toFixed(3), frames_over_10pct: holes.filter(h => h > .1).length } : null,
      grip_frames: grips.length, grip_cards: [...new Set(grips.map(g => `${g.k}:${g.view}:${g.card?.split('/').pop()}`))], grip_hold_to_trial_prop_cm_median: med(grips.map(g => g.holdToPropCm).filter(v => v != null)),
      ear_frames: ears.length, ear_site_to_trial_prop_cm_median: med(ears.map(e => e.earToPropCm).filter(v => v != null)) };
    inv.trials[id] = { name, ...extra, frames: info.n, camera_yaw: info.yaw, height_cm: +info.H.toFixed(1), hip_width_cm: +(info.rec.hips * (info.K.hips ?? 1)).toFixed(1), K: info.K, wrong_view_frames: wrong.length, wrong_view_examples: wrong.slice(0, 6),
      layer_order_bad_frames: layerBad, facing_mismatch_frames: facing.length, facing_mismatch_examples: facing.slice(0, 8),
      socket_offset_max_cm: Math.max(0, ...Object.values(parts).map(p => p.sockOffMax)), bind: info.bind, max_miss_cm: +maxMiss.toFixed(2), max_miss_at: maxMissAt, planted_toe_slide_max_cm_per_frame: +slideMax.toFixed(2), planted_frames: slideN,
      sheets_per_view: Object.fromEntries(Object.entries(sheetsPerView).map(([v, s]) => [v, [...s]])), torso_view_swaps: swaps, parts };
    log(id, name, 'frames', info.n, 'facing', facing.length, 'sockOff', inv.trials[id].socket_offset_max_cm, 'wrongView', wrong.length, 'layerBad', layerBad, 'maxMiss', maxMiss.toFixed(1), 'slide', slideMax.toFixed(2));
    // full-size key frames at playback size (1600x900), for the passage trials
    const KEYS = { T009: [0, 20, 40, 100, 160], T025: [0, 40, 80, 120, 200], T014: [0, 40, 80, 120, 140] };
    const want = (process.env.KEYS || '').split(';').filter(Boolean).map(s => s.split(':')).filter(([t]) => t === id).flatMap(([, fs]) => fs.split(',').map(Number));
    for (const f of (want.length ? want : (PROBE ? [] : KEYS[id] || []))) { fs.mkdirSync(path.join(OUT, 'keys'), { recursive: true });
      save(`keys/${id}_f${String(f).padStart(3, '0')}.jpg`, await page.evaluate(f => { __goto(f); return __shot(0.85); }, f)); }
    if (PROBE) continue;
    // strips
    if (id === 'T014') {
      const fr = []; for (let f = 0; f < info.n; f += 5) fr.push(f);
      save('turnaround_T014.webp', await page.evaluate((fr) => __strip(fr, 10, 'T014 turn — trial camera, every 5th frame; label: frame, torso card view (red ! = a card showing the wrong view)'), fr));
      const keys = []; for (const s of swaps) keys.push(Math.max(0, s.f - 2), s.f, Math.min(info.n - 1, s.f + 2));
      if (keys.length) save('turn_swaps_T014.webp', await page.evaluate((fr) => __strip(fr, Math.min(9, fr.length), 'T014: each torso view swap, 2 frames before / at / 2 after'), keys));
      // three fixed cameras on one pose: side, front, back of the same body (the turnaround proper)
      const views = [];
      for (const v of ['side', 'front', 'back']) { await trial('T014', v === 'back' ? 'front' : v);
        if (v === 'back') await page.evaluate((bind) => { S.yaw = ((S.yaw + 180 + 540) % 360) - 180; layout(); __setTrialBind(bind, true); draw(); }, C.bind_frame || 0);
        views.push(await page.evaluate(() => { __goto(0); return __shot(0.9); })); }
      await page.evaluate(async (views) => { const o = document.createElement('canvas'); o.width = 1600; o.height = 900; const g = o.getContext('2d');
        g.fillStyle = '#0d0b0a'; g.fillRect(0, 0, 1600, 900);
        const ims = await Promise.all(views.map(u => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = u; })));
        ims.forEach((im, i) => g.drawImage(im, 800 - 270, 0, 540, 900, i * 533, 0, 533, 888));
        g.fillStyle = '#efe6da'; g.font = '600 18px Inter'; ['side (camera at his side)', 'front (camera in front)', 'back (camera behind)'].forEach((t, i) => g.fillText(t, i * 533 + 12, 26));
        window.__tri = o.toDataURL('image/webp', 0.85); }, views);
      save('turnaround_views.webp', await page.evaluate(() => __tri));
      await trial('T014');
    } else {
      const step = id === 'T009' || id === 'T025' ? 6 : 10, fr = []; for (let f = 0; f < info.n; f += step) fr.push(f);
      save(`${name}_${id}.webp`, await page.evaluate((fr, l) => __strip(fr, 10, l), fr, `${id} ${name} — every ${step}th frame, trial camera, puppet IK`));
    }
    if ((id === 'T009' || id === 'T025' || id === 'T014') && !NOVIDEO) {
      const dir = fs.mkdtempSync(path.join(TMP, id));
      for (let f = 0; f < info.n; f += 1) { const u = await page.evaluate(f => { __goto(f); return __shot(0.8); }, f); fs.writeFileSync(path.join(dir, String(f).padStart(4, '0') + '.jpg'), Buffer.from(u.split(',')[1], 'base64')); }
      execFileSync('/usr/bin/ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '30', '-i', path.join(dir, '%04d.jpg'), '-vf', 'scale=1280:720', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '30', '-preset', 'veryfast', path.join(OUT, `${name}_${id}.mp4`)]);
      log('mp4', id);
    }
  }
  // the contract's per-part canon and a one-line verdict per invariant
  const all = Object.values(inv.trials);
  inv.summary = {
    wrong_view_frames: Object.fromEntries(Object.entries(inv.trials).map(([k, t]) => [k, t.wrong_view_frames])),
    layer_order_bad_frames: all.reduce((a, t) => a + t.layer_order_bad_frames, 0),
    max_miss_cm: Object.fromEntries(Object.entries(inv.trials).map(([k, t]) => [k, t.max_miss_cm])),
    stretch_range: (() => { let lo = 9, hi = 0; for (const t of all) for (const p of Object.values(t.parts)) { lo = Math.min(lo, p.stretchMin); hi = Math.max(hi, p.stretchMax); } return [lo, hi]; })(),
    canon_range: (() => { let lo = 9, hi = 0; for (const t of all) for (const p of Object.values(t.parts)) { lo = Math.min(lo, p.shownCanonMin); hi = Math.max(hi, p.shownCanonMax); } return [lo, hi]; })(),
    stretch_outside_12pct: Object.entries(inv.trials).flatMap(([t, v]) => Object.entries(v.parts).filter(([, p]) => p.stretchMin < .88 || p.stretchMax > 1.12).map(([k, p]) => `${t} ${k} ${p.stretchMin}-${p.stretchMax} (${p.ids.join(', ')})`)),
    canon_outside_075_135: Object.entries(inv.trials).flatMap(([t, v]) => Object.entries(v.parts).filter(([, p]) => p.shownCanonMin < .75 || p.shownCanonMax > 1.35).map(([k]) => `${t} ${k}`)),
    // where a chain ends (wrist, ankle) the rigid cards are solved to reach; the middle joints (elbow, knee) are free to miss
    chain_end_miss_max_cm: Object.fromEntries(Object.entries(inv.trials).map(([t, v]) => [t, Object.fromEntries(['forearm_L', 'forearm_R', 'shin_L', 'shin_R'].filter(k => v.parts[k]).map(k => [k, v.parts[k].missMax]))])),
    facing_mismatch_frames: Object.fromEntries(Object.entries(inv.trials).map(([k, t]) => [k, t.facing_mismatch_frames])),
    planted_toe_slide_max_cm_per_frame: Object.fromEntries(Object.entries(inv.trials).map(([k, t]) => [k, t.planted_toe_slide_max_cm_per_frame])),
    shoulder_hip_socket_drift_max_cm: Object.fromEntries(Object.entries(inv.trials).map(([k, t]) => [k, t.socket_offset_max_cm])),
    sheets: [...new Set(all.flatMap(t => Object.values(t.sheets_per_view).flat()))],
    page_errors: errs,
    seconds: Math.round((Date.now() - t0) / 1000),
  };
  fs.writeFileSync(path.join(OUT, PROBE ? 'probe.json' : 'invariants.json'), JSON.stringify(inv, null, 1));
  log('wrote', path.relative(ROOT, OUT), JSON.stringify(inv.summary));
  await done(0);
} catch (e) { console.error(e); await done(1); }
