"""Inventory every sheet that holds (or was laid out to hold) puppet parts.

    python3 shots/suite/tools/sheets.py       # writes shots/suite/data/sheets.json

Groups:
  kit3_v2_template  kit3/v2/templates/*.png          kit.py layouts (ghost cells + brad crosses), never painted
  kit3_v2_pack      kit3/v2/packs/*.jpg              A layout + B who + C style, the prompt image for a painter
  kit3_v2_render    kit3/v2/rendered/*.png           painted from a v2 pack
  poem_kit          kits/packs/poem_NN/0X_*/*.png    painted poem kits (unique by content hash; aliases kept)
  tracksuit_source  kits/packs/poet_tracksuit_v1/{02,03}_*/*.png
  weave_man         weave/cast/man/sheets/*.jpg      painted man sheets (cut into weave/cast/man/{parts,library})
  dummy             arena/cast/dummy/_sheet_*.jpg    Bolas dummy sheets
"""
import glob, hashlib, json, os, re
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..'))
rel = lambda p: os.path.relpath(p, SHOTS)

KITS = json.load(open(os.path.join(SHOTS, 'arena/parts/kit3/v2/kits.json')))
CAST_IDS = [c['id'] for c in KITS['cast']]


def character_of(sid):
    """Sheet id -> (cast id, role/costume hint)."""
    t = sid.split('.')
    head = t[0]
    if head in CAST_IDS:
        return head, None
    if head == 'poet_soul':
        return 'poet', 'soul'
    if head == 'young_ghost':
        return 'ghost_child', None
    if head == 'props' or head == 'vehicle':
        return '-', None
    if head == 'cast' or (head.isdigit() and len(t) > 2 and t[1] == 'cast'):
        who = t[2] if t[1] == 'cast' else t[1]
        if who.startswith('angel'):
            return 'angels', who
        if who.startswith('club') or who.startswith('dj') or who == 'shared':
            return 'party', who
        return 'party', who
    if head.isdigit():
        if t[1] == 'elders':
            return 'family', 'elders'
        if re.search(r'(^|[.-])poet([.-]|$)', sid):
            return 'poet', None  # e.g. 04.props.poet-jointed-hands, 02.props.poet-eye-aperture
        return '-', None  # poem prop/set/fx sheets
    return '-', None


def sheet_type(sid):
    s = sid
    m = re.search(r'\.body\.(front|back|profile|threequarter_back|threequarter)$', s)
    if m:
        return 'body', m.group(1)
    m = re.search(r'\.face\.(front|profile)$', s)
    if m:
        return 'face', m.group(1)
    m = re.search(r'\.replacements(?:\.([a-z_]+))?$', s)
    if m:
        return 'replacements', m.group(1)
    for k, pat in (('hands', r'\.hands(-completion)?$'), ('heads', r'\.heads$'), ('feet', r'\.feet$'), ('hipcore', r'\.hipcore$'),
                   ('core', r'(compact-core|\.core|torso-variants)$'), ('mixed', r'(heads-hands|faces-hands|face-feet(\.\w+)?|features-hands|\.faces|noses|cap-noses-headphones|crowd-head-variants|\.heads|action-hands|wings)$'),
                   ('rolebody', r'\.body$'), ('poses', r'(main-?poses|action|parts(\.\d+)?|poses|instances|choreography|orbits|restage|prayer|walk|argument|identities\.\d+|gifts-gate|plaza-twelve|source-actions|head-turns|memory-drop|dissolve-state\d+|crouch-parts|lean-parts|master|window-action)$')):
        if re.search(pat, s):
            return k, None
    return 'other', None


def layout_fill(img, box):
    """Painted vs empty: an empty kit layout is paper + pale ghost cells + thin crosses."""
    a = np.asarray(img.convert('RGB').crop(box).resize((512, 288)), dtype=np.int16)
    sat = a.max(2) - a.min(2)
    lum = a.mean(2)
    return round(float(((lum < 110) | (sat > 70)).mean()), 4)


