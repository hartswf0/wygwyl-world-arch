// frame = draw(scene, set, solved, t). One renderer for the editor, the checks and the headless film.
// Every placement is a DOMMatrix in set pixels; the same matrix that draws a card also reports where its
// sockets landed (soles, palms), so the checks measure what was drawn, not what the solver intended.
import { img } from './adapters.js';
import { viewOf, axes, D2R, lerp, smooth } from './rig.js';
import { socketWorld } from './solver.js';
import { EXT } from './ext.js';

const COLORS = ['#e7a35a', '#7fd3c4', '#ff7b6b', '#b9a5ff', '#9fe08a', '#f2d16b', '#6fb5ff', '#ff9ad5'];
const RING = ['front', 'threequarter', 'profile', 'threequarter_back', 'back'];
// substitution order when a view is missing: never show a face where the back is wanted, and the reverse
const PREF = { front: ['front', 'threequarter', 'profile', 'threequarter_back', 'back'], threequarter: ['threequarter', 'front', 'profile', 'threequarter_back', 'back'],
  profile: ['profile', 'threequarter', 'threequarter_back', 'front', 'back'], threequarter_back: ['threequarter_back', 'back', 'profile', 'threequarter', 'front'],
  back: ['back', 'threequarter_back', 'profile', 'threequarter', 'front'] };
const ringD = (have, want) => { const o = PREF[want] || RING; const i = o.indexOf(have); return i < 0 ? 9 : i; };

// ───── assets ─────
export async function loadAssets(scene, set, ctx) {
  const A = { layers: {}, parts: {}, archive: {}, occ: {} };
  await Promise.all(set.layers.filter(l => l.url).map(async l => { A.layers[l.id] = await img(l.url); }));
  await Promise.all(set.occluders.filter(o => o.url).map(async o => { A.occ[o.id] = await img(o.url); }));
  const chars = new Set((scene.cast || []).map(c => c.character));
  const want = ctx.parts.filter(p => chars.has(p.character));
  await Promise.all(want.map(async p => { A.parts[p.id] = await img(p.url); }));
  const clips = new Set((scene.joins || []).map(j => j.clip).filter(Boolean));
  await Promise.all([...clips].map(async k => { const m = ctx.archive[k]; if (m) A.archive[k] = { meta: m, im: await img(m.url) }; }));
  await Promise.all(EXT.preload.map(fn => fn(scene, set, ctx, A)));   // lib/ext.js
  return A;
}

// a card is sized so its figure is the character's height (lane B's height wins over the card's own note)
export const cardPPC = (card, tr) => card.figure_px ? card.figure_px / tr.B.H : card.scale.px_per_cm;
// ───── picking parts and cards ─────
export function partsFor(ctx, c) {
  const key = c.character + '|' + (c.costume || '');
  ctx._pcache = ctx._pcache || {};
  if (!ctx._pcache[key]) {
    const all = ctx.parts.filter(p => p.character === c.character);
    const cos = all.filter(p => !c.costume || !p.costume || p.costume === c.costume);
    ctx._pcache[key] = { all, own: cos.length ? cos : all, fallback: !cos.some(p => p.part === 'torso') && all.some(p => p.part === 'torso') };
  }
  return ctx._pcache[key];
}
export function pickPart(ctx, c, part, view, side, state) {
  const { own, all } = partsFor(ctx, c);
  let pool = own.filter(p => p.part === part); if (!pool.length) pool = all.filter(p => p.part === part);
  if (!pool.length) return null;
  let best = null, bs = Infinity;
  for (const p of pool) {
    let s = ringD(p.view, view) * 10;
    if (state && p.state !== state) s += 4;
    if (p.side !== '-' && side && p.side !== side) s += 2;
    if (s < bs) { bs = s; best = p; }
  }
  return best;
}
export function pickCard(ctx, tr, fr) {
  const c = tr.cast, { own, all } = partsFor(ctx, c);
  let pool = own.filter(p => p.part === 'body'); if (!pool.length) pool = all.filter(p => p.part === 'body');
  if (!pool.length) return null;
  const v = viewOf(fr.phi).view;
  const want = fr.card.state;
  const pin = c.cards?.[want] || (String(want).startsWith('card.') ? want : null);   // the scene can pin a card per state (or a pose beat names one)
  let cands = pin ? pool.filter(p => (Array.isArray(pin) ? pin : [pin]).includes(p.id)) : [];
  if (!cands.length) {
    const sameState = pool.filter(p => p.state === want || (want === 'dance' && p.state === 'dance'));
    const base = sameState.length ? sameState : pool.filter(p => p.state === 'stand' || p.state === 'walk').length ? pool.filter(p => p.state === 'stand' || p.state === 'walk') : pool;
    const dmin = Math.min(...base.map(p => ringD(p.view, v)));
    cands = base.filter(p => ringD(p.view, v) === dmin);
  }
  let k = 0;
  if (want === 'walk') { const w = tr.walks.find(w => fr.t >= w.t0 && fr.t <= w.t1); if (w) k = w.steps.filter(s => s.land <= fr.t).length; }
  if (want === 'dance') k = fr.swayCard;
  const card = cands[k % cands.length];
  const faceSide = Math.cos(fr.phi * D2R) >= 0 ? 'R' : 'L';
  card._flip = !['front', 'back'].includes(card.view) && (card.facing || 'R') !== faceSide;
  return card;
}

