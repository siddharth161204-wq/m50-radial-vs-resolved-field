#!/usr/bin/env python3
"""Stage 4, V3 (D25): the main case's shares and share spread recomputed by a separate routine with explicit loops
(no NumPy), from results/stage4_RT.csv and results/stage4_unit_temps.json, against results/stage4_units.csv and
results/stage4_errors.csv. Registered choices: ORegan2022, 100 % state of charge, time average, area weights.
python3 src/stage4_v3.py -> results/stage4_checks_v3.json"""
import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

R = C.RESULTS


def main():
    grid = []
    for r in csv.DictReader(open(os.path.join(R, "stage4_RT.csv"))):
        if r["set"] == "ORegan2022" and float(r["soc"]) == 1.0:
            grid.append((float(r["T_C"]), float(r["R_ohm"])))
    grid.sort()
    case = json.load(open(os.path.join(R, "stage4_unit_temps.json")))["cases"]["21700_b_m5C_2C"]
    Rc = C.cell_constants("21700")["R"]
    out = {}
    for field in ("radial", "corrected", "resolved"):
        temps = case[field]["time_average"]
        n = len(temps)
        res = []
        for T in temps:                                   # ln R linear between the two bracketing grid points
            k = 0
            while grid[k + 1][0] < T:
                k += 1
            (T0, R0), (T1, R1) = grid[k], grid[k + 1]
            f = (T - T0) / (T1 - T0)
            res.append(math.exp((1 - f) * math.log(R0) + f * math.log(R1)))
        w = []
        for i in range(n):
            ri, ro = Rc * i / n, Rc * (i + 1) / n
            w.append((ro * ro - ri * ri) / (Rc * Rc))
        norm = 0.0
        for i in range(n):
            norm += w[i] / res[i]
        shares = [(1.0 / res[i]) / norm for i in range(n)]
        rmean = 0.0
        for i in range(n):
            rmean += w[i] * res[i]
        out[field] = {"R_mean_mOhm": 1e3 * rmean, "spread": max(shares) - min(shares), "inner": shares[0],
                      "outer": shares[-1], "shares": shares}
    units = [r for r in csv.DictReader(open(os.path.join(R, "stage4_units.csv")))
             if r["case"] == "21700_b_m5C_2C" and r["set"] == "ORegan2022" and float(r["soc"]) == 1.0 and r["reading"] == "time_average"]
    errs = {(r["field"]): r for r in csv.DictReader(open(os.path.join(R, "stage4_errors.csv")))
            if r["case"] == "21700_b_m5C_2C" and r["set"] == "ORegan2022" and float(r["soc"]) == 1.0
            and r["reading"] == "time_average" and r["weighting"] == "area"}
    chk = {}
    for field in ("radial", "corrected", "resolved"):
        stored = [float(r["share_area_weighted"]) for r in units if r["field"] == field]
        chk[f"{field}_max_abs_share_diff"] = max(abs(a - b) for a, b in zip(stored, out[field]["shares"]))
    for field in ("radial", "corrected"):
        sp_rel = out[field]["spread"] / out["resolved"]["spread"] - 1
        rm_rel = out[field]["R_mean_mOhm"] / out["resolved"]["R_mean_mOhm"] - 1
        chk[f"{field}_spread_rel"] = {"hand": sp_rel, "stored": float(errs[field]["share_spread_rel_error"])}
        chk[f"{field}_R_mean_rel"] = {"hand": rm_rel, "stored": float(errs[field]["R_mean_rel_error"])}
    chk["agree"] = (all(chk[f"{f}_max_abs_share_diff"] < 5e-6 for f in ("radial", "corrected", "resolved"))
                    and all(abs(v["hand"] - v["stored"]) < 1e-5 for k, v in chk.items() if isinstance(v, dict)))
    for f in out:
        out[f].pop("shares")
    json.dump({"hand": out, "check": chk}, open(os.path.join(R, "stage4_checks_v3.json"), "w"), indent=1)
    print(json.dumps(chk, indent=1))


if __name__ == "__main__":
    main()
