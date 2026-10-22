"""The stage's sound library: shots/stage/sfx/index.json + small mono MP3s.

    python3 shots/stage/sfx/build_sfx.py

Every recorded sound comes from the project's own libraries on disk (nothing downloaded, no invented URLs):
  WY   butterfly-halfworld/wygwyl/pack/audio  the ATLANTIS pack mined from the project's media (pack/pack.json),
       named by atlantis-standard.json (EarSketch schema) and labelled zero-shot by CLAP (labels.json)
  CH   butterfly-halfworld/wygwyl/chops       her voice, 1-3 word power phrases (chops.json)
  BF   butterfly-halfworld/audio/foley + audio/sound   the sister film's foley and room cues
       (written by harness/build-foley.mjs and build-sound.mjs: synthesised, deterministic)
Where no file on disk is the thing asked for, the id is still built so the stage can play *something*, but from
a deterministic recipe in the manner of shots/weave/build_sound.py (click, tap, room murmur). Those entries carry
"unsourced": true and "source": "synth: ..." so nobody mistakes them for recordings.

Output: 24 kHz mono MP3, 48 kbps, peak-normalised to -3 dBFS, trimmed to at most MAXDUR seconds.
"""
import json, os, subprocess, tempfile, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = '/home/user/hartswf0/butterfly-halfworld'
WY = os.path.join(HOME, 'wygwyl')
SR = 24000
MAXDUR = 9.0
rng = np.random.default_rng(1956)

