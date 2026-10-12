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
