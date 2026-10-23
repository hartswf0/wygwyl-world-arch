"""Evolve library-card candidates for one pose.

    python3 -m evolve.evolve kill            (run from shots/scion2)  -> evolve/kill/candidates.json + sheets
    python3 -m evolve.evolve one <char> <costume> <painting id>

Per target: population POP, GENS generations, tournament selection, elitism, crossover that swaps whole limb chains
(arm L, arm R, leg L, leg R, head, torso+pelvis), mutation that swaps one card (half the time for a card of the same
kit family as its chain neighbour) or nudges a part's scale (+-10% of canon at most), rotation trim or mirror.
A child with the same card set as a population member is not admitted (diversity), and every genome ever scored
goes into an archive; the top 6 returned are the best that differ from each other in at least MIN_DIFF slots.
Feet are flipped to point the way the toe marker does and heads to face the way the chin does (not evolved).
"""
import json, math, os, random, sys, time
import numpy as np

from . import library, assemble as AS, cards as C, fitness as FIT

HERE = os.path.dirname(os.path.abspath(__file__))
K_RANGE = {'hand': (.85, 1.3), 'head': (.85, 1.2), 'foot': (.85, 1.25), 'pelvis': (.85, 1.25)}   # uniform scale only
POP, GENS, ELITE, MIN_DIFF, TOP, ISLANDS = 56, 30, 2, 4, 6, 7
KILL = [('poet', 'red_black_sunglasses', 'poet.09.main-poses/falter-at-shoulder-contact'),
        ('poet', 'red_black_sunglasses', 'poet.04.main-poses/04-6-rise-flex-reflect'),
        ('poet', 'red_black_sunglasses', 'poet.13.main-poses/06-refocus'),
        ('ex', 'ex_jacket', 'ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01')]
PROP_HEADS = {'harvest.poet.13.main-poses/05-becoming-arms/head': 'flower crown painted on (a poem prop, not the costume)'}
BLANK_HEADS = {'poet.red_black_sunglasses.heads/front', 'poet.red_black_sunglasses.heads/threequarter',
               'poet.red_black_sunglasses.heads/profile'}   # painted blank (no features); seen on the contact sheet
CONTRACT = os.path.join(library.SKIN, 'contracts/poet.json')


TARGET_PROPS = {'ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01': ('vape',)}
_CUR = {'tid': None}


def tid_props(c):
    """props the current target painting itself holds (a hand holding that prop is allowed)"""
    return TARGET_PROPS.get(_CUR['tid'], ())


def usable(c, k, char):
    """None if the prepared card may enter the pool, else why not (junk for its slot)"""
    if not k.ok:
        return 'unusable: ' + '; '.join(k.why or [])
    i, slot = c['id'].lower(), c['slot']
    if any(w in i for w in ('dissolve', 'haze', 'state0')):
        return 'an effect state (dissolve / haze), not the costume'
    if slot == 'head':
        if c['id'] in PROP_HEADS:
            return PROP_HEADS[c['id']]
        if 'blank' in i or 'plate' in i or c['id'] in BLANK_HEADS or (k.eyes_dark or 0) < .06:
            return 'blank face (no painted features)'
        if k.skin < .15:
            return 'not a head (no skin)'
        if k.lean > 35:
            return 'head painted bent %.0f deg off upright (reads wrong when stood up)' % k.lean
        r = c['h'] / c['w']
        if r < .7 or r > 2.6:
            return 'not a head (shape)'
    elif slot == 'hand':
        if k.skin < .4 or any(w in i for w in ('eyes', 'mouth', 'face', 'celebration-hands', 'partner-grip-hands', 'stand-front')):
            return 'not a hand'
        props = ('daisy', 'flower', 'blossom', 'mic', 'phone', 'letter', 'coin', 'journal', 'knob', 'vape', 'suitcase', 'poppy')
        if any(w in i for w in props) and not any(w in tid_props(c) for w in props if w in i):
            return 'hand holds a prop of another scene'
    else:
        if slot != 'foot' and k.skin > (.3 if slot != 'pelvis' else .5):
            return 'cloth card carries skin (a hand or head on it)'
        if char == 'poet' and k.lab[0] > 45 and slot != 'pelvis':
            return 'unpainted / white card'
        if slot == 'torso' and 'pocket' in i:
            return 'a pocket patch, not a torso'
        if slot == 'pelvis':
            x0, y0, x1, y1 = k.bbox
            if (y1 - y0) > .85 * (x1 - x0) and 'waist-link' not in i:
                return 'not a hip piece (a torso or trouser-leg drawing filed as pelvis)'
        if slot == 'foot' and c['kind'] == 'harvest' and (k.rise or 0) > .6:
            return 'boot carries a cut trouser stub above the ankle'
    return None


