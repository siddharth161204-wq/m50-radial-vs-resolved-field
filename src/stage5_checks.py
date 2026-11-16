#!/usr/bin/env python3
"""Stage 5, checks V2, V3, V4 and V6 (D33); V1 is in src/stage5_report.py (P1) and the kernel files, V5 in
src/stage5_v5.py.

python3 src/stage5_checks.py runs     (the extra runs: V2's fixed-temperature run, V3's halved steps, V4's 30 groups)
python3 src/stage5_checks.py report   -> results/stage5_checks.json"""
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import stage5_common as S5  # noqa: E402
import stage5_coupled as SC  # noqa: E402
import stage5_report as REP  # noqa: E402
import stage5_runs as RN  # noqa: E402

MAIN = "21700_b_m5C_2C"
CHG = "0.3C_0C"
PSET = "ORegan2022"


def v2_run():
    cell, ends, Ta, I, g0 = RN.DISCHARGE_CASES[MAIN]
    k = REP.kernel_for(MAIN, "resolved")
    single = SC.load_run(RN.run_name("C", MAIN, "resolved", PSET, "one-way", True, k.G))
    Tave = RN.oneway_group_temps(k, Ta, g0) @ k.W
    n = len(Tave) - 1
    b = RN.built_for(PSET, 1.0, k.W, False)
    out = SC.run("discharge", cell, PSET, Ta, I, k, heat="fixed", fixed_T=lambda kk: np.full(k.G, Tave[min(kk, n)]),
                 built=b, label="V2")
    SC.save_run(out, "V2_uniform_temperature_coupled")
    return out, single


def runs():
    v2_run()
    for G, grid in ((S5.G_REG, "m5C_2C_half"), (30, "m5C_2C")):
        RN.discharge(MAIN, PSET, gridname=grid, G=G, part="V")
    for G, grid in ((S5.G_REG, "charge10_half"), (30, "charge10")):
        RN.charge("21700", PSET, cases=(CHG,), gridname=grid, G=G, part="V")


def readings_discharge(part, grid, G):
    """The registered readings of the main case for V3 and V4 (D33)."""
    case = MAIN if grid == "m5C_2C" else f"{MAIN}_{grid}"
    out = {}
    for label in REP.LABELS:
        for heat in REP.HEATS:
            nc = RN.run_name(part, case, label, PSET, heat, False, G)
            ns = RN.run_name(part, case, label, PSET, heat, True, G)
            if not (REP.exists(nc) and REP.exists(ns)):
                continue
            rc, rs = SC.load_run(nc), SC.load_run(ns)
            Ec, Qc = REP.energy_capacity(rc)
            Es, Qs = REP.energy_capacity(rs)
            sh = REP.shares_reading(rc)
            if heat == "two-way":
                out[f"penalty_energy|{label}"] = Es / Ec - 1
                out[f"penalty_capacity|{label}"] = Qs / Qc - 1
            out[f"spread_tavg|{label}|{heat}"] = sh["spread_tavg"]
            if sh["reversal_s"] is not None:
                out[f"reversal_s|{label}|{heat}"] = sh["reversal_s"]
    return out


def readings_charge(part, grid, G):
    case = f"21700_{CHG}" + ("" if grid == "charge10" else f"_{grid}")
    out = {}
    for label in REP.LABELS:
        n = RN.run_name(part, case, label, PSET, "two-way", False, G)
        if REP.exists(n):
            r = REP.margin_reading(SC.load_run(n))
            out[f"margin_V|{label}"] = r["margin_V"]
            out[f"charge_Ah|{label}"] = r["charge_Ah"]
    return out


def compare(base, alt, limit):
    rows = {}
    for k, v in base.items():
        if k in alt:
            rel = (alt[k] / v - 1) if v != 0 else None
            rows[k] = {"registered": v, "check": alt[k], "rel_change": rel,
                       "within": bool(rel is not None and abs(rel) < limit)}
    return {"readings": rows, "all_within": bool(rows and all(r["within"] for r in rows.values())), "limit": limit}


