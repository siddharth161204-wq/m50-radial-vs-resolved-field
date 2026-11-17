# Stage 5: the independent read

A separate checking agent did this read in three passes on branch stage5. The first pass ran while the runs were still being made, on the files then present (17 November 2026, from about 07:10 UTC). The second ran on the final files at commit 097e2af, and this README reports it. A third pass checked the public texts at commit 0716381; what it added about the files is under "After the second pass". The agent did not see the runs being made. It was given predictions_stage5.md and DECISIONS.md D27 to D35, and was pointed to `src/stage5_*.py` to see what was done.

Its scripts import nothing from `src/`. They work in three ways:
- they recompute every reading from the stored kernels, runs and search records;
- they re-solve the one-dimensional models' step responses with their own finite elements;
- they re-run single DFNs with PyBaMM 26.9.0.0 where a check needs the model itself.

No coupled solve was run.

**Result.** Every registered number and verdict reproduces from the files.
- **The four tables.** Every row of `results/stage5_discharge.csv` (72), `stage5_shares.csv` (72), `stage5_charge.csv` (120) and `stage5_limit.csv` (72) matches my recomputation, covering both sets and both heat rules: 4,614 values in all. Neither side has a row the other lacks.
  - Every value agrees within 4.9e-9 relative, the CSVs' own nine-figure rounding.
  - The exception is the current-balance residuals: they are round-off-level numbers and agree within 3e-16 absolute.
- **The scorecard.** Every value of `results/stage5_scorecard.json` equals my scoring by the rules of predictions_stage5.md.
  - Registered verdicts: P1, P2, P6, P7 and P8 hold; P3, P4, P5 and P9 do not.
  - Chen2020 brackets: the conditions of P2, P4, P5, P6, P7 and P8 are met; those of P3 and P9 are not.
  - The brackets are recorded as `condition_met`, and P9's bracket is read at the searches' 0.00625C.
- **The checks.** Every value of `results/stage5_checks.json` equals mine.
  - V1, V2, V5 and V6 hold.
  - V3 fails on four readings and V4 on five, as reported and as D35 states.
- **D35** (at 097e2af). It makes 64 statements that the files can test.
  - 59 agree, three of them only to the one significant figure they are given to.
  - 5 do not; they are listed below. All eight were corrected in commit fe19d0c (see "After the second pass").
- **Summary and paper numbers.** All 546 numbers of `results/stage5_summary.md` and all 768 values of `results/stage5_paper_numbers.json` agree with my values.

## What does not follow from the files

| D35 says | From the files (my value) |
|---|---|
| ORegan2022, 2C at 25 C, with 160 points: ends at "1,469 s" | 1,468.4976 s, which rounds to 1,468 s (my own run gives the same) |
| With 40 points or more, "4.30 A h charged" | 4.2903 A h for 0.7C at 25 C with 40 points, which rounds to 4.29. The other five are 4.2973 to 4.3022 A h. |
| Chen2020, d ln R/dT at 20 points: "0.01121 per K" | 0.01120498 per K in magnitude, which rounds to 0.01120. The 160-point 0.01072 and the 4 % move (4.35 %) hold. |
| ORegan2022's graphite diffusivity at 25 C: "1.4e-13 m^2/s at a stoichiometry of 0.98" | PyBaMM's function gives 9.954e-14 at 0.98. The value 1.411e-13 belongs to 0.9842, the 100 % stoichiometry of D27. With 0.98 the two quoted points are 354-fold apart; with 0.9842 they are 502-fold apart. "About 500-fold" holds over the operating window 0.0296 to 0.9842 (539-fold). |
| The example of a non-monotonic margin: "at 0 C in the M50's coupled search, minus 0.03 mV at 0.28625C and minus 3.66 mV at 0.283125C" | Both values are as stored (−0.0254 and −3.6648 mV), but neither is a smallest margin over a charge: each is the first output below zero of a trial that D32's rule stopped there, so its depth depends on where the crossing falls within the 10 s step. The pair therefore does not show what it is cited for. The statement itself holds (see below). |

