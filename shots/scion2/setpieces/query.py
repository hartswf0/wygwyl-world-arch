#!/usr/bin/env python3
"""Query the merged set-piece registry (shots/scion2/setpieces/registry.json).

Library:
    import sys; sys.path.insert(0, 'shots/scion2/setpieces'); import query
    query.find(category='furniture-seat', affordance='seat', poem='09')        # best first
    query.find(text='mug', usable_only=True, min_grade='A')
    query.get('13.props.cafe/7-espresso-cup-table'); print(query.explain(pid))
    query.scale_px(rec, px_per_cm=4.0)   # factor to resize the part's webp so it renders at size_cm

find() arguments (all optional, all ANDed):
    category     str or list   one of the categories in registry.json summary.all_by_category
    poem         str/int       '09' or 9; matches the sheet's poems list
    affordance   str or list   seat|surface|grip|aperture|lean|occluder|stand_on (part must carry one)
    min_aff_conf float         minimum confidence for that affordance (default 0.0)
    plane        str or list   far_backdrop|mid_set|ground_plane|near_set|foreground_occluder|overlay_fx
    contact      str or list   stands|rests|lies_flat|inset|hangs|floats|full-frame|overlay|worn|attached
    min_grade    'A'|'B'|'C'   default 'B' (A and B)
    usable_only  bool          default True
    include_dups bool          default False: hide parts whose duplicate_of is set (keep the best copy)
    scene        str           substring of a staged location name (e.g. 'bedroom'), or a sheet id
    sheet        str           substring of the sheet id
    text         str           every word must appear in id/label/name
    exclude_flags list         drop parts carrying any of these flags (e.g. ['size_doubt','label_doubt'])
    need_size    bool          only parts with size_cm
    size_cm      (lo, hi)      longest side in cm within range
    limit        int
Ordering: registry rank (grade, best copy, semantics confidence, fewer flags, has size), then affordance
confidence when an affordance is asked for. Rank is a heuristic (inferred), not a probability.

CLI:
    python3 query.py find --category furniture-seat --affordance seat --poem 09 [--plane near_set] [--min-grade A]
                          [--text chair] [--scene bedroom] [--all] [--dups] [--exclude-flags size_doubt,label_doubt]
                          [--limit 20] [--json]
    python3 query.py show <part id>          # full record with provenance
    python3 query.py why <part id>           # one-paragraph explanation of every decision
    python3 query.py stats                   # counts
"""
import json, os, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
_REG = None
GRADE = {'A': 3, 'B': 2, 'C': 1}


def load(path=None):
    global _REG
    if _REG is None or path:
        _REG = json.load(open(path or os.path.join(HERE, 'registry.json')))
    return _REG


def _as_set(v):
    if v is None:
        return None
    return {v} if isinstance(v, str) else set(v)


def _poem(v):
    v = str(v).strip()
    return v.zfill(2) if v.isdigit() else v


def find(category=None, poem=None, affordance=None, plane=None, min_grade='B', usable_only=True,
         include_dups=False, scene=None, sheet=None, text=None, contact=None, exclude_flags=None,
         need_size=False, size_cm=None, min_aff_conf=0.0, limit=None):
    R = load()['parts']
    cats, planes, affs, contacts = _as_set(category), _as_set(plane), _as_set(affordance), _as_set(contact)
    words = [w.lower() for w in (text or '').split()]
    exf = set(exclude_flags or [])
    out = []
    for r in R.values():
        if usable_only and not r['usable']:
            continue
        if GRADE.get(r['grade'], 0) < GRADE[min_grade]:
            continue
        if not include_dups and r.get('duplicate_of'):
            continue
        if cats and r['category'] not in cats:
            continue
        if planes and r['plane'] not in planes:
            continue
        if contacts and (r.get('contact') or {}).get('type') not in contacts:
            continue
        if poem is not None and _poem(poem) not in r['poems']:
            continue
        if sheet and sheet not in r['sheet']:
            continue
        if scene and not (any(scene in s for s in r['scene']) or scene in r['sheet']):
            continue
        if words:
            hay = ' '.join([r['id'], r.get('label') or '', r.get('name') or '']).lower()
            if not all(w in hay for w in words):
                continue
        if exf & set(r['flags']):
            continue
        sz = r.get('size_cm')
        if need_size and not sz:
            continue
        if size_cm:
            if not sz:
                continue
            m = max(sz.get('h') or 0, sz.get('w') or 0)
            if not (size_cm[0] <= m <= size_cm[1]):
                continue
        aconf = 0.0
        if affs:
            hits = [a for a in r['affordances'] if a['kind'] in affs and a['confidence'] >= min_aff_conf]
            if not hits:
                continue
            aconf = max(a['confidence'] for a in hits)
        out.append((r['rank'] + aconf, r))
    out.sort(key=lambda t: -t[0])
    res = [r for _, r in out]
    return res[:limit] if limit else res


