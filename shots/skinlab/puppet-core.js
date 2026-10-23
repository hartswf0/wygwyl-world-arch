/* puppet-core.js — the Skin Lab's puppet machinery, factored out of shots/skinlab/index.html so a player can use it.

   A plain script (no modules, no DOM beyond a canvas context): it defines one global, PuppetCore.
   It is a copy: index.html keeps its own code; keep the two in step by hand when either changes.

     const P = PuppetCore;
     P.S.lib = await (await fetch('library.json')).json(); P.index();      // cards, by id
     P.S.data = P.decode(bankJson);  P.S.actor = 'A';  P.measureActor();   // a trial (or any frames {a:{A:{j,fwd,hfwd,pfwd}}})
     P.S.skin = {...}; P.S.style = 'hips'; P.S.stack = {...}; P.S.K = {...}; // a character contract (contracts/*.json)
     const port = P.makePort(x, y, w, h, yaw, elev, 'label');               // or any object with p(q) → [x, y, depth], k, toward, right
     const sol = P.solve(frame, port);  for (const x of sol.order) P.drawCard(ctx, x, 1);

   What is here: the 26-joint Bolas skeleton and its retarget (joints, retarget, measure, the Vitruvian canon); segments and
   rig styles (SEG, STYLES); which view's card shows (active); placing a card (mk, fwd, inv, scaleOf); where a child
   hangs on its parent (socket); two-card IK (ik2); the per-view layer stack by near/far role (roleOf, STACK0); the
   whole-figure solve; drawCard; the compact bank decoder (decode, decodeProps); auto-dress and kitbash; cards built by code.

   Hooks a host may set on S (all optional):
     S.bindFrame(k, parentPlaced, port) → the frame to bind a socket at (default S.data.frames[S.bindF])
     S.centre(port, frame)              → set port.cx / port.cz before binding (default: follow the pelvis)
     PuppetCore.canvas(w, h)            → an offscreen canvas for cards built by code (default document.createElement)
     PuppetCore.loadImage(src)          → an image-like object (default new Image())
*/
(function (root) {
'use strict';
const P = {};
// ---------- the Bolas skeleton (26 joints, cm, y up, floor y=0) plus four points of our own ----------
const J = 'pelvis hipL hipR kneeL kneeR ankleL ankleR heelL heelR ballL ballR toeL toeR spineMid neckBase chest shoulderL shoulderR elbowL elbowR wristL wristR headBase head headTop nose'.split(' ');
const ji = Object.fromEntries(J.map((n, i) => [n, i]));
Object.assign(ji, { tipL: 26, tipR: 27, waist: 28, crotch: 29 });
const HAND_CM = 18.5;

const S = { lib: [], byId: {}, data: null, actor: 'A', skin: {}, style: 'hips', puppet: true, bindF: 0, sock: {}, fix: {}, follow: true,
  K: {}, preset: 'bolas', pv: 0, rec: null, H: 180, stack: null };

// ---------- proportions: the skeleton is retargeted bone by bone (FK from the pelvis), then put back on the floor ----------
const TOPO = ['hipL','hipR','kneeL','kneeR','ankleL','ankleR','heelL','heelR','ballL','ballR','toeL','toeR','spineMid','chest','neckBase','shoulderL','shoulderR','elbowL','elbowR','wristL','wristR','headBase','head','headTop','nose'];
const PAR = { hipL:'pelvis', hipR:'pelvis', kneeL:'hipL', kneeR:'hipR', ankleL:'kneeL', ankleR:'kneeR', heelL:'ankleL', heelR:'ankleR', ballL:'ankleL', ballR:'ankleR', toeL:'ballL', toeR:'ballR',
  spineMid:'pelvis', chest:'spineMid', neckBase:'chest', shoulderL:'neckBase', shoulderR:'neckBase', elbowL:'shoulderL', elbowR:'shoulderR', wristL:'elbowL', wristR:'elbowR', headBase:'neckBase', head:'headBase', headTop:'head', nose:'head' };
const GRP = { hipL:'hips', hipR:'hips', kneeL:'thigh', kneeR:'thigh', ankleL:'shin', ankleR:'shin', heelL:'foot', heelR:'foot', ballL:'foot', ballR:'foot', toeL:'foot', toeR:'foot',
  spineMid:'torso', chest:'torso', neckBase:'torso', shoulderL:'shoulders', shoulderR:'shoulders', elbowL:'upper_arm', elbowR:'upper_arm', wristL:'forearm', wristR:'forearm', headBase:'head', head:'head', headTop:'head', nose:'head' };
const GROUPS = ['head', 'torso', 'shoulders', 'hips', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot'];
// Leonardo's Vitruvian man, as fractions of the height
const VIT = { head: 1 / 6, torso: .31, shoulders: .2, hips: .11, upper_arm: .165, forearm: .15, hand: .1, thigh: .25, shin: .23, foot: 1 / 7 };
const FEET = ['ankleL','ankleR','heelL','heelR','ballL','ballR','toeL','toeR'].map(n => ji[n]);
function v3(a, b) { return [b[0] - a[0], b[1] - a[1], b[2] - a[2]]; }
function len3(a) { return Math.hypot(a[0], a[1], a[2]); }
const hyp = (p, q) => Math.hypot(q[0] - p[0], q[1] - p[1]);
const rot = (u, a) => [u[0] * Math.cos(a) - u[1] * Math.sin(a), u[0] * Math.sin(a) + u[1] * Math.cos(a)];
function measure(j) {
  const d = (a, b) => len3(v3(j[ji[a]], j[ji[b]])), av = (a, b) => (d(a + 'L', b + 'L') + d(a + 'R', b + 'R')) / 2;
  return { head: d('neckBase', 'headTop'), torso: d('pelvis', 'spineMid') + d('spineMid', 'chest') + d('chest', 'neckBase'), shoulders: d('shoulderL', 'shoulderR'),
    hips: d('hipL', 'hipR'), upper_arm: av('shoulder', 'elbow'), forearm: av('elbow', 'wrist'), hand: HAND_CM, thigh: av('hip', 'knee'), shin: av('knee', 'ankle'), foot: av('heel', 'toe') };
}
function retarget(raw, K) {
  const out = []; out[0] = raw[0].slice();
  for (const n of TOPO) { const i = ji[n], p = ji[PAR[n]], k = K[GRP[n]] ?? 1; out[i] = [0, 1, 2].map(a => out[p][a] + (raw[i][a] - raw[p][a]) * k); }
  const lo = Math.min(...FEET.map(i => raw[i][1])), ln = Math.min(...FEET.map(i => out[i][1]));
  for (const q of out) q[1] += lo - ln;
  return out;
}
const JC = new WeakMap();
function joints(fr, id) {
  let c = JC.get(fr); if (!c || c.v !== S.pv) { c = { v: S.pv }; JC.set(fr, c); }
  if (c[id]) return c[id];
  const a = fr.a[id]; if (!a) return null;
  const K = id === S.actor ? S.K : {};
  const j = Object.keys(K).length ? retarget(a.j, K) : a.j.map(q => q.slice());
  for (const s of ['L', 'R']) {              // fingertip: the forearm carried on by a hand length
    const e = j[ji['elbow' + s]], w = j[ji['wrist' + s]], d = v3(e, w), l = len3(d) || 1, h = HAND_CM * (K.hand ?? 1);
    j.push([w[0] + d[0] / l * h, w[1] + d[1] / l * h, w[2] + d[2] / l * h]);
  }
  const p = j[0], u = v3(p, j[ji.spineMid]), l = len3(u) || 1;   // waist above the pelvis joint, crotch below: the hip bridge's span
  j.push([p[0] + u[0] / l * 7, p[1] + u[1] / l * 7, p[2] + u[2] / l * 7], [p[0] - u[0] / l * 13, p[1] - u[1] / l * 13, p[2] - u[2] / l * 13]);
  return c[id] = j;
}

// ---------- segments and rig styles ----------
const SEG = {
  pelvis: { slots: ['pelvis'], from: 'waist', to: 'crotch', par: [], face: 'pfwd', g: 'hips' },
  torso: { slots: ['torso'], from: 'waist', to: 'neckBase', par: ['pelvis'], face: 'fwd', g: 'torso' },
  head: { slots: ['head'], from: 'neckBase', to: 'headTop', par: ['torso'], face: 'hfwd', g: 'head' },
};
for (const s of ['L', 'R']) Object.assign(SEG, {
  ['upper_arm_' + s]: { slots: ['upper_arm'], from: 'shoulder' + s, to: 'elbow' + s, par: ['torso'], face: 'fwd', g: 'upper_arm' },
  ['forearm_' + s]: { slots: ['forearm'], from: 'elbow' + s, to: 'wrist' + s, par: ['upper_arm_' + s], face: 'fwd', ik: 'upper_arm_' + s, g: 'forearm' },
  ['mitt_' + s]: { slots: ['forearm', 'hand'], from: 'elbow' + s, to: 'tip' + s, par: ['upper_arm_' + s], face: 'fwd', ik: 'upper_arm_' + s, g: 'forearm' },
  ['arm_' + s]: { slots: ['upper_arm', 'forearm'], from: 'shoulder' + s, to: 'wrist' + s, par: ['torso'], face: 'fwd', g: 'upper_arm' },
  ['hand_' + s]: { slots: ['hand'], from: 'wrist' + s, to: 'tip' + s, par: ['forearm_' + s, 'arm_' + s], face: 'fwd', g: 'hand' },
  ['thigh_' + s]: { slots: ['thigh'], from: 'hip' + s, to: 'knee' + s, par: ['pelvis', 'torso'], face: 'pfwd', g: 'thigh' },
  ['shin_' + s]: { slots: ['shin'], from: 'knee' + s, to: 'ankle' + s, par: ['thigh_' + s], face: 'pfwd', ik: 'thigh_' + s, g: 'shin' },
  ['leg_' + s]: { slots: ['thigh', 'shin'], from: 'hip' + s, to: 'ankle' + s, par: ['pelvis', 'torso'], face: 'pfwd', g: 'thigh' },
  ['foot_' + s]: { slots: ['foot'], from: 'ankle' + s, to: 'toe' + s, par: ['shin_' + s, 'leg_' + s], face: 'pfwd', g: 'foot' },
});
const LR = (...n) => n.flatMap(x => [x + '_L', x + '_R']);
const STYLES = {
  classic: { label: '14 cards', segs: ['torso', 'head', ...LR('upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot')] },
  hips: { label: '15 · hip bridge', segs: ['pelvis', 'torso', 'head', ...LR('upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot')] },
  mitt: { label: '13 · hip bridge + mitts', segs: ['pelvis', 'torso', 'head', ...LR('upper_arm', 'mitt', 'thigh', 'shin', 'foot')] },
  long: { label: '10 · long limbs', segs: ['torso', 'head', ...LR('arm', 'hand', 'leg', 'foot')] },
};
// draw order, back to front, by role: the limb nearer the camera is "near"; a child sits on its parent (shoe over calf)
const STACK0 = ['far_upper_arm', 'far_arm', 'far_forearm', 'far_mitt', 'far_hand', 'far_thigh', 'far_leg', 'far_shin', 'far_foot', 'near_thigh', 'near_leg', 'pelvis',
  'near_shin', 'near_foot', 'torso', 'head', 'near_upper_arm', 'near_arm', 'near_forearm', 'near_mitt', 'near_hand'];
S.stack = { side: STACK0.slice(), front: STACK0.slice(), back: STACK0.slice() };
const ARMS = /^(upper_arm|forearm|mitt|arm|hand)$/;
const VIEWS = ['side', 'front', 'back'];
const VIEWOF = v => v === 'profile' || v === 'side' ? 'side' : v === 'front' || v === 'threequarter' ? 'front' : v === 'back' || v === 'threequarter_back' ? 'back' : null;
const viewOf = c => VIEWOF(S.fix[c.id]?.view || c.human?.view || c.view || (c.clip?.view_l_p > .8 && c.clip.view_l) || c.est_view) || 'side';
const OTHER = k => k.endsWith('_L') ? k.slice(0, -1) + 'R' : k.endsWith('_R') ? k.slice(0, -1) + 'L' : null;
const STICK = [['pelvis','spineMid'],['spineMid','chest'],['chest','neckBase'],['neckBase','headBase'],['headBase','headTop'],['head','nose'],
  ['neckBase','shoulderL'],['neckBase','shoulderR'],['shoulderL','elbowL'],['elbowL','wristL'],['shoulderR','elbowR'],['elbowR','wristR'],
  ['pelvis','hipL'],['pelvis','hipR'],['hipL','kneeL'],['kneeL','ankleL'],['ankleL','heelL'],['heelL','ballL'],['ballL','toeL'],['ankleL','ballL'],
  ['hipR','kneeR'],['kneeR','ankleR'],['ankleR','heelR'],['heelR','ballR'],['ballR','toeR'],['ankleR','ballR']];
const NAME = { upper_arm: /upper|uarm|bicep|arm-a\b|^arm/, forearm: /fore|farm/, hand: /hand|palm|fist|grip|point|pinch|relax|open|thumb|wave|cup|claw/,
  thigh: /thigh/, shin: /shin|calf|leg-lower|lower-leg/, foot: /foot|shoe|boot|sneak|heel|toe/, head: /head|profile|face|front|threequarter|back/,
  torso: /torso|chest|body|jacket|shirt|vest|bodice/, pelvis: /hip|pelvis|waist/ };
const NOT = { hand: /face|head|eye|mouth/, head: /hand|arm|leg|foot/, thigh: /pelvis|connect|waist/ };
const nameOK = c => { const hb = S.fix[c.id]?.bad ?? c.human?.bad; if (hb != null) return !hb; if (S.fix[c.id]?.slot ?? c.human?.slot) return true; if (c.odd || c.clip?.flags?.some(f => f.startsWith('looks like'))) return false; if (!NAME[c.slot]) return true; const n = c.id.split('/').pop().toLowerCase(), sh = c.id.split('/')[0].toLowerCase(); return NAME[c.slot].test(n) && !(NOT[c.slot] && NOT[c.slot].test(sh + ' ' + n)); };
const human = (c, f) => S.fix[c.id]?.[f] ?? c.human?.[f];
const painted = c => human(c, 'painted') ?? (c.clip?.face === 'painted' && c.clip.face_p > .75);

// ---------- cards and their images ----------
const IMG = {};
P.loadImage = src => { const im = new Image(); im.src = src; return im; };
P.canvas = (w, h) => { const o = document.createElement('canvas'); o.width = w; o.height = h; return o; };
P.imgBase = '';   // prefix for card img paths (library img paths are relative to shots/skinlab/)
const img = c => IMG[c.id] || (IMG[c.id] = P.loadImage(c.img.startsWith('data:') ? c.img : P.imgBase + c.img));
const AB = c => ({ A: S.fix[c.id]?.A || c.A, B: S.fix[c.id]?.B || c.B });
const pts = (c, sk) => { const p = AB(c); return sk.swap ? { A: p.B, B: p.A } : p; };
const cardLeft = c => S.fix[c.id]?.left ?? c.human?.left ?? (c.slot === 'foot' ? AB(c).B[0] < AB(c).A[0] : c.faces === 'L');
function index() {
  for (const c of S.lib) { c.odd = c.slot === 'head' && (c.skin < .1 || c.h / c.w > 1.9); c.slot0 = c.slot0 || c.slot; const re = S.fix[c.id]?.slot ?? c.human?.slot; if (re) c.slot = re; }
  S.byId = Object.fromEntries(S.lib.map(c => [c.id, c]));
}

// ---------- 3D -> 2D ----------
function makePort(x, y, w, h, yaw, elev, label) {
  const cy = Math.cos(yaw * Math.PI / 180), sy = Math.sin(yaw * Math.PI / 180), ce = Math.cos(elev * Math.PI / 180), se = Math.sin(elev * Math.PI / 180);
  const k = h / 230;                          // px per cm: a 230 cm tall window
  return { x, y, w, h, yaw, label, k, cx: 0, cz: 0, toward: [sy, 0, cy], right: [cy, 0, -sy],
    p(q) {
      const X = q[0] - this.cx, Z = q[2] - this.cz;
      const rx = X * cy - Z * sy, rz = X * sy + Z * cy;
      const ry = q[1] * ce - rz * se, d = q[1] * se + rz * ce;
      return [this.x + this.w / 2 + rx * k, this.y + this.h - 22 - ry * k, d];
    } };
}
function centre(port, fr) {
  if (S.centre) return S.centre(port, fr);
  const j = joints(fr, S.actor); if (S.follow && j) { port.cx = j[0][0]; port.cz = j[0][2]; } else { port.cx = 0; port.cz = 0; }
}

// ---------- which card shows: the body's facing against the camera ----------
function active(k, sk, a, port) {
  const f = a[SEG[k].face] || a.fwd, dot = (u, v) => u[0] * v[0] + u[1] * v[1] + u[2] * v[2];
  const d = dot(f, port.toward), lat = dot(f, port.right);
  const want = d > .55 ? 'front' : d < -.55 ? 'back' : 'side';
  const order = { side: ['side', 'front', 'back'], front: ['front', 'side', 'back'], back: ['back', 'front', 'side'] }[want];
  const v = order.find(v => sk.cards[v] && S.byId[sk.cards[v]]); if (!v) return null;
  const c = S.byId[sk.cards[v]];
  // profile cards are drawn facing right unless marked: mirror across the A→B line when the body faces screen-left
  const mir = sk.mirror !== (v === 'side' && (lat < 0) !== cardLeft(c));
  return { c, view: v, want, mir };
}

// ---------- placing a card ----------
// screen = P + R(ang)·(off + s·M·R(-ax)·(q − A)), M mirrors across the card's own A→B line
function mk(k, c, sk, Pp, ang, s, mir) {
  const { A, B } = pts(c, sk), ax = Math.atan2(B[1] - A[1], B[0] - A[0]), lab = Math.hypot(B[0] - A[0], B[1] - A[1]) || 1;
  return { k, c, sk, P: Pp, ang, s, mir, A, B, ax, lab, off: [sk.dx * lab * s / 100, sk.dy * lab * s / 100] };
}
function fwd(x, q) { let u = rot([q[0] - x.A[0], q[1] - x.A[1]], -x.ax); u = [u[0] * x.s + x.off[0], u[1] * x.s * (x.mir ? -1 : 1) + x.off[1]]; u = rot(u, x.ang); return [x.P[0] + u[0], x.P[1] + u[1]]; }
function inv(x, p) { let u = rot([p[0] - x.P[0], p[1] - x.P[1]], -x.ang); u = [(u[0] - x.off[0]) / x.s, (u[1] - x.off[1]) / x.s * (x.mir ? -1 : 1)]; u = rot(u, x.ax); return [u[0] + x.A[0], u[1] + x.A[1]]; }
function scaleOf(k, c, sk, j, pj, port, puppet) {
  const sg = SEG[k], { A, B } = pts(c, sk), lab = Math.hypot(B[0] - A[0], B[1] - A[1]) || 1;
  if (sk.mode === 'true') return port.k / c.px_per_cm * sk.scale;
  // fit: pinned cards stretch to the bone as seen; puppet cards stay rigid at the bone's real 3D length
  return (puppet ? len3(v3(j[ji[sg.from]], j[ji[sg.to]])) * port.k : hyp(pj[ji[sg.from]], pj[ji[sg.to]])) / lab * sk.scale;
}
// where a child hangs on its parent: the parent's B when the child continues the chain, its A when they share a root,
// otherwise read off the parent card at the bind frame (and snapped to the nearest real brad on it)
function socket(k, px, port, puppet) {
  const sg = SEG[k], ps = SEG[px.k];
  if (ps.to === sg.from) return { p: fwd(px, px.B), how: 'chain' };
  if (ps.from === sg.from) return { p: fwd(px, px.A), how: 'root' };
  const key = [port.label, Math.round(port.yaw), port.k, px.c.id, px.sk.mode, px.sk.scale, px.sk.swap, px.mir, k, S.bindF, puppet, S.actor, S.pv].join('|');
  let q = S.sock[key];
  if (!q) {
    const fr = S.bindFrame ? S.bindFrame(k, px, port) : S.data.frames[S.bindF], cx = port.cx, cz = port.cz; centre(port, fr);
    const j = joints(fr, S.actor), pj = j.map(v => port.p(v)), Pp = pj[ji[ps.from]], Q = pj[ji[ps.to]];
    const b = mk(px.k, px.c, px.sk, Pp, Math.atan2(Q[1] - Pp[1], Q[0] - Pp[0]) + px.sk.rot * Math.PI / 180, scaleOf(px.k, px.c, px.sk, j, pj, port, puppet), px.mir);
    const raw = inv(b, pj[ji[sg.from]]);
    let best = null, bd = .22 * b.lab;
    for (const br of px.c.brads || []) { const d = hyp(br, raw); if (d < bd) { bd = d; best = br; } }
    q = S.sock[key] = { q: best || raw, how: best ? 'brad' : 'bound' };
    port.cx = cx; port.cz = cz;
  }
  return { p: fwd(px, q.q), how: q.how };
}
// two rigid cards from S0 reaching for T, bending the way the skeleton's middle joint E bends
function ik2(S0, T, E, l1, l2) {
  const dx = T[0] - S0[0], dy = T[1] - S0[1], base = Math.atan2(dy, dx);
  const d = Math.max(Math.abs(l1 - l2) + 1e-3, Math.min(l1 + l2 - 1e-3, Math.hypot(dx, dy)));
  const a = Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))));
  return base + (dx * (E[1] - S0[1]) - dy * (E[0] - S0[0]) >= 0 ? 1 : -1) * a;
}
function roleOf(k, near) {
  const m = k.match(/^(.*)_([LR])$/); if (!m) return k;
  return (m[2] === (ARMS.test(m[1]) ? near.arm : near.leg) ? 'near_' : 'far_') + m[1];
}
// the whole figure for one frame in one view: a placed card per segment, with its gap to its parent and its miss to its target
function solve(fr, port, style = S.style, puppet = S.puppet) {
  const j = joints(fr, S.actor); if (!j) return null;
  const a = fr.a[S.actor], pj = j.map(q => port.p(q)), segs = STYLES[style].segs, X = {};
  const near = { arm: pj[ji.shoulderL][2] > pj[ji.shoulderR][2] ? 'L' : 'R', leg: pj[ji.hipL][2] > pj[ji.hipR][2] ? 'L' : 'R' };
  for (const k of segs) {
    const sg = SEG[k], sk = S.skin[k]; if (!sk) continue;
    const ac = active(k, sk, a, port); if (!ac) continue;
    const Pp = pj[ji[sg.from]], Q = pj[ji[sg.to]], s = scaleOf(k, ac.c, sk, j, pj, port, puppet);
    const parent = sg.par.find(p => X[p]);
    const sock = parent ? socket(k, X[parent], port, puppet) : null;
    let start = puppet && sock ? sock.p : Pp, ang = Math.atan2(Q[1] - start[1], Q[0] - start[0]);
    const low = puppet && segs.find(q => SEG[q].ik === k && S.skin[q]);
    if (low) {
      const lc = active(low, S.skin[low], a, port);
      if (lc) { const { A, B } = pts(lc.c, S.skin[low]); const l2 = Math.hypot(B[0] - A[0], B[1] - A[1]) * scaleOf(low, lc.c, S.skin[low], j, pj, port, puppet);
        const { A: a1, B: b1 } = pts(ac.c, sk); ang = ik2(start, pj[ji[SEG[low].to]], Q, Math.hypot(b1[0] - a1[0], b1[1] - a1[1]) * s, l2); }
    }
    const x = mk(k, ac.c, sk, start, ang + sk.rot * Math.PI / 180, s, ac.mir);
    x.view = ac.view; x.want = ac.want; x.parent = parent; x.sockHow = sock?.how; x.sockP = sock?.p;
    x.gap = sock ? hyp(fwd(x, x.A), sock.p) / port.k : 0;
    x.miss = hyp(fwd(x, x.B), Q) / port.k;
    x.d = (Pp[2] + Q[2]) / 2; x.role = roleOf(k, near);
    X[k] = x;
  }
  const view = (X.torso || X.pelvis)?.want || 'side', st = S.stack[view];
  const rank = x => { const i = st.indexOf(x.role); return i < 0 ? 99 : i; };
  const order = Object.values(X).sort((a, b) => rank(a) - rank(b) || a.d - b.d);
  return { X, pj, j, near, view, order };
}
function drawCard(g, x, alpha) {
  const im = img(x.c); if (!im.complete || !im.naturalWidth) return;
  g.save(); g.globalAlpha = alpha;
  g.translate(x.P[0], x.P[1]); g.rotate(x.ang); g.translate(x.off[0], x.off[1]);
  g.scale(x.s, x.s * (x.mir ? -1 : 1)); g.rotate(-x.ax);
  g.drawImage(im, -x.A[0], -x.A[1]);
  g.restore();
}

