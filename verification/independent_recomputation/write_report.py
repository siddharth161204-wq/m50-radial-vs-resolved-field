"""Assemble REPORT.md: status line, own numbers, convergence evidence, problems, and (if present)
the comparison with the study written by compare_study.py (comparison.md)."""
import json, os

T = json.load(open("report_tables.json"))
R = json.load(open("results.json"))
F = R["final"]

status_path = "status_line.txt"
status = open(status_path).read().strip() if os.path.exists(status_path) else \
    "STATUS: own numbers complete and converged; comparison with the study not yet run."


def g(k, m):
    return F[k][m]


sens = R.get("rhocp_sensitivity", [])
sens_txt = "; ".join(f"({s['case']}) {s['cell']}: core-to-surface changes by {s['d_dT_core_surface_K']:.2e} K, volume mean by {s['d_vol_mean_K']:.2e} K"
                     for s in sens) if sens else "not run"

d_extra = F.get("d_21700", {}).get("extra_1d_h25")

lines = []
lines.append("# Independent check: 1D radial model vs resolved (r, z) field, Chen2020 heat at -5 C, 2C")
lines.append("")
lines.append(status)
lines.append("")
lines.append("All numbers below were computed with my own code in this folder before the study's results file was opened. "
             "Nothing under the study's src or inputs folders, or under /home/claude/ext, was opened or imported; the only study file read "
             "before my numbers existed was results/heat/Chen2020_m5C_2C.csv.")
lines.append("")
lines.append("## Method in brief")
lines.append("")
lines.append("- Heat source: q(t) = Q(t) / (pi 0.01055^2 0.0701) with Q = heat_total_W, linear in time between the 1708 samples "
             "(1 s spacing, last interval 0.7446 s); end time 1706.7446 s. The same q(t) in W/m3 is applied to the 4680. "
             "Generated heat: 6506.479 J (21700), 35291.391 J (4680).")
lines.append("- Primary 3D solver (scheme V): vertex-centred finite volumes on a uniform axisymmetric (r, z) grid with nodes on r = 0, r = R, "
             "z = 0, z = H and z = H/2. Radial conductance k_r 2 pi r_face L / dr, axial k_z A / dz. The shell lives on the boundary nodes: heat "
             "capacity 841.7358 J/(m2 K) times the node's share of outer area, in-plane links k t 2 pi R / dz along the side and "
             "k t 2 pi r_face / dr along the end faces, with the two rim nodes belonging to both the side and the end-face shell (half a "
             "side segment plus the outermost half annulus), so shell conduction is continuous around the rim. Convection h times the node's "
             "outer area: side only in (a), side and ends in (b) and (d).")
lines.append("- Time integration: Crank-Nicolson at dt = 1 s with a Rannacher start (first two steps replaced by four backward-Euler half "
             "steps); each step uses the exact mean of the piecewise-linear q(t), so the generated heat is exact.")
lines.append("- Outputs: T(0, H/2), T(R, H/2), T(0, 0), T(0, H) are node values. Unit averages are exact integrals of the bilinear "
             "interpolant over each equal-thickness annulus (45 or 111) and the full height. Volume mean is the control-volume sum over the "
             "roll. Energy: generated = exact integral of q times pi R^2 H; lost = trapezoidal time integral of the convective loss; stored = "
             "sum of node capacities (roll and shell) times the temperature rise.")
lines.append("- 1D model: solved semi-analytically as a Bessel series in J0(beta_n r) whose eigenvalue condition includes the shell heat "
             "capacity, x J1(x) = (Bi - sigma x^2) J0(x) with Bi = h R / k_r and sigma = C_shell / (rho cp R), 40000 modes, exact time "
             "convolution with the piecewise-linear q(t). A 1D finite-volume ladder converges onto it at second order.")
lines.append("- Cross-check 3D solver (scheme C): cell-centred finite volumes with separate zero-volume shell nodes, half-cell links to the "
             "roll and a series corner link around the rim. Different node placement, shell coupling and rim treatment from scheme V.")
lines.append("- rho cp = 2938.7 x 842.4 = 2475560.88 J/(m3 K) (see Problems).")
lines.append("")
lines.append("## My numbers at the end of discharge (t = 1706.7446 s)")
lines.append("")
lines.append("1D values are from the Bessel series; 3D values are from scheme V on the finest grid (21700: 360 x 528; 4680: 444 x 344), dt = 1 s. "
             "They are accurate to about 1e-5 K (worst case 1.3e-4 K, see Convergence evidence). Every unit's temperature and offset is in "
             "units_end_21700.csv and units_end_4680.csv.")
lines.append("")
lines.append(T["main"])
lines.append("")
lines.append("Unit offsets (1D unit temperature minus 3D unit average, unweighted statistics over the units):")
lines.append("")
lines.append(T["offsets"])
lines.append("")
near = []
for k in ("a_21700", "b_21700", "a_4680", "b_4680"):
    o = F.get(k, {}).get("offsets_1d_minus_3d")
    if o and o["units_within_0p05K_of_1K"]:
        near.append(f"{k.replace('_', ' ')}: " + ", ".join(f"unit {u} at {v:.4f} K" for u, v in o["units_within_0p05K_of_1K"]))
