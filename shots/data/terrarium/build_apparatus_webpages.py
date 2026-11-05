#!/usr/bin/env python3
"""
Build Dedicated Interactive Webpages for:
  1. Each of the 6 Narrative Apparatus Paradigms (across all 14 poems):
       - shots/apparatus_opt1_pointcloud.html   (Option I: True 3D points.ply WebGL/Canvas Point Cloud + Depth-Occluded Worldtext)
       - shots/apparatus_opt2_multiplane.html   (Option II: 3D Isometric Exploded Multiplane Stratigraphy + Golden Riverbed Laws)
       - shots/apparatus_opt3_perspective.html  (Option III: Solved 3D Perspective Grid, Horizon/VP & Animation Line Layout + Assembly Manuscript)
       - shots/apparatus_opt4_perceptual.html   (Option IV: Pixel-Accurate SAM2 Contours, Vector Program & Perceptual ΔE Compiler)
       - shots/apparatus_opt5_kits.html         (Option V: Tactile Cut-Out Multiplane Set & Prop Kits Workbench + Brass-Brad Loupe)
       - shots/apparatus_opt6_xray.html         (Option VI: Unobstructed 4-Layer Optical X-Ray & Shared Common-Place Echo Curtain)
  2. Each of the 14 Poems (all 6 paradigms + all Common Place views + 4K contact sheet + H.264 film for that poem):
       - shots/poem_01_apparatus.html .. shots/poem_14_apparatus.html
  3. Master Cross-Link Bar + URL Query Params (?poem=NN&mode=M) in shots/vesper_apparatus.html
"""

import json
from pathlib import Path

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch")
SHOTS_DIR = ROOT / "shots"
BUNDLE_PATH = SHOTS_DIR / "data/terrarium/seeing_spacetime_films/vesper_world_bundle.json"

PARADIGM_META = [
    {
        "mode": 1,
        "slug": "apparatus_opt1_pointcloud.html",
        "short": "OPT I · 3D POINT CLOUD",
        "title": "Option I — True 3D Metric Point Cloud (points.ply) & Depth-Occluded Worldtext",
        "accent": "#ffbe52",
        "master_sheet": "data/terrarium/seeing_spacetime_films/all_14_poems_pointcloud_worldtext_sheet.png",
        "subtitle": "Live binary points.ply (129,264 vertices per view) + metric Z-plane worldtext occluded by foreground architecture across all 14 poems",
    },
    {
        "mode": 2,
        "slug": "apparatus_opt2_multiplane.html",
        "short": "OPT II · EXPLODED MULTIPLANE",
        "title": "Option II — 3D Isometric Exploded Multiplane Stratigraphy & Golden Riverbed Laws",
        "accent": "#5ce4ff",
        "master_sheet": "data/terrarium/seeing_spacetime_films/all_14_poems_exploded_multiplane_sheet.png",
        "subtitle": "Separated P0–P6 painted planes (multiplane/exploded.jpg) with metric Z medians, parallax multipliers & Golden Riverbed laws (riverbed_NN.json)",
    },
    {
        "mode": 3,
        "slug": "apparatus_opt3_perspective.html",
        "short": "OPT III · PERSPECTIVE & LAYOUT",
        "title": "Option III — Solved 3D Perspective Grid, Horizon/VP & Animation Line Layout",
        "accent": "#82f5af",
        "master_sheet": "data/terrarium/seeing_spacetime_films/all_14_poems_perspective_layout_sheet.png",
        "subtitle": "Solved 3D perspective floor grid (cartoon/layout_sheet.png) ↔ traditional animation line layout (multiplane/layout_drawing.png) + assembly manuscripts",
    },
    {
        "mode": 4,
        "slug": "apparatus_opt4_perceptual.html",
        "short": "OPT IV · SAM2 & ΔE COMPILER",
        "title": "Option IV — Pixel-Accurate SAM2 Contours, Vector Program & Perceptual ΔE Compiler",
        "accent": "#ff82c3",
        "master_sheet": "data/terrarium/seeing_spacetime_films/all_14_poems_semantic_perceptual_sheet.png",
        "subtitle": "Pixel-accurate SAM2 object boundaries (overlay.jpg), SVG vector reconstruction & ΔE error map (compare.jpg), and 5-level squint SSIM pyramid",
    },
    {
        "mode": 5,
        "slug": "apparatus_opt5_kits.html",
        "short": "OPT V · TACTILE CUT-OUT KITS",
        "title": "Option V — Tactile Cut-Out Multiplane Set & Prop Kits Workbench",
        "accent": "#ffbe52",
        "master_sheet": "data/terrarium/seeing_spacetime_films/all_14_poems_tactile_kits_sheet.png",
        "subtitle": "Physical multiplane cardboard craft kits (poems/kits/NN.*.jpg) with brass-brad pivots (+) & grip crosses (+), prop build cards & puppet breakdowns",
    },
    {
        "mode": 6,
        "slug": "apparatus_opt6_xray.html",
        "short": "OPT VI · X-RAY & ECHO CURTAIN",
        "title": "Option VI — Unobstructed 4-Layer Optical X-Ray & Shared Common-Place Echo Curtain",
        "accent": "#5ce4ff",
        "master_sheet": "data/terrarium/seeing_spacetime_films/all_14_poems_xray_echo_sheet.png",
        "subtitle": "4-seam optical peel: Original Still ↔ Cartoon Cel ↔ Blueprint Line Layout ↔ Paired Echo Common Place + horizon-anchored poem verse",
    },
]


