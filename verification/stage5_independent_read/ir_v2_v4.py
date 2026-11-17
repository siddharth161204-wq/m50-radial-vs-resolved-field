#!/usr/bin/env python3
"""Independent read, item 6 (phase 2): checks V2, V3 and V4 (D33) from the stored runs, with my own readings.

V2: every group at the single-unit model's T_ave (main case, one-way heat, resolved kernel, ORegan2022): the coupled
    solve within 1 mV of the single-unit model in voltage at every step and within 0.1 % in capacity.
V3: the current balance in every coupled run (below 1e-6 of I_app at every output), and the time step halved (every
    kernel on the halved grid) in the main case and in the M50's 1,455 mA, 0 C charge: each registered reading
    changes by less than 1 %.
V4: 30 groups in the same two cases: each registered reading changes by less than 5 %.
Registered readings (D33): main case, the energy and capacity penalties under each kernel with two-way heat, the
time-averaged spread under each kernel with both heat rules, the reversal time where there is one; charge case,
the margin under each kernel and the charge capacity at 4.2 V.
Also: the coupling rule of D30 in each check run, with its own kernel, and the stored results/stage5_checks.json.
-> out/v2_v4.json"""
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402
import ir_readings as RD  # noqa: E402   (my own reading functions)

MAIN, CHG, PSET = "21700_b_m5C_2C", "0.3C_0C", "ORegan2022"


def kfile(label, grid, G):
    return L.kernel_file(label, "b", "21700", grid, G)


def discharge_readings(part, grid, G):
    cell, ends, Ta, I, g0 = L.DISCHARGE[MAIN]
    case = MAIN if grid == g0 else f"{MAIN}_{grid}"
    W = L.group_w(45, G)
    out, rule = {}, {}
    for label in L.LABELS:
        for heat in L.HEATS:
            fc, fs = L.run_file(part, case, label, PSET, heat, False, G), L.run_file(part, case, label, PSET, heat, True, G)
            if not (os.path.exists(fc) and os.path.exists(fs)):
                continue
            rc, rs = L.load_run(fc), L.load_run(fs)
            kp = kfile(label, grid, G)
            kern = L.load_kernel(kp, keys=("S_group", "S_inf_group"))
            og = RD.oneway_groups(kern, Ta, grid) if heat == "one-way" else None
            rule[f"{label}|{heat}"] = {"coupled_K": RD.coupling_check(rc, kern, Ta, heat, False, og)[0],
                                       "single_K": RD.coupling_check(rs, kern, Ta, heat, True, og)[0],
                                       "kernel_ok": os.path.basename(kp) == rc["meta"]["kernel"] == rs["meta"]["kernel"],
                                       "dt_ok": abs(rc["meta"]["dt"] - L.grid(grid)[0]) < 1e-12}
            Ec, Qc = RD.energy_capacity(rc)
            Es, Qs = RD.energy_capacity(rs)
            sh, _ = RD.share_readings(rc, W)
            if heat == "two-way":
                out[f"penalty_energy|{label}"] = Es / Ec - 1
                out[f"penalty_capacity|{label}"] = Qs / Qc - 1
            out[f"spread_tavg|{label}|{heat}"] = sh["spread_tavg"]
            if sh["reversal_s"] is not None:
                out[f"reversal_s|{label}|{heat}"] = sh["reversal_s"]
    return out, rule


def charge_readings(part, grid, G):
    Ta = L.CHARGE[CHG][1]
    case = f"21700_{CHG}" + ("" if grid == "charge10" else f"_{grid}")
    out, rule = {}, {}
    for label in L.LABELS:
        f = L.run_file(part, case, label, PSET, "two-way", False, G)
        if not os.path.exists(f):
            continue
        r = L.load_run(f)
        kp = kfile(label, grid, G)
        kern = L.load_kernel(kp, keys=("S_group", "S_inf_group"))
        rule[label] = {"coupled_K": RD.coupling_check(r, kern, Ta, "two-way", False)[0],
                       "kernel_ok": os.path.basename(kp) == r["meta"]["kernel"]}
        m = RD.margin_readings(r)
        out[f"margin_V|{label}"] = m["margin_V"]
        out[f"charge_Ah|{label}"] = m["charge_Ah"]
        fs = L.run_file(part, case, label, PSET, "two-way", True, G)
        if os.path.exists(fs):
            rule[label]["single_K"] = RD.coupling_check(L.load_run(fs), kern, Ta, "two-way", True)[0]
    return out, rule


def compare(base, alt, limit):
    rows = {}
    for k, v in base.items():
        if k in alt:
            rel = alt[k] / v - 1 if v != 0 else None
            rows[k] = {"registered": v, "check": alt[k], "rel_change": rel,
                       "within": bool(rel is not None and abs(rel) < limit)}
    missing = [k for k in base if k not in alt]
    return {"readings": rows, "missing": missing, "all_within": bool(rows and not missing and all(r["within"] for r in rows.values())),
            "limit": limit}


