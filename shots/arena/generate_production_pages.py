#!/usr/bin/env python3
"""
GENERATE PRODUCTION PAGES
Builds:
1. shots/production.html (Master Production Bible & Reference Center for all 14 poems)
2. shots/poems/p01.html .. p14.html (14 standalone, deep-dive poem production kits)
"""
import os, json, glob, html

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS_DIR = os.path.join(HERE, '..')
BREAKDOWN_DIR = os.path.join(SHOTS_DIR, 'poems', 'breakdown')
POEMS_JSON = os.path.join(SHOTS_DIR, 'film', 'poems.json')
FOOTAGE_JSON = os.path.join(SHOTS_DIR, 'atlas_footage.json')
CATALOG_JSON = os.path.join(HERE, 'parts', 'kit3', 'v2', 'cut', 'catalog.json')
OUT_MASTER = os.path.join(SHOTS_DIR, 'production.html')
OUT_POEMS_DIR = os.path.join(SHOTS_DIR, 'poems')
os.makedirs(OUT_POEMS_DIR, exist_ok=True)

# Load master data
poems_meta = {p['num']: p for p in json.load(open(POEMS_JSON, 'r', encoding='utf-8'))}
footage_data = json.load(open(FOOTAGE_JSON, 'r', encoding='utf-8')).get('by_poem', {})
catalog = json.load(open(CATALOG_JSON, 'r', encoding='utf-8'))
catalog_by_sheet = {c['sheet']: c for c in catalog}

# Map characters/costumes to catalog sheets
def get_matching_rendered_sheets(poem_num, bodies):
    matched = []
    for c in catalog:
        s = c['sheet']
        # Check if sheet is relevant to this poem
        if f".{poem_num}." in s:
            matched.append(c)
        elif 'props.narrative.master' in s:
            matched.append(c)
        elif poem_num in ['01', '02', '03'] and 'black_tshirt' in s:
            matched.append(c)
        elif int(poem_num) >= 4 and 'red_black_sunglasses' in s:
            matched.append(c)
        elif poem_num in ['01', '02', '03', '07', '08', '09'] and 'ex.ex_jacket' in s:
            matched.append(c)
        elif poem_num in ['09', '13'] and 'woman' in s:
            matched.append(c)
        elif poem_num == '10' and 'vehicle.motorcycle' in s:
            matched.append(c)
        elif poem_num == '02' and 'ghost_child' in s:
            matched.append(c)
        elif poem_num in ['02', '13'] and 'young_poet' in s:
            matched.append(c)
        elif poem_num in ['02', '09'] and 'parents' in s:
            matched.append(c)
    return matched

# HTML helper
def esc(s):
    return html.escape(str(s or ''))

