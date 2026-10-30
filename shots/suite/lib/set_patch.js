// Scene-side additions to a lane-C set (stage lane 1). Lane C measures the plate (horizon, px/cm, surfaces, occluder
// silhouettes); a staged scene still has to say where people may walk, what the named marks are, at what depth a
// surface stands (base_y: the ground row under it) and how deep an occluder's footprint goes. Those are blocking
// decisions, so they live in the scene JSON as `set_patch` and are merged here after the set loads:
//
//   set_patch: {
//     walkable:  [[x,y]...] | [[[x,y]...], [[x,y]...]]   replaces the default "everything below the horizon"
//     marks:     {name: [x,y]}                           named ground points for walk_to / go_to
//     surfaces:  [{id, base_y?, stand?, polygon?, kind?}] merged by id into lane C's surfaces (or added)
//     occluders: [{id, footprint?, base_y?, polygon?, remove?}]  merged by id (or added: drawn from the plate under its polygon)
//     fx:        [...]                                   code-drawn set pieces (rail, deck, glass, darken, …) added to set.fx
//     layers:    [{id, depth_m?, parallax?, alpha?, why}]  re-seat a lane-C plane (e.g. a P4 that holds both the room and the
//                                                    view through its glass goes behind a figure standing outside the glass)
//   }
// It never touches scale: figure size stays lane C's horizon + px_per_cm_at_ground_line.
import { fileURL } from './adapters.js';

export function applySetPatch(set, patch) {
  // lane C stores the plate's measured focal length under its own key; the camera reads focal_px
  if (set.scale && set.scale.focal_px == null && set.scale.focal_px_stage) set.scale.focal_px = set.scale.focal_px_stage;
  if (!patch) return set;
  if (patch.walkable) {
    set.grounds = typeof patch.walkable[0][0] === 'number' ? [patch.walkable] : patch.walkable;
    set.walkable = set.grounds[0];
  }
  if (patch.marks) set.marks = { ...(set.marks || {}), ...patch.marks };
  for (const s of patch.surfaces || []) {
    const have = set.surfaces.find(x => x.id === s.id);
    if (have) Object.assign(have, s); else set.surfaces.push({ kind: 'pane', ...s });
  }
  for (const o of patch.occluders || []) {
    if (o.remove) { set.occluders = set.occluders.filter(x => x.id !== o.id); continue; }   // e.g. a city far below a fall is not in front of anyone
    const have = set.occluders.find(x => x.id === o.id);
    if (have) Object.assign(have, o);
    else set.occluders.push({ ...o, base_y: o.base_y ?? Math.max(...o.polygon.map(p => p[1])), url: fileURL(o.file) });
  }
  for (const l of patch.layers || []) {
    const have = set.layers.find(x => x.id === l.id);
    if (have) { const { why, ...rest } = l; Object.assign(have, rest); }
  }
  if (patch.fx) set.fx = [...(set.fx || []), ...patch.fx];
  set._patched = true;
  return set;
}
