"""Sound for poem 04 (the hands). Reads only the clip: her voice, plus one sound per logged contact.

  voice      her recording, 364.0-392.6 s of the suite (OBSERVED)
  room       a quiet night room tone: brown noise, low-passed, swelling slightly in the dark stretch (DRAWN)
  knees      a soft double thud when both knees land
  pats       a muffled card-on-earth thump for each wrong attempt, with grit
  dust       one faint tick for every dust particle when it lands (times from clip['dust_land'])
  brads      a metal snap when each hand goes on (hand A on the near wrist, hand B on the far wrist)
  grip/let   a paper tap when A pinches B and when A lets go
  stick      a wooden slide while the citizen rises on his stick
No archive audio: clip 6bb6d333 is silent in the library, and nothing is put in his mouth.
usage: python3 shots/weave/p04_hands/build_sound.py   -> shots/weave/p04_hands/passage.wav
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from weave_lib import WEAVE, SR, wav_read, wav_write, movavg, reverb

clip = json.load(open(os.path.join(WEAVE, 'clips', 'p04_hands.json')))
N, FPS = clip['clock']['frames'], clip['clock']['fps']
L = int(N / FPS * SR)
rng = np.random.default_rng(404)
off = clip['audio']['voice_offset']
voice = wav_read(os.path.join(WEAVE, clip['audio']['voice']))[int(off * SR):int(off * SR) + L]
voice = np.pad(voice, (0, max(0, L - len(voice))))

fx = np.zeros(L, np.float32)


def put(t, s, amp):
    i = int(t * SR)
    if i >= L or i < 0:
        return
    n = min(len(s), L - i)
    fx[i:i + n] += amp * s[:n]


def env(n, attack, decay):
    tt = np.arange(n) / SR
    return (1 - np.exp(-tt / max(attack, 1e-4))) * np.exp(-tt / decay)


def lowpass(x, n):
    return movavg(movavg(x, n), n)


def thud(f0=70, secs=0.28, grit=0.25):
    n = int(secs * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * (f0 * tt + 18 * (1 - np.exp(-tt * 30)) / 30)) * env(n, 0.002, 0.07)
    g = lowpass(rng.standard_normal(n), 6) * env(n, 0.001, 0.03) * grit
    return (body + g).astype(np.float32)


def tick(f0):
    n = int(0.018 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f0 * tt) * env(n, 0.0005, 0.004) + 0.4 * rng.standard_normal(n) * env(n, 0.0002, 0.002)).astype(np.float32)


def snap():
    n = int(0.22 * SR); tt = np.arange(n) / SR
    click = rng.standard_normal(n) * env(n, 0.0002, 0.003)
    ring = (np.sin(2 * np.pi * 2380 * tt) + 0.6 * np.sin(2 * np.pi * 3710 * tt) + 0.3 * np.sin(2 * np.pi * 5230 * tt)) * env(n, 0.0005, 0.05)
    return (click + 0.35 * ring).astype(np.float32)


def paper_tap():
    n = int(0.09 * SR)
    x = rng.standard_normal(n)
    x = x - lowpass(x, 20)            # keep the papery top
    return (x * env(n, 0.001, 0.018)).astype(np.float32)


def slide(secs):
    n = int(secs * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = lowpass(x, 4) - lowpass(x, 40)  # a band of wood-on-card friction
    grain = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 9 * tt + rng.uniform(0, 6)))
    shape = np.sin(np.pi * np.clip(tt / secs, 0, 1)) ** 0.7
    return (x * grain * shape).astype(np.float32)


events = []
for c in clip['contacts']:
    w, t = c['what'], c['t']
    if 'both knees' in w:
        put(t, thud(64), 0.55); put(t + 0.06, thud(72), 0.45); events.append((t, 'knees'))
    elif 'wrong attempt' in w:
        put(t, thud(95, 0.2, 0.6), 0.42); events.append((t, 'pat'))
    elif 'brad in' in w:
        put(t, snap(), 0.42); events.append((t, 'brad'))
    elif 'pinches' in w or 'lets go' in w:
        put(t, paper_tap(), 0.35); events.append((t, 'tap'))
    elif 'wrist tab' in w:
        put(t, thud(120, 0.12, 0.4), 0.25); events.append((t, 'press'))
for t in clip['dust_land']:
    put(t, tick(rng.uniform(3200, 6200)), rng.uniform(0.05, 0.11))
r0, r1 = clip['cit_rise']
put(r0, slide(r1 - r0 + 0.15), 0.12); events.append((r0, 'stick'))

# room tone: brown noise, low-passed; a little louder while the garden is dark
brown = np.cumsum(rng.standard_normal(L)).astype(np.float32)
brown -= movavg(brown, SR // 4)
brown /= np.abs(brown).max() + 1e-9
dark = np.repeat(np.array([fr['g']['dark'] for fr in clip['frames']], np.float32), SR // FPS)[:L]
dark = np.pad(dark, (0, L - len(dark)), mode='edge')
room = lowpass(brown, 30) * (0.05 + 0.08 * dark)

# duck the effects a touch under her words
speaking = np.zeros(L, np.float32)
T0 = clip['clock']['t0']
for wd in clip['words']:
    a, b = int((wd['t0'] - T0) * SR), int((wd['t1'] - T0) * SR)
    speaking[max(0, a):max(0, b)] = 1
duck = 1 - 0.35 * np.clip(movavg(speaking, int(0.2 * SR)), 0, 1)
fx_w = reverb(fx * duck, rng, 0.9, 0.25)
side = reverb(room, rng, 1.2, 1.0)
left = voice * 0.95 + fx_w + room + 0.15 * side
right = voice * 0.95 + fx_w + room - 0.15 * side
out = os.path.join(HERE, 'passage.wav')
wav_write(out, np.stack([left, right], 1))
print('wrote', out, round(L / SR, 2), 's;', len(events), 'contact sounds,', len(clip['dust_land']), 'dust ticks')
for t, k in sorted(events):
    print('  %6.2f %s' % (t, k))
