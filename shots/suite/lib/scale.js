/* WYGWYL cut-out suite: scale, solved once.
 *
 * One unit: the real centimetre. Every character has a real height_cm; every cut part has its own measured
 * px_per_cm (shots/suite/data/cast_parts.json, from the Kit 3 template it was painted into); every set has a
 * px_per_cm at its ground line and a horizon. Everything else follows:
 *
 *   screen px per cm at a foot line y      ppc(y) = ppc_ground * (y - horizon) / (ground_y - horizon)
 *   (a pinhole camera over a flat floor: size falls off linearly to zero at the horizon; the camera height is
 *    camera_h_cm = (ground_y - horizon) / ppc_ground, so a figure as tall as the camera has its head ON the horizon)
 *   foot line for a depth d (m)            y(d) = horizon + (ground_y - horizon) * d_ground / d
 *   a figure's height on screen            height_px = height_cm * ppc(y)
 *   a part's draw scale                    s = ppc(y) * k / part.px_per_cm      (k = height_cm / build height)
 *
 * Per-character corrections (measured, see shots/suite/AUDIT_cast.md) are data, not code: part px_per_cm
 * normalises parts painted at different sheet scales; the collar tuck, ankle height and knee slot are constants
 * below. Python twin: scale.py (same names, same numbers; both are tested against the same cases).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.WYScale = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const CORRECTIONS = {
    collar_tuck_cm: 0.8,         // head's neck brad pinned this far inside the collar
    head_brad_up_tab: 0.04,      // ... and this fraction up the head card's neck tab
    knee_above_hem_cm: 4.0,      // skirt/robe: the knee slot is the template knee, 4 cm above the hem
    wing_to_torso: 1.35,         // wings: no ghost; canonical length 1.35 x torso (rig library table)
    reach_top_arm_frac: 0.92,    // highest comfortable socket = shoulder + 0.92 x (upper arm + forearm)
    far_limb_shade: 0.72,        // far-side cards are darkened, not resized
  };

  /** k: the factor from the build's template skeleton (the ghosts the parts were painted into) to the real person. */
  function kOf(ch) { return ch.height_cm / ch.build_height_cm; }

  /** A set's ground-line scale and horizon -> camera height (cm). */
  function cameraHeightCm(set) {
    const g = set.ground, s = set.scale;
    return (g.y_px - g.horizon_y_px) / s.px_per_cm_at_ground_line;
  }

  /** Screen px per real cm for a foot line at y (px). Zero at the horizon, negative above it (not placeable). */
  function pxPerCmAt(set, y) {
    const g = set.ground, s = set.scale;
    return s.px_per_cm_at_ground_line * (y - g.horizon_y_px) / (g.y_px - g.horizon_y_px);
  }

  /** Foot line y for a figure standing depth_m from the camera, given the ground line's distance. */
  function footYForDepth(set, depthM) {
    const g = set.ground, d0 = set.scale.camera_distance_m;
    return g.horizon_y_px + (g.y_px - g.horizon_y_px) * d0 / depthM;
  }

  /** Depth (m) of a foot line y. */
  function depthForFootY(set, y) {
    const g = set.ground, d0 = set.scale.camera_distance_m;
    return d0 * (g.y_px - g.horizon_y_px) / (y - g.horizon_y_px);
  }

  /** Place a character standing at (x, y_foot): its height in px, the px/cm used, the draw order (lower = nearer). */
  function place(ch, set, x, yFoot) {
    const ppc = pxPerCmAt(set, yFoot);
    if (!(ppc > 0)) throw new Error('foot line at or above the horizon: nothing can stand there');
    return {
      x, y: yFoot, px_per_cm: ppc, height_px: ch.height_cm * ppc, head_top_y: yFoot - ch.height_cm * ppc,
      depth_m: set.scale.camera_distance_m ? depthForFootY(set, yFoot) : null, z: yFoot,
    };
  }

  /** Draw scale for one cut part of this character at a screen px/cm. */
  function partScale(part, ch, ppc) { return ppc * kOf(ch) / part.px_per_cm; }

  /** Highest socket (cm above the floor) this character can comfortably reach; sockets above it are re-staged. */
  function reachTopCm(ch) {
    const p = ch.proportions;
    return p.shoulder_height_cm + CORRECTIONS.reach_top_arm_frac * (p.upper_arm_cm + p.forearm_cm);
  }

  /** A prop the ACTION owns (a chair, a cup) scales with the actor's leg; a socket the SET owns does not. */
  function propScale(ch, owner, refLegCm) {
    if (owner === 'set') return 1;
    return ch.proportions.leg_cm / (refLegCm || 88.4);
  }

  /** Two characters side by side: the ratio their heights must keep on screen at the same foot line. */
  function heightRatio(a, b) { return a.height_cm / b.height_cm; }

  /** Check a placed figure against the set: is its measured px height within tol of what the rule says? */
  function checkPlaced(ch, set, yFoot, measuredHeightPx, tolPct) {
    const want = ch.height_cm * pxPerCmAt(set, yFoot);
    const err = 100 * (measuredHeightPx / want - 1);
    return { want_px: want, err_pct: err, ok: Math.abs(err) <= (tolPct == null ? 3 : tolPct) };
  }

  return { CORRECTIONS, kOf, cameraHeightCm, pxPerCmAt, footYForDepth, depthForFootY, place, partScale, reachTopCm,
           propScale, heightRatio, checkPlaced };
});
