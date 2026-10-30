// Ground-plane camera for a set: one pinhole, level, at the height the set's scale implies.
//   px_per_cm(y) = (y - horizon) / camera_height_cm        (a figure standing at y is H * px_per_cm(y) tall)
//   camera_height_cm = (ground.y_px - horizon_y_px) / scale.px_per_cm_at_ground_line
// Every figure is scaled by where its feet are; nothing in a scene carries a hand-set size.
// Lane B ships shots/suite/lib/scale.js; if it loads, expectedHeightPx() uses it so the scale check is independent.

let LANE_B = null;
export async function probeLaneB() {
  try {
    let m = await import('./scale.js');
    if (!Object.keys(m).length || (m.default && !Object.keys(m).filter(k => k !== 'default').length)) m = self.WYScale || m.default || m;   // lane B ships a UMD file
    const fn = m.figureHeightPx || m.figureHeightAt || m.heightPxAt || m.expectedHeightPx || (m.default && m.default.figureHeightPx);
    const ppc = m.pxPerCmAt || m.pxPerCm || m.px_per_cm_at || (m.default && m.default.pxPerCmAt);
    if (fn || ppc) LANE_B = { fn, ppc, names: Object.keys(m) };
  } catch (e) { LANE_B = null; }
  return LANE_B;
}
export const laneB = () => LANE_B;

export function makeCamera(set) {
  const W = set.frame[0], H = set.frame[1];
  const yh = set.ground.horizon_y_px, yg = set.ground.y_px;
  const ppcG = set.scale.px_per_cm_at_ground_line;
  const hc = (yg - yh) / ppcG;                                    // camera height, cm
  const f = set.scale.focal_px || (W / 2) / Math.tan((set.scale.hfov_deg || 50) * Math.PI / 360);
  const cx = set.scale.cx_px ?? W / 2;
  const cam = {
    W, H, yh, yg, hc, f, cx,
    ppcAt: y => (y - yh) / hc,
    project: (X, Y, Z) => { const z = Math.max(Z, 1); return [cx + f * X / z, yh + f * (hc - Y) / z, f / z]; },
    groundToWorld: (x, y) => { const Z = f * hc / Math.max(y - yh, 0.5); return [(x - cx) * Z / f, Z]; },
    worldToGround: (X, Z) => [cx + f * X / Z, yh + f * hc / Z],
  };
  cam.expectedHeightPx = (y, heightCm) => {
    if (LANE_B && LANE_B.fn) { try { const v = LANE_B.fn(set, y, heightCm); if (Number.isFinite(v)) return { px: v, by: 'lane B scale.js' }; } catch (e) {} }
    if (LANE_B && LANE_B.ppc) { try { const v = LANE_B.ppc(set, y); if (Number.isFinite(v)) return { px: v * heightCm, by: 'lane B scale.js' }; } catch (e) {} }
    return { px: heightCm * cam.ppcAt(y), by: 'set horizon + px_per_cm_at_ground_line' };
  };
  return cam;
}

// small geometry helpers shared by solver, draw and checks
export const pip = (pt, poly) => {               // point in polygon
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if (((yi > pt[1]) !== (yj > pt[1])) && (pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi)) c = !c;
  }
  return c;
};
export const polyBox = poly => {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of poly) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  return [x0, y0, x1, y1];
};
export const segHitsPoly = (a, b, poly) => {     // does segment a-b cross or enter polygon
  if (pip(a, poly) || pip(b, poly)) return true;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) if (segX(a, b, poly[j], poly[i])) return true;
  return false;
};
function segX(p, p2, q, q2) {
  const d = (p2[0] - p[0]) * (q2[1] - q[1]) - (p2[1] - p[1]) * (q2[0] - q[0]);
  if (Math.abs(d) < 1e-9) return false;
  const u = ((q[0] - p[0]) * (q2[1] - q[1]) - (q[1] - p[1]) * (q2[0] - q[0])) / d;
  const v = ((q[0] - p[0]) * (p2[1] - p[1]) - (q[1] - p[1]) * (p2[0] - p[0])) / d;
  return u > 0 && u < 1 && v > 0 && v < 1;
}
export const clampToPoly = (pt, poly) => {       // nearest point inside (on edge) if outside
  if (pip(pt, poly)) return pt;
  let best = null, bd = Infinity;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[j], b = poly[i], dx = b[0] - a[0], dy = b[1] - a[1];
    const t = Math.max(0, Math.min(1, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / (dx * dx + dy * dy || 1)));
    const q = [a[0] + t * dx, a[1] + t * dy], d = Math.hypot(q[0] - pt[0], q[1] - pt[1]);
    if (d < bd) { bd = d; best = q; }
  }
  // nudge 2 px toward the polygon centroid so the point is strictly inside
  const c = poly.reduce((s, p) => [s[0] + p[0] / poly.length, s[1] + p[1] / poly.length], [0, 0]);
  const v = [c[0] - best[0], c[1] - best[1]], n = Math.hypot(...v) || 1;
  return [best[0] + 2 * v[0] / n, best[1] + 2 * v[1] / n];
};

export const onGround = (pt, set) => (set.grounds || [set.walkable]).some(g => pip(pt, g));
export const groundOf = (pt, set) => (set.grounds || [set.walkable]).find(g => pip(pt, g)) || set.walkable;
