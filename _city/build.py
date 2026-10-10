#!/usr/bin/env python3
# Builds the district board (index.html) and districts.json from the measured palettes and the design notes below.
import json, html, re
SP='/private/tmp/claude-502/-Users-gaia-Downloads-butterfly-halfworld--claude-worktrees-hungry-cori-d982c1/e070c8cd-f44b-44d0-b1fd-468839c4b140/scratchpad/arch'
fs=json.load(open(SP+'/index.json')); P=json.load(open('_city/palettes.json'))
def cap(i):
    s=fs[i-1][10:]; s=re.sub(r'_[0-9a-f]{8}-[0-9a-f-]+_\d+\.png$','',s); s=s.replace('_',' ')
    s=re.sub(r'^(4\. )','',s); s=re.sub(r'(Camera |Canon |Leica |Panasonic |RED |Shot using ).*$','',s).strip() or 'untitled view'
    return s[:72]
D=[
 dict(id='naraka',name='Naraka Market',realm='B · the old harbor city',where='the nightlife district (2089, 1891), around The Severn and its fire escapes',
  eras='harbor → docks → warehouses → the Fall → clubs under neon → the twilight market',
  mood='twilight that never ends · humid, crowded, devotional, improvised · someone else’s rain',
  arch='shipping containers stacked two to four high into shops and rooms; corrugated awnings; cable webs and string lights across the street; AC units; stair alleys climbing between walls; the underpass flooded into a shadow-pool; a teahouse breathing vapor',
  materials='rusted teal and turquoise steel, painted plywood, wet asphalt as a mirror',
  key=['the Container Rows (17–20)','the Underpass Shadow-Pool, where children stand in the reflection (92–93)','the Teahouse of Saints (96)','the Hidden Stairwells (44, 45, 61)','the market crush (59, 60)'],
  moments=['the shadow-pool ritual (93)','vapor bloom outside the teahouse (96)','the club crowd dissolving in warm haze (36)'],
  poems=['01 Out of Life — his high-rise room in The Severn above the market, dusk into night','14 Hot Minute — the harbor party, the haze that takes him','07 DJ Turn Me Up borrows its crowd (36)'],
  signature='always 19:00–20:30 (twilight-only) · light rain · teal haze'),
 dict(id='haze',name='The Orange Haze',realm='B · the old harbor city',where='the industrial district (2621, 2146) and the highway ring',
  eras='field → mills → factories → the Fall (the fire) → ruins kept as a park → the haze that never lifted',
  mood='oppressive scale, heat, solitude · one figure on a bridge · the Fall’s air still burning',
  arch='elevated concrete catwalks with glowing kerb strips; expressway undercrofts of pillars and stairs; brutalist slabs and a line of smokestacks; skyways through smog; a sodium tunnel stair with a single chair',
  materials='raw concrete, rust, soot; sodium light that colours everything',
  key=['the Orange Catwalk, an elevated walk along the expressways (84, 85)','the Undercroft beneath the ring (1–3)','the Smokestack Line (64)','the Skyway through the smog (65, 79–81)','the Stair with the Chair (5)'],
  moments=['lightning crawling along the undercroft (1)','a lone walker on the skyway (80, 81)','shadow play beneath the solar bridges by day (77)'],
  poems=['10 Magic Ride — the motorcycle through tunnel light toward dawn: the undercroft and the skyway'],
  signature='any hour, but always the haze: dense orange fog, sodium glow, silhouettes'),
 dict(id='hive',name='The Hive',realm='B · the old harbor city',where='the downtown district (1463, 1824): the New Boroughs’ towers',
  eras='field → … → the towers of the New Boroughs (“a language made exact”) → darkened in the Fall → still standing, lit by signal',
  mood='grandeur and dread · density · vertigo looking up · beacons blinking like a nervous system',
  arch='dense slab towers and gothic needle spires; lattice signal towers with red and blue beacons; a megastructure atrium',
  materials='dark glass, steel lattice, wet concrete',
  key=['the Signal Lattices (46–48)','the Needles (12, 70)','the Well, looking straight up (38)','the atrium (10)'],
  moments=['the city of needles burning seen from above (70)'],
  poems=['01 Out of Life — the high-rise, the haze, then cloud and total black','02 Flashing Lights — black space with lights flashing: the beacons'],
  signature='night · mist · cold blue with pulsing red'),
 dict(id='overseer',name='The Overseer',realm='B · the old harbor city',where='the rowhouses district (2099, 1179), the northern edge facing the mountains',
  eras='rowhouses → … → the Overseer’s quarter, the old order’s watch',
  mood='cold watchfulness · symmetry · the moon · sterile indigo',
  arch='blue industrial pipework among towers; the old palace roofless under the moon; a canyon of slabs framing the moon; a glass skywalk over the indigo city',
  materials='glass, painted steel pipe, pale render gone blue',
  key=['the Moon Canyon (88)','the Pipe Works (86)','the Old Palace (87)','the Skywalk (49)','the mirrored skyline of blue and red (25)'],
  moments=['the moon standing in the slot between towers (88)'],
  poems=['02 Flashing Lights — the winter-night flashback, headlights raking a dark room'],
  signature='moonlit · clear · cold; the one warm colour is an alarm crimson'),
 dict(id='bay',name='Mirror Thread Bay',realm='B and C · the harbor and the shore',where='the waterfront district (1469, 2345) and the south shore',
  eras='shore → fishing → harbor → harbor → flooded (the Fall) → promenade → the bay of mirrors',
  mood='reflection, memory, tenderness · drowned rooms remembered · handprints on glass',
  arch='turquoise lagoons with garden islands; boardwalks under the great bridge; flooded colonnades and atria with bioluminescent floors; submerged corridors; the oil-slick canal under the radio bridge; the sleep-dam wall with words',
  materials='water above all; concrete under water; moss; glass',
  key=['the Sleep-Dam, “REMEMBER THE …” (75, 76)','the Drowned Atrium (53–56)','the submerged corridors (57, 58)','the Radio Bridge canal (63)','the Bridge Boardwalk (24)','the Lagoon (23)'],
  moments=['handprints on the glass of a drowned corridor (57)','the canal under the radio bridge at night (63)'],
  poems=['13 How to Win My Heart — the daylight harbor walk to the corner café (23, 24)','04 Nevermore — the shore at twilight, calm waves','03 How to Break off an Engagement — the storm and its aftermath: the flooded corridors'],
  signature='night bioluminescence / daytime turquoise · water first'),
 dict(id='commons',name='Cortex Commons',realm='B · the old harbor city',where='the old town district (1036, 2130): the cathedral square “too large for it”',
  eras='the old center’s square → … → the commons that listens',
  mood='communal, civic, joyful · children running · the city listening to the sky',
  arch='radio-telescope dishes set in the squares (WYGWYL radio, made civic); a sunken oculus forum; a mosaic canopy over the crowd; a misted square of glowing cubes; the cathedral among glass towers under the moon',
  materials='pale stone, wet paving painted with light, mosaic',
  key=['the Listening Dishes (15, 16)','the Oculus forum (14)','the Canopy (21)','the square of glowing cubes (22)','the Cathedral Square (51)'],
  moments=['children running across the light-painted square under a dish (16)'],
  poems=['no poem lives here: it is where the city listens to them'],
  signature='dusk · blue hour, warm windows'),
 dict(id='plaza',name='The Light Gate & Atlantis Central Plaza',realm='A · Atlantis',where='the gates (realm A) and the site of 06 (5120, 3540)',
  eras='the field of stones (the Shore) → … → the Light Gates open (Resurrection)',
  mood='threshold, then arrival · dazzle · manifestation',
  arch='a perimeter of transparent, high-frequency fences of light that becomes the gate; beyond it a circular plaza ringed by rose terraces; a hall of crystal trees over a mirror pool',
  materials='light itself at the gate; rose stone; crystal; still water',
  key=['the Light Gate (89, 90)','the Central Plaza (33)','the Hall of Crystal Trees (34)'],
  moments=['the gate’s glare on wet ground (90)'],
  poems=['06 Resurrecting Atlantis — he sees the entrance, goes in through the gates'],
  signature='still night · the gate’s white glare'),
 dict(id='ankhu',name='Ankhu Spires',realm='A · Atlantis',where='the high ground of realm A (the forest at 5280, 3640, h 101 m; the mountains at 5180, 3940, h 127 m)',
  eras='the lone peak → … → the high city, grown in Resurrection',
  mood='altitude, breath, mist · gardens in the air · domestic life at height (laundry under the stars)',
  arch='coral and terracotta spires with carved arches, a souk at their feet; mushroom-cap platforms on slender stems with hanging gardens; planter-pillars with trees above the cloud; sky bridges and observation decks; glass spires among palms; the Spire Elevator Shaft, a hundred-storey red core; laundry lines on the roofs',
  materials='terracotta, coral render, pale steel, glass, living green',
  key=['the Spire Elevator Shaft (82, 83)','the Sky Gardens (28, 29, 31)','the Observation Deck (27)','the coral spires (8)','the floating domes over the water (9)','the Laundry Roofs (73, 74)'],
  moments=['laundry under a starfield (73)','looking down through the glass filament (99)'],
  poems=['08 Newly Single — the open-air rooftop club, the city glowing blue and pink below (28, 31, 11)','05 Bloodline — the night garden becomes the gardens in the air','04 Nevermore — the field below the spires'],
  signature='blue-hour mist · violet underlights at night'),
 dict(id='cenotaph',name='Cenotaph Rail',realm='B → A → C · the rail along the spines',where='rises at the ruin field (2107, 3201) and runs along the spines, the poet’s own routes between the realms',
  eras='field → village → quarter → ruins (the Fall) → ruins walked as a monument → the rail that carries the names',
  mood='elegy, transit, height, rust · a figure at the railing above the mist',
  arch='rusted platforms high above the city; viaduct arches carved with names (the cenotaph); wet stone steps down to the lake under the mountain; a platform in orange haze; a platform where the city dissolves into pixels',
  materials='rusted steel, carved stone, wet granite',
  key=['the Named Arches (43)','the high platform (37)','the Lake Steps (97)','the haze platform (50)'],
  moments=['a cleaning drone’s last memory, the city coming apart (98)'],
  poems=['11 New Day — dawn: he rides back to the shore, the ruins, mist on the sea (97)','every journey between the realms: the spines'],
  signature='dawn and dusk'),
 dict(id='arcade',name='The Shrouded Arcade',realm='B · the old harbor city',where='the suburb district (1168, 2774)',
  eras='suburb → consumer district → abandoned → the arcade of screens',
  mood='spectacle and its ruin · a memory corridor · chrome and static',
  arch='an abandoned mall with its escalators still lit; the LED canyon crossroads, a screen canopy of galaxies over an avenue; a neon memory corridor in red and blue; chrome doors in neon alleys',
  materials='chrome, LED skin, wet tile, dead shopfronts',
  key=['the LED Canyon (94, 95)','the Shrouded Arcade (91)','the Memory Corridor (62)','the chrome doors (6, 7)'],
  moments=['the street soaked in someone else’s rain (100)'],
  poems=['09 Yet Heard — the sidewalk crowd, neon, the moon in the puddles (62, 100)','02 Flashing Lights and 10 Magic Ride pass under the canopy (94)'],
  signature='rain · neon reflections'),
 dict(id='temple',name='The White Temple & its Pools',realm='C · the shore',where='the chapel / white temple on the south shore (the site of 12, 3422, 4181)',
  eras='the chapel on the tidal flat → loses its roof and bell in the Fall → the white temple on its ruins',
  mood='stillness, return · warm hall light · decades compressed',
  arch='a white portico across a reflecting pool among trees; a mirror-pool hall framing the night skyline; the Reflecting Pool Mouth holding the stars',
  materials='white stone, still water, warm interior light',
  key=['the Portico Pool (52)','the Mirror Hall (42)','the Reflecting Pool Mouth (72)'],
  moments=['the stars held in the pool (72)'],
  poems=['12 Reunion — the hall in warm light, the grounds at twilight, the lit porch','11 and 13 begin here'],
  signature='twilight into a lit porch'),
 dict(id='ascent',name='The Ascent',realm='above the city',where='the sky, the moon and the void: the vertical moments, not a district',
  eras='always',
  mood='the ancestors, the gifts, the soul leaving · the whole city seen at once',
  arch='organic cosmic arches over a parade; the city as a blue crystal seen from above; the moon; the milky way over the spires; blue flowers over the night city; red ground under a single spotlight; the reconstructed skyline across the water',
  materials='starlight, nebula, night water',
  key=['the Ancestors’ Parade (68)','the soul ascending over Atlantis (69)','the moon (67)','the milky way over the spires (41)','the skyline across the water (35)'],
  moments=['he enters the Ancestors’ parade, receiving cosmic gifts (68)','his soul rising, seeing Atlantis whole (69)'],
  poems=['05 Bloodline — the gifts are stars and galaxies (68)','14 Hot Minute — floating in black (69, 67)','the film’s overture and credits: the Powers-of-Ten descent and rise are this view (69)'],
  signature='the heavens as a stage'),
]
for d in D: d.update({k: P[d['id']][k] for k in ('images','body','glow','glow_share','dark','mean_lum')})
# an identity colour per district: the most characteristic of its measured glows (or body), so the districts read apart
IDC={'naraka':'#01acd4','haze':'#fa8d15','hive':'#b5342d','overseer':'#1078da','bay':'#465fb1','commons':'#29b6ed','plaza':'#bb7362','ankhu':'#d36f46','cenotaph':'#a94022','arcade':'#be5791','temple':'#c99765','ascent':'#2560e1'}
for d in D: assert IDC[d['id']] in d['glow'] + d['body'], d['id']; d['color'] = IDC[d['id']]
POEMS=[('01','Out of Life','naraka',[38,40,26]),('02','Flashing Lights','overseer',[88,46,48]),('03','How to Break off an Engagement','bay',[57,58,75]),
 ('04','Nevermore','bay',[67,32,24]),('05','Bloodline','ascent',[68,41,73]),('06','Resurrecting Atlantis','plaza',[89,33,34]),('07','DJ Turn Me Up','naraka',[36,94]),
 ('08','Newly Single','ankhu',[28,31,11]),('09','Yet Heard','arcade',[100,62,88]),('10','Magic Ride','haze',[3,65,85]),('11','New Day','cenotaph',[97,77,75]),
 ('12','Reunion','temple',[52,42,72]),('13','How to Win My Heart','bay',[23,24,9]),('14','Hot Minute','ascent',[69,67,36])]
