#!/usr/bin/env python3
"""Compare the resolved cell with the one-dimensional model, score P1 to P5 and collect the checks (D10, D11).

Reads results/fields/*.json and re-runs the one-dimensional model (it is cheap and deterministic) to obtain its
field at exactly the times of each three-dimensional snapshot. Writes:
  results/results_3d.csv        one row per run and output time (end of discharge, largest core-to-surface)
  results/comparison_vs_a.csv   (b), (c), (d) against (a) on the same heat and time
  results/units_*.csv           unit temperatures, one- and three-dimensional, for the scored cases
  results/verification.json     V1 (equivalence and full can), V2, V3
  results/scorecard.json, results/scorecard.md
Usage: python3 src/analyse.py
"""
import csv
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402

FIELDS = os.path.join(C.RESULTS, "fields")
_cache = {}


def one_d(heat, cell, props_kind, times):
    key = (heat, cell, props_kind, tuple(sorted(times)))
    if key not in _cache:
        allp = C.roll_properties()
        props = allp["registered"] if props_kind == "registered" else next(r for r in allp["table"] if r["T_C"] == -5.0)
        q, t_end, _ = R1.load_heat(heat)
        m = R1.Radial1D(cell, props=props, can=True)
        r = m.run(q, t_end, R1.amb_of(heat), snap_times=times)
        _cache[key] = (r, m)
    return _cache[key]


def load_runs():
    runs = {}
    for p in sorted(glob.glob(os.path.join(FIELDS, "*.json"))):
        d = json.load(open(p))
        key = (d["cell"], d["bc"], d.get("refine", 1.0), d.get("props", "registered"), d["heat"])
        runs[key] = d
    return runs


def unit_compare(s3, s1):
    u3, u1 = np.array(s3["units"]), np.array(s1["units"])
    off = u1 - u3
    return {"max_abs_diff_K": float(np.abs(off).max()), "n_units_over_1K": int((np.abs(off) > 1.0).sum()),
            "mean_offset_1d_minus_3d_K": float(off.mean()), "min_offset_K": float(off.min()),
            "max_offset_K": float(off.max()), "spread_3d_K": float(u3.max() - u3.min()),
            "spread_1d_K": float(u1.max() - u1.min()),
            "spread_change_rel": float((u3.max() - u3.min()) / (u1.max() - u1.min()) - 1)}


def profile_compare(s3, s1, which="rings"):
    r3 = np.array(s3[f"{which}_r"])
    T3 = np.array(s3[f"{which}_T"])
    T1 = np.interp(r3, np.array(s1["profile_r"]), np.array(s1["profile_T"]))
    d = T3 - T1
    return {"max_abs_diff_K": float(np.abs(d).max()), "rel_to_1d_dT": float(np.abs(d).max() / s1["dT_core_surface"]),
            "n_radii": int(len(r3))}


