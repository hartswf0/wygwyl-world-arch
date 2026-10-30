// CozyClay-style checks, measured on the render: every frame is drawn, the probes report where soles, palms
// and cards actually landed, and each puppet is drawn alone into a mask to measure its silhouette.
import { drawFrame, camAt, camMatrix } from './draw.js';
import { pip, onGround } from './camera.js';
import { wordAt } from './solver.js';
import { viewOf, D2R } from './rig.js';

export const THRESHOLDS = {
  foot_slide_cm_per_frame: 0.6,      // arena crash-lab standard
  contact_error_pct_height: 1.0,     // weave standard
  scale_error_pct: 4.0,
  reach_ratio: 1.0,
  off_frame_fraction: 0.2,
  occluded_fraction_warn: 0.6,
  word_sync_frames: 1,
  view_vs_travel_deg: 75,
};

const rangeStr = fs => { // [3,4,5,9] -> "3-5, 9"
  if (!fs.length) return '';
  const out = []; let a = fs[0], b = fs[0];
  for (const f of fs.slice(1)) { if (f === b + 1) b = f; else { out.push(a === b ? `${a}` : `${a}-${b}`); a = b = f; } }
  out.push(a === b ? `${a}` : `${a}-${b}`); return out.join(', ');
};

function mask(cnv, g) {
  const d = g.getImageData(0, 0, cnv.width, cnv.height).data, n = cnv.width * cnv.height, m = new Uint8Array(n);
  let x0 = Infinity, y0 = Infinity, x1 = -1, y1 = -1, c = 0;
  for (let i = 0; i < n; i++) if (d[i * 4 + 3] > 40) { m[i] = 1; c++; const x = i % cnv.width, y = (i / cnv.width) | 0; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return { m, c, box: c ? [x0, y0, x1 + 1, y1 + 1] : null };
}

// F0: {scene, set, cam, comp, ctx, A}. opts: {scale (mask resolution), every (mask every N frames), onProgress}
export async function runChecks(F0, opts = {}) {
  const { scene, set, cam, comp } = F0;
  const W = set.frame[0], H = set.frame[1], k = opts.scale || 0.5, every = opts.every || 1;
  const cv = document.createElement('canvas'); cv.width = Math.round(W * 0.25); cv.height = Math.round(H * 0.25);
  const g = cv.getContext('2d', { willReadFrequently: true });
  const mc = document.createElement('canvas'); mc.width = Math.round(W * k); mc.height = Math.round(H * k);
  const mg = mc.getContext('2d', { willReadFrequently: true });
  const oc = document.createElement('canvas'); oc.width = mc.width; oc.height = mc.height;
  const og = oc.getContext('2d', { willReadFrequently: true });
  const ids = comp.order, N = comp.N;
  const R = { slide: {}, contact: [], scale: {}, inOcc: {}, occFrac: {}, pair: {}, view: {}, off: {}, walk: {}, travel: {}, reach: {}, per: {} };
  for (const id of ids) { R.slide[id] = []; R.scale[id] = []; R.inOcc[id] = []; R.occFrac[id] = []; R.view[id] = []; R.off[id] = []; R.walk[id] = []; R.travel[id] = []; R.reach[id] = []; }
  const prev = {};
  const probes = [];
  for (let f = 0; f < N; f++) {
    const t = f / comp.fps;
    g.setTransform(cv.width / W, 0, 0, cv.height / H, 0, 0);
    const pr = drawFrame(g, { ...F0, t, opts: { captions: false } });
    probes.push(pr);
    // foot slide: drawn sole points of planted feet, frame to frame, in cm at that foot's depth
    for (const id of ids) {
      const p = pr.chars[id]; if (!p || p.hidden) { for (const k of Object.keys(prev)) if (k.startsWith(id + ':')) delete prev[k]; continue; }   // a vanished body re-plants where it reappears
      for (const s of p.soles) {
        const key = id + ':' + s.side, q = prev[key];
        if (q && q.planted && s.planted && q.pts.length === s.pts.length) {
          let d = 0; for (let i = 0; i < s.pts.length; i++) d = Math.max(d, Math.hypot(s.pts[i][0] - q.pts[i][0], s.pts[i][1] - q.pts[i][1]));
          R.slide[id].push({ f, cm: d / s.ppc });
        }
        prev[key] = s;
      }
      // EX rule and other view rules: the view actually drawn (head card or body card)
      const tr = comp.chars[id];
      if (tr.allowed) { const v = p.cardView || p.headView || p.view; if (!tr.allowed.includes(v)) R.view[id].push(f); }
      const fr = tr.frames[f];
      if (!onGround(p.foot, set)) R.walk[id].push(f);
      for (const o of set.occluders) if (o.footprint && pip(p.foot, o.footprint)) R.inOcc[id].push(f);
      // cards: does the card face where it travels?
      if (tr.mode === 'cards' && fr.walking && p.cardView && p.cardState === 'walk') {   // dance steps may travel sideways
        const w = tr.walks.find(w => t >= w.t0 && t <= w.t1);
        if (w) {
          const hd = w.at(Math.max(0.1, Math.min(w.L - 0.1, w.L * 0.5))).hd, cardPhi = cardFacingPhi(p.cardView, p.card, fr.phi, tr, F0);
          const d = Math.abs(((hd - cardPhi) % 360 + 540) % 360 - 180);
          if (d > THRESHOLDS.view_vs_travel_deg) R.travel[id].push(f);
        }
      }
      for (const s of ['L', 'R']) { const a = fr.arms[s]; if (a.weight > 0.99 && fr.J.ratios['arm' + s] > THRESHOLDS.reach_ratio) R.reach[id].push(f); }
    }
    // pairs: bodies closer than their radii
    for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
      const a = comp.chars[ids[i]], b = comp.chars[ids[j]], fa = a.frames[f], fb = b.frames[f];
      if (fa.alpha < 0.05 || fb.alpha < 0.05) continue;
      const d = Math.hypot(fa.X - fb.X, fa.Z - fb.Z), clr = d - (a.B.radius + b.B.radius), key = ids[i] + '|' + ids[j];
      (R.pair[key] = R.pair[key] || { min: Infinity, frames: [], minF: 0, touch: false });
      if (clr < R.pair[key].min) { R.pair[key].min = clr; R.pair[key].minF = f; }
      const touching = scene.beats?.some(bt => bt.action === 'reach' && [ids[i], ids[j]].includes(bt.who) && [ids[i], ids[j]].includes(bt.args?.target?.who));
      if (clr < 0) { R.pair[key].frames.push(f); R.pair[key].touch = touching; }
    }
    // contacts: drawn hand socket vs drawn target, while the reach is fully on
    for (const c of comp.contacts) {
      const tr = comp.chars[c.who], fr = tr.frames[f], a = fr.arms[c.side];
      if (t < c.t || t > c.t_release || a.weight < 0.99) continue;
      const hand = pr.chars[c.who]?.contact[c.side]; if (!hand) continue;
      let target = null;
      if (c.target?.surface) { target = a.targetPoint ? cam.project(...a.targetPoint) : null; }
      else if (c.target?.who) { const o = pr.chars[c.target.who]; target = o?.contact['card:' + c.target.socket] || (a.targetPoint && cam.project(...a.targetPoint)); }
      else if (a.targetPoint) target = cam.project(...a.targetPoint);
      if (!target) continue;
      const hpx = tr.B.H * pr.chars[c.who].ppc;
      R.contact.push({ f, who: c.who, side: c.side, what: a.targetDesc, px: Math.hypot(hand[0] - target[0], hand[1] - target[1]), pct: 100 * Math.hypot(hand[0] - target[0], hand[1] - target[1]) / hpx });
    }
    // silhouettes: each puppet alone into a mask, plus the occluders standing in front of it
    if (f % every === 0) for (const id of ids) {
      const tr = comp.chars[id], fr = tr.frames[f]; if (fr.alpha < 0.5) continue;
      mg.setTransform(1, 0, 0, 1, 0, 0); mg.clearRect(0, 0, mc.width, mc.height);
      mg.setTransform(k, 0, 0, k, 0, 0);
      // masks are drawn in set space (camera off) so they line up with the probes and the occluder polygons
      const F1 = { ...F0, scene: { ...F0.scene, camera: null } };
      drawFrame(mg, { ...F1, t, opts: { captions: false, only: id, greybox: opts.greybox } });
      const S = mask(mc, mg); if (!S.box) continue;
      const cm = camMatrix(set, camAt(F0.scene, t), 1);
      const c0 = cm.transformPoint(new DOMPoint(S.box[0] / k, S.box[1] / k)), c1 = cm.transformPoint(new DOMPoint(S.box[2] / k, S.box[3] / k));
      const box = [c0.x, c0.y, c1.x, c1.y];                    // what the camera sees, for off-frame
      // off frame
      const bw = box[2] - box[0], bh = box[3] - box[1];
      const inW = Math.max(0, Math.min(box[2], W) - Math.max(box[0], 0)), inH = Math.max(0, Math.min(box[3], H) - Math.max(box[1], 0));
      const outFrac = 1 - (inW * inH) / Math.max(1, bw * bh);
      if (outFrac > THRESHOLDS.off_frame_fraction) R.off[id].push(f);
      // scale vs set: standing frames only (not mid-stride, not swaying, not sitting)
      const p = pr.chars[id];
      const standing = !fr.walking && !fr.swaying && fr.posture === 'stand' && (tr.mode !== 'cards' || ['stand', 'walk', 'lean'].includes(p.cardState)) && Math.abs(fr.headPitch) < 6 && S.box[1] / k > 2 && S.box[3] / k < H - 2;
      if (standing) {
        const exp = cam.expectedHeightPx(p.foot[1], tr.B.H);
        // height from the body alone (no arms, no props): a raised hand or a held page is not the figure's scale
        mg.setTransform(1, 0, 0, 1, 0, 0); mg.clearRect(0, 0, mc.width, mc.height); mg.setTransform(k, 0, 0, k, 0, 0);
        drawFrame(mg, { ...F1, t, opts: { captions: false, only: id, bodyOnly: true } });
        const SB = mask(mc, mg);
        // head top to the ground point under the body: a heel nearer the lens than the hips is perspective, not scale
        const hpx = (tr.mode === 'cards' && p.cardState === 'lean') || !SB.box ? null : p.foot[1] - SB.box[1] / k;
        if (hpx) R.scale[id].push({ f, px: hpx, exp: exp.px, err: 100 * (hpx - exp.px) / exp.px, by: exp.by });
      }
      // occluders in front of this puppet: how much of it they hide
      const Zc = fr.Z; og.setTransform(1, 0, 0, 1, 0, 0); og.clearRect(0, 0, oc.width, oc.height); og.setTransform(k, 0, 0, k, 0, 0);
      let any = false;
      for (const o of set.occluders) { const Zo = cam.groundToWorld(o.polygon[0][0], o.base_y)[1]; if (Zo < Zc) { any = true; og.fillStyle = '#000'; og.beginPath(); o.polygon.forEach((q, i) => i ? og.lineTo(q[0], q[1]) : og.moveTo(q[0], q[1])); og.closePath(); og.fill(); } }
      if (any) { const O = mask(oc, og); let hid = 0; for (let i = 0; i < S.m.length; i++) if (S.m[i] && O.m[i]) hid++; R.occFrac[id].push({ f, frac: hid / S.c }); }
    }
    if (opts.onProgress && f % 12 === 0) { opts.onProgress(f / N); await new Promise(r => setTimeout(r, 0)); }
  }
  globalThis.__suiteRaw = R;                       // raw per-frame measures, for inspection
  return summarize(R, F0, probes);
}

