# Stage 4: the independent read

A separate checking agent did this read on commit 2310bb6, before the note's Stage 4 section was written. It was given the files, predictions_stage4.md and D22 to D25, not the author's working. Its scripts import nothing from `src/`: they recompute from the stored files, and they re-solve the one-dimensional models from D7 and D18 with their own solver.

**Result:** no registered number, verdict, definition, area weight or case label is wrong. P1, P2 and P4 hold; P3, P5, P6 and P7 fail, at the registered choices and at every bracket.

What each script checks:
- `check_ab.py`: the readings (time averages and end values) for every case, field and unit, and V1.
  - The readings equal the stored ones exactly.
  - The end values equal the archive: exactly for the 21700, and within 3.6e-15 K for the 4680.
  - The registered offsets and spreads match Stage 2's within 1.4e-17 and Stage 1's within 5.6e-17.
- `check_1d_resolve.py`: the radial and end-corrected histories, re-solved independently. Every stored row matches within 5e-8 K, the rounding of the stored values.
- `check_cd.py`: all 160 rows of `results/stage4_errors.csv` and all 6,984 rows of `results/stage4_units.csv`, recomputed and equal at the stored precision.
  - It also re-scores P1 to P7 at the registered choices and at the four brackets (`my_scorecard.json`), matching within 1.7e-13 with every verdict the same.
- `check_e.py`: the sensitivities, which are identical. R(T) is strictly decreasing with no outliers.
- `check_f.py`, `check_f_soc50.py`: R re-derived in PyBaMM by two routes of the checker's own at seven set, temperature and state-of-charge points, within 5.8e-7 of the table.
- `check_g.py`: the definitions against DECISIONS.md and the scoring rules.

Two notes from the read, recorded in D26:
- In every case, field and reading the hottest unit is the innermost and the coldest the outermost, so the hottest and coldest units' shares (D24) are the innermost and outermost shares in `results/stage4_errors.csv`.
- The case (a) flag in `results/stage4_unit_temps.json` compares against the three-decimal values of Stage 1's table; the full-precision values in `results/results_3d.csv` also match.

Run from this folder with `python3 -I -B <script>`. `check_g.py` reads the predictions' commit through git. `check_f*.py` need PyBaMM 26.9.
