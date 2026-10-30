// Extra code-drawn set pieces and props for the suite (stage lane 1). draw.js calls FX_EXTRA[kind] for any scene/set
// fx kind it does not draw itself. Everything is sized in cm through the set's camera (px/cm at a ground row), so a
// prop is as big as it would be at that depth; nothing is a free screen size.
//
//   prop       a prop card that rides a hand and can be thrown, float free and shatter:
//              {kind:'prop', prop:'tambourine'|'ring'|'phone'|'sunglasses'|'lantern'|'petal'|'seed'|'page'|'heart'|'raven'|'hand'|'star'|'orb'|'micstand'|'mic'|'coin'|'card',
//               size_cm?, keys:[{t, who, side} | {t, who, joint:'chest'|'neck'|…} | {t, at:[x,y], ground_y?} | {t, shatter:true} | {t, hide:true}], spin_dps?, arc_px?, color?}
//   sweep      headlights / passing light: a soft band crossing the frame {t0, t1, period, dir:1|-1, width, color, alpha, polygon?}
//   flash      lightning: {times:[t...], dur?, alpha?, bolt?:{x, y0, y1}}
//   rain       {t0?, t1?, n?, alpha?, slant?}
//   footprints {points:[[x,y]...], times:[t...], color?}     prints pressed into the ground one at a time
//   blinds     {polygon:[[x,y]x4], t0, t1, slats?, color?}    blind slats lifting from the bottom between t0 and t1
//   cracks     {at:[x,y], t, polygon?, black_t?}              forking cracks from a point; the pane goes black at black_t
//   glow       {at:[x,y], ground_y?, times:[t...], r_cm?, color?} a pulse of light (a phone buzzing, an ember)
//   iris       {at:[x,y], t0, dur, r0?, r1?}                  an iris to black around a point (r shrinks r0 -> r1 px)
//   cobweb     {at:[x,y], t0, dur, r_px?, spokes?}           a web spins in from a corner
//   stars      {n?, seed?, alpha?}                            pin-pricked black card (the void)
//   scatter    {prop, n, t0, spread_s, x0, x1, y0, y1}          seeds / petals falling and settling on the ground rows y0..y1
//   reticle    {at, t0, t_open, dur, r_px}                    a scope crosshair that dissolves into widening rings
import { smooth } from './rig.js';

const rnd = seed => { let s = (seed >>> 0) || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); };
const pathPoly = (g, poly) => { g.beginPath(); poly.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.closePath(); };
const boxOf = poly => { let a = [Infinity, Infinity, -Infinity, -Infinity]; for (const [x, y] of poly) a = [Math.min(a[0], x), Math.min(a[1], y), Math.max(a[2], x), Math.max(a[3], y)]; return a; };

