// The solver: authored beats + goals -> a per-frame state for every puppet.
//   beats  {t, who, action, word_anchor, args, contact}    authored, snapped to the reading's words
//   goals  {who, kind, args, t0, t1}                         autonomous: compiled into beats marked auto:true
// Walks are footstep plans in world cm (plants fixed in the world, swing arcs, pelvis height from leg IK);
// reaches and gestures are IK targets; card-only characters (no jointed parts yet) hop-step between plants.
import { D2R, add, sub, mul, len, norm, lerp, lerp3, smooth, wrapDeg, axes, bodyOf, poseBody, bodyPoint, viewOf } from './rig.js';
import { pip, clampToPoly, segHitsPoly, polyBox, onGround, groundOf } from './camera.js';
import { extFrame } from './ext.js';

export const ACTIONS = {
  walk_to:      { args: '{to:[x,y] | mark | surface:id, speed?, arrive_word?}', doc: 'footstep-planned walk on the ground plane; detours round occluder footprints' },
  stop:         { args: '{}', doc: 'cut the current walk short with a closing step' },
  turn:         { args: '{to: deg | camera | away | left | right | who | surface:id}', doc: 'turn in place (a view swap for cards)' },
  reach:        { args: '{side, target:{surface,at:[x,y]} | {who,socket}, hold?, dur?}', doc: 'two-bone IK to a socket or a point on a surface; logged as a contact' },
  hold_gesture: { args: '{side, name: page_up|palm_out|hand_chest|arms_up|reach_out, dur?}', doc: 'a held arm shape (IK to a body-local point)' },
  release:      { args: '{side}', doc: 'end a reach or gesture' },
  sit:          { args: '{height_cm?}', doc: 'pelvis down to seat height, feet stay planted' },
  stand:        { args: '{}', doc: 'back up from sit / crouch' },
  head_lowers:  { args: '{deg?}', doc: 'head pitches down (and swaps to the "down" head if one exists)' },
  head_raises:  { args: '{}', doc: 'head back to level' },
  hand_opens:   { args: '{side}', doc: 'swap to the open hand' },
  hand_closes:  { args: '{side, shape?}', doc: 'swap to a closed hand (relaxed / grip / fist)' },
  hand_off:     { args: '{to, prop, side?}', doc: 'both reach to the midpoint; the prop changes hands; logged as a contact' },
  wince:        { args: '{amp?}', doc: 'head dips, small crouch, recovers in 0.4 s' },
  falter:       { args: '{}', doc: 'step falters: pelvis dips, head drops, lean' },
  sway:         { args: '{bpm, amp?, bars?}', doc: 'sway to the beat (cards alternate dance cards on the beat)' },
  vanish:       { args: '{dur?}', doc: 'fade out (haze dissolve)' },
  appear:       { args: '{dur?}', doc: 'fade in' },
  swap_head:    { args: '{head}', doc: 'replacement head' },
};
export const GOALS = {
  go_to:         { args: '{target: mark|[x,y]|surface:id, word?}', doc: 'walk there (one beat, placed at the word)' },
  keep_distance: { args: '{from, min_cm, max_cm}', doc: 'when the other comes inside min_cm, step back toward the middle of the band' },
  sway_to_beat:  { args: '{bpm, amp?}', doc: 'sway on every bar of the given tempo' },
  wander:        { args: '{zone:[[x,y]...], every_bars, bpm, step_cm}', doc: 'drift within a zone, a few steps every N bars, never into another body' },
  walk_with:     { args: '{who, side:L|R, gap_cm}', doc: 'match the other\'s walks, shoulder to shoulder' },
  face:          { args: '{who | surface | camera}', doc: 'turn toward a target when it moves more than 40 degrees off' },
};

const VIEW_PHI = { profile: 0, threequarter: 40, front: 90, threequarter_back: -40, back: -90 };
export function phiFor(view, side) { const p = VIEW_PHI[view] ?? 0; return side === 'L' ? 180 - p : p; }
const headingPhi = (dX, dZ) => Math.atan2(-dZ, dX) / D2R;

function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
function trap(u, r) { // trapezoid velocity profile, position 0..1 for u in 0..1 with ramp fraction r
  r = Math.min(0.49, Math.max(0.01, r)); const vmax = 1 / (1 - r);
  if (u <= 0) return 0; if (u >= 1) return 1;
  if (u < r) return 0.5 * vmax * u * u / r;
  if (u > 1 - r) { const w = 1 - u; return 1 - 0.5 * vmax * w * w / r; }
  return 0.5 * vmax * r + vmax * (u - r);
}

