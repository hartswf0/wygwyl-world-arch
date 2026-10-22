"""Scale model for the cut-out stage: one pinhole camera per scene, a floor plane, real heights.

    python3 shots/stage/scale.py          # (re)measure the footage planes and write shots/stage/scale.json

The stage is 1600x900. A scene's staging text gives the SHOT SIZE and the CAMERA HEIGHT; from them:

  ppc       pixels per centimetre at the subject's depth = 900 / visible_cm (how many cm of the subject's
            world the frame height covers there: extreme wide 1400 cm ... close-up 95 cm)
  foot_y    where the subject's feet meet the floor (wide shots: low in frame; medium/close: below frame,
            the head is placed instead and the feet fall out of shot)
  horizon   eye level: horizon_y = foot_y - cam_cm * ppc  (a camera 160 cm up puts the horizon through a
            standing man's chest/eyes; a floor-level camera drops it to his ankles; a high camera lifts it)

Anything standing on the floor k times farther than the subject (k > 1 farther, k < 1 nearer) is drawn at
  ppc_k = ppc / k,   foot_y_k = horizon + (foot_y - horizon) / k
so farther things are smaller and higher, all converging on the horizon. A body of real height h_cm is
h_cm * ppc_k pixels tall (adult man 180, woman 165, child of 6 ~115, child of 7 ~122); a prop is its
dossier scale_cm (longest side) * ppc_k; a set piece takes a height from PIECE_CM by what it is.

Set bands register to the same lines: sky [0, horizon], back strips sit ON the horizon, water hangs from it,
the floor runs from the horizon (or an interior's wall base) to the bottom edge, front strips bleed off the
bottom. Footage depth planes are registered by their own measured horizon (scale.json) so their sky and
distance plates line up with the cardboard.
"""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1600, 900

# shot size -> visible cm of the subject's world (frame height at the subject), where the subject sits, camera
SHOTS = {
    'ELS':    {'name': 'extreme wide', 'vis': 1500, 'foot': .84, 'cam': 520, 'x': 760},
    'WS':     {'name': 'wide',         'vis': 430,  'foot': .86, 'cam': 165, 'x': 720},
    'MWS':    {'name': 'medium wide',  'vis': 240,  'foot': .95, 'cam': 160, 'x': 700},
    'MS':     {'name': 'medium',       'vis': 140,  'head': .10, 'cam': 155, 'x': 690},
    'CU':     {'name': 'close-up',     'vis': 95,   'head': .07, 'cam': 160, 'x': 760},
    'INSERT': {'name': 'insert',       'vis': 120,  'foot': .80, 'cam': 140, 'x': 800},
    'TOP':    {'name': 'top-down',     'vis': 520,  'foot': .70, 'cam': 2000, 'x': 760},
    'POV':    {'name': 'POV',          'vis': 380,  'foot': .86, 'cam': 165, 'x': 820},
}
# first-match patterns, tried clause by clause; later shot types in the same text are kept as alternates
SHOT_RX = [
    ('TOP', r'\b(overhead|top[- ]down|bird\'?s[- ]eye|from above, flat|plan view)\b'),
    ('POV', r'\b(pov|point of view|through his eyes|over[- ]the[- ]shoulder|ots)\b'),
    ('INSERT', r'\b(insert|macro|extreme close|ecu)\b'),
    ('CU', r'\b(close[- ]?up|tight|cu\b|face fills|head and shoulders)'),
    ('MS', r'\b(medium(?! wide)|mid[- ]shot|waist|two[- ]shot|chest)\b'),
    ('MWS', r'\b(medium[- ]wide|full[- ]figure|full[- ]length|knees|cowboy)\b'),
    ('ELS', r'\b(extreme wide|establishing|aerial|vista|panorama|tiny figure|tiny against|very wide|epic wide)\b'),
    ('WS', r'\b(wide|long shot|full shot|lateral track|tracking|track along|profile track|dolly|follow(?:s|ing)? from behind|follows? him|walks? (?:away|toward|into|through))\b'),
]
LOW = r'\b(low[- ]angle|from floor level|worm|from below|ground level|low camera)\b'
HIGH = r'\b(high[- ]angle|from above|crane|looking down|bird)\b'

HEIGHT_CM = {'poet': 180, 'poet_soul': 180, 'ex': 180, 'woman': 165, 'young_poet': 115, 'ghost_child': 122,
             'parents': 178, 'party': 175, 'angels': 186, 'ancestors': 172, 'atlantis': 175, 'family': 174}
YOUNG_POET_CM = {'02': 115, '13': 122}   # six at the pencil notch in 02; 'our younger selves' in 13

