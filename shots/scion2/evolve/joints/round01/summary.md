# Joint lab round 01

| joint | best method | clean TRAIN | clean HELD-OUT | pair-angles | top failing tests (best method) |
|---|---|---|---|---|---|
| neck | tab_trim_under | 62% | 37% | 216 | width_step 23, exposed_A 9, gap 6 |
| wrist | naive | 19% | 10% | 216 | facing 126, gap 3, exposed_A 2 |
| ankle | naive | 3% | 0% | 216 | facing 144, exposed_A 42, width_step 17, exposed_B 2 |

## all methods (clean on TRAIN)

| joint | brad_pivot | naive | rigkit | tab_trim_over | tab_trim_under | tuck_trim |
|---|---|---|---|---|---|---|
| neck | 4% | 1% | 3% | 60% | 62% | 3% |
| wrist | 19% | 19% | 8% | 8% | 12% | 19% |
| ankle | 3% | 3% | 3% | 3% | 3% | 3% |