// ───── camera ─────
export function camAt(scene, t) {
  const keys = scene.camera?.keys || [];
  let z = 1, x = null, y = null, shake = 0;
  if (keys.length) {
    let a = keys[0], b = keys[keys.length - 1];
    for (let i = 0; i < keys.length - 1; i++) if (t >= keys[i].t && t <= keys[i + 1].t) { a = keys[i]; b = keys[i + 1]; }
    const u = b.t > a.t ? smooth((t - a.t) / (b.t - a.t)) : (t >= b.t ? 1 : 0);
    z = lerp(a.zoom ?? 1, b.zoom ?? 1, u); x = lerp(a.x ?? 960, b.x ?? 960, u); y = lerp(a.y ?? 540, b.y ?? 540, u);
  }
  for (const s of scene.camera?.shakes || []) { const u = (t - s.t) / (s.dur || 0.35); if (u >= 0 && u < 1) shake += (s.amp || 8) * (1 - u) * Math.sin(u * 40); }
  return { z, x, y, shake };
}
export function camMatrix(set, cv, p) {
  const z = 1 + (cv.z - 1) * p, fx = cv.x ?? set.frame[0] / 2, fy = cv.y ?? set.frame[1] / 2;
  return new DOMMatrix().translate(fx, fy + cv.shake * p).scale(z).translate(-fx, -fy);
}

// ───── archive strips ─────
function stripFrame(A, clip, tau) {
  const a = A.archive[clip]; if (!a?.im) return null;
  const m = a.meta, i = ((Math.floor(tau * m.fps) % m.n) + m.n) % m.n;
  return { im: a.im, sx: (i % m.cols) * m.w, sy: Math.floor(i / m.cols) * m.h, sw: m.w, sh: m.h, meta: m };
}
function coverInto(g, fr, box) {
  const [x0, y0, x1, y1] = box, bw = x1 - x0, bh = y1 - y0, s = Math.max(bw / fr.sw, bh / fr.sh);
  const dw = fr.sw * s, dh = fr.sh * s;
  g.drawImage(fr.im, fr.sx, fr.sy, fr.sw, fr.sh, x0 + (bw - dw) / 2, y0 + (bh - dh) / 2, dw, dh);
}
const boxOf = poly => { let a = [Infinity, Infinity, -Infinity, -Infinity]; for (const [x, y] of poly) a = [Math.min(a[0], x), Math.min(a[1], y), Math.max(a[2], x), Math.max(a[3], y)]; return a; };
const pathPoly = (g, poly) => { g.beginPath(); poly.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.closePath(); };
function tag(g, text, x, y, scale = 1) {
  g.save(); g.font = `${Math.round(17 * scale)}px "JetBrains Mono", ui-monospace, monospace`;
  if (text.length > 64) text = text.slice(0, 61) + '…';
  const w = g.measureText(text).width + 14 * scale;
  x = Math.max(8, Math.min(x, 1920 - w - 8));
  g.fillStyle = 'rgba(13,11,10,.82)'; g.fillRect(x, y, w, 26 * scale);
  g.fillStyle = '#efe6da'; g.fillText(text, x + 7 * scale, y + 18 * scale); g.restore();
  return [x, y, x + w, y + 26 * scale];
}
const fade = (t, t0, t1, d = 0.4) => Math.max(0, Math.min(1, (t - t0) / d, (t1 - t) / d));

// ───── the frame ─────
// F = {t, scene, set, cam, comp, ctx, A, opts:{greybox, debug, captions, solid:charId}}
export function drawFrame(g, F) {
  const { t, scene, set, cam, comp, ctx, A } = F, opts = F.opts || {};
  const f = Math.min(comp.N - 1, Math.round(t * comp.fps));
  const cv = camAt(scene, t);
  const base = g.getTransform();                       // output transform (set px -> canvas px)
  const probe = { f, t, chars: {}, joins: [], tags: [] };
  g.save();
  // background: image layers without depth, far to near by z
  const items = [];
  const layers = [...set.layers].sort((a, b) => (a.z ?? 0) - (b.z ?? 0));
  for (const l of layers) {
    const Z = l.depth_m != null ? l.depth_m * 100 : Infinity;
    items.push({ Z, kind: 'layer', draw: () => drawLayer(g, base, l, set, cv, A, t, scene) });
  }
  for (const o of set.occluders) {
    const Z = cam.groundToWorld((boxOf(o.polygon)[0] + boxOf(o.polygon)[2]) / 2, o.base_y)[1];
    items.push({ Z, kind: 'occluder', draw: () => drawOccluder(g, base, o, set, cv, A) });
  }
  for (const fx of [...(set.fx || []), ...(scene.fx || [])]) {
    const Z = fx.depth_m != null ? fx.depth_m * 100 : fx.ground_y ? cam.groundToWorld(960, fx.ground_y)[1] : (fx.over ? -1 : Infinity);
    items.push({ Z, kind: 'fx', draw: () => drawFx(g, base, fx, F, cv) });
  }
  for (const j of scene.joins || []) {
    if (t < j.t - 0.5 || t > (j.t_end ?? scene.duration) + 0.5) continue;
    if (j.kind === 'answer') continue;                   // drawn over everything below
    let Z = Infinity;
    const s = set.surfaces.find(x => x.id === j.surface);
    if (s) Z = cam.groundToWorld(boxOf(s.polygon)[0], s.base_y ?? cam.yg)[1] - 0.5;   // just in front of its own occluder
    if (j.kind === 'citizen' && j.at) Z = cam.groundToWorld(j.at[0], j.at[1])[1];
    if (j.ground_y != null) Z = cam.groundToWorld(j.ground_x ?? 960, j.ground_y)[1] - 0.5;   // a join may stand at its own ground line (a pane cut in the plate)
    items.push({ Z, kind: 'join', draw: () => drawJoin(g, base, j, s, F, cv, probe) });
  }
  for (const id of comp.order) {
    const tr = comp.chars[id], fr = tr.frames[f];
    if (opts.only && opts.only !== id) continue;
    items.push({ Z: fr.Z, kind: 'char', id, draw: () => { probe.chars[id] = drawCharacter(g, base, tr, fr, F, cv, opts); } });
  }
  // far first; at equal depth: layer, join, occluder, character
  const rank = { layer: 0, fx: 1, join: 2, occluder: 3, char: 4 };
  items.sort((a, b) => (b.Z - a.Z) || (rank[a.kind] - rank[b.kind]));
  for (const it of items) {
    if (opts.only && it.kind !== 'char') continue;
    g.save(); it.draw(); g.restore();
  }
  g.setTransform(base);
  if (!opts.only) {
    for (const j of scene.joins || []) if (j.kind === 'answer') drawAnswer(g, j, F, probe);
    if (opts.captions !== false) drawCaption(g, scene, t);
    if (opts.debug) drawDebug(g, F, probe, cv);
    if (scene.title_card && t < 2.2) titleCard(g, scene, t);
  }
  g.restore();
  return probe;
}

