// Stage 2 (poems 08-14) additions to the Cut-Out Suite, registered through lib/ext.js. A scene loads it with
//   "extensions": ["lib/stage2_extra.js"]
//
// fx kinds (set pieces and code layers, depth-sorted at their ground line like any fx):
//   card   {file, at:[x, y_ground], height_cm, flip?, alpha?, t0?, t1?, fade?, bob_cm?, lift_cm?, rot?, tint?}   a painted prop / set card
//          standing on the ground: sized from the set's px/cm at its foot line and its real height, never by hand
//   glow   {at:[x,y], r_cm, color?, alpha?, flicker?, ground_y}                                  firelight, a lamp, a phone light
//   smoke  {t0?, t1?, alpha?, color?, y0?, y1?, n?}                                            drifting smoke filling a room
//   pour   {from:[x,y], to:[x,y], t0, t1, color?, width_cm?, ground_y}                          a stream of water falling
//   stars  {n?, alpha?, y1?, seed?}                                                              a slow star field (black sets)
// join kinds:
//   pane   a 'screen' join clipped to a pane cut inside a real surface of the set (j.polygon, set px), framed like
//          a painted window; the surface id is kept so the clip lives in a measured part of the plate. Labelled
//          ARCHIVE for as long as it shows.
// cast.ghost: 0..1 opacity for a vellum puppet (the soul, a muse, a memory)
// held props:  cast.props[] {kind:'card', side, file, h_cm, rot?, dx_cm?, dy_cm?}  a prop card in the hand (palm)
// actions (per-frame channels): lean_back {deg, dur} .. lean_reset {dur}; nod {amp}; laugh {dur}; breathe {bars, bpm};
//   pose {card} .. pose_clear: replacement animation for card puppets (a painted pose card per beat, e.g. POET's 30 cards)
import { EXT } from './ext.js';
import { ACTIONS } from './solver.js';
import { img, fileURL } from './adapters.js';
import { smooth, lerp } from './rig.js';

Object.assign(ACTIONS, {
  lean_back:  { args: '{deg?, dur?}', doc: 'lean the torso back (held until lean_reset) [stage2_extra]' },
  lean_reset: { args: '{dur?}', doc: 'back to upright [stage2_extra]' },
  nod:        { args: '{amp?}', doc: 'one head nod, no crouch [stage2_extra]' },
  laugh:      { args: '{dur?}', doc: 'shoulders and head bob with laughter [stage2_extra]' },
  breathe:    { args: '{bars?, bpm?}', doc: 'a slow, deep breath: chest lifts, head tips back [stage2_extra]' },
  pose:       { args: '{card}', doc: 'replacement animation: swap to a painted pose card (held until the next pose, pose_clear or a walk) [stage2_extra]' },
  pose_clear: { args: '{}', doc: 'back to the standing card [stage2_extra]' },
});
const cardId = (tr, id) => !id ? null : id.startsWith('card.') ? id : `card.${tr.cast.character}.${tr.cast.costume}.${id}`;

// ───── action channels ─────
EXT.frame.push((tr, t) => {
  const bs = tr.beats || [];
  if (!bs.length && tr.cast.ghost == null) return null;
  let lean = 0, head = 0, drop = 0, any = false;
  // lean_back holds until lean_reset
  let L = 0;
  for (const b of bs) {
    if (b.t > t) break;
    if (b.action === 'lean_back') { const u = smooth((t - b.t) / (b.args?.dur || 0.8)); L = lerp(L, -(b.args?.deg ?? 12), u); any = true; }
    if (b.action === 'lean_reset') { const u = smooth((t - b.t) / (b.args?.dur || 0.8)); L = lerp(L, 0, u); any = true; }
  }
  lean += L; head += L * 0.6;
  let card = null;                              // pose: the painted card held from its beat to the next pose / clear / walk
  for (const b of bs) { if (b.t > t) break; if (b.action === 'pose') { card = cardId(tr, b.args?.card); any = true; } if (b.action === 'pose_clear' || b.action === 'walk_to') card = null; }
  for (const b of bs) {
    const a = b.args || {}, dt = t - b.t;
    if (dt < 0) continue;
    if (b.action === 'nod' && dt < 0.6) { head += 14 * (a.amp || 1) * Math.sin(Math.PI * dt / 0.6); any = true; }
    if (b.action === 'laugh' && dt < (a.dur || 1.4)) { const d = a.dur || 1.4, env = Math.sin(Math.PI * dt / d); head += -6 * env + 5 * env * Math.abs(Math.sin(dt * 14)); lean += -3 * env; drop += 0.6 * env * Math.abs(Math.sin(dt * 14)); any = true; }
    if (b.action === 'breathe') { const d = (a.bars || 1) * 240 / (a.bpm || 60); if (dt < d) { const k = Math.sin(Math.PI * dt / d); lean += -5 * k; head += -9 * k; any = true; } }
  }
  const ghost = tr.cast.ghost;                 // a vellum puppet (the soul, a muse, a memory): drawn at this opacity
  if (ghost != null) any = true;
  return any ? { lean, headPitch: head, drop, card, alpha: ghost ?? 1 } : null;
});

