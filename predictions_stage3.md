# Stage 3 predictions

Written by the author in the Stage 3 brief and committed here as written, with each expectation, before any Part B run. The estimator, its checks V1 to V4 and the settings of DECISIONS.md D19 and D20 were coded and run first, as the brief orders (results/stage3_checks.json).

P1. With the ends insulated, the radial forecast alone is within 0.3 K of the resolved core throughout (Stage 1's 0.29 K), and the estimator does not make it worse: its mean absolute error is below 0.3 K in all three M50 cases. Expectation: likely.

P2. With the ends cooled at 2C, minus 5 C, the radial forecast alone misses the resolved core by more than 0.8 K at the end of discharge in the M50 (Stage 1's offsets averaged 1.19 K over the units). Expectation: likely.

P3. The estimator with the paper's error model cuts that end-of-discharge miss by at least half. Expectation: uncertain; it depends on how fast the error model learns against a bias that grows through the discharge.

P4. The estimator whose forecast carries the end correction has a smaller mean absolute error than the estimator without it, in every cooled-ends case. Expectation: likely; the correction removes most of the bias before the estimator sees it.

P5. In the cooled-ends M50 cases the learned error, averaged over the second half of the discharge, lies within 30 % of the end correction's sink term on the same history. Expectation: uncertain; the two need not share a form.

P6. In the 4680 with cooled ends the radial forecast's end-of-discharge miss exceeds 5 K (Stage 1's offsets averaged 7.96 K) and the estimator with the paper's error model leaves more than 1 K of it. Expectation: uncertain.

P7. Doubling the observation noise raises the estimator's mean absolute error by less than the noise's standard deviation. Expectation: likely.

## Scoring rules
Registered settings (D20): the model-error level sigma_ref = 1.238e4 W/m3, readings every 20 s, noise 0.1 K, seed 20261027, 3000 members. Each prediction is also evaluated at 0.1 and 10 times sigma_ref, and read against that bracket. Errors are the estimate minus the resolved centre node at mid-length, at every archived time (about every 10 s).
- P1: in cases (a), 1.25C and 2C at 25 C and 2C at minus 5 C: the forecast's largest absolute error over the discharge is at most 0.3 K, and the estimator's mean absolute error is below 0.3 K, in all three.
- P2: case (b), 2C at minus 5 C, 21700: the forecast's absolute error at the end of discharge exceeds 0.8 K.
- P3: the same case: the estimator's absolute end-of-discharge error is at most half the forecast's.
- P4: every case (b), the three 21700 conditions and the 4680: the end-corrected estimator's mean absolute error is below the estimator's.
- P5: the three 21700 cases (b): the learned error's volume mean over the second half of the discharge lies within 30 % of the end sink's volume mean on the same history, in each.
- P6: 4680, case (b), 2C at minus 5 C: the forecast's absolute end error exceeds 5 K and the estimator's exceeds 1 K.
- P7: 21700, case (b), 2C at minus 5 C: the estimator's mean absolute error with 0.2 K noise exceeds that with 0.1 K by less than 0.1 K (the paper's noise level).
