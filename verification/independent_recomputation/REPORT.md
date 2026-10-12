> Filed copy. This folder is the independent checker's work, copied unchanged from /home/claude/independent_radial except for this note. The checker wrote its own code from the physics stated in its brief, without opening the study's src or inputs folders. Before its numbers were on disk, the only study file it read was the heat series results/heat/Chen2020_m5C_2C.csv. Its scripts use those absolute paths.
>
> Status at filing: the comparison was rerun once the study's (d) and 4680 rows existed (`compare_study.py`, `write_comparison_md.py`, `write_report.py`). Every compared quantity agrees within 0.15 % of the core-to-surface difference. The core-to-surface differences are:
> - (a) 21700: 4.1224 against 4.1165 K
> - (b) 21700: 3.4531 against 3.4487 K
> - (d) 21700: 3.1800 against 3.1760 K
> - (a) 4680: 18.173 against 18.166 K
> - (b) 4680: 10.613 against 10.611 K
>
> One count differs. In the 4680 under (a), the study counts 45 units more than 1 K off the radial model and the checker counts 44, because one unit sits at 1.00 K in both. The status line below was written before the (d) and 4680 rows existed. The study's refined mesh later gave 4.1185 K for (a), which matches the checker's second-order extrapolation of 4.1182 K.

# Independent check: 1D radial model vs resolved (r, z) field, Chen2020 heat at -5 C, 2C

STATUS: done. Own numbers converged (grid error below 1e-4 K, time-step error below 1e-6 K, energy balance closed to 1e-12). Comparison: AGREEMENT on every row the study file holds ((a) and (b) 21700: all within 0.15 % of the core-to-surface difference, counts over 1 K match); (d) 21700 and both 4680 rows were absent from the study file.

All numbers below were computed with my own code in this folder before the study's results file was opened. Nothing under the study's src or inputs folders, or under /home/claude/ext, was opened or imported; the only study file read before my numbers existed was results/heat/Chen2020_m5C_2C.csv.

## Method in brief

- Heat source: q(t) = Q(t) / (pi 0.01055^2 0.0701) with Q = heat_total_W, linear in time between the 1708 samples (1 s spacing, last interval 0.7446 s); end time 1706.7446 s. The same q(t) in W/m3 is applied to the 4680. Generated heat: 6506.479 J (21700), 35291.391 J (4680).
- Primary 3D solver (scheme V): vertex-centred finite volumes on a uniform axisymmetric (r, z) grid with nodes on r = 0, r = R, z = 0, z = H and z = H/2. Radial conductance k_r 2 pi r_face L / dr, axial k_z A / dz. The shell lives on the boundary nodes: heat capacity 841.7358 J/(m2 K) times the node's share of outer area, in-plane links k t 2 pi R / dz along the side and k t 2 pi r_face / dr along the end faces, with the two rim nodes belonging to both the side and the end-face shell (half a side segment plus the outermost half annulus), so shell conduction is continuous around the rim. Convection h times the node's outer area: side only in (a), side and ends in (b) and (d).
- Time integration: Crank-Nicolson at dt = 1 s with a Rannacher start (first two steps replaced by four backward-Euler half steps); each step uses the exact mean of the piecewise-linear q(t), so the generated heat is exact.
- Outputs: T(0, H/2), T(R, H/2), T(0, 0), T(0, H) are node values. Unit averages are exact integrals of the bilinear interpolant over each equal-thickness annulus (45 or 111) and the full height. Volume mean is the control-volume sum over the roll. Energy: generated = exact integral of q times pi R^2 H; lost = trapezoidal time integral of the convective loss; stored = sum of node capacities (roll and shell) times the temperature rise.
- 1D model: solved semi-analytically as a Bessel series in J0(beta_n r) whose eigenvalue condition includes the shell heat capacity, x J1(x) = (Bi - sigma x^2) J0(x) with Bi = h R / k_r and sigma = C_shell / (rho cp R), 40000 modes, exact time convolution with the piecewise-linear q(t). A 1D finite-volume ladder converges onto it at second order.
- Cross-check 3D solver (scheme C): cell-centred finite volumes with separate zero-volume shell nodes, half-cell links to the roll and a series corner link around the rim. Different node placement, shell coupling and rim treatment from scheme V.
- rho cp = 2938.7 x 842.4 = 2475560.88 J/(m3 K) (see Problems).

## My numbers at the end of discharge (t = 1706.7446 s)

1D values are from the Bessel series; 3D values are from scheme V on the finest grid (21700: 360 x 528; 4680: 444 x 344), dt = 1 s. They are accurate to about 1e-5 K (worst case 1.3e-4 K, see Convergence evidence). Every unit's temperature and offset is in units_end_21700.csv and units_end_4680.csv.