# id, source path (relative to HOME) or None for synth, tags, note, options
REC = [
    ('sfx.rain', 'wygwyl/pack/audio/ATL_LOOP_BGDEEPVINTAGER_47.mp3', ['rain', 'weather', 'loop', 'bed'], 'CLAP RAIN 0.98 (labels.json)', {'loop': True}),
    ('sfx.rain.heavy', 'wygwyl/pack/audio/ATL_TEXTURE_BGGRITTYBROADC_02.mp3', ['rain', 'storm', 'weather', 'loop'], 'CLAP RAIN 0.99', {'loop': True}),
    ('sfx.wind', 'wygwyl/pack/audio/ATL_BED_WIND_28.mp3', ['wind', 'weather', 'loop', 'outdoor'], 'pack BED from LIZARD/TEMP_LAYERS/wind.wav; CLAP ATMOS', {'loop': True}),
    ('sfx.wind.open', 'audio/foley/wind_lot.wav', ['wind', 'outdoor', 'loop'], 'butterfly foley wind_lot (open air)', {'loop': True}),
    ('sfx.waves', 'wygwyl/pack/audio/ATL_TEXTURE_AMBIENT_10.mp3', ['waves', 'sea', 'water', 'ocean', 'loop', 'shore'], 'nearest: CLAP ATMOS/OCEANIC 0.91 ambience; no surf recording found', {'loop': True}),
    ('sfx.water', 'audio/sound/water.wav', ['water', 'pool', 'lap', 'loop'], 'butterfly room cue "water" (pool)', {'loop': True}),
    ('sfx.water.drip', 'audio/foley/drip.wav', ['water', 'drip'], 'butterfly foley drip', {}),
    ('sfx.sea.drone', 'wygwyl/pack/audio/ATL_LOOP_DRONE_01.mp3', ['drone', 'sea', 'atlantis', 'loop', 'oceanic'], 'pack LOOP drone, CLAP SUBBASS/OCEANIC', {'loop': True}),
    ('sfx.crowd', 'wygwyl/pack/audio/ATL_LOOP_AF5A3002_17.mp3', ['crowd', 'street', 'party', 'loop', 'location'], 'nearest: location audio from shoot camera clip AF5A3002 (CLAP STREET); no crowd-walla recording found', {'loop': True}),
    ('sfx.street', 'wygwyl/pack/audio/ATL_LOOP_AF5A3002_16.mp3', ['street', 'location', 'noise', 'loop'], 'location audio, shoot camera clip AF5A3002 (CLAP NOISEFX/STREET)', {'loop': True}),
    ('sfx.footsteps', 'audio/foley/step_stone.wav', ['footsteps', 'step', 'walk', 'stone'], 'butterfly foley step_stone', {}),
    ('sfx.footsteps.soft', 'audio/foley/step_soft.wav', ['footsteps', 'step', 'walk', 'soft'], 'butterfly foley step_soft', {}),
    ('sfx.footsteps.stairs', 'audio/foley/stairs.wav', ['footsteps', 'stairs', 'descend'], 'butterfly foley stairs', {}),
    ('sfx.door', 'audio/foley/door_fire.wav', ['door', 'open', 'close', 'heavy'], 'butterfly foley door_fire (bar, swing, seal)', {}),
    ('sfx.door.glass', 'audio/foley/door_glass.wav', ['door', 'glass', 'booth'], 'butterfly foley door_glass (phone-booth door)', {}),
    ('sfx.wings', 'audio/sound/wingbeat.wav', ['wings', 'flap', 'bird', 'angel', 'loop'], 'butterfly cue wingbeat (9 Hz soft beats)', {'loop': True}),
    ('sfx.glass.set', 'audio/foley/glass_set.wav', ['glass', 'set down', 'cup'], 'butterfly foley glass_set', {}),
    ('sfx.glass.tap', 'audio/sound/tap_ring.wav', ['glass', 'tap', 'ring'], 'butterfly cue tap_ring', {}),
    ('sfx.vinyl.crackle', 'wygwyl/pack/audio/ATL_TEXTURE_VINYLCRACKLE_08.mp3', ['vinyl', 'record', 'crackle', 'dj', 'loop'], 'pack TEXTURE from LIZARD/TEMP_FIXED/vinyl_crackle.wav', {'loop': True}),
    ('sfx.chimes', 'wygwyl/pack/audio/ATL_TEXTURE_AMBIENTCHIMES_14.mp3', ['chimes', 'bells', 'magic', 'loop'], 'pack TEXTURE ambient_chimes', {'loop': True}),
    ('sfx.portal.open', 'wygwyl/pack/audio/ATL_RISER_NATIVEDELAYED_11.mp3', ['portal', 'riser', 'magic', 'open', 'whoosh'], 'pack RISER, CLAP RISER 0.93', {}),
    ('sfx.portal.hum', 'wygwyl/pack/audio/ATL_BED_NATIVEDELAYED_01.mp3', ['portal', 'atmos', 'loop', 'hum'], 'pack BED, CLAP ATMOS/OCEANIC', {'loop': True}),
    ('sfx.lights.hum', 'audio/sound/fluorescent.wav', ['lights', 'hum', 'booth', 'neon', 'loop'], 'butterfly cue fluorescent (mains hum)', {'loop': True}),
    ('sfx.projector', 'audio/sound/projector.wav', ['projector', 'film', 'loop', 'machine'], 'butterfly cue projector (12 Hz shutter)', {'loop': True}),
    ('sfx.paper', 'audio/foley/paper.wav', ['paper', 'letter', 'page'], 'butterfly foley paper', {}),
    ('sfx.photo.turn', 'audio/foley/photo_turn.wav', ['photo', 'card', 'turn'], 'butterfly foley photo_turn', {}),
    ('sfx.coat', 'audio/foley/coat.wav', ['cloth', 'coat', 'movement'], 'butterfly foley coat', {}),
    ('sfx.breath.in', 'audio/foley/breath_in.wav', ['breath', 'body'], 'butterfly foley breath_in', {}),
    ('sfx.breath.out', 'audio/foley/breath_out.wav', ['breath', 'sigh', 'body'], 'butterfly foley breath_out', {}),
    ('sfx.shutter', 'audio/foley/shutter_close.wav', ['shutter', 'machine', 'stop'], 'butterfly foley shutter_close', {}),
    ('sfx.room.night', 'audio/sound/room_lot.wav', ['room', 'night', 'outdoor', 'loop', 'ambience'], 'butterfly room cue room_lot', {'loop': True}),
    # her voice, from the chop kit: the poem naming its own sounds
    ('sfx.voice.tambourine', 'wygwyl/chops/03/03_C02.mp3', ['voice', 'tambourine', '03'], 'her reading, chop 03_C02 "a tambourine sounds"', {}),
    ('sfx.voice.dj', 'wygwyl/chops/07/07_C01.mp3', ['voice', 'dj', '07'], 'her reading, chop 07_C01 "DJ turn"', {}),
    ('sfx.voice.waves', 'wygwyl/chops/04/04_C04.mp3', ['voice', 'waves', '04'], 'her reading, chop 04_C04 "waves will calm"', {}),
    ('sfx.voice.winds', 'wygwyl/chops/04/04_C05.mp3', ['voice', 'wind', '04'], 'her reading, chop 04_C05 "winds will mute"', {}),
    ('sfx.voice.heart', 'wygwyl/chops/04/04_C06.mp3', ['voice', 'heart', '04'], 'her reading, chop 04_C06 "A familiar heart"', {}),
    ('sfx.voice.rain', 'wygwyl/chops/03/03_C22.mp3', ['voice', 'rain', '03'], 'her reading, chop 03_C22 "rotted by rain"', {}),
]