# Shared CSS styles
COMMON_STYLE = """
:root{
  --bg:#0d0b0a;--panel:#16120f;--panel-card:#1c1713;--line:#2a221c;--line-lit:#42362c;
  --ink:#efe6da;--dim:#9a8d7e;--card:#c79a62;--ok:#9fe08a;--bad:#ff7b6b;--acc:#e7a35a;
  --gold:#f5b942;--teal:#01acd4;--mono:'JetBrains Mono',ui-monospace,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 Inter,system-ui,sans-serif}
header.prod-header{display:flex;align-items:center;gap:12px;padding:12px max(18px,env(safe-area-inset-right)) 12px max(18px,env(safe-area-inset-left));border-bottom:1px solid var(--line);flex-wrap:wrap;position:sticky;top:0;background:var(--bg);z-index:10}
header.prod-header h1{font:400 24px 'Permanent Marker',cursive;margin:0;color:var(--acc)}
header.prod-header h1 small{font:12px var(--mono);color:var(--dim);margin-left:10px;letter-spacing:.08em}
header.prod-header a{color:var(--dim);font:12px var(--mono);text-decoration:none;border:1px solid var(--line);padding:5px 12px;border-radius:999px;transition:all .15s}
header.prod-header a:hover{color:var(--ink);border-color:var(--card)}
header.prod-header .sp{flex:1}
nav.p-nav{display:flex;gap:5px;flex-wrap:wrap;margin:10px 0}
nav.p-nav a{font:12px var(--mono);color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:4px 10px;text-decoration:none;transition:all .15s}
nav.p-nav a:hover{border-color:var(--card);color:var(--card)}
nav.p-nav a.active{background:var(--card);color:#16120f;font-weight:600;border-color:var(--card)}

main.prod-main{max-width:1380px;margin:0 auto;padding:24px max(18px,env(safe-area-inset-right)) 100px max(18px,env(safe-area-inset-left));display:grid;gap:36px}
h2{font:400 32px 'Permanent Marker',cursive;margin:0;color:var(--card)}
h3{font:600 18px Inter;margin:0;color:var(--ink)}
h4{font:600 14px var(--mono);margin:0;color:var(--acc);text-transform:uppercase;letter-spacing:.05em}
p{margin:0;max-width:80ch}
.dim{color:var(--dim)}

.card-box{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;display:grid;gap:16px}
.badge{font:11px var(--mono);padding:3px 9px;border-radius:999px;background:#241c14;border:1px solid var(--line);color:var(--card);display:inline-block}
.badge.ok{border-color:var(--ok);color:var(--ok)}
.badge.gold{border-color:var(--gold);color:var(--gold)}
.badge.teal{border-color:var(--teal);color:var(--teal)}

.grid-3{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.grid-2{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:18px}
.grid-parts{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}

.part-item{background:var(--panel-card);border:1px solid var(--line);border-radius:8px;padding:10px;display:flex;flex-direction:column;gap:8px}
.part-thumb{height:160px;background:#090807 url("data:image/svg+xml,%3Csvg width='16' height='16' viewBox='0 0 16 16' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='8' height='8' fill='%23120f0c'/%3E%3Crect x='8' y='8' width='8' height='8' fill='%23120f0c'/%3E%3Crect x='8' width='8' height='8' fill='%23181410'/%3E%3Crect y='8' width='8' height='8' fill='%23181410'/%3E%3C/svg%3E");border-radius:6px;display:flex;align-items:center;justify-content:center;padding:6px;overflow:hidden}
.part-thumb img{max-width:100%;max-height:100%;object-fit:contain;filter:drop-shadow(0 4px 6px rgba(0,0,0,.6))}

.foot-item{background:#120f0c;border:1px solid var(--line);border-radius:8px;padding:12px;display:grid;gap:6px}
.foot-item .title{font:600 13px var(--mono);color:var(--ink);word-break:break-all}
.foot-item .tags{display:flex;gap:4px;flex-wrap:wrap}
.foot-item .tag{font:10px var(--mono);background:#1a1510;border:1px solid var(--line);color:var(--dim);padding:1px 6px;border-radius:4px}

.shot-table{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}
.shot-table th,.shot-table td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}
.shot-table th{background:#110e0b;font:600 12px var(--mono);color:var(--acc)}
.shot-table tr:nth-child(even){background:#13100d}

.btn{font:600 12px Inter;color:#16120f;background:var(--card);border:0;border-radius:999px;padding:5px 14px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:6px}
.btn.ghost{background:none;color:var(--card);border:1px solid var(--card)}
.btn:hover{background:var(--gold);color:#16120f}
.btn.ghost:hover{background:rgba(199,154,98,.1);border-color:var(--gold);color:var(--gold)}

.hero-banner{background:radial-gradient(ellipse at top left,#2d2116 0%,#14100c 70%);border:1px solid var(--card);border-radius:14px;padding:28px;display:grid;gap:14px}
.hero-banner h1{font:400 36px 'Permanent Marker',cursive;margin:0;color:var(--gold)}
.hero-banner .meta-row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;font:13px var(--mono);color:var(--dim)}
"""

