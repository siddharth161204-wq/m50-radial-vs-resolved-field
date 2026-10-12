"""Write comparison.md from comparison.json, the study snapshot, results.json and hottest_check.json."""
import csv, json, os

C = json.load(open("comparison.json"))
meta = json.load(open("comparison_meta.json"))
F = json.load(open("results.json"))["final"]
snap_time = open("study_snapshot_time.txt").read().strip()
rows = [r for r in csv.DictReader(open("study_results_3d_snapshot.csv"))
        if r.get("heat") == "Chen2020_m5C_2C" and r.get("when") == "end"
        and r.get("refine") in ("1.0", "1") and r.get("props") == "registered"]
byk = {(r["cell"], r["bc"]): r for r in rows}
hot = json.load(open("hottest_check.json")) if os.path.exists("hottest_check.json") else {}

req = [c for c in C if c.get("group") == "requested"]
ext = [c for c in C if c.get("group") == "extra"]
L = []
L.append("## Comparison with the study's results_3d.csv")
L.append("")
L.append(f"Snapshot of results/results_3d.csv taken {snap_time} (file last modified {meta.get('source_mtime', 'unknown')}; saved here as "
         "study_results_3d_snapshot.csv). Rows used: heat = Chen2020_m5C_2C, when = end, refine = 1.0, props = registered.")
L.append("")
pres = ", ".join(f"{c} ({b})" for c, b in meta["present"])
miss = ", ".join(f"({b}) {c}" for c, b in meta["missing"])
L.append(f"Present in the study file: {pres}. Missing: {miss or 'none'}. At snapshot time the study's 4680 run and a refine = 2 run of the "
         "21700 (a, b) were still executing; re-run `python3 compare_study.py && python3 write_comparison_md.py && python3 write_report.py` "
         "when more rows land. My values for the missing cases are in the tables above.")
L.append("")
worst = max((abs(c["pct_of_my_dTcs"]) for c in req if "pct_of_my_dTcs" in c), default=None)
allin = all(c.get("within_0p5pct_of_dTcs", True) for c in C if "within_0p5pct_of_dTcs" in c)
counts_ok = all(c.get("match", True) for c in C if "match" in c)
L.append(f"**Verdict: {'agreement' if (allin and counts_ok) else 'DISAGREEMENT'}.** Every requested quantity present for (a) and (b) 21700 agrees with mine within "
         f"{worst:.3f} % of the core-to-surface difference ({'all inside' if allin else 'NOT all inside'} the 0.5 % target), and the counts of units "
         f"over 1 K {'match' if counts_ok else 'DO NOT match'}.")
L.append("")
L.append("| Case | Study column | Study | Mine | Study minus mine | As % of my core-to-surface |")
L.append("|---|---|---|---|---|---|")
for c in req + ext:
    if c.get("study") is None:
        continue
    pct = f"{c['pct_of_my_dTcs']:+.3f} %" if "pct_of_my_dTcs" in c else ("match" if c.get("match") else ("MISMATCH" if "match" in c else "ratio"))
    tag = "" if c["group"] == "requested" else " (extra)"
    if c["column"] == "units_n_units_over_1K":
        L.append(f"| ({c['bc']}) {c['cell']} | {c['column']} | {int(c['study'])} | {int(c['mine'])} | {int(c['study'] - c['mine'])} | {pct} |")
    else:
        L.append(f"| ({c['bc']}) {c['cell']} | {c['column']}{tag} | {c['study']:.6f} | {c['mine']:.6f} | {c['study_minus_mine']:+.6f} | {pct} |")
