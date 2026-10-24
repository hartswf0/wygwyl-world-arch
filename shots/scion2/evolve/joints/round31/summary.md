# Joint lab round 31

| joint | best method | clean TRAIN | clean HELD-OUT | clean NATIVE pairs | pair-angles | top failing tests (best method) |
|---|---|---|---|---|---|---|
| neck | register | 100% | 60% | 91% (44) | 44 |  |
| wrist | register_under | 99% | 100% | 100% (198) | 198 | gap 1 |
| ankle | register_under | 93% | 88% | 92% (108) | 108 | tab_visible 6, exposed_A 3 |

## all methods (clean on TRAIN)

| joint | brad_pivot | collar_round | naive | neck_fit | neck_push | register | register_big_brad | register_notab | register_notab_big | register_notab_under | register_round_big | register_under | register_view | rigkit | tab_trim_over | tab_trim_under | tuck_trim |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| neck | 0% | 0% | 0% | 0% | 0% | 100% | 100% | - | - | - | 100% | 76% | 76% | 0% | 0% | 0% | 0% |
| wrist | 0% | - | 11% | - | - | 98% | - | 97% | 97% | 99% | - | 99% | - | 0% | 0% | 0% | 0% |
| ankle | 40% | - | 39% | - | - | 89% | - | 93% | 93% | 93% | - | 93% | - | 40% | 19% | 43% | 49% |