# Render individual standalone poem page
def generate_poem_page(num, b_data):
    p_meta = poems_meta.get(num, {})
    title = b_data.get('title', p_meta.get('title', f"Poem {num}"))
    district = p_meta.get('district_name', 'The Suite')
    tagline = p_meta.get('tagline', '')
    sets = b_data.get('sets', [])
    scenes = b_data.get('scenes', [])
    needs = b_data.get('needs', {})
    bodies = needs.get('bodies', [])
    props = needs.get('props', [])
    fx_list = needs.get('fx', [])
    footage_items = footage_data.get(num, [])
    rendered_sheets = get_matching_rendered_sheets(num, bodies)

    nav_links = "".join([f'<a href="p{n:02d}.html" class="{"active" if f"{n:02d}" == num else ""}">{n:02d}</a>' for n in range(1, 15)])

    # Format scenes and shots
    scenes_html = []
    for sc in scenes:
        shots_rows = []
        for sh in sc.get('shots', []):
            bodies_desc = "<br>".join([
                f"<b>{esc(b.get('role'))}</b> ({esc(b.get('costume'))}): {esc(b.get('view'))} · {esc(b.get('pose'))} · <i>{esc(b.get('action'))}</i>"
                for b in sh.get('bodies', [])
            ])
            props_desc = ", ".join([esc(p.get('id') if isinstance(p, dict) else p) for p in sh.get('props', [])]) or "—"
            shots_rows.append(f"""
              <tr>
                <td><b>{esc(sh.get('id'))}</b></td>
                <td><span class="badge">{esc(sh.get('framing'))}</span><br><span class="dim" style="font-size:11px">{esc(sh.get('camera'))}</span></td>
                <td>{esc(sh.get('set'))}</td>
                <td>{esc(sh.get('action'))}</td>
                <td>{bodies_desc}</td>
                <td>{props_desc}</td>
              </tr>
            """)
        
        scenes_html.append(f"""
          <div class="card-box" style="margin-top:14px">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
              <h3>Movement {esc(sc.get('movement'))} <small class="dim" style="font-size:13px;font-family:var(--mono)">({sc.get('seconds')}s)</small></h3>
              <span class="badge teal">Scene {esc(sc.get('id'))}</span>
            </div>
            <p style="font-style:italic;color:var(--dim);border-left:3px solid var(--card);padding-left:12px;margin:4px 0">"{esc(sc.get('lines'))}"</p>
            <p><b>Staging Treatment:</b> {esc(sc.get('treatment'))}</p>
            <table class="shot-table">
              <thead>
                <tr>
                  <th>Shot</th>
                  <th>Framing / Cam</th>
                  <th>Set</th>
                  <th>Action</th>
                  <th>Puppet Bodies</th>
                  <th>Props</th>
                </tr>
              </thead>
              <tbody>
                {''.join(shots_rows)}
              </tbody>
            </table>
          </div>
        """)

    # Format rendered parts
    parts_html = []
    for r in rendered_sheets:
        for pc in r.get('pieces', []):
            rel_img = f"../{pc['rel_path']}"
            parts_html.append(f"""
              <div class="part-item">
                <div class="part-thumb"><img src="{esc(rel_img)}" alt="{esc(pc['label'])}" loading="lazy"></div>
                <div style="font:600 12px var(--mono);color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="{esc(pc['label'])}">{esc(pc['label'])}</div>
                <div style="display:flex;justify-content:space-between;font:11px var(--mono);color:var(--dim)">
                  <span>{pc['bbox'][2]}×{pc['bbox'][3]}px</span>
                  <span class="badge ok">{len(pc['brads'])} Brads</span>
                </div>
                <a class="btn ghost" href="{esc(rel_img)}" download style="margin-top:4px;text-align:center;justify-content:center">Download</a>
              </div>
            """)

    # Format Props
    props_html = []
    for p in props:
        pid = p.get('id', '') if isinstance(p, dict) else str(p)
        what = p.get('what', '') if isinstance(p, dict) else ''
        scale = f"{p.get('scale_cm')} cm" if isinstance(p, dict) and p.get('scale_cm') else ''
        props_html.append(f"""
          <div style="background:var(--panel-card);border:1px solid var(--line);border-radius:8px;padding:12px;display:grid;gap:6px">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font:600 13px var(--mono);color:var(--gold)">{esc(pid)}</span>
              {f'<span class="badge">{esc(scale)}</span>' if scale else ''}
            </div>
            {f'<p class="dim" style="font-size:12px">{esc(what)}</p>' if what else ''}
          </div>
        """)

    # Format Sets
    sets_html = []
    for s in sets:
        sets_html.append(f"""
          <div style="background:var(--panel-card);border:1px solid var(--line);border-radius:8px;padding:12px;display:grid;gap:6px">
            <span style="font:600 13px var(--mono);color:var(--teal)">{esc(s.get('id'))}</span>
            <p class="dim" style="font-size:12px">{esc(s.get('what'))}</p>
          </div>
        """)

    # Format Footage Items
    foot_html = []
    for ft in footage_items:
        tags_chips = "".join([f'<span class="tag">{esc(t)}</span>' for t in ft.get('tags', [])])
        foot_html.append(f"""
          <div class="foot-item">
            <div class="title">{esc(ft.get('file'))}</div>
            <div style="display:flex;justify-content:space-between;font:11px var(--mono);color:var(--dim)">
              <span>Source: {esc(ft.get('source'))}</span>
              <span>{ft.get('dur')}s</span>
            </div>
            <div class="tags">{tags_chips}</div>
          </div>
        """)

    page_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poem {num} · {title} · Production Kit · WYGWYL</title>
