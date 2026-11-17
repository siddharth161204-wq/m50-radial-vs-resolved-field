#!/usr/bin/env python3
"""Independent read, an end-to-end check of the setup behind the stored histories (one DFN, no coupled solve):
the single-unit model of the main discharge and of the M50's 1,455 mA, 0 C charge, two-way heat, resolved kernel,
ORegan2022, re-run with my own stepping code and compared with the stored runs.

As D23 and D30 state it: PyBaMM 26.9.0.0's DFN, default isothermal options plus the isothermal heat source; the 2.5
to 4.2 V window; the initial stoichiometries PyBaMM gives for 100 % (discharge) or 0 % (charge) written into the
set; the temperature an input held over each step at the step's start; the heat "Total heating [W]" over the 21700's
volume at the step's end entering the convolution for the next step's temperature, through the single-unit model's
response T_ave = sum_g W_g T_g to uniform heat (the area-weighted mean of the kernel's group responses); only the
voltage events kept; IDAKLU rtol 1e-6, atol 1e-8.
-> out/single_rerun.json"""
import json
import os
import sys
import time

import numpy as np
import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402

WINDOW = {"Upper voltage cut-off [V]": 4.2, "Open-circuit voltage at 100% SOC [V]": 4.2,
          "Lower voltage cut-off [V]": 2.5, "Open-circuit voltage at 0% SOC [V]": 2.5}
MARG = ["Negative electrode surface potential difference [V]",
        "Negative electrode surface potential difference at separator interface [V]"]


def simulation(pset, soc, I, charge):
    pv = pybamm.ParameterValues(pset)
    pv.update(WINDOW)
    x, y = pybamm.lithium_ion.get_initial_stoichiometries(soc, pv)
    pv.update({"Initial concentration in negative electrode [mol.m-3]": x * pv["Maximum concentration in negative electrode [mol.m-3]"],
               "Initial concentration in positive electrode [mol.m-3]": y * pv["Maximum concentration in positive electrode [mol.m-3]"]})
    pv.update({"Current function [A]": I, "Ambient temperature [K]": pybamm.InputParameter("T"),
               "Initial temperature [K]": pybamm.InputParameter("T")})
    m = pybamm.lithium_ion.DFN({"calculate heat source for isothermal models": "true"})
    m.events = [e for e in m.events if e.name in ("Minimum voltage [V]", "Maximum voltage [V]")]
    outs = ["Voltage [V]", "Total heating [W]"] + (MARG if charge else [])
    return pybamm.Simulation(m, parameter_values=pv, solver=pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8, output_variables=outs))