// ── prop cards (drawn about their centre, s = px per cm) ──
const PROPS = {
  tambourine(g, s, o) {
    const r = (o.size_cm || 25) / 2 * s;
    g.fillStyle = '#e9dcc0'; g.beginPath(); g.ellipse(0, 0, r, r * 0.92, 0, 0, 7); g.fill();
    g.lineWidth = Math.max(2, r * 0.16); g.strokeStyle = '#8a5a2b'; g.stroke();
    g.lineWidth = Math.max(1, r * 0.03); g.strokeStyle = '#3a2614'; g.stroke();
    for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; g.fillStyle = '#d7d9dc'; g.beginPath(); g.ellipse(Math.cos(a) * r, Math.sin(a) * r * 0.92, r * 0.13, r * 0.08, a, 0, 7); g.fill(); g.strokeStyle = '#555'; g.lineWidth = 1; g.stroke(); }
  },
  ring(g, s, o) {
    const r = (o.size_cm || 3) / 2 * s; g.lineWidth = Math.max(2, r * 0.28); g.strokeStyle = o.color || '#e7c35a';
    g.beginPath(); g.ellipse(0, 0, r, r * 0.8, 0, 0, 7); g.stroke();
    g.fillStyle = '#f4fbff'; g.beginPath(); g.arc(0, -r * 0.95, Math.max(2, r * 0.22), 0, 7); g.fill();
  },
  phone(g, s, o) {
    const w = 7 * s, h = 14 * s; g.fillStyle = '#121418'; g.fillRect(-w / 2, -h / 2, w, h);
    g.fillStyle = o.lit === false ? '#1c2228' : '#bfe6ff'; g.fillRect(-w / 2 + s * 0.6, -h / 2 + s * 1.2, w - s * 1.2, h - s * 2.4);
  },
  sunglasses(g, s) {
    const w = 14 * s; g.fillStyle = '#0d0d0f'; g.strokeStyle = '#c0392b'; g.lineWidth = Math.max(1, 0.5 * s);
    for (const sx of [-1, 1]) { g.beginPath(); g.ellipse(sx * w * 0.26, 0, w * 0.22, w * 0.15, 0, 0, 7); g.fill(); g.stroke(); }
    g.beginPath(); g.moveTo(-w * 0.06, -w * 0.03); g.lineTo(w * 0.06, -w * 0.03); g.stroke();
  },
  lantern(g, s, o) {
    const w = 14 * s, h = 22 * s; g.fillStyle = '#2b2118'; g.fillRect(-w / 2, -h / 2, w, h);
    const gl = g.createRadialGradient(0, 0, 0, 0, 0, w * 1.6); gl.addColorStop(0, 'rgba(255,200,110,.95)'); gl.addColorStop(1, 'rgba(255,170,70,0)');
    g.fillStyle = '#ffd98a'; g.fillRect(-w / 2 + 2, -h / 2 + 4, w - 4, h - 8); g.fillStyle = gl; g.beginPath(); g.arc(0, 0, w * 1.6, 0, 7); g.fill();
  },
  petal(g, s, o) { const r = (o.size_cm || 4) * s; g.fillStyle = o.color || '#f2b8c6'; g.beginPath(); g.ellipse(0, 0, r, r * 0.45, 0.4, 0, 7); g.fill(); },
  seed(g, s, o) { const r = Math.max(2, (o.size_cm || 1) * s); g.fillStyle = o.color || '#d9b44a'; g.beginPath(); g.arc(0, 0, r, 0, 7); g.fill(); },
  page(g, s) {
    const pw = 21 * s, ph = 28 * s; g.fillStyle = '#f2ece0'; g.strokeStyle = '#3a2f26'; g.lineWidth = 1; g.fillRect(-pw / 2, -ph / 2, pw, ph); g.strokeRect(-pw / 2, -ph / 2, pw, ph);
    g.fillStyle = 'rgba(40,30,20,.55)'; for (let i = 1; i < 9; i++) g.fillRect(-pw * 0.4, -ph / 2 + i * ph / 10, pw * (0.5 + 0.15 * (i % 3)), Math.max(1, s * 0.6));
  },
  heart(g, s, o, t) {                                     // a cut-paper heart, beating ~70 bpm
    const b = 1 + 0.08 * Math.max(0, Math.sin((t || 0) * Math.PI * 2 * (o.bpm || 70) / 60)) ** 6, r = (o.size_cm || 12) / 2 * s * b;
    g.fillStyle = o.color || '#b3202a'; g.strokeStyle = '#3a0d10'; g.lineWidth = Math.max(1, 0.4 * s);
    g.beginPath(); g.moveTo(0, r * 0.9); g.bezierCurveTo(-r * 1.4, -r * 0.1, -r * 0.6, -r * 1.2, 0, -r * 0.45); g.bezierCurveTo(r * 0.6, -r * 1.2, r * 1.4, -r * 0.1, 0, r * 0.9); g.fill(); g.stroke();
  },
  raven(g, s, o, t) {                                     // a black cut-paper bird, wings flapping
    const w = (o.size_cm || 60) * s, f = Math.sin((t || 0) * Math.PI * 2 * (o.flap_hz || 2.2)), d = o.dir || 1;
    g.scale(d, 1); g.fillStyle = '#0b0b0d';
    g.beginPath(); g.ellipse(0, 0, w * 0.16, w * 0.06, 0, 0, 7); g.fill();
    g.beginPath(); g.moveTo(w * 0.14, -w * 0.02); g.lineTo(w * 0.24, 0); g.lineTo(w * 0.14, w * 0.02); g.fill();
    for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(-w * 0.05, 0); g.quadraticCurveTo(-w * 0.12, -w * 0.25 * f * sd - w * 0.05, -w * 0.32, -w * 0.32 * f * sd); g.lineTo(w * 0.06, 0); g.fill(); }
    g.beginPath(); g.moveTo(-w * 0.15, 0); g.lineTo(-w * 0.27, -w * 0.04); g.lineTo(-w * 0.27, w * 0.04); g.fill();
  },
  hand(g, s, o) {                                         // a hand card lying palm-down (placeholder until a hand-on-ground card is cut)
    const L = (o.size_cm || 19) * s; g.fillStyle = o.color || '#5a3a26'; g.strokeStyle = '#1d120b'; g.lineWidth = Math.max(1, 0.3 * s);
    g.beginPath(); g.ellipse(0, 0, L * 0.3, L * 0.14, 0, 0, 7); g.fill(); g.stroke();
    for (let i = 0; i < 4; i++) { g.beginPath(); g.ellipse(L * 0.3 + L * 0.12, (i - 1.5) * L * 0.07, L * 0.14, L * 0.03, 0, 0, 7); g.fill(); g.stroke(); }
    g.beginPath(); g.ellipse(L * 0.05, -L * 0.17, L * 0.12, L * 0.035, -0.6, 0, 7); g.fill(); g.stroke();
  },
  star(g, s, o, t) {                                      // a cut-foil star with a glow
    const r = (o.size_cm || 10) * s, gl = g.createRadialGradient(0, 0, 0, 0, 0, r * 2.4); gl.addColorStop(0, 'rgba(255,236,170,.9)'); gl.addColorStop(1, 'rgba(255,220,140,0)');
    g.fillStyle = gl; g.beginPath(); g.arc(0, 0, r * 2.4, 0, 7); g.fill(); g.fillStyle = o.color || '#ffe9a8';
    g.beginPath(); for (let i = 0; i < 10; i++) { const a = i * Math.PI / 5 - Math.PI / 2, rr = i % 2 ? r * 0.42 : r; i ? g.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : g.moveTo(Math.cos(a) * rr, Math.sin(a) * rr); } g.closePath(); g.fill();
  },
  orb(g, s, o) {                                          // a universe: rings of light-matter round a core
    const r = (o.size_cm || 30) / 2 * s; const gl = g.createRadialGradient(0, 0, 0, 0, 0, r); gl.addColorStop(0, 'rgba(255,255,255,.95)'); gl.addColorStop(0.4, 'rgba(160,190,255,.6)'); gl.addColorStop(1, 'rgba(90,110,255,0)');
    g.fillStyle = gl; g.beginPath(); g.arc(0, 0, r, 0, 7); g.fill(); g.strokeStyle = 'rgba(200,220,255,.7)'; g.lineWidth = Math.max(1, r * 0.04);
    for (const k of [0.55, 0.8]) { g.beginPath(); g.ellipse(0, 0, r * k, r * k * 0.35, 0.5, 0, 7); g.stroke(); }
  },
  micstand(g, s, o) {                                     // a mic stand standing on the ground: drawn upward from its foot
    const h = (o.h_cm || 150) * s; g.strokeStyle = '#121212'; g.lineWidth = Math.max(2, 1.6 * s);
    g.beginPath(); g.moveTo(-14 * s, 0); g.lineTo(14 * s, 0); g.moveTo(0, 0); g.lineTo(0, -h); g.lineTo(6 * s, -h - 8 * s); g.stroke();
    g.fillStyle = '#2a2a2a'; g.beginPath(); g.ellipse(7 * s, -h - 11 * s, 3 * s, 5 * s, 0.5, 0, 7); g.fill();
  },
  mic(g, s) { g.fillStyle = '#151515'; g.fillRect(-1.6 * s, -9 * s, 3.2 * s, 9 * s); g.fillStyle = '#3a3a3a'; g.beginPath(); g.arc(0, -10 * s, 2.6 * s, 0, 7); g.fill(); },
  coin(g, s) { const r = 2.6 * s; const gl = g.createRadialGradient(0, 0, 0, 0, 0, r * 3); gl.addColorStop(0, 'rgba(160,255,220,.9)'); gl.addColorStop(1, 'rgba(120,255,200,0)'); g.fillStyle = gl; g.beginPath(); g.arc(0, 0, r * 3, 0, 7); g.fill(); g.fillStyle = '#c8fff0'; g.beginPath(); g.arc(0, 0, Math.max(2, r), 0, 7); g.fill(); },
  card(g, s, o) { const w = (o.w_cm || 10) * s, h = (o.h_cm || 10) * s; g.fillStyle = o.color || '#c79a62'; g.fillRect(-w / 2, -h / 2, w, h); },
};

