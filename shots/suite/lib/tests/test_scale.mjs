// node --test shots/suite/lib/tests/test_scale.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import fs from 'node:fs';
const require = createRequire(import.meta.url);
const S = require('../scale.js');
const C = JSON.parse(fs.readFileSync(new URL('./scale_cases.json', import.meta.url)));
const E = C.expect, set = C.set;
const near = (a, b, eps = 1e-3) => assert.ok(Math.abs(a - b) <= eps, `${a} != ${b}`);

test('camera height from ground scale and horizon', () => near(S.cameraHeightCm(set), E.camera_height_cm));
test('px per cm: ground, horizon, half way', () => {
  near(S.pxPerCmAt(set, 1050), E.ppc_at_ground);
  near(S.pxPerCmAt(set, 867), E.ppc_at_horizon);
  near(S.pxPerCmAt(set, 958.5), E.ppc_at_958_5);
});
test('depth <-> foot line round trip', () => {
  near(S.footYForDepth(set, 12), E.foot_y_at_12m);
  near(S.depthForFootY(set, 958.5), E.depth_at_958_5);
  near(S.footYForDepth(set, set.scale.camera_distance_m), set.ground.y_px);
});
test('a figure as tall as the camera has its head on the horizon, at any depth', () => {
  const cam = { height_cm: S.cameraHeightCm(set), build_height_cm: 1 };
  for (const y of [900, 958.5, 1050, 1200]) near(S.place(cam, set, 0, y).head_top_y, E.camera_tall_head_on_horizon);
});
test('placing the poet', () => near(S.place(C.poet, set, 500, 1050).height_px, E.poet_height_px_at_ground));
test('nothing stands above the horizon', () => assert.throws(() => S.place(C.poet, set, 0, 800)));
test('part scale', () => near(S.partScale(C.thigh, C.poet, S.pxPerCmAt(set, 1050)), E.thigh_scale_at_ground, 1e-4));
test('reach top: adult vs child', () => { near(S.reachTopCm(C.poet), E.poet_reach_top_cm); near(S.reachTopCm(C.child), E.child_reach_top_cm); });
test('props: action-owned scale with the leg, set-owned do not', () => {
  near(S.propScale(C.child, 'action', 94.8), E.child_chair_scale, 1e-4);
  assert.equal(S.propScale(C.child, 'set'), 1);
});
test('a child and the poet keep their ratio at the same foot line', () => {
  const a = S.place(C.child, set, 0, 1000).height_px, b = S.place(C.poet, set, 0, 1000).height_px;
  near(a / b, S.heightRatio(C.child, C.poet), 1e-9);
});
test('checkPlaced flags a figure 6 % too tall', () => {
  const want = S.place(C.poet, set, 0, 1050).height_px;
  assert.equal(S.checkPlaced(C.poet, set, 1050, want * 1.06).ok, false);
  assert.equal(S.checkPlaced(C.poet, set, 1050, want * 1.02).ok, true);
});
