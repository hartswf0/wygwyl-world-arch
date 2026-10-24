# Joint lab round 03

| joint | best method | clean TRAIN | clean HELD-OUT | clean NATIVE pairs | pair-angles | top failing tests (best method) |
|---|---|---|---|---|---|---|
| neck | register | 23% | 14% | 7% (60) | 156 | width_step 54, trim_cut 23, grommet_peek 14, gap 10 |
| wrist | register_under | 26% | 13% | 21% (198) | 396 | trim_cut 174, grommet_peek 50, exposed_B 12, gap 2 |
| ankle | register_under | 66% | 40% | 68% (108) | 216 | trim_cut 40, tab_visible 11, exposed_A 9, width_step 9 |

## all methods (clean on TRAIN)

| joint | brad_pivot | collar_round | naive | neck_fit | neck_push | register | register_big_brad | register_notab | register_notab_big | register_notab_under | register_round_big | register_under | rigkit | tab_trim_over | tab_trim_under | tuck_trim |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| neck | 12% | 10% | 7% | 12% | 6% | 23% | 14% | - | - | - | 23% | 15% | 5% | 3% | 5% | 7% |
| wrist | 0% | - | 2% | - | - | 26% | - | 24% | 24% | 26% | - | 26% | 0% | 0% | 0% | 0% |
| ankle | 23% | - | 23% | - | - | 55% | - | 52% | 52% | 66% | - | 66% | 28% | 1% | 22% | 36% |