def rerun(kind, stored_name, kernel_name, pset, Ta, I, soc, max_steps):
    charge = kind == "charge"
    k = L.load_kernel(os.path.join(L.KDIR, kernel_name), keys=("S_group", "S_inf_group"))
    G, N = k["meta"]["G"], k["meta"]["N"]
    W = L.group_w(N, G)
    dt = k["meta"]["dt"]
    S = np.einsum("g,kgj->k", W, k["S_group"].astype(float))           # T_ave's response to uniform heat
    S_inf = float(W @ k["S_inf_group"].sum(axis=1))
    h = np.concatenate([S[:1], np.diff(S), [S_inf - S[-1]]])           # impulse response, lags 1..K+1
    sim = simulation(pset, soc, I, charge)
    t0 = time.time()
    sol = None
    T_now = Ta
    rec = {"t": [0.0], "V": [], "q": [], "T": [Ta], "mn": [], "mi": []}
    qs = []
    status = "max steps"
    for step in range(1, max_steps + 1):
        sol = sim.step(dt, inputs={"T": T_now + 273.15}, save=False, starting_solution=sol)
        tt = np.asarray(sol["Time [s]"].entries)
        V = np.asarray(sol["Voltage [V]"].entries)
        Q = np.asarray(sol["Total heating [W]"].entries)
        if step == 1:
            rec["V"].append(float(V[0]))
            rec["q"].append(float(Q[0]) / L.V21700)
            if charge:
                rec["mn"].append(float(np.asarray(sol[MARG[0]].entries)[:, 0].min()))
                rec["mi"].append(float(np.asarray(sol[MARG[1]].entries)[0]))
        rec["t"].append(float(tt[-1]))
        rec["V"].append(float(V[-1]))
        rec["q"].append(float(Q[-1]) / L.V21700)
        rec["T"].append(T_now)
        if charge:
            rec["mn"].append(float(np.asarray(sol[MARG[0]].entries)[:, -1].min()))
            rec["mi"].append(float(np.asarray(sol[MARG[1]].entries)[-1]))
        if sol.termination != "final time":
            status = sol.termination
            break
        qs.append(float(Q[-1]) / L.V21700)
        j = len(qs)
        lags = np.arange(j, 0, -1)                                       # for q_1..q_j: lag j - m + 1
        hh = np.where(lags <= len(h), h[np.minimum(lags, len(h)) - 1], 0.0)
        T_now = Ta + float(hh @ np.array(qs))
    wall = time.time() - t0
    st = L.load_run(os.path.join(L.RDIR, stored_name + ".npz"))
    t = np.array(rec["t"])
    V = np.array(rec["V"])
    q = np.array(rec["q"])
    T = np.array(rec["T"])
    n = min(len(t), len(st["t"]))
    Iabs = abs(I)
    E_mine = float(np.sum(0.5 * (V[1:] + V[:-1]) * Iabs * np.diff(t)) / 3600)
    E_st = float(np.sum(0.5 * (st["V"][1:] + st["V"][:-1]) * Iabs * np.diff(st["t"])) / 3600)
    out = {"run": stored_name, "kernel": kernel_name, "status_mine": str(status), "status_stored": st["meta"]["status"],
           "outputs_mine": int(len(t)), "outputs_stored": int(len(st["t"])),
           "t_end_mine_s": float(t[-1]), "t_end_stored_s": float(st["t"][-1]),
           "max_abs_dV_V": float(np.abs(V[:n] - st["V"][:n]).max()),
           "max_rel_dq": float(np.abs(q[:n] / st["q"][:n, 0].astype(float) - 1).max()),
           "max_abs_dT_K": float(np.abs(T[:n] - st["T"][:n, 0].astype(float)).max()),
           "energy_mine_Wh": E_mine, "energy_stored_Wh": E_st, "wall_s": wall}
    if charge:
        both = np.minimum(np.array(rec["mn"]), np.array(rec["mi"]))
        sb = np.minimum(st["margin_nodes_min"][:, 0].astype(float), st["margin_interface"][:, 0].astype(float))
        out.update({"margin_min_mine_V": float(both.min()), "margin_min_stored_V": float(sb.min()),
                    "t_margin_min_mine_s": float(t[int(np.argmin(both))]), "t_margin_min_stored_s": float(st["t"][int(np.argmin(sb))]),
                    "max_abs_d_margin_V": float(np.abs(both[:n] - sb[:n]).max())})
    return out


def p9_edges():
    """The single-unit model's fine bracket for P9 (0 C, two-way heat, resolved kernel, ORegan2022), both cells: the
    largest passing and the smallest failing rate of the stored search, each re-run to 4.2 V with my own stepping."""
    out = {}
    for cell in ("21700", "4680"):
        d = json.load(open(os.path.join(L.RDIR, f"limit_{cell}_ORegan2022_0C.json")))["resolved|single"]
        for rate in (d["fine_rate"], d["fine_fail_above"]):
            tr = next(t for t in d["trials"] if abs(t["rate"] - rate) < 2e-6)
            r = rerun_margin(cell, rate)
            r.update({"stored_passed": tr["passed"], "stored_min_margin_V": tr["min_margin_V"], "stored_t_min_s": tr["t_min_s"],
                      "stored_status": tr["status"]})
            r["verdict_match"] = r["passed"] == tr["passed"]
            out[f"{cell}|{rate:.8f}"] = r
            print(cell, rate, json.dumps(r), flush=True)
    return out


