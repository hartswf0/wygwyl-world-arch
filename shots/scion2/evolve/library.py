"""The card library as the evolver sees it: shots/skinlab/library.json + labels.json overlays + the poet contract's
fix fields + library_harvest.json, with one hard filter per target: no card that shares a pixel with the target painting.

    cards(char, costume)          -> list of normalised card dicts (all slots, before the per-target filter)
    pool(char, costume, target)   -> {slot: [card, ...]} usable against that target painting, with the reasons cards left

A normalised card:
  id, img (abs path), w, h, slot, side (L/R/None), view ('front' / 'threequarter' / 'side' / 'back' / 'threequarter_back' / None),
  A, B (card px: proximal joint, distal joint), ppc (px per cm), left (profile drawn facing screen-left, or None),
  erase [[x0,y0,x1,y1]], trim (px of alpha erosion), family (kit sheet id, or 'harvest:<source painting>'),
  kind ('kit' or 'harvest'), source (painting the pixels were cut from, harvest only), sheet_bbox (kit card's box on its sheet)
"""
import json, os, functools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SKIN = os.path.join(ROOT, 'shots/skinlab')
CUT = os.path.join(ROOT, 'shots/kits/cut')

BODY = ('head', 'torso', 'pelvis', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot')
VIEWN = {'profile': 'side', 'side': 'side', 'front': 'front', 'threequarter': 'threequarter', 'back': 'back',
         'threequarter_back': 'threequarter_back'}


@functools.lru_cache(None)
def _sheet(sid):
    p = os.path.join(CUT, sid, 'sheet.json')
    if not os.path.exists(p):
        return {}
    return {q['id']: q for q in json.load(open(p)).get('parts', [])}


@functools.lru_cache(None)
def _raw():
    L = json.load(open(os.path.join(SKIN, 'library.json')))
    H = json.load(open(os.path.join(SKIN, 'library_harvest.json')))['cards']
    lab = json.load(open(os.path.join(SKIN, 'labels.json'))).get('cards', {})
    fix = json.load(open(os.path.join(SKIN, 'contracts/poet.json'))).get('fix', {})
    return L, H, lab, fix


@functools.lru_cache(None)
def cards(char, costume):
    L, H, lab, fix = _raw()
    out = []
    # the library lists 41 ids twice under two slots (re-filed: hip bridges as thigh and pelvis, ...); the later
    # entry is the re-filing and wins, so one id is one card
    last = {c['id']: c for c in L + H}
    for c in last.values():
        if c['character'] != char:
            continue
        h = dict(lab.get(c['id'], {}))
        h.update(fix.get(c['id'], {}))     # the contract's A/B / px_per_cm / erase fixes win over the library
        harvest = c['id'].startswith('harvest.')
        slot = h.get('slot') or c['slot']
        if slot not in BODY:
            continue
        # the same man's head from another costume sheet is allowed (the contract does this), marked for coherence
        if c['costume'] != costume and slot != 'head':
            continue
        sid = c['id'].rsplit('/', 1)[0]
        part = {} if harvest else _sheet(sid).get(c['id'], {})
        img = os.path.normpath(os.path.join(SKIN, c['img']))
        if not os.path.exists(img):
            continue
        d = {
            'id': c['id'], 'img': img, 'w': c['w'], 'h': c['h'], 'slot': slot, 'side': c.get('side'),
            'view': VIEWN.get(h.get('view') or c.get('view') or ''), 'A': list(h.get('A') or c['A']), 'B': list(h.get('B') or c['B']),
            'ppc': float(h.get('px_per_cm') or c['px_per_cm']), 'ppc_fixed': 'px_per_cm' in h, 'left': h.get('left'), 'erase': h.get('erase', []), 'trim': h.get('trim', 0),
            'kind': 'harvest' if harvest else 'kit', 'source': c.get('source'), 'q': c.get('q'), 'pts': c.get('pts'),
            'family': ('harvest:' + str(c.get('source'))) if harvest else sid, 'sheet_kind': part.get('kind'), 'sheet_bbox': part.get('bbox'),
            'bad': bool(h.get('bad') or c.get('bad')), 'why_bad': c.get('why') or ([h.get('note')] if h.get('bad') else []),
            'tone': c.get('tone'), 'pal': c.get('pal'), 'faces': c.get('faces'), 'brads': c.get('brads') or [],
            'painted': h.get('painted'), 'other_costume': c['costume'] != costume, 'facing': c.get('facing'), 'ratio': c.get('ratio'), 'label': c.get('label', ''),
        }
        if d['view'] is None and (c.get('clip') or {}).get('view_l_p', 0) > .8:
            d['view'] = VIEWN.get(c['clip']['view_l'])
        if d['view'] is None and slot == 'head':
            # heads: the library's pixel estimate, and the card's own name (rear / back / profile / three-quarter)
            nm = c['id'].rsplit('/', 1)[-1].lower()
            d['view'] = ('back' if any(w in nm for w in ('rear', 'back')) else 'side' if 'profile' in nm else
                         'threequarter' if 'three' in nm else VIEWN.get(c.get('est_view') or ''))
        out.append(d)
    return out


def _boxes_touch(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def excluded(c, target_id, all_targets=()):
    """None if the card may be used against target_id, else the reason it may not."""
    sheet, _ = target_id.rsplit('/', 1)
    if c['kind'] == 'harvest' and c['source'] == target_id:
        return 'cut from the target painting'
    if c['id'] == target_id:
        return 'is the target painting'
    if c['kind'] == 'kit':
        if c['family'] == sheet:
            tb = _sheet(sheet).get(target_id, {}).get('bbox')
            if tb and c['sheet_bbox'] and _boxes_touch(tb, c['sheet_bbox']):
                return 'overlaps the target painting on its sheet'
        if c['id'] in all_targets:
            return 'a whole painting filed as a card'
        if c['sheet_kind'] in ('ref', 'pose') and c['slot'] != 'head':
            return 'sheet calls it a reference / pose figure, not a part'
    if c['bad']:
        return 'flagged bad: ' + '; '.join(map(str, c['why_bad']))[:80]
    return None


def pool(char, costume, target_id, all_targets=()):
    P, gone = {s: [] for s in BODY}, []
    for c in cards(char, costume):
        why = excluded(c, target_id, all_targets)
        if why:
            gone.append((c['id'], why))
        else:
            P[c['slot']].append(c)
    return P, gone