def energies_halved_step():
    """The energies and capacities behind V3's penalties: registered against the halved step, two-way heat."""
    out = {}
    for label in L.LABELS:
        for single in (False, True):
            a = L.run_file("C", MAIN, label, PSET, "two-way", single)
            b = L.run_file("V", f"{MAIN}_m5C_2C_half", label, PSET, "two-way", single, 15)
            if os.path.exists(a) and os.path.exists(b):
                ra, rb = L.load_run(a), L.load_run(b)
                Ea, Qa = RD.energy_capacity(ra)
                Eb, Qb = RD.energy_capacity(rb)
                out[f"{label}|{'single' if single else 'coupled'}"] = {"energy": Eb / Ea - 1, "capacity": Qb / Qa - 1}
    return out


def v2():
    fc = os.path.join(L.RDIR, "V2_uniform_temperature_coupled.npz")
    fs = L.run_file("C", MAIN, "resolved", PSET, "one-way", True)
    if not os.path.exists(fc):
        return None
    c, s = L.load_run(fc), L.load_run(fs)
    cell, ends, Ta, I, g0 = L.DISCHARGE[MAIN]
    kern = L.load_kernel(L.kernel_file("resolved", "b", cell, g0), keys=("S_group", "S_inf_group"))
    W = L.group_w(45, 15)
    Tave = RD.oneway_groups(kern, Ta, g0) @ W                     # steps 0..n
    n = len(Tave) - 1
    Tc = c["T"].astype(float)
    steps = Tc.shape[0] - 1
    want = Tave[np.minimum(np.arange(steps), n)]
    Trule = float(np.abs(Tc[1:] - want[:, None]).max())
    # voltages at the common full steps
    dt = c["meta"]["dt"]
    tc, ts = c["t"].astype(float), s["t"].astype(float)
    full = lambda t: len(t) - 1 if abs(t[-1] - dt * (len(t) - 1)) < 1e-9 else len(t) - 1
    m = min(full(tc), full(ts))
    dV = np.abs(c["V"][:m] - s["V"][:m])
    Qc = abs(c["meta"]["I_app_A"]) * tc[-1] / 3600
    Qs = abs(s["meta"]["I_app_A"]) * ts[-1] / 3600
    # the stored check compares every common index, including a final partial step
    mm = min(len(tc), len(ts))
    dV_all = float(np.abs(c["V"][:mm] - s["V"][:mm]).max())
    return {"T_rule_max_abs_K": Trule, "max_abs_voltage_difference_full_steps_V": float(dV.max()),
            "max_abs_voltage_difference_all_common_indices_V": dV_all, "t_cut_coupled_s": float(tc[-1]),
            "t_cut_single_s": float(ts[-1]), "capacity_rel_difference": Qc / Qs - 1,
            "held": bool(dV_all < 1e-3 and abs(Qc / Qs - 1) < 1e-3), "steps_compared": int(m)}


def single_g30_vs_g15():
    """With 30 groups the single-unit model sees the same area-weighted mean temperature, so its runs should equal
    the 15-group ones."""
    out = {}
    for label in L.LABELS:
        for heat in L.HEATS:
            a, b = L.run_file("V", MAIN, label, PSET, heat, True, 30), L.run_file("C", MAIN, label, PSET, heat, True, 15)
            if os.path.exists(a) and os.path.exists(b):
                ra, rb = L.load_run(a), L.load_run(b)
                m = min(len(ra["t"]), len(rb["t"]))
                out[f"{label}|{heat}"] = {"max_abs_dV": float(np.abs(ra["V"][:m] - rb["V"][:m]).max()),
                                          "t_cut_diff_s": float(ra["t"][-1] - rb["t"][-1])}
    return out