def rerun_margin(cell, rate):
    k = L.load_kernel(os.path.join(L.KDIR, f"resolved_b_{cell}_charge10_G15.npz"), keys=("S_group", "S_inf_group"))
    G, N = k["meta"]["G"], k["meta"]["N"]
    W = L.group_w(N, G)
    dt = k["meta"]["dt"]
    S = np.einsum("g,kgj->k", W, k["S_group"].astype(float))
    S_inf = float(W @ k["S_inf_group"].sum(axis=1))
    h = np.concatenate([S[:1], np.diff(S), [S_inf - S[-1]]])
    I = -rate * L.C_SPEC
    sim = simulation("ORegan2022", 0.0, I, True)
    Ta = 0.0
    T_now, sol, qs = Ta, None, []
    mins, ts = [], []
    t0 = time.time()
    status = "max steps"
    for step in range(1, 20001):
        sol = sim.step(dt, inputs={"T": T_now + 273.15}, save=False, starting_solution=sol)
        if step == 1:
            mins.append(min(float(np.asarray(sol[MARG[0]].entries)[:, 0].min()), float(np.asarray(sol[MARG[1]].entries)[0])))
            ts.append(0.0)
        mins.append(min(float(np.asarray(sol[MARG[0]].entries)[:, -1].min()), float(np.asarray(sol[MARG[1]].entries)[-1])))
        ts.append(float(np.asarray(sol["Time [s]"].entries)[-1]))
        if sol.termination != "final time":
            status = sol.termination
            break
        qs.append(float(np.asarray(sol["Total heating [W]"].entries)[-1]) / L.V21700)
        j = len(qs)
        lags = np.arange(j, 0, -1)
        hh = np.where(lags <= len(h), h[np.minimum(lags, len(h)) - 1], 0.0)
        T_now = Ta + float(hh @ np.array(qs))
    mins = np.array(mins)
    neg = np.where(mins < 0)[0]
    return {"rate": rate, "passed": bool(str(status).startswith("event") and mins.min() >= 0.0), "min_margin_V": float(mins.min()),
            "t_first_negative_s": float(ts[neg[0]]) if len(neg) else None, "first_negative_margin_V": float(mins[neg[0]]) if len(neg) else None,
            "t_end_s": ts[-1], "status": str(status), "wall_s": time.time() - t0}


def scan():
    """D35 says the margin is not monotonic in the rate near the plating-limited rate (D32 took monotonicity as
    given). One DFN can test it: the M50's single-unit model (0 C, two-way heat, resolved kernel, ORegan2022), each
    rate charged to 4.2 V without stopping, its smallest margin over the whole charge."""
    rates = [round(0.270 + 0.0025 * i, 4) for i in range(13)]
    out = {}
    for r in rates:
        x = rerun_margin("21700", r)
        out[f"{r:.4f}"] = {"min_margin_mV": 1e3 * x["min_margin_V"], "passed": x["passed"],
                           "t_first_negative_s": x["t_first_negative_s"], "t_end_s": x["t_end_s"]}
        print(r, json.dumps(out[f"{r:.4f}"]), flush=True)
    m = [out[f"{r:.4f}"]["min_margin_mV"] for r in rates]
    falls = all(b <= a + 1e-9 for a, b in zip(m, m[1:]))
    return {"rates": rates, "by_rate": out, "min_margin_nonincreasing_in_rate": bool(falls),
            "rises": [[rates[i], rates[i + 1], m[i], m[i + 1]] for i in range(len(m) - 1) if m[i + 1] > m[i] + 1e-9]}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    res = {}
    if which == "scan":
        res = {"single_unit_margin_scan": scan(), "peak_memory": L.mem_note()}
        L.dump("single_rerun_scan.json", res)
        print(json.dumps({k: v for k, v in res["single_unit_margin_scan"].items() if k != "by_rate"}, indent=1))
        sys.exit(0)
    if which == "p9":
        res = {"p9_single_edges": p9_edges(), "peak_memory": L.mem_note()}
        L.dump("single_rerun_p9.json", res)
        sys.exit(0)
    if which in ("both", "discharge"):
        res["discharge"] = rerun("discharge", "C_21700_b_m5C_2C_resolved_ORegan2022_two-way_single_G15",
                                 "resolved_b_21700_m5C_2C_G15.npz", "ORegan2022", -5.0, 10.0, 1.0, 5000)
        print(json.dumps(res["discharge"], indent=1), flush=True)
    if which in ("both", "charge"):
        res["charge"] = rerun("charge", "D_21700_0.3C_0C_resolved_ORegan2022_two-way_single_G15",
                              "resolved_b_21700_charge10_G15.npz", "ORegan2022", 0.0, -0.3 * L.C_SPEC, 0.0, 5000)
        print(json.dumps(res["charge"], indent=1), flush=True)
    res["peak_memory"] = L.mem_note()
    L.dump("single_rerun.json", res)
