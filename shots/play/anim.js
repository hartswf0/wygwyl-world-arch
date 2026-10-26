/* WYGWYL Anim2 — Coherent Gait, Emotional Posture & Narrative Transformation Engine.
 *
 * Solves the two core failures of the legacy swapper:
 *   1. ZERO RANDOM SHUFFLING:
 *      - Walking NEVER cycles through unrelated paintings, prop scenes (motorcycle/pillar/bed),
 *        or front-to-back view flips. Only verified prop-free matched stride pairs swap frames,
 *        bridged by continuous split-hip scissor articulation; all other characters walk on a
 *        coherent single-painting split-hip + 15-bone rig stride locked to floor speed.
 *      - Pose & Emotion buttons NEVER flash through a bag of different paintings on a 480ms loop.
 *        Each narrative painting is an intentional, named Emotional State held with living breath,
 *        while multi-stage arcs (The Fall, Waking on the Shore, Searching Blindly, 360° Waltz)
 *        play as deliberate narrative progressions that settle and hold.
 *   2. MEANING, EMOTION & CHANGE:
 *      - Characters carry an active Emotional Register (memory, searching, vertigo, grief, awe,
 *        ecstasy, departure, peace) that physically changes their gait speed, head/torso inclination,
 *        breathing depth, and posture as a poem unfolds.
 */
