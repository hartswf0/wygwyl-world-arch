"""Build every mechanism clip + index.json.

    python3 shots/stage/mech/derive.py   # derived cards (once)
    python3 shots/stage/mech/build.py    # clips/*.json, index.json
    node shots/stage/mech/render.mjs shots/stage/mech/clips/*.json   # frames/*.png (server on :8781)
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Clip, ease, lerp, flick, HERE

OUT = os.path.join(HERE, 'clips')
BUILT = []
TAU = math.tau


def done(C, file, kind):
    d = C.save(os.path.join(OUT, file))
    BUILT.append({'id': d['id'], 'file': 'clips/' + file, 'title': d['title'], 'poems': d['poems'], 'kind': kind, 'loop': d['loop'],
                  'frames': C.n, 'fps': d['clock']['fps'], 'anchors': sorted(C.anchors), 'sfx': sorted(C.sfx), 'parts': sorted(set(C.parts.values())),
                  'notes': C.notes})
    print('built', d['id'], C.n, 'frames')


def tri(p):
    """0..1..0 over p in 0..1"""
    p %= 1
    return 1 - abs(2 * p - 1)


# ════════════════════════════════════════════════════════════════════════════════════════════════
# 02 · THE FAMILY CAR
# ════════════════════════════════════════════════════════════════════════════════════════════════
CAR_W = {'front': (137, 214), 'rear': (612, 214)}
CAR_HEAD = (36, 151)
CAR_HAZ = [(63, 151), (772, 142)]
CAR_CABIN = [(214, 98), (300, 24), (330, 16), (560, 16), (640, 96), (640, 118), (214, 118)]
CAR_WINDOWS = [[(227, 98), (282, 34), (282, 98)], [(282, 26), (392, 26), (392, 100), (282, 100)],
               [(426, 26), (524, 26), (524, 100), (426, 100)], [(537, 34), (565, 34), (600, 98), (537, 98)]]


def beam(C, f, hx, hy, dirx, a, length=440, spread=1.0, color=(255, 238, 190), tilt=8):
    """a light cone as nested screen-blend sectors (round far edge, soft falloff, no gradient needed)"""
    r, g, b = color
    base = 0 if dirx > 0 else 180
    for L, half, al in ((1.0, 15, .05), (.86, 12, .06), (.72, 9.5, .07), (.56, 7, .08), (.40, 5, .10), (.24, 3.5, .12)):
        pts = [(hx, hy - 3), (hx, hy + 3)]
        for i in range(13):
            t = math.radians(base + (tilt * dirx) + (-half + 2 * half * i / 12) * spread)
            pts.append((hx + math.cos(t) * length * L, hy + math.sin(t) * length * L))
        C.poly(f, pts, fill='rgba(%d,%d,%d,%.2f)' % (r, g, b, al), a=a, blend='screen')


def car_images(C):
    C.img('body', '02.props.car/car.webp')
    C.img('body_nodoor', 'stage/mech/parts/car_body_nodoor.webp')
    C.img('door', 'stage/mech/parts/car_door.webp')
    C.img('wheel', '02.props.car/wheel-disc-w-axle-mark.webp')
    C.img('wheel2', '02.props.car/wheel-disc-w-axle-mark-2.webp')
    C.img('headlight', '02.props.car/headlight-left.webp')
    C.img('hazard', '02.props.car/hazard-light-left.webp')
    C.img('hazard_r', '02.props.car/inserts-right-2.webp')
    C.img('dome', '02.props.car/dome-light-insert.webp')
    C.img('glass', '02.props.car/side-window-glass-insert.webp')


def car_draw(C, f, spin=0.0, bob=0.0, lights=1.0, hazard=0.0, dome=0.0, door=0.0, interior=None, cone=True):
    """one frame of the car. spin deg, bob px, lights 0..1, hazard 0..1, dome 0..1, door 0 shut .. 1 open (75°)"""
    if cone and lights > 0:   # the beam lies on the road in front: drawn first, under everything
        hx, hy = CAR_HEAD[0], CAR_HEAD[1] + bob
        beam(C, f, hx, hy, -1, lights)
        C.glow(f, hx - 300, CAR_W['front'][1] + 64, 120, '#ffe9b0', 0.22 * lights)   # pool on the road
    for k, (x, y) in CAR_W.items():
        C.shadow(f, x, y + 63, 70, 0.7)
    # cabin seen through the window holes (clip mask = the cabin outline)
    C.clip(f, [(x, y + bob) for x, y in CAR_CABIN])
    C.poly(f, [(x, y + bob) for x, y in CAR_CABIN], fill='#16110e')
    if dome > 0:
        C.glow(f, 430, 30 + bob, 190, '#ffd98a', 0.75 * dome)
    if interior:
        interior(C, f, bob)
    C.unclip(f)
    if door > 0:   # dark door aperture: the cabin shows where the door was
        C.poly(f, [(213, 97 + bob), (318, 21 + bob), (393, 19 + bob), (394, 219 + bob), (213, 219 + bob), (209, 160 + bob)], fill='#120d0a')
        if dome > 0:
            C.glow(f, 300, 120 + bob, 120, '#ffd98a', 0.4 * dome)
    for i, (k, (x, y)) in enumerate(CAR_W.items()):
        C.card(f, 'wheel' if i == 0 else 'wheel2', x, y, rot=spin + i * 17, s=0.66)
    C.card(f, 'body' if door <= 0 else 'body_nodoor', 0, bob, px=0, py=0)
    # glass inserts: a faint acetate sheen over each window hole
    for w in CAR_WINDOWS[1:3]:
        x0, y0 = w[0]; x1, y1 = w[2]
        C.card(f, 'glass', (x0 + x1) / 2, (y0 + y1) / 2 + bob, sx=(x1 - x0 + 6) / 226, sy=(y1 - y0 + 6) / 112, a=0.18, blend='screen')
    # headlight insert + light
    C.card(f, 'headlight', CAR_HEAD[0] - 2, CAR_HEAD[1] + bob, s=0.24, a=0.55 + 0.45 * lights)
    if lights > 0:
        C.glow(f, CAR_HEAD[0] - 4, CAR_HEAD[1] + bob, 70, '#fff1c8', 0.95 * lights)
        C.glow(f, CAR_HEAD[0] - 4, CAR_HEAD[1] + bob, 22, '#ffffff', 0.9 * lights)
        C.glow(f, 772, 142 + bob, 30, '#ff3b22', 0.55 * lights)      # tail lamp
    # hazards: amber inserts behind the cut holes, front marker and rear lamp
    C.card(f, 'hazard', CAR_HAZ[0][0], CAR_HAZ[0][1] + bob, s=0.17, a=0.35 + 0.65 * hazard)
    if hazard > 0:
        for x, y in CAR_HAZ:
            C.glow(f, x, y + bob, 85, '#ffa21f', 0.95 * hazard)
            C.glow(f, x, y + bob, 18, '#fff0c0', hazard)
    if door > 0:   # the door swings toward camera on its front hinge: seen edge-on it narrows
        ang = 64 * door
        sxx = math.cos(math.radians(ang))
        # door card spans body x 209..395; hinge at x=211
        C.card(f, 'door', 211, 19 + bob, px=2, py=0, sx=sxx, skew=-0.10 * math.sin(math.radians(ang)))
        C.poly(f, [(211, 97 + bob), (211 + 6 * math.sin(math.radians(ang)), 97 + bob), (211 + 6 * math.sin(math.radians(ang)), 219 + bob), (211, 219 + bob)], fill='#5b4630')


def car_clips():
    # 1 · rolling down the road, wheels turning on their brads, lit
    C = Clip('mech.car.drive', 'family car: rolling, wheels on brads, headlights and beam', ['02'], 48, cm_px=1.78, floor_y=277,
             view=(-440, -40, 1270, 360),
             notes='Car stays put; scroll the road under it. Wheels turn 15°/frame on their axle brads; body rides 2 px on the bumps. Beam = two screen-blend polys + a glow pool on the road.')
    car_images(C); C.size_cm(450, 150)
    for f in range(48):
        car_draw(C, f, spin=-f * 15, bob=2.2 * math.sin(f / 48 * TAU * 4) + (3 if 30 <= f < 34 else 0), lights=1)
    C.event(0, 'sfx.car.engine_idle_loop', 'engine running (loop)')
    C.event(30, 'sfx.car.bump', 'cresting the bump')
    C.anchor('driver_head', (330, 62)); C.anchor('passenger_head', (470, 62)); C.anchor('headlight', CAR_HEAD)
    done(C, 'car.drive.json', 'mech')

    # 2 · idling in the driveway: hazards flashing, dome light on
    C = Clip('mech.car.hazards', 'family car: idling, hazards flashing, dome light on', ['02'], 24, cm_px=1.78, floor_y=277,
             view=(-440, -40, 1270, 360), notes='Hazards: amber inserts behind the cut holes + glows, 12 on / 12 off (1 Hz). Dome light lights the cabin through the window holes.')
    car_images(C); C.size_cm(450, 150)
    for f in range(24):
        on = 1.0 if f < 11 else (0.4 if f == 11 else 0.0)
        car_draw(C, f, spin=0, bob=0.6 * math.sin(f / 24 * TAU * 6), lights=1, hazard=on, dome=1)
    C.event(0, 'sfx.car.hazard_tick', 'hazard relay on'); C.event(12, 'sfx.car.hazard_tock', 'hazard relay off')
    C.event(0, 'sfx.car.engine_idle_loop', 'engine idling (loop)')
    C.anchor('driver_head', (330, 62)); C.anchor('passenger_head', (470, 62))
    done(C, 'car.hazards.json', 'mech')

    # 3 · the door swings open, holds, slams
    C = Clip('mech.car.door', 'family car: front door swings open on its hinge, holds, slams', ['02'], 60, loop=False, cm_px=1.78, floor_y=277,
             view=(-440, -40, 1270, 360), notes='Front door is a knife cut from the side card (parts/car_door.webp) on a hinge at its front edge; seen edge-on it narrows (cos) with a slight skew; the aperture shows the dark lit cabin.')
    car_images(C); C.size_cm(450, 150)
    for f in range(60):
        if f < 16: d = ease(f / 16)
        elif f < 40: d = 1
        elif f < 48: d = 1 - ((f - 40) / 8) ** 2
        else: d = 0
        bob = (2.5 * math.sin((f - 48) * 1.6) * math.exp(-(f - 48) / 4)) if f >= 48 else 0
        car_draw(C, f, lights=1, dome=1 if 2 <= f < 50 else 0, door=d, bob=bob)
    C.event(0, 'sfx.car.door_open', 'door unlatches and swings'); C.event(48, 'sfx.car.door_slam', 'door slams')
    C.anchor('door_handle', (360, 128)); C.anchor('door_step', (300, 277))
    C.anchor('door_handle_track', [(211 + (360 - 211) * math.cos(math.radians(64 * (ease(f / 16) if f < 16 else 1 if f < 40 else max(0, 1 - ((f - 40) / 8) ** 2) if f < 48 else 0))), 128) for f in range(60)])
    done(C, 'car.door.json', 'mech')

    # 4 · interior cutaway: the parents seated, seen through the window holes
    C = Clip('mech.car.interior', 'family car cutaway: parents arguing behind the windows (window clip masks)', ['02'], 48, cm_px=1.78, floor_y=277,
             view=(-60, -40, 900, 360),
             notes='Seats and people sit between the cabin backing and the body card, masked by the cabin clip so they only read through the window holes. Seats are anchors (driver_seat, passenger_seat, rear_seat): any seated actor clip can be dropped in. Demo uses parents.02.car-argument profiles (father front, turned back; mother behind, leaning in).')
    car_images(C); C.size_cm(450, 150)
    C.img('seat_f', '02.props.car/front-seat-silhouette.webp'); C.img('seat_r', '02.props.car/rear-seat-silhouette.webp')
    C.img('wheel_s', '02.props.car/steering-wheel-open-centre.webp')
    C.img('father', 'parents.02.car-argument/father-driver-profile.webp'); C.img('mother', 'parents.02.car-argument/part-2.webp')

    def inside(C, f, bob):
        C.card(f, 'seat_r', 520, 120 + bob, s=0.42)
        C.card(f, 'seat_f', 395, 108 + bob, s=0.46, flip=True)
        jab = 3 * max(0, math.sin(f / 48 * TAU * 3))
        C.card(f, 'mother', 520, 112 + bob - jab * 0.5, s=0.5, flip=False, rot=-2 - jab)
        C.card(f, 'father', 352 + jab, 116 + bob, s=0.5, rot=1 + jab * 0.6)
        C.card(f, 'wheel_s', 268, 92 + bob, s=0.36, sx=0.35, rot=-18)
    for f in range(48):
        car_draw(C, f, lights=0.6, dome=0.7, interior=inside, cone=False, bob=0.6 * math.sin(f / 48 * TAU * 8))
    C.event(0, 'sfx.car.engine_idle_loop', 'engine idling (loop)')
    C.anchor('driver_seat', (352, 140)); C.anchor('passenger_seat', (440, 140)); C.anchor('rear_seat', (540, 140))
    done(C, 'car.interior.json', 'mech')


# ════════════════════════════════════════════════════════════════════════════════════════════════
# 10 · THE MOTORCYCLE (ride skeleton; close build with slide-in plates)
# ════════════════════════════════════════════════════════════════════════════════════════════════
BK = '10.props.bike-skeleton/'
BIKE_HEAD = (509, 13)          # steering-head brad on the frame card (frame placed at 0,0)
BIKE_REAR = (56, 244)          # swing-arm axle brad
FORK_ROT = -22                 # rake the fork card so the front axle sits level with the rear
BIKE_VOIDS = [(463, 71, 78, 58, 'p3'), (386, 96, 75, 50, 'p1'), (317, 140, 93, 44, 'p4'), (205, 156, 92, 63, 'p2'), (182, 108, 81, 41, 'p1')]


def fork_axle():
    r = math.radians(FORK_ROT)
    vx, vy = 128 - 53, 298 - 19
    return (BIKE_HEAD[0] + vx * math.cos(r) - vy * math.sin(r), BIKE_HEAD[1] + vx * math.sin(r) + vy * math.cos(r))


def bike_images(C):
    C.img('frame', BK + 'open-triangulated-frame-with-white-voids.webp')
    C.img('fork', BK + '6-fork.webp')
    C.img('tyre', BK + '8-7-front-tyre-ring.webp')
    C.img('disc_f', BK + '8-front-spoked-disc-axle-pivot.webp')
    C.img('disc_r', BK + '10-rear-disc-axle-pivot-2.webp')
    C.img('tank', BK + '11-fuel-tank.webp')
    C.img('lamp', BK + '13.webp')
    C.img('seat', BK + '12-seat.webp')
    C.img('bars', BK + '14.webp')
    C.img('pipe', '11.props.parked-motorcycle/10-exhaust-pipe.webp')
    for k, n in (('p1', '2-steel-plate-p1'), ('p2', '3-steel-plate'), ('p3', '4-steel-plate-p3'), ('p4', '5-steel-plate-p4')):
        C.img(k, BK + n + '.webp')


def glint(C, f, x, y, s, a):
    """the tank glint: a four-point white star card + glow"""
    if a <= 0: return
    pts = []
    for i in range(8):
        r = s if i % 2 == 0 else s * 0.18
        t = i * math.pi / 4
        pts.append((x + r * math.sin(t), y - r * math.cos(t)))
    C.glow(f, x, y, s * 2.2, '#ffffff', 0.7 * a)
    C.poly(f, pts, fill='#ffffff', a=a)


def bike_draw(C, f, spin=0.0, bob=0.0, light=1.0, glint_a=0.0, plates=None, puff=None, rider=None):
    ax = fork_axle()
    if light > 0:
        beam(C, f, 640, 42 + bob, +1, light, length=520, spread=0.9)
    C.shadow(f, (BIKE_REAR[0] + ax[0]) / 2, BIKE_REAR[1] + 124, 420, 0.75)
    # wheels on their brads (behind the frame)
    for (x, y), disc, k in ((BIKE_REAR, 'disc_r', 0), (ax, 'disc_f', 1)):
        C.card(f, 'tyre', x, y, rot=spin + 40 * k, flip=bool(k))
        C.card(f, disc, x, y, rot=spin * 1.0 + 11 * k, s=1.0)
        C.poly(f, [(x - 5, y - 5), (x + 5, y - 5), (x + 5, y + 5), (x - 5, y + 5)], fill='#b08a3a')   # brass axle brad
    C.card(f, 'pipe', 150, 238 + bob, rot=-8, s=0.95, flip=True)
    if puff:
        puff(C, f)
    if plates:
        plates(C, f, bob)
    C.card(f, 'frame', 0, bob, px=0, py=0)
    C.card(f, 'seat', 175, 18 + bob, rot=-3, s=1.0)
    C.card(f, 'tank', 372, 20 + bob, rot=-6, s=0.86)
    if rider:
        rider(C, f, bob)
    # fork rides on the steering head brad, in front of the frame
    C.card(f, 'fork', BIKE_HEAD[0], BIKE_HEAD[1] + bob, px=53, py=19, rot=FORK_ROT)
    C.card(f, 'bars', BIKE_HEAD[0] + 6, BIKE_HEAD[1] - 12 + bob, px=148, py=83, s=0.62, sx=0.7, rot=8)
    C.card(f, 'lamp', 585, 46 + bob, px=59, py=113, s=0.62, rot=0)
    if light > 0:
        C.glow(f, 612, 40 + bob, 90, '#fff1c8', 0.85 * light)
        C.glow(f, 612, 40 + bob, 26, '#ffffff', 0.95 * light)
    glint(C, f, 420, -2 + bob, 16, glint_a)


def moto_clips():
    # 1 · the ride: wheels spin, suspension, lamp beam, exhaust puffs, rider sockets
    N = 48
    C = Clip('mech.motorcycle.ride', 'motorcycle (ride skeleton): wheels spin on brads, fork, beam, exhaust puffs, tank glint', ['10', '11'], N,
             cm_px=4.4, floor_y=369, view=(-260, -170, 1500, 600),
             notes='Bike holds frame centre; stream the world past it. Rear wheel on the swing-arm brad, front wheel on the fork-foot brad, fork on the steering-head brad (raked -22° so both axles sit level). Exhaust puffs are grey tissue discs drifting back; the glint fires twice (double-click) at f30/f34. Anchors: seat, handlebar_L/R, footpeg, tank (rub), headlight; per-frame tracks follow the bob.')
    bike_images(C); C.size_cm(210, 110)

    def puffs(C, f):
        for i in range(4):
            p = ((f + i * 12) % N) / N * 4 % 1
            ph = ((f + i * 12) % 12) / 12
            x = 60 - ph * 220 - i * 6
            y = 270 - ph * 40
            r = 10 + ph * 34
            C.glow(f, x, y, r * 1.8, '#b8b0a4', 0.85 * (1 - ph) ** 0.7, blend='source-over')
    seat, barL, barR, peg = [], [], [], []
    for f in range(N):
        bob = 1.6 * math.sin(f / N * TAU * 6) + 1.0 * math.sin(f / N * TAU * 2)
        ga = 1.0 if f in (30, 31, 34, 35) else (0.5 if f in (29, 32, 33, 36) else 0)
        bike_draw(C, f, spin=f * 15, bob=bob, light=1, glint_a=ga, puff=puffs)
        seat.append((190, 2 + bob)); barL.append((470, -28 + bob)); barR.append((548, -12 + bob)); peg.append((250, 236 + bob))
    C.anchor('seat', seat); C.anchor('handlebar_L', barL); C.anchor('handlebar_R', barR); C.anchor('footpeg', peg)
    C.anchor('tank', (380, 10)); C.anchor('headlight', (612, 40))
    C.event(0, 'sfx.motorcycle.ride_loop', 'engine at speed (loop)')
    C.event(30, 'sfx.glint.ping', 'tank glint'); C.event(34, 'sfx.glint.ping', 'tank glint again (double-click)')
    done(C, 'motorcycle.ride.json', 'mech')

    # 2 · close build: parked under the moon, plates slide into the frame voids as he rubs
    N = 96
    C = Clip('mech.motorcycle.plates', 'motorcycle close build: steel plates slide into the frame as the tank is rubbed', ['10'], N, loop=False,
             cm_px=4.4, floor_y=369, view=(-260, -170, 1500, 600),
             notes='One-shot. Five plate cards slide in behind the triangulated frame, one per 14 frames, from below-left (the rubbing hand side); each lands with a clunk. Engine catches at f84, lamp comes up, glint.')
    bike_images(C); C.size_cm(210, 110)
    order = [3, 2, 4, 1, 0]

    def plates_at(f):
        def P(C, f, bob):
            for n, vi in enumerate(order):
                x, y, w, h, key = BIKE_VOIDS[vi]
                t0 = 6 + n * 14
                p = ease((f - t0) / 10)
                if p <= 0: continue
                W, H = C.wh(key)
                s = max(w / W, h / H) * 1.35
                C.card(f, key, x - 120 * (1 - p), y + 70 * (1 - p) + bob, s=s, rot=-12 * (1 - p), a=min(1, p * 3))
                if 0 <= f - t0 - 10 < 4:
                    C.glow(f, x, y + bob, 70, '#fff6e0', 0.6 * (1 - (f - t0 - 10) / 4))
        return P
    for f in range(N):
        light = ease((f - 84) / 6)
        bike_draw(C, f, spin=0, bob=0, light=light, plates=plates_at(f), glint_a=(1 if 88 <= f <= 90 else 0))
    for n in range(5):
        C.event(6 + n * 14 + 10, 'sfx.metal.plate_clunk', 'plate %d seats' % (n + 1))
    C.event(84, 'sfx.motorcycle.start', 'engine catches'); C.event(88, 'sfx.glint.ping', 'glint')
    C.anchor('tank', (380, 10)); C.anchor('seat', (190, 2)); C.anchor('handlebar_L', (470, -28))
    done(C, 'motorcycle.plates.json', 'mech')


# ════════════════════════════════════════════════════════════════════════════════════════════════
# 04 · THE BEATING HEART (NEVERMORE)
# ════════════════════════════════════════════════════════════════════════════════════════════════
HP = '04.props.heart/'
HEART = {'lub': ('h-lub-normal', (167, 117)), 'dub': ('dub-slightly-squeezed', (148, 108)),
         'dusted': ('dusted-coated-ash-in', (163, 117)), 'clean': ('cleaned', (161, 117))}
BLUE = '#5aa7ff'


def heart_images(C):
    for k, (n, _) in HEART.items():
        C.img(k, HP + n + '.webp')
    C.img('blue', HP + 'blue-point.webp'); C.img('stem', HP + 'acetate-support.webp')
    C.img('ash1', HP + 'vv.webp'); C.img('ash2', HP + 'vv-ash-fleck-overlay.webp'); C.img('ash3', HP + 'overlay.webp')


def beat_phase(f, period=24):
    """(card, pulse 0..1): lub-dub, the second beat softer"""
    p = f % period
    if p in (0, 1, 2): return 'dub', (1.0, 0.85, 0.5)[p]
    if p in (6, 7): return 'dub', (0.55, 0.35)[p - 6]
    if p in (3, 8): return 'lub', 0.25
    return 'lub', 0.0


def heart_draw(C, f, x, y, state='lub', pulse=0.0, dust=0.0, s=1.0, rot=0.0, stem=False, blue_gain=1.0):
    """the heart hung by its punched hole at (x, y)"""
    if stem:   # the clear acetate stem behind the heart, ring on the punched hole, foot showing below
        C.card(f, 'stem', x, y, px=31, py=18, s=2.75 * s, sx=0.5, a=0.6)
    # the blue point lies behind the punched hole
    C.card(f, 'blue', x, y, s=0.32 * s)
    squeezed = state == 'dub'
    base = 'dub' if squeezed else ('lub' if dust < 1 else 'dusted')
    n, (hx, hy) = HEART[base]
    if dust >= 1 and squeezed:
        # the dusted card is single-state: squeeze it a touch instead
        n, (hx, hy) = HEART['dusted']; C.card(f, 'dusted', x, y, px=hx, py=hy, s=s * 0.95, sx=0.97, rot=rot)
    else:
        key = base if base != 'lub' or dust <= 0 else 'clean'
        key = 'dub' if squeezed else ('clean' if dust < 1 else 'dusted')
        _, (hx, hy) = HEART[key]
        C.card(f, key, x, y, px=hx, py=hy, s=s, rot=rot)
        if 0 < dust < 1:   # cross-fade: the dusted card over the clean one
            _, (dx, dy) = HEART['dusted']
            C.card(f, 'dusted', x, y, px=dx, py=dy, s=s * (0.95 if squeezed else 1), rot=rot, a=dust)
    a = (0.45 + 0.55 * pulse) * blue_gain
    C.glow(f, x, y, (26 + 40 * pulse) * s, BLUE, a)
    C.glow(f, x, y, 9 * s, '#d6ecff', min(1, a * 1.2))


def heart_clips():
    # 1 · beat, clean
    C = Clip('mech.heart.beat', 'the heart: lub/dub replacement beat, blue point pulse', ['04'], 24, cm_px=26, view=(-220, -170, 440, 420),
             notes='Replacement cycle hung on the punched hole (the hole never moves): dub card on f0-2 and f6-7 (second beat softer), lub otherwise. The blue point card sits behind the hole; the coded #5aa7ff glow pulses with the beat. 60 bpm at 24 fps.')
    heart_images(C); C.size_cm(12, 14)
    for f in range(24):
        st, pu = beat_phase(f)
        heart_draw(C, f, 0, 0, st, pu)
    C.event(0, 'sfx.heart.lub', 'lub'); C.event(6, 'sfx.heart.dub', 'dub (softer)')
    C.anchor('heart', (0, 0)); C.anchor('blue_point', (0, 0))
    done(C, 'heart.beat.json', 'mech')

    # 2 · dusted: beating under ash in the sand
    C = Clip('mech.heart.dusted', 'the heart dusted in ash, beating in the sand', ['04'], 24, cm_px=26, view=(-220, -170, 440, 420),
             notes='Ash-coated card, squeezed a touch on the beats; the blue point shows dimmer through the grit.')
    heart_images(C); C.size_cm(12, 14)
    for f in range(24):
        st, pu = beat_phase(f)
        heart_draw(C, f, 0, 0, st, pu, dust=1, blue_gain=0.55)
    C.event(0, 'sfx.heart.lub', 'lub (muffled)'); C.event(6, 'sfx.heart.dub', 'dub (muffled)')
    C.anchor('heart', (0, 0))
    done(C, 'heart.dusted.json', 'mech')

    # 3 · dusted → clean: ash flecks fall away, the red comes through
    N = 72
    C = Clip('mech.heart.clean_off', 'the heart wiped clean: ash flecks fall, dusted card dissolves to the cleaned one', ['04'], N, loop=False, cm_px=26,
             view=(-220, -170, 440, 520), notes='One-shot. The dusted card fades off the cleaned card over f12-48 while three ash fleck cards drop and tumble away; the blue point brightens to full.')
    heart_images(C); C.size_cm(12, 14)
    flecks = [('ash1', -60, 40, 0), ('ash2', 30, 90, 6), ('ash3', 70, -10, 12), ('ash1', -20, 130, 18), ('ash3', -90, 100, 24)]
    for f in range(N):
        st, pu = beat_phase(f)
        dust = 1 - ease((f - 12) / 36)
        heart_draw(C, f, 0, 0, st, pu, dust=dust if dust < 1 else 1, blue_gain=0.55 + 0.45 * (1 - dust))
        for k, x0, y0, t0 in flecks:
            p = (f - 10 - t0) / 30
            if p < 0:
                C.card(f, k, x0, y0, s=0.8)
            elif p < 1:
                C.card(f, k, x0 + 20 * p * (1 if x0 > 0 else -1), y0 + 300 * p * p, rot=200 * p * (1 if x0 > 0 else -1), s=0.8, a=1 - p ** 3)
    C.event(10, 'sfx.ash.sift', 'ash sifts off'); C.event(0, 'sfx.heart.lub', 'lub'); C.event(48, 'sfx.heart.clean_chime', 'clean: the blue comes up')
    C.anchor('heart', (0, 0))
    done(C, 'heart.clean_off.json', 'mech')

    # 4 · float on the acetate stem
    N = 48
    C = Clip('mech.heart.float', 'the heart floating on its acetate stem, beating, lit blue', ['04'], N, cm_px=26, view=(-260, -190, 520, 520),
             notes='The clear acetate stem (drawn at 45% alpha) holds the heart by its punched hole; the heart bobs 10 px and sways ±3° while it beats. anchor_track "heart" for a sequence to lead it into the chest (dossier: 33 cells, no overshoot).')
    heart_images(C); C.size_cm(12, 22)
    tr = []
    for f in range(N):
        st, pu = beat_phase(f)
        y = -10 * math.sin(f / N * TAU)
        rot = 3 * math.sin(f / N * TAU * 2)
        heart_draw(C, f, 0, y, st, pu, rot=rot, stem=True)
        tr.append((0, y))
    C.anchor('heart', tr); C.anchor('stem_foot', (0, 230))
    C.event(0, 'sfx.heart.lub', 'lub'); C.event(6, 'sfx.heart.dub', 'dub'); C.event(24, 'sfx.heart.lub', 'lub'); C.event(30, 'sfx.heart.dub', 'dub')
    done(C, 'heart.float.json', 'mech')


# ════════════════════════════════════════════════════════════════════════════════════════════════
# 12 · HOURGLASSES
# ════════════════════════════════════════════════════════════════════════════════════════════════
LH = '12.props.last-hourglass/'
HH = '12.props.hand-hourglass/'
UPPER = ['09-14-lower-09', 'lower-sand-inserts-10', 'inserts-filling-11', '12', '13', '14']      # U1..U6 (emptying)
LOWER = ['09-li', '10-l2', '11-l3', '12-l4', '13-l5', '14-2']                                   # L1..L6 (filling)
TONGUES = [('15', (41, 237)), ('15-16-f2', (27, 207)), ('20-ember', (29, 218)), ('ember-fleck', (23, 211)), ('hinged', (31, 212))]
SMALL = ['small', 'reference-proofs', '3-states', '04', '06', '07', '09', '10-2', '11', '12']
EMBER = '#ff8a2a'


def hg_images(C):
    C.img('hframe', LH + '21-25-assembled-states.webp'); C.img('hglass', LH + 'front-view.webp')
    for i, n in enumerate(UPPER): C.img('U%d' % (i + 1), LH + n + '.webp')
    for i, n in enumerate(LOWER): C.img('L%d' % (i + 1), LH + n + '.webp')
    for i, (n, _) in enumerate(TONGUES): C.img('F%d' % (i + 1), LH + n + '.webp')
    C.img('ember', LH + 'ember-fleck-2.webp')


def tall_draw(C, f, ox, oy, level, flames, s=1.0, stream=True, glow_a=1.0):
    """the tall hourglass; level 0 (top full) .. 1 (run out); flames: list of (index, scale 0..1)"""
    X = lambda x: ox + x * s
    Y = lambda y: oy + y * s
    ui = min(5, int(level * 6)); li = min(5, int(level * 6))
    C.clip(f, [(X(30), Y(40)), (X(203), Y(40)), (X(203), Y(212)), (X(30), Y(212))])
    if True:
        C.card(f, 'U%d' % (ui + 1), X(116), Y(208), px=C.wh('U%d' % (ui + 1))[0] / 2, py=C.wh('U%d' % (ui + 1))[1] - 2, s=1.28 * s)
    C.unclip(f)
    C.clip(f, [(X(30), Y(226)), (X(203), Y(226)), (X(203), Y(392)), (X(30), Y(392))])
    k = 'L%d' % (li + 1)
    C.card(f, k, X(116), Y(382), px=C.wh(k)[0] / 2, py=C.wh(k)[1] - 2, s=1.32 * s)
    C.unclip(f)
    if stream and level < 0.98:   # the falling stream: a coded dashed line through the neck
        off = (f * 3) % 8
        C.line(f, [(X(116), Y(206 + off)), (X(116), Y(340 - level * 60))], '#d9a54a', w=2.5 * s, dash=[5 * s, 3 * s])
    for i, sc in flames:   # painted tongues on hinges, separate flicker clocks
        if sc <= 0.02: continue
        key = 'F%d' % (i + 1); hx, hy = TONGUES[i][1]
        rot = 6 * math.sin(f * (0.9 + 0.23 * i) + i * 1.7) - 8 + 4 * i
        sy = (0.86 + 0.14 * flick(i, f, 0, 1, 1.3)) * sc
        C.card(f, key, X(84 + 16 * i), Y(372), px=hx, py=hy, s=0.62 * s, sy=sy, rot=rot)
    if glow_a > 0 and flames:
        tot = sum(sc for _, sc in flames) / 5
        C.glow(f, X(116), Y(300), 170 * s * (0.6 + 0.4 * tot), '#ff9a3c', glow_a * tot * flick(9, f, 0.7, 1.0, 1.5))
    C.card(f, 'hglass', X(116.5), Y(214), s=0.9 * s, a=0.5)
    C.card(f, 'hframe', ox, oy, px=0, py=0, s=s)


def hourglass_clips():
    # 1 · the tall hourglass running, full fire
    N = 96
    C = Clip('mech.hourglass.run', 'the last hourglass: sand runs (6+6 replacement inserts), five flame tongues on hinges', ['12'], N, loop=False,
             cm_px=4.0, view=(-30, -60, 300, 500),
             notes='Upper inserts U1→U6 empty and lower inserts L1→L6 fill (replacement every 16 f), each masked to its bulb (clip) so the hanging tabs hide; the stream is a coded dashed line. Five painted tongues hinge on their tabs at the lower bulb floor on separate flicker clocks + one glow. Glass overlay at 50% over the sand, frame on top.')
    hg_images(C); C.size_cm(58, 106)
    for f in range(N):
        lv = f / (N - 1)
        tall_draw(C, f, 0, 0, lv, [(i, ease((f - 4 * i) / 10)) for i in range(5)])
    C.event(0, 'sfx.sand.trickle_loop', 'sand trickling (loop)'); C.event(0, 'sfx.fire.catch', 'flames catch'); C.event(20, 'sfx.fire.crackle_loop', 'fire crackle (loop)')
    C.anchor('top', (116, 0)); C.anchor('base', (116, 425)); C.anchor('neck', (116, 212))
    done(C, 'hourglass.run.json', 'mech')

    # 2 · the last one alight: tongues go out, the ember lifts and drifts off over the sea
    N = 120
    C = Clip('mech.hourglass.last_ember', 'the last hourglass goes out: tongues die one by one, the ember lifts off the rim and drifts away', ['12'], N, loop=False,
             cm_px=4.0, view=(-30, -260, 760, 700),
             notes='One-shot. Tongues drop out on f8/20/32/44, the last shrinks to nothing by f64; the ember card (with glow) rises from the neck, slips out over the top rail and drifts up and right on a slow sine, fading at the end. anchor_track "ember" for the camera or a sequence to follow.')
    hg_images(C); C.size_cm(58, 106)
    tr = []
    for f in range(N):
        fl = []
        for i in range(5):
            die = [8, 20, 32, 44, 54][i]
            sc = 1 - ease((f - die) / (10 if i < 4 else 12))
            fl.append((i, sc))
        tall_draw(C, f, 0, 0, 0.98, fl, stream=False)
        p = (f - 56) / (N - 56)
        if p < 0:
            ex, ey = 116, 300
        else:
            q = ease(min(1, p * 1.6))
            ex = 116 + 560 * p ** 1.3 + 30 * math.sin(p * 9)
            ey = 300 - 240 * q - 200 * p - 20 * math.sin(p * 7)
        a = 1.0 if p < 0.75 else max(0, 1 - (p - 0.75) / 0.25)
        if f >= 50:
            C.glow(f, ex, ey, 90, EMBER, 0.95 * a * flick(3, f, 0.7, 1, 2))
            C.card(f, 'ember', ex, ey, s=1.8, rot=f * 4, a=a)
            C.glow(f, ex, ey, 16, '#fff1c0', a)
        tr.append((ex, ey))
    C.anchor('ember', tr)
    C.event(8, 'sfx.fire.gutter', 'a tongue gutters out'); C.event(44, 'sfx.fire.gutter', 'another goes'); C.event(64, 'sfx.fire.out_hiss', 'the last flame goes out')
    C.event(66, 'sfx.ember.lift', 'the ember lifts (soft rising tone)')
    done(C, 'hourglass.last_ember.json', 'mech')

    # 3 · the yard: twelve hourglasses going out one by one (k*7 mod 12)
    N = 168
    C = Clip('mech.hourglass.yard', 'the yard of hourglasses going out one by one', ['12'], N, loop=False, cm_px=2.2,
             view=(-60, -60, 1560, 640),
             notes='Twelve copies of the master in two rows (back row 0.7×): lit (A2) → guttering, outline broken (A3) → dead and slumped (A4) + a smoke card rising. Neck flame tongues flicker on their own clocks. Deaths ordered k*7 mod 12, every 12 f from f12; the last one (k=11) stays alight.')
    C.img('lit', HH + 'a2-lit-intact.webp'); C.img('gut', HH + 'slumped-a4-dead.webp'); C.img('dead', HH + 'a4-dead-slumped.webp')
    C.img('smoke', HH + 'smoke-only-hide-body.webp'); C.img('fl', HH + '10.webp'); C.img('fl2', HH + 'part-8.webp')
    C.size_cm(600, 160)
    pos = []
    for r in range(2):
        for c in range(6):
            sc = 0.62 if r == 0 else 0.9
            x = 110 + c * 225 + (0 if r else 112) * 0.9
            y = 300 if r == 0 else 520
            pos.append((x, y, sc))
    order = [(k * 7) % 12 for k in range(12)]
    death = {order[k]: 12 + 12 * k for k in range(11)}     # the 12th never dies
    draw_order = list(range(6)) + list(range(6, 12))
    for f in range(N):
        for i in draw_order:
            x, y, sc = pos[i]
            t = f - death.get(i, 10 ** 6)
            if t < 0:
                st = 'lit'
            elif t < 8:
                st = 'gut'
            else:
                st = 'dead'
            C.shadow(f, x, y, 95 * sc, 0.6)
            if st == 'dead':
                C.card(f, 'dead', x, y, px=133, py=262, s=sc * 0.8)
            else:
                C.card(f, st, x, y, px=105, py=318, s=sc)
            if st != 'dead':
                fsc = 1.0 if st == 'lit' else 0.55 * (1 - t / 8)
                rot = 7 * math.sin(f * (0.8 + 0.07 * i) + i)
                C.card(f, 'fl', x, y - 168 * sc, px=53, py=262, s=sc * 0.45, sy=(0.85 + 0.15 * flick(i, f, 0, 1, 1.4)) * max(0.05, fsc), rot=rot)
                C.glow(f, x, y - 190 * sc, 120 * sc, '#ff9a3c', (0.55 if st == 'lit' else 0.3) * flick(i + 2, f, 0.7, 1, 1.6))
            if 4 <= t < 52:   # smoke card rises and thins
                p = (t - 4) / 48
                C.card(f, 'smoke', x + 20 * p * sc, y - 230 * sc - 160 * p * sc, s=sc * (0.45 + 0.4 * p), a=0.5 * (1 - p), rot=8 * p)
    for k in range(11):
        C.event(12 + 12 * k, 'sfx.fire.gutter', 'hourglass %d goes out' % order[k])
    C.event(0, 'sfx.fire.crackle_loop', 'many small fires (loop)')
    for i, (x, y, sc) in enumerate(pos):
        C.anchor('hg%02d' % i, (round(x), round(y)))
    done(C, 'hourglass.yard.json', 'mech')

    # 4 · a hand-held hourglass running (replacement levels)
    N = 120
    C = Clip('mech.hourglass.hand', 'the hand hourglass: sand running through ten replacement levels', ['12'], N, cm_px=6, view=(-80, -110, 160, 220),
             notes='Ten small replacement cards ordered by measured sand (top→bottom), 12 f each; a dashed stream through the neck. Anchor "grip" at the waist for a hand.')
    for i, n in enumerate(SMALL): C.img('s%d' % i, HH + n + '.webp')
    C.size_cm(14, 24)
    for f in range(N):
        i = min(9, f // 12)
        C.card(f, 's%d' % i, 0, 0)
        if i < 9:
            C.line(f, [(0, -4 + (f * 2) % 6), (0, 40)], '#c99a52', w=1.6, dash=[3, 2])
    C.anchor('grip', (0, 0)); C.event(0, 'sfx.sand.trickle_loop', 'sand trickling')
    done(C, 'hourglass.hand.json', 'mech')


# ════════════════════════════════════════════════════════════════════════════════════════════════
# 02 → 03 → 04 · THE TAMBOURINE
# ════════════════════════════════════════════════════════════════════════════════════════════════
TB = '02.props.tambourine/'
TBR = '03.props.tambourine-broken/'
JINGLES = ['part-3', 'part-4', 'part-5', 'part-6', 'eight', 'jingles-paired-brass', 'j1-j8-each-pair-one', 'piece']
FRAGS = ['fo1', 'fo2', 'fo3', 'fo4', 'fo5', 'fo6', 'fo7', 'fo8', 'fo9', 'f10', 'f11', 'f12', 'f13']
WIN = '02.props.window/'


def tamb_images(C):
    C.img('rim', TB + 'wooden-rim-with-8-jingle-slots.webp'); C.img('skin', TB + 'skin-disc-pale-parchment-skin.webp')
    for i, n in enumerate(JINGLES): C.img('j%d' % i, TB + n + '.webp')
    C.img('t_front', TB + 'front.webp'); C.img('t_spin', TB + 'spin.webp'); C.img('t_edge', TB + 'edge.webp'); C.img('t_blur', TBR + 'whole-tambourine-tumble-blur.webp')
    for i, n in enumerate(FRAGS): C.img('fr%d' % i, TBR + n + '.webp')


def tamb_whole(C, f, x, y, s=1.0, rot=0.0, shiver=1.0):
    """front-on jointed tambourine: skin disc, rim, eight jingle pairs on brads"""
    C.card(f, 'skin', x, y, s=s * 0.86, rot=rot)
    C.card(f, 'rim', x, y, s=s, rot=rot)
    for i in range(8):
        ang = rot + i * 45 + 22.5
        r = 196 * s
        jx, jy = x + r * math.cos(math.radians(ang)), y + r * math.sin(math.radians(ang))
        wob = shiver * 9 * math.sin(f * 2.3 + i * 1.9)
        C.card(f, 'j%d' % i, jx, jy, s=0.34 * s, rot=ang + 90 + wob)


def throw_pose(f, i):
    """replacement card + angle while spinning through the air"""
    seq = ['t_front', 't_spin', 't_edge', 't_spin', 't_blur', 't_spin']
    return seq[(f // 2 + i) % len(seq)]


def tambourine_clips():
    # 1 · held: jingles shiver on their brads
    C = Clip('mech.tambourine.shake', 'tambourine (jointed): eight jingle pairs shiver on their brads', ['02', '03'], 24, cm_px=1.7,
             view=(-300, -300, 600, 600), notes='Skin disc behind the open rim; eight jingle cards hung radially, each rocking on its own clock. Anchor "grip" on the rim for a hand.')
    tamb_images(C); C.size_cm(25, 25)
    for f in range(24):
        sh = 1.0 if f < 12 else 0.4
        tamb_whole(C, f, 0, 0, rot=3 * math.sin(f / 24 * TAU * 2), shiver=sh)
    C.anchor('grip', (0, 210)); C.event(0, 'sfx.tambourine.shake', 'jingles shiver'); C.event(12, 'sfx.tambourine.jingle_soft', 'settling jingle')
    done(C, 'tambourine.shake.json', 'mech')

    # 2 · thrown: arc + spin by replacement
    N = 40
    C = Clip('mech.tambourine.throw', 'tambourine thrown: parabolic arc, spinning by replacement (front/spin/edge/blur)', ['02', '03'], N, loop=False,
             cm_px=1.7, view=(-150, -420, 1500, 600), notes='One-shot. Released at (0,0) (anchor "release"), lands at (1250,0) on f39; replacement cycle every 2 f plus a 31°/f rotation. anchor_track "tambourine" for whatever it hits (window, rose window).')
    tamb_images(C); C.size_cm(25, 25)
    tr = []
    for f in range(N):
        p = f / (N - 1)
        x = 1250 * p; y = -360 * 4 * p * (1 - p)
        C.shadow(f, x, 120, 70 * (0.5 + 0.5 * (1 - 4 * p * (1 - p))), 0.35)
        C.card(f, throw_pose(f, 0), x, y, s=0.5, rot=f * 31)
        tr.append((x, y))
    C.anchor('release', (0, 0)); C.anchor('tambourine', tr)
    C.event(0, 'sfx.whoosh.throw', 'thrown'); C.event(6, 'sfx.tambourine.jingle_spin', 'jingles rattle in the spin')
    done(C, 'tambourine.throw.json', 'mech')

    # 3 · through the living-room window (02): the pane cracks, shards fall and stay fallen
    N = 72
    C = Clip('mech.tambourine.window', 'tambourine through the window: pane struck, cracked, eleven shards fall and stay; night outside', ['02'], N, loop=False,
             cm_px=2.0, view=(-120, -60, 720, 560),
             notes='Frame card with its opening clip-masked onto a plate (the night driveway card). Tambourine flies in from camera (big) toward the pane, shrinking with depth; f16 strike: clear pane → cracked pane; f18 the eleven shard cards drop with spin and stay on the sill/floor; the tambourine carries on, still whole, out into the plate. Curtains on the rod, sill in front.')
    tamb_images(C); C.size_cm(220, 190)
    C.img('wframe', WIN + 'window-sill.webp'); C.img('pane', WIN + 'suse-pane.webp'); C.img('cracked', WIN + 'curtain-rod.webp')
    C.img('mullion', WIN + 'cross-mullion.webp'); C.img('cur_l', WIN + 'window.webp'); C.img('cur_r', WIN + 'curtain-right.webp')
    C.img('rod', WIN + 'curtain-rod-2.webp'); C.img('sill', WIN + 'window-sill-2.webp')
    shards = ['g01', 'part-10', 'part-11', 'part-12', 'part-13', 'part-14', 'part-15', 'part-16', 'part-17', 'g10', 'g11']
    for i, n in enumerate(shards): C.img('g%d' % i, WIN + n + '.webp')
    OP = (65, 53, 309, 251)       # opening in the frame card
    ox, oy, ow, oh = OP
    hole = [(ox, oy), (ox + ow, oy), (ox + ow, oy + oh), (ox, oy + oh)]
    import random
    rnd = random.Random(2)
    sh = [(ox + 30 + rnd.random() * (ow - 60), oy + 30 + rnd.random() * (oh - 80), rnd.uniform(-1, 1), rnd.uniform(-20, 20)) for _ in shards]
    tr = []
    for f in range(N):
        C.clip(f, hole)
        C.plate(f, '../kits/cut/02.set.driveway_road_night/02-driveway-downhill-road-separate-layers.webp', ox - 40, oy - 10, ow + 80, oh + 30, sy=0.3, sh=0.7)
        C.poly(f, hole, fill='rgba(10,14,30,0.35)')
        if f < 16:
            C.card(f, 'pane', ox + ow / 2, oy + oh / 2, sx=ow / 208, sy=oh / 319, a=0.55)
        elif f < 20:
            C.card(f, 'cracked', ox + ow / 2, oy + oh / 2, sx=ow / 223, sy=oh / 322, a=0.8)
        # through the hole: the tambourine carries on out into the night
        if f >= 16:
            p = (f - 16) / 40
            if p < 1:
                C.card(f, throw_pose(f, 1), ox + ow * 0.55 + 140 * p, oy + oh * 0.45 - 60 * math.sin(p * 2.5), s=0.18 * (1 - 0.8 * p), rot=f * 25)
        C.unclip(f)
        if f < 20:
            C.card(f, 'mullion', ox + ow / 2, oy + oh / 2, sx=ow / 205, sy=oh / 307)
        C.card(f, 'wframe', 0, 0, px=0, py=0)
        C.card(f, 'rod', 220, 30, s=0.72)
        C.card(f, 'cur_l', 40, 190, s=0.85, rot=-1)
        C.card(f, 'cur_r', 400, 190, s=0.85, rot=1)
        C.card(f, 'sill', 220, 345, s=0.8)
        # shards fall and stay fallen on the floor line
        if f >= 18:
            for i, (sx0, sy0, dx, sp) in enumerate(sh):
                t = (f - 18 - i % 4) / 18
                if t < 0:
                    C.card(f, 'g%d' % i, sx0, sy0, s=0.5); continue
                q = min(1, t)
                y = sy0 + (470 - sy0) * q * q
                C.card(f, 'g%d' % i, sx0 + dx * 60 * q, y, s=0.5, rot=sp * 9 * q, sy=(1 - 0.6 * q))
        if f < 16:   # flying in from camera
            p = f / 16
            x = lerp(-40, ox + ow * 0.55, p); y = lerp(560, oy + oh * 0.45, ease(p))
            C.card(f, throw_pose(f, 0), x, y, s=lerp(1.1, 0.22, p), rot=f * 33)
            tr.append((x, y))
        else:
            tr.append((ox + ow * 0.55, oy + oh * 0.45))
        if 16 <= f < 20:
            C.glow(f, ox + ow * 0.55, oy + oh * 0.45, 160, '#dfeeff', 0.7 * (1 - (f - 16) / 4))
    C.anchor('tambourine', tr); C.anchor('strike', (ox + ow * 0.55, oy + oh * 0.45))
    C.event(0, 'sfx.whoosh.throw', 'thrown'); C.event(16, 'sfx.glass.shatter', 'pane shatters'); C.event(30, 'sfx.glass.tinkle', 'shards land and settle')
    done(C, 'tambourine.window.json', 'mech')

    # 4 · shatters into the thirteen fragments (03), landing as a trail
    N = 72
    C = Clip('mech.tambourine.shatter', 'tambourine shatters into its thirteen fragments, which land and stay as a trail', ['03', '04'], N, loop=False,
             cm_px=1.7, view=(-760, -520, 1520, 760),
             notes='One-shot. Tumble-blur card falls to f20 and bursts: the thirteen rim-arc fragments (each with skin wedge + jingle) fly out on their own arcs with spin, land on the floor line (y=180) on f34-50 in a trail along x, and stay. Each landing has a jingle click.')
    tamb_images(C); C.size_cm(300, 140)
    import random
    rnd = random.Random(5)
    land = sorted([(-620 + i * 98 + rnd.uniform(-20, 20)) for i in range(13)])
    rnd.shuffle(land)
    tfall = []
    for i in range(13):
        tl = 14 + rnd.randint(0, 16)
        tfall.append((land[i], tl, rnd.uniform(-1, 1) * 40, rnd.uniform(160, 300), rnd.uniform(-90, 90) + 180 * (1 if i % 2 else -1)))
    for f in range(N):
        if f < 20:
            p = f / 20
            C.card(f, 't_blur', 0, -360 + 360 * p * p, s=0.6, rot=f * 23)
            continue
        if f < 24:
            C.glow(f, 0, 0, 200, '#fff3d8', 0.8 * (1 - (f - 20) / 4))
        for i, (lx, tl, rot0, h, spin) in enumerate(tfall):
            t = min(1, (f - 20) / tl)
            x = lerp(0, lx, t)
            y = lerp(0, 180, t) - h * 4 * t * (1 - t)
            r = rot0 + spin * t * 3 if t < 1 else rot0 + spin * 3
            C.card(f, 'fr%d' % i, x, y, s=0.5, rot=r, py=C.wh('fr%d' % i)[1] * 0.75)
    for i, (lx, tl, *_r) in enumerate(tfall):
        C.event(20 + tl, 'sfx.tambourine.fragment_land', 'fragment %d lands' % (i + 1))
    C.event(20, 'sfx.tambourine.shatter', 'the tambourine shatters')
    C.anchor('burst', (0, 0)); C.anchor('trail_start', (-620, 180)); C.anchor('trail_end', (560, 180))
    done(C, 'tambourine.shatter.json', 'mech')

    # 5 · the trail in the sand (04): fragments half-buried, leading off into depth
    C = Clip('mech.tambourine.trail', 'the trail: thirteen fragments half-buried in sand, receding (ash sifting over)', ['04'], 48, cm_px=1.7,
             view=(-500, -300, 1000, 560),
             notes='Each fragment sits in its own sand clip (a wavy polygon cutting off its lower part) so it reads half-buried; scale falls off with depth. A slow sift of ash over the trail (tiny drifting specks). Anchors trail_00..12 = each fragment, for the heart to lead along.')
    tamb_images(C); C.size_cm(400, 200)
    for f in range(48):
        for i in range(13):
            k = 12 - i
            d = k / 12
            s = 0.55 * (1 - 0.65 * d)
            x = -300 + 520 * d + 120 * math.sin(d * 5)
            y = 200 - 380 * d ** 0.8
            cut = y + 20 * s / 0.55
            C.clip(f, [(x - 120, y - 200), (x + 120, y - 200), (x + 120, cut + 6 * math.sin(i)), (x, cut - 8), (x - 120, cut + 4)])
            C.card(f, 'fr%d' % k, x, y, s=s, rot=(k * 47) % 80 - 40)
            C.unclip(f)
        for j in range(18):
            px = -450 + ((j * 137 + f * 3) % 900); py = -250 + ((j * 71 + f * 4) % 480)
            C.poly(f, [(px, py), (px + 3, py + 1), (px + 1, py + 3)], fill='rgba(210,205,195,0.6)')
    for k in range(13):
        d = k / 12
        C.anchor('trail_%02d' % k, (round(-300 + 520 * d + 120 * math.sin(d * 5)), round(200 - 380 * d ** 0.8)))
    C.event(0, 'sfx.wind.shore_loop', 'shore wind, ash sifting (loop)')
    done(C, 'tambourine.trail.json', 'mech')


# ════════════════════════════════════════════════════════════════════════════════════════════════
# SKY & LIGHT · clouds over the moon, stars hidden dot by dot, lamps, neon, the LED canopy
# ════════════════════════════════════════════════════════════════════════════════════════════════
MR = '04.fx.moon-reach/'
CAN = '09.hero.canopy/'
TR = '07.set.projection_three_roads/'


def star(C, f, x, y, s, a, color='#fff6dc'):
    if a <= 0.02: return
    pts = []
    for i in range(8):
        r = s if i % 2 == 0 else s * 0.22
        t = i * math.pi / 4
        pts.append((x + r * math.sin(t), y - r * math.cos(t)))
    C.glow(f, x, y, s * 2.4, color, 0.5 * a)
    C.poly(f, pts, fill=color, a=a)


STARS = [(-520, -230, 9), (-430, -120, 6), (-300, -260, 7), (-160, -200, 5), (40, -280, 8), (160, -150, 6), (330, -250, 9), (470, -170, 6), (560, -60, 5), (-560, -20, 6), (250, -40, 5), (-60, -90, 4)]


def sky_clips():
    # 1 · clouds drifting across the moon
    N = 192
    C = Clip('mech.sky.moon_clouds', 'cloud cards drifting across the moon; the sky clipped to its window, stars twinkling', ['04', '09', '10'], N, cm_px=1.0,
             view=(-640, -360, 1280, 720),
             notes='Loop. Everything sits inside a clip (the sky window) so clouds enter/leave cleanly at its edges. Moon card + cool glow behind; three cloud cards (04.fx.moon-reach) drift right at different speeds and wrap; where a cloud covers the moon the glow dims (coverage computed per frame). Stars are coded pin-holes (four-point cards + glow) that twinkle.')
    C.img('moon', MR + '7-reach1-small-reach2-small-medium.webp'); C.img('c1', MR + 'one-one.webp'); C.img('c2', MR + '4-b-hide-one-star.webp'); C.img('c3', MR + 'a-small.webp')
    C.size_cm(1280, 720)
    sky = [(-640, -360), (640, -360), (640, 360), (-640, 360)]
    clouds = [('c1', 0.0, 40, 1.0, 0.9), ('c2', 0.45, -160, 1.0, 0.7), ('c3', 0.75, 120, 2.0, 0.75)]
    for f in range(N):
        C.clip(f, sky)
        C.poly(f, sky, fill='#0b1226')
        for i, (x, y, s) in enumerate(STARS):
            star(C, f, x, y, s, flick(i, f * 0.5, 0.45, 1.0, 1.0))
        cover = 0
        cl = []
        for k, ph, y, speed, s in clouds:
            x = -900 + ((f / N * speed + ph) % 1) * 1800
            cl.append((k, x, y, s))
            if abs(x - 120) < 220 * s and abs(y + 60) < 200: cover = max(cover, 1 - abs(x - 120) / (220 * s))
        C.glow(f, 120, -60, 420, '#9fb8ff', 0.45 * (1 - 0.7 * cover))
        C.card(f, 'moon', 120, -60, s=0.62)
        for k, x, y, s in cl:
            C.card(f, k, x, y, s=s)
        C.unclip(f)
    C.anchor('moon', (120, -60)); C.event(0, 'sfx.wind.night_loop', 'night air (loop)')
    done(C, 'sky.moon_clouds.json', 'mech')

    # 2 · stars taken dot by dot (04), moon covered then revealed
    N = 144
    C = Clip('mech.sky.stars_hide', 'stars muted: cloud lumps take the stars dot by dot, the moon hides then is revealed', ['04'], N, loop=False, cm_px=1.0,
             view=(-640, -360, 1280, 720),
             notes='One-shot. A cloud lump card pops over each star in turn (f8 + 7k, scale-in 4 f, the star dies under it). From f100 the big cloud slides off the moon to reveal it (moon reach). Reverse the clip to bring the stars back.')
    C.img('moon', MR + '7-reach1-small-reach2-small-medium.webp'); C.img('lump', MR + 'a-small.webp'); C.img('lump2', MR + 'one-one.webp'); C.img('big', MR + '4-b-hide-one-star.webp')
    C.size_cm(1280, 720)
    sky = [(-640, -360), (640, -360), (640, 360), (-640, 360)]
    for f in range(N):
        C.clip(f, sky); C.poly(f, sky, fill='#0b1226')
        rev = ease((f - 100) / 30)
        C.glow(f, 120, 40, 380, '#9fb8ff', 0.15 + 0.4 * rev)
        C.card(f, 'moon', 120, 40, s=0.55)
        C.card(f, 'big', lerp(130, 760, rev), 40, s=1.25)
        for i, (x, y, s) in enumerate(STARS):
            t0 = 8 + 7 * i
            p = (f - t0) / 4
            star(C, f, x, y, s, flick(i, f * 0.5, 0.45, 1.0) * (1 if p < 0.5 else 0))
            if p > 0:
                C.card(f, 'lump' if i % 2 else 'lump2', x, y + 6, s=0.32 * ease(p) + 0.001, rot=(i * 37) % 30 - 15)
        C.unclip(f)
    for i in range(len(STARS)):
        C.event(8 + 7 * i, 'sfx.star.wink_out', 'a star is taken')
    C.event(100, 'sfx.moon.reveal', 'moon revealed (soft swell)')
    C.anchor('moon', (120, 40))
    done(C, 'sky.stars_hide.json', 'mech')


def light_clips():
    # 1 · street lamps and their pools; one buzzes and stutters
    N = 96
    C = Clip('mech.light.streetlamps', 'street lamps: warm heads, light pools on the ground, one stuttering', ['07', '09', '10', '12'], N, cm_px=1.0,
             view=(-80, -60, 1100, 520),
             notes='Three lamp-post cards (07 three roads); each head has a glow and a light-pool card (04 light pool) screen-blended on the ground under it, both following the lamp level. Lamp 2 is a dying tube: random-looking stutter with an off stretch.')
    C.img('lampA', TR + 'streetlamp-a-dim-warm.webp'); C.img('lampB', TR + 'streetlamp-dim-warm.webp'); C.img('lampC', TR + 'streetlamp-c-dim-warm.webp')
    C.img('pool', MR + 'medium.webp')
    C.size_cm(1100, 450)
    lamps = [('lampA', 120, 0.95, (104, 30)), ('lampB', 500, 1.0, (60, 30)), ('lampC', 860, 1.0, (74, 30))]
    for f in range(N):
        C.poly(f, [(-80, 400), (1020, 400), (1020, 460), (-80, 460)], fill='#15110e')
        for i, (k, x, s, (hx, hy)) in enumerate(lamps):
            w, h = C.wh(k)
            lv = flick(i, f, 0.85, 1.0)
            if i == 1:
                stut = (f % 37) in (3, 4, 9, 22, 23, 24) or 52 <= f < 66
                lv = 0.12 if stut else lv
            C.card(f, 'pool', x, 405, s=0.9, sy=0.5, a=0.65 * lv, blend='screen')
            C.glow(f, x, 400, 200, '#ffcc7a', 0.18 * lv)
            C.card(f, k, x, 400, px=w / 2, py=h, s=1.6 * s)
            gx = x + (hx - w / 2) * 1.6 * s; gy = 400 - (h - hy) * 1.6 * s
            C.glow(f, gx, gy, 130, '#ffcf80', 0.75 * lv)
            C.glow(f, gx, gy, 20, '#fff4d8', lv)
        if True:
            pass
    C.event(0, 'sfx.lamp.hum_loop', 'sodium lamp hum (loop)')
    for f in (3, 22, 40, 52, 66):
        C.event(f, 'sfx.lamp.buzz_flicker', 'tube stutters')
    for i, (k, x, s, _) in enumerate(lamps):
        C.anchor('pool_%d' % i, (x, 400))
    done(C, 'light.streetlamps.json', 'mech')

    # 2 · neon trims flickering, reflected in the wet pavement
    N = 96
    C = Clip('mech.light.neon', 'neon tubes flickering with their wet-pavement reflections', ['06', '07', '09', '10'], N, cm_px=1.0,
             view=(-40, -40, 1200, 520),
             notes='Four neon tube cards (09 canopy trims) each with a coloured glow on its own clock; tube 3 stutters. Below the kerb line each tube is drawn again flipped, darkened and squashed (the reflection), alpha following its tube, with a wavy clip.')
    tubes = [('n_pink', 'n-curb-strip-1', '#ff4fb8'), ('n_teal', 'k-neon-trim-1-pc', '#38f0e0'), ('n_purple', 'part-13', '#9a5cff'), ('n_orange', 'part-15', '#ffa040')]
    for k, n, _ in tubes: C.img(k, CAN + n + '.webp')
    C.img('sign', CAN + 'j-neon-trim-1-1-pc-k-neon-trim-1-pc.webp')
    C.size_cm(1200, 480)
    pos = [(250, 60), (850, 60), (250, 190), (850, 190)]
    for f in range(N):
        C.poly(f, [(-40, -40), (1160, -40), (1160, 300), (-40, 300)], fill='#0d0a10')
        C.card(f, 'sign', 550, 120, s=0.9, a=0.7)
        C.poly(f, [(-40, 300), (1160, 300), (1160, 480), (-40, 480)], fill='#07060a')
        lv = []
        for i, (k, n, col) in enumerate(tubes):
            l = flick(i, f, 0.8, 1.0, 1.2)
            if i == 2 and ((f % 29) in (5, 6, 14) or 70 <= f < 76): l = 0.1
            lv.append(l)
            x, y = pos[i]
            C.glow(f, x, y, 260, col, 0.55 * l)
            C.card(f, k, x, y, s=1.4, a=0.35 + 0.65 * l)
            C.glow(f, x, y, 60, '#ffffff', 0.25 * l)
        C.clip(f, [(-40, 300)] + [(x, 300 + 4 * math.sin(x / 40 + f / 5)) for x in range(-40, 1180, 40)] + [(1160, 480), (-40, 480)])
        for i, (k, n, col) in enumerate(tubes):
            x, y = pos[i]
            ry = 300 + (300 - y) * 0.8
            C.glow(f, x, ry, 200, col, 0.25 * lv[i])
            C.card(f, k, x + 4 * math.sin(f / 4 + i), ry, s=1.4, sy=-0.7, a=0.35 * lv[i])
        C.unclip(f)
    C.event(0, 'sfx.neon.hum_loop', 'neon hum (loop)'); C.event(5, 'sfx.neon.flicker', 'tube stutters'); C.event(70, 'sfx.neon.flicker', 'tube stutters')
    done(C, 'light.neon.json', 'mech')

    # 3 · the LED canopy (09): chase lights ripple along the ceiling
    N = 96
    C = Clip('mech.light.canopy', 'the LED canopy: colour chases rippling along the galaxy ceiling, reflected below', ['09'], N, cm_px=1.0,
             view=(-560, -160, 1120, 520),
             notes='The canopy card (09.hero.canopy) lit by coded LED chases: three colour waves (magenta, cyan, violet) travel along it as rows of screen-blend glows; a flipped dark copy under the street line reflects it.')
    C.img('canopy', CAN + 'b-palm-row-left-c-palm-row-right-pc-pe-1-1.webp')
    C.img('palms', CAN + 'd-palm-tree-1-e-palm-tree-2-pe-pe-1-1.webp')
    C.size_cm(1100, 500)
    cols = ['#ff3fb0', '#33e6ff', '#9b5bff']
    for f in range(N):
        C.poly(f, [(-560, -160), (560, -160), (560, 360), (-560, 360)], fill='#06050c')
        C.card(f, 'palms', -270, 150, s=1.0, a=0.85); C.card(f, 'palms', 270, 150, s=1.0, flip=True, a=0.85)
        C.card(f, 'canopy', 0, -60, s=1.0)
        C.clip(f, [(-526, -160), (526, -160), (526, 40), (-526, 40)])
        for w, col in enumerate(cols):
            for j in range(14):
                x = -520 + ((j * 80 + f * (6 + 3 * w) + w * 250) % 1040)
                y = -100 + 50 * math.sin(x / 140 + w)
                C.glow(f, x, y, 70, col, 0.45 * (0.5 + 0.5 * math.sin(f / 6 + j + w * 2)), blend='screen')
        C.unclip(f)
        C.poly(f, [(-560, 250), (560, 250), (560, 360), (-560, 360)], fill='#08070d')
        C.card(f, 'canopy', 0, 330, s=1.0, sy=-0.45, a=0.35)
        for w, col in enumerate(cols):
            C.glow(f, -520 + ((f * (6 + 3 * w) + w * 250) % 1040), 320, 160, col, 0.18)
    C.event(0, 'sfx.canopy.led_hum_loop', 'electric hum, faint crowd (loop)')
    done(C, 'light.canopy.json', 'mech')

    # 4 · a bare bulb under its shade switched on, flickering, off (12 niche/porch)
    N = 72
    C = Clip('mech.light.bulb', 'bare bulb under a shade: switched on, flickers, goes out (replacement off/on cards)', ['12', '09'], N, cm_px=4.0,
             view=(-200, -120, 400, 520), notes='Shade on its socket brad; bulb is replaced off↔on (12.props.niche-porch), with a warm glow and a cone pool on the wall/floor. On at f8, stutters at f40-46, out at f60.')
    C.img('shade', '12.props.niche-porch/shade.webp'); C.img('off', '12.props.niche-porch/b7-sagging.webp'); C.img('on', '12.props.niche-porch/on.webp')
    C.size_cm(60, 120)
    for f in range(N):
        on = 8 <= f < 60 and f not in (40, 41, 44, 46)
        lv = flick(1, f, 0.88, 1.0) if on else 0
        sw = 2 * math.sin(f / 18)
        C.line(f, [(0, -120), (0, -40)], '#1a1410', w=3)
        if lv:
            beam(C, f, 0, 40, 1, lv, length=360, spread=2.4, tilt=90)
        C.card(f, 'on' if on else 'off', 0, 60, s=0.8, rot=sw)
        C.card(f, 'shade', 0, -10, s=0.95, rot=sw)
        if lv:
            C.glow(f, 0, 70, 180, '#ffd58a', 0.7 * lv); C.glow(f, 0, 70, 30, '#fff6e0', lv)
    C.event(8, 'sfx.switch.click', 'switch on'); C.event(40, 'sfx.lamp.buzz_flicker', 'bulb stutters'); C.event(60, 'sfx.switch.click', 'switch off')
    C.anchor('pull_cord', (0, 40))
    done(C, 'light.bulb.json', 'mech')


# ════════════════════════════════════════════════════════════════════════════════════════════════
# 09 · THE PHONE BOOTH · 14 · THE DOOR TO ANOTHER WORLD
# ════════════════════════════════════════════════════════════════════════════════════════════════
PB = '09.props.phonebooth/'


def cord(C, f, a, b, sag, color='#2a2a2e', w=5):
    pts = []
    for i in range(17):
        t = i / 16
        x = lerp(a[0], b[0], t); y = lerp(a[1], b[1], t) + sag * 4 * t * (1 - t)
        pts.append((x, y))
    C.line(f, pts, color, w=w)
    C.line(f, pts, '#77777c', w=w * 0.5, dash=[3, 4])   # the armoured coil


def phone_clips():
    N = 120
    C = Clip('mech.phone.booth_handset', 'phone booth: handset lifted off the hook to the ear, held, hung back; ceiling light on, off at dawn', ['09'], N, loop=False,
             cm_px=1.3, view=(-60, -80, 420, 520),
             notes='Back panel with the payphone body; handset card hangs on the hook, lifts on an arc to the "ear" socket (anchor_track handset, for the caller\'s hand), held, hung back at f84. The armoured cord is coded (catenary + coil dashes). Lit ceiling strip replaced by the grey one at f104 (dawn). Front frame + clear pane at 25% over everything; the caller slides between back panel and glass.')
    C.img('back', PB + 'back-with-payphone-body-no-handset.webp'); C.img('frame', PB + 'steel-mullion.webp'); C.img('pane', PB + 'front-glass-pane-clear.webp')
    C.img('lit', PB + 'cream-yellow.webp'); C.img('unlit', PB + 'light-off-grey.webp'); C.img('floor', PB + 'steel-grey.webp')
    C.img('wedge', PB + 'pavement-grey.webp'); C.img('hand', '09.props.phones-chair/a-payphone.webp')
    C.size_cm(110, 260)
    HOOK = (122, 178); EAR = (165, 70)
    tr = []
    for f in range(N):
        if f < 12: p = 0
        elif f < 24: p = ease((f - 12) / 12)
        elif f < 84: p = 1
        elif f < 96: p = 1 - ease((f - 84) / 12)
        else: p = 0
        lit = f < 104
        if lit:
            C.card(f, 'wedge', 147, 455, s=1.1, a=0.9); C.glow(f, 147, 440, 220, '#ffe7a0', 0.35)
        C.card(f, 'floor', 147, 420, s=0.85)
        C.card(f, 'back', 147, 230, s=1.05)
        x = lerp(HOOK[0], EAR[0], p) - 25 * math.sin(p * math.pi); y = lerp(HOOK[1], EAR[1], p)
        cord(C, f, (128, 262), (x + 4, y + 52), 30 + 50 * (1 - p))
        C.card(f, 'hand', x, y, s=0.42, rot=-28 * p + 3 * math.sin(f / 5) * (1 if 30 < f < 80 else 0))
        tr.append((x, y))
        C.card(f, 'pane', 147, 225, sx=1.75, sy=1.1, a=0.22)
        C.card(f, 'frame', 147, 230, s=1.05)
        C.card(f, 'lit' if lit else 'unlit', 147, 20, s=1.05)
        if lit:
            C.glow(f, 147, 40, 260, '#ffe7a0', 0.55 * flick(4, f, 0.9, 1.0))
    C.anchor('handset', tr); C.anchor('caller', (150, 420)); C.anchor('hook', HOOK)
    C.event(0, 'sfx.phone.booth_hum_loop', 'booth light hum (loop)'); C.event(12, 'sfx.phone.handset_lift', 'handset lifted')
    C.event(26, 'sfx.phone.dial_tone', 'dial tone / the line open'); C.event(96, 'sfx.phone.handset_hang', 'handset hung up'); C.event(104, 'sfx.switch.click', 'booth light goes off at dawn')
    done(C, 'phone.booth_handset.json', 'mech')


def portal_clips():
    N = 96
    C = Clip('mech.portal.door', 'a door that opens onto another world: slab swings on its hinge, the aperture shows a plate', ['14', '11', '12'], N, loop=False,
             cm_px=2.6, view=(-140, -40, 600, 660),
             notes='Frame card (14.props.door) with its aperture as a clip mask; inside, a plate from another world (world 08fe12af_0: a sunlit pool). The slab hinges on its left edge and narrows (cos) as it swings toward camera; light from the other side spills as a glow and a floor wedge. Swap the plate src for any world backdrop or film (video: true).')
    C.img('frame', '14.props.door/10-main-states-assembled.webp'); C.img('slab', '14.props.door/2-door-slab-shut.webp'); C.img('knob', '14.props.door/8-door-knob-back.webp')
    C.size_cm(115, 217)
    ax, ay, aw, ah = 37, 52, 218, 513
    hole = [(ax, ay), (ax + aw, ay), (ax + aw, ay + ah), (ax, ay + ah)]
    for f in range(N):
        p = ease((f - 12) / 30) if f < 70 else ease((f - 12) / 30)
        C.poly(f, [(-140, 565), (460, 565), (460, 620), (-140, 620)], fill='#120e0b')
        if p > 0:
            C.poly(f, [(ax, 565), (ax + aw, 565), (ax + aw + 160 * p, 620), (ax - 60 * p, 620)], fill='rgba(255,236,190,0.35)', a=p, blend='screen')
        C.clip(f, hole)
        C.plate(f, '../world/08fe12af_0/backdrop.webp', ax - 250 + 40 * p, ay, ah * 16 / 9, ah, sx=0.0)
        C.unclip(f)
        if p > 0:
            C.glow(f, ax + aw / 2, ay + ah / 2, 380, '#fff1cf', 0.35 * p)
        C.card(f, 'frame', 0, 0, px=0, py=0)
        ang = 80 * p
        sx = math.cos(math.radians(ang))
        C.card(f, 'slab', ax, ay, px=0, py=0, sx=sx * aw / 238, sy=ah / 538, skew=0.12 * math.sin(math.radians(ang)))
        if sx > 0.15:
            C.card(f, 'knob', ax + (aw - 25) * sx, ay + ah * 0.52, s=0.28)
    C.anchor('knob', (ax + aw - 25, ay + ah * 0.52)); C.anchor('threshold', (ax + aw / 2, 565))
    C.event(10, 'sfx.door.handle', 'handle turns'); C.event(12, 'sfx.door.creak_open', 'door creaks open'); C.event(20, 'sfx.world.other_side_air', 'the other world breathes in (birdsong/water)')
    done(C, 'portal.door.json', 'mech')


if __name__ == '__main__':
    only = sys.argv[1:]
    groups = {k[:-6]: v for k, v in globals().items() if k.endswith('_clips') and callable(v)}
    for k, fn in groups.items():
        if not only or k in only:
            fn()
    # index: merge with existing entries so partial rebuilds keep the rest
    ip = os.path.join(HERE, 'index.json')
    old = json.load(open(ip)) if os.path.exists(ip) else []
    by = {e['id']: e for e in old}
    for e in BUILT:
        by[e['id']] = e
    json.dump(sorted(by.values(), key=lambda e: e['id']), open(ip, 'w'), indent=1)
