// Adapters to lanes A (parts), B (characters, scale.js) and C (sets).
// Each source is tried in order; the first that loads wins. The real lane files come first, so when they land on main
// the suite switches to them with no code change. To pin a source, edit the one line in SOURCES.
const SUITE = new URL('../', import.meta.url);        // shots/suite/
const SHOTS = new URL('../../', import.meta.url);     // shots/

export const SOURCES = {
  rigParts: ['data/cast_parts.json'],                                      // lane B: rig-ready parts (A/B pivots, px/cm)
  parts: ['data/proxy/parts.json'],                                        // stand-in: weave man parts + play replacement cards
  registry: ['data/parts.json'],                                           // lane A: the full registry (opt-in: ?registry=1, 9k parts)
  characters: ['data/characters.json', 'data/proxy/characters.json'],      // lane B, then stand-in
  set: id => [`data/sets/${id}.json`, `data/proxy/sets/${id}.json`],       // lane C, then stand-in
};
// lane B may name characters differently; map suite ids to the ids we accept from characters.json
const ALIASES = { poet: ['poet', 'POET', 'poet_man'], ex: ['ex', 'EX'], father_elder: ['father_elder', 'father', 'FATHER', 'elder_1', 'ELDER_1'],
  dancer_dress: ['dancer_dress', 'club_dress'], dancer_shirt: ['dancer_shirt', 'club_shirt'], dancer_jacket: ['dancer_jacket', 'club_jacket'] };

export const suiteURL = p => new URL(p, SUITE).href;
export function fileURL(f) {
  if (!f) return null;
  if (/^(https?:|data:|blob:)/.test(f)) return f;
  if (f.startsWith('/')) return f;
  if (f.startsWith('shots/')) return new URL(f.slice(6), SHOTS).href;
  if (f.startsWith('suite/')) return new URL(f.slice(6), SUITE).href;
  if (f.startsWith('data/') || f.startsWith('lib/') || f.startsWith('sets/') || f.startsWith('parts/') || f.startsWith('cast/')) return new URL(f, SUITE).href;   // lane files are relative to shots/suite/
  return new URL(f, SHOTS).href;                    // contract paths are relative to shots/
}

async function firstJSON(paths) {
  for (const p of paths) {
    try {
      const r = await fetch(suiteURL(p), { cache: 'no-cache' });
      if (r.ok) return { data: await r.json(), from: p, standIn: p.includes('/proxy/') };
    } catch (e) { /* try next */ }
  }
  return null;
}

const VIEWS = { prof: 'profile', q3: 'threequarter', back3q: 'threequarter_back', '3q': 'threequarter', '3q_back': 'threequarter_back' };
const normView = v => VIEWS[v] || v || 'profile';

// lane B character ids for a suite character (+ costume)
const LANE_B_ID = { 'poet|black_tshirt': 'poet_tshirt', 'poet|red_black_sunglasses': 'poet_tracksuit', poet: 'poet_tracksuit', ex: 'ex', father_elder: 'father_elder',
  dancer_dress: 'dancer_dress', dancer_shirt: 'dancer_shirt', dancer_jacket: 'dancer_jacket' };
const B_TO_SUITE = { poet_tshirt: ['poet', 'black_tshirt'], poet_tracksuit: ['poet', 'red_black_sunglasses'], ex: ['ex', 'ex_jacket'], father_elder: ['father_elder', 'elder_father_coat'],
  dancer_dress: ['dancer_dress', 'club_dress'], dancer_shirt: ['dancer_shirt', 'club_shirt'], dancer_jacket: ['dancer_jacket', 'club_jacket'] };
const KIND = { thigh: 'thigh', shin: 'shin', foot: 'foot', uarm: 'upper_arm', farm: 'forearm', hand: 'hand', torso: 'torso' };

