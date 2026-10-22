// The Creature Lab's physics: one creature, one world, simulated without drawing; runs in a Web Worker (or the page).
// A creature is the cut-out cards as rigid bodies (true length, average width, mass from painted area), hinged at the
// brads with anatomical limits and motors (muscles: torque capped by strength), springs across joints (tendons),
// driven by an oscillator per joint (Karl Sims' "brain", kept simple: offset + amplitude·sin(2πft + phase)) plus a
// balance reflex on the torso's tilt; in "track" mode the motors also chase a Crash Lab trial's joint angles.
/* global planck */
if (typeof importScripts === 'function' && typeof planck === 'undefined') importScripts('vendor/planck.min.js');

const SIM = { dt: 1 / 60, rec: 3 };   // step 60 Hz, record every 3rd step (20 fps)

function simulate(job, setup) {
  const { Vec2, Box, Edge, World, RevoluteJoint, DistanceJoint } = planck;
  const w = new World({ gravity: Vec2(0, -9.8) });
  const ground = w.createBody(); ground.createFixture(Edge(Vec2(-200, 0), Vec2(400, 0)), { friction: 1 });
  const B = {}, J = {};
  for (const s of job.segs) {   // a body at the segment's middle, along it
    const [x0, y0, x1, y1] = s.rest, a = Math.atan2(y1 - y0, x1 - x0);
    const b = w.createBody({ type: 'dynamic', position: Vec2((x0 + x1) / 2, (y0 + y1) / 2), angle: a, angularDamping: .2 });
    b.createFixture(Box(s.L / 2, Math.max(.01, s.W / 2)), { density: s.m / (s.L * s.W), friction: /foot/.test(s.k) ? 1.2 : .6, filterGroupIndex: -1 });
    B[s.k] = b;
  }
  const mass = job.segs.reduce((t, s) => t + s.m, 0), mscale = mass / 70;
  for (const s of job.segs) if (s.par) {   // hinge at the child's top end
    const lim = s.lim.map(d => d * Math.PI / 180);
    J[s.k] = w.createJoint(RevoluteJoint({ enableLimit: true, lowerAngle: lim[0], upperAngle: lim[1], enableMotor: true, maxMotorTorque: 1, motorSpeed: 0 },
      B[s.par], B[s.k], Vec2(s.rest[0], s.rest[1])));
  }
  for (const t of job.tendons || []) {
    if (!(t.hz > .05) || !B[t.a] || !B[t.b]) continue;
    const pa = B[t.a].getWorldPoint(Vec2(t.pa[0], t.pa[1])), pb = B[t.b].getWorldPoint(Vec2(t.pb[0], t.pb[1]));
    const dj = w.createJoint(DistanceJoint({ frequencyHz: t.hz, dampingRatio: .4 }, B[t.a], B[t.b], pa, pb));
    dj.setLength(dj.getLength() * t.len);
  }
  const g = job.brain, T = setup.T, steps = Math.round(T / SIM.dt), nb = job.segs.length;
  const rec = new Float32Array(Math.ceil(steps / SIM.rec) * nb * 3);
  const head0 = B.head ? B.head.getPosition().y : 1.5, x0 = B.pelvis.getPosition().x;
  let up = 0, err = 0, en = 0, fell = -1, r = 0, energy = 0;
  for (let i = 0; i < steps; i++) {
    const t = i * SIM.dt, tilt = B.torso ? B.torso.getAngle() - Math.PI / 2 : 0;
    const tf = setup.track && setup.track.n ? Math.floor(t * setup.track.fps) % setup.track.n : -1;
    for (const s of job.segs) {
      const j = J[s.k]; if (!j) continue;
      const c = g.joints[s.k] || {};
      let target = (c.off || 0) + (c.amp || 0) * Math.sin(2 * Math.PI * g.f * t + (c.ph || 0)) + (c.kb || 0) * tilt;
      if (tf >= 0 && setup.track.a[s.k]) { const tt = setup.track.a[s.k][tf]; target += tt; err += Math.abs(j.getJointAngle() - tt); en++; }
      const lim = s.lim; target = Math.max(lim[0] * Math.PI / 180, Math.min(lim[1] * Math.PI / 180, target));
      j.setMaxMotorTorque(s.torque * (c.str ?? 1) * mscale);
      j.setMotorSpeed(Math.max(-12, Math.min(12, 10 * (target - j.getJointAngle()))));
      energy += Math.abs(j.getMotorTorque(1 / SIM.dt) * j.getJointSpeed()) * SIM.dt;
    }
    w.step(SIM.dt, 8, 3);
    const hy = B.head ? B.head.getPosition().y : B.torso.getPosition().y;
    if (fell < 0 && hy < .55 * head0) fell = t;
    if (fell < 0) up += SIM.dt;
    if (i % SIM.rec === 0) for (const s of job.segs) { const b = B[s.k], p = b.getPosition(); rec[r++] = p.x; rec[r++] = p.y; rec[r++] = b.getAngle(); }
    if (fell >= 0 && t - fell > 1.5) break;   // a second and a half on the floor is enough to see it fall
  }
  const dist = B.pelvis.getPosition().x - x0, mode = setup.mode;
  let fit;
  if (mode === 'walk') fit = (fell < 0 ? dist : dist * .5) + .15 * up - energy / (mass * 400);
  else if (mode === 'stand') fit = up - .5 * Math.abs(dist) - energy / (mass * 800);
  else fit = up * .6 - (en ? err / en : 1) * 4 + (setup.track && setup.track.dist ? Math.min(dist, setup.track.dist) / setup.track.dist : 0);
  return { fit, dist, up, fell, err: en ? err / en : null, frames: r / (nb * 3), rec: rec.slice(0, r) };
}

if (typeof importScripts === 'function') {
  let setup = null;
  onmessage = e => {
    const m = e.data;
    if (m.setup) { setup = m.setup; return; }
    try { const out = simulate(m.job, setup); postMessage({ id: m.id, ...out }, [out.rec.buffer]); }
    catch (err) { postMessage({ id: m.id, fit: -1e9, error: String(err), rec: new Float32Array(0), frames: 0 }); }
  };
}
