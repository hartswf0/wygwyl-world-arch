# Joint lab round 04

| joint | best method | clean TRAIN | clean HELD-OUT | clean NATIVE pairs | pair-angles | top failing tests (best method) |
|---|---|---|---|---|---|---|
| neck | register | 78% | 62% | 91% (44) | 104 | tab_visible 16 |
| wrist | register | 98% | 87% | 98% (198) | 396 | exposed_A 3, tab_visible 1 |
| ankle | register_under | 89% | 86% | 92% (108) | 216 | tab_visible 6, facing 6, exposed_B 4, exposed_A 3 |

## all methods (clean on TRAIN)

| joint | boot_over_align | brad_pivot | collar_round | naive | neck_fit | neck_push | register | register_align | register_big_brad | register_notab | register_notab_big | register_notab_under | register_round_big | register_under | register_under_align | register_view | register_view_align | rigkit | shin_over_align | tab_trim_over | tab_trim_under | tuck_trim |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| neck | - | 6% | 3% | 8% | 4% | 3% | 78% | 76% | 78% | - | - | - | 78% | 67% | - | 67% | 65% | 3% | - | 11% | 3% | 31% |
| wrist | - | 0% | - | 15% | - | - | 98% | 96% | - | 97% | 97% | 98% | - | 98% | 96% | - | - | 0% | - | 0% | 0% | 0% |
| ankle | 85% | 35% | - | 37% | - | - | 81% | - | - | 85% | 85% | 89% | - | 89% | - | - | - | 31% | 89% | 15% | 36% | 39% |