def main():
    runs = load_runs()
    rows, vs_a, v1, v2, units_out = [], [], {}, {}, {}
    for key, d in runs.items():
        cell, bc, refine, props, heat = key
        times = [d["end"]["t"], d["max_dT"]["t"]]
        r1, _m = one_d(heat, cell, props, times)
        v2[f"{cell}|{bc}|refine {refine:g}|{props}|{heat}"] = d["energy_J"]["residual_rel"]
        for when in ("end", "max_dT"):
            s3 = d[when]
            s1 = r1["snaps"][s3["t"]]
            uc = unit_compare(s3, s1)
            row = {"cell": cell, "bc": bc, "refine": refine, "props": props, "heat": heat, "when": when,
                   "t_s": s3["t"], "dT_core_surface_3d_K": s3["dT_core_surface"],
                   "dT_axial_bottom_K": s3["dT_axial_bottom"], "dT_axial_top_K": s3["dT_axial_top"],
                   "dT_axial_K": s3["dT_axial"], "axial_over_radial": s3["dT_axial"] / s3["dT_core_surface"],
                   "hottest_T_C": s3["hottest"]["T"], "hottest_r_mm": s3["hottest"]["r_mm"],
                   "hottest_z_mm": s3["hottest"]["z_mm"], "T_roll_mean_3d_C": s3["T_roll_mean"],
                   "T_core_mid_3d_C": s3["T_core_mid"], "T_surface_mid_3d_C": s3["T_surface_mid"],
                   "dT_core_surface_1d_K": s1["dT_core_surface"], "T_mean_1d_C": s1["T_mean"],
                   "T_core_1d_C": s1["T_core"], "T_surface_1d_C": s1["T_surface"],
                   **{f"units_{k}": v for k, v in uc.items()}}
            rows.append(row)
            if bc in ("a_eq", "a"):
                v1[f"{cell}|{bc}|refine {refine:g}|{props}|{heat}|{when}"] = {
                    "rings": profile_compare(s3, s1, "rings"), "fine": profile_compare(s3, s1, "profile"),
                    "dT_cs_3d_K": s3["dT_core_surface"], "dT_cs_1d_K": s1["dT_core_surface"]}
            if (refine == 1.0 and props == "registered" and heat == "Chen2020_m5C_2C" and when == "end"
                    and bc in ("a", "b", "c", "d")):
                units_out[f"{cell}_{bc}"] = {"r_mid_mm": (1e3 * 0.5 * (np.array(R1.Radial1D(cell).unit_edges[:-1]) +
                                                              np.array(R1.Radial1D(cell).unit_edges[1:]))).tolist(),
                                             "units_3d": s3["units"], "units_1d": s1["units"]}
        if bc in ("b", "c", "d"):
            ka = (cell, "a", refine, props, heat)
            if ka in runs:
                da = runs[ka]
                for when in ("end",):
                    sx, sa = d[when], da[when]
                    ux, ua = np.array(sx["units"]), np.array(sa["units"])
                    vs_a.append({"cell": cell, "bc": bc, "refine": refine, "props": props, "heat": heat, "when": when,
                                 "t_s": sx["t"], "dT_cs_ratio_to_a": sx["dT_core_surface"] / sa["dT_core_surface"],
                                 "dT_cs_change_rel": sx["dT_core_surface"] / sa["dT_core_surface"] - 1,
                                 "dT_axial_K": sx["dT_axial"], "dT_axial_a_K": sa["dT_axial"],
                                 "units_mean_shift_K": float((ux - ua).mean()),
                                 "units_max_abs_shift_K": float(np.abs(ux - ua).max()),
                                 "units_n_over_1K": int((np.abs(ux - ua) > 1.0).sum()),
                                 "spread_x_K": float(ux.max() - ux.min()), "spread_a_K": float(ua.max() - ua.min()),
                                 "T_roll_mean_shift_K": sx["T_roll_mean"] - sa["T_roll_mean"]})
    # V3: refinement
    v3 = {}
    for key, d in runs.items():
        cell, bc, refine, props, heat = key
        if refine != 1.0:
            base = runs.get((cell, bc, 1.0, props, heat))
            if base:
                e2, e1 = d["end"], base["end"]
                u2, u1 = np.array(e2["units"]), np.array(e1["units"])
                v3[f"{cell}|{bc}|{heat}"] = {
                    "dT_cs_refined_K": e2["dT_core_surface"], "dT_cs_base_K": e1["dT_core_surface"],
                    "dT_cs_change_rel": e2["dT_core_surface"] / e1["dT_core_surface"] - 1,
                    "dT_axial_refined_K": e2["dT_axial"], "dT_axial_base_K": e1["dT_axial"],
                    "units_max_abs_change_K": float(np.abs(u2 - u1).max()),
                    "pass": abs(e2["dT_core_surface"] / e1["dT_core_surface"] - 1) < 0.05}
    os.makedirs(C.RESULTS, exist_ok=True)
    for name, data in (("results_3d.csv", rows), ("comparison_vs_a.csv", vs_a)):
        if data:
            with open(os.path.join(C.RESULTS, name), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                w.writeheader()
                for r in data:
                    w.writerow(r)
    for k, u in units_out.items():
        with open(os.path.join(C.RESULTS, f"units_{k}_2C_minus5C_end.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["unit", "r_mid_mm", "T_1d_C", "T_3d_C", "offset_1d_minus_3d_K"])
            for i, (rm, t3, t1) in enumerate(zip(u["r_mid_mm"], u["units_3d"], u["units_1d"])):
                w.writerow([i + 1, f"{rm:.4f}", f"{t1:.5f}", f"{t3:.5f}", f"{t1 - t3:.5f}"])
    v1_pass = {k: v["rings"]["rel_to_1d_dT"] <= 0.01 for k, v in v1.items()}
    ver = {"V1": v1, "V1_pass_within_1_percent": v1_pass,
           "V2_energy_residual_rel": v2, "V2_max_abs": max(abs(x) for x in v2.values()) if v2 else None,
           "V3": v3}
    with open(os.path.join(C.RESULTS, "verification.json"), "w") as f:
        json.dump(ver, f, indent=2)
    score(rows, vs_a)


def pick(rows, **kw):
    out = [r for r in rows if all(r[k] == v for k, v in kw.items())]
    return out[0] if out else None


def score(rows, vs_a):
    base = dict(refine=1.0, props="registered", heat="Chen2020_m5C_2C", when="end")
    sc = {}
    a = pick(rows, cell="21700", bc="a", **base)
    b = pick(rows, cell="21700", bc="b", **base)
    if a:
        v = a["dT_core_surface_3d_K"]
        sc["P1"] = {"value_K": v, "range": [3, 10], "central": 6, "held": bool(3 <= v <= 10)}
    if a and b:
        ch = b["dT_core_surface_3d_K"] / a["dT_core_surface_3d_K"] - 1
        ratio = b["dT_axial_K"] / b["dT_core_surface_3d_K"]
        sc["P2"] = {"change_rel": ch, "axial_over_radial_b": ratio, "clause1_held": bool(abs(ch) < 0.30),
                    "clause2_held": bool(ratio > 1 / 3), "central": {"change": 0.15, "ratio": 0.5}}
        sc["P2"]["held"] = sc["P2"]["clause1_held"] and sc["P2"]["clause2_held"]
    if b:
        mo = b["units_mean_offset_1d_minus_3d_K"]
        sc["P3"] = {"mean_offset_K": mo, "min_offset_K": b["units_min_offset_K"], "max_offset_K": b["units_max_offset_K"],
                    "spread_change_rel": b["units_spread_change_rel"], "spread_1d_K": b["units_spread_1d_K"],
                    "spread_3d_K": b["units_spread_3d_K"],
                    "clause1_held": bool(1 <= mo <= 3), "clause2_held": bool(b["units_min_offset_K"] > 0),
                    "clause3_held": bool(abs(b["units_spread_change_rel"]) < 0.20),
                    "every_offset_within_1_to_3K": bool(b["units_min_offset_K"] >= 1 and b["units_max_offset_K"] <= 3),
                    "central_offset_K": 1.5}
        sc["P3"]["held"] = sc["P3"]["clause1_held"] and sc["P3"]["clause2_held"] and sc["P3"]["clause3_held"]
    b4 = pick(rows, cell="4680", bc="b", **base)
    if b and b4:
        r21, r46 = b["axial_over_radial"], b4["axial_over_radial"]
        sc["P4"] = {"ratio_21700": r21, "ratio_4680": r46, "held": bool(r46 < r21), "central": {"4680": 0.3, "21700": 0.5}}
    d_m = pick(rows, cell="21700", bc="d", refine=1.0, props="registered", heat="Chen2020_m5C_2C", when="end")
    d_p = pick(rows, cell="21700", bc="d", refine=1.0, props="registered", heat="Chen2020_p25C_2C", when="end")
    if d_m and d_p:
        vals = {"minus5C": {"dT_cs_K": d_m["dT_core_surface_3d_K"], "dT_axial_K": d_m["dT_axial_K"]},
                "25C": {"dT_cs_K": d_p["dT_core_surface_3d_K"], "dT_axial_K": d_p["dT_axial_K"]}}
        sc["P5"] = {"values": vals, "held": bool(all(v < 1.0 for x in vals.values() for v in x.values()))}
    with open(os.path.join(C.RESULTS, "scorecard.json"), "w") as f:
        json.dump(sc, f, indent=2)
    print(json.dumps(sc, indent=1))


if __name__ == "__main__":
    main()
