/**
 * audio_drone.js — Web Audio Ambient Drone & Prosody Synthesizer for WYGWYL
 *
 * Recreates the microtonal drone beds and harmonic steps for the 14 poems of
 * Where You Go When You Leave (Mark Anthony Thomas).
 */
(function (root, factory) {
  if (typeof define === 'function' && define.amd) { define([], factory); }
  else if (typeof module === 'object' && module.exports) { module.exports = factory(); }
  else { root.AudioDrone = factory(); }
}(typeof self !== 'undefined' ? self : this, function () {

  let ac = null, master = null, oscs = [], noiseGain = null, isPlaying = false;
  let curDrone = { base: 16.35, steps: [0, 0, -11, -9, -12] };

  function init() {
    if (ac) return;
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    ac = new AudioCtx();

    master = ac.createGain();
    master.gain.value = 0;
    master.connect(ac.destination);

    // Multi-oscillator microtonal bed: fundamental + slight detune + octave harmonic
    const defs = [
      [1.0, "sine", 0.22],
      [1.008, "triangle", 0.08],
      [2.003, "sine", 0.05]
    ];

    oscs = defs.map(([mult, type, gainVal]) => {
      const o = ac.createOscillator();
      const g = ac.createGain();
      o.type = type;
      o.frequency.value = curDrone.base * mult;
      g.gain.value = gainVal;
      o.connect(g);
      g.connect(master);
      o.start();
      return { o, g, mult, defaultGain: gainVal };
    });

    // 2-second looped pink/brown atmospheric noise bed
    const bufSize = ac.sampleRate * 2;
    const noiseBuf = ac.createBuffer(1, bufSize, ac.sampleRate);
    const data = noiseBuf.getChannelData(0);
    let s = 101;
    for (let i = 0; i < bufSize; i++) {
      s ^= s << 13; s ^= s >>> 17; s ^= s << 5;
      data[i] = (((s >>> 0) / 4294967296) * 2 - 1) * 0.4;
    }

    const noiseSrc = ac.createBufferSource();
    noiseSrc.buffer = noiseBuf;
    noiseSrc.loop = true;

    const filter = ac.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 280;
    filter.Q.value = 0.8;

    noiseGain = ac.createGain();
    noiseGain.gain.value = 0.04;

    noiseSrc.connect(filter);
    filter.connect(noiseGain);
    noiseGain.connect(master);
    noiseSrc.start();
  }

  function setPoemDrone(droneSpec) {
    if (!droneSpec || !droneSpec.base) return;
    curDrone = droneSpec;
    if (!ac) return;

    const now = ac.currentTime;
    oscs.forEach(({ o, mult }) => {
      o.frequency.cancelScheduledValues(now);
      // Smooth pitch glissando to the poem's base frequency
      o.frequency.exponentialRampToValueAtTime(Math.max(10, curDrone.base * mult), now + 1.2);
    });
  }

  function play(targetGain = 0.35) {
    init();
    if (!ac) return;
    if (ac.state === "suspended") ac.resume();
    const now = ac.currentTime;
    master.gain.cancelScheduledValues(now);
    master.gain.linearRampToValueAtTime(targetGain, now + 1.5);
    isPlaying = true;
  }

  function stop() {
    if (!ac || !master) return;
    const now = ac.currentTime;
    master.gain.cancelScheduledValues(now);
    master.gain.linearRampToValueAtTime(0.0001, now + 0.8);
    isPlaying = false;
  }

  function toggle() {
    if (isPlaying) stop();
    else play();
    return isPlaying;
  }

  return {
    init,
    setPoemDrone,
    play,
    stop,
    toggle,
    get isPlaying() { return isPlaying; }
  };
}));
