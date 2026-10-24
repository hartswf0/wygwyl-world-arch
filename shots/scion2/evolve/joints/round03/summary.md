# Joint lab round 03

| joint | best method | clean TRAIN | clean HELD-OUT | pair-angles | top failing tests (best method) |
|---|---|---|---|---|---|
| neck | tab_trim_under | 3% | 0% | 180 | trim_cut 105, width_step 74, exposed_A 58, register 55 |
| wrist | tuck_trim | 1% | 0% | 180 | trim_cut 107, register 70 |
| ankle | naive | 0% | 0% | 180 | trim_cut 109, exposed_A 67, register 67, width_step 17 |

## all methods (clean on TRAIN)

| joint | brad_pivot | collar_round | naive | neck_fit | neck_push | register | register_under | rigkit | tab_trim_over | tab_trim_under | tuck_trim |
|---|---|---|---|---|---|---|---|---|---|---|---|
| neck | 0% | 0% | 0% | 3% | 1% | 0% | 0% | 0% | 0% | 3% | 0% |
| wrist | 1% | - | 0% | - | - | 0% | 0% | 0% | 0% | 0% | 1% |
| ankle | 0% | - | 0% | - | - | 0% | 0% | 0% | 0% | 0% | 0% |