function drawLayer(g, base, l, set, cv, A, t, scene) {
  g.setTransform(base.multiply(camMatrix(set, cv, l.parallax ?? 1)));
  if (l.kind === 'code') return;                      // code layers are scene fx
  const im = A.layers[l.id]; if (!im) return;
  g.globalAlpha = l.alpha ?? 1;
  const r = l.rect || [0, 0, set.frame[0], set.frame[1]];
  g.drawImage(im, r[0], r[1], r[2], r[3]);
}
function drawOccluder(g, base, o, set, cv, A) {
  g.setTransform(base.multiply(camMatrix(set, cv, o.parallax ?? 1)));
  const src = A.occ[o.id] || A.layers[o.from || set.layers.find(l => l.kind === 'image')?.id];
  if (!src) return;
  pathPoly(g, o.polygon); g.clip();
  if (A.occ[o.id]) { const r = o.rect || [0, 0, set.frame[0], set.frame[1]]; g.drawImage(src, r[0], r[1], r[2], r[3]); }
  else g.drawImage(src, 0, 0, set.frame[0], set.frame[1]);
}

// ───── characters ─────
function boneM(A, B, card, pv, dist, lenCm, s, mirror) {
  // card pivot pv -> distal socket dist mapped onto screen A -> B; across scale from true length
  const cvx = dist[0] - pv[0], cvy = dist[1] - pv[1], Lc = Math.hypot(cvx, cvy) || 1, thc = Math.atan2(cvy, cvx);
  const dx = B[0] - A[0], dy = B[1] - A[1], Ls = Math.hypot(dx, dy), ths = Math.atan2(dy, dx);
  // across: the part's measured px/cm when it has one (lane B), else its socket span fitted to the bone's true length
  const across = card?.scale?.px_per_cm ? s / card.scale.px_per_cm : s * lenCm / Lc, along = Math.max(Ls / Lc, across * 0.3);
  return new DOMMatrix().translate(A[0], A[1]).rotate(ths / D2R).scale(along, mirror ? -across : across).rotate(-thc / D2R).translate(-pv[0], -pv[1]);
}
const HAND_PART = { open: 'open', relaxed: 'relaxed', grip: 'grip', fist: 'fist', point: 'point', pinch: 'grip', claw: 'open', flat_push: 'open' };