// ───── images ─────
const IM = new Map();
const keyOf = f => fileURL(f);
EXT.preload.push(async (scene, set, ctx, A) => {
  // Set layers as occluders. Lane C cuts the plate into planes with ONE depth each; a ground plane (P3) at its median
  // depth is drawn over every puppet standing beyond that depth, covering legs with the floor they stand on. A floor
  // never hides a figure standing on it, so P3 goes behind the puppets; a scene can send other planes back too
  // (set_layers: {P0: 'back'}) when a plane's single depth is wrong for its pixels (e.g. a ceiling cut as a near plane).
  const rule = Object.assign({ P3: 'back' }, scene.set_layers || {});
  for (const l of set.layers) {
    if (l._stage2) continue; l._stage2 = true;
    if (rule[l.plane] === 'back' && l.depth_m != null) { l.depth_m_lane_c = l.depth_m; l.depth_m = 1000 + l.depth_m; }
  }
  // cast.play_key: play the character by its painted whole-figure cards from play/data.json (skirt and robe bodies
  // have no working jointed rig in the stager: the knees live in a skirt card it does not draw)
  await Promise.all((scene.cast || []).filter(c => c.play_key).map(c => playCards(c, ctx, A)));
  // two of POET's cards carry an unmeasured body_px in play/data.json (the card is drawn 2x too big); same proportion as his
  // measured kneel (28) and seated (27) cards
  for (const part of ctx.parts) if (CARD_FIGURE_FIX[part.id]) part.figure_px = CARD_FIGURE_FIX[part.id];
  const files = new Set();
  for (const fx of [...(scene.fx || []), ...(set.fx || [])]) if (fx.kind === 'card' && fx.file) files.add(fx.file);
  for (const c of scene.cast || []) for (const p of c.props || []) if (p.kind === 'card' && p.file) files.add(p.file);
  await Promise.all([...files].map(async f => { const im = await img(keyOf(f)); if (im) IM.set(f, { im, box: alphaBox(im) }); }));
});
const CARD_FIGURE_FIX = { 'card.poet.red_black_sunglasses.29': 398, 'card.poet.red_black_sunglasses.26': 339 };
let PLAY = null;
async function playCards(c, ctx, A) {
  PLAY = PLAY || fetch(fileURL('play/data.json')).then(r => r.json());
  const pc = (await PLAY).characters.find(x => x.key === c.play_key); if (!pc) { console.warn('no play card set', c.play_key); return; }
  const VIEW = { prof: 'profile', q3: 'threequarter', front: 'front', back: 'back', back3q: 'threequarter_back' };
  await Promise.all(pc.draws.map(async d => {
    const id = `card.${c.play_key.replace('/', '.')}.${d.f.slice(0, -5)}`;
    if (ctx.parts.some(p => p.id === id && p.character === c.character)) return;
    const file = `play/assets/${c.play_key.replace('/', '__')}/${d.f}`, im = await img(fileURL(file)); if (!im) return;
    const [, y0, , y1] = alphaBox(im), still = d.cls === 'stand' || d.cls === 'walk';
    const figure_px = still ? y1 - y0 : d.body_px;
    ctx.parts.push({ id, character: c.character, costume: c.costume, part: 'body', side: '-', view: VIEW[d.view] || d.view, state: d.cls, file, url: fileURL(file), w: d.w, h: d.h,
      pivot: [d.ax, y1], sockets: {}, scale: { px_per_cm: figure_px / pc.height_cm, source: 'play/data.json card, measured on its alpha' }, figure_px, alpha_top: y0, painted: true, label: d.sem_label, facing: 'R' });
    A.parts[id] = im;
  }));
  ctx._pcache = null;
}
function alphaBox(im) {            // the inked box of a card (cut PNGs carry a margin and a kraft edge)
  const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight;
  const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(im, 0, 0);
  const d = g.getImageData(0, 0, c.width, c.height).data; let x0 = c.width, y0 = c.height, x1 = 0, y1 = 0;
  for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) if (d[(y * c.width + x) * 4 + 3] > 40) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return x1 > x0 ? [x0, y0, x1 + 1, y1 + 1] : [0, 0, c.width, c.height];
}
const win = (t, fx, d = 0.5) => Math.max(0, Math.min(1, fx.t0 != null ? (t - fx.t0) / (fx.fade ?? d) : 1, fx.t1 != null ? (fx.t1 - t) / (fx.fade ?? d) : 1));

