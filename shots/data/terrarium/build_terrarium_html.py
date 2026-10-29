#!/usr/bin/env python3
"""
build_terrarium_html.py
Builds `shots/terrarium.html` by enhancing `terrarium/unset-04-hartsoe-iii.html` with:
1. Automatic interception & enrichment of `?cart=`, `?land=`, `?wt=`, `?stage=`, `?poem=`, and `?foundry=`
   so `WORLDTEXT GROUND` (`?cart=...landpack.json`) and `PLAY THE REAL CITY` (`?land=...&wt=...`)
   both mount:
   - The 3D terrain heightfield (`hf`), texture (`tex`), and 3D buildings (`bld`),
   - The Continuous 3D Poem Tape & WorldText Ground Ribbon (`play/levels/XX/poem_tape.webp` + `wt/XX.json`),
   - All 6 Multiplane Sidescrolling Scene Stages (`play/levels/XX/s0_ext.webp..s5_ext.webp`) along `A → B → C → D → E → F`,
   - Live 3D Video Screens playing our film cuts (`cel_assets/patches/PXX-00Y.mp4` & `film/poem_XX.mp4`) + spoken audio (`reading.mp3`),
   - 3D Cut-Out Props (`play/levels/XX/props/*.png`) & Articulated Character Standees,
   - Real WYGWYL Deleuze Camera Frustums (`S1 PERCEPT`..`S6 CRYSTAL`) + Foundry Inverse-Topology Pink Wedges,
   - Populated left `FILM STUDIO` drawer with the active poem's real beats, clips, and scenes (replacing the generic "keeper of the storm gate").
2. Seamless Camera Switcher (`[V]` key or Top HUD):
   - `🗺️ 3D OVERVIEW` (Bird's-eye isometric overview of the entire city/island & all 6 stages)
   - `↔️ HORIZONTAL SIDESCROLLER` (Orthographic-like side-scrolling camera locked parallel to the active poem's `A → F` multiplane stage corridor with horizontal scrub slider & `←`/`→` dolly!)
   - `🎥 FRUSTUM POV` (Steps directly into any S1..S6 beat or Foundry shot camera)
   - `🚗 STREET DRIVE` (Standard rig/character street chase cam)
3. 🐕 THE DOG (`HALFWORLD HOUND`) — Interactive 3D AI Helper & Asset/Clip Fetcher:
   - Spawns the iconic orange 3D voxel Dog (with wagging tail, perky ears, snout, collar, and floating 3D speech bubble; toggles between Roof Lookout and Street Companion).
   - Interactive Chat & Fetch Console where you can type natural language requests to fetch clips, props, characters, sounds, scenes, or Foundry worlds directly into the 3D Terrarium.
4. Foundry 3D Worlds, Shots & Inverse Topography Switcher:
   - Instant selector for all 10 Real-City Landpacks, all 14 Poems, and all 6 Elite Foundry Worlds (`w1623`, `w1578`, `w0746`, `w1165`, `w0889`, `w0980`), plus ground map mode toggle (`Satellite/Map` ↔ `Palimpsest` ↔ `Inverse Sculpted After` ↔ `Inverse Before`).
"""

import os

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
SRC_HTML = "/tmp/terrarium_ref/terrarium_unset04.html"
OUT_HTML = os.path.join(ROOT, "shots", "terrarium.html")