function cardFacingPhi(view, cardId, phi, tr, F0) {
  // the direction a card's figure faces, from its view and whether it was drawn mirrored
  const card = F0.ctx.parts.find(p => p.id === cardId); if (!card) return phi;
  const sideR = (card.facing || 'R') === 'R' ? !card._flip : card._flip;
  const base = { profile: 0, threequarter: 40, front: 90, threequarter_back: -40, back: -90 }[view] ?? 0;
  return sideR ? base : 180 - base;
}

function summarize(R, F0, probes) {
  const { scene, comp } = F0, T = THRESHOLDS, items = [];
  const ids = comp.order;
  // foot slide
  { const per = {}; let worst = 0, frames = [];
    for (const id of ids) { const v = R.slide[id]; const m = v.reduce((a, b) => Math.max(a, b.cm), 0); per[id] = +m.toFixed(3); worst = Math.max(worst, m); frames.push(...v.filter(x => x.cm > T.foot_slide_cm_per_frame).map(x => x.f)); }
    items.push({ id: 'foot_slide', label: 'foot slide (planted soles, as drawn)', value: +worst.toFixed(3), unit: 'cm/frame max', threshold: `≤ ${T.foot_slide_cm_per_frame}`, pass: worst <= T.foot_slide_cm_per_frame, frames: [...new Set(frames)].sort((a, b) => a - b), per }); }
  // reach
  { const per = {}; let worst = 0, frames = [];
    for (const id of ids) { per[id] = +comp.chars[id].ratioMax.toFixed(3); worst = Math.max(worst, comp.chars[id].ratioMax); frames.push(...R.reach[id]); }
    const legs = Math.max(...ids.map(id => comp.chars[id].legRatioMax));
    items.push({ id: 'reach', label: 'reach (IK target / arm length, held reaches)', value: +worst.toFixed(3), unit: `ratio max · legs ${legs.toFixed(3)}`, threshold: `≤ ${T.reach_ratio}`, pass: worst <= T.reach_ratio && legs <= 1.0001, frames: [...new Set(frames)], per }); }
  // contact
  { const per = {}; let worst = 0, worstPx = 0, frames = [];
    for (const c of R.contact) { const k = `${c.who}.${c.side}→${c.what}`; per[k] = Math.max(per[k] || 0, +c.pct.toFixed(3)); if (c.pct > worst) { worst = c.pct; worstPx = c.px; } if (c.pct > T.contact_error_pct_height) frames.push(c.f); }
    items.push({ id: 'contact_error', label: 'contact error (drawn palm to drawn target)', value: R.contact.length ? +worst.toFixed(3) : null, unit: `% of figure height max (${worstPx.toFixed(1)} px) over ${R.contact.length} contact-frames`, threshold: `≤ ${T.contact_error_pct_height}%`, pass: worst <= T.contact_error_pct_height, frames: [...new Set(frames)], per }); }
  // scale
  { const per = {}; let worst = 0, frames = [], by = '';
    for (const id of ids) { const v = R.scale[id]; if (!v.length) { per[id] = 'no standing frames'; continue; } const m = v.reduce((a, b) => Math.abs(b.err) > Math.abs(a) ? b.err : a, 0); per[id] = `${m >= 0 ? '+' : ''}${m.toFixed(2)}% (n=${v.length}, ${v[0].px.toFixed(0)} vs ${v[0].exp.toFixed(0)} px)`; worst = Math.max(worst, Math.abs(m)); by = v[0].by; frames.push(...v.filter(x => Math.abs(x.err) > T.scale_error_pct).map(x => x.f)); }
    items.push({ id: 'scale_vs_set', label: 'figure scale vs set scale (drawn head top to the ground point, vs H × px/cm there)', value: +worst.toFixed(2), unit: `% max |error| · expected from ${by || '—'}`, threshold: `≤ ${T.scale_error_pct}%`, pass: worst <= T.scale_error_pct, frames: [...new Set(frames)], per }); }
  // occluders
  { const per = {}, frames = []; let maxHidden = 0;
    for (const id of ids) { frames.push(...R.inOcc[id]); const h = R.occFrac[id].reduce((a, b) => Math.max(a, b.frac), 0); maxHidden = Math.max(maxHidden, h); per[id] = `inside footprint ${R.inOcc[id].length} f · hidden max ${(100 * h).toFixed(0)}%`; }
    items.push({ id: 'occlusion', label: 'occluders (standing inside a footprint; share hidden behind nearer occluders)', value: frames.length, unit: `frames inside · max hidden ${(100 * maxHidden).toFixed(0)}%`, threshold: '0 frames inside', pass: frames.length === 0, frames: [...new Set(frames)].sort((a, b) => a - b), per, warn: maxHidden > T.occluded_fraction_warn }); }
  // pairs
  { const per = {}, frames = []; let minClr = Infinity, bad = 0;
    for (const [k, v] of Object.entries(R.pair)) { per[k] = `${v.min.toFixed(0)} cm @${v.minF}${v.frames.length ? ` · overlap ${v.frames.length} f${v.touch ? ' (touch beat)' : ''}` : ''}`; minClr = Math.min(minClr, v.min); if (!v.touch) { frames.push(...v.frames); bad += v.frames.length; } }
    items.push({ id: 'bodies', label: 'bodies intersecting each other (ground clearance between body radii)', value: Number.isFinite(minClr) ? +minClr.toFixed(1) : null, unit: 'cm min clearance (negative = overlap)', threshold: '≥ 0 (except touch beats)', pass: bad === 0, frames: [...new Set(frames)].sort((a, b) => a - b), per }); }
  // view rules
  { const per = {}, frames = []; let ruled = 0;
    for (const id of ids) if (comp.chars[id].allowed) { ruled++; per[id] = `${R.view[id].length} frames off-rule (allowed: ${comp.chars[id].allowed.join(', ')})`; frames.push(...R.view[id]); }
    items.push({ id: 'ex_facing', label: "EX facing rule (face never seen: drawn view must be back / three-quarter back)", value: ruled ? frames.length : null, unit: ruled ? 'frames off-rule' : 'no ruled character in scene', threshold: '0', pass: frames.length === 0, frames, per }); }
  // off frame
  { const per = {}, frames = []; for (const id of ids) { per[id] = R.off[id].length + ' f'; frames.push(...R.off[id]); }
    items.push({ id: 'off_frame', label: `off-frame (more than ${100 * T.off_frame_fraction}% of the silhouette outside)`, value: new Set(frames).size, unit: 'frames', threshold: '0 (unless an exit)', pass: frames.length === 0, frames: [...new Set(frames)].sort((a, b) => a - b), per }); }
  // walkable
  { const per = {}, frames = []; for (const id of ids) { per[id] = R.walk[id].length + ' f'; frames.push(...R.walk[id]); }
    items.push({ id: 'ground', label: 'feet on the walkable ground', value: new Set(frames).size, unit: 'frames off the ground polygon', threshold: '0', pass: frames.length === 0, frames: [...new Set(frames)].sort((a, b) => a - b), per }); }
  // card view vs travel
  { const per = {}, frames = []; for (const id of ids) if (comp.chars[id].mode === 'cards') { per[id] = R.travel[id].length + ' f'; frames.push(...R.travel[id]); }
    items.push({ id: 'view_vs_travel', label: `card view vs direction of travel (more than ${T.view_vs_travel_deg}° off = walking sideways or backwards)`, value: new Set(frames).size, unit: 'frames', threshold: '0', pass: frames.length === 0, frames: [...new Set(frames)].sort((a, b) => a - b), per, warnOnly: true }); }
  // word sync
  { const words = scene.audio?.words || []; let bad = 0; const per = {};
    for (const b of scene.beats || []) if (b.word_anchor != null) { const w = wordAt(words, b.word_anchor, b.t); const d = w ? Math.abs(b.t - w.w[1]) * comp.fps : Infinity; if (d > T.word_sync_frames) bad++; per[`${b.who} ${b.action} @"${b.word_anchor}"`] = w ? `${(d).toFixed(2)} f` : 'word not found'; }
    items.push({ id: 'word_sync', label: 'beats on their words (beat time vs word start)', value: bad, unit: `beats off by > ${T.word_sync_frames} frame`, threshold: '0', pass: bad === 0, frames: [], per }); }
  for (const it of items) it.frame_ranges = rangeStr(it.frames);
  const contactsDrawn = R.contact.length;
  return { items, frames: comp.N, fps: comp.fps, contact_frames: contactsDrawn, pass: items.filter(i => !i.warnOnly).every(i => i.pass), measured_on: 'render (drawn soles, palms, silhouettes)' };
}

export function checksForScene(Q) { // the contract's checks block (+ the rest)
  const by = id => Q.items.find(i => i.id === id);
  const pick = it => ({ value: it.value, unit: it.unit, threshold: it.threshold, pass: it.pass, frames: it.frame_ranges, per: it.per });
  const out = { measured_on: Q.measured_on, frames: Q.frames, pass: Q.pass };
  for (const it of Q.items) out[it.id] = pick(it);
  return out;
}