// ---------- the compact bank (build.py): per actor one flat list of integers, delta-coded frame to frame ----------
function decode(d) {
  const frames = Array.from({ length: d.n }, () => ({ a: {} })), Pn = d.per_frame;
  for (const [id, flat] of Object.entries(d.a)) {
    const cur = new Array(Pn).fill(0);
    for (let f = 0; f < d.n; f++) {
      for (let i = 0; i < Pn; i++) cur[i] += flat[f * Pn + i];
      const j = []; for (let i = 0; i < 26; i++) j.push([cur[i * 3] / 2, cur[i * 3 + 1] / 2, cur[i * 3 + 2] / 2]);
      const v = o => [cur[78 + o] / 100, cur[79 + o] / 100, cur[80 + o] / 100];
      frames[f].a[id] = { j, fwd: v(0), hfwd: v(3), pfwd: v(6) };
    }
  }
  decodeProps(d, frames);
  return { ...d, frames };
}
// props (build.py 'props'): per frame fr.p[name] = {type, size, pos [x,y,z] cm, rot [rx,ry,rz] deg, held: 'A.R' | null}
function decodeProps(d, frames) {
  for (const [name, q] of Object.entries(d.props || {})) {
    const cur = new Array(q.per_frame).fill(0);
    for (let f = 0; f < d.n; f++) {
      for (let i = 0; i < q.per_frame; i++) cur[i] += q.f[f * q.per_frame + i];
      if (cur[6] < 0) continue;
      (frames[f].p ||= {})[name] = { type: q.type, size: q.size, pos: [cur[0] / 2, cur[1] / 2, cur[2] / 2], rot: [cur[3], cur[4], cur[5]], held: q.held[cur[6]] ?? null };
    }
  }
}
function measureActor(fr) {
  const a = (fr || S.data.frames[0]).a[S.actor]; if (!a) return;
  S.rec = measure(a.j); S.H = 8 + S.rec.shin + S.rec.thigh + S.rec.torso + S.rec.head;
  if (S.preset !== 'custom') S.K = presetK(S.preset);
  S.pv++;
}
function presetK(name) {
  if (name === 'bolas' || !S.rec) return {};
  if (name === 'vitruvian') return Object.fromEntries(GROUPS.map(g => [g, VIT[g] * S.H / S.rec[g]]));
  if (name === 'cards') {   // make the skeleton fit the dressed cards (true lengths)
    const SEGS = { head: ['head'], torso: ['torso'], upper_arm: LR('upper_arm'), forearm: LR('forearm'), hand: LR('hand'), thigh: LR('thigh'), shin: LR('shin'), foot: LR('foot') };
    const K = {};
    for (const [g, ks] of Object.entries(SEGS)) {
      const cms = ks.map(k => { const sk = S.skin[k]; const c = sk && S.byId[sk.cards.side || sk.cards.front || sk.cards.back]; if (!c) return null; const { A, B } = AB(c); return Math.hypot(B[0] - A[0], B[1] - A[1]) / c.px_per_cm * sk.scale; }).filter(Boolean);
      if (cms.length) K[g] = (cms.reduce((a, b) => a + b) / cms.length + (g === 'torso' ? 7 : 0)) / S.rec[g];
    }
    return K;
  }
  return S.K;
}
const cur = g => S.rec ? S.rec[g] * (S.K[g] ?? 1) : 0;

