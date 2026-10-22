/* engine.js — the cut-out stage's shared engine (shots/stage/index.html and shots/stage/play/index.html).

   One clock, display-list clips (FORMATS.md §1), ensembles (§2), the new layer kinds (§3) and sound (§4).
   Every data path is relative to shots/stage/ (this file's folder); E.url() turns one into a URL from any page.

   Clips   E.loadClip(src, {imgBase}) → C {j, IMG, PLATE, box, n, fps, cm_px, anchors, events}
           images resolve against the clip file (+ image_root when the path itself is not ./ or ../ relative);
           an older Arena clip passes imgBase (its paths are relative to shots/arena/).
           E.drawOps(g, C, f)  draws one frame under the current transform: img {a, blend, shade}, poly, line,
           shadow, clip … unclip (masks, nestable), plate {src, m, w, h, video, poster}, glow, text. bg/floor ignored.
           E.drawClip(cv, C, f) fits the clip's box into a canvas (what an action/clip layer is).
           E.anchorAt(C, name, f) the socket in clip px (anchor_tracks if given, else anchors).
   Sound   E.sfx: index (sfx/index.json), resolve(id) by id → alias → longest prefix → tag, play(id, {vol, loop, offset}).
           Played through WebAudio from fetched, decoded buffers so a cue lands on the audio clock, not on a timer.
   Library E.library(assets) → what the tray can offer (mechanisms, characters, sequences, ensembles, sounds),
           reading only the files assets.json says exist (build_assets.py), so absent folders cost no 404s.
   Canvas  E.drawLayer(g, L, T, env) draws any stage layer on a 2D canvas (the playground, PNG export). */
