/* pose-core.js — the Pose Lab's math, shared by shots/rig/pose.html (and checked against shots/rig/solve.py).

   One 3D skeleton per character, measured from the Rig Builder's front cards at true scale.
   Body frame: X = the actor's LEFT, Y = DOWN, Z = FORWARD; the floor is Y = 0. Angles in degrees.
   A view is a yaw psi: 0 front, +90 profile facing screen-right, +-45 three-quarter, 180 back:
     depth = -X sin psi + Z cos psi (toward the camera), screen_x = X cos psi + Z sin psi + 0.12 depth |sin psi|.
   Every function here mirrors solve.py one-for-one (same names), so a pose solved in the batch plays here. */
(function (root) {
  'use strict';
  const DEG = Math.PI / 180;
  const PN = ['ox', 'oy', 'oz', 'pitch', 'roll', 'twist', 'tf', 'tb', 'hf', 'hb',
    'shLf', 'shLb', 'elL', 'wrL', 'shRf', 'shRb', 'elR', 'wrR',
    'hpLf', 'hpLb', 'knL', 'anL', 'hpRf', 'hpRb', 'knR', 'anR', 'shLt', 'shRt', 'hpLt', 'hpRt',
    'kT', 'kU', 'kF', 'kTh', 'kSh', 'kHd'];
  const PI = Object.fromEntries(PN.map((n, i) => [n, i]));
  const NP = PN.length;
  const LIM = {
    pitch: [-120, 120], roll: [-100, 100], twist: [-50, 50], tf: [-30, 90], tb: [-35, 35], hf: [-50, 60], hb: [-45, 45],
    shLf: [-60, 180], shLb: [-30, 180], elL: [0, 150], wrL: [-70, 70], shRf: [-60, 180], shRb: [-30, 180], elR: [0, 150], wrR: [-70, 70],
    hpLf: [-30, 125], hpLb: [-25, 70], knL: [0, 140], anL: [-45, 30], hpRf: [-30, 125], hpRb: [-25, 70], knR: [0, 140], anR: [-45, 30],
    shLt: [-90, 90], shRt: [-90, 90], hpLt: [-45, 45], hpRt: [-45, 45],
    kT: [-.3, .3], kU: [-.3, .3], kF: [-.3, .3], kTh: [-.3, .3], kSh: [-.3, .3], kHd: [-.3, .3]
  };
  const KN = ['kT', 'kU', 'kF', 'kTh', 'kSh', 'kHd'];
  const ANG = PN.map((n, i) => i).filter(i => i >= 6 && !KN.includes(PN[i]));
  const JOINTS = ['neck', 'waist', 'shL', 'shR', 'elL', 'elR', 'wrL', 'wrR', 'hipL', 'hipR', 'knL', 'knR', 'anL', 'anR'];
  const JOINT_WORD = { neck: 'neck', waist: 'waist', shL: 'shoulder L', shR: 'shoulder R', elL: 'elbow L', elR: 'elbow R', wrL: 'wrist L', wrR: 'wrist R', hipL: 'hip L', hipR: 'hip R', knL: 'knee L', knR: 'knee R', anL: 'ankle L', anR: 'ankle R' };
  // the angle a joint dot reports (for the limit arcs): [param, label]
  const JOINT_DOF = { neck: 'hf', waist: 'tf', shL: 'shLf', shR: 'shRf', elL: 'elL', elR: 'elR', wrL: 'wrL', wrR: 'wrR', hipL: 'hpLf', hipR: 'hpRf', knL: 'knL', knR: 'knR', anL: 'anL', anR: 'anR' };
  // labelled target markers (Mixamo-style) and the rig point each one pins
  const MARKERS = [['head', 'top'], ['chin', 'chin'], ['neck', 'neck'], ['shoulderL', 'shL'], ['shoulderR', 'shR'], ['elbowL', 'elL'], ['elbowR', 'elR'],
    ['wristL', 'wrL'], ['wristR', 'wrR'], ['groin', 'pelvis'], ['hipL', 'hipL'], ['hipR', 'hipR'], ['kneeL', 'knL'], ['kneeR', 'knR'],
    ['ankleL', 'anL'], ['ankleR', 'anR'], ['toeL', 'toeL'], ['toeR', 'toeR']];
  const MARKER_J = Object.fromEntries(MARKERS);
  const MW = { head: .5, chin: .5, toeL: .6, toeR: .6 };
  const MIRROR_M = n => n.endsWith('L') ? n.slice(0, -1) + 'R' : n.endsWith('R') ? n.slice(0, -1) + 'L' : n;
  const SEGS = [['waist', 'neck', 14], ['pelvis', 'waist', 13], ['neck', 'top', 9], ['shL', 'elL', 5.5], ['elL', 'wrL', 4.5],
    ['wrL', 'tipL', 4], ['shR', 'elR', 5.5], ['elR', 'wrR', 4.5], ['wrR', 'tipR', 4], ['hipL', 'knL', 7],
    ['knL', 'anL', 5.5], ['heelL', 'toeL', 4], ['hipR', 'knR', 7], ['knR', 'anR', 5.5], ['heelR', 'toeR', 4]];
  const FLAT = [['shL', 'elL'], ['elL', 'wrL'], ['shR', 'elR'], ['elR', 'wrR'], ['hipL', 'knL'], ['knL', 'anL'], ['hipR', 'knR'], ['knR', 'anR'], ['waist', 'neck']];
  const INSIDE = ['top', 'headC', 'tipL', 'tipR', 'toeL', 'toeR', 'heelL', 'heelR', 'mUaL', 'mUaR', 'mFaL', 'mFaR',
    'mThL', 'mThR', 'mShL', 'mShR', 'chest', 'pelvis'].concat(JOINTS);
  // Dempster / Winter segment masses (fraction of body mass) and COM position from the proximal end
  const MASS = [['pelvis', 'waist', .142, .5], ['waist', 'neck', .355, .5], ['neck', 'top', .081, .55],
    ['shL', 'elL', .028, .436], ['elL', 'wrL', .016, .43], ['wrL', 'tipL', .006, .506],
    ['shR', 'elR', .028, .436], ['elR', 'wrR', .016, .43], ['wrR', 'tipR', .006, .506],
    ['hipL', 'knL', .100, .433], ['knL', 'anL', .0465, .433], ['heelL', 'toeL', .0145, .5],
    ['hipR', 'knR', .100, .433], ['knR', 'anR', .0465, .433], ['heelR', 'toeR', .0145, .5]];
  const NORM = { upper_arm: .186, forearm: .145, hand: .108, thigh: .245, shin: .246 };

  function lims(sandbox, stretch) {
    const lo = new Float64Array(NP + 1).fill(-1e4), hi = new Float64Array(NP + 1).fill(1e4);
    for (const n in LIM) { const i = PI[n]; const lift = sandbox && n !== 'pitch' && n !== 'roll' && !KN.includes(n); lo[i] = lift ? -180 : LIM[n][0]; hi[i] = lift ? 180 : LIM[n][1]; }
    if (!stretch) for (const n of KN) { lo[PI[n]] = -1e-6; hi[PI[n]] = 1e-6; }
    lo[PI.oz] = -1e-6; hi[PI.oz] = 1e-6;
    lo[NP] = Math.log(.55); hi[NP] = Math.log(1.8);
    return [lo, hi];
  }

  // ---------------------------------------------------------------- 3x3 rotations (row-major arrays of 9)
  const Rx = a => { const c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, c, -s, 0, s, c]; };
  const Ry = a => { const c = Math.cos(a), s = Math.sin(a); return [c, 0, s, 0, 1, 0, -s, 0, c]; };
  const Rz = a => { const c = Math.cos(a), s = Math.sin(a); return [c, -s, 0, s, c, 0, 0, 0, 1]; };
  function mm(A, B) {
    const o = new Array(9);
    for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) o[i * 3 + j] = A[i * 3] * B[j] + A[i * 3 + 1] * B[3 + j] + A[i * 3 + 2] * B[6 + j];
    return o;
  }
  const mv = (R, v) => [R[0] * v[0] + R[1] * v[1] + R[2] * v[2], R[3] * v[0] + R[4] * v[1] + R[5] * v[2], R[6] * v[0] + R[7] * v[1] + R[8] * v[2]];
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]], sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s], mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
  const len3 = a => Math.hypot(a[0], a[1], a[2]);

  // ---------------------------------------------------------------- forward kinematics
  function fk(S, x) {
    const g = n => x[PI[n]] * DEG, ek = n => Math.exp(x[PI[n]]);
    const R0 = mm(mm(Ry(g('twist')), Rx(-g('pitch'))), Rz(g('roll')));
    const J = { pelvis: [0, 0, 0] };
    J.hipL = mv(R0, [S.hipHalf, 0, 0]); J.hipR = mv(R0, [-S.hipHalf, 0, 0]);
    J.waist = mv(R0, [0, -S.waistUp * ek('kT'), 0]);
    const Rt = mm(mm(R0, Rx(-g('tf'))), Rz(g('tb')));
    J.neck = add(J.waist, mv(Rt, [0, -S.torso * ek('kT'), 0]));
    J.chest = add(J.waist, mv(Rt, [0, -.6 * S.torso * ek('kT'), 0]));
    const Rh = mm(mm(Rt, Rx(-g('hf'))), Rz(g('hb')));
    J.top = add(J.neck, mv(Rh, [0, -S.head * ek('kHd'), 0]));
    J.headC = add(J.neck, mv(Rh, [0, -.55 * S.head * ek('kHd'), 0]));
    J.chin = add(J.neck, mv(Rh, [0, -.33 * S.head * ek('kHd'), 0]));
    const F = { R0, Rt, Rh };
    for (const [sd, sg] of [['L', 1], ['R', -1]]) {
      const sh = S['sh' + sd];
      J['sh' + sd] = add(J.neck, mv(Rt, [sh[0], sh[1], 0]));
      const Ru = mm(mm(mm(Rt, Rx(g('sh' + sd + 'f'))), Rz(-sg * g('sh' + sd + 'b'))), Ry(sg * g('sh' + sd + 't')));
      J['el' + sd] = add(J['sh' + sd], mv(Ru, [0, S['uarm' + sd] * ek('kU'), 0]));
      const Rf = mm(Ru, Rx(g('el' + sd)));
      J['wr' + sd] = add(J['el' + sd], mv(Rf, [0, S['farm' + sd] * ek('kF'), 0]));
      const Rw = mm(Rf, Rx(g('wr' + sd)));
      J['tip' + sd] = add(J['wr' + sd], mv(Rw, [0, S['hand' + sd], 0]));
      const Rth = mm(mm(mm(R0, Rx(g('hp' + sd + 'f'))), Rz(-sg * g('hp' + sd + 'b'))), Ry(sg * g('hp' + sd + 't')));
      J['kn' + sd] = add(J['hip' + sd], mv(Rth, [0, S['thigh' + sd] * ek('kTh'), 0]));
      const Rs = mm(Rth, Rx(-g('kn' + sd)));
      J['an' + sd] = add(J['kn' + sd], mv(Rs, [0, S['shin' + sd] * ek('kSh'), 0]));
      const Rft = mm(Rs, Rx(g('an' + sd)));
      J['heel' + sd] = add(J['an' + sd], mv(Rft, S.heel));
      J['toe' + sd] = add(J['an' + sd], mv(Rft, S.toe));
      J['ball' + sd] = add(J['an' + sd], mv(Rft, [0, S.toe[1], .72 * S.toe[2]]));
      J['ankUp' + sd] = add(J['an' + sd], mv(Rft, [0, -10, 0]));
      J['mUa' + sd] = mid(J['sh' + sd], J['el' + sd]); J['mFa' + sd] = mid(J['el' + sd], J['wr' + sd]);
      J['mTh' + sd] = mid(J['hip' + sd], J['kn' + sd]); J['mSh' + sd] = mid(J['kn' + sd], J['an' + sd]);
      Object.assign(F, { ['Ru' + sd]: Ru, ['Rf' + sd]: Rf, ['Rw' + sd]: Rw, ['Rth' + sd]: Rth, ['Rs' + sd]: Rs, ['Rft' + sd]: Rft });
    }
    J._F = F;
    return J;
  }

  function project(p, psi, ox = 0, oy = 0, T) {
    const c = Math.cos(psi * DEG), s = Math.sin(psi * DEG);
    const X = p[0] + (T ? T[0] : 0), Y = p[1] + (T ? T[1] : 0), Z = p[2] + (T ? T[2] : 0);
    const depth = -X * s + Z * c;
    return [X * c + Z * s + .12 * depth * Math.abs(s) + ox, Y + oy, depth];
  }
  const VIEWKEYS = ['front', 'threequarter', 'profile', 'threequarter_back', 'back'];
  function viewKey(psi) { const a = Math.abs((((psi + 180) % 360) + 360) % 360 - 180); return VIEWKEYS[Math.min(4, Math.floor((a + 22.5) / 45))]; }

  // ---------------------------------------------------------------- rig data -> skeleton
  const SLOTS = [['hip', 'hip', null], ['torso', 'torso', null], ['head', 'head', null],
    ['upper_arm_L', 'upper_arm', 'L'], ['forearm_L', 'forearm', 'L'], ['hand_L', 'hand', 'L'],
    ['upper_arm_R', 'upper_arm', 'R'], ['forearm_R', 'forearm', 'R'], ['hand_R', 'hand', 'R'],
    ['thigh_L', 'thigh', 'L'], ['shin_L', 'shin', 'L'], ['shoe_L', 'shoe', 'L'],
    ['thigh_R', 'thigh', 'R'], ['shin_R', 'shin', 'R'], ['shoe_R', 'shoe', 'R']];
  const KIND = { torso: 'torso', hip: 'hip', head: 'head', hand: 'hand', shoe: 'shoe' };
  function pt(p, name) {
    const q = p.pts || {};
    if (q[name]) return q[name];
    const w = p.w, h = p.h, k = KIND[p.cls] || 'limb';
    const F = { pivot: [w / 2, .07 * h], socket: [w / 2, .93 * h], neck: k === 'head' ? [w / 2, .92 * h] : [w / 2, .05 * h], waist: k === 'hip' ? [w / 2, .15 * h] : [w / 2, .95 * h],
      shVL: [.12 * w, .17 * h], shVR: [.88 * w, .17 * h], hipVL: [.2 * w, .8 * h], hipVR: [.8 * w, .8 * h], top: [w / 2, 0], wrist: [w / 2, .08 * h], tip: [w / 2, h],
      ankle: [w / 2, .15 * h], heel: [0, h], toe: [w, h] };
    return F[name] || [w / 2, h / 2];
  }
  function score(p, side, view) {
    let s = 0;
    if (side) s += p.side === side ? 4 : (p.side ? -3 : 1);
    if (p.view) s += p.view === view ? 3 : -2;
    s += { A: 3, B: 1, C: -6 }[p.q] || 0;
    if ((p.nb || 0) >= 2) s += 1;
    const names = { torso: ['neck', 'waist', 'shVL', 'shVR'], hip: ['waist', 'hipVL', 'hipVR'], head: ['neck', 'top'], hand: ['wrist', 'tip'], shoe: ['ankle', 'heel', 'toe'] }[p.cls] || ['pivot', 'socket'];
    for (const n of names) if ((p.src || {})[n] === 'brad') s += .5;
    if (p.ppc_src === 'sheet') s += 1;
    if (p.not_costume) s -= 10;
    if (p.state && (p.state.includes('uncut') || p.state.includes('pair'))) s -= 4;
    if (p.cls === 'hand' && p.shape && p.shape !== 'relaxed') s -= 1;
    return s;
  }
  function cardsExact(doc, view) {
    const d = Object.assign({}, (doc.defaults || {})[view] || {}), out = {};
    for (const [n, cls, side] of SLOTS) {
      let pid = d[n];
      if (!pid || !doc.P[pid]) {
        const L = doc.parts.filter(p => p.cls === cls).sort((a, b) => score(b, side, view) - score(a, side, view));
        pid = L[0] ? L[0].id : null;
      }
      out[n] = pid;
    }
    return out;
  }
  function cardsFor(doc, view, override) {
    let base;
    if (view === 'front' || view === 'profile' || view === 'back') base = cardsExact(doc, view);
    else {
      base = cardsExact(doc, view === 'threequarter' ? 'front' : 'back');
      for (const [n, cls, side] of SLOTS) if (cls === 'torso' || cls === 'head') {
        const L = doc.parts.filter(p => p.cls === cls && p.view === view && (p.q === 'A' || p.q === 'B')).sort((a, b) => score(b, side, view) - score(a, side, view));
        if (L.length) base[n] = L[0].id;
      }
    }
    if (override && override[view]) for (const k in override[view]) if (override[view][k] && doc.P[override[view][k].pid || override[view][k]]) base[k] = override[view][k].pid || override[view][k];
    return base;
  }
  function prep(doc) {
    doc.P = {}; for (const p of doc.parts) doc.P[p.id] = p;
    const pp = doc.parts.map(p => p.ppc).filter(Boolean).sort((a, b) => a - b);
    doc.ppcMedian = pp[pp.length >> 1] || 8;
    return doc;
  }
  // rig: optional Builder rig {slots: {slot: {pid, s}}} for the front view; autofix: the critic's scale fix
  function skeleton(doc, rig, autofix = true) {
    const H = doc.stature_cm, P = doc.P, fixes = [];
    const front = cardsExact(doc, 'front');
    if (rig) for (const k in rig) if (rig[k] && rig[k].pid) front[k] = rig[k].pid;
    const card = n => { const pid = front[n]; if (!pid) return [null, 0]; const p = P[pid]; const s = (rig && rig[n] && rig[n].s) || p.user_scale || 1; return [p, s / (p.ppc || doc.ppcMedian)]; };
    const L = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
    const fixlen = (slot, l) => { const nr = NORM[slot.replace(/_[LR]$/, '')]; if (!autofix || !nr || rig) return l; const r = l / (nr * H); if (r < .85 || r > 1.18) { fixes.push(`${slot} ${r.toFixed(2)}x norm -> rescaled`); return nr * H; } return l; };
    const S = { H, cards: front };
    let [p, k] = card('hip');
    if (p) { const a = pt(p, 'hipVL'), b = pt(p, 'hipVR'), m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; S.hipHalf = L(a, b) / 2 * k; S.waistUp = Math.max(4, (m[1] - pt(p, 'waist')[1]) * k); }
    else { S.hipHalf = .05 * H; S.waistUp = .06 * H; }
    [p, k] = card('torso');
    if (p) { const n = pt(p, 'neck'), w = pt(p, 'waist'); S.torso = L(n, w) * k; const sl = pt(p, 'shVR'), sr = pt(p, 'shVL'); S.shL = [(sl[0] - n[0]) * k, (sl[1] - n[1]) * k]; S.shR = [(sr[0] - n[0]) * k, (sr[1] - n[1]) * k]; }
    else { S.torso = .3 * H; S.shL = [.11 * H, .03 * H]; S.shR = [-.11 * H, .03 * H]; }
    [p, k] = card('head'); S.head = p ? L(pt(p, 'neck'), pt(p, 'top')) * k : .14 * H;
    for (const sd of ['L', 'R']) for (const [slot, key, a, b] of [['upper_arm', 'uarm', 'pivot', 'socket'], ['forearm', 'farm', 'pivot', 'socket'], ['hand', 'hand', 'wrist', 'tip'], ['thigh', 'thigh', 'pivot', 'socket'], ['shin', 'shin', 'pivot', 'socket']]) {
      [p, k] = card(slot + '_' + sd);
      S[key + sd] = p ? fixlen(slot + '_' + sd, L(pt(p, a), pt(p, b)) * k) : NORM[slot] * H;
    }
    const pf = cardsExact(doc, 'profile').shoe_L; p = pf ? P[pf] : null;
    if (p && p.pts && p.pts.heel && p.view === 'profile') {
      const kk = (p.user_scale || 1) / (p.ppc || doc.ppcMedian), an = pt(p, 'ankle'), he = pt(p, 'heel'), to = pt(p, 'toe'), f = p.faces || 1;
      S.heel = [0, (he[1] - an[1]) * kk, (he[0] - an[0]) * kk * f]; S.toe = [0, (to[1] - an[1]) * kk, (to[0] - an[0]) * kk * f];
      if (S.heel[2] > S.toe[2]) { const t = S.heel[2]; S.heel[2] = S.toe[2]; S.toe[2] = t; }
      if (!(.08 * H < S.toe[2] - S.heel[2] && S.toe[2] - S.heel[2] < .25 * H) || !(.02 * H < S.heel[1] && S.heel[1] < .09 * H)) p = null;
    } else p = null;
    if (!p) { S.heel = [0, .04 * H, -.03 * H]; S.toe = [0, .04 * H, .12 * H]; }
    S.fixes = fixes;
    const J = fk(S, new Float64Array(NP));
    S.standing_cm = Math.max(J.heelL[1], J.toeL[1]) - J.top[1];
    return S;
  }

  // ---------------------------------------------------------------- card placement in a view
  const CARD = { hip: ['waist', 'hips', 'waist', 'pelvis', true], torso: ['waist', 'neck', 'waist', 'neck', true], head: ['neck', 'top', 'neck', 'top', false],
    upper_arm: ['pivot', 'socket', 'sh', 'el', true], forearm: ['pivot', 'socket', 'el', 'wr', true], hand: ['wrist', 'tip', 'wr', 'tip', 'shrink'],
    thigh: ['pivot', 'socket', 'hip', 'kn', true], shin: ['pivot', 'socket', 'kn', 'an', true], shoe: ['ankle', null, 'an', null, false] };
  const BIAS = { hip: -10, shoe: -6, shin: -5, thigh: -4, torso: 0, head: 2, upper_arm: 3, forearm: 4, hand: 5 };
  const SIDED = new Set(['sh', 'el', 'wr', 'hip', 'kn', 'an', 'tip']);
  // -> [{slot, p, M:[a,b,c,d,e,f] card px -> screen cm, depth, far}] back to front
  // rest: {order: [slot, ...] back to front, far: {slot: true}, facing: 1} from the Rest rig step for this view
  function placeCards(doc, J, psi, ox, oy, cards, T, rest) {
    const vk = viewKey(psi); cards = cards || cardsFor(doc, vk);
    const face = (((psi % 360) + 360) % 360) < 180 ? 1 : -1;
    const sideView = vk === 'profile' || vk === 'threequarter' || vk === 'threequarter_back';
    const P2 = n => { const q = project(J[n], psi, ox, oy, T); return [q[0], q[1]]; };
    const D = n => project(J[n], psi, 0, 0, T)[2];
    const tdep = D('chest'), out = [];
    for (const [slot, cls, side] of SLOTS) {
      const pid = cards[slot]; if (!pid) continue;
      const p = doc.P[pid]; if (!p) continue;
      const [cp, ca, sa, sb, stretch] = CARD[cls], sd = side || '';
      const A = SIDED.has(sa) ? sa + sd : sa;
      const k = (p.user_scale || 1) / (p.ppc || doc.ppcMedian);
      let flip = false;
      if (sideView) flip = cls === 'shoe' ? (p.faces || 1) * face < 0 : face < 0;
      else if (side && p.side && p.side !== side) flip = true;
      const w = p.w, fx = q => flip ? [w - q[0], q[1]] : [q[0], q[1]];
      const pv = fx(pt(p, cp));
      let ax = null;
      if (ca === 'hips') { const a_ = pt(p, 'hipVL'), b_ = pt(p, 'hipVR'); ax = fx([(a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2]); }
      else if (ca) ax = fx(pt(p, ca));
      const Aw = P2(A);
      let Bv, uc;
      if (cls === 'shoe') {
        if (sideView && p.pts && p.pts.heel) { const pa = fx(pt(p, 'heel')), pb = fx(pt(p, 'toe')); const t1 = P2('toe' + sd), h1 = P2('heel' + sd); Bv = [t1[0] - h1[0], t1[1] - h1[1]]; uc = [pb[0] - pa[0], pb[1] - pa[1]]; }
        else { const u = P2('ankUp' + sd); Bv = [u[0] - Aw[0], u[1] - Aw[1]]; uc = [0, -1]; }
      } else {
        const B = SIDED.has(sb) ? sb + sd : sb, b2 = P2(B);
        Bv = [b2[0] - Aw[0], b2[1] - Aw[1]]; uc = [ax[0] - pv[0], ax[1] - pv[1]];
      }
      const lc = Math.hypot(uc[0], uc[1]) || 1, ld = Math.hypot(Bv[0], Bv[1]);
      const uh = [uc[0] / lc, uc[1] / lc], dh = ld > 1e-6 ? [Bv[0] / ld, Bv[1] / ld] : [0, 1];
      let along;
      if (cls === 'shoe' || stretch === false) along = k;
      else { along = ld / lc; along = stretch === 'shrink' ? Math.min(k, Math.max(.5 * k, along)) : Math.min(1.7 * k, Math.max(.3 * k, along)); }
      const nc = [-uh[1], uh[0]], nd = [-dh[1], dh[0]];
      // L = along * dh uh^T + k nd nc^T  (then the mirror on the right)
      let L00 = along * dh[0] * uh[0] + k * nd[0] * nc[0], L01 = along * dh[0] * uh[1] + k * nd[0] * nc[1];
      let L10 = along * dh[1] * uh[0] + k * nd[1] * nc[0], L11 = along * dh[1] * uh[1] + k * nd[1] * nc[1];
      if (flip) { L00 = -L00; L10 = -L10; }
      const pv0 = pt(p, cp);
      const tx = Aw[0] - (L00 * pv0[0] + L01 * pv0[1]), ty = Aw[1] - (L10 * pv0[0] + L11 * pv0[1]);
      // canvas setTransform order: a=L00 b=L10 c=L01 d=L11 e f
      const M = [L00, L10, L01, L11, tx, ty];
      let dep;
      if (cls === 'shoe') dep = D('an' + sd);
      else if (sb === 'neck' || sb === 'pelvis' || sb === 'top') dep = D(A) * .5 + D(sb) * .5;
      else dep = (D(A) + D(SIDED.has(sb) ? sb + sd : sb)) / 2;
      let far = sideView && side != null && dep < tdep - 4;
      let key = dep + BIAS[cls];
      if (rest && rest.order && rest.order.includes(slot)) {
        const swap = sideView && face !== (rest.facing || 1), rs = swap && side ? slot.replace(/_[LR]$/, '_' + (side === 'L' ? 'R' : 'L')) : slot;
        key = rest.order.indexOf(rs) * 10 + .25 * dep;           // the rest stack, re-sorted only by big depth changes
        if (sideView && rest.far && side) far = !!rest.far[rs];
      }
      out.push({ slot, p, M, depth: key, far, cls, side, dep });
    }
    out.sort((a, b) => a.depth - b.depth);
    return out;
  }

  // ---------------------------------------------------------------- weight: COM, support, loads (Bolas crash-lab rules)
  function comOf(J) {
    let m = 0, c = [0, 0, 0];
    for (const [a, b, w, f] of MASS) { const p = add(J[a], mul(sub(J[b], J[a]), f)); c = add(c, mul(p, w)); m += w; }
    return mul(c, 1 / m);
  }
  function hull2(pts) {
    if (pts.length < 3) return pts.slice();
    const P = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const lo = [], hi = [];
    for (const p of P) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
    for (let i = P.length - 1; i >= 0; i--) { const p = P[i]; while (hi.length >= 2 && cr(hi[hi.length - 2], hi[hi.length - 1], p) <= 0) hi.pop(); hi.push(p); }
    hi.pop(); lo.pop(); return lo.concat(hi);
  }
  function segDist2(p, a, b) { const dx = b[0] - a[0], dy = b[1] - a[1]; const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy || 1))); return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy); }
  function inPoly(pt_, poly, margin = 0) {
    if (poly.length < 3) { if (!poly.length) return false; let d = 1e9; for (let i = 0; i < poly.length; i++) d = Math.min(d, segDist2(pt_, poly[i], poly[(i + 1) % poly.length])); return d < 6 + margin; }
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const a = poly[i], b = poly[j]; if (((a[1] > pt_[1]) !== (b[1] > pt_[1])) && (pt_[0] < (b[0] - a[0]) * (pt_[1] - a[1]) / (b[1] - a[1]) + a[0])) inside = !inside; }
    if (inside) return true;
    let d = 1e9; for (let i = 0; i < poly.length; i++) d = Math.min(d, segDist2(pt_, poly[i], poly[(i + 1) % poly.length])); return d < margin;
  }
  // world points (body frame + T, floor at Y = 0): what holds the body up
  const SUPJ = [['pelvis', 16], ['knL', 7], ['knR', 7], ['wrL', 9], ['wrR', 9], ['elL', 6], ['elR', 6]];
  function groundPts(J, T) {
    const W = n => add(J[n], T || [0, 0, 0]); const g = [];
    for (const S of ['L', 'R']) for (const k of ['heel', 'ball', 'toe']) { const q = W(k + S); if (q[1] > -2.5) g.push({ x: q[0], z: q[2], side: S, k, h: -q[1] }); }
    for (const [k, hi] of SUPJ) { const q = W(k); if (q[1] > -hi && q[1] < 3) g.push({ x: q[0], z: q[2], side: 'X', k }); }
    return g;
  }
  function weight(J, T, windowPts) {
    const com = add(comOf(J), T || [0, 0, 0]);
    const gp = groundPts(J, T);
    const pts = (windowPts || gp).map(g => [g.x, g.z]);
    const support = hull2(pts);
    const air = !gp.length;
    const balanced = !air && inPoly([com[0], com[2]], support, windowPts ? 5 : 3);
    const gL = gp.filter(g => g.side === 'L'), gR = gp.filter(g => g.side === 'R');
    const load = { L: 0, R: 0 };
    const cen = L => [L.reduce((s, g) => s + g.x, 0) / L.length, L.reduce((s, g) => s + g.z, 0) / L.length];
    if (gL.length && gR.length) { const cL = cen(gL), cR = cen(gR); const dL = Math.hypot(com[0] - cL[0], com[2] - cL[1]) + 1, dR = Math.hypot(com[0] - cR[0], com[2] - cR[1]) + 1; load.L = dR / (dL + dR); load.R = dL / (dL + dR); }
    else if (gL.length) load.L = 1; else if (gR.length) load.R = 1;
    // feet: the left foot stays on the left (body frame), crash-lab rule
    const flags = [];
    if (gL.length && gR.length) { const xb = n => J[n][0]; if (xb('ballL') < xb('ballR') - 2 && xb('heelL') < xb('heelR') - 2) flags.push('feet crossed'); }
    if (!air && !balanced) flags.push('centre of mass outside the support');
    return { com, gp, support, air, balanced, load, flags, restOn: gp.filter(g => g.side === 'X').map(g => g.k) };
  }

  // ---------------------------------------------------------------- target problem (live solver)
  function chamfer(mask, W, H) {      // distance (px) to the nearest inside pixel, 3-4 chamfer, 0 inside
    const d = new Float32Array(W * H), INF = 1e9;
    for (let i = 0; i < W * H; i++) d[i] = mask[i] ? 0 : INF;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const i = y * W + x; let v = d[i]; if (!v) continue;
      if (x > 0) v = Math.min(v, d[i - 1] + 3); if (y > 0) { v = Math.min(v, d[i - W] + 3); if (x > 0) v = Math.min(v, d[i - W - 1] + 4); if (x < W - 1) v = Math.min(v, d[i - W + 1] + 4); } d[i] = v; }
    for (let y = H - 1; y >= 0; y--) for (let x = W - 1; x >= 0; x--) { const i = y * W + x; let v = d[i]; if (!v) continue;
      if (x < W - 1) v = Math.min(v, d[i + 1] + 3); if (y < H - 1) { v = Math.min(v, d[i + W] + 3); if (x < W - 1) v = Math.min(v, d[i + W + 1] + 4); if (x > 0) v = Math.min(v, d[i + W - 1] + 4); } d[i] = v; }
    for (let i = 0; i < W * H; i++) d[i] /= 3;
    return d;
  }
  function contour(mask, W, H, n = 48) {
    const pts = [];
    for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) { const i = y * W + x; if (mask[i] && (!mask[i - 1] || !mask[i + 1] || !mask[i - W] || !mask[i + W])) pts.push([x, y]); }
    if (!pts.length) return [];
    const cx = pts.reduce((s, p) => s + p[0], 0) / pts.length, cy = pts.reduce((s, p) => s + p[1], 0) / pts.length;
    pts.sort((a, b) => Math.atan2(a[1] - cy, a[0] - cx) - Math.atan2(b[1] - cy, b[0] - cx));
    const out = []; for (let i = 0; i < n; i++) out.push(pts[Math.floor(i * pts.length / n)]);
    return out;
  }
  // target: {brads:[[x,y,r,src]], cx, floor, mask(Uint8 W*H), W, H}; returns a Problem
  function problem(S, target, psi, s0, ssig, opt = {}) {
    const pr = { S, t: target, psi, s0, ssig: ssig || .15, sandbox: !!opt.sandbox, flat: 3 };
    if (target.mask && !target.dt) { target.dt = chamfer(target.mask, target.W, target.H); target.C = contour(target.mask, target.W, target.H); }
    pr.setStretch = on => { [pr.lo, pr.hi] = lims(pr.sandbox, on); const w = on ? .05 : Math.min(Math.log(1.8), 2.2 * pr.ssig); pr.lo[NP] = -w; pr.hi[NP] = w; };
    pr.setStretch(false);
    pr.match = [];
    return pr;
  }
  function toPx(pr, xy, ls) { const s = pr.s0 * Math.exp(ls); return [xy[0] * s + pr.t.cx, xy[1] * s + pr.t.floor]; }
  function dtAt(t, x, y) {
    const W = t.W, H = t.H; let ex = 0;
    if (x < 0) { ex += -x; x = 0; } if (x > W - 1) { ex += x - W + 1; x = W - 1; }
    if (y < 0) { ex += -y; y = 0; } if (y > H - 1) { ex += y - H + 1; y = H - 1; }
    const x0 = Math.floor(x), y0 = Math.floor(y), x1 = Math.min(W - 1, x0 + 1), y1 = Math.min(H - 1, y0 + 1), fx = x - x0, fy = y - y0, d = t.dt;
    return ex + d[y0 * W + x0] * (1 - fx) * (1 - fy) + d[y0 * W + x1] * fx * (1 - fy) + d[y1 * W + x0] * (1 - fx) * fy + d[y1 * W + x1] * fx * fy;
  }
  function residuals(pr, z, stage) {
    const S = pr.S, x = z, ls = z[NP], s = pr.s0 * Math.exp(ls), J = fk(S, x), out = [];
    const P = {}; const pj = n => P[n] || (P[n] = toPx(pr, project(J[n], pr.psi, x[0], x[1]), ls));
    const B = pr.t.brads;
    if (stage === 'M') {
      for (const n in pr.t.markers || {}) { const m = pr.t.markers[n]; if (!m || m[2] <= 0 || !MARKER_J[n]) continue; const q = pj(MARKER_J[n]), w = m[2] * (MW[n] || 1); out.push(w * (q[0] - m[0]) / s, w * (q[1] - m[1]) / s); }
    } else if (B.length) {
      if (stage === 'A') {
        const jp = JOINTS.map(pj);
        const dj = new Array(JOINTS.length).fill(1e9);
        for (const b of B) { let m = 1e9; jp.forEach((q, j) => { const d = Math.hypot(q[0] - b[0], q[1] - b[1]) / s; if (d < m) m = d; if (d < dj[j]) dj[j] = d; }); out.push(m); }
        for (const d of dj) out.push(.5 * Math.min(d, 12));
      } else for (const [bi, ji] of pr.match) { const q = pj(JOINTS[ji]), b = B[bi]; out.push(1.5 * (q[0] - b[0]) / s, 1.5 * (q[1] - b[1]) / s); }
    }
    if (pr.t.dt) {
      for (const n of INSIDE) { const q = pj(n); out.push(.7 * dtAt(pr.t, q[0], q[1]) / s); }
      for (const c of pr.t.C) {
        let m = 1e9;
        for (const [a, b, rad] of SEGS) { const A = pj(a), Bq = pj(b); m = Math.min(m, segDist2(c, A, Bq) / s - rad); }
        out.push(.45 * Math.max(0, m));
      }
    }
    for (const [a, b] of FLAT) { const pa = project(J[a], pr.psi), pb = project(J[b], pr.psi); const L3 = len3(sub(J[b], J[a])); out.push(pr.flat * (Math.hypot(pb[0] - pa[0], pb[1] - pa[1]) / Math.max(L3, 1e-6) - 1)); }
    for (const i of ANG) out.push(.35 * x[i] / 90);
    for (let i = 3; i < 6; i++) out.push(.25 * x[i] / 90);
    for (const n of KN) out.push(x[PI[n]] / .07);
    out.push(ls / pr.ssig);
    return out;
  }
  const STEP = PN.map(n => KN.includes(n) ? .002 : .05).concat([.002]);
  // projected Levenberg-Marquardt with soft_l1 (IRLS) weights, as scipy's least_squares(loss='soft_l1', f_scale=3)
  function solve(pr, z0, stage, iters = 40, fscale = 3) {
    const n = NP + 1, lo = pr.lo, hi = pr.hi;
    let z = Float64Array.from(z0).map((v, i) => Math.min(hi[i] - 1e-8, Math.max(lo[i] + 1e-8, v)));
    const robust = r => { const w = new Float64Array(r.length); let c = 0; for (let i = 0; i < r.length; i++) { const q = r[i] / fscale; w[i] = 1 / Math.sqrt(Math.sqrt(1 + q * q)); c += 2 * fscale * fscale * (Math.sqrt(1 + q * q) - 1); } return [w, c]; };
    let r = residuals(pr, z, stage), [w, cost] = robust(r), lam = 1e-2;
    const free = i => hi[i] - lo[i] > 1e-4;
    for (let it = 0; it < iters; it++) {
      const m = r.length, Jm = [];
      for (let j = 0; j < n; j++) { if (!free(j)) { Jm.push(null); continue; } const z2 = Float64Array.from(z); z2[j] += STEP[j]; const r2 = residuals(pr, z2, stage); const col = new Float64Array(m); for (let i = 0; i < m; i++) col[i] = (r2[i] - r[i]) / STEP[j]; Jm.push(col); }
      const A = Array.from({ length: n }, () => new Float64Array(n)), g = new Float64Array(n);
      for (let a = 0; a < n; a++) { if (!Jm[a]) { A[a][a] = 1; continue; } for (let i = 0; i < m; i++) g[a] += Jm[a][i] * w[i] * w[i] * r[i];
        for (let b = a; b < n; b++) { if (!Jm[b]) continue; let s_ = 0; for (let i = 0; i < m; i++) s_ += Jm[a][i] * w[i] * w[i] * Jm[b][i]; A[a][b] = A[b][a] = s_; } }
      let improved = false;
      for (let tries = 0; tries < 6; tries++) {
        const M = A.map((row, i) => { const q = Float64Array.from(row); if (Jm[i]) q[i] += lam * (row[i] + 1e-6); return q; });
        const dz = gauss(M, Array.from(g, v => -v));
        const z2 = Float64Array.from(z, (v, i) => Jm[i] ? Math.min(hi[i] - 1e-8, Math.max(lo[i] + 1e-8, v + dz[i])) : v);
        const r2 = residuals(pr, z2, stage), [w2, c2] = robust(r2);
        if (c2 < cost) { z = z2; r = r2; w = w2; const dc = cost - c2; cost = c2; lam = Math.max(1e-6, lam / 3); improved = true; if (dc < 1e-6 * (1 + cost)) it = iters; break; }
        lam *= 4;
      }
      if (!improved) break;
    }
    return { z, cost: cost / 2 };
  }
  // generic projected Levenberg-Marquardt: fun(x) -> residual array; used by the loop solver (pinned feet)
  function lm(fun, x0, lo, hi, steps, iters = 25) {
    const n = x0.length; let x = Float64Array.from(x0, (v, i) => Math.min(hi[i], Math.max(lo[i], v)));
    let r = fun(x), cost = r.reduce((s, v) => s + v * v, 0), lam = 1e-2;
    for (let it = 0; it < iters; it++) {
      const m = r.length, Jm = [];
      for (let j = 0; j < n; j++) { const x2 = Float64Array.from(x); x2[j] += steps[j]; const r2 = fun(x2); const c = new Float64Array(m); for (let i = 0; i < m; i++) c[i] = (r2[i] - r[i]) / steps[j]; Jm.push(c); }
      const A = Array.from({ length: n }, () => new Float64Array(n)), g = new Float64Array(n);
      for (let a = 0; a < n; a++) { for (let i = 0; i < m; i++) g[a] += Jm[a][i] * r[i]; for (let b = a; b < n; b++) { let s_ = 0; for (let i = 0; i < m; i++) s_ += Jm[a][i] * Jm[b][i]; A[a][b] = A[b][a] = s_; } }
      let ok = false;
      for (let t = 0; t < 6; t++) {
        const M = A.map((row, i) => { const q = Float64Array.from(row); q[i] += lam * (row[i] + 1e-6); return q; });
        const dx = gauss(M, Array.from(g, v => -v)), x2 = Float64Array.from(x, (v, i) => Math.min(hi[i], Math.max(lo[i], v + dx[i])));
        const r2 = fun(x2), c2 = r2.reduce((s, v) => s + v * v, 0);
        if (c2 < cost) { const dc = cost - c2; x = x2; r = r2; cost = c2; lam = Math.max(1e-6, lam / 3); ok = true; if (dc < 1e-7 * (1 + cost)) it = iters; break; }
        lam *= 4;
      }
      if (!ok) break;
    }
    return { x, cost };
  }
  function gauss(A, b) {
    const n = b.length, M = A.map((row, i) => Array.from(row).concat([b[i]]));
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      [M[c], M[p]] = [M[p], M[c]]; const d = M[c][c] || 1e-12;
      for (let r = 0; r < n; r++) if (r !== c) { const f = M[r][c] / d; if (f) for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k]; }
    }
    return M.map((row, i) => row[n] / (row[i] || 1e-12));
  }
  // Hungarian (Kuhn-Munkres) for a rows x cols cost matrix, rows <= cols; returns [[row, col]]
  function hungarian(C) {
    const n = C.length, m = C[0].length, INF = 1e18, u = new Float64Array(n + 1), v = new Float64Array(m + 1), p = new Int32Array(m + 1), way = new Int32Array(m + 1);
    for (let i = 1; i <= n; i++) {
      p[0] = i; let j0 = 0; const minv = new Float64Array(m + 1).fill(INF), used = new Uint8Array(m + 1);
      do { used[j0] = 1; const i0 = p[j0]; let delta = INF, j1 = 0;
        for (let j = 1; j <= m; j++) if (!used[j]) { const cur = C[i0 - 1][j - 1] - u[i0] - v[j]; if (cur < minv[j]) { minv[j] = cur; way[j] = j0; } if (minv[j] < delta) { delta = minv[j]; j1 = j; } }
        for (let j = 0; j <= m; j++) if (used[j]) { u[p[j]] += delta; v[j] -= delta; } else minv[j] -= delta;
        j0 = j1; } while (p[j0] !== 0);
      do { const j1 = way[j0]; p[j0] = p[j1]; j0 = j1; } while (j0);
    }
    const out = []; for (let j = 1; j <= m; j++) if (p[j]) out.push([p[j] - 1, j - 1]); return out;
  }
  function jointsPx(pr, z) { const J = fk(pr.S, z); return JOINTS.map(n => toPx(pr, project(J[n], pr.psi, z[0], z[1]), z[NP])); }
  function doMatch(pr, z, gate = 9) {
    const B = pr.t.brads; if (!B.length) { pr.match = []; return; }
    const jp = jointsPx(pr, z), s = pr.s0 * Math.exp(z[NP]);
    const D = B.map(b => jp.map(q => { const d = Math.hypot(q[0] - b[0], q[1] - b[1]) / s; return d < gate ? d : 1e3; }));
    let pairs;
    if (B.length <= JOINTS.length) pairs = hungarian(D);
    else pairs = hungarian(JOINTS.map((_, j) => B.map((_, b) => D[b][j]))).map(([j, b]) => [b, j]);
    pr.match = pairs.filter(([b, j]) => D[b][j] < 1e3);
  }
  function errors(pr, z) {
    const jp = jointsPx(pr, z), s = pr.s0 * Math.exp(z[NP]), e = {};
    for (const [bi, ji] of pr.match) { const b = pr.t.brads[bi]; e[JOINTS[ji]] = Math.hypot(jp[ji][0] - b[0], jp[ji][1] - b[1]) / s; }
    return e;
  }
  function markerErrors(pr, z) {
    const J = fk(pr.S, z), s = pr.s0 * Math.exp(z[NP]), e = {};
    for (const n in pr.t.markers || {}) { const m = pr.t.markers[n]; if (!m || m[2] <= 0) continue; const q = toPx(pr, project(J[MARKER_J[n]], pr.psi, z[0], z[1]), z[NP]); e[n] = Math.hypot(q[0] - m[0], q[1] - m[1]) / s; }
    return e;
  }
  // the same joint angles on the rig as built (k = 0): feet on the target's floor, centred on the markers
  function rigidify(pr, z) {
    const o = Float64Array.from(z); for (const n of KN) o[PI[n]] = 0;
    const J = fk(pr.S, o);
    let low = -1e9; for (const n of ['heelL', 'heelR', 'toeL', 'toeR', 'knL', 'knR', 'pelvis', 'tipL', 'tipR', 'wrL', 'wrR', 'top']) low = Math.max(low, J[n][1]);
    o[PI.oy] = -low;
    const s = pr.s0 * Math.exp(o[NP]), dx = [];
    const M = pr.t.markers || {};
    for (const n in M) { const m = M[n]; if (!m || m[2] <= 0 || !MARKER_J[n]) continue; const q = project(J[MARKER_J[n]], pr.psi, o[0], o[1]); dx.push((m[0] - (q[0] * s + pr.t.cx)) / s); }
    if (!dx.length) for (const [bi, ji] of pr.match || []) { const q = project(J[JOINTS[ji]], pr.psi, o[0], o[1]); dx.push((pr.t.brads[bi][0] - (q[0] * s + pr.t.cx)) / s); }
    if (dx.length) { dx.sort((a, b) => a - b); o[PI.ox] += dx[dx.length >> 1]; }
    return o;
  }
  function markerPx(pr, z) { const J = fk(pr.S, z); const o = {}; for (const [n, j] of MARKERS) o[n] = toPx(pr, project(J[j], pr.psi, z[0], z[1]), z[NP]); return o; }
  function scoreOf(iou, e, opt) {
    const vals = Object.values(e), mean = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 12;
    const names = opt && opt.names || JOINTS;
    const fit = 1 / (1 + (mean / 4) ** 2), cover = Math.min(1, vals.length / names.length);
    return { score: iou * (.55 + .45 * fit) * (.7 + .3 * cover), mean, flagged: Object.keys(e).filter(k => e[k] > 4), unmatched: names.filter(j => !(j in e)) };
  }
  function fromParams(params, scale, s0) {
    const z = new Float64Array(NP + 1);
    for (const k in params) if (k in PI) z[PI[k]] = params[k];
    z[NP] = scale && s0 ? Math.log(scale / s0) : 0;
    return z;
  }
  function toParams(z) { const o = {}; PN.forEach((n, i) => o[n] = +(+z[i]).toFixed(2)); return o; }
  function mirror(z) {   // the same pose with the actor's L and R exchanged (for walk cycles)
    const o = Float64Array.from(z);
    const sw = (a, b) => { const t = o[PI[a]]; o[PI[a]] = o[PI[b]]; o[PI[b]] = t; };
    [['shLf', 'shRf'], ['shLb', 'shRb'], ['elL', 'elR'], ['wrL', 'wrR'], ['hpLf', 'hpRf'], ['hpLb', 'hpRb'], ['knL', 'knR'], ['anL', 'anR'], ['shLt', 'shRt'], ['hpLt', 'hpRt']].forEach(([a, b]) => sw(a, b));
    for (const n of ['roll', 'twist', 'tb', 'hb']) o[PI[n]] = -o[PI[n]];
    return o;
  }

  // MoveNet keypoints (17: nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles; person's L/R) + painted
  // brads + the silhouette -> labelled markers {name: [x, y, weight, src, conf]} in target px
  const MN = ['nose', 'eyeL', 'eyeR', 'earL', 'earR', 'shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR'];
  function prefillMarkers(kps, brads, mask, W, H, bbox) {
    const K = {}; MN.forEach((n, i) => K[n] = kps[i]);
    const figH = (bbox ? bbox[3] - bbox[1] : H) || H, M = {};
    const put = (n, p, conf, src) => { M[n] = [+p[0].toFixed(1), +p[1].toFixed(1), conf < .15 ? .3 : .5 + conf, src, +conf.toFixed(3)]; };
    for (const n of ['shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR']) put(n, K[n], K[n][2], 'movenet');
    const midp = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, Math.min(a[2], b[2])];
    const neck = midp(K.shoulderL, K.shoulderR); put('neck', neck, neck[2], 'movenet');
    const groin = midp(K.hipL, K.hipR); put('groin', groin, groin[2], 'movenet');
    const nose = K.nose; put('chin', [nose[0] + (neck[0] - nose[0]) * .4, nose[1] + (neck[1] - nose[1]) * .4], Math.min(nose[2], neck[2]), 'movenet');
    // crown: walk from the nose away from the neck until the silhouette ends
    const inside = (x, y) => x >= 0 && y >= 0 && x < W && y < H && mask[(y | 0) * W + (x | 0)];
    let d = [nose[0] - neck[0], nose[1] - neck[1]]; const dl = Math.hypot(d[0], d[1]) || 1; d = [d[0] / dl, d[1] / dl];
    let cr = [nose[0], nose[1]]; for (let t = 0; t < figH * .25; t++) { const q = [nose[0] + d[0] * t, nose[1] + d[1] * t]; if (inside(q[0], q[1])) cr = q; else if (t > 4) break; }
    put('head', cr, nose[2], 'movenet+silhouette');
    // toes: the silhouette pixel farthest from each ankle, below it, within 13% of the figure height
    for (const sd of ['L', 'R']) {
      const a = K['ankle' + sd], R = .13 * figH; let best = null, bd = -1;
      for (let y = Math.max(0, a[1] | 0); y < Math.min(H, a[1] + R); y += 2) for (let x = Math.max(0, (a[0] - R) | 0); x < Math.min(W, a[0] + R); x += 2) if (mask[y * W + x]) { const dd = Math.hypot(x - a[0], y - a[1]); if (dd < R && dd > bd) { bd = dd; best = [x, y]; } }
      if (best) put('toe' + sd, best, a[2] * .8, 'silhouette');
    }
    // snap joint markers onto a painted brad when one is close (brads are the true pivots)
    const used = new Set();
    for (const n of ['shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'neck']) {
      const m = M[n]; if (!m) continue; let bi = -1, bd = .06 * figH;
      (brads || []).forEach((b, i) => { if (used.has(i)) return; const dd = Math.hypot(b[0] - m[0], b[1] - m[1]); if (dd < bd) { bd = dd; bi = i; } });
      if (bi >= 0) { used.add(bi); const b = brads[bi]; M[n] = [b[0], b[1], Math.min(2, m[2] + .5), m[3] + '+brad', m[4]]; }
    }
    return M;
  }
  const API = { rigidify, MW, MN, prefillMarkers, MARKERS, MARKER_J, MIRROR_M, markerErrors, markerPx, DEG, PN, PI, NP, LIM, KN, ANG, JOINTS, JOINT_WORD, JOINT_DOF, SEGS, MASS, NORM, SLOTS, VIEWKEYS,
    lims, fk, project, viewKey, pt, score, cardsExact, cardsFor, prep, skeleton, placeCards,
    comOf, hull2, inPoly, groundPts, weight, chamfer, contour, problem, residuals, solve, hungarian, jointsPx, doMatch,
    errors, scoreOf, fromParams, toParams, mirror, add, sub, mul, mid, lm, gauss, toPx, segDist2 };
  if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.PoseCore = API;
})(typeof self !== 'undefined' ? self : this);