| Case | T core mid (C) | T surface mid (C) | Core-to-surface (K) | Axial T(0,H/2)-T(0,0) (K) | Axial T(0,H/2)-T(0,H) (K) | Unit spread (K) | Volume-mean T (C) |
|---|---|---|---|---|---|---|---|
| 1D 21700 | 1.74984 | -2.51381 | 4.26365 | n/a | n/a | 4.16843 | -0.37843 |
| (a) 21700 | 1.55729 | -2.55917 | 4.11645 | 0.31243 | 0.31243 | 3.88099 | -0.51159 |
| (b) 21700 | 0.56772 | -2.88097 | 3.44870 | 1.27750 | 1.27750 | 3.05715 | -1.36817 |
| (d) 21700 | 28.15009 | 24.97411 | 3.17598 | 0.78263 | 0.78263 | 2.94568 | 26.40326 |
| 1D 4680 | 19.30479 | 0.19227 | 19.11252 | n/a | n/a | 18.93682 | 9.81338 |
| (a) 4680 | 18.23531 | 0.06907 | 18.16624 | 0.39638 | 0.39638 | 17.73015 | 9.24122 |
| (b) 4680 | 9.09691 | -1.51368 | 10.61059 | 3.43261 | 3.43261 | 9.54849 | 3.49196 |

Unit offsets (1D unit temperature minus 3D unit average, unweighted statistics over the units):

| 3D case | 1D used | Mean offset (K) | Min offset (K) | Max offset (K) | Units with abs offset > 1 K | Largest abs offset (K) |
|---|---|---|---|---|---|---|
| (a) 21700 | 1D 21700, h = 400 | 0.18454 | 0.00205 | 0.28949 | 0 of 45 | 0.28949 |
| (b) 21700 | 1D 21700, h = 400 | 1.18507 | 0.47550 | 1.58678 | 31 of 45 | 1.58678 |
| (d) 21700 | 1D 21700, h = 400 | -26.57118 | -27.37058 | -26.14782 | 45 of 45 | 27.37058 |
| (d) 21700 (extra) | 1D 21700, h = 25 | 4.08040 | 3.68473 | 4.29541 | 45 of 45 | 4.29541 |
| (a) 4680 | 1D 4680, h = 400 | 0.78146 | -0.00563 | 1.20103 | 44 of 111 | 1.20103 |
| (b) 4680 | 1D 4680, h = 400 | 7.95781 | 1.94807 | 11.33640 | 111 of 111 | 11.33640 |

Units whose offset lies within 0.05 K of the 1 K threshold (the count is sensitive to these): b 21700: unit 31 at 1.0216 K, unit 32 at 0.9863 K, unit 33 at 0.9502 K; a 4680: unit 40 at 1.0421 K, unit 41 at 1.0339 K, unit 42 at 1.0255 K, unit 43 at 1.0169 K, unit 44 at 1.0081 K, unit 45 at 0.9991 K, unit 46 at 0.9898 K, unit 47 at 0.9804 K, unit 48 at 0.9707 K, unit 49 at 0.9609 K, unit 50 at 0.9508 K.

Energy balance:

| Case | Heat generated (J) | Heat lost by convection (J) | Heat stored, roll + shell (J) | (gen - lost - stored)/gen |
|---|---|---|---|---|
| 1D 21700 | 6506.479 | 6216.318 | 290.162 | 2.5e-12 |
| (a) 21700 | 6506.479 | 6221.782 | 284.697 | -1.5e-13 |
| (b) 21700 | 6506.479 | 6276.339 | 230.140 | -1.0e-13 |
| (d) 21700 | 6506.479 | 4465.779 | 2040.701 | -5.8e-14 |
| 1D 4680 | 35291.391 | 30365.317 | 4926.074 | -2.9e-12 |
| (a) 4680 | 35291.391 | 30513.904 | 4777.487 | 1.7e-13 |
| (b) 4680 | 35291.391 | 32444.507 | 2846.884 | 9.0e-14 |

The 1D energies are per unit height multiplied by H. The 3D balance closes to round-off because the scheme is conservative and the source integral is exact; it confirms the assembly (volumes, capacities, convective areas) rather than accuracy.

## Convergence evidence

### Space (3D, scheme V)

**(a) 21700** (vertex-centred scheme, dt = 1 s)

| Nr x Nz | Core-to-surface (K) | Axial bot (K) | Unit spread (K) | Volume mean (C) | Mean offset (K) | Min offset (K) | Max offset (K) | n > 1 K |
|---|---|---|---|---|---|---|---|---|
| 45 x 66 | 4.1159393 | 0.3124601 | 3.8806678 | -0.5129364 | 0.185746 | 0.002945 | 0.290706 | 0 |
| 90 x 132 | 4.1163150 | 0.3124421 | 3.8809148 | -0.5119374 | 0.184861 | 0.002299 | 0.289812 | 0 |
| 180 x 264 | 4.1164248 | 0.3124323 | 3.8809726 | -0.5116585 | 0.184611 | 0.002103 | 0.289559 | 0 |
| 360 x 528 | 4.1164542 | 0.3124292 | 3.8809861 | -0.5115851 | 0.184544 | 0.002050 | 0.289492 | 0 |