ALIASES = {
    'sfx.footsteps': ['sfx.step', 'sfx.walk', 'sfx.footstep'], 'sfx.door': ['sfx.door.open', 'sfx.door.close', 'sfx.door.slam'],
    'sfx.door.glass': ['sfx.booth.door', 'sfx.phone.booth.door'], 'sfx.waves': ['sfx.sea', 'sfx.ocean', 'sfx.shore'],
    'sfx.wings': ['sfx.wing', 'sfx.wings.flap', 'sfx.flap'], 'sfx.crowd': ['sfx.party', 'sfx.crowd.murmur', 'sfx.walla'],
    'sfx.lights.hum': ['sfx.neon', 'sfx.lamp.hum', 'sfx.booth.hum', 'sfx.lights.on'], 'sfx.portal.open': ['sfx.portal', 'sfx.whoosh', 'sfx.riser'],
    'sfx.vinyl.crackle': ['sfx.vinyl', 'sfx.record'], 'sfx.rain': ['sfx.storm.rain'], 'sfx.water': ['sfx.splash.small'],
    'sfx.engine.start': ['sfx.engine', 'sfx.car.start', 'sfx.ignition'], 'sfx.engine.idle': ['sfx.car.idle', 'sfx.motor'],
    'sfx.engine.rev': ['sfx.car.rev', 'sfx.motorcycle.rev', 'sfx.motorcycle'], 'sfx.phone.ring': ['sfx.phone', 'sfx.ring', 'sfx.telephone'],
    'sfx.phone.hangup': ['sfx.phone.hang_up', 'sfx.hangup', 'sfx.phone.down'], 'sfx.phone.pickup': ['sfx.phone.lift', 'sfx.phone.up'],
    'sfx.phone.dial': ['sfx.dial', 'sfx.phone.dialtone'], 'sfx.heartbeat': ['sfx.heart', 'sfx.heart.beat', 'sfx.pulse'],
    'sfx.clock.tick': ['sfx.clock', 'sfx.tick', 'sfx.hourglass'], 'sfx.fire.crackle': ['sfx.fire', 'sfx.flames'],
    'sfx.tambourine': ['sfx.tambourine.jingle', 'sfx.jingle'], 'sfx.vinyl.scratch': ['sfx.scratch', 'sfx.dj.scratch'],
    'sfx.glass.shatter': ['sfx.shatter', 'sfx.glass.break'], 'sfx.card.tap': ['sfx.tap', 'sfx.cardboard', 'sfx.brad'],
    'sfx.knob.detent': ['sfx.knob', 'sfx.click', 'sfx.dj.knob'], 'sfx.chimes': ['sfx.sparkle', 'sfx.magic'],
}