**Better evidence for the non-monotonic margin.** Passing trials run to 4.2 V, so their stored margin is the smallest over the charge, and these show the margin rising with rate:
- In the 4680's single-unit search at 25 C (radial kernel): +37.97 mV at 0.500C and +38.37 mV at 0.525C; also +34.77 mV at 0.5375C and +35.43 mV at 0.54375C.
- In the M50's coupled search at 25 C (radial kernel): +34.363 mV at 0.530C and +34.368 mV at 0.53625C.
- In my own scan of the M50's single-unit model at 0 C (resolved kernel, two-way heat, each rate charged to 4.2 V): +18.45 mV at 0.270C and +19.56 mV at 0.275C.

In every one of the 72 searches, and in the scan, each failing rate lies above each passing rate. So the outcome that D32's monotonicity assumption bears on is monotonic, even though the margin is not.

Three statements of D35 hold only to the one significant figure they are given to:
- **Discharges "within 0.2 s".** Chen2020's 2C discharge at minus 5 C spans 0.2022 s across the meshes: 1,705.0550 s with 20 points, 1,704.8528 s with 320.
- **Margins "within 0.01 mV".** Chen2020's 0.7C, 25 C margin spans 0.0106 mV: +0.4759 mV with 20 points, +0.4865 mV with 160. My own runs give the same two values.
- **Pulse resistances "move by 3 to 5 %"** between 20 and 160 points: the range is 3.03 to 5.31 %. Chen2020's at 25 C moves by 5.31 %.

Nothing else in D35, the scorecard, the four tables or the checks file differs from the files.

**The summary's rate table.** At 097e2af it printed the searches' rates to four decimals, and 33 values that fall halfway were rounded either way by their binary representation (0.36875 as 0.3688, but 0.28125 as 0.2812). Since fe19d0c it prints every rate exactly (see "After the second pass").

## After the second pass

D35 was corrected in commit fe19d0c, after the second pass, and the runs' console logs were added in `results/stage5_runs/logs/`. The third pass checked both against the files with short scripts kept outside this folder. The scripts and `out/` files here are the second pass's.

- **D35's corrections agree with the files.** The five statements in the table above now read 1,468 s; 4.29 to 4.30 A h; 0.01120 per K; a stoichiometry of 0.9842; and, for the non-monotonic margin, the 4680's single-unit search at 25 C "and two more such pairs", which are the three pairs listed above. The one-figure items now read 0.21 s, 0.011 mV and 3.0 to 5.3 %. D35 also gives the 4680 kernels' recorded 4.8 GB beside D28's 5.5 GB, and says V3's energies and capacities move by at most 0.15 % (0.147 %).
- **The ripple, now stated for every ORegan2022 discharge, holds.** I removed a local cubic fitted over ±15 outputs (1 s apart) and read each run from 60 s to 20 s before its end.
  - All 68 ORegan2022 discharge runs ripple, coupled and single-unit. The voltage's rms about the trend is 0.34 to 13.9 mV. Under Chen2020 it is at most 0.062 mV, with no regular period.
  - The median spacing of the innermost share's upward zero crossings is 10.4 to 11.3 s at 2C and minus 5 C and 6.5 to 19.0 s in the other cases, as D35 says.
  - The period drifts within a run: at 25 C it ranges from about 6 to 24 s depending on the window. No script in `src/` measures it.
- **The summary's rate table** now prints each search's rate exactly (for example 0.2815625). All 72 entries equal `results/stage5_limit.csv` and my replay of the trials, and all 546 numbers of the summary still agree.
- **What the logs confirm** (at 0716381):
  - the 4680 kernel's second run resuming from step 1,600;
  - the memory guard stopping the M50's 30-group kernels twice at 04:39, at 6,265 and 6,210 MB;
  - the 30-group runs' peak of 4,099 MB;
  - the four jobs that D35 says were stopped and run again.