# how much of standing height the pose card's height is, by what the pose is doing
POSE_FACTOR = [(r'lying|lie|lies|sprawl|flat on|floating|float', 'lying'), (r'kneel', .74), (r'deep crouch|squat|crouch|search', .64),
               (r'sit|seated|couch|bench|stool', .72), (r'fall', .92), (r'ride|rider|mount|motorbike|bike', .78),
               (r'arms? up|hands up|raise|lighter up|reach up|open arms|chin up', 1.08), (r'jump|leap', 1.05)]

# set pieces by what they are: (height cm, default depth k)
PIECE_CM = [(r'tower|spire|skyscraper|slab tower', 4500, 9), (r'city|skyline|dome|rotunda|observatory', 3000, 10),
            (r'chapel|temple|church|cathedral|forum', 1400, 4.5), (r'building|facade|house|container|stacked|plaza', 900, 3.4),
            (r'mountain|cliff|hill', 8000, 25), (r'tree(?! line)|palm|cypress', 650, 2.4), (r'gate|portal|arch|doorway|surround|wing', 420, 2.0),
            (r'column|pillar|pylon|beacon|lamppost|street ?lamp|lamp post|pole|mast', 420, 1.9),
            (r'door', 215, 1.6), (r'window|glass|pane|mirror|frame|panel|sign|poster|billboard|screen', 160, 1.8),
            (r'truck|van|boat|ship|car\b|taxi', 260, 2.6), (r'motorbike|motorcycle|bike', 115, 1.0), (r'booth|phone ?box|phonebooth|kiosk', 230, 1.6),
            (r'fridge|wardrobe|cabinet|shelf|bookcase', 185, 1.5), (r'sofa|couch|bed|mattress|headboard', 90, 1.35),
            (r'counter|bar\b|desk|table|altar|pew|bench', 95, 1.3), (r'chair|stool|seat', 90, 1.25), (r'lamp|light', 160, 1.4),
            (r'stair|steps', 280, 1.8), (r'fence|rail|railing|wall|kerb|curb', 120, 1.6), (r'stump|rock|stone|boulder|mound|plinth|pedestal', 70, 1.4),
            (r'bush|shrub|flower|weed|grass|reed', 80, 1.2), (r'speaker|amp', 130, 1.5), (r'statue|figure|angel', 260, 2.0), (r'cage|car\b|elevator', 250, 1.8)]
PIECE_DEFAULT = (180, 1.6)

INTERIOR = r'room|bedroom|interior|hall|basement|booth|cafe|club(?!_sidewalk)|party(?!_exterior)|church|pews|shaft|atrium|backroom|living|elevator|teahouse|catwalk|marquee'
VOID = r'^(black|black_void)$|void'


def shot_of(text):
    """(primary shot, [all shots in order], camera height cm) from a staging text. The first shot named wins,
    except that an insert / top-down is only primary when nothing else is named (the stage holds one frame per
    scene, so it shows the scene's master; the inserts stay as alternates)."""
    t = str(text).lower()
    found, where = [], {}
    clauses = re.split(r';|\. |, then |cut to|then cut|\bend:', t)
    for ci, clause in enumerate(clauses):
        hits = sorted((m.start(), k) for k, rx in SHOT_RX for m in [re.search(rx, clause)] if m)
        for _, k in hits:
            if k not in found:
                found.append(k)
                where[k] = clause
    main = [k for k in found if k not in ('INSERT', 'TOP')] or found or ['WS']
    shot = main[0]
    cam = SHOTS[shot]['cam']
    ctx = where.get(shot, clauses[0] if clauses else t)   # the angle words of the clause that names the shot
    if re.search(LOW, ctx):
        cam = 45
    elif re.search(HIGH, ctx) and shot not in ('TOP',):
        cam = max(cam, 420)
    return shot, found or ['WS'], cam


def camera(shot, cam_cm=None, subject_cm=180):
    S = SHOTS[shot]
    ppc = H / S['vis']
    cam_cm = S['cam'] if cam_cm is None else cam_cm
    foot = S['foot'] * H if 'foot' in S else S['head'] * H + subject_cm * ppc
    hor = foot - cam_cm * ppc
    if shot != 'TOP':   # keep a band of world above the eye-line visible: a camera too high for its framing is lowered
        lo, hi = (130, 760) if shot in ('MS', 'CU') else (90, 780)
        if hor < lo:
            cam_cm, hor = (foot - lo) / ppc, lo
        if hor > hi:
            cam_cm, hor = (foot - hi) / ppc, hi
    return {'shot': shot, 'size': S['name'], 'cam_cm': round(cam_cm), 'ppc': round(ppc, 4), 'foot_y': round(foot), 'horizon_y': round(hor),
            'x': S['x'], 'visible_cm': S['vis']}


