"""Re-gate every slot of a character and list the identity cases on a sheet:
- every card whose library2 part differs from the library's filing (re-filed by fixes.json or labels.json);
- every part whose identity gate warns or fails, with the votes (name / CLIP / raw card length / torso structure)
  and the evidence numbers.

    python3 shots/scion2/library2/qa/identity_sheet.py poet   # -> qa/identity_<char>.json, qa/sheets/<char>_identity_NN.jpg
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))
sys.path.insert(0, HERE)
import common as C  # noqa: E402
import gates  # noqa: E402

COL = {'pass': (60, 60, 60), 'warn': (220, 140, 0), 'fail': (200, 0, 0), 'refiled': (0, 90, 200), 'rejected': (150, 0, 150)}


def main(ch):
    idx = C.load_json(os.path.join(C.LIB2, 'index.json'))['parts']
    slot = {c['id']: c['slot'] for c in C.cards()}
    rows = []
    for k, rec in sorted(idx.items()):
        if rec['character'] != ch or 'composed' in rec.get('flags', []):
            continue
        filed = slot.get(rec['source_card'])
        if rec['status'] != 'ok':
            if rec.get('refile_as') or (filed and filed != rec['part']):
                rows.append(dict(key=k, card=rec['source_card'], filed=filed, part=rec['part'], kind='rejected', why=rec.get('reason', ''), img=None))
            continue
        g = gates.gate(rec)
        idn = g['identity'] if g else None
        refiled = filed and filed != rec['part']
        if refiled or (idn and idn['result'] != 'pass') or (g and g['verdict'] == 'fail'):
            why = []
            if refiled:
                why.append('re-filed %s -> %s' % (filed, rec['part']))
            if idn and idn['result'] != 'pass':
                why.append('identity %s: %s' % (idn['result'].upper(), idn['why']))
            if g and g['verdict'] == 'fail':
                why.append('gates FAIL: ' + '; '.join('%s: %s' % (t, g[t]['why']) for t in ('cutoff', 'contamination', 'connection', 'view') if g[t]['result'] == 'fail'))
            ev = idn['evidence'] if idn else {}
            rows.append(dict(key=k, card=rec['source_card'], filed=filed, part=rec['part'],
                             kind='fail' if (g and g['verdict'] == 'fail') or (idn and idn['result'] == 'fail') else 'warn' if idn and idn['result'] == 'warn' else 'refiled',
                             why=' | '.join(why), img=rec['image'], votes=ev.get('votes'), raw_length_cm=ev.get('raw_length_cm'),
                             clip_top=max(ev['clip'], key=ev['clip'].get) if ev.get('clip') else None, refile_as=ev.get('refile_as')))
    with open(os.path.join(HERE, 'identity_%s.json' % ch), 'w') as f:
        json.dump(rows, f, indent=1)
    T = 150
    tiles = []
    for r in rows:
        im = Image.new('RGB', (T * 5, T), (255, 255, 255))
        if r['img']:
            p = Image.open(os.path.join(C.LIB2, r['img'])).convert('RGBA')
            p.thumbnail((T - 6, T - 6))
            bg = Image.new('RGBA', p.size, (240, 238, 230, 255)); bg.alpha_composite(p)
            im.paste(bg.convert('RGB'), (3, 3))
        else:
            c = next((c for c in C.cards() if c['id'] == r['card']), None)
            if c:
                p = Image.fromarray(C.load_rgba(c)); p.thumbnail((T - 6, T - 6))
                bg = Image.new('RGBA', p.size, (240, 238, 230, 255)); bg.alpha_composite(p)
                im.paste(bg.convert('RGB'), (3, 3))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, T * 5 - 1, T - 1], outline=COL[r['kind']], width=3)
        d.text((T + 4, 6), r['card'][-60:], fill=(0, 0, 0), font=C.font(12))
        d.text((T + 4, 24), 'filed %s  ->  library2 %s   [%s]' % (r['filed'], r['part'], r['kind'].upper()), fill=COL[r['kind']], font=C.font(12))
        txt = r['why']
        lines = [txt[i:i + 95] for i in range(0, len(txt), 95)][:6]
        for i, l in enumerate(lines):
            d.text((T + 4, 44 + 15 * i), l, fill=(40, 40, 40), font=C.font(11))
        tiles.append(im)
    paths = C.sheet(tiles, os.path.join(HERE, 'sheets', '%s_identity_%%02d.jpg' % ch), cols=2,
                    title='%s identity: re-filed cards and identity warn/fail (blue re-filed, amber warn, red fail, purple rejected)' % ch)
    from collections import Counter
    print(Counter(r['kind'] for r in rows))
    print('\n'.join(paths))


if __name__ == '__main__':
    main(sys.argv[1])