Core-to-surface: observed order 1.90, Richardson error estimate of the finest grid 1.08e-05 K = 2.62e-06 of the core-to-surface difference (0.00026 %). Largest Richardson error estimate over all listed quantities: 2.62e-05 K.

**(b) 21700** (vertex-centred scheme, dt = 1 s)

| Nr x Nz | Core-to-surface (K) | Axial bot (K) | Unit spread (K) | Volume mean (C) | Mean offset (K) | Min offset (K) | Max offset (K) | n > 1 K |
|---|---|---|---|---|---|---|---|---|
| 45 x 66 | 3.4483570 | 1.2772561 | 3.0569445 | -1.3691209 | 1.185896 | 0.476123 | 1.587607 | 31 |
| 90 x 132 | 3.4486076 | 1.2774436 | 3.0571086 | -1.3684134 | 1.185281 | 0.475669 | 1.586989 | 31 |
| 180 x 264 | 3.4486782 | 1.2774907 | 3.0571424 | -1.3682202 | 1.185112 | 0.475534 | 1.586820 | 31 |
| 360 x 528 | 3.4486968 | 1.2775025 | 3.0571496 | -1.3681698 | 1.185067 | 0.475497 | 1.586776 | 31 |

Core-to-surface: observed order 1.92, Richardson error estimate of the finest grid 6.69e-06 K = 1.94e-06 of the core-to-surface difference (0.00019 %). Largest Richardson error estimate over all listed quantities: 1.78e-05 K.

**(d) 21700** (vertex-centred scheme, dt = 1 s)

| Nr x Nz | Core-to-surface (K) | Axial bot (K) | Unit spread (K) | Volume mean (C) | Mean offset (K) | Min offset (K) | Max offset (K) | n > 1 K |
|---|---|---|---|---|---|---|---|---|
| 45 x 66 | 3.1758708 | 0.7825192 | 2.9455205 | 26.4025342 | -26.570579 | -27.370134 | -26.147227 | 45 |
| 90 x 132 | 3.1759560 | 0.7826046 | 2.9456464 | 26.4030734 | -26.571025 | -27.370451 | -26.147669 | 45 |
| 180 x 264 | 3.1759780 | 0.7826258 | 2.9456718 | 26.4032217 | -26.571150 | -27.370548 | -26.147792 | 45 |
| 360 x 528 | 3.1759836 | 0.7826311 | 2.9456770 | 26.4032604 | -26.571182 | -27.370576 | -26.147824 | 45 |

Core-to-surface: observed order 1.98, Richardson error estimate of the finest grid 1.91e-06 K = 6.03e-07 of the core-to-surface difference (0.00006 %). Largest Richardson error estimate over all listed quantities: 1.37e-05 K.

**(a) 4680** (vertex-centred scheme, dt = 1 s)

| Nr x Nz | Core-to-surface (K) | Axial bot (K) | Unit spread (K) | Volume mean (C) | Mean offset (K) | Min offset (K) | Max offset (K) | n > 1 K |
|---|---|---|---|---|---|---|---|---|
| 111 x 86 | 18.1654980 | 0.3963797 | 17.7297563 | 9.2396695 | 0.782897 | -0.004611 | 1.202449 | 45 |
| 222 x 172 | 18.1660706 | 0.3963799 | 17.7300816 | 9.2408805 | 0.781779 | -0.005392 | 1.201342 | 44 |
| 444 x 344 | 18.1662354 | 0.3963796 | 17.7301545 | 9.2412198 | 0.781463 | -0.005632 | 1.201030 | 44 |

Core-to-surface: observed order 1.80, Richardson error estimate of the finest grid 6.66e-05 K = 3.67e-06 of the core-to-surface difference (0.00037 %). Largest Richardson error estimate over all listed quantities: 1.32e-04 K.

**(b) 4680** (vertex-centred scheme, dt = 1 s)

| Nr x Nz | Core-to-surface (K) | Axial bot (K) | Unit spread (K) | Volume mean (C) | Mean offset (K) | Min offset (K) | Max offset (K) | n > 1 K |
|---|---|---|---|---|---|---|---|---|
| 111 x 86 | 10.6103580 | 3.4324519 | 9.5483866 | 3.4911942 | 7.958499 | 1.948615 | 11.337044 | 111 |
| 222 x 172 | 10.6105399 | 3.4325786 | 9.5484801 | 3.4917978 | 7.957957 | 1.948195 | 11.336531 | 111 |
| 444 x 344 | 10.6105885 | 3.4326122 | 9.5484901 | 3.4919604 | 7.957812 | 1.948069 | 11.336395 | 111 |

