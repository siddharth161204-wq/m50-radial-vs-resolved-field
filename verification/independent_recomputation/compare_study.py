"""Compare my numbers (results.json) with the study's results_3d.csv.

Run only after my own numbers exist. Re-runnable: pass a path to compare against a newer copy
(default: the live study file; a snapshot is copied into this folder each run).
Rows used: heat = Chen2020_m5C_2C, when = end, refine = 1.0, props = registered.
"""
import csv, json, shutil, sys, time
import numpy as np

SRC = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/m50-radial-vs-resolved-field/results/results_3d.csv"
import os
src_mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(os.path.getmtime(SRC))) + " UTC"
shutil.copy(SRC, "study_results_3d_snapshot.csv")
open("study_snapshot_time.txt", "w").write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
rows = [r for r in csv.DictReader(open("study_results_3d_snapshot.csv"))
        if r.get("heat") == "Chen2020_m5C_2C" and r.get("when") == "end"
        and r.get("refine") in ("1.0", "1") and r.get("props") == "registered"]
F = json.load(open("results.json"))["final"]

# (study column, my key path, kind) ; kind "T" = temperature difference, "n" = count, "rel" = ratio
REQ = [
    ("dT_core_surface_3d_K", ("3d", "dT_core_surface_K"), "T"),
    ("dT_axial_K", ("3d", "dT_axial_bot_K"), "T"),
    ("dT_axial_bottom_K", ("3d", "dT_axial_bot_K"), "T"),
    ("dT_axial_top_K", ("3d", "dT_axial_top_K"), "T"),
    ("units_spread_3d_K", ("3d", "units_spread_K"), "T"),
    ("units_mean_offset_1d_minus_3d_K", ("off", "mean"), "T"),
    ("units_min_offset_K", ("off", "min"), "T"),
    ("units_max_offset_K", ("off", "max"), "T"),
    ("units_n_units_over_1K", ("off", "n_over_1K"), "n"),
    ("dT_core_surface_1d_K", ("1d", "dT_core_surface_K"), "T"),
    ("units_spread_1d_K", ("1d", "units_spread_K"), "T"),
]
EXTRA = [
    ("T_core_mid_3d_C", ("3d", "T_core_mid_C"), "T"),
    ("T_surface_mid_3d_C", ("3d", "T_surf_mid_C"), "T"),
    ("T_roll_mean_3d_C", ("3d", "vol_mean_C"), "T"),
    ("T_core_1d_C", ("1d", "T_core_mid_C"), "T"),
    ("T_surface_1d_C", ("1d", "T_surf_mid_C"), "T"),
    ("T_mean_1d_C", ("1d", "vol_mean_C"), "T"),
    ("units_max_abs_diff_K", ("off", "max_abs"), "T"),
    ("axial_over_radial", ("ratio", None), "rel"),
    ("units_spread_change_rel", ("spreadrel", None), "rel"),
]


def mine(cell, bc, path):
    k3 = f"{bc}_{cell}"; k1 = f"1D_{cell}"
    if k3 not in F:
        return None
    src, key = path
    if src == "3d":
        return F[k3][key]
    if src == "1d":
        return F[k1][key]
    if src == "off":
        return F[k3]["offsets_1d_minus_3d"][key]
    if src == "ratio":
        return F[k3]["dT_axial_bot_K"] / F[k3]["dT_core_surface_K"]
    if src == "spreadrel":
        return (F[k3]["units_spread_K"] - F[k1]["units_spread_K"]) / F[k1]["units_spread_K"]


out = []
for r in rows:
    cell, bc = r["cell"], r["bc"]
    k3 = f"{bc}_{cell}"
    if k3 not in F:
        out.append(dict(cell=cell, bc=bc, column="(row present in study, case not in my task)", study=None, mine=None))
        continue
    dts = F[k3]["dT_core_surface_K"]
    for group, lst in (("requested", REQ), ("extra", EXTRA)):
        for col, path, kind in lst:
            if col not in r or r[col] in ("", None):
                continue
            s = float(r[col]); m = mine(cell, bc, path)
            d = s - m
            rec = dict(cell=cell, bc=bc, group=group, column=col, study=s, mine=m, study_minus_mine=d)
            if kind == "T":
                rec["rel_to_own_value"] = d / m if m != 0 else None
                rec["pct_of_my_dTcs"] = 100 * d / dts
                rec["within_0p5pct_of_dTcs"] = abs(d) <= 0.005 * dts
            elif kind == "n":
                rec["match"] = int(round(s)) == int(m)
            else:
                rec["rel_to_own_value"] = d / m if m != 0 else None
            out.append(rec)

json.dump(out, open("comparison.json", "w"), indent=1)
cols = ["cell", "bc", "group", "column", "study", "mine", "study_minus_mine", "rel_to_own_value",
        "pct_of_my_dTcs", "within_0p5pct_of_dTcs", "match"]
with open("comparison.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for rec in out:
        w.writerow(rec)

present = sorted({(r["cell"], r["bc"]) for r in rows})
wanted = [("21700", "a"), ("21700", "b"), ("21700", "d"), ("4680", "a"), ("4680", "b")]
missing = [w_ for w_ in wanted if w_ not in present]
print("study rows present (cell, bc):", present)
print("requested but missing in study file:", missing)
for rec in out:
    if rec.get("study") is None:
        print(rec)
        continue
    extra = ""
    if "pct_of_my_dTcs" in rec:
        extra = f"  ({rec['pct_of_my_dTcs']:+.3f} % of my dTcs; within 0.5 %: {rec['within_0p5pct_of_dTcs']})"
    if "match" in rec:
        extra = f"  match: {rec['match']}"
    print(f"{rec['cell']} {rec['bc']:5s} {rec['group']:9s} {rec['column']:33s} study={rec['study']:.6f} mine={rec['mine']:.6f} diff={rec['study_minus_mine']:+.6f}{extra}")
json.dump(dict(present=present, missing=missing, source=SRC, source_mtime=src_mtime), open("comparison_meta.json", "w"))
