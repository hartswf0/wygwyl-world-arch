// The puppet as a skeleton in world centimetres (X right, Y up, Z away from camera), posed per frame and
// projected through the set's camera. Feet are planted at world points, so depth scale and foot pinning
// come from the same projection; arms and legs are two-bone IK with a pole.
//   facing phi: 0 = screen right, 90 = toward camera, 180 = screen left, 270 = away
//   local (u forward, v up, w the puppet's left) -> world: X = u cos phi + w sin phi ; Z = -u sin phi + w cos phi

export const D2R = Math.PI / 180;
export const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
export const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
export const mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
export const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const len = a => Math.hypot(a[0], a[1], a[2]);
export const norm = a => { const l = len(a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
export const lerp = (a, b, t) => a + (b - a) * t;
export const lerp3 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
export const smooth = t => t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t);
export const wrapDeg = a => ((a % 360) + 540) % 360 - 180;

export function axes(phiDeg) {
  const p = phiDeg * D2R, c = Math.cos(p), s = Math.sin(p);
  return { fwd: [c, 0, -s], left: [s, 0, c], up: [0, 1, 0] };
}
export const local = (ax, u, v, w) => [ax.fwd[0] * u + ax.left[0] * w, v, ax.fwd[2] * u + ax.left[2] * w];

// view label from facing; EX-style rules clamp this upstream
export function viewOf(phiDeg) {
  const p = phiDeg * D2R, c = Math.cos(p), s = Math.sin(p);
  const side = c >= 0 ? 'R' : 'L';
  if (Math.abs(c) > 0.88) return { view: 'profile', side };
  if (s > 0) return { view: s > 0.9 ? 'front' : 'threequarter', side };
  return { view: s < -0.9 ? 'back' : 'threequarter_back', side };
}

// body lengths in cm from height and the character's proportions (7.5 heads adult default)
export function bodyOf(ch) {
  const H = ch.height_cm || 175, hh = ch.head_heights || 7.5, pr = ch.proportions || {};
  if (pr.thigh_cm && pr.upper_arm_cm) {           // lane B measured proportions
    const head = pr.head_cm, hip = pr.hip_height_cm, ankle = 0.045 * H, torso = pr.torso_cm;
    const legK = (hip - ankle) / (pr.thigh_cm + pr.shin_cm);
    return { H, head, hip, ankle, thigh: pr.thigh_cm * legK, shin: pr.shin_cm * legK, torso, neck: Math.max(1, H - hip - torso - head),
      uarm: pr.upper_arm_cm, farm: pr.forearm_cm, hand: pr.hand_cm, foot: Math.min(pr.foot_cm, 0.16 * H), toeBack: 0.045 * H,
      shoulderHalf: (pr.shoulder_width_cm || 0.23 * H) / 2, hipHalf: 0.065 * H, shoulderDrop: Math.max(0.02 * H, (hip + torso) - (pr.shoulder_height_cm || hip + torso)), radius: 0.13 * H, laneB: true };
  }
  const head = H / hh, hip = (pr.hip || 0.53) * H, ankle = 0.045 * H;
  const leg = hip - ankle;
  const torso = (pr.torso_len || 0.30) * H;                // hip joint to neck base
  return {
    H, head, hip, ankle, thigh: leg * 0.5, shin: leg * 0.5, torso, neck: Math.max(1, H - hip - torso - head),
    uarm: 0.172 * H, farm: 0.150 * H, hand: 0.105 * H, foot: 0.15 * H, toeBack: 0.045 * H,
    shoulderHalf: 0.115 * H, hipHalf: 0.065 * H, shoulderDrop: 0.035 * H, radius: 0.13 * H,
  };
}

// analytic two-bone IK in 3D. Returns {mid, end, ratio} where ratio = |target-root| / (a+b) (>1 means short)
export function ik2(root, target, a, b, pole) {
  const d = sub(target, root), dist = len(d), ratio = dist / (a + b);
  const L = Math.min(dist, (a + b) * 0.9995), dir = norm(d);
  let pl = sub(pole, mul(dir, dot(pole, dir)));
  if (len(pl) < 1e-6) pl = Math.abs(dir[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
  pl = norm(pl);
  const cosA = Math.max(-1, Math.min(1, (a * a + L * L - b * b) / (2 * a * L || 1)));
  const sinA = Math.sqrt(1 - cosA * cosA);
  const mid = add(root, add(mul(dir, a * cosA), mul(pl, a * sinA)));
  const end = add(root, mul(dir, L));
  return { mid, end, ratio };
}

// pose a body from a frame state. st = {X, Z, phi, pelvisY, lean, headPitch, feet:{L,R}, arms:{L,R}, bob, twist}
// arms[s] = {target:[X,Y,Z]|null, swing, bend}; feet[s] = {X, Z, lift, pitch}
export function poseBody(B, st) {
  const ax = axes(st.phi);
  const P = [st.X, st.pelvisY + (st.bob || 0), st.Z];
  const J = { pelvis: P, ax };
  const lean = (st.lean || 0) * D2R;
  const spine = norm(add(mul(ax.up, Math.cos(lean)), mul(ax.fwd, Math.sin(lean))));
  J.neck = add(P, mul(spine, B.torso));
  const hp = (st.headPitch || 0) * D2R;
  const hdir = norm(add(mul(ax.up, Math.cos(lean + hp)), mul(ax.fwd, Math.sin(lean + hp))));
  J.headBase = add(J.neck, mul(hdir, B.neck));
  J.headTop = add(J.headBase, mul(hdir, B.head));
  J.ratios = {};
  for (const s of ['L', 'R']) {
    const sg = s === 'L' ? 1 : -1;
    // legs
    const hip = add(P, mul(ax.left, sg * B.hipHalf));
    const f = st.feet[s];
    const fdir = [Math.cos(f.dir * D2R), 0, -Math.sin(f.dir * D2R)];
    const ankle = [f.X + fdir[0] * B.toeBack * 0.2, (f.Y || 0) + B.ankle + (f.lift || 0), f.Z + fdir[2] * B.toeBack * 0.2];
    const leg = ik2(hip, ankle, B.thigh, B.shin, add(ax.fwd, [0, 0.15, 0]));
    J['hip' + s] = hip; J['knee' + s] = leg.mid; J['ankle' + s] = leg.end; J.ratios['leg' + s] = leg.ratio;
    const pitch = (f.pitch || 0) * D2R;
    const toeDir = norm([fdir[0] * Math.cos(pitch), -Math.sin(pitch) * 0.6, fdir[2] * Math.cos(pitch)]);
    J['toe' + s] = add(leg.end, add(mul(toeDir, B.foot - B.toeBack), [0, -B.ankle * 0.8, 0]));
    J['heel' + s] = add(leg.end, add(mul(toeDir, -B.toeBack), [0, -B.ankle * 0.9, 0]));
    // arms
    const sh = add(add(J.neck, mul(spine, -B.shoulderDrop)), mul(ax.left, sg * B.shoulderHalf));
    J['shoulder' + s] = sh;
    const a = st.arms[s] || {};
    let target;
    if (a.target) target = a.target;
    else {
      const sw = (a.swing || 0) * D2R, bend = (a.bend ?? 12) * D2R, abd = (a.abduct ?? 6) * D2R;
      // forward kinematics in the sagittal plane, then IK onto the FK wrist so both paths share one solver
      const ud = norm(add(add(mul(spine, -Math.cos(sw)), mul(ax.fwd, Math.sin(sw))), mul(ax.left, sg * Math.sin(abd))));
      const el = add(sh, mul(ud, B.uarm));
      const fd = norm(add(mul(spine, -Math.cos(sw + bend)), mul(ax.fwd, Math.sin(sw + bend))));
      target = add(el, mul(fd, B.farm));
    }
    const pole = add(add(mul(ax.fwd, -0.7), [0, -0.6, 0]), mul(ax.left, sg * 0.5));
    const arm = ik2(sh, target, B.uarm, B.farm, pole);
    J['elbow' + s] = arm.mid; J['wrist' + s] = arm.end; J.ratios['arm' + s] = a.target ? arm.ratio : 0;
    const hd = a.handDir ? norm(a.handDir) : norm(sub(arm.end, arm.mid));
    J['tip' + s] = add(arm.end, mul(hd, B.hand));
  }
  return J;
}

// project every joint; returns {name: [x, y, s]} with s = px per cm at that depth
export function projectJoints(J, cam) {
  const out = {};
  for (const [k, v] of Object.entries(J)) if (Array.isArray(v) && v.length === 3 && typeof v[0] === 'number') out[k] = cam.project(v[0], v[1], v[2]);
  return out;
}

// local-body target helper (gestures): u forward, v up from the pelvis, w toward the named side
export function bodyPoint(st, B, u, v, w, side) {
  const ax = axes(st.phi), sg = side === 'L' ? 1 : -1;
  return add([st.X, st.pelvisY, st.Z], local(ax, u * B.H, v * B.H, sg * w * B.H));
}
