/**
 * cartoon_character.js — Multiplane Cartoon Character Rig & Kinematic Solver
 *
 * Implements the classical Multiplane Animation Studio character engine:
 * 1. VOLUME, NOT LINE: Tapered limb capsules, quadrilateral torso, mass-conserved skull.
 * 2. SILHOUETTE READABILITY: High-contrast contours with instant Notan testing.
 * 3. PASSES: Cel wash (ink + posterized flats) or Notan (pure silhouette).
 * 4. MULTIPLANE INTEGRATION: Native Three.js canvas-texture plane generator for Plane 2 (Hero).
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) { define([], factory); }
  else if (typeof module === 'object' && module.exports) { module.exports = factory(); }
  else { root.CartoonCharacter = factory(); }
}(typeof self !== 'undefined' ? self : this, function () {

  const TAU = Math.PI * 2;
  const L = { ankle: 0.045, knee: 0.285, hip: 0.500, waist: 0.605, chest: 0.720, shoulder: 0.815, chin: 0.855, crown: 1.0 };
  const W = {
    head: 0.076, jaw: 0.058, neck: 0.032,
    shoulder: 0.112, chestHalf: 0.098, waistHalf: 0.076, hipHalf: 0.084,
    armTop: 0.042, armMid: 0.033, armEnd: 0.024,
    legTop: 0.060, legMid: 0.046, legEnd: 0.030,
    hand: 0.032, foot: 0.036,
  };

  const GUISES = {
    everyman: { hair: 0, beard: 0, shoulderSlope: 0, shoulderWide: 1, stoop: 0, neck: 1, headScale: 1, coat: 0 },
    poet:     { hair: 0.38, beard: 0.30, shoulderSlope: 0.24, shoulderWide: 1.10, stoop: 0.05, neck: 1.20, headScale: 1.04, coat: 0.85, scarf: 1 },
    turned:   { hair: 0.42, beard: 0, shoulderSlope: 0.24, shoulderWide: 1.08, stoop: 0.03, neck: 1.18, headScale: 1.04, coat: 0.85, back: 1 },
    elder:    { hair: 0.14, beard: 0.44, shoulderSlope: 0.42, shoulderWide: 0.94, stoop: 0.16, neck: 0.92, headScale: 1.06, coat: 0.5 },
    child:    { hair: 0.26, beard: 0, shoulderSlope: 0.10, shoulderWide: 0.84, stoop: 0, neck: 0.85, headScale: 1.30, coat: 0 }
  };

  function lerp(a, b, t) { return a + (b - a) * t; }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function smooth(t) { return t * t * (3 - 2 * t); }

  /**
   * Kinematic Bone Solver
   */
  function solve(h, pose, G) {
    const face = pose.face === -1 ? -1 : 1;
    const mode = pose.mode || "stand";
    const ph = pose.phase || 0;
    const arms = pose.arms || (mode === "walk" ? "swing" : "down");
    const turn = pose.turn ?? (mode === "walk" ? 0.88 : 0);
    const crouch = (pose.crouch || 0) * h * 0.14;
    const lean = (pose.lean || 0) * h * 0.12;

    // Moving hold breath cycle
    const breath = (pose.breath ?? 1) * Math.sin(ph * TAU * 0.5) * h * 0.008;

    // Contrapposto weight shift
    const wt = pose.weight ?? (mode === "stand" ? 0.5 : 0);
    const hipTilt = (wt - 0.5) * h * 0.03 * face;
    const shTilt = -(wt - 0.5) * h * 0.02 * face;

    const hipY = L.hip * h - crouch;
    const shY = L.shoulder * h + breath - crouch;

    // Leg endpoints
    let footA = [-W.hipHalf * h * 0.85, 0], footB = [W.hipHalf * h * 0.85, 0];
    let kneeA = null, kneeB = null;

    if (mode === "walk") {
      const q = ph * TAU;
      const stride = h * 0.32;
      const xA = Math.sin(q) * stride, xB = -xA;
      // Stance vs swing foot height
      const yA = Math.cos(q) > 0 ? Math.sin(Math.cos(q) * Math.PI) * h * 0.08 : 0;
      const yB = Math.cos(q) < 0 ? Math.sin(Math.abs(Math.cos(q)) * Math.PI) * h * 0.08 : 0;

      footA = [xA * face, yA];
      footB = [xB * face, yB];

      const kAx = lerp(0, footA[0], 0.5) + (yA > 0 ? 0.06 * h * face : 0.02 * h * face);
      const kAy = lerp(hipY, footA[1], 0.5);
      kneeA = [kAx, kAy];

      const kBx = lerp(0, footB[0], 0.5) + (yB > 0 ? 0.06 * h * face : 0.02 * h * face);
      const kBy = lerp(hipY, footB[1], 0.5);
      kneeB = [kBx, kBy];
    } else if (mode === "fall") {
      const q = ph * TAU;
      footA = [-h * 0.15 * face + Math.sin(q) * 6, -h * 0.08];
      footB = [h * 0.18 * face + Math.cos(q) * 6, -h * 0.14];
      kneeA = [footA[0] * 0.6 - 4 * face, hipY * 0.5];
      kneeB = [footB[0] * 0.6 + 6 * face, hipY * 0.55];
    } else {
      // Stand default
      kneeA = [footA[0] * 0.7 + lean * 0.2, hipY * 0.52];
      kneeB = [footB[0] * 0.7 + lean * 0.2, hipY * 0.52];
    }

    // Shoulder & Hip Spans
    const shSpan = W.shoulder * h * G.shoulderWide * (1 - turn * 0.35);
    const hipSpan = W.hipHalf * h * (1 - turn * 0.4);

    const hipL = [-hipSpan, hipY - hipTilt];
    const hipR = [hipSpan, hipY + hipTilt];
    const shL = [-shSpan + lean, shY - shTilt];
    const shR = [shSpan + lean, shY + shTilt];

    // Neck & Head
    const headTilt = (pose.headTurn || 0) * 0.25;
    const neckY = shY + h * 0.04;
    const headX = lean * 1.1 + headTilt * h * 0.1 * face;
    const headY = shY + (L.chin - L.shoulder + 0.06) * h * G.neck;
    const craniumR = W.head * h * G.headScale;

    // Arm Chains (near / far)
    let armA_elbow, armA_hand, armB_elbow, armB_hand;

    if (arms === "swing" && mode === "walk") {
      const q = ph * TAU;
      const swing = Math.sin(q) * h * 0.22;
      armA_elbow = [shL[0] - swing * face * 0.5, shY - h * 0.18];
      armA_hand = [shL[0] - swing * face, shY - h * 0.36];
      armB_elbow = [shR[0] + swing * face * 0.5, shY - h * 0.18];
      armB_hand = [shR[0] + swing * face, shY - h * 0.36];
    } else if (arms === "reach") {
      armA_elbow = [shL[0] + h * 0.20 * face, shY + h * 0.02];
      armA_hand = [shL[0] + h * 0.40 * face, shY + h * 0.08];
      armB_elbow = [shR[0] + h * 0.14 * face, shY - h * 0.10];
      armB_hand = [shR[0] + h * 0.26 * face, shY - h * 0.06];
    } else if (arms === "open" || mode === "fall") {
      armA_elbow = [shL[0] - h * 0.22 * face, shY + h * 0.10];
      armA_hand = [shL[0] - h * 0.38 * face, shY + h * 0.20];
      armB_elbow = [shR[0] + h * 0.24 * face, shY + h * 0.12];
      armB_hand = [shR[0] + h * 0.42 * face, shY + h * 0.22];
    } else {
      // Arms down at sides
      armA_elbow = [shL[0] - h * 0.03 * face, shY - h * 0.18];
      armA_hand = [shL[0] - h * 0.04 * face, shY - h * 0.36];
      armB_elbow = [shR[0] + h * 0.03 * face, shY - h * 0.18];
      armB_hand = [shR[0] + h * 0.04 * face, shY - h * 0.36];
    }

    return {
      face, h, G, mode,
      head: [headX, headY, craniumR],
      neck: [lean, neckY],
      shL, shR, hipL, hipR,
      footA, footB, kneeA, kneeB,
      armA: { sh: shL, elbow: armA_elbow, hand: armA_hand },
      armB: { sh: shR, elbow: armB_elbow, hand: armB_hand },
      coat: G.coat, scarf: G.scarf,
      rot: pose.rot || 0
    };
  }

  /**
   * Helper: draw tapered capsule between two joints
   */
  function drawCapsule(ctx, p0, p1, r0, r1) {
    const dx = p1[0] - p0[0], dy = p1[1] - p0[1];
    const d = Math.hypot(dx, dy);
    if (d < 0.001) { ctx.beginPath(); ctx.arc(p0[0], p0[1], r0, 0, TAU); ctx.fill(); ctx.stroke(); return; }

    const nx = -dy / d, ny = dx / d;
    ctx.beginPath();
    ctx.arc(p0[0], p0[1], r0, Math.atan2(ny, nx), Math.atan2(-ny, -nx), false);
    ctx.arc(p1[0], p1[1], r1, Math.atan2(-ny, -nx), Math.atan2(ny, nx), false);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  /**
   * Draw classical cartoon figure into standard 2D Canvas context
   */
  function drawFigure(ctx, x, y, h, pose = {}, style = {}) {
    const guiseName = typeof pose.guise === "string" ? pose.guise : "poet";
    const G = GUISES[guiseName] || GUISES.poet;
    const S = solve(h, pose, G);

    ctx.save();
    ctx.translate(x, y);
    if (S.rot) ctx.rotate(S.rot);

    // Style parameters
    const isNotan = style.mode === "notan";
    const inkColor = isNotan ? "#000000" : (style.inkColor || "#090c12");
    const bodyTone = isNotan ? "#000000" : (style.bodyTone || "#26202e");
    const skinTone = isNotan ? "#000000" : (style.skinTone || "#d49f82");
    const coatTone = isNotan ? "#000000" : (style.coatTone || "#18141d");
    const accentTone = isNotan ? "#000000" : (style.accentTone || "#f2a541");
    const lineWidth = isNotan ? 0.5 : Math.max(1.8, h * 0.038);

    ctx.strokeStyle = inkColor;
    ctx.fillStyle = bodyTone;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    // In Three / Canvas screen space, positive y is DOWN. Our solver treats +y as UP.
    // Invert y inside drawing function
    ctx.scale(1, -1);

    // --- 1. FAR LEG (Limb B)
    ctx.fillStyle = isNotan ? "#000" : "#1e1824";
    drawCapsule(ctx, S.hipB || S.hipR, S.kneeB, W.legTop * h * 0.85, W.legMid * h * 0.85);
    drawCapsule(ctx, S.kneeB, S.footB, W.legMid * h * 0.85, W.legEnd * h * 0.85);
    // Far Foot
    ctx.beginPath();
    ctx.ellipse(S.footB[0], S.footB[1], W.foot * h, W.foot * h * 0.5, 0, 0, TAU);
    ctx.fill(); ctx.stroke();

    // --- 2. FAR ARM (Arm B)
    ctx.fillStyle = bodyTone;
    drawCapsule(ctx, S.armB.sh, S.armB.elbow, W.armTop * h * 0.8, W.armMid * h * 0.8);
    drawCapsule(ctx, S.armB.elbow, S.armB.hand, W.armMid * h * 0.8, W.armEnd * h * 0.8);
    // Far Hand
    ctx.fillStyle = skinTone;
    ctx.beginPath();
    ctx.arc(S.armB.hand[0], S.armB.hand[1], W.hand * h * 0.85, 0, TAU);
    ctx.fill(); ctx.stroke();

    // --- 3. TORSO QUADRILATERAL
    ctx.fillStyle = coatTone;
    ctx.beginPath();
    ctx.moveTo(S.shL[0], S.shL[1]);
    ctx.lineTo(S.shR[0], S.shR[1]);
    ctx.lineTo(S.hipR[0], S.hipR[1]);
    ctx.lineTo(S.hipL[0], S.hipL[1]);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Poet Coat Tails (Silhouette expansion on twos)
    if (S.coat > 0) {
      ctx.fillStyle = coatTone;
      const tailX = -S.face * h * 0.18 + Math.sin((pose.phase || 0) * TAU) * h * 0.04;
      const tailY = S.hipL[1] - h * 0.22;
      ctx.beginPath();
      ctx.moveTo(S.hipL[0], S.hipL[1]);
      ctx.lineTo(S.hipR[0], S.hipR[1]);
      ctx.quadraticCurveTo(S.face * h * 0.05, tailY + h * 0.05, tailX, tailY);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // --- 4. NEAR LEG (Limb A)
    ctx.fillStyle = isNotan ? "#000" : "#241d2c";
    drawCapsule(ctx, S.hipL, S.kneeA, W.legTop * h, W.legMid * h);
    drawCapsule(ctx, S.kneeA, S.footA, W.legMid * h, W.legEnd * h);
    // Near Foot
    ctx.beginPath();
    ctx.ellipse(S.footA[0], S.footA[1], W.foot * h * 1.1, W.foot * h * 0.55, 0, 0, TAU);
    ctx.fill(); ctx.stroke();

    // --- 5. NECK & HEAD
    ctx.fillStyle = skinTone;
    ctx.beginPath();
    ctx.arc(S.neck[0], S.neck[1], W.neck * h * 1.2, 0, TAU);
    ctx.fill();

    // Head / Cranium
    const [hx, hy, hr] = S.head;
    ctx.beginPath();
    ctx.arc(hx, hy, hr, 0, TAU);
    ctx.fill();
    ctx.stroke();

    // Jaw / Chin
    ctx.beginPath();
    ctx.arc(hx + S.face * hr * 0.35, hy - hr * 0.35, hr * 0.65, 0, TAU);
    ctx.fill();
    ctx.stroke();

    // Hair Mass (Classical crescent hugging skull)
    if (G.hair > 0) {
      ctx.fillStyle = isNotan ? "#000" : "#120e15";
      ctx.beginPath();
      ctx.arc(hx, hy + hr * 0.15, hr * 1.12, 0, TAU);
      ctx.fill();
      // Wind-blown hair locks for Poet
      ctx.beginPath();
      ctx.moveTo(hx - S.face * hr * 0.8, hy + hr * 0.5);
      ctx.quadraticCurveTo(hx - S.face * hr * 1.4, hy + hr * 0.3, hx - S.face * hr * 1.1, hy - hr * 0.2);
      ctx.lineTo(hx, hy);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // Beard
    if (G.beard > 0 && !isNotan) {
      ctx.fillStyle = "#120e15";
      ctx.beginPath();
      ctx.arc(hx + S.face * hr * 0.45, hy - hr * 0.55, hr * 0.45, 0, TAU);
      ctx.fill();
    }

    // Scarf Accent (Poet signature splash of amber)
    if (S.scarf && !isNotan) {
      ctx.fillStyle = accentTone;
      ctx.beginPath();
      ctx.ellipse(S.neck[0], S.neck[1], hr * 0.85, hr * 0.45, S.face * 0.2, 0, TAU);
      ctx.fill();
      ctx.stroke();
      // Fluttering tail
      ctx.beginPath();
      ctx.moveTo(S.neck[0], S.neck[1]);
      ctx.lineTo(S.neck[0] - S.face * h * 0.12, S.neck[1] - h * 0.10);
      ctx.lineTo(S.neck[0] - S.face * h * 0.08, S.neck[1] - h * 0.14);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // --- 6. NEAR ARM (Arm A)
    ctx.fillStyle = coatTone;
    drawCapsule(ctx, S.armA.sh, S.armA.elbow, W.armTop * h, W.armMid * h);
    drawCapsule(ctx, S.armA.elbow, S.armA.hand, W.armMid * h, W.armEnd * h);
    // Near Hand
    ctx.fillStyle = skinTone;
    ctx.beginPath();
    ctx.arc(S.armA.hand[0], S.armA.hand[1], W.hand * h, 0, TAU);
    ctx.fill(); ctx.stroke();

    ctx.restore();
  }

  /**
   * Generates a 7-key exposure sheet (X-Sheet) for an action beat
   */
  function generateExposureSheet(actionName, durationFrames = 48) {
    const fps = 24;
    const actions = {
      search: [
        { key: "K01", frame: 1,  mode: "stand", arms: "down", face: 1,  note: "Standing in door hold" },
        { key: "K02", frame: 8,  mode: "stand", arms: "reach", face: 1, note: "Anticipates door latch" },
        { key: "K03", frame: 16, mode: "walk",  arms: "swing", face: 1, phase: 0.25, note: "Steps into corridor" },
        { key: "K04", frame: 26, mode: "walk",  arms: "swing", face: 1, phase: 0.75, note: "Extreme stride passing column" },
        { key: "K05", frame: 34, mode: "stand", arms: "reach", face: -1, lean: -0.15, note: "Startle recoil: turns back" },
        { key: "K06", frame: 40, mode: "stand", arms: "down", face: -1, crouch: 0.2, note: "Compression settle" },
        { key: "K07", frame: 48, mode: "stand", arms: "down", face: 1,  headTurn: 0.6, note: "Moving hold gaze" }
      ],
      fall: [
        { key: "K01", frame: 1,  mode: "stand", arms: "open", face: 1, rot: 0.1, note: "Loss of footing edge" },
        { key: "K02", frame: 6,  mode: "fall",  arms: "open", face: 1, rot: 0.4, note: "Tipping threshold" },
        { key: "K03", frame: 14, mode: "fall",  arms: "open", face: 1, rot: 1.1, note: "Tumbling airborne" },
        { key: "K04", frame: 24, mode: "fall",  arms: "reach", face: -1, rot: 1.8, note: "Extreme arc inverted" },
        { key: "K05", frame: 32, mode: "fall",  arms: "open", face: -1, rot: 2.5, note: "Centrifugal glide" },
        { key: "K06", frame: 40, mode: "fall",  arms: "reach", face: 1, rot: 3.1, note: "Drifting in cloud layer" },
        { key: "K07", frame: 48, mode: "stand", arms: "open", face: 1, rot: 0.0, note: "Descent equilibrium" }
      ],
      gaze: [
        { key: "K01", frame: 1,  mode: "stand", arms: "down", face: 1, guise: "turned", note: "Back to camera holding window" },
        { key: "K02", frame: 10, mode: "stand", arms: "down", face: 1, guise: "turned", breath: 1.5, note: "Deep breath hold" },
        { key: "K03", frame: 20, mode: "stand", arms: "reach", face: 1, guise: "turned", note: "Hand touches glass plane" },
        { key: "K04", frame: 28, mode: "stand", arms: "reach", face: 1, guise: "poet", turn: 0.4, note: "3/4 profile turn" },
        { key: "K05", frame: 36, mode: "stand", arms: "down", face: 1, guise: "poet", note: "Shoulder drop settle" },
        { key: "K06", frame: 42, mode: "stand", arms: "down", face: 1, guise: "poet", headTurn: 0.4, note: "Gaze follows drone" },
        { key: "K07", frame: 48, mode: "stand", arms: "down", face: 1, guise: "poet", note: "Living hold" }
      ]
    };
    return actions[actionName] || actions.search;
  }

  /**
   * Three.js helper: creates a textured PlaneMesh on Plane 2 (Hero)
   */
  function createCharacterMesh(THREE, options = {}) {
    const W = 512, H = 512;
    const canvas = document.createElement("canvas");
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;

    const material = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide
    });

    const worldHeight = options.worldHeight || 1.8; // 1.8 meters tall
    const geometry = new THREE.PlaneGeometry(worldHeight * (W / H), worldHeight);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = "P2_Hero_Character";

    mesh.userData = {
      canvas, ctx, texture,
      pose: { mode: "walk", phase: 0, face: 1, guise: "poet" },
      style: { mode: "cel" },
      dirty: true
    };

    mesh.updatePose = function (pose, style) {
      if (pose) Object.assign(mesh.userData.pose, pose);
      if (style) Object.assign(mesh.userData.style, style);

      const c = mesh.userData.canvas, g = mesh.userData.ctx;
      g.clearRect(0, 0, c.width, c.height);

      // Draw character centered at bottom of 512x512 canvas
      drawFigure(g, c.width * 0.5, c.height * 0.88, c.height * 0.72, mesh.userData.pose, mesh.userData.style);
      mesh.userData.texture.needsUpdate = true;
    };

    mesh.updatePose();
    return mesh;
  }

  return {
    drawFigure,
    solve,
    generateExposureSheet,
    createCharacterMesh,
    GUISES
  };
}));