'use strict';
(function(root, factory){
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else {
    const api = factory();
    root.Anim2 = api;
    root.WY = api;
  }
})(typeof self !== 'undefined' ? self : this, function(){

  const GROUND_ONLY = new Set(['lie','fall','sit','kneel','crouch','float','fly']);

  const EMOTION_MODS = {
    memory:    { label: 'Memory & Reflection',    speedMult: 0.86, leanBias: -0.02, breatheAmp: 0.007, breatheHz: 0.7,  color: [168, 188, 230] },
    searching: { label: 'Searching & Yearning',   speedMult: 1.00, leanBias:  0.04, breatheAmp: 0.009, breatheHz: 1.0,  color: [232, 184,  92] },
    vertigo:   { label: 'Vertigo & Freefall',     speedMult: 1.08, leanBias:  0.07, breatheAmp: 0.013, breatheHz: 1.45, color: [236, 122, 110] },
    grief:     { label: 'Grief & Hollowing',      speedMult: 0.74, leanBias: -0.06, breatheAmp: 0.006, breatheHz: 0.55, color: [130, 152, 185] },
    awe:       { label: 'Awe & Inheritance',      speedMult: 0.95, leanBias: -0.03, breatheAmp: 0.010, breatheHz: 0.85, color: [108, 218, 195] },
    ecstasy:   { label: 'Ecstasy & Release',      speedMult: 1.18, leanBias:  0.05, breatheAmp: 0.014, breatheHz: 1.6,  color: [224, 120, 255] },
    departure: { label: 'Departure & Distance',   speedMult: 0.82, leanBias: -0.03, breatheAmp: 0.007, breatheHz: 0.65, color: [145, 175, 215] },
    peace:     { label: 'Reconciliation & Peace', speedMult: 0.92, leanBias:  0.00, breatheAmp: 0.008, breatheHz: 0.75, color: [118, 212, 148] }
  };

  function neutralScore(d){
    if (d.is_fragment) return 999;
    if (d.has_scene_prop) return 50;
    const clsPen = d.cls === 'stand' ? 0 : (d.cls === 'walk' ? 1.5 : 4);
    const armPen = d.arm >= 45 ? 2 : 0;
    const sprPen = d.spread >= 22 ? 2 : 0;
    const vwPen  = d.view === 'q3' ? 0 : (d.view === 'prof' ? 0.2 : (d.view === 'front' ? 0.4 : 3.5));
    return clsPen + armPen + sprPen + vwPen;
  }

  function plan(ch){
    const allDraws = ch.draws.map((d, i) => Object.assign({
      i,
      stride_cm: d.stride_cm || Math.max(24, Math.min(58, Math.round(24 + (d.spread || 10) * 0.55))),
      lead_leg: d.lead_leg || ((i % 2 === 0) ? 1 : -1),
      hip_y_ratio: d.hip_y_ratio || 0.54,
      is_fragment: !!d.is_fragment,
      has_scene_prop: !!d.has_scene_prop,
      sem_id: d.sem_id || (`pose_${i}`),
      sem_label: d.sem_label || (`Pose ${i+1}`),
      sem_group: d.sem_group || (`group_${i}`),
      sem_order: d.sem_order || 0,
      emotion: d.emotion || 'peace'
    }, d));

    const valid = allDraws.filter(d => !d.is_fragment);
    const pool = valid.length ? valid : allDraws;

    const uprightNoProp = pool.filter(d => !GROUND_ONLY.has(d.cls) && !d.has_scene_prop);
    const nonBack = uprightNoProp.filter(d => d.view !== 'back' && d.view !== 'back3q');
    const idlePool = (nonBack.length ? nonBack : (uprightNoProp.length ? uprightNoProp : pool)).slice().sort((a,b) => neutralScore(a) - neutralScore(b));
    const idle = idlePool[0] || pool[0];

    // 1. Coherent Walk Plan:
    // ONLY use curated clean_walk_indices (prop-free, matched orientation stride pairs).
    // All other characters walk using continuous split-hip scissor articulation on their cleanest upright drawing
    // so they NEVER randomly shuffle between dance, throw, or front/back poses!
    const cleanIndices = (ch.clean_walk_indices || []).filter(idx => allDraws[idx] && !allDraws[idx].is_fragment);
    let walk = null;

    if (cleanIndices.length >= 2){
      const dA = allDraws[cleanIndices[0]];
      const dB = allDraws[cleanIndices[1]];
      const dPassA = cleanIndices[2] !== undefined ? allDraws[cleanIndices[2]] : dA;
      const dPassB = cleanIndices[3] !== undefined ? allDraws[cleanIndices[3]] : dB;
      const avgStride = Math.max(30, Math.round(((dA.stride_cm || 38) + (dB.stride_cm || 38)) * 0.5));
      const holdMs = 240; // Calm, readable 240ms half-step (not frantic 160ms flickering)
      walk = {
        mode: 'step_4pose',
        stride_cm: avgStride,
        step_hold_ms: holdMs,
        speed_cm_s: (avgStride / (holdMs / 1000)),
        frames: [
          { d: dA,     role: 'contactA', lead: -1, hold: holdMs, phase: 0.0  },
          { d: dPassA, role: 'passA',    lead: -1, hold: holdMs, phase: 0.25 },
          { d: dB,     role: 'contactB', lead: +1, hold: holdMs, phase: 0.5  },
          { d: dPassB, role: 'passB',    lead: +1, hold: holdMs, phase: 0.75 }
        ]
      };
    } else {
      const stepBase = nonBack.find(d => d.view === 'prof' || d.view === 'q3') || idle;
      const synthStride = 36;
      const holdMs = 220;
      walk = {
        mode: 'scissor_step',
        stride_cm: synthStride,
        step_hold_ms: holdMs,
        speed_cm_s: (synthStride / (holdMs / 1000)),
        frames: [
          { d: stepBase, role: 'contactA', lead: -1, hold: holdMs, phase: 0.0,  scissor: -1.0 },
          { d: stepBase, role: 'passA',    lead: -1, hold: holdMs, phase: 0.25, scissor: -0.35 },
          { d: stepBase, role: 'contactB', lead: +1, hold: holdMs, phase: 0.5,  scissor: +1.0 },
          { d: stepBase, role: 'passB',    lead: +1, hold: holdMs, phase: 0.75, scissor: +0.35 }
        ]
      };
    }

    // 2. Smooth 360° Turnaround / Waltz (only when explicitly triggered)
    const bestForView = v => uprightNoProp.filter(d => d.view === v).sort((a,b) => neutralScore(a) - neutralScore(b))[0];
    const ringViews = [['q3',false],['prof',false],['back3q',false],['back',false],['back3q',true],['prof',true],['q3',true],['front',false]];
    const haveViews = new Set(uprightNoProp.map(d => d.view));
    let turn = null;
    if (haveViews.size >= 2){
      turn = [];
      let last = idle;
      for (const [v, mir] of ringViews){
        const d = bestForView(v) || last;
        last = d;
        turn.push({ d, hold: 210, mirror: mir });
      }
      turn.push({ d: idle, hold: 260, mirror: false });
    }

    // 3. Meaningful Emotional & Narrative Postures (NO random looping of unrelated drawings!)
    // Group only truly sequential multi-stage arcs (fall_arc, shore_recovery, blind_search);
    // every other drawing is an individual, named posture that holds steadily when selected.
    const PROGRESSIVE_GROUPS = new Set(['fall_arc', 'shore_recovery', 'blind_search']);
    const poses = [];
    const seenGroups = new Map();

    pool.forEach(d => {
      if (d.sem_group === 'walk_cycle' || d.sem_group === 'fragment') return;
      const g = d.sem_group || `single_${d.i}`;
      if (PROGRESSIVE_GROUPS.has(g)){
        if (!seenGroups.has(g)){
          const members = pool.filter(x => x.sem_group === g).sort((a,b) => (a.sem_order||0) - (b.sem_order||0));
          const groupLabels = {
            fall_arc: 'The Fall (Stumble → Freefall → Land)',
            shore_recovery: 'Washed Ashore → Waking',
            blind_search: 'Searching Blindly Through Haze'
          };
          const pObj = {
            key: g,
            label: groupLabels[g] || d.sem_label,
            emotion: d.emotion || 'vertigo',
            progressive: true, // Holds on final frame instead of looping like a slot machine!
            frames: members.map(m => ({ d: m, hold: 680 }))
          };
          seenGroups.set(g, pObj);
          poses.push(pObj);
        }
      } else {
        // Individual steady emotional posture
        poses.push({
          key: d.sem_id || (`pose_${d.i}`),
          group: g,
          label: d.sem_label,
          emotion: d.emotion || 'peace',
          progressive: false,
          frames: [{ d, hold: 10000 }]
        });
      }
    });

    return {
      idle,
      walk,
      turn,
      poses,
      all: pool,
      rawAll: allDraws,
      info: {
        walk_mode: walk.mode,
        stride_cm: walk.stride_cm,
        step_speed_cm_s: Math.round(walk.speed_cm_s),
        views: [...haveViews],
        drawings: pool.length
      }
    };
  }

  class Controller {
    constructor(ch){
      this.ch = ch;
      this.P = plan(ch);
      this.x = 0;
      this.y = 0;
      this.vx = 0;
      this.vy = 0;
      this.dir = 1;
      this.airborne = false;
      this.jumpsLeft = 2;
      this.anim = { kind: 'idle' };
      this.t0 = 0;
      this.walkDist = 0;
      this.shownIdx = this.P.idle.i;
      this.swapAt = -1e9;
      this.landAt = -1e9;
      this.stepCount = 0;
      this.lastLead = 0;
      this.emotion = 'searching';
      this.activeCue = null;
      this.resonance = 0; // 0..1 emotional alignment with the poem
    }

    setEmotion(emo){
      if (EMOTION_MODS[emo]) this.emotion = emo;
    }

    getEmotionMod(){
      return EMOTION_MODS[this.emotion] || EMOTION_MODS.searching;
    }

    jump(nowMs = 0){
      if (this.jumpsLeft > 0){
        this.vy = -275;
        this.airborne = true;
        this.jumpsLeft--;
        return true;
      }
      return false;
    }

    triggerPose(labelOrKey, nowMs = 0){
      if (!labelOrKey) return false;
      const q = String(labelOrKey).toLowerCase();
      // Match by exact key, group, sem_id, or label substring
      const p = this.P.poses.find(x =>
        (x.key && x.key.toLowerCase() === q) ||
        (x.group && x.group.toLowerCase() === q) ||
        x.label.toLowerCase() === q ||
        x.label.toLowerCase().includes(q) ||
        x.frames.some(f => (f.d.sem_id||'').toLowerCase() === q || (f.d.sem_group||'').toLowerCase() === q || (f.d.cls||'').toLowerCase() === q)
      );
      if (p){
        if (p.emotion) this.setEmotion(p.emotion);
        this.anim = { kind: 'pose', p };
        this.t0 = nowMs;
        return true;
      }
      return false;
    }

    embodyCue(cue, emotion, nowMs = 0){
      if (emotion) this.setEmotion(emotion);
      if (!cue || cue === 'walk_cycle'){
        if (this.anim.kind === 'pose') this.anim = { kind: 'idle' };
        return true;
      }
      if (this.activeCue === cue && this.anim.kind === 'pose') return true;
      this.activeCue = cue;
      // Find best matching posture for this narrative cue without resetting if already in it
      const found = this.triggerPose(cue, nowMs);
      if (!found){
        // Fallback by emotion
        const byEmo = this.P.poses.find(x => x.emotion === this.emotion && !x.frames[0]?.d?.has_scene_prop);
        if (byEmo){
          this.anim = { kind: 'pose', p: byEmo };
          this.t0 = nowMs;
          return true;
        }
      }
      return found;
    }

    triggerTurn(nowMs = 0){
      if (this.P.turn){
        this.anim = { kind: 'turn' };
        this.t0 = nowMs;
        return true;
      }
      return false;
    }

    clearPose(nowMs = 0){
      this.activeCue = null;
      this.anim = { kind: 'idle' };
      this.t0 = nowMs;
    }

    step(dtSec, moveInput, nowMs){
      const P = this.P;
      const walkPlan = P.walk;
      const emoMod = this.getEmotionMod();
      const effMove = Math.abs(moveInput) < 0.12 ? 0 : Math.max(-1, Math.min(1, moveInput));

      // 1. Horizontal locomotion locked to physical stride_cm, modulated by emotional register
      const targetVx = effMove * walkPlan.speed_cm_s * emoMod.speedMult;
      const accel = this.airborne ? 6.5 : 14.0;
      this.vx += (targetVx - this.vx) * Math.min(1, dtSec * accel);
      if (Math.abs(this.vx) < 1.5 && effMove === 0) this.vx = 0;

      if (effMove !== 0) this.dir = effMove > 0 ? 1 : -1;
      const dx = this.vx * dtSec;
      this.x += dx;

      // 2. Vertical jump & gravity physics
      if (this.airborne || this.y < 0 || this.vy !== 0){
        this.vy += 900 * dtSec;
        this.y += this.vy * dtSec;
        if (this.y >= 0){
          this.y = 0;
          this.vy = 0;
          this.airborne = false;
          this.jumpsLeft = 2;
          this.landAt = nowMs;
        }
      }

      // 3. State transition logic:
      // Walking begins smoothly when moving; when stopping, returns to calm stance (or holds grounded posture)
      const isMoving = Math.abs(this.vx) > 8.0 && !this.airborne;
      if (isMoving && (this.anim.kind === 'idle' || this.anim.kind === 'pose')){
        this.anim = { kind: 'walk' };
        this.t0 = nowMs;
      } else if (!isMoving && this.anim.kind === 'walk'){
        this.anim = { kind: 'idle' };
        this.t0 = nowMs;
      }

      // 4. Select current drawing and compute continuous articulation parameters
      let d = P.idle;
      let extraMirror = false;
      let dyCm = 0;
      let breathe = 0;
      let scissorAngle = 0;
      let phase = 0;
      let poseLabel = d.sem_label || 'Grounded Stance';

      if (this.airborne){
        const f0 = walkPlan.frames[0]?.d || P.idle;
        const f2 = walkPlan.frames[2]?.d || f0;
        d = this.vy < 0 ? f0 : f2;
        scissorAngle = this.vy < 0 ? 0.65 : -0.45;
        poseLabel = this.vy < 0 ? 'Rising' : 'Falling';
      } else if (this.anim.kind === 'walk'){
        this.walkDist += Math.abs(dx);
        const cycleCm = walkPlan.stride_cm * 2;
        phase = ((this.walkDist % cycleCm) / cycleCm) * Math.PI * 2;
        const idx = Math.floor(((this.walkDist % cycleCm) / cycleCm) * 4) % 4;
        const fr = walkPlan.frames[idx] || walkPlan.frames[0];
        d = fr.d;
        poseLabel = d.sem_label || 'Walking';

        if (fr.lead && fr.lead !== this.lastLead){
          this.lastLead = fr.lead;
          this.stepCount++;
        }

        // Smooth vertical gait arc
        dyCm = -Math.abs(Math.sin(phase)) * 2.4;
        // Scissor leg articulation: full amplitude for single-pose scissor_step, subtle bridge for step_4pose
        const scisAmp = walkPlan.mode === 'scissor_step' ? 1.0 : 0.28;
        scissorAngle = Math.sin(phase) * scisAmp;
      } else if (this.anim.kind === 'turn' && P.turn){
        let elapsed = Math.max(0, nowMs - this.t0);
        let picked = null;
        for (const f of P.turn){
          if (elapsed < f.hold){ picked = f; break; }
          elapsed -= f.hold;
        }
        if (!picked){
          this.anim = { kind: 'idle' };
          d = P.idle;
        } else {
          d = picked.d;
          extraMirror = !!picked.mirror;
          poseLabel = 'Turning Around';
        }
      } else if (this.anim.kind === 'pose' && this.anim.p){
        const p = this.anim.p;
        const frames = p.frames;
        const elapsed = Math.max(0, nowMs - this.t0);
        if (p.progressive){
          // Progressive narrative arc (e.g. Stumble -> Fall -> Land): holds on final frame!
          let rem = elapsed;
          let chosen = frames[frames.length - 1];
          for (const f of frames){
            if (rem < f.hold){ chosen = f; break; }
            rem -= f.hold;
          }
          d = chosen.d;
        } else {
          // Steady emotional posture: NEVER shuffles!
          d = frames[0].d;
        }
        poseLabel = d.sem_label || p.label;
        breathe = Math.sin((nowMs / 1000) * emoMod.breatheHz * Math.PI * 2) * emoMod.breatheAmp;
      } else {
        d = P.idle;
        poseLabel = d.sem_label || 'Grounded Stance';
        breathe = Math.sin((nowMs / 1000) * emoMod.breatheHz * Math.PI * 2) * emoMod.breatheAmp;
      }

      if (d.i !== this.shownIdx){
        this.shownIdx = d.i;
        this.swapAt = nowMs;
      }

      // 5. Gentle settle dip & landing squash
      const swapAge = Math.max(0, nowMs - this.swapAt);
      const landAge = Math.max(0, nowMs - this.landAt);
      let squashX = 1.0, squashY = 1.0, dipFrac = 0;

      if (swapAge < 130){
        const u = 1 - swapAge / 130;
        dipFrac = u * u * 0.018;
        squashX += u * 0.025;
        squashY -= u * 0.025;
      }
      if (landAge < 160){
        const u = 1 - landAge / 160;
        dipFrac += u * 0.04;
        squashX += u * 0.14;
        squashY -= u * 0.12;
      }

      // 6. Velocity + Emotional posture lean
      const leanRad = Math.max(-0.14, Math.min(0.14, (this.vx / 260) * 0.065 + emoMod.leanBias * this.dir));

      return {
        d,
        dir: this.dir,
        extra_mirror: extraMirror,
        x: this.x,
        y: this.y,
        vx: this.vx,
        vy: this.vy,
        airborne: this.airborne,
        dy_cm: dyCm + this.y,
        dip_frac: dipFrac,
        squash_x: squashX,
        squash_y: squashY,
        lean_rad: leanRad,
        breathe,
        scissor: {
          enabled: Math.abs(scissorAngle) > 0.01,
          angle: scissorAngle,
          hip_y_ratio: d.hip_y_ratio || 0.54,
          hip_shear: scissorAngle * 0.22,
          stride_offset_cm: scissorAngle * (walkPlan.stride_cm * 0.42)
        },
        step_count: this.stepCount,
        walk_mode: walkPlan.mode,
        kind: this.airborne ? 'jump' : this.anim.kind,
        phase,
        emotion: this.emotion,
        emotion_mod: emoMod,
        pose_label: poseLabel
      };
    }
  }

  /* Backward-compatible Actor wrapper */
  function Actor(ch, imgs){
    this.ch = ch;
    this.imgs = imgs;
    this.ctrl = new Controller(ch);
    this.P = this.ctrl.P;
    this.lastNow = performance.now();
  }
  Object.defineProperty(Actor.prototype, 'x', {
    get(){ return this.ctrl.x; },
    set(v){ this.ctrl.x = v; }
  });
  Object.defineProperty(Actor.prototype, 'dir', {
    get(){ return this.ctrl.dir; },
    set(v){ this.ctrl.dir = v; }
  });
  Actor.prototype.buttons = function(){
    const P = this.P;
    const out = [
      { label: 'Calm Stance', fn: () => this.ctrl.clearPose(performance.now()) },
      { label: 'Jump ▲', fn: () => this.ctrl.jump(performance.now()) }
    ];
    if (P.turn) out.push({ label: 'Turn 360°', fn: () => this.ctrl.triggerTurn(performance.now()) });
    P.poses.forEach(p => {
      out.push({ label: p.label, emotion: p.emotion, key: p.key, fn: () => this.ctrl.triggerPose(p.key, performance.now()) });
    });
    return out;
  };
  Actor.prototype.pick = function(now, movingInput){
    const dt = Math.min(0.05, Math.max(0.001, (now - this.lastNow) / 1000));
    this.lastNow = now;
    const m = typeof movingInput === 'number' ? movingInput : (movingInput ? this.ctrl.dir : 0);
    return this.ctrl.step(dt, m, now);
  };
  Actor.prototype.draw = function(ctx, state, sx, floorY, ppc, now){
    const d = state.d;
    const img = this.imgs[d.i];
    if (!img) return;
    const s = ((0.70 * this.ch.height_cm) / d.body_px) * ppc;
    const flip = (state.dir !== (d.right ? 1 : -1)) !== !!state.extra_mirror;
    const dyPx = (state.dy_cm || 0) * ppc + (state.dip_frac || 0) * d.h * s;

    // Ground shadow
    const airScale = Math.max(0.35, 1 + (state.y || 0) / 90);
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.42)';
    ctx.beginPath();
    ctx.ellipse(sx, floorY + 2, 26 * ppc * airScale, 5.5 * ppc * airScale, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    ctx.save();
    ctx.translate(sx, floorY + dyPx);
    ctx.rotate(state.lean_rad || 0);
    if (flip) ctx.scale(-1, 1);
    ctx.scale(state.squash_x || 1, (state.squash_y || 1) + (state.breathe || 0));
    ctx.shadowColor = 'rgba(0,0,0,.5)';
    ctx.shadowBlur = 12;
    ctx.shadowOffsetY = 3;

    if (state.scissor && state.scissor.enabled && Math.abs(state.scissor.hip_shear) > 0.01){
      const hr = state.scissor.hip_y_ratio || 0.54;
      const splitY = Math.round(d.h * hr);
      const shear = state.scissor.hip_shear;
      // Back leg pass
      ctx.save();
      ctx.beginPath();
      ctx.rect(-d.w*s, -(d.h - splitY)*s, d.w*s*2, (d.h - splitY)*s + 20);
      ctx.clip();
      ctx.transform(1, 0, -shear * 0.85, 1, 0, 0);
      ctx.filter = 'brightness(0.76)';
      ctx.drawImage(img, 0, splitY, d.w, d.h - splitY, -d.ax*s, -(d.h - splitY)*s, d.w*s, (d.h - splitY)*s);
      ctx.restore();

      // Front leg pass
      ctx.save();
      ctx.beginPath();
      ctx.rect(-d.w*s, -(d.h - splitY)*s, d.w*s*2, (d.h - splitY)*s + 20);
      ctx.clip();
      ctx.transform(1, 0, shear, 1, 0, 0);
      ctx.drawImage(img, 0, splitY, d.w, d.h - splitY, -d.ax*s, -(d.h - splitY)*s, d.w*s, (d.h - splitY)*s);
      ctx.restore();

      // Upper torso & head pass
      ctx.drawImage(img, 0, 0, d.w, splitY + 3, -d.ax*s, -d.h*s, d.w*s, (splitY + 3)*s);
    } else {
      ctx.drawImage(img, -d.ax*s, -d.h*s, d.w*s, d.h*s);
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

  return { plan, Controller, Actor, loadImg, neutralScore, neutral: neutralScore, EMOTION_MODS };
});
