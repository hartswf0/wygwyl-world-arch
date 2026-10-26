/* WYGWYL Upgraded Animation Engine v2 (anim2.js)
   Combines:
   1. 4-Phase Stride-Locked Replacement Pose Cycle (ContactA -> PassA -> ContactB -> PassB)
      with side-on view preference (prof/q3 over front), opposite leading legs, and velocity-locked cadence.
   2. Split-Body Scissor Articulation for sparse-drawing characters so 37/37 characters step with alternating legs (0 gliding).
   3. 15-Bone Articulated Cut-Out IK Rig Mode (from crash_lab_catalog.json) with cuff-tuck wrist/ankle joins and hybrid action swaps.
   4. Jump & Double-Jump parabolic physics, velocity lean, landing squash/settle, and spoken-word lip/breath cadence.
   Zero browser dependencies in plan() / Actor.step() / Actor.pick() so it can be tested numerically in Node.
*/
'use strict';

const WY = (function(){
  const LABEL = {
    dance:'Dance', sit:'Sit', kneel:'Kneel', crouch:'Crouch',
    lean:'Lean', lunge:'Lunge', lie:'Lie down', fall:'Fall',
    run:'Run', fly:'Fly', float:'Float', throw:'Throw',
    reach:'Reach', point:'Point'
  };
  const GROUND_ONLY = new Set(['lie','fall','sit','kneel','crouch','float','fly']);

  function viewPenalty(v, forWalk){
    if (forWalk){
      if (v === 'prof') return 0.0;
      if (v === 'q3') return 0.35;
      if (v === 'front') return 2.8;
      return 4.0;
    }
    if (v === 'q3') return 0.0;
    if (v === 'front') return 0.4;
    if (v === 'prof') return 1.2;
    return 3.5;
  }

  function neutralScore(d){
    return (d.cls === 'stand' ? 0 : 2.2)
      + (d.arm >= 45 ? 1.8 : 0)
      + (d.spread >= 22 ? 1.8 : 0)
      + viewPenalty(d.view, false)
      + (d.is_fragment ? 50 : 0);
  }

  function strideScore(d){
    const spread = d.spread || 0;
    const goodSpread = (spread >= 24 && spread <= 68) ? 0 : Math.abs(spread - 40) * 0.06;
    const walkBonus = d.cls === 'walk' ? -1.5 : (d.cls === 'run' || d.cls === 'lunge' ? -0.4 : 0);
    const armPenalty = d.arm >= 85 ? 1.2 : 0;
    return viewPenalty(d.view, true) + goodSpread + walkBonus + armPenalty + (d.is_fragment ? 50 : 0);
  }

  function plan(ch){
    const raw = (ch.draws || []).map((d, i) => Object.assign({ i }, d));
    const D = raw.filter(d => !d.is_fragment);
    const pool = D.length ? D : raw;

    // 1. Pick best neutral idle pose (prefer q3/front standing, low spread)
    const idleCands = pool
      .filter(d => !GROUND_ONLY.has(d.cls) && d.view !== 'back' && d.view !== 'back3q')
      .sort((a, b) => neutralScore(a) - neutralScore(b));
    const idle = idleCands[0] || pool[0];

    // 2. Pick best side-on passing pose (prefer prof/q3 upright, narrower spread than contact)
    const passCands = pool
      .filter(d => !GROUND_ONLY.has(d.cls) && d.view !== 'back' && d.view !== 'back3q')
      .sort((a, b) => {
        const va = viewPenalty(a.view, true) + Math.abs((a.spread || 12) - 14) * 0.08 + (a.arm >= 75 ? 1.5 : 0);
        const vb = viewPenalty(b.view, true) + Math.abs((b.spread || 12) - 14) * 0.08 + (b.arm >= 75 ? 1.5 : 0);
        return va - vb;
      });

    // 3. Pick side-on stride contact poses with opposite leading legs
    const uprightSide = pool
      .filter(d => !GROUND_ONLY.has(d.cls) && (d.view === 'prof' || d.view === 'q3'))
      .sort((a, b) => strideScore(a) - strideScore(b));
    const hasNonBackUpright = pool.some(d => !GROUND_ONLY.has(d.cls) && d.view !== 'back' && d.view !== 'back3q');
    const strideCands = pool
      .filter(d => !GROUND_ONLY.has(d.cls) && (!hasNonBackUpright || (d.view !== 'back' && d.view !== 'back3q')) && ((d.spread || 0) >= 18 || d.cls === 'walk'))
      .sort((a, b) => strideScore(a) - strideScore(b));

    // Always prefer side-on (prof or q3) upright poses over front-facing poses for side-scrolling walk
    const sideStrides = strideCands.filter(d => d.view === 'prof' || d.view === 'q3');
    const activeStrides = sideStrides.length >= 1 ? sideStrides : (uprightSide.length >= 1 ? uprightSide : strideCands);

    let contactA = activeStrides[0] || idle;
    let leadA = contactA.lead_leg || 1;
    let contactB = activeStrides.find(d => d.i !== contactA.i && (d.lead_leg || -leadA) !== leadA)
      || activeStrides.find(d => d.i !== contactA.i)
      || strideCands.find(d => d.i !== contactA.i)
      || idle;

    // Pick passing poses guaranteed distinct from contactA and contactB when possible
    let passA = passCands.find(d => d.i !== contactA.i && d.i !== contactB.i)
      || passCands.find(d => d.i !== contactA.i)
      || idle;
    let passB = passCands.find(d => d.i !== contactB.i && d.i !== contactA.i && d.i !== passA.i)
      || passA;

    const avgStrideCm = Math.max(
      28,
      Math.min(
        46,
        ((contactA.stride_cm || 36) + (contactB.stride_cm || 36)) * 0.5
      )
    );

    const hasDistinctContacts = contactA.i !== contactB.i;
    const walkMode = hasDistinctContacts ? 'step_4pose' : 'scissor_step';

    // 4-pose walk cycle: ContactA (L) -> PassA -> ContactB (R) -> PassB
    // Each full stride (A -> passA) advances the body by avgStrideCm
    const baseSpeedCmS = 132; // natural walking speed in cm/s
    const halfStrideHoldMs = Math.round((avgStrideCm / baseSpeedCmS) * 1000 * 0.5); // ~136ms per phase

    const walk = {
      mode: walkMode,
      stride_cm: avgStrideCm,
      base_speed_cm_s: baseSpeedCmS,
      frames: [
        { d: contactA, phase: 'contactA', lead: +1, scissor: +1.0, dy_cm: -0.6, hold: halfStrideHoldMs },
        { d: passA,    phase: 'passA',    lead: +0.3, scissor: -0.35, dy_cm: -3.2, hold: halfStrideHoldMs },
        { d: contactB, phase: 'contactB', lead: -1, scissor: -1.0, dy_cm: -0.6, hold: halfStrideHoldMs },
        { d: passB,    phase: 'passB',    lead: -0.3, scissor: +0.35, dy_cm: -3.2, hold: halfStrideHoldMs }
      ]
    };

    // Turnaround ring
    const bestFor = v => pool.filter(d => d.view === v && !GROUND_ONLY.has(d.cls)).sort((a, b) => neutralScore(a) - neutralScore(b))[0];
    const ring = [['q3',false],['prof',false],['back3q',false],['back',false],['back3q',true],['prof',true],['q3',true],['front',false]];
    const have = new Set(pool.map(d => d.view));
    let turn = null;
    if (have.size >= 2){
      turn = [];
      let last = idle;
      for (const [v, m] of ring){
        const d = bestFor(v) || last;
        last = d;
        turn.push({ d, hold: 145, mirror: m });
      }
      turn.push({ d: idle, hold: 190 });
    }

    // Action poses grouped by class
    const poses = [], byCls = {};
    pool.forEach(d => {
      if (d.cls !== 'stand' && d.cls !== 'walk'){
        (byCls[d.cls] = byCls[d.cls] || []).push(d);
      }
    });
    for (const [c, list] of Object.entries(byCls)){
      poses.push({ cls: c, label: LABEL[c] || ('Pose: ' + c), frames: list.map(d => ({ d, hold: 480 })) });
    }
    const reach = pool.filter(d => d.arm >= 55 && (d.cls === 'stand' || d.cls === 'walk' || d.cls === 'dance') && !(byCls[d.cls] || []).includes(d));
    if (reach.length){
      poses.push({ cls: 'reach', label: 'Reach', frames: reach.map(d => ({ d, hold: 480 })) });
    }

    // Best jump / aerial pose
    const jumpPose = pool.find(d => d.cls === 'fly' || d.cls === 'float' || d.cls === 'lunge')
      || reach[0]
      || contactA;
    // Best crouch / land pose
    const crouchPose = pool.find(d => d.cls === 'crouch' || d.cls === 'kneel' || d.cls === 'sit')
      || passA;

    return { idle, walk, turn, poses, jumpPose, crouchPose, all: pool };
  }

  /* 2-Bone Analytical IK for 15-Bone Rig Mode */
  function solveIK2D(sx, sy, tx, ty, L1, L2, bendDir){
    const dx = tx - sx, dy = ty - sy;
    const dist = Math.max(1e-3, Math.min(L1 + L2 - 1e-3, Math.hypot(dx, dy)));
    const cosKnee = Math.max(-1, Math.min(1, (L1*L1 + L2*L2 - dist*dist) / (2*L1*L2)));
    const kneeAngle = Math.PI - Math.acos(cosKnee);
    const baseAngle = Math.atan2(dy, dx);
    const cosAlpha = Math.max(-1, Math.min(1, (L1*L1 + dist*dist - L2*L2) / (2*L1*dist)));
    const alpha = Math.acos(cosAlpha);
    const theta1 = baseAngle - (bendDir || 1) * alpha;
    const jx = sx + Math.cos(theta1) * L1;
    const jy = sy + Math.sin(theta1) * L1;
    return { jx, jy, ex: jx + Math.cos(theta1 + (bendDir || 1) * kneeAngle) * L2, ey: jy + Math.sin(theta1 + (bendDir || 1) * kneeAngle) * L2 };
  }

  function Actor(ch, imgs, rigSpec, rigImgs){
    this.ch = ch;
    this.imgs = imgs || [];
    this.rigSpec = rigSpec || null;
    this.rigImgs = rigImgs || {};
    this.P = plan(ch);
    this.x = 0;
    this.dir = 1;
    this.vx = 0; // stage px/s
    this.vy = 0; // vertical velocity in cm/s
    this.airY = 0; // height above floor in cm
    this.jumpsLeft = 2;
    this.landT = -1e9;
    this.anim = { kind: 'idle' };
    this.t0 = 0;
    this.shown = this.P.idle ? this.P.idle.i : 0;
    this.shownPhase = 'idle';
    this.swapT = -1e9;
    this.walkDistCm = 0;
    this.leanRad = 0;
    this.engineMode = 'hybrid'; // 'hybrid' | 'pose_v2' | 'rig_15bone'
    this.speaking = false;
  }

  Actor.prototype.set = function(a, now){
    const t = now !== undefined ? now : (typeof performance !== 'undefined' ? performance.now() : 0);
    this.anim = a;
    this.t0 = t;
  };

  Actor.prototype.jump = function(now){
    const t = now !== undefined ? now : (typeof performance !== 'undefined' ? performance.now() : 0);
    if (this.jumpsLeft > 0){
      this.vy = this.jumpsLeft === 2 ? 205 : 175; // cm/s upward impulse
      this.jumpsLeft--;
      this.swapT = t;
      return true;
    }
    return false;
  };

  Actor.prototype.triggerPoseByCls = function(cls, now){
    const t = now !== undefined ? now : (typeof performance !== 'undefined' ? performance.now() : 0);
    const found = this.P.poses.find(p => p.cls === cls || p.label.toLowerCase() === cls.toLowerCase());
    if (found){
      this.set({ kind: 'pose', p: found, cls: found.cls }, t);
      return true;
    }
    // Even if character lacks a dedicated drawing for cls, set synthetic pose state!
    this.set({ kind: 'synth_pose', cls: cls, label: LABEL[cls] || cls }, t);
    return true;
  };

  Actor.prototype.buttons = function(){
    const P = this.P, out = [
      { label: 'Idle', fn: () => this.set({ kind: 'idle' }) },
      { label: '▲ Jump', fn: () => this.jump() }
    ];
    if (P.turn) out.push({ label: 'Turn 360°', fn: () => this.set({ kind: 'turn' }) });
    // Standard poem action beats always available on every character (either via painted pose or articulated rig!)
    const coreCls = ['dance', 'sit', 'kneel', 'crouch', 'fall', 'reach'];
    const added = new Set();
    P.poses.forEach(p => {
      added.add(p.cls);
      out.push({ label: p.label, cls: p.cls, fn: () => {
        if (this.anim.p === p) this.set({ kind: 'idle' });
        else this.set({ kind: 'pose', p, cls: p.cls });
      }});
    });
    coreCls.forEach(c => {
      if (!added.has(c)){
        out.push({ label: LABEL[c], cls: c, fn: () => {
          if (this.anim.cls === c) this.set({ kind: 'idle' });
          else this.triggerPoseByCls(c);
        }});
      }
    });
    out.push({
      label: 'Next painting',
      fn: () => this.set({ kind: 'one', k: ((this.anim.k === undefined ? -1 : this.anim.k) + 1) % P.all.length })
    });
    return out;
  };

  /* Advance physics (stride distance, jump arc, lean, landing settle) */
  Actor.prototype.stepPhysics = function(dtSec, moveInput, ppc, fw, now){
    const t = now !== undefined ? now : (typeof performance !== 'undefined' ? performance.now() : 0);
    const speedCmS = this.P.walk.base_speed_cm_s || 132;
    const eff = Math.abs(moveInput) < 0.12 ? 0 : Math.max(-1, Math.min(1, moveInput));

    if (eff !== 0){
      this.dir = eff > 0 ? 1 : -1;
      const dxCm = eff * speedCmS * dtSec;
      this.walkDistCm += Math.abs(dxCm);
      this.x = Math.max(40, Math.min((fw || 1280) - 40, this.x + dxCm * (ppc || 1)));
    }
    const targetLean = eff * 0.085; // ~5 deg lean into movement
    this.leanRad += (targetLean - this.leanRad) * Math.min(1, dtSec * 12);

    // Jump & gravity in cm
    if (this.airY > 0 || this.vy !== 0){
      this.airY += this.vy * dtSec;
      this.vy -= 480 * dtSec; // gravity cm/s^2
      if (this.airY <= 0){
        this.airY = 0;
        this.vy = 0;
        this.jumpsLeft = 2;
        this.landT = t;
        this.swapT = t;
      }
    }
  };

  /* Pick current frame state { d, phase, lead, scissor, dy, breathe, squashX, squashY, lean, airY } */
  Actor.prototype.pick = function(now, moving){
    const a = this.anim, P = this.P, dt = Math.max(0, now - this.t0);

    // Compute landing / swap settle squash
    const landAge = now - this.landT;
    const swapAge = now - this.swapT;
    let squashX = 1.0, squashY = 1.0;
    if (landAge >= 0 && landAge < 180){
      const k = Math.sin((1 - landAge / 180) * Math.PI * 0.5);
      squashX = 1 + 0.16 * k;
      squashY = 1 - 0.15 * k;
    } else if (swapAge >= 0 && swapAge < 130){
      const k = 1 - swapAge / 130;
      squashX = 1 + 0.045 * k;
      squashY = 1 - 0.045 * k;
    }

    // Mid-air jump state overrides ground walk
    if (this.airY > 1.5){
      const d = this.vy > -30 ? P.jumpPose : P.crouchPose;
      return {
        d,
        phase: this.vy > 0 ? 'jump_rise' : 'jump_fall',
        lead: this.vy > 0 ? 1 : -1,
        scissor: this.vy > 0 ? 0.85 : -0.55,
         extra: false,
        dy: -this.airY,
        breathe: 0,
        squashX: this.vy > 40 ? 0.93 : 1.04,
        squashY: this.vy > 40 ? 1.08 : 0.96,
        lean: this.leanRad * 1.35
      };
    }

    if (moving && (a.kind === 'idle' || a.kind === 'one')){
      this.set({ kind: 'walk' }, now);
      return this.pick(now, moving);
    }
    if (!moving && a.kind === 'walk'){
      this.set({ kind: 'idle' }, now);
      return this.pick(now, moving);
    }

    if (a.kind === 'walk'){
      // Lock walk cycle phase directly to distance walked (walkDistCm) so stride never slips!
      const strideCm = P.walk.stride_cm || 36;
      const fullCycleCm = strideCm * 2; // 2 steps (L + R) per full 4-frame cycle
      const distProgress = this.walkDistCm > 0 ? (this.walkDistCm % fullCycleCm) / fullCycleCm : ((dt % 560) / 560);
      const idx = Math.min(3, Math.floor(distProgress * 4));
      const subT = (distProgress * 4) - idx;
      const f = P.walk.frames[idx];
      const nextF = P.walk.frames[(idx + 1) % 4];
      const smoothScissor = f.scissor + (nextF.scissor - f.scissor) * (subT * subT * (3 - 2 * subT));
      const smoothDy = f.dy_cm + (nextF.dy_cm - f.dy_cm) * Math.sin(subT * Math.PI * 0.5);

      if (f.phase !== this.shownPhase){
        this.shownPhase = f.phase;
        this.shown = f.d.i;
        this.swapT = now;
      }
      return {
        d: f.d,
        phase: f.phase,
        lead: f.lead,
        scissor: smoothScissor,
        extra: false,
        dy: smoothDy,
        breathe: 0,
        squashX,
        squashY,
        lean: this.leanRad
      };
    }

    if (a.kind === 'turn'){
      let t = dt, f = null;
      for (const x of P.turn){
        if (t < x.hold){ f = x; break; }
        t -= x.hold;
      }
      if (!f){
        this.set({ kind: 'idle' }, now);
        return this.pick(now, moving);
      }
      return { d: f.d, phase: 'turn', lead: 0, scissor: 0, extra: !!f.mirror, dy: 0, squashX, squashY, lean: 0 };
    }

    if (a.kind === 'pose'){
      const fr = a.p.frames, k = Math.floor((dt % (fr.length * 480)) / 480);
      return {
        d: fr[k].d,
        phase: 'pose:' + (a.cls || a.p.label),
        poseCls: a.cls || a.p.cls,
        lead: 0,
        scissor: Math.sin(dt / 240) * 0.35,
        extra: false,
        dy: (a.cls === 'dance' ? -Math.abs(Math.sin(dt / 190)) * 3.5 : 0),
        squashX,
        squashY,
        lean: a.cls === 'dance' ? Math.sin(dt / 380) * 0.09 : 0
      };
    }

    if (a.kind === 'synth_pose'){
      const cls = a.cls;
      let dy = 0, sqX = squashX, sqY = squashY, lean = 0, sc = 0;
      if (cls === 'sit' || cls === 'crouch' || cls === 'kneel'){
        sqX = 1.12; sqY = 0.74; dy = 4.0; sc = 0.65;
      } else if (cls === 'fall' || cls === 'lie'){
        lean = 1.25; dy = 12.0; sqX = 1.08; sqY = 0.88;
      } else if (cls === 'dance'){
        dy = -Math.abs(Math.sin(dt / 180)) * 4.5;
        lean = Math.sin(dt / 320) * 0.14;
        sc = Math.sin(dt / 180) * 0.9;
      } else if (cls === 'reach'){
        dy = -2.5; sqY = 1.07; lean = 0.12; sc = 0.5;
      }
      return {
        d: P.idle,
        phase: 'synth:' + cls,
        poseCls: cls,
        lead: 0,
        scissor: sc,
        extra: false,
        dy,
        squashX: sqX,
        squashY: sqY,
        lean
      };
    }

    if (a.kind === 'one'){
      return { d: P.all[a.k] || P.idle, phase: 'one', lead: 0, scissor: 0, extra: false, dy: 0, squashX, squashY, lean: 0 };
    }

    return {
      d: P.idle,
      phase: 'idle',
      lead: 0,
      scissor: 0,
      extra: false,
      dy: 0,
      breathe: Math.sin(dt / 950) * 0.008 + (this.speaking ? Math.sin(dt / 110) * 0.012 : 0),
      squashX,
      squashY,
      lean: this.leanRad * 0.4
    };
  };

  /* Draw character at stage pixel (sx, floorY); ppc is stage px per cm */
  Actor.prototype.draw = function(ctx, c, sx, floorY, ppc, now, showRigOverlay){
    const d = c.d;
    if (!d) return;
    if (d.i !== this.shown){
      this.shown = d.i;
      this.swapT = now;
    }

    // If in 15-Bone Rig Mode (or Hybrid Walk when 15-bone images are loaded), allow 15-bone rendering
    if (this.engineMode === 'rig_15bone' && this.rigSpec && Object.keys(this.rigImgs).length >= 6){
      this.draw15BoneRig(ctx, c, sx, floorY, ppc, now, true);
      return;
    }

    const img = this.imgs[d.i];
    if (!img) return;

    const hCm = this.ch.height_cm || 170;
    const s = ((0.70 * hCm) / Math.max(140, d.body_px || d.h)) * ppc;
    const flip = (this.dir !== (d.right ? 1 : -1)) !== !!c.extra;
    const age = now - this.swapT;
    const dip = age >= 0 && age < 140 ? (1 - age / 140) * 0.028 * d.h * s : 0;

    ctx.save();
    ctx.translate(sx, floorY + dip + (c.dy || 0) * ppc);
    if (flip) ctx.scale(-1, 1);
    if (c.lean) ctx.rotate(c.lean);
    ctx.scale(c.squashX || 1, (c.squashY || 1) * (1 + (c.breathe || 0)));

    ctx.shadowColor = 'rgba(0,0,0,.55)';
    ctx.shadowBlur = 12;
    ctx.shadowOffsetY = 3;

    const wScaled = d.w * s;
    const hScaled = d.h * s;
    const axScaled = d.ax * s;

    // Check if we should apply Split-Body Scissor Leg Articulation
    // (Used when walking in scissor_step mode OR to add live leg-swing & knee articulation!)
    const useScissor = (this.anim.kind === 'walk' || c.phase === 'jump_rise' || c.phase === 'jump_fall' || (c.scissor && Math.abs(c.scissor) > 0.05))
      && (this.P.walk.mode === 'scissor_step' || this.engineMode === 'hybrid' || Math.abs(c.scissor || 0) > 0.15);

    if (useScissor){
      const hipRatio = d.hip_y_ratio || 0.54;
      const hipYImg = Math.round(d.h * hipRatio);
      const legHImg = d.h - hipYImg;
      const hipYScaled = -hScaled + hipYImg * s;
      const legHScaled = legHImg * s;
      const scissorAmt = c.scissor || 0;

      // 1. Trailing Leg Slice (slightly darkened for 2.5D depth)
      ctx.save();
      ctx.translate(0, hipYScaled);
      ctx.rotate(-scissorAmt * 0.24);
      ctx.filter = 'brightness(0.84)';
      ctx.drawImage(
        img,
        0, hipYImg, d.w, legHImg,
        -axScaled, 0, wScaled, legHScaled * (1 - Math.max(0, scissorAmt) * 0.04)
      );
      ctx.restore();

      // 2. Leading Leg Slice (planted / reaching)
      ctx.save();
      ctx.translate(0, hipYScaled);
      ctx.rotate(scissorAmt * 0.26);
      ctx.drawImage(
        img,
        0, hipYImg, d.w, legHImg,
        -axScaled, 0, wScaled, legHScaled
      );
      ctx.restore();

      // 3. Upper Torso & Head Slice (with slight overlap at hip seam and counter-pendulum)
      const torsoHImg = Math.min(d.h, Math.round(d.h * (hipRatio + 0.05)));
      const torsoHScaled = torsoHImg * s;
      ctx.save();
      ctx.translate(0, hipYScaled);
      ctx.rotate(scissorAmt * 0.055);
      ctx.drawImage(
        img,
        0, 0, d.w, torsoHImg,
        -axScaled, -hipYImg * s, wScaled, torsoHScaled
      );
      ctx.restore();
    } else {
      ctx.drawImage(img, -axScaled, -hScaled, wScaled, hScaled);
    }

    // Optional Bolas IK & Brass-Pivot Telemetry Overlay in Hybrid Mode
    if (showRigOverlay){
      const hipY = -hScaled * 0.46;
      const shY = -hScaled * 0.76;
      const headY = -hScaled * 0.88;
      const sc = c.scissor || 0;
      const lFootX = sc * 18 * ppc, lFootY = -Math.max(0, -sc) * 6 * ppc;
      const rFootX = -sc * 18 * ppc, rFootY = -Math.max(0, sc) * 6 * ppc;
      const ikL = solveIK2D(0, hipY, lFootX, lFootY, hScaled*0.23, hScaled*0.23, 1);
      const ikR = solveIK2D(0, hipY, rFootX, rFootY, hScaled*0.23, hScaled*0.23, 1);

      ctx.strokeStyle = 'rgba(0, 229, 255, 0.85)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, headY); ctx.lineTo(0, hipY);
      ctx.moveTo(0, hipY); ctx.lineTo(ikL.jx, ikL.jy); ctx.lineTo(ikL.ex, ikL.ey);
      ctx.moveTo(0, hipY); ctx.lineTo(ikR.jx, ikR.jy); ctx.lineTo(ikR.ex, ikR.ey);
      ctx.stroke();

      [ [0, headY], [0, shY], [0, hipY], [ikL.jx, ikL.jy], [ikR.jx, ikR.jy], [ikL.ex, ikL.ey], [ikR.ex, ikR.ey] ].forEach(([jx, jy], idx) => {
        ctx.fillStyle = idx >= 5 ? '#4ee88a' : '#f5c64e';
        ctx.beginPath(); ctx.arc(jx, jy, 3.5, 0, Math.PI * 2); ctx.fill();
      });
    }

    ctx.restore();
  };

  /* 15-Bone Cut-Out Articulated Rig Renderer */
  Actor.prototype.draw15BoneRig = function(ctx, c, sx, floorY, ppc, now, showOverlay){
    const hCm = this.ch.height_cm || 170;
    const figH = hCm * ppc;
    const sc = c.scissor || 0;
    const hipY = -figH * 0.48;
    const shY = -figH * 0.78;
    const headY = -figH * 0.86;
    const thighL = figH * 0.24, shinL = figH * 0.24;
    const uarmL = figH * 0.18, farmL = figH * 0.17;

    const lFootX = sc * 19 * ppc, lFootY = -Math.max(0, -sc) * 7 * ppc;
    const rFootX = -sc * 19 * ppc, rFootY = -Math.max(0, sc) * 7 * ppc;
    const legL = solveIK2D(0, hipY, lFootX, lFootY, thighL, shinL, 1);
    const legR = solveIK2D(0, hipY, rFootX, rFootY, thighL, shinL, 1);

    const lHandX = -sc * 15 * ppc, lHandY = hipY + figH * 0.04;
    const rHandX = sc * 15 * ppc, rHandY = hipY + figH * 0.04;
    const armL = solveIK2D(0, shY, lHandX, lHandY, uarmL, farmL, -1);
    const armR = solveIK2D(0, shY, rHandX, rHandY, uarmL, farmL, -1);

    ctx.save();
    ctx.translate(sx, floorY + (c.dy || 0) * ppc);
    if (this.dir < 0) ctx.scale(-1, 1);
    if (c.lean) ctx.rotate(c.lean);
    ctx.scale(c.squashX || 1, c.squashY || 1);

    function drawBoneCard(slotImg, slotSpec, ax, ay, bx, by, cuffClip){
      if (!slotImg || !slotSpec) return;
      const pA = slotSpec.pivot_A || [0.5, 0.15];
      const sB = slotSpec.socket_B || [0.5, 0.85];
      const cardDx = (sB[0] - pA[0]) * slotImg.width;
      const cardDy = (sB[1] - pA[1]) * slotImg.height;
      const cardSpan = Math.max(10, Math.hypot(cardDx, cardDy));
      const worldSpan = Math.max(4, Math.hypot(bx - ax, by - ay));
      const scale = worldSpan / cardSpan;
      const worldAng = Math.atan2(by - ay, bx - ax);
      const cardAng = Math.atan2(cardDy, cardDx);
      ctx.save();
      ctx.translate(ax, ay);
      ctx.rotate(worldAng - cardAng);
      const clipH = cuffClip ? slotImg.height * cuffClip : slotImg.height;
      ctx.drawImage(
        slotImg,
        0, 0, slotImg.width, clipH,
        -pA[0] * slotImg.width * scale, -pA[1] * slotImg.height * scale,
        slotImg.width * scale, clipH * scale
      );
      ctx.restore();
    }

    const S = (this.rigSpec && this.rigSpec.slots) || {};
    const I = this.rigImgs;
    // Back limbs
    drawBoneCard(I.uarm_L, S.uarm_L, 0, shY, armL.jx, armL.jy);
    drawBoneCard(I.hand_L, S.hand_L, armL.ex, armL.ey, armL.ex + 4*ppc, armL.ey + 9*ppc);
    drawBoneCard(I.farm_L, S.farm_L, armL.jx, armL.jy, armL.ex, armL.ey, 0.84);
    drawBoneCard(I.thigh_L, S.thigh_L, 0, hipY, legL.jx, legL.jy);
    drawBoneCard(I.foot_L, S.foot_L, legL.ex, legL.ey, legL.ex + 10*ppc, legL.ey);
    drawBoneCard(I.shin_L, S.shin_L, legL.jx, legL.jy, legL.ex, legL.ey, 0.86);

    // Pelvis & Torso & Head
    drawBoneCard(I.pelvis, S.pelvis, 0, hipY - figH*0.04, 0, hipY + figH*0.06);
    drawBoneCard(I.torso, S.torso, 0, shY, 0, hipY);
    drawBoneCard(I.head, S.head, 0, headY, 0, headY - figH*0.13);

    // Front limbs (with cuff-tuck: foot/hand drawn before shin/forearm!)
    drawBoneCard(I.thigh_R, S.thigh_R, 0, hipY, legR.jx, legR.jy);
    drawBoneCard(I.foot_R, S.foot_R, legR.ex, legR.ey, legR.ex + 10*ppc, legR.ey);
    drawBoneCard(I.shin_R, S.shin_R, legR.jx, legR.jy, legR.ex, legR.ey, 0.86);
    drawBoneCard(I.uarm_R, S.uarm_R, 0, shY, armR.jx, armR.jy);
    drawBoneCard(I.hand_R, S.hand_R, armR.ex, armR.ey, armR.ex + 4*ppc, armR.ey + 9*ppc);
    drawBoneCard(I.farm_R, S.farm_R, armR.jx, armR.jy, armR.ex, armR.ey, 0.84);

    if (showOverlay){
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.9)';
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.moveTo(0, headY); ctx.lineTo(0, hipY);
      ctx.moveTo(0, hipY); ctx.lineTo(legL.jx, legL.jy); ctx.lineTo(legL.ex, legL.ey);
      ctx.moveTo(0, hipY); ctx.lineTo(legR.jx, legR.jy); ctx.lineTo(legR.ex, legR.ey);
      ctx.stroke();
    }
    ctx.restore();
  };

  function loadImg(src){
    return new Promise(r => {
      const i = new Image();
      i.onload = () => r(i);
      i.onerror = () => r(null);
      i.src = src;
    });
  }

  return { plan, Actor, loadImg, neutral: neutralScore, strideScore, solveIK2D };
})();

if (typeof module !== 'undefined' && module.exports){
  module.exports = WY;
}
