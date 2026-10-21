#!/usr/bin/env python3
"""
Update shots/kits.html with the rendered sheets, 105 separated parts, and interactive explorer.
"""
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))
KITS_HTML = os.path.join(HERE, '..', 'kits.html')
CATALOG_PATH = os.path.join(HERE, 'parts', 'kit3', 'v2', 'cut', 'catalog.json')

with open(KITS_HTML, 'r', encoding='utf-8') as f:
    html = f.read()

with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
    catalog = json.load(f)

total_pieces = sum(c['piece_count'] for c in catalog)
total_sheets = len(catalog)

# Extra CSS for the rendered kit explorer and parts gallery
EXTRA_CSS = """
/* Rendered Kits & Sliced Parts Explorer Styles */
.shelf-header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:8px}
.shelf-header h2{font:400 28px 'Permanent Marker',cursive;color:var(--acc);margin:0}
.shelf-badge{font:600 12px var(--mono);background:#2c2014;color:var(--acc);border:1px solid var(--card);padding:4px 12px;border-radius:999px}
.filter-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 0;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}
.filter-chip{font:12px var(--mono);color:var(--ink);background:#201812;border:1px solid var(--line);border-radius:999px;padding:5px 12px;cursor:pointer;transition:all .15s}
.filter-chip:hover{border-color:var(--card);color:var(--card)}
.filter-chip.active{background:var(--card);color:#16120f;font-weight:600;border-color:var(--card)}
.search-box{flex:1;min-width:200px;font:13px var(--mono);background:#0f0c0a;color:var(--ink);border:1px solid var(--line);border-radius:999px;padding:6px 14px;outline:none}
.search-box:focus{border-color:var(--acc)}

.parts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px;margin-top:14px}
.part-card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px;display:flex;flex-direction:column;gap:8px;position:relative;transition:border-color .15s,transform .15s}
.part-card:hover{border-color:var(--acc);transform:translateY(-2px)}
.part-preview{width:100%;height:180px;background:#0a0807 url("data:image/svg+xml,%3Csvg width='16' height='16' viewBox='0 0 16 16' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='8' height='8' fill='%23120f0c'/%3E%3Crect x='8' y='8' width='8' height='8' fill='%23120f0c'/%3E%3Crect x='8' width='8' height='8' fill='%23181410'/%3E%3Crect y='8' width='8' height='8' fill='%23181410'/%3E%3C/svg%3E");border-radius:6px;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;padding:8px;cursor:pointer}
.part-preview img{max-width:100%;max-height:100%;object-fit:contain;filter:drop-shadow(0 4px 8px rgba(0,0,0,.6));transition:transform .2s}
.part-preview:hover img{transform:scale(1.06)}
.part-info{display:grid;gap:4px;font:11px var(--mono)}
.part-title{font:600 12px var(--mono);color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.part-meta{display:flex;justify-content:space-between;color:var(--dim)}
.part-badge{background:#231a12;border:1px solid var(--line);color:var(--card);padding:1px 6px;border-radius:4px;font-size:10px}
.part-btns{display:flex;gap:6px;margin-top:4px}
.part-btn{flex:1;text-align:center;font:600 11px Inter;background:none;border:1px solid var(--line);color:var(--ink);border-radius:999px;padding:4px 8px;cursor:pointer;text-decoration:none}
.part-btn:hover{border-color:var(--card);color:var(--card)}

.sheet-gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;margin-top:14px}
.sheet-card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;display:grid;gap:10px}
.sheet-card img{width:100%;height:auto;border-radius:4px;background:#fff;cursor:pointer}
.sheet-card .row{justify-content:space-between}

/* Tab toggle on pack cards */
.pk-tabs{display:flex;gap:4px;margin-bottom:6px;background:#0d0a08;padding:2px;border-radius:6px;border:1px solid var(--line)}
.pk-tab{flex:1;background:none;border:0;color:var(--dim);font:600 10px var(--mono);padding:3px 6px;border-radius:4px;cursor:pointer;text-align:center}
.pk-tab.active{background:var(--card);color:#16120f}
.pk-tab:hover:not(.active){color:var(--ink)}
.pk-rendered-badge{position:absolute;top:6px;right:6px;background:var(--ok);color:#0a1e04;font:700 9px var(--mono);padding:2px 6px;border-radius:4px;letter-spacing:.04em;z-index:2}
.pk{position:relative}

/* Lightbox Modal */
.lb-modal{position:fixed;inset:0;background:rgba(8,6,5,.9);backdrop-filter:blur(6px);z-index:9999;display:none;align-items:center;justify-content:center;padding:24px}
.lb-modal.active{display:flex}
.lb-box{max-width:960px;width:100%;max-height:90vh;background:var(--panel);border:1px solid var(--card);border-radius:12px;overflow:hidden;display:flex;flex-direction:column}
.lb-bar{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;border-bottom:1px solid var(--line)}
.lb-title{font:600 15px var(--mono);color:var(--card)}
.lb-close{background:none;border:0;color:var(--dim);font:20px Inter;cursor:pointer}
.lb-close:hover{color:#fff}
.lb-body{padding:20px;overflow:auto;display:flex;flex-direction:column;align-items:center;gap:16px}
.lb-body img{max-width:100%;max-height:60vh;object-fit:contain;background:#0a0807;border-radius:6px;padding:12px}
"""