// ───── fx ─────
EXT.fx.card = (g, base, fx, F) => {
  const c = IM.get(fx.file); if (!c) return;
  const a = (fx.alpha ?? 1) * win(F.t, fx); if (a <= 0.01) return;
  const [x, y] = fx.at, ppc = F.cam.ppcAt(y), [bx0, by0, bx1, by1] = c.box;
  const k = (fx.height_cm || 100) * ppc / (by1 - by0), bob = (fx.bob_cm || 0) * ppc * Math.sin(F.t * 2.2) + (fx.lift_cm || 0) * ppc;
  g.save(); g.globalAlpha = a; if (fx.tint) g.filter = fx.tint;
  g.translate(x, y - bob); if (fx.rot) g.rotate(fx.rot); g.scale(fx.flip ? -k : k, k);
  g.drawImage(c.im, -(bx0 + bx1) / 2, -by1);
  g.restore();
};
EXT.fx.glow = (g, base, fx, F) => {
  const [x, y] = fx.at, ppc = F.cam.ppcAt(fx.ground_y || y), r = (fx.r_cm || 120) * ppc;
  const fl = fx.flicker ? 0.82 + 0.18 * Math.sin(F.t * 17.3) * Math.sin(F.t * 5.1 + 1) : 1;
  const a = (fx.alpha ?? 0.6) * fl * win(F.t, fx);
  g.save(); g.globalCompositeOperation = 'screen';
  const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, fx.color || 'rgba(255,170,80,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.globalAlpha = a; g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); g.restore();
};
EXT.fx.smoke = (g, base, fx, F) => {
  const { t } = F, W = F.set.frame[0], H = F.set.frame[1];
  const u = fx.t0 != null ? smooth((t - fx.t0) / (fx.rise_s || 3)) : 1; if (u <= 0) return;
  const n = fx.n || 9;
  g.save(); g.filter = 'blur(26px)';
  for (let i = 0; i < n; i++) {
    const ph = i * 2.399, x = ((i * 0.618 * W + t * (18 + 6 * (i % 3))) % (W + 400)) - 200;
    const y = lerp(H * (fx.y1 ?? 0.95), H * (fx.y0 ?? 0.15), ((i * 0.37 + t * 0.03) % 1)) ;
    const r = 160 + 90 * Math.sin(ph + t * 0.3);
    g.globalAlpha = (fx.alpha ?? 0.13) * u; g.fillStyle = fx.color || '#cfd6dc';
    g.beginPath(); g.ellipse(x, y, r * 1.6, r, 0, 0, 7); g.fill();
  }
  g.restore();
};
EXT.fx.pour = (g, base, fx, F) => {
  const a = win(F.t, fx, 0.3); if (a <= 0.01) return;
  const [x0, y0] = fx.from, [x1, y1] = fx.to, ppc = F.cam.ppcAt(fx.ground_y || y1), w = (fx.width_cm || 6) * ppc;
  g.save(); g.globalAlpha = 0.75 * a; g.strokeStyle = fx.color || 'rgba(190,230,255,1)'; g.lineCap = 'round';
  for (let k = 0; k < 3; k++) {
    g.lineWidth = w * (1 - k * 0.3); g.beginPath(); g.moveTo(x0 + k * 2, y0);
    for (let s = 1; s <= 12; s++) { const u = s / 12; g.lineTo(lerp(x0, x1, u) + Math.sin(F.t * 9 + s * 1.3 + k) * w * 0.4, lerp(y0, y1, u * u * 0.5 + u * 0.5)); }
    g.stroke();
  }
  g.globalCompositeOperation = 'screen'; g.fillStyle = 'rgba(220,240,255,.5)';
  for (let s = 0; s < 6; s++) { const ph = (F.t * 2.5 + s / 6) % 1; g.beginPath(); g.ellipse(x1 + Math.sin(s * 7) * w * 2, y1 - ph * w * 2, w * (0.4 + ph), w * 0.3 * (0.4 + ph), 0, 0, 7); g.fill(); }
  g.restore();
};
EXT.fx.stars = (g, base, fx, F) => {
  const W = F.set.frame[0], H = F.set.frame[1], n = fx.n || 220; let s = fx.seed || 7;
  const R = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  g.save();
  for (let i = 0; i < n; i++) { const x = R() * W, y = R() * H * (fx.y1 ?? 1), r = 0.6 + R() * 1.8, tw = 0.6 + 0.4 * Math.sin(F.t * (1 + R() * 2) + i);
    g.globalAlpha = (fx.alpha ?? 0.8) * tw * win(F.t, fx); g.fillStyle = '#efe6da'; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); }
  g.restore();
};