Core-to-surface: observed order 1.90, Richardson error estimate of the finest grid 1.77e-05 K = 1.67e-06 of the core-to-surface difference (0.00017 %). Largest Richardson error estimate over all listed quantities: 5.99e-05 K.

### Time step (3D, scheme V)

| Case (grid 90 x 132) | dt (s) | Core-to-surface (K) | Axial bot (K) | Volume mean (C) |
|---|---|---|---|---|
| (a) 21700 | 4 | 4.116307468 | 0.312441861 | -0.511950266 |
| (a) 21700 | 2 | 4.116313485 | 0.312442041 | -0.511940096 |
| (a) 21700 | 1 | 4.116315015 | 0.312442087 | -0.511937445 |
| (a) 21700 | 0.5 | 4.116315402 | 0.312442099 | -0.511936772 |
| (a) 21700 | 0.25 | 4.116315498 | 0.312442102 | -0.511936603 |
| (b) 21700 | 4 | 3.448595751 | 1.277439545 | -1.368429493 |
| (b) 21700 | 2 | 3.448605218 | 1.277442770 | -1.368416707 |
| (b) 21700 | 1 | 3.448607623 | 1.277443586 | -1.368413390 |
| (b) 21700 | 0.5 | 3.448608230 | 1.277443791 | -1.368412549 |
| (b) 21700 | 0.25 | 3.448608382 | 1.277443842 | -1.368412338 |
| (d) 21700 | 4 | 3.175952794 | 0.782603860 | 26.403054954 |
| (d) 21700 | 2 | 3.175955310 | 0.782604492 | 26.403069715 |
| (d) 21700 | 1 | 3.175955952 | 0.782604650 | 26.403073399 |
| (d) 21700 | 0.5 | 3.175956115 | 0.782604690 | 26.403074319 |
| (d) 21700 | 0.25 | 3.175956156 | 0.782604700 | 26.403074549 |

- (a): observed temporal order 2.00; core-to-surface at dt = 1 s differs from dt = 0.25 s by -4.83e-07 K; plain Crank-Nicolson without the Rannacher start gives 4.116315015 K at dt = 1 s.
- (b): observed temporal order 2.00; core-to-surface at dt = 1 s differs from dt = 0.25 s by -7.58e-07 K; plain Crank-Nicolson without the Rannacher start gives 3.448607623 K at dt = 1 s.
- (d): observed temporal order 2.00; core-to-surface at dt = 1 s differs from dt = 0.25 s by -2.04e-07 K; plain Crank-Nicolson without the Rannacher start gives 3.175956103 K at dt = 1 s.

### 1D finite volumes vs the Bessel series

| Case | Nr | Core-to-surface (K) | Error vs Bessel series (K) | Max abs unit error vs series (K) |
|---|---|---|---|---|
| 1D 21700 | 45 | 4.2636329 | -1.53e-05 | 3.57e-04 |
| 1D 21700 | 90 | 4.2636440 | -4.18e-06 | 9.01e-05 |
| 1D 21700 | 180 | 4.2636468 | -1.40e-06 | 2.33e-05 |
| 1D 21700 | 360 | 4.2636475 | -7.04e-07 | 6.60e-06 |
| 1D 4680 | 111 | 19.1124703 | -4.86e-05 | 2.92e-04 |
| 1D 4680 | 222 | 19.1125073 | -1.16e-05 | 7.28e-05 |
| 1D 4680 | 444 | 19.1125165 | -2.38e-06 | 1.85e-05 |

### Second 3D discretisation (scheme C) vs scheme V finest grid

| Case | Scheme C grid | Core-to-surface C minus V (K) | Axial C minus V (K) | Unit spread C minus V (K) | Volume mean C minus V (K) | Max abs unit diff (K) |
|---|---|---|---|---|---|---|
| (a) 21700 | 180 x 265 | 1.06e-04 | -1.10e-05 | 5.68e-06 | 1.85e-04 | 1.83e-04 |
| (b) 21700 | 180 x 265 | 6.62e-05 | 2.85e-05 | -1.90e-05 | 1.25e-04 | 1.32e-04 |
| (d) 21700 | 180 x 265 | 5.03e-05 | 9.89e-06 | -5.95e-06 | 9.95e-05 | 1.01e-04 |
| (a) 4680 | 444 x 345 | 1.57e-04 | 1.98e-06 | 1.44e-05 | 2.83e-04 | 2.80e-04 |
| (b) 4680 | 444 x 345 | 4.75e-05 | 4.39e-05 | -4.10e-05 | 1.32e-04 | 1.53e-04 |