def at(cam, k):
    """(foot_y, ppc) for a thing standing on the floor k times the subject's distance."""
    return cam['horizon_y'] + (cam['foot_y'] - cam['horizon_y']) / k, cam['ppc'] / k


def depth_for_y(cam, y):
    """Inverse of at(): the depth k whose floor line is at stage y (y must be below the horizon)."""
    return (cam['foot_y'] - cam['horizon_y']) / max(1, y - cam['horizon_y'])


def pose_factor(label, bbox):
    lab = (label or '').lower()
    for rx, f in POSE_FACTOR:
        if re.search(rx, lab):
            return f
    if bbox[2] > bbox[3] * 1.35:
        return 'lying'
    return 1.0


def piece_size(label):
    lab = (label or '').lower()
    for rx, cm, k in PIECE_CM:
        if re.search(rx, lab):
            return cm, k
    return PIECE_DEFAULT


def character_cm(who, poem):
    if who == 'young_poet':
        return YOUNG_POET_CM.get(poem, 118)
    return HEIGHT_CM.get(who, 175)


# ── footage planes: measured once, cached in scale.json ──
def _measure(path):
    from PIL import Image
    im = Image.open(path)
    if im.mode != 'RGBA':
        return {'bbox': [0, 0, 1, 1], 'peak': None, 'opaque': True}
    a = im.getchannel('A').resize((96, 54))
    px = a.load()
    rows = [sum(1 for x in range(96) if px[x, y] > 128) / 96 for y in range(54)]
    cols = [sum(1 for y in range(54) if px[x, y] > 128) / 54 for x in range(96)]
    ys = [y for y, r in enumerate(rows) if r > .02] or [0, 53]
    xs = [x for x, c in enumerate(cols) if c > .02] or [0, 95]
    cover = sum(rows) / 54
    peak = max(range(54), key=lambda y: rows[y])
    return {'bbox': [round(xs[0] / 96, 3), round(ys[0] / 54, 3), round((xs[-1] + 1) / 96, 3), round((ys[-1] + 1) / 54, 3)],
            'peak': round((peak + .5) / 54, 3), 'cover': round(cover, 3), 'wide': round((len(xs)) / 96, 3)}


def measure_planes(assets):
    out = {}
    for sid, S in assets['planes'].items():
        sheets = {}
        for s in S['sheets']:
            p = os.path.join(HERE, s['file'])
            if os.path.exists(p):
                sheets[s['sheet']] = _measure(p) | {'plane': s.get('plane')}
        # the still's horizon: where its distant background (else midground) is widest; else 0.5
        far = [m for m in sheets.values() if m.get('plane') == 'distant background' and m.get('wide', 0) > .45]
        mid = [m for m in sheets.values() if m.get('plane') == 'midground' and m.get('wide', 0) > .45]
        src = far or mid
        hz = sorted(m['peak'] for m in src)[len(src) // 2] if src else .5
        out[sid] = {'horizon': min(.75, max(.3, hz)), 'sheets': sheets}
    return out


def rules():
    return {'stage': [W, H], 'shots': SHOTS, 'shot_patterns': dict(SHOT_RX), 'low_angle': LOW, 'high_angle': HIGH,
            'heights_cm': HEIGHT_CM, 'young_poet_cm': YOUNG_POET_CM, 'pose_factor': [[r, f] for r, f in POSE_FACTOR],
            'pieces_cm_k': [[r, c, k] for r, c, k in PIECE_CM], 'piece_default': PIECE_DEFAULT, 'interior': INTERIOR,
            'formulae': {'ppc': '900 / visible_cm', 'horizon_y': 'foot_y - cam_cm * ppc',
                         'depth k': 'foot_y_k = horizon_y + (foot_y - horizon_y) / k ; ppc_k = ppc / k',
                         'body px': 'height_cm * ppc_k / pose_factor-adjusted', 'prop px': 'scale_cm (longest side) * ppc_k'}}


def load():
    p = os.path.join(HERE, 'scale.json')
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    assets = json.load(open(os.path.join(HERE, 'assets.json')))
    out = {'about': __doc__.strip().split('\n')[0], 'rules': rules(), 'planes': measure_planes(assets)}
    json.dump(out, open(os.path.join(HERE, 'scale.json'), 'w'), indent=1)
    print(len(out['planes']), 'footage stills measured; horizons',
          sorted(round(v['horizon'], 2) for v in out['planes'].values())[::8])


if __name__ == '__main__':
    main()
