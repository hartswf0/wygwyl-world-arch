"""Stage plans for every poem (shots/stage/plans/NN.json) and a reusable set spec per place (shots/stage/sets/NN.<set>.json).

    python3 shots/stage/scale.py                 # once: measure the footage planes (scale.json)
    python3 shots/stage/plan_poems.py            # set specs for every poem + plans for poems without a plan
    python3 shots/stage/plan_poems.py 07 13 -f   # these, replacing an existing auto plan (hand plans are kept unless -F)

SET SPECS (sets/NN.<set>.json): for each dossier place, every material that can build it, sorted by depth band
  sky · wall (interiors) · back · water · mid · floor · front, each a list of alternatives, best first:
    part   cardboard strips from the poem's cut set / hero sheets (the sheet named like the place first)
    plane  segmented footage: the place's own stills (dossier refs) split into sky / distant / mid / near sheets,
           with their measured horizon so they register under the cardboard
  plus pieces (free-standing cut set parts with a real height and a default depth), fx washes, archive/atlas
  images (tagged, with the blend that seats them) and the footage stills themselves.
SCENES reference a set spec ("setSpec") + a camera from the scale model (scale.py: shot size, camera height,
horizon, floor line, px per cm) + overrides (which alternative each band uses), and carry the resolved layers,
back to front: footage base · sky · far footage · back · water · mid · floor · pieces/archive/cast/props by depth
(far first) · front strip · fx · hidden extras (solved action, alternates, atlas refs).
Everything is a first pass to rearrange on the stage; plans without "auto": true are never overwritten.
"""
import json, os, re, sys
from PIL import Image, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scale as SC

SHOTS = os.path.dirname(HERE)
CAT = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'catalog.json')))['sheets']
ASSETS = json.load(open(os.path.join(HERE, 'assets.json')))
SCALE = SC.load()
if not SCALE:
    SC.main()
    SCALE = SC.load()
W, H = 1600, 900
STOP = {'the', 'and', 'set', 'hero', 'props', 'with', 'his', 'her', 'separate', 'parts', 'layers', 'poem', 'card', 'cards', 'from', 'into', 'for', 'one', 'two',
        'its', 'that', 'this', 'are', 'all', 'only', 'then', 'each', 'off', 'out', 'over', 'under', 'night', 'day'}
words = lambda s: {w.rstrip('s') for w in re.findall(r'[a-z]+', str(s).lower().replace('_', ' ')) if len(w) > 2} - STOP

REF = re.compile(r'reference|assembled|assembly|composite|not a cutout|overview|example|proof|instruction|turnaround|labels?\b|key\b|legend|sheet\b', re.I)
SKY = r'\bsky\b|clouds?\b|stars?\b|starfield|gradient|ceiling|heaven|moon ?sky|dusk|dawn|backdrop|galaxy|milky'
WATER = r'\bsea\b|ocean|water|lake|\bpool\b|river|tide|wave|harbou?r water|reflection'
FLOOR = r'floor|ground|deck|street|pavement|paving|road|asphalt|sand|\bash\b|soil|grass|tiles?\b|apron|carpet|boards|quay|terrace|plaza|courtyard|field|earth|dirt|path|trail|platform|stage floor|causeway'
FRONT = r'\bfront\b|foreground|\bnear\b|rail|kerb|curb|bush|weeds?|heads|silhouettes?|counter|railing|fence|hedge|bar front'
FAR = r'skyline|city|treeline|tree line|mountains?|horizon|hills?|\bfar\b|distant|cliffs?|dunes?|range|outline'
WALL = r'\bwall|backwall|brick|projection|curtain|interior|backing|panel wall|window wall'


def num(code):
    try:
        return float(code)
    except (TypeError, ValueError):
        return None


def clean(p):
    lab = p.get('label') or ''
    return not REF.search(lab) and p['bbox'][2] >= 40 and p['bbox'][3] >= 40 and p['bbox'][2] * p['bbox'][3] >= 3500


def sheets_of(n, folder):
    return {sid: dict(s, parts=[p for p in s['parts'] if clean(p)]) for sid, s in CAT.items()
            if n in s['poems'] and s['folder'] == folder and s['parts']}


def lab_of(p):
    return ((p.get('label') or '') + ' ' + p['id'].split('/')[1].replace('-', ' ')).lower()


