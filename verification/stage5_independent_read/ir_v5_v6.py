#!/usr/bin/env python3
"""Independent read, item 6 (phase 1): checks V5 and V6 (D33) from the stored files.

V5: route 2 (results/stage5_runs/V5_route2.npz: separate voltage-mode DFNs, secant search on the current balance)
against the stepwise route's run of the main case (two-way heat, resolved kernel, ORegan2022): every group's share
at every common step within 0.5 % of its value; the secant tolerance 1e-8 of I_app.
V6: the margin of the main charge run (M50, 1,455 mA, 0 C, resolved kernel, ORegan2022) recomputed from the stored
phi_s,n and phi_e at the negative electrode's nodes: the node minimum, and the separator-interface value by linear
extrapolation from the two nodes next to the separator (uniform mesh: 1.5 d_N - 0.5 d_N-1).
-> out/v5_v6.json"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402


def v5():
    r2 = L.load_run(os.path.join(L.RDIR, "V5_route2.npz"))
    r1 = L.load_run(L.run_file("C", "21700_b_m5C_2C", "resolved", "ORegan2022", "two-way", False))
    Iapp = r1["meta"]["I_app_A"]
    dt = r1["meta"]["dt"]
    W = L.group_w(45, 15)
    t1, t2 = r1["t"].astype(float), r2["t"].astype(float)
    # common steps: both routes record step k at t = k dt; route 1's last record is the partial cut-off step
    full1 = len(t1) - 1 if abs(t1[-1] - dt * (len(t1) - 1)) < 1e-9 else len(t1) - 1
    n = min(len(t2), full1)
    assert np.abs(t1[:n] - t2[:n]).max() < 1e-9, "the two routes' step times differ"
    s1 = r1["I"][:n].astype(float) / Iapp
    s2 = r2["I"][:n].astype(float) / Iapp
    relx = np.abs(s2 / s1 - 1.0)
    k, g = np.unravel_index(int(np.argmax(relx)), relx.shape)
    dV = np.abs(r2["V"][:n] - r1["V"][:n])
    kv = int(np.argmax(dV))
    bal2 = np.abs(r2["I"].astype(float) @ W / Iapp - 1.0)
    stored = json.load(open(os.path.join(L.RES, "stage5_v5.json")))
    # the voltage difference over time, to see where it comes from
    prof = {f"{t1[i]:.0f}s": float(dV[i]) for i in (1, 10, 50, 100, 150, n - 5, n - 2, n - 1) if 0 <= i < n}
    return {"steps_compared": int(n), "max_rel_share_difference": float(relx.max()), "step_of_max": int(k),
            "group_of_max": int(g) + 1, "within_0.5_percent": bool(relx.max() < 0.005),
            "max_abs_voltage_difference_V": float(dV.max()), "step_of_max_voltage_difference": kv,
            "t_of_max_voltage_difference_s": float(t1[kv]), "voltage_difference_profile_V": prof,
            "route2_balance_from_I_max_rel": float(bal2.max()), "route2_stored_resid_max": float(r2["resid"].max()),
            "secant_tolerance_met_1e-8": bool(float(r2["resid"].max()) <= 1e-8 and bal2.max() <= 1e-8 * 1.0001),
            "route2_last_t_s": float(t2[-1]), "route1_cut_s": float(t1[-1]),
            "route2_ends_before_route1_cut": bool(t2[-1] < t1[-1] <= t2[-1] + dt + 1e-9),
            "stored": {k_: stored.get(k_) for k_ in ("steps_compared", "max_rel_share_difference", "step_of_max",
                                                     "group_of_max", "max_abs_voltage_difference_V",
                                                     "max_current_balance_residual", "within_0.5_percent")}}


def v6():
    r = L.load_run(L.run_file("D", "21700_0.3C_0C", "resolved", "ORegan2022", "two-way", False))
    ps = r["phi_s_n"].astype(np.float64)
    pe = r["phi_e_n"].astype(np.float64)
    d = ps - pe                                                         # (outputs, groups, 20 nodes)
    node_min = d.min(axis=2)
    node_arg = d.argmin(axis=2)
    iface = d[:, :, -1] + 0.5 * (d[:, :, -1] - d[:, :, -2])            # the last node is next to the separator
    both = np.minimum(node_min, iface)
    k, g = np.unravel_index(int(np.argmin(both)), both.shape)
    mn_st = r["margin_nodes_min"].astype(float)
    mi_st = r["margin_interface"].astype(float)
    both_st = np.minimum(mn_st, mi_st)
    ks, gs = np.unravel_index(int(np.argmin(both_st)), both_st.shape)
    # which end of the node list is the separator: the interface value should sit next to the last node
    near_last = float(np.abs(iface - d[:, :, -1]).max())
    near_first = float(np.abs(iface - d[:, :, 0]).max())
    return {"outputs": int(d.shape[0]), "groups": int(d.shape[1]), "nodes": int(d.shape[2]),
            "margin_recomputed_V": float(both[k, g]), "group_recomputed": int(g) + 1, "t_recomputed_s": float(r["t"][k]),
            "at_interface_recomputed": bool(iface[k, g] <= node_min[k, g]),
            "margin_stored_arrays_V": float(both_st[ks, gs]), "group_stored_arrays": int(gs) + 1,
            "abs_difference_V": abs(float(both[k, g]) - float(both_st[ks, gs])),
            "node_min_max_abs_difference_V": float(np.abs(node_min - mn_st).max()),
            "interface_max_abs_difference_V": float(np.abs(iface - mi_st).max()),
            "node_argmin_matches_fraction": float(np.mean(node_arg == r["margin_nodes_argmin"])),
            "interface_minus_last_node_max_abs_V": near_last, "interface_minus_first_node_max_abs_V": near_first,
            "within_1e-6_V": bool(abs(float(both[k, g]) - float(both_st[ks, gs])) < 1e-6)}


if __name__ == "__main__":
    res = {"V5": v5(), "V6": v6(), "peak_memory": L.mem_note()}
    L.dump("v5_v6.json", res)
    print(json.dumps(res, indent=1))
