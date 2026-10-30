#!/usr/bin/env python3
"""The reels page: every poem's staged reel with its scenes' measured checks. Reads data/scenes/*.json, writes reels.html.  python3 tools/build_reels.py"""
import os, json, html
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); e = lambda x: html.escape(str(x if x is not None else ''))
idx = json.load(open(os.path.join(S, 'data/scenes/index.json')))['scenes']
poems = {}
for s in idx: poems.setdefault(s['id'][:2], []).append(s)
def row(s):
    d = json.load(open(os.path.join(S, f"data/scenes/{s['id']}.json"))); c = d.get('checks') or {}
    joins = d.get('joins') or []; warn = [k for k, v in c.items() if isinstance(v, dict) and v.get('pass') is False]
    st = 'pass' if c.get('pass') else 'fail'; g = ' · warn: ' + ', '.join(warn) if warn and c.get('pass') else ''
    fs = (c.get('foot_slide') or {}).get('value'); ce = (c.get('contact_error') or {}).get('value')
    return (f'<tr><td><a href="index.html?scene={e(s["id"])}">{e(s["id"])}</a></td><td>{e(s.get("title", "").split(" · ")[-1])}</td><td>{s.get("duration", 0):.1f} s</td>'
            f'<td class="{st}">{st}{e(g)}</td><td>{e(fs)}</td><td>{e(ce)}</td><td>{e(", ".join(sorted({j.get("kind", "") for j in joins})))} ({len(joins)})</td></tr>')
cards = ''
tot = sum(s.get('duration', 0) for s in idx)
for p, ss in poems.items():
    t = (ss[0].get('title') or '').split(' · ')[0]; dur = sum(s.get('duration', 0) for s in ss)
    cards += f"""<section id="p{p}"><h2>{p}</h2><p class="dim">{len(ss)} scenes · {dur:.0f} s</p>
<video controls preload="none" playsinline src="renders/poem_{p}.mp4" poster="data/scenes/{ss[len(ss) // 2]['id']}.sheet.jpg"></video>
<div class="tbl"><table><tr><th>scene</th><th>movement</th><th>length</th><th>checks</th><th>foot slide cm/f</th><th>contact %</th><th>archive joins</th></tr>{''.join(row(s) for s in ss)}</table></div></section>"""
toc = ''.join(f'<a href="#p{p}">{p}</a>' for p in poems)
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><title>Staged Reels · WYGWYL</title><link rel="icon" href="../../favicon.svg">
<link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet"><style>
:root{{--bg:#0d0b0a;--panel:#16120f;--line:#2a221c;--ink:#efe6da;--dim:#9a8d7e;--card:#c79a62;--ok:#9fe08a;--bad:#ff7b6b;--mono:'JetBrains Mono',ui-monospace,monospace}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}}
header{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:12px 16px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}}
header h1{{font:400 24px 'Permanent Marker',cursive;margin:0}}header a{{color:var(--dim);font:12px var(--mono);text-decoration:none;border:1px solid var(--line);padding:4px 10px;border-radius:999px}}
main{{max-width:1100px;margin:0 auto;padding:20px 16px 80px;display:grid;gap:36px}}section{{display:grid;gap:10px;min-width:0;scroll-margin-top:110px}}h2{{font:400 28px 'Permanent Marker',cursive;margin:0;color:var(--card)}}
p{{margin:0;max-width:76ch}}.dim{{color:var(--dim)}}video{{width:100%;background:#000;border-radius:8px;display:block}}
.tbl{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;white-space:nowrap}}th{{font:600 11.5px var(--mono);color:var(--dim)}}a{{color:var(--card)}}.pass{{color:var(--ok)}}.fail{{color:var(--bad)}}
</style></head><body><header><a href="../../index.html" id="wy-index">← Index</a><h1>Staged Reels</h1><span style="flex:1"></span><a href="index.html">Cut-Out Suite</a><a href="body.html">Body Lab</a><a href="cast.html">Cast</a><a href="sets.html">Sets</a><nav style="display:flex;gap:4px;flex-wrap:wrap">{toc}</nav></header>
<main><section><p style="font-size:17px">Every poem staged in the Cut-Out Suite: {len(idx)} scenes, {tot / 60:.1f} minutes of the reading. Puppets are sized by each set's solved scale, beats land on the words, and archive film opens in surfaces of the set, labelled as long as it shows.</p>
<p class="dim">"Pass" means the render's measurements hold (foot slide, reach, contact, scale, bodies, EX facing, off-frame, ground, word sync), not that the scene is good. Known limits: {e('6 scenes stand in for plates we still need (01.4, 05.2, 05.5, 13.1, 13.5, 13.6); many archive picks are weak in meaning because only 2,292 of 15,149 clips are cached; scenes 03.1, 03.2, 03.3, 03.4 and 03.6 have no bodies to measure.')} Per-scene notes: <a href="STAGED_01-07.md">01–07</a>, <a href="STAGED_08-14.md">08–14</a>.</p></section>{cards}</main><script src="../../nav.js" defer></script></body></html>"""
open(os.path.join(S, 'reels.html'), 'w').write(page); print(len(idx), 'scenes', round(tot / 60, 1), 'min')