# ─────────────────────────── set specs ───────────────────────────
def band_of(p):
    lab, (w, h) = lab_of(p), p['bbox'][2:]
    ar = w / h
    if ar >= 2.6 and w >= 380:
        for band, rx in (('sky', SKY), ('water', WATER), ('floor', FLOOR), ('front', FRONT), ('back', FAR), ('wall', WALL)):
            if re.search(rx, lab):
                return band
        return 'mid'
    if w >= 480 and h >= 200:
        if re.search(SKY, lab) and ar >= 1.6:
            return 'sky'
        if re.search(WALL, lab):
            return 'wall'
        if re.search(FLOOR, lab) and ar >= 1.8:
            return 'floor'
    if re.search(r'^(\W|part|\d)*$', p.get('label') or '') and ar > 4:   # an unlabelled strip-ish card: middle band
        return 'mid'
    if w * h >= 9000 and h >= 70:
        return 'piece'
    return None


def footage_for(n, S):
    """The place's own footage stills (dossier refs), else the poem's still whose plane contents share most words
    with the place (marked borrowed)."""
    own = [r for r in S.get('refs') or [] if '/' not in r and r in ASSETS['planes']]
    out = [(r, True) for r in own]
    if not out:
        ws = words(S.get('name', '') + ' ' + S.get('look', '') + ' ' + ' '.join((S.get('layers') or {}).values()))
        cands = []
        for r in ASSETS['poems'][n]['planes']:
            P = ASSETS['planes'][r]
            cw = words(' '.join(' '.join(s.get('contents') or []) for s in P['sheets']))
            cands.append((len(cw & ws), r))
        cands.sort(key=lambda t: -t[0])
        out = [(r, False) for sc, r in cands[:2]]
    res = []
    for r, mine in out:
        P, M = ASSETS['planes'][r], SCALE['planes'].get(r, {'horizon': .5, 'sheets': {}})

        def pick(plane, need_wide=.4):
            c = [s for s in P['sheets'] if s.get('plane') == plane and M['sheets'].get(s['sheet'], {}).get('wide', 1) >= need_wide]
            c.sort(key=lambda s: -M['sheets'].get(s['sheet'], {}).get('cover', 0))
            return [{'kind': 'plane', 'src': s['file'], 'still': P['short'], 'plane': plane, 'contents': s.get('contents', [])[:4],
                     'bbox': M['sheets'].get(s['sheet'], {}).get('bbox'), 'opaque': M['sheets'].get(s['sheet'], {}).get('opaque', False)} for s in c[:1]]
        res.append({'still': r, 'short': P['short'], 'own': mine, 'horizon': M['horizon'], 'backdrop': P['backdrop'], 'thumb': P['thumb'],
                    'sky': pick('sky / atmosphere', .6), 'far': pick('distant background'), 'mid': pick('midground'), 'front': pick('foreground')})
    return res


def image_meta(rel_from_poems):
    p = os.path.join(SHOTS, 'poems', rel_from_poems)
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert('L')
    w, h = im.size
    lum = ImageStat.Stat(im).mean[0] / 255
    return {'ar': round(h / w, 4), 'lum': round(lum, 3)}


def archive_for(n, S, extra=()):
    imgs = {i['file']: i for i in ASSETS['poems'][n]['images']}
    out, seen = [], set()
    for r in list(extra) + list(S.get('atlas_refs') or []):
        f = '../poems/' + r
        if f in seen:
            continue
        seen.add(f)
        meta = image_meta(r)
        if not meta:
            continue
        i = imgs.get(f, {})
        lab = i.get('label') or S.get('name') or ''
        if REF.search(lab):
            continue
        src = r.split('/')[2] if r.count('/') > 2 else 'atlas'
        out.append({'kind': 'image', 'src': f, 'label': lab[:90], 'source': src, 'use': i.get('use'), 'ar': meta['ar'], 'lum': meta['lum'],
                    'blend': 'screen' if meta['lum'] < .42 else 'multiply', 'tag': f'ARCHIVE · {src} · {lab}'[:70]})
    return out