json.dump({'note':'WYGWYL world views grouped into the districts of Atlantis: measured palettes (body: what it is made of; glow: what it lights with), architecture, key places, moments, the poems each holds, and where it lands on the movie map’s city','districts':D,
  'poems':[{'num':n,'title':t,'district':d,'images':im} for n,t,d,im in POEMS],'files':{i+1:f for i,f in enumerate(fs)}},open('_city/districts.json','w'),indent=1,ensure_ascii=False)
E=html.escape; DM={d['id']:d for d in D}
sw=lambda cs,cls='': ''.join(f'<i class="{cls}" style="background:{c}" title="{c}"></i>' for c in cs)
def img(i, big=False): return f'<a href="../{E(fs[i-1])}" target="_blank" class="im{" big" if big else ""}"><img src="thumbs/{i:03d}.webp" loading="lazy" alt="{E(cap(i))}"><b>{i}</b><span>{E(cap(i))}</span></a>'
sec=[]
for d in D:
    lst=lambda xs: '<ul>'+''.join(f'<li>{E(x)}</li>' for x in xs)+'</ul>'
    sec.append(f'''<section id="{d["id"]}" style="--g:{d["color"]}"><header><div><h2>{E(d["name"])}</h2><div class="realm">{E(d["realm"])} · {E(d["where"])}</div></div>
<div class="pal"><div><small>made of</small>{sw(d["body"])}</div><div><small>glows with</small>{sw(d["glow"],"g")}</div></div></header>
<p class="mood">{E(d["mood"])}</p>
<div class="cols"><div><h3>architecture</h3><p>{E(d["arch"])}</p><h3>materials</h3><p>{E(d["materials"])}</p><h3>across the eras</h3><p>{E(d["eras"])}</p><h3>signature</h3><p>{E(d["signature"])}</p></div>
<div><h3>key buildings and places</h3>{lst(d["key"])}<h3>moments</h3>{lst(d["moments"])}<h3>the poems it holds</h3>{lst(d["poems"])}</div></div>
<div class="grid">{"".join(img(i) for i in d["images"])}</div></section>''')
prow=''.join(f'<tr><td>{n}</td><td>{E(t)}</td><td><a href="#{d}">{E(DM[d]["name"])}</a></td><td class="strip">{"".join(img(i) for i in im)}</td></tr>' for n,t,d,im in POEMS)
nav=''.join(f'<a href="#{d["id"]}"><i style="background:{d["color"]}"></i>{E(d["name"])}</a>' for d in D)
# a small map of the realms on the movie map's own coordinates
MX=lambda x: 20+x/8000*560; MY=lambda y: 20+y/6000*420
PTS={'naraka':(2089,1891),'haze':(2621,2146),'hive':(1463,1824),'overseer':(2099,1179),'bay':(1469,2345),'commons':(1036,2130),'arcade':(1168,2774),'cenotaph':(2107,3201),'plaza':(5120,3540),'ankhu':(5280,3740),'temple':(3422,4181)}
LBL={'naraka':(0,-14),'hive':(-30,-4),'overseer':(0,-16),'haze':(34,8),'bay':(-36,18),'commons':(-50,-6),'arcade':(-10,26),'cenotaph':(0,22),'plaza':(-40,-20),'ankhu':(30,26),'temple':(0,24)}
dots=''.join(f'<circle cx="{MX(x):.0f}" cy="{MY(y):.0f}" r="9" fill="{DM[k]["color"]}"/><text x="{MX(x)+LBL[k][0]:.0f}" y="{MY(y)+LBL[k][1]:.0f}">{E(DM[k]["name"].replace("The ","").split(" &")[0])}</text>' for k,(x,y) in PTS.items())
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlantis Districts</title>
<style>
:root{{--bg:#0b0d10;--ink:#ece6da;--dim:#9a958c;--line:rgba(255,255,255,.12);color-scheme:dark}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 ui-sans-serif,-apple-system,"Helvetica Neue",Arial}}
main{{max-width:1180px;margin:0 auto;padding:28px 16px 80px}}h1{{font:600 30px/1.15 Georgia,serif;margin:0 0 6px}}h2{{font:600 24px Georgia,serif;margin:0}}
h3{{font:600 10px ui-monospace,Menlo,monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--dim);margin:14px 0 4px}}
.lede{{font:17px/1.6 Georgia,serif;color:#e5dccb;max-width:820px}}nav{{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0}}nav a{{color:var(--ink);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:12px;display:flex;gap:6px;align-items:center}}
nav i,.pal i{{display:inline-block;width:14px;height:14px;border-radius:3px}}section{{border-top:1px solid var(--line);padding:26px 0 10px;margin-top:22px}}
header{{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;align-items:flex-start}}.realm{{color:var(--dim);font-size:12px;margin-top:3px}}
.pal{{display:flex;flex-direction:column;gap:4px}}.pal div{{display:flex;gap:3px;align-items:center}}.pal small{{width:68px;color:var(--dim);font-size:11px}}.pal i{{width:26px;height:18px}}.pal i.g{{box-shadow:0 0 10px currentColor}}
.mood{{font:italic 17px/1.5 Georgia,serif;color:#fff1da;border-left:3px solid var(--g);padding-left:12px;margin:14px 0}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:4px 28px}}.cols p{{margin:0}}ul{{margin:0;padding-left:18px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px;margin-top:16px}}
.im{{position:relative;display:block;border-radius:8px;overflow:hidden;background:#000;aspect-ratio:16/9}}.im img{{width:100%;height:100%;object-fit:cover;display:block}}
.im b{{position:absolute;left:6px;top:5px;font:600 11px ui-monospace,Menlo,monospace;background:rgba(0,0,0,.6);padding:1px 5px;border-radius:4px}}
.im span{{position:absolute;left:0;right:0;bottom:0;font-size:10.5px;line-height:1.3;padding:14px 7px 5px;background:linear-gradient(transparent,rgba(0,0,0,.85));opacity:0;transition:opacity .2s}}.im:hover span{{opacity:1}}
table{{border-collapse:collapse;width:100%;margin-top:10px}}td{{border-top:1px solid var(--line);padding:8px 8px;vertical-align:middle}}td a{{color:var(--ink)}}
td.strip{{display:flex;gap:6px}}td.strip .im{{width:150px;flex:0 0 150px}}td:first-child{{font:600 12px ui-monospace,Menlo,monospace;color:var(--dim)}}
.overview{{display:grid;grid-template-columns:600px 1fr;gap:24px;align-items:start;margin-top:18px}}svg text{{font:11px ui-sans-serif,Arial;fill:#fff;text-anchor:middle;paint-order:stroke;stroke:#121820;stroke-width:3px}}
.heights td{{font-size:13px}}.heights td:first-child{{font:600 12px ui-monospace,Menlo,monospace;color:var(--ink);width:120px}}
@media (max-width:760px){{.cols,.overview{{grid-template-columns:1fr}}svg{{width:100%;height:auto}}td.strip .im{{width:96px;flex-basis:96px}}}}
</style></head><body><main>
<h1>Atlantis, by district</h1>
<p class="lede">A vertical city of memory, rebuilt by the diaspora on the ruins of the Fall. The low city lives by water and trade in a twilight that never ends (Mirror Thread Bay, Naraka Market). The middle city is the concrete inheritance of the New Boroughs, still burned orange by the Fall’s smoke and crossed on catwalks above it (the Orange Haze, Cenotaph Rail, the Shrouded Arcade). The old order’s cold blue towers still keep watch (the Hive, the Overseer). On the mountain the new high city grows gardens in the air (Ankhu Spires), reached through the Light Gate into the Central Plaza. Its civic heart listens: radio dishes stand in Cortex Commons. Above everything, the sky is ancestral (the Ascent).</p>
<nav>{nav}</nav>
<div class="overview"><svg viewBox="0 0 600 460" width="600" height="460"><rect x="20" y="20" width="560" height="420" fill="#121820" stroke="rgba(255,255,255,.15)"/>
<text x="150" y="44" style="fill:#9a958c">B · the old harbor city</text><text x="470" y="290" style="fill:#9a958c">A · Atlantis, on the high ground</text><text x="330" y="430" style="fill:#9a958c">C · the shore</text>{dots}
<path d="M {MX(2107):.0f} {MY(3201):.0f} C {MX(3000):.0f} {MY(3600):.0f}, {MX(4200):.0f} {MY(3700):.0f}, {MX(5120):.0f} {MY(3540):.0f}" stroke="#f06629" stroke-dasharray="4 4" fill="none"/><text x="{MX(3700):.0f}" y="{MY(3500):.0f}" style="fill:#f06629">Cenotaph Rail</text></svg>
<div><h3>colour by height</h3><table class="heights">
<tr><td>the sky</td><td>star white, cosmic violet, deep ultramarine — the Ascent</td></tr>
<tr><td>the high city</td><td>terracotta and coral stone, periwinkle mist, violet underlight, one red core — Ankhu Spires</td></tr>
<tr><td>the towers</td><td>cold blue and indigo, signal red, the moon — the Hive, the Overseer</td></tr>
<tr><td>the middle</td><td>sodium orange smog, rust, raw concrete — the Orange Haze, Cenotaph Rail; screen-light — the Arcade</td></tr>
<tr><td>the ground</td><td>teal steel and turquoise water, tungsten bulbs, coral neon, bioluminescent cobalt — Naraka, the Bay</td></tr>
<tr><td>the civic</td><td>pale stone, rose terraces, warm windows at dusk — Cortex Commons, the Plaza, the White Temple</td></tr></table>
<h3>how to read this</h3><p style="color:var(--dim);font-size:13px">Every palette is measured from the images: <i>made of</i> is the body of the frames; <i>glows with</i> is their bright, saturated light. Numbers are the views (hover for the prompt, click for the full image). Places are on the movie map’s own coordinates and districts.</p></div></div>
<section><h2>The fourteen poems, placed</h2><table>{prow}</table></section>
{"".join(sec)}
</main></body></html>'''
open('_city/index.html','w').write(page)
print('wrote _city/index.html and _city/districts.json')
