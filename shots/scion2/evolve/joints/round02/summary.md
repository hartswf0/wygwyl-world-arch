# Joint lab round 02

| joint | best method | clean TRAIN | clean HELD-OUT | pair-angles | top failing tests (best method) |
|---|---|---|---|---|---|
| neck | tab_trim_over | 9% | 8% | 216 | registration 82, width_step 70, grommet_peek 65, gap 17 |
| wrist | register | 29% | 33% | 396 | trim_cut 152, tab_visible 25, grommet_peek 23, gap 1 |
| ankle | register_under | 52% | 39% | 216 | trim_cut 48, tab_visible 29, width_step 8, grommet_peek 4 |

## all methods (clean on TRAIN)

| joint | brad_pivot | collar_round | naive | neck_fit | neck_push | register | register_under | rigkit | tab_trim_over | tab_trim_under | tuck_trim |
|---|---|---|---|---|---|---|---|---|---|---|---|
| neck | 0% | 0% | 0% | 0% | 0% | 0% | 4% | 0% | 9% | 1% | 2% |
| wrist | 4% | - | 7% | - | - | 29% | 29% | 5% | 0% | 4% | 7% |
| ankle | 11% | - | 12% | - | - | 31% | 52% | 12% | 0% | 14% | 14% |
