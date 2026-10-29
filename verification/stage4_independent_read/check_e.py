#!/usr/bin/env python3
"""Independent check (e): the sensitivities d ln R / dT at -5, 0, 25 C (central difference over +-0.5 K) from
results/stage4_RT.csv against results/stage4_RT.json; internal consistency of the table; monotonicity and smoothness
of R(T) per set and state of charge (second and third differences of ln R, residuals of a smooth fit).
Writes check4/out_e.json."""
import csv
import json
import math
import os

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RES = os.path.join(REPO, "results")
OUT = os.path.dirname(os.path.abspath(__file__))


def main():
    rows = list(csv.DictReader(open(os.path.join(RES, "stage4_RT.csv"))))
    js = json.load(open(os.path.join(RES, "stage4_RT.json")))
    out = {"n_rows": len(rows), "groups": {}, "sens": {}, "max_sens_abs_diff": 0.0, "max_RmOhm_abs_diff": 0.0}
    groups = {}
    for r in rows:
        groups.setdefault((r["set"], float(r["soc"])), []).append(r)
    for (s, soc), g in groups.items():
        g.sort(key=lambda r: float(r["T_C"]))
        T = np.array([float(r["T_C"]) for r in g])
        R = np.array([float(r["R_ohm"]) for r in g])
        Vr = np.array([float(r["V_rest_V"]) for r in g])
        V10 = np.array([float(r["V_10s_V"]) for r in g])
        lnR = np.log(R)
        info = {"n": len(g), "T_first_last": [T[0], T[-1]],
                "grid_is_-10_to_35_step_0.5": bool(np.allclose(T, -10 + 0.5 * np.arange(91)) and len(T) == 91),
                "R_from_V_max_rel_diff": float(np.max(np.abs((Vr - V10) / 5.0 / R - 1))),
                "R_mOhm_range": [float(R.min() * 1e3), float(R.max() * 1e3)],
                "V_rest_range": [float(Vr.min()), float(Vr.max())]}
        d1 = np.diff(lnR)
        info["strictly_decreasing"] = bool(np.all(d1 < 0))
        info["n_nonnegative_first_diffs"] = int(np.sum(d1 >= 0))
        d2 = np.diff(lnR, 2)
        d3 = np.diff(lnR, 3)
        info["d2_lnR_range"] = [float(d2.min()), float(d2.max())]
        info["d2_lnR_sign_changes"] = int(np.sum(np.diff(np.sign(d2)) != 0))
        info["d3_lnR_maxabs"] = float(np.max(np.abs(d3)))
        # robust outlier test on second differences: deviation from the median of the 7 neighbours
        flags = []
        for i in range(len(d2)):
            lo, hi = max(0, i - 3), min(len(d2), i + 4)
            nb = np.delete(d2[lo:hi], i - lo)
            med = np.median(nb)
            mad = np.median(np.abs(nb - med)) + 1e-15
            z = (d2[i] - med) / mad
            if abs(z) > 10 and abs(d2[i] - med) > 1e-6:
                flags.append({"T_centre": float(T[i + 1]), "d2": float(d2[i]), "local_median": float(med), "z_mad": float(z)})
        info["d2_outliers"] = flags
        # residuals of a smooth fit (degree-8 polynomial in T) to ln R
        x = (T - T.mean()) / (T.max() - T.min())
        c = np.polyfit(x, lnR, 8)
        res = lnR - np.polyval(c, x)
        info["poly8_resid_maxabs_lnR"] = float(np.max(np.abs(res)))
        info["poly8_resid_argmax_T"] = float(T[int(np.argmax(np.abs(res)))])
        # same for V_rest
        d2v = np.diff(Vr, 2)
        info["V_rest_d2_range"] = [float(d2v.min()), float(d2v.max())]
        info["d2_lnR_by_T_sample"] = {f"{T[i+1]:g}": float(d2[i]) for i in range(0, len(d2), 10)}
        out["groups"][f"{s}|soc={soc:g}"] = info
        # sensitivities
        key = f"{s}|soc={soc:g}"
        out["sens"][key] = {}
        for Tc in (-5.0, 0.0, 25.0):
            i = int(np.where(np.isclose(T, Tc))[0][0])
            sens = (lnR[i + 1] - lnR[i - 1]) / (T[i + 1] - T[i - 1])
            st = js["sensitivity"][key][f"{Tc:g}"]
            d = sens - st["dlnR_dT_per_K"]
            dR = R[i] * 1e3 - st["R_mOhm"]
            out["sens"][key][f"{Tc:g}"] = {"mine": float(sens), "stored": st["dlnR_dT_per_K"], "diff": float(d),
                                           "R_mOhm_mine": float(R[i] * 1e3), "R_mOhm_stored": st["R_mOhm"], "R_diff": float(dR),
                                           "one_sided_minus": float(lnR[i] - lnR[i - 1]) / 0.5,
                                           "one_sided_plus": float(lnR[i + 1] - lnR[i]) / 0.5}
            out["max_sens_abs_diff"] = max(out["max_sens_abs_diff"], abs(d))
            out["max_RmOhm_abs_diff"] = max(out["max_RmOhm_abs_diff"], abs(dR))
    out["json_meta"] = {k: js[k] for k in js if k != "sensitivity"}
    json.dump(out, open(os.path.join(OUT, "out_e.json"), "w"), indent=1)
    print("rows", out["n_rows"], "groups", list(out["groups"]))
    for k, v in out["groups"].items():
        print(k, {kk: vv for kk, vv in v.items() if kk not in ("d2_lnR_by_T_sample",)})
        print("   d2 sample", v["d2_lnR_by_T_sample"])
    print("max |sens diff|", out["max_sens_abs_diff"], "max |R_mOhm diff|", out["max_RmOhm_abs_diff"])
    for k, v in out["sens"].items():
        print(k, {t: (round(x["mine"], 8), round(x["stored"], 8), x["diff"]) for t, x in v.items()})
    print(out["json_meta"])


if __name__ == "__main__":
    main()
