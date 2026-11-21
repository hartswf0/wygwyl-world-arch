#!/usr/bin/env node
'use strict';

// Exercises the real page initializers with a small, deterministic DOM double.
// This checks media ownership and generated markup, not browser layout or video contents.
// Run from any directory: node scripts/check-landing-scenes.cjs
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');

const ROOT = __dirname.replace(/[/\\]scripts$/, '');
const BASE = 'https://hartswf0.github.io/wygwyl-world-arch/';
const read = file => fs.readFileSync(ROOT + '/' + file, 'utf8');
const clone = value => JSON.parse(JSON.stringify(value));
const canonical = value => {
  const url = new URL(value, BASE);
  url.search = ''; url.hash = '';
  return url.href;
};
const manifestCode = read('landing/manifest.js');
const planCode = read('landing/scene-plan.js');
const requiredTools = {
  foundryinverse: 'shots/foundry_inverse.html', pngbrowser: 'shots/png_browser.html',
  terrarium: 'shots/terrarium.html', worldfoundry: 'shots/world_foundry.html',
  wagstack: 'shots/wag_stack.html', playlevels: 'shots/play/levels.html',
  film: 'shots/film.html#grid', suitesolo: 'shots/film.html#suite',
  worldscore: 'shots/wag_stack.html#worldscore', cutbook: 'shots/wag_stack.html#cutbook',
  spacetime: 'shots/wag_stack.html#spacetime', sonicfield: 'shots/wag_stack.html#sonicfield',
  soundtable: 'shots/wag_stack.html#Dr-OUT', ring: 'shots/wag_stack.html?line=02_L06#ring',
  spine: 'shots/wag_stack.html#spine', floor: 'shots/wag_stack.html#floor',
  bodylab: 'shots/body_lab.html', crashlab: 'shots/crash_lab.html',
  arenaactors: 'shots/arena_actors.html', multiplanestage: 'shots/stage.html',
  weave: 'shots/weave.html', world: 'shots/world.html', map: 'shots/map.html',
  guide: '_city/index.html', shotlab: 'shots/index.html', storyboard: 'shots/storyboard.html',
  pointcloud: 'shots/pointcloud.html', poemsidx: 'shots/poems/index.html',
  filmview: 'shots/film.html', reels: 'shots/reel.html', studio: 'shots/studio.html',
  animator: 'shots/animate.html', scion: 'shots/scion.html', arena: 'shots/arena.html',
  acts: 'shots/acts.html', gallery: 'shots/arena/gallery.html',
  cineosis: 'shots/arena/puppet/scion.html', kit3: 'shots/kit3.html', kits2: 'shots/kits.html',
  design: 'shots/design/index.html', suite: 'shots/suite/index.html',
  suitereels: 'shots/suite/reels.html', suitebody: 'shots/suite/body.html',
  suitecast: 'shots/suite/cast.html', suitesets: 'shots/suite/sets.html'
};

function registry(manifest) {
  const errors = [];
  const context = vm.createContext({URL, console: {error: message => errors.push(message)}});
  context.window = context;
  vm.runInContext(manifestCode, context, {filename: 'landing/manifest.js'});
  if (manifest) context.LANDING = manifest;
  vm.runInContext(planCode, context, {filename: 'landing/scene-plan.js'});
  return {context, media: context.LANDING_MEDIA, manifest: context.LANDING, errors};
}

const initial = registry();
const plan = clone(initial.media.plan);
const manifest = clone(initial.manifest);
assert.equal(initial.errors.length, 0, 'The checked-in allocation must initialize without errors');
assert.equal(initial.media.validatePlan(plan, manifest).length, 0, 'The checked-in plan must be valid');
assert.equal(new Set(plan.map(entry => entry.owner)).size, plan.length, 'Each owner must be unique');
assert.equal(new Set(plan.map(entry => manifest[entry.scene].sourceSid || manifest[entry.scene].sid)).size,
  plan.length, 'Each presentation must have a unique source identity');
