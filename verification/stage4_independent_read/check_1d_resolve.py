#!/usr/bin/env python3
"""Independent re-solve of the 1-D radial model (D7) and the end-corrected model (D18) from the stored heat and
properties, with my own assembly and a banded (tridiagonal) solver, to test every stored history row in
results/stage4_hist_1d.json (not only the end, which V1 tests). Also: the resolved history at t = 539.92 s against
the post-hoc matched-time statistics (D15), and smoothness checks of the resolved history.
Writes check4/out_1d_resolve.json."""
import csv
import json
import math
import os

import numpy as np
from scipy.linalg import solve_banded

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RES = os.path.join(REPO, "results")
OUT = os.path.dirname(os.path.abspath(__file__))

GEOM = {"21700": (21.1e-3 / 2, 70.1e-3, 45), "4680": (46.0e-3 / 2, 80.0e-3, 111)}
CASES = {"21700_b_m5C_2C": ("21700", "b", "m5C_2C"), "21700_b_p25C_2C": ("21700", "b", "p25C_2C"),
         "21700_b_p25C_1.25C": ("21700", "b", "p25C_1.25C"), "21700_a_m5C_2C": ("21700", "a", "m5C_2C"),
         "4680_b_m5C_2C": ("4680", "b", "m5C_2C")}
H_CONV = 400.0
SUB = 20


def props():
    p = json.load(open(os.path.join(REPO, "inputs", "properties.json")))["registered"]
    return p["rho"] * p["cp"], p["k_across"], p["k_along"]


def can_per_area():
    R, H, _ = GEOM["21700"]
    return 9e-3 * 500.0 / (2 * math.pi * R * H + 2 * math.pi * R ** 2)


def heat(cond):
    t, Q = [], []
    with open(os.path.join(RES, "heat", f"Chen2020_{cond}.csv")) as f:
        for r in csv.DictReader(f):
            t.append(float(r["t_s"]))
            Q.append(float(r["heat_total_W"]))
    R, H, _ = GEOM["21700"]
    V = math.pi * R ** 2 * H                                  # q per volume of the 21700 (D6), also for the 4680
    return np.array(t), np.array(Q) / V


def solve(cell, cond, beta, snap_times):
    rho_cp, k, kz = props()
    R, H, nu = GEOM[cell]
    N = nu * SUB
    r = np.array([R * j / N for j in range(N + 1)])
    dr = R / N
    tp = 2.0 * math.pi
    # lumped (row-sum) capacity weights: integral of phi_j r dr, exact for linear phi
    a, b = r[:-1], r[1:]
    wa, wb = tp * dr * (2 * a + b) / 6.0, tp * dr * (a + 2 * b) / 6.0
    wv = np.zeros(N + 1)
    wv[:-1] += wa
    wv[1:] += wb
    ke = tp * k * (a + b) / 2.0 / dr                       # element stiffness coefficient
    diag = np.zeros(N + 1)
    diag[:-1] += ke
    diag[1:] += ke
    off = -ke                                              # (j, j+1) and (j+1, j)
    Cap = rho_cp * wv
    Cap[-1] += can_per_area() * tp * R
    conv = np.zeros(N + 1)
    conv[-1] = H_CONV * tp * R
    sink = beta * wv
    t_q, q_arr = heat(cond)
    t_end = t_q[-1]
    n = int(math.ceil(t_end / 1.0 - 1e-9))
    dt = t_end / n
    ab = np.zeros((3, N + 1))
    ab[0, 1:] = off
    ab[1, :] = diag + Cap / dt + conv + sink
    ab[2, :-1] = off
    Ta = -5.0 if cond.startswith("m5C") else 25.0
    T = np.full(N + 1, Ta)
    # unit-average operator: integral of T r dr over each annulus (exact for P1) / integral of r dr
    U = np.zeros((nu, N + 1))
    for i in range(nu):
        for e in range(i * SUB, (i + 1) * SUB):
            U[i, e] += wa[e]
            U[i, e + 1] += wb[e]
        U[i] /= U[i].sum()
    snap_step = {int(round(ts / dt)): ts for ts in snap_times}
    snaps = {}
    for kstep in range(1, n + 1):
        t = kstep * dt
        q = float(np.interp(t, t_q, q_arr))
        rhs = Cap / dt * T + (conv + sink) * Ta + wv * q
        T = solve_banded((1, 1), ab, rhs)
        if kstep in snap_step:
            snaps[snap_step[kstep]] = U @ T
    return snaps, U @ T, t_end, dt, n


def beta_of(cell):
    kz = props()[2]
    R, H, _ = GEOM[cell]
    he = 1.0 / (1.0 / H_CONV + H / (6.0 * kz))
    return 2.0 * he / H, he


