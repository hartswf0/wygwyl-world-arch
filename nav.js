/* WYGWYL · WAG-STACK Context-Preserving Navigation & Switcher
 * One route registry, used by the root index and by every tool in the WAG-STACK.
 *
 * Improvements:
 *  - Preserves active context (`?poem=`, `?scene=`, `?line=`, `?t=`) when jumping between
 *    WAG-STACK tools (Play Spectrogram Worlds, Seven Cuts #grid/#suite, WAG-STACK Workbench,
 *    World Score Desk, Cut Book, Sound Table #Dr-OUT, Narrative 3D Ring, Spine-Cut & Floor).
 *  - Enhances `<a id="wy-index">` with a clean keyboard-accessible modal switcher (`Escape` to close).
 */
(function () {
  'use strict';

  var ROUTES = [
    { id: 'foundryinverse', name: '🔨 Foundry & Inverse Builder', does: 'Build on top of & through 72 Foundry worlds, 104 CLIP refs, 168 sculpted wedges, walk-in sets & metric cut-out cast', path: 'shots/foundry_inverse.html', carry: true },
    { id: 'pngbrowser', name: '🖼️ Saved PNG Grid Browser',   does: '866 saved project PNGs: 62 Foundry/Inverse builds, 341 session proofs/audits, 90 multiplane plates & 365 kit sheets', path: 'shots/png_browser.html', carry: true },
    { id: 'terrarium',  name: '🐕 3D Terrarium & AI Dog',   does: '90 multiplane scenes, film portals, WorldText, Foundry 3D topography, Overview ↔ Horizontal Sidescroller & AI Dog Helper', path: 'shots/terrarium.html', carry: true },
    { id: 'worldfoundry',name:'🌍 World & Foundry Atlas',   does: '14 real-city landpacks, 77 evolved Foundry worlds, 882 camera shots & 104 CLIP Inverse-Topology sculptures', path: 'shots/world_foundry.html', carry: true },
    { id: 'wagstack',   name: '🪐 WAG-STACK Workbench',     does: 'Unified 24:00 hub: Districts, World Score, Cut Book, Worm, Sound Table, 3D Ring & Floor', path: 'shots/wag_stack.html', carry: true },
    { id: 'playlevels', name: '🎮 Spectrogram World Levels', does: '14 sidescrolling poem worlds, 90 spectrogram-blended scenes & pinned World Score tape',  path: 'shots/play/levels.html', carry: true },
    { id: 'film',       name: '⊞ Seven Cuts & 2×2 Grid',    does: 'Suite, Scenes, Cineosis, Drift, Cels, Spine-Cels & Spectrogram Tape on one 24:00 clock', path: 'shots/film.html#grid', carry: true },
    { id: 'suitesolo',  name: '🎬 WYGWYL #suite Cut',       does: 'Canonical 24-minute Suite cut with Deleuze signs & beat patch strip',                    path: 'shots/film.html#suite', carry: true },
    { id: 'worldscore', name: '🎼 Halfworld Pacing Desk',   does: 'Tighten Reading, Scene Beds, Hits on Cues & Sung Ghosts beneath our Halfworld film',     path: 'shots/wag_stack.html#worldscore', carry: true },
    { id: 'cutbook',    name: '✂️ Cut Book & Bayer DJ',     does: '48×192 8×8 Bayer spectrogram, Free Cuts (kill ≤ 0.20) & 3s Hole-Drop audition',          path: 'shots/wag_stack.html#cutbook', carry: true },
    { id: 'spacetime',  name: '🌀 Spacetime Worm',          does: 'Sketchradio 24-minute 3D spacetime worm across all 14 poems & 90 scenes',                 path: 'shots/wag_stack.html#spacetime', carry: true },
    { id: 'sonicfield', name: '⛰️ Sonic Field Topography',  does: '1,442 sounds mapped across Ecology, DINOv2 Form & CLAP Meaning hills',                    path: 'shots/wag_stack.html#sonicfield', carry: true },
    { id: 'soundtable', name: '🎛️ Sound Table (#Dr-OUT)',   does: '17 Sound Families × IN/OFF/OUT Chion rows + 16 live keyboard sampler pads',              path: 'shots/wag_stack.html#Dr-OUT', carry: true },
    { id: 'ring',       name: '💍 Narrative 3D Ring',       does: 'Orbiting 3D cylinder of candidate shots for each spoken poem line (e.g. 02_L06#ring)',    path: 'shots/wag_stack.html?line=02_L06#ring', carry: true },
    { id: 'spine',      name: '脊椎 Spine-Cut & Videotext',  does: '4-row horizontal comparison strip (hers/blend/cel/world) + kinetic word-grip',            path: 'shots/wag_stack.html#spine', carry: true },
    { id: 'floor',      name: '🎞️ Cutting Room Floor',      does: 'Every candidate shot for every beat with KEEP / MAYBE / FLOOR keyboard triage',          path: 'shots/wag_stack.html#floor', carry: true },
    { id: 'bodylab',    name: '🧬 Body Lab & CLIP Search',  does: '3,997 anatomical parts, all shoes/hands/heads wall, 512-D CLIP search & cuff-tuck',      path: 'shots/body_lab.html', carry: false },
    { id: 'crashlab',   name: '🛡️ Crash Lab & CAPTCHAs',    does: '20 ROM crash tests across 9 rigs, Centaur puppet builder & 12 repair CAPTCHAs',          path: 'shots/crash_lab.html', carry: false },
    { id: 'arenaactors',name: '🎭 Character Acting Arena',  does: '8 canonical rigs moving across the stage with solved 7.5H vs 5.2H anatomical scale',     path: 'shots/arena_actors.html', carry: false },
    { id: 'stage',      name: '🏛️ Multiplane Stage',        does: '6-plane parallax stage across all 14 poems with calibrated prop & figure scales',        path: 'shots/stage.html', carry: true },
    { id: 'weave',      name: '🧶 WEAVE',                   does: 'Archive footage, painted gouache sets & cut-out puppets registered in one frame',        path: 'shots/weave.html', carry: false },
    { id: 'world',      name: '🌆 Atlantis 3D World',       does: 'Walk through layered 3D shot dioramas across twelve districts',                          path: 'shots/world.html', carry: false },
    { id: 'guide',      name: '📖 13-District Guide',       does: 'Colour Onto Time, district palettes, sky hours & physical inter-poem transitions',       path: 'shots/wag_stack.html#districts', carry: true },
    { id: 'poems',      name: '📑 Poem Dossiers (01–14)',   does: 'One production page per poem: breakdowns, cast, props, places & kits',                   path: 'shots/poems/index.html', carry: false },
    { id: 'film',       name: 'Film',       does: 'Compare film cuts',               path: 'shots/film.html' },
    { id: 'reels',      name: 'Reels',      does: 'Watch a poem sequence',           path: 'shots/reel.html' },
    { id: 'world',      name: 'World',      does: 'Walk through shot dioramas',      path: 'shots/world.html' },
    { id: 'map',        name: 'Map',        does: 'Locate shots in the city',        path: 'shots/map.html' },
    { id: 'guide',      name: 'World guide', does: 'Read the districts',             path: '_city/index.html' },
    { id: 'shotlab',    name: 'Shot Lab',   does: 'Inspect a shot and its layers',   path: 'shots/index.html' },
    { id: 'storyboard', name: 'Storyboard', does: 'Inspect scene staging',           path: 'shots/storyboard.html' },
    { id: 'studio',     name: 'Studio',     does: 'Inspect animation',               path: 'shots/studio.html' },
    { id: 'animator',   name: 'Animator',   does: 'Live cartoon action & cues',       path: 'shots/animate.html' },
    { id: 'pointcloud', name: '3D Points & Splats', does: 'Metric depth point clouds & Gaussians', path: 'shots/pointcloud.html' },
    { id: 'scion',      name: 'SCION',      does: 'Direct the cel: beats, X-sheet, gates', path: 'shots/scion.html' },
    { id: 'weave',      name: 'WEAVE',      does: 'Archive, cel and AI in one registered shot', path: 'shots/weave.html' },
    { id: 'arena',      name: 'Acting Arena', does: 'Cut-out rig takes, checked and kept', path: 'shots/arena.html' },
    { id: 'acts',       name: 'Acts Compendium', does: 'All 32 challenges, contact sheets & dossiers', path: 'shots/acts.html' },
    { id: 'gallery',    name: 'Rig Gallery', does: 'Side-by-side pose & piece disassembly audit', path: 'shots/arena/gallery.html' },
    { id: 'cineosis',   name: 'Cineosis Takes', does: 'Fifty vignettes on the card rig, gated', path: 'shots/arena/puppet/scion.html' },
    { id: 'kit3',       name: 'Puppet Kit 3', does: 'One image + one prompt per parts sheet', path: 'shots/kit3.html' },
    { id: 'kits2',      name: 'Character Kits v2', does: 'Every character, every poem: sheets to generate', path: 'shots/kits.html' },
    { id: 'design',     name: 'Production Design', does: 'Each poem: reading, kit, props, places, needs', path: 'shots/design/index.html' },
    { id: 'suite',      name: '✂️ Cut-Out Suite', does: 'Stage a scene: sets at true scale, cast, beats on words, archive joins, live checks, export & render', path: 'shots/suite/index.html' },
    { id: 'suitereels', name: '🎞️ Staged Reels', does: 'All 14 poems staged in the suite: 80 scenes with measured checks', path: 'shots/suite/reels.html' },
    { id: 'suitebody',  name: '🧤 Body Lab · every part', does: '9,108 cut parts: all hands, feet, heads, eyes, mouths, limbs at one cm scale, with missing cells', path: 'shots/suite/body.html' },
    { id: 'suitecast',  name: '🚶 Cast in the Arena', does: '34 characters × 6 takes, measured: proportions, scale problems and how each was solved', path: 'shots/suite/cast.html' },
    { id: 'suitesets',  name: '🧱 Sets & Scale', does: '80 scenes as planes with solved scale, surfaces and archive slots', path: 'shots/suite/sets.html' },
  ];
  window.WYGWYL_ROUTES = ROUTES;

  var me = document.currentScript || document.querySelector('script[src$="nav.js"]');
  var ROOT = new URL('.', me ? me.src : location.href);
  var rootIndex = new URL('index.html', ROOT).href;

  function getContextParams() {
    var p = new URLSearchParams(location.search);
    var ctx = {};
    if (p.get('poem')) ctx.poem = p.get('poem');
    if (p.get('scene')) ctx.scene = p.get('scene');
    if (p.get('line')) ctx.line = p.get('line');
    if (p.get('t')) ctx.t = p.get('t');
    return ctx;
  }

  function href(r) {
    var base = new URL(r.path, ROOT);
    if (r.carry) {
      var ctx = getContextParams();
      Object.keys(ctx).forEach(function (k) {
        if (!base.searchParams.has(k)) base.searchParams.set(k, ctx[k]);
      });
    }
    return base.href;
  }

  function samePage(u) {
    var a = new URL(u).pathname.replace(/\/index\.html$/, '/');
    var b = location.pathname.replace(/\/index\.html$/, '/');
    return a === b;
  }
  var current = ROUTES.filter(function (r) { return samePage(href(r)); })[0] || null;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function listHTML(withCurrent) {
    return ROUTES.map(function (r) {
      var isCur = withCurrent && current && current.id === r.id && (!r.path.includes('#') || location.hash === '#' + r.path.split('#')[1]);
      var inner = '<span class="wy-n">' + esc(r.name) + '</span><span class="wy-d">' + esc(r.does) + '</span>' +
                  (isCur ? '<span class="wy-c">Current</span>' : '<span class="wy-go" aria-hidden="true">→</span>');
      return isCur
        ? '<li><div class="wy-row is-current" aria-current="page">' + inner + '</div></li>'
        : '<li><a class="wy-row" href="' + esc(href(r)) + '">' + inner + '</a></li>';
    }).join('');
  }

  var CSS = '' +
    ':root{--wy-bg:#0b0a09;--wy-panel:#141210;--wy-line:#2c2722;--wy-ink:#ece6da;--wy-mute:#a9a093;--wy-amber:#f2a541;--wy-teal:#c4f46a}' +
    '.wy-list{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}' +
    '@media (max-width:640px){.wy-list{grid-template-columns:1fr}}' +
    '.wy-row{display:grid;grid-template-columns:1fr auto;grid-template-rows:auto auto;column-gap:10px;align-items:baseline;' +
      'padding:11px 14px;min-height:50px;border:1px solid var(--wy-line);border-radius:8px;background:var(--wy-panel);color:var(--wy-ink);' +
      'text-decoration:none;font:13px/1.35 "IBM Plex Mono",ui-monospace,Menlo,monospace;' +
      'transition:border-color .15s,transform .15s,background .15s}' +
    'a.wy-row:hover,a.wy-row:focus-visible{border-color:var(--wy-amber);background:#1c1915;transform:translateY(-1px);outline:none}' +
    '.wy-n{font:600 14.5px/1.2 "Fraunces",Georgia,serif;color:var(--wy-ink)}.wy-d{grid-column:1;color:var(--wy-mute);font-size:11.5px;margin-top:2px}' +
    '.wy-go{grid-row:1/3;grid-column:2;align-self:center;color:var(--wy-amber);opacity:.4;transition:opacity .15s,transform .15s}' +
    'a.wy-row:hover .wy-go,a.wy-row:focus-visible .wy-go{opacity:1;transform:translateX(3px)}' +
    '.wy-c{grid-row:1/3;grid-column:2;align-self:center;font:600 10.5px ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--wy-teal)}' +
    '.wy-row.is-current{border-style:dashed;cursor:default;opacity:.85}' +
    '#wy-sw{position:fixed;inset:0;z-index:2147483646;display:none}#wy-sw.on{display:block}' +
    '#wy-sw .wy-back{position:absolute;inset:0;background:rgba(5,5,4,.78);backdrop-filter:blur(4px)}' +
    '#wy-sw .wy-card{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:min(820px,calc(100vw - 24px));max-height:calc(100vh - 24px);overflow:auto;' +
      'background:var(--wy-bg);border:1px solid var(--wy-line);border-radius:12px;padding:16px;box-shadow:0 30px 80px rgba(0,0,0,.75)}' +
    '#wy-sw .wy-hd{display:flex;justify-content:space-between;align-items:center;margin:0 0 12px;color:var(--wy-ink);font:600 12.5px ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase}' +
    '#wy-sw .wy-x{min-width:40px;min-height:36px;padding:0 12px;border:1px solid var(--wy-line);border-radius:6px;background:var(--wy-panel);color:var(--wy-ink);font:inherit;cursor:pointer}' +
    '#wy-sw .wy-x:hover{border-color:var(--wy-amber)}' +
    '#wy-sw .wy-all{display:inline-block;margin-top:12px;color:var(--wy-amber);font:600 12px ui-monospace,Menlo,monospace}';

  function addStyle() {
    if (document.getElementById('wy-nav-css')) return;
    var s = document.createElement('style');
    s.id = 'wy-nav-css';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  var host = document.getElementById('wy-list');
  if (host) { addStyle(); host.innerHTML = listHTML(false); host.className = 'wy-list'; return; }

  var link = document.getElementById('wy-index');
  if (!link) return;
  addStyle();

  var sw = document.createElement('div');
  sw.id = 'wy-sw';
  sw.setAttribute('role', 'dialog');
  sw.setAttribute('aria-modal', 'true');
  sw.setAttribute('aria-label', 'Switch WAG-STACK tool');

  function renderSwitcherModal() {
    sw.innerHTML = '<div class="wy-back" data-wy-close></div><div class="wy-card">' +
      '<div class="wy-hd"><span>🪐 WAG-STACK Tool Switcher (Context-Preserving)</span><button type="button" class="wy-x" data-wy-close>✕ Close</button></div>' +
      '<ul class="wy-list">' + listHTML(true) + '</ul>' +
      '<a class="wy-all" href="' + esc(rootIndex) + '">← Return to Root Index Page</a></div>';
  }
  renderSwitcherModal();
  document.body.appendChild(sw);

  var opener = null;
  function open() {
    renderSwitcherModal();
    opener = document.activeElement;
    sw.classList.add('on');
    link.setAttribute('aria-expanded', 'true');
    var f = sw.querySelector('a.wy-row, .wy-x');
    if (f) f.focus();
  }
  function close() {
    sw.classList.remove('on');
    link.setAttribute('aria-expanded', 'false');
    (opener && opener.focus ? opener : link).focus();
  }
  link.setAttribute('aria-haspopup', 'dialog');
  link.setAttribute('aria-expanded', 'false');
  link.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    sw.classList.contains('on') ? close() : open();
  });
  sw.addEventListener('click', function (e) { if (e.target.closest('[data-wy-close]')) close(); });
  document.addEventListener('keydown', function (e) {
    if (!sw.classList.contains('on')) return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(); }
  }, true);
})();