const byOwner = new Map(plan.map(entry => [entry.owner, entry]));
const chapterPlan = plan.filter(entry => entry.kind === 'chapter');
assert.equal(chapterPlan.length, 3, 'The landing has three curated chapters, independent of the tool count');

// These mutations exercise the real validator. Different keys, filenames, query
// strings and relative spellings must not turn one source into two allocations.
let negativeCases = 0;
function rejects(label, entries, sources) {
  assert.ok(initial.media.validatePlan(entries, sources).length, 'Validator accepted ' + label);
  negativeCases++;
}
const [first, second] = plan;
rejects('a repeated owner', plan.concat({...first}), clone(manifest));
rejects('a second owner of an existing scene', plan.concat({...first, owner: 'duplicate-owner'}), clone(manifest));
{
  const sources = clone(manifest);
  sources.alias = {...clone(sources[first.scene]), poster: 'landing/new-name/poster.webp', planes: []};
  rejects('a scene alias with a different filename', plan.concat({...first, owner: 'alias-owner', scene: 'alias'}), sources);
  sources.alias.sid = 'apparently-new-derivative';
  sources.alias.sourceSid = sources[first.scene].sourceSid || sources[first.scene].sid;
  rejects('a derivative sharing sourceSid', plan.concat({...first, owner: 'derivative-owner', scene: 'alias'}), sources);
}
for (const [label, transform] of [
  ['same poster path', value => value],
  ['poster path with a query and fragment', value => './' + value + '?crop=wide#preview'],
  ['poster path with dot segments', value => value.replace('/poster.', '/temporary/../poster.')],
  ['absolute poster URL alias', value => new URL(value, BASE).href]
]) {
  const sources = clone(manifest);
  sources[second.scene].poster = transform(sources[first.scene].poster);
  rejects(label, clone(plan), sources);
}
{
  const sources = clone(manifest);
  sources[second.scene].planes[0].src = './' + sources[first.scene].planes[0].src + '?variant=2';
  rejects('a shared layer between separate scene owners', clone(plan), sources);
  rejects('a missing source scene', plan.concat({owner: 'missing', scene: '__missing__'}), clone(manifest));
}

function element(owner) { return {dataset: owner ? {sceneOwner: owner} : {}, hidden: false}; }
{
  const {media, errors} = registry();
  const original = element();
  assert.ok(media.claim(first.owner, original), 'A valid owner must be able to claim its element');
  assert.ok(media.claim(first.owner, original), 'Reinitializing the same presentation is idempotent');
  const duplicate = element();
  assert.equal(media.claim(first.owner, duplicate), null, 'A second DOM root must be rejected');
  assert.equal(duplicate.hidden, true, 'Rejected duplicate roots must be hidden');
  assert.equal(original.hidden, false, 'Rejecting a duplicate must not hide the accepted root');
  const unknown = element();
  assert.equal(media.claim('__unallocated__', unknown), null, 'Unknown owners must be rejected');
  assert.equal(unknown.hidden, true);
  assert.ok(errors.length >= 2, 'Claim failures must be observable');
  negativeCases += 2;
}
{
  // Alias introduced after startup: the live claim guard must still use source
  // identity instead of trusting distinct owner names or scene keys.
  const live = registry();
  assert.ok(live.media.claim(first.owner, element()));
  live.manifest[second.scene].sourceSid = live.manifest[first.scene].sourceSid || live.manifest[first.scene].sid;
  const duplicate = element();
  assert.equal(live.media.claim(second.owner, duplicate), null, 'A live sourceSid alias must not get a second DOM root');
  assert.equal(duplicate.hidden, true);
  negativeCases++;
}
{
  const {media} = registry();
  const posters = plan.filter(entry => entry.kind === 'poster').map(entry => element(entry.owner));
  const scope = {querySelectorAll: () => posters};
  media.mountPosters(scope);
  posters.forEach(image => assert.equal(image.src, manifest[byOwner.get(image.dataset.sceneOwner).scene].poster));
  media.mountPosters(scope); // Same nodes are safe to mount again.
  const duplicate = element(posters[0].dataset.sceneOwner);
  media.mountPosters({querySelectorAll: () => [duplicate]});
  assert.equal(duplicate.hidden, true, 'mountPosters must apply the duplicate guard');
  assert.equal(duplicate.src, undefined, 'A rejected poster must not load its duplicate image');
  negativeCases++;
}