export function drawCharacter(g, base, tr, fr, F, cv, opts) {
  const { cam, set, ctx, A } = F, c = tr.cast, B = tr.B, J = fr.J;
  const stageM = base.multiply(camMatrix(set, cv, 1));
  const P = {}; for (const k in J) if (Array.isArray(J[k]) && J[k].length === 3) P[k] = cam.project(...J[k]);
  const { view, side } = viewOf(fr.phi);
  const out = { id: tr.id, view, side, mode: tr.mode, Z: fr.Z, soles: [], contact: {}, ppc: cam.project(fr.X, 0, fr.Z)[2], parts: [], alpha: fr.alpha };
  const foot = cam.project(fr.X, 0, fr.Z); out.foot = [foot[0], foot[1]];
  if (fr.alpha <= 0.01) { out.hidden = true; return out; }
  g.globalAlpha = fr.alpha;
  const color = COLORS[(F.scene.cast || []).findIndex(x => x.id === tr.id) % COLORS.length];
  const solid = opts.solidColor;
  if (opts.greybox) { drawGrey(g, stageM, P, B, color, fr, out, solid); return out; }
  if (tr.mode === 'cards') { drawCard(g, stageM, tr, fr, F, out, solid); if (!opts.bodyOnly) drawProps(g, stageM, tr, fr, P, F, out); return out; }
  // jointed: one card per bone, far to near
  const mirror = Math.cos(fr.phi * D2R) < 0;
  const bones = [];
  const torsoZ = (J.pelvis[2] + J.neck[2]) / 2;
  const limbView = 'profile';
  for (const s of ['L', 'R']) {
    const zf = k => J[k + s][2];
    const shadeFar = ((J['shoulder' + s][2] + J['hip' + s][2]) / 2) > torsoZ + 1.5;
    bones.push({ part: 'thigh', a: 'hip' + s, b: 'knee' + s, cm: B.thigh, Z: (zf('hip') + zf('knee')) / 2 + 0.3, far: shadeFar });
    bones.push({ part: 'shin', a: 'knee' + s, b: 'ankle' + s, cm: B.shin, Z: (zf('knee') + zf('ankle')) / 2 + 0.2, far: shadeFar });
    bones.push({ part: 'foot', a: 'ankle' + s, b: 'toe' + s, cm: B.foot - B.toeBack, Z: zf('ankle') + 0.1, far: shadeFar, side: s });
    bones.push({ part: 'upper_arm', a: 'shoulder' + s, b: 'elbow' + s, cm: B.uarm, Z: (zf('shoulder') + zf('elbow')) / 2 - 0.6, far: shadeFar });
    bones.push({ part: 'forearm', a: 'elbow' + s, b: 'wrist' + s, cm: B.farm, Z: (zf('elbow') + zf('wrist')) / 2 - 0.7, far: shadeFar });
    bones.push({ part: 'hand', a: 'wrist' + s, b: 'tip' + s, cm: B.hand, Z: zf('wrist') - 0.8, far: shadeFar, side: s });
  }
  bones.push({ part: 'pelvis', a: 'pelvis', b: 'neck', cm: B.torso, Z: torsoZ + 0.4 });
  bones.push({ part: 'torso', a: 'pelvis', b: 'neck', cm: B.torso, Z: torsoZ });
  bones.push({ part: 'head', a: 'neck', b: 'headTop', cm: B.neck + B.head, Z: torsoZ - 1.2 });
  bones.sort((x, y) => y.Z - x.Z);
  if (opts.bodyOnly) for (let i = bones.length - 1; i >= 0; i--) if (['upper_arm', 'forearm', 'hand'].includes(bones[i].part)) bones.splice(i, 1);
  const frontish = Math.abs(Math.cos(fr.phi * D2R)) < 0.6;
  for (const bn of bones) {
    let part, dist, pv, M;
    const A2 = P[bn.a], B2 = P[bn.b]; if (!A2 || !B2) continue;
    const s = (A2[2] + B2[2]) / 2;
    if (bn.part === 'head') {
      part = pickPart(ctx, c, 'head', view, side, fr.head);
      if (!part) continue;
      pv = part.sockets.neck || part.pivot; dist = part.sockets.top || [pv[0], 0];
      M = boneM(A2, B2, null, pv, dist, bn.cm, s, part.view === 'profile' && part.side === '-' && part.laneB && mirror);
    } else if (bn.part === 'torso' || bn.part === 'pelvis') {
      const tv = bn.part === 'torso' ? view : (frontish ? 'front' : 'profile');
      part = pickPart(ctx, c, bn.part, bn.part === 'pelvis' ? tv : view, side);
      if (!part) continue;
      if (bn.part === 'torso') { pv = part.sockets.hip || part.pivot; dist = part.sockets.neck; M = boneM(A2, B2, part, pv, dist, bn.cm, s, part.view === 'profile' && mirror); }
      else {
        const torso = pickPart(ctx, c, 'torso', view, side);
        const tl = Math.hypot(torso.sockets.neck[0] - torso.sockets.hip[0], torso.sockets.neck[1] - torso.sockets.hip[1]);
        const k = s * (part.view === 'profile' ? 0.15 : 0.2) * B.H / part.w, ang = Math.atan2(B2[1] - A2[1], B2[0] - A2[0]) / D2R + 90;
        pv = part.sockets.hip || part.pivot;
        M = new DOMMatrix().translate(A2[0], A2[1]).rotate(ang).scale(part.view === 'profile' && mirror ? -k : k, k).translate(-pv[0], -pv[1]);
      }
    } else if (bn.part === 'foot') {
      // the boot's view follows that foot's own direction (fixed while planted), not the body's turn
      const fdir = fr.feet[bn.side].dir * D2R, ffront = Math.abs(Math.cos(fdir)) < 0.6;
      const fv = ffront ? (Math.sin(fdir) > 0 ? 'front' : 'back') : 'profile';
      part = pickPart(ctx, c, 'foot', fv, bn.side, 'flat');
      if (!part) continue;
      pv = part.sockets.ankle || part.pivot;
      if (part.sockets.sole) {                         // upright front/back boot: ankle -> ground under it
        const a = tr.frames[fr.f].J['ankle' + bn.side];
        const gnd = cam.project(a[0], 0, a[2]);
        if (part.scale?.px_per_cm) { const u = s / part.scale.px_per_cm; M = new DOMMatrix().translate(A2[0], A2[1]).scale(u, u).translate(-pv[0], -pv[1]); }
        else {                                         // keep the boot upright and sized by the foot length across
          const k = s * B.foot * 0.62 / part.w, kk = (gnd[1] - A2[1]) / ((part.sockets.sole[1] - pv[1]) || 1);
          M = new DOMMatrix().translate(A2[0], A2[1]).scale(k, Math.max(kk, k * 0.5)).translate(-pv[0], -pv[1]);
        }
      } else {
        dist = part.sockets.toe; M = boneM(A2, B2, part, pv, dist, bn.cm, s, Math.cos(fdir) < 0);
      }
    } else if (bn.part === 'hand') {
      const shape = HAND_PART[fr.hands[bn.side]] || 'relaxed';
      part = pickPart(ctx, c, 'hand', partsFor(ctx, c).own.some(p => p.part === 'hand' && p.laneB) ? view : 'profile', bn.side, shape);
      if (!part) continue;
      pv = part.sockets.wrist || part.pivot;
      // every hand card is sized wrist -> fingertips = hand length (closed hands: 0.8 of it)
      const tip = part.sockets.fingertips || part.sockets.tip || part.sockets.palm, k = ['grip', 'fist'].includes(part.state) ? 0.8 : 1;
      const B3 = [A2[0] + (B2[0] - A2[0]) * k, A2[1] + (B2[1] - A2[1]) * k];
      dist = tip; M = boneM(A2, B3, part, pv, dist, bn.cm * k, s, mirror);
      // the contact socket (palm, 0.62 along wrist -> fingertips) as drawn
      const palm = tip;
      const cpt = [pv[0] + (tip[0] - pv[0]) * 0.62, pv[1] + (tip[1] - pv[1]) * 0.62];
      const q = M.transformPoint(new DOMPoint(cpt[0], cpt[1]));
      out.contact[bn.side] = [q.x, q.y];
      const qt = M.transformPoint(new DOMPoint(tip[0], tip[1])); out.contact['tip' + bn.side] = [qt.x, qt.y];
    } else {
      const bs = bn.a.slice(-1);                      // L / R from the joint name
      part = pickPart(ctx, c, bn.part, partsFor(ctx, c).own.some(p => p.part === bn.part && p.view !== 'profile') ? view : limbView, bs);
      if (!part) continue;
      const S = { upper_arm: ['shoulder', 'elbow'], forearm: ['elbow', 'wrist'], thigh: ['hip', 'knee'], shin: ['knee', 'ankle'] }[bn.part];
      pv = part.sockets[S[0]] || part.pivot; dist = part.sockets[S[1]];
      M = boneM(A2, B2, part, pv, dist, bn.cm, s, mirror);
    }
    const im = A.parts[part.id]; if (!im) continue;
    g.setTransform(stageM.multiply(M));
    if (bn.far && !solid) g.filter = 'brightness(0.74)';
    g.drawImage(im, 0, 0);
    g.filter = 'none';
    out.parts.push(part.id);
    if (bn.part === 'hand' && !opts.bodyOnly) drawProps(g, stageM, tr, fr, P, F, out, bn.side);
    if (bn.part === 'foot') {
      const pts = part.sockets.sole ? [part.sockets.sole] : [part.sockets.heel, part.sockets.toe_sole || part.sockets.toe].filter(Boolean);
      out.soles.push({ side: bn.side, planted: fr.feet[bn.side].planted && !fr.feet[bn.side].lift, pts: pts.map(p => { const q = M.transformPoint(new DOMPoint(p[0], p[1])); return [q.x, q.y]; }), ppc: s });
    }
  }
  if (solid) { g.setTransform(base); }
  out.headView = pickPart(ctx, c, 'head', view, side, fr.head)?.view;
  return out;
}

