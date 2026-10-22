/* Mechanism clip player: draws one frame of a FORMATS.md clip on a 2D canvas.
   Ops: img {id,m,a?,blend?} · poly {pts,fill,stroke,w,a?} · line {pts|x1..y2,stroke,w,a?} · shadow {x,y,rx,a}
        clip {pts} … unclip · plate {src,m,w,h,video?,poster?} · glow {x,y,r,color,a,blend?} · text {x,y,s,color,txt}
        bg {color} · floor (ignored)
   Image paths: clip.images[id] relative to the clip file (+ clip.image_root). Plate src relative to shots/stage/. */
(function () {
  const IMGS = new Map(), VIDS = new Map();
  function loadImg(url) {
    if (IMGS.has(url)) return IMGS.get(url);
    const p = new Promise(res => { const im = new Image(); im.onload = () => res(im); im.onerror = () => { console.warn('missing', url); res(null); }; im.src = url; });
    IMGS.set(url, p); return p;
  }
  function loadVid(url) {
    if (VIDS.has(url)) return VIDS.get(url);
    const v = document.createElement('video'); v.muted = true; v.loop = true; v.playsInline = true; v.preload = 'auto'; v.crossOrigin = 'anonymous'; v.src = url;
    v.play().catch(() => {}); VIDS.set(url, v); return v;
  }
  const rgba = (hex, a) => { if (!hex || hex[0] !== '#') return hex || '#fff'; let h = hex.slice(1); if (h.length === 3) h = h.split('').map(c => c + c).join('');
    const n = parseInt(h.slice(0, 6), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; };

  async function load(url, opt = {}) {
    const abs = new URL(url, location.href);
    const j = await (await fetch(abs, {cache: 'no-cache'})).json();
    const root = new URL(j.image_root || './', abs);
    const stageBase = opt.stageBase ? new URL(opt.stageBase, location.href) : new URL(abs.href.replace(/\/shots\/stage\/.*$/, '/shots/stage/'));
    const C = {j, url: abs.href, IMG: {}, PLATE: {}, fps: j.clock?.fps || 24, n: j.frames.length};
    await Promise.all(Object.entries(j.images || {}).map(async ([k, p]) => { C.IMG[k] = await loadImg(new URL(p, root).href); }));
    const plates = new Set();
    for (const fr of j.frames) for (const o of fr.draw) if (o.t === 'plate') plates.add(JSON.stringify([o.src, o.video || false, o.poster || null]));
    await Promise.all([...plates].map(async s => { const [src, vid, poster] = JSON.parse(s);
      const P = {}; if (vid && !opt.noVideo) P.video = loadVid(new URL(src, stageBase).href);
      if (!vid) P.img = await loadImg(new URL(src, stageBase).href);
      if (poster) P.poster = await loadImg(new URL(poster, stageBase).href);
      C.PLATE[src] = P; }));
    const v = j.view || {};
    C.box = v.w ? [v.x || 0, v.y || 0, (v.x || 0) + v.w, (v.y || 0) + v.h] : autoBox(C);
    return C;
  }
  function autoBox(C) {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (const fr of C.j.frames) for (const o of fr.draw) {
      if (o.t !== 'img' || !C.IMG[o.id]) continue;
      const [a, b, c, d, e, g] = o.m, w = C.IMG[o.id].naturalWidth, h = C.IMG[o.id].naturalHeight;
      for (const [u, v] of [[0, 0], [w, 0], [0, h], [w, h]]) { const X = a * u + c * v + e, Y = b * u + d * v + g; x0 = Math.min(x0, X); y0 = Math.min(y0, Y); x1 = Math.max(x1, X); y1 = Math.max(y1, Y); }
    }
    return [x0 - 20, y0 - 20, x1 + 20, y1 + 20];
  }
  function path(g, pts, close = true) { g.beginPath(); pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); if (close) g.closePath(); }

  /* draw frame f of clip C into ctx; the clip box maps onto [dx,dy,dw,dh] (default: whole canvas, letterboxed) */
  function draw(g, C, f, o = {}) {
    const cv = g.canvas, [x0, y0, x1, y1] = o.box || C.box;
    const dw = o.dw || cv.width, dh = o.dh || cv.height, dx = o.dx || 0, dy = o.dy || 0;
    const k = Math.min(dw / (x1 - x0), dh / (y1 - y0)), ox = dx + (dw - (x1 - x0) * k) / 2, oy = dy + (dh - (y1 - y0) * k) / 2;
    g.save();
    if (o.bg !== false) { g.fillStyle = o.bg || C.j.bg || '#0d0b0a'; g.fillRect(dx, dy, dw, dh); }
    g.beginPath(); g.rect(dx, dy, dw, dh); g.clip();
    g.setTransform(k, 0, 0, k, ox - x0 * k, oy - y0 * k);
    const base = g.getTransform();
    const fr = C.j.frames[((f % C.n) + C.n) % C.n];
    let depth = 0;
    for (const op of fr.draw) {
      const t = op.t;
      if (t === 'img') { const im = C.IMG[op.id]; if (!im) continue; g.save(); if (op.a != null) g.globalAlpha = op.a; if (op.blend) g.globalCompositeOperation = op.blend; g.transform(...op.m); g.drawImage(im, 0, 0); g.restore(); }
      else if (t === 'clip') { g.save(); depth++; path(g, op.pts); g.clip(); }
      else if (t === 'unclip') { if (depth > 0) { g.restore(); depth--; } }
      else if (t === 'plate') { const P = C.PLATE[op.src] || {}; let s = P.img;
        if (P.video && P.video.readyState >= 2) s = P.video; else if (!s) s = P.poster;
        if (!s) continue; g.save(); if (op.a != null) g.globalAlpha = op.a; g.transform(...(op.m || [1, 0, 0, 1, 0, 0]));
        const sw = s.videoWidth || s.naturalWidth, sh = s.videoHeight || s.naturalHeight;
        const sx = op.sx || 0, sy = op.sy || 0; g.drawImage(s, sx * sw, sy * sh, (op.sw || 1) * sw, (op.sh || 1) * sh, 0, 0, op.w || sw, op.h || sh); g.restore(); }
      else if (t === 'glow') { g.save(); g.globalCompositeOperation = op.blend || 'screen'; const a = op.a ?? 1;
        const gr = g.createRadialGradient(op.x, op.y, 0, op.x, op.y, op.r);
        gr.addColorStop(0, rgba(op.color, a)); gr.addColorStop(0.25, rgba(op.color, a * 0.6)); gr.addColorStop(0.6, rgba(op.color, a * 0.18)); gr.addColorStop(1, rgba(op.color, 0));
        g.fillStyle = gr; g.fillRect(op.x - op.r, op.y - op.r, op.r * 2, op.r * 2); g.restore(); }
      else if (t === 'poly') { g.save(); if (op.a != null) g.globalAlpha = op.a; if (op.blend) g.globalCompositeOperation = op.blend; path(g, op.pts);
        if (op.fill) { g.fillStyle = op.fill; g.fill(); } if (op.stroke) { g.lineWidth = op.w || 2; g.strokeStyle = op.stroke; g.stroke(); } g.restore(); }
      else if (t === 'line') { g.save(); if (op.a != null) g.globalAlpha = op.a; if (op.blend) g.globalCompositeOperation = op.blend; path(g, op.pts || [[op.x1, op.y1], [op.x2, op.y2]], false);
        g.lineCap = 'round'; g.lineJoin = 'round'; if (op.dash) g.setLineDash(op.dash); g.lineWidth = op.w || 2; g.strokeStyle = op.stroke || op.color || '#1a120b'; g.stroke(); g.restore(); }
      else if (t === 'shadow') { g.save(); g.globalAlpha = (op.a ?? .6) * .6; g.fillStyle = '#000'; g.beginPath(); g.ellipse(op.x, op.y, op.rx, op.ry || op.rx * .18, 0, 0, 7); g.fill(); g.restore(); }
      else if (t === 'text') { g.save(); if (op.a != null) g.globalAlpha = op.a; g.fillStyle = op.color || '#efe6da'; g.font = `${op.s || 24}px ${op.font || "'Permanent Marker', cursive"}`; g.textAlign = op.align || 'center'; g.textBaseline = 'middle';
        if (op.rot) { g.translate(op.x, op.y); g.rotate(op.rot * Math.PI / 180); g.fillText(op.txt, 0, 0); } else g.fillText(op.txt, op.x, op.y); g.restore(); }
      else if (t === 'bg') { g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = op.color || '#000'; g.fillRect(dx, dy, dw, dh); g.restore(); }
    }
    while (depth-- > 0) g.restore();
    if (o.anchors) {
      g.setTransform(base); const A = C.j.anchor_tracks || {}, S = C.j.anchors || {};
      g.font = `${12 / k}px JetBrains Mono, monospace`; g.lineWidth = 1.5 / k;
      for (const name of Object.keys(S)) { const p = A[name] ? A[name][((f % C.n) + C.n) % C.n] : S[name]; if (!p) continue;
        g.strokeStyle = '#5fd0ff'; g.beginPath(); g.arc(p[0], p[1], 6 / k, 0, 7); g.moveTo(p[0] - 10 / k, p[1]); g.lineTo(p[0] + 10 / k, p[1]); g.moveTo(p[0], p[1] - 10 / k); g.lineTo(p[0], p[1] + 10 / k); g.stroke();
        g.fillStyle = '#5fd0ff'; g.fillText(name, p[0] + 8 / k, p[1] - 6 / k); }
    }
    g.restore();
  }
  window.MechPlayer = {load, draw};
})();
