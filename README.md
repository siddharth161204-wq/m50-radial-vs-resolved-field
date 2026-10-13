# The axial blind spot of a radial cell model: the temperature field a multi-unit model assumes, tested on the LG M50 and a 4680

Author: Siddharth Satte, independent researcher, Pune, India (ORCID 0009-0001-3584-1008).

Archived at https://doi.org/10.5281/zenodo.23320970 (version v1.0.1).

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

- `DECISIONS.md`: every choice, D1 to D16.
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
  - `make_figure.py`
- `results/`:
  - `heat/`, `heat_summary.*`: the heat inputs
  - `radial1d*`: the one-dimensional results
  - `fields/`: one JSON per resolved run
  - `results_3d.csv`, `comparison_vs_a.csv`, `units_*.csv`: the comparisons
  - `scorecard.json`, `verification.json`
  - `posthoc_matched_time.json`
  - `figure.png`, `figure.pdf`
- `verification/`: V0 to V4, the one-dimensional convergence check, the 3C cut-off check, the independent recomputation, and the audit report (`reviews/`).
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
```

V4 needs the paper's figure images in `verification/v4/`. They are extracted from the publisher's PDF with `pdfimages -f 5 -l 6 -j`. They are not redistributed here: the PDF's SHA-256 is recorded in `verification/v4.json`, and the paper is © 2026 The Electrochemical Society.

## Versions

- v1.0.0 (12 October 2026): the study as registered and run, with the corrections of the independent audit.
- v1.0.1 (13 October 2026): adds what the paper's property source says about its properties (D16) to the note, this README and DECISIONS.md. No input, code or result changed.

## Tooling

The code and text in this repository were developed with the assistance of Claude (Anthropic) as a programming, writing and checking assistant, working from the author's brief. The study design and the five predictions are the author's, and the author is responsible for the decisions and interpretations.

## Licence

Code: MIT (`LICENSE`). Note, figure and results: CC BY 4.0 (`LICENSE-CC-BY-4.0.md`).
