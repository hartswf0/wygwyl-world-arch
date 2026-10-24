# Joint lab round 01

| joint | best method | clean TRAIN | clean HELD-OUT | pair-angles | top failing tests (best method) |
|---|---|---|---|---|---|
| neck | tab_trim_under | 46% | 48% | 216 | width_step 58, exposed_A 34, exposed_B 11, facing 6 |
| wrist | brad_pivot | 99% | 98% | 216 | exposed_B 2 |
| ankle | brad_pivot | 75% | 80% | 216 | exposed_A 33, width_step 11, facing 6, exposed_B 3 |

## all methods (clean on TRAIN)

| joint | brad_pivot | naive | rigkit | tab_trim_over | tab_trim_under | tuck_trim |
|---|---|---|---|---|---|---|
| neck | 1% | 10% | 0% | 45% | 46% | 0% |
| wrist | 99% | 97% | 56% | 55% | 76% | 87% |
| ankle | 75% | 68% | 64% | 47% | 73% | 45% |