// where a key puts the prop on screen (set px) and at what px/cm
function keyPoint(k, F, f) {
  const { cam, comp } = F;
  if (k.who) {
    const tr = comp.chars[k.who]; if (!tr) return null;
    const fr = tr.frames[Math.max(0, Math.min(tr.frames.length - 1, f))], J = fr.J; if (!J) return null;
    let w = J['tip' + (k.side || 'R')] || J['wrist' + (k.side || 'R')];
    if (k.joint === 'chest') w = [J.neck[0] * 0.7 + J.pelvis[0] * 0.3, J.neck[1] * 0.7 + J.pelvis[1] * 0.3, J.neck[2] * 0.7 + J.pelvis[2] * 0.3 - 6];
    else if (k.joint) w = J[k.joint] || w;
    const p = cam.project(w[0], w[1], w[2]);
    return { x: p[0], y: p[1], s: p[2], alpha: fr.alpha ?? 1 };
  }
  if (k.at) { const gy = k.ground_y ?? k.at[1]; return { x: k.at[0], y: k.at[1], s: Math.max(0.3, cam.ppcAt(gy)), alpha: 1 }; }
  return null;
}

function drawProp(g, fx, F) {
  const { t, comp } = F, f = Math.round(t * comp.fps), keys = fx.keys || [];
  if (!keys.length || t < keys[0].t) return;
  let i = 0; while (i + 1 < keys.length && keys[i + 1].t <= t) i++;
  const k0 = keys[i], k1 = keys[i + 1];
  if (k0.hide) return;                                       // seated / gone (e.g. a hand back on its wrist)
  const sh = keys.find(k => k.shatter);
  const spin = (fx.spin_dps || 0) * (t - keys[0].t) * Math.PI / 180;
  const draw = PROPS[fx.prop] || PROPS.card;
  if (sh && t >= sh.t) {                                    // shattered: pieces fly out, fall and fade
    const prev = keys.filter(k => !k.shatter && k.t <= sh.t).pop(), P = keyPoint(prev, F, Math.round(sh.t * comp.fps)); if (!P) return;
    const R = rnd(fx.seed || 7), u = t - sh.t, n = fx.pieces || 9;
    for (let q = 0; q < n; q++) {
      const a = R() * Math.PI * 2, v = (60 + 140 * R()) * P.s, x = P.x + Math.cos(a) * v * u, y = P.y + Math.sin(a) * v * u * 0.5 + 0.5 * 980 * P.s * u * u * 0.35;
      const al = Math.max(0, 1 - u / (fx.fade_s || 1.6)); if (al <= 0) continue;
      g.save(); g.globalAlpha = al; g.translate(x, Math.min(y, sh.ground_y ?? 1e9)); g.rotate(a + u * 6);
      g.beginPath(); g.moveTo(0, 0); g.lineTo(5 * P.s * (0.5 + R()), 2 * P.s); g.lineTo(2 * P.s, 5 * P.s * (0.5 + R())); g.closePath();
      g.fillStyle = q % 3 ? '#e9dcc0' : '#8a5a2b'; g.fill(); if (q % 4 === 0) { g.fillStyle = '#d7d9dc'; g.beginPath(); g.arc(0, 0, 1.4 * P.s, 0, 7); g.fill(); }
      g.restore();
    }
    return;
  }
  const A = keyPoint(k0, F, f); if (!A) return;
  let x = A.x, y = A.y, s = A.s, al = A.alpha;
  if (k1 && !k1.shatter) {
    const B = keyPoint(k1, F, f); if (B) {
      const u = (t - k0.t) / Math.max(1e-3, k1.t - k0.t), e = k1.ease === 'linear' ? u : smooth(u);
      x = A.x + (B.x - A.x) * e; y = A.y + (B.y - A.y) * e - Math.sin(Math.PI * e) * (k1.arc_px ?? fx.arc_px ?? 0); s = A.s + (B.s - A.s) * e;
    }
  }
  g.save(); g.globalAlpha = (fx.alpha ?? 1) * al; g.translate(x, y); g.rotate(spin + (fx.rot || 0)); draw(g, s, fx, t); g.restore();
}

