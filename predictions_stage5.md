# Stage 5 predictions

The author wrote these in the Stage 5 brief, each with its expectation, and they are committed here as written. The commit comes after Part A0 and before any kernel is computed or any coupled solve is run. DECISIONS.md D27 to D33 fix the procedure they are scored on.

Part A0 found two things in single-cell runs before this commit, and the author read them before choosing to keep the registered set (D27):
- Under ORegan2022 the main case's discharge ends at 147 s, while the registered heat lasts 1,707 s.
- At both of the specification's charge limits, ORegan2022's negative-electrode surface next to the separator reaches its stoichiometric limit before 4.2 V.

The predictions and their expectations are unchanged.

P1. The kernels reproduce Stage 4's unit temperatures in its five cases within 0.01 K at every archived time. Expectation: likely.

P2. Main case, one-way heat, ORegan2022: the coupled solve's time-averaged share spread under the radial kernel exceeds that under the resolved kernel by 25 to 45 %. Expectation: likely (the proxy gave +36.4 %).

P3. Same case, resolved kernel: the coupled time-averaged share spread lies within 20 % of the proxy's 5.54 %. Expectation: uncertain.

P4. Main case, two-way heat: the multi-unit penalty in discharge energy is smaller under the resolved kernel than under the radial one by at least a fifth of the radial value. Expectation: uncertain.

P5. The 4680, two-way heat: the penalty under the radial kernel is at least 1.5 times that under the resolved kernel. Expectation: uncertain.

P6. Main case, resolved kernel: per-group heat changes the time-averaged spread of the unit temperatures by less than 10 % of its value under uniform heat. Expectation: uncertain.

P7. Charge at the specification's two limits, M50: the plating margin under the radial kernel differs from that under the resolved kernel by less than 2 mV in both cases. Expectation: likely (the heat at these rates is a small part of the 2C heat).

P8. In every registered charge case the smallest margin is held by the outermost group. Expectation: uncertain (the outer units are the coldest, but the warmer inner units carry more current).

P9. At 0 C the single-unit model's plating-limited rate exceeds the coupled model's under the resolved kernel by less than 5 % in the M50 and by more than 5 % in the 4680. Expectation: uncertain.

## Scoring rules

**Registered choices:**
- ORegan2022.
- 15 groups.
- Two-way heat, except in P2 and P3, which name one-way heat.
- Each discharge case on its registered heat's time grid, and each charge in 10 s steps.

**Terms used below:**
- The main case is the 21700 (the M50) at 2C and minus 5 C with the ends cooled at h = 400 W/(m^2 K). The 4680 case is the same condition in the 4680.
- The specification's two limits are 1,455 mA at 0 C and 3,395 mA at 25 C (D32).
- Each kernel is a thermal model: radial, resolved (here with the ends cooled) or end-corrected.
- The penalty is the single-unit model's energy to 2.5 V over the coupled model's, less one (D31), with both models under the same kernel and heat rule.
- The share spread at a time is the largest group share minus the smallest. It is time-averaged over the coupled run's own discharge (D31).

**Brackets.** Each prediction is also evaluated under Chen2020 and reported beside the registered verdict, without a verdict of its own. P3's Chen2020 bracket is read against Stage 4's Chen2020 proxy spread, 2.538 %.

**Rules:**
- P1: radial, resolved and end-corrected kernels (the end-corrected is the radial with the ends insulated). The uniform-heat response (the sum of the group responses) is convolved with the registered heat on the archive's grid in the five Stage 4 cases. Holds if the largest absolute difference from the stored histories (results/stage4_hist_1d.json, results/stage4_hist_3d_21700.json, results/stage4_hist_3d_4680.json) is below 0.01 K, over every case, unit and archived time.
- P2: main case, one-way heat. Holds if the radial kernel's time-averaged share spread over the resolved kernel's, less one, lies between 0.25 and 0.45 inclusive.
- P3: main case, one-way heat, resolved kernel. Holds if the time-averaged share spread over 0.0554168 (Stage 4's registered proxy spread, results/stage4_errors.csv), less one, lies between minus 0.20 and plus 0.20 inclusive.
- P4: main case, two-way heat. Holds if the radial kernel's energy penalty is positive and the resolved kernel's is at most 0.8 times it.
- P5: 4680 case, two-way heat. Holds if the radial kernel's energy penalty is positive and at least 1.5 times the resolved kernel's.
- P6: main case, two-way heat, resolved kernel. The time-averaged spread of the 45 unit temperatures (largest minus smallest, trapezoidal rule over the discharge) is compared between two heat distributions from the same total heat history: each group's own heat, and every unit at the area-weighted mean of the groups' heats, convolved with the uniform-heat response. Holds if the first over the second, less one, lies strictly between minus 0.10 and plus 0.10.
- P7: M50, coupled model, two-way heat, at both of the specification's limits. Holds if the radial kernel's margin minus the resolved kernel's is below 2 mV in absolute value in both.
- P8: coupled model, two-way heat, at both of the specification's limits, both cells, under each of the three kernels (12 cases). Holds if in all 12 the margin's minimum lies in the outermost group.
- P9: 0 C, two-way heat, resolved kernel, rates refined to 0.001C (D32). With e = single-unit rate over coupled rate, less one, holds if e is below 0.05 in the M50 and above 0.05 in the 4680.