def build_set(n, S):
    sid_words = words(S['id'] + ' ' + S.get('name', ''))
    look = S.get('look', '') + ' ' + S.get('light', '')
    sheets = sheets_of(n, '04_SETS_AND_BUILDINGS')
    if not re.search(SC.VOID, S['id']):   # a black void card is never a band of a lit place
        sheets = {k: v for k, v in sheets.items() if not re.search(r'void|\.black\b', k)}

    def sheet_score(sid):
        sh = CAT[sid]
        return 2 * len(sid_words & words(sid.split('.', 2)[-1] + ' ' + (sh.get('title') or ''))) + .4 * len(words(look) & words(sid)) + (.5 if sid.startswith(n) else 0)
    ranked = sorted(sheets, key=lambda s: -sheet_score(s))
    primary = [s for s in ranked if sheet_score(s) >= 2][:2]
    bands = {b: [] for b in ('sky', 'wall', 'back', 'water', 'mid', 'floor', 'front')}
    pieces = []
    layer_txt = S.get('layers') or {}
    for sid in ranked:
        prio = 0 if sid in primary else 1 if sid.startswith(n) else 2
        for p in sheets[sid]['parts']:
            b = band_of(p)
            if not b:
                continue
            fit = len(words(lab_of(p)) & words(layer_txt.get(b if b in layer_txt else {'wall': 'back', 'water': 'back'}.get(b, b), '') + ' ' + look))
            alt = {'kind': 'part', 'part': p['id'], 'label': p.get('label') or '', 'size': p['bbox'][2:], 'from': sid, 'prio': prio, 'fit': fit}
            if b == 'piece':
                if prio == 0:
                    cm, k = SC.piece_size(lab_of(p))
                    pieces.append(alt | {'height_cm': cm, 'k': k})
            else:
                bands[b].append(alt)
    interior = bool(re.search(SC.INTERIOR, S['id']))
    OUTDOOR, INDOOR = r'reflect|water|\bsea\b|wave|field|soil|ground|grass|sand|\bash\b|planted|earth|dirt|road|street|trail|path|causeway|quay|asphalt', r'carpet|boards|parquet|rug|dance floor|lino'
    for b in ('floor', 'front', 'mid'):   # borrowed lengths must suit the place: no planted ground in a living room
        bands[b] = [a for a in bands[b] if a['prio'] == 0 or not re.search(OUTDOOR if interior else INDOOR, lab_of({'label': a['label'], 'id': a['part']}))]
    bands['mid'] = [a for a in bands['mid'] if a['prio'] == 0]
    for b in bands:
        bands[b].sort(key=lambda a: (a['prio'], -a['fit'], -a['size'][0]))
        bands[b] = bands[b][:6]
    pieces.sort(key=lambda a: (-a['fit'], -a['size'][0] * a['size'][1]))
    foot = footage_for(n, S)
    for f in foot:   # the footage sheets as alternates in their bands
        for band, key in (('sky', 'sky'), ('back', 'far'), ('mid', 'mid'), ('front', 'front')):
            for a in f[key]:
                bands[band].append(a | {'own': f['own'], 'horizon': f['horizon']})
    fx = []
    for sid, sh in sheets_of(n, '05_PAINTED_EFFECTS').items():
        for p in sh['parts']:
            lab = lab_of(p)
            if re.search(r'haze|mist|fog|smoke|glow|wash|rain|dust|spray|light', lab) and p['bbox'][2] >= 300:
                fx.append({'kind': 'part', 'part': p['id'], 'label': p.get('label'), 'size': p['bbox'][2:], 'fit': len(words(lab) & words(look))})
    fx.sort(key=lambda a: -a['fit'])
    name = (S['id'] + ' ' + S.get('name', '')).lower()
    return {'id': S['id'], 'poem': n, 'name': S.get('name'), 'look': S.get('look'), 'light': S.get('light'), 'dossier_layers': layer_txt,
            'interior': bool(re.search(SC.INTERIOR, S['id'])), 'void': bool(re.search(SC.VOID, S['id'])),
            'screen_wall': bool(re.search(r'screen|projection|billboard|poster|marquee|\btv\b|signs?\b|led', name + ' ' + (S.get('look') or '').lower())),
            'cut_sheets': primary, 'bands': bands, 'pieces': pieces[:8], 'fx': fx[:4], 'footage': foot,
            'archive': archive_for(n, S), 'reuse': S.get('reuse') or []}


# ─────────────────────────── cast and props ───────────────────────────
WHO_RX = {'poet': r'poet|\bhe\b|\bhim\b|\bman\b', 'ex': r'\bex\b|lover', 'young_poet': r'young|child|younger|\bboy\b|six', 'ghost_child': r'ghost|\bgirl\b|seven',
          'woman': r'mother|\bshe\b|woman|\bher\b', 'parents': r'father|parents|\bcar\b', 'party': r'party|guests?|crowd|dancers?|\bdj\b|fans?|strangers',
          'angels': r'angels?', 'ancestors': r'ancestors?|parade|orchestra|elders?|\bmae\b', 'atlantis': r'generations|citizens|gatekeeper|travell?ers|crowd|people',
          'family': r'family|brother|friends?|couples?|watchers|elders|people|b-roll|mason'}
CROWD = {'party', 'ancestors', 'atlantis', 'family', 'angels'}