export function wordAt(words, anchor, near) {
  if (anchor == null) return null;
  if (typeof anchor === 'number') return words[anchor] ? { i: anchor, w: words[anchor] } : null;
  const want = String(anchor).toLowerCase().replace(/[^a-z0-9']/g, '');
  let best = null;
  words.forEach((w, i) => {
    if (w[0].toLowerCase().replace(/[^a-z0-9']/g, '') !== want) return;
    if (!best || (near != null && Math.abs(w[1] - near) < Math.abs(best.w[1] - near))) best = { i, w };
  });
  return best;
}
export function snapBeats(scene, words) { // beats with a word_anchor take that word's start time
  for (const b of scene.beats || []) {
    const hit = wordAt(words, b.word_anchor, b.t);
    if (hit) { b.t = +hit.w[1].toFixed(3); b.word_i = hit.i; }
  }
}

// ───────────────────────── compile ─────────────────────────
export function compileScene(scene, ctx) {
  const fps = scene.fps || 24, N = Math.round(scene.duration * fps);
  const { cam, set } = ctx;
  const words = scene.audio?.words || [];
  snapBeats(scene, words);
  for (const j of scene.joins || []) { const hit = wordAt(words, j.word_anchor, j.t); if (hit) j.t = +hit.w[1].toFixed(3); const he = wordAt(words, j.end_word, j.t_end); if (he) j.t_end = +he.w[2].toFixed(3); }
  // a touch join is a reach to a surface: it becomes a beat, and the surface's clip is gated by the contact
  const touchBeats = [];
  for (const j of (scene.joins || []).filter(j => j.kind === 'touch' && j.who)) {
    touchBeats.push({ t: j.t, who: j.who, action: 'reach', args: { side: j.side || 'R', target: { surface: j.surface, at: j.at }, hand: 'open', dur: j.reach_s || 0.6 }, auto: true, goal: 'touch join', why: `touch ${j.surface}` });
    touchBeats.push({ t: j.t_end ?? scene.duration, who: j.who, action: 'release', args: { side: j.side || 'R' }, auto: true, goal: 'touch join' });
    j.gate = { who: j.who, side: j.side || 'R', floor: j.floor ?? 0 };
  }
  const authoredBeats = scene.beats;
  scene = { ...scene, beats: [...(scene.beats || []), ...touchBeats] };
  const out = { fps, N, chars: {}, contacts: [], auto: [...touchBeats], log: [], order: [] };
  const cast = scene.cast || [];
  const goalsOf = id => (scene.goals || []).filter(g => g.who === id);
  // dependency order: no goals first, then goal-driven characters whose dependencies are compiled
  const pending = cast.map(c => c.id);
  const deps = id => goalsOf(id).map(g => g.args?.from || g.args?.who).filter(Boolean);
  let guard = 0;
  while (pending.length && guard++ < 50) {
    for (let k = 0; k < pending.length; k++) {
      const id = pending[k];
      if (deps(id).every(d => out.chars[d] || d === id || !cast.find(c => c.id === d))) {
        const c = cast.find(x => x.id === id);
        out.chars[id] = compileChar(c, scene, ctx, out, fps, N);
        out.order.push(id); pending.splice(k, 1); k--;
      }
    }
  }
  for (const id of pending) { const c = cast.find(x => x.id === id); out.chars[id] = compileChar(c, scene, ctx, out, fps, N); out.order.push(id); }
  // second pass for reach targets on other characters (sockets need the other's frames)
  for (const id of out.order) out.chars[id].cardFor = fr => ctx.pickCard ? ctx.pickCard(ctx, out.chars[id], fr) : null;
  for (const id of out.order) resolveTargets(out.chars[id], out, ctx);
  for (const id of out.order) out.contacts.push(...out.chars[id].contacts);
  return out;
}

function charSpec(c, ctx) {
  const base = ctx.characters[c.character] || { id: c.character, height_cm: 175 };
  const ch = base.byCostume?.[c.costume] || base;
  const B = bodyOf(ch);
  const hasJointed = ctx.parts.some(p => p.character === c.character && p.part === 'torso' && (!c.costume || !p.costume || p.costume === c.costume || c.costume_fallback));
  const mode = c.mode || (hasJointed ? 'jointed' : (ch.suite_mode === 'jointed' && ctx.parts.some(p => p.character === c.character && p.part === 'torso') ? 'jointed' : 'cards'));
  const allowed = ch.view_rule?.allowed || (c.id === 'EX' ? ['back', 'threequarter_back'] : null);
  return { ch, B, mode, allowed, stride: c.stride_cm || ch.walk?.stride_cm || 0.36 * B.H, stepT: (ch.walk?.cycle_frames || 26) / 24 / 2 };
}

function clampPhi(phi, allowed) {
  if (!allowed) return phi;
  const v = viewOf(phi).view;
  if (allowed.includes(v)) return phi;
  // nearest allowed facing: back views live in sin(phi) < -0.47
  const c = Math.cos(phi * D2R);
  return c >= 0 ? -32 : -148;
}

function resolvePoint(spec, set, cam, fallback) {
  if (!spec) return fallback;
  if (Array.isArray(spec)) return spec;
  if (typeof spec === 'string') {
    if (set.marks[spec]) return set.marks[spec];
    if (spec.startsWith('surface:')) { const s = set.surfaces.find(x => x.id === spec.slice(8)); if (s?.stand) return s.stand; }
    if (set.marks[spec.replace(/^mark:/, '')]) return set.marks[spec.replace(/^mark:/, '')];
  }
  if (spec.mark && set.marks[spec.mark]) return set.marks[spec.mark];
  return fallback;
}

// a straight ground path (screen ground points) with one detour round any occluder footprint it crosses
function planPath(a, b, set) {
  const pts = [a], ground = groundOf(a, set);
  for (const o of set.occluders) {
    const fp = o.footprint; if (!fp) continue;
    if (segHitsPoly(pts[pts.length - 1], b, fp)) {
      const [x0, y0, x1, y1] = polyBox(fp), m = 30;
      const corners = [[x0 - m, y0 - m], [x1 + m, y0 - m], [x1 + m, y1 + m], [x0 - m, y1 + m]].filter(p => pip(p, ground) && !pip(p, fp));
      corners.sort((p, q) => (Math.hypot(p[0] - a[0], p[1] - a[1]) + Math.hypot(b[0] - p[0], b[1] - p[1])) - (Math.hypot(q[0] - a[0], q[1] - a[1]) + Math.hypot(b[0] - q[0], b[1] - q[1])));
      if (corners[0]) pts.push(corners[0]);
    }
  }
  pts.push(clampToPoly(b, ground));
  return pts;
}

function compileChar(c, scene, ctx, out, fps, N) {
  const { cam, set } = ctx;
  const S = charSpec(c, ctx);
  const words = scene.audio?.words || [];
  const authored = (scene.beats || []).filter(b => b.who === c.id);
  let beats = authored.map(b => ({ ...b }));
  const tr = { id: c.id, cast: c, ...S, frames: [], beats, walks: [], contacts: [], log: [] };
  const build = () => { tr.beats = beats.sort((a, b) => a.t - b.t); buildFrames(tr, scene, ctx, out, fps, N); };
  build();
  // goals -> auto beats
  for (const g of (scene.goals || []).filter(g => g.who === c.id)) {
    const made = runGoal(g, tr, scene, ctx, out, fps, N, build, () => beats, nb => { beats.push(nb); build(); });
    for (const b of made) out.auto.push(b);
  }
  return tr;
}

function posAt(tr, t, fps) { const f = Math.max(0, Math.min(tr.frames.length - 1, Math.round(t * fps))); return tr.frames[f]; }

function runGoal(g, tr, scene, ctx, out, fps, N, build, getBeats, push) {
  const { cam, set } = ctx, made = [], words = scene.audio?.words || [];
  const t0 = g.t0 ?? 0, t1 = Math.min(g.t1 ?? scene.duration, scene.duration), a = g.args || {};
  const B = tr.B;
  const mk = (t, action, args, why) => { const b = { t: +t.toFixed(3), who: tr.id, action, args, auto: true, goal: g.kind, why }; push(b); made.push(b); return b; };
  const walkingAt = t => tr.walks.some(w => t >= w.t0 - 0.05 && t <= w.t1 + 0.05);
  if (g.kind === 'go_to') {
    const hit = wordAt(words, a.word, t0); const t = hit ? hit.w[1] : t0;
    mk(t, 'walk_to', { to: a.target, speed: a.speed }, `goal go_to ${JSON.stringify(a.target)}`);
  } else if (g.kind === 'keep_distance') {
    const other = out.chars[a.from]; if (!other) return made;
    const min = a.min_cm || 250, max = a.max_cm || min * 1.6;
    for (let t = t0; t <= t1; t += 0.25) {
      if (walkingAt(t)) continue;
      const p = posAt(tr, t, fps), q = posAt(other, t, fps);
      const d = Math.hypot(p.X - q.X, p.Z - q.Z);
      if (d < min) {
        const want = (min + max) / 2, k = (want - d) / Math.max(d, 1);
        const X = p.X + (p.X - q.X) * k, Z = p.Z + (p.Z - q.Z) * k;
        let to = cam.worldToGround(X, Math.max(Z, 50));
        to = clampToPoly(to, a.zone || groundOf(cam.worldToGround(p.X, p.Z), set));
        const from = cam.worldToGround(p.X, p.Z);
        if (Math.hypot(to[0] - from[0], to[1] - from[1]) < 6) { tr.log.push(`keep_distance: boxed in at t=${t.toFixed(2)}s (d=${d.toFixed(0)} cm)`); continue; }
        mk(t, 'walk_to', { to: to.map(v => Math.round(v)), keep_facing: !!tr.allowed, speed: a.speed || 0.8 }, `keep ${min}-${max} cm from ${a.from}: was ${d.toFixed(0)} cm`);
        t = (tr.walks[tr.walks.length - 1]?.t1 ?? t) + 0.25;
      }
    }
  } else if (g.kind === 'sway_to_beat') {
    const bpm = a.bpm || 120, bar = 240 / bpm;
    const ph = a.phase || 0;
    for (let t = t0 + ph; t < t1 - 0.1; t += bar) mk(t, 'sway', { bpm, amp: a.amp || 1, bars: 1 }, `sway @${bpm} bpm`);
  } else if (g.kind === 'wander') {
    const bpm = a.bpm || 120, bar = 240 / bpm, every = a.every_bars || 2, R = rng(a.seed || (tr.id.length * 7919));
    const zone = a.zone || set.walkable;
    for (let t = t0 + bar * (0.5 + R()); t < t1 - 1.2; t += bar * every) {
      if (walkingAt(t)) continue;
      const p = posAt(tr, t, fps);
      let best = null;
      for (let k = 0; k < 12; k++) {
        const ang = R() * Math.PI * 2, r = (a.step_cm || 60) * (0.5 + R());
        const X = p.X + Math.cos(ang) * r, Z = p.Z + Math.sin(ang) * r;
        const g2 = cam.worldToGround(X, Math.max(Z, 50));
        if (!pip(g2, zone)) continue;
        // clearance from every other body at the time of arrival (compiled so far)
        let clear = Infinity;
        for (const o of Object.values(out.chars)) {
          if (o.id === tr.id) continue;
          const q = posAt(o, Math.min(t + 1.2, scene.duration), fps);
          clear = Math.min(clear, Math.hypot(X - q.X, Z - q.Z) - (B.radius + o.B.radius));
        }
        if (clear > 15 && (!best || clear > best.clear)) best = { g2, clear };
      }
      if (best) mk(t, 'walk_to', { to: best.g2.map(v => Math.round(v)), speed: a.speed || 0.7, keep_facing: true }, `wander (clearance ${best.clear.toFixed(0)} cm)`);
    }
  } else if (g.kind === 'walk_with') {
    const other = out.chars[a.who]; if (!other) return made;
    const gap = a.gap_cm || 55, sg = a.side === 'L' ? 1 : -1;
    for (const w of other.walks) {
      const end = w.endWorld, hd = w.endHeading;
      const left = [Math.sin(hd * D2R), Math.cos(hd * D2R)];
      const X = end[0] + left[0] * sg * gap, Z = end[1] + left[1] * sg * gap;
      mk(Math.max(0, w.t0 + (a.lag || 0)), 'walk_to', { to: cam.worldToGround(X, Z).map(v => Math.round(v)), arrive_t: w.t1 + (a.lag || 0) }, `walk with ${a.who} (${a.side || 'R'} side, ${gap} cm)`);
    }
  } else if (g.kind === 'face') {
    let last = null;
    for (let t = t0; t <= t1; t += 0.25) {
      if (walkingAt(t)) continue;
      const p = posAt(tr, t, fps); let tx, tz;
      if (a.who && out.chars[a.who]) { const q = posAt(out.chars[a.who], t, fps); tx = q.X; tz = q.Z; }
      else if (a.surface) { const s = set.surfaces.find(x => x.id === a.surface); const [cx, , , cy] = [...centroid(s.polygon), 0, s.base_y || cam.yg]; [tx, tz] = cam.groundToWorld(centroid(s.polygon)[0], s.base_y || cam.yg); }
      else continue;
      const want = clampPhi(headingPhi(tx - p.X, tz - p.Z), tr.allowed);
      if (Math.abs(wrapDeg(want - p.phi)) > 40 && (last == null || t - last > 1)) { mk(t, 'turn', { to: Math.round(want) }, `face ${a.who || a.surface}`); last = t; }
    }
  }
  return made;
}
const centroid = poly => poly.reduce((s, p) => [s[0] + p[0] / poly.length, s[1] + p[1] / poly.length], [0, 0]);

// ── build every frame of one character from its beats ──
function buildFrames(tr, scene, ctx, out, fps, N) {
  const { cam, set } = ctx, c = tr.cast, B = tr.B;
  const words = scene.audio?.words || [];
  const [X0, Z0] = cam.groundToWorld(c.place[0], c.place[1]);
  let phi0 = c.facing ?? phiFor(c.view || 'front', c.side || 'R');
  phi0 = clampPhi(phi0, tr.allowed);
  // feet start either side of the root
  const ax0 = axes(phi0);
  const footAt = (X, Z, phi, s) => { const a = axes(phi), sg = s === 'L' ? 1 : -1; return { X: X + a.left[0] * sg * B.hipHalf * 1.1, Z: Z + a.left[2] * sg * B.hipHalf * 1.1, dir: phi }; };
  // ---- locomotion ----
  tr.walks = [];
  let cur = { X: X0, Z: Z0, phi: phi0, feet: { L: footAt(X0, Z0, phi0, 'L'), R: footAt(X0, Z0, phi0, 'R') }, t: 0 };
  const turns = [{ t: 0, phi: phi0, dur: 0 }];
  for (const b of tr.beats) {
    if (b.action === 'turn') {
      let to = b.args?.to; let phi;
      if (typeof to === 'number') phi = to;
      else if (to === 'camera') phi = 90; else if (to === 'away') phi = -90; else if (to === 'left') phi = 180; else if (to === 'right') phi = 0;
      else if (typeof to === 'string' && VIEW_PHI[to] != null) phi = phiFor(to, b.args?.side || 'R');
      if (phi != null) turns.push({ t: b.t, phi: clampPhi(phi, tr.allowed), dur: b.args?.dur || 0.3 });
    }
    if (b.action !== 'walk_to') continue;
    const t0 = Math.max(b.t, cur.t);
    const from = cam.worldToGround(cur.X, cur.Z);
    const target = resolvePoint(b.args?.to, set, cam, null);
    if (!target) { tr.log.push(`walk_to at ${b.t}s: no target`); continue; }
    const pts = planPath(from, target, set).map(p => cam.groundToWorld(p[0], p[1]));
    // arclength
    const segs = []; let L = 0;
    for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); segs.push({ a: pts[i - 1], b: pts[i], s0: L, l }); L += l; }
    if (L < 8) continue;
    const at = s => { s = Math.max(0, Math.min(L, s)); const g = segs.find(q => s <= q.s0 + q.l + 1e-6) || segs[segs.length - 1]; const u = g.l ? (s - g.s0) / g.l : 0; return { X: lerp(g.a[0], g.b[0], u), Z: lerp(g.a[1], g.b[1], u), hd: headingPhi(g.b[0] - g.a[0], g.b[1] - g.a[1]) }; };
    let stride = tr.stride * (b.args?.speed ? Math.sqrt(b.args.speed) : 1);
    const n = Math.max(1, Math.ceil(L / stride)), l = L / n;
    let T = tr.stepT / (b.args?.speed ? Math.sqrt(b.args.speed) : 1);
    if (b.args?.arrive_t != null) T = Math.max(0.3, Math.min(0.9, (b.args.arrive_t - t0) / (n + 0.8)));
    const wordArr = wordAt(words, b.args?.arrive_word, t0);
    if (wordArr) T = Math.max(0.3, Math.min(0.9, (wordArr.w[1] - t0) / (n + 0.8)));
    const keep = !!b.args?.keep_facing;
    const hd0 = at(0).hd;
    let walkPhi = keep ? cur.phi : hd0;
    if (keep && tr.allowed) walkPhi = clampPhi(cur.phi, tr.allowed);
    else if (tr.allowed) walkPhi = clampPhi(hd0, tr.allowed);
    // lead with the foot on the far side of the first heading change
    const lead = 'R', trail = 'L';
    const steps = [];
    const plant = (s, side, phiF) => { const p = at(s), a = axes(p.hd), sg = side === 'L' ? 1 : -1; return { X: p.X + a.left[0] * sg * B.hipHalf * 1.1, Z: p.Z + a.left[2] * sg * B.hipHalf * 1.1, dir: keep ? walkPhi : p.hd }; };
    let prev = { L: { ...cur.feet.L }, R: { ...cur.feet.R } };
    for (let k = 1; k <= n; k++) {
      const side = k % 2 ? lead : trail;
      const to = plant(k * l, side);
      steps.push({ side, lift: t0 + (k - 1) * T, land: t0 + (k - 1) * T + 0.8 * T, from: prev[side], to });
      prev[side] = to;
    }
    const closeSide = n % 2 ? trail : lead;
    const toC = plant(L, closeSide);
    steps.push({ side: closeSide, lift: t0 + n * T, land: t0 + n * T + 0.8 * T, from: prev[closeSide], to: toC, closing: true });
    prev[closeSide] = toC;
    const ts = t0 + 0.2 * T, te = t0 + n * T + 0.6 * T;
    const w = { t0, t1: steps[steps.length - 1].land, ts, te, L, at, steps, T, keep, phi: walkPhi, beat: b, endWorld: [at(L).X, at(L).Z], endHeading: at(L).hd, pts };
    // a later stop beat cuts this walk
    const stop = tr.beats.find(s => s.action === 'stop' && s.t > t0 && s.t < w.t1);
    if (stop) {
      const keepSteps = steps.filter(s => s.land <= stop.t + 0.8 * T && !s.closing);
      const last = keepSteps[keepSteps.length - 1];
      if (last) {
        const other = last.side === 'L' ? 'R' : 'L';
        const lastOf = (side) => [...keepSteps].reverse().find(s => s.side === side)?.to || cur.feet[side];
        const pos = { X: (last.to.X + lastOf(other).X) / 2, Z: (last.to.Z + lastOf(other).Z) / 2 };
        // closing step: bring the other foot alongside the last plant
        const a = axes(last.to.dir), sg = other === 'L' ? 1 : -1;
        const mid = { X: last.to.X - a.left[0] * (last.side === 'L' ? 1 : -1) * B.hipHalf * 1.1, Z: last.to.Z - a.left[2] * (last.side === 'L' ? 1 : -1) * B.hipHalf * 1.1 };
        const closeTo = { X: mid.X + a.left[0] * sg * B.hipHalf * 1.1, Z: mid.Z + a.left[2] * sg * B.hipHalf * 1.1, dir: last.to.dir };
        keepSteps.push({ side: other, lift: last.land + 0.2 * T, land: last.land + T, from: lastOf(other), to: closeTo, closing: true });
        w.steps = keepSteps; w.t1 = last.land + T;
        // pelvis: re-time so it settles over the two plants
        const sStop = Math.min(L, Math.hypot(mid.X - at(0).X, mid.Z - at(0).Z) + 0);
        w.L = sStop; w.te = last.land + 0.6 * T;
        w.endWorld = [mid.X, mid.Z];
      }
    }
    tr.walks.push(w);
    const endFeet = { L: { ...cur.feet.L }, R: { ...cur.feet.R } };
    for (const s of w.steps) endFeet[s.side] = s.to;
    cur = { X: w.endWorld[0], Z: w.endWorld[1], phi: keep ? walkPhi : (tr.allowed ? clampPhi(w.endHeading, tr.allowed) : w.endHeading), feet: endFeet, t: w.t1 };
    turns.push({ t: t0, phi: walkPhi, dur: 0.3, walk: true });
    if (b.args?.face_after != null) turns.push({ t: w.t1, phi: clampPhi(b.args.face_after, tr.allowed), dur: 0.3 });
  }
  turns.sort((a, b) => a.t - b.t);

  // ---- channels from beats ----
  const arms = { L: [], R: [] }, hands = { L: [{ t: 0, shape: c.hands?.L || 'relaxed' }], R: [{ t: 0, shape: c.hands?.R || 'relaxed' }] };
  const head = [{ t: 0, pitch: c.head_pitch || 0 }], heads = [{ t: 0, head: c.head || null }], posture = [{ t: 0, drop: 0, back: 0 }];
  const pulses = [], sways = [], alpha = [{ t: 0, a: c.alpha ?? 1, dur: 0 }];
  const props = (c.props || []).map(p => ({ ...p }));
  const propEvents = [];
  for (const b of tr.beats) {
    const a = b.args || {}, side = a.side || 'R';
    if (b.action === 'reach' || b.action === 'hold_gesture') {
      const dur = a.dur ?? (b.action === 'reach' ? 0.55 : 0.4);
      const end = tr.beats.find(r => r.action === 'release' && (r.args?.side || 'R') === side && r.t > b.t);
      arms[side].push({ t0: b.t, tIn: b.t + dur, tOut: end ? end.t : (a.hold === false ? b.t + dur + 0.6 : Infinity), out: end?.args?.dur || 0.45, kind: b.action, a, beat: b });
      if (b.action === 'reach' && (b.contact || a.contact !== false)) tr.contacts.push({ who: tr.id, side, t: b.t + dur, t_release: end ? end.t : scene.duration, target: a.target, beat: b });
      if (a.hand) hands[side].push({ t: b.t + dur * 0.5, shape: a.hand });
    }
    if (b.action === 'head_lowers') { head.push({ t: b.t, pitch: a.deg ?? 24, dur: a.dur || 0.5 }); if (a.head) heads.push({ t: b.t, head: a.head }); }
    if (b.action === 'head_raises') head.push({ t: b.t, pitch: 0, dur: a.dur || 0.5 });
    if (b.action === 'hand_opens') hands[side].push({ t: b.t, shape: 'open' });
    if (b.action === 'hand_closes') hands[side].push({ t: b.t, shape: a.shape || 'relaxed' });
    if (b.action === 'swap_head') heads.push({ t: b.t, head: a.head });
    if (b.action === 'sit') posture.push({ t: b.t, drop: B.hip - (a.height_cm || 0.27 * B.H) - B.ankle, back: 0.08 * B.H, dur: 0.7 });
    if (b.action === 'stand') posture.push({ t: b.t, drop: 0, back: 0, dur: 0.6 });
    if (b.action === 'wince') pulses.push({ t: b.t, kind: 'wince', amp: a.amp || 1 });
    if (b.action === 'falter') pulses.push({ t: b.t, kind: 'falter', amp: a.amp || 1 });
    if (b.action === 'sway') sways.push({ t0: b.t, t1: b.t + (a.bars || 1) * 240 / (a.bpm || 120), bpm: a.bpm || 120, amp: a.amp || 1 });
    if (b.action === 'vanish') alpha.push({ t: b.t, a: 0, dur: a.dur || 1.2 });
    if (b.action === 'appear') alpha.push({ t: b.t, a: 1, dur: a.dur || 0.8 });
    if (b.action === 'hand_off') {
      const dur = a.dur || 0.6;
      arms[side].push({ t0: b.t, tIn: b.t + dur, tOut: b.t + dur + 0.35, out: 0.4, kind: 'hand_off', a: { ...a, target: { meet: a.to } }, beat: b });
      propEvents.push({ t: b.t + dur, prop: a.prop, to: a.to, side: a.to_side || 'R' });
      tr.contacts.push({ who: tr.id, side, t: b.t + dur, t_release: b.t + dur + 0.35, target: { who: a.to, socket: 'tip' + (a.to_side || 'R') }, beat: b, kind: 'hand_off' });
      out._handoffs = out._handoffs || []; out._handoffs.push({ from: tr.id, to: a.to, t: b.t, dur, side, to_side: a.to_side || 'R', prop: a.prop });
    }
  }
  // receivers of a hand-off reach back to the meeting point
  for (const h of (out._handoffs || []).filter(h => h.to === tr.id)) arms[h.to_side].push({ t0: h.t, tIn: h.t + h.dur, tOut: h.t + h.dur + 0.35, out: 0.4, kind: 'hand_off', a: { target: { meet: h.from } } });
  tr.arms = arms; tr.propEvents = propEvents; tr.props = props;
  const stepAt = (arr, t, key) => { let v = arr[0][key]; for (const e of arr) if (e.t <= t) v = e[key]; return v; };
  const easeAt = (arr, t, key) => { // eased transitions between keyed values
    let v = arr[0][key];
    for (let i = 1; i < arr.length; i++) { const e = arr[i]; if (e.t > t) break; const u = smooth((t - e.t) / (e.dur || 1e-3)); v = lerp(v, e[key], u); }
    return v;
  };

  // ---- per-frame state ----
  tr.frames = [];
  let phiNow = phi0;
  for (let f = 0; f < N; f++) {
    const t = f / fps;
    // facing: follow the latest turn key with a short ease (a view swap for cards)
    let phi = phi0;
    for (const k of turns) { if (k.t > t) break; const u = smooth((t - k.t) / (k.dur || 1e-3)); phi = phi + wrapDeg(k.phi - phi) * u; }
    phi = clampPhi(phi, tr.allowed);
    // root and feet
    let X = X0, Z = Z0, walking = false, w = null;
    const feet = { L: { ...footAt(X0, Z0, phi0, 'L'), lift: 0, pitch: 0, planted: true }, R: { ...footAt(X0, Z0, phi0, 'R'), lift: 0, pitch: 0, planted: true } };
    let phase = 0;
    for (const wk of tr.walks) {
      if (t < wk.t0) break;
      w = wk;
      for (const s of wk.steps) {
        if (t < s.lift) { if (s === wk.steps[0]) Object.assign(feet[s.side], s.from, { planted: true }); continue; }
        if (t >= s.land) { Object.assign(feet[s.side], s.to, { lift: 0, pitch: 0, planted: true }); continue; }
        const u = (t - s.lift) / (s.land - s.lift), e = smooth(u);
        feet[s.side] = { X: lerp(s.from.X, s.to.X, e), Z: lerp(s.from.Z, s.to.Z, e), dir: s.from.dir + wrapDeg(s.to.dir - s.from.dir) * e,
          lift: 0.035 * B.H * Math.sin(Math.PI * u), pitch: u < 0.3 ? -22 * (1 - u / 0.3) : 10 * Math.sin(Math.PI * (u - 0.3) / 0.7) * (u > 0.85 ? (1 - u) / 0.15 : 1), planted: false };
        walking = true; phase = (s.side === 'R' ? 0 : Math.PI) + Math.PI * u;
      }
      const sNow = wk.L * trap((t - wk.ts) / (wk.te - wk.ts), Math.min(0.45, 0.6 * wk.T / (wk.te - wk.ts)));
      const p = wk.at(sNow);
      X = p.X; Z = p.Z;
      if (t >= wk.t1) { X = wk.endWorld[0]; Z = wk.endWorld[1]; }
      else walking = true;
    }
    // when not walking, the root sits over the two plants
    if (!walking) { X = (feet.L.X + feet.R.X) / 2; Z = (feet.L.Z + feet.R.Z) / 2; }
    // posture, pulses, sway
    const drop = easeAt(posture, t, 'drop'), back = easeAt(posture, t, 'back');
    let headPitch = easeAt(head, t, 'pitch'), lean = (c.lean || 0) + (walking ? 3 : 0), bob = 0, sway = 0, swayCard = 0, dropPulse = 0;
    const xm = extFrame(tr, t, B); if (xm) { headPitch += xm.headPitch; lean += xm.lean; dropPulse += xm.drop; }   // lib/ext.js action channels
    for (const p of pulses) {
      const u = (t - p.t) / 0.45; if (u < 0 || u > 1) continue;
      const k = Math.sin(Math.PI * Math.min(1, u * 1.6)) * (1 - u) * 1.6;
      if (p.kind === 'wince') { headPitch += 16 * k * p.amp; dropPulse += 0.022 * B.H * k * p.amp; lean += 4 * k; }
      if (p.kind === 'falter') { headPitch += 20 * k; dropPulse += 0.03 * B.H * k; lean += 7 * k; }
    }
    let swaying = null;
    for (const s of sways) if (t >= s.t0 && t < s.t1) swaying = s;
    if (swaying) {
      const beat = (t - swaying.t0) * swaying.bpm / 60;
      sway = Math.sin(beat * Math.PI) * swaying.amp; bob = -Math.abs(Math.sin(beat * Math.PI)) * 0.012 * B.H * swaying.amp; swayCard = Math.floor(beat) % 2;
    }
    // pelvis height: standing height, lowered so both legs reach their feet (leg IK feasibility), plus walk bob
    const ax = axes(phi);
    const P0 = [X - ax.fwd[0] * back, 0, Z - ax.fwd[2] * back];
    let pelvisY = B.hip * 0.995 - drop - dropPulse + (walking ? 0.008 * B.H * Math.cos(2 * phase) : 0);
    const legMax = (B.thigh + B.shin) * 0.995;
    for (const s of ['L', 'R']) {
      const sg = s === 'L' ? 1 : -1, ft = feet[s];
      const hx = P0[0] + ax.left[0] * sg * B.hipHalf, hz = P0[2] + ax.left[2] * sg * B.hipHalf;
      const fd = [Math.cos(ft.dir * D2R), -Math.sin(ft.dir * D2R)];                 // the ankle sits a little forward of the plant
      const hd = Math.hypot(ft.X + fd[0] * B.toeBack * 0.2 - hx, ft.Z + fd[1] * B.toeBack * 0.2 - hz), ay = B.ankle + (ft.lift || 0);
      const maxY = ay + Math.sqrt(Math.max(0, legMax * legMax - hd * hd));
      pelvisY = Math.min(pelvisY, maxY);            // both legs, the swinging one included, must reach
    }
    // arms: rest swing, then reach/gesture windows blend toward IK targets
    const armSt = {};
    for (const s of ['L', 'R']) {
      const sg = s === 'L' ? 1 : -1;
      armSt[s] = { swing: walking ? 16 * Math.sin(phase) * -sg : (swaying ? 10 * sway * sg : 2), bend: walking ? 18 : 12, abduct: 6, weight: 0, win: null };
      for (const win of arms[s]) {
        if (t < win.t0 || t > win.tOut + win.out) continue;
        let wgt = t < win.tIn ? smooth((t - win.t0) / (win.tIn - win.t0)) : t > win.tOut ? 1 - smooth((t - win.tOut) / win.out) : 1;
        if (wgt > armSt[s].weight) { armSt[s].weight = wgt; armSt[s].win = win; }
      }
    }
    // the card hop-step (for replacement-card characters): the card moves only while lifted
    let cardLift = 0, cardX = X, cardZ = Z, cardPlanted = true;
    if (w && t >= w.t0 && t < w.t1 + 0.01) {
      const mid = { X: (feet.L.X + feet.R.X) / 2, Z: (feet.L.Z + feet.R.Z) / 2 };
      cardX = mid.X; cardZ = mid.Z;
      const sw = w.steps.find(s => t >= s.lift && t < s.land);
      if (sw) { const u = (t - sw.lift) / (sw.land - sw.lift); cardLift = 0.03 * B.H * Math.pow(Math.sin(Math.PI * u), 0.5); cardPlanted = false; }
    } else if (!walking) { cardX = X; cardZ = Z; }
    const hShape = { L: stepAt(hands.L, t, 'shape'), R: stepAt(hands.R, t, 'shape') };
    const a2 = easeAt(alpha, t, 'a');
    // prop holders
    tr.frames.push({ f, t, X, Z, phi, pelvisY, lean: lean + sway * 3, headPitch, bob, feet, arms: armSt, hands: hShape, head: stepAt(heads, t, 'head'),
      walking, phase, alpha: a2 * (xm?.alpha ?? 1), swayCard, swayRot: swaying ? sway * 2.5 : 0, swaying: !!swaying,
      card: { X: cardX, Z: cardZ, lift: cardLift, planted: cardPlanted, state: (!walking && xm?.card) ? xm.card : (walking && swaying && w?.keep) ? 'dance' : walking ? 'walk' : swaying ? 'dance' : ((tr.walks.some(wk => t >= wk.t1) && c.card_state_after_walk) || c.card_state || 'stand') },
      posture: drop > 0.1 * B.H ? 'sit' : 'stand', back });
  }
}

// reach targets need everyone's frames: resolve world targets and pose every frame
function resolveTargets(tr, out, ctx) {
  const { cam, set } = ctx, B = tr.B;
  tr.ratioMax = 0; tr.legRatioMax = 0;
  for (const fr of tr.frames) {
    const st = { X: fr.X - axes(fr.phi).fwd[0] * fr.back, Z: fr.Z - axes(fr.phi).fwd[2] * fr.back, phi: fr.phi, pelvisY: fr.pelvisY, lean: fr.lean, headPitch: fr.headPitch, bob: fr.bob, feet: fr.feet, arms: {} };
    for (const s of ['L', 'R']) st.arms[s] = { swing: fr.arms[s].swing, bend: fr.arms[s].bend, abduct: fr.arms[s].abduct };
    const J0 = poseBody(B, st);
    for (const s of ['L', 'R']) {
      const a = fr.arms[s]; if (!a.win || a.weight <= 0) continue;
      const T = targetWorld(a.win, s, fr, tr, out, ctx, st);
      if (!T) continue;
      const k = a.weight;
      st.arms[s] = { ...st.arms[s], target: lerp3(J0['wrist' + s], T.wrist, k), handDir: T.handDir };
      a.targetPoint = T.point; a.targetDesc = T.desc;
    }
    fr.J = poseBody(B, st);
    fr.st = st;
    for (const s of ['L', 'R']) { const r = fr.J.ratios['arm' + s]; if (r > tr.ratioMax && fr.arms[s].weight > 0.99) tr.ratioMax = r; }
    tr.legRatioMax = Math.max(tr.legRatioMax, fr.J.ratios.legL, fr.J.ratios.legR);
  }
}

// a reach target as a world point for the wrist, so the hand's contact socket lands on the point
function targetWorld(win, side, fr, tr, out, ctx, st) {
  const { cam, set } = ctx, B = tr.B, a = win.a || {};
  const tg = a.target || {};
  let point = null, desc = '';
  if (tg.surface) {
    const s = set.surfaces.find(x => x.id === tg.surface);
    if (!s) return null;
    const at = tg.at || centroid(s.polygon);
    const Z = cam.groundToWorld(at[0], s.base_y ?? cam.yg)[1] - (tg.in_front_cm || 0);
    point = [(at[0] - cam.cx) * Z / cam.f, cam.hc - (at[1] - cam.yh) * Z / cam.f, Z];
    desc = `${tg.surface}@${at.map(Math.round)}`;
  } else if (tg.who) {
    const o = out.chars[tg.who]; if (!o) return null;
    const of = o.frames[fr.f];
    point = socketWorld(o, of, tg.socket || 'shoulder_L', ctx);
    desc = `${tg.who}.${tg.socket}`;
  } else if (tg.meet) {
    const o = out.chars[tg.meet]; if (!o) return null;
    const of = o.frames[fr.f];
    const me = [st.X, B.hip * 1.12, st.Z], them = [of.X, o.B.hip * 1.12, of.Z];
    point = lerp3(me, them, 0.5); desc = `meet ${tg.meet}`;
  } else if (win.kind === 'hold_gesture' || a.name) {
    const G = { page_up: [0.22, 0.22, 0.05], palm_out: [0.3, 0.38, 0.1], hand_chest: [0.07, 0.36, -0.02], arms_up: [0.06, 0.62, 0.12], reach_out: [0.34, 0.3, 0.07], hand_low: [0.12, 0.05, 0.1] }[a.name || 'page_up'];
    point = bodyPoint(st, B, G[0], G[1], G[2], side); desc = a.name;
    return { wrist: point, point, desc, handDir: null };
  }
  if (!point) return null;
  // put the contact socket (palm / fingertip) on the point: back the wrist off along the approach direction
  const sh = add(add([st.X, st.pelvisY, st.Z], [0, B.torso * 0.93, 0]), [0, 0, 0]);
  const dir = norm(sub(point, sh));
  const wrist = sub(point, mul(dir, B.hand * (a.socket === 'tip' ? 1 : 0.62)));
  return { wrist, point, desc, handDir: dir };
}

// world position of a named socket on a character at a frame (jointed: a joint; cards: a socket read off the card)
export function socketWorld(o, of, socket, ctx) {
  if (o.mode === 'jointed' || !o.cardFor) {
    const map = { shoulder_L: 'shoulderL', shoulder_R: 'shoulderR', tipL: 'tipL', tipR: 'tipR', neck: 'neck', head: 'headTop' };
    const J = of.J; return J ? (J[map[socket] || socket] || J.neck) : null;
  }
  const card = o.cardFor(of);
  const sk = card?.sockets?.[socket];
  if (!sk || !card) { const J = of.J; return J ? (J[{ shoulder_L: 'shoulderL', shoulder_R: 'shoulderR' }[socket] || 'neck']) : null; }
  const ppcCard = card.figure_px ? card.figure_px / o.B.H : card.scale.px_per_cm, flip = card._flip ? -1 : 1;
  const dx = (sk[0] - card.pivot[0]) / ppcCard * flip, dy = (card.pivot[1] - sk[1]) / ppcCard;
  return [of.card.X + dx, dy + of.card.lift, of.card.Z - 4];
}