<link rel="icon" href="../../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
{COMMON_STYLE}
</style>
</head>
<body>
<header class="prod-header">
  <a href="../production.html">← Production Master</a>
  <a href="../kits.html">Kits Explorer</a>
  <a href="{num}.html">Design brief, atlas &amp; prompts →</a>
  <a href="../../index.html">Suite Index</a>
  <span class="sp"></span>
  <span style="font:600 13px var(--mono);color:var(--card)">POEM {num}</span>
</header>
<main class="prod-main">
  <!-- Nav across poems -->
  <nav class="p-nav">{nav_links}</nav>

  <!-- Hero Header -->
  <section class="hero-banner">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px">
      <div>
        <span class="badge gold" style="font-size:12px;margin-bottom:6px">POEM {num} · PRODUCTION DESIGN BIBLE</span>
        <h1>{num}. {title}</h1>
        <p style="font-size:17px;color:var(--ink);max-width:70ch">{esc(tagline)}</p>
      </div>
      <div style="text-align:right;display:grid;gap:6px">
        <span class="badge teal" style="font-size:12px">District: {esc(district)}</span>
        <span class="dim" style="font:11px var(--mono)">{len(scenes)} Movements · {len(sets)} Sets · {len(props)} Props</span>
      </div>
    </div>
  </section>

  <!-- 1. The Cardboard Cut Parts & Modular Assets -->
  <section class="card-box">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      <div>
        <h2>🧩 Cardboard Puppet Parts &amp; Poses for Poem {num}</h2>
        <p class="dim">Physical cut cards with visible brass split-pin brads and eyelets, matched directly to this poem's choreographic requirements.</p>
      </div>
      <a class="btn" href="../kits.html#rendered-shelf">Browse All 140 Kit Parts →</a>
    </div>
    <div class="grid-parts">
      {''.join(parts_html) if parts_html else '<p class="dim" style="grid-column:1/-1;padding:20px;text-align:center">Parts linked from master kits.</p>'}
    </div>
  </section>

  <!-- 2. Sets and Props Specifications -->
  <section class="grid-2">
    <div class="card-box">
      <h2>🏛️ Stage Sets &amp; Places ({len(sets)})</h2>
      <p class="dim">Die-cut multiplane environments and cardboard scenic layers.</p>
      <div style="display:grid;gap:10px;margin-top:8px">
        {''.join(sets_html)}
      </div>
    </div>
    <div class="card-box">
      <h2>🧰 Narrative Props Kit ({len(props)})</h2>
      <p class="dim">Physical hand props, scale in centimeters, and joint attachment points.</p>
      <div style="display:grid;gap:10px;margin-top:8px;max-height:480px;overflow:auto">
        {''.join(props_html)}
      </div>
    </div>
  </section>

  <!-- 3. Archive Footage References & 3D Pointcloud Assets -->
  <section class="card-box">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      <div>
        <h2>🎞️ Archive Footage &amp; 3D Splat References ({len(footage_items)})</h2>
        <p class="dim">Curated camera shots, volumetric haze passes, and real-world reference footage matching Poem {num}.</p>
      </div>
      <span class="badge ok">1,367 Archive Assets Connected</span>
    </div>
    <div class="grid-3" style="margin-top:8px">
      {''.join(foot_html)}
    </div>
  </section>

  <!-- 4. Detailed Shot Breakdown & Choreography -->
  <section>
    <h2>🎬 Shot-by-Shot Scene Breakdown &amp; Choreography</h2>
    <p class="dim">Complete treatment, camera moves, and puppet body postures for each movement.</p>
    {''.join(scenes_html)}
  </section>
