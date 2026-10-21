# Stage 2 predictions

Written by the author in the Stage 2 brief and committed here as written, before any Stage 2 computation (A2, A3, B2). P1 to P4 were written before ref. 33 was read. They are committed after its values were recorded (inputs/ref33_values.md, commit bf4055e), which the brief allows, so P1 can be checked against that file directly; it is scored as written. The central values of P5 to P8 come from the steady solution of the corrected equation, worked by the author before the brief from Stage 1's inputs (end share 18.9 % in the M50 and 38.6 % in the 4680; corrected radial difference 0.770 and 0.505 of the uncorrected one).

P1 Ref. 33's cross-layer conductivity is lower than O'Regan's 1.2251 W/(m K), by a factor between 1.0 and 2.5 (central 1.4).

P2 With ref. 33's properties alone, the factor at 2C and minus 5 C stays above 1.5 (central 2.5): the heat, not the conductivity, carries the low-temperature gap.

P3 The property substitution leaves the ratio of the minus 5 C factor to the 25 C, 2C factor unchanged within 10 % (it can move it only if ref. 33's properties depend on temperature).

P4 If the heat part can be computed, ref. 33's heat over the paper's minus 5 C window exceeds Chen2020's by a factor between 1.5 and 4 (central 2).

P5 Case (b): the corrected model's share of the heat through the ends lies within 2 percentage points of the resolved cell's in both cells (central 18.9 against 19 %, 38.6 against 38 %).

P6 Case (b): the corrected model's mean absolute per-unit offset falls below 0.3 K in the M50 (from 1.19 K; central 0.1 K) and below 1.0 K in the 4680 (from 7.96 K; central 0.3 K).

P7 Case (b): the spread overstatement falls below 10 % in both cells (from 36 and 98 %; central 5 % and under 1 %).

P8 Case (b): the reconstructed axial difference at the core lies within 15 % of the resolved one in both cells (central within 5 %).

P9 Case (d), h = 25: the corrected model's mean absolute per-unit offset falls below 0.5 K, from the 4.08 K of the uncorrected model at h = 25.

P10 Case (d), h = 25: the parabolic reconstruction misses the resolved axial difference at the core by more than 15 % (central 30 % low), because at low h the steady estimate gives 0.18 of the radial difference against the resolved 0.25.

## Scoring rules
As in Stage 1, every prediction is scored on the registered inputs at 2C and minus 5 C at the end of discharge (1706.7 s), unless it names another condition. The factors and the paper's values are those of D17.
- P1: the ratio 1.2251 / lambda_ref33; held if it lies in [1.0, 2.5].
- P2: the factor with ref. 33's properties and the Chen2020 heat at 482.4 and 540.0 s; held if both exceed 1.5.
- P3: R = (factor at 2C, minus 5 C) / (factor at 2C, 25 C), with O'Regan's properties and with ref. 33's, both with the Chen2020 heat; held if R changes by at most 10 % at both 482.4 and 540.0 s.
- P4: ref. 33's heat integrated from 0 to 482.4 s and to 540.0 s at 2C and minus 5 C, over Chen2020's; held if both ratios lie in [1.5, 4]. Not scored if the ref. 33 discharge ends before 482.4 s.
- P5: the share of the heat leaving through the ends over the whole discharge, the corrected model against the resolved cell's surface split (D15); held if the two differ by at most 2 percentage points in each cell.
- P6: the mean over units of |corrected minus resolved| at the end of discharge; held if below 0.3 K (21700) and 1.0 K (4680).
- P7: the spread overstatement, |corrected spread / resolved spread - 1|; held if below 10 % in each cell.
- P8: the reconstructed beta (T(0) - T_amb) L^2 / (8 k_z) against the resolved T(0, H/2) - T(0, 0) (D10); held if within 15 % in each cell.
- P9: as P6 in case (d), 21700; held if below 0.5 K.
- P10: as P8 in case (d), 21700; held if the miss exceeds 15 %.
