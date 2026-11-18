# The axial blind spot of a radial cell model: the temperature field a multi-unit model assumes, tested on the LG M50 and a 4680

Author: Siddharth Satte, independent researcher, Pune, India (ORCID 0009-0001-3584-1008).

Archived at https://doi.org/10.5281/zenodo.23320969 (all versions). This is version v1.4.0, whose own DOI is added when it is archived; v1.3.0 is https://doi.org/10.5281/zenodo.23753700, v1.2.0 https://doi.org/10.5281/zenodo.23689145 and v1.1.0 https://doi.org/10.5281/zenodo.23320970.

## Result

The paper's radial model carries no heat along the cell's axis. In three dimensions that means insulated ends. Under that condition the resolved three-dimensional cell supports the radial model. At 2C and minus 5 C, every unit of the LG M50 lies within 0.29 K of its radial temperature, and the unit-to-unit spread is 7 % lower in three dimensions. In the 4680 the units lie within 1.2 K and the spread is 6 % lower. These small differences come from the can's end caps, which carry heat from the ends of the roll to the side.

Cooling the ends at the paper's own h = 400 W/(m^2 K) changes this. At 2C and minus 5 C:
- **The axial difference the radial model cannot see** is 37 % of the radial core-to-surface difference in the M50 (1.28 of 3.45 K) and 32 % in the 4680 (3.44 of 10.61 K). These fractions do not change with the rate, the ambient, the heat input, or the time within the discharge. With the two tab strips added the M50's rises to 43 %.
- **The per-unit offset.** The radial model puts every unit too warm. In the M50 the offset is 0.48 to 1.59 K (mean 1.19 K), with 31 of 45 units off by more than 1 K. In the 4680 it is 1.95 to 11.34 K (mean 7.96 K).
- **The spread.** The radial model overstates the unit-to-unit spread by 36 % in the M50 (4.17 against 3.06 K) and by 98 % in the 4680 (18.94 against 9.55 K). Over the six rates and ambients these figures are 34 to 36 % and 78 to 101 %.
- **Where the heat leaves.** The 4680's ends remove 38 % of the heat, against 19 % in the M50. The roll conducts heat along its 40 mm half-height more easily than across its 23 mm radius.

These are temperature offsets, not energy errors. The paper's surrogate would turn them into current and energy differences, and this study does not compute those.