(function () {
  const STAGE = new URL('./', document.currentScript?.src || location.href).href;   // .../shots/stage/
  const url = p => (!p ? '' : /^(https?:|data:|blob:|\/)/.test(p) ? p : new URL(p, STAGE).href);
  const rel = u => (u && u.startsWith(STAGE) ? u.slice(STAGE.length) : u);
  const FPS = 24;
  const E = {STAGE, url, rel, FPS, CUT: '../kits/cut/'};

  /* ── media caches ── */
  const IMGS = new Map(), VIDS = new Map(), WAIT = new Set();
  E.onMedia = null;   // called when a lazily requested picture arrives (the page redraws)
  function img(u) {
    if (!u) return null;
    if (IMGS.has(u)) return IMGS.get(u);
    const im = new Image(); im.decoding = 'async';
    const p = new Promise(res => { im.onload = () => { res(im); E.onMedia?.(); }; im.onerror = () => { im.bad = true; res(im); }; });
    im.ready = p; im.src = u; IMGS.set(u, im); return im;
  }
  E.img = p => img(url(p));
  function vid(u) {
    if (VIDS.has(u)) return VIDS.get(u);
    const v = document.createElement('video'); Object.assign(v, {muted: true, loop: true, playsInline: true, preload: 'auto'}); v.src = u;
    if (E.playing) v.play().catch(() => {});
    VIDS.set(u, v); return v;
  }
  E.vid = p => vid(url(p));
  E.playing = false;
  E.setPlaying = on => { E.playing = on; VIDS.forEach(v => on ? v.play().catch(() => {}) : v.pause()); };
  const ok = im => im && im.complete && im.naturalWidth > 0 && !im.bad;

  /* ── JSON ── */
  const JS = new Map();
  E.json = p => { const u = url(p); if (!JS.has(u)) JS.set(u, fetch(u).then(r => r.ok ? r.json() : null).catch(() => null)); return JS.get(u); };

  /* ── clips ── */
  const CL = new Map();
  E.clips = CL;
  E.loadClip = (src, opt = {}) => {
    const u = url(src), key = u + '|' + (opt.imgBase || '');
    if (!CL.has(key)) CL.set(key, (async () => {
      const j = await E.json(src); if (!j || !Array.isArray(j.frames) || !j.frames.length) return null;
      const C = {j, src: rel(u), url: u, IMG: {}, PLATE: {}, fps: j.clock?.fps || FPS, n: j.frames.length, cm_px: j.cm_px || j.cast?.[0]?.cm_px || null,
        events: (j.events || []).filter(e => e && e.f != null).sort((a, b) => a.f - b.f)};
      const root = opt.imgBase ? url(opt.imgBase) : u;
      const resolve = p => {
        if (/^(https?:|data:|blob:|\/)/.test(p)) return p;
        if (opt.imgBase || /^\.\.?\//.test(p) || !j.image_root || !/^\.\.?\/?/.test(j.image_root)) return new URL(p, root).href;
        return new URL(p, new URL(j.image_root, u)).href;   // FORMATS §1: images relative to the clip file + image_root
      };
      await Promise.all(Object.entries(j.images || {}).map(([k, p]) => { const im = img(resolve(p)); C.IMG[k] = im; return im.ready; }));
      const plates = new Map();
      for (const fr of j.frames) for (const o of fr.draw || []) if (o.t === 'plate' && o.src && !plates.has(o.src)) plates.set(o.src, o);
      await Promise.all([...plates.values()].map(o => { const P = {};
        if (o.video || /\.(mp4|webm|mov)$/i.test(o.src)) P.video = vid(url(o.src)); else P.img = img(url(o.src));
        if (o.poster) P.poster = img(url(o.poster));
        C.PLATE[o.src] = P; return Promise.race([P.img?.ready || P.poster?.ready || Promise.resolve(), new Promise(r => setTimeout(r, 4000))]); }));
      const v = j.view || {};
      C.box = v.w ? [v.x || 0, v.y || 0, (v.x || 0) + v.w, (v.y || 0) + v.h] : autoBox(C);
      C.anchors = j.anchors || {};
      C.tracks = j.anchor_tracks || {};
      return C;
    })());
    return CL.get(key);
  };
  function autoBox(C) {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    const add = (X, Y) => { if (!isFinite(X) || !isFinite(Y)) return; x0 = Math.min(x0, X); y0 = Math.min(y0, Y); x1 = Math.max(x1, X); y1 = Math.max(y1, Y); };
    const step = Math.max(1, Math.floor(C.n / 50));
    for (let f = 0; f < C.n; f += step) for (const o of C.j.frames[f].draw || []) {
      if (o.t === 'img' && ok(C.IMG[o.id])) { const [a, b, c, d, e, g] = o.m, w = C.IMG[o.id].naturalWidth, h = C.IMG[o.id].naturalHeight;
        for (const [p, q] of [[0, 0], [w, 0], [0, h], [w, h]]) add(a * p + c * q + e, b * p + d * q + g); }
      else if ((o.t === 'poly' || o.t === 'line' || o.t === 'clip') && o.pts) for (const [x, y] of o.pts) add(x, y);
      else if (o.t === 'line') { add(o.x1, o.y1); add(o.x2, o.y2); }
      else if (o.t === 'plate' && o.m) { const [a, b, c, d, e, g] = o.m; for (const [p, q] of [[0, 0], [o.w, 0], [0, o.h], [o.w, o.h]]) add(a * p + c * q + e, b * p + d * q + g); }
      else if (o.t === 'shadow') { add(o.x - o.rx, o.y); add(o.x + o.rx, o.y); }
      else if (o.t === 'text') add(o.x, o.y);
    }
    for (const p of Object.values(C.j.anchors || {})) add(p[0], p[1]);
    if (x0 > x1) return [0, 0, 100, 100];
    return [x0 - 20, y0 - 20, x1 + 20, y1 + 20];
  }
  E.ar = C => C ? (C.box[3] - C.box[1]) / (C.box[2] - C.box[0]) : 1;

  const rgba = (c, a) => { if (!c || c[0] !== '#') return c || '#fff'; let h = c.slice(1); if (h.length === 3) h = h.split('').map(x => x + x).join('');
    const n = parseInt(h.slice(0, 6), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; };
  const path = (g, pts) => { g.beginPath(); pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); };

  /* one frame of a clip, drawn under the current transform */
  E.drawOps = (g, C, f, opt = {}) => {
    const fr = C.j.frames[((f % C.n) + C.n) % C.n]; let masks = 0;
    for (const o of fr.draw || []) {
      const t = o.t;
      if (t === 'img') {
        const im = C.IMG[o.id]; if (!ok(im)) continue;
        g.save(); if (o.a != null) g.globalAlpha *= o.a; if (o.blend) g.globalCompositeOperation = o.blend;
        if (o.shade && !opt.noShade) g.filter = `brightness(${(1 - o.shade * 0.55).toFixed(3)})`;
        g.transform(...o.m); g.drawImage(im, 0, 0); g.restore();
      } else if (t === 'shadow') {
        if (opt.noShadow) continue;
        g.save(); g.globalAlpha *= (o.a ?? .6) * .6; g.fillStyle = '#000'; g.beginPath(); g.ellipse(o.x, o.y, o.rx, o.ry || o.rx * .18, 0, 0, 7); g.fill(); g.restore();
      } else if (t === 'poly') {
        if (!o.pts) continue; g.save(); if (o.a != null) g.globalAlpha *= o.a; path(g, o.pts); g.closePath();
        if (o.fill) { g.fillStyle = o.fill; g.fill(); } if (o.stroke) { g.lineWidth = o.w || 2; g.strokeStyle = o.stroke; g.stroke(); } g.restore();
      } else if (t === 'line') {
        g.save(); if (o.a != null) g.globalAlpha *= o.a; path(g, o.pts || [[o.x1, o.y1], [o.x2, o.y2]]);
        g.lineWidth = o.w || 2; g.lineCap = 'round'; g.lineJoin = 'round'; g.strokeStyle = o.stroke || o.color || '#1a120b'; g.stroke(); g.restore();
      } else if (t === 'clip') {
        if (!o.pts) continue; g.save(); masks++; path(g, o.pts); g.closePath(); g.clip();
      } else if (t === 'unclip') {
        if (masks > 0) { g.restore(); masks--; }
      } else if (t === 'plate') {
        const P = C.PLATE[o.src]; if (!P) continue;
        let src = null;
        if (P.video && P.video.readyState >= 2) src = P.video; else if (ok(P.poster)) src = P.poster; else if (ok(P.img)) src = P.img;
        if (!src) continue;
        g.save(); if (o.a != null) g.globalAlpha *= o.a; if (o.blend) g.globalCompositeOperation = o.blend; if (o.m) g.transform(...o.m);
        const w = o.w || src.videoWidth || src.naturalWidth, h = o.h || src.videoHeight || src.naturalHeight;
        try { g.drawImage(src, 0, 0, w, h); } catch (_) {} g.restore();
      } else if (t === 'glow') {
        g.save(); g.globalCompositeOperation = o.blend || 'lighter'; const a = o.a ?? .8;
        const gr = g.createRadialGradient(o.x, o.y, 0, o.x, o.y, Math.max(1, o.r));
        gr.addColorStop(0, rgba(o.color || '#fff6d8', a)); gr.addColorStop(.35, rgba(o.color || '#fff6d8', a * .45)); gr.addColorStop(1, rgba(o.color || '#fff6d8', 0));
        g.fillStyle = gr; g.beginPath(); g.arc(o.x, o.y, Math.max(1, o.r), 0, 7); g.fill(); g.restore();
      } else if (t === 'text') {
        g.save(); if (o.a != null) g.globalAlpha *= o.a; g.fillStyle = o.color || '#1a120b'; g.font = `${o.s || 24}px ${o.font || "'Permanent Marker', cursive"}`;
        g.textAlign = o.align || 'center'; g.textBaseline = 'middle'; if (o.rot) { g.translate(o.x, o.y); g.rotate(o.rot * Math.PI / 180); g.fillText(o.txt || '', 0, 0); } else g.fillText(o.txt || '', o.x, o.y); g.restore();
      }
    }
    while (masks-- > 0) g.restore();
  };
  E.drawClip = (cv, C, f) => {
    const g = cv.getContext('2d'), [x0, y0, x1] = C.box, k = cv.width / (x1 - x0);
    g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, cv.width, cv.height);
    g.setTransform(k, 0, 0, k, -x0 * k, -y0 * k); E.drawOps(g, C, f); g.setTransform(1, 0, 0, 1, 0, 0);
  };
  E.hasVideo = C => Object.values(C?.PLATE || {}).some(P => P.video);

  /* the frame a clip shows at T: after a play cue at t (once holds the last frame, loop wraps), else T itself, looped */
  E.frameAt = (C, T, play, f0 = 0, f1 = 0, loopDefault = true) => {
    const n = Math.max(1, (f1 || C.n) - f0);
    const k = play ? Math.floor((T - play.t) * (C.fps || FPS) + 1e-6) : Math.floor(T * (C.fps || FPS) + 1e-6);
    const once = play ? play.mode === 'once' : !loopDefault;
    return f0 + (once ? Math.min(Math.max(0, k), n - 1) : ((k % n) + n) % n);
  };
  /* events crossed between two frames of a clip (a play window that may wrap) */
  E.eventsCrossed = (C, fa, fb, wrapped) => {
    if (!C?.events?.length) return [];
    if (!wrapped) return C.events.filter(e => e.f > fa && e.f <= fb);
    return C.events.filter(e => e.f > fa || e.f <= fb);
  };

  /* anchors: per-frame track if given, else the frame-0 socket */
  E.anchorAt = (C, name, f) => {
    const tr = C?.tracks?.[name]; if (tr && tr.length) return tr[((f % tr.length) + tr.length) % tr.length];
    return C?.anchors?.[name] || null;
  };
  E.anchorNames = C => [...new Set([...Object.keys(C?.anchors || {}), ...Object.keys(C?.tracks || {})])];
  /* clip px → stage px for a layer drawn at centre (cx, cy), size w×h, flipped and rotated about its centre */
  E.toStage = (C, geo, p) => {
    const [x0, y0, x1, y1] = C.box, k = geo.w / (x1 - x0);
    let u = (p[0] - x0) * k - geo.w / 2, v = (p[1] - y0) * k - geo.h / 2;
    if (geo.flip) u = -u;
    const r = (geo.rot || 0) * Math.PI / 180, c = Math.cos(r), s = Math.sin(r);
    return [geo.cx + u * c - v * s, geo.cy + u * s + v * c];
  };
  /* the drawn cards' bounds in one frame (an actor walks across its clip's box, so its feet are found per frame) */
  E.frameBox = (C, f) => {
    C._fb = C._fb || new Map(); const k = ((f % C.n) + C.n) % C.n; if (C._fb.has(k)) return C._fb.get(k);
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (const o of C.j.frames[k].draw || []) { if (o.t !== 'img' || !ok(C.IMG[o.id])) continue; const [a, b, c, d, e, g] = o.m, w = C.IMG[o.id].naturalWidth, h = C.IMG[o.id].naturalHeight;
      for (const [p, q] of [[0, 0], [w, 0], [0, h], [w, h]]) { const X = a * p + c * q + e, Y = b * p + d * q + g; x0 = Math.min(x0, X); y0 = Math.min(y0, Y); x1 = Math.max(x1, X); y1 = Math.max(y1, Y); } }
    const r = x0 > x1 ? null : [x0, y0, x1, y1]; C._fb.set(k, r); return r;
  };
  E.stagePpc = (C, geo) => C?.cm_px ? geo.w / (C.box[2] - C.box[0]) * C.cm_px : null;   // stage px per cm of a clip as drawn
  /* the point a rider hangs from an anchor by: its own 'seat'/'hips'/'hand_R' socket if it has one, else its feet */
  E.mountPoint = (C, f, prefer) => {
    for (const n of [prefer, 'mount', 'seat', 'hips', 'pelvis', 'root'].filter(Boolean)) { const p = E.anchorAt(C, n, f); if (p) return p; }
    const fb = E.frameBox(C, f), fl = C.j.floor_y ?? C.j.floor;
    const feet = fb ? [(fb[0] + fb[2]) / 2, fl != null && Math.abs(fl - fb[3]) < 60 ? Math.min(fl, fb[3]) : fb[3]] : [(C.box[0] + C.box[2]) / 2, fl != null && fl < C.box[3] ? fl : C.box[3] - 20];
    if (prefer === 'hips' && fb) return [feet[0], feet[1] - 0.47 * (feet[1] - fb[1])];
    if (prefer === 'hips') return [feet[0], feet[1] - 0.47 * (feet[1] - (C.box[1] + 20))];   // no socket: hips ≈ 47% of the drawn height up from the feet
    return feet;
  };

  /* ── sound: sfx/index.json on WebAudio ── */
  const SFX = E.sfx = {list: [], byId: {}, buf: new Map(), ctx: null, live: new Set(), muted: false, gain: null};
  SFX.load = async () => {
    const j = await E.json('sfx/index.json'); const L = Array.isArray(j) ? j : (j?.sounds || []);
    SFX.list = L; SFX.byId = {};
    for (const s of L) { SFX.byId[s.id] = s; for (const a of s.aliases || []) if (!SFX.byId[a]) SFX.byId[a] = s; }
    return L;
  };
  SFX.resolve = id => {
    if (!id) return null; if (SFX.byId[id]) return SFX.byId[id];
    let k = id; while (k.includes('.')) { k = k.slice(0, k.lastIndexOf('.')); if (SFX.byId[k]) return SFX.byId[k]; }
    const words = id.replace(/^sfx\./, '').split(/[._-]/);
    return SFX.list.find(s => words.every(w => s.tags?.includes(w))) || SFX.list.find(s => words.some(w => s.tags?.includes(w) && w.length > 3)) || null;
  };
  SFX.audio = () => {
    if (!SFX.ctx) { const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return null; SFX.ctx = new AC(); SFX.gain = SFX.ctx.createGain(); SFX.gain.connect(SFX.ctx.destination); }
    if (SFX.ctx.state === 'suspended') SFX.ctx.resume().catch(() => {});
    return SFX.ctx;
  };
  SFX.buffer = s => {
    if (!s) return Promise.resolve(null);
    if (!SFX.buf.has(s.id)) SFX.buf.set(s.id, fetch(url(s.file)).then(r => r.ok ? r.arrayBuffer() : null)
      .then(ab => ab && (SFX.audio()?.decodeAudioData(ab) || null)).catch(() => null));
    return SFX.buf.get(s.id);
  };
  SFX.preload = ids => Promise.all(ids.map(id => SFX.buffer(SFX.resolve(id))));
  /* play now; offset seeks into it (a looped bed joined mid-way). Returns a handle with stop(). */
  SFX.play = (id, o = {}) => {
    const s = SFX.resolve(id), h = {id, s, stopped: false, stop() { this.stopped = true; try { this.src?.stop(); } catch (_) {} SFX.live.delete(this); }};
    if (!s || SFX.muted) return h;
    SFX.live.add(h); const t0 = performance.now();
    SFX.buffer(s).then(b => {
      const ctx = SFX.audio(); if (!b || !ctx || h.stopped) return;
      const src = ctx.createBufferSource(), g = ctx.createGain(); src.buffer = b; src.loop = !!(o.loop ?? false);
      g.gain.value = o.vol ?? 1; src.connect(g); g.connect(SFX.gain);
      const late = (performance.now() - t0) / 1000, off = Math.max(0, (o.offset || 0) + late);
      src.start(0, src.loop ? off % b.duration : Math.min(off, b.duration));
      if (!src.loop && off >= b.duration) return h.stop();
      src.onended = () => SFX.live.delete(h); h.src = src; h.g = g;
    });
    return h;
  };
  SFX.stopAll = () => { [...SFX.live].forEach(h => h.stop()); };

  /* ── library: what the tray offers, from files build_assets.py found on disk ── */
  const listOf = j => Array.isArray(j) ? j : !j ? [] : (['clips', 'items', 'mechs', 'mechanisms', 'sequences', 'seqs', 'ensembles', 'sounds', 'entries'].map(k => j[k]).find(Array.isArray)
    || Object.entries(j).filter(([, v]) => v && typeof v === 'object' && !Array.isArray(v) && (v.path || v.file || v.src || v.clip)).map(([id, v]) => ({id, ...v})));
  const pathOf = (it, dir) => {
    const p = it.path || it.file || it.src || it.clip || it.json; if (!p) return null;
    const top = dir.split('/').filter(Boolean)[0];
    if (p.startsWith(top + '/') || p.startsWith('../')) return p.startsWith('../') ? rel(new URL(p, url(dir)).href) : p;
    return rel(new URL(p, url(dir)).href);
  };
  E.library = async (assets) => {
    const lib = assets?.library || {};
    const out = {mech: [], chars: {}, charClips: [], seq: [], ens: [], sfx: []};
    const clipsFrom = async (idx, files, dir, kind) => {
      const j = idx ? await E.json(idx) : null, L = [];
      for (const it of listOf(j)) { const p = pathOf(it, dir); if (p && /\.json$/.test(p)) L.push({...it, id: it.id || p, title: it.title || it.name || it.id || p.split('/').pop(), src: p, kind}); }
      for (const f of files || []) if (!L.some(x => x.src === f.src)) L.push({kind, ...f});
      return L;
    };
    out.mech = await clipsFrom(lib.mech, lib.mech_clips, 'mech/', 'mech');
    out.seq = await clipsFrom(lib.seq, lib.seq_clips, 'seq/', 'sequence');
    const A = lib.anim !== null ? await E.json(lib.anim || 'anim/index.json') : null;
    if (A) { out.chars = A.characters || {}; out.cm_px = A.cm_px;
      out.charClips = (A.clips || []).map(c => ({...c, src: rel(new URL(c.path, url('anim/index.json')).href), kind: 'action'})); }
    out.ens = (lib.ensembles || []).map(e => ({...e, kind: 'ensemble'}));
    if (lib.sfx !== null) out.sfx = await SFX.load();
    return out;
  };

  /* ── ensembles: a set piece is its layers, placed relative to its anchor at scale_px_per_cm ── */
  E.ENS = {};
  E.loadEnsemble = async (idOrFile, manifest) => {
    const m = (manifest || []).find(e => e.id === idOrFile || e.file === idOrFile);
    const file = m?.file || (/\.json$/.test(idOrFile) ? idOrFile : 'ensembles/' + idOrFile + '.json');
    if (E.ENS[file]) return E.ENS[file];
    const j = await E.json(file); if (!j) return null;
    j.file = file; E.ENS[file] = j; E.ENS[j.id] = j;
    await Promise.all((j.layers || []).filter(l => l.kind === 'clip' && l.src).map(l => E.loadClip(l.src)));
    return j;
  };
  /* the ensemble's own box on the stage (anchor floor-centre by default): [left, top, w, h] */
  E.ensBox = (ens, L) => {
    const s = L.scale_px_per_cm || L.ppc || 2, w = (ens?.size_cm?.w || 200) * s, h = (ens?.size_cm?.h || 200) * s;
    const a = ens?.anchor || 'floor-centre';
    const left = L.x - (a.includes('left') ? 0 : a.includes('right') ? w : w / 2), top = a.startsWith('centre') || a === 'center' ? L.y - h / 2 : L.y - h;
    return [left, top, w, h];
  };
  const BAND = {back: 0, far: 0, mid: 1, front: 2, near: 2};
  /* its layers as ordinary stage layers (centre x, y in stage px), back to front */
  E.ensLayers = (ens, L, partsById) => {
    if (!ens) return [];
    const s = L.scale_px_per_cm || L.ppc || 2, fx = L.flip ? -1 : 1;
    return (ens.layers || []).map((l, k) => ({l, k})).sort((a, b) => (BAND[a.l.band] ?? 1) - (BAND[b.l.band] ?? 1) || a.k - b.k).map(({l}) => {
      const M = {...l}; delete M.x_cm; delete M.y_cm; delete M.w_cm; delete M.h_cm;
      M.kind = l.kind || (l.part ? 'part' : l.src && /\.json$/.test(l.src) ? 'clip' : 'image');
      M.w = (l.w_cm || 50) * s; if (l.h_cm) M.h = l.h_cm * s;
      let h = M.h;
      if (!h) { const p = M.part && partsById?.[M.part]; if (p) h = M.w * p.bbox[3] / p.bbox[2]; }
      if (!h && M.kind === 'clip') { const C = E.clipNow(M.src); if (C) h = M.w * E.ar(C); }
      if (!h) h = M.w;
      M.h = M.h || undefined;
      const yc = l.origin === 'centre' || l.origin === 'center' ? (l.y_cm || 0) * s : (l.y_cm || 0) * s + (l.origin === 'top' ? -h / 2 : h / 2);   // y_cm: the card's foot, up from the floor
      M.x = L.x + fx * (l.x_cm || 0) * s; M.y = L.y - yc; M.flip = !!l.flip !== !!L.flip; M._h = h;
      return M;
    });
  };
  E.ensSlots = (ens, L) => {
    const s = L.scale_px_per_cm || L.ppc || 2, fx = L.flip ? -1 : 1;
    return (ens?.slots || []).map(sl => ({...sl, x: L.x + fx * (sl.x_cm || 0) * s, y: L.y - (sl.y_cm || 0) * s}));
  };
  /* synchronous peek at a loaded clip */
  const NOW = new Map();
  E.clipNow = (src, imgBase) => NOW.get(url(src) + '|' + (imgBase || '')) || null;
  const _load = E.loadClip;
  E.loadClip = (src, opt = {}) => { const p = _load(src, opt); p.then(C => { if (C) NOW.set(url(src) + '|' + (opt.imgBase || ''), C); }); return p; };

  /* ── canvas renderer for any stage layer (playground, PNG export) ──
     env: {parts, CUT, frameOf(L, C) → frame, T, ens} ; L: {kind, x, y, w, h?, rot, flip, op, blend, hide} */
  E.partUrl = (parts, id, CUT) => { const p = parts?.[id]; return p ? url((CUT || '../kits/cut/') + p.file) : null; };
  E.geo = (L, env) => {
    const k = L.kind || (L.part ? 'part' : L.action ? 'action' : 'image');
    let w = L.w || 100, h = L.h;
    if (!h) {
      if (k === 'part') { const p = env.parts?.[L.part]; h = p ? w * p.bbox[3] / p.bbox[2] : w; }
      else if (k === 'clip' || k === 'action') { const C = env.clipOf?.(L); h = C ? w * E.ar(C) : w; }
      else if (k === 'image' || k === 'plane') { const im = E.img(L.src); h = ok(im) ? w * im.naturalHeight / im.naturalWidth : w * (L.ar || 9 / 16); }
      else h = w * (L.ar || 9 / 16);
    }
    return {cx: L.x, cy: L.y, w, h, rot: L.rot || 0, flip: !!L.flip};
  };
  E.drawLayer = (g, L, env) => {
    if (L.hide) return;
    const k = L.kind || (L.part ? 'part' : L.action ? 'action' : 'image');
    if (k === 'sfx') return;
    g.save(); g.globalAlpha *= L.op ?? 1; if (L.blend) g.globalCompositeOperation = L.blend;
    if (k === 'ensemble') {
      const ens = env.ens?.(L); for (const M of E.ensLayers(ens, L, env.parts)) E.drawLayer(g, M, {...env, parentT: env.T});
      g.restore(); return;
    }
    const G = L._geo || E.geo(L, env);
    g.translate(G.cx, G.cy); g.rotate(G.rot * Math.PI / 180); if (G.flip) g.scale(-1, 1);
    if (k === 'part' || k === 'image' || k === 'plane') {
      const im = k === 'part' ? img(E.partUrl(env.parts, L.part, env.CUT)) : E.img(L.src);
      if (ok(im)) g.drawImage(im, -G.w / 2, -G.h / 2, G.w, G.h);
    } else if (k === 'video') {
      const v = E.vid(L.src); if (v.readyState >= 2) try { g.drawImage(v, -G.w / 2, -G.h / 2, G.w, G.h); } catch (_) {}
    } else if (k === 'clip' || k === 'action') {
      const C = env.clipOf?.(L); if (C) { const [x0, y0, x1] = C.box, s = G.w / (x1 - x0); g.translate(-G.w / 2, -G.h / 2); g.scale(s, s); g.translate(-x0, -y0);
        E.drawOps(g, C, env.frameOf ? env.frameOf(L, C) : 0); }
    } else if (k === 'portal') {
      E.drawPortal(g, L, G, env);
    }
    g.restore();
  };
  /* a portal: a mask (ellipse) that opens onto a plate (a world backdrop, still or film), with a rim of light */
  E.drawPortal = (g, L, G, env) => {
    const open = Math.max(0, Math.min(1, L.open ?? 1)), rx = G.w / 2 * open, ry = G.h / 2 * open; if (open <= 0) return;
    g.save(); g.beginPath(); g.ellipse(0, 0, Math.max(1, rx), Math.max(1, ry), 0, 0, 7); g.clip();
    const src = /\.(mp4|webm)$/i.test(L.plate || '') ? E.vid(L.plate) : E.img(L.plate);
    const ready = src && (src.tagName === 'VIDEO' ? src.readyState >= 2 : ok(src));
    if (ready) { const sw = src.videoWidth || src.naturalWidth, sh = src.videoHeight || src.naturalHeight, s = Math.max(G.w / sw, G.h / sh);
      try { g.drawImage(src, -sw * s / 2, -sh * s / 2, sw * s, sh * s); } catch (_) {} }
    else { g.fillStyle = '#0b1a2a'; g.fillRect(-G.w / 2, -G.h / 2, G.w, G.h); }
    g.restore();
    g.save(); g.globalCompositeOperation = 'lighter'; g.lineWidth = Math.max(4, G.w * .03); g.strokeStyle = rgba(L.rim || '#9fe3ff', .55 * open);
    g.beginPath(); g.ellipse(0, 0, Math.max(1, rx), Math.max(1, ry), 0, 0, 7); g.stroke();
    const gr = g.createRadialGradient(0, 0, Math.min(rx, ry) * .8, 0, 0, Math.max(rx, ry) * 1.25); gr.addColorStop(0, rgba(L.rim || '#9fe3ff', 0)); gr.addColorStop(.6, rgba(L.rim || '#9fe3ff', .25 * open)); gr.addColorStop(1, rgba(L.rim || '#9fe3ff', 0));
    g.fillStyle = gr; g.beginPath(); g.ellipse(0, 0, rx * 1.25, ry * 1.25, 0, 0, 7); g.fill(); g.restore();
    // cardboard edge: the portal is a cut hole in a card
    g.save(); g.lineWidth = 3; g.strokeStyle = 'rgba(40,28,18,.85)'; g.setLineDash([10, 7]); g.beginPath(); g.ellipse(0, 0, rx + 3, ry + 3, 0, 0, 7); g.stroke(); g.restore();
  };

  window.STAGE_ENGINE = E;
})();
