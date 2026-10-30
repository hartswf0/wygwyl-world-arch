#!/usr/bin/env python3
"""One reel per poem: the poem's scene renders in order, with the reading (stage lane 1).

  python3 shots/suite/tools/stage_reels.py 01 02 ...      -> shots/suite/renders/poem_NN.mp4 (+ poem_NN_720p.mp4 if large)

The scene windows tile the poem's reading end to end (tools/stage_windows.py), and each scene film carries its own
cut of the reading, so concatenating the films in order plays the poem's reading through. Re-encoded at crf 26
(x264, 1080p) so the reel stays small; a 720p preview is written when the 1080p reel is over 40 MB.
"""
import os, sys, json, subprocess, tempfile
SUITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(SUITE, 'renders')

def shrink(f, max_kbps=1200):
    """re-encode a scene film at crf 26 when render.mjs (crf 20) left it heavier than max_kbps"""
    pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=bit_rate', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip()
    if not pr or int(pr) / 1000 <= max_kbps: return
    tmp = f[:-4] + '.tmp.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-c:v', 'libx264', '-crf', '26', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, f)

def reel(p):
    idx = json.load(open(os.path.join(SUITE, 'data/scenes/index.json')))['scenes']
    ids = [s['id'] for s in idx if s['id'].startswith(p + '.')]
    films = [os.path.join(R, i + '.mp4') for i in ids]
    miss = [f for f in films if not os.path.exists(f)]
    if miss: raise SystemExit('missing renders: ' + ', '.join(os.path.basename(m) for m in miss))
    for f in films: shrink(f)
    out = os.path.join(R, f'poem_{p}.mp4')
    args = ['ffmpeg', '-v', 'error', '-y']
    for f in films: args += ['-i', f]
    fc = ''.join(f'[{i}:v:0][{i}:a:0]' for i in range(len(films))) + f'concat=n={len(films)}:v=1:a=1[v][a]'
    args += ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '26', '-preset', 'medium', '-pix_fmt', 'yuv420p',
             '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out]
    subprocess.run(args, check=True)
    mb = os.path.getsize(out) / 1e6
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out], capture_output=True, text=True).stdout)
    print(f'poem_{p}.mp4  {len(films)} scenes  {dur:.1f} s  {mb:.1f} MB')
    if mb > 40:
        prev = os.path.join(R, f'poem_{p}_720p.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', out, '-vf', 'scale=1280:-2', '-c:v', 'libx264', '-crf', '28', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', prev], check=True)
        print(f'poem_{p}_720p.mp4  {os.path.getsize(prev) / 1e6:.1f} MB')

if __name__ == '__main__':
    for p in sys.argv[1:] or ['01', '02', '03', '04', '05', '06', '07']: reel(p)