EXPLORER_HTML = """
  <section id="rendered-shelf" aria-labelledby="byrendered" style="background:#13100d;border:1px solid var(--card);border-radius:12px;padding:20px;display:grid;gap:16px">
    <div class="shelf-header">
      <div>
        <h2 id="byrendered">✨ Finished Puppet Sheets &amp; Sliced Parts (""" + str(total_pieces) + """ Parts across """ + str(total_sheets) + """ Kits)</h2>
        <p class="dim" style="margin-top:4px">Full 2048x1152 painted cardboard sheets, high-res die-cut transparent parts, and whole-body action poses. Zero rectangular borders, corrugated kraft edges, and detected brass brad fasteners.</p>
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <span class="shelf-badge">""" + str(total_sheets) + """ Rendered Kits</span>
        <span class="shelf-badge" style="border-color:var(--ok);color:var(--ok)">""" + str(total_pieces) + """ Cut Pieces</span>
      </div>
    </div>

    <!-- Mode and Filters -->
    <div class="filter-bar">
      <div style="display:flex;gap:6px;align-items:center;margin-right:8px">
        <button class="filter-chip active" id="btn-mode-parts" onclick="setMode('parts')">🧩 Cut Parts &amp; Poses</button>
        <button class="filter-chip" id="btn-mode-sheets" onclick="setMode('sheets')">🖼️ Painted Sheets (2048x1152)</button>
      </div>
      <input type="text" id="part-search" class="search-box" placeholder="Filter parts (e.g. crouch, sitting, torso, arm, boot, fist)..." oninput="renderFiltered()">
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <button class="filter-chip active" data-filter="all" onclick="setFilter('all', this)">All Cast</button>
        <button class="filter-chip" data-filter="poet" onclick="setFilter('poet', this)">Poet (Red/Black &amp; T-Shirt)</button>
        <button class="filter-chip" data-filter="woman" onclick="setFilter('woman', this)">The Woman</button>
        <button class="filter-chip" data-filter="ex" onclick="setFilter('ex', this)">EX</button>
        <button class="filter-chip" data-filter="young_poet" onclick="setFilter('young_poet', this)">Young Poet</button>
        <button class="filter-chip" data-filter="ghost_child" onclick="setFilter('ghost_child', this)">Ghost Child</button>
        <button class="filter-chip" data-filter="dummy" onclick="setFilter('dummy', this)">Crash Dummies (Bola &amp; Dot)</button>
      </div>
    </div>

    <!-- Parts Container -->
    <div id="parts-container" class="parts-grid"></div>

    <!-- Sheets Container -->
    <div id="sheets-container" class="sheet-gallery" style="display:none"></div>
  </section>
"""