def poses(n, who, fallback=False):
    """Cut pose figures for a character in this poem."""
    out = []
    for sid, s in sheets_of(n, '02_ACTIONS_AND_POSES').items():
        if 'pose' not in sid:
            continue
        head = sid.split('.')[0]
        ok = {'poet': head == 'poet', 'young_poet': head == 'young_poet', 'ghost_child': head == 'young_ghost', 'family': head == 'family',
              'party': head == 'party' or sid.startswith('08.cast.club'), 'angels': sid.startswith('08.cast.angel')}.get(who, head == who)
        for p in s['parts']:
            exy = re.search(r'\bex\b', p.get('label') or '', re.I)
            if who == 'ex' and not exy:
                continue
            if who != 'ex' and (not ok or exy):
                continue
            w, h = p['bbox'][2:]
            if p['kind'] == 'pose' and h >= 150 and w >= .12 * h and not re.search(r'fx only|boots', p.get('label') or '', re.I):
                out.append(p)
    if not out and who == 'poet' and not fallback:   # no pose sheet for this poem: the same costume's poses from the nearest poem
        D = json.load(open(os.path.join(SHOTS, 'poems', 'dossier', f'{n}.json')))
        cos = next((c.get('costume') for c in D.get('characters') or [] if c['id'] == 'poet'), None)
        for m in sorted((f'{i:02d}' for i in range(1, 15)), key=lambda m: abs(int(m) - int(n))):
            Dm = json.load(open(os.path.join(SHOTS, 'poems', 'dossier', f'{m}.json')))
            if m != n and next((c.get('costume') for c in Dm.get('characters') or [] if c['id'] == 'poet'), None) == cos:
                out = poses(m, 'poet', fallback=True)
                if out:
                    break
    return out


def panel_no(p):
    m = re.match(r'\s*0?(\d{1,2})\b', p['label'] or '')
    return int(m.group(1)) if m else None


def pick_pose(ps, key, used, i, text=''):
    """The figure for scene `key` (the i-th scene): its scene number, a label that the staging names, its panel
    number in order, else the least used."""
    k = num(key)
    tw = words(text)
    tests = (lambda p: p.get('scene') == key, lambda p: len(words(p['label']) & tw) >= 2, lambda p: panel_no(p) == i + 1, lambda p: len(words(p['label']) & tw) >= 1)
    for test in tests:
        hit = [p for p in ps if test(p) and p['id'] not in used]
        if hit:
            return hit[0]
    ranked = sorted(ps, key=lambda p: (p['id'] in used, abs(num(p.get('scene')) - k) if num(p.get('scene')) and k else 99))
    return ranked[0] if ranked else None


# ─────────────────────────── scene composition ───────────────────────────
def r(v):
    return round(v)


def plane_reg(src, hz, cam, label, cover_bottom=True):
    """A full-frame footage sheet scaled and shifted so its measured horizon `hz` lands on the scene's horizon
    and it still covers the frame top (and bottom, for a base plate)."""
    Hy = cam['horizon_y']
    if Hy < 0:   # top-down: no horizon, fill the frame
        return {'kind': 'plane', 'src': src, 'x': 800, 'y': 450, 'w': 1600, 'h': 900, 'label': label}
    s = max(1.0, Hy / (hz * H) + .02)
    if cover_bottom:
        s = max(s, (H - Hy) / ((1 - hz) * H) + .02)
    top = Hy - hz * H * s
    return {'kind': 'plane', 'src': src, 'x': 800, 'y': r(top + H * s / 2), 'w': r(W * s), 'h': r(H * s), 'label': label}


def stretch(part, y0, y1, w=1720, x=800, **kw):
    return {'part': part, 'x': x, 'y': r((y0 + y1) / 2), 'w': w, 'h': r(y1 - y0)} | kw


def strip_h(alt, w=1720):
    return alt['size'][1] * w / alt['size'][0]