def sha1(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()


def inventory():
    S = []
    k3 = os.path.join(SHOTS, 'arena/parts/kit3/v2')
    cutdirs = {os.path.basename(d) for d in glob.glob(os.path.join(k3, 'cut', '*')) if os.path.isdir(d)}
    for p in sorted(glob.glob(os.path.join(k3, 'templates', '*.png'))):
        sid = os.path.basename(p)[:-4]
        S.append(dict(id='tpl:' + sid, file=rel(p), group='kit3_v2_template', painted=False, state='empty_layout', build=sid.split('.')[0],
                      sheet=sid.split('.', 1)[1], holds_parts=sid.split('.', 1)[1] != 'cutchart'))
    for p in sorted(glob.glob(os.path.join(k3, 'packs', '*.jpg'))):
        sid = os.path.basename(p)[:-4]
        im = Image.open(p)
        fill = layout_fill(im, (0, 0, int(im.width * 2048 / 2688), int(im.height * 1152 / 1560)))
        ch, hint = character_of(sid)
        composited = sid.startswith('poem.')  # generate_v2_kits.py filled these with code-drawn props / footage plates
        S.append(dict(id='pack:' + sid, file=rel(p), group='kit3_v2_pack', painted=False, panelA_ink=fill,
                      state='composited' if composited else ('painted' if fill > 0.06 else 'empty_layout'), character=ch,
                      kind=sheet_type(sid), holds_parts=not sid.endswith('.sets')))
    for p in sorted(glob.glob(os.path.join(k3, 'rendered', '*.png'))):
        sid = os.path.basename(p)[:-4]
        ch, hint = character_of(sid)
        S.append(dict(id='v2:' + sid, file=rel(p), group='kit3_v2_render', painted=True, state='painted', character=ch, role=hint,
                      kind=sheet_type(sid), holds_parts=True, previously_cut=('arena/parts/kit3/v2/cut/' + sid) if sid in cutdirs else None))
    # poem kits, unique by content
    byhash = {}
    for p in sorted(glob.glob(os.path.join(SHOTS, 'kits/packs/poem_*/0*_*/*.png'))):
        h = sha1(p)
        sid = os.path.basename(p)[:-4]
        poem = re.search(r'poem_(\d\d)', p).group(1)
        sub = p.split('/')[-2]
        e = byhash.setdefault(h, dict(id=sid, file=rel(p), group='poem_kit', painted=True, state='painted', subfolder=sub,
                                      aliases=[], poems=[], sha1=h))
        if sid not in e['aliases']:
            e['aliases'].append(sid)
        if poem not in e['poems']:
            e['poems'].append(poem)
    rel_cuts = os.path.join(SHOTS, 'arena/parts/kit3/release_v2/cuts')
    for e in byhash.values():
        ch, hint = character_of(e['id'])
        e.update(character=ch, role=hint, kind=sheet_type(e['id']),
                 holds_parts=e['subfolder'] in ('01_CHARACTER_CORE', '02_ACTIONS_AND_POSES', '03_PROPS'))
        d = os.path.join(rel_cuts, e['id'])
        e['previously_cut'] = rel(d) if os.path.isdir(d) and os.listdir(d) else None
        S.append(e)
    for p in sorted(glob.glob(os.path.join(SHOTS, 'kits/packs/poet_tracksuit_v1/0[23]_*/*.png'))):
        sid = os.path.basename(p)[:-4]
        S.append(dict(id='tracksuit:' + sid, file=rel(p), group='tracksuit_source', painted=True, state='painted', character='poet',
                      kind=sheet_type(sid), holds_parts=True, previously_cut='kits/packs/poet_tracksuit_v1/01_COMPONENTS (31 parts, by hand)'))
    for p in sorted(glob.glob(os.path.join(SHOTS, 'weave/cast/man/sheets/*.jpg'))):
        sid = os.path.basename(p)[:-4]
        S.append(dict(id='weave_man:' + sid, file=rel(p), group='weave_man', painted=True, state='painted', character='poet',
                      kind=('draft', None) if 'draft' in sid else ('weave', sid), holds_parts=True,
                      previously_cut='weave/cast/man/{parts,library} (cast.json, library_manifest.json)'))
    for p in sorted(glob.glob(os.path.join(SHOTS, 'arena/cast/dummy/_sheet_*'))):
        sid = os.path.basename(p).split('.')[0]
        S.append(dict(id='dummy:' + sid, file=rel(p), group='dummy', painted=True, state='painted', character=sid.replace('_sheet_', ''),
                      kind=('dummy', None), holds_parts=True, previously_cut='arena/cast/dummy/*.png'))
    return S


if __name__ == '__main__':
    S = inventory()
    json.dump({'about': 'Every sheet that holds or was laid out to hold puppet parts. Written by shots/suite/tools/sheets.py.', 'sheets': S},
              open(os.path.join(SHOTS, 'suite/data/sheets.json'), 'w'), indent=1)
    from collections import Counter
    print(Counter((s['group'], s['state'], s.get('holds_parts')) for s in S))