function drawCard(g, stageM, tr, fr, F, out, solid) {
  const { cam, ctx, A } = F;
  const card = pickCard(ctx, tr, fr); if (!card) return;
  const im = A.parts[card.id]; if (!im) return;
  const an = cam.project(fr.card.X, fr.card.lift, fr.card.Z), k = an[2] / cardPPC(card, tr);
  const M = new DOMMatrix().translate(an[0], an[1]).rotate(fr.swayRot || 0).scale(card._flip ? -k : k, k).translate(-card.pivot[0], -card.pivot[1]);
  g.setTransform(stageM.multiply(M));
  g.drawImage(im, 0, 0);
  const sole = M.transformPoint(new DOMPoint(card.pivot[0], card.pivot[1]));
  const gnd = cam.project(fr.card.X, 0, fr.card.Z);
  out.soles.push({ side: 'card', planted: fr.card.planted, pts: [[sole.x, sole.y]], ppc: an[2], lift: fr.card.lift });
  out.card = card.id; out.cardView = card.view; out.cardState = card.state; out.anchor = [gnd[0], gnd[1]];
  out.cardBox = ['tl', 'br'].map((_, i) => { const q = M.transformPoint(new DOMPoint(i ? card.w : 0, i ? card.h : (card.alpha_top || 0))); return [q.x, q.y]; });
  for (const [name, p] of Object.entries(card.sockets || {})) { const q = M.transformPoint(new DOMPoint(p[0], p[1])); out.contact['card:' + name] = [q.x, q.y]; }
  out.headView = card.view;
}

function drawGrey(g, stageM, P, B, color, fr, out, solid) {
  g.setTransform(stageM);
  g.lineCap = 'round'; g.lineJoin = 'round';
  const cap = (a, b, wcm, col) => { if (!P[a] || !P[b]) return; g.strokeStyle = col; g.lineWidth = wcm * (P[a][2] + P[b][2]) / 2; g.beginPath(); g.moveTo(P[a][0], P[a][1]); g.lineTo(P[b][0], P[b][1]); g.stroke(); };
  const far = 'rgba(80,70,62,.95)';
  const sideFar = s => fr.J['hip' + s][2] > fr.J.pelvis[2] + 1;
  for (const s of ['L', 'R'].sort((a, b) => fr.J['hip' + b][2] - fr.J['hip' + a][2])) {
    const col = solid || (sideFar(s) ? far : color);
    cap('hip' + s, 'knee' + s, 0.075 * B.H, col); cap('knee' + s, 'ankle' + s, 0.06 * B.H, col); cap('heel' + s, 'toe' + s, 0.045 * B.H, col);
    if (!sideFar(s)) continue;
    cap('shoulder' + s, 'elbow' + s, 0.05 * B.H, col); cap('elbow' + s, 'wrist' + s, 0.045 * B.H, col); cap('wrist' + s, 'tip' + s, 0.035 * B.H, col);
  }
  cap('pelvis', 'neck', 0.17 * B.H, solid || '#d9cbb8');
  const hb = P.headBase, ht = P.headTop;
  g.fillStyle = solid || '#d9cbb8'; g.beginPath(); g.ellipse((hb[0] + ht[0]) / 2, (hb[1] + ht[1]) / 2, B.head * 0.42 * ht[2], Math.hypot(ht[0] - hb[0], ht[1] - hb[1]) / 2, Math.atan2(ht[1] - hb[1], ht[0] - hb[0]) + Math.PI / 2, 0, 7); g.fill();
  for (const s of ['L', 'R']) {
    if (sideFar(s)) continue;
    const col = solid || color;
    cap('shoulder' + s, 'elbow' + s, 0.05 * B.H, col); cap('elbow' + s, 'wrist' + s, 0.045 * B.H, col); cap('wrist' + s, 'tip' + s, 0.035 * B.H, col);
  }
  for (const s of ['L', 'R']) {
    out.soles.push({ side: s, planted: fr.feet[s].planted && !fr.feet[s].lift, pts: [P['heel' + s], P['toe' + s]].map(p => [p[0], p[1]]), ppc: P['ankle' + s][2] });
    const w = P['wrist' + s], tp = P['tip' + s];
    out.contact[s] = [w[0] + (tp[0] - w[0]) * 0.62, w[1] + (tp[1] - w[1]) * 0.62]; out.contact['tip' + s] = [tp[0], tp[1]];
  }
}