def build_global_nav_html(active_slug: str, poems: list) -> str:
    """Builds a compact top navigation bar linking the Master Hub, all 6 Paradigm pages, and all 14 Poem pages."""
    p_links = []
    hub_cls = "nav-pill active" if active_slug == "vesper_apparatus.html" else "nav-pill"
    p_links.append(f'<a class="{hub_cls}" href="vesper_apparatus.html">ALL 14×6 HUB</a>')
    for pm in PARADIGM_META:
        cls = "nav-pill active" if active_slug == pm["slug"] else "nav-pill"
        p_links.append(f'<a class="{cls}" href="{pm["slug"]}">{pm["short"]}</a>')

    poem_links = []
    for p in poems:
        ns = f"{int(p['num']):02d}"
        pslug = f"poem_{ns}_apparatus.html"
        cls = "poem-pill active" if active_slug == pslug else "poem-pill"
        poem_links.append(f'<a class="{cls}" href="{pslug}" title="Poem {ns}: {p["title"]}">P{ns}</a>')

    return f"""
<nav class="global-apparatus-nav">
  <div class="gnav-group">
    <span class="gnav-label">PARADIGM WEBPAGES:</span>
    {''.join(p_links)}
  </div>
  <div class="gnav-group">
    <span class="gnav-label">POEM WEBPAGES (01–14):</span>
    {''.join(poem_links)}
  </div>
</nav>
"""


GLOBAL_NAV_CSS = """
  .global-apparatus-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    padding: 6px 14px;
    background: #05070b;
    border-bottom: 1px solid rgba(92, 228, 255, 0.22);
    font-family: "SF Mono", "Menlo", "Monaco", monospace;
    font-size: 10px;
    flex-shrink: 0;
  }
  .gnav-group {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
  }
  .gnav-label {
    color: #8ea3b8;
    font-weight: 700;
    margin-right: 4px;
    letter-spacing: 0.05em;
  }
  .nav-pill, .poem-pill {
    color: #d5e2ee;
    text-decoration: none;
    padding: 3px 7px;
    border-radius: 3px;
    background: #0e141d;
    border: 1px solid rgba(142, 163, 184, 0.25);
    transition: all 0.12s ease;
  }
  .nav-pill:hover, .poem-pill:hover {
    border-color: #5ce4ff;
    color: #ffffff;
    background: rgba(92, 228, 255, 0.14);
  }
  .nav-pill.active, .poem-pill.active {
    background: rgba(92, 228, 255, 0.22);
    border-color: #5ce4ff;
    color: #5ce4ff;
    font-weight: 700;
  }
"""


def generate_paradigm_webpage(pm: dict, poems: list) -> str:
    mode = pm["mode"]
    slug = pm["slug"]
    title = pm["title"]
    accent = pm["accent"]
    subtitle = pm["subtitle"]
    master_sheet = pm["master_sheet"]
    nav_html = build_global_nav_html(slug, poems)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>WYGWYL — {title}</title>
