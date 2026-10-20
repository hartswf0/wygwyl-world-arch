/* WYGWYL · navigation
 * One route registry, used by the root index (renders the list) and by every tool (the Index switcher).
 *
 * Contract
 *  - Every tool carries a STATIC <a id="wy-index" href=".../index.html"> before this script runs, so the way back exists
 *    even if the tool's own scripts fail. This script only *enhances* that link.
 *  - Enhanced click (no modifier keys) opens a switcher OVER the tool; the tool's DOM is never touched or rebuilt.
 *    Ctrl/Cmd/Shift/middle-click, or no JS, follow the real link to the root index (Back, copy URL, new tab all work).
 *  - The row for the open tool reads "Current" and is not a link. Close / Escape / backdrop return to the workspace.
 *  - Links open each tool's starting view. Context (shot / poem / district) is NOT carried, because Map and Storyboard
 *    do not read it yet; "continue with this shot" should be added per route only when the destination supports it.
 */
(function () {
  'use strict';

  // path is relative to the repository root
  var ROUTES = [
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
    { id: 'gallery',    name: 'Rig Gallery', does: 'Side-by-side pose & piece disassembly audit', path: 'shots/arena/gallery.html' }
  ];
  window.WYGWYL_ROUTES = ROUTES;

  // repository root, resolved from this script's own URL (works on file://, localhost and GitHub Pages sub-paths)
  var me = document.currentScript || document.querySelector('script[src$="nav.js"]');
  var ROOT = new URL('.', me ? me.src : location.href);
  var rootIndex = new URL('index.html', ROOT).href;
  var href = function (r) { return new URL(r.path, ROOT).href; };
  var samePage = function (u) { // compare pathnames, ignoring trailing index.html differences
    var a = new URL(u).pathname.replace(/\/index\.html$/, '/'), b = location.pathname.replace(/\/index\.html$/, '/');
    return a === b;
  };
  var current = ROUTES.filter(function (r) { return samePage(href(r)); })[0] || null;

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function listHTML(withCurrent) {
    return ROUTES.map(function (r) {
      var isCur = withCurrent && current && current.id === r.id;
      var inner = '<span class="wy-n">' + esc(r.name) + '</span><span class="wy-d">' + esc(r.does) + '</span>' +
                  (isCur ? '<span class="wy-c">Current</span>' : '<span class="wy-go" aria-hidden="true">→</span>');
      return isCur
        ? '<li><div class="wy-row is-current" aria-current="page">' + inner + '</div></li>'
        : '<li><a class="wy-row" href="' + esc(href(r)) + '">' + inner + '</a></li>';
    }).join('');
  }

  var CSS = '' +
    ':root{--wy-bg:#0b0e14;--wy-panel:#11151d;--wy-line:#232a38;--wy-ink:#e9ecf3;--wy-mute:#8b95a8;--wy-amber:#f2a541;--wy-teal:#2ad4c0}' +
    '.wy-list{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}' +
    '@media (max-width:640px){.wy-list{grid-template-columns:1fr}}' +
    '.wy-row{display:grid;grid-template-columns:1fr auto;grid-template-rows:auto auto;column-gap:12px;align-items:baseline;' +
      'padding:14px 16px;min-height:56px;border:1px solid var(--wy-line);border-radius:12px;background:var(--wy-panel);color:var(--wy-ink);' +
      'text-decoration:none;font:14px/1.3 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;' +
      'transition:border-color .15s,transform .15s,background .15s}' +
    'a.wy-row:hover,a.wy-row:focus-visible{border-color:var(--wy-amber);background:#161b26;transform:translateY(-1px);outline:none}' +
    'a.wy-row:focus-visible{box-shadow:0 0 0 2px var(--wy-amber)}' +
    '.wy-n{font-weight:650;font-size:16px;letter-spacing:.01em}.wy-d{grid-column:1;color:var(--wy-mute);font-size:13px;margin-top:2px}' +
    '.wy-go{grid-row:1/3;grid-column:2;align-self:center;color:var(--wy-amber);opacity:.0;transition:opacity .15s,transform .15s}' +
    'a.wy-row:hover .wy-go,a.wy-row:focus-visible .wy-go{opacity:1;transform:translateX(3px)}' +
    '.wy-c{grid-row:1/3;grid-column:2;align-self:center;font:600 11px ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--wy-teal)}' +
    '.wy-row.is-current{border-style:dashed;cursor:default;opacity:.85}' +
    // switcher
    '#wy-sw{position:fixed;inset:0;z-index:2147483646;display:none}#wy-sw.on{display:block}' +
    '#wy-sw .wy-back{position:absolute;inset:0;background:rgba(5,7,11,.72);backdrop-filter:blur(3px)}' +
    '#wy-sw .wy-card{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:min(720px,calc(100vw - 24px));max-height:calc(100vh - 24px);overflow:auto;' +
      'background:var(--wy-bg);border:1px solid var(--wy-line);border-radius:16px;padding:18px;box-shadow:0 30px 80px rgba(0,0,0,.6)}' +
    '#wy-sw .wy-hd{display:flex;justify-content:space-between;align-items:center;margin:0 0 14px;color:var(--wy-ink);font:600 13px ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase}' +
    '#wy-sw .wy-x{min-width:44px;min-height:44px;padding:0 14px;border:1px solid var(--wy-line);border-radius:10px;background:var(--wy-panel);color:var(--wy-ink);font:inherit;cursor:pointer}' +
    '#wy-sw .wy-x:hover,#wy-sw .wy-x:focus-visible{border-color:var(--wy-amber);outline:none}' +
    '#wy-sw .wy-all{display:inline-block;margin-top:12px;color:var(--wy-mute);font:13px ui-sans-serif,system-ui,sans-serif}' +
    '@media (prefers-reduced-motion:reduce){.wy-row,.wy-go{transition:none}}';

  function addStyle() {
    if (document.getElementById('wy-nav-css')) return;
    var s = document.createElement('style'); s.id = 'wy-nav-css'; s.textContent = CSS; document.head.appendChild(s);
  }

  // ---------- root index: render the registry into #wy-list ----------
  var host = document.getElementById('wy-list');
  if (host) { addStyle(); host.innerHTML = listHTML(false); host.className = 'wy-list'; return; }

  // ---------- inside a tool: enhance the static Index link ----------
  var link = document.getElementById('wy-index');
  if (!link) return;
  addStyle();

  var sw = document.createElement('div');
  sw.id = 'wy-sw'; sw.setAttribute('role', 'dialog'); sw.setAttribute('aria-modal', 'true'); sw.setAttribute('aria-label', 'Switch tool');
  sw.innerHTML = '<div class="wy-back" data-wy-close></div><div class="wy-card">' +
    '<div class="wy-hd"><span>Index</span><button type="button" class="wy-x" data-wy-close>Close</button></div>' +
    '<ul class="wy-list">' + listHTML(true) + '</ul>' +
    '<a class="wy-all" href="' + esc(rootIndex) + '">Open the index page</a></div>';
  document.body.appendChild(sw);

  var opener = null;
  function open() {
    opener = document.activeElement; sw.classList.add('on'); link.setAttribute('aria-expanded', 'true');
    var f = sw.querySelector('a.wy-row, .wy-x'); if (f) f.focus();
  }
  function close() {
    sw.classList.remove('on'); link.setAttribute('aria-expanded', 'false');
    (opener && opener.focus ? opener : link).focus();
  }
  link.setAttribute('aria-haspopup', 'dialog'); link.setAttribute('aria-expanded', 'false');
  link.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return; // let the real link work
    e.preventDefault(); sw.classList.contains('on') ? close() : open();
  });
  sw.addEventListener('click', function (e) { if (e.target.closest('[data-wy-close]')) close(); });
  document.addEventListener('keydown', function (e) {
    if (!sw.classList.contains('on')) return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(); return; }
    if (e.key === 'Tab') {                                   // keep focus inside the switcher
      var f = [].slice.call(sw.querySelectorAll('a[href],button')); if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }, true);

  // the label says where you are
  if (current) link.setAttribute('title', current.name + ' · open the index');
})();
