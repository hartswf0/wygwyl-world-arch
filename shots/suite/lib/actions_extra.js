// Extra actions for the suite (stage lane 1): moves the shared solver does not have, applied to the solved frames.
// They are ordinary beats ({t, who, action, word_anchor, args}); the solver ignores actions it does not know, and
// applyExtras() runs right after compileScene(). Each one moves the whole posed skeleton (fr.J) in world cm, so the
// renderer, the drawn soles and every check see the moved body; nothing is hand-placed on screen.
//
//   drop     {cm=320, dur=1.1, tumble_deg=0, ease='in'}   the body falls cm below where it stands (offset is kept):
//                                                          a fall from a rail, a trip into a hole, a plunge in the void
//   rise     {cm=0, dur=0.9, tumble_deg=0, ease='out'}    back to an offset of -cm (0 = on the ground again)
//   float    {amp_cm=6, period_s=2.6, t1?}                 a slow hover (the void, the dream): bob around the current offset
//   tumble   {deg=360, dur=1.6}                            turn over in the picture plane about the pelvis (offset kept)
// It also tags the frames of the solver's own sit / stand transitions as posture 'sit_transition'.
//
// While a body is off the ground its soles are not planted (so foot slide does not count a fall), its posture is
// 'air' (so the scale check, which needs a standing figure on its ground point, skips those frames).
import { smooth, D2R } from './rig.js';

export const EXTRA_ACTIONS = {
  drop: { args: '{cm?, dur?, tumble_deg?, ease?}', doc: 'fall cm below the ground point (kept); soles unplanted while off the ground' },
  rise: { args: '{cm?, dur?, tumble_deg?, ease?}', doc: 'come back up to -cm (0 = standing on the ground again)' },
  float: { args: '{amp_cm?, period_s?, t1?}', doc: 'hover: slow bob in the air (void scenes)' },
  tumble: { args: '{deg?, dur?}', doc: 'turn over in the picture plane about the pelvis' },
};

const EASE = { in: u => u * u, out: u => 1 - (1 - u) * (1 - u), linear: u => u, smooth };

export function applyExtras(comp, scene) {
  const fps = comp.fps;
  // sitting down and getting up are neither standing nor seated: tag those frames so a scale check that wants a
  // standing figure on its ground point does not read a half-bent body as a wrong scale (sit 0.7 s, stand 0.6 s in the solver)
  for (const id of comp.order) for (const b of (scene.beats || []).filter(b => b.who === id && (b.action === 'sit' || b.action === 'stand'))) {
    const d = b.action === 'sit' ? 0.7 : 0.6;
    for (const fr of comp.chars[id].frames) if (fr.t >= b.t - 1e-6 && fr.t <= b.t + d + 0.05 && fr.posture === 'stand') fr.posture = 'sit_transition';
  }
  for (const id of comp.order) {
    const tr = comp.chars[id];
    const bs = (scene.beats || []).filter(b => b.who === id && EXTRA_ACTIONS[b.action]).sort((a, b) => a.t - b.t);
    if (!bs.length) continue;
    // keyed channels: vertical offset (cm, negative = down) and picture-plane roll (deg)
    const yKeys = [{ t: 0, v: 0, dur: 0, ease: 'linear' }], rKeys = [{ t: 0, v: 0, dur: 0, ease: 'linear' }], floats = [];
    let y = 0, r = 0;
    for (const b of bs) {
      const a = b.args || {};
      if (b.action === 'drop') { y = -(a.cm ?? 320); yKeys.push({ t: b.t, v: y, dur: a.dur ?? 1.1, ease: a.ease || 'in' }); if (a.tumble_deg) { r += a.tumble_deg; rKeys.push({ t: b.t, v: r, dur: a.dur ?? 1.1, ease: 'smooth' }); } }
      if (b.action === 'rise') { y = -(a.cm ?? 0); yKeys.push({ t: b.t, v: y, dur: a.dur ?? 0.9, ease: a.ease || 'out' }); if (a.tumble_deg) { r += a.tumble_deg; rKeys.push({ t: b.t, v: r, dur: a.dur ?? 0.9, ease: 'smooth' }); } }
      if (b.action === 'tumble') { r += a.deg ?? 360; rKeys.push({ t: b.t, v: r, dur: a.dur ?? 1.6, ease: 'smooth' }); }
      if (b.action === 'float') floats.push({ t0: b.t, t1: a.t1 ?? scene.duration, amp: a.amp_cm ?? 6, per: a.period_s ?? 2.6 });
    }
    const at = (keys, t) => { let v = keys[0].v; for (let i = 1; i < keys.length; i++) { const k = keys[i]; if (k.t > t) break; const u = k.dur <= 0.05 ? 1 : Math.min(1, (t - k.t) / k.dur); v = v + (k.v - v) * EASE[k.ease](u); } return v; };
    tr.extra = { yKeys, rKeys, floats };
    for (const fr of tr.frames) {
      const t = fr.f / fps;
      let dy = at(yKeys, t), rot = at(rKeys, t);
      let fl = 0, floating = false;
      for (const q of floats) if (t >= q.t0 && t <= q.t1) { floating = true; fl += q.amp * Math.sin(2 * Math.PI * (t - q.t0) / q.per) * Math.min(1, (t - q.t0) / 0.6); }
      dy += fl;
      if (!floating && Math.abs(dy) < 0.01 && Math.abs(rot) < 0.01) continue;
      const J = fr.J, P = J.pelvis, c = Math.cos(rot * D2R), s = Math.sin(rot * D2R);
      const piv = [P[0], P[1], P[2]];
      for (const k of Object.keys(J)) {
        const v = J[k];
        if (!Array.isArray(v) || v.length !== 3 || typeof v[0] !== 'number') continue;
        let x = v[0] - piv[0], yy = v[1] - piv[1];
        if (rot) { const x2 = x * c - yy * s, y2 = x * s + yy * c; x = x2; yy = y2; }
        J[k] = [piv[0] + x, piv[1] + yy + dy, v[2]];
      }
      for (const sd of ['L', 'R']) {
        const a = fr.arms[sd]; if (a?.targetPoint) a.targetPoint = [a.targetPoint[0], a.targetPoint[1] + dy, a.targetPoint[2]];
      }
      const moving = yKeys.some(k => k.dur > 0.05 && t >= k.t && t <= k.t + k.dur) || rKeys.some(k => k.dur > 0.05 && t >= k.t && t <= k.t + k.dur);
      const air = floating || moving || Math.abs(dy) > 0.5 || Math.abs(rot) > 1;
      if (air) {
        fr.feet = { L: { ...fr.feet.L, planted: false }, R: { ...fr.feet.R, planted: false } };
        fr.posture = 'air'; fr.air = { dy, rot };
        fr.card = { ...fr.card, planted: false };
      }
    }
  }
  return comp;
}
