# Per-pair bendability (round 07)

Clean ROM = the run of 15-degree steps round the rest angle with no background in the crook (core_bg), no notch
cut by the method (cut_bg; not counted at neck / wrist / ankle) and the under piece >= 40% visible. Measured by rom.py
on every lab pair (natives + cross, train + held). hull = the literal local-convex-hull measure (adds <= 1 point over
the pair's own straight pose).

| joint | method | pairs | full-ROM range | clean ROM median (deg) | p25 | pairs clean over the whole range | no clean rest | hull ROM median |
|---|---|---|---|---|---|---|---|---|
| ankle | register | 36 | -30..45 | 75 | 75 | 35 | 1 | 60 |
| ankle | boot_over_align | 36 | -30..45 | 75 | 75 | 35 | 1 | 60 |
| elbow | register | 36 | 0..150 | 30 | 15 | 0 | 5 | 0 |
| elbow | register_notab | 36 | 0..150 | 68 | 49 | 4 | 2 | 0 |
| elbow | register_round | 36 | 0..150 | 150 | 150 | 33 | 2 | 0 |
| hip | register | 36 | -30..125 | 155 | 108 | 8 | 21 | 155 |
| hip | register_align | 36 | -30..125 | 145 | 90 | 16 | 2 | 155 |
| knee | register | 36 | 0..150 | 15 | 15 | 0 | 5 | 0 |
| knee | register_notab | 36 | 0..150 | 45 | 30 | 3 | 5 | 0 |
| knee | register_round | 36 | 0..150 | 150 | 150 | 24 | 5 | 0 |
| neck | register | 12 | -35..35 | 60 | 41 | 3 | 0 | 70 |
| neck | register_align | 12 | -35..35 | 60 | 30 | 3 | 0 | 70 |
| shoulder | register | 16 | -60..180 | 0 | 0 | 0 | 16 | 38 |
| shoulder | register_align | 16 | -60..180 | 240 | 240 | 16 | 0 | 45 |
| wrist | register | 36 | -70..70 | 140 | 140 | 30 | 0 | 140 |
| wrist | register_align | 36 | -70..70 | 140 | 140 | 30 | 0 | 140 |
| wrist | register_under_align | 36 | -70..70 | 140 | 140 | 30 | 0 | 140 |

## pack pairs (round 07): clean ROM and the sampled angle

| joint | method | parent | child | clean ROM | angle |
|---|---|---|---|---|---|
| hip | register_align | waist-hip-bridge-3-eyelets | 8-thigh-l | -30..125 | 15 |
| neck | register | 3a-torso-rear-3-4 | 15-head-rear-3-4 | -35..25 | -35 |
| neck | register | 3a-torso-rear-3-4 | 14-head-rear | -35..10 | -35 |
| shoulder | register_align | 1 | 5-upper-arm | -60..180 | -45 |
| shoulder | register_align | torso-no-head-hips-legs-no-arms-no-no | right-upper-arm | -60..180 | -45 |
| wrist | register_align | left-forearm | right-hand-hand-only | -70..70 | 20 |
| ankle | boot_over_align | shin-l | foot-l | -30..45 | -15 |
| ankle | boot_over_align | shin-l | foot-l | -30..45 | 45 |
| elbow | register_round | uarm-r-2 | 10-forearm-r | 0..150 | 15 |
| elbow | register_round | uarm-l | farm-l | 0..135 | 60 |
| knee | register_round | 8-thigh-l | 12-shinr | 0..150 | 150 |
| knee | register_round | poet-red-black-sunglasses-body-back | left-shin | 0..150 | 15 |