<style>
  :root {{
    --bg: #07090d;
    --panel: #0d1118;
    --panel-2: #121822;
    --border: rgba(92, 228, 255, 0.22);
    --accent: {accent};
    --cyan: #5ce4ff;
    --amber: #ffbe52;
    --green: #82f5af;
    --pink: #ff82c3;
    --text: #e6eef6;
    --muted: #8ea3b8;
    --mono: "SF Mono", "Menlo", "Monaco", "Consolas", monospace;
    --serif: "Georgia", "Iowan Old Style", serif;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--mono);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  {GLOBAL_NAV_CSS}
  header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    background: #0a0e14;
    border-bottom: 1px solid var(--border);
    gap: 12px;
    flex-shrink: 0;
  }}
  .brand-title {{
    font-size: 13px;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 0.05em;
  }}
  .brand-sub {{
    font-size: 11px;
    color: var(--muted);
    margin-top: 2px;
  }}
  .view-mode-bar {{
    display: flex;
    gap: 6px;
  }}
  .v-btn {{
    background: #101620;
    color: var(--text);
    border: 1px solid rgba(142, 163, 184, 0.3);
    padding: 6px 12px;
    font-family: var(--mono);
    font-size: 11px;
    cursor: pointer;
    border-radius: 3px;
  }}
  .v-btn.active, .v-btn:hover {{
    background: rgba(92, 228, 255, 0.16);
    border-color: var(--accent);
    color: var(--accent);
    font-weight: 700;
  }}
  .workspace {{
    flex: 1;
    display: grid;
    grid-template-columns: 310px 1fr 410px;
    min-height: 0;
  }}
  .sidebar {{
    background: var(--panel);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow-y: auto;
    padding: 10px;
    gap: 10px;
  }}
  .inspector {{
    background: var(--panel);
    border-left: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow-y: auto;
    padding: 12px;
    gap: 12px;
  }}
  .section-title {{
    font-size: 10px;
    letter-spacing: 0.08em;
    color: var(--accent);
    text-transform: uppercase;
    border-bottom: 1px solid rgba(92, 228, 255, 0.18);
    padding-bottom: 4px;
    margin-bottom: 6px;
  }}
  .poem-card {{
    display: flex;
    gap: 8px;
    align-items: center;
    padding: 6px;
    background: var(--panel-2);
    border: 1px solid transparent;
    border-radius: 4px;
    cursor: pointer;
    margin-bottom: 5px;
    transition: all 0.12s ease;
  }}
  .poem-card:hover {{
    border-color: rgba(92, 228, 255, 0.4);
  }}
  .poem-card.active {{
    border-color: var(--accent);
    background: rgba(92, 228, 255, 0.12);
  }}
  .poem-card img {{
    width: 84px;
    height: 47px;
    object-fit: cover;
    border-radius: 2px;
    border: 1px solid rgba(255,255,255,0.12);
    flex-shrink: 0;
  }}
  .poem-card-info {{
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }}
  .poem-card-num {{
    font-size: 11px;
    font-weight: 700;
    color: var(--accent);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .poem-card-sub {{
    font-size: 10px;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .view-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 5px;
  }}
  .view-chip {{
    padding: 5px 6px;
    background: #0f151f;
    border: 1px solid rgba(142, 163, 184, 0.22);
    border-radius: 3px;
    font-size: 10px;
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .view-chip.active {{
    border-color: var(--green);
    color: var(--green);
    background: rgba(130, 245, 175, 0.12);
    font-weight: 700;
  }}
  .stage-wrap {{
    position: relative;
    background: #040609;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }}
  .canvas-box {{
    flex: 1;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 0;
    overflow: hidden;
  }}
  canvas {{
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    aspect-ratio: 16 / 9;
    display: block;
    background: #06090e;
  }}
  #matrixGridView {{
    display: none;
    flex: 1;
    overflow-y: auto;
    padding: 14px;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 12px;
    align-content: start;
  }}
  .matrix-cell {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.12s ease, border-color 0.12s ease;
  }}
  .matrix-cell:hover {{
    border-color: var(--accent);
    transform: translateY(-2px);
  }}
  .matrix-cell img {{
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    display: block;
  }}
  .matrix-cell-cap {{
    padding: 7px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
  }}
  .controls-bar {{
    padding: 8px 14px;
    background: #0a0e15;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
    font-size: 11px;
  }}
  .ctrl-group {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  input[type="range"] {{
    accent-color: var(--accent);
    width: 120px;
  }}
  .data-card {{
    background: var(--panel-2);
    border: 1px solid rgba(142, 163, 184, 0.2);
    border-radius: 4px;
    padding: 9px;
    font-size: 11px;
    line-height: 1.45;
  }}
  .verse-text {{
    font-family: var(--serif);
    font-size: 13px;
    color: #f4ebd9;
    white-space: pre-line;
    line-height: 1.45;
  }}
</style>
</head>
<body>
{nav_html}
<header>
  <div>
    <div class="brand-title">{title.upper()}</div>
    <div class="brand-sub">{subtitle}</div>
  </div>
  <div class="view-mode-bar">
    <button class="v-btn active" id="btnInteractive" onclick="setDisplayMode('interactive')">INTERACTIVE STAGE (16:9)</button>
    <button class="v-btn" id="btnAll14Grid" onclick="setDisplayMode('grid')">ALL 14 POEMS MATRIX GRID</button>
    <button class="v-btn" id="btnMaster4K" onclick="setDisplayMode('master4k')">4K 14-POEM CONTACT SHEET</button>
    <a class="v-btn" id="btnOpenPoemPage" href="poem_01_apparatus.html" style="text-decoration:none">OPEN POEM WEBPAGE →</a>
  </div>
</header>

<div class="workspace">
  <aside class="sidebar">
    <div>
      <div class="section-title">All 14 Poems ({pm['short']})</div>
      <div id="poemList"></div>
    </div>
    <div>
      <div class="section-title">Common Place Views in Poem</div>
      <div class="view-grid" id="viewGrid"></div>
    </div>
  </aside>

  <main class="stage-wrap">
    <div class="canvas-box" id="canvasBox">
      <canvas id="stageCanvas" width="1920" height="1080"></canvas>
    </div>
    <div id="matrixGridView"></div>
    <div class="controls-bar">
      <div class="ctrl-group">
        <label>Camera / Curtain Scrub (X):</label>
        <input type="range" id="scrubX" min="0" max="100" value="35" />
      </div>
      <div class="ctrl-group">
        <label>Metric Depth Plane (Z):</label>
        <input type="range" id="scrubZ" min="1.2" max="24.0" step="0.2" value="4.8" />
        <span id="scrubZVal">4.8m</span>
      </div>
      <div class="ctrl-group">
        <label>Worldtext / Layer Opacity:</label>
        <input type="range" id="textAlpha" min="0" max="100" value="95" />
      </div>
      <button class="v-btn" id="toggleExactBtn">Mode: Pre-Rendered 3D Plate + Live Scrub</button>
      <button class="v-btn" id="togglePlyBtn" style="{'display:inline-block' if mode == 1 else 'display:none'}">Load Live Binary points.ply (129K pts)</button>
    </div>
  </main>

  <aside class="inspector">
    <div>
      <div class="section-title">Poem Verse & Scene Treatment</div>
      <div class="data-card verse-text" id="verseBox">Loading...</div>
    </div>
    <div>
      <div class="section-title">Golden Riverbed Law & Architecture</div>
      <div class="data-card" id="riverbedBox">Loading...</div>
    </div>
    <div>
      <div class="section-title">Multiplane Stack (P0–P6) & Camera</div>
      <div class="data-card" id="planesBox">Loading...</div>
    </div>
    <div>
      <div class="section-title">Verbatim Midjourney Prompt & Staging</div>
      <div class="data-card" id="promptBox" style="color:var(--muted)">Loading...</div>
    </div>
  </aside>
</div>

<script>
const PARADIGM_MODE = {mode};
const MASTER_SHEET_URL = "{master_sheet}";
const state = {{
  bundle: null,
  poemIdx: 0,
  viewIdx: 0,
  displayMode: "interactive",
  scrubX: 0.35,
  scrubZ: 4.8,
  textAlpha: 0.95,
  useExactPlate: true,
  livePlyMode: false,
  plyPoints: null,
  images: {{}},
  t: 0,
}};

const canvas = document.getElementById("stageCanvas");
const ctx = canvas.getContext("2d");

function loadImage(src) {{
  if (!src) return Promise.resolve(null);
  if (state.images[src]) return Promise.resolve(state.images[src]);
  return new Promise((resolve) => {{
    const img = new Image();
    img.onload = () => {{ state.images[src] = img; resolve(img); }};
    img.onerror = () => resolve(null);
    img.src = src;
  }});
}}

function getPoemTextString(poem) {{
  if (typeof poem.poem_text === "string" && poem.poem_text.trim() && !poem.poem_text.startsWith("{{")) return poem.poem_text;
  if (Array.isArray(poem.full_text)) {{
    return poem.full_text.map((x) => (x && typeof x === "object" ? x.line || "" : String(x))).filter(Boolean).join("\\n");
  }}
  return String(poem.full_text || "");
}}

async function loadBinaryPly(plyUrl) {{
  const res = await fetch(plyUrl);
  const buf = await res.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let headerEnd = 0;
  const dec = new TextDecoder("ascii");
  const headStr = dec.decode(bytes.slice(0, 2048));
  const idx = headStr.indexOf("end_header\\n");
  if (idx === -1) return null;
  headerEnd = idx + "end_header\\n".length;
  const body = buf.slice(headerEnd);
  const stride = 15; // float32 x,y,z (12) + uint8 r,g,b (3)
  const count = Math.floor(body.byteLength / stride);
  const dv = new DataView(body);
  const step = Math.max(1, Math.floor(count / 65000));
  const pts = [];
  for (let i = 0; i < count; i += step) {{
    const off = i * stride;
    const x = dv.getFloat32(off, true);
    const y = dv.getFloat32(off + 4, true);
    const z = -dv.getFloat32(off + 8, true);
    const r = dv.getUint8(off + 12);
    const g = dv.getUint8(off + 13);
    const b = dv.getUint8(off + 14);
    if (z > 0.4) pts.push({{ x, y, z, r, g, b }});
  }}
  pts.sort((a, b) => b.z - a.z);
  return pts;
}}

function setDisplayMode(m) {{
  state.displayMode = m;
  document.getElementById("btnInteractive").classList.toggle("active", m === "interactive");
  document.getElementById("btnAll14Grid").classList.toggle("active", m === "grid");
  document.getElementById("btnMaster4K").classList.toggle("active", m === "master4k");
  const cBox = document.getElementById("canvasBox");
  const gBox = document.getElementById("matrixGridView");
  if (m === "grid") {{
    cBox.style.display = "none";
    gBox.style.display = "grid";
  }} else {{
    cBox.style.display = "flex";
    gBox.style.display = "none";
    if (m === "master4k") loadImage(MASTER_SHEET_URL);
  }}
}}

function renderSidebar() {{
  const pList = document.getElementById("poemList");
  pList.innerHTML = "";
  state.bundle.poems.forEach((p, idx) => {{
    const ns = String(p.num).padStart(2, "0");
    const optImg = `data/terrarium/seeing_spacetime_films/poem_${{ns}}_opt${{PARADIGM_MODE}}.jpg`;
    const card = document.createElement("div");
    card.className = "poem-card" + (idx === state.poemIdx ? " active" : "");
    card.innerHTML = `
      <img src="${{optImg}}" alt="Poem ${{ns}}" />
      <div class="poem-card-info">
        <div class="poem-card-num">${{ns}} · ${{p.title}}</div>
        <div class="poem-card-sub">Hero ${{p.hero_view_id || ''}} ↔ Echo ${{p.echo_view_id || ''}}</div>
      </div>
    `;
    card.onclick = () => selectPoem(idx);
    pList.appendChild(card);
  }});

  const gBox = document.getElementById("matrixGridView");
  gBox.innerHTML = "";
  state.bundle.poems.forEach((p, idx) => {{
    const ns = String(p.num).padStart(2, "0");
    const optImg = `data/terrarium/seeing_spacetime_films/poem_${{ns}}_opt${{PARADIGM_MODE}}.jpg`;
    const cell = document.createElement("div");
    cell.className = "matrix-cell";
    cell.innerHTML = `
      <img src="${{optImg}}" alt="Poem ${{ns}}" />
      <div class="matrix-cell-cap">
        <strong style="color:var(--accent)">POEM ${{ns}} · ${{p.title.toUpperCase()}}</strong>
        <span style="color:var(--muted)">Hero ${{p.hero_view_id || ''}} ↔ Echo ${{p.echo_view_id || ''}}</span>
      </div>
    `;
    cell.onclick = () => {{
      selectPoem(idx);
      setDisplayMode("interactive");
    }};
    gBox.appendChild(cell);
  }});
}}

async function selectPoem(pIdx) {{
  state.poemIdx = pIdx;
  const poem = state.bundle.poems[pIdx];
  const ns = String(poem.num).padStart(2, "0");
  document.getElementById("btnOpenPoemPage").href = `poem_${{ns}}_apparatus.html`;
  renderSidebar();
  const heroId = poem.hero_view_id;
  const hIdx = Math.max(0, (poem.views || []).findIndex((v) => v.id === heroId));
  await selectView(hIdx);
}}

async function selectView(vIdx) {{
  state.viewIdx = vIdx;
  const poem = state.bundle.poems[state.poemIdx];
  const views = poem.views || [];
  const vGrid = document.getElementById("viewGrid");
  vGrid.innerHTML = "";
  views.forEach((v, idx) => {{
    const chip = document.createElement("div");
    chip.className = "view-chip" + (idx === vIdx ? " active" : "");
    chip.textContent = `${{v.id}} · ${{v.place_name || ""}}`;
    chip.onclick = () => selectView(idx);
    vGrid.appendChild(chip);
  }});

  const view = views[vIdx] || {{}};
  const sd = view.dir || view.shot_dir || "";
  const ns = String(poem.num).padStart(2, "0");
  const optPath = `data/terrarium/seeing_spacetime_films/poem_${{ns}}_opt${{PARADIGM_MODE}}.jpg`;
  view._optPath = optPath;
  view._assets = view.assets || {{
    image: `out/${{sd}}/image.jpg`,
    cel: `out/${{sd}}/cartoon/cel.png`,
    layout_sheet: `out/${{sd}}/cartoon/layout_sheet.png`,
    planes_gs: `out/${{sd}}/cartoon/planes_gs.png`,
    exploded: `out/${{sd}}/multiplane/exploded.jpg`,
    layout_drawing: `out/${{sd}}/multiplane/layout_drawing.png`,
    plane_map: `out/${{sd}}/multiplane/plane_map.jpg`,
    overlay: `out/${{sd}}/overlay.jpg`,
    compare: `out/${{sd}}/program/compare.jpg`,
    perceive: `out/${{sd}}/program/perceive.jpg`,
    points_ply: `out/${{sd}}/points.ply`,
  }};

  await Promise.all([
    loadImage(optPath),
    loadImage(view._assets.image),
    loadImage(view._assets.cel),
    loadImage(view._assets.exploded),
    loadImage(view._assets.plane_map),
    loadImage(view._assets.layout_sheet),
    loadImage(view._assets.layout_drawing),
    loadImage(view._assets.overlay),
    loadImage(view._assets.compare),
    loadImage(view._assets.perceive),
  ]);

  if (state.livePlyMode && PARADIGM_MODE === 1) {{
    state.plyPoints = await loadBinaryPly(view._assets.points_ply);
  }}

  // Update Inspector
  const sc0 = (poem.breakdown_scenes || [])[0] || {{}};
  const pText = getPoemTextString(poem).split("\\n").slice(0, 8).join("\\n");
  document.getElementById("verseBox").textContent = sc0.lines
    ? `[SCENE ${{sc0.id}} · ${{sc0.movement || ""}}]\\n“${{sc0.lines}}”\\n\\n${{pText}}`
    : pText;

  const rb = poem.riverbed || {{}};
  document.getElementById("riverbedBox").innerHTML = `
    <div><strong style="color:var(--amber)">Core Identity:</strong> ${{rb.core_identity || poem.essence || ""}}</div>
    <div style="margin-top:4px"><strong style="color:var(--cyan)">Mutable Flow:</strong> ${{(rb.mutable_variables || []).join(", ")}}</div>
    <div style="margin-top:4px"><strong style="color:var(--green)">World Rules:</strong> ${{(rb.world_rules || []).join(" · ")}}</div>
  `;

  const planesHtml = (view.planes || []).map((pl) => {{
    const zm = typeof pl.z_m === "number" ? `${{pl.z_m.toFixed(2)}}m` : "∞";
    const par = typeof pl.parallax === "number" ? `×${{pl.parallax.toFixed(2)}}` : "";
    return `<div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,0.06);padding:2px 0"><span style="color:var(--cyan)">${{pl.id}} ${{pl.name || ""}}</span><span>Z=${{zm}} ${{par}}</span></div>`;
  }}).join("");
  document.getElementById("planesBox").innerHTML = planesHtml || "No plane metadata.";
  document.getElementById("promptBox").textContent = view.prompt || "";
}}

function drawFitContain(img, x, y, w, h, bg = "#06090e") {{
  ctx.fillStyle = bg;
  ctx.fillRect(x, y, w, h);
  if (!img) return;
  const scale = Math.min(w / img.width, h / img.height);
  const nw = img.width * scale;
  const nh = img.height * scale;
  ctx.drawImage(img, x + (w - nw) / 2, y + (h - nh) / 2, nw, nh);
}}

function renderStage() {{
  if (!state.bundle || state.displayMode === "grid") return;
  const W = canvas.width;
  const H = canvas.height;
  ctx.fillStyle = "#06090e";
  ctx.fillRect(0, 0, W, H);

  if (state.displayMode === "master4k") {{
    drawFitContain(state.images[MASTER_SHEET_URL], 0, 0, W, H);
    return;
  }}

  const poem = state.bundle.poems[state.poemIdx];
  const view = (poem.views || [])[state.viewIdx];
  if (!view || !view._assets) return;

  if (state.livePlyMode && PARADIGM_MODE === 1 && state.plyPoints) {{
    const pts = state.plyPoints;
    const angle = (state.scrubX - 0.5) * 0.45 + Math.sin(state.t * 1.3) * 0.05;
    const ca = Math.cos(angle), sa = Math.sin(angle);
    const fx = W * 0.72, fy = W * 0.72, cx = W * 0.5, cy = H * 0.52;
    const zPiv = state.scrubZ;
    for (let i = 0; i < pts.length; i++) {{
      const p = pts[i];
      const dz = p.z - zPiv;
      const xr = p.x * ca + dz * sa;
      const zr = -p.x * sa + dz * ca + zPiv;
      if (zr <= 0.5) continue;
      const u = (cx + (xr / zr) * fx) | 0;
      const v = (cy - (p.y / zr) * fy) | 0;
      if (u >= 0 && u < W && v >= 0 && v < H) {{
        ctx.fillStyle = `rgb(${{p.r}},${{p.g}},${{p.b}})`;
        ctx.fillRect(u, v, 3, 3);
      }}
    }}
    return;
  }}

  const optImg = state.images[view._optPath];
  const A = view._assets;
  if (state.useExactPlate && optImg && view.id === poem.hero_view_id) {{
    const shift = (state.scrubX - 0.35) * 28;
    drawFitContain(optImg, shift * 0.3, 0, W, H);
  }} else {{
    // Live multi-asset composite for ANY of the 97 Common Place views!
    if (PARADIGM_MODE === 1) {{
      drawFitContain(state.images[A.image], 0, 0, W, H);
    }} else if (PARADIGM_MODE === 2) {{
      drawFitContain(state.images[A.exploded], 0, 0, W * 0.62, H);
      drawFitContain(state.images[A.plane_map], W * 0.62, 0, W * 0.38, H);
    }} else if (PARADIGM_MODE === 3) {{
      drawFitContain(state.images[A.layout_sheet], 0, 0, W * state.scrubX, H);
      drawFitContain(state.images[A.layout_drawing], W * state.scrubX, 0, W * (1 - state.scrubX), H);
    }} else if (PARADIGM_MODE === 4) {{
      drawFitContain(state.images[A.overlay], 0, 0, W * 0.5, H);
      drawFitContain(state.images[A.compare], W * 0.5, 0, W * 0.5, H * 0.65);
      drawFitContain(state.images[A.perceive], W * 0.5, H * 0.65, W * 0.5, H * 0.35);
    }} else if (PARADIGM_MODE === 5) {{
      drawFitContain( optImg || state.images[A.image], 0, 0, W, H);
    }} else {{
      const s1 = Math.floor(W * state.scrubX * 0.65);
      const s2 = Math.floor(W * (0.35 + state.scrubX * 0.55));
      drawFitContain(state.images[A.image], 0, 0, W, H);
      if (state.images[A.cel]) {{
        ctx.save();
        ctx.beginPath(); ctx.rect(s1, 0, s2 - s1, H); ctx.clip();
        drawFitContain(state.images[A.cel], 0, 0, W, H);
        ctx.restore();
      }}
      if (state.images[A.layout_drawing]) {{
        ctx.save();
        ctx.beginPath(); ctx.rect(s2, 0, W - s2, H); ctx.clip();
        drawFitContain(state.images[A.layout_drawing], 0, 0, W, H);
        ctx.restore();
      }}
    }}
  }}
}}

document.getElementById("scrubX").oninput = (e) => {{ state.scrubX = Number(e.target.value) / 100; }};
document.getElementById("scrubZ").oninput = (e) => {{
  state.scrubZ = Number(e.target.value);
  document.getElementById("scrubZVal").textContent = `${{state.scrubZ.toFixed(1)}}m`;
}};
document.getElementById("textAlpha").oninput = (e) => {{ state.textAlpha = Number(e.target.value) / 100; }};
document.getElementById("toggleExactBtn").onclick = (e) => {{
  state.useExactPlate = !state.useExactPlate;
  e.target.textContent = state.useExactPlate ? "Mode: Pre-Rendered 3D Plate + Live Scrub" : "Mode: Live Any-View Composite";
}};
document.getElementById("togglePlyBtn").onclick = async (e) => {{
  state.livePlyMode = !state.livePlyMode;
  e.target.textContent = state.livePlyMode ? "Showing Live Binary points.ply (Click for Plate)" : "Load Live Binary points.ply (129K pts)";
  if (state.livePlyMode) {{
    const poem = state.bundle.poems[state.poemIdx];
    const view = (poem.views || [])[state.viewIdx];
    if (view && view._assets) state.plyPoints = await loadBinaryPly(view._assets.points_ply);
  }}
}};

canvas.addEventListener("mousemove", (e) => {{
  const r = canvas.getBoundingClientRect();
  state.scrubX = Math.max(0.05, Math.min(0.95, (e.clientX - r.left) / r.width));
  document.getElementById("scrubX").value = Math.round(state.scrubX * 100);
}});

function loop() {{
  state.t += 0.016;
  renderStage();
  requestAnimationFrame(loop);
}}

fetch("data/terrarium/seeing_spacetime_films/vesper_world_bundle.json")
  .then((r) => r.json())
  .then(async (b) => {{
    state.bundle = b;
    const params = new URLSearchParams(window.location.search);
    const pParam = Number(params.get("poem") || 1);
    const pIdx = Math.max(0, Math.min(b.poems.length - 1, pParam - 1));
    await selectPoem(pIdx);
    loop();
  }});
</script>
</body>
</html>
"""


def generate_poem_webpage(poem: dict, all_poems: list) -> str:
    num = int(poem["num"])
    ns = f"{num:02d}"
    slug = f"poem_{ns}_apparatus.html"
    title = poem.get("title", "")
    hid = poem.get("hero_view_id", "V92")
    eid = poem.get("echo_view_id", "V26")
    nav_html = build_global_nav_html(slug, all_poems)

    prev_num = 14 if num == 1 else num - 1
    next_num = 1 if num == 14 else num + 1
    prev_slug = f"poem_{prev_num:02d}_apparatus.html"
    next_slug = f"poem_{next_num:02d}_apparatus.html"

    opt_cards_html = []
    for m_idx, pm in enumerate(PARADIGM_META, start=1):
        img_url = f"data/terrarium/seeing_spacetime_films/poem_{ns}_opt{m_idx}.jpg"
        opt_cards_html.append(f"""
        <div class="opt-grid-card" onclick="openOptionStage({m_idx})">
          <img src="{img_url}" alt="Poem {ns} Option {m_idx}" />
          <div class="opt-grid-cap">
            <span style="color:{pm['accent']};font-weight:700">{pm['short']}</span>
            <a href="{pm['slug']}?poem={num}" onclick="event.stopPropagation()" style="color:#8ea3b8;text-decoration:none;font-size:10px">Open Paradigm Page →</a>
          </div>
        </div>
        """)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Poem {ns}: {title} — 6 Narrative Apparatus Paradigms</title>
<style>
  :root {{
    --bg: #07090d;
    --panel: #0d1118;
    --panel-2: #121822;
    --border: rgba(92, 228, 255, 0.22);
    --cyan: #5ce4ff;
    --amber: #ffbe52;
    --green: #82f5af;
    --pink: #ff82c3;
    --text: #e6eef6;
    --muted: #8ea3b8;
    --mono: "SF Mono", "Menlo", "Monaco", "Consolas", monospace;
    --serif: "Georgia", "Iowan Old Style", serif;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--mono);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  {GLOBAL_NAV_CSS}
  header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    background: #0a0e14;
    border-bottom: 1px solid var(--border);
    gap: 12px;
    flex-shrink: 0;
  }}
  .brand-title {{
    font-size: 14px;
    font-weight: 700;
    color: var(--cyan);
    letter-spacing: 0.05em;
  }}
  .brand-sub {{
    font-size: 11px;
    color: var(--muted);
    margin-top: 2px;
  }}
  .mode-bar {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }}
  .m-btn {{
    background: #101620;
    color: var(--text);
    border: 1px solid rgba(142, 163, 184, 0.28);
    padding: 6px 10px;
    font-family: var(--mono);
    font-size: 11px;
    cursor: pointer;
    border-radius: 3px;
    text-decoration: none;
  }}
  .m-btn.active, .m-btn:hover {{
    background: rgba(92, 228, 255, 0.18);
    border-color: var(--cyan);
    color: var(--cyan);
    font-weight: 700;
  }}
  .workspace {{
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 420px;
    min-height: 0;
  }}
  .main-stage {{
    display: flex;
    flex-direction: column;
    min-height: 0;
    background: #05070b;
    overflow-y: auto;
    padding: 12px;
    gap: 12px;
  }}
  .six-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }}
  .opt-grid-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.14s ease;
  }}
  .opt-grid-card:hover {{
    border-color: var(--amber);
    transform: translateY(-2px);
  }}
  .opt-grid-card img {{
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    display: block;
  }}
  .opt-grid-cap {{
    padding: 6px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
  }}
  .hero-viewer {{
    flex: 1;
    min-height: 440px;
    background: #030508;
    border: 1px solid var(--border);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
  }}
  .hero-viewer img, .hero-viewer video {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    display: block;
  }}
  .inspector {{
    background: var(--panel);
    border-left: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow-y: auto;
    padding: 12px;
    gap: 12px;
  }}
  .section-title {{
    font-size: 10px;
    letter-spacing: 0.08em;
    color: var(--cyan);
    text-transform: uppercase;
    border-bottom: 1px solid rgba(92, 228, 255, 0.18);
    padding-bottom: 4px;
    margin-bottom: 6px;
  }}
  .data-card {{
    background: var(--panel-2);
    border: 1px solid rgba(142, 163, 184, 0.2);
    border-radius: 4px;
    padding: 9px;
    font-size: 11px;
    line-height: 1.45;
  }}
  .view-strip {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
  }}
  .view-thumb {{
    background: #0d131c;
    border: 1px solid rgba(142, 163, 184, 0.22);
    border-radius: 3px;
    overflow: hidden;
    cursor: pointer;
  }}
  .view-thumb:hover {{
    border-color: var(--green);
  }}
  .view-thumb img {{
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    display: block;
  }}
  .view-thumb-cap {{
    padding: 4px 6px;
    font-size: 10px;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
</style>
</head>
<body>
{nav_html}
<header>
  <div>
    <div class="brand-title">POEM {ns} · {title.upper()} — ALL 6 NARRATIVE APPARATUS PARADIGMS</div>
    <div class="brand-sub">Hero Common Place: {hid} ↔ Paired Echo Common Place: {eid} · Click any of the 6 paradigm plates below to inspect at full resolution</div>
  </div>
  <div class="mode-bar">
    <a class="m-btn" href="{prev_slug}">← POEM {prev_num:02d}</a>
    <button class="m-btn active" id="btnOpt0" onclick="openOptionStage(0)">6-PARADIGM OVERVIEW</button>
    <button class="m-btn" id="btnOpt1" onclick="openOptionStage(1)">I · 3D PLY</button>
    <button class="m-btn" id="btnOpt2" onclick="openOptionStage(2)">II · MULTIPLANE</button>
    <button class="m-btn" id="btnOpt3" onclick="openOptionStage(3)">III · PERSPECTIVE</button>
    <button class="m-btn" id="btnOpt4" onclick="openOptionStage(4)">IV · SAM2/ΔE</button>
    <button class="m-btn" id="btnOpt5" onclick="openOptionStage(5)">V · CUT-OUT KITS</button>
    <button class="m-btn" id="btnOpt6" onclick="openOptionStage(6)">VI · X-RAY ECHO</button>
    <button class="m-btn" id="btnOpt7" onclick="openOptionStage(7)">4K SHEET</button>
    <button class="m-btn" id="btnOpt8" onclick="openOptionStage(8)">▶ PLAY H.264 FILM</button>
    <a class="m-btn" href="{next_slug}">POEM {next_num:02d} →</a>
  </div>
</header>

<div class="workspace">
  <main class="main-stage">
    <div class="six-grid" id="sixGrid">
      {''.join(opt_cards_html)}
    </div>
    <div class="hero-viewer" id="heroViewer">
      <img id="heroImg" src="data/terrarium/seeing_spacetime_films/poem_{ns}_apparatus_6options.png" alt="Poem {ns} 6-Option Sheet" />
      <video id="heroVid" src="data/terrarium/seeing_spacetime_films/poem_{ns}_apparatus.mp4" controls loop muted playsinline style="display:none"></video>
    </div>
  </main>

  <aside class="inspector">
    <div>
      <div class="section-title">Poem {ns} Full Verse & Scene Breakdown</div>
      <div class="data-card" id="verseBox" style="font-family:var(--serif);font-size:13px;color:#f5ecda;white-space:pre-line">Loading...</div>
    </div>
    <div>
      <div class="section-title">Common Place Views in Poem {ns} (Click to Inspect Layer Stack)</div>
      <div class="view-strip" id="viewStrip"></div>
    </div>
    <div>
      <div class="section-title">Multiplane Kit Sheets (poems/kits/{ns}.*.jpg)</div>
      <div class="view-strip" id="kitStrip"></div>
    </div>
    <div>
      <div class="section-title">Working Assembly Manuscript</div>
      <div class="data-card" id="assemblyBox" style="white-space:pre-line;color:var(--muted)">Loading...</div>
    </div>
  </aside>
</div>

<script>
const POEM_NUM = {num};
const POEM_NS = "{ns}";

function openOptionStage(idx) {{
  for (let i = 0; i <= 8; i++) {{
    const b = document.getElementById("btnOpt" + i);
    if (b) b.classList.toggle("active", i === idx);
  }}
  const img = document.getElementById("heroImg");
  const vid = document.getElementById("heroVid");
  if (idx === 8) {{
    img.style.display = "none";
    vid.style.display = "block";
    vid.play().catch(() => {{}});
  }} else {{
    vid.pause();
    vid.style.display = "none";
    img.style.display = "block";
    if (idx === 0 || idx === 7) {{
      img.src = `data/terrarium/seeing_spacetime_films/poem_${{POEM_NS}}_apparatus_6options.png`;
    }} else {{
      img.src = `data/terrarium/seeing_spacetime_films/poem_${{POEM_NS}}_opt${{idx}}.jpg`;
    }}
  }}
}}

fetch("data/terrarium/seeing_spacetime_films/vesper_world_bundle.json")
  .then((r) => r.json())
  .then((b) => {{
    const poem = b.poems.find((p) => Number(p.num) === POEM_NUM) || b.poems[0];
    const pText = (poem.poem_text && !poem.poem_text.startsWith("{{"))
      ? poem.poem_text
      : (poem.full_text || []).map((x) => (x && typeof x === "object" ? x.line || "" : String(x))).join("\\n");
    document.getElementById("verseBox").textContent = pText;
    document.getElementById("assemblyBox").textContent = poem.assembly_excerpt || "";

    const vStrip = document.getElementById("viewStrip");
    (poem.views || []).forEach((v) => {{
      const sd = v.dir || v.shot_dir || "";
      const card = document.createElement("div");
      card.className = "view-thumb";
      card.innerHTML = `<img src="out/${{sd}}/multiplane/exploded.jpg" alt="${{v.id}}" /><div class="view-thumb-cap">${{v.id}} · ${{v.place_name || ""}}</div>`;
      card.onclick = () => {{
        const img = document.getElementById("heroImg");
        const vid = document.getElementById("heroVid");
        vid.pause(); vid.style.display = "none"; img.style.display = "block";
        img.src = `out/${{sd}}/multiplane/exploded.jpg`;
      }};
      vStrip.appendChild(card);
    }});

    const kStrip = document.getElementById("kitStrip");
    (poem.kit_sheets || []).forEach((k) => {{
      const card = document.createElement("div");
      card.className = "view-thumb";
      card.innerHTML = `<img src="${{k.image}}" alt="${{k.id}}" /><div class="view-thumb-cap">${{k.id}}</div>`;
      card.onclick = () => {{
        const img = document.getElementById("heroImg");
        const vid = document.getElementById("heroVid");
        vid.pause(); vid.style.display = "none"; img.style.display = "block";
        img.src = k.image;
      }};
      kStrip.appendChild(card);
    }});
  }});
</script>
</body>
</html>
"""


def main():
    bundle = json.loads(BUNDLE_PATH.read_text())
    poems = bundle["poems"]

    # 1. Generate the 6 dedicated Paradigm Webpages
    for pm in PARADIGM_META:
        out_path = SHOTS_DIR / pm["slug"]
        out_path.write_text(generate_paradigm_webpage(pm, poems))
        print(f"[paradigm-page] Wrote {out_path}")

    # 2. Generate the 14 dedicated Per-Poem Webpages
    for p in poems:
        ns = f"{int(p['num']):02d}"
        out_path = SHOTS_DIR / f"poem_{ns}_apparatus.html"
        out_path.write_text(generate_poem_webpage(p, poems))
        print(f"[poem-page] Wrote {out_path}")

    # 3. Inject Global Nav + URL query param support into shots/vesper_apparatus.html
    hub_path = SHOTS_DIR / "vesper_apparatus.html"
    hub_html = hub_path.read_text()
    nav_bar = build_global_nav_html("vesper_apparatus.html", poems)
    if "global-apparatus-nav" not in hub_html:
        hub_html = hub_html.replace("</style>", GLOBAL_NAV_CSS + "\n</style>", 1)
        hub_html = hub_html.replace("<body>", "<body>\n" + nav_bar, 1)
    if "URLSearchParams(window.location.search)" not in hub_html:
        hub_html = hub_html.replace(
            "await selectPoem(0);",
            """const params = new URLSearchParams(window.location.search);
    const pParam = Number(params.get("poem") || 1);
    const mParam = Number(params.get("mode") || 1);
    await selectPoem(Math.max(0, Math.min(data.poems.length - 1, pParam - 1)));
    if (mParam >= 1 && mParam <= 8) setMode(mParam);""",
        )
    hub_path.write_text(hub_html)
    print(f"[hub-page] Updated {hub_path}")


if __name__ == "__main__":
    main()