MODAL_HTML = """
<div id="lb-modal" class="lb-modal" onclick="if(event.target===this)closeLightbox()">
  <div class="lb-box">
    <div class="lb-bar">
      <span class="lb-title" id="lb-title">Piece Inspector</span>
      <button class="lb-close" onclick="closeLightbox()">&times;</button>
    </div>
    <div class="lb-body" id="lb-body">
      <img id="lb-img" src="" alt="piece">
      <div id="lb-details" style="font:12px var(--mono);color:var(--ink);width:100%"></div>
    </div>
  </div>
</div>
"""

# Inject CSS
if '/* Rendered Kits & Sliced Parts Explorer Styles */' not in html:
    html = html.replace('</style>', EXTRA_CSS + '\n</style>')

# Inject Navigation Link into Header
if '#rendered-shelf' not in html:
    nav_link = f'<a href="#rendered-shelf" style="color:var(--ok);border-color:var(--ok)">✨ Finished Sheets &amp; Parts ({total_pieces})</a>\n  '
    html = html.replace('<a href="arena/parts/kit3/v2/kits.json">kits.json</a>', nav_link + '<a href="arena/parts/kit3/v2/kits.json">kits.json</a>')

# Inject Shelf Section right before <section aria-labelledby="bypoem">
if 'id="rendered-shelf"' not in html:
    html = html.replace('<section aria-labelledby="bypoem">', EXPLORER_HTML + '\n  <section aria-labelledby="bypoem">')

# Inject Modal right before </body>
if 'id="lb-modal"' not in html:
    html = html.replace('</body>', MODAL_HTML + '\n</body>')

# Inject Catalog JSON data script
catalog_script = f'<script id="catalog-data" type="application/json">{json.dumps(catalog)}</script>\n'
if 'id="catalog-data"' not in html:
    html = html.replace('<script id="data"', catalog_script + '<script id="data"')