if near:
    lines.append("Units whose offset lies within 0.05 K of the 1 K threshold (the count is sensitive to these): " + "; ".join(near) + ".")
    lines.append("")
lines.append("Energy balance:")
lines.append("")
lines.append(T["energy"])
lines.append("")
lines.append("The 1D energies are per unit height multiplied by H. The 3D balance closes to round-off because the scheme is conservative "
             "and the source integral is exact; it confirms the assembly (volumes, capacities, convective areas) rather than accuracy.")
lines.append("")
lines.append("## Convergence evidence")
lines.append("")
lines.append("### Space (3D, scheme V)")
lines.append("")
lines.append(T["ladders"])
lines.append("")
lines.append("### Time step (3D, scheme V)")
lines.append("")
lines.append(T["timestep"])
lines.append("")
lines.append("### 1D finite volumes vs the Bessel series")
lines.append("")
lines.append(T["oned"])
lines.append("")
lines.append("### Second 3D discretisation (scheme C) vs scheme V finest grid")
lines.append("")
lines.append(T["cross"])
lines.append("")
lines.append("The scheme C minus scheme V differences fall by a factor of about 3.6 (21700) and 2.8 (4680) per halving of the scheme C grid "
             "(about 4 for the 4680 once scheme V's own remaining error of about 7e-5 K is allowed for), i.e. both schemes converge to the same "
             "field at second order. All differences stay below 1e-3 K, far inside the 0.5 % target, which also checks the treatment of the shell "
             "around the rim, where the two schemes differ most.")
lines.append("")
lines.append("Verdict on accuracy: every Richardson error estimate for the core-to-surface difference is below 1e-4 K and below 4e-6 of the "
             "difference itself, more than three orders of magnitude inside the 0.5 % target; the largest estimate for any reported quantity is "
             "1.3e-4 K (the 4680 (a) volume mean). Time-step error at dt = 1 s is below 1e-6 K.")
lines.append("")
lines.append("## Problems hit and notes")
lines.append("")
lines.append(f"1. The task text says rho cp = 2475540, but 2938.7 x 842.4 = 2475560.88 (8.5 ppm higher). I used the product. "
             f"Re-running with 2475540: {sens_txt}. Immaterial.")
if d_extra:
    o25 = F["d_21700"]["extra_offsets_vs_1d_h25"]
    lines.append(f"2. Case (d) offsets, as specified, compare the h = 400 1D model with the h = 25 3D field, so they measure the change of h, not "
                 f"the 1D approximation (mean {F['d_21700']['offsets_1d_minus_3d']['mean']:.3f} K). For reference, a 1D model with h = 25 gives "
                 f"core-to-surface {d_extra['dT_core_surface_K']:.4f} K, unit spread {d_extra['units_spread_K']:.4f} K, and offsets against (d) of "
                 f"mean {o25['mean']:.4f} K, min {o25['min']:.4f} K, max {o25['max']:.4f} K, {o25['n_over_1K']} units over 1 K.")
lines.append("3. The count of units with offset above 1 K sits on a knife edge in (a) 4680 (a unit at about 0.999 K) and is close in (b) 21700; "
             "a code with slightly different discretisation error can legitimately differ by one unit there.")
lines.append("4. The machine has 2 cores and the study's own 3D runs were using both throughout, so my runs were slower; results are unaffected. "
             "I saw those processes only as command lines in the process list and did not open their files.")
lines.append("5. Plain Crank-Nicolson oscillation risk from the stiff shell start-up (shell-roll equilibration time about 0.2 s) was handled by "
             "the Rannacher start; dropping it changes the core-to-surface difference by less than 2e-7 K.")
lines.append("")
lines.append("## Files")
lines.append("")
lines.append("- Code: params.py (constants, heat source), network.py (assembly, Crank-Nicolson integrator, energy bookkeeping), discretise.py "
             "(schemes V and C, 1D finite volumes), analytic_1d.py (Bessel series), run_all.py (all production runs), hottest_check.py, "
             "test_basic.py (verification tests; output in test_basic.log).")
lines.append("- My results: runs.jsonl (every run, including unit averages), results.json and results.csv (headline numbers, convergence, "
             "offsets), convergence.csv, units_end_21700.csv, units_end_4680.csv, hottest_check.json, run_all.log.")
lines.append("- Comparison: compare_study.py, write_comparison_md.py, comparison.csv, comparison.json, comparison.md, "
             "study_results_3d_snapshot.csv (the study rows exactly as compared).")
lines.append("")
if os.path.exists("comparison.md"):
    lines.append(open("comparison.md").read().strip())
    lines.append("")
open("REPORT.md", "w").write("\n".join(lines) + "\n")
print("REPORT.md written,", len(lines), "lines")