def v6():
    name = RN.run_name("D", f"21700_{CHG}", "resolved", PSET, "two-way", False, S5.G_REG)
    r = SC.load_run(name)
    ps, pe = r["phi_s_n"].astype(np.float64), r["phi_e_n"].astype(np.float64)    # (steps, G, 20)
    d = ps - pe
    node_min = d.min(axis=2)
    # interface value by linear extrapolation from the two nodes next to the separator (uniform mesh)
    iface = 1.5 * d[:, :, -1] - 0.5 * d[:, :, -2]
    both = np.minimum(node_min, iface)
    k, g = np.unravel_index(int(np.argmin(both)), both.shape)
    stored = REP.margin_reading(r)
    return {"run": name, "margin_recomputed_V": float(both[k, g]), "margin_stored_V": stored["margin_V"],
            "abs_difference_V": abs(float(both[k, g]) - stored["margin_V"]),
            "group_recomputed": int(g) + 1, "group_stored": stored["group"],
            "node_min_max_abs_difference_V": float(np.abs(node_min - r["margin_nodes_min"][:len(node_min)]).max()),
            "interface_max_abs_difference_V": float(np.abs(iface - r["margin_interface"][:len(iface)]).max())}


def report():
    res = {}
    # V2
    c = SC.load_run("V2_uniform_temperature_coupled")
    s = SC.load_run(RN.run_name("C", MAIN, "resolved", PSET, "one-way", True, S5.G_REG))
    m = min(len(c["t"]), len(s["t"]))
    dV = float(np.abs(c["V"][:m] - s["V"][:m]).max())
    dQ = float(REP.energy_capacity(c)[1] / REP.energy_capacity(s)[1] - 1)
    res["V2"] = {"max_abs_voltage_difference_V": dV, "capacity_rel_difference": dQ,
                 "held": bool(dV < 1e-3 and abs(dQ) < 1e-3)}
    # V3: current balance in every coupled run, and the halved step
    worst, worst_name = 0.0, None
    for p in glob.glob(os.path.join(S5.RUNDIR, "*_coupled_G*.npz")):
        rr = np.load(p, allow_pickle=False)
        v = float(rr["resid"].max())
        if v > worst:
            worst, worst_name = v, os.path.basename(p)
    base_d = readings_discharge("C", "m5C_2C", S5.G_REG)
    base_c = readings_charge("D", "charge10", S5.G_REG)
    res["V3"] = {"max_current_balance_residual": worst, "run_of_max": worst_name, "residual_held": bool(worst < 1e-6),
                 "halved_step_discharge": compare(base_d, readings_discharge("V", "m5C_2C_half", S5.G_REG), 0.01),
                 "halved_step_charge": compare(base_c, readings_charge("V", "charge10_half", S5.G_REG), 0.01)}
    res["V4"] = {"doubled_groups_discharge": compare(base_d, readings_discharge("V", "m5C_2C", 30), 0.05),
                 "doubled_groups_charge": compare(base_c, readings_charge("V", "charge10", 30), 0.05)}
    res["V6"] = v6()
    p = os.path.join(C.RESULTS, "stage5_v5.json")
    if os.path.exists(p):
        res["V5"] = json.load(open(p))
    p1 = os.path.join(C.RESULTS, "stage5_p1.json")
    if os.path.exists(p1):
        res["V1"] = {"P1": json.load(open(p1))}
    kern = {}
    for f in sorted(glob.glob(os.path.join(S5.KDIR, "*.json"))):
        mm = json.load(open(f))
        kern[os.path.basename(f)[:-5]] = {k: mm[k] for k in ("reciprocity_load_weighted_max_rel", "reciprocity_sampled_max_rel",
                                                           "load_weighted_vs_sampled_group_mean_max_rel", "K_stored",
                                                           "final_rel_distance_to_steady")}
        kern[os.path.basename(f)[:-5]]["sum_of_loads_vs_w_vol_max_rel"] = mm["loads"]["sum_of_loads_vs_w_vol_max_rel"]
    res.setdefault("V1", {})["kernels"] = kern
    res["V1"]["reciprocity_worst"] = max(v["reciprocity_load_weighted_max_rel"] for v in kern.values())
    res["V1"]["reciprocity_held"] = bool(res["V1"]["reciprocity_worst"] < 1e-9)
    json.dump(res, open(os.path.join(C.RESULTS, "stage5_checks.json"), "w"), indent=1)
    print(json.dumps({k: (v if k != "V1" else {kk: vv for kk, vv in v.items() if kk != "kernels"}) for k, v in res.items()},
                     indent=1, default=str)[:6000])


if __name__ == "__main__":
    {"runs": runs, "report": report}[sys.argv[1]]()