def compose(n, sc, g, si, spec, cam, D, chars, used, all_prop_parts):
    text = ' '.join([sc.get('what', ''), g.get('shot', ''), sc.get('block') or ''])
    Hy, foot, ppc = cam['horizon_y'], cam['foot_y'], cam['ppc']
    B = spec['bands']
    cut = lambda b: [a for a in B[b] if a['kind'] == 'part']
    foot_alts = [f for f in spec['footage']]
    F = foot_alts[0] if foot_alts else None
    use, back, objs, front, hidden = {}, [], [], [], []
    top = cam['shot'] == 'TOP'
    interior = spec['interior']
    kw = {'ELS': 1.5, 'WS': 2.0, 'POV': 2.0, 'MWS': 2.4, 'MS': 3.0, 'CU': 4.0, 'INSERT': 3.0}.get(cam['shot'], 2.0)
    wall_base = SC.at(cam, kw)[0] if interior and not top else Hy
    floor_top = wall_base if interior else Hy

    # 1 base plate: footage registered to the horizon (fills any gap under the cardboard)
    if F:
        back.append(plane_reg(F['backdrop'], F['horizon'], cam, F['short'] + ' backdrop (base plate)'))
        use['base'] = 'plane:' + F['short']
    elif cut('sky'):
        back.append(stretch(cut('sky')[0]['part'], -10, 910, w=1700))
        use['base'] = 'part:' + cut('sky')[0]['part']

    if spec['void']:
        void = [a for b in ('sky', 'mid', 'wall', 'back') for a in cut(b)]
        allp = [p for p in CAT.get(f'{n}.set.black_void', {}).get('parts', [])] + [p for sid in spec['cut_sheets'] for p in CAT[sid]['parts']]
        if allp:
            back = [stretch(allp[0]['id'], -10, 910, w=1700)]
            use['base'] = 'part:' + allp[0]['id']
        elif void:
            back = [stretch(void[0]['part'], -10, 910, w=1700)]
        floor_top = 905
    elif top:
        fl = cut('floor') or cut('mid')
        if fl:
            back.append(stretch(fl[0]['part'], -20, 920, w=1700))
            use['floor'] = fl[0]['part']
    else:
        # 2 sky / ceiling + wall
        own_foot = F and F['own']
        sky_cut = cut('sky')
        sky_foot = [a for a in B['sky'] if a['kind'] == 'plane' and a.get('own')]
        if interior:
            walls = cut('wall') or [a for a in cut('back') if a['size'][1] >= 150]
            c = max(70, .28 * wall_base) if sky_cut and walls else wall_base
            if sky_cut and Hy > 40:
                back.append(stretch(sky_cut[0]['part'], -12, c + 12, w=1720))
                use['ceiling'] = sky_cut[0]['part']
            if walls:
                back.append(stretch(walls[0]['part'], (c - 10) if sky_cut else -12, wall_base + 10))
                use['wall'] = walls[0]['part']
                for extra in walls[1:2]:
                    hidden.append(stretch(extra['part'], -12, wall_base + 10, hide=True))
        else:
            if sky_foot and (not sky_cut or (own_foot and si % 2 == 1)):   # mosaic: the place's own sky plate on alternate scenes
                a = sky_foot[0]
                back.append(plane_reg(a['src'], a['horizon'], cam, a['still'] + ' sky plate', cover_bottom=False))
                use['sky'] = 'plane:' + a['still']
                if sky_cut:
                    hidden.append(stretch(sky_cut[0]['part'], -12, Hy + 50, hide=True))
            elif sky_cut:
                back.append(stretch(sky_cut[0]['part'], -12, Hy + 50))
                use['sky'] = sky_cut[0]['part']
                if sky_foot:
                    hidden.append(plane_reg(sky_foot[0]['src'], sky_foot[0]['horizon'], cam, sky_foot[0]['still'] + ' sky plate', cover_bottom=False) | {'hide': True})
            # 3 the place's own distant footage registered on the horizon, under the cardboard back strip
            far_foot = [a for a in B['back'] if a['kind'] == 'plane' and a.get('own')]
            if far_foot:
                a = far_foot[0]
                back.append(plane_reg(a['src'], a['horizon'], cam, a['still'] + ' distance (' + ', '.join(a['contents'][:2]) + ')', cover_bottom=False))
                use['far'] = 'plane:' + a['still']
            # 4 back strip sitting on the horizon
            bk = cut('back')
            if bk and Hy > 60:
                h = min(max(70, strip_h(bk[0])), max(90, .75 * Hy))
                back.append(stretch(bk[0]['part'], Hy + 14 - h, Hy + 14))
                use['back'] = bk[0]['part']
            # 5 water hangs from the horizon to the shore
            wt = cut('water')
            if wt:
                shore = SC.at(cam, 3.2)[0]
                h = max(strip_h(wt[0]), shore - Hy)
                back.append(stretch(wt[0]['part'], Hy - 4, min(905, Hy - 4 + h)))
                use['water'] = wt[0]['part']
                floor_top = max(floor_top, min(Hy - 4 + h - 30, foot - 40))
        # 6 floor from the horizon / wall base to the bottom edge (two lengths when one would stretch too far)
        fl = cut('floor')
        if fl:
            need = 908 - (floor_top - 8)
            nat = strip_h(fl[0])
            if need > 2.6 * nat and len(fl) > 1:
                mid = floor_top + .38 * need
                back.append(stretch(fl[1]['part'], floor_top - 8, mid + 6))
                back.append(stretch(fl[0]['part'], mid, 910))
            else:
                back.append(stretch(fl[0]['part'], floor_top - 8, 910))
            use['floor'] = fl[0]['part']
        # 7 mid strips: stand on the floor between horizon and subject
        for a, k in zip(cut('mid')[:2], (3.0, 1.9)):
            if interior and cam['shot'] in ('CU', 'MS'):
                break
            yb = SC.at(cam, k * (1.6 if interior else 1))[0]
            h = min(strip_h(a), .5 * H, max(60, yb - min(Hy, wall_base) + 140))
            back.append(stretch(a['part'], yb - h, yb + 6))
            use.setdefault('mid', []).append(a['part'])

    # 8 objects by depth: pieces, archive element, cast, props
    big = max(1, cam['ppc'] / 2.1) ** .75
    sx = cam['x']
    if not spec['void'] and not top:
        slots = [x for x in (250, 1360, 520, 1110, 120, 1500) if abs(x - sx) > 260]
        for a, x in zip(spec['pieces'][:4], slots):
            k = a['k'] * big
            fy, pk = SC.at(cam, k)
            ph = a['height_cm'] * pk
            pw = ph * a['size'][0] / a['size'][1]
            if pw > 900:
                pw, ph = 900, 900 * a['size'][1] / a['size'][0]
            if ph < 24 or fy - ph > fy - 10 and fy < Hy:
                continue
            if re.search(r'window|mirror|frame|poster|sign|screen|glass|pane|clock', lab_of({'label': a['label'], 'id': a['part']})) and interior:
                fy = wall_base - 90 * SC.at(cam, kw)[1]
            objs.append((k, {'part': a['part'], 'x': x, 'y': r(fy - ph / 2 + 4), 'w': r(pw)}))
            use.setdefault('pieces', []).append(a['part'])
    # archive element as an object in the world
    arch = archive_for(n, {'atlas_refs': spec_archive_refs(spec)}, extra=g.get('refs') or [])
    arch = [a for a in arch if a['source'] != 'foundry' or 'projection' in spec['id']] or []
    if arch and not spec['void'] and not top:
        a = arch[si % len(arch)]
        ax = 1200 if sx < 800 else 400
        if interior or spec['screen_wall']:
            kk = kw if interior else 2.6 * big
            fy, pk = SC.at(cam, kk)
            aw = min(640, max(200, 300 * pk))
            bottom = (wall_base if interior else fy) - 95 * pk
            L = {'kind': 'image', 'src': a['src'], 'x': ax, 'y': r(bottom - aw * a['ar'] / 2), 'w': r(aw), 'ar': a['ar']}
            objs.append((kk + .01, L | {'label': 'archive in the set: ' + a['label'][:60], 'tag': a['tag'], 'op': .92}))   # a print hung in the set: drawn plain
        else:   # exterior: a memory hung in the sky over the far distance
            aw = 380
            L = {'kind': 'image', 'src': a['src'], 'x': ax, 'y': r(max(aw * a['ar'] / 2 + 20, Hy - 60 - aw * a['ar'] / 2)), 'w': aw, 'ar': a['ar']}
            objs.append((50, L | {'label': 'archive in the sky: ' + a['label'][:60], 'tag': a['tag'], 'blend': 'screen', 'op': .75}))
        use['archive'] = a['src']
    # cast
    who = []
    for c in chars:
        if c in who:
            continue
        if c == 'poet' and cam['shot'] in ('POV', 'INSERT'):
            continue
        if c == 'poet' or re.search(WHO_RX.get(c, r'\b' + c + r'\b'), text, re.I):
            who.append(c)
    if cam['shot'] == 'INSERT':
        who = []
    k_others = iter([(1.25, 1.0), (2.1, -1.0), (3.0, 1.0)])
    crowd_x = iter([1230, 330, 1440, 170, 980])
    cast_layers = []
    subject = None
    for ci, c in enumerate(who[:4]):
        ps = poses(n, c)
        reps = 3 if c in CROWD and cam['shot'] in ('ELS', 'WS', 'MWS', 'POV') else 1
        for rep in range(reps):
            p = pick_pose(ps, sc['key'], used, si, text)
            if not p:
                break
            used.add(p['id'])
            hcm = SC.character_cm(c, n)
            if subject is None and rep == 0:
                k, x = 1.0, sx
            elif c in CROWD:
                k, x = (1.5 + .8 * rep) * (1.0 if cam['shot'] in ('ELS', 'WS', 'POV') else 1.4), next(crowd_x, 1300)
            else:
                k, side = next(k_others, (2.5, 1.0))
                x = sx + side * (110 * ppc / k + 160)
            fy, pk = SC.at(cam, k)
            f = SC.pose_factor(p.get('label'), p['bbox'])
            bw, bh = p['bbox'][2:]
            if f == 'lying':
                pw = hcm * 1.05 * pk
                ph = pw * bh / bw
            else:
                ph = hcm * f * pk
                pw = ph * bw / bh
            x = min(1600 - pw / 3, max(pw / 3, x))
            L = {'part': p['id'], 'x': r(x), 'y': r(fy - ph / 2 + .012 * ph), 'w': r(pw)}
            if x > 900 and c != 'poet' and rep == 0:
                L['flip'] = True
            if subject is None:
                subject = {'who': c, 'x': x, 'w': pw, 'h': ph, 'foot': fy, 'ppc': pk}
            cast_layers.append((k, L, c))
            objs.append((k, L))
        if ci == 0 and c == 'poet':
            pass
    # props the staging names (by the prop's own name), two at most, each part once
    placed = 0
    insert_ppc = None
    for pr in sorted(D.get('props') or [], key=lambda pr: not pr.get('hero')):
        toks = words(pr.get('name', '')) | words(pr['id'])
        if placed >= 2 or not toks & words(text):
            continue
        cand = [p for p in all_prop_parts if p['id'] not in used and (words(p.get('label')) & toks or words(p['id'].split('/')[0]) & toks)]
        cand = [p for p in cand if 1 / 6 < p['bbox'][2] / p['bbox'][3] < 6]
        if not cand:
            continue
        p = cand[0]
        used.add(p['id'])
        placed += 1
        cm = pr.get('scale_cm') or 40
        bw, bh = p['bbox'][2:]
        if cam['shot'] == 'INSERT' and placed == 1:   # the insert's subject fills about half the frame
            k = 1.0
            pk = min(30, .5 * H / cm)
            insert_ppc = pk
            fy = cam['foot_y']
            x = 800
        elif cm >= 250:   # a set-sized prop stands back in the set
            k = 2.2 * big
            fy, pk = SC.at(cam, k)
            x = 1180 if sx < 800 else 420
        else:
            k = .98
            fy, pk = SC.at(cam, k)
            held = pr.get('who') and cm <= 70 and subject
            if held:
                x = subject['x'] + .3 * subject['w'] * (1 if placed == 1 else -1)
                fy = subject['foot'] - .42 * subject['h']
            else:
                x = (subject['x'] if subject else sx) + (1 if placed == 1 else -1) * ((subject['w'] / 2 if subject else 0) + 45 * pk)
        long_px = cm * pk
        pw = long_px * bw / max(bw, bh)
        ph = pw * bh / bw
        if ph > 1.1 * H:
            pw, ph = pw * 1.1 * H / ph, 1.1 * H
        pw = max(pw, 26)
        ph = pw * bh / bw
        objs.append((k, {'part': p['id'], 'x': r(x), 'y': r(fy - ph / 2), 'w': r(pw)}))
        use.setdefault('props', []).append(p['id'])
    objs.sort(key=lambda t: -t[0])
    # painted fx wash across the middle distance, behind the cast so it hazes the set, not the faces
    if spec['fx'] and not spec['void']:
        a = spec['fx'][0]
        y = min(780, max(200, (Hy + foot) / 2 if not top else 450))
        back.append({'part': a['part'], 'x': 800, 'y': r(y), 'w': 1750, 'h': r(min(260, 1750 * a['size'][1] / a['size'][0])), 'op': .55, 'blend': 'screen'})
        use['fx'] = a['part']
    layers = back + [L for _, L in objs]

    # 9 front strip bleeding off the bottom (in front of the cast)
    fr = cut('front')
    if fr and not spec['void'] and not top and cam['shot'] != 'INSERT':
        h = min(strip_h(fr[0]), 150 if cam['shot'] in ('WS', 'ELS', 'POV', 'MWS') else 230)
        front.append(stretch(fr[0]['part'], 915 - h, 915))
        use['front'] = fr[0]['part']
    layers += front
    # 11 hidden extras: solved action for the movement, the atlas references
    for pat, act in ((r'\bwalk|stroll|climb|step|follow', 'ACT-001__man'), (r'kneel|crouch|search', 'ACT-003__man'),
                     (r'\bfall|falls|fell|drop', 'ACT-008__man'), (r'danc|spin', 'ACT-017__man'), (r'wait|stand|sits?\b|seated', 'ACT-024__man')):
        if re.search(pat, text, re.I) and any(a['id'] == act for a in ASSETS['actions']):
            ah = 180 * ppc
            hidden.append({'kind': 'action', 'action': act, 'x': r(sx), 'y': r(foot - ah / 2), 'w': r(ah * .6), 'hide': True,
                           'label': 'solved action for this beat (switch on to replace the still pose)'})
            break
    for a in arch[:3]:
        if a['src'] != use.get('archive'):
            hidden.append({'kind': 'image', 'src': a['src'], 'x': 1250, 'y': 230, 'w': 480, 'ar': a['ar'], 'label': a['label'][:60], 'tag': a['tag'],
                           'blend': a['blend'], 'op': .85, 'hide': True})
    layers += hidden
    cam_out = dict(cam)
    if insert_ppc:
        cam_out['insert_ppc'] = round(insert_ppc, 3)
    return layers, use, [c for c in who]


