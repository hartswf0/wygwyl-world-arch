# Joint lab: connection methods evolved per joint type, bottom up

    python3 -m evolve.joints.lab <round> neck,wrist,ankle        (from shots/scion2; 2 processes)

## What it does
- **Parts.** The poet's parts come from `shots/scion2/library2/index.json`: `status ok`, and the part gate (`library2/qa/gates.py`) not FAIL.
- **On-the-fly parts.** Part types that library2 does not have yet are regularised the same way from the old library (`parts.py`). They use the same 10 px/cm grid, with the pivot and axis from `evolve/cards.prep`.
- **Connecting a pair** (`connect.py`). The parent stays in its canonical pose. The child's pivot goes onto the parent's joint keypoint, and the child is turned by the sweep angle about that joint. A method is a set of genes:
  - pivot choice;
  - overlap;
  - which part is on top;
  - child trim to the parent's contour;
  - width match by uniform scale;
  - brad seam;
  - facing flip;
  - the parent's tab or collar trim.
- **Fitness** (`qa.py`).
  - Each pair-angle is scored with `library2/qa/seam.py` `score()`, the shared definition. A pair-angle is CLEAN, WARN (amber) or MUTILATED (red).
  - One lab-side term is added: `trim_cut`, a straight scissor cut made by the trim gene that stays visible. seam.py has no such term yet.
  - Fitness is the share of CLEAN pair-angles on TRAIN pairs, over the sweep −60, −30, 0, 30, 60 and 90°. HELD-OUT pairs (a third, chosen by a hash of the pair) are reported, never used for selection.
- **Outputs.** Each round writes `round<NN>/`:
  - `summary.md` and `summary.json`;
  - `<joint>.json`, holding every pair-angle verdict;
  - `<joint>_sheet.jpg`, the best method, with one row per pair across the sweep. Each cell is outlined green, amber or red, and the failing spot is circled.
  - `<joint>_failures.jpg`;
  - `critic/s01..s12.jpg`, pair renders with no names. Their key is `critic_key.json`, outside the folder.
- **New methods.** These go in `methods/<joint>.json` as {name: genes}, next to the seed methods in `lab.py`.