- **What the logs do not show:**
  - where the first run of the 4680 kernel stopped (its last line is step 2,000 of 2,455);
  - why its second run stopped (its loop ends at 04:42:39, three minutes after the guard's kills);
  - the 2 GB that D35 gives for a 15-group coupled process;
  - any line naming 22 of the 256 discharge and charge run files. These are the 4680's ORegan2022 charges under the radial and resolved kernels (20 files) and its one-way discharge under the end-corrected kernel (2).
- **Two more stopped jobs.** Two jobs stopped before the runs were split are not among D35's four, and both were completed later in `wA.log`:
  - the M50's ORegan2022 charges, after six of fifteen (`q_reg21700.log`);
  - its coupled search at 0 C under the radial kernel, before any trial (`q_cl_21700_reg.log`).
- **The cut-triangle subdivision.** D29 says the resolved cell's cut triangles are subdivided to 12 levels. `src/stage5_kernels.py` uses 10, and all 12 resolved kernels record depth 10. The kernels' own volume check bounds the effect: every inner group's volume lies within 3.1e-5 of its exact annulus. D35 does not mention the difference.

## The checks V3 and V4, recomputed

Main case (M50, 2C, minus 5 C, ends cooled, ORegan2022). The penalties and spreads are in percent; "change" is the check's value over the registered one, less one. Limits: 1 % for V3, 5 % for V4.

| Reading | Registered | Halved step (V3) | Change | 30 groups (V4) | Change |
|---|---|---|---|---|---|
| energy penalty, radial | −1.0014 | −1.0146 | +1.32 % fails | −1.0086 | +0.71 % |
| capacity penalty, radial | −1.1957 | −1.2117 | +1.34 % fails | −1.2043 | +0.72 % |
| spread, radial, two-way heat | 8.3847 | 8.4439 | +0.71 % | 8.7874 | +4.80 % |
| spread, radial, one-way heat | 4.5735 | 4.6068 | +0.73 % | 4.8051 | +5.06 % fails |
| energy penalty, resolved | −0.3633 | −0.3642 | +0.27 % | −0.3659 | +0.72 % |
| capacity penalty, resolved | −0.4233 | −0.4240 | +0.17 % | −0.4263 | +0.72 % |
| spread, resolved, two-way heat | 6.0781 | 6.1193 | +0.68 % | 6.3956 | +5.22 % fails |
| spread, resolved, one-way heat | 3.6316 | 3.6576 | +0.72 % | 3.8273 | +5.39 % fails |
| energy penalty, end-corrected | −0.3905 | −0.3948 | +1.09 % fails | −0.3934 | +0.72 % |
| capacity penalty, end-corrected | −0.4522 | −0.4573 | +1.12 % fails | −0.4555 | +0.72 % |
| spread, end-corrected, two-way heat | 6.4116 | 6.4549 | +0.68 % | 6.7408 | +5.13 % fails |
| spread, end-corrected, one-way heat | 3.8036 | 3.8309 | +0.72 % | 4.0053 | +5.30 % fails |

- **The charge case (M50, 1,455 mA, 0 C).** It passes both checks:
  - the margins move by at most 0.0013 % (halved step) and by 0.013 to 0.017 % (30 groups);
  - the charge at 4.2 V moves by at most 0.00011 %.
- **The main case has no reversal under ORegan2022**, so no reversal reading enters either check.
- **Energies behind V3's failures.** The energies behind the four failed penalties move by at most 0.132 %, as D35 says. The capacities behind the two capacity penalties move by up to 0.147 %.
- **The main case's prediction quantities under the checks' runs.** As context only, not as readings, they move but keep their verdicts:
  - P2's ratio is +0.2595 (halved step) and +0.2555 (30 groups), against +0.2594 registered and a rule of 0.25 to 0.45;
  - P3's ratio is −0.340 and −0.309;
  - P4's penalties stay negative;
  - P7's difference at 0.3C and 0 C is 0.164 and 0.156 mV.

## The post hoc mesh check, reproduced

My own PyBaMM script uses the stored script's settings:
- one DFN held at the ambient on D23's window;
- `initial_soc` passed to the solve;
- IDAKLU at rtol 1e-6 and atol 1e-8;
- outputs every 1 s (discharges) or 10 s (charges), keeping the solver's own steps.

Every value equals `results/stage5_posthoc_mesh.json` exactly, apart from one energy that differs by 2e-15 Wh because of summation order:

| Set | Points | 1,455 mA, 0 C: margin | 3,395 mA, 25 C: margin | 2C, 25 C: cut-off | 2C, minus 5 C: cut-off |
|---|---|---|---|---|---|
| ORegan2022 | 20 | −193.6326 mV | −237.2984 mV | 978.3664 s | 125.7266 s |
| ORegan2022 | 80 | +19.6939 mV | +28.5648 mV | 1,456.4120 s | 140.9066 s |
| ORegan2022 | 160 | | | 1,468.4976 s | |
| Chen2020 | 20 | −1.5135 mV | +0.4759 mV | 1,722.4393 s | 1,705.0550 s |
| Chen2020 | 160 | | +0.4865 mV | | |

- **Margin from the raw potentials.** Computed from φ_s,n and φ_e myself (node minimum, interface by linear extrapolation from the two nodes next to the separator), it equals PyBaMM's two margin variables to 2e-16 V.
- **Initial stoichiometries.** Writing them into the parameter set, as the coupled models do (D30), instead of passing `initial_soc`, gives identical results.
- **Stoichiometry at 100 %.** It is 0.98420, as D27 says.

## What each script checks

- `ir_lib.py`: shared definitions, written from D5, D6, D24 and D28 to D33.
  - The cells, and the area weights (2i − 1)/N^2.
  - The group edges: the integer nearest kN/G, by exact rational arithmetic.
  - The registered heat: `heat_total_W` over the 21700's volume, interpolated linearly at the end of each step of t_end / ceil(t_end / 1 s).
  - The convolution, in impulse form evaluated by FFT. This is a different algorithm from the code's step-response sum.
- `ir_inventory.py`: every run and search that D31 to D33 call for is present (294 runs, 72 searches), and nothing else is.
- `ir_p1_v1.py`: P1 and V1.
  - **P1.** The units' uniform-heat responses are convolved with the registered heat and compared with Stage 4's stored histories, over five cases, three kernels and every unit and archived time. The largest difference is 9.50e-7 K, as stored (`results/stage5_p1.json`, within 4e-9 relative). P1 holds.
  - **V1, in all 34 kernel files:**
    - grid and archive length;
    - group edges and weights;
    - group volumes: the one-dimensional ones equal the exact annuli within 1.1e-14. The resolved cell's agree with the metadata and lie within 3.1e-5 of the exact annuli, except the outermost group, which is short because the mesh's outer polygon is inscribed in r = R: by 0.28 % with 15 groups in the M50, 0.81 % with 30, and 0.06 % in the 4680;
    - the uniform response is the sum of the group responses, and the group means are area-weighted unit means;
    - reciprocity, V_i S_ij = V_j S_ji, holds within 5.7e-15 on the double-precision steady states. On the single-precision step responses it holds within 1.0e-7, with every pair inside its single-precision rounding bound. D33's 1e-9 can only be shown on the steady states, since the steps are stored in single precision;
    - the load-weighted and sampled group means differ by 3.6e-4 to 2.2e-3 of the largest value in the resolved cell (9.7e-4 with 15 groups in the M50), as each file's metadata says.
  - **My own one-dimensional finite elements.** These are P1 in r with the weight 2πr, with lumped capacity, the can, side convection, D18's sink and backward Euler. They re-solve the radial and end-corrected models for all 15 groups on the M50's main and charge grids and on the 4680's main grid. Every unit's response is within 3.5e-8 to 5.9e-8 of the stored values, which is their single-precision rounding, and the steady states are within 3e-11.
- `ir_readings.py`: the four tables, the coupling rule, the searches, C3, P6 and the scorecard.
  - **Readings by D31 and D32**, from each run's stored history:
    - energies (V times I_app, trapezoidal rule), capacities and penalties;
    - shares, their spread and its time average from t = 0;
    - the area-weighted standard deviation, and the innermost and outermost averages;
    - the reversal time;
    - margins: smallest over outputs, nodes, the interface value and groups, with the group and time;
    - held steps.
  - **The coupling rule of D30, in every stored discharge and charge run.** The temperature recorded over each step equals my convolution of the heat recorded at the earlier steps (two-way heat), or of the registered heat held past the archive (one-way heat), within 3.9e-6 K, the single-precision storage.
  - **The current balance**, recomputed from the stored group currents in all 147 coupled runs: at most 5.73e-10 of I_app.
  - **Cut-offs.** Every discharge ends on the 2.5 V event and every charge on the 4.2 V event.
  - **The searches.**
    - Each of the 700 trials' pass or fail follows from its own record.
    - Each of the 72 trial sequences, replayed under D32's rules against the stored outcomes, gives the same trials in the same order, the same start and the same readings. That includes the four refined to 0.001C.
    - No coupled search's start failed, so none stepped down.
    - The same replay gives the sequences that `tests/test_stage5.py` expects on its synthetic margin. The test itself was not run, because the same file runs a coupled solve.
  - **C3.**
    - Stage 4's proxy values come from `results/stage4_errors.csv`.
    - The like-for-like proxy over each coupled one-way run's window is computed from `results/stage4_RT.csv` and the kernels, at unit and group level, with each run's own set's R(T) as D35 records.
  - **P6.** +0.02839 (Chen2020 −0.00270). Leaving out the last, partial step gives +0.02829.
  - **The scorecard**, entry by entry and recursively: P9's per-cell values, P7's pair and P8's twelve holders.
- `ir_v5_v6.py`: V5 and V6.
  - **V5**, from `results/stage5_runs/V5_route2.npz` against the stepwise run:
    - largest share difference 0.037 %;
    - secant residual 9.9e-9 of I_app;
    - the voltages differ by up to 6.5 mV at the last full step, which V5's criterion does not cover.
  - **V6.** The margin rebuilt from the stored potentials is within 7e-9 V of the stored margin, in the same group.
- `ir_v2_v4.py`: V2, V3 and V4.
  - **V2.** Every step's voltage is within 0.75 µV of the single-unit model's, and the capacity within 1.3e-7. V2 holds.
  - **V3 and V4.** The readings from the check runs (table above), and each check run's coupling rule.
  - **The checks file.** Every value of `results/stage5_checks.json` is compared with mine.
  - **Single-unit runs with 30 groups** equal those with 15 within 0.4 µV, as they must, since T_ave does not depend on the grouping.
- `ir_summary.py`: the 546 numbers of the summary tables at their displayed precision, and the 768 values of the paper-numbers file.
- `ir_single_rerun.py`: one DFN at a time, with my own stepping. The temperature is held over each step at the convolution of the model's own heat.
  - **The main case's single-unit discharge and the M50's 1,455 mA, 0 C single-unit charge** (two-way heat, resolved kernel, ORegan2022) equal the stored runs: voltages within 4e-12 and 7e-14 V, the same cut-offs, and margins within 3e-8 V.
  - **The single-unit P9 bracket edges.** At the four rates that bound P9's two single-unit brackets, the model passes or fails as stored, with the same margins.
  - **The scan.** It covers 13 rates from 0.270C to 0.300C, as described above.
- `ir_mesh.py`: the post hoc mesh check, as above.
- `ir_d35.py`: each statement of D35 against the files, recorded with the file's value and a note (`out/d35.json`). It checks:
  - the cgroup's memory limit (6,266,372,096 bytes) and the two cores;
  - the 4680 kernel's resume flag;
  - the trials from the store (17 of 700, in 3 searches);
  - the hold rule's 15 runs:
    - 12 Chen2020 runs for 1 to 7 steps;
    - 3 ORegan2022 runs at 3C and 25 C for 47 to 59 steps, past the heat's 558.3 s;
  - the 25 failed trials at the cut-off (20 ORegan2022 at −199 to −161 mV, 5 Chen2020 at −0.096 to −0.0025 mV);
  - the innermost group at 3C and 25 C, 270 s, under the end-corrected and resolved kernels: 0.22 K warmer in the registered heat's field, 0.18 K in the two-way coupled runs. The coupled run under the end-corrected kernel ends at 604.2 s, and the other three near 280 s;
  - the ripple: 10.3 to 11.5 s in the voltage of the coupled and single-unit models alike, and 10.8 to 11.0 s in the innermost share, between 60 and 140 s. It lengthens to about 14 s near the cut-off, and there is none under Chen2020;
  - P9's bracket resolution, and the figure's panel (b), which is drawn under Chen2020.

## Notes from the read

- **First pass.** It found two things, both resolved in the final files:
  - the scorecard committed in 845ef02 predated the report code's last edit, so its brackets carried `held` and the mesh note was missing;
  - the ORegan2022 runs of four discharge cases were not yet listed among the runs still to be made.
- **The reversal's tolerance.** With no tolerance on "having risen above 1", round-off of up to 2.2e-16 in the shares at t = 0 gives a false reversal near t = 0 in 18 runs: both sets at 1.25C and 25 C, and Chen2020 at 3C and 25 C. With any tolerance from 1e-12 to 1e-9 the readings are as stored.
- **The ripple at 25 C.** It also appears at 2C and 25 C under ORegan2022, which D35 at 097e2af did not mention (it does since fe19d0c).
- **Near-zero passes.** One passing Chen2020 trial clears zero by 3.9 µV (the 4680's single-unit search at 10 C, radial kernel, 0.44375C). The next smallest clear it by 54 to 91 µV.
- **Memory of the 4680 kernel jobs.** They record a peak of 4.83 GB. D35's "about 5.5 GB" at 097e2af was D28's figure from the cost test; since fe19d0c D35 gives both.
- **Sign of d ln R/dT.** It is negative; D35 quotes its magnitude.
- **Panel (c) of the figure.** It plots the size of each penalty on a log scale, with open markers where the single-unit model gives less energy. The two largest open markers are the 4680 under the radial kernel (−53.5 %: the coupled discharge runs to 843 s, the single-unit one to 363 s) and the M50 at 3C and 25 C under the end-corrected kernel (−48.9 %: 604 s against 278 s, the case D35 describes).

## What the read does not cover

- **The coupled solves were not run.** The coupled runs are checked through:
  - their stored histories (every reading, the coupling rule in the stored temperatures, the current balance);
  - V2 and V5 as stored;
  - re-runs of single-unit models.
- **The resolved cell's kernels were not re-solved.** They are checked through:
  - P1, against Stage 4's independently solved histories;
  - their group volumes;
  - reciprocity and internal consistency.
- **`tests/test_stage5.py` was not run**, because its second test runs a coupled solve.
- **The machine's history in D35.** At the second pass the files recorded only the 4680 kernel's resume flag, the kernels' peak memories and which searches hold stored trials. The console logs added in fe19d0c record most of the rest; what they do not show is under "After the second pass". The two-hour limit appears only in the workers' "time budget used" lines.

## Running

From this folder:
- `./run_all.sh` runs everything, about 7 minutes on two free cores.
- `./run_all.sh quick` leaves out the PyBaMM runs, about 30 s.

Each step:
- waits until the machine's memory in use is at most 4.6e9 bytes (`memgate.sh`);
- runs as `python3 -I -B` with one thread at nice 10;
- writes `out/<name>.json` and `out/log_<step>.txt`.

No process exceeded 0.5 GB. Software: Python 3.13, NumPy 2.5.3, SciPy 1.18.1, PyBaMM 26.9.0.0.

Outputs:
- `out/p1_v1.json` (P1, V1, the finite-element re-solve)
- `out/readings.json` (every recomputed reading, the run-level checks, the searches, my scorecard and its comparison)
- `out/readings_mismatches.json` (empty)
- `out/v5_v6.json`, `out/v2_v4.json`
- `out/summary_check.json`
- `out/single_rerun.json`, `out/single_rerun_p9.json`, `out/single_rerun_scan.json`
- `out/mesh_*.json`
- `out/d35.json`
- `out/inventory.json`