def build_pool(char, costume, tid):
    _CUR['tid'] = tid
    P, gone = library.pool(char, costume, tid, AS.all_targets(char).keys())
    lib, pool = {}, {}
    for slot, cs in P.items():
        pool[slot] = []
        for c in cs:
            k = C.prep(c)
            why = usable(c, k, char)
            if why:
                gone.append((c['id'], why))
                continue
            lib[c['id']] = c
            pool[slot].append(c['id'])
    return lib, pool, gone


def allowed_views(t):
    return ['back', 'threequarter_back'] if t['back'] else ['front', 'threequarter', 'side']


def view_w(cv, v):
    return {0.: 1., .15: .35, .3: .5, .8: .04}[FIT.view_cost(cv, v)]


class Evo:
    def __init__(self, char, costume, tid, seed=0):
        self.rng = random.Random(seed)
        self.t = AS.target(char, costume, tid)
        self.lib, self.pool, self.gone = build_pool(char, costume, tid)
        self.ref = FIT.prep_reference(self.t)
        self.views = allowed_views(self.t)
        self.archive = {}
        self.fams = {}
        for slot, ids in self.pool.items():
            for i in ids:
                self.fams.setdefault(self.lib[i]['family'], {}).setdefault(slot, []).append(i)
        self.evals = 0

    # ---------------------------------------------------------- genome pieces
    def pick(self, key, view, fam=None):
        slot = AS.SLOT[key]
        ids = self.pool[slot]
        if fam and self.rng.random() < .6:
            f = [i for i in self.fams.get(fam, {}).get(slot, []) if view_w(self.lib[i]['view'], view) >= .35]
            if f:
                return self.rng.choice(f)
        w = [view_w(self.lib[i]['view'], view) * (1. if self.lib[i]['kind'] == 'kit' else .5) for i in ids]
        return self.rng.choices(ids, w)[0]

    def gene(self, key, cid):
        c = self.lib[cid]
        mir = 0
        if key[-1] in 'LR' and c.get('side') in ('L', 'R') and self.t['back'] is False:
            mir = int(c['side'] != key[-1])
        return {'id': cid, 'k': round(self.rng.uniform(.96, 1.04), 3), 'rot': round(self.rng.uniform(-15, 15), 1) if key.startswith('hand') else 0.,
                'mir': mir}

    def fix_auto(self, G):
        """feet point the way the toe marker does, the head faces the way the chin does"""
        for S in 'LR':
            g = G['parts']['foot' + S]
            g['mir'] = AS.foot_mirror(C.prep(self.lib[g['id']]), self.t, S)
        g = G['parts']['head']
        g['mir'] = AS.head_mirror(None, self.t, self.lib[g['id']])
        return G

    def random_genome(self, fam=None):
        v = self.rng.choice(self.views)
        if fam is not None and self.rng.random() < .75:      # the view the home sheet is drawn in
            ids = sum(self.fams[fam].values(), [])
            v = max(self.views, key=lambda w: np.mean([view_w(self.lib[i]['view'], w) for i in ids]))
        if fam is None:
            fams = [f for f, d in self.fams.items() if not f.startswith('harvest') and len(d) >= 4]
            fam = self.rng.choice(fams) if fams else None
        G = {'view': v, 'parts': {}}
        for key in AS.KEYS:
            G['parts'][key] = self.gene(key, self.pick(key, v, fam))
        return self.fix_auto(G)

    def contract_genome(self):
        if self.t['char'] != 'poet':
            return None
        K = json.load(open(CONTRACT))['limbs']
        cv = {'front': 'front', 'threequarter': 'threequarter', 'side': 'side'}
        out = []
        for v in self.views:
            G = {'view': v, 'parts': {}}
            for key in AS.KEYS:
                ck = key if key in ('torso', 'pelvis', 'head') else AS.SLOT[key] + '_' + key[-1]
                cid = (K.get(ck) or {}).get('cards', {}).get(cv[v])
                if cid not in self.lib:
                    cid = self.pick(key, v)
                G['parts'][key] = self.gene(key, cid)
                G['parts'][key]['k'] = 1.0
                G['parts'][key]['rot'] = 0.
            out.append(self.fix_auto(G))
        return out

    # ---------------------------------------------------------- operators
    def mutate(self, G, home=None):
        G = json.loads(json.dumps(G))
        r = self.rng.random()
        keys = [k for k in AS.KEYS]
        key = self.rng.choice(keys)
        g = G['parts'][key]
        if r < .05:
            G['view'] = self.rng.choice(self.views)
        elif r < .55 or g is None:
            if False:
                pass
            else:
                nb = {'farm': 'uarm', 'uarm': 'farm', 'hand': 'hand', 'shin': 'thigh', 'thigh': 'shin', 'foot': 'foot'}.get(key[:-1])
                fam = home if (home and self.rng.random() < .5) else None
                if nb and fam is None:
                    other = G['parts'].get(nb + (key[-1] if nb != key[:-1] else ('R' if key[-1] == 'L' else 'L')))
                    fam = self.lib[other['id']]['family'] if other else None
                G['parts'][key] = self.gene(key, self.pick(key, G['view'], fam))
        elif r < .8:
            lo, hi = K_RANGE.get(key[:-1] if key[-1] in 'LR' else key, (.9, 1.1))
            g['k'] = round(float(np.clip(g['k'] + self.rng.gauss(0, .04), lo, hi)), 3)
        elif r < .95:
            lim = 30 if key.startswith('hand') else 10
            g['rot'] = round(float(np.clip(g['rot'] + self.rng.gauss(0, 4), -lim, lim)), 1)
        else:
            if key[:-1] in ('uarm', 'farm', 'hand', 'thigh', 'shin'):
                g['mir'] = 1 - g['mir']
        return self.fix_auto(G)

    def cross(self, A, B):
        C_ = json.loads(json.dumps(A))
        for ch, keys in AS.CHAINS.items():
            if self.rng.random() < .5:
                for k in keys:
                    C_['parts'][k] = json.loads(json.dumps(B['parts'][k]))
        if self.rng.random() < .3:
            C_['view'] = B['view']
        return self.fix_auto(C_)

    # ---------------------------------------------------------- evaluation
    @staticmethod
    def sig(G):
        return tuple((G['parts'][k] or {}).get('id') for k in AS.KEYS)

    def key(self, G):
        return json.dumps(G, sort_keys=True)

    def evaluate(self, G):
        kk = self.key(G)
        if kk in self.archive:
            return self.archive[kk][1]
        sc = FIT.score(G, self.t, self.lib, prep_ref=self.ref)
        self.evals += 1
        self.archive[kk] = (G, sc)
        return sc

    def island_families(self, n):
        """home kit families for the islands: the sheets that can dress most of the body in a fitting view"""
        sc = []
        for f, d in self.fams.items():
            if f.startswith('harvest'):
                continue
            cover = sum(1 for slot in ('torso', 'upper_arm', 'forearm', 'thigh', 'shin', 'hand', 'foot', 'head') if d.get(slot))
            ids = sum(d.values(), [])
            fit = max(np.mean([view_w(self.lib[i]['view'], v) for i in ids]) for v in self.views)
            core = '.body.' in f          # the character's own body sheets (front / 3-4 / profile / back) come first
            sc.append((core and fit > .5, cover * fit, f))
        sc.sort(reverse=True)
        return [f for c, w, f in sc if w >= 2][:n]

    def run(self, pop=POP, gens=GENS, log=None, islands=ISLANDS):
        """island model: each island starts from (and mutates toward) its own home kit family; no migration, so the
        islands stay distinct card sets; the poet contract assembly seeds island 0"""
        homes = self.island_families(islands - 1)
        homes = homes + [None] * (islands - len(homes))     # the last island(s): no home family
        per = max(6, pop // islands)
        isl = []
        for i, h in enumerate(homes):
            P = []
            if i == 0:
                P += self.contract_genome() or []
            while len(P) < per:
                P.append(self.random_genome(fam=h))
            isl.append(P[:per])
        hist = []
        for gen in range(gens):
            bests, meds = [], []
            for i, P in enumerate(isl):
                scored = sorted(((self.evaluate(G)['total'], j, G) for j, G in enumerate(P)), key=lambda x: x[0])
                bests.append(scored[0][0]); meds += [x[0] for x in scored]
                nxt = [G for _, _, G in scored[:ELITE]]
                sigs = {self.sig(G) for G in nxt}

                def tour():
                    a = self.rng.sample(scored, min(3, len(scored)))
                    return min(a, key=lambda x: x[0])[2]
                tries = 0
                while len(nxt) < per and tries < per * 30:
                    tries += 1
                    ch = self.cross(tour(), tour()) if self.rng.random() < .6 else tour()
                    for _ in range(self.rng.choice([1, 1, 2, 3])):
                        ch = self.mutate(ch, homes[i])
                    s_ = self.sig(ch)
                    if s_ in sigs and self.rng.random() < .8:
                        continue
                    sigs.add(s_)
                    nxt.append(ch)
                isl[i] = nxt
            hist.append([round(min(bests), 3), round(float(np.median(meds)), 3)])
            if log:
                log('gen %d best %.3f median %.3f evals %d island bests %s' % (gen, hist[-1][0], hist[-1][1], self.evals,
                                                                              ' '.join('%.2f' % b_ for b_ in bests)))
        self.islands = [(homes[i], P) for i, P in enumerate(isl)]
        for P in isl:
            for G in P:
                self.evaluate(G)
        return hist

    def polish(self, G, rounds=2):
        """coordinate descent on the continuous genes of one candidate (scale, trim) for the final six"""
        best, bs = G, self.evaluate(G)['total']
        for _ in range(rounds):
            for key in AS.KEYS:
                if not best['parts'][key]:
                    continue
                klo, khi = K_RANGE.get(key[:-1] if key[-1] in 'LR' else key, (.9, 1.1))
                for field, steps, lo, hi in (('k', (-.04, .04), klo, khi), ('rot', (-6, 6), -30, 30)):
                    for d in steps:
                        H = json.loads(json.dumps(best))
                        v = H['parts'][key][field] + d
                        if field == 'rot' and not key.startswith(('hand', 'head', 'foot')):
                            v = float(np.clip(v, -10, 10))
                        H['parts'][key][field] = round(float(np.clip(v, lo, hi)), 3)
                        s = self.evaluate(H)['total']
                        if s < bs - 1e-4:
                            best, bs = H, s
        return best

    @staticmethod
    def groups(G):
        """the card set by slot group, left/right ignored: swapping the L and R card of a pair is not a new candidate"""
        g = lambda k: (G['parts'][k] or {}).get('id')
        return [frozenset([g(a), g(b)]) if b else g(a) for a, b in
                (('torso', None), ('pelvis', None), ('head', None), ('uarmL', 'uarmR'), ('farmL', 'farmR'),
                 ('handL', 'handR'), ('thighL', 'thighR'), ('shinL', 'shinR'), ('footL', 'footR'))]

    def distinct(self, G, H):
        return sum(a != b for a, b in zip(self.groups(G), self.groups(H)))

    def top(self, n=TOP):
        """the best of each island first, then the archive; every pick differs from every other in >= MIN_DIFF of
        the 9 slot groups (torso, hips, head and the six L/R pairs)"""
        out = []
        firsts = []
        for home, P in getattr(self, 'islands', []):
            b = min(P, key=lambda G: self.evaluate(G)['total'])
            firsts.append((b, self.evaluate(b)))
        items = sorted(firsts, key=lambda x: x[1]['total']) + sorted(self.archive.values(), key=lambda x: x[1]['total'])
        nvalid = sum(1 for _, sc in self.archive.values() if sc['valid'])
        self.n_valid = nvalid
        for G, sc in items:
            if not sc['valid'] and nvalid >= n:
                continue
            if all(self.distinct(G, H) >= MIN_DIFF for H, _ in out):
                out.append((G, sc))
            if len(out) == n:
                break
        return sorted(out, key=lambda x: x[1]['total'])


def run_target(spec, outdir, seed=0):
    char, costume, tid = spec
    t0 = time.time()
    logf = open(os.path.join(outdir, 'log_%s.txt' % tid.replace('/', '__')), 'w')
    log = lambda s: (logf.write(s + '\n'), logf.flush())
    E = Evo(char, costume, tid, seed)
    log('pool: ' + json.dumps({k: len(v) for k, v in E.pool.items()}) + ' excluded %d' % len(E.gone))
    hist = E.run(log=log)
    tops = []
    for G, sc in E.top():
        G2 = E.polish(G)
        tops.append((G2, E.evaluate(G2)))
    # re-pick distinct after polish
    tops.sort(key=lambda x: x[1]['total'])
    res = {'target': tid, 'char': char, 'costume': costume, 's_px_per_card_cm': E.t['s'], 'painting_scale_prior': E.t['scale_prior'],
           'facing': E.t['facing'], 'views_tried': E.views, 'valid_genomes': E.n_valid, 'scored_genomes': len(E.archive),
           'ref_brads': E.t['ref_brads'].tolist(), 'brad_joints': {k: v.tolist() for k, v in E.t['brad_joints'].items()}, 'pool_sizes': {k: len(v) for k, v in E.pool.items()},
           'excluded': [{'id': i, 'why': w} for i, w in E.gone], 'history_best_median': hist, 'evals': E.evals,
           'seconds': round(time.time() - t0, 1),
           'candidates': [{'rank': r + 1, 'genome': G, 'scores': sc,
                           'cards': {k: (G['parts'][k] or {}).get('id') for k in AS.KEYS},
                           'families': sorted({E.lib[g['id']]['family'] for g in G['parts'].values() if g})}
                          for r, (G, sc) in enumerate(tops)]}
    log('done %.1fs' % (time.time() - t0))
    return res


def _job(a):
    spec, outdir, seed = a
    return run_target(spec, outdir, seed)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'kill'
    outdir = os.path.join(HERE, 'kill')
    os.makedirs(outdir, exist_ok=True)
    specs = KILL if mode == 'kill' else [tuple(sys.argv[2:5])]
    from multiprocessing import Pool
    with Pool(min(2, len(specs))) as pool:
        res = pool.map(_job, [(s, outdir, 1 + i) for i, s in enumerate(specs)])
    path = os.path.join(outdir, 'candidates.json')
    old = json.load(open(path)) if os.path.exists(path) and mode != 'kill' else {}
    for r in res:
        old[r['target']] = r
    json.dump(old, open(path, 'w'), indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))
    from . import sheet
    for r in res:
        print(sheet.make(r, outdir))


if __name__ == '__main__':
    main()
