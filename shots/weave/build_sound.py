"""Sound for the weave passage, synthesised from the same event times that drive the picture.

  her voice      OBSERVED, the suite recording 661.0-674.8 s, untouched
  the archive    OBSERVED, Sound And The Story (1956) audio at passage time + 8 s; its gain follows the canopy mix
                 (the knob), ducked under her words, in a large reverb (it is playing in the canopy space)
  knob detents   one click each time the knob crosses 15 degrees (read from the clip's knob track)
  grip / release a cardboard tap on the contact begin and release events
  room           low crowd murmur that rises with the canopy
Writes shots/weave/passage.wav (stereo, 48 kHz). Loudness is normalised to -16 LUFS at the mux.
Smoothing uses a cumulative-sum moving average (never an O(N x kernel) convolution over full-length audio).
"""
import json, os, wave
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
SR = 48000
clip = json.load(open(os.path.join(ROOT, 'clips', 'p07_turn_me_up.json')))
N = clip['clock']['frames']; FPS = clip['clock']['fps']; DUR = N / FPS; L = int(DUR * SR)
rng = np.random.default_rng(1956)

def read(path):
    with wave.open(path) as w:
        ch, sr, n = w.getnchannels(), w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
    assert sr == SR, (path, sr)
    return x.reshape(-1, ch).mean(1) if ch > 1 else x

def movavg(x, n):
    c = np.cumsum(np.concatenate([[0.0], x]))
    y = (c[n:] - c[:-n]) / n
    return np.concatenate([np.full(n // 2, y[0]), y, np.full(len(x) - len(y) - n // 2, y[-1])])

def per_frame(vals):  # frame track -> sample track
    v = np.repeat(np.asarray(vals, np.float32), SR // FPS)
    return np.pad(v, (0, max(0, L - len(v))), mode='edge')[:L]

voice = read(os.path.join(ROOT, 'voice', 'p07_659_675.wav'))[int(2.0 * SR):int(2.0 * SR) + L]
voice = np.pad(voice, (0, L - len(voice)))
arch = read(os.path.join(ROOT, 'archive', 'da69.wav'))[int(8.0 * SR):int(8.0 * SR) + L]
arch = np.pad(arch, (0, L - len(arch)))

mix = per_frame([f['mix'] for f in clip['frames']])
speaking = np.zeros(L, np.float32)
for w in clip['words']:
    a, b = int((w['t0'] - clip['clock']['t0']) * SR), int((w['t1'] - clip['clock']['t0']) * SR)
    speaking[max(0, a):max(0, min(L, b))] = 1
duck = 1 - 0.55 * np.clip(movavg(speaking, int(0.25 * SR)), 0, 1)
g_arch = (0.05 + 0.55 * mix) * duck
g_arch = movavg(g_arch, int(0.05 * SR))

# reverb: exponential-decay noise impulse, by FFT
def reverb(x, secs=1.9, wet=0.45):
    n = int(secs * SR)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.linspace(0, 7, n)).astype(np.float32)
    ir /= np.sqrt((ir ** 2).sum())
    m = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:len(x)]
    return (1 - wet) * x + wet * y.astype(np.float32)

arch_out = reverb(arch * g_arch)

# events
def click(t, amp=0.25, f0=2400):
    n = int(0.03 * SR); tt = np.arange(n) / SR
    s = (rng.standard_normal(n) * np.exp(-tt * 260) * 0.6 + np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 140)) * amp
    i = int(t * SR); out[i:i + n] += s[:max(0, min(n, L - i))]

def tap(t, amp=0.35):
    n = int(0.08 * SR); tt = np.arange(n) / SR
    s = (movavg(rng.standard_normal(n).astype(np.float32), 24) * 6 * np.exp(-tt * 60) + np.sin(2 * np.pi * 140 * tt) * np.exp(-tt * 45) * 0.5) * amp
    i = int(t * SR); out[i:i + n] += s[:max(0, min(n, L - i))]

out = np.zeros(L, np.float32)
prev = 0.0
events = []
for fr in clip['frames']:
    k = fr['knob']
    for d in range(15, 106, 15):
        if prev < d <= k:
            click(fr['t']); events.append(('detent', fr['t'], d))
    prev = max(prev, k)
for c in clip['contacts']:
    if c['event'] in ('begin', 'release'):
        tap(c['t'], 0.3 if c['event'] == 'begin' else 0.2); events.append((c['event'], c['t']))

room = movavg(rng.standard_normal(L).astype(np.float32), 180) * 4.0
room *= (0.035 + 0.05 * movavg(mix, int(0.6 * SR)))

mono_bed = arch_out + room + out
left = voice * 0.95 + mono_bed * 0.9 + reverb(room, 0.8, 1.0) * 0.2
right = voice * 0.95 + mono_bed * 0.9 - reverb(room, 0.8, 1.0) * 0.2
st = np.stack([left, right], 1)
st /= max(1.0, np.abs(st).max() / 0.95)
with wave.open(os.path.join(ROOT, 'passage.wav'), 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
json.dump({'events': events, 'archive_gain': '0.05 + 0.55 x canopy mix, ducked 55% under her words'},
          open(os.path.join(ROOT, 'clips', 'p07_sound_events.json'), 'w'), indent=1)
print('wrote passage.wav', round(DUR, 2), 's;', len(events), 'sound events')
