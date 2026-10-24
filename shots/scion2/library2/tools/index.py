"""index.json records + sheet tiles shared by every part type."""
import json, os, datetime
import numpy as np
from PIL import Image, ImageDraw
import common as C

INDEX = os.path.join(C.LIB2, 'index.json')
# characters whose sheets an agent has looked at card by card (fixes.json); every other character is automatic only
REVIEWED = {'poet', 'ex'}


def _cls(cls):
    return {k: {'value': v[0], 'conf': round(float(v[1]), 2), 'source': v[2]} for k, v in cls.items()}


def part_record(c, part, r, ppc):
    M = r['M']
    return {
        'key': '%s/%s/%s' % (c['character'], part, C.slug(c['id'])),
        'status': 'ok',
        'source_card': c['id'],
        'source_image': os.path.relpath(C.card_path(c), C.LIB2),
        'character': c['character'], 'costume': c.get('costume'),
        'part': part,
        'image': '%s/%s/%s.png' % (c['character'], part, C.slug(c['id'])),
        'canvas': list(C.GRID[part]['canvas']) if part in C.GRID else None,
        'transform': {'matrix_card_to_canonical': [[round(float(x), 6) for x in row] for row in M],
                      'rotation_deg_ccw': round(r['rot'], 2), 'scale': round(float(r['scale']), 5),
                      'canonical_px_per_cm': ppc, 'card_px_per_cm_est': round(float(r['scale']) and ppc / float(r['scale']), 3),
                      'library_px_per_cm': c.get('px_per_cm'), 'scale_source': r.get('ssrc')},
        'keypoints': {'canonical': r['kc'], 'card': {k: [round(float(v[0]), 1), round(float(v[1]), 1)] for k, v in r['kp'].items() if v is not None}},
        'pivot_source': r['psrc'],
        'classes': _cls(r['cls']),
        'pixel_tests': r.get('px'),
        'flags': sorted(set(r['flags'] + ([] if c['character'] in REVIEWED else ['auto_only']))),
        'removed_components': r.get('removed', []),
    }


def reject_record(c, part, why, refile=None):
    return {'key': '%s/%s/%s' % (c['character'], part, C.slug(c['id'])), 'status': 'rejected', 'source_card': c['id'],
            'character': c['character'], 'part': part, 'reason': why, 'refile_as': refile}


def tile(rgba, part, kps, bones, lines, dirs=()):
    return C.draw_tile(rgba, part, kps, bones, lines, dirs=dirs)


def reject_tile(rgba, c, why, tile=256):
    bg = Image.new('RGBA', rgba.shape[1::-1], (246, 244, 238, 255))
    bg.alpha_composite(Image.fromarray(rgba))
    s = (tile - 8) / max(bg.size)
    im = bg.convert('RGB').resize((max(1, round(bg.width * s)), max(1, round(bg.height * s))), Image.LANCZOS)
    T = Image.new('RGB', (tile, tile + 81), (255, 236, 236))
    T.paste(im, ((tile - im.width) // 2, 4))
    d = ImageDraw.Draw(T)
    f = C.font(11)
    d.text((4, tile + 3), c['id'][-44:], fill=(40, 40, 140), font=f)
    words, line, out = why.split(), '', []
    for w in words:
        if len(line) + len(w) > 42:
            out.append(line); line = ''
        line += w + ' '
    out.append(line)
    for i, l in enumerate(out[:4]):
        d.text((4, tile + 18 + 15 * i), l, fill=(150, 0, 0), font=f)
    return T


def merge(recs, ch, part):
    idx = C.load_json(INDEX) if os.path.exists(INDEX) else {'about': 'library2 regularized parts; see README.md', 'parts': {}}
    idx['parts'] = {k: v for k, v in idx['parts'].items() if not (v['character'] == ch and v['part'] == part)}
    for r in recs:
        idx['parts'][r['key']] = r
    idx['updated'] = datetime.date.today().isoformat()
    idx['grid'] = C.GRID
    idx['canonical_px_per_cm'] = C.CANON_PPC
    with open(INDEX, 'w') as f:
        json.dump(idx, f, indent=1)