WYGWYL_EXTENSION = r"""
<!-- ═══════════════════════════════════════════════════════════════════════════
     WYGWYL TERRARIUM BRIDGE · 90 SCENES + FILM + FOUNDRY TOPOGRAPHY + AI DOG
     ═══════════════════════════════════════════════════════════════════════════ -->
<style id="wygwyl-terrarium-styles">
  #wyg-top-hud {
    position: fixed;
    top: 8px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    background: rgba(8, 13, 19, 0.94);
    border: 1px solid rgba(255, 210, 63, 0.38);
    border-radius: 14px;
    padding: 6px 10px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    font: 600 11px/1.2 -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    color: #f3ead2;
    max-width: calc(100vw - 16px);
  }
  #wyg-top-hud select, #wyg-top-hud button, #wyg-top-hud a {
    font: 700 10px/1 -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    letter-spacing: 0.06em;
    border-radius: 8px;
    padding: 6px 9px;
    border: 1px solid rgba(243, 234, 210, 0.22);
    background: #121a24;
    color: #f3ead2;
    cursor: pointer;
    text-decoration: none;
    white-space: nowrap;
    transition: all 0.15s ease;
  }
  #wyg-top-hud select:hover, #wyg-top-hud button:hover, #wyg-top-hud a:hover {
    border-color: #ffd23f;
    color: #ffd23f;
  }
  #wyg-top-hud button.active {
    background: linear-gradient(180deg, #ffd23f, #e0a81e);
    color: #090d12;
    border-color: #ffd23f;
    box-shadow: 0 0 14px rgba(255, 210, 63, 0.45);
  }
  #wyg-top-hud button.teal-active {
    background: linear-gradient(180deg, #19e6c8, #0fb39b);
    color: #041815;
    border-color: #19e6c8;
    box-shadow: 0 0 14px rgba(25, 230, 200, 0.45);
  }
  #wyg-top-hud .wyg-sep {
    width: 1px;
    height: 18px;
    background: rgba(243, 234, 210, 0.16);
    margin: 0 2px;
  }
  /* Horizontal Sidescroller Scrub Bar */
  #wyg-scroller-bar {
    position: fixed;
    bottom: 66px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9998;
    width: min(780px, calc(100vw - 24px));
    background: rgba(8, 13, 19, 0.94);
    border: 1px solid rgba(25, 230, 200, 0.42);
    border-radius: 14px;
    padding: 8px 14px;
    display: none;
    flex-direction: column;
    gap: 6px;
    box-shadow: 0 12px 32px rgba(0,0,0,0.65);
    backdrop-filter: blur(12px);
    color: #f3ead2;
    font: 600 11px/1.3 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
  }
  #wyg-scroller-bar.show {
    display: flex;
  }
  #wyg-scroller-stops {
    display: flex;
    justify-content: space-between;
    gap: 4px;
  }
  #wyg-scroller-stops button {
    flex: 1;
    background: #141e28;
    border: 1px solid rgba(243,234,210,0.18);
    color: #ddd3bb;
    padding: 5px 6px;
    border-radius: 7px;
    font: 700 10px/1.1 sans-serif;
    cursor: pointer;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  #wyg-scroller-stops button.on {
    border-color: #19e6c8;
    color: #19e6c8;
    background: rgba(25,230,200,0.12);
  }
  /* 🐕 THE DOG — AI Helper & Clip/Asset Fetcher Dock */
  #wyg-dog-dock {
    position: fixed;
    right: 12px;
    bottom: 12px;
    z-index: 9999;
    width: min(410px, calc(100vw - 24px));
    background: linear-gradient(180deg, rgba(16, 22, 30, 0.96), rgba(9, 13, 19, 0.98));
    border: 1.5px solid #ff8a3d;
    border-radius: 16px;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.72), 0 0 22px rgba(255, 138, 61, 0.22);
    color: #f3ead2;
    font: 500 12px/1.4 -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: transform 0.2s ease, height 0.2s ease;
  }
  #wyg-dog-dock.minimized #wyg-dog-body {
    display: none;
  }
  #wyg-dog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 12px;
    background: linear-gradient(90deg, rgba(255, 138, 61, 0.22), rgba(255, 210, 63, 0.08));
    border-bottom: 1px solid rgba(255, 138, 61, 0.3);
    cursor: pointer;
  }
  #wyg-dog-header .dog-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 0.08em;
    color: #ffb067;
    text-transform: uppercase;
  }
  #wyg-dog-header .dog-actions {
    display: flex;
    gap: 5px;
  }
  #wyg-dog-header button {
    background: rgba(0,0,0,0.45);
    border: 1px solid rgba(255,138,61,0.4);
    color: #ffd23f;
    border-radius: 6px;
    padding: 3px 7px;
    font: 700 9px/1 sans-serif;
    cursor: pointer;
  }
  #wyg-dog-body {
    display: flex;
    flex-direction: column;
    max-height: 410px;
  }
  #wyg-dog-log {
    padding: 10px 12px;
    overflow-y: auto;
    max-height: 235px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .dog-msg {
    padding: 8px 10px;
    border-radius: 10px;
    font-size: 11.5px;
    line-height: 1.4;
  }
  .dog-msg.hound {
    background: rgba(255, 138, 61, 0.11);
    border-left: 3px solid #ff8a3d;
    color: #f5ecda;
  }
  .dog-msg.user {
    background: rgba(25, 230, 200, 0.12);
    border-right: 3px solid #19e6c8;
    color: #d8fff8;
    align-self: flex-end;
    max-width: 90%;
  }
  .dog-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    margin-top: 6px;
  }
  .dog-card {
    background: #0c1219;
    border: 1px solid rgba(255, 210, 63, 0.28);
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    transition: border-color 0.15s;
  }
  .dog-card:hover {
    border-color: #ffd23f;
  }
  .dog-card img, .dog-card video {
    width: 100%;
    height: 64px;
    object-fit: cover;
    display: block;
    background: #000;
  }
  .dog-card .dc-meta {
    padding: 4px 6px;
    font-size: 10px;
    color: #cfc6ae;
  }
  .dog-card .dc-meta b {
    color: #ffd23f;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  #wyg-dog-chips {
    display: flex;
    gap: 5px;
    overflow-x: auto;
    padding: 6px 10px;
    border-top: 1px solid rgba(243, 234, 210, 0.1);
    scrollbar-width: none;
  }
  #wyg-dog-chips button {
    flex: 0 0 auto;
    background: #151f2b;
    border: 1px solid rgba(255, 138, 61, 0.32);
    color: #ffcc99;
    padding: 4px 8px;
    border-radius: 12px;
    font: 600 10px/1 sans-serif;
    cursor: pointer;
    white-space: nowrap;
  }
  #wyg-dog-chips button:hover {
    border-color: #ffd23f;
    color: #ffd23f;
  }
  #wyg-dog-input-row {
    display: flex;
    gap: 6px;
    padding: 8px 10px;
    background: rgba(0, 0, 0, 0.35);
    border-top: 1px solid rgba(243, 234, 210, 0.12);
  }
  #wyg-dog-input {
    flex: 1;
    background: #090e14;
    border: 1px solid rgba(255, 138, 61, 0.4);
    border-radius: 10px;
    color: #fff;
    padding: 7px 10px;
    font: 500 12px/1.2 sans-serif;
    outline: none;
  }
  #wyg-dog-input:focus {
    border-color: #ffd23f;
  }
  #wyg-dog-send {
    background: linear-gradient(180deg, #ff8a3d, #e06318);
    color: #fff;
    border: 0;
    border-radius: 10px;
    padding: 0 12px;
    font: 800 11px/1 sans-serif;
    cursor: pointer;
  }
  /* Push default top AGENT bar slightly down so it never collides with #wyg-top-hud */
  #ai-bar.std-agent-shell {
    top: calc(env(safe-area-inset-top, 0px) + 54px) !important;
  }
</style>

<div id="wyg-top-hud">
  <a href="wag_stack.html" title="Back to WAG-STACK Suite">◀ WAG-STACK</a>
  <a href="world_foundry.html" title="World & Foundry Atlas">🌍 WORLD & FOUNDRY ATLAS</a>
  <span class="wyg-sep"></span>
  <label style="font-size:10px;color:#a99f86">STAGE / CITY:</label>
  <select id="wyg-sel-stage" title="Select Scouted Real-City Landpack"></select>
  <label style="font-size:10px;color:#a99f86">POEM:</label>
  <select id="wyg-sel-poem" title="Select Poem 01..14 (Mounts 6 Multiplane Scenes + Film + WorldText)"></select>
  <label style="font-size:10px;color:#a99f86">FOUNDRY 3D:</label>
  <select id="wyg-sel-foundry" title="Mount Evolved Foundry World Topography & Inverse Camera Stands">
    <option value="">— Real City Ground —</option>
  </select>
  <select id="wyg-sel-texmode" title="Switch Ground Texture Layer (Map / Palimpsest / Inverse Sculpted)">
    <option value="map">Ground: Map / Sat</option>
    <option value="palimpsest">Ground: Palimpsest (Routes)</option>
    <option value="sculpted_after">Ground: Inverse Sculpted (After)</option>
    <option value="sculpted_before">Ground: Inverse Before</option>
  </select>
  <span class="wyg-sep"></span>
  <button type="button" id="wyg-cam-overview" title="3D Bird's-Eye Overview of City, Frustums & All 6 Stage Portals">🗺️ 3D OVERVIEW</button>
  <button type="button" id="wyg-cam-scroller" title="Switch to Horizontal 2.5D/3D Sidescroller along the Poem Corridor (Shortcut: V)">↔️ HORIZONTAL SIDESCROLLER [V]</button>
  <button type="button" id="wyg-cam-frustum" title="Cycle through the Poem's Camera Frustums & Foundry Shots">🎥 SHOT FRUSTUM POV</button>
  <button type="button" id="wyg-cam-drive" title="Drive/Walk Street Chase Camera">🚗 STREET DRIVE</button>
  <span class="wyg-sep"></span>
  <button type="button" id="wyg-btn-playfilm" title="Play/Pause Spoken Poem Reading + In-World 3D Film Screens">▶ PLAY POEM FILM</button>
</div>

<div id="wyg-scroller-bar">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
    <span><b style="color:#19e6c8">↔️ HORIZONTAL SIDESCROLLER MODE</b> · <span id="wyg-scroller-label">Poem 01 · Corridor A → F</span></span>
    <div style="display:flex;gap:8px;align-items:center">
      <label style="font-size:10px;color:#a99f86">Elevation:</label>
      <input type="range" id="wyg-scroller-elev" min="1.5" max="18" step="0.5" value="4.2" style="width:75px">
      <label style="font-size:10px;color:#a99f86">Distance:</label>
      <input type="range" id="wyg-scroller-dist" min="8" max="42" step="1" value="18" style="width:75px">
      <button type="button" id="wyg-scroller-auto" style="background:#14242b;border:1px solid #19e6c8;color:#19e6c8;border-radius:6px;padding:3px 8px;cursor:pointer;font:700 10px sans-serif">▶ AUTO-SCROLL</button>
    </div>
  </div>
  <input type="range" id="wyg-scroller-scrub" min="0" max="1" step="0.002" value="0" style="width:100%;accent-color:#19e6c8">
  <div id="wyg-scroller-stops"></div>
</div>

<div id="wyg-dog-dock">
  <div id="wyg-dog-header">
    <div class="dog-title">
      <span style="font-size:16px">🐕</span>
      <span>THE DOG · AI CLIP, PROP & WORLD FETCHER</span>
    </div>
    <div class="dog-actions">
      <button type="button" id="wyg-dog-roof-btn" title="Move Dog between Building Roof Lookout and Street Companion">📍 ON ROOF</button>
      <button type="button" id="wyg-dog-come-btn" title="Call the Dog to your current position">🐾 COME HERE</button>
      <button type="button" id="wyg-dog-min-btn" title="Minimize / Expand Dog Chat">—</button>
    </div>
  </div>
  <div id="wyg-dog-body">
    <div id="wyg-dog-log"></div>
    <div id="wyg-dog-chips">
      <button type="button" data-q="fetch clips for this poem">🎬 Fetch Poem Clips</button>
      <button type="button" data-q="spawn all 6 scenes & props here">🖼️ Mount 6 Scenes & Props</button>
      <button type="button" data-q="bring poet tracksuit and vintage couple">🕺 Spawn Poet & Couple</button>
      <button type="button" data-q="show inverse topology sculpted shots">⛰️ Inverse Topology Shots</button>
      <button type="button" data-q="load foundry world w1623 harbor">🏝️ Foundry w1623 Harbor</button>
      <button type="button" data-q="switch to horizontal sidescroller">↔️ Horizontal Sidescroller</button>
      <button type="button" data-q="fetch shoes and hands from body lab">👞 Fetch Shoes & Hands</button>
    </div>
    <div id="wyg-dog-input-row">
      <input type="text" id="wyg-dog-input" placeholder="Ask the Dog for any shot, clip, prop, character, or world…" autocomplete="off">
      <button type="button" id="wyg-dog-send">WOOF ↵</button>
    </div>
  </div>
</div>

<script id="wygwyl-terrarium-bridge">
(function() {
  'use strict';

  const STATE = {
    master: null,
    foundryShots: null,
    foundryRefs: null,
    foundryInv: null,
    bodyLab: null,
    activeStageKey: 'mount-vernon',
    activePoemNum: '01',
    activeFoundryId: '',
    texMode: 'map',
    viewMode: 'overview', // 'overview' | 'scroller' | 'frustum' | 'drive'
    scrollerT: 0,
    scrollerElev: 4.2,
    scrollerDist: 18,
    scrollerAuto: false,
    frustumIdx: 0,
    stageGroup: null,
    dogGroup: null,
    dogBubbleSprite: null,
    dogMode: 'roof', // 'roof' | 'companion' | 'fetching'
    dogTarget: null,
    spawnedCardsGroup: null,
    videoElements: [],
    readingAudio: new Audio(),
    isPlayingFilm: false,
    corridorPts: [],
    frustumMarkers: [],
  };
  STATE.readingAudio.preload = 'none';

  // Helper: Ground height at (x, z)
  function groundY(x, z) {
    try {
      if (window.HARTSOE_GROUND && window.HARTSOE_GROUND.on && typeof window.HARTSOE_GROUND.y === 'function') {
        const y = window.HARTSOE_GROUND.y(x, z);
        if (Number.isFinite(y)) return y;
      }
    } catch (_) {}
    return 0;
  }

  // Helper: Create high-contrast canvas label sprite
  function makeTextSprite(lines, opts = {}) {
    const bg = opts.bg || 'rgba(10, 15, 22, 0.88)';
    const border = opts.border || '#ffd23f';
    const fg = opts.fg || '#f3ead2';
    const accent = opts.accent || '#ffd23f';
    const w = opts.w || 512, h = opts.h || 144;
    const cv = document.createElement('canvas');
    cv.width = w; cv.height = h;
    const ctx = cv.getContext('2d');
    ctx.fillStyle = bg;
    ctx.strokeStyle = border;
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(4, 4, w - 8, h - 8, 16) : ctx.rect(4, 4, w - 8, h - 8);
    ctx.fill();
    ctx.stroke();

    const arr = Array.isArray(lines) ? lines : [String(lines)];
    arr.forEach((ln, idx) => {
      ctx.font = idx === 0 ? '800 24px "Helvetica Neue", Arial, sans-serif' : '500 18px Georgia, serif';
      ctx.fillStyle = idx === 0 ? accent : fg;
      ctx.fillText(String(ln).slice(0, 46), 20, 38 + idx * 32);
    });

    const tex = new THREE.CanvasTexture(cv);
    tex.colorSpace = THREE.SRGBColorSpace;
    const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false });
    const sp = new THREE.Sprite(mat);
    sp.scale.set(opts.scaleX || 8.5, opts.scaleY || 2.4, 1);
    sp.renderOrder = 950;
    return sp;
  }

  // ── 1. BUILD THE 3D ORANGE DOG (HALFWORLD HOUND) ON ROOF OR STREET ──────────
  function ensureDog() {
    if (STATE.dogGroup && STATE.dogGroup.parent) return STATE.dogGroup;
    if (typeof THREE === 'undefined' || typeof scene === 'undefined') return null;

    const g = new THREE.Group();
    g.name = 'WYGWYL_AI_DOG';
    const furMat = new THREE.MeshLambertMaterial({ color: 0xff8a3d });
    const darkFurMat = new THREE.MeshLambertMaterial({ color: 0xc85a17 });
    const creamMat = new THREE.MeshLambertMaterial({ color: 0xfff0d6 });
    const collarMat = new THREE.MeshBasicMaterial({ color: 0x19e6c8 });
    const eyeMat = new THREE.MeshBasicMaterial({ color: 0x111111 });

    // Torso
    const body = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.85, 2.1), furMat);
    body.position.set(0, 0.85, 0);
    g.add(body);

    // Chest
    const chest = new THREE.Mesh(new THREE.BoxGeometry(1.15, 0.75, 0.6), creamMat);
    chest.position.set(0, 0.82, 0.85);
    g.add(chest);

    // Collar
    const collar = new THREE.Mesh(new THREE.BoxGeometry(1.22, 0.18, 0.35), collarMat);
    collar.position.set(0, 1.18, 0.78);
    g.add(collar);

    // Head
    const head = new THREE.Mesh(new THREE.BoxGeometry(1.05, 0.92, 0.98), furMat);
    head.position.set(0, 1.58, 0.92);
    g.add(head);

    // Snout
    const snout = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.44, 0.65), creamMat);
    snout.position.set(0, 1.42, 1.52);
    g.add(snout);
    const nose = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.18, 0.18), eyeMat);
    nose.position.set(0, 1.54, 1.84);
    g.add(nose);

    // Eyes
    [-0.28, 0.28].forEach(ex => {
      const eye = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.14, 0.1), eyeMat);
      eye.position.set(ex, 1.68, 1.41);
      g.add(eye);
    });

    // Perky Ears
    [-0.36, 0.36].forEach(ex => {
      const ear = new THREE.Mesh(new THREE.ConeGeometry(0.24, 0.55, 4), darkFurMat);
      ear.position.set(ex, 2.22, 0.85);
      ear.rotation.y = Math.PI / 4;
      g.add(ear);
    });

    // 4 Legs
    const legs = [];
    [[-0.42, 0.72], [0.42, 0.72], [-0.42, -0.72], [0.42, -0.72]].forEach(([lx, lz]) => {
      const leg = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.75, 0.32), furMat);
      leg.position.set(lx, 0.38, lz);
      g.add(leg);
      legs.push(leg);
    });

    // Wagging Tail
    const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.16, 0.95, 6), darkFurMat);
    tail.position.set(0, 1.32, -1.15);
    tail.rotation.x = -0.55;
    g.add(tail);

    // Speech Bubble Sprite above the Dog
    const bubble = makeTextSprite(['🐕 HALFWORLD HOUND', 'Ask me to fetch any clip, prop, or world!'], {
      bg: 'rgba(18, 12, 6, 0.92)',
      border: '#ff8a3d',
      accent: '#ffb067',
      fg: '#fff3e0',
      scaleX: 7.5,
      scaleY: 2.1
    });
    bubble.position.set(0, 3.3, 0);
    g.add(bubble);

    g.userData = {
      id: 'wygwyl-dog',
      name: 'HALFWORLD HOUND (AI HELPER)',
      label: '🐕 HALFWORLD HOUND',
      type: 'cast-actor',
      isAssembly: true,
      tail,
      head,
      legs,
    };

    scene.add(g);
    STATE.dogGroup = g;
    STATE.dogBubbleSprite = bubble;
    placeDogAtMode();
    return g;
  }

  function updateDogBubble(title, subtitle) {
    if (!STATE.dogGroup) return;
    if (STATE.dogBubbleSprite) {
      try { STATE.dogGroup.remove(STATE.dogBubbleSprite); } catch (_) {}
    }
    const sp = makeTextSprite([title || '🐕 HALFWORLD HOUND', subtitle || 'Ready to fetch!'], {
      bg: 'rgba(18, 12, 6, 0.92)',
      border: '#ff8a3d',
      accent: '#ffb067',
      fg: '#fff3e0',
      scaleX: 8.0,
      scaleY: 2.2
    });
    sp.position.set(0, 3.3, 0);
    STATE.dogGroup.add(sp);
    STATE.dogBubbleSprite = sp;
  }

  function placeDogAtMode() {
    if (!STATE.dogGroup) return;
    if (STATE.dogMode === 'roof') {
      // Find a prominent building near the first stop or center so the Dog sits on its roof like the reference screenshot!
      let bestRoof = { x: 4, y: groundY(4, -6) + 8.5, z: -6 };
      try {
        const refPt = STATE.corridorPts[0] || { x: 0, z: 0 };
        let bestDist = 9999;
        scene.traverse(o => {
          if (o.isMesh && o.userData && o.userData.type === 'block' && o.userData._hartsoe && o.userData.dims) {
            const d = Math.hypot(o.position.x - refPt.x, o.position.z - refPt.z);
            if (d < 28 && d > 2 && o.userData.dims.h >= 3.5 && d < bestDist) {
              bestDist = d;
              bestRoof = {
                x: o.position.x,
                y: o.position.y + o.userData.dims.h / 2 + 0.05,
                z: o.position.z
              };
            }
          }
        });
      } catch (_) {}
      STATE.dogGroup.position.set(bestRoof.x, bestRoof.y, bestRoof.z);
      STATE.dogGroup.scale.setScalar(1.35);
    } else if (typeof P !== 'undefined' && P.pos) {
      const gx = P.pos.x + 3.8, gz = P.pos.z + 2.4;
      STATE.dogGroup.position.set(gx, groundY(gx, gz), gz);
      STATE.dogGroup.scale.setScalar(1.15);
    }
  }

  // ── 2. MOUNT 90 SIDESCROLLING SCENES, POEM TAPE, VIDEO PORTALS & FRUSTUMS ──
  function clearStageGroup() {
    STATE.videoElements.forEach(v => {
      try { v.pause(); v.src = ''; v.load(); } catch (_) {}
    });
    STATE.videoElements = [];
    if (STATE.stageGroup && typeof scene !== 'undefined') {
      try {
        scene.remove(STATE.stageGroup);
        STATE.stageGroup.traverse(o => {
          if (o.geometry) o.geometry.dispose();
          if (o.material) {
            const mats = Array.isArray(o.material) ? o.material : [o.material];
            mats.forEach(m => { if (m.map) m.map.dispose(); m.dispose(); });
          }
        });
      } catch (_) {}
    }
    STATE.stageGroup = null;
    STATE.corridorPts = [];
    STATE.frustumMarkers = [];
  }

  function mountPoemAssetsOnGround(poemNum) {
    if (!STATE.master || typeof THREE === 'undefined' || typeof scene === 'undefined') return;
    const pNum = String(poemNum || STATE.activePoemNum || '01').padStart(2, '0');
    STATE.activePoemNum = pNum;
    const pm = STATE.master.poems[pNum];
    if (!pm) return;

    clearStageGroup();
    const grp = new THREE.Group();
    grp.name = 'WYGWYL_POEM_' + pNum;
    STATE.stageGroup = grp;

    // Determine set piece coordinates from active landpack's wygwyl block or poem metadata
    let setPieces = [];
    let wtStops = [];
    let invWedges = [];
    try {
      const lp = window.__wygCurrentPack;
      if (lp && lp.wygwyl && Array.isArray(lp.wygwyl.poems)) {
        const matchP = lp.wygwyl.poems.find(p => String(p.num).padStart(2, '0') === pNum) || lp.wygwyl.poems[0];
        if (matchP && Array.isArray(matchP.set_pieces)) setPieces = matchP.set_pieces;
        if (matchP && Array.isArray(matchP.wt_stops)) wtStops = matchP.wt_stops;
        if (Array.isArray(lp.wygwyl.inverse_wedges)) {
          invWedges = lp.wygwyl.inverse_wedges.filter(w => w.poem === pNum);
        }
      }
    } catch (_) {}

    // Fallback corridor if setPieces has < 6 items
    if (setPieces.length < 6) {
      setPieces = pm.scenes.map((sc, idx) => {
        const ex = setPieces[idx] || {};
        return {
          k: chr(65 + idx),
          name: ex.name || sc.name,
          line: ex.line || sc.caption,
          x: Number.isFinite(ex.x) ? ex.x : (-35 + idx * 14),
          z: Number.isFinite(ex.z) ? ex.z : (-10 + Math.sin(idx * 0.7) * 8),
          plate: sc.plate,
          clip: (pm.clips[idx % Math.max(1, pm.clips.length)] || {}).src || pm.film_mp4,
          sign: ['PERCEPT', 'ACTION', 'AFFECT', 'OPSIGN', 'SONSIGN', 'CRYSTAL'][idx % 6]
        };
      });
    }

    function chr(c) { return String.fromCharCode(c); }

    const loader = new THREE.TextureLoader();

    // A. DRAPE THE CONTINUOUS `poem_tape.webp` SPECTROGRAM & SCENE RIBBON ON THE GROUND
    const pts3D = setPieces.map((sp, i) => {
      const x = Number.isFinite(sp.x) ? sp.x : (-30 + i * 12);
      const z = Number.isFinite(sp.z) ? sp.z : 0;
      return new THREE.Vector3(x, groundY(x, z) + 0.22, z);
    });
    STATE.corridorPts = pts3D.map(v => ({ x: v.x, y: v.y, z: v.z }));

    if (pts3D.length >= 2 && pm.tape) {
      const curve = new THREE.CatmullRomCurve3(pts3D);
      const segs = 120;
      const halfW = 3.2;
      const posArr = [];
      const uvArr = [];
      const idxArr = [];
      for (let i = 0; i <= segs; i++) {
        const u = i / segs;
        const pt = curve.getPointAt(u);
        const tan = curve.getTangentAt(u).normalize();
        const nx = -tan.z, nz = tan.x;
        for (const side of [-1, 1]) {
          const rx = pt.x + nx * halfW * side;
          const rz = pt.z + nz * halfW * side;
          const ry = groundY(rx, rz) + 0.18;
          posArr.push(rx, ry, rz);
          uvArr.push(u, side < 0 ? 0 : 1);
        }
        if (i < segs) {
          const base = i * 2;
          idxArr.push(base, base + 2, base + 1, base + 1, base + 2, base + 3);
        }
      }
      const ribGeo = new THREE.BufferGeometry();
      ribGeo.setAttribute('position', new THREE.Float32BufferAttribute(posArr, 3));
      ribGeo.setAttribute('uv', new THREE.Float32BufferAttribute(uvArr, 2));
      ribGeo.setIndex(idxArr);
      ribGeo.computeVertexNormals();

      const tapeTex = loader.load(pm.tape);
      tapeTex.colorSpace = THREE.SRGBColorSpace;
      const ribMat = new THREE.MeshBasicMaterial({
        map: tapeTex,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.92,
      });
      const ribMesh = new THREE.Mesh(ribGeo, ribMat);
      ribMesh.name = 'POEM_TAPE_GROUND_RIBBON';
      grp.add(ribMesh);

      // Gold edge rails along the poem tape highway
      const tubeGeo = new THREE.TubeGeometry(curve, 96, 0.14, 6, false);
      const tubeMesh = new THREE.Mesh(tubeGeo, new THREE.MeshBasicMaterial({ color: 0xffd23f }));
      grp.add(tubeMesh);
    }

    // B. ERECT THE 6 MULTIPLANE SIDESCROLLING SCENE STAGES (`s0_ext.webp`..`s5_ext.webp`) + VIDEO PORTALS + PROPS
    const cineShots = [];
    setPieces.slice(0, 6).forEach((sp, idx) => {
      const sc = pm.scenes[idx] || pm.scenes[0] || {};
      const plateUrl = sp.plate || sc.plate || `play/levels/${pNum}/s${idx}_ext.webp`;
      const clipObj = pm.clips[idx % Math.max(1, pm.clips.length)] || {};
      const clipUrl = sp.clip || clipObj.src || pm.film_mp4;
      const signName = sp.sign || clipObj.sign || ['PERCEPT', 'ACTION', 'AFFECT', 'OPSIGN', 'SONSIGN', 'CRYSTAL'][idx % 6];

      const x = Number.isFinite(sp.x) ? sp.x : (-30 + idx * 12);
      const z = Number.isFinite(sp.z) ? sp.z : 0;
      const gy = groundY(x, z);

      // Compute stage orientation along the corridor tangent so horizontal sidescroller faces all stages cleanly!
      const nextSp = setPieces[Math.min(setPieces.length - 1, idx + 1)];
      const prevSp = setPieces[Math.max(0, idx - 1)];
      const dx = (nextSp.x || 0) - (prevSp.x || 0);
      const dz = (nextSp.z || 0) - (prevSp.z || 0);
      const corridorYaw = (Math.abs(dx) + Math.abs(dz) > 0.01) ? Math.atan2(dx, dz) : (Math.PI / 2);
      // Normal facing the camera (perpendicular to corridor)
      const stageYaw = corridorYaw - Math.PI / 2;

      const stg = new THREE.Group();
      stg.position.set(x, gy, z);
      stg.rotation.y = stageYaw;
      stg.userData = {
        stopIdx: idx,
        stopKey: sp.k || chr(65 + idx),
        name: sp.name || sc.name,
        plate: plateUrl,
        clip: clipUrl,
        stageYaw,
      };

      // 1. Backplane Multiplane Wide Plate (`s<idx>_ext.webp`, 16.5m x 6.8m)
      const plateW = 16.5, plateH = 6.8;
      const plateTex = loader.load(plateUrl);
      plateTex.colorSpace = THREE.SRGBColorSpace;
      const plateGeo = new THREE.PlaneGeometry(plateW, plateH);
      const plateMat = new THREE.MeshBasicMaterial({ map: plateTex, side: THREE.DoubleSide });
      const plateMesh = new THREE.Mesh(plateGeo, plateMat);
      plateMesh.position.set(0, plateH / 2 + 0.35, -1.8);
      stg.add(plateMesh);

      // Gold proscenium frame around the scene plate
      const frameEdges = new THREE.LineSegments(
        new THREE.EdgesGeometry(plateGeo),
        new THREE.LineBasicMaterial({ color: 0xffd23f })
      );
      frameEdges.position.copy(plateMesh.position);
      stg.add(frameEdges);

      // 2. Live 3D Film Video Portal (`cel_assets/patches/PXX-00Y.mp4`) in the upper-right / window portal plane
      if (clipUrl) {
        const vid = document.createElement('video');
        vid.src = clipUrl;
        vid.crossOrigin = 'anonymous';
        vid.loop = true;
        vid.muted = true;
        vid.playsInline = true;
        vid.autoplay = true;
        vid.play().catch(() => {});
        STATE.videoElements.push(vid);

        const vidTex = new THREE.VideoTexture(vid);
        vidTex.colorSpace = THREE.SRGBColorSpace;
        const vidW = 6.2, vidH = 3.5;
        const vidGeo = new THREE.PlaneGeometry(vidW, vidH);
        const vidMat = new THREE.MeshBasicMaterial({ map: vidTex, side: THREE.DoubleSide });
        const vidMesh = new THREE.Mesh(vidGeo, vidMat);
        vidMesh.position.set(4.4, 4.3, -0.55);
        stg.add(vidMesh);

        const vidFrame = new THREE.LineSegments(
          new THREE.EdgesGeometry(vidGeo),
          new THREE.LineBasicMaterial({ color: 0x19e6c8 })
        );
        vidFrame.position.copy(vidMesh.position);
        stg.add(vidFrame);
      }

      // 3. Multiplane Cut-Out Prop Standees (`play/levels/XX/props/*.png`) in the midplane (z = +0.2 .. +1.4)
      if (Array.isArray(pm.props) && pm.props.length > 0) {
        for (let pOffset = 0; pOffset < 2; pOffset++) {
          const propPath = pm.props[(idx * 2 + pOffset) % pm.props.length];
          if (!propPath) continue;
          const propTex = loader.load(propPath);
          propTex.colorSpace = THREE.SRGBColorSpace;
          const pGeo = new THREE.PlaneGeometry(2.8, 3.2);
          const pMat = new THREE.MeshBasicMaterial({
            map: propTex,
            transparent: true,
            alphaTest: 0.08,
            side: THREE.DoubleSide
          });
          const pMesh = new THREE.Mesh(pGeo, pMat);
          pMesh.position.set(pOffset === 0 ? -4.2 : 1.6, 1.85, 0.65 + pOffset * 0.55);
          stg.add(pMesh);
        }
      }

      // 4. Articulated Character Standee on the Stage Floor (z = +1.35)
      const heroParts = [
        'kits/packs/poet_tracksuit_v1/01_COMPONENTS/01_torso_front.png',
        'arena/bodies/ACT-001_p0.png',
        'arena/bodies/ACT-011_p0.png',
        'arena/bodies/ACT-014_p0.png',
        'arena/bodies/ACT-019_p0.png',
        'arena/bodies/ACT-028_p0.png'
      ];
      const charTex = loader.load(heroParts[idx % heroParts.length]);
      charTex.colorSpace = THREE.SRGBColorSpace;
      const charGeo = new THREE.PlaneGeometry(2.4, 3.6);
      const charMat = new THREE.MeshBasicMaterial({
        map: charTex,
        transparent: true,
        alphaTest: 0.08,
        side: THREE.DoubleSide
      });
      const charMesh = new THREE.Mesh(charGeo, charMat);
      charMesh.position.set(-1.2, 2.0, 1.35);
      stg.add(charMesh);

      // 5. Overhead Banner Sprite (`STOP A · S1 PERCEPT · Scene Name + Stanza Line`)
      const banner = makeTextSprite([
        `STOP ${sp.k || chr(65 + idx)} · S${idx + 1} ${signName} · ${(sp.name || sc.name || '').toUpperCase()}`,
        `“${(sp.line || sc.caption || pm.title || '').slice(0, 56)}”`
      ], {
        bg: 'rgba(9, 14, 20, 0.92)',
        border: '#ffd23f',
        accent: '#ffd23f',
        fg: '#f3ead2',
        scaleX: 11.5,
        scaleY: 2.8
      });
      banner.position.set(0, plateH + 2.1, -0.5);
      stg.add(banner);

      // 6. Deleuze Purple Camera Frustum Wedge in front of the stage (z = +11)
      const frustumGroup = new THREE.Group();
      frustumGroup.position.set(0, 2.8, 11.5);
      const coneGeo = new THREE.ConeGeometry(2.2, 4.2, 4, 1, true);
      coneGeo.rotateX(Math.PI / 2);
      coneGeo.rotateZ(Math.PI / 4);
      const coneEdges = new THREE.LineSegments(
        new THREE.EdgesGeometry(coneGeo),
        new THREE.LineBasicMaterial({ color: 0xa855f7 })
      );
      frustumGroup.add(coneEdges);
      const fTag = makeTextSprite([`S${idx + 1} ${signName}`, `${sp.k || chr(65 + idx)}: ${(sp.name || '').slice(0, 22)}`], {
        bg: 'rgba(28, 12, 46, 0.9)',
        border: '#a855f7',
        accent: '#d8b4fe',
        fg: '#f3ead2',
        scaleX: 5.4,
        scaleY: 1.4
      });
      fTag.position.set(0, 2.1, 0);
      frustumGroup.add(fTag);
      stg.add(frustumGroup);

      grp.add(stg);

      // Compute world-space camera position & target for this stage portal
      const camWorldPos = new THREE.Vector3(0, 3.6, 13.5).applyAxisAngle(new THREE.Vector3(0, 1, 0), stageYaw).add(new THREE.Vector3(x, gy, z));
      const camWorldTarget = new THREE.Vector3(0, 3.4, -0.5).applyAxisAngle(new THREE.Vector3(0, 1, 0), stageYaw).add(new THREE.Vector3(x, gy, z));
      STATE.frustumMarkers.push({
        label: `S${idx + 1} ${signName} · ${sp.k || chr(65 + idx)} ${sp.name || sc.name}`,
        line: sp.line || sc.caption || '',
        p: [Number(camWorldPos.x.toFixed(2)), Number(camWorldPos.y.toFixed(2)), Number(camWorldPos.z.toFixed(2))],
        t: [Number(camWorldTarget.x.toFixed(2)), Number(camWorldTarget.y.toFixed(2)), Number(camWorldTarget.z.toFixed(2))],
        stopX: x,
        stopZ: z,
        stageYaw
      });
      cineShots.push({
        p: [Number(camWorldPos.x.toFixed(2)), Number(camWorldPos.y.toFixed(2)), Number(camWorldPos.z.toFixed(2))],
        t: [Number(camWorldTarget.x.toFixed(2)), Number(camWorldTarget.y.toFixed(2)), Number(camWorldTarget.z.toFixed(2))],
        mode: 'FREE',
        hold: 4.0,
        travel: 3.0
      });
    });

    // C. PLANT WORLDTEXT STOPS (`wt/01..14.json`) ON THE GROUND
    if (Array.isArray(wtStops) && wtStops.length > 0 && window.ATLAS && typeof window.ATLAS.testify === 'function') {
      wtStops.forEach((wst, wi) => {
        if (Math.abs(wst.x) <= 78 && Math.abs(wst.z) <= 78) {
          try { window.ATLAS.testify(wst.text, { x: wst.x, z: wst.z }); } catch (_) {}
        }
      });
    }

    // D. PLANT PINK INVERSE-TOPOLOGY CAMERA WEDGES & BEFORE/AFTER CARDS (WHEN AVAILABLE)
    const invList = invWedges.length ? invWedges : (pm.foundry_inverse || []);
    invList.slice(0, 6).forEach((iw, idx) => {
      const ix = Number.isFinite(iw.x) ? iw.x : ((iw.cam ? (iw.cam.x / 8000 - 0.5) * 160 : -20 + idx * 8));
      const iz = Number.isFinite(iw.z) ? iw.z : ((iw.cam ? (iw.cam.y / 6000 - 0.5) * 120 : 18));
      const iy = groundY(ix, iz) + 2.4;
      const ig = new THREE.Group();
      ig.position.set(ix, iy, iz);
      const hdRad = ((iw.hd || (iw.cam && iw.cam.hd) || 0) * Math.PI) / 180;
      ig.rotation.y = -hdRad;

      // Pink inverse camera wedge
      const wGeo = new THREE.ConeGeometry(1.6, 3.4, 4, 1, true);
      wGeo.rotateX(Math.PI / 2);
      wGeo.rotateZ(Math.PI / 4);
      const wLine = new THREE.LineSegments(
        new THREE.EdgesGeometry(wGeo),
        new THREE.LineBasicMaterial({ color: 0xff3d6e })
      );
      ig.add(wLine);

      // Sculpted render billboard
      if (iw.b) {
        const bTex = loader.load(iw.b);
        bTex.colorSpace = THREE.SRGBColorSpace;
        const bMesh = new THREE.Mesh(
          new THREE.PlaneGeometry(5.2, 2.2),
          new THREE.MeshBasicMaterial({ map: bTex, side: THREE.DoubleSide })
        );
        bMesh.position.set(0, 2.4, -2.2);
        ig.add(bMesh);
      }

      const grownTxt = (iw.grown && iw.grown[0]) ? iw.grown[0] : `Match ${Math.round((iw.before||0.4)*100)}% → ${Math.round((iw.after||0.5)*100)}%`;
      const iSp = makeTextSprite([`⛰️ INVERSE SCULPT · ${iw.ref || ''}`, grownTxt], {
        bg: 'rgba(38, 8, 20, 0.92)',
        border: '#ff3d6e',
        accent: '#ff8da8',
        fg: '#f3ead2',
        scaleX: 6.8,
        scaleY: 1.7
      });
      iSp.position.set(0, 4.1, -2.2);
      ig.add(iSp);
      grp.add(ig);
    });

    scene.add(grp);

    // E. SYNC CINE SHOT RIVER & LEFT FILM STUDIO DRAWER WITH REAL POEM BEATS
    try {
      if (window.CINE && typeof window.CINE.restore === 'function' && cineShots.length) {
        window.CINE.restore({ v: 1, shots: cineShots });
      }
      populateFilmStudioWithPoem(pm, setPieces);
    } catch (e) {
      console.warn('[wygwyl] CINE sync error', e);
    }

    // F. UPDATE HORIZONTAL SIDESCROLLER BAR
    renderScrollerStops(pm, setPieces);

    // G. ENSURE THE DOG IS IN THE SCENE & ANNOUNCE THE MOUNTED POEM
    ensureDog();
    placeDogAtMode();
    updateDogBubble(`🐕 POEM ${pNum}: ${pm.title.toUpperCase()}`, `${setPieces.length} Multiplane Stages + ${pm.clips.length} Clips Live!`);
  }

  // Replace the generic "keeper of the storm gate" in FILM STUDIO with the real WYGWYL poem blueprint!
  function populateFilmStudioWithPoem(pm, setPieces) {
    const inp = document.getElementById('film-seed-input');
    if (inp) {
      inp.value = `Poem ${pm.num} · ${pm.title} (${pm.place})`;
    }
    if (!window.LEDGER || typeof window.__ledgerCompose !== 'function') return;
    const fns = ['perception', 'action', 'affection', 'opsign', 'sonsign', 'crystal', 'recollection'];
    const layers = ['past', 'present', 'future'];
    const beats = [];
    setPieces.slice(0, 6).forEach((sp, i) => {
      beats.push({
        title: `Stop ${sp.k || String.fromCharCode(65 + i)} · ${sp.name}`,
        dur: 6,
        fn: fns[i % fns.length],
        layer: layers[i % layers.length],
        subject: 'poet',
        image: sp.plate || `play/levels/${pm.num}/s${i}_ext.webp`,
        action: sp.line || sp.name,
        sound: `Poem ${pm.num} reading + score`,
        transition: 'cut'
      });
    });
    const bp = {
      format: 'cineosis-film/v1',
      title: `POEM ${pm.num} · ${pm.title.toUpperCase()}`,
      seed: `${pm.title} — ${pm.place}`,
      engine: `Continuous poem tape + 6 multiplane sidescrolling sets across ${pm.place}`,
      abc: {
        a: `Poet in ${pm.place}`,
        b: `${setPieces.length} staged multiplane sets & film portals`,
        c: `WorldText stops & Foundry topography`
      },
      motifs: setPieces.slice(0, 3).map(sp => ({
        name: sp.name,
        past: sp.name + ' (memory)',
        present: sp.name + ' (staged set)',
        future: sp.name + ' (afterimage)'
      })),
      cast: [
        { name: 'POET', desc: 'Poet in red/black tracksuit rig' },
        { name: 'HOUND', desc: 'Halfworld AI Dog Companion' }
      ],
      beats
    };
    try {
      window.__ledgerCompose(bp);
      // Align LEDGER shot-stage ghosts directly onto our actual setPieces coordinates!
      setPieces.slice(0, 6).forEach((sp, i) => {
        const r = window.LEDGER.get('shot-' + i);
        if (r && Number.isFinite(sp.x) && Number.isFinite(sp.z)) {
          r.placement = { x: sp.x, z: sp.z, ry: 0 };
        }
      });
      if (typeof updateSceneGraph === 'function') updateSceneGraph();
    } catch (_) {}
  }

  // ── 3. CAMERA MODES: 3D OVERVIEW ↔ HORIZONTAL SIDESCROLLER ↔ FRUSTUM POV ──
  function setViewMode(mode) {
    STATE.viewMode = mode;
    document.getElementById('wyg-cam-overview')?.classList.toggle('active', mode === 'overview');
    document.getElementById('wyg-cam-scroller')?.classList.toggle('teal-active', mode === 'scroller');
    document.getElementById('wyg-cam-frustum')?.classList.toggle('active', mode === 'frustum');
    document.getElementById('wyg-cam-drive')?.classList.toggle('active', mode === 'drive');

    const scrollerBar = document.getElementById('wyg-scroller-bar');
    if (scrollerBar) scrollerBar.classList.toggle('show', mode === 'scroller');

    if (typeof camMode !== 'undefined') {
      if (mode === 'drive') {
        camMode = 'CAR';
        if (typeof orbit !== 'undefined') orbit.enabled = true;
      } else {
        camMode = 'FREE';
      }
    }

    if (mode === 'overview') {
      // Bird's-eye overview of the active poem's corridor
      const pts = STATE.corridorPts;
      let cx = 0, cz = 0;
      if (pts.length) {
        pts.forEach(p => { cx += p.x; cz += p.z; });
        cx /= pts.length; cz /= pts.length;
      }
      const gy = groundY(cx, cz);
      if (typeof camera !== 'undefined' && typeof orbit !== 'undefined') {
        camera.fov = 50;
        camera.updateProjectionMatrix();
        camera.position.set(cx + 22, gy + 58, cz + 56);
        orbit.target.set(cx, gy + 2, cz);
        orbit.update();
      }
      if (typeof notify === 'function') notify('🗺️ 3D OVERVIEW — ALL MULTIPLANE STAGES & WORLDTEXT STOPS');
    } else if (mode === 'scroller') {
      if (typeof camera !== 'undefined') {
        // Telephoto flatter perspective for horizontal sidescrolling!
        camera.fov = 34;
        camera.updateProjectionMatrix();
      }
      applyHorizontalScrollerCamera(STATE.scrollerT);
      if (typeof notify === 'function') notify('↔️ HORIZONTAL SIDESCROLLER — USE SLIDER OR ←/→ KEYS TO SCROLL CORRIDOR');
    } else if (mode === 'frustum') {
      if (!STATE.frustumMarkers.length) return;
      const m = STATE.frustumMarkers[STATE.frustumIdx % STATE.frustumMarkers.length];
      STATE.frustumIdx = (STATE.frustumIdx + 1) % STATE.frustumMarkers.length;
      if (typeof camera !== 'undefined' && typeof orbit !== 'undefined') {
        camera.fov = 45;
        camera.updateProjectionMatrix();
        camera.position.fromArray(m.p);
        orbit.target.fromArray(m.t);
        orbit.update();
      }
      if (typeof notify === 'function') notify('🎥 ' + m.label);
    }
  }

  function applyHorizontalScrollerCamera(tNorm) {
    const pts = STATE.corridorPts;
    if (!pts || pts.length === 0 || typeof camera === 'undefined' || typeof orbit === 'undefined') return;
    const t = Math.max(0, Math.min(1, Number(tNorm) || 0));
    STATE.scrollerT = t;
    const scrub = document.getElementById('wyg-scroller-scrub');
    if (scrub && Math.abs(Number(scrub.value) - t) > 0.005) scrub.value = String(t);

    let pos, tan;
    if (pts.length === 1) {
      pos = new THREE.Vector3(pts[0].x, pts[0].y, pts[0].z);
      tan = new THREE.Vector3(1, 0, 0);
    } else {
      const curve = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(p.x, p.y, p.z)));
      pos = curve.getPointAt(t);
      tan = curve.getTangentAt(t).normalize();
    }

    // Camera stands perpendicular to the corridor tangent at distance `scrollerDist` and height `scrollerElev`
    const nx = -tan.z, nz = tan.x;
    const dist = STATE.scrollerDist || 18;
    const elev = STATE.scrollerElev || 4.2;
    const gy = groundY(pos.x, pos.z);

    camera.position.set(pos.x + nx * dist, gy + elev, pos.z + nz * dist);
    orbit.target.set(pos.x, gy + 3.2, pos.z);
    orbit.update();

    // Highlight active stop button
    const activeIdx = Math.min(pts.length - 1, Math.round(t * (pts.length - 1)));
    document.querySelectorAll('#wyg-scroller-stops button').forEach((b, bi) => {
      b.classList.toggle('on', bi === activeIdx);
    });
  }

  function renderScrollerStops(pm, setPieces) {
    const wrap = document.getElementById('wyg-scroller-stops');
    const lbl = document.getElementById('wyg-scroller-label');
    if (lbl) lbl.textContent = `Poem ${pm.num} · ${pm.title} (${setPieces.length} Multiplane Stops)`;
    if (!wrap) return;
    const sps = setPieces.slice(0, 6);
    wrap.innerHTML = sps.map((sp, i) =>
      `<button type="button" data-idx="${i}" class="${i === 0 ? 'on' : ''}">${sp.k || String.fromCharCode(65 + i)} · ${(sp.name || '').slice(0, 18)}</button>`
    ).join('');
    wrap.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        const i = Number(btn.dataset.idx) || 0;
        const t = sps.length > 1 ? i / (sps.length - 1) : 0;
        setViewMode('scroller');
        applyHorizontalScrollerCamera(t);
      });
    });
  }

  // ── 4. PLAY / PAUSE POEM FILM & SPOKEN READING IN THE 3D WORLD ─────────────
  function togglePoemFilmPlayback() {
    const btn = document.getElementById('wyg-btn-playfilm');
    const pm = STATE.master && STATE.master.poems[STATE.activePoemNum];
    if (!pm) return;

    if (STATE.isPlayingFilm) {
      STATE.isPlayingFilm = false;
      try { STATE.readingAudio.pause(); } catch (_) {}
      STATE.videoElements.forEach(v => { try { v.muted = true; } catch (_) {} });
      if (btn) { btn.textContent = '▶ PLAY POEM FILM'; btn.classList.remove('active'); }
      return;
    }

    STATE.isPlayingFilm = true;
    if (btn) { btn.textContent = '⏸ PLAYING POEM ' + pm.num; btn.classList.add('active'); }
    if (pm.reading_audio) {
      if (!STATE.readingAudio.src.endsWith(pm.reading_audio)) {
        STATE.readingAudio.src = pm.reading_audio;
      }
      STATE.readingAudio.play().catch(err => console.warn('[audio]', err));
    }
    STATE.videoElements.forEach((v, idx) => {
      try {
        v.muted = (idx !== 0); // unmute primary portal if reading_audio isn't carrying voice
        v.play().catch(() => {});
      } catch (_) {}
    });
    updateDogBubble(`🐕 ROLLING POEM ${pm.num}`, `Playing "${pm.title}" reading & 6 stage screens!`);
  }

  // ── 5. FOUNDRY TOPOGRAPHY & TEXTURE LAYER SWITCHER ─────────────────────────
  async function loadStageOrFoundry({ stageKey, poemNum, foundryId, cartUrl }) {
    if (!STATE.master) return;

    let packUrl = cartUrl || '';
    if (foundryId) {
      STATE.activeFoundryId = foundryId;
      const fw = STATE.master.foundry_worlds.find(w => w.id === foundryId);
      if (fw) packUrl = fw.landpack_url;
    } else if (stageKey) {
      STATE.activeFoundryId = '';
      STATE.activeStageKey = stageKey;
      const st = STATE.master.real_stages.find(s => s.key === stageKey);
      if (st) {
        packUrl = st.landpack_url;
        if (!poemNum && st.poems && st.poems.length) poemNum = st.poems[0];
      }
    }

    if (poemNum) {
      STATE.activePoemNum = String(poemNum).padStart(2, '0');
      // If no explicit stageKey or foundryId was given, pick the stage that hosts this poem
      if (!foundryId && !stageKey && !cartUrl) {
        const hostStage = STATE.master.real_stages.find(s => (s.poems || []).includes(STATE.activePoemNum));
        if (hostStage) {
          STATE.activeStageKey = hostStage.key;
          packUrl = hostStage.landpack_url;
        }
      }
    }

    syncSelectorsUI();

    if (packUrl) {
      try {
        const res = await fetch(packUrl);
        if (res.ok) {
          const pack = await res.json();
          window.__wygCurrentPack = pack;
          if (typeof window.autoEnterPlay === 'function') {
            try { window.autoEnterPlay(); } catch (_) {}
          }
          if (typeof window.loadLandPack === 'function') {
            window.loadLandPack(pack);
          }
        }
      } catch (e) {
        console.warn('[wygwyl] pack fetch failed:', packUrl, e);
      }
    }

    setTimeout(() => {
      mountPoemAssetsOnGround(STATE.activePoemNum);
      applyGroundTextureMode(STATE.texMode);
      if (STATE.viewMode === 'scroller') applyHorizontalScrollerCamera(STATE.scrollerT);
      else if (STATE.viewMode === 'overview') setViewMode('overview');
    }, 350);
  }

  function applyGroundTextureMode(mode) {
    STATE.texMode = mode || 'map';
    const pack = window.__wygCurrentPack;
    if (!pack || typeof THREE === 'undefined' || typeof scene === 'undefined') return;
    let url = null;
    if (mode === 'palimpsest' && pack.tex_palimpsest) url = pack.tex_palimpsest;
    else if (mode === 'sculpted_after' && pack.tex_sculpted_after) url = pack.tex_sculpted_after;
    else if (mode === 'sculpted_before' && pack.tex_sculpted_before) url = pack.tex_sculpted_before;
    else if (mode === 'map') url = pack.tex_map || pack.tex;
    if (!url) return;

    const tex = new THREE.TextureLoader().load(url);
    tex.colorSpace = THREE.SRGBColorSpace;
    scene.traverse(o => {
      if (o.isMesh && o.userData && o.userData.type === 'terrain' && /GROUND/.test(o.userData.name || '')) {
        o.material.map = tex;
        o.material.needsUpdate = true;
      }
    });
  }

  // ── 6. 🐕 THE DOG — CONVERSATIONAL AI ASSET, CLIP, PROP & WORLD FETCHER ────
  function dogLogMessage(role, html, cards = []) {
    const log = document.getElementById('wyg-dog-log');
    if (!log) return;
    const div = document.createElement('div');
    div.className = 'dog-msg ' + (role === 'user' ? 'user' : 'hound');
    div.innerHTML = html;

    if (cards && cards.length > 0) {
      const grid = document.createElement('div');
      grid.className = 'dog-cards';
      cards.slice(0, 6).forEach((c, idx) => {
        const card = document.createElement('div');
        card.className = 'dog-card';
        const mediaHtml = c.video
          ? `<video src="${c.video}" muted loop autoplay playsinline></video>`
          : `<img src="${c.img || 'play/levels/01/s0_ext.webp'}" alt="">`;
        card.innerHTML = `${mediaHtml}<div class="dc-meta"><b>${c.title || 'Asset'}</b><span>${c.sub || 'Click to spawn in 3D'}</span></div>`;
        card.addEventListener('click', () => {
          spawnFetchedItemInWorld(c, idx);
        });
        grid.appendChild(card);
      });
      div.appendChild(grid);
    }

    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }

  function spawnFetchedItemInWorld(item, offsetIdx = 0) {
    if (typeof THREE === 'undefined' || typeof scene === 'undefined') return;
    if (!STATE.spawnedCardsGroup) {
      STATE.spawnedCardsGroup = new THREE.Group();
      STATE.spawnedCardsGroup.name = 'WYGWYL_DOG_FETCHED_ASSETS';
      scene.add(STATE.spawnedCardsGroup);
    }

    // Place near current camera target or player rig
    let basePos = new THREE.Vector3(0, 0, 0);
    if (typeof orbit !== 'undefined' && orbit.target) {
      basePos.copy(orbit.target);
    } else if (typeof P !== 'undefined' && P.pos) {
      basePos.copy(P.pos);
    }
    const angle = (offsetIdx * 0.55) - 0.5;
    const x = basePos.x + Math.sin(angle) * 7.5;
    const z = basePos.z + Math.cos(angle) * 7.5;
    const gy = groundY(x, z);

    const g = new THREE.Group();
    g.position.set(x, gy, z);
    if (typeof camera !== 'undefined') {
      g.lookAt(camera.position.x, gy + 2.5, camera.position.z);
    }

    if (item.video) {
      const vid = document.createElement('video');
      vid.src = item.video;
      vid.crossOrigin = 'anonymous';
      vid.loop = true;
      vid.muted = false;
      vid.playsInline = true;
      vid.autoplay = true;
      vid.play().catch(() => { vid.muted = true; vid.play().catch(() => {}); });
      STATE.videoElements.push(vid);

      const vTex = new THREE.VideoTexture(vid);
      vTex.colorSpace = THREE.SRGBColorSpace;
      const mesh = new THREE.Mesh(
        new THREE.PlaneGeometry(6.4, 3.6),
        new THREE.MeshBasicMaterial({ map: vTex, side: THREE.DoubleSide })
      );
      mesh.position.y = 2.4;
      g.add(mesh);
      const border = new THREE.LineSegments(
        new THREE.EdgesGeometry(mesh.geometry),
        new THREE.LineBasicMaterial({ color: 0xff8a3d })
      );
      border.position.copy(mesh.position);
      g.add(border);
    } else if (item.img) {
      const tex = new THREE.TextureLoader().load(item.img);
      tex.colorSpace = THREE.SRGBColorSpace;
      const isProp = item.kind === 'prop' || item.kind === 'anatomy' || item.kind === 'rig';
      const w = isProp ? 3.2 : 7.2;
      const h = isProp ? 3.6 : 3.4;
      const mesh = new THREE.Mesh(
        new THREE.PlaneGeometry(w, h),
        new THREE.MeshBasicMaterial({
          map: tex,
          transparent: isProp,
          alphaTest: isProp ? 0.06 : 0,
          side: THREE.DoubleSide
        })
      );
      mesh.position.y = h / 2 + 0.3;
      g.add(mesh);
    }

    const lbl = makeTextSprite([`🐕 FETCHED · ${(item.title || 'ASSET').toUpperCase()}`, item.sub || ''], {
      bg: 'rgba(20, 12, 6, 0.92)',
      border: '#ff8a3d',
      accent: '#ffd23f',
      fg: '#f3ead2',
      scaleX: 6.5,
      scaleY: 1.6
    });
    lbl.position.set(0, 4.7, 0);
    g.add(lbl);

    STATE.spawnedCardsGroup.add(g);

    // Move the Dog over to the spawned asset and wag tail!
    ensureDog();
    STATE.dogMode = 'companion';
    STATE.dogGroup.position.set(x + 2.4, gy, z + 1.2);
    updateDogBubble(`🐕 WOOF! FETCHED: ${(item.title || '').slice(0, 22)}`, item.sub || 'Mounted right here in 3D!');
    if (typeof notify === 'function') notify('🐕 DOG FETCHED: ' + (item.title || 'ASSET'));
  }

  async function handleDogQuery(rawText) {
    const q = String(rawText || '').trim();
    if (!q || !STATE.master) return;
    dogLogMessage('user', q);

    const ql = q.toLowerCase();

    // 1. Direct Camera / Mode commands
    if (/horizontal|sidescroll|side-scroll|side scroll|flat/.test(ql)) {
      setViewMode('scroller');
      dogLogMessage('hound', `🐾 <b>Woof! Switched to Horizontal 2.5D/3D Sidescroller Mode!</b> Use the cyan slider or <code>←</code> / <code>→</code> keys to glide along Poem ${STATE.activePoemNum}'s multiplane stage corridor.`);
      return;
    }
    if (/overview|bird|top|map view/.test(ql)) {
      setViewMode('overview');
      dogLogMessage('hound', `🐾 <b>Switched to 3D Bird's-Eye Overview!</b> You can see the whole ground, all 6 multiplane stage portals, and the camera frustums.`);
      return;
    }

    // 2. Direct Foundry World request (e.g. w1623, w1578, w0746, w1165, w0889, w0980, harbor, estuary)
    const fMatch = ql.match(/\b(w1623|w1578|w0746|w1165|w0889|w0980)\b/) || (/\b(foundry|harbor|estuary|island)\b/.test(ql) ? ['w1623', 'w1623'] : null);
    if (fMatch && /\b(load|mount|foundry|world|topography|island|harbor|estuary)\b/.test(ql)) {
      const wid = fMatch[1] || 'w1623';
      await loadStageOrFoundry({ foundryId: wid, poemNum: STATE.activePoemNum });
      const fw = STATE.master.foundry_worlds.find(w => w.id === wid);
      dogLogMessage('hound', `🐾 <b>Mounted Evolved Foundry World <code>${wid}</code> (${fw ? fw.layout : 'harbor'}) in 3D!</b><br>Heightfield, 280 3D buildings, 28 pink inverse-topology camera wedges, and all 6 multiplane scenes for Poem ${STATE.activePoemNum} are now standing on the island.`,
        fw ? [{ img: fw.map_img, title: `Foundry ${wid} Map`, sub: fw.layout }, { img: fw.inv_after_img, title: `${wid} Inverse Sculpted`, sub: `${fw.inverse_count} sculpted cameras` }] : []
      );
      return;
    }

    // 3. Poem / Stage navigation request ("poem 13", "fells point", "mount vernon", etc.)
    const pMatch = ql.match(/poem\s*(\d{1,2})/);
    const stageMatch = STATE.master.real_stages.find(s => ql.includes(s.key.replace('-', ' ')) || ql.includes(s.name.toLowerCase().split(',')[0]));
    if ((pMatch || stageMatch) && /\b(go|load|open|switch|play|take me|mount)\b/.test(ql)) {
      const targetPoem = pMatch ? String(Math.max(1, Math.min(14, parseInt(pMatch[1], 10)))).padStart(2, '0') : (stageMatch.poems[0] || '01');
      const targetStage = stageMatch ? stageMatch.key : null;
      await loadStageOrFoundry({ stageKey: targetStage, poemNum: targetPoem });
      const pm = STATE.master.poems[targetPoem];
      dogLogMessage('hound', `🐾 <b>Loaded Poem ${targetPoem}: ${pm.title} (${pm.place})!</b> All 6 sidescrolling scenes, film video screens, and WorldText stops are mounted.`);
      return;
    }

    // 4. Inverse topology / sculpted shots request
    if (/inverse|sculpt|before.*after|topolog/.test(ql)) {
      const pm = STATE.master.poems[STATE.activePoemNum];
      const invs = (pm && pm.foundry_inverse && pm.foundry_inverse.length) ? pm.foundry_inverse : STATE.master.poems['01'].foundry_inverse;
      const cards = invs.slice(0, 6).map(iv => ({
        img: iv.b,
        title: `Inverse ${iv.ref} (${iv.world})`,
        sub: (iv.grown && iv.grown[0]) || `Match ${Math.round(iv.after * 100)}%`,
        kind: 'scene'
      }));
      cards.slice(0, 2).forEach((c, i) => spawnFetchedItemInWorld(c, i));
      dogLogMessage('hound', `🐾 <b>Fetched ${cards.length} Inverse-Topology Sculpted Shots!</b> Pink wedges show where the reference photographs carved water and raised towers into the 3D terrain. Click any card to place it at your mark:`, cards);
      return;
    }

    // 5. Body Lab / Shoes / Hands / Heads / Characters request
    if (/\b(shoe|shoes|boot|boots|hand|hands|head|heads|eye|eyes|sunglass|tracksuit|poet|couple|ex|woman|child|rig|actor|character)\b/.test(ql)) {
      const cards = [];
      // Check character rigs
      (STATE.master.character_rigs || []).forEach(r => {
        if (ql.includes(r.id.split('_')[0]) || /character|rig|actor|cast|poet|couple|all/.test(ql)) {
          if (r.preview_part) {
            cards.push({
              img: r.preview_part,
              title: r.name,
              sub: `Poems ${(r.poems || []).join(', ')} · Scale ${r.height_ratio}`,
              kind: 'rig'
            });
          }
        }
      });
      // Lazy-load body_lab_unified.json if needed for shoes/hands/heads
      if (/\b(shoe|boot|foot|feet|hand|palm|fist|head|face|eye|sunglass)\b/.test(ql)) {
        if (!STATE.bodyLab) {
          try {
            STATE.bodyLab = await fetch('arena/parts/body_lab/body_lab_unified.json').then(r => r.json());
          } catch (_) {}
        }
        const parts = (STATE.bodyLab && STATE.bodyLab.parts) || (Array.isArray(STATE.bodyLab) ? STATE.bodyLab : []);
        const wantCat = /shoe|boot|foot|feet/.test(ql) ? 'shoes_feet'
          : /hand|palm|fist/.test(ql) ? 'hands'
          : /head|face/.test(ql) ? 'heads'
          : /eye/.test(ql) ? 'eyes_brows' : 'sunglasses_acc';
        parts.filter(p => p.category === wantCat).slice(0, 6).forEach(p => {
          cards.push({
            img: p.file,
            title: p.clip_tag || p.name || wantCat,
            sub: `${p.character_group || 'Cast'} · ${p.view_angle || 'front'}`,
            kind: 'anatomy'
          });
        });
      }
      if (cards.length > 0) {
        cards.slice(0, 2).forEach((c, i) => spawnFetchedItemInWorld(c, i));
        dogLogMessage('hound', `🐾 <b>Woof! Fetched ${cards.length} matching Character & Body Lab cut-outs!</b> I've placed the top 2 right in the street in front of you — click any card below to spawn more:`, cards);
        return;
      }
    }

    // 6. General Search Across All 14 Poems' Clips, Multiplane Scenes, Props, Foundry Shots & CLIP Refs
    const toks = ql.replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(w => w.length > 2 && !['fetch', 'show', 'find', 'get', 'the', 'for', 'with', 'and', 'from', 'here', 'this', 'all'].includes(w));
    const activePm = STATE.master.poems[STATE.activePoemNum];
    const cards = [];

    // If user asked for "this poem" or no specific tokens, return active poem's clips, scenes & props
    if (toks.length === 0 || ql.includes('this poem') || ql.includes('6 scenes')) {
      (activePm.clips || []).slice(0, 3).forEach(cl => {
        cards.push({
          video: cl.src,
          img: cl.thumb,
          title: `${cl.id} · ${cl.sign}`,
          sub: cl.line || activePm.title,
          kind: 'clip'
        });
      });
      (activePm.scenes || []).slice(0, 3).forEach(sc => {
        cards.push({
          img: sc.plate,
          title: `Scene ${sc.key} · ${sc.name}`,
          sub: sc.caption || activePm.place,
          kind: 'scene'
        });
      });
    } else {
      // Score across all 14 poems' scenes, clips, Foundry shots, and CLIP refs
      const scored = [];
      Object.values(STATE.master.poems).forEach(pm => {
        (pm.clips || []).forEach(cl => {
          const hay = `${pm.num} ${pm.title} ${pm.place} ${cl.id} ${cl.line} ${cl.sign}`.toLowerCase();
          let s = 0;
          toks.forEach(t => { if (hay.includes(t)) s += 3; });
          if (s > 0) scored.push({ score: s + 1, card: { video: cl.src, img: cl.thumb, title: `${cl.id} (${pm.title})`, sub: cl.line || cl.sign, kind: 'clip' } });
        });
        (pm.scenes || []).forEach(sc => {
          const hay = `${pm.num} ${pm.title} ${pm.place} ${sc.name} ${sc.caption}`.toLowerCase();
          let s = 0;
          toks.forEach(t => { if (hay.includes(t)) s += 3; });
          if (s > 0) scored.push({ score: s, card: { img: sc.plate, title: `P${pm.num} Scene ${sc.key}: ${sc.name}`, sub: sc.caption || pm.place, kind: 'scene' } });
        });
        (pm.foundry_refs || []).forEach(rf => {
          const hay = `${pm.num} ${pm.title} ${rf.desc} ${rf.line} ${rf.source}`.toLowerCase();
          let s = 0;
          toks.forEach(t => { if (hay.includes(t)) s += 2; });
          if (s > 0) scored.push({ score: s, card: { img: rf.img, title: `Ref ${rf.id} (${rf.source})`, sub: rf.desc || rf.line, kind: 'ref' } });
        });
        (pm.foundry_shots || []).forEach(fs => {
          const hay = `${pm.num} ${pm.title} ${fs.line} ${fs.kind} ${fs.subject} ${fs.light}`.toLowerCase();
          let s = 0;
          toks.forEach(t => { if (hay.includes(t)) s += 2; });
          if (s > 0) scored.push({ score: s, card: { img: fs.img, title: `Shot P${pm.num} · ${fs.kind} ${fs.mm}mm`, sub: fs.line, kind: 'shot' } });
        });
      });
      scored.sort((a, b) => b.score - a.score);
      scored.slice(0, 6).forEach(x => cards.push(x.card));
    }

    if (cards.length === 0) {
      // Fallback to active poem's top clips & scenes
      (activePm.clips || []).slice(0, 2).forEach(cl => cards.push({ video: cl.src, title: cl.id, sub: cl.line, kind: 'clip' }));
      (activePm.scenes || []).slice(0, 2).forEach(sc => cards.push({ img: sc.plate, title: sc.name, sub: sc.caption, kind: 'scene' }));
    }

    cards.slice(0, 2).forEach((c, i) => spawnFetchedItemInWorld(c, i));
    dogLogMessage(
      'hound',
      `🐾 <b>Woof! Found ${cards.length} matching WYGWYL clips, multiplane plates & Foundry shots for "${q}"!</b><br>I ran out and mounted the top 2 in the 3D street — click any card below to spawn more:`,
      cards
    );
  }

  // ── 7. UI WIRING & URL PARAMETER INTERCEPTION ──────────────────────────────
  function syncSelectorsUI() {
    const selStage = document.getElementById('wyg-sel-stage');
    const selPoem = document.getElementById('wyg-sel-poem');
    const selFoundry = document.getElementById('wyg-sel-foundry');
    if (selStage && STATE.activeStageKey) selStage.value = STATE.activeStageKey;
    if (selPoem && STATE.activePoemNum) selPoem.value = STATE.activePoemNum;
    if (selFoundry) selFoundry.value = STATE.activeFoundryId || '';
  }

  async function initWygwylTerrarium() {
    try {
      const res = await fetch('data/terrarium/terrarium_master_index.json');
      STATE.master = await res.json();
    } catch (e) {
      console.error('[wygwyl] Failed to load terrarium_master_index.json', e);
      return;
    }

    // Populate Top HUD Selectors
    const selStage = document.getElementById('wyg-sel-stage');
    const selPoem = document.getElementById('wyg-sel-poem');
    const selFoundry = document.getElementById('wyg-sel-foundry');
    const selTex = document.getElementById('wyg-sel-texmode');

    if (selStage) {
      selStage.innerHTML = STATE.master.real_stages.map(s =>
        `<option value="${s.key}">${s.name} (P${s.poems.join(', P')})</option>`
      ).join('');
      selStage.addEventListener('change', () => {
        loadStageOrFoundry({ stageKey: selStage.value });
      });
    }

    if (selPoem) {
      selPoem.innerHTML = Object.values(STATE.master.poems).map(p =>
        `<option value="${p.num}">Poem ${p.num} · ${p.title}</option>`
      ).join('');
      selPoem.addEventListener('change', () => {
        loadStageOrFoundry({
          stageKey: STATE.activeFoundryId ? null : STATE.activeStageKey,
          foundryId: STATE.activeFoundryId || null,
          poemNum: selPoem.value
        });
      });
    }

    if (selFoundry) {
      selFoundry.innerHTML = `<option value="">— Real City Ground —</option>` +
        STATE.master.foundry_worlds.map(w =>
          `<option value="${w.id}">Foundry ${w.id} · ${w.layout.toUpperCase()} (${Math.round(w.q * 100)}%)</option>`
        ).join('');
      selFoundry.addEventListener('change', () => {
        if (selFoundry.value) {
          loadStageOrFoundry({ foundryId: selFoundry.value, poemNum: STATE.activePoemNum });
        } else {
          loadStageOrFoundry({ stageKey: STATE.activeStageKey, poemNum: STATE.activePoemNum });
        }
      });
    }

    if (selTex) {
      selTex.addEventListener('change', () => applyGroundTextureMode(selTex.value));
    }

    // Camera Mode Buttons
    document.getElementById('wyg-cam-overview')?.addEventListener('click', () => setViewMode('overview'));
    document.getElementById('wyg-cam-scroller')?.addEventListener('click', () => setViewMode('scroller'));
    document.getElementById('wyg-cam-frustum')?.addEventListener('click', () => setViewMode('frustum'));
    document.getElementById('wyg-cam-drive')?.addEventListener('click', () => setViewMode('drive'));
    document.getElementById('wyg-btn-playfilm')?.addEventListener('click', togglePoemFilmPlayback);

    // Horizontal Sidescroller Controls
    const scrub = document.getElementById('wyg-scroller-scrub');
    scrub?.addEventListener('input', () => {
      STATE.scrollerAuto = false;
      applyHorizontalScrollerCamera( parseFloat(scrub.value) || 0 );
    });
    const elevInp = document.getElementById('wyg-scroller-elev');
    elevInp?.addEventListener('input', () => {
      STATE.scrollerElev = parseFloat(elevInp.value) || 4.2;
      if (STATE.viewMode === 'scroller') applyHorizontalScrollerCamera(STATE.scrollerT);
    });
    const distInp = document.getElementById('wyg-scroller-dist');
    distInp?.addEventListener('input', () => {
      STATE.scrollerDist = parseFloat(distInp.value) || 18;
      if (STATE.viewMode === 'scroller') applyHorizontalScrollerCamera(STATE.scrollerT);
    });
    const autoBtn = document.getElementById('wyg-scroller-auto');
    autoBtn?.addEventListener('click', () => {
      STATE.scrollerAuto = !STATE.scrollerAuto;
      autoBtn.textContent = STATE.scrollerAuto ? '⏸ PAUSE SCROLL' : '▶ AUTO-SCROLL';
    });

    // Keyboard shortcuts: [V] toggles Overview <-> Horizontal Sidescroller; Left/Right arrows scrub in Scroller mode
    window.addEventListener('keydown', e => {
      const tag = ((document.activeElement || {}).tagName || '');
      if (/input|textarea|select/i.test(tag) || e.metaKey || e.ctrlKey) return;
      if (e.key === 'v' || e.key === 'V') {
        e.preventDefault();
        setViewMode(STATE.viewMode === 'scroller' ? 'overview' : 'scroller');
      } else if (STATE.viewMode === 'scroller' && (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D')) {
        applyHorizontalScrollerCamera(Math.min(1, STATE.scrollerT + 0.04));
      } else if (STATE.viewMode === 'scroller' && (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A')) {
        applyHorizontalScrollerCamera(Math.max(0, STATE.scrollerT - 0.04));
      }
    });

    // Dog UI Wiring
    const dogInput = document.getElementById('wyg-dog-input');
    const dogSend = document.getElementById('wyg-dog-send');
    const submitDog = () => {
      const v = dogInput.value.trim();
      if (!v) return;
      dogInput.value = '';
      handleDogQuery(v);
    };
    dogSend?.addEventListener('click', submitDog);
    dogInput?.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); submitDog(); }
    });
    document.querySelectorAll('#wyg-dog-chips button').forEach(b => {
      b.addEventListener('click', () => handleDogQuery(b.dataset.q));
    });
    document.getElementById('wyg-dog-roof-btn')?.addEventListener('click', e => {
      STATE.dogMode = STATE.dogMode === 'roof' ? 'companion' : 'roof';
      e.target.textContent = STATE.dogMode === 'roof' ? '📍 ON ROOF' : '🐾 ON STREET';
      placeDogAtMode();
    });
    document.getElementById('wyg-dog-come-btn')?.addEventListener('click', () => {
      STATE.dogMode = 'companion';
      const rb = document.getElementById('wyg-dog-roof-btn');
      if (rb) rb.textContent = '🐾 ON STREET';
      placeDogAtMode();
      updateDogBubble('🐕 RIGHT BESIDE YOU!', 'Tell me what clip, prop, or scene to fetch!');
    });
    document.getElementById('wyg-dog-min-btn')?.addEventListener('click', e => {
      const dock = document.getElementById('wyg-dog-dock');
      dock?.classList.toggle('minimized');
      e.target.textContent = dock?.classList.contains('minimized') ? '+' : '—';
    });

    // Initial Greeting from the Dog
    dogLogMessage(
      'hound',
      `🐕 <b>Woof! I'm the Halfworld Hound — your in-world AI Director & Asset Fetcher.</b><br>` +
      `We've mounted our <b>90 sidescrolling multiplane scenes</b>, <b>continuous poem tapes</b>, <b>playable film portals</b>, <b>WorldText stops</b>, and <b>Foundry 3D topographies</b> right onto the Terrarium ground! Press <b>[V]</b> anytime to toggle between <b>🗺️ 3D Overview</b> and <b>↔️ Horizontal Sidescroller</b>, or ask me to fetch any shot, clip, prop, or world.`
    );

    // Parse URL parameters (`?cart=`, `?stage=`, `?poem=`, `?foundry=`, `?wt=`, `?land=`, `?view=`)
    const q = new URLSearchParams(location.search);
    let initStage = q.get('stage') || '';
    let initPoem = q.get('poem') || '';
    let initFoundry = q.get('foundry') || '';
    const rawCart = q.get('cart') || '';
    const rawWt = q.get('wt') || '';

    if (rawCart) {
      const mStage = rawCart.match(/([a-z0-9-]+)\.landpack\.json/i);
      if (mStage) {
        const key = mStage[1].toLowerCase();
        if (STATE.master.foundry_worlds.some(w => w.id === key)) initFoundry = key;
        else initStage = key;
      }
    }
    if (rawWt && !initPoem) {
      const mWt = rawWt.match(/(\d{2})\.json/);
      if (mWt) initPoem = mWt[1];
    }
    if (!initStage && !initFoundry && !initPoem) {
      initStage = 'mount-vernon';
      initPoem = '01';
    }

    await loadStageOrFoundry({
      stageKey: initFoundry ? null : (initStage || 'mount-vernon'),
      foundryId: initFoundry || null,
      poemNum: initPoem || null
    });

    if (q.get('view') === 'scroller') {
      setTimeout(() => setViewMode('scroller'), 600);
    } else {
      setTimeout(() => setViewMode('overview'), 600);
    }

    // Hook into `window.loadLandPack` so even if the user drags & drops a `.landpack.json` or clicks a chip, our WYGWYL stages mount automatically!
    const origLoadLandPack = window.loadLandPack;
    if (typeof origLoadLandPack === 'function') {
      window.loadLandPack = function(pack) {
        window.__wygCurrentPack = pack;
        const ok = origLoadLandPack(pack);
        try {
          if (pack && pack.wygwyl && Array.isArray(pack.wygwyl.poems) && pack.wygwyl.poems.length) {
            const p0 = String(pack.wygwyl.poems[0].num || STATE.activePoemNum || '01').padStart(2, '0');
            setTimeout(() => mountPoemAssetsOnGround(p0), 180);
          }
        } catch (_) {}
        return ok;
      };
    }

    // Animation loop for Dog tail wagging + Auto-scroll in Horizontal Sidescroller mode
    function wygTick(now) {
      requestAnimationFrame(wygTick);
      const t = now * 0.001;
      if (STATE.dogGroup && STATE.dogGroup.userData) {
        const { tail, head } = STATE.dogGroup.userData;
        if (tail) tail.rotation.z = Math.sin(t * 7.5) * 0.38;
        if (head) head.rotation.z = Math.sin(t * 2.2) * 0.06;
      }
      if (STATE.viewMode === 'scroller' && STATE.scrollerAuto) {
        const nextT = (STATE.scrollerT + 0.0007) % 1.0;
        applyHorizontalScrollerCamera(nextT);
      }
    }
    requestAnimationFrame(wygTick);
  }

  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', () => setTimeout(initWygwylTerrarium, 450));
  } else {
    setTimeout(initWygwylTerrarium, 450);
  }
})();
</script>
"""


def main():
    with open(SRC_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace title
    html = html.replace(
        "<title>THUNDER RIGS — III</title>",
        "<title>WYGWYL · 3D Terrarium, Multiplane Sidescroller & Foundry World Studio</title>"
    )

    # Also patch the default ?cart= and ?land= startup inside unset-04-hartsoe-iii.html
    # so local relative paths and our enriched landpacks work without CORS issues
    idx = html.rfind("</body>")
    if idx != -1:
        html = html[:idx] + WYGWYL_EXTENSION + "\n</body>\n</html>\n"
    else:
        html = html + WYGWYL_EXTENSION

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Built {OUT_HTML} ({os.path.getsize(OUT_HTML):,} bytes)")


if __name__ == "__main__":
    main()
