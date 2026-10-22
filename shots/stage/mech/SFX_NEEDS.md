# Sound effects the mechanisms need

Ids used in `events[].sfx` of `shots/stage/mech/clips/*.json` (FORMATS.md §4). The engine/sfx agent maps each to a small mono file in `shots/stage/sfx/index.json`, drawn from the project's own sound libraries. `_loop` ids should loop seamlessly.

| id | what it should sound like | used by |
|---|---|---|
| `sfx.ash.sift` | fine ash/grit sliding off card, 1-2 s, soft hiss | heart.clean_off |
| `sfx.canopy.led_hum_loop` | electric LED hum under a faint street crowd, loopable | light.canopy |
| `sfx.car.bump` | car suspension thump over a road bump | car.drive |
| `sfx.car.door_open` | car door unlatch + swing (old 1990s sedan) | car.door |
| `sfx.car.door_slam` | car door slam, solid | car.door |
| `sfx.car.engine_idle_loop` | small petrol engine idling, loopable | car.drive, car.hazards, car.interior |
| `sfx.car.hazard_tick` | hazard relay click (on) | car.hazards |
| `sfx.car.hazard_tock` | hazard relay click (off), slightly lower | car.hazards |
| `sfx.door.creak_open` | old wooden door creaking open, 1.5 s | portal.door |
| `sfx.door.handle` | brass door knob turning, latch | portal.door |
| `sfx.ember.lift` | single soft rising tone / breath as the ember lifts (2-3 s) | hourglass.last_ember |
| `sfx.fire.catch` | small flame whoomp as fire catches | hourglass.run |
| `sfx.fire.crackle_loop` | small candle/lamp fire crackle, loopable | hourglass.run, hourglass.yard |
| `sfx.fire.gutter` | a small flame guttering out (sputter, 0.5 s) | hourglass.last_ember, hourglass.yard |
| `sfx.fire.out_hiss` | last flame goes out: short hiss + tiny smoke puff | hourglass.last_ember |
| `sfx.glass.shatter` | window pane shatter (single pane, domestic) | tambourine.window |
| `sfx.glass.tinkle` | glass shards settling on a sill/floor | tambourine.window |
| `sfx.glint.ping` | tiny bright metallic ping (the tank glint), very short | motorcycle.plates, motorcycle.ride |
| `sfx.heart.clean_chime` | soft clean chime/swell as the blue point brightens | heart.clean_off |
| `sfx.heart.dub` | heartbeat second beat (softer) | heart.beat, heart.dusted, heart.float |
| `sfx.heart.lub` | heartbeat first beat (stronger) | heart.beat, heart.clean_off, heart.dusted, heart.float |
| `sfx.lamp.buzz_flicker` | electric lamp buzz/stutter, 0.3-1 s | light.bulb, light.streetlamps |
| `sfx.lamp.hum_loop` | sodium street lamp hum, loopable | light.streetlamps |
| `sfx.metal.plate_clunk` | steel plate seating into a metal frame, dull clunk | motorcycle.plates |
| `sfx.moon.reveal` | soft airy swell as the moon is revealed | sky.stars_hide |
| `sfx.motorcycle.ride_loop` | motorcycle engine at steady cruising speed, loopable | motorcycle.ride |
| `sfx.motorcycle.start` | motorcycle engine catching / starting | motorcycle.plates |
| `sfx.neon.flicker` | neon tube flicker crackle | light.neon |
| `sfx.neon.hum_loop` | neon sign hum, loopable | light.neon |
| `sfx.phone.booth_hum_loop` | phone booth fluorescent light hum, loopable | phone.booth_handset |
| `sfx.phone.dial_tone` | payphone dial tone / open line | phone.booth_handset |
| `sfx.phone.handset_hang` | payphone handset hung on hook (clack) | phone.booth_handset |
| `sfx.phone.handset_lift` | payphone handset lifted off hook | phone.booth_handset |
| `sfx.sand.trickle_loop` | fine sand trickling through an hourglass neck, loopable | hourglass.hand, hourglass.run |
| `sfx.star.wink_out` | tiny soft tick/pluck as a star is taken (12 in a row; vary pitch) | sky.stars_hide |
| `sfx.switch.click` | light switch / pull cord click | light.bulb, phone.booth_handset |
| `sfx.tambourine.fragment_land` | a tambourine fragment landing on sand/stone with its jingle (short) | tambourine.shatter |
| `sfx.tambourine.jingle_soft` | tambourine jingles settling | tambourine.shake |
| `sfx.tambourine.jingle_spin` | tambourine jingles rattling in a spin | tambourine.throw |
| `sfx.tambourine.shake` | tambourine shake | tambourine.shake |
| `sfx.tambourine.shatter` | tambourine bursting apart: wood crack + jingle scatter | tambourine.shatter |
| `sfx.whoosh.throw` | object thrown, short whoosh | tambourine.throw, tambourine.window |
| `sfx.wind.night_loop` | quiet night air, loopable | sky.moon_clouds |
| `sfx.wind.shore_loop` | shore wind with faint surf, loopable | tambourine.trail |
| `sfx.world.other_side_air` | the other world through the door: open air, water, distant birds (loop or 4 s) | portal.door |