The scheme C minus scheme V differences fall by a factor of about 3.6 (21700) and 2.8 (4680) per halving of the scheme C grid (about 4 for the 4680 once scheme V's own remaining error of about 7e-5 K is allowed for), i.e. both schemes converge to the same field at second order. All differences stay below 1e-3 K, far inside the 0.5 % target, which also checks the treatment of the shell around the rim, where the two schemes differ most.

Verdict on accuracy: every Richardson error estimate for the core-to-surface difference is below 1e-4 K and below 4e-6 of the difference itself, more than three orders of magnitude inside the 0.5 % target; the largest estimate for any reported quantity is 1.3e-4 K (the 4680 (a) volume mean). Time-step error at dt = 1 s is below 1e-6 K.

## Problems hit and notes

1. The task text says rho cp = 2475540, but 2938.7 x 842.4 = 2475560.88 (8.5 ppm higher). I used the product. Re-running with 2475540: (a) 21700: core-to-surface changes by 6.85e-07 K, volume mean by 6.65e-07 K; (b) 21700: core-to-surface changes by 4.65e-07 K, volume mean by 4.29e-07 K. Immaterial.
2. Case (d) offsets, as specified, compare the h = 400 1D model with the h = 25 3D field, so they measure the change of h, not the 1D approximation (mean -26.571 K). For reference, a 1D model with h = 25 gives core-to-surface 3.6376 K, unit spread 3.5564 K, and offsets against (d) of mean 4.0804 K, min 3.6847 K, max 4.2954 K, 45 units over 1 K.
3. The count of units with offset above 1 K sits on a knife edge in (a) 4680 (a unit at about 0.999 K) and is close in (b) 21700; a code with slightly different discretisation error can legitimately differ by one unit there.
4. The machine has 2 cores and the study's own 3D runs were using both throughout, so my runs were slower; results are unaffected. I saw those processes only as command lines in the process list and did not open their files.
5. Plain Crank-Nicolson oscillation risk from the stiff shell start-up (shell-roll equilibration time about 0.2 s) was handled by the Rannacher start; dropping it changes the core-to-surface difference by less than 2e-7 K.

## Files

- Code: params.py (constants, heat source), network.py (assembly, Crank-Nicolson integrator, energy bookkeeping), discretise.py (schemes V and C, 1D finite volumes), analytic_1d.py (Bessel series), run_all.py (all production runs), hottest_check.py, test_basic.py (verification tests; output in test_basic.log).
- My results: runs.jsonl (every run, including unit averages), results.json and results.csv (headline numbers, convergence, offsets), convergence.csv, units_end_21700.csv, units_end_4680.csv, hottest_check.json, run_all.log.
- Comparison: compare_study.py, write_comparison_md.py, comparison.csv, comparison.json, comparison.md, study_results_3d_snapshot.csv (the study rows exactly as compared).

## Comparison with the study's results_3d.csv

Snapshot of results/results_3d.csv taken 2026-10-12 13:27:00 (file last modified 2026-10-12 13:26:59 UTC; saved here as study_results_3d_snapshot.csv). Rows used: heat = Chen2020_m5C_2C, when = end, refine = 1.0, props = registered.

Present in the study file: 21700 (a), 21700 (a_eq), 21700 (b), 21700 (c), 21700 (d), 4680 (a), 4680 (b). Missing: none. At snapshot time the study's 4680 run and a refine = 2 run of the 21700 (a, b) were still executing; re-run `python3 compare_study.py && python3 write_comparison_md.py && python3 write_report.py` when more rows land. My values for the missing cases are in the tables above.

**Verdict: DISAGREEMENT.** Every requested quantity present for (a) and (b) 21700 agrees with mine within 0.146 % of the core-to-surface difference (all inside the 0.5 % target), and the counts of units over 1 K DO NOT match.

| Case | Study column | Study | Mine | Study minus mine | As % of my core-to-surface |
|---|---|---|---|---|---|
| (a) 21700 | dT_core_surface_3d_K | 4.122352 | 4.116454 | +0.005898 | +0.143 % |
| (a) 21700 | dT_axial_K | 0.316150 | 0.312429 | +0.003721 | +0.090 % |
| (a) 21700 | dT_axial_bottom_K | 0.308225 | 0.312429 | -0.004204 | -0.102 % |
| (a) 21700 | dT_axial_top_K | 0.316150 | 0.312429 | +0.003721 | +0.090 % |
| (a) 21700 | units_spread_3d_K | 3.885579 | 3.880986 | +0.004593 | +0.112 % |
| (a) 21700 | units_mean_offset_1d_minus_3d_K | 0.186545 | 0.184544 | +0.002001 | +0.049 % |
| (a) 21700 | units_min_offset_K | 0.004246 | 0.002050 | +0.002196 | +0.053 % |
| (a) 21700 | units_max_offset_K | 0.290220 | 0.289492 | +0.000728 | +0.018 % |
| (a) 21700 | units_n_units_over_1K | 0 | 0 | 0 | match |
| (a) 21700 | dT_core_surface_1d_K | 4.264119 | 4.263648 | +0.000471 | +0.011 % |
| (a) 21700 | units_spread_1d_K | 4.168886 | 4.168428 | +0.000457 | +0.011 % |
| (b) 21700 | dT_core_surface_3d_K | 3.453138 | 3.448697 | +0.004441 | +0.129 % |
| (b) 21700 | dT_axial_K | 1.282541 | 1.277502 | +0.005038 | +0.146 % |
| (b) 21700 | dT_axial_bottom_K | 1.273635 | 1.277502 | -0.003868 | -0.112 % |
| (b) 21700 | dT_axial_top_K | 1.282541 | 1.277502 | +0.005038 | +0.146 % |
| (b) 21700 | units_spread_3d_K | 3.060013 | 3.057150 | +0.002864 | +0.083 % |
| (b) 21700 | units_mean_offset_1d_minus_3d_K | 1.187044 | 1.185067 | +0.001977 | +0.057 % |
| (b) 21700 | units_min_offset_K | 0.477189 | 0.475497 | +0.001692 | +0.049 % |
| (b) 21700 | units_max_offset_K | 1.586279 | 1.586776 | -0.000496 | -0.014 % |
| (b) 21700 | units_n_units_over_1K | 31 | 31 | 0 | match |
| (b) 21700 | dT_core_surface_1d_K | 4.264119 | 4.263648 | +0.000471 | +0.014 % |
| (b) 21700 | units_spread_1d_K | 4.168886 | 4.168428 | +0.000457 | +0.013 % |
| (d) 21700 | dT_core_surface_3d_K | 3.180023 | 3.175984 | +0.004039 | +0.127 % |
| (d) 21700 | dT_axial_K | 0.786213 | 0.782631 | +0.003582 | +0.113 % |
| (d) 21700 | dT_axial_bottom_K | 0.778836 | 0.782631 | -0.003795 | -0.119 % |
| (d) 21700 | dT_axial_top_K | 0.786213 | 0.782631 | +0.003582 | +0.113 % |
| (d) 21700 | units_spread_3d_K | 2.948740 | 2.945677 | +0.003063 | +0.096 % |
| (d) 21700 | units_mean_offset_1d_minus_3d_K | -26.568506 | -26.571182 | +0.002676 | +0.084 % |
| (d) 21700 | units_min_offset_K | -27.368093 | -27.370576 | +0.002483 | +0.078 % |
| (d) 21700 | units_max_offset_K | -26.147707 | -26.147824 | +0.000117 | +0.004 % |
| (d) 21700 | units_n_units_over_1K | 45 | 45 | 0 | match |
| (d) 21700 | dT_core_surface_1d_K | 4.264119 | 4.263648 | +0.000471 | +0.015 % |
| (d) 21700 | units_spread_1d_K | 4.168886 | 4.168428 | +0.000457 | +0.014 % |
| (a) 4680 | dT_core_surface_3d_K | 18.173124 | 18.166235 | +0.006889 | +0.038 % |
| (a) 4680 | dT_axial_K | 0.401070 | 0.396380 | +0.004691 | +0.026 % |
| (a) 4680 | dT_axial_bottom_K | 0.391604 | 0.396380 | -0.004775 | -0.026 % |
| (a) 4680 | dT_axial_top_K | 0.401070 | 0.396380 | +0.004691 | +0.026 % |
| (a) 4680 | units_spread_3d_K | 17.735651 | 17.730155 | +0.005497 | +0.030 % |
| (a) 4680 | units_mean_offset_1d_minus_3d_K | 0.783706 | 0.781463 | +0.002243 | +0.012 % |
| (a) 4680 | units_min_offset_K | -0.003736 | -0.005632 | +0.001896 | +0.010 % |
| (a) 4680 | units_max_offset_K | 1.201726 | 1.201030 | +0.000696 | +0.004 % |
| (a) 4680 | units_n_units_over_1K | 45 | 44 | 1 | MISMATCH |
| (a) 4680 | dT_core_surface_1d_K | 19.113300 | 19.112519 | +0.000781 | +0.004 % |
| (a) 4680 | units_spread_1d_K | 18.937583 | 18.936816 | +0.000767 | +0.004 % |
| (b) 4680 | dT_core_surface_3d_K | 10.612626 | 10.610588 | +0.002037 | +0.019 % |
| (b) 4680 | dT_axial_K | 3.439458 | 3.432612 | +0.006846 | +0.065 % |
| (b) 4680 | dT_axial_bottom_K | 3.426544 | 3.432612 | -0.006068 | -0.057 % |
| (b) 4680 | dT_axial_top_K | 3.439458 | 3.432612 | +0.006846 | +0.065 % |
| (b) 4680 | units_spread_3d_K | 9.548727 | 9.548490 | +0.000237 | +0.002 % |
| (b) 4680 | units_mean_offset_1d_minus_3d_K | 7.960865 | 7.957812 | +0.003053 | +0.029 % |
| (b) 4680 | units_min_offset_K | 1.949056 | 1.948069 | +0.000987 | +0.009 % |
| (b) 4680 | units_max_offset_K | 11.337912 | 11.336395 | +0.001516 | +0.014 % |
| (b) 4680 | units_n_units_over_1K | 111 | 111 | 0 | match |
| (b) 4680 | dT_core_surface_1d_K | 19.113300 | 19.112519 | +0.000781 | +0.007 % |
| (b) 4680 | units_spread_1d_K | 18.937583 | 18.936816 | +0.000767 | +0.007 % |
| (a) 21700 | T_core_mid_3d_C (extra) | 1.563402 | 1.557287 | +0.006115 | +0.149 % |
| (a) 21700 | T_surface_mid_3d_C (extra) | -2.558950 | -2.559167 | +0.000217 | +0.005 % |
| (a) 21700 | T_roll_mean_3d_C (extra) | -0.512948 | -0.511585 | -0.001363 | -0.033 % |
| (a) 21700 | T_core_1d_C (extra) | 1.750493 | 1.749841 | +0.000652 | +0.016 % |
| (a) 21700 | T_surface_1d_C (extra) | -2.513626 | -2.513807 | +0.000181 | +0.004 % |
| (a) 21700 | T_mean_1d_C (extra) | -0.378023 | -0.378431 | +0.000408 | +0.010 % |
| (a) 21700 | units_max_abs_diff_K (extra) | 0.290220 | 0.289492 | +0.000728 | +0.018 % |
| (a) 21700 | axial_over_radial (extra) | 0.076692 | 0.075898 | +0.000794 | ratio |
| (a) 21700 | units_spread_change_rel (extra) | -0.067957 | -0.068957 | +0.001000 | ratio |
| (b) 21700 | T_core_mid_3d_C (extra) | 0.572642 | 0.567723 | +0.004919 | +0.143 % |
| (b) 21700 | T_surface_mid_3d_C (extra) | -2.880496 | -2.880974 | +0.000477 | +0.014 % |
| (b) 21700 | T_roll_mean_3d_C (extra) | -1.369405 | -1.368170 | -0.001235 | -0.036 % |
| (b) 21700 | T_core_1d_C (extra) | 1.750493 | 1.749841 | +0.000652 | +0.019 % |
| (b) 21700 | T_surface_1d_C (extra) | -2.513626 | -2.513807 | +0.000181 | +0.005 % |
| (b) 21700 | T_mean_1d_C (extra) | -0.378023 | -0.378431 | +0.000408 | +0.012 % |
| (b) 21700 | units_max_abs_diff_K (extra) | 1.586279 | 1.586776 | -0.000496 | -0.014 % |
| (b) 21700 | axial_over_radial (extra) | 0.371413 | 0.370430 | +0.000983 | ratio |
| (b) 21700 | units_spread_change_rel (extra) | -0.265988 | -0.266594 | +0.000607 | ratio |
| (d) 21700 | T_core_mid_3d_C (extra) | 28.153904 | 28.150089 | +0.003816 | +0.120 % |
| (d) 21700 | T_surface_mid_3d_C (extra) | 24.973882 | 24.974105 | -0.000223 | -0.007 % |
| (d) 21700 | T_roll_mean_3d_C (extra) | 26.401257 | 26.403260 | -0.002004 | -0.063 % |
| (d) 21700 | T_core_1d_C (extra) | 1.750493 | 1.749841 | +0.000652 | +0.021 % |
| (d) 21700 | T_surface_1d_C (extra) | -2.513626 | -2.513807 | +0.000181 | +0.006 % |
| (d) 21700 | T_mean_1d_C (extra) | -0.378023 | -0.378431 | +0.000408 | +0.013 % |
| (d) 21700 | units_max_abs_diff_K (extra) | 27.368093 | 27.370576 | -0.002483 | -0.078 % |
| (d) 21700 | axial_over_radial (extra) | 0.247235 | 0.246422 | +0.000813 | ratio |
| (d) 21700 | units_spread_change_rel (extra) | -0.292679 | -0.293336 | +0.000657 | ratio |
| (a) 4680 | T_core_mid_3d_C (extra) | 18.242430 | 18.235306 | +0.007124 | +0.039 % |
| (a) 4680 | T_surface_mid_3d_C (extra) | 0.069305 | 0.069071 | +0.000235 | +0.001 % |
| (a) 4680 | T_roll_mean_3d_C (extra) | 9.239574 | 9.241220 | -0.001646 | -0.009 % |
| (a) 4680 | T_core_1d_C (extra) | 19.305769 | 19.304793 | +0.000976 | +0.005 % |
| (a) 4680 | T_surface_1d_C (extra) | 0.192469 | 0.192274 | +0.000195 | +0.001 % |
| (a) 4680 | T_mean_1d_C (extra) | 9.814074 | 9.813378 | +0.000695 | +0.004 % |
| (a) 4680 | units_max_abs_diff_K (extra) | 1.201726 | 1.201030 | +0.000696 | +0.004 % |
| (a) 4680 | axial_over_radial (extra) | 0.022069 | 0.021820 | +0.000250 | ratio |
| (a) 4680 | units_spread_change_rel (extra) | -0.063468 | -0.063720 | +0.000252 | ratio |
| (b) 4680 | T_core_mid_3d_C (extra) | 9.099652 | 9.096905 | +0.002746 | +0.026 % |
| (b) 4680 | T_surface_mid_3d_C (extra) | -1.512974 | -1.513683 | +0.000709 | +0.007 % |
| (b) 4680 | T_roll_mean_3d_C (extra) | 3.489942 | 3.491960 | -0.002019 | -0.019 % |
| (b) 4680 | T_core_1d_C (extra) | 19.305769 | 19.304793 | +0.000976 | +0.009 % |
| (b) 4680 | T_surface_1d_C (extra) | 0.192469 | 0.192274 | +0.000195 | +0.002 % |
| (b) 4680 | T_mean_1d_C (extra) | 9.814074 | 9.813378 | +0.000695 | +0.007 % |
| (b) 4680 | units_max_abs_diff_K (extra) | 11.337912 | 11.336395 | +0.001516 | +0.014 % |
| (b) 4680 | axial_over_radial (extra) | 0.324091 | 0.323508 | +0.000583 | ratio |
| (b) 4680 | units_spread_change_rel (extra) | -0.495779 | -0.495771 | -0.000008 | ratio |

Notes on the comparison:

1. The study's 3D core-to-surface difference is higher than mine by 0.0069 K in (a) and 0.0020 K in (b). Almost all of it is in the core temperature (+0.0071 K and +0.0027 K); the mid-height surface agrees within 0.0007 K. My own grid and time errors are about 1e-5 K, so the gap is the study's discretisation error at refine = 1.0. It is inside the 0.5 % target.
2. The problem is symmetric about mid-height, and my bottom and top axial differences are equal to 1e-13 K. The study's are not: its T(0,0) is warmer than its T(0,H) by 0.0079 K in (a), 0.0089 K in (b) and 0.0094 K in a_eq, the same sign every time. That points to an asymmetric mesh or solver bias, not to noise. The study's dT_axial_K equals its top value, so it sits 0.0047 K (a) and 0.0068 K (b) above my symmetric value. The mean of its bottom and top values agrees with mine to -0.00024 K (a) and +0.00059 K (b).
3. Hottest point: mine is on the axis at mid-height in both cases ((a): 1.557239 C at r = 0.000 mm, z = 35.050 mm; (b): z = 35.050 mm, on the 180 x 264 grid; field symmetric about mid-height to 7.8e-13 K). The study puts the (a) hottest point at z = 36.576 mm, 1.526 mm off mid-plane. That fits note 2 and a very flat axial plateau; the study's hottest value is only 5.9e-05 K above its own mid-height core value.
4. Unit statistics: the study's mean offset is larger than mine by 0.0022 K (a) and 0.0031 K (b). Its 3D unit spread is larger by 0.0055 K and 0.0002 K, and its 3D roll mean is cooler by 0.0016 K and 0.0020 K. The counts over 1 K match (0 and 31). In (b) my unit nearest the threshold is at 0.9863 K, so the count is robust to differences of this size.
5. The study's 1D model is within 0.00078 K of my exact Bessel-series core-to-surface difference (0.018 %). Its unit spread is within 0.00077 K and its core, surface and mean temperatures are within 0.0007 K.
6. Information only: the study also has an a_eq row, which I was not asked to compute and whose definition I have not seen. Its name and its near-zero axial differences (-0.0047 K and +0.0047 K) suggest a 3D run set up to reproduce the 1D model. If that is right, comparing it with my exact 1D solution isolates the study's 3D discretisation error: core-to-surface +0.0067 K, core +0.0069 K, surface +0.0002 K, roll mean -0.0011 K, unit spread +0.0052 K. That is the same signature as the (a) and (b) gaps in notes 1 and 4, which supports reading those gaps as mesh error rather than a difference in physics or set-up. (My 3D code reproduces the 1D solution to better than 1e-12 K when the shell's in-plane conduction and end shells are switched off; see test_basic.log.)
7. Prediction for the study's refine = 2 run, which was executing at snapshot time: its core-to-surface values should move toward mine (4.11645 K (a), 3.44870 K (b)). If refine = 2 halves the element size, a second-order scheme would give about 4.1182 K (a) and 3.4492 K (b), and a first-order one about 4.1199 K and 3.4497 K. A value moving away from mine would point to something other than mesh error.

