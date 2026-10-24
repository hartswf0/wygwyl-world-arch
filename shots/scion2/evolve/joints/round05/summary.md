# Joint lab round 05

| joint | best method | clean TRAIN | clean HELD-OUT | clean NATIVE pairs | pair-angles | top failing tests (best method) |
|---|---|---|---|---|---|---|
| neck | register | 80% | 75% | 73% (44) | 56 | covered 8 |
| wrist | register_align | 93% | 95% | 98% (198) | 396 | tab_visible 14, exposed_A 3, gap 1 |
| ankle | register | 90% | 93% | 92% (108) | 216 | exposed_A 12, gap 2, light_rim 1 |
| shoulder | register_under | 49% | 12% | 16% (289) | 391 | width_step 119, exposed_A 111, tab_visible 80, exposed_B 18 |
| elbow | register | 26% | 39% | 41% (198) | 396 | colour_jump 165, exposed_A 10, gap 2 |
| hip | register_align | 26% | 22% | 38% (216) | 432 | width_step 225, exposed_A 141, gap 18, tab_visible 15 |
| knee | register | 14% | 14% | 17% (198) | 396 | colour_jump 194, width_step 18, exposed_A 11, trim_cut 3 |
| waist | register_under | 8% | 7% | 5% (162) | 324 | exposed_A 151, width_step 106, trim_cut 84, tab_visible 49 |

## all methods (clean on TRAIN)

| joint | boot_over_align | boot_over_trim | brad_pivot | collar_round | naive | neck_fit | neck_push | register | register_align | register_big_brad | register_notab | register_notab_big | register_notab_under | register_round_big | register_under | register_under_align | register_view | register_view_align | rigkit | shin_over_align | tab_trim_over | tab_trim_under | tuck_trim |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| neck | - | - | 10% | 5% | 15% | 8% | 5% | 80% | 78% | 80% | - | - | - | 80% | 80% | - | 80% | 78% | 5% | - | 0% | 5% | 15% |
| wrist | - | - | 0% | - | 13% | - | - | 92% | 93% | - | 92% | 92% | 90% | - | 90% | 90% | - | - | 0% | - | 0% | 0% | 0% |
| ankle | 89% | 88% | 38% | - | 37% | - | - | 90% | - | - | 89% | 89% | 86% | - | 86% | - | - | - | 33% | 86% | 14% | 38% | 40% |
| shoulder | - | - | 0% | - | 0% | - | - | 48% | 44% | - | - | - | - | - | 49% | 49% | - | - | 0% | - | 0% | 0% | 0% |
| elbow | - | - | 14% | - | 11% | - | - | 26% | 25% | - | - | - | - | - | 14% | 14% | - | - | 9% | - | 0% | 2% | 8% |
| hip | - | - | 0% | - | 1% | - | - | 22% | 26% | - | - | - | - | - | 18% | 18% | - | - | 0% | - | 0% | 0% | 0% |
| knee | - | - | 2% | - | 4% | - | - | 14% | 10% | - | - | - | - | - | 4% | 4% | - | - | 0% | - | 0% | 0% | 1% |
| waist | - | - | 0% | - | 0% | - | - | 0% | 0% | - | - | - | - | - | 8% | 8% | - | - | 4% | - | 0% | 0% | 1% |