def spec_archive_refs(spec):
    return [a['src'].replace('../poems/', '') for a in spec['archive']]


def plan(n, write_sets=True):
    D = json.load(open(os.path.join(SHOTS, 'poems', 'dossier', f'{n}.json')))
    A = json.load(open(os.path.join(SHOTS, 'poems', 'atlas', f'{n}.json')))
    stg = {g['scene']: g for g in (D.get('atlas') or {}).get('staging') or []}
    sets = {s['id']: s for s in D.get('sets') or []}
    specs = {sid: build_set(n, S) for sid, S in sets.items()}
    if write_sets:
        os.makedirs(os.path.join(HERE, 'sets'), exist_ok=True)
        for sid, spec in specs.items():
            json.dump(spec, open(os.path.join(HERE, 'sets', f'{n}.{sid}.json'), 'w'), indent=1)
    chars = [c['id'] for c in D.get('characters') or []]
    chars = list(dict.fromkeys(chars))
    prop_parts = [p for s in sheets_of(n, '03_PROPS').values() for p in s['parts']]
    used, scenes = set(), []
    for si, sc in enumerate(A['scenes']):
        g = stg.get(sc['key'], {})
        set_id = g.get('set') if g.get('set') in specs else next(iter(specs), '')
        spec = specs.get(set_id)
        shot_txt = g.get('shot') or sc.get('block') or sc.get('camera') or ''
        shot, alts, cam_cm = SC.shot_of(shot_txt)
        if shot == 'INSERT':   # an insert needs a prop the staging names; a macro on the body is a close-up of him
            names = set().union(*[words(pr.get('name', '')) | words(pr['id']) for pr in D.get('props') or []] or [set()])
            if not names & words(shot_txt):
                shot, cam_cm = 'CU', SC.SHOTS['CU']['cam']
        subj = 'young_poet' if re.search(r'young_poet|young poet|\bboy\b', shot_txt, re.I) and 'young_poet' in chars and not re.search(r'\bpoet\b', shot_txt.replace('YOUNG', ''), re.I) else 'poet'
        cam = SC.camera(shot, cam_cm, SC.character_cm(subj, n))
        if spec:
            layers, use, who = compose(n, sc, g, si, spec, cam, D, chars, used, prop_parts)
        else:
            layers, use, who = [], {}, []
        scenes.append({'key': sc['key'], 'name': sc['name'], 'set': set_id, 'setSpec': f'sets/{n}.{set_id}.json' if spec else None,
                       'shot': shot_txt, 'camera': cam | {'alternates': alts}, 'overrides': use,
                       'note': f"{cam['size']} · camera {cam['cam_cm']} cm · horizon y{cam['horizon_y']} · {cam['ppc']} px/cm at the subject · set {set_id}"
                               + (' (interior)' if spec and spec['interior'] else '') + (' · footage ' + spec['footage'][0]['short'] if spec and spec['footage'] else ''),
                       'layers': layers})
    return {'num': n, 'title': D.get('title'), 'auto': True, 'scale': 'scale.json',
            'note': 'Built by plan_poems.py: each scene = a set spec (sets/) + a camera from the scale model (scale.py) + overrides; rearrange on the stage and export to keep.',
            'scenes': scenes}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    force, hard = '-f' in sys.argv, '-F' in sys.argv
    os.makedirs(os.path.join(HERE, 'plans'), exist_ok=True)
    for n in args or [f'{i:02d}' for i in range(1, 15)]:
        out = os.path.join(HERE, 'plans', f'{n}.json')
        P = plan(n)   # always refresh the set specs
        if os.path.exists(out):
            old = json.load(open(out))
            if not (hard or (force and old.get('auto'))):
                print(n, 'sets written; plan kept (exists' + ('' if old.get('auto') else ', hand plan') + ')')
                continue
        json.dump(P, open(out, 'w'), indent=1)
        print(n, P['title'], len(P['scenes']), 'scenes,', sum(len(s['layers']) for s in P['scenes']), 'layers ·',
              ' | '.join(f"{s['key']} {s['camera']['shot']}" for s in P['scenes']))


if __name__ == '__main__':
    main()