def main():
    h1 = json.load(open(os.path.join(RES, "stage4_hist_1d.json")))
    h3 = {}
    h3.update(json.load(open(os.path.join(RES, "stage4_hist_3d_21700.json"))))
    h3.update(json.load(open(os.path.join(RES, "stage4_hist_3d_4680.json"))))
    out = {"radial": {}, "corrected": {}, "beta": {}, "posthoc_539s": {}, "resolved_vs_my_corrected": {},
           "resolved_mean_vs_series_T_mean": {}}
    my_hist = {}
    for key, (cell, bc, cond) in CASES.items():
        a = h1[key]
        times = a["times"]
        # radial
        sn, end, t_end, dt, n = solve(cell, cond, 0.0, times)
        stored = np.array(a["radial"])
        mine = np.array([sn[t] for t in times])
        out["radial"][key] = {"max_abs_diff_all_rows_K": float(np.max(np.abs(mine - stored))),
                              "end_max_abs_diff_vs_radial_end_K": float(np.max(np.abs(end - np.array(a["radial_end"])))),
                              "n_steps": n, "dt": dt, "t_end": t_end}
        my_hist[(key, "radial")] = mine
        if bc == "b":
            beta, he = beta_of(cell)
            out["beta"][key] = {"mine": beta, "h_e": he, "stored": a["beta"], "diff": beta - a["beta"]}
            sn, end, *_ = solve(cell, cond, beta, times)
            stored = np.array(a["corrected"])
            mine = np.array([sn[t] for t in times])
            out["corrected"][key] = {"max_abs_diff_all_rows_K": float(np.max(np.abs(mine - stored))),
                                     "end_max_abs_diff_vs_corrected_end_K": float(np.max(np.abs(end - np.array(a["corrected_end"]))))}
            my_hist[(key, "corrected")] = mine
            # resolved vs my corrected over time (a coarse sanity check of the resolved history: same case, same times)
            rs = np.array(h3[key]["resolved"])
            d = np.abs(rs - mine)
            out["resolved_vs_my_corrected"][key] = {"max_abs_diff_per_row_first_mid_last": [float(d[0].max()), float(d[len(d) // 2].max()), float(d[-1].max())],
                                                    "max_over_all_rows": float(d.max()),
                                                    "row_maxdiff_monotone_nondecreasing_frac": float(np.mean(np.diff(d.max(axis=1)) >= -1e-6))}
        # the resolved history's area-weighted mean vs the archived series T_mean (incl. can): smooth difference?
        f3 = json.load(open(os.path.join(RES, "fields", f"{cell}_{bc}_Chen2020_{cond}.json")))
        Tm = np.array([row[7] for row in f3["series"]])
        Tc = np.array([row[1] for row in f3["series"]])
        nu = GEOM[cell][2]
        w = np.array([(2 * i - 1) / nu ** 2 for i in range(1, nu + 1)])
        rs = np.array(h3[key]["resolved"])
        dm = rs @ w - Tm
        out["resolved_mean_vs_series_T_mean"][key] = {
            "diff_first_mid_last_K": [float(dm[0]), float(dm[len(dm) // 2]), float(dm[-1])],
            "max_abs_second_difference_of_diff_K": float(np.max(np.abs(np.diff(dm, 2)[:-1]))),   # last interval shorter
            "unit1_minus_core_mid_first_mid_last_K": [float(rs[0, 0] - Tc[0]), float(rs[len(rs) // 2, 0] - Tc[len(rs) // 2]), float(rs[-1, 0] - Tc[-1])],
            "end_area_mean_vs_T_roll_mean_K": float(rs[-1] @ w - f3["end"]["T_roll_mean"]),
        }
    # post-hoc matched-time statistics at t = 539.92 s (snapshot 54) for the three m5C_2C cases
    post = json.load(open(os.path.join(RES, "posthoc_matched_time.json")))["cases"]
    for key, pk in (("21700_b_m5C_2C", "21700_b"), ("21700_a_m5C_2C", "21700_a"), ("4680_b_m5C_2C", "4680_b")):
        P = post[pk]["1.50 A h"]
        times = h1[key]["times"]
        idx = [i for i, t in enumerate(times) if abs(t - P["t_s"]) < 1e-9]
        if not idx:
            out["posthoc_539s"][key] = "no snapshot at that time"
            continue
        i = idx[0]
        r1 = np.array(h1[key]["radial"][i])
        r3 = np.array(h3[key]["resolved"][i])
        offs = r1 - r3
        mine = {"mean_offset_K": float(offs.mean()), "min_offset_K": float(offs.min()), "max_offset_K": float(offs.max()),
                "spread_1d_K": float(r1.max() - r1.min()), "spread_3d_K": float(r3.max() - r3.min()),
                "n_units_over_1K": int(np.sum(np.abs(offs) > 1.0))}
        mine["spread_overstatement"] = mine["spread_1d_K"] / mine["spread_3d_K"] - 1
        out["posthoc_539s"][key] = {"snapshot_index": i, "t": times[i],
                                    **{k: {"mine": mine[k], "posthoc": P[k], "diff": mine[k] - P[k]} for k in mine}}
    json.dump(out, open(os.path.join(OUT, "out_1d_resolve.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