// lane B's cast_parts.json + characters.json -> contract part records the stager draws
function laneBParts(castParts, chars) {
  const out = [];
  for (const [bid, entry] of Object.entries(castParts.characters || {})) {
    const map = B_TO_SUITE[bid]; if (!map) continue;
    const [cid, costume] = map, ch = (chars || []).find(c => c.id === bid);
    for (const [view, parts] of Object.entries(entry.views || {})) {
      for (const [key, p] of Object.entries(parts)) {
        const [k, side] = key.split('.'), part = KIND[k]; if (!part) continue;
        const A = p.A, B = p.B, sk = { A, B };
        if (part === 'thigh') Object.assign(sk, { hip: A, knee: B });
        if (part === 'shin') Object.assign(sk, { knee: A, ankle: B });
        if (part === 'upper_arm') Object.assign(sk, { shoulder: A, elbow: B });
        if (part === 'forearm') Object.assign(sk, { elbow: A, wrist: B });
        if (part === 'hand') Object.assign(sk, { wrist: A, tip: B, fingertips: B });
        if (part === 'torso') Object.assign(sk, { neck: A, hip: B }, p.sockets || {});
        if (part === 'foot') { if (view === 'profile' || view === 'threequarter') Object.assign(sk, { ankle: A, toe: p.toe || B, heel: p.heel, toe_sole: p.toe || B }); else Object.assign(sk, { ankle: A, sole: B }); }
        out.push({ id: `B.${bid}.${view}.${key}`, character: cid, costume, part, side: side || '-', view, state: part === 'foot' ? 'flat' : '-', file: p.file, w: p.size[0], h: p.size[1],
          pivot: A, sockets: sk, scale: { px_per_cm: p.px_per_cm, source: 'lane B cast_parts.json (measured against the Kit 3 template)' }, len_cm: p.len_cm, laneB: true });
      }
    }
    // replacement heads, pinned at the view's neck joint
    for (const f of ch?.replacement?.heads || []) {
      const m = f.match(/head\.([a-z_]+)(?:\.([a-z_]+))?\.png$/); if (!m) continue;
      const view = m[1], state = m[2] || '-', j = ch.views?.[view]?.joints?.neck?.head || ch.views?.front?.joints?.neck?.head;
      if (!j) continue;
      out.push({ id: `B.${bid}.head.${view}${state !== '-' ? '.' + state : ''}`, character: cid, costume, part: 'head', side: '-', view, state, file: f, pivot: j, sockets: { neck: j, top: [j[0], 6] },
        scale: { px_per_cm: null, source: 'lane B replacement head; sized neck brad -> crown = neck + head' }, laneB: true });
    }
  }
  return out;
}

export async function loadParts(characters) {
  const proxy = await firstJSON(SOURCES.parts);
  let parts = proxy ? (proxy.data.parts || proxy.data) : [];
  const from = [];
  const rig = await firstJSON(SOURCES.rigParts);
  if (rig) {
    const B = laneBParts(rig.data, characters?._laneB || []);
    const covered = new Set(B.map(p => p.character + '|' + p.costume));
    // lane B rigs replace the stand-in jointed parts of the same character+costume; replacement cards stay
    parts = parts.filter(p => p.part === 'body' || !covered.has(p.character + '|' + p.costume)).concat(B);
    from.push(rig.from + ` (${B.length} rig parts)`);
  }
  if (new URLSearchParams(location.search).get('registry') === '1') {
    const reg = await firstJSON(SOURCES.registry);
    if (reg) { parts = parts.concat((reg.data.parts || []).filter(p => p.view !== 'unknown').map(p => ({ ...p, registry: true }))); from.push(reg.from); }
  }
  if (proxy) from.push(proxy.from);
  parts = parts.map(p => ({ ...p, view: normView(p.view), url: fileURL(p.file) }));
  return { parts, from: from.join(' + '), standIn: !rig };
}