L.append("")
L.append("Notes on the comparison:")
L.append("")
a = {c["column"]: c for c in C if c.get("bc") == "a" and c.get("column")}
b = {c["column"]: c for c in C if c.get("bc") == "b" and c.get("column")}
if a and b:
    L.append(f"1. The study's 3D core-to-surface difference is higher than mine by {a['dT_core_surface_3d_K']['study_minus_mine']:.4f} K in (a) and "
             f"{b['dT_core_surface_3d_K']['study_minus_mine']:.4f} K in (b). Almost all of it is in the core temperature "
             f"({a['T_core_mid_3d_C']['study_minus_mine']:+.4f} K and {b['T_core_mid_3d_C']['study_minus_mine']:+.4f} K); the mid-height surface agrees "
             f"within {max(abs(a['T_surface_mid_3d_C']['study_minus_mine']), abs(b['T_surface_mid_3d_C']['study_minus_mine'])):.4f} K. "
             "My own grid and time errors are about 1e-5 K, so the gap is the study's discretisation error at refine = 1.0. It is inside the 0.5 % target.")
    asym = {k: float(byk[("21700", k)]["dT_axial_top_K"]) - float(byk[("21700", k)]["dT_axial_bottom_K"]) for k in ("a", "b", "a_eq") if ("21700", k) in byk}
    meanab = {k: 0.5 * (float(byk[("21700", k)]["dT_axial_top_K"]) + float(byk[("21700", k)]["dT_axial_bottom_K"])) for k in ("a", "b") if ("21700", k) in byk}
    L.append(f"2. The problem is symmetric about mid-height, and my bottom and top axial differences are equal to 1e-13 K. The study's are not: its T(0,0) is "
             f"warmer than its T(0,H) by {asym.get('a', float('nan')):.4f} K in (a), {asym.get('b', float('nan')):.4f} K in (b)"
             + (f" and {asym['a_eq']:.4f} K in a_eq" if "a_eq" in asym else "") +
             ", the same sign every time. That points to an asymmetric mesh or solver bias, not to noise. The study's dT_axial_K equals its top value, so it sits "
             f"{a['dT_axial_K']['study_minus_mine']:.4f} K (a) and {b['dT_axial_K']['study_minus_mine']:.4f} K (b) above my symmetric value. The mean of its bottom "
             f"and top values agrees with mine to {meanab['a'] - F['a_21700']['dT_axial_bot_K']:+.5f} K (a) and {meanab['b'] - F['b_21700']['dT_axial_bot_K']:+.5f} K (b).")
    if hot:
        ra = byk.get(("21700", "a"))
        L.append(f"3. Hottest point: mine is on the axis at mid-height in both cases ((a): {hot['a']['hottest_T_C']:.6f} C at r = {hot['a']['hottest_r_mm']:.3f} mm, "
                 f"z = {hot['a']['hottest_z_mm']:.3f} mm; (b): z = {hot['b']['hottest_z_mm']:.3f} mm, on the 180 x 264 grid; field symmetric about mid-height to "
                 f"{max(hot['a']['max_abs_T_minus_mirror_K'], hot['b']['max_abs_T_minus_mirror_K']):.1e} K). The study puts the (a) hottest point at z = "
                 f"{float(ra['hottest_z_mm']):.3f} mm, {float(ra['hottest_z_mm']) - 35.05:.3f} mm off mid-plane. That fits note 2 and a very flat axial plateau; "
                 f"the study's hottest value is only {float(ra['hottest_T_C']) - float(ra['T_core_mid_3d_C']):.1e} K above its own mid-height core value.")
    L.append(f"4. Unit statistics: the study's mean offset is larger than mine by {a['units_mean_offset_1d_minus_3d_K']['study_minus_mine']:.4f} K (a) and "
             f"{b['units_mean_offset_1d_minus_3d_K']['study_minus_mine']:.4f} K (b). Its 3D unit spread is larger by {a['units_spread_3d_K']['study_minus_mine']:.4f} K and "
             f"{b['units_spread_3d_K']['study_minus_mine']:.4f} K, and its 3D roll mean is cooler by {-a['T_roll_mean_3d_C']['study_minus_mine']:.4f} K and "
             f"{-b['T_roll_mean_3d_C']['study_minus_mine']:.4f} K. The counts over 1 K match (0 and 31). In (b) my unit nearest the threshold is at "
             f"{F['b_21700']['offsets_1d_minus_3d']['closest_to_1K']:.4f} K, so the count is robust to differences of this size.")
    L.append(f"5. The study's 1D model is within {a['dT_core_surface_1d_K']['study_minus_mine']:.5f} K of my exact Bessel-series core-to-surface difference "
             f"({100 * a['dT_core_surface_1d_K']['study_minus_mine'] / F['1D_21700']['dT_core_surface_K']:.3f} %). Its unit spread is within "
             f"{a['units_spread_1d_K']['study_minus_mine']:.5f} K and its core, surface and mean temperatures are within 0.0007 K.")
if ("21700", "a_eq") in byk:
    r = byk[("21700", "a_eq")]
    one = F["1D_21700"]
    d_cs = float(r["dT_core_surface_3d_K"]) - one["dT_core_surface_K"]
    d_core = float(r["T_core_mid_3d_C"]) - one["T_core_mid_C"]
    d_surf = float(r["T_surface_mid_3d_C"]) - one["T_surf_mid_C"]
    d_mean = float(r["T_roll_mean_3d_C"]) - one["vol_mean_C"]
    d_spr = float(r["units_spread_3d_K"]) - one["units_spread_K"]
    L.append(f"6. Information only: the study also has an a_eq row, which I was not asked to compute and whose definition I have not seen. Its name and its "
             f"near-zero axial differences ({float(r['dT_axial_bottom_K']):+.4f} K and {float(r['dT_axial_top_K']):+.4f} K) suggest a 3D run set up to reproduce "
             "the 1D model. If that is right, comparing it with my exact 1D solution isolates the study's 3D discretisation error: core-to-surface "
             f"{d_cs:+.4f} K, core {d_core:+.4f} K, surface {d_surf:+.4f} K, roll mean {d_mean:+.4f} K, unit spread {d_spr:+.4f} K. That is the same signature as the "
             "(a) and (b) gaps in notes 1 and 4, which supports reading those gaps as mesh error rather than a difference in physics or set-up. "
             "(My 3D code reproduces the 1D solution to better than 1e-12 K when the shell's in-plane conduction and end shells are switched off; see test_basic.log.)")
if a and b:
    pa2 = F["a_21700"]["dT_core_surface_K"] + a["dT_core_surface_3d_K"]["study_minus_mine"] / 4
    pb2 = F["b_21700"]["dT_core_surface_K"] + b["dT_core_surface_3d_K"]["study_minus_mine"] / 4
    pa1 = F["a_21700"]["dT_core_surface_K"] + a["dT_core_surface_3d_K"]["study_minus_mine"] / 2
    pb1 = F["b_21700"]["dT_core_surface_K"] + b["dT_core_surface_3d_K"]["study_minus_mine"] / 2
    L.append(f"7. Prediction for the study's refine = 2 run, which was executing at snapshot time: its core-to-surface values should move toward mine "
             f"({F['a_21700']['dT_core_surface_K']:.5f} K (a), {F['b_21700']['dT_core_surface_K']:.5f} K (b)). If refine = 2 halves the element size, a "
             f"second-order scheme would give about {pa2:.4f} K (a) and {pb2:.4f} K (b), and a first-order one about {pa1:.4f} K and {pb1:.4f} K. A value "
             "moving away from mine would point to something other than mesh error.")
open("comparison.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