# Update Client JavaScript
NEW_JS = """
// -------------------------------------------------------------
// RENDERED KITS & SLICED PARTS ENGINE
// -------------------------------------------------------------
const CATALOG = JSON.parse(document.getElementById('catalog-data')?.textContent || '[]');
const catalogMap = Object.fromEntries(CATALOG.map(c => [c.sheet, c]));

let currentMode = 'parts';
let currentFilter = 'all';

function setMode(mode) {
  currentMode = mode;
  document.getElementById('btn-mode-parts').classList.toggle('active', mode === 'parts');
  document.getElementById('btn-mode-sheets').classList.toggle('active', mode === 'sheets');
  document.getElementById('parts-container').style.display = mode === 'parts' ? 'grid' : 'none';
  document.getElementById('sheets-container').style.display = mode === 'sheets' ? 'grid' : 'none';
  renderFiltered();
}

function setFilter(filt, btn) {
  currentFilter = filt;
  document.querySelectorAll('.filter-bar button[data-filter]').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderFiltered();
}

function renderFiltered() {
  const query = (document.getElementById('part-search')?.value || '').toLowerCase().trim();
  
  if (currentMode === 'parts') {
    const partsCont = document.getElementById('parts-container');
    let allPieces = [];
    CATALOG.forEach(sheetEntry => {
      const s = sheetEntry.sheet;
      let matchChar = true;
      if (currentFilter === 'poet') matchChar = s.startsWith('poet.');
      else if (currentFilter === 'woman') matchChar = s.startsWith('woman.');
      else if (currentFilter === 'ex') matchChar = s.startsWith('ex.');
      else if (currentFilter === 'young_poet') matchChar = s.startsWith('young_poet.');
      else if (currentFilter === 'ghost_child') matchChar = s.startsWith('ghost_child.');
      else if (currentFilter === 'dummy') matchChar = s.startsWith('bola.') || s.startsWith('dot.');
      
      if (matchChar) {
        sheetEntry.pieces.forEach(p => {
          allPieces.push({ ...p, sheetName: s, sheetImg: sheetEntry.image });
        });
      }
    });
    
    if (query) {
      allPieces = allPieces.filter(p => 
        p.label.toLowerCase().includes(query) || 
        p.file.toLowerCase().includes(query) || 
        p.sheetName.toLowerCase().includes(query)
      );
    }
    
    partsCont.innerHTML = allPieces.map((p, idx) => `
      <div class="part-card" data-idx="${idx}">
        <div class="part-preview" onclick="openLightbox('${esc(p.rel_path)}', '${esc(p.label)}', '${esc(p.sheetName)}', ${JSON.stringify(p.bbox)}, ${JSON.stringify(p.brads)})">
          <img src="${esc(p.rel_path)}" alt="${esc(p.label)}" loading="lazy">
        </div>
        <div class="part-info">
          <div class="part-title" title="${esc(p.label)}">${esc(p.label)}</div>
          <div class="part-meta">
            <span>${p.bbox[2]}×${p.bbox[3]}px</span>
            <span class="part-badge">${p.brads.length ? `${p.brads.length} Brad${p.brads.length>1?'s':''}` : 'No Brads'}</span>
          </div>
          <div class="dim" style="font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(p.sheetName)}</div>
        </div>
        <div class="part-btns">
          <button class="part-btn" onclick="openLightbox('${esc(p.rel_path)}', '${esc(p.label)}', '${esc(p.sheetName)}', ${JSON.stringify(p.bbox)}, ${JSON.stringify(p.brads)})">Inspect</button>
          <a class="part-btn" href="${esc(p.rel_path)}" download="${esc(p.file)}">Download</a>
        </div>
      </div>
    `).join('') || `<p class="dim" style="grid-column:1/-1;text-align:center;padding:40px">No parts match your filter.</p>`;
  } else {
    const sheetsCont = document.getElementById('sheets-container');
    let sheets = CATALOG;
    if (currentFilter !== 'all') {
      sheets = sheets.filter(s => {
        if (currentFilter === 'poet') return s.sheet.startsWith('poet.');
        if (currentFilter === 'woman') return s.sheet.startsWith('woman.');
        if (currentFilter === 'ex') return s.sheet.startsWith('ex.');
        if (currentFilter === 'young_poet') return s.sheet.startsWith('young_poet.');
        if (currentFilter === 'ghost_child') return s.sheet.startsWith('ghost_child.');
        if (currentFilter === 'dummy') return s.sheet.startsWith('bola.') || s.sheet.startsWith('dot.');
        return true;
      });
    }
    sheetsCont.innerHTML = sheets.map(s => `
      <div class="sheet-card">
        <a href="${esc(s.image)}" target="_blank" rel="noopener">
          <img src="${esc(s.image)}" alt="${esc(s.sheet)}" loading="lazy">
        </a>
        <div style="font:600 13px var(--mono);color:var(--ink)">${esc(s.sheet)}</div>
        <div class="row">
          <span class="part-badge" style="border-color:var(--ok);color:var(--ok)">${s.piece_count} Cut Parts Available</span>
          <a class="btn ghost" href="${esc(s.image)}" download>Download Sheet</a>
        </div>
      </div>
    `).join('');
  }
}

function openLightbox(relPath, label, sheet, bbox, brads) {
  const modal = document.getElementById('lb-modal');
  const img = document.getElementById('lb-img');
  const title = document.getElementById('lb-title');
  const details = document.getElementById('lb-details');
  
  img.src = relPath;
  title.textContent = `${label} · ${sheet}`;
  details.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;background:#0d0b0a;padding:12px;border-radius:8px;border:1px solid var(--line)">
      <div><b>Piece:</b> ${esc(label)}</div>
      <div><b>Sheet:</b> ${esc(sheet)}</div>
      <div><b>Dimensions:</b> ${bbox[2]}px × ${bbox[3]}px</div>
      <div><b>Detected Brads:</b> ${brads.length}</div>
      ${brads.map((b, i) => `<div>Brad #${i+1}: (${b.cx}px, ${b.cy}px) radius ${b.radius}px</div>`).join('')}
    </div>
    <div style="display:flex;gap:8px;margin-top:10px">
      <a class="btn" href="${esc(relPath)}" download>Download High-Res Card</a>
    </div>
  `;
  modal.classList.add('active');
}

function closeLightbox() {
  document.getElementById('lb-modal').classList.remove('active');
}

// Enhance packCard to show tabs if rendered sheet exists
const origPackCard = packCard;
packCard = p => {
  const rendered = catalogMap[p.id] || catalogMap[p.sheet];
  if (!rendered) return origPackCard(p);
  
  return `<div class="pk" id="pk-${esc(p.id)}">
    <span class="pk-rendered-badge">✨ RENDERED</span>
    <div class="pk-tabs">
      <button class="pk-tab active" onclick="switchPkTab(this, 'pack', '${esc(p.image)}')">Pack</button>
      <button class="pk-tab" onclick="switchPkTab(this, 'sheet', '${esc(rendered.image)}')">Sheet</button>
      <button class="pk-tab" onclick="switchPkTab(this, 'parts', '${esc(rendered.sheet)}')">Parts (${rendered.piece_count})</button>
    </div>
    <div class="pk-view" id="pv-${esc(p.id)}">
      <a href="${esc(p.image)}" target="_blank" rel="noopener"><img src="${esc(p.image)}" alt="${esc(p.id)} pack" loading="lazy"></a>
    </div>
    <span class="t">${esc(p.sheet || p.id)}</span>
    <div class="row">
      <button class="btn" data-i="${reg(p.prompt)}">Copy prompt</button>
      <a class="btn ghost" href="${esc(rendered.image)}" download>Get Sheet</a>
      <span class="ok" aria-live="polite"></span>
    </div>
  </div>`;
};

window.switchPkTab = function(btn, type, target) {
  const pk = btn.closest('.pk');
  pk.querySelectorAll('.pk-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  const view = pk.querySelector('.pk-view');
  
  if (type === 'pack') {
    view.innerHTML = `<a href="${target}" target="_blank" rel="noopener"><img src="${target}" alt="pack" loading="lazy"></a>`;
  } else if (type === 'sheet') {
    view.innerHTML = `<a href="${target}" target="_blank" rel="noopener"><img src="${target}" alt="rendered sheet" loading="lazy"></a>`;
  } else if (type === 'parts') {
    const entry = catalogMap[target];
    if (entry) {
      view.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(70px,1fr));gap:6px;max-height:220px;overflow:auto;background:#0d0a08;padding:6px;border-radius:4px">
        ${entry.pieces.map(pc => `
          <div style="background:#16120f;border:1px solid var(--line);border-radius:4px;padding:4px;display:flex;flex-direction:column;align-items:center;cursor:pointer" onclick="openLightbox('${esc(pc.rel_path)}', '${esc(pc.label)}', '${esc(entry.sheet)}', ${JSON.stringify(pc.bbox)}, ${JSON.stringify(pc.brads)})">
            <img src="${esc(pc.rel_path)}" alt="${esc(pc.label)}" style="width:100%;height:50px;object-fit:contain">
            <span style="font-size:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%;text-align:center">${esc(pc.label)}</span>
          </div>
        `).join('')}
      </div>`;
    }
  }
};

setTimeout(renderFiltered, 50);
"""

# Replace the script block or append
html = html.replace('const packCard = p => `<div class="pk">', 'let packCard = p => `<div class="pk">')
if 'RENDERED KITS & SLICED PARTS ENGINE' not in html:
    html = html.replace('if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();', 'if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();\n' + NEW_JS)

with open(KITS_HTML, 'w', encoding='utf-8') as f:
    f.write(html)

print("kits.html successfully updated!")