export const FX_EXTRA = {
  prop: drawProp,
  sweep(g, fx, F) {
    const { t, set } = F, W = set.frame[0], H = set.frame[1];
    if (t < (fx.t0 ?? 0) || t > (fx.t1 ?? 1e9)) return;
    const per = fx.period || 2.4, u = ((t - (fx.t0 ?? 0)) % per) / per, d = fx.dir || 1;
    const x = d > 0 ? -0.3 * W + u * 1.6 * W : 1.3 * W - u * 1.6 * W, w = fx.width || 380;
    g.save(); if (fx.polygon) { pathPoly(g, fx.polygon); g.clip(); }
    g.globalCompositeOperation = 'screen'; g.globalAlpha = (fx.alpha ?? 0.4) * Math.sin(Math.PI * u);
    const gr = g.createLinearGradient(x - w, 0, x + w, 0); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(0.5, fx.color || '#fff1c8'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.beginPath(); g.moveTo(x - w, 0); g.lineTo(x + w, 0); g.lineTo(x + w * 1.8 * d, H); g.lineTo(x - w * 0.2 * d, H); g.closePath(); g.fill(); g.restore();
  },
  flash(g, fx, F) {
    const { t, set } = F, W = set.frame[0], H = set.frame[1], dur = fx.dur || 0.3;
    for (const t0 of fx.times || []) {
      const u = (t - t0) / dur; if (u < 0 || u > 1) continue;
      const a = (fx.alpha ?? 0.75) * (u < 0.15 ? 1 : Math.exp(-(u - 0.15) * 5)) * (u > 0.3 && u < 0.4 ? 0.3 : 1);
      g.save(); g.globalCompositeOperation = 'screen'; g.globalAlpha = a; g.fillStyle = fx.color || '#dfe9ff'; g.fillRect(0, 0, W, H);
      if (fx.bolt) {
        const R = rnd(Math.round(t0 * 100)), b = fx.bolt; let x = b.x, y = b.y0; g.globalAlpha = Math.min(1, a * 1.4); g.strokeStyle = '#ffffff'; g.lineWidth = 5; g.shadowColor = '#bcd2ff'; g.shadowBlur = 24;
        g.beginPath(); g.moveTo(x, y); while (y < b.y1) { y += 30 + 40 * R(); x += (R() - 0.5) * 90; g.lineTo(x, y); } g.stroke();
      }
      g.restore();
    }
  },
  rain(g, fx, F) {
    const { t, set } = F, W = set.frame[0], H = set.frame[1];
    if (t < (fx.t0 ?? 0) || t > (fx.t1 ?? 1e9)) return;
    const R = rnd(fx.seed || 3), n = fx.n || 260, sl = fx.slant ?? 0.18;
    g.save(); g.strokeStyle = fx.color || 'rgba(210,225,240,1)'; g.globalAlpha = fx.alpha ?? 0.35; g.lineWidth = 1.6;
    g.beginPath();
    for (let i = 0; i < n; i++) { const x0 = R() * W * 1.2 - 0.1 * W, sp = 1400 + 900 * R(), ph = R() * H, y = (ph + t * sp) % (H + 120) - 60, L = 26 + 30 * R(); g.moveTo(x0 + y * sl, y); g.lineTo(x0 + (y + L) * sl, y + L); }
    g.stroke(); g.restore();
  },
  footprints(g, fx, F) {
    const { t, cam } = F;
    (fx.points || []).forEach((p, i) => {
      const t0 = (fx.times || [])[i] ?? 0; if (t < t0) return;
      const s = cam.ppcAt(p[1]), a = Math.min(1, (t - t0) / 0.25);
      g.save(); g.globalAlpha = (fx.alpha ?? 0.7) * a; g.fillStyle = fx.color || 'rgba(35,28,22,1)';
      g.beginPath(); g.ellipse(p[0], p[1], 5 * s, 12 * s * 0.35, 0, 0, 7); g.fill();
      g.beginPath(); g.ellipse(p[0], p[1] - 9 * s * 0.35, 4 * s, 5 * s * 0.35, 0, 0, 7); g.fill(); g.restore();
    });
  },
  blinds(g, fx, F) {
    const { t } = F, b = boxOf(fx.polygon), n = fx.slats || 14, u = smooth((t - fx.t0) / Math.max(0.01, fx.t1 - fx.t0));
    const h = b[3] - b[1], slat = h / n, top = b[1], stack = Math.round(n * u);   // lifted slats bunch at the top
    g.save(); pathPoly(g, fx.polygon); g.clip();
    for (let i = 0; i < n; i++) {
      const lifted = i >= n - stack, y = lifted ? top + (n - 1 - i) * slat * 0.18 : top + i * slat;
      g.fillStyle = fx.color || 'rgba(222,214,196,.94)'; g.fillRect(b[0], y, b[2] - b[0], lifted ? slat * 0.16 : slat * 0.82);
      g.fillStyle = 'rgba(0,0,0,.25)'; g.fillRect(b[0], y + (lifted ? slat * 0.14 : slat * 0.72), b[2] - b[0], 2);
    }
    g.restore();
  },
  cracks(g, fx, F) {
    const { t } = F; if (t < fx.t) return;
    const R = rnd(fx.seed || 11), u = Math.min(1, (t - fx.t) / 0.35), [cx, cy] = fx.at;
    g.save(); if (fx.polygon) { pathPoly(g, fx.polygon); g.clip(); }
    if (fx.black_t != null && t >= fx.black_t && fx.polygon) { g.globalAlpha = Math.min(1, (t - fx.black_t) / 0.6); g.fillStyle = '#050505'; pathPoly(g, fx.polygon); g.fill(); g.globalAlpha = 1; }
    g.strokeStyle = 'rgba(240,248,255,.9)'; g.lineWidth = 2.2; g.shadowColor = '#fff'; g.shadowBlur = 6;
    for (let k = 0; k < (fx.n || 11); k++) {
      let a = R() * Math.PI * 2, x = cx, y = cy, L = (180 + 380 * R()) * u;
      g.beginPath(); g.moveTo(x, y);
      for (let d = 0; d < L; d += 34) { a += (R() - 0.5) * 0.7; x += Math.cos(a) * 34; y += Math.sin(a) * 34; g.lineTo(x, y); }
      g.stroke();
    }
    g.restore();
  },
  glow(g, fx, F) {
    const { t, cam } = F, [x, y] = fx.at, s = cam.ppcAt(fx.ground_y ?? y), r = (fx.r_cm || 40) * s;
    for (const t0 of fx.times || []) {
      const u = (t - t0) / (fx.dur || 0.5); if (u < 0 || u > 1) continue;
      g.save(); g.globalCompositeOperation = 'screen'; g.globalAlpha = (fx.alpha ?? 0.8) * Math.sin(Math.PI * u);
      const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, fx.color || 'rgba(190,230,255,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); g.restore();
    }
  },
  iris(g, fx, F) {
    const { t, set } = F; if (t < fx.t0) return;
    const u = smooth((t - fx.t0) / (fx.dur || 1)), r0 = fx.r0 ?? 1400, r1 = fx.r1 ?? 0, r = r0 + (r1 - r0) * u, [x, y] = fx.at;
    g.save(); g.fillStyle = fx.color || '#040404'; g.beginPath(); g.rect(0, 0, set.frame[0], set.frame[1]); g.arc(x, y, Math.max(0.1, r), 0, Math.PI * 2, true); g.fill('evenodd'); g.restore();
  },
  cobweb(g, fx, F) {
    const { t } = F; if (t < fx.t0) return;
    const u = smooth((t - fx.t0) / (fx.dur || 2)), [x, y] = fx.at, R = fx.r_px || 260, n = fx.spokes || 9, dirx = fx.flip ? -1 : 1;
    g.save(); g.strokeStyle = 'rgba(235,235,235,.55)'; g.lineWidth = 1.2;
    for (let i = 0; i < n; i++) { const a = (i / (n - 1)) * Math.PI / 2; g.beginPath(); g.moveTo(x, y); g.lineTo(x + dirx * Math.cos(a) * R * Math.min(1, u * 1.6), y + Math.sin(a) * R * Math.min(1, u * 1.6)); g.stroke(); }
    const rings = Math.floor(10 * u);
    for (let k = 1; k <= rings; k++) { const rr = R * k / 10; g.beginPath(); for (let i = 0; i < n; i++) { const a = (i / (n - 1)) * Math.PI / 2, px = x + dirx * Math.cos(a) * rr, py = y + Math.sin(a) * rr; i ? g.lineTo(px, py) : g.moveTo(px, py); } g.stroke(); }
    g.restore();
  },
  scatter(g, fx, F) {                                     // seeds / petals / stars falling and settling on the ground
    const { t, cam } = F, R = rnd(fx.seed || 5), n = fx.n || 40, draw = PROPS[fx.prop || 'seed'];
    for (let i = 0; i < n; i++) {
      const t0 = (fx.t0 ?? 0) + R() * (fx.spread_s ?? 2), x = fx.x0 + R() * (fx.x1 - fx.x0), gy = fx.y0 + R() * (fx.y1 - fx.y0), dur = 1.2 + R();
      if (t < t0) continue;
      const u = Math.min(1, (t - t0) / dur), y = -40 + (gy + 40) * u * u, s = Math.max(0.3, cam.ppcAt(gy));
      g.save(); g.globalAlpha = fx.alpha ?? 1; g.translate(x + Math.sin(i + t) * 6 * (1 - u), y); g.rotate(R() * 6 + (1 - u) * t * 3); draw(g, s, fx, t); g.restore();
    }
  },
  reticle(g, fx, F) {                                     // a scope's crosshair on a point; its arms dissolve into rings that widen off the frame
    const { t } = F; if (t < fx.t0) return;
    const [x, y] = fx.at, r = fx.r_px || 220, u = smooth((t - (fx.t_open ?? fx.t0 + 2)) / (fx.dur || 3));
    g.save(); g.strokeStyle = fx.color || 'rgba(255,90,80,.85)'; g.lineWidth = 3;
    const arm = r * (1 - u);
    if (u < 1) { g.globalAlpha = 1 - u; g.beginPath(); g.arc(x, y, r * 0.55, 0, 7); g.moveTo(x - r, y); g.lineTo(x - r + arm * 0.8, y); g.moveTo(x + r, y); g.lineTo(x + r - arm * 0.8, y);
      g.moveTo(x, y - r); g.lineTo(x, y - r + arm * 0.8); g.moveTo(x, y + r); g.lineTo(x, y + r - arm * 0.8); g.stroke(); }
    if (u > 0) { g.strokeStyle = fx.ring_color || 'rgba(255,230,190,.8)'; for (let k = 0; k < 4; k++) { const rr = r * 0.55 + (k * 0.25 + u) * 1400 * u; g.globalAlpha = Math.max(0, 0.8 - u * 0.6 - k * 0.15); g.beginPath(); g.arc(x, y, rr, 0, 7); g.stroke(); } }
    g.restore();
  },
  stars(g, fx, F) {
    const { set } = F, R = rnd(fx.seed || 21), W = set.frame[0], H = set.frame[1];
    g.save(); g.fillStyle = '#f2ece0';
    for (let i = 0; i < (fx.n || 160); i++) { g.globalAlpha = (fx.alpha ?? 0.6) * (0.3 + 0.7 * R()); const r = 0.6 + 1.6 * R(); g.beginPath(); g.arc(R() * W, R() * H, r, 0, 7); g.fill(); }
    g.restore();
  },
};
