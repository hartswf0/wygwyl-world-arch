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

   ---------------------------------------------------------------------------------------------------------------------------
   API CONTRACT: the general renderer (stable; Builder B owns this file, hosts call it)

     await PuppetCore.prepare({ contract, library, imgBase?, harvest? }) // loads every card the contract names (and harvested cards), builds code cards
     const r = PuppetCore.renderPose(ctx, {
       contract,               // a character contract (contracts/<ch>.json, parsed); applied on first use if prepare() was not awaited
       library?,               // library.json (parsed); needed when the contract is new and prepare() was not called
       joints3d,               // EITHER {name: [x, y, z]} with the 26 Bolas names (pelvis hipL hipR kneeL kneeR ankleL ankleR heelL heelR ballL ballR
                               //   toeL toeR spineMid neckBase chest shoulderL shoulderR elbowL elbowR wristL wristR headBase head headTop nose;
                               //   optional tipL tipR), cm, x = his LEFT, y = UP, z = his FORWARD; missing feet/spine/head points are filled
                               // OR a Pose Lab fk() result (names shL, knL, ...: converted by PuppetCore.fromPoseLab)
                               // OR a frame record {j: [26 joints in that order], ...} in the same body frame
       view?, facing?,         // 'front' | 'side' (= 'profile') | 'back' | 'threequarter' | 'threequarter_back';  'right' | 'left'
       psi?,                   // or the Pose Lab view yaw (0 front, +90 profile facing screen-right, 180 back); wins over view/facing
       port?,                  // or a host projection {p(q) -> [x, y, depth], k px/cm, right, toward, label}; wins over psi/view and x/y/heightPx
       heightPx?, x?, y?,      // without a port: his standing height in px, screen x of the pelvis, screen y of the floor
       handStates?,            // {L: 'open' | 'grip' | ..., R: ...}: limbs.hand_*.states
       harvest?, harvestExclude?, // replacement cards (harvestExclude: a source id, a list of them, or a predicate (card) => bool) (library_harvest.json rows: slot/side/view/dir_cam/ratio/bad): used for a foreshortened limb
                               //   when one of the same part and view has a bone direction within ~20 deg; harvestExclude leaves one source out
       headScale? = 1.05,      // heads at the paintings' canon: top of hair to chin = 0.152 of his height, measured on 7 standing paintings; headCm?, target? (the Pose Lab target: its neck/head markers give paintedHeadDeg), paintedHeadDeg? (the painting's head axis from its markers, screen deg clockwise from up: the drawn head stays within 15 deg of it), headLeanDeg? = 10 (only without a painted head axis), neckDeg?, farShade? = .72,
       rescale?,               // card scales, sockets and width matches are fixed by the first pose drawn with a contract; true re-fits them to this skeleton
       cardView?, ground?      // force the card view; ground (default true without a port) puts his lowest foot point on the floor
     })
     PuppetCore.adjustJoints(args) -> {adjusted, named (= joints3d), j, tips, yaw, moves, warnings}: the joints renderPose will draw,
       after every joint move (head into the picture plane, neck, hand at the head with the elbow re-solved): pick cards from these;
       passing the result back as joints3d draws it as is
     -> { cards: [{part, card, view, role, mirrored, projRatio, verdict, method, gap_cm, miss_cm}],
          segments: [{k, role, card, view, want, mirrored, miss_cm, ratio, atlas, drawn, P, Q, end}],   // the same, in the harness's shape
          sol, warnings: [string], view, yaw, px_per_cm, bbox }

   What it does, the same for every pose (no tuning to a shot):
   - card view from the yaw: front |yaw| <= 22.5, three-quarter <= 67.5 (contract 'threequarter' cards, else front), side, back >= 112.5;
     every card of the figure in that one view (no mid-swap); a profile or sided three-quarter card is mirrored for a figure facing left
   - one scale per card: A->B over its bone in a neutral pose built from this skeleton's own bone lengths (fix.rigid_ppc wins; heads one
     painted height in every view, times headScale); sockets bind on that neutral pose turned to the card's view and facing
   - the joint atlas per segment: projected / true length >= .88 rotate; .55-.88 replace (contract limbs[k].states.bent[view], or a
     harvested card) or declared shortening (x >= .88, along the card's own axis) + overlap; < .55 a dedicated card
     (states.endon[view], or harvested), else shortened and flagged for restaging
   - hinges bending across the screen use two-card IK the anatomical way (knees forward, elbows back); hinges bending toward the camera
     get no IK (each card aims at its own joint), so front legs stand straight with the skeleton's stance, never bowed into a diamond
   - the head is a painted card: bowed toward the camera it is turned into the picture plane; across the screen the painting decides
     (paintedHeadDeg: the solve's tilt within 15 deg of the painted head axis, else the painted axis), else it rolls at most headLeanDeg (10) off the torso; hands bend <= 80 deg
   - near limbs (his right when he faces screen-right) over the body, far limbs under and darker (farShade); the contract's stack per
     view; its fix fields: A/B, px_per_cm, rigid_ppc, view, left, sockets, hold, erase, trim, flare, states; code-built cards (the seat)
   Proven on 12 painted poses: shots/skinlab/core_check.html + production/recognition/core_check/ (painting | puppet side-by-sides).
   ---------------------------------------------------------------------------------------------------------------------------

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
  for (const s of ['L', 'R']) {              // fingertip: the forearm carried on by a hand length (or where the host aims the hand: a.tips)
    const e = j[ji['elbow' + s]], w = j[ji['wrist' + s]], h = HAND_CM * (K.hand ?? 1), t = a.tips?.[s], d = t ? v3(w, t) : v3(e, w), l = len3(d) || 1;
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
const VIEWS = ['side', 'front', 'back', 'threequarter'];
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
const ppcOf = c => S.fix[c.id]?.px_per_cm || c.px_per_cm;   // a contract may re-claim a card's true scale
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
// A host may declare, per frame, on the actor's frame record a: a.views = {body: 'side'|'front'|'back', head: ...} (the view every card
// shows, so a swap lands where the host says: hysteresis, planted feet), a.lat = ±1 (which way a side figure faces, one sign for every
// card, head included) and a.hands = {L: 'grip', R: 'open'} (a hand state: limbs.hand_L.states[state] = {side, front, back}).
// a.states = {segment: state} picks limbs[k].states[state] for any segment (e.g. a bent-knee card); a.hands names a hand's state
function cardsOf(k, sk, a) {
  if (a.cardIds?.[k]) { const id = a.cardIds[k]; return { side: id, front: id, back: id, threequarter: id }; }   // a host's chosen card for this pose
  if (!sk.states) return sk.cards;
  const m = k.match(/^(hand|mitt)_([LR])$/), st = a.states?.[k] || (m ? a.hands?.[m[2]] || 'open' : null);
  return st && sk.states[st] ? { ...sk.cards, ...sk.states[st] } : sk.cards;
}
function active(k, sk, a, port) {
  const f = a[SEG[k].face] || a.fwd, dot = (u, v) => u[0] * v[0] + u[1] * v[1] + u[2] * v[2];
  const d = dot(f, port.toward), lat = a.lat ?? dot(f, port.right);
  const want = a.views ? (k === 'head' ? a.views.head || a.views.body : a.views.body) : d > .55 ? 'front' : d < -.55 ? 'back' : 'side';
  const cards = cardsOf(k, sk, a);
  const order = { side: ['side', 'front', 'back'], front: ['front', 'side', 'back'], back: ['back', 'front', 'side'], threequarter: ['threequarter', 'front', 'side', 'back'] }[want];
  const v = order.find(v => cards[v] && S.byId[cards[v]]); if (!v) return null;
  const c = S.byId[cards[v]];
  // profile cards are drawn facing right unless marked: mirror across the A→B line when the body faces screen-left; a three-quarter
  // card is mirrored the same way when its facing is known (a declared fix.left, a library 'faces', or a boot's toe)
  const sided = v === 'side' || (v === 'threequarter' && (S.fix[c.id]?.left != null || c.faces || c.slot === 'foot'));
  const mir = sk.mirror !== (sided && (lat < 0) !== cardLeft(c));
  return { c, view: v, want, mir };
}

// ---------- placing a card ----------
// screen = P + R(ang)·(off + s·M·R(-ax)·(q − A)), M mirrors across the card's own A→B line
// sx: an optional shortening along the card's own A→B axis (a declared foreshortening, never below 0.88 by the 12% rule)
function mk(k, c, sk, Pp, ang, s, mir, sx = 1) {
  const { A, B } = pts(c, sk), ax = Math.atan2(B[1] - A[1], B[0] - A[0]), lab = Math.hypot(B[0] - A[0], B[1] - A[1]) || 1;
  return { k, c, sk, P: Pp, ang, s, mir, sx, A, B, ax, lab, off: [sk.dx * lab * s / 100, sk.dy * lab * s / 100] };
}
function fwd(x, q) { let u = rot([q[0] - x.A[0], q[1] - x.A[1]], -x.ax); u = [u[0] * x.s * (x.sx || 1) + x.off[0], u[1] * x.s * (x.mir ? -1 : 1) + x.off[1]]; u = rot(u, x.ang); return [x.P[0] + u[0], x.P[1] + u[1]]; }
function inv(x, p) { let u = rot([p[0] - x.P[0], p[1] - x.P[1]], -x.ang); u = [(u[0] - x.off[0]) / (x.s * (x.sx || 1)), (u[1] - x.off[1]) / x.s * (x.mir ? -1 : 1)]; u = rot(u, x.ax); return [u[0] + x.A[0], u[1] + x.A[1]]; }
function scaleOf(k, c, sk, j, pj, port, puppet) {
  const sg = SEG[k], { A, B } = pts(c, sk), lab = Math.hypot(B[0] - A[0], B[1] - A[1]) || 1;
  if (sk.mode === 'true') return port.k / ppcOf(c) * sk.scale;
  // rigid: a host may fix each card's scale once (S.cardPpc[id] = card px per cm), so pose edits never resize a card
  if (puppet && S.cardPpc?.[c.id]) return port.k / S.cardPpc[c.id] * sk.scale;
  // fit: pinned cards stretch to the bone as seen; puppet cards stay rigid at the bone's real 3D length
  return (puppet ? len3(v3(j[ji[sg.from]], j[ji[sg.to]])) * port.k : hyp(pj[ji[sg.from]], pj[ji[sg.to]])) / lab * sk.scale;
}
// where a child hangs on its parent: the parent's B when the child continues the chain, its A when they share a root,
// otherwise read off the parent card at the bind frame (and snapped to the nearest real brad on it)
function socket(k, px, port, puppet) {
  const sg = SEG[k], ps = SEG[px.k];
  const site = S.fix[px.c.id]?.sockets?.[sg.g];   // the contract names where this child hangs on that card (a drawn armhole)
  if (site) return { p: fwd(px, site), how: 'site' };
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
function ik2(S0, T, E, l1, l2, side) {
  const dx = T[0] - S0[0], dy = T[1] - S0[1], base = Math.atan2(dy, dx);
  const d = Math.max(Math.abs(l1 - l2) + 1e-3, Math.min(l1 + l2 - 1e-3, Math.hypot(dx, dy)));
  const a = Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))));
  return base + (side || (dx * (E[1] - S0[1]) - dy * (E[0] - S0[0]) >= 0 ? 1 : -1)) * a;
}
function roleOf(k, near) {
  const m = k.match(/^(.*)_([LR])$/); if (!m) return k;
  return (m[2] === (ARMS.test(m[1]) ? near.arm : near.leg) ? 'near_' : 'far_') + m[1];
}
// the whole figure for one frame in one view: a placed card per segment, with its gap to its parent and its miss to its target
function solve(fr, port, style = S.style, puppet = S.puppet) {
  let x0clamp = false;
  const j = joints(fr, S.actor); if (!j) return null;
  const a = fr.a[S.actor], pj = j.map(q => port.p(q)), segs = STYLES[style].segs, X = {};
  const near = { arm: pj[ji.shoulderL][2] > pj[ji.shoulderR][2] ? 'L' : 'R', leg: pj[ji.hipL][2] > pj[ji.hipR][2] ? 'L' : 'R' };
  for (const k of segs) {
    const sg = SEG[k], sk = S.skin[k]; if (!sk) continue;
    const ac = active(k, sk, a, port); if (!ac) continue;
    const Pp = pj[ji[sg.from]], Q = pj[ji[sg.to]], s = scaleOf(k, ac.c, sk, j, pj, port, puppet);
    let sx = a.sx?.[k] ?? 1;
    if (a.minLen?.[k]) { const { A: a0, B: b0 } = pts(ac.c, sk), drawn = Math.hypot(b0[0] - a0[0], b0[1] - a0[1]) * s * sx, want = a.minLen[k] * len3(v3(j[ji[sg.from]], j[ji[sg.to]])) * port.k;
      if (drawn < want) { sx = Math.min(2, sx * want / drawn); a.lenNote = (a.lenNote || []).concat(k); } }   // a shin never drawn shorter than 88% of its true length (a replacement card stretched back to it)
    const parent = sg.par.find(p => X[p]);
    const sock = parent ? socket(k, X[parent], port, puppet) : null;
    let start = puppet && sock ? sock.p : Pp, ang = Math.atan2(Q[1] - start[1], Q[0] - start[0]);
    if (k === 'head' && a.headLim != null) {   // the head looks the skeleton's way from its own neck (not from wherever the collar socket sits), rolled at most headLim off the drawn torso
      ang = Math.atan2(Q[1] - Pp[1], Q[0] - Pp[0]);
      if (a.headRef != null) {   // the painting decides: its own head axis (screen deg, clockwise from up); clamp only past 15 deg of it
        const ref = a.headRef * Math.PI / 180 - Math.PI / 2, rel = Math.atan2(Math.sin(ang - ref), Math.cos(ang - ref)), L = 15 * Math.PI / 180; if (Math.abs(rel) > L) ang = ref; }   // within 15 deg the solve's own tilt stands; beyond, the painting's angle
      else if (X.torso) { const rel = Math.atan2(Math.sin(ang - X.torso.ang), Math.cos(ang - X.torso.ang)), L = a.headLim * Math.PI / 180; if (Math.abs(rel) > L) ang = X.torso.ang + Math.sign(rel) * L; } }
    const low = puppet && !a.noik?.[k] && segs.find(q => SEG[q].ik === k && S.skin[q]);
    if (low) {
      const lc = active(low, S.skin[low], a, port);
      if (lc) { const { A, B } = pts(lc.c, S.skin[low]); const l2 = Math.hypot(B[0] - A[0], B[1] - A[1]) * scaleOf(low, lc.c, S.skin[low], j, pj, port, puppet) * (a.sx?.[low] ?? 1);
        const { A: a1, B: b1 } = pts(ac.c, sk); ang = ik2(start, pj[ji[SEG[low].to]], Q, Math.hypot(b1[0] - a1[0], b1[1] - a1[1]) * s * sx, l2, a.bend?.[k] ?? a.bend?.[k.slice(-1)]); }   // a.bend = {thigh_L: ±1} or {L: ±1}: the host fixes which way a folded limb bends on screen
    }
    if (k === 'torso' && a.torsoLim && X.pelvis) {   // the torso turns on the pelvis link, never as a free card: held within torsoLim of the pelvis
      const base = X.pelvis.ang + Math.PI; let rel = Math.atan2(Math.sin(ang - base), Math.cos(ang - base)); const L = a.torsoLim * Math.PI / 180;
      if (Math.abs(rel) > L) { ang = base + Math.sign(rel) * L; x0clamp = true; } }
    const x = mk(k, ac.c, sk, start, ang + sk.rot * Math.PI / 180, s, ac.mir, sx);
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
// fix[id].erase = [[x0,y0,x1,y1],...]: card-px rectangles made transparent (printed sheet labels);
// fix[id].trim = px: erode the card's alpha by that many px (a white cut fringe goes); done once per card on a canvas
const TRIM = {};
// fix[id].flare = [at A, at B]: the card's width (across its A->B axis, which must run down the card) scaled row by row, from the
// first factor at A's row to the second at B's (held beyond): a trouser leg keeps its painted cloth but its width at the knee
// can be matched to the next card's. The canvas is padded sideways; drawCard reads o.pad.
function flared(c, im, fl) {
  const w = im.naturalWidth || im.width, h = im.naturalHeight || im.height, { A, B } = AB(c);
  const mx = Math.max(fl[0], fl[1], 1), pad = Math.ceil(w * (mx - 1) / 2) + 2, o = P.canvas(w + 2 * pad, h), g = o.getContext('2d');
  for (let y = 0; y < h; y++) { const t = Math.max(0, Math.min(1, (y - A[1]) / ((B[1] - A[1]) || 1))), k = fl[0] + (fl[1] - fl[0]) * t, ax = A[0] + (B[0] - A[0]) * t;
    g.drawImage(im, 0, y, w, 1, pad + ax - ax * k, y, w * k, 1); }
  o.pad = pad; return o;
}
function trimmed(c) {
  const f = S.fix[c.id] || {}, fl = f.flare || S.autoFlare?.[c.id], r = Math.round(f.trim || 0), im = img(c);
  if ((!r && !f.erase && !fl) || !im.complete || !im.naturalWidth) return im;
  if (TRIM[c.id]) return TRIM[c.id];
  let o = im;
  if (r || f.erase) {
    const w = im.naturalWidth || im.width, h = im.naturalHeight || im.height; o = P.canvas(w, h); const g = o.getContext('2d'); g.drawImage(im, 0, 0);
    for (const [x0, y0, x1, y1] of f.erase || []) g.clearRect(x0, y0, x1 - x0, y1 - y0);
    if (r) { let d; try { d = g.getImageData(0, 0, w, h); } catch { d = null; }
      if (d) { const A = new Uint8Array(w * h); for (let i = 0; i < A.length; i++) A[i] = d.data[i * 4 + 3];
        const B = new Uint8Array(w * h);
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { let m = 255; for (let q = Math.max(0, x - r); q <= Math.min(w - 1, x + r) && m; q++) m = Math.min(m, A[y * w + q]); B[y * w + x] = m; }
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { let m = 255; for (let q = Math.max(0, y - r); q <= Math.min(h - 1, y + r) && m; q++) m = Math.min(m, B[q * w + x]); d.data[(y * w + x) * 4 + 3] = m; }
        g.putImageData(d, 0, 0); } }
    o.complete = true; o.naturalWidth = w;
  }
  if (fl) { o = flared(c, o, fl); o.complete = true; o.naturalWidth = o.width; }
  return TRIM[c.id] = o;
}
// a card's opaque bounding box [x0, y0, x1, y1] in card px (cached)
const ABOX = {};
function alphaBox(c) {
  if (ABOX[c.id] !== undefined) return ABOX[c.id];
  const im = img(c); if (!im.complete || !im.naturalWidth) return null;
  const w = c.w, h = c.h, o = P.canvas(w, h), g = o.getContext('2d'); g.drawImage(im, 0, 0, w, h); let d; try { d = g.getImageData(0, 0, w, h).data; } catch { return ABOX[c.id] = null; }
  let x0 = w, y0 = h, x1 = 0, y1 = 0; for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) if (d[(y * w + x) * 4 + 3] > 100) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return ABOX[c.id] = x1 > x0 ? [x0, y0, x1, y1] : null;
}
// a card's painted width (px) across its A->B axis at fraction u from A (alpha scan both ways from the axis)
const WIDTHS = {};
function widthAt(c, u) {
  const key = c.id + '|' + u; if (WIDTHS[key] != null) return WIDTHS[key];
  const im = img(c); if (!im.complete || !im.naturalWidth) return null;
  let d = WIDTHS[c.id + '|data']; const w = c.w, h = c.h;
  if (!d) { const o = P.canvas(w, h), g = o.getContext('2d'); g.drawImage(im, 0, 0, w, h); try { d = g.getImageData(0, 0, w, h).data; } catch { return null; } WIDTHS[c.id + '|data'] = d; }
  const { A, B } = AB(c), L = Math.hypot(B[0] - A[0], B[1] - A[1]) || 1, ux = (B[0] - A[0]) / L, uy = (B[1] - A[1]) / L, px = A[0] + ux * L * u, py = A[1] + uy * L * u;
  const solid = (x, y) => { x = Math.round(x); y = Math.round(y); return x >= 0 && y >= 0 && x < w && y < h && d[(y * w + x) * 4 + 3] > 100; };
  let n = 0; for (const sg of [1, -1]) { let t = 0; while (t < w + h && solid(px - uy * sg * t, py + ux * sg * t)) t++; n += t; }
  return WIDTHS[key] = n;
}
// where a held thing sits on a placed hand card: fix[id].hold (card px) when the contract gives it, else u along A→B
function holdPoint(x, u = .45) {
  const h = S.fix[x.c.id]?.hold; if (h) return fwd(x, h);
  const A = x.A, B = x.B; return fwd(x, [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u]);
}
// the neck holds: the head turns at most lim degrees off the torso (up/down and sideways); returns a new joint list and hfwd
function clampNeck(j, fwdv, hfwd, lim = 35) {
  const out = j.map(q => q.slice()), nb = j[ji.neckBase], tor = v3(j[0], nb), hd = v3(nb, j[ji.headTop]);
  const ang = (u, v) => Math.acos(Math.max(-1, Math.min(1, (u[0] * v[0] + u[1] * v[1] + u[2] * v[2]) / ((len3(u) * len3(v)) || 1))));
  const a = ang(tor, hd), L = lim * Math.PI / 180;
  if (a > L) {   // rotate the head points about the neck base, in the plane of the torso and head axes, back to lim
    const n = [tor[1] * hd[2] - tor[2] * hd[1], tor[2] * hd[0] - tor[0] * hd[2], tor[0] * hd[1] - tor[1] * hd[0]], nl = len3(n) || 1, k = n.map(v => v / nl), th = -(a - L);
    const R = p => { const c = Math.cos(th), s = Math.sin(th), d = k[0] * p[0] + k[1] * p[1] + k[2] * p[2], x = [k[1] * p[2] - k[2] * p[1], k[2] * p[0] - k[0] * p[2], k[0] * p[1] - k[1] * p[0]];
      return [0, 1, 2].map(i => p[i] * c + x[i] * s + k[i] * d * (1 - c)); };
    for (const nme of ['headBase', 'head', 'headTop', 'nose']) { const i = ji[nme], r = R(v3(nb, j[i])); out[i] = [nb[0] + r[0], nb[1] + r[1], nb[2] + r[2]]; }
  }
  // sideways: the head's facing within lim of the torso's
  const yf = Math.atan2(fwdv[0], fwdv[2]), yh = Math.atan2(hfwd[0], hfwd[2]); let dy = yh - yf; dy = Math.atan2(Math.sin(dy), Math.cos(dy));
  const cy = Math.max(-L, Math.min(L, dy)), hl = Math.hypot(hfwd[0], hfwd[2]);
  const h2 = Math.abs(dy) > L ? [Math.sin(yf + cy) * hl, hfwd[1], Math.cos(yf + cy) * hl] : hfwd.slice();
  return { j: out, hfwd: h2 };
}
function drawCard(g, x, alpha) {
  const im = trimmed(x.c); if (!im.complete || !im.naturalWidth) return;
  g.save(); g.globalAlpha = alpha;
  if (S.farShade && /^far_/.test(x.role || '')) g.filter = `brightness(${S.farShade})`;   // the far limbs a step darker: the legs read as two
  g.translate(x.P[0], x.P[1]); g.rotate(x.ang); g.translate(x.off[0], x.off[1]);
  g.scale(x.s * (x.sx || 1), x.s * (x.mir ? -1 : 1)); g.rotate(-x.ax);
  g.drawImage(im, -x.A[0] - (im.pad || 0), -x.A[1]);
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
// a profile seat built by code (no painted card shows the seat from the side): the outline of a man's seat and hip in profile,
// facing right (+x forward), in cm from the waist brad (y down); filled with the painted cloth of the rear-seat card (its cheek
// shading) and edged like the kit cards. A = waist brad, B = crotch line (the pelvis bone), a brad at the hip joint for the thighs.
function buildSeat(ch, srcId, o = {}) {
  const id = `gen.${ch}/built-seat-side`; if (S.byId[id]) return S.byId[id];
  const K = 8, m = 6, hip = o.hip_cm ?? 7, sh = hip - 7, out0 = o.outline || [[5, -3], [-9, -3], [-11.5, 1], [-14.5, 6], [-17.5, 11], [-18, 15.5], [-16.5, 19.5], [-13, 23], [-9, 25.5], [-4, 24.5], [5, 20]];
  const out = out0.map(p => [p[0], p[1] + (o.outline ? 0 : sh)]);   // the default outline is drawn for a hip joint 7 cm under the waist brad; moved with it
  const xs = out.map(p => p[0]), ys = out.map(p => p[1]), x0 = Math.min(...xs), y0 = Math.min(...ys);
  const W = Math.ceil((Math.max(...xs) - x0) * K + 2 * m), Hp = Math.ceil((Math.max(...ys) - y0) * K + 2 * m), Pt = p => [m + (p[0] - x0) * K, m + (p[1] - y0) * K];
  const brads = [[0, 0], [0, hip]], src = S.byId[srcId];
  const c = { id, gen: true, w: W, h: Hp, slot: 'pelvis', side: null, view: 'profile', character: ch, costume: 'built', px_per_cm: K,
    A: Pt([0, 0]), B: Pt([0, o.crotch_cm ?? 20]), pts: 'brads', q: 'A', label: 'built by code: profile seat', brads: brads.map(Pt), pal: src?.pal, skin: 0, img: '' };
  const paint = () => {
    const cv = P.canvas(W, Hp), g = cv.getContext('2d'), path = () => { const q = out.map(Pt), n = q.length, mid = i => { const a = q[i % n], b = q[(i + 1) % n]; return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; };   // a smooth outline through the points' midpoints
      g.beginPath(); g.moveTo(...mid(0)); for (let i = 1; i <= n; i++) g.quadraticCurveTo(...q[i % n], ...mid(i)); g.closePath(); };
    path(); g.save(); g.clip();
    const im = src && img(src);
    const th = S.byId[S.skin?.thigh_L?.cards?.side], ti = th && img(th);
    if (ti && ti.complete && ti.naturalWidth && !o.src_rect) {   // the profile trouser's own cloth (the thigh card's upper half, its folds and sheen): seat and thigh read as one garment
      const iw = ti.naturalWidth, ih = ti.naturalHeight; g.drawImage(ti, iw * .22, ih * .08, iw * .5, ih * .42, -m, -m, W + 2 * m, Hp + 2 * m);
    } else if (im && im.complete && im.naturalWidth) {   // one cheek of the rear seat (its right half), its outer curve to the back
      const iw = im.naturalWidth, ih = im.naturalHeight, sx = o.src_rect || [iw * .5, ih * .08, iw * .46, ih * .86];
      g.translate(W, 0); g.scale(-1, 1); g.drawImage(im, sx[0], sx[1], sx[2], sx[3], -m, 0, W + 2 * m, Hp); g.setTransform(1, 0, 0, 1, 0, 0);
    } else { g.fillStyle = '#1b1a1d'; g.fillRect(0, 0, W, Hp); if (im && im.addEventListener) im.addEventListener('load', paint, { once: true }); }
    const gr = g.createRadialGradient(...Pt([-6, 14]), 2, ...Pt([-6, 14]), 16 * K); gr.addColorStop(0, '#ffffff1c'); gr.addColorStop(.6, '#0000'); gr.addColorStop(1, '#0004'); g.fillStyle = gr; g.fillRect(0, 0, W, Hp);
    g.restore(); g.lineJoin = 'round'; path();
    g.lineWidth = 5; g.strokeStyle = '#c9a26b'; g.stroke(); g.lineWidth = 1; g.strokeStyle = '#6b4a2a'; g.stroke();
    for (const b of brads) { const q = Pt(b), rg = g.createRadialGradient(q[0] - 2, q[1] - 2, 1, q[0], q[1], 9); rg.addColorStop(0, '#fff3c0'); rg.addColorStop(.5, '#d9a640'); rg.addColorStop(1, '#7a5410'); g.fillStyle = rg; g.beginPath(); g.arc(q[0], q[1], 8, 0, 7); g.fill(); }
    IMG[id] = cv; cv.complete = true; cv.naturalWidth = W;
  };
  paint(); S.lib.push(c); S.byId[id] = c;
  return c;
}
// the trouser top for front, back and three-quarter views, built by code: waist to below the hip joints, as wide as the thigh roots, so
// the jacket hem, the hips and both thigh tops read as one piece of cloth (no gap at the hip seam). Filled with the costume's own
// cloth: the rear-seat card (pockets, seat seam) for the back, the hip bridge's cloth for the front. A = waist brad, B = crotch line,
// brads on the hip joints. Geometry from the skeleton: drop = waist to hip line, hh = half the hip span (cm).
function buildHips(ch, view, srcId, o) {
  const id = `gen.${ch}/built-hips-${view}`; if (S.byId[id] && !o.rebuild) return S.byId[id];
  S.lib = S.lib.filter(c => c.id !== id); delete IMG[id]; delete TRIM[id];
  const K = 8, m = 6, d = o.drop, hh = o.hh, out = [[-(hh + 2), -3], [hh + 2, -3], [hh + 3, d * .55], [hh + 3, d + 1], [hh + 1.5, d + 4], [2.5, d + 4], [0, d + 2.5], [-2.5, d + 4], [-(hh + 1.5), d + 4], [-(hh + 3), d + 1], [-(hh + 3), d * .55]];   // inside the thigh roots' outline: no lobes past the legs
  const xs = out.map(p => p[0]), ys = out.map(p => p[1]), x0 = Math.min(...xs), y0 = Math.min(...ys);
  const W = Math.ceil((Math.max(...xs) - x0) * K + 2 * m), Hp = Math.ceil((Math.max(...ys) - y0) * K + 2 * m), Pt = p => [m + (p[0] - x0) * K, m + (p[1] - y0) * K];
  const brads = [[0, 0], [hh, d], [-hh, d]], src = S.byId[srcId];
  const c = { id, gen: true, w: W, h: Hp, slot: 'pelvis', side: null, view, character: ch, costume: 'built', px_per_cm: K,
    A: Pt([0, 0]), B: Pt([0, 20]), pts: 'brads', q: 'A', label: 'built by code: trouser top (' + view + ')', brads: brads.map(Pt), pal: src?.pal, skin: 0, img: '' };
  const paint = () => {
    const cv = P.canvas(W, Hp), g = cv.getContext('2d'), q = out.map(Pt), n = q.length, mid = i => { const a = q[i % n], b = q[(i + 1) % n]; return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; };
    const path = () => { g.beginPath(); g.moveTo(...mid(0)); for (let i = 1; i <= n; i++) g.quadraticCurveTo(...q[i % n], ...mid(i)); g.closePath(); };
    path(); g.save(); g.clip();
    const im = src && img(src);
    if (im && im.complete && im.naturalWidth) { const iw = im.naturalWidth, ih = im.naturalHeight;
      if (view === 'back') g.drawImage(im, iw * .05, ih * .02, iw * .9, ih * .62, 0, 0, W, Hp);      // the rear seat: waistband, pockets, the seat seam
      else { const sw = iw * .3, sh = ih * .3; for (let y = 0; y < Hp; y += sh) for (let x = 0; x < W; x += sw) g.drawImage(im, iw * .35, ih * .3, sw, sh, x, y, sw, sh); } }
    else { g.fillStyle = '#1b1a1d'; g.fillRect(0, 0, W, Hp); }
    const gr = g.createLinearGradient(0, 0, W, 0); gr.addColorStop(0, '#0006'); gr.addColorStop(.5, '#0000'); gr.addColorStop(1, '#0006'); g.fillStyle = gr; g.fillRect(0, 0, W, Hp);
    g.restore(); g.lineJoin = 'round'; path(); g.lineWidth = 5; g.strokeStyle = '#c9a26b'; g.stroke(); g.lineWidth = 1; g.strokeStyle = '#6b4a2a'; g.stroke();
    for (const b of brads) { const p = Pt(b), rg = g.createRadialGradient(p[0] - 2, p[1] - 2, 1, p[0], p[1], 9); rg.addColorStop(0, '#fff3c0'); rg.addColorStop(.5, '#d9a640'); rg.addColorStop(1, '#7a5410'); g.fillStyle = rg; g.beginPath(); g.arc(p[0], p[1], 8, 0, 7); g.fill(); }
    IMG[id] = cv; cv.complete = true; cv.naturalWidth = W;
  };
  paint(); S.lib.push(c); S.byId[id] = c; return c;
}
// cards a skin names by id that are built by code: rebuild them (index.html does this at boot)
function rebuildGen(skin) {
  for (const k in skin) for (const id of Object.values(skin[k].cards || {})) if (id.startsWith('gen.')) {
    const m = id.match(/^gen\.(.+)\/built-(torso|hip)-(\w+)$/); if (m) buildCard(m[2] === 'hip' ? 'pelvis' : 'torso', m[3], m[1]);
    const ms = id.match(/^gen\.(.+)\/built-seat-side$/); if (ms) buildSeat(ms[1], S.fix[id]?.from, S.fix[id] || {});
  }
}
function stick(g, pj, col, w) {
  g.strokeStyle = col; g.lineWidth = w; g.lineCap = 'round';
  for (const [a, b] of STICK) { const p = pj[ji[a]], q = pj[ji[b]]; g.beginPath(); g.moveTo(p[0], p[1]); g.lineTo(q[0], q[1]); g.stroke(); }
}


// =====================================================================================================================
// renderPose: one general renderer, any pose through the same puppet (see the API contract at the top of this file)
// =====================================================================================================================
const RP = { contract: null, ready: false, key: null, bind: {}, statureCm: null, headCm: null };
const POSELAB = { pelvis: 'pelvis', hipL: 'hipL', hipR: 'hipR', knL: 'kneeL', knR: 'kneeR', anL: 'ankleL', anR: 'ankleR', heelL: 'heelL', heelR: 'heelR',
  ballL: 'ballL', ballR: 'ballR', toeL: 'toeL', toeR: 'toeR', waist: 'spineMid', chest: 'chest', neck: 'neckBase', shL: 'shoulderL', shR: 'shoulderR',
  elL: 'elbowL', elR: 'elbowR', wrL: 'wristL', wrR: 'wristR', headC: 'head', top: 'headTop' };
// Pose Lab fk() output (X = his left, Y = down, Z = forward) -> renderPose joints (x = his left, y = up, z = forward)
function fromPoseLab(J) {
  const o = {}, c = q => [q[0], -q[1], q[2]];
  for (const [a, b] of Object.entries(POSELAB)) if (J[a]) o[b] = c(J[a]);
  if (J.tipL) o.tipL = c(J.tipL); if (J.tipR) o.tipR = c(J.tipR);
  if (J.neck && J.top) o.headBase = c(J.neck.map((v, i) => v + (J.top[i] - v) * .12));
  // pose-core matrices are flat row-major arrays: the head's forward (its z column) is [R[2], R[5], R[8]]
  const Rh = J._F?.Rh; if (Rh && J.headC) { const f = [Rh[2], Rh[5], Rh[8]], l = Math.hypot(...f) || 1; o.nose = c(J.headC.map((v, i) => v + f[i] / l * 10)); }
  // the Pose Lab waist is the jacket hem (19 cm above the hip line); the puppet hangs its torso card from 7 cm above its pelvis
  // joint, so that joint is put 7 cm under the Pose Lab waist: the torso card spans the painted hem -> neck (the thighs still
  // hang from the true hip joints)
  if (J.waist && J.pelvis) { const u = J.waist.map((v, i) => v - J.pelvis[i]), lu = Math.hypot(...u) || 1; o.pelvis = c(J.waist.map((v, i) => v - u[i] / lu * 7)); }
  return o;
}
function applyContract(c) {
  S.style = c.style || 'hips'; S.fix = c.fix || {}; index();
  S.skin = {}; for (const [k, l] of Object.entries(c.limbs || {})) S.skin[k] = { ...newSkin(), ...l, cards: { ...(l.cards || {}) } };
  const st = c.stack || {}; S.stack = Object.fromEntries(VIEWS.map(v => [v, (st[v]?.length ? st[v] : v === 'threequarter' && st.front?.length ? st.front : STACK0).slice()]));
  S.K = {}; S.sock = {}; S.cardPpc = null; S.pv++;
  RP.base = Object.fromEntries(Object.entries(S.skin).map(([k, sk]) => [k, { ...sk.cards }]));   // the contract's own cards: the scale reference
}
const loaded = im => new Promise(r => { if (!im || im.complete && im.naturalWidth) return r(); const t = setTimeout(r, 15000); im.addEventListener?.('load', () => { clearTimeout(t); r(); }); im.addEventListener?.('error', () => { clearTimeout(t); r(); }); });
// prepare({contract, library, imgBase}) → Promise: indexes the library, applies the contract, loads every card it names, builds code cards
async function prepare(o) {
  if (o.library) { S.lib = o.library.filter(c => !c.gen); RP.library = o.library; }
  if (o.imgBase != null) P.imgBase = o.imgBase;
  applyContract(o.contract);
  const ids = new Set();
  for (const sk of Object.values(S.skin)) { for (const id of Object.values(sk.cards)) ids.add(id); for (const st of Object.values(sk.states || {})) for (const id of Object.values(st)) ids.add(id); }
  for (const [id, f] of Object.entries(S.fix)) if (id.startsWith('gen.') && f.from) ids.add(f.from);
  await Promise.all([...ids].map(id => S.byId[id] && !S.byId[id].gen ? loaded(img(S.byId[id])) : null));
  if (o.harvest) await Promise.all(o.harvest.filter(c => !c.bad).map(c => { if (!S.byId[c.id]) { S.lib.push(c); S.byId[c.id] = c; } return loaded(img(c)); }));   // replacement cards ready to draw
  rebuildGen(S.skin);
  RP.contract = o.contract; RP.ready = true; RP.key = null; RP.bind = {};
  return { cards: ids.size, missing: [...ids].filter(id => !S.byId[id]) };
}
const ORDER26 = J;
function jointArray(o, warn) {
  const g = n => o[n], j = [];
  for (const n of ORDER26) {
    let q = g(n);
    if (!q && /^(heel|ball|toe)[LR]$/.test(n)) { const s = n.slice(-1), an = g('ankle' + s), kn = g('knee' + s); if (an) { const f = [0, 0, 1]; const d = n.startsWith('heel') ? -5 : n.startsWith('ball') ? 14 : 19; q = [an[0] + f[0] * d, Math.max(0, an[1] - 9), an[2] + f[2] * d]; } }
    if (!q && n === 'spineMid') { const p = g('pelvis'), nb = g('neckBase'); if (p && nb) q = p.map((v, i) => v + (nb[i] - v) * .33); }
    if (!q && n === 'chest') { const p = g('pelvis'), nb = g('neckBase'); if (p && nb) q = p.map((v, i) => v + (nb[i] - v) * .7); }
    if (!q && n === 'headBase') { const nb = g('neckBase'), t = g('headTop'); if (nb && t) q = nb.map((v, i) => v + (t[i] - v) * .12); }
    if (!q && n === 'head') { const nb = g('neckBase'), t = g('headTop'); if (nb && t) q = nb.map((v, i) => v + (t[i] - v) * .55); }
    if (!q && n === 'nose') { const h = g('head') || j[ji.head]; if (h) q = [h[0], h[1] - 2, h[2] + 10]; }
    if (!q) { warn.push('missing joint ' + n); q = [0, 0, 0]; }
    j.push(q.slice());
  }
  return j;
}
const nrm3 = v => { const l = len3(v) || 1; return v.map(x => x / l); };
function rotAB3(a, b, v) {   // v turned by the rotation that takes unit a to unit b
  const k = cross3(a, b), sn = len3(k), cs = dot3(a, b); if (sn < 1e-6) return v.slice();
  const u = k.map(x => x / sn), d = dot3(u, v), x = cross3(u, v); return [0, 1, 2].map(i => v[i] * cs + x[i] * sn + u[i] * d * (1 - cs));
}
const cross3 = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
function facings(j) {   // body frame x = his left, y = up: forward = left x up
  const pf = nrm3(cross3(v3(j[ji.hipR], j[ji.hipL]), v3(j[0], j[ji.spineMid]))), tf = nrm3(cross3(v3(j[ji.shoulderR], j[ji.shoulderL]), v3(j[ji.spineMid], j[ji.neckBase])));
  const hf = nrm3(v3(j[ji.head], j[ji.nose]));
  return { fwd: tf, pfwd: pf, hfwd: hf };
}
// a neutral standing pose with this skeleton's own bone lengths, facing +z: sockets are bound and card scales fixed on it
function neutralOf(j) {
  const d = (a, b) => len3(v3(j[ji[a]], j[ji[b]])), av = (a, b) => (d(a + 'L', b + 'L') + d(a + 'R', b + 'R')) / 2;
  const ankH = Math.min(12, Math.max(6, .72 * (d('ankleL', 'heelL') + d('ankleR', 'heelR')) / 2 || 9));   // from the skeleton, not the pose: the bind pose stays one per skeleton
  const footL = av('heel', 'toe') || 26, th = av('hip', 'knee'), sh = av('knee', 'ankle'), hy = ankH + th + sh, hh = d('hipL', 'hipR') / 2;
  const n = {}; n.pelvis = [0, hy, 0];
  for (const [s, x] of [['L', 1], ['R', -1]]) {
    n['hip' + s] = [x * hh, hy, 0]; n['knee' + s] = [x * hh, hy - th, 0]; n['ankle' + s] = [x * hh, ankH, 0];
    n['heel' + s] = [x * hh, 0, -.25 * footL]; n['ball' + s] = [x * hh, 0, .5 * footL]; n['toe' + s] = [x * hh, 0, .75 * footL];
  }
  n.spineMid = [0, hy + d('pelvis', 'spineMid'), 0]; n.chest = [0, n.spineMid[1] + d('spineMid', 'chest'), 0]; n.neckBase = [0, n.chest[1] + d('chest', 'neckBase'), 0];
  const shl = (d('neckBase', 'shoulderL') + d('neckBase', 'shoulderR')) / 2, sw = d('shoulderL', 'shoulderR') / 2, sdrop = Math.sqrt(Math.max(0, shl * shl - sw * sw));
  for (const [s, x] of [['L', 1], ['R', -1]]) {
    n['shoulder' + s] = [x * sw, n.neckBase[1] - sdrop, 0]; n['elbow' + s] = [x * (sw + 2), n['shoulder' + s][1] - av('shoulder', 'elbow'), -1];
    n['wrist' + s] = [x * (sw + 3), n['elbow' + s][1] - av('elbow', 'wrist'), 1];
  }
  n.headBase = [0, n.neckBase[1] + d('neckBase', 'headBase'), 0]; n.head = [0, n.headBase[1] + d('headBase', 'head'), 0]; n.headTop = [0, n.head[1] + d('head', 'headTop'), 0];
  n.nose = [0, n.head[1] - 2, Math.max(8, d('head', 'nose'))];
  return ORDER26.map(k => n[k]);
}
const rotYv = (v, t) => [v[0] * Math.cos(t) + v[2] * Math.sin(t), v[1], -v[0] * Math.sin(t) + v[2] * Math.cos(t)];
function frameOf(j, f, extra) { return { a: { A: { j, fwd: f.fwd, hfwd: f.hfwd, pfwd: f.pfwd, ...extra } } }; }
// the yaw of the camera: view + facing (or psi, the Pose Lab's view yaw: +90 = profile facing screen-right)
function yawOf(o) {
  if (o.psi != null) return -o.psi;
  const r = (o.facing || 'right') !== 'left';
  return { front: 0, back: 180, side: r ? -90 : 90, profile: r ? -90 : 90, threequarter: r ? -45 : 45, threequarter_back: r ? -135 : 135 }[o.view || 'side'] ?? 0;
}
function cardViewOf(yaw) { const a = Math.abs((((yaw + 180) % 360) + 360) % 360 - 180); return a <= 22.5 ? 'front' : a <= 67.5 ? 'threequarter' : a >= 112.5 ? 'back' : 'side'; }
function paintedH(c) {
  const im = img(c); if (!im || !(im.naturalWidth || im.width)) return null;
  const w = c.w, h = c.h, o = P.canvas(w, h), g = o.getContext('2d'); g.drawImage(im, 0, 0, w, h);
  let d; try { d = g.getImageData(0, 0, w, h).data; } catch { return null; }
  let y0 = h, y1 = 0; for (let y = 0; y < h; y++) for (let x = 0; x < w; x += 2) if (d[(y * w + x) * 4 + 3] > 128) { if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return y1 - y0;
}
// one scale per card for every pose: its A→B length over its bone in the neutral pose; heads one painted height in every view
function rigidScalesFor(nj, headCm) {
  const fr = frameOf(nj, { fwd: [0, 0, 1], hfwd: [0, 0, 1], pfwd: [0, 0, 1] }), j = joints(fr, 'A'), out = {};
  const bone = k => len3(v3(j[ji[SEG[k].from]], j[ji[SEG[k].to]]));
  for (const [k, sk] of Object.entries(S.skin)) { if (!SEG[k]) continue;
    for (const id of new Set([...Object.values(sk.cards), ...Object.values(sk.states || {}).flatMap(o => Object.values(o))])) { const c = S.byId[id]; if (!c) continue; const { A, B } = pts(c, sk); out[id] = Math.hypot(B[0] - A[0], B[1] - A[1]) / bone(k); } }
  const hk = S.skin.head; let hcm = headCm;
  if (hk) { const side = S.byId[hk.cards.side]; if (!hcm && side && out[side.id]) { const h = paintedH(side); if (h) hcm = h / out[side.id]; }
    if (hcm) for (const id of Object.values(hk.cards)) { const c = S.byId[id], h = c && paintedH(c); if (h) out[id] = h / hcm; } }
  for (const id in out) if (S.fix[id]?.rigid_ppc && S.fix[id].px_per_cm) out[id] = S.fix[id].px_per_cm;
  return { ppc: out, headCm: hcm };
}
// a harvested replacement card (Builder A's library_harvest.json: library fields + view, facing, dir_cam = the bone's unit direction in
// camera space [screen x, screen y down, toward the camera], ratio, bad): same part and side, same card view, the closest bone direction
function harvestFor(H, kk, view, jj, sg, port, exclude) {
  if (!H || !H.length) return null;
  const m = kk.match(/^(.*)_([LR])$/), d = nrm3(v3(jj[ji[sg.from]], jj[ji[sg.to]])), cam = [dot3(d, port.right), -d[1], dot3(d, port.toward)];
  let best = null;
  for (const c of H) {
    if (c.bad || (c.slot || c.part) !== m[1] || (c.side && c.side !== m[2]) || !c.dir_cam) continue;
    if (VIEWOF(c.view) !== VIEWOF(view) && !(view === 'threequarter' && c.view === 'threequarter')) continue;
    if (exclude && (typeof exclude === 'function' ? exclude(c) : [].concat(exclude).some(e => e === c.source || e === c.pose || (c.id || '').includes(e)))) continue;   // leave-one-out: an id, a list, or a predicate on the card
    const cs = dot3(nrm3(c.dir_cam), cam); if (cs > .94 && (!best || cs > best.cos)) best = { c, cos: cs };
  }
  if (!best) return null;
  const im = img(best.c); if (!(im.complete && im.naturalWidth)) return null;   // not loaded (pass harvest to prepare() to preload): fall back
  if (!S.byId[best.c.id]) { S.lib.push(best.c); S.byId[best.c.id] = best.c; if (best.c.facing && !best.c.faces) best.c.faces = best.c.facing === 'left' ? 'L' : 'R'; }
  return best;
}
// the painting's own head axis, screen deg clockwise from up: o.paintedHeadDeg, or from o.target (a Pose Lab target): its neck and
// head markers when both are confident (>= .4). Uniform scale and offset (the host's registration) do not change the angle.
function paintedHead(o) {
  if (o.paintedHeadDeg != null) return o.paintedHeadDeg;
  const mk = o.target?.markers, c = n => mk?.[n] ? (mk[n][4] ?? 1) : 0, ang = (a, b) => Math.atan2(b[0] - a[0], -(b[1] - a[1])) * 180 / Math.PI;
  if (!(c('head') >= .4 && (c('neck') >= .4 || (c('head') >= .5 && c('neck') >= .25)))) return null;   // a confident head marker carries a weaker neck
  const nh = Math.hypot(mk.head[0] - mk.neck[0], mk.head[1] - mk.neck[1]);
  if (c('shoulderL') >= .4 && c('shoulderR') >= .4 && nh < .62 * Math.hypot(mk.shoulderL[0] - mk.shoulderR[0], mk.shoulderL[1] - mk.shoulderR[1])) return null;   // a head the painting bows toward us: its marker axis is not its tilt
  let a = ang(mk.neck, mk.head);
  // the head marker rides the hair and the face turn: the painted head axis is held within 30 deg of the painted torso (groin -> neck)
  if (c('groin') >= .35) { const t = ang(mk.groin, mk.neck); let d = a - t; while (d > 180) d -= 360; while (d < -180) d += 360; if (Math.abs(d) > 30) a = t + Math.sign(d) * 30; }
  return a;
}
const VERDICT = r => r >= .88 ? 'rotate' : r >= .55 ? 'replace/shorten' : 'dedicated/restage';
const LIMB = /^(upper_arm|forearm|thigh|shin)_[LR]$/;

// adjustJoints(joints3d, o): every move this renderer makes to the joints themselves, before any card is chosen, so a host that picks
// cards (harvested chains) from joints picks them from the moved ones. Takes what renderPose takes (named joints, a Pose Lab fk()
// result, a frame record {j}; and o.port | o.psi | o.view+o.facing; o.target; o.ground; o.neckDeg; o.headLeanDeg; o.paintedHeadDeg).
// Call adjustJoints(joints3d, opts) or adjustJoints(renderPoseArgs). Returns {adjusted: true, j: [26 Bolas joints, cm, x his left,
// y up, z forward], tips: {L, R} | null, named = joints3d: {name: [x,y,z]} (also tipL/tipR), yaw, moves: [what moved and why], warnings}. Pass the result back as renderPose's joints3d: it is used as is.
// The moves: a head bowed toward the camera turned into the picture plane; the neck clamp; without a painted head axis, the head's
// lean across the screen held to headLeanDeg; the hand bent at most 80 deg off the forearm; a hand the painting holds at the head
// brought to it, the elbow re-solved in 3D with the arm's own bone lengths (so the arm cards reach the moved hand).
function adjustJoints(joints3d, o) {
  if (o === undefined && joints3d && joints3d.joints3d !== undefined) { o = joints3d; joints3d = o.joints3d; }   // also adjustJoints(renderPoseArgs)
  o = o || {}; const warnings = [], moves = [];
  let src = joints3d || {}, tips = null;
  let j;
  if (Array.isArray(src.j)) j = src.j.map((q, i) => q ? q.slice() : (warnings.push('missing joint ' + J[i]), [0, 0, 0])).slice(0, 26);   // a frame record {j: 26 Bolas joints}
  else { if (src.shL || src.knL) src = fromPoseLab(src); j = jointArray(src, warnings); if (src.tipL && src.tipR) tips = { L: src.tipL.slice(), R: src.tipR.slice() }; }
  if (o.ground ?? !o.port) { const lo = Math.min(...FEET.map(i => j[i][1])); j = j.map(q => [q[0], q[1] - lo, q[2]]); if (tips) for (const s of 'LR') tips[s][1] -= lo; }
  const yaw = o.port ? Math.atan2(-o.port.right[2], o.port.right[0]) * 180 / Math.PI : yawOf(o), view = o.cardView || cardViewOf(yaw), cy = Math.cos(yaw * Math.PI / 180), sy = Math.sin(yaw * Math.PI / 180);
  const port = { toward: [sy, 0, cy], right: [cy, 0, -sy] };
  // the head is a painted card: it is drawn in the picture plane at full size, so a head bowed toward (or away from) the camera is
  // turned into the plane about the neck, keeping its lean across the screen, and held within the neck's reach of the torso
  { const nb = j[ji.neckBase], uh = v3(nb, j[ji.headTop]), L = len3(uh), tw = port.toward, along = dot3(uh, tw) / (L || 1);
    if (Math.abs(along) > .45) { const inPl = nrm3(uh.map((x, i) => x - along * L * tw[i])), ut = nrm3(v3(j[ji.spineMid], nb)), w = Math.min(1, len3(uh.map((x, i) => x - along * L * tw[i])) / L / .45);
      const tgt = nrm3(inPl.map((x, i) => x * w + ut[i] * (1 - w)));
      for (const n of ['headBase', 'head', 'headTop', 'nose']) { const r = rotAB3(nrm3(uh), tgt, v3(nb, j[ji[n]])); j[ji[n]] = nb.map((x, i) => x + r[i]); }
      moves.push(`head: bowed ${(Math.asin(Math.min(1, Math.abs(along))) * 180 / Math.PI) | 0} deg toward the camera; turned into the picture plane (a painted head cannot foreshorten)`); }
    const F0 = facings(j), cn = clampNeck(j, F0.fwd, F0.hfwd, o.neckDeg ?? (Math.abs(along) > .45 ? 20 : 40)); j = cn.j; }
  // a painted head is drawn nearly upright on its collar: across the screen it leans at most headLeanDeg off the torso (front, back, 3/4)
  if (view !== 'side' && paintedHead(o) == null) { const lim = (o.headLeanDeg ?? 10) * Math.PI / 180, up = [0, 1, 0], nb = j[ji.neckBase];
    const sa = v => Math.atan2(dot3(v, port.right), dot3(v, up)), dt = sa(v3(j[ji.spineMid], nb)), dh = sa(v3(nb, j[ji.headTop]));
    let df = Math.atan2(Math.sin(dh - dt), Math.cos(dh - dt));
    if (Math.abs(df) > lim) { const th = (Math.abs(df) - lim) * Math.sign(df), ax = port.toward, c = Math.cos(th), sn = Math.sin(th);
      const R = v => { const d = dot3(ax, v), x = cross3(ax, v); return [0, 1, 2].map(i => v[i] * c + x[i] * sn + ax[i] * d * (1 - c)); };
      const test = R(v3(nb, j[ji.headTop])), sgn = Math.abs(Math.atan2(Math.sin(sa(test) - dt), Math.cos(sa(test) - dt))) < Math.abs(df) ? 1 : -1;
      const R2 = v => { const t2 = th * sgn, c2 = Math.cos(t2), s2 = Math.sin(t2), d = dot3(ax, v), x = cross3(ax, v); return [0, 1, 2].map(i => v[i] * c2 + x[i] * s2 + ax[i] * d * (1 - c2)); };
      for (const n of ['headBase', 'head', 'headTop', 'nose']) { const r = R2(v3(nb, j[ji[n]])); j[ji[n]] = nb.map((x, i) => x + r[i]); }
      moves.push(`head: leaned ${(Math.abs(df) * 180 / Math.PI) | 0} deg off the torso across the screen; held to ${(lim * 180 / Math.PI) | 0}`); } }
  if (tips) {   // the hand follows the solve's wrist, bent at most 80 deg off the forearm (a cut-out wrist past 90 reads as broken)
    for (const s of 'LR') { const w = j[ji['wrist' + s]], fa = nrm3(v3(j[ji['elbow' + s]], w)), h = v3(w, tips[s]), hl = len3(h) || 1, c = dot3(fa, h) / hl;
      if (c < Math.cos(80 * Math.PI / 180)) { const t = nrm3(h.map((x, i) => x / hl - c * fa[i])), m = 80 * Math.PI / 180, d = fa.map((x, i) => (x * Math.cos(m) + t[i] * Math.sin(m)) * hl);
        tips[s] = w.map((x, i) => x + d[i]); moves.push(`hand_${s}: wrist bend held to 80 deg`); } } }
  // a hand the painting puts at the head (its wrist within 1.6 neck->head lengths of the head marker, between the neck and the top of
  // the head, raised from an elbow below the shoulder) is brought to the drawn head, the elbow re-solved with the arm's own lengths
  { const mk = o.target?.markers, ok = n => mk?.[n] && (mk[n][4] ?? 1) >= .4;
    if (ok('neck') && ok('head')) { const nh = Math.hypot(mk.head[0] - mk.neck[0], mk.head[1] - mk.neck[1]), hc = j[ji.head];
      for (const sd of ['L', 'R']) { if (!ok('wrist' + sd) || !ok('elbow' + sd) || !ok('shoulder' + sd) || Math.hypot(mk['wrist' + sd][0] - mk.head[0], mk['wrist' + sd][1] - mk.head[1]) > 1.6 * nh) continue;
        const wy = mk['wrist' + sd][1]; if (!(wy > mk.head[1] && wy < mk.neck[1] && mk['elbow' + sd][1] > mk['shoulder' + sd][1] + .2 * nh)) continue;
        const sh = j[ji['shoulder' + sd]], el = j[ji['elbow' + sd]], w = j[ji['wrist' + sd]], l1 = len3(v3(sh, el)), l2 = len3(v3(el, w));
        const d = v3(hc, w), dl = len3(d), want = 20; if (dl <= want || dl > 70) continue;
        let nw = hc.map((v, i) => v + d[i] / dl * want); const sw = v3(sh, nw), swl = len3(sw);
        if (swl > l1 + l2 - .5) nw = sh.map((v, i) => v + sw[i] / swl * (l1 + l2 - .5));   // within the arm's reach
        const D = len3(v3(sh, nw)), u = nrm3(v3(sh, nw)), a1 = Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D))));
        const pole = v3(sh, el), pp = nrm3(pole.map((x, i) => x - dot3(pole, u) * u[i])), ne = sh.map((v, i) => v + (u[i] * Math.cos(a1) + pp[i] * Math.sin(a1)) * l1);   // the elbow keeps its side
        const mv = v3(w, nw); j[ji['elbow' + sd]] = ne; j[ji['wrist' + sd]] = nw; if (tips?.[sd]) tips[sd] = tips[sd].map((v, i) => v + mv[i]);
        moves.push(`hand_${sd}: brought ${(dl - want).toFixed(0)} cm to the head, elbow re-solved (the painting holds the hand there)`); } } }
  // an arm the painting holds straight (its shoulder-elbow-wrist markers open to more than 145 deg, elbow marker conf >= .3) is drawn
  // straight: elbow and wrist laid along the solve's shoulder->wrist line at the arm's own length, the hand carried with the wrist
  const straight = {};
  { const mk = o.target?.markers, c = n => mk?.[n] ? (mk[n][4] ?? 1) : 0;
    for (const sd of ['L', 'R']) { if (c('shoulder' + sd) < .4 || c('wrist' + sd) < .4 || c('elbow' + sd) < .3) continue;
      const S0 = mk['shoulder' + sd], E = mk['elbow' + sd], W = mk['wrist' + sd], u = [S0[0] - E[0], S0[1] - E[1]], v = [W[0] - E[0], W[1] - E[1]];
      const angd = Math.acos(Math.max(-1, Math.min(1, (u[0] * v[0] + u[1] * v[1]) / ((Math.hypot(...u) * Math.hypot(...v)) || 1)))) * 180 / Math.PI;
      if (angd < 145) continue;
      const sh = j[ji['shoulder' + sd]], el = j[ji['elbow' + sd]], w = j[ji['wrist' + sd]], l1 = len3(v3(sh, el)), l2 = len3(v3(el, w)), dir = nrm3(v3(sh, w));
      const flex = Math.acos(Math.max(-1, Math.min(1, dot3(nrm3(v3(el, sh)), nrm3(v3(el, w)))))) * 180 / Math.PI;
      const ne = sh.map((x, i) => x + dir[i] * l1), nw = sh.map((x, i) => x + dir[i] * (l1 + l2)), mv = v3(w, nw);
      j[ji['elbow' + sd]] = ne; j[ji['wrist' + sd]] = nw; if (tips?.[sd]) tips[sd] = tips[sd].map((x, i) => x + mv[i]); straight[sd] = true;
      moves.push(`arm_${sd}: straightened (painted ${angd | 0} deg, the solve had ${flex | 0} deg)`); } }
  const named = Object.fromEntries(J.map((n, i) => [n, j[i].slice()])); if (tips) { named.tipL = tips.L.slice(); named.tipR = tips.R.slice(); }
  return { adjusted: true, j, tips, named, joints3d: named, yaw, straight, moves, warnings: warnings.concat(moves) };
}
function renderPose(ctx, o) {
  const warnings = [];
  if (o.contract && o.contract !== RP.contract) {   // not prepared for this contract: apply it now (images the host has not loaded yet draw blank)
    if (o.library && o.library !== RP.library) { S.lib = o.library.filter(c => !c.gen); RP.library = o.library; }
    applyContract(o.contract); rebuildGen(S.skin); RP.contract = o.contract; RP.ready = true; RP.key = null; RP.bind = {};
  }
  if (!RP.ready) return { cards: [], segments: [], warnings: ['no contract: pass o.contract or await PuppetCore.prepare({contract, library})'] };
  const AJ = o.joints3d?.adjusted ? o.joints3d : adjustJoints(o.joints3d, o);   // every joint move happens before any card is chosen
  let j = AJ.j.map(q => q.slice()); const tips = AJ.tips ? { L: AJ.tips.L.slice(), R: AJ.tips.R.slice() } : null; warnings.push(...AJ.warnings);
  const yaw = AJ.yaw, view = o.cardView || cardViewOf(yaw), cy = Math.cos(yaw * Math.PI / 180), sy = Math.sin(yaw * Math.PI / 180);
  // the skeleton's own bone lengths fix the card scales and the bind pose (recomputed only when they change); heads drawn at the
  // painted canon (o.headScale, default 1.05: top of hair to chin is 0.152 of his height in 7 standing paintings; 0.145 at 1.0)
  const hs = o.headScale ?? 1.05, nj = neutralOf(j), key = nj.map(q => q.map(v => Math.round(v)).join(',')).join(';') + '|' + hs + '|' + (o.headCm || '');
  if (RP.key == null || (o.rescale && key !== RP.key)) {   // card scales are fixed once per contract (one scale per card for every pose); o.rescale re-fits them to a new skeleton
    // the code-built seat sits on this skeleton's hip line: its hip brad as far under the waist brad as the hips are
    const nfr = frameOf(nj, { fwd: [0, 0, 1], hfwd: [0, 0, 1], pfwd: [0, 0, 1] }), njj = joints(nfr, 'A'), drop = njj[ji.waist][1] - (njj[ji.hipL][1] + njj[ji.hipR][1]) / 2;
    for (const id of Object.values(S.skin.pelvis?.cards || {})) { const mm = id.match(/^gen\.(.+)\/built-seat-side$/); if (!mm || Math.abs((RP.seatDrop ?? 7) - drop) < .5 && S.byId[id]) continue;
      S.lib = S.lib.filter(c => c.id !== id); delete S.byId[id]; delete IMG[id]; delete TRIM[id]; buildSeat(mm[1], S.fix[id]?.from, { ...(S.fix[id] || {}), hip_cm: drop }); RP.seatDrop = drop; }
    RP.hips = {}; if (o.builtHips === true && S.skin.pelvis) { const ch = (S.skin.pelvis.cards.side || '').match(/^gen\.(.+)\//)?.[1] || 'puppet', hh = len3(v3(njj[ji.hipL], njj[ji.hipR])) / 2;
      const front = S.skin.pelvis.cards.front, rear = Object.values(S.fix).find(f => f.from && /seat/.test(f.from))?.from || S.skin.pelvis.cards.back;
      for (const v of ['front', 'back']) RP.hips[v] = buildHips(ch, v, v === 'back' ? rear : front, { drop, hh, rebuild: true }).id; }
    const r = rigidScalesFor(nj, o.headCm); for (const id of Object.values(S.skin.head?.cards || {})) if (r.ppc[id]) r.ppc[id] /= hs;
    for (const id of Object.values(RP.hips)) r.ppc[id] = 8 * len3(v3(njj[ji.waist], njj[ji.crotch])) / 20 > 0 ? 160 / len3(v3(njj[ji.waist], njj[ji.crotch])) : 8;
    S.cardPpc = r.ppc; RP.headCm = r.headCm; RP.key = key; RP.bind = {}; S.sock = {}; RP.statureCm = nj[ji.headTop][1]; RP.harvested = {};
    // matched widths at a shared joint: a child card whose root is wider or narrower than its parent's end (>10%) is flared to meet it
    S.autoFlare = {}; RP.flares = [];
    for (const v of VIEWS) for (const sd of ['L', 'R']) for (const [pk, ck] of [['thigh_', 'shin_'], ['upper_arm_', 'forearm_']]) {
      const pid = S.skin[pk + sd]?.cards[v], cid = S.skin[ck + sd]?.cards[v], pc = S.byId[pid], cc = S.byId[cid];
      if (!pc || !cc || S.fix[cid]?.flare || S.autoFlare[cid]) continue;
      const wp = widthAt(pc, .9), wc = widthAt(cc, .1); if (!wp || !wc || !S.cardPpc[pid] || !S.cardPpc[cid]) continue;
      const cmP = wp / S.cardPpc[pid], cmC = wc / S.cardPpc[cid], q = cmP / cmC;
      if (Math.abs(q - 1) > .1) { S.autoFlare[cid] = [Math.max(.7, Math.min(1.4, q)), 1]; delete TRIM[cid]; RP.flares.push(`${cid.split('/').pop()} (${v}) root ${cmC.toFixed(1)} cm -> ${cmP.toFixed(1)} cm, its parent's end`); }
    }
  }
  const stature = o.statureCm || RP.statureCm, k = o.port ? o.port.k : (o.heightPx || 400) / stature;
  const port = o.port || { label: 'rp' + key.length, yaw, k, cx: 0, cz: 0, toward: [sy, 0, cy], right: [cy, 0, -sy],
    p(q) { const X = q[0] - this.cx, Z = q[2] - this.cz; return [o.x + (X * cy - Z * sy) * k, o.y - q[1] * k, X * sy + Z * cy]; } };
  S.centre = (pt, fr) => { const q = fr.a.A.j[0]; pt.cx = q[0]; pt.cz = q[2]; };
  // sockets bind on the neutral pose turned to show the card the way it is drawn now
  S.bindFrame = (kk, px, pt) => {
    const v = px.view || 'side', c = px.c, sk = px.sk, mirLeft = sk.mirror !== (true !== cardLeft(c));
    const want = v === 'side' ? (px.mir === mirLeft ? 'left' : 'right') : v === 'threequarter' ? (RP.lat < 0 ? 'tqL' : 'tqR') : v;
    const id = want + '|' + Math.round(pt.yaw);
    if (!RP.bind[id]) { const tq = s => pt.toward.map((x, i) => (x + s * pt.right[i]) / Math.SQRT2);
      const d = { front: pt.toward, back: pt.toward.map(x => -x), right: pt.right, left: pt.right.map(x => -x), tqR: tq(1), tqL: tq(-1) }[want], t = Math.atan2(d[0], d[2]);
      const jj = nj.map(q => rotYv(q, t)), f = rotYv([0, 0, 1], t); RP.bind[id] = frameOf(jj, { fwd: f, hfwd: f, pfwd: f }, { views: { body: v, head: v } }); }
    return RP.bind[id];
  };
  const F = facings(j), lat = Math.sign(dot3(F.pfwd, port.right)) || ((o.facing || 'right') === 'left' ? -1 : 1);
  // the head follows the body's view; only a head turned more than 80 deg off the body (and not bowed to the floor) takes another (three-quarter if the contract
  // has a non-profile one, else profile); a three-quarter body whose contract head for that view is a profile card keeps a front head
  let headView = view; { const hz = v => Math.atan2(v[0], v[2]), dyaw = Math.abs(Math.atan2(Math.sin(hz(F.hfwd) - hz(F.fwd)), Math.cos(hz(F.hfwd) - hz(F.fwd)))) * 180 / Math.PI;
    const hc = S.skin.head?.cards || {}, tqHead = hc.threequarter && S.byId[hc.threequarter], tqProfile = tqHead && viewOf(tqHead) === 'side';
    const hh = Math.hypot(F.hfwd[0], F.hfwd[2]);   // a head bowed toward the floor has no reliable yaw: it keeps the body's view
    if (dyaw > 80 && hh > .5 && view !== 'side') headView = tqHead && !tqProfile && view !== 'threequarter' ? 'threequarter' : 'side';
    else if (view === 'threequarter' && tqProfile) headView = 'front';
    if (headView !== view) warnings.push(`head: ${headView} card on a ${view} body (head turned ${dyaw | 0} deg off the body)`); }
  const a = { j, ...F, views: { body: view, head: headView }, torsoLim: o.torsoLimDeg ?? 50, headLim: o.headLeanDeg ?? 10, headRef: paintedHead(o), lat: o.facing ? (o.facing === 'left' ? -1 : 1) : lat, hands: o.handStates || {}, bend: {}, sx: {}, states: {} };
  RP.lat = a.lat;
  if (tips) a.tips = tips;
  a.noik = {}; a.cardIds = {}; a.minLen = { shin_L: o.minShin ?? .88, shin_R: o.minShin ?? .88 };
  // the pelvis card: built trouser top in front/back/three-quarter; a seated or kneeling three-quarter figure takes the profile seat (its seat mass shows)
  { const hipFlex = s => { const sp = nrm3(v3(j[0], j[ji.spineMid])), th = nrm3(v3(j[ji['hip' + s]], j[ji['knee' + s]])); return Math.acos(Math.max(-1, Math.min(1, -dot3(sp, th)))) * 180 / Math.PI; };
    const seated = (hipFlex('L') + hipFlex('R')) / 2 > 55, seat = S.skin.pelvis?.cards.side;
    if (view === 'threequarter' && seated && seat?.startsWith('gen.')) a.cardIds.pelvis = seat;
    else if (view !== 'side' && RP.hips?.[view === 'back' ? 'back' : 'front']) a.cardIds.pelvis = RP.hips[view === 'back' ? 'back' : 'front'];
    if (a.cardIds.pelvis) RP.pelvisNote = a.cardIds.pelvis === seat ? 'profile seat (seated three-quarter)' : 'built trouser top (hip sleeve)'; }
  // per segment: how much of its true length the view shows (the joint atlas verdict), and what the puppet does about it
  const fr = { a: { A: a } }; port.cx = j[0][0]; port.cz = j[0][2];
  const jj = joints(fr, 'A'), pj = jj.map(q => port.p(q)), report = {};
  for (const kk of STYLES[S.style].segs) {
    const sg = SEG[kk], sk = S.skin[kk]; if (!sg || !sk) continue;
    const L3 = len3(v3(jj[ji[sg.from]], jj[ji[sg.to]])), r = L3 ? hyp(pj[ji[sg.from]], pj[ji[sg.to]]) / (L3 * k) : 1;
    let method = 'rotate';
    if (!LIMB.test(kk)) { method = /^(hand|foot)_/.test(kk) ? (r >= .55 ? 'rigid card (own size)' : 'rigid card (own size), end-on: the view\'s ' + view + ' card') : 'body card (' + view + ')';
      if ((kk === 'torso' || kk === 'pelvis') && r < .88) { a.sx[kk] = Math.max(r, .7); method += ` shortened x${a.sx[kk].toFixed(2)} (a jacket bent toward the camera)`; } }
    else if (r < .88) {
      const bent = sk.states?.bent?.[view] && S.byId[sk.states.bent[view]], endon = sk.states?.endon?.[view] && S.byId[sk.states.endon[view]];
      const hv = harvestFor(o.harvest, kk, view, jj, sg, port, o.harvestExclude);
      if (hv) { a.cardIds[kk] = hv.c.id; S.cardPpc[hv.c.id] = ppcOf(hv.c); method = `harvested foreshortened card (${hv.c.id}, bone direction ${(hv.cos * 100) | 0}% alike)`; }
      else if (r < .55 && endon) { a.states[kk] = 'endon'; method = 'dedicated end-on card'; }
      else if (bent) { a.states[kk] = 'bent'; method = 'replacement card (bent)'; }
      else { a.sx[kk] = Math.max(r, .88); method = r >= .55 ? `declared shortening x${a.sx[kk].toFixed(2)} + overlap` : 'shortened x0.88 + overlap; END-ON: needs a dedicated card or another view';
        if (r < .55) warnings.push(`${kk}: end-on in ${view} view (shows ${(r * 100) | 0}% of its length) - restage or add a dedicated card`); }
    }
    report[kk] = { projRatio: +r.toFixed(3), verdict: VERDICT(r), method };
  }
  // a hinge that bends toward the camera is not bent across the screen: each card aims at its own joint (no IK), so front legs stand
  // straight with the stance the skeleton gives, never bowed into a diamond; the foreshortening is the shortening/replacement above
  for (const s of ['L', 'R']) for (const [up, mid, end, seg] of [['hip', 'knee', 'ankle', 'thigh_'], ['shoulder', 'elbow', 'wrist', 'upper_arm_']]) {
    const u = v3(jj[ji[up + s]], jj[ji[mid + s]]), w = v3(jj[ji[mid + s]], jj[ji[end + s]]), n = cross3(u, w), nl = len3(n) / ((len3(u) * len3(w)) || 1);
    if (nl >= .17 && Math.abs(dot3(nrm3(n), port.toward)) <= .5) { a.noik[seg + s] = true; if (report[seg + s]) report[seg + s].method += ' (bends toward the camera: no IK, aimed at its own joint)'; }
  }
  for (const sd of Object.keys(AJ.straight || {})) { a.noik['upper_arm_' + sd] = true; if (report['upper_arm_' + sd]) report['upper_arm_' + sd].method += ' (painted straight: no IK bend)'; }
  // hinges that bend across the screen bend the anatomical way: knees forward, elbows back (side and three-quarter views)
  if (view === 'side' || Math.abs(Math.abs(yaw) - 90) < 50) {
    const fs = Math.sign(dot3(F.pfwd, port.right)) || a.lat, fa = Math.sign(dot3(F.fwd, port.right)) || a.lat;
    for (const s of ['L', 'R']) for (const [up, mid, end, sgn] of [['hip', 'knee', 'ankle', -fs], ['shoulder', 'elbow', 'wrist', fa]]) {
      const u = v3(jj[ji[up + s]], jj[ji[mid + s]]), w = v3(jj[ji[mid + s]], jj[ji[end + s]]), n = cross3(u, w), nl = len3(n) / ((len3(u) * len3(w)) || 1);
      if (nl < .17 || Math.abs(dot3(nrm3(n), port.toward)) > .5) a.bend[(up === 'hip' ? 'thigh_' : 'upper_arm_') + s] = sgn;   // straight or bending across the screen
    }
  }
  const prevShade = S.farShade; S.farShade = o.farShade ?? .72;
  const sol = solve(fr, port, S.style, true);
  if (!sol) { S.farShade = prevShade; return { cards: [], warnings: warnings.concat('no solve') }; }
  for (const kk of Object.keys(report)) if (!sol.X[kk]) warnings.push(`${kk}: no ${view} card in the contract`);
  // layering by depth: an arm card goes under the torso unless the pose puts it in front of the chest (>6 cm nearer the camera)
  { const T = sol.X.torso; if (T) { const arm = x => /^(far|near)_(upper_arm|forearm|hand|mitt|arm)$/.test(x.role), under = [], rest = [];
      for (const x of sol.order) (x !== T && arm(x) && x.d <= T.d + 6 && (x.role.startsWith('far_') || x.d < T.d - 6) ? under : rest).push(x);
      // under the torso AND the head (whichever the stack draws first), so a far hand never lands on the face
      const H = sol.X.head, ti = Math.min(rest.indexOf(T), H && rest.indexOf(H) >= 0 ? rest.indexOf(H) : Infinity); sol.order = [...rest.slice(0, ti), ...under, ...rest.slice(ti)];
      // a hand at the head that is farther from the camera than the head (a hand under the cheek, behind the ear) goes under the head;
      // a hand nearer than the head (at the ear with a handset, over the eyes) stays over it
      // and a hand the drawing lays on the face while the painting holds that wrist at or below the neck (a hand propping the head from
      // under the cheek), goes under the head too
      const mk = o.target?.markers, okm = n => mk?.[n] && (mk[n][4] ?? 1) >= .4, under9 = x => { const sd = x.k.slice(-1); return okm('neck') && okm('head') && okm('wrist' + sd) && mk['wrist' + sd][1] >= mk.neck[1] - .05 * Math.hypot(mk.head[0] - mk.neck[0], mk.head[1] - mk.neck[1]); };
      if (H) for (const x of sol.order.slice()) { if (!/_hand$/.test(x.role) || (x.d >= H.d - 2 && !under9(x))) continue; const hp = fwd(H, [(H.A[0] + H.B[0]) / 2, (H.A[1] + H.B[1]) / 2]), r = H.lab * H.s * .6;
        if (Math.hypot(x.P[0] - hp[0], x.P[1] - hp[1]) < r && sol.order.indexOf(x) > sol.order.indexOf(H)) { sol.order.splice(sol.order.indexOf(x), 1); sol.order.splice(sol.order.indexOf(H), 0, x); } } } }
  // hard overlaps at the knee: the thigh (the parent) is drawn right after its shin, so the thigh's own painted end lies crisply over
  // the shin's root, as paper overlaps (no redrawn disc, no feathering)
  if (o.overlapKnees !== false) for (const sd of ['L', 'R']) { const th = sol.X['thigh_' + sd], sh = sol.X['shin_' + sd]; if (!th || !sh) continue;
    const it = sol.order.indexOf(th), is = sol.order.indexOf(sh); if (it < 0 || is < 0) continue;
    if (sh.d > th.d + 6) {   // a folded shin nearer the camera than its thigh (sitting on the floor, the near shin of a kneel) lies over it, its boot with it
      if (is < it) { sol.order.splice(is, 1); sol.order.splice(sol.order.indexOf(th) + 1, 0, sh); const ft = sol.X['foot_' + sd]; if (ft && sol.order.indexOf(ft) < sol.order.indexOf(sh)) { sol.order.splice(sol.order.indexOf(ft), 1); sol.order.splice(sol.order.indexOf(sh) + 1, 0, ft); } }
      continue; }
    if (it > is) continue; sol.order.splice(it, 1); sol.order.splice(sol.order.indexOf(sh) + 1, 0, th); }
  // one true scale per figure: no two boots, and no replacement limb card against the contract's, may differ by more than 10%;
  // a harvested boot is brought to the other boot's length; anything still off is a SCALE INVARIANT warning (the gate fails on it)
  { const cmLen = x => { const b = alphaBox(x.c); return b ? Math.max(b[2] - b[0], b[3] - b[1]) * x.s * (x.sx || 1) / port.k : null; };
    const fl = sol.X.foot_L, fr_ = sol.X.foot_R;
    if (fl && fr_) { let a1 = cmLen(fl), a2 = cmLen(fr_);
      if (a1 && a2 && Math.max(a1, a2) / Math.min(a1, a2) > 1.1) { const h = /^harvest\./.test(fl.c.id) ? fl : /^harvest\./.test(fr_.c.id) ? fr_ : null;
        if (h) { const ref = h === fl ? a2 : a1, cur = h === fl ? a1 : a2; h.s *= ref / cur; warnings.push(`boot scale: ${h.k} (harvested) brought from ${cur.toFixed(0)} to ${ref.toFixed(0)} cm long, the other boot's size`); a1 = cmLen(fl); a2 = cmLen(fr_); }
        if (Math.max(a1, a2) / Math.min(a1, a2) > 1.1) warnings.push(`SCALE INVARIANT: boots ${a1.toFixed(0)} and ${a2.toFixed(0)} cm long (more than 10% apart)`); } }
    // a limb card other than the contract's own (a harvested or replacement card) is drawn at the contract card's true scale: its
    // width across the limb within 10% of the contract card's (same part, same view)
    for (const x of Object.values(sol.X)) { if (!LIMB.test(x.k) && !/^(hand|foot)_/.test(x.k)) continue; const base = S.byId[RP.base?.[x.k]?.[x.view]]; if (!base || base.id === x.c.id || /^foot_/.test(x.k)) continue;
      const wb = widthAt(base, .5), wx = widthAt(x.c, .5); if (!wb || !wx || !S.cardPpc[base.id]) continue;
      const fl = S.fix[base.id]?.flare || S.autoFlare?.[base.id], cb = wb * (fl ? (fl[0] + fl[1]) / 2 : 1) / S.cardPpc[base.id], cx = wx * x.s / port.k;
      if (Math.max(cb, cx) / Math.min(cb, cx) > 1.1) {   // brought to the contract's width by a width-only flare (its length still meets the joints)
        const q0 = S.autoFlare?.[x.c.id]?.[0] ?? 1, q = Math.max(.5, Math.min(2, cb / cx)), after = cx * q;
        if (Math.abs(q - q0) > .01) { S.autoFlare = S.autoFlare || {}; S.autoFlare[x.c.id] = [q, q]; delete TRIM[x.c.id]; }
        if (Math.max(cb, after) / Math.min(cb, after) > 1.1) warnings.push(`SCALE INVARIANT: ${x.k} drawn ${after.toFixed(1)} cm wide, the contract's ${x.view} card is ${cb.toFixed(1)} cm (more than 10% apart)`);
        else warnings.push(`width matched: ${x.k} (${x.c.id.split('/').slice(-2).join('/')}) ${cx.toFixed(1)} -> ${cb.toFixed(1)} cm, the contract card's width`); } } }
  if (ctx) {
    for (const x of sol.order) drawCard(ctx, x, 1);
  }
  S.farShade = prevShade;
  const cards = sol.order.map(x => ({ part: x.k, card: x.c.id, view: x.view, role: x.role, mirrored: !!x.mir, ...(report[x.k] || {}), gap_cm: +x.gap.toFixed(1), miss_cm: +x.miss.toFixed(1) }));
  for (const c of cards) if (c.miss_cm > 12 && LIMB.test(c.part)) warnings.push(`${c.part}: card ends ${c.miss_cm} cm from its joint`);
  const segments = sol.order.map(x => { const sg = SEG[x.k], e = fwd(x, x.B), q = pj[ji[sg.to]], rp = report[x.k] || {};
    return { k: x.k, role: x.role, card: x.c.id, view: x.view, want: x.want, mirrored: !!x.mir, miss_cm: +x.miss.toFixed(1), ratio: rp.projRatio, atlas: rp.verdict, drawn: rp.method,
      P: [Math.round(x.P[0]), Math.round(x.P[1])], Q: [Math.round(q[0]), Math.round(q[1])], end: [Math.round(e[0]), Math.round(e[1])] }; });
  if (RP.flares?.length) warnings.push(...RP.flares.map(f => 'width matched: ' + f));
  if (a.lenNote) warnings.push(...a.lenNote.map(k => `${k}: replacement card stretched to 88% of the shin's true length`));
  return { cards, segments, sol, warnings, view, yaw, px_per_cm: k, bbox: (() => { const xs = sol.order.flatMap(x => [x.P[0]]), ys = sol.order.flatMap(x => [x.P[1]]); return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]; })() };
}
Object.assign(P, { renderPose, adjustJoints, prepare, applyContract, fromPoseLab, neutralOf, yawOf, cardViewOf, rigidScalesFor });

Object.assign(P, { ppcOf, cardsOf, trimmed, holdPoint, clampNeck, S, J, ji, HAND_CM, TOPO, PAR, GRP, GROUPS, VIT, FEET, measure, retarget, joints, SEG, LR, STYLES, STACK0, ARMS, VIEWS, VIEWOF, viewOf, OTHER, STICK,
  NAME, NOT, nameOK, human, painted, IMG, img, AB, pts, cardLeft, index, v3, len3, hyp, rot, makePort, centre, active, mk, fwd, inv, scaleOf, socket, ik2, roleOf, solve,
  drawCard, decode, decodeProps, measureActor, presetK, cur, newSkin, dE, dress, kitbash, labCss, buildCard, buildSeat, buildHips, rebuildGen, stick });
root.PuppetCore = P;
})(typeof window !== 'undefined' ? window : globalThis);