if __name__ == "__main__":
    base_d, _ = discharge_readings("C", "m5C_2C", 15)
    base_c, _ = charge_readings("D", "charge10", 15)
    h_d, h_d_rule = discharge_readings("V", "m5C_2C_half", 15)
    h_c, h_c_rule = charge_readings("V", "charge10_half", 15)
    g_d, g_d_rule = discharge_readings("V", "m5C_2C", 30)
    g_c, g_c_rule = charge_readings("V", "charge10", 30)
    res = {"V2": v2(),
           "V3": {"current_balance": RD.v3_residuals(),
                  "halved_step_discharge": compare(base_d, h_d, 0.01), "halved_step_charge": compare(base_c, h_c, 0.01),
                  "coupling_rule": {"discharge": h_d_rule, "charge": h_c_rule},
                  "energies_halved_step": energies_halved_step()},
           "V4": {"doubled_groups_discharge": compare(base_d, g_d, 0.05), "doubled_groups_charge": compare(base_c, g_c, 0.05),
                  "coupling_rule": {"discharge": g_d_rule, "charge": g_c_rule}, "single_unit_G30_vs_G15": single_g30_vs_g15()},
           "registered_readings": {"discharge": base_d, "charge": base_c}}
    # context, not a registered check: the main-case predictions' quantities recomputed from the V3 and V4 runs
    def ctx(dd, cc):
        o = {}
        a, b = dd.get("spread_tavg|radial|one-way"), dd.get("spread_tavg|resolved|one-way")
        if a and b:
            o["P2_radial_over_resolved_minus_1"] = a / b - 1
            o["P2_condition"] = bool(0.25 <= a / b - 1 <= 0.45)
            o["P3_ratio_minus_1"] = b / 0.0554168 - 1
        a, b = dd.get("penalty_energy|radial"), dd.get("penalty_energy|resolved")
        if a is not None and b is not None:
            o["P4_penalties"] = [a, b]
            o["P4_condition"] = bool(a > 0 and b <= 0.8 * a)
        a, b = cc.get("margin_V|radial"), cc.get("margin_V|resolved")
        if a is not None and b is not None:
            o["P7_0.3C_0C_radial_minus_resolved_mV"] = 1e3 * (a - b)
        return o
    res["context_predictions_under_checks"] = {"registered": ctx(base_d, base_c), "halved_step": ctx(h_d, h_c),
                                               "doubled_groups": ctx(g_d, g_c)}
    sp = os.path.join(L.RES, "stage5_checks.json")
    if os.path.exists(sp):
        st = json.load(open(sp))
        cmp = {}
        for V, sect in (("V3", "halved_step_discharge"), ("V3", "halved_step_charge"), ("V4", "doubled_groups_discharge"),
                        ("V4", "doubled_groups_charge")):
            mine = res[V][sect]["readings"]
            theirs = st.get(V, {}).get(sect, {}).get("readings", {})
            cmp[f"{V}|{sect}"] = {k: {"mine": mine[k]["check"], "stored": theirs.get(k, {}).get("check"),
                                      "match": RD.same(mine[k]["check"], theirs.get(k, {}).get("check"), rtol=1e-9)}
                                  for k in mine}
            cmp[f"{V}|{sect}|all_within"] = {"mine": res[V][sect]["all_within"], "stored": st.get(V, {}).get(sect, {}).get("all_within")}
        if res["V2"] and "V2" in st:
            cmp["V2"] = {"mine": res["V2"], "stored": st["V2"]}
        cmp["V3|residual"] = {"mine": res["V3"]["current_balance"]["max_rel_residual"],
                              "stored": st.get("V3", {}).get("max_current_balance_residual")}
        if "V6" in st:
            mine6 = json.load(open(os.path.join(L.OUT, "v5_v6.json")))["V6"] if os.path.exists(os.path.join(L.OUT, "v5_v6.json")) else {}
            cmp["V6"] = {"stored": st["V6"], "mine_margin_V": mine6.get("margin_recomputed_V"), "mine_group": mine6.get("group_recomputed"),
                         "match": bool(mine6 and RD.same(mine6["margin_recomputed_V"], st["V6"]["margin_recomputed_V"], rtol=1e-9)
                                       and mine6["group_recomputed"] == st["V6"]["group_recomputed"])}
        if "V5" in st and os.path.exists(os.path.join(L.OUT, "v5_v6.json")):
            m5 = json.load(open(os.path.join(L.OUT, "v5_v6.json")))["V5"]
            cmp["V5"] = {k: {"mine": m5.get(k), "stored": st["V5"].get(k), "match": RD.same(m5.get(k), st["V5"].get(k), rtol=1e-9)}
                         for k in ("steps_compared", "max_rel_share_difference", "step_of_max", "group_of_max",
                                   "max_abs_voltage_difference_V", "within_0.5_percent")}
            cmp["V5"]["secant_residual"] = {"mine": m5.get("route2_stored_resid_max"), "stored": st["V5"].get("max_current_balance_residual"),
                                            "match": RD.same(m5.get("route2_stored_resid_max"), st["V5"].get("max_current_balance_residual"), rtol=1e-9)}
        if "V1" in st and os.path.exists(os.path.join(L.OUT, "p1_v1.json")):
            m1 = json.load(open(os.path.join(L.OUT, "p1_v1.json")))
            cmp["V1"] = {"P1_max_abs_K": {"mine": m1["P1"]["max_abs_K"], "stored": st["V1"]["P1"]["max_abs_K"],
                                          "match": RD.same(m1["P1"]["max_abs_K"], st["V1"]["P1"]["max_abs_K"], rtol=1e-7)},
                         "P1_held": {"mine": m1["P1"]["held"], "stored": st["V1"]["P1"]["held"]},
                         "reciprocity_worst_meta": {"stored": st["V1"].get("reciprocity_worst"), "held": st["V1"].get("reciprocity_held"),
                                                    "mine_from_float64_steady_states": m1["V1_kernel_files"]["reciprocity_steady_f64_worst"],
                                                    "mine_from_float32_steps": m1["V1_kernel_files"]["reciprocity_stored_f32_worst"],
                                                    "mine_all_pairs_within_f32_rounding": m1["V1_kernel_files"]["reciprocity_all_within_f32_rounding"]},
                         "kernels_listed": {"stored": len(st["V1"].get("kernels", {})), "mine": len(m1["V1_kernel_files"]["kernels"])}}
        res["vs_stored_checks"] = cmp
    else:
        res["vs_stored_checks"] = "results/stage5_checks.json not present yet"
    L.dump("v2_v4.json", res)
    print(json.dumps({k: v for k, v in res.items() if k != "registered_readings"}, indent=1, default=str)[:8000])