The kelvin values belong to this study's heat (PyBaMM's Doyle-Fuller-Newman model, Chen2020 parameter set) and properties (O'Regan et al. 2022). They are not the paper's: the paper's own unit differences are larger (check V4). At 2C and minus 5 C the paper's discharge stops near 1.34 to 1.50 A h (its Fig. 4d), about 482 to 540 s, where its Fig. 5 shows 11.54 K from the innermost to the outermost unit. This study's radial model gives 3.22 to 3.26 K at those times, and its Chen2020 discharge runs on to 4.74 A h. At 1.25C and 2C at 25 C both discharges end near 4.6 to 5.0 A h, and there the paper's differences are 2.2 and 1.7 times this model's. The paper's heat is therefore larger, or its conductivity lower. What carries over is the axial-to-radial fraction.

Prediction scorecard: P1 held, P2 held, P3 failed, P4 held, P5 failed (details below).

## Stage 2 (v1.1.0): which of conductivity or heat makes the gap, and a one-term end correction

Stage 2 follows the author's second brief. Its predictions (`predictions_stage2.md`) were committed as 0cb04c3c3c88d8be015b4284bfb4fb142a447b47 and pushed at 06:37:48 UTC on 21 October 2026, after the values of the paper's ref. 33 were recorded (`inputs/ref33_values.md`, which the brief allows) and before any Stage 2 computation. DECISIONS.md D17 and D18 record its design. Stage 1's code and results are unchanged; Stage 2 adds new files only.

**What ref. 33 gives** (Yang and Tartakovsky, J. Power Sources 664 (2026) 238948). Its thermal model is the radial model Stage 1 assumed (D2; its Eqs. B.1 to B.4). Its thermal values are fitted, with four electrochemical values, to one 1C discharge of the same LG M50 (its Section 4.1 and Table 1): 0.62 W/(m K) across the layers and a diffusivity of 1.80e-7 m2/s, so rho c = 3.44e6 J/(m3 K), against O'Regan's 1.2251 W/(m K) and 2.48e6 J/(m3 K). Its fitted h, 29.56 W/(m2 K), belongs to its own experiment and is not used. Its untuned values are O'Regan's, which PyBaMM's ORegan2022 set holds (checked value by value).

**Part A, the split** (`results/stage2_ref33.csv`, `results/stage2_ref33.json`). The factor is the paper's innermost-unit difference (V4) over this radial model's innermost-minus-outermost unit difference.

| Condition | Factor, O'Regan's properties (Stage 1) | Property ratio | Factor, ref. 33's properties | Heat ratio | Remainder, ref. 33's properties and heat |
|---|---|---|---|---|---|
| 1.25C, 25 C, end of discharge | 2.16 | 1.92 | 1.13 | 1.37 | 0.82 |
| 2C, 25 C, end of discharge | 1.68 | 1.91 | 0.88 | 1.04 | 0.85 |
| 2C, minus 5 C, 482.4 s | 3.58 | 1.87 | 1.91 | 1.43 | 1.33 |
| 2C, minus 5 C, 540.0 s | 3.55 | 1.90 | 1.87 | 1.49 | 1.25 |
| 4680, 2C, minus 5 C, end of discharge | 1.98 | 1.73 | 1.14 | 0.71 | 1.61 |

- Ref. 33's properties raise this model's unit differences by a factor of 1.7 to 1.9 at every condition. At 25 C that closes the gap; with ref. 33's heat as well, this model's unit differences exceed the paper's by 15 to 18 %.
- Ref. 33's set, run in PyBaMM (D17), ends the 2C, minus 5 C discharge at 545 s and 1.51 A h, against the paper's 1.34 to 1.50 A h (its Fig. 4d). Its heat over the paper's window is 1.38 (to 482.4 s) and 1.40 (to 540.0 s) times Chen2020's. At 25 C it ends at 4.63 A h (1.25C) and 4.29 A h (2C).
- At 2C and minus 5 C, the properties supply a factor of 1.9, the heat a further 1.43 to 1.49, and 1.25 to 1.33 remains.
- The 4680 row is indicative only. Its heat is the 21700's history (D6), which with ref. 33's set stops at 545 s, while Stage 1's 4680 comparison is at 1706.7 s, so its heat ratio compares different states of discharge.

**Part B, the end correction** (`results/stage2_correction.csv`, `results/stage2_correction.json`). D18 derives the sink beta (T - T_amb) with beta = 2 h_e / L and 1/h_e = 1/h + L/(6 k_z): 9620 W/(m3 K) in the 21700 and 8247 W/(m3 K) in the 4680 at h = 400, and 705 W/(m3 K) in the 21700 at h = 25. Nothing is fitted. At 2C and minus 5 C, end of discharge:

| Quantity | 21700, case (b) | 4680, case (b) | 21700, case (d), h = 25 |
|---|---|---|---|
| Share of the heat through the ends, corrected against resolved | 18.8 against 18.6 % | 38.2 against 37.8 % | 13.6 against 13.5 % |
| Mean absolute unit offset, radial model to corrected | 1.19 to 0.10 K | 7.96 to 0.21 K | 4.08 to 0.16 K |
| Largest absolute unit offset, radial model to corrected | 1.59 to 0.16 K | 11.34 to 0.30 K | 4.29 to 0.24 K |
| Spread overstatement, radial model to corrected | 36 to 5 % | 98 to 3 % | 21 to 7 % |
| Axial difference at the core, reconstructed against resolved | 1.25 against 1.27 K | 3.49 against 3.43 K | 0.57 against 0.78 K |

- Over the six rates and ambients, the corrected mean offset is 0.03 to 0.20 K in the 21700 and 0.07 to 0.37 K in the 4680 in case (b), and 0.05 to 0.33 K in case (d). The spread overstatement is 5.0 to 5.1 % and 3.2 to 3.4 % in case (b), and 7.0 to 7.1 % in case (d). The reconstructed axial difference is 0.98 to 1.00 and 1.02 to 1.03 times the resolved one in case (b), and 0.72 to 0.74 times in case (d). In the 21700 the corrected share of heat through the ends lies within 0.19 percentage points of the resolved one at every heat in case (b) (resolved 18.6 to 18.7 %) and within 0.05 points in case (d) (resolved 13.5 %).
- The correction leaves the core-to-surface difference 4.6 % (21700) and 6.0 % (4680) below the resolved one in case (b): 3.29 against 3.45 K, and 9.98 against 10.61 K.
- B3, with ref. 33's properties (and O'Regan's along-layer conductivity, which ref. 33 does not give) at the paper's conditions: the correction lowers the innermost-minus-outermost unit difference by 29 to 31 % in the 21700 and by 41 % (ref. 33's heat) to 59 % (Chen2020's heat) in the 4680, for a cell whose ends are cooled as its side is.

**Checks.**
- V1: with beta = 0 the corrected model reproduces Stage 1's radial results exactly (difference 0.0 K).
- V2: energy closes to 2.3e-11 of the heat generated.
- V3: the code's steady solution matches the modified Bessel solution within 4.2e-6 K (21700) and 1.8e-6 K (4680), with steady end shares of 18.85 and 38.58 %.
- V4: the resolved shares come from the heat removed through each surface: `src/stage2_split.py` for the 21700 in cases (b) and (d) at every heat, and D15 for the 4680 at 2C and minus 5 C. The 4680's other five heats were not re-solved, for their computing time. The re-solves reproduce the registered end-of-discharge fields exactly.

**Stage 2 scorecard** (rules in `predictions_stage2.md`; `results/stage2_scorecard.json`).

| | Result | Computed |
|---|---|---|
| P1 | Held | ref. 33's conductivity is 1.98 times lower |
| P2 | Held | 1.91 and 1.87 with ref. 33's properties alone |
| P3 | Held | the ratio of the minus 5 C to the 25 C factor moves by +1.8 % and +0.4 % |
| P4 | Failed | ref. 33's heat is 1.38 and 1.40 times Chen2020's over the window, below the predicted 1.5 to 4 |
| P5 | Held | 0.18 and 0.46 percentage points |
| P6 | Held | 0.10 and 0.21 K |
| P7 | Held | 5.1 and 3.3 % |
| P8 | Held | 0.98 and 1.02 times the resolved |
| P9 | Held | 0.16 K |
| P10 | Held | 27 % low |

P2's reason, "the heat, not the conductivity, carries the low-temperature gap", does not hold as stated: at minus 5 C the properties supply a factor of 1.9 and the heat 1.4 to 1.5.

## Stage 3 (v1.2.0): ref. 33's core-temperature estimator against the resolved cell

Stage 3 follows the author's third brief. Its predictions (`predictions_stage3.md`) were committed as 70606633fa0f2669080ba6a0ba420fcea017f025 and pushed at 09:36:31 UTC on 27 October 2026, after the estimator was coded and checked and before any test run. DECISIONS.md D19 records the estimator as ref. 33 states it, D20 the implementation, with the author's choices of 27 October, and D21 what the independent read changed. Stage 1 and 2 code and results are unchanged.

**The estimator.** Ref. 33 estimates core temperature with an ensemble Kalman filter whose model error, a heat source per layer, is learned from the readings (its Section 3, Eqs. 4 to 9 and Algorithm 1). It gives 3000 members and a surface-temperature noise of 0.1 C, but no value for the model error's noise, the time step or the reading interval, and its core-temperature accuracy only in figures (`results/stage3_paper_numbers.json`). Here the forecast is Stage 1's radial model with the heat and properties of the resolved cell, so its only error is what the radial model leaves out. The reading is the resolved cell's mid-length surface temperature every 20 s with 0.1 K noise; the terminal voltage is not used, since neither model here has electrochemistry. The error's noise is bracketed at 0.1, 1 and 10 times 1.238e4 W/m3, the source that moves a unit by 0.1 K in one interval, and the middle level is registered. Truth is Stage 1's resolved field, itself a model.

**Results at the registered level** (`results/stage3_errors.csv`; core error, estimate minus the resolved centre node at mid-length, in K):

| Case | Forecast: mean abs., end | Estimator: mean abs., end | Estimator on the end-corrected forecast: mean abs., end |
|---|---|---|---|
| 21700, 1.25C, 25 C, ends insulated | 0.047, 0.059 | 0.045, 0.061 | as the estimator |
| 21700, 1.25C, 25 C, ends cooled | 0.293, 0.373 | 0.284, 0.364 | 0.040, 0.054 |
| 21700, 2C, 25 C, ends insulated | 0.114, 0.157 | 0.110, 0.151 | as the estimator |
| 21700, 2C, 25 C, ends cooled | 0.715, 0.990 | 0.693, 0.959 | 0.100, 0.134 |
| 21700, 2C, minus 5 C, ends insulated | 0.143, 0.187 | 0.139, 0.176 | as the estimator |
| 21700, 2C, minus 5 C, ends cooled | 0.901, 1.178 | 0.874, 1.137 | 0.125, 0.154 |
| 4680, 2C, minus 5 C, ends cooled | 6.89, 10.21 | 6.62, 9.74 | 0.236, 0.314 |

- With the ends cooled, the estimator leaves the core close to where the forecast put it: it removes 2 to 5 % of the end-of-discharge miss at the registered level. At ten times that level it removes 59 % in the M50 at 2C and minus 5 C (0.48 K left) and 42 % in the 4680 (5.93 K left); at a tenth, under 0.1 %.
- The learned error, the posterior heat source averaged over the cell and over the second half of the discharge, is 1.4 to 1.7 % of the end sink of D18 on the same history in the three cooled M50 cases (for example -652 against -38 656 W/m3 at 2C and minus 5 C), 36 to 44 % at ten times the level, and under 0.02 % at a tenth.
- On Stage 2's end-corrected forecast the same estimator has mean errors of 0.04 to 0.13 K in the cooled M50 cases and 0.14 to 0.24 K in the 4680 across the bracket (0.24 K at the registered level).
- Sensitivity (2C, minus 5 C, cooled ends, M50; `results/stage3_sensitivity.json`): noise of 0.05, 0.1 and 0.2 K gives mean errors of 0.81, 0.87 and 0.89 K; readings every 10, 20 and 40 s give 0.874, 0.874 and 0.872 K. With ref. 33's fitted properties in the forecast, the forecast misses by 3.71 K on average and the estimator by 3.68 K.

**Checks** (`results/stage3_checks.json`). V1: with a truth made by the radial model itself, the estimator recovers the core to 0.004 K on average (end 0.006 K); the paper gives no number to compare. V2: the forecast alone equals Stage 1's radial model to 6e-15 K. V3: the archived truth read by two routines is identical. V4: the same seed gives identical output, and with no model-error noise the estimator equals the forecast to 9e-16 K. An independent read, before the note was written, recomputed every error, the scorecard at all three levels and every row of the table from the stored histories, and P5 and P7 from the series kept for them (`results/stage3_series.json`; the seven repeated runs reproduce the stored values bit for bit), and found no registered value or verdict wrong (`verification/stage3_independent_read/`). It found two mislabelled fields in the stored runs, corrected under D21, and checked every number in this section, the note and the archive description against the files.

**Stage 3 scorecard** (rules in `predictions_stage3.md`; `results/stage3_scorecard.json`).

| | Result | Computed (registered level; bracket) |
|---|---|---|
| P1 | Held | forecast within 0.06, 0.16 and 0.19 K throughout; estimator 0.045, 0.110 and 0.139 K (held across the bracket) |
| P2 | Held | forecast end miss 1.18 K |
| P3 | Failed | the estimator leaves 1.14 K, 97 % of the miss (held only at ten times the level: 41 %) |
| P4 | Held | 0.04 against 0.28, 0.10 against 0.69, 0.13 against 0.87 and 0.24 against 6.62 K (held across the bracket) |
| P5 | Failed | learned error 1.4 to 1.7 % of the end sink (36 to 44 % at ten times the level) |
| P6 | Held | forecast end miss 10.2 K; the estimator leaves 9.7 K (5.9 K at ten times the level) |
| P7 | Held | doubling the noise raises the mean error by 0.02 K |

## Stage 4 (v1.3.0): the current each unit draws

Stage 4 follows the author's fourth brief. Its predictions (`predictions_stage4.md`) were committed as 895bd6510128f550a3cff626cdba7c1cad74fc29 and pushed at 04:06:15 UTC on 29 October 2026, before any Stage 4 computation. DECISIONS.md D22 to D25 record the procedure and the author's three choices of 29 October: the re-solve for unit histories, area weights, and P6's expectation. Stage 1 to 3 code and results are unchanged.

**The question.** The multi-unit model gives each unit its own temperature so that each unit draws its own current. Stage 4 carries the radial field's thermal error to that current. Each unit is put at the temperature that the radial, resolved and end-corrected fields give it. The question is what share of the current it then draws in parallel with the others.

**Unit temperatures.** The archive holds every unit's temperature at the end of discharge only. The three thermal models were therefore run again for the five cases with Stage 1 and 2 code unchanged, saving every unit every 10 s (`src/stage4_units.py`). The end values equal the archive exactly; the 4680's resolved run, which uses a conjugate-gradient solver, agrees to 4e-15 K. The registered reading is each unit's time average over the discharge; the end of discharge is a bracket.

**Resistance against temperature** (`src/stage4_RT.py`, `results/stage4_RT.csv`):
- R(T) is the whole cell's resistance from a 1C (5 A) pulse of 10 s after a 600 s rest, in PyBaMM's isothermal Doyle-Fuller-Newman model.
- It starts from 100 % state of charge on the rated 2.5 to 4.2 V window. PyBaMM's ORegan2022 places 100 % at 4.4 V, so it is set to 4.2 V, as the lever study did.
- It is tabulated every 0.5 K from minus 10 to 35 C, for ORegan2022 (main) and Chen2020 (bracket), with 50 % state of charge as a further bracket.
- Values at minus 5, 0 and 25 C: ORegan2022 48.75, 43.49 and 23.57 mOhm, with d ln R/dT of -0.0223, -0.0234 and -0.0237 per K. Chen2020 52.24, 49.57 and 37.33 mOhm, with -0.0104, -0.0106 and -0.0121 per K.
- O'Regan et al. measured the kinetics from 15 to 45 C and solid diffusion from 5 to 45 C (ChemRxiv preprint, Table 2). The minus 5 C cases therefore use ORegan2022's Arrhenius fits below their data. Chen2020's activation energies come from impedance at room temperature to 60 C.

**The share.** At a common voltage each unit's current density is proportional to 1/R at its temperature. A unit's share is that current density over the cell's mean (D24). The units are equal-thickness annuli, so their electrode areas grow with radius: the outermost 21700 unit has 89 times the innermost's. Means are therefore area-weighted, and the brief's unweighted formula is kept as a bracket. The share is instantaneous: units that draw more current deplete faster, a redistribution the multi-unit model carries and this proxy does not.

**Results at the registered choices** (ORegan2022, 100 % state of charge, time-averaged temperatures, area weights; `results/stage4_errors.csv`). Spread is the largest unit share minus the smallest, in % of the mean current density; pp is percentage points of it.

| Case | Resolved: spread, unit-mean R | Radial: spread error, R error | Radial: innermost, outermost share error | End-corrected: spread error, R error |
|---|---|---|---|---|
| M50, 2C, minus 5 C, ends cooled | 5.54 %, 45.69 mOhm | +36.4 %, -1.73 % | +1.11, -0.91 pp | +5.2 %, -0.13 % |
| M50, 2C, 25 C, ends cooled | 4.45 %, 22.34 mOhm | +34.3 %, -1.38 % | +0.83, -0.70 pp | +5.0 %, -0.11 % |
| M50, 1.25C, 25 C, ends cooled | 1.81 %, 23.07 mOhm | +35.6 %, -0.58 % | +0.35, -0.30 pp | +5.1 %, -0.04 % |
| M50, 2C, minus 5 C, ends insulated | 7.04 %, 45.00 mOhm | +7.3 %, -0.24 % | +0.28, -0.23 pp | as the radial field |
| 4680, 2C, minus 5 C, ends cooled | 16.94 %, 42.01 mOhm | +95.1 %, -9.64 % | +9.30, -6.80 pp | +3.3 %, -0.27 % |

- **The spread error follows the temperature-spread error.** In the three cooled M50 cases the share-spread error is within 1.1 points of the overstatement of the units' time-averaged temperature spread (35.2 to 35.9 %), and with the ends insulated it is 7.3 % against 7.2 %. In the 4680 it is 95 % against a temperature-spread overstatement of 88 %.
- **The set changes the size of the shares, not the error.** Under Chen2020, whose resistance is less than half as sensitive to temperature at minus 5 C and full charge, the errors are 36 % (M50) and 93 % (4680), within 2 % of ORegan2022's. The share spread is about half as large: the M50's resolved spread is 2.5 % against 5.5 %.
- **The cell's resistance moves much less.** The radial field underestimates the unit-mean resistance by 0.6 to 1.7 % in the cooled M50 cases and by 9.6 % in the 4680. The area-weighted time-averaged units are 0.76 K too warm in the main case and 4.33 K too warm in the 4680.
- **Across cases.** From 25 C to minus 5 C at 2C, the resistance error grows from 1.38 to 1.73 % and the spread error stays between 34 and 36 %. From 1.25C to 2C at 25 C, the resistance error grows from 0.58 to 1.38 %. From the M50 to the 4680, the spread error grows 2.6 times and the resistance error 5.6 times.
- **The end correction** removes 85 to 97 % of every error in the four cooled cases: 85 to 97 % of the spread error and 92 to 97 % of the resistance error.
- **With the ends insulated** the spread error is 7.3 %, the radial field's 7.2 % wider time-averaged temperature spread.
- **Brackets.** 50 % state of charge, end-of-discharge temperatures and unweighted means give the same verdicts. Across them, the main case's spread error is 35.9 to 37.6 % and its resistance error -1.88 to -2.26 %.

**Checks.** V1 (`results/stage4_unit_temps.json`): the end values equal the archive, as above. The unit-mean offsets and spread overstatements computed from them equal Stage 2's stored values bit for bit, and Stage 1's insulated-ends table.
- V2 (`results/stage4_checks_v2.json`): separate code gives R within 0.0001 % at minus 5, 0 and 25 C for both sets. It applies the current as a current function, takes the voltage before the pulse from the electrode potentials, and uses a solver tolerance 100 times tighter.
- V3 (`results/stage4_checks_v3.json`): the main case's shares, recomputed with explicit loops, agree within 5e-7.
- V4: both states of charge, both readings and both weightings are in `results/stage4_errors.csv` for every case.
- Independent read (`verification/stage4_independent_read/`, D26). The note's Stage 4 section was drafted while the read ran and added to the note only after it had found nothing wrong; a later text pass corrected one number and several statements in the README, the note, the archive text and the read's own record. A separate agent recomputed:
  - every reading, re-solving the one-dimensional models itself;
  - every row of the errors and units tables;
  - the scorecard at every bracket;
  - seven R(T) points, by PyBaMM routes of its own.
  It found nothing wrong.

**Stage 4 scorecard** (rules in `predictions_stage4.md`; `results/stage4_scorecard.json`). Every verdict is the same at every bracket (P6 has no verdict under Chen2020, by its own rule).

| | Result | Computed (registered; range across the brackets) |
|---|---|---|
| P1 | Held | radial spread error +36.4 % (35.8 to 37.6 %) |
| P2 | Held | end-corrected spread error +5.2 % (5.1 to 5.2 %) |
| P3 | Failed | radial resistance error -1.73 % (-0.80 to -2.26 %; needs below -4 %) |
| P4 | Held | -1.38 % at 2C and 25 C (-0.74 to -1.87 %) |
| P5 | Failed | 4680 +95.1 % against the M50's +36.4 %: 2.61 times (2.50 to 2.80; needs 3) |
| P6 | Failed | Chen2020 over ORegan2022 for the five quantities: 0.99, 0.99, 0.46, 0.54, 0.98 (each needs below 0.5); expectation registered as unlikely |
| P7 | Failed | ends insulated: spread error +7.3 % (needs below 1 %); resistance -0.24 %, innermost +0.28 and outermost -0.23 pp |

## Stage 5 (v1.4.0): the multi-unit model with a resolved thermal field

Stage 5 follows the author's fifth brief. Its predictions (`predictions_stage5.md`) were committed as e436c25317dfcbcbdc0950d36b0412833269d4c8 and pushed at 12:08:45 UTC on 16 November 2026, after Part A0 (D27 and D28: the paper's statements, the cell's specification, the linearity of the thermal models and the cost test) and before any kernel was computed or any coupled solve was run. DECISIONS.md D27 to D34 record the procedure. D27 records two facts found in single-cell runs before the predictions, and the author's choice, after reading them, to keep ORegan2022 registered. D35 records what was found after the predictions. Stage 1 to 4 code and results are unchanged.

**The question.** Stage 4 carried the radial field's error to the current each unit draws through a proxy: a resistance at each unit's time-averaged temperature. Stage 5 solves the multi-unit model itself. The units are Doyle-Fuller-Newman models at one terminal voltage, each at its own temperature, each heating the cell with its own heat. With it, Stage 5 reads three things under each thermal model: the paper's headline, the single-unit model's discharge-energy penalty; how well Stage 4's proxy did; and, on charge, the plating margin and the largest rate that keeps it.

**What it found.** Five of the nine predictions held (scorecard below). Checks V3 and V4 failed on some of their readings (below). After the predictions, PyBaMM's default particle mesh was found not to resolve the registered parameter set, ORegan2022 (below, and D35). Every ORegan2022 reading belongs to that mesh and is reported as registered. Chen2020, the bracket, settles at that mesh in every quantity checked, and under it:
- The single-unit model's discharge-energy penalty is at most 0.05 % in every case under every thermal model, and the thermal model changes it by at most 0.033 percentage points. The paper's 3.45 to 11.45 % come from its own parameters and properties and are set beside these as context only.
- The thermal model still sets how unevenly the units share the current. The radial field makes the coupled spread of the shares 31 to 36 % too wide in the cooled M50 cases and 84 % too wide in the 4680, close to Stage 4's proxy (36 and 93 %), and the end correction leaves 3 to 5 %. The spread itself is a fifth to a third of the proxy's in Stage 4's five cases, because units that draw more current deplete faster. Before the end of every discharge the innermost group's share falls below the mean.
- On charge at the specification's two limits the plating margin lies within 3 mV of zero: minus 1.31 to minus 1.35 mV at 0.3C and 0 C, and plus 0.83 to plus 0.92 mV at 0.7C and 25 C, in the coupled M50. The outermost group holds it in every case, and in the coupled model the thermal model moves it by at most 0.1 mV in the M50 and 0.5 mV in the 4680. The M50's plating-limited rates are 0.29C, 0.43C and 0.71C at 0, 10 and 25 C. Every kernel gives them, for the single-unit and the coupled model alike, within the search's 0.00625C. The specification allows 0.3C up to 25 C and 0.7C from 25 C.

Under ORegan2022 with the registered mesh the discharges end early: 170 s into the main case, against 1,707 s under Chen2020. Whether a discharge gets past that early end can turn on a fraction of a kelvin. In the M50 at 3C and 25 C the end-corrected field's innermost group is 0.2 K warmer than the resolved field's at 270 s, and its coupled discharge goes on to 604 s while the single-unit model stops at 278 s, a penalty of minus 49 %; under the resolved kernel both stop near 280 s. In the 4680 under the radial kernel, whose core runs 19 K above the outermost group by 331 s, the coupled discharge goes on to 843 s while the single-unit model stops at 363 s, a penalty of minus 54 %. Elsewhere, with two-way heat, the penalty lies between minus 1.0 and plus 0.6 % in the M50. Under the resolved field the 4680's discharge ends at 333 s with a penalty of plus 0.38 %; over the discharge its groups draw between 1.5C and 3.0C (1.8C to 2.3C at its end), and the paper's 4680 units draw 1.25C to 2.75C (its Fig. 8).

**The kernels** (`src/stage5_kernels.py`, `results/stage5_kernels/`). The three thermal models are linear in the heat: constant properties, a fixed ambient and no radiation (D27). A unit's temperature under any heat history is therefore the convolution of the history's increments with a step response computed once.
- The 45 units of the M50 are gathered into 15 groups of 3, and the 111 of the 4680 into 15 groups of 7 or 8 (D28).
- Each group is heated in turn at 1 W/m^3 over its annulus and the full height, and every unit's response is recorded on each model's own solver steps.
- In the resolved cell the group's heat is the integral of the basis functions over the part of the mesh inside the annulus: exact on the triangles wholly inside one group, and by adaptive subdivision on those the group's boundary cuts (D29, D35).
- The convolution reproduces each solver step by step: the kernels give Stage 4's unit temperatures in its five cases within 9.5e-7 K at every archived time (P1).
- A group's heat is uniform over its annulus and the full height. A real roll's heat varies along the height, with the tabs, and that is left out (D29).

**The coupled solve** (`src/stage5_coupled.py`). Fifteen copies of PyBaMM's DFN share one terminal voltage. Each copy is PyBaMM 26.9.0.0 with D23's isothermal options plus the heat, at its group's temperature. The area-weighted sum of their currents is the applied current.
- The voltage and the currents are unknowns of one differential-algebraic system, which IDAKLU's Newton iteration solves at every internal step.
- The system advances one thermal step at a time. Each group's temperature is held over the step, and its heat at the step's end enters the convolution.
- Under two-way heat (registered) each group's heat is its own. Under one-way heat every group takes the registered Chen2020 heat of Stages 1 to 4, which gives Stage 4's temperatures.
- The single-unit model is one DFN at the area-weighted mean temperature of the same thermal model, under the same heat rule, as the paper defines it (p. 3).

**Found after the predictions: the registered set needs a finer particle mesh** (D35, `src/stage5_posthoc_mesh.py`, `results/stage5_posthoc_mesh.json`; post hoc, not scored). D30 registered PyBaMM's default mesh, 20 points along each particle's radius. Under ORegan2022, one cell's DFN held at the ambient on the same window is far from settled at that mesh:

| Points per particle radius | 20 (registered) | 40 | 80 | 160 | 320 |
|---|---|---|---|---|---|
| 2C discharge at 25 C: cut-off | 978 s | 1,282 s | 1,456 s | 1,468 s | |
| 2C discharge at minus 5 C: cut-off | 126 s | 121 s | 141 s | 186 s | 247 s |
| 0.3C charge at 0 C: smallest margin | -193.6 mV (stops at 3.14 A h) | +19.1 mV | +19.7 mV | +19.6 mV | |
| 0.7C charge at 25 C: smallest margin | -237.3 mV (stops at 2.84 A h) | +27.4 mV | +28.6 mV | +28.6 mV | |
| Plating-limited rate at 0, 10, 25 C (cell at the ambient) | 0.280C, 0.369C, 0.536C | 0.405C, 0.618C, 1.024C | 0.430C, 0.670C, 1.228C | | |

- The cause is ORegan2022's graphite diffusivity, a fit that varies about 500-fold with stoichiometry. Twenty points along the radius do not resolve the steep concentration profiles it produces.
- Chen2020, whose diffusivity is constant, settles at 20 points in every row: discharges within 0.21 s, margins within 0.011 mV, rates within 0.001C.
- Every ORegan2022 reading below therefore belongs to the 20-point mesh. The second fact of D27, the negative surface reaching its limit at both of the specification's charge limits, belongs to that mesh: with 40 points or more the margin stays positive to 4.2 V at both limits. The minus 5 C discharges under ORegan2022 have not settled at any mesh tried. D36 (below) runs the coupled model under ORegan2022 with 160 points, post hoc.
- Stage 4's pulse resistances move by 3.0 to 5.3 % with the mesh, and their temperature sensitivity, which sets the shares, by 0.2 % (ORegan2022) and 4 % (Chen2020).

**Discharge** (`results/stage5_discharge.csv`, `results/stage5_shares.csv`, `results/stage5_summary.md`). Two-way heat. The penalty is the single-unit model's energy to 2.5 V over the coupled model's, less one; positive means the single-unit model gives more, as in the paper. The spread is the largest group share minus the smallest, time-averaged over the coupled discharge, in % of the cell's mean current density; its error is the radial or end-corrected kernel's against the resolved kernel's.

Under Chen2020 (settled at the registered mesh):

| Case | Penalty: radial, resolved, end-corrected | Resolved: spread | Spread error: radial, end-corrected | Innermost share below the mean from |
|---|---|---|---|---|
| M50, 2C, minus 5 C, ends cooled | +0.0033, +0.0018, +0.0020 % | 0.71 % | +35.0 %, +5.2 % | 1,353 s (of 1,707 s) |
| M50, 2C, 25 C, ends cooled | +0.0018, +0.0010, +0.0011 % | 0.48 % | +34.5 %, +5.1 % | 1,361 s (of 1,724 s) |
| M50, 1.25C, 25 C, ends cooled | +0.0002, +0.0001, +0.0001 % | 0.29 % | +35.9 %, +5.2 % | 2,219 s (of 2,852 s) |
| M50, 2C, minus 5 C, ends insulated | +0.0033, +0.0029 % | 0.89 % | +7.3 % | 1,354 s (of 1,708 s) |
| 4680, 2C, minus 5 C, ends cooled | +0.0467, +0.0143, +0.0153 % | 2.03 % | +83.9 %, +3.2 % | 1,359 s (of 1,710 s) |
| M50, 3C, 25 C, ends cooled | -0.0075, -0.0043, -0.0049 % | 0.52 % | +31.5 %, +5.0 % | 479 s (of 558 s) |

Under ORegan2022 (registered; the 20-point mesh):

| Case | Penalty: radial, resolved, end-corrected | Coupled cut-off: radial, resolved | Resolved: spread | Spread error: radial, end-corrected |
|---|---|---|---|---|
| M50, 2C, minus 5 C, ends cooled | -1.00, -0.36, -0.39 % | 189, 170 s | 6.08 % | +37.9 %, +5.5 % |
| M50, 2C, 25 C, ends cooled | +0.62, -0.25, -0.43 % | 1,055, 783 s | 6.01 % | +94.1 %, +4.6 % |
| M50, 1.25C, 25 C, ends cooled | +0.05, -0.05, -0.03 % | 2,290, 2,276 s | 2.42 % | +35.5 %, +2.4 % |
| M50, 2C, minus 5 C, ends insulated | -1.00, -0.83 % | 189, 185 s | 7.72 % | +8.6 % |
| 4680, 2C, minus 5 C, ends cooled | -53.53, +0.38, +0.44 % | 843, 333 s | 21.90 % | +141.6 %, +0.6 % |
| M50, 3C, 25 C, ends cooled | -0.68, -0.73, -48.92 % | 615, 280 s | 9.26 % | +97.6 %, +77.0 % |

With the ends insulated the end-corrected model is the radial model (D29).
- **Under Chen2020 the penalty is small.** It is at most 0.0075 % in size in every M50 case and below 0.05 % in the 4680. The radial kernel gives the largest penalty in size in every case, but the thermal model moves the penalty by at most 0.033 percentage points. The paper's 3.45 % (3C, 25 C), 11.32 % (2C, minus 5 C) and 11.45 % (the 4680) come from its own parameters and thermal properties, whose unit differences Stage 2 found 1.7 to 3.6 times this model's.
- **The shares carry Stage 4's thermal error.** Under Chen2020 the radial kernel's spread error is 31.5 to 35.9 % in the cooled M50 cases, 7.3 % with the ends insulated and 83.9 % in the 4680; Stage 4's proxy gave 36, 7 and 93 % under that set. The end correction leaves 3.2 to 5.2 %. Under one-way heat, the condition of P2, the radial kernel's spread is 25.9 % above the resolved kernel's under ORegan2022 and 35.7 % under Chen2020.
- **The redistribution the proxy leaves out.** The innermost group's share first rises above the mean and the outermost's falls below it; as the units that draw more current deplete faster, both cross back. Under Chen2020 they do so before the end of every discharge; under ORegan2022 the discharges at minus 5 C end before they do, except the 4680's under two-way heat. Under one-way heat, the proxy's own heat, the coupled spread under Chen2020 is 20 to 31 % of Stage 4's proxy in its five cases (main case: 0.72 % against 2.54 %), and 21 to 32 % of the proxy evaluated at group level over the same window; at 3C, which Stage 4 did not run, it is 11 % of the latter. Under ORegan2022, whose discharges end in a fraction of the archive's time, the coupled spread under the resolved kernel is 1.27 to 1.68 times the group-level proxy over the coupled run's own window (main case: 3.63 % against 2.86 %), and 0.66 times Stage 4's registered 5.54 % (P3).
- **The 4680 under ORegan2022 and the radial kernel.** With two-way heat the radial field puts the 4680's core far above the resolved field's, and under ORegan2022's temperature sensitivity the inner groups then draw ever more current: the innermost group's temperature, from minus 5 C, reaches 21 C after 331 s and 28 C after 600 s, while the outermost stays below 4 C, and the group currents span 0.98C to 4.54C. The coupled discharge runs to 843 s, while the single-unit model at the mean temperature stops at 363 s.
- **Per-group heat.** In the main case under the resolved kernel, giving each group its own heat changes the time-averaged spread of the unit temperatures by plus 2.8 % (ORegan2022) and minus 0.3 % (Chen2020) against the same total heat spread uniformly (P6).
- **Ranges.** Minus 5 C lies outside both sets' measured ranges (D23), so every minus 5 C number extrapolates the set.

**Charge** (`results/stage5_charge.csv`, `results/stage5_limit.csv`). Constant current from 0 % to 4.2 V with the ends cooled and two-way heat. The margin is the smallest value of the negative electrode's solid potential less the electrolyte's, over the charge, the electrode's thickness and the groups (D32). It is a thermodynamic indicator, not an amount of plated lithium. 0 C lies below ORegan2022's measured ranges for the kinetics (15 C) and solid diffusion (5 C), and 10 C below the first. The rates describe this parameter set, an energy cell, which the 4680 inherits as the paper assumes; they do not describe a fast-charging cell.

At the specification's limits (coupled model; the single-unit model under the resolved kernel in brackets), mV:

| Cell, charge | Chen2020: radial, resolved, end-corrected | ORegan2022 (20 points): radial, resolved, end-corrected |
|---|---|---|
| M50, 0.3C at 0 C | -1.31, -1.35, -1.35 (-1.31) | -192.83, -192.99, -192.98 (-192.73) |
| M50, 0.7C at 25 C | +0.92, +0.83, +0.84 (+0.98) | -236.50, -236.66, -236.66 (-236.41) |
| 4680, 0.3C at 0 C | -0.92, -1.17, -1.16 (-1.02) | -191.39, -192.31, -192.30 (-191.42) |
| 4680, 0.7C at 25 C | +1.69, +1.19, +1.19 (+1.67) | -235.22, -236.02, -236.01 (-235.21) |

The plating-limited rate, the largest rate whose margin stays at or above zero to 4.2 V, in the specification's C (4.85 A in the M50; the 4680 at the same current per unit area). Each search brackets the rate to 0.00625C; P9's four rates are refined to 0.001C (marked *):

| Cell, ambient | Chen2020: single-unit, radial / resolved / end-corrected | Chen2020: coupled | ORegan2022 (20 points): single-unit | ORegan2022: coupled |
|---|---|---|---|---|
| M50, 0 C | 0.2875 / 0.2875 / 0.2875 | 0.28625 / 0.28625 / 0.28625 | 0.28125 / 0.28125* / 0.28125 | 0.28 / 0.28156* / 0.28 |
| M50, 10 C | 0.43125 / 0.43125 / 0.43125 | 0.43 / 0.43 / 0.43 | 0.36875 / 0.36875 / 0.36875 | 0.36625 / 0.36625 / 0.36625 |
| M50, 25 C | 0.7125 / 0.7125 / 0.7125 | 0.71 / 0.71 / 0.71 | 0.5375 / 0.5375 / 0.5375 | 0.53625 / 0.53625 / 0.53625 |
| 4680, 0 C | 0.29375 / 0.2875 / 0.2875 | 0.29 / 0.28625 / 0.28625 | 0.28125 / 0.28281* / 0.28125 | 0.28 / 0.28234* / 0.28 |
| 4680, 10 C | 0.44375 / 0.4375 / 0.4375 | 0.43375 / 0.43 / 0.43 | 0.375 / 0.36875 / 0.36875 | 0.37 / 0.3725 / 0.3725 |
| 4680, 25 C | 0.7375 / 0.71875 / 0.71875 | 0.7175 / 0.71 / 0.71 | 0.54375 / 0.5375 / 0.5375 | 0.54625 / 0.53625 / 0.53625 |

- **The outermost group holds the margin** in every charge case under Chen2020, including the brackets outside the specification (0.7C at 0 C: minus 41 to 42 mV; 1C at 25 C: minus 14 to 15 mV; 2C at 25 C: minus 71 to 75 mV), and in every registered case under ORegan2022 (P8). Under ORegan2022 the innermost group holds it at 0.7C and 0 C and at 2C and 25 C in both cells, and at 1C and 25 C in the 4680 under the radial kernel, at minus 253 to minus 297 mV.
- **At the specification's limits the thermal model barely moves the margin.** Under Chen2020 the coupled model's margin under the radial kernel lies 0.04 to 0.09 mV above that under the resolved kernel in the M50 and 0.25 to 0.50 mV above it in the 4680; the end correction is within 0.01 mV of the resolved. In the single-unit model the radial kernel moves it by up to 0.14 mV (M50) and 0.93 mV (4680). The coupled model's margin lies 0.04 to 0.20 mV below the single-unit model's in the M50 and up to 0.9 mV below it in the 4680. At 2C and 25 C, outside the specification, the radial kernel's coupled margin lies up to 0.48 mV (M50) and 2.37 mV (4680) above the resolved kernel's, and the coupled model's margin up to 1.35 and 6.09 mV below the single-unit model's.
- **The rates.** Under Chen2020 the M50's rates are the same under every kernel, and the single-unit and coupled brackets overlap at every ambient. In the 4680 the coupled model's rate lies 0.0075 to 0.02C below the single-unit model's at 10 and 25 C, where the brackets do not overlap, and the radial kernel raises the single-unit rate at 25 C from 0.719C to 0.738C. Under Chen2020 the specification's two limits lie at this model's plating-limited rates: 0.3C against 0.29C at 0 C, and 0.7C against 0.71C at 25 C.
- **Under ORegan2022 the rates belong to the mesh.** At 20 points they are set by the barrier at the stoichiometric limit (D27); one cell at the ambient gives 0.40C, 0.62C and 1.02C with 40 points and 0.43C, 0.67C and 1.23C with 80, so they have not settled. The single-unit and coupled brackets overlap in every case. At 0 C, P9's refined rates are 0.28125C (single-unit) and 0.28156C (coupled) in the M50, and 0.28281C and 0.28234C in the 4680: equal within 0.001C in both cells, so the 4680's difference is not above 5 % and P9 failed. Under ORegan2022 the smallest margin of a passing charge is not always monotonic in the rate, but in all 72 searches pass and fail are (D35).

**Post hoc: the registered set at a settled particle mesh** (D36, `src/stage5_posthoc_settled.py`, `results/stage5_posthoc_settled/`). Run at the author's request after the results above. It is not scored, and no registered reading or verdict is replaced. One cell held at the ambient, as in D35's check, settles at 80 points per particle radius in six readings: each moves by less than 1 % from 80 to 160 points and on every later doubling computed. Its 2C discharge at minus 5 C settles only at 640 points:

| Points per particle radius | 20 (registered) | 40 | 80 | 160 | 320 | 640 | 1,280 |
|---|---|---|---|---|---|---|---|
| 2C discharge at 25 C: cut-off | 978 s | 1,282 s | 1,456 s | 1,468 s | 1,469 s | 1,470 s | |
| 0.3C charge at 0 C: smallest margin | -193.63 mV | +19.06 mV | +19.69 mV | +19.56 mV | +19.38 mV | +19.33 mV | |
| 0.7C charge at 25 C: smallest margin | -237.30 mV | +27.39 mV | +28.56 mV | +28.59 mV | +28.77 mV | +28.81 mV | |
| Plating-limited rate at 0 C | 0.280C | 0.405C | 0.430C | 0.430C | 0.430C | | |
| Plating-limited rate at 10 C | 0.369C | 0.618C | 0.670C | 0.671C | 0.673C | | |
| Plating-limited rate at 25 C | 0.536C | 1.024C | 1.228C | 1.239C | 1.236C | | |
| 2C discharge at minus 5 C: cut-off | 126 s | 121 s | 141 s | 186 s | 247 s | 258 s | 259 s |

The coupled and single-unit models were then run with 160 points in both particles, the author's choice among the meshes the coupled model can carry on this machine: the six readings are settled there, and the minus 5 C discharges are not. The readings below are at 160 points, with the registered 20-point value in brackets (ORegan2022, two-way heat):

| Case | Penalty: radial, resolved, end-corrected | Coupled cut-off: radial, resolved, end-corrected | Resolved: spread | Spread error: radial, end-corrected |
|---|---|---|---|---|
| M50, 2C, minus 5 C, ends cooled | -1.32 (-1.00), -0.84 (-0.36), -0.94 (-0.39) % | 496 (189), 418 (170), 424 (172) s | 9.63 (6.08) % | +33.8 (+37.9), +5.2 (+5.5) % |
| 4680, 2C, minus 5 C, ends cooled | +4.21 (-53.53), -5.56 (+0.38), -5.93 (+0.44) % | 1,245 (843), 888 (333), 910 (334) s | 28.57 (21.90) % | +22.9 (+141.6), +3.9 (+0.6) % |
| M50, 3C, 25 C, ends cooled | +0.20 (-0.68), +0.10 (-0.73), +0.12 (-48.92) % | 897 (615), 887 (280), 888 (604) s | 4.28 (9.26) % | +27.6 (+97.6), +4.7 (+77.0) % |

| Cell, charge | Margin, coupled: radial, resolved, end-corrected | Single-unit, resolved |
|---|---|---|
| M50, 0.3C at 0 C | +19.80 (-192.83), +19.75 (-192.99), +19.76 (-192.98) mV | +19.83 (-192.73) mV |
| M50, 0.7C at 25 C | +28.99 (-236.50), +28.92 (-236.66), +28.92 (-236.66) mV | +29.07 (-236.41) mV |

- **Where 160 points settle, the penalty is small.** At 3C and 25 C, the one of the paper's three cases that 160 points settle, the single-unit model gives 0.10 to 0.20 % more energy than the multi-unit model, against the paper's 3.45 %, and the thermal model moves the penalty by 0.1 percentage points. The three kernels' discharges end within 10 s of one another: the early ends that the 20-point mesh gave, and their sensitivity to a fraction of a kelvin, are gone.
- **At minus 5 C the readings have not settled.** There the penalty is -0.84 to -1.32 % in the M50 (the paper: 11.32 %) and -5.93 to +4.21 % in the 4680 (11.45 %). In the 4680 it reaches the paper's order in size, and the thermal model sets its sign: the radial field gives the paper's direction and the resolved and end-corrected fields the opposite one.
- **The shares.** The radial kernel makes the spread 27.6 to 33.8 % too wide in the M50 and 22.9 % in the 4680; the end correction leaves 3.9 to 5.2 %.
- **The margins at the specification's limits are positive**, about +20 mV at 0.3C and 0 C and +29 mV at 0.7C and 25 C, reached at 4.2 V and held by the outermost group in every case. The thermal model moves the coupled margin by under 0.1 mV (P7's reading: +0.05 and +0.08 mV, against +0.16 and +0.16 mV at 20 points).
- **How the runs were made.** A coupled step at 160 points costs about 4 to 50 times one at 20 points. Each run saves its state every 20 steps and resumes after the machine's two-hour limit on a job; the solver keeps only each step's first and last states, and the garbage collector runs after every step. None of these changes a result: a stored registered run made again with them is identical to it. Four runs were stopped by the memory limit or a guard and resumed from their saved states, among them the main case under the radial kernel, which stopped twice in one step before the storage was changed (D36).
- **Still running** when this was written: 2C at 25 C, the 4680's charges, P9's plating-limited rates, the insulated case and 1.25C at 25 C.