# ── synth recipes (in the manner of shots/weave/build_sound.py: seeded noise, decaying partials) ──
def env(n, a=0.005, d=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4))
    return e * (np.exp(-t * d) if d else 1)

def movavg(x, n):
    c = np.cumsum(np.concatenate([[0.0], x])); y = (c[n:] - c[:-n]) / n
    return np.concatenate([np.full(n // 2, y[0]), y, np.full(len(x) - len(y) - n // 2, y[-1])])

def place(out, t, s):
    i = int(t * SR); m = min(len(s), len(out) - i)
    if m > 0: out[i:i + m] += s[:m]

def click(f0=2400, amp=0.25):          # weave build_sound.click
    n = int(0.03 * SR); tt = np.arange(n) / SR
    return (rng.standard_normal(n) * np.exp(-tt * 260) * 0.6 + np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 140)) * amp

def tap(amp=0.35, f=140):              # weave build_sound.tap
    n = int(0.08 * SR); tt = np.arange(n) / SR
    return (movavg(rng.standard_normal(n), 24) * 6 * np.exp(-tt * 60) + np.sin(2 * np.pi * f * tt) * np.exp(-tt * 45) * 0.5) * amp

def tone(fs, dur, amps=None):
    t = np.arange(int(dur * SR)) / SR
    return sum((amps[k] if amps else 1) * np.sin(2 * np.pi * f * t) for k, f in enumerate(fs))

def engine(dur, f0, f1, rough=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 + (f1 - f0) * np.clip(t / dur, 0, 1) ** 0.6
    ph = 2 * np.pi * np.cumsum(f) / SR
    pulse = sum(np.sin(k * ph) / k for k in range(1, 9))          # firing pulses
    noise = movavg(rng.standard_normal(n), 6) * rough
    am = 0.7 + 0.3 * np.sin(ph / 2)                                 # cylinder unevenness
    return (pulse * am + noise) * 0.3

def synth(name):
    if name == 'engine.start':
        out = np.zeros(int(2.6 * SR))
        for k in range(5): place(out, 0.08 * k, tap(0.3, 90))                        # starter cranks
        place(out, 0.45, engine(2.1, 22, 38) * np.minimum(1, np.arange(int(2.1 * SR)) / (0.15 * SR)))
        return out
    if name == 'engine.idle': return engine(4.0, 26, 26, 0.3)
    if name == 'engine.rev':
        a = engine(1.2, 28, 90); b = engine(1.3, 90, 32)
        return np.concatenate([a, b])
    if name == 'phone.ring':                                                       # bell trill, ring-ring, pause
        out = np.zeros(int(4.0 * SR))
        for b in (0.0, 0.5):
            for k in range(int(0.4 * 20)):
                n = int(0.05 * SR); place(out, b + k / 20, tone([1200, 1640, 2310], 0.05, [1, .5, .25])[:n] * env(n, 0.001, 50) * 0.3)
        return out
    if name == 'phone.dial':                                                       # rotary dial: wind, then pulses
        out = np.zeros(int(2.2 * SR))
        place(out, 0, movavg(rng.standard_normal(int(0.35 * SR)), 30) * 0.4 * env(int(0.35 * SR), 0.02))
        for k in range(7): place(out, 0.5 + k * 0.1, click(1800, 0.3))
        for k in range(4): place(out, 1.4 + k * 0.1, click(1800, 0.3))
        return out
    if name == 'phone.pickup':
        out = np.zeros(int(0.8 * SR)); place(out, 0, tap(0.4, 220)); place(out, 0.06, click(3000, 0.2))
        place(out, 0.25, tone([350, 440], 0.5) * 0.08); return out
    if name == 'phone.hangup':
        out = np.zeros(int(0.7 * SR)); place(out, 0, click(2600, 0.25)); place(out, 0.03, tap(0.6, 110)); place(out, 0.12, tap(0.25, 160)); return out
    if name == 'heartbeat':
        out = np.zeros(int(2.0 * SR))
        for b in (0.0, 1.0):
            for dt, a in ((0, 0.9), (0.22, 0.6)):
                n = int(0.16 * SR); place(out, b + dt, tone([48, 62], 0.16) * env(n, 0.01, 22) * a * 0.5)
        return out
    if name == 'clock.tick':
        out = np.zeros(int(2.0 * SR))
        for k in range(4): place(out, 0.5 * k, click(3200 if k % 2 else 2600, 0.22))
        return out
    if name == 'tambourine':
        out = np.zeros(int(1.6 * SR))
        for k, t in enumerate((0, 0.4, 0.6, 0.8, 1.2)):
            n = int(0.35 * SR); jing = (rng.standard_normal(n) - movavg(rng.standard_normal(n), 4)) * 0.5
            jing += tone([5200, 6900, 8100], 0.35, [.3, .2, .15])[:n] * rng.uniform(.5, 1)
            place(out, t, jing * env(n, 0.002, 14) * 0.35); place(out, t, tap(0.2, 300))
        return out
    if name == 'vinyl.scratch':
        n = int(1.0 * SR); t = np.arange(n) / SR
        rate = np.sin(2 * np.pi * 2.5 * t) * np.exp(-t * 1.2)                        # back and forth
        ph = np.cumsum(np.abs(rate)) * 800 / SR
        s = np.sin(2 * np.pi * ph * 3) * 0.4 + movavg(rng.standard_normal(n), 3) * np.abs(rate) * 0.6
        return s * 0.5
    if name == 'glass.shatter':
        out = np.zeros(int(2.0 * SR))
        place(out, 0, tap(0.6, 400))
        for k in range(60):
            t = abs(rng.normal(0.05, 0.25)); f = rng.uniform(2500, 9000); n = int(0.12 * SR)
            place(out, t, tone([f, f * 1.47], 0.12, [1, .5])[:n] * env(n, 0.0005, rng.uniform(25, 60)) * rng.uniform(0.03, 0.12))
        return out
    if name == 'fire.crackle':
        n = int(6.0 * SR); out = movavg(rng.standard_normal(n), 40) * 0.25
        for k in range(110): place(out, rng.uniform(0, 6), click(rng.uniform(900, 4000), rng.uniform(0.04, 0.22)))
        return out
    if name == 'card.tap': return np.concatenate([tap(0.4), np.zeros(int(0.2 * SR))])
    if name == 'knob.detent':
        out = np.zeros(int(0.8 * SR))
        for k in range(5): place(out, k * 0.12, click(2400, 0.25))
        return out
    raise KeyError(name)

SYN = [
    ('sfx.engine.start', 'engine.start', ['engine', 'car', 'motorcycle', 'start'], 'no engine recording on disk'),
    ('sfx.engine.idle', 'engine.idle', ['engine', 'car', 'motorcycle', 'idle', 'loop'], 'no engine recording on disk'),
    ('sfx.engine.rev', 'engine.rev', ['engine', 'motorcycle', 'rev'], 'no engine recording on disk'),
    ('sfx.phone.ring', 'phone.ring', ['phone', 'ring', 'booth', 'bell'], 'no telephone recording on disk'),
    ('sfx.phone.dial', 'phone.dial', ['phone', 'dial', 'rotary'], 'no telephone recording on disk'),
    ('sfx.phone.pickup', 'phone.pickup', ['phone', 'handset', 'pick up'], 'no telephone recording on disk'),
    ('sfx.phone.hangup', 'phone.hangup', ['phone', 'handset', 'hang up'], 'no telephone recording on disk'),
    ('sfx.heartbeat', 'heartbeat', ['heart', 'heartbeat', 'pulse', 'loop'], 'no heartbeat recording on disk'),
    ('sfx.clock.tick', 'clock.tick', ['clock', 'tick', 'hourglass', 'time', 'loop'], 'weave click recipe'),
    ('sfx.tambourine', 'tambourine', ['tambourine', 'jingle', 'percussion'], 'no tambourine recording on disk (her voice says it: sfx.voice.tambourine)'),
    ('sfx.vinyl.scratch', 'vinyl.scratch', ['vinyl', 'scratch', 'dj', 'decks'], 'no scratch recording on disk (crackle is real: sfx.vinyl.crackle)'),
    ('sfx.glass.shatter', 'glass.shatter', ['glass', 'shatter', 'break'], 'no breaking-glass recording on disk (sfx.glass.set is real)'),
    ('sfx.fire.crackle', 'fire.crackle', ['fire', 'crackle', 'flames', 'loop'], 'no fire recording on disk'),
    ('sfx.card.tap', 'card.tap', ['cardboard', 'tap', 'brad', 'contact'], 'weave tap recipe (grip / release)'),
    ('sfx.knob.detent', 'knob.detent', ['knob', 'click', 'dj', 'detent'], 'weave detent click recipe'),
]
LOOPS = {'sfx.engine.idle', 'sfx.heartbeat', 'sfx.clock.tick', 'sfx.fire.crackle'}


def encode(x, dst):
    x = np.asarray(x, np.float32)[:int(MAXDUR * SR)]
    x = x / max(1e-6, np.abs(x).max()) * 0.708                                  # -3 dBFS
    f = int(0.006 * SR); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        with wave.open(tmp.name, 'w') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp.name, '-ac', '1', '-ar', str(SR), '-b:a', '48k', dst], check=True)
    os.unlink(tmp.name)
    return round(len(x) / SR, 3)


def decode(src):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


def main():
    out, missing = [], []
    for sid, src, tags, note, opt in REC:
        p = os.path.join(HOME, src)
        if not os.path.exists(p):
            missing.append(sid); continue
        fn = sid[4:].replace('.', '_') + '.mp3'
        dur = encode(decode(p), os.path.join(HERE, fn))
        out.append({'id': sid, 'file': 'sfx/' + fn, 'dur': dur, 'tags': tags, 'loop': bool(opt.get('loop')),
                    'source': 'butterfly-halfworld/' + src, 'note': note, 'kind': 'voice' if sid.startswith('sfx.voice') else 'recording'})
    for sid, rec, tags, why in SYN:
        fn = sid[4:].replace('.', '_') + '.mp3'
        dur = encode(synth(rec), os.path.join(HERE, fn))
        out.append({'id': sid, 'file': 'sfx/' + fn, 'dur': dur, 'tags': tags, 'loop': sid in LOOPS, 'source': 'synth: shots/stage/sfx/build_sfx.py ' + rec,
                    'note': why, 'kind': 'synth', 'unsourced': True})
    have = {e['id'] for e in out}
    for e in out:
        e['aliases'] = [a for a in ALIASES.get(e['id'], []) if a not in have]
    # FORMATS.md section 4: a plain list. file is relative to shots/stage/. kind: recording | voice (her reading) |
    # synth (unsourced: no recording on disk, built from a recipe). The stage resolves an id by id, aliases, then longest prefix.
    json.dump(out, open(os.path.join(HERE, 'index.json'), 'w'), indent=1)
    idx = {'unsourced': [e['id'] for e in out if e.get('unsourced')]}
    size = sum(os.path.getsize(os.path.join(HERE, os.path.basename(e['file']))) for e in out)
    print(len(out), 'sounds,', len(idx['unsourced']), 'synth stand-ins,', round(size / 1024), 'KB; missing sources:', missing)


if __name__ == '__main__':
    main()