def get(pid):
    return load()['parts'].get(pid)


def path(rec):
    """Absolute path of the part's cut-out webp."""
    return os.path.join(ROOT, rec['file'])


def scale_px(rec, px_per_cm):
    """Resize factor for the part's webp so its longest side renders at size_cm * px_per_cm. None if no size."""
    sz, px = rec.get('size_cm'), rec.get('px')
    if not sz or not px:
        return None
    if (sz.get('h') or 0) >= (sz.get('w') or 0):
        return sz['h'] * px_per_cm / px[1]
    return sz['w'] * px_per_cm / px[0]


def explain(pid):
    r = get(pid)
    if not r:
        return f'{pid}: not in registry'
    p = r['provenance']
    rules = load()['rules']
    lines = [f"{pid}  [{r['grade']}] {'USABLE' if r['usable'] else 'UNUSABLE'}  {r['category']} / {r['plane']}",
             f"  file: {r['file']}   label: {r['label']!r}   name: {r['name']!r} ({p['name']['src']})",
             f"  category by {p['category']['by']}: label_class={p['category']['evidence']['label_class']} "
             f"clip={p['category']['evidence']['clip_class']} knn={p['category']['evidence']['knn']} conf={p['category']['evidence']['confidence']}",
             f"  grade by hygiene: defects={[d['kind'] + ':' + str(d.get('severity')) for d in r['defects']]}",
             f"  plane by {p['plane']['by']} (space said {p['plane']['space_plane']}); contact={r['contact']}; view={r['view']} ({r['view_conf']})",
             f"  size_cm={r['size_cm']} via {r['scale_src']}; doubt={p['size_cm']['doubt']}",
             f"  affordances={[(a['kind'], a['confidence']) for a in r['affordances']]} dropped={[(a['kind']) for a in r['affordances_dropped']]}",
             f"  flags={r['flags']}  duplicate_of={r['duplicate_of']}"]
    for w in r['unusable_reasons']:
        lines.append(f"  UNUSABLE {w['rule']} ({w['by']}): {w['reason']}")
    for m in r['merge_rules']:
        lines.append(f"  rule {m}: {rules.get(m, '')[:160]}")
    return '\n'.join(lines)


def _row(r):
    sz = r.get('size_cm')
    s = f"{max(sz.get('h') or 0, sz.get('w') or 0):.0f}cm" if sz else '?'
    a = ','.join(f"{x['kind']}{x['confidence']:.2f}" for x in r['affordances'])
    return f"{r['grade']} {r['category'][:16]:16} {str(r['plane'])[:13]:13} {s:>7} {a:24} {r['id']}  | {(r['name'] or '')[:40]}" + \
           (f"  !{','.join(r['flags'])}" if r['flags'] else '')


def main(argv=None):
    ap = argparse.ArgumentParser(description='Query the WYGWYL set-piece registry')
    sub = ap.add_subparsers(dest='cmd', required=True)
    f = sub.add_parser('find')
    for k in ('category', 'poem', 'affordance', 'plane', 'contact', 'scene', 'sheet', 'text'):
        f.add_argument('--' + k)
    f.add_argument('--min-grade', default='B', choices=['A', 'B', 'C'])
    f.add_argument('--min-aff-conf', type=float, default=0.0)
    f.add_argument('--all', action='store_true', help='include unusable parts')
    f.add_argument('--dups', action='store_true', help='include non-best duplicate copies')
    f.add_argument('--exclude-flags', default='')
    f.add_argument('--need-size', action='store_true')
    f.add_argument('--limit', type=int, default=30)
    f.add_argument('--json', action='store_true')
    s = sub.add_parser('show'); s.add_argument('id')
    w = sub.add_parser('why'); w.add_argument('id')
    sub.add_parser('stats')
    a = ap.parse_args(argv)
    if a.cmd == 'find':
        split = lambda v: v.split(',') if v and ',' in v else v
        res = find(category=split(a.category), poem=a.poem, affordance=split(a.affordance), plane=split(a.plane),
                   contact=split(a.contact), scene=a.scene, sheet=a.sheet, text=a.text, min_grade=a.min_grade,
                   usable_only=not a.all, include_dups=a.dups, min_aff_conf=a.min_aff_conf,
                   exclude_flags=[x for x in a.exclude_flags.split(',') if x], need_size=a.need_size, limit=a.limit)
        if a.json:
            print(json.dumps([{k: r[k] for k in r if k != 'provenance'} for r in res], indent=1))
        else:
            for r in res:
                print(_row(r))
            print(f'-- {len(res)} shown', file=sys.stderr)
    elif a.cmd == 'show':
        print(json.dumps(get(a.id), indent=1))
    elif a.cmd == 'why':
        print(explain(a.id))
    elif a.cmd == 'stats':
        print(json.dumps(load()['summary'], indent=1))


if __name__ == '__main__':
    main()