**Checks** (`results/stage5_checks.json`, `results/stage5_v5.json`, `results/stage5_p1.json`).
- V1: P1's comparison, worst 9.5e-7 K over every case, unit and archived time. Reciprocity (each group's mean taken with its own load as the weight): within 2.6e-14 of the largest value in all 34 kernels. The load-weighted group mean and the sampled group mean of D29 differ by up to 0.22 %. Every kernel reaches its discrete steady state within 1e-8.
- V2: with every group at the single-unit model's temperature, the coupled solve matches the single-unit model within 7.5e-7 V at every step and 1.3e-7 in capacity. Held.
- V3: the current balance closes within 5.7e-10 of the applied current in every stored coupled run (the searches' trials store their margins only). Halving the time step, with every kernel recomputed on the halved grid, changes the charge case's margins by under 0.002 % and the main case's spreads by under 0.8 %. It changes the main case's penalties under the radial and end-corrected kernels by 1.1 to 1.3 % of their values (at most 0.016 percentage points), above the 1 % limit; the energies and capacities behind them change by at most 0.15 %. V3 therefore failed on four of its 18 readings.
- V4: with 30 groups (1 or 2 units each in the M50), the main case's penalties change by 0.7 % of their values, and the charge case's margins by under 0.02 % and its charge by under 1e-7. Five of the six time-averaged spreads grow by 5.1 to 5.4 % and the sixth by 4.8 %, against the 5 % limit, much as D28 found for the group-level proxy (4.8 %): smaller groups resolve more extreme units. The radial kernel's spread error moves from 37.9 to 37.4 % (two-way heat) and from 25.9 to 25.5 % (one-way), and the end correction's stays at 5.4 to 5.5 % and 4.7 %. V4 therefore failed on five of its 18 readings.
- V5: the second route, separate DFNs in voltage mode with a secant search on the current balance at each step, agrees with the coupled solve within 0.037 % in every share at every step (limit 0.5 %). The voltages differ by up to 6.5 mV at the last full step.
- V6: the margin recomputed from the stored potentials by separate code agrees within 7e-9 V and finds the same group.

**Independent read** (`verification/stage5_independent_read/`). A separate agent that did not see the runs being made read the files in three passes, the last of them a reading of the texts, with scripts that import nothing from `src/`. It recomputed every row of the four tables (4,614 values) and replayed every search's trials under D32's rules. It scored the scorecard and its brackets, recomputed V1 to V4 and V6, including the failures of V3 and V4, and checked V5's stored second route against the coupled run. It also re-solved six of the 22 one-dimensional kernels with its own finite elements, and re-ran single DFNs with PyBaMM for two single-unit runs, the edges of P9's single-unit brackets and the mesh check. Every registered number and verdict reproduced. It found five statements in D35 that did not follow from the files (a cut-off time, a charge, a temperature sensitivity, the stoichiometry of a diffusivity and the example of a non-monotonic margin), three figures in D35 that held only to one significant figure, and that D29's subdivision depth is not the one the code used (D35). Its text pass found wordings and figures that went beyond the files in this section, the Files and How to run entries, the note, D35, the logs' README and the archive text. All were corrected before the release, except Stage 1's sentence that the study does not compute energy differences, which is kept as Stage 1's record.

**Stage 5 scorecard** (rules in `predictions_stage5.md`; `results/stage5_scorecard.json`). Verdicts are under ORegan2022 at the registered mesh. The Chen2020 column records whether each rule's condition holds under that set, without a verdict of its own.

| | Result | Computed (ORegan2022, registered) | Chen2020 |
|---|---|---|---|
| P1 | Held | worst 9.5e-7 K (needs below 0.01 K) | |
| P2 | Held | radial spread 25.9 % above the resolved (needs 25 to 45 %) | 35.7 %, met |
| P3 | Failed | 3.63 % against the proxy's 5.54 %: 34.5 % below (needs within 20 %) | 0.72 against 2.54 %: 71.8 % below, not met |
| P4 | Failed | radial -1.00 %, resolved -0.36 % (the radial penalty must be positive) | +0.0033 and +0.0018 %, met |
| P5 | Failed | radial -53.5 %, resolved +0.38 % (the radial penalty must be positive) | +0.047 and +0.014 %: 3.3 times, met |
| P6 | Held | +2.8 % (needs within 10 %) | -0.3 %, met |
| P7 | Held | +0.16 and +0.16 mV (needs below 2 mV) | +0.04 and +0.09 mV, met |
| P8 | Held | the outermost group in all 12 cases | all 12, met |
| P9 | Failed | M50 -0.11 %, 4680 +0.17 % (the 4680 needs above 5 %) | +0.44 % in both, at 0.00625C; not met |

## The question

Yang, Cui and Tartakovsky (J. Electrochem. Soc. 173 (2026) 050520, doi:10.1149/1945-7111/ae4b6d) resolve the 45 spiral units of an LG M50 cell at their own temperatures. They find that a single-unit model at the averaged temperature overestimates the discharge energy by 3.45 % at 3C and 25 C and by 11.32 % at 2C and minus 5 C, and that a 4680 at 2C and minus 5 C holds a temperature difference of more than 30 C. Each unit's temperature comes from a one-dimensional radial conduction model: zero flux at the core, convection with h = 400 W/(m^2 K) at the outer surface, and no axial conduction, end cooling or tabs.

In the M50 the jelly roll conducts about twenty times better along its layers than across them, so the path to the ends of the cell can matter as much as the path to its side. This study asks what the one-dimensional model leaves out under the paper's own conditions. The heat is held equal, and the paper's radial model is compared with a three-dimensional cell that has an anisotropic roll and a can. The study does not rerun the paper's electrochemistry. It measures the temperature field that the paper's model assumes.

## Pre-registration

The study follows the author's written brief: its question, inputs, design, checks, predictions and rules. "The brief" below means that document. Its predictions (`predictions.md`) were committed as b92f9a8de8db3af392edc67fa854c84248432dea and pushed to this public repository at 11:12:48 UTC on 12 October 2026. The first three-dimensional field of the study was written at 11:19 UTC. As the brief orders, the DFN heat runs and the one-dimensional model ran before the predictions commit, together with three-dimensional checks that compute no field of the study (`verification/v0_checks.json`).

Four things came after the predictions, and DECISIONS.md records them:
- **D13.** The first equivalence run (V1) failed by 1.7 %. On the two-cell study's mesh, a circumferential conductivity twenty times the radial one carries heat across the coarse triangles near the axis. Every field here is axisymmetric, so the circumferential conductivity cannot change the exact solution, and it was set to the radial value. V1 then passed within 0.15 %. The failed run is kept in `results/fields_superseded/`. With the original tensor, a mesh with every spacing halved cuts the error from 1.70 % to 0.51 %, which confirms it was discretisation error.
- **D14.** A fix to the field sampler for points on the cylinder's polygonal edge. It changes no physics.
- **D15.** A post-hoc re-solve at the paper's own end of discharge, with the heat split by surface.
- **D16.** What the paper's property source says about its properties, from the parts of it that were available. No input, code or result changed.

V4 also ran after the predictions, because the paper's figure images were found only then. V4 involves no three-dimensional field.

## Prediction scorecard

All are scored on the registered inputs at the end of discharge, at 2C and minus 5 C unless stated.

| | Prediction | Result | Computed |
|---|---|---|---|
| P1 | With side cooling only, the mid-height core-to-surface difference is 3 to 10 K (central 6 K) | Held | 4.12 K in (a) |
| P2 | End cooling changes it by less than 30 % (central 15 %) and creates an axial difference above a third of the radial (central 50 %) | Held | -16.2 %; 1.28 of 3.45 K, 0.37 |
| P3 | With end cooling the radial units exceed the resolved averages by 1 to 3 K (central 1.5 K), about equally, so the spread changes by less than 20 % | Failed | The mean offset (1.19 K) and the signs held. The spread falls 27 % (4.17 to 3.06 K). The offsets run from 0.48 to 1.59 K (reported, not scored) |
| P4 | The 4680's ratio of axial to radial difference is smaller than the 21700's (central 0.3 against 0.5) | Held | 0.32 against 0.37 |
| P5 | At h = 25 both differences are below 1 K at 2C | Failed | Radial 3.18 K (minus 5 C) and 2.62 K (25 C); axial 0.79 and 0.65 K |

P5 fails because the core-to-surface difference is set by the heat generated inside the roll and the roll's conductivity across the layers, far more than by h. A sixteen-fold lower h raises the whole cell to 31 K above ambient by the end of the minus 5 C, 2C discharge. The core-to-surface difference changes by only 8 %: 3.18 K against 3.45 K in (b). Every difference here peaks at the end of discharge, so the values at the time of the largest core-to-surface difference equal those at the end (`results/results_3d.csv` lists both).

## Results at 2C and minus 5 C, end of discharge (1706.7 s)

The registered heat is Chen2020: mean 3.81 W, q = 1.56e5 W/m^3 in the 21700 (predictions.md gives it as 1.55e5). The one-dimensional model is the paper's radial model with the same heat, properties and can. "Offset" means the one-dimensional unit temperature minus the resolved annulus average over the full height.

| Cell | Case | Core-to-surface at mid-height (K) | Axial, mid-height to end (K) | Axial / radial | Mean offset (K) | Offset range (K) | Units off by more than 1 K | Unit spread (K) |
|---|---|---|---|---|---|---|---|---|
| 21700 | radial model | 4.264 | none | none | | | | 4.169 |
| 21700 | (a) side cooled, ends insulated | 4.122 | 0.316 | 0.077 | 0.187 | 0.004 to 0.290 | 0 of 45 | 3.886 |
| 21700 | (b) side and ends at h = 400 | 3.453 | 1.283 | 0.371 | 1.187 | 0.477 to 1.586 | 31 of 45 | 3.060 |
| 21700 | (c) as (b) with the tab strips | 3.426 | 1.458 | 0.426 | 1.225 | 0.492 to 1.646 | 32 of 45 | 3.015 |
| 21700 | (d) as (b) at h = 25 | 3.180 | 0.786 | 0.247 | see below | | | 2.949 |
| 4680 | radial model | 19.113 | none | none | | | | 18.938 |
| 4680 | (a) side cooled, ends insulated | 18.173 | 0.401 | 0.022 | 0.784 | -0.004 to 1.202 | 45 of 111 | 17.736 |
| 4680 | (b) side and ends at h = 400 | 10.613 | 3.439 | 0.324 | 7.961 | 1.949 to 11.338 | 111 of 111 | 9.549 |

Notes on the table:
- **The hottest point** is on the axis at mid-height: z = 35.05 mm in the 21700 and 40.0 mm in the 4680. In (a) it sits one mesh layer higher (1.53 mm above mid-height) and is 6e-5 K warmer than the mid-height axis node.
- **(d)** holds the h = 400 heat while losing it at h = 25, so the cell runs 27 K warmer than (a). Against the radial model at the same h = 25 (side cooling only), its units are 4.08 K cooler on average, all 45 by more than 1 K.
- **Against (a)**, as the brief asks, (b) lowers the core-to-surface difference by 16 % and the unit temperatures by 1.00 K on average, 25 units by more than 1 K. In the 4680, (b) lowers the difference by 42 % and the unit temperatures by 7.18 K on average.
- **The 4680 count in (a)** is on the edge: one unit sits at 1.00 K, and the independent recomputation counts 44.
- **The axial difference** is the larger of mid-height minus base and mid-height minus cap (D10). In the symmetric cases the two ends differ by at most 0.024 K, and by at most 2.5 % of the axial difference, because the tetrahedral split of the mesh is not symmetric in height.

## Results at every rate and ambient (21700)

The core-to-surface difference at the end of discharge, in K, with the axial difference in (b) in brackets.

| Rate, ambient | Radial | (a) | (b) | (c) | (d) | (b): axial / radial; mean offset; units over 1 K |
|---|---|---|---|---|---|---|
| 1.25C, minus 5 C | 1.805 | 1.745 | 1.463 (0.543) | 1.451 | 1.427 | 0.371; 0.502 K; 0 |
| 2C, minus 5 C | 4.264 | 4.122 | 3.453 (1.283) | 3.426 | 3.180 | 0.371; 1.187 K; 31 |
| 3C, minus 5 C | 8.310 | 8.043 | 6.794 (2.515) | 6.742 | 4.416 | 0.370; 2.244 K; 43 |
| 1.25C, 25 C | 1.361 | 1.316 | 1.105 (0.410) | 1.096 | 1.052 | 0.371; 0.377 K; 0 |
| 2C, 25 C | 3.618 | 3.499 | 2.936 (1.090) | 2.913 | 2.618 | 0.371; 1.001 K; 26 |
| 3C, 25 C | 7.382 | 7.148 | 6.056 (2.239) | 6.011 | 3.853 | 0.370; 1.972 K; 41 |

In every case:
- (a)'s core-to-surface difference lies 3.2 to 3.3 % below the radial model's.
- (b)'s lies 15 to 16 % below (a)'s.
- The axial-to-radial ratio of (b) stays at 0.37.
- The spread in (b) is 26 to 27 % below the radial model's.

The offsets scale with the heat, at about 0.27 to 0.28 times the radial model's core-to-surface difference.

## Results at every rate and ambient (4680)

The core-to-surface difference at the end of discharge, in K, with the axial difference in (b) in brackets.

| Rate, ambient | Radial | (a) | (b) | (b): mean offset; units over 1 K; spread, radial against (b) |
|---|---|---|---|---|
| 1.25C, minus 5 C | 8.235 | 7.819 | 4.513 (1.463) | 3.47 K; 108 of 111; 8.16 against 4.06 K |
| 2C, minus 5 C | 19.113 | 18.173 | 10.613 (3.439) | 7.96 K; 111; 18.94 against 9.55 K |
| 3C, minus 5 C | 32.124 | 30.883 | 19.732 (6.405) | 12.02 K; 111; 31.81 against 17.76 K |
| 1.25C, 25 C | 6.122 | 5.816 | 3.378 (1.095) | 2.57 K; 102; 6.07 against 3.04 K |
| 2C, 25 C | 15.891 | 15.123 | 8.915 (2.890) | 6.55 K; 111; 15.74 against 8.02 K |
| 3C, 25 C | 27.959 | 26.893 | 17.301 (5.618) | 10.38 K; 111; 27.68 against 15.57 K |

In the 4680:
- (a)'s core-to-surface difference lies 3.8 to 5.1 % below the radial model's. Its largest unit offset is 0.39 to 1.62 K, depending on the rate and ambient.
- (b) lowers the core-to-surface difference by 38 to 45 % against the radial model.
- The axial-to-radial ratio of (b) stays at 0.32 (0.324 to 0.325).
- The spread in (b) is 44 to 50 % below the radial model's.

## At the paper's own end of discharge (post hoc, D15)

At 2C and minus 5 C the paper's discharge ends near 482 to 540 s. At those times:
- In (b) the axial-to-radial ratio is 0.37 in the M50 and 0.32 in the 4680, as at 1706.7 s. From 100 s to the end it stays within 0.368 to 0.372 and 0.324 to 0.334.
- The radial model overstates the spread by 36 % in the M50, as at the end, and by 77 to 82 % in the 4680, against 98 % at the end: the 4680 has not reached its quasi-steady profile by then.
- The mean offset in (b) is 0.92 to 0.93 K in the M50 (22 of 45 units over 1 K) and 4.79 to 5.17 K in the 4680.
- In (a) the units lie within 0.23 K (M50) and 0.70 K (4680) of the radial model.

The share of heat each surface removes over the whole discharge is in `results/posthoc_matched_time.json`.

## Heat generation (registered: Chen2020, lumped thermal model, h = 400 on the side)

| Rate, ambient | Duration (s) | Capacity (A h) | Mean heat (W) | Peak heat (W) | Lumped T at end (C) | Time at 2.6 V (s) |
|---|---|---|---|---|---|---|
| 1.25C, minus 5 C | 2835.0 | 4.922 | 1.669 | 2.006 | -3.94 | 2807.9 |
| 2C, minus 5 C | 1706.7 | 4.741 | 3.812 | 4.747 | -2.49 | 1673.8 |
| 3C, minus 5 C | 557.8 | 2.324 | 7.866 | 11.699 | 0.10 | 556.1 |
| 1.25C, 25 C | 2852.0 | 4.951 | 1.193 | 1.532 | 25.81 | 2830.0 |
| 2C, 25 C | 1723.5 | 4.787 | 3.040 | 4.109 | 27.14 | 1699.0 |
| 3C, 25 C | 558.3 | 2.326 | 6.777 | 11.248 | 29.60 | 557.5 |

**Early cut-off.** The DFN does not stop early at minus 5 C and 2C: it reaches 4.74 A h. The paper's discharge at that condition ends near 1.34 to 1.50 A h (its Fig. 4d). The two parameter sets run here bracket that: ORegan2022 stops after 166 s at 0.46 A h. At 3C the Chen2020 discharge stops at 2.32 and 2.33 A h, where the paper's 3C, 25 C discharge reaches 4.2 to 4.4 A h (its Fig. 4b). At that cut-off the electrolyte concentration has fallen to zero in part of the positive electrode, and some positive particle surfaces are full (stoichiometry 0.9998), while the positive particles hold 0.53 on average (`verification/cutoff_3c.json`).

**Warming.** With h = 400 on the side, the lumped cell warms by at most 5.1 K.

## Verification

- **V0** (before the predictions, no field of the study). Every operator annihilates a uniform field. Capacities, convective and strip conductances, and source weights reproduce the exact totals. A pure-conduction relaxation conserves energy to 4e-14 (`verification/v0_checks.json`). The 21700 mesh is the two-cell study's mesh node for node, and the field sampler reproduces the finite-element field to 3e-14 (`verification/test_mesh.py`).
- **V1.** With the can on the side only, the resolved mid-height profile matches the one-dimensional model within 0.147 % of the core-to-surface difference, for all six heat inputs at both output times (criterion 1 %). This holds after D13; before it, the error was 1.7 %.
- **V1, the brief's (a) row.** With the can's end caps in place, the mid-height profile deviates from the radial model by at most 4.3 to 4.5 % of the radial core-to-surface difference in the 21700 and 4.3 to 5.7 % in the 4680. This is the end caps' conduction to the side, not a bug, because the equivalence run has already tested the solver (D11).
- **V2.** The energy account of every resolved run (heat stored plus heat lost against heat generated) closes within 2.0e-12, and within 4.6e-13 in the 21700.
- **V3.** One mesh refinement (every spacing halved, 297,057 nodes) at 2C and minus 5 C:
  - The core-to-surface difference changes by -0.09 % in (a) (4.1224 to 4.1185 K) and -0.08 % in (b) (3.4531 to 3.4504 K), against the 5 % criterion.
  - The axial difference changes by -0.9 % and -0.3 %.
  - Every unit average changes by at most 0.004 K.
- **V4.** Digitised from the paper's embedded figure images (`verification/v4_digitise.py`, `verification/v4.json`, `verification/v4_digitised.csv`; reading errors 0.09 K for Fig. 5 and 0.29 K for Fig. 7a). The paper's Fig. 5 gives innermost-unit differences at the end of each discharge:
  - 2.88, 5.94 and 13.13 K at 1.25C, 2C and 3C at 25 C, and 11.54 K at 2C and minus 5 C.
  - This radial model at its own end of discharge gives 1.33, 3.54, 7.21 and 4.17 K, so the paper's values are 2.2, 1.7, 1.8 and 2.8 times larger.
  - The comparison is like for like only at 1.25C and 2C at 25 C, where both discharges end near 4.6 to 5.0 A h. At 3C and 25 C the paper's discharge runs to 4.2 to 4.4 A h and this one stops at 2.33 A h. At 2C and minus 5 C the paper's stops near 1.34 to 1.50 A h, where this model gives 3.22 to 3.26 K, a ratio of 3.5 to 3.6.
  - The ratio also varies along the radius, from 0.7 near the surface to 2.9 near the core.
  - The 4680 (Fig. 7a; both discharges near full) gives 37.5 K against this model's 18.9 K, 2.0 times.

  They do not agree within the reading error. The paper's heat is larger, or its conductivity lower, than Chen2020 with O'Regan's properties. The available parts of its property source (D16) do not say which. The figures also place the paper's innermost unit at 0.165 to 0.169 R, which is a hollow core of radius 1.74 to 1.79 mm. With that core, this radial model's differences would fall by a further 10 %.
- **Independent recomputation** (`verification/independent_recomputation/`). A separate axisymmetric solver, written from the physics alone without the study's code, reproduces every compared quantity within 0.15 % of the core-to-surface difference, for (a), (b) and (d) in the 21700 and (a) and (b) in the 4680. Its core-to-surface differences are 4.116, 3.449, 3.176, 18.166 and 10.611 K, against 4.122, 3.453, 3.180, 18.173 and 10.613 K here. The counts of units over 1 K match except in the 4680 under (a), 44 against 45, where one unit sits at 1.00 K. Its own grid error is at most 1.3e-4 K. Its refined-mesh prediction for (a), 4.1182 K, matches V3's 4.1185 K.
- **Independent audit** of the text against the files, at commit ed0fdd8 (report in `verification/reviews/`). A second checker, who did not build the study, traced the numbers in this README, the note, DECISIONS.md, predictions.md and the release metadata to the results files, the paper and the sources. It found the tables and scorecard verdicts correct and raised 2 high, 5 medium and 26 low points, mostly on interpretation: V4 compared different states of discharge, the note was stale, four claims overstated the results, and the note gave the wrong direction for the conductivity. They are taken up in this README, the note and DECISIONS.md (D14, D15), and the post-hoc analysis of D15 replaces the auditor's own re-solves.

## Secondary results (reported, not scored)

At 2C and minus 5 C, one-dimensional model:
- **The heat of mixing**, which PyBaMM leaves out by default, adds 38 % to the heat. With it the core-to-surface difference is 6.19 K (21700) and 26.47 K (4680).
- **ORegan2022**, Chen2020 plus O'Regan's measured temperature dependence, ends the minus 5 C, 2C discharge after 166 s at 0.46 A h. The difference reached by then is 5.13 K (21700).
- **The minus 5 C property table** raises the difference by 4.9 % (21700) and 5.7 % (4680).
- **The paper's form without the can** changes it by 0.01 %.

The resolved cell with these inputs, at 2C (`results/results_3d.csv`):
- In (b) the axial-to-radial ratio stays at 0.37 for every input: 0.371 with the heat of mixing, 0.367 and 0.372 with ORegan2022, and 0.370 with the minus 5 C properties.
- The spread in (b) stays 20 to 27 % below the radial model's.
- With the heat of mixing at minus 5 C, the mean offset in (b) grows to 1.68 K, with 39 of 45 units off by more than 1 K. With the minus 5 C properties it is 1.25 K, with 32 units.
- In (a) every unit stays within 0.41 K of the radial model under every input.

## What differs from the brief, and why

- **The parameter set.** The brief describes the Chen 2020 set this way: "the one already used here". The author's preceding study, the thermal lever (github.com/siddharth161204-wq/thermal-lever-duplicate-floor), in fact used ORegan2022, which is Chen 2020 plus O'Regan's temperature dependence. Chen2020 is registered because the brief names it, and ORegan2022 is a declared secondary input (D3).
- **The circumferential conductivity** of the roll is the radial value, not the two-cell study's along-layer value (D13, after V1 failed). The conductivities that carry heat here are unchanged.
- **The registered heat** is PyBaMM's default total heating, without the heat of mixing (D3). For this parameter set the heat of mixing would add 36 to 54 %.
- **The end path.** The roll's end faces touch the can's end caps directly, as in the two-cell cell. The end path is therefore at its most conductive, and the end effects here are upper bounds for a cell with insulating discs or a headspace (D9).
- **The paper's property source.** Reference 33 of the paper (Yang and Tartakovsky, J. Power Sources 664 (2026) 238948, doi:10.1016/j.jpowsour.2025.238948) holds the paper's thermal properties. Only its abstract, introduction and the opening lines of its sections were available (D16). They show that it models the same cell, the LG M50 21700, with a pseudo-two-dimensional electrochemical model coupled to a one-dimensional thermal model, parameterized by fitting to 1C discharge data, while this study takes its properties from O'Regan et al.'s measurements. Its property values are in the part that was not available, so the difference is stated in kind, not in size. V4 measures only the combined effect of the paper's heat, properties and discharge duration on its unit differences, not the property difference alone.
- **V4's timing.** V4 ran after the predictions, because the paper's figure images were found only then.

## Inputs and sources

1. **The paper.** Yang, X., Cui, Y. and Tartakovsky, D. M. Electrochemical Models of Multi-Unit Lithium Batteries Under Thermal Gradient. J. Electrochem. Soc. 173, 050520 (2026). https://doi.org/10.1149/1945-7111/ae4b6d. Used from it:
   - Eq. 2 to Eq. 4 (pp. 2 and 3)
   - h = 400 W/(m^2 K), the ambient temperatures, 45 units in the 21700, and about 111 units in the 4680 of 46 mm by 80 mm (p. 3)
   - Fig. 4 (p. 5), Fig. 5 (p. 5) and Fig. 7 (p. 6) for V4
2. **Its property source**, read in part (its abstract, introduction and section openings, from the publisher's page; D16): Yang, X. and Tartakovsky, D. M. Estimation of battery core temperature from indirect observations and models with error. J. Power Sources 664, 238948 (2026). https://doi.org/10.1016/j.jpowsour.2025.238948 (the DOI comes from Crossref).
3. **Chen2020.** Chen, C.-H. et al. Development of Experimental Techniques for Parameterization of Multi-scale Lithium-ion Battery Models. J. Electrochem. Soc. 167, 080534 (2020). https://doi.org/10.1149/1945-7111/ab9050. Used through PyBaMM's parameter set Chen2020.
4. **Thermal properties.** O'Regan, K., Brosa Planella, F., Widanage, W. D. and Kendrick, E. Thermal-electrochemical parameters of a high energy lithium-ion cylindrical battery. Electrochim. Acta 425, 140700 (2022). https://doi.org/10.1016/j.electacta.2022.140700. Used through PyBaMM's parameter set ORegan2022, computed as in the two-cell study (`inputs/properties.py`, `inputs/properties.json`).
5. **The resolved cell, the can and the strips.** Satte, S. (2026). Where and when a neighbour cell first reaches thermal-runaway onset temperatures: resolved against lumped, a pre-registered two-cell LG M50 pilot (v1.0.0). Zenodo. https://doi.org/10.5281/zenodo.23253738. Its mesh generator, solver and property script are copied unchanged into `inputs/` as `twocell_*`. They are kept for provenance: the solver copy is not imported, because its own imports are not copied. The can's values (0.25 mm, 15 W/(m K), 9 g at 500 J/(kg K)) and the strip value (6.23 mW/K) are its D10 and D24, which give no primary source for the can's values.
6. **Software.** PyBaMM 26.9.0.0 (Sulzer et al., J. Open Res. Softw. 9, 14 (2021), https://doi.org/10.5334/jors.309), scikit-fem 12.0.2, pyamg 5.3.0, NumPy 2.5.3, SciPy 1.18.1, matplotlib 3.11.2 (also used for point location in the field sampler).

## Files

- `DECISIONS.md`: every choice, D1 to D35.
- `predictions_stage2.md`, `inputs/ref33_values.md`: Stage 2's predictions and the values of the paper's ref. 33.
- `predictions_stage3.md`: Stage 3's predictions.
- `predictions_stage4.md`: Stage 4's predictions.
- `predictions_stage5.md`: Stage 5's predictions.
- `predictions.md`: P1 to P5 with their scoring rules.
- `inputs/`: the property computation and the two-cell study's files, copied unchanged.
- `src/`:
  - `common.py`: constants
  - `heat_generation.py`: the DFN runs
  - `radial1d.py`: the paper's radial model
  - `mesh.py`, `cell3d.py`: the resolved cell
  - `run3d.py`: the sweep
  - `analyse.py`: comparisons, checks, scorecard
  - `posthoc_matched_time.py`: D15
  - `stage2_correction.py`, `stage2_ref33.py`, `stage2_split.py`, `stage2_report.py`: Stage 2
  - `stage3_enkf.py`, `stage3_report.py`, `stage3_relabel.py`: Stage 3
  - `stage4_units.py`, `stage4_RT.py`, `stage4_report.py`, `stage4_v2.py`, `stage4_v3.py`: Stage 4
  - `stage5_common.py` (groups, kernels, convolution), `stage5_kernels.py` (the kernels), `stage5_coupled.py` (the coupled solve), `stage5_runs.py` (the discharge and charge runs and the searches), `stage5_queue.py` (the job lists the runs were made from), `stage5_v5.py`, `stage5_checks.py`, `stage5_report.py`, `stage5_posthoc_mesh.py` (D35), `stage5_posthoc_settled.py` (D36): Stage 5
  - `make_figure.py`
- `results/`:
  - `heat/`, `heat_summary.*`: the heat inputs
  - `radial1d*`: the one-dimensional results
  - `fields/`: one JSON per resolved run
  - `results_3d.csv`, `comparison_vs_a.csv`, `units_*.csv`: the comparisons
  - `scorecard.json`, `verification.json`
  - `posthoc_matched_time.json`
  - `figure.png`, `figure.pdf`
  - `stage2_*`: Stage 2's tables, scorecard and figure
  - `stage3_*`: Stage 3's runs with every core history, the series behind P5 and P7, the errors table, scorecard, checks, sensitivity, the paper's numbers and the figure
  - `stage4_*`: Stage 4's unit histories (`stage4_hist_*`), the unit-temperature readings with V1, the R(T) table, the per-unit table, the errors table, the scorecard, the checks, the paper's numbers and the figure
  - `stage5_*`: Stage 5's kernels (`stage5_kernels/`), every run and search with the runs' logs (`stage5_runs/`, `stage5_runs/logs/`), the discharge, shares, charge and limit tables, the summary tables, P1's and V5's records, the checks, the scorecard, the paper's numbers, the post hoc mesh check, the post hoc runs at 160 points with their logs (`stage5_posthoc_settled/`, D36) and the figure
- `verification/`: V0 to V4, the one-dimensional convergence check, the 3C cut-off check, the independent recomputation, the audit report (`reviews/`), and the independent reads of Stages 3, 4 and 5 (`stage3_independent_read/`, `stage4_independent_read/`, `stage5_independent_read/`: their scripts, outputs and findings).
- `tests/test_stage5.py`: tests of Stage 5's machinery: the groups, the convolution against direct stepping, the cut-triangle integrals, the search rule of D32 and the coupled solve at one temperature.
- `note/`: the one-page note (`radial_vs_resolved_note.pdf`), its source and the script that renders it.
- `CITATION.cff`, `.zenodo.json`: citation and archive metadata.

## How to run

```
python3 inputs/properties.py
python3 src/heat_generation.py
python3 src/radial1d.py
python3 verification/test_mesh.py && python3 verification/v0_checks.py && python3 verification/check_1d_steps.py
python3 src/run3d.py --cell 21700 --bcs a_eq,a,b,c,d --heats registered
python3 src/run3d.py --cell 4680 --bcs a,b --heats registered
python3 src/run3d.py --cell 21700 --bcs a,b --heats Chen2020_m5C_2C --refine 2
python3 src/run3d.py --cell 21700 --bcs a,b --heats Chen2020_m5C_2C_mixing,Chen2020_p25C_2C_mixing,ORegan2022_m5C_2C,ORegan2022_p25C_2C
python3 src/run3d.py --cell 21700 --bcs a,b --heats Chen2020_m5C_2C --props cold
python3 src/run3d.py --cell 21700 --bcs a_eq --heats Chen2020_m5C_2C --refine 2 --k-theta along
python3 src/analyse.py
python3 src/posthoc_matched_time.py
python3 src/make_figure.py
python3 verification/cutoff_3c.py
python3 verification/v4_digitise.py
python3 src/stage2_split.py
python3 src/stage2_correction.py
python3 src/stage2_ref33.py
python3 src/stage2_report.py
python3 src/stage3_enkf.py checks
STAGE3_CELL=21700 python3 src/stage3_enkf.py run
STAGE3_CELL=4680 python3 src/stage3_enkf.py run
python3 src/stage3_enkf.py series
python3 src/stage3_report.py
python3 src/stage4_units.py --fields 1d
python3 src/stage4_units.py --fields 3d --cell 21700
python3 src/stage4_units.py --fields 3d --cell 4680
python3 src/stage4_units.py --collect
python3 src/stage4_RT.py
python3 src/stage4_report.py
python3 src/stage4_v2.py
python3 src/stage4_v3.py
python3 src/stage5_kernels.py --all1d
python3 src/stage5_kernels.py --model resolved --bc b --cell 21700 --grid m5C_2C --units
for g in p25C_2C p25C_1.25C p25C_3C charge10 m5C_2C_half charge10_half; do python3 src/stage5_kernels.py --model resolved --bc b --cell 21700 --grid $g; done
for g in m5C_2C charge10; do python3 src/stage5_kernels.py --model resolved --bc b --cell 21700 --grid $g --G 30; done
python3 src/stage5_kernels.py --model resolved --bc a --cell 21700 --grid m5C_2C
for g in m5C_2C charge10; do python3 src/stage5_kernels.py --model resolved --bc b --cell 4680 --grid $g; done
python3 src/stage5_queue.py singles
for q in seg_21700_ORegan2022 seg_4680_ORegan2022 seg_21700_Chen2020 seg_4680_Chen2020 checks_d15 checks_c15 checks_d30 checks_c30; do while python3 src/stage5_queue.py $q --claims claims --one; do :; done; done
python3 src/stage5_v5.py
python3 src/stage5_posthoc_mesh.py
python3 src/stage5_report.py
# post hoc, D36: the mesh study, the runs at 160 points (one job each; see results/stage5_posthoc_settled/logs/queue.txt), the readings
python3 src/stage5_posthoc_settled.py mesh --points 160,320,640 --what discharges,charges,rates_0,rates_10,rates_25
python3 src/stage5_posthoc_settled.py runs --points 160 --job discharge:21700_b_m5C_2C:resolved
python3 src/stage5_posthoc_settled.py report --points 160
python3 src/stage5_checks.py report
python3 tests/test_stage5.py
```

`src/stage5_queue.py` runs a queue of jobs; with `--one` it runs one job per call, in a fresh process, and exits with code 3 when its queue has none left. The queue `singles` holds the single-unit searches for the plating-limited rate and runs first, since each coupled search starts from its single-unit result. The queues `seg_<cell>_<set>` hold the coupled searches and every discharge and charge run (the single-unit model's beside the coupled one), one job per kernel, and `checks_d15`, `checks_c15`, `checks_d30` and `checks_c30` hold the runs of V2 to V4. Several processes can share a queue through the claims directory. Each run can also be made directly with `src/stage5_runs.py`. A coupled process with 15 groups needs about 2 GB of memory, one with 30 groups about 4 GB, and the 4680's resolved kernels about 5 GB.

With one BLAS thread (`OMP_NUM_THREADS=1`), the seven Stage 3 runs repeated under D21 reproduced the stored values bit for bit; with two, a repeat of one run differed by at most 2.2e-16 K in its core history and no reported number changed.

V4 needs the paper's figure images in `verification/v4/`. They are extracted from the publisher's PDF with `pdfimages -f 5 -l 6 -j`. They are not redistributed here: the PDF's SHA-256 is recorded in `verification/v4.json`, and the paper is © 2026 The Electrochemical Society.

## Versions

- v1.0.0 (12 October 2026): the study as registered and run, with the corrections of the independent audit.
- v1.0.1 (13 October 2026): adds what the paper's property source says about its properties (D16) to the note, this README and DECISIONS.md. No input, code or result changed.
- v1.1.0 (21 October 2026): Stage 2 (D17, D18, predictions_stage2.md): the factor to the paper split into properties, heat and remainder with ref. 33's values, and a one-term end correction for the radial model. Stage 1's code, results and text are unchanged.
- v1.2.0 (27 October 2026): Stage 3 (D19 to D21, predictions_stage3.md): ref. 33's core-temperature estimator against the resolved cell. Stage 1 and 2 code and results are unchanged.
- v1.3.0 (29 October 2026): Stage 4 (D22 to D26, predictions_stage4.md): the radial field's thermal error carried to the current each unit draws. Stage 1 to 3 code and results are unchanged.
- v1.4.0 (17 November 2026): Stage 5 (D27 to D35, predictions_stage5.md): the multi-unit model solved directly under the three thermal models through convolution kernels; the paper's discharge penalty, Stage 4's proxy against the coupled solve, and the plating margin and plating-limited rate on charge. Stage 1 to 4 code and results are unchanged.

## Tooling

The code and text in this repository were developed with the assistance of Claude (Anthropic) as a programming, writing and checking assistant, working from the author's brief. The study design and the five predictions are the author's, and the author is responsible for the decisions and interpretations.

## Licence

Code: MIT (`LICENSE`). Note, figure and results: CC BY 4.0 (`LICENSE-CC-BY-4.0.md`).
