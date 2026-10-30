#!/usr/bin/env python3
"""Stage 2: one reel per poem (08-14) from the rendered scenes, in reading order, with the reading.

  python3 shots/suite/tools/stage2_reels.py [NN ...]  ->  shots/suite/renders/poem_NN.mp4

The scenes' windows tile the poem's reading (tools/stage2_windows.py), so the reel is the scenes' pictures concatenated in
order of suite_in, laid over one continuous cut of the reading (first scene in -> last scene out), 1280 wide, x264 crf 26.
Each scene's own mp4 is first shrunk in place to 1280 wide, crf 28 (the film the page shows), to keep the repository light.
"""
import os, sys, json, subprocess, tempfile
H = os.path.dirname(os.path.abspath(__file__)); SUITE = os.path.dirname(H)
sys.path.insert(0, H)
import prep
REN = os.path.join(SUITE, 'renders')
WIN = json.load(open(os.path.join(SUITE, 'data/scenes/stage2_windows.json')))

def probe(f, what):
    return subprocess.run(['ffprobe', '-v', 'error', '-show_entries', what, '-of', 'default=nw=1:nk=1', f], capture_output=True, text=True).stdout.split()

def shrink(f):
    if int(probe(f, 'stream=width')[0]) <= 1280: return
    tmp = f[:-4] + '.tmp.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-vf', 'scale=1280:-2', '-c:v', 'libx264', '-crf', '28', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, f)

def reel(poem):
    sc = sorted(WIN[poem]['scenes'], key=lambda s: s['in'])
    files = [os.path.join(REN, s['id'] + '.mp4') for s in sc]
    missing = [f for f in files if not os.path.exists(f)]
    if missing: raise SystemExit('missing renders: ' + ', '.join(missing))
    for f in files: shrink(f)
    t_in, t_out = sc[0]['in'], sc[-1]['out']
    with tempfile.TemporaryDirectory() as td:
        lst = os.path.join(td, 'list.txt')
        open(lst, 'w').write(''.join(f"file '{f}'\n" for f in files))
        out = os.path.join(REN, f'poem_{poem}.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                        '-ss', f'{t_in:.3f}', '-to', f'{t_out:.3f}', '-i', prep.safe(prep.SUITE_AUDIO),
                        '-map', '0:v', '-map', '1:a', '-vf', 'scale=1280:-2,fps=24', '-c:v', 'libx264', '-crf', '26', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '128k', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-shortest', '-movflags', '+faststart', out], check=True)
    d = float(probe(out, 'format=duration')[0])
    print(f'poem_{poem}.mp4', ' '.join(s['id'] for s in sc), f'{d:.1f}s (reading {t_out - t_in:.1f}s)', f'{os.path.getsize(out) / 1e6:.1f} MB')

if __name__ == '__main__':
    for p in sys.argv[1:] or sorted(WIN): reel(p)