// ---------- skins: auto-dress and kitbash (index.html dress / kitbash / buildCard) ----------
function newSkin() { return { cards: {}, mode: 'fit', scale: 1, rot: 0, dx: 0, dy: 0, mirror: false, swap: false }; }
const dE = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
// dress every limb, every view, from one character's cards; returns the skin (index.html calls setSkin on it)
function dress(ch, fr) {
  const j = joints(fr, S.actor);
  const mine = S.lib.filter(c => c.character === ch && c.q !== 'C' && nameOK(c));
  const cover = {}; for (const c of mine) (cover[c.costume] ||= new Set()).add(c.slot + viewOf(c));
  const costume = Object.keys(cover).sort((a, b) => cover[b].size - cover[a].size)[0];   // one costume, the one that covers most
  const sk = {}, home = {};
  for (const pass of [0, 1]) for (const k of Object.keys(SEG)) {
    const sg = SEG[k], side = k.endsWith('_L') ? 'L' : k.endsWith('_R') ? 'R' : null, bl = len3(v3(j[ji[sg.from]], j[ji[sg.to]])) || 1;
    for (const v of VIEWS) {
      const pool = mine.filter(c => sg.slots.includes(c.slot) && viewOf(c) === v);
      if (!pool.length) continue;
      const score = c => { const { A, B } = AB(c); const r = Math.hypot(B[0] - A[0], B[1] - A[1]) / c.px_per_cm / bl;
        return Math.abs(Math.log(r)) + (c.costume === costume ? 0 : .5) + (side && c.side && c.side !== side ? .2 : 0) + (c.view ? 0 : .15)
          + (c.q === 'A' ? 0 : .15) + (/brads|eyelet|ankle|neck|waist/.test(c.pts) ? 0 : .25) + (sg.slots[0] === c.slot ? 0 : .3)
          + (pass && home[v] && c.id.split('/')[0] !== home[v] ? .35 : 0); };
      pool.sort((a, b) => score(a) - score(b));
      (sk[k] ||= newSkin()).cards[v] = pool[0].id;
    }
    if (!pass) for (const v of VIEWS) { const n = {}; for (const x of Object.values(sk)) if (x.cards[v]) { const sh = x.cards[v].split('/')[0]; n[sh] = (n[sh] || 0) + 1; }
      home[v] = Object.keys(n).sort((a, b) => n[b] - n[a])[0]; }
  }
  kitbash(sk, ch, mine, j);
  return sk;
}
function kitbash(sk, ch, mine, j) {
  const mean = (cs, f) => { cs = cs.filter(c => c[f]); return cs.length ? [0, 1, 2].map(i => cs.reduce((t, c) => t + c[f][i], 0) / cs.length) : null; };
  const tone = mean(mine.filter(c => c.slot === 'hand' || c.slot === 'head'), 'tone');
  for (const k of Object.keys(SEG)) {
    const sg = SEG[k], side = k.endsWith('_L') ? 'L' : k.endsWith('_R') ? 'R' : null, bl = len3(v3(j[ji[sg.from]], j[ji[sg.to]])) || 1;
    for (const v of VIEWS) {
      if (sk[k]?.cards[v]) continue;
      if (k === 'torso' || k === 'pelvis') { const c = buildCard(k, v, ch); (sk[k] ||= newSkin()).cards[v] = c.id; (sk[k].src ||= {})[v] = 'built'; continue; }
      const pal = mean(mine.filter(c => sg.slots.includes(c.slot)), 'pal') || mean(mine, 'pal');
      const pool = S.lib.filter(c => c.character !== ch && !c.gen && sg.slots.includes(c.slot) && c.q !== 'C' && nameOK(c) && viewOf(c) === v && !(side && c.side && c.side !== side));
      if (!pool.length) continue;
      const score = c => { const { A, B } = AB(c);
        return (pal && c.pal ? dE(pal, c.pal) / 25 : 1) + Math.abs(Math.log(Math.hypot(B[0] - A[0], B[1] - A[1]) / c.px_per_cm / bl))
          + (tone && c.tone && /head|hand/.test(c.slot) ? dE(tone, c.tone) / 15 : 0) + (c.q === 'A' ? 0 : .2); };
      pool.sort((a, b) => score(a) - score(b));
      (sk[k] ||= newSkin()).cards[v] = pool[0].id; (sk[k].src ||= {})[v] = 'bashed';
    }
  }
}
const labCss = L => { const fy = (L[0] + 16) / 116, fx = fy + L[1] / 500, fz = fy - L[2] / 200, f = t => t ** 3 > .008856 ? t ** 3 : (t - 16 / 116) / 7.787;
  const X = f(fx) * .9505, Y = f(fy), Z = f(fz) * 1.089, g = c => 255 * Math.max(0, Math.min(1, c > .0031308 ? 1.055 * c ** (1 / 2.4) - .055 : 12.92 * c));
  return `rgb(${g(3.2406 * X - 1.5372 * Y - .4986 * Z)},${g(-.9689 * X + 1.8758 * Y + .0415 * Z)},${g(.0557 * X - .204 * Y + 1.057 * Z)})`; };
