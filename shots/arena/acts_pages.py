#!/usr/bin/env python3
"""
ONE PAGE PER ACT.

    python3 shots/arena/acts_pages.py     -> shots/acts/ACT-0NN.html  + index

acts.html is one 57 KB scroll holding all thirty-two. That is a compendium, and
a compendium is the wrong shape for work you return to: you cannot link someone
to a single challenge, you cannot see what is wrong with ACT-029 without passing
ACT-001 through ACT-028, and nothing has an address.

Each page carries everything this repository actually knows about that act:
the situation and success condition from the spec, the real authored beats from
bolas/bank/beats.json, the pose sheet for its vignette, and the technical result
for all three skins with the failing checks named. Where a check did not run it
says so rather than leaving a blank that reads as a pass.

Writes only new files, under shots/acts/.
"""
import json, os, glob, html, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SH = os.path.join(ROOT, 'shots')
OUT = os.path.join(SH, 'acts')
E = lambda s: html.escape(str(s or ''), quote=True)

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#17110a;color:#f0e3d0;font:15px/1.6 ui-monospace,Menlo,monospace;padding:0 18px 70px}
.w{max-width:1120px;margin:0 auto}
a{color:#e6a15c}
header{padding:22px 0 16px;border-bottom:2px solid #4a3a28}
.up{font-size:12px;letter-spacing:.14em;text-transform:uppercase}
h1{font:800 26px/1.15 ui-monospace,monospace;letter-spacing:.04em;margin:14px 0 6px;color:#f3e7d4}
h1 small{display:block;font:700 11px/1.6 ui-monospace,monospace;letter-spacing:.18em;
 text-transform:uppercase;color:#caa06a;margin-top:8px}
.sit{margin:16px 0 0;max-width:78ch;color:#d8c7ad}
.ok{margin:8px 0 0;max-width:78ch;color:#9a8468;font-size:13.5px}
h2{font:800 11px/1 ui-monospace,monospace;letter-spacing:.2em;text-transform:uppercase;
 color:#caa06a;margin:34px 0 12px;border-bottom:1px solid #4a3a28;padding-bottom:8px}
table{border-collapse:collapse;width:100%;font-size:13px}
td,th{border-bottom:1px solid #2a1f14;padding:6px 9px;text-align:left;vertical-align:top}
th{color:#a08a6a;font-weight:700;font-size:11px;letter-spacing:.1em;text-transform:uppercase}
.pass{color:#8ad88a;font-weight:700}.fail{color:#ff8a6a;font-weight:700}.na{color:#6a5a48}
.beat{color:#f0e3d0}.who{color:#a08a6a}
img.sheet{width:100%;border:1px solid #4a3a28;background:#0f0b06;display:block;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}
.card{border:1px solid #4a3a28;background:#0f0b06;padding:11px 12px}
.card b{display:block;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#caa06a;margin-bottom:7px}
.flag{color:#ff8a6a;font-size:12px;line-height:1.5}
.note{color:#8a7558;font-size:12.5px;max-width:80ch;margin-top:10px}
nav.pager{display:flex;gap:12px;justify-content:space-between;margin-top:34px;
 border-top:2px solid #4a3a28;padding-top:14px;font-size:13px}
ul.idx{list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:7px}
ul.idx a{display:block;border:1px solid #4a3a28;padding:9px 11px;text-decoration:none;background:#0f0b06}
ul.idx a:hover{background:#241a10}
ul.idx .id{color:#caa06a;font-size:11px;letter-spacing:.12em}
"""

def load():
    A = os.path.join(HERE)
    spec = json.load(open(os.path.join(A, 'spec', 'acting_arena_v0.2.json')))
    beats = json.load(open(os.path.join(A, 'bolas', 'bank', 'beats.json')))
    t2a, titles = {}, {}
    for f in sorted(glob.glob(os.path.join(A, 'bolas', 'bank', 'T1*.json'))):
        d = json.load(open(f)); a = d.get('after') or ''
        if 'ACT-' in a:
            cid = 'ACT-' + a.split('ACT-')[1][:3]
            t2a[cid] = d['id']; titles[cid] = d.get('title')
    clips = collections.defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(A, 'clips', '*__*.json'))):
        b = os.path.basename(f)[:-5]
        cid, skin = b.split('__')
        try: clips[cid][skin] = json.load(open(f))
        except Exception: pass
    return spec, beats, t2a, titles, clips

def tech_card(skin, clip):
    if not clip: return f'<div class="card"><b>{skin}</b><span class="na">no clip</span></div>'
    t = clip.get('technical') or {}
    r = t.get('result'); v = f'<span class="{"pass" if r=="pass" else "fail"}">{E(r).upper()}</span>'
    rows = []
    for k, tol in (('worst_planted_drift_cm_per_frame', 'tolerance_planted_drift_cm_per_frame'),
                   ('worst_brad_gap_cm', 'tolerance_brad_gap_cm'),
                   ('balanced_pct_of_grounded_frames', 'tolerance_balanced_pct'),
                   ('worst_axial_stretch_ratio', None)):
        if k in t:
            rows.append(f'{k.replace("_"," ").replace("cm per frame","cm/f")}: <b>{t[k]}</b>'
                        + (f' <span class="na">(tol {t[tol]})</span>' if tol and tol in t else ''))
    fl = t.get('flagged_frame_ranges') or {}
    nm = t.get('not_measured') or []
    return ('<div class="card"><b>' + E(skin) + ' &middot; ' + v + '</b>'
            + '<br>'.join(rows)
            + (('<div class="flag">' + '<br>'.join(f'{E(k)} — frames {E(x)}' for k, x in fl.items()) + '</div>')
               if fl else '')
            + (f'<div class="na" style="margin-top:7px">not measured: {E(", ".join(nm))}</div>' if nm else '')
            + '</div>')

def main():
    os.makedirs(OUT, exist_ok=True)
    spec, beats, t2a, titles, clips = load()
    ch = {c['id']: c for c in spec['challenges']}
    ids = sorted(ch)
    made = []
    for i, cid in enumerate(ids):
        c = ch[cid]; tid = t2a.get(cid)
        bs = beats.get(tid) or []
        sheet = f'../arena/gen_pack/poses/{cid}_{tid}.jpg' if tid else None
        have_sheet = tid and os.path.exists(os.path.join(HERE, 'gen_pack', 'poses', f'{cid}_{tid}.jpg'))
        prev = ids[i-1] if i else None; nxt = ids[i+1] if i+1 < len(ids) else None
        rows = ''.join(
            f'<tr><td>{b["f"]}</td><td class="who">{E(b.get("who"))}</td>'
            f'<td class="beat">{E(b.get("beat"))}</td></tr>' for b in sorted(bs, key=lambda x: x['f']))
        cl = clips.get(cid, {})
        body = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(cid)} &middot; {E(c['title'])} &middot; WYGWYL Acting Arena</title>
<style>{CSS}</style></head><body><div class="w">
<header><a class="up" href="index.html">&larr; all acts</a>
 &nbsp;<a class="up" href="../arena.html">arena</a>
 &nbsp;<a class="up" href="../arena-compare.html">compare</a>
<h1>{E(c['title'])}<small>{E(cid)} &middot; {E(c.get('family'))} &middot; bolas {E(tid)}</small></h1>
<p class="sit">{E(c.get('situation'))}</p>
<p class="ok">Passes when: {E(c.get('success_observation'))}</p>
</header>

<h2>Beats <small style="color:#6a5a48">{len(bs)} authored</small></h2>
{'<table><tr><th>frame</th><th>who</th><th>beat</th></tr>' + rows + '</table>' if rows
 else '<p class="na">No authored beats recorded for this vignette.</p>'}

<h2>The motion</h2>
{f'<img class="sheet" src="{sheet}" alt="{E(cid)} pose sheet">' if have_sheet
 else '<p class="na">No pose sheet built for this vignette yet.</p>'}

<h2>Technical</h2>
<div class="grid">{''.join(tech_card(s, cl.get(s)) for s in ('bolas','man','poet'))}</div>
<p class="note">Thresholds come from the spec's crash_lab_checks and are read by the verdict,
not restated beside it. A check that did not run says so; a blank is not a pass.</p>

<h2>Stress variations, not yet run</h2>
<p class="na">{E(' &middot; '.join(c.get('stress_variations') or []) or 'none listed')}</p>

<nav class="pager">
 <span>{f'<a href="{prev}.html">&larr; {prev}</a>' if prev else ''}</span>
 <span>{f'<a href="{nxt}.html">{nxt} &rarr;</a>' if nxt else ''}</span>
</nav>
</div></body></html>"""
        open(os.path.join(OUT, cid + '.html'), 'w').write(body)
        made.append((cid, c['title'], len(bs), have_sheet,
                     {s: ((cl.get(s) or {}).get('technical') or {}).get('result') for s in ('bolas','man','poet')}))

    li = ''.join(
        f'<li><a href="{cid}.html"><span class="id">{cid}</span><br>{E(t)}<br>'
        f'<span class="na">{n} beats &middot; '
        + ' '.join(f'<span class="{"pass" if v=="pass" else ("fail" if v else "na")}">{s}</span>'
                   for s, v in r.items()) + '</span></a></li>'
        for cid, t, n, _s, r in made)
    idx = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Acts &middot; WYGWYL Acting Arena</title><style>{CSS}</style></head><body><div class="w">
<header><a class="up" href="../arena.html">&larr; arena</a>
<h1>The Acts<small>{len(made)} challenges, one page each</small></h1>
<p class="sit">Every act has its own address. The beats are the authored ones from the Bolas
bank; the technical result is whatever the checks currently say, per skin, including when they
say nothing.</p></header>
<h2>All {len(made)}</h2><ul class="idx">{li}</ul></div></body></html>"""
    open(os.path.join(OUT, 'index.html'), 'w').write(idx)

    nb = sum(m[2] for m in made); ns = sum(1 for m in made if m[3])
    print(f'{len(made)} act pages + index -> shots/acts/')
    print(f'   {nb} authored beats across them, {ns} with a pose sheet')
    bad = [m[0] for m in made if m[2] == 0]
    if bad: print(f'   no beats for: {" ".join(bad)}')

if __name__ == '__main__':
    main()