// ───── joins ─────
EXT.joins.pane = (g, base, j, s, F, cv, probe, H) => {
  const { t, scene, set } = F, t1 = j.t_end ?? scene.duration;
  const a = H.fade(t, j.t, t1, j.fade || 0.5) * (j.mix ?? 0.9);
  if (a <= 0.01) return;
  const poly = j.polygon || s?.polygon; if (!poly) return;
  g.setTransform(base.multiply(H.camMatrix(set, cv, s?.parallax ?? 1)));
  g.save();
  if (s && j.inside !== false) { H.pathPoly(g, s.polygon); g.clip(); }
  H.pathPoly(g, poly); g.clip();
  g.globalAlpha = a; g.globalCompositeOperation = j.blend || 'source-over'; if (j.tint) g.filter = j.tint;
  H.coverInto(g, H.fr, H.boxOf(poly));
  g.restore();
  if (j.frame !== false) {            // a cut cardboard edge round the pane so it reads as a window in the set
    g.save(); g.globalAlpha = Math.min(1, a * 1.1); g.strokeStyle = j.frame_color || 'rgba(20,16,12,.85)'; g.lineWidth = j.frame_px || 5; g.lineJoin = 'round';
    H.pathPoly(g, poly); g.stroke(); g.restore();
  }
  const b = H.boxOf(poly), m = H.fr.meta;
  probe.tags.push(H.tag(g, `ARCHIVE · ${m.title}${m.year ? ', ' + m.year : ''}`, b[0] + 4, Math.max(8, b[1] + 4), 0.75));
  probe.joins.push({ kind: 'pane', clip: j.clip, a, surface: j.surface });
};

// ───── held prop cards ─────
EXT.props.card = (g, p, s, F) => {
  const c = IM.get(p.file); if (!c) return false;
  const [bx0, by0, bx1, by1] = c.box, k = (p.h_cm || 20) * s / (by1 - by0);
  g.rotate(p.rot || 0); g.translate((p.dx_cm || 0) * s, (p.dy_cm || 0) * s); g.scale(p.flip ? -k : k, k);
  g.drawImage(c.im, -(bx0 + bx1) / 2, -(by0 + by1) / 2);
  return true;
};