export async function loadCharacters() {
  const got = await firstJSON(SOURCES.characters);
  if (!got) return { characters: {}, from: null };
  const arr = Array.isArray(got.data) ? got.data : (got.data.characters || Object.values(got.data));
  const byId = {};
  for (const c of arr) byId[c.id] = c;
  const out = {};
  if (!got.standIn) {           // lane B: one entry per costume; the suite keys by character and picks the costume at solve time
    for (const [key, bid] of Object.entries(LANE_B_ID)) {
      const [sid, cos] = key.split('|'), hit = byId[bid]; if (!hit) continue;
      out[sid] = out[sid] || { ...hit, id: sid, source_id: hit.id, byCostume: {} };
      if (cos) out[sid].byCostume[cos] = { ...hit, id: sid, source_id: hit.id };
    }
  }
  for (const [sid, names] of Object.entries(ALIASES)) { if (out[sid]) continue; const hit = names.map(n => byId[n]).find(Boolean); if (hit) out[sid] = { ...hit, id: sid, source_id: hit.id }; }
  for (const c of arr) if (!Object.values(out).some(o => o.source_id === c.id)) out[c.id] = c;
  // if lane B is live but lacks a character the scene needs, fall back to the stand-in entry for that one
  if (!got.standIn) {
    const proxy = await firstJSON([SOURCES.characters[1]]);
    for (const c of (proxy?.data.characters || [])) if (!out[c.id]) out[c.id] = { ...c, _standIn: true };
  }
  Object.defineProperty(out, '_laneB', { value: got.standIn ? [] : arr, enumerable: false });
  return { characters: out, from: got.from, standIn: got.standIn };
}

export async function loadSet(sceneId, setId) {
  const got = await firstJSON(SOURCES.set(sceneId).concat(setId ? [`data/sets/${setId}.json`, `data/proxy/sets/${setId}.json`] : []));
  if (!got) throw new Error('no set for ' + sceneId);
  const s = normSet(got.data);
  s._from = got.from; s._standIn = got.standIn;
  return s;
}

// contract -> what the suite needs; tolerant of fields lane C may add or leave out
export function normSet(s) {
  const set = JSON.parse(JSON.stringify(s));
  set.frame = set.frame || set.size || [1920, 1080];
  set.ground = set.ground || {};
  set.scale = set.scale || {};
  if (set.ground.horizon_y_px == null) set.ground.horizon_y_px = set.frame[1] * 0.45;
  if (set.ground.y_px == null) set.ground.y_px = set.frame[1] * 0.86;
  if (!set.scale.px_per_cm_at_ground_line && set.scale.figure_height_px) set.scale.px_per_cm_at_ground_line = set.scale.figure_height_px / 175;
  // lane C stores the whole plate beside its planes: it is the back card, under every plane cut from it
  const layers = set.layers || [];
  if (set.plate && !layers.some(l => l.file === set.plate)) layers.unshift({ id: `${set.scene_id}.plate`, plane: 'P6', kind: 'image', file: set.plate, parallax: 1, z: -1 });
  set.layers = layers.map((l, i) => ({ parallax: 1, z: i, ...l, url: fileURL(l.file) }));
  set.surfaces = set.surfaces || [];
  set.occluders = (set.occluders || []).map(o => ({ ...o, base_y: o.base_y ?? Math.max(...(o.polygon || [[0, 0]]).map(p => p[1])), url: fileURL(o.file) }));
  set.walkable = set.walkable || [[0, set.ground.horizon_y_px + 20], [set.frame[0], set.ground.horizon_y_px + 20], [set.frame[0], set.frame[1]], [0, set.frame[1]]];
  // walkable: one polygon, or several (a room floor and a fire-escape landing); grounds keeps them all
  set.grounds = typeof set.walkable[0][0] === 'number' ? [set.walkable] : set.walkable;
  set.walkable = set.grounds[0];
  set.marks = set.marks || {};
  set.fx = set.fx || [];
  return set;
}

export async function loadArchive() {
  const got = await firstJSON(['data/archive/index.json']);
  const idx = got ? got.data : {};
  for (const [k, v] of Object.entries(idx)) v.url = suiteURL('data/archive/' + v.file);
  return idx;
}

export async function loadScene(id) {
  const got = await firstJSON([`data/scenes/${id}.json`]);
  if (!got) throw new Error('no scene ' + id);
  return got.data;
}
export async function loadSceneIndex() {
  const got = await firstJSON(['data/scenes/index.json']);
  return got ? got.data : { scenes: [] };
}

const IMG = new Map();
export function img(url) {
  if (!url) return Promise.resolve(null);
  if (!IMG.has(url)) IMG.set(url, new Promise(res => {
    const im = new Image(); im.crossOrigin = 'anonymous';
    im.onload = () => res(im); im.onerror = () => { console.warn('image failed', url); res(null); };
    im.src = url;
  }));
  return IMG.get(url);
}