function drawProps(g, stageM, tr, fr, P, F, out, only) {
  for (const p of tr.props || []) {
    let side = p.side || 'R';
    if (only && side !== only) continue;
    const w = out.contact['tip' + side] || (P['tip' + side] && [P['tip' + side][0], P['tip' + side][1]]);
    if (!w) continue;
    const s = P['wrist' + side]?.[2] || out.ppc;
    g.setTransform(stageM);
    g.save(); g.translate(w[0], w[1]);
    if (p.id === 'poem_page') {
      g.rotate(-0.25); g.fillStyle = '#f2ece0'; g.strokeStyle = '#3a2f26'; g.lineWidth = 1;
      const pw = 21 * s, ph = 28 * s; g.fillRect(-pw * 0.5, -ph * 0.9, pw, ph); g.strokeRect(-pw * 0.5, -ph * 0.9, pw, ph);
      g.fillStyle = 'rgba(40,30,20,.55)'; for (let i = 1; i < 9; i++) g.fillRect(-pw * 0.4, -ph * 0.9 + i * ph / 10, pw * (0.5 + 0.3 * ((i * 7) % 3) / 2), Math.max(1, s * 0.6));
    } else if (p.id === 'vape_pen') {
      g.rotate(-1.1); g.fillStyle = '#111'; g.fillRect(0, -0.6 * s, 12 * s, 1.2 * s);
      const gl = g.createRadialGradient(12 * s, 0, 0, 12 * s, 0, 5 * s); gl.addColorStop(0, 'rgba(255,170,70,1)'); gl.addColorStop(1, 'rgba(240,138,36,0)');
      g.fillStyle = gl; g.beginPath(); g.arc(12 * s, 0, 5 * s, 0, 7); g.fill();
    } else if (EXT.props[p.kind] && EXT.props[p.kind](g, p, s, F)) {   // lib/ext.js prop cards
    } else {
      g.fillStyle = p.color || '#c79a62'; g.fillRect(-(p.w_cm || 10) * s / 2, -(p.h_cm || 10) * s, (p.w_cm || 10) * s, (p.h_cm || 10) * s);
    }
    g.restore();
  }
}

// ───── joins ─────
function drawJoin(g, base, j, s, F, cv, probe) {
  const { t, set, cam, scene, A, comp } = F;
  const t1 = j.t_end ?? scene.duration;
  const fr = stripFrame(A, j.clip, (t - j.t) + (j.clip_in || 0));
  if (!fr) return;
  if (EXT.joins[j.kind]) return EXT.joins[j.kind](g, base, j, s, F, cv, probe, { fr, camMatrix, tag, pathPoly, boxOf, coverInto, fade });   // lib/ext.js
  g.setTransform(base.multiply(camMatrix(set, cv, s?.parallax ?? 1)));
  let a = fade(t, j.t, t1, j.fade || 0.4) * (j.mix ?? 0.9);
  if (j.gate) { // touch-gated: plays while the named contact is held
    const tr = comp.chars[j.gate.who]; const fr2 = tr?.frames[Math.min(comp.N - 1, Math.round(t * comp.fps))];
    const w = fr2?.arms?.[j.gate.side || 'R']?.weight || 0; a *= Math.max(j.gate.floor ?? 0.15, w);
  }
  if (a <= 0.01) return;
  const label = `ARCHIVE · ${fr.meta.title}${fr.meta.year ? ', ' + fr.meta.year : ''}${j.kind === 'touch' ? ' · on touch' : ''}`;
  if (j.kind === 'screen' || j.kind === 'touch') {
    g.save(); pathPoly(g, s.polygon); g.clip(); g.globalAlpha = a; g.globalCompositeOperation = j.blend || 'source-over';
    if (j.tint) g.filter = j.tint;
    coverInto(g, fr, boxOf(s.polygon)); g.restore();
    const b = boxOf(s.polygon), dy = probe.tags.filter(q => Math.abs(q[0] - b[0] - 6) < 2).length * 24; probe.tags.push(tag(g, label, b[0] + 6, b[1] + 6 + dy, 0.8)); probe.joins.push({ kind: j.kind, clip: j.clip, a });
  } else if (j.kind === 'wipe') {
    const b = boxOf(s.polygon), dur = j.wipe_s || 0.9;
    const pin = smooth((t - j.t) / dur), pout = 1 - smooth((t - (t1 - dur)) / dur), p = Math.min(pin, pout);
    if (p <= 0) return;
    const yEdge = b[1] + (b[3] - b[1]) * p;
    g.save(); pathPoly(g, s.polygon); g.clip();
    g.beginPath(); g.moveTo(b[0] - 5, b[1] - 5); g.lineTo(b[2] + 5, b[1] - 5);
    for (let x = b[2] + 5, i = 0; x >= b[0] - 5; x -= 18, i++) g.lineTo(x, yEdge + ((i * 37) % 11 - 5) * 1.6);
    g.closePath(); g.clip(); g.globalAlpha = j.mix ?? 0.92; g.globalCompositeOperation = j.blend || 'source-over';
    if (j.tint) g.filter = j.tint;
    coverInto(g, fr, b); g.restore();
    probe.tags.push(tag(g, label + ' · reconstruction', b[0] + 6, Math.max(b[1] + 6, 8), 0.8)); probe.joins.push({ kind: 'wipe', clip: j.clip, a: p });
  } else if (j.kind === 'citizen') {
    const [x, y] = j.at, ppc = cam.ppcAt(y), hpx = (j.height_cm || 120) * ppc, wpx = hpx * fr.sw / fr.sh;
    const rise = smooth((t - j.t) / 0.6) * (1 - smooth((t - (t1 - 0.6)) / 0.6));
    const top = y - hpx * 1.12 + (1 - rise) * hpx * 0.6;
    g.save(); g.globalAlpha = Math.min(1, rise * 1.2);
    g.fillStyle = '#2a221c'; g.fillRect(x - 0.012 * hpx, top + hpx, 0.024 * hpx, y - top - hpx);   // the stick
    const poly = []; for (let i = 0; i < 16; i++) { const u = i / 16, ang = u * Math.PI * 2; poly.push([x + Math.cos(ang) * wpx * 0.5 * (1 + ((i * 13) % 5 - 2) * 0.012), top + hpx / 2 + Math.sin(ang) * hpx * 0.5 * (1 + ((i * 7) % 5 - 2) * 0.012)]); }
    g.fillStyle = '#efe6da'; g.beginPath(); poly.forEach((p, i) => i ? g.lineTo(p[0] + Math.sign(p[0] - x) * 4, p[1] + Math.sign(p[1] - top - hpx / 2) * 4) : g.moveTo(p[0], p[1])); g.closePath(); g.fill();
    pathPoly(g, poly); g.clip(); if (j.tint) g.filter = j.tint; coverInto(g, fr, [x - wpx / 2, top, x + wpx / 2, top + hpx]); g.restore();
    if (rise > 0.3) probe.tags.push(tag(g, label, x - wpx / 2, top - 30, 0.8));
    probe.joins.push({ kind: 'citizen', clip: j.clip, a: rise, box: [x - wpx / 2, top, x + wpx / 2, y] });
  }
}
function drawAnswer(g, j, F, probe) {
  const { t, scene, A, set } = F;
  const t1 = j.t_end ?? scene.duration, a = fade(t, j.t, t1, 0.5);
  if (a <= 0.01) return;
  const fr = stripFrame(A, j.clip, t - j.t + (j.clip_in || 0)); if (!fr) return;
  const W = set.frame[0], w = W * (j.w || 0.27), h = w * fr.sh / fr.sw, x = W - w - 40, y = set.frame[1] - h - 150;
  g.save(); g.globalAlpha = a; g.fillStyle = '#efe6da'; g.fillRect(x - 8, y - 8, w + 16, h + 16); coverInto(g, fr, [x, y, x + w, y + h]); g.restore();
  probe.tags.push(tag(g, `ANSWER · ${fr.meta.title}${fr.meta.year ? ', ' + fr.meta.year : ''}`, x - 8, y + h + 12, 0.8));
  if (j.caption) { g.save(); g.globalAlpha = a; g.font = 'italic 24px Inter, system-ui, sans-serif'; g.fillStyle = '#efe6da'; g.fillText(j.caption, x - 8, y - 18); g.restore(); }
  probe.joins.push({ kind: 'answer', clip: j.clip, a });
}