</main>
<script src="../../nav.js" defer></script>
</body>
</html>
"""
    out_path = os.path.join(OUT_POEMS_DIR, f"p{num}.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(page_html)
    return out_path

# Generate master portal shots/production.html
def generate_master_portal(breakdowns):
    nav_links = "".join([f'<a href="poems/p{n:02d}.html">{n:02d}</a>' for n in range(1, 15)])
    
    poem_cards = []
    for b in breakdowns:
        num = b['num']
        p_meta = poems_meta.get(num, {})
        title = b.get('title', p_meta.get('title', ''))
        tagline = p_meta.get('tagline', '')
        district = p_meta.get('district_name', 'The Suite')
        scenes = b.get('scenes', [])
        sets = b.get('sets', [])
        needs = b.get('needs', {})
        bodies = needs.get('bodies', [])
        props = needs.get('props', [])
        footage_items = footage_data.get(num, [])
        rendered_sheets = get_matching_rendered_sheets(num, bodies)
        
        # Thumbnail preview: first rendered sheet if available, or first pack image
        thumb_img = ""
        if rendered_sheets:
            thumb_img = rendered_sheets[0]['image']
        else:
            thumb_img = f"arena/parts/kit3/v2/packs/poet.{num}.action.jpg"

        poem_cards.append(f"""
          <div class="card-box" id="p{num}" style="transition:border-color .15s">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px">
              <div>
                <span class="badge gold" style="margin-bottom:4px">POEM {num}</span>
                <h3 style="font-size:22px;color:var(--ink);margin:2px 0">{num}. {title}</h3>
                <p class="dim" style="font-size:13px;max-width:60ch">{esc(tagline)}</p>
              </div>
              <span class="badge teal">District: {esc(district)}</span>
            </div>
            
            <div style="display:grid;grid-template-columns:minmax(0,180px) minmax(0,1fr);gap:14px;align-items:center;margin-top:6px">
              <a href="poems/p{num}.html" style="display:block;border-radius:6px;overflow:hidden;border:1px solid var(--line)">
                <img src="{esc(thumb_img)}" alt="Poem {num} visual" style="width:100%;height:100px;object-fit:cover;background:#fff;display:block">
              </a>
              <div style="display:grid;gap:6px;font:12px var(--mono)">
                <div style="display:flex;gap:8px;flex-wrap:wrap">
                  <span class="badge ok">{len(scenes)} Movements</span>
                  <span class="badge">{len(sets)} Stage Sets</span>
                  <span class="badge">{len(props)} Props</span>
                  <span class="badge ok">{len(footage_items)} Archive Shots</span>
                </div>
                <div class="dim" style="font-size:11px">Bodies: {esc(', '.join(bodies[:3]))}</div>
                <div style="margin-top:4px">
                  <a class="btn" href="poems/p{num}.html">Open Production Bible →</a>
                  <a class="btn ghost" href="kits.html#p{num}">Character Kits</a>
                </div>
              </div>
            </div>
          </div>
        """)

    master_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Production Design &amp; References Bible · WYGWYL</title>
<link rel="icon" href="../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
{COMMON_STYLE}
</style>
</head>
<body>
<header class="prod-header">
  <a href="../index.html">← Suite Index</a>
  <h1>WYGWYL Production Bible<small>EVERY POEM · EVERY PLACE · ALL PROPS &amp; KITS</small></h1>
  <span class="sp"></span>
  <a href="poems/index.html">Poem design pages (briefs, atlas, prompts) →</a>
  <a href="kits.html" style="color:var(--ok);border-color:var(--ok)">Character Kits (140 Parts) →</a>
  <a href="arena/parts/kit3/v2/kits.json">kits.json</a>
</header>
<main class="prod-main">
  <!-- Hero Banner -->
  <section class="hero-banner">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px">
      <div>
        <span class="badge gold" style="font-size:13px;margin-bottom:8px">MASTER PRODUCTION REFERENCE SYSTEM</span>
        <h1>Where You Go When You Leave</h1>
        <p style="font-size:17px;color:var(--ink);max-width:75ch">Complete production design bibles, 1,367 footage archive matches, and cardboard puppet engineering kits across all 14 poems. From the fire escape of Naraka to the cosmic ascent above the city.</p>
      </div>
      <div style="display:grid;gap:8px;text-align:right">
        <span class="badge ok" style="font-size:13px">14 Standalone Poem Bibles</span>
        <span class="badge gold" style="font-size:13px">17 Finished Rendered Sheets</span>
        <span class="badge teal" style="font-size:13px">140 Sliced Modular Cards</span>
      </div>
    </div>
    <nav class="p-nav" style="margin-top:10px">
      <span style="font:600 12px var(--mono);color:var(--dim);margin-right:8px;align-self:center">Jump to Poem:</span>
      {nav_links}
    </nav>
  </section>

  <!-- Production Grid -->
  <section style="display:grid;gap:18px">
    <h2>🎬 The 14 Poem Production Bibles</h2>
    <p class="dim">Click any poem to open its complete, standalone production bible with shot choreography, multiplane set layers, physical prop blueprints, and archive footage references.</p>
    <div class="grid-2">
      {''.join(poem_cards)}
    </div>
  </section>

  <!-- Quick Links Section -->
  <section class="card-box" style="border-color:var(--card)">
    <h2>🛠️ Production Assets &amp; Specifications Quick Access</h2>
    <div class="grid-3" style="margin-top:8px">
      <div style="background:var(--panel-card);border:1px solid var(--line);border-radius:8px;padding:16px;display:grid;gap:8px">
        <h3 style="color:var(--gold)">🧩 Puppet Kits Explorer</h3>
        <p class="dim" style="font-size:13px">All 140 die-cut transparent parts, 31 action replacement poses, 12 hand shapes, and 6 Chelsea boots with detected brass brads.</p>
        <a class="btn" href="kits.html#rendered-shelf">Launch Parts Explorer →</a>
      </div>
      <div style="background:var(--panel-card);border:1px solid var(--line);border-radius:8px;padding:16px;display:grid;gap:8px">
        <h3 style="color:var(--teal)">📜 Architectural Blueprint</h3>
        <p class="dim" style="font-size:13px">The complete analytical breakdown connecting spoken lines, 3D Gaussian splat camera grammar, and cardboard mechanics.</p>
        <a class="btn ghost" href="arena/POEMS_FOOTAGE_PUPPET_BLUEPRINT.md">View Markdown Blueprint →</a>
      </div>
      <div style="background:var(--panel-card);border:1px solid var(--line);border-radius:8px;padding:16px;display:grid;gap:8px">
        <h3 style="color:var(--ok)">🎞️ Footage Archive</h3>
        <p class="dim" style="font-size:13px">1,367 curated archive video clips across all 12 districts, complete with tags, durations, and lens specifications.</p>
        <a class="btn ghost" href="atlas_footage.json">Inspect atlas_footage.json →</a>
      </div>
    </div>
  </section>
</main>
<script src="../nav.js" defer></script>
</body>
</html>
"""
    with open(OUT_MASTER, 'w', encoding='utf-8') as f:
        f.write(master_html)
    return OUT_MASTER

def main():
    files = sorted(glob.glob(os.path.join(BREAKDOWN_DIR, '[0-9][0-9].json')))
    print(f"Generating production pages for {len(files)} poems...")
    
    breakdowns = []
    for fpath in files:
        b_data = json.load(open(fpath, 'r', encoding='utf-8'))
        num = b_data['num']
        out_p = generate_poem_page(num, b_data)
        breakdowns.append(b_data)
        print(f"  Generated {out_p}")
        
    master_path = generate_master_portal(breakdowns)
    print(f"Master production portal generated at {master_path}")

if __name__ == '__main__':
    main()
