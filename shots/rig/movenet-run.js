/* movenet-run.js — MoveNet Lightning (the Bolas range-test model, shots/rig/movenet.js) on a still image, in the
   browser. TensorFlow.js is vendored (vendor/tf.min.js, 4.22.0, Apache-2.0) so it runs offline. */
(function () {
  'use strict';
  let model = null, loading = null;
  const loadScript = src => new Promise((res, rej) => { const s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = () => rej(new Error('could not load ' + src)); document.head.appendChild(s); });
  async function ensure(base = '') {
    if (model) return model;
    if (loading) return loading;
    loading = (async () => {
      if (!window.tf) await loadScript(base + 'vendor/tf.min.js');
      if (!window.BOLAS_MOVENET) await loadScript(base + 'movenet.js');
      const mdl = window.BOLAS_MOVENET, bin = atob(mdl.weights), buf = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
      let ok = false; try { ok = await tf.setBackend('webgl'); } catch (e) { ok = false; }
      if (!ok) await tf.setBackend('cpu');
      await tf.ready();
      model = await tf.loadGraphModel(tf.io.fromMemory({ modelTopology: mdl.modelTopology, weightSpecs: mdl.weightSpecs, weightData: buf.buffer, format: mdl.format, generatedBy: mdl.generatedBy, convertedBy: mdl.convertedBy, signature: mdl.signature }));
      window.BOLAS_MOVENET = null;
      return model;
    })();
    return loading;
  }
  // image (loaded HTMLImageElement) -> 17 x [x, y, score] in image px; bg fills the transparent card
  async function detect(im, bg = '#7a7a7a', crop) {
    const m = await ensure(), S = 192, cv = document.createElement('canvas'); cv.width = S; cv.height = S;
    const g = cv.getContext('2d', { willReadFrequently: true });
    const [x0, y0, w0, h0] = crop || [0, 0, im.naturalWidth, im.naturalHeight];
    const k = S / Math.max(w0, h0) * .92, dw = w0 * k, dh = h0 * k, ox = (S - dw) / 2, oy = (S - dh) / 2;
    g.fillStyle = bg; g.fillRect(0, 0, S, S); g.drawImage(im, x0, y0, w0, h0, ox, oy, dw, dh);
    const input = tf.tidy(() => tf.browser.fromPixels(cv).toInt().expandDims(0));
    const out = m.execute(input), d = await out.data(); input.dispose(); out.dispose();
    const kp = []; for (let j = 0; j < 17; j++) { const y = d[j * 3], x = d[j * 3 + 1], s = d[j * 3 + 2]; kp.push([x0 + (x * S - ox) / k, y0 + (y * S - oy) / k, s]); }
    return kp;
  }
  function maskOf(im) {
    const W = im.naturalWidth, H = im.naturalHeight, c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(im, 0, 0);
    const d = g.getImageData(0, 0, W, H).data, m = new Uint8Array(W * H);
    for (let i = 0; i < W * H; i++) m[i] = d[i * 4 + 3] > 100 ? 1 : 0;
    const lab = new Int32Array(W * H), st = new Int32Array(W * H); let best = 0, bestN = 0, id = 0;
    for (let i = 0; i < W * H; i++) if (m[i] && !lab[i]) { id++; let sp = 0, n = 0; st[sp++] = i; lab[i] = id;
      while (sp) { const j = st[--sp]; n++; const x = j % W, y = (j / W) | 0;
        if (x > 0 && m[j - 1] && !lab[j - 1]) { lab[j - 1] = id; st[sp++] = j - 1; } if (x < W - 1 && m[j + 1] && !lab[j + 1]) { lab[j + 1] = id; st[sp++] = j + 1; }
        if (y > 0 && m[j - W] && !lab[j - W]) { lab[j - W] = id; st[sp++] = j - W; } if (y < H - 1 && m[j + W] && !lab[j + W]) { lab[j + W] = id; st[sp++] = j + W; } }
      if (n > bestN) { bestN = n; best = id; } }
    for (let i = 0; i < W * H; i++) m[i] = lab[i] === best ? 1 : 0;
    return { m, W, H };
  }
  window.RigMoveNet = { ensure, detect, maskOf };
})();