// Minimal DOM used only for deterministic initialization and generated-markup
// assertions. It deliberately supplies no layout engine, networking or video.
const decode = text => String(text).replace(/&(?:amp|lt|gt|quot|apos|#39|#\d+|#x[\da-f]+);/gi, entity => {
  const named = {'&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'", '&#39;': "'"};
  return named[entity.toLowerCase()] || String.fromCodePoint(parseInt(entity.slice(entity[2].toLowerCase() === 'x' ? 3 : 2, -1), entity[2].toLowerCase() === 'x' ? 16 : 10));
});
const attrName = key => 'data-' + key.replace(/[A-Z]/g, char => '-' + char.toLowerCase());
function attributes(source) {
  const result = {};
  const rx = /([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g;
  for (const match of source.matchAll(rx)) result[match[1].toLowerCase()] = decode(match[2] ?? match[3] ?? match[4] ?? '');
  return result;
}
function matchesSimple(node, selector) {
  if (!node.tagName) return false;
  const attrs = [...selector.matchAll(/\[([^\]=\s]+)(?:\s*=\s*["']?([^\]"']*)["']?)?\]/g)];
  selector = selector.replace(/\[[^\]]*\]/g, '');
  const tag = selector.match(/^[\w-]+/);
  if (tag && node.tagName !== tag[0].toUpperCase()) return false;
  const id = selector.match(/#([\w-]+)/);
  if (id && node.id !== id[1]) return false;
  if ([...selector.matchAll(/\.([\w-]+)/g)].some(match => !node.classList.contains(match[1]))) return false;
  return attrs.every(match => node.hasAttribute(match[1]) && (match[2] === undefined || node.getAttribute(match[1]) === match[2]));
}
function matches(node, selector) {
  return selector.split(',').some(branch => {
    const parts = branch.trim().split(/\s+(?![^\[]*\])/).filter(Boolean);
    if (!matchesSimple(node, parts.pop() || '*')) return false;
    let parent = node.parentNode;
    while (parts.length) {
      const part = parts.pop();
      while (parent && !matchesSimple(parent, part)) parent = parent.parentNode;
      if (!parent) return false;
      parent = parent.parentNode;
    }
    return true;
  });
}
class Node {
  constructor(tag = '', attrs = {}, text = '') {
    this.tagName = tag ? tag.toUpperCase() : '';
    this.attrs = {...attrs}; this.childNodes = []; this.parentNode = null; this.text = text;
    this.listeners = {}; this.value = ''; this.scrollTop = 0; this.currentTime = 0; this.paused = true;
    this.clientWidth = 1200; this.clientHeight = 680; this.scrollHeight = 680; this.offsetTop = 0;
    this.style = {setProperty(key, value) { this[key] = String(value); }};
    this.dataset = new Proxy({}, {
      get: (_, key) => this.getAttribute(attrName(key)) ?? undefined,
      set: (_, key, value) => { this.setAttribute(attrName(key), value); return true; }
    });
    this.classList = {
      contains: name => this.className.split(/\s+/).includes(name),
      add: (...names) => { this.className = [...new Set(this.className.split(/\s+/).filter(Boolean).concat(names))].join(' '); },
      remove: (...names) => { this.className = this.className.split(/\s+/).filter(name => !names.includes(name)).join(' '); },
      toggle: (name, force) => {
        const on = force === undefined ? !this.classList.contains(name) : force;
        this.classList[on ? 'add' : 'remove'](name); return on;
      }
    };
  }
  get children() { return this.childNodes.filter(node => node.tagName); }
  get firstChild() { return this.childNodes[0] || null; }
  get lastChild() { return this.childNodes[this.childNodes.length - 1] || null; }
  get id() { return this.attrs.id || ''; }
  set id(value) { this.attrs.id = String(value); }
  get className() { return this.attrs.class || ''; }
  set className(value) { this.attrs.class = String(value); }
  get src() { return this.attrs.src || ''; }
  set src(value) { this.attrs.src = String(value); if (this.onload) this.onload(); }
  get href() { return new URL(this.attrs.href || '', BASE).href; }
  set href(value) { this.attrs.href = String(value); }
  get hidden() { return this.hasAttribute('hidden'); }
  set hidden(value) { value ? this.setAttribute('hidden', '') : this.removeAttribute('hidden'); }
  get textContent() { return this.text + this.childNodes.map(node => node.textContent).join(''); }
  set textContent(value) { this.text = String(value); this.childNodes = []; }
  get innerText() { return this.textContent; }
  get innerHTML() { return this.text + this.childNodes.map(serialize).join(''); }
  set innerHTML(value) { this.text = ''; this.childNodes = []; parse(String(value), this); }
  setAttribute(key, value) { this.attrs[key] = String(value); }
  getAttribute(key) { return Object.hasOwn(this.attrs, key) ? this.attrs[key] : null; }
  hasAttribute(key) { return Object.hasOwn(this.attrs, key); }
  removeAttribute(key) { delete this.attrs[key]; }
  appendChild(node) { if (node.parentNode) node.parentNode.childNodes = node.parentNode.childNodes.filter(child => child !== node); node.parentNode = this; this.childNodes.push(node); return node; }
  replaceChildren(...nodes) { this.childNodes = []; nodes.forEach(node => this.appendChild(node)); }
  querySelectorAll(selector) { const out = []; const visit = node => node.childNodes.forEach(child => { if (matches(child, selector)) out.push(child); visit(child); }); visit(this); return out; }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  closest(selector) { for (let node = this; node; node = node.parentNode) if (matches(node, selector)) return node; return null; }
  matches(selector) { return matches(this, selector); }
  contains(node) { for (; node; node = node.parentNode) if (node === this) return true; return false; }
  addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); }
  removeEventListener(type, handler) { this.listeners[type] = (this.listeners[type] || []).filter(fn => fn !== handler); }
  dispatchEvent(event) { event.target ||= this; event.preventDefault ||= () => {}; [...(this.listeners[event.type] || [])].forEach(handler => handler.call(this, event)); if (this['on' + event.type]) this['on' + event.type](event); return true; }
  getBoundingClientRect() { const top = this.id === 'hero' ? 0 : this.id === 'made' ? 900 : 3000; return {top, bottom: top + 700, left: 0, right: 1200, width: 1200, height: 700}; }
  getClientRects() { return this.hidden ? [] : [this.getBoundingClientRect()]; }
  scrollIntoView() {}
  focus() {}
  select() {}
  play() { this.paused = false; return Promise.resolve(); }
  pause() { this.paused = true; }
}
const VOID = new Set('area base br col embed hr img input link meta param source track wbr'.split(' '));
function serialize(node) {
  if (!node.tagName) return node.text;
  const tag = node.tagName.toLowerCase();
  const attrs = Object.entries(node.attrs).map(([key, value]) => ' ' + key + '="' + value.replace(/&/g, '&amp;').replace(/"/g, '&quot;') + '"').join('');
  return '<' + tag + attrs + '>' + (VOID.has(tag) ? '' : node.innerHTML + '</' + tag + '>');
}
function parse(html, root) {
  const stack = [root];
  const clean = html.replace(/<!--[^]*?-->/g, '').replace(/<(script|style)\b[^>]*>[^]*?<\/\1\s*>/gi, '');
  const tokens = clean.match(/<![^>]*>|<\/?[A-Za-z][^>]*>|[^<]+/g) || [];
  for (const token of tokens) {
    if (token.startsWith('<!')) continue;
    if (token.startsWith('</')) {
      const tag = token.slice(2).match(/^[\w-]+/)[0].toUpperCase();
      const index = stack.findLastIndex(node => node.tagName === tag);
      if (index > 0) stack.length = index;
    } else if (token.startsWith('<')) {
      const match = token.match(/^<([\w-]+)([^]*?)\/?>$/);
      const node = new Node(match[1], attributes(match[2]));
      stack[stack.length - 1].appendChild(node);
      if (!VOID.has(match[1].toLowerCase()) && !token.endsWith('/>')) stack.push(node);
    } else stack[stack.length - 1].appendChild(new Node('', {}, decode(token)));
  }
  return root;
}

function runPage(page, {extraTool = false} = {}) {
  const html = read(page), document = parse(html, new Node());
  document.createElement = tag => new Node(tag);
  document.getElementById = id => document.querySelector('#' + id);
  document.documentElement = document.querySelector('html');
  document.body = document.querySelector('body');
  const staticOwners = document.querySelectorAll('[data-scene-owner]').map(node => node.dataset.sceneOwner);
  for (const entry of plan.filter(entry => entry.page === page && entry.kind !== 'chapter')) {
    assert.equal(staticOwners.filter(owner => owner === entry.owner).length, 1, page + ' must declare ' + entry.owner + ' exactly once');
  }
  staticOwners.forEach(owner => assert.equal(byOwner.get(owner)?.page, page, 'Unknown or wrong-page owner ' + owner));
  assert.equal(document.querySelectorAll('[data-shot]').length, 0, 'Tools must not allocate scenes through data-shot');
  assert.equal(document.querySelectorAll('[data-scene]').length, 0, 'A scene switcher must not reintroduce already allocated scenes');
  if (extraTool) {
    const li = new Node('li');
    li.innerHTML = '<a data-key="__text_only_control__" href="shots/new-tool.html"><b>Additional tool</b><span>No image allocation</span></a>';
    document.getElementById('tools').appendChild(li);
  }
  const errors = [], timers = [];
  const context = vm.createContext({
    URL, document, console: {error: message => errors.push(message), log() {}, warn() {}},
    innerWidth: 1200, innerHeight: 800, scrollY: 0,
    matchMedia: () => ({matches: false}), getComputedStyle: () => ({overflowY: 'visible'}),
    requestAnimationFrame: () => 0, cancelAnimationFrame() {},
    setTimeout: fn => (timers.push(fn), timers.length), clearTimeout() {},
    addEventListener() {}, history: {replaceState() {}},
    location: {href: BASE + page, pathname: '/wygwyl-world-arch/' + page, hash: '', search: ''},
    navigator: {}, Event: class { constructor(type) { this.type = type; } },
    Image: function () { return new Node('img'); },
    IntersectionObserver: class { constructor(callback) { this.callback = callback; } observe(target) { this.callback([{target, isIntersecting: true}]); } disconnect() {} }
  });
  context.window = context;
  for (const script of html.matchAll(/<script\b([^>]*)>([^]*?)<\/script\s*>/gi)) {
    const attrs = attributes(script[1]);
    if (attrs.type && !/^(?:text|application)\/javascript$/.test(attrs.type)) continue;
    if (attrs.src && /^https?:/i.test(attrs.src)) throw new Error('Unmodeled external script: ' + attrs.src);
    const code = attrs.src ? read(attrs.src) : script[2];
    if (code.trim()) vm.runInContext(code, context, {filename: attrs.src || page + ':inline', timeout: 3000});
  }
  assert.equal(errors.length, 0, page + ' logged a media ownership failure: ' + errors.join('; '));
  return {page, document, context, html};
}

function assertTextOnly(node, label) {
  assert.ok(node, label + ' must remain available');
  assert.equal(node.querySelectorAll('img,picture,svg,canvas,video').length, 0, label + ' must not recycle media');
  for (const child of [node, ...node.querySelectorAll('*')]) {
    const styles = (child.getAttribute('style') || '') + ' ' + Object.values(child.style).filter(value => typeof value === 'string').join(' ');
    assert.ok(!/url\s*\(/i.test(styles), label + ' must not recycle background images');
  }
}

function inspectPage(run) {
  const {page, document} = run;
  const owners = document.querySelectorAll('[data-scene-owner]');
  const expected = plan.filter(entry => entry.page === page);
  assert.equal(owners.length, expected.length, page + ' has an unexpected number of scene presentations');
  const seen = new Set(), paths = new Map();
  for (const entry of expected) {
    const roots = owners.filter(node => node.dataset.sceneOwner === entry.owner);
    assert.equal(roots.length, 1, entry.owner + ' must have exactly one actual DOM presentation');
    const root = roots[0], scene = manifest[entry.scene], sid = scene.sourceSid || scene.sid;
    assert.equal(root.dataset.sceneId, sid, entry.owner + ' must pass through the runtime claim guard');
    assert.equal(root.dataset.sceneKey, entry.scene);
    assert.equal(root.hidden, false, entry.owner + ' must not disappear to conceal a duplicate');
    assert.ok(!seen.has(sid), page + ' repeats canonical source ' + sid); seen.add(sid);
    const expectedAssets = new Set([scene.poster, ...scene.planes.map(plane => plane.src)].map(canonical));
    const images = root.tagName === 'IMG' ? [root] : root.querySelectorAll('img');
    assert.ok(images.length, entry.owner + ' must retain its original artwork');
    const withinOwner = new Set();
    for (const image of images) {
      const url = canonical(image.src || image.dataset.src || '');
      assert.ok(expectedAssets.has(url), entry.owner + ' displays an unallocated image: ' + url);
      assert.ok(!withinOwner.has(url), entry.owner + ' mounts the same image twice'); withinOwner.add(url);
      if (paths.has(url)) assert.equal(paths.get(url), entry.owner, 'Image reused by separate owners');
      paths.set(url, entry.owner);
    }
    if (entry.kind !== 'poster') {
      for (const plane of scene.planes) assert.ok(withinOwner.has(canonical(plane.src)), entry.owner + ' lost its distinct ' + plane.id + ' layer');
    }
  }
  for (const image of document.querySelectorAll('img')) assert.ok(image.closest('[data-scene-owner]'), page + ' has an unowned image: ' + image.src);
  assert.equal(document.querySelectorAll('#expModal,#expModalImg').length, 0, 'Proof images must open at their source, not duplicate in an inline modal');
  if (page === 'index.html') {
    const tools = document.querySelectorAll('#tools a');
    for (const [key, href] of Object.entries(requiredTools)) {
      const links = tools.filter(node => node.dataset.key === key);
      assert.equal(links.length, 1, 'Missing or repeated tool ' + key);
      assert.equal(links[0].getAttribute('href'), href, 'Changed destination for ' + key);
    }
    const chapters = document.querySelectorAll('#chapters .chap');
    assert.deepEqual(chapters.map(node => node.id).sort(), chapterPlan.map(entry => entry.tool).sort(), 'Only allocated chapters may be generated');
    const tiles = document.getElementById('tiles');
    assert.equal(tiles.querySelectorAll('.tile').length, tools.length, 'Text-only navigation must retain every tool');
    assertTextOnly(tiles, 'Tool sheet');
    assertTextOnly(document.getElementById('expGrid'), 'Experiment archive');
    assert.equal(document.querySelectorAll('#expGrid .exp-card').length, 68, 'All 68 archive entries must remain accessible');
    const video = document.getElementById('vid');
    assert.ok(!video.hasAttribute('loop'), 'The landing film must not loop automatically');
    video.currentTime = 191.5;
    video.dispatchEvent({type: 'ended'});
    assert.equal(video.currentTime, 191.5, 'Ending the film must not seek back to its opening scene');
    // Exercise the actual renderer after each category/search update, not only
    // its initial markup. Duplicate imagery must not return through filtering.
    for (const button of document.querySelectorAll('#expControls .exp-tab')) {
      button.dispatchEvent({type: 'click'});
      assertTextOnly(document.getElementById('expGrid'), 'Filtered experiment archive');
    }
    const search = document.getElementById('expSearch');
    for (const value of ['poem', 'rig', '__no_matching_record__', '']) {
      search.value = value; search.dispatchEvent({type: 'input'});
      assertTextOnly(document.getElementById('expGrid'), 'Searched experiment archive');
    }
    assert.equal(document.querySelectorAll('[data-scene-owner]').length, expected.length, 'Filtering must not allocate additional scenes');
  }
  return {owners, paths};
}

const main = runPage('index.html');
const design = runPage('design-prompts.html');
const mainResult = inspectPage(main), designResult = inspectPage(design);
const ownership = new Map();
for (const {owners} of [mainResult, designResult]) for (const root of owners) {
  assert.ok(!ownership.has(root.dataset.sceneId), 'A source scene repeats across the landing and design page');
  ownership.set(root.dataset.sceneId, root.dataset.sceneOwner);
}
for (const [url, owner] of designResult.paths) assert.ok(!mainResult.paths.has(url), 'Design page reuses landing image ' + url + ' at ' + owner);

// A newly added tool must stay text-only unless it receives a new explicit scene
// allocation. This catches the old per-tool chapter loop without matching prose.
inspectPage(runPage('index.html', {extraTool: true}));

// CSS can bypass the DOM allocator. Permit only the entrance's own no-script
// fallback; it is part of that composition, not another presentation.
const cssSources = [read('landing/entrance.css'), ...[...main.html.matchAll(/<style\b[^>]*>([^]*?)<\/style>/gi)].map(match => match[1]), ...[...design.html.matchAll(/<style\b[^>]*>([^]*?)<\/style>/gi)].map(match => match[1])];
const allAssets = new Set(plan.flatMap(entry => [manifest[entry.scene].poster, ...manifest[entry.scene].planes.map(plane => plane.src)]).map(canonical));
for (const css of cssSources) {
  for (const rule of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) for (const match of rule[2].matchAll(/url\(\s*["']?([^\s)"']+)["']?\s*\)/g)) {
    const url = canonical(match[1]);
    if (allAssets.has(url)) {
      assert.equal(url, canonical(manifest[byOwner.get('entrance').scene].poster), 'CSS recycles an allocated image outside its owner');
      assert.ok(/#hero\s+\.stage/.test(rule[1]), 'Only the entrance owner may use its own poster as a CSS fallback');
    } else if (/\.(?:png|jpe?g|webp|avif|svg)(?:[?#]|$)/i.test(match[1])) {
      assert.fail('Unallocated CSS image: ' + match[1]);
    }
  }
}

// Filename uniqueness is insufficient: catch copies saved under new filenames.
const hashes = new Map(), missing = [];
for (const entry of plan) {
  const scene = manifest[entry.scene], url = new URL(scene.poster, BASE);
  if (url.origin !== new URL(BASE).origin || !url.pathname.startsWith(new URL(BASE).pathname)) {
    missing.push(scene.poster); continue;
  }
  const local = ROOT + '/' + decodeURIComponent(url.pathname.slice(new URL(BASE).pathname.length));
  if (!fs.existsSync(local)) { missing.push(scene.poster); continue; }
  const bytes = fs.readFileSync(local);
  assert.ok(bytes.length, 'Empty poster: ' + scene.poster);
  const hash = crypto.createHash('sha256').update(bytes).digest('hex');
  assert.ok(!hashes.has(hash), 'Identical poster bytes at ' + scene.poster + ' and ' + hashes.get(hash));
  hashes.set(hash, scene.poster);
}
if (process.env.CI) assert.equal(missing.length, 0, 'CI must check every poster; missing: ' + missing.join(', '));
if (missing.length) console.warn('Poster-byte check skipped unavailable local files: ' + missing.join(', '));
console.log('PASS: ' + ownership.size + ' exclusive scene owners across two pages; three curated chapters; all 45 tools and 68 archive entries retained.');
console.log('PASS: real page initialization, category/search rerenders, and an added text-only tool produce no repeated media; film end does not rewind.');
console.log('PASS: ' + negativeCases + ' duplicate/alias rejection cases; ' + hashes.size + ' unique poster byte hashes.');