// ───── fx (code layers) ─────
function drawFx(g, base, fx, F, cv) {
  const { t, set, scene } = F, W = set.frame[0], H = set.frame[1];
  g.setTransform(base.multiply(camMatrix(set, cv, fx.parallax ?? 1)));
  if (EXT.fx[fx.kind]) return EXT.fx[fx.kind](g, base, fx, F, cv, { camMatrix, tag, pathPoly, boxOf });   // lib/ext.js
  if (fx.kind === 'haze') {           // torn tracing-paper sheets on rails, sliding in from the left
    const n = fx.sheets || 3;
    for (let i = 0; i < n; i++) {
      const t0 = (fx.t0 ?? 0) + i * (fx.stagger ?? 1.2), u = smooth((t - t0) / (fx.slide_s || 2.6));
      if (u <= 0) continue;
      const x1 = -W * 0.2 + u * W * (fx.reach ?? 1.25), y0 = H * (fx.y0 ?? 0.05) + i * 40, y1 = H * (fx.y1 ?? 0.98);
      g.save(); g.globalAlpha = (fx.alpha ?? 0.16);
      const gr = g.createLinearGradient(x1 - W * 0.45, 0, x1, 0);      // thick behind the leading edge, thin at it
      gr.addColorStop(0, fx.color || '#a9c9cf'); gr.addColorStop(1, 'rgba(169,201,207,0)');
      g.fillStyle = gr; g.filter = 'blur(14px)';
      g.beginPath(); g.moveTo(-80, y0); g.lineTo(x1, y0);
      for (let y = y0, k = 0; y <= y1; y += 26, k++) g.lineTo(x1 + Math.sin(k * 1.7 + i) * 26 + ((k * 31) % 9 - 4) * 3, y);
      g.lineTo(-80, y1); g.closePath(); g.fill(); g.restore();
    }
  } else if (fx.kind === 'strobe') {
    const bpm = fx.bpm || 124, beat = t * bpm / 60, ph = beat - Math.floor(beat), k = Math.floor(beat);
    if (t < (fx.t0 ?? 0) || t > (fx.t1 ?? 1e9)) return;
    const cols = fx.colors || ['#ff4fa8', '#4f8bff'];
    g.save(); g.globalCompositeOperation = 'screen'; g.globalAlpha = (fx.alpha ?? 0.22) * Math.exp(-ph * 5);
    g.fillStyle = cols[k % cols.length]; g.fillRect(0, 0, W, H); g.restore();
  } else if (fx.kind === 'sunrise') {
    const u = smooth((t - (fx.t0 ?? 0)) / ((fx.t1 ?? scene.duration) - (fx.t0 ?? 0)));
    const [x, y] = fx.at || [W / 2, H / 2], r = (fx.r0 ?? 60) + u * (fx.r1 ?? 520);
    g.save(); g.globalCompositeOperation = 'screen';
    const gr = g.createRadialGradient(x, y - u * (fx.rise ?? 60), 0, x, y - u * (fx.rise ?? 60), r);
    gr.addColorStop(0, `rgba(255,214,150,${0.85 * u})`); gr.addColorStop(0.35, `rgba(255,150,60,${0.45 * u})`); gr.addColorStop(1, 'rgba(255,120,40,0)');
    g.fillStyle = gr; g.fillRect(0, 0, W, H); g.restore();
  } else if (fx.kind === 'rail') {    // a fire-escape rail card at a ground line (code-drawn set piece)
    const [x0, x1] = fx.x, y = fx.ground_y, ppc = F.cam.ppcAt(y), h = (fx.height_cm || 100) * ppc;
    g.save(); g.strokeStyle = fx.color || '#1a1d22'; g.lineWidth = Math.max(2, 4 * ppc);
    g.beginPath(); g.moveTo(x0, y - h); g.lineTo(x1, y - h); g.moveTo(x0, y - h * 0.5); g.lineTo(x1, y - h * 0.5); g.stroke();
    g.lineWidth = Math.max(1.5, 3 * ppc); for (let x = x0; x <= x1; x += 22 * ppc) { g.beginPath(); g.moveTo(x, y - h); g.lineTo(x, y + 6 * ppc); g.stroke(); }
    g.fillStyle = fx.deck || 'rgba(20,24,30,.92)'; g.fillRect(x0 - 10 * ppc, y, x1 - x0 + 20 * ppc, 6 * ppc); g.restore();
  } else if (fx.kind === 'glass') {   // a pane of glass at its ground line: what is behind it reads as outside
    g.save(); g.globalAlpha = fx.alpha ?? 0.22; g.fillStyle = fx.color || '#9fd0d8'; pathPoly(g, fx.polygon); g.fill(); g.restore();
  } else if (fx.kind === 'deck') {    // a code-drawn landing / floor slab
    g.save(); g.fillStyle = fx.color || 'rgba(18,22,28,.9)'; pathPoly(g, fx.polygon); g.fill();
    g.strokeStyle = fx.line || 'rgba(120,140,150,.35)'; g.lineWidth = 2; const b = boxOf(fx.polygon);
    for (let y = b[1]; y <= b[3]; y += 9) { g.beginPath(); g.moveTo(b[0], y); g.lineTo(b[2], y); g.stroke(); } g.restore();
  } else if (fx.kind === 'darken') {
    const u = smooth((t - (fx.t0 ?? 0)) / (fx.dur ?? 1)) * (fx.alpha ?? 0.3);
    g.save(); g.globalAlpha = u; g.fillStyle = fx.color || '#000'; g.fillRect(0, 0, W, H); g.restore();
  }
}