// a torso or hip bridge drawn by code to the skeleton's own widths, in the kit's cloth, with a kraft edge and brass brads
function buildCard(kind, view, ch, onPaint) {
  const id = `gen.${ch}/built-${kind === 'torso' ? 'torso' : 'hip'}-${view}`;
  if (S.byId[id]) return S.byId[id];
  const sw = cur('shoulders') + 10, hw = cur('hips') + 10;
  let pts_, brads, h, A, B;
  if (kind === 'torso') {
    h = cur('torso') - 7;
    if (view === 'side') { const cd = sw * .5, wd = hw * .5;
      pts_ = [[-wd / 2, 0], [wd / 2, 0], [wd / 2 + 2, h * .45], [cd / 2 + 2, h * .78], [cd / 2 - 2, h * .95], [5, h], [-6, h], [-cd / 2 + 1, h * .93], [-cd / 2, h * .7], [-wd / 2 - 1, h * .35]];
      brads = [[0, 4], [0, h - 3], [0, h - 9]]; }
    else { pts_ = [[-hw / 2, 0], [hw / 2, 0], [hw / 2 + 1, h * .35], [sw / 2, h * .8], [sw / 2 - 3, h * .97], [7, h], [-7, h], [-sw / 2 + 3, h * .97], [-sw / 2, h * .8], [-hw / 2 - 1, h * .35]];
      brads = [[0, 4], [0, h - 3], [sw / 2 - 6, h - 7], [-(sw / 2 - 6), h - 7]]; }
    A = brads[0]; B = brads[1];
  } else {
    h = 20; const w = view === 'side' ? hw * .55 : hw;
    pts_ = [[-w * .3, 0], [w * .3, 0], [w / 2, h * .6], [w / 2, h], [-w / 2, h], [-w / 2, h * .6]];
    brads = view === 'side' ? [[0, h - 3], [0, h * .45]] : [[0, h - 3], [hw / 2 - 7, h * .45], [-(hw / 2 - 7), h * .45]];
    A = brads[0]; B = [0, 0];
  }
  const K = 4, m = 6, xs = pts_.map(p => p[0]), W = Math.ceil((Math.max(...xs) - Math.min(...xs)) * K + 2 * m), Hp = Math.ceil(h * K + 2 * m), x0 = -Math.min(...xs) * K + m;
  const Pt = p => [x0 + p[0] * K, Hp - m - p[1] * K];
  const src = S.lib.find(c => c.character === ch && c.slot === kind && !c.gen && nameOK(c) && c.q !== 'C') || S.lib.find(c => c.character === ch && c.slot === 'torso' && !c.gen);
  const c = { id, gen: true, w: W, h: Hp, slot: kind, side: null, view: view === 'side' ? 'profile' : view, character: ch, costume: 'built', px_per_cm: K,
    A: Pt(A), B: Pt(B), pts: 'brads', q: 'A', label: 'built by code', brads: brads.map(Pt), pal: src?.pal, skin: 0, img: '' };
  const paint = () => {
    const o = P.canvas(W, Hp), g = o.getContext('2d');
    g.beginPath(); pts_.forEach((p, i) => { const q = Pt(p); i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]); }); g.closePath();
    g.save(); g.clip();
    const im = src && img(src);
    if (im && im.complete && im.naturalWidth) { const tw = im.naturalWidth * .34, th = im.naturalHeight * .3;
      for (let y = 0; y < Hp; y += th) for (let x = 0; x < W; x += tw) g.drawImage(im, im.naturalWidth * .33, im.naturalHeight * .35, tw, th, x, y, tw, th); }
    else { g.fillStyle = src?.pal ? labCss(src.pal) : '#2a2422'; g.fillRect(0, 0, W, Hp); if (im && im.addEventListener) im.addEventListener('load', paint, { once: true }); }
    const gr = g.createLinearGradient(0, 0, W, 0); gr.addColorStop(0, '#0007'); gr.addColorStop(.5, '#0000'); gr.addColorStop(1, '#0007'); g.fillStyle = gr; g.fillRect(0, 0, W, Hp);
    g.restore(); g.lineJoin = 'round';
    g.lineWidth = 5; g.strokeStyle = '#c9a26b'; g.stroke(); g.lineWidth = 1; g.strokeStyle = '#6b4a2a'; g.stroke();
    for (const b of brads) { const q = Pt(b), rg = g.createRadialGradient(q[0] - 2, q[1] - 2, 1, q[0], q[1], 7); rg.addColorStop(0, '#fff3c0'); rg.addColorStop(.5, '#d9a640'); rg.addColorStop(1, '#7a5410'); g.fillStyle = rg; g.beginPath(); g.arc(q[0], q[1], 6, 0, 7); g.fill(); }
    IMG[id] = o; o.complete = true; o.naturalWidth = W;   // a canvas draws like an image
    if (onPaint) onPaint(c);
  };
  paint(); S.lib.push(c); S.byId[id] = c;
  return c;
}
// cards a skin names by id that are built by code: rebuild them (index.html does this at boot)
function rebuildGen(skin) {
  for (const k in skin) for (const id of Object.values(skin[k].cards || {})) if (id.startsWith('gen.')) {
    const m = id.match(/^gen\.(.+)\/built-(torso|hip)-(\w+)$/); if (m) buildCard(m[2] === 'hip' ? 'pelvis' : 'torso', m[3], m[1]);
  }
}
function stick(g, pj, col, w) {
  g.strokeStyle = col; g.lineWidth = w; g.lineCap = 'round';
  for (const [a, b] of STICK) { const p = pj[ji[a]], q = pj[ji[b]]; g.beginPath(); g.moveTo(p[0], p[1]); g.lineTo(q[0], q[1]); g.stroke(); }
}

Object.assign(P, { S, J, ji, HAND_CM, TOPO, PAR, GRP, GROUPS, VIT, FEET, measure, retarget, joints, SEG, LR, STYLES, STACK0, ARMS, VIEWS, VIEWOF, viewOf, OTHER, STICK,
  NAME, NOT, nameOK, human, painted, IMG, img, AB, pts, cardLeft, index, v3, len3, hyp, rot, makePort, centre, active, mk, fwd, inv, scaleOf, socket, ik2, roleOf, solve,
  drawCard, decode, decodeProps, measureActor, presetK, cur, newSkin, dE, dress, kitbash, labCss, buildCard, rebuildGen, stick });
root.PuppetCore = P;
})(typeof window !== 'undefined' ? window : globalThis);
