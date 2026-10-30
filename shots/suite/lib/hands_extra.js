// Replacement hands (stage lane 1): lane B's rigs carry one painted hand per view; the kits also hold a full set of
// hand shapes (open, relaxed, grip, fist, point, pinch, claw, flat_push, cup, ...) on a common template. This adds them
// as hand parts for every view, palm-side cards when the body faces us and back-side cards when it faces away, so a
// beat's hand shape ('open' on glass, 'fist', 'point') is a real card swap. Measured by tools/stage_hands.py.
export function addReplacementHands(parts, cards, B_TO_SUITE) {
  const out = [];
  for (const [bid, shapes] of Object.entries(cards?.hands || {})) {
    const map = B_TO_SUITE[bid] || [bid, bid], [cid, costume] = map;
    for (const [shape, faces] of Object.entries(shapes)) {
      for (const view of ['front', 'threequarter', 'profile', 'threequarter_back', 'back']) {
        const face = view.includes('back') ? (faces.back || faces.palm) : (faces.palm || faces.back);
        if (!face) continue;
        out.push({ id: `H.${bid}.${shape}.${view}`, character: cid, costume, part: 'hand', side: '-', view, state: shape, file: face.file, w: face.w, h: face.h, pivot: face.wrist,
          sockets: { wrist: face.wrist, tip: face.tip, fingertips: face.tip }, scale: { px_per_cm: null, source: 'replacement hand: sized wrist to fingertips = hand length' }, laneB: true, replacement: true });
      }
    }
  }
  return parts.concat(out);
}