// ───── overlays ─────
function drawCaption(g, scene, t) {
  const words = scene.audio?.words || []; if (!words.length) return;
  // the current line: words within 2.4 s around now
  let i = words.findIndex(w => w[2] > t); if (i < 0) i = words.length - 1;
  const lineId = words[i][3];
  const line = words.filter(w => w[3] === lineId && Math.abs(w[1] - t) < 4.5);
  if (!line.length || t < line[0][1] - 0.6 || t > line[line.length - 1][2] + 1.2) return;
  g.save(); g.font = '600 34px Inter, system-ui, sans-serif'; g.textBaseline = 'middle';
  const parts = line.map(w => w[0]), widths = parts.map(p => g.measureText(p + ' ').width), total = widths.reduce((a, b) => a + b, 0);
  let x = 960 - total / 2; const y = 1080 - 64;
  g.fillStyle = 'rgba(13,11,10,.55)'; g.fillRect(x - 18, y - 30, total + 36, 60);
  line.forEach((w, k) => { g.fillStyle = t >= w[1] && t < w[2] + 0.15 ? '#e7a35a' : t >= w[1] ? '#efe6da' : 'rgba(239,230,218,.45)'; g.fillText(w[0], x, y); x += widths[k]; });
  g.restore();
}
function titleCard(g, scene, t) {
  const a = 1 - smooth((t - 1.4) / 0.8);
  g.save(); g.globalAlpha = a; g.font = '400 44px "Permanent Marker", cursive'; g.fillStyle = '#efe6da'; g.fillText(scene.title_card, 60, 92);
  g.font = '18px "JetBrains Mono", monospace'; g.fillStyle = '#c79a62'; g.fillText(`${scene.scene_id} · cut-out suite staging`, 62, 126); g.restore();
}
function drawDebug(g, F, probe, cv) {
  const { set, cam, comp, t } = F;
  g.save(); g.setTransform(g.getTransform().multiply(camMatrix(set, cv, 1)));
  g.lineWidth = 2; g.font = '16px "JetBrains Mono", monospace';
  g.strokeStyle = 'rgba(127,211,196,.8)'; g.setLineDash([10, 8]); g.beginPath(); g.moveTo(0, cam.yh); g.lineTo(set.frame[0], cam.yh); g.stroke();
  g.fillStyle = 'rgba(127,211,196,.9)'; g.fillText(`horizon ${cam.yh.toFixed(0)} · camera ${cam.hc.toFixed(0)} cm`, 10, cam.yh - 8);
  g.strokeStyle = 'rgba(159,224,138,.6)'; for (const gp of set.grounds || [set.walkable]) { pathPoly(g, gp); g.stroke(); }
  g.setLineDash([]);
  for (const s of set.surfaces) { g.strokeStyle = 'rgba(231,163,90,.9)'; pathPoly(g, s.polygon); g.stroke(); g.fillStyle = '#e7a35a'; g.fillText(s.id, s.polygon[0][0] + 4, s.polygon[0][1] + 18); }
  for (const o of set.occluders) { g.strokeStyle = 'rgba(255,123,107,.8)'; pathPoly(g, o.polygon); g.stroke(); if (o.footprint) { g.setLineDash([4, 6]); pathPoly(g, o.footprint); g.stroke(); g.setLineDash([]); } }
  for (const id of comp.order) {
    const p = probe.chars[id]; if (!p) continue;
    for (const s of p.soles) for (const q of s.pts) { g.fillStyle = s.planted ? '#9fe08a' : '#ff7b6b'; g.beginPath(); g.arc(q[0], q[1], 5, 0, 7); g.fill(); }
    const tr = comp.chars[id], fr = tr.frames[probe.f];
    g.fillStyle = '#efe6da'; g.fillText(`${id} ${p.view}${p.card ? ' card' : ''} · ${(p.ppc).toFixed(2)} px/cm`, p.foot[0] - 60, p.foot[1] + 22);
    for (const s of ['L', 'R']) {
      const a = fr.arms[s]; if (!a.targetPoint || a.weight < 0.05) continue;
      const tp = cam.project(...a.targetPoint), hp = p.contact[s];
      g.strokeStyle = '#ff7b6b'; g.beginPath(); g.arc(tp[0], tp[1], 9, 0, 7); g.stroke();
      if (hp) { g.beginPath(); g.moveTo(tp[0], tp[1]); g.lineTo(hp[0], hp[1]); g.stroke(); }
    }
  }
  g.restore();
}
