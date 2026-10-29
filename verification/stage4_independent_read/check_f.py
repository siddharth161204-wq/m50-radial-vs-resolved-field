#!/usr/bin/env python3
"""Independent check (f): re-derive R(T) with PyBaMM's DFN (default, isothermal) at a few temperatures, two ways:
 route A: an Experiment written as "Rest for 600 seconds" then "Discharge at 1C for 10 seconds", voltages read from
          the full time arrays at t = 600 s and t = 610 s (not from cycle objects);
 route B: no experiment; "Current function [A]" = 5 * (t > 600) (a Heaviside step, so the solver splits at 600 s),
          solved over 0..610 s, voltage interpolated at 600 s and 610 s.
Both: "Ambient temperature [K]" = "Initial temperature [K]" = T; window 2.5 to 4.2 V on the four parameters; initial_soc = 1.
Compares with results/stage4_RT.csv. Writes check4/out_f.json."""
import csv
import json
import os
import sys
import time

import numpy as np
import pybamm

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RES = os.path.join(REPO, "results")
OUT = os.path.dirname(os.path.abspath(__file__))


def pv(pset, T_C):
    p = pybamm.ParameterValues(pset)
    p["Ambient temperature [K]"] = 273.15 + T_C
    p["Initial temperature [K]"] = 273.15 + T_C
    p["Upper voltage cut-off [V]"] = 4.2
    p["Open-circuit voltage at 100% SOC [V]"] = 4.2
    p["Lower voltage cut-off [V]"] = 2.5
    p["Open-circuit voltage at 0% SOC [V]"] = 2.5
    return p


def route_a(pset, T_C, soc=1.0):
    p = pv(pset, T_C)
    cap = p["Nominal cell capacity [A.h]"]
    exp = pybamm.Experiment(["Rest for 600 seconds (5 second period)", "Discharge at 1C for 10 seconds (0.05 second period)"])
    sim = pybamm.Simulation(pybamm.lithium_ion.DFN(), parameter_values=p, experiment=exp,
                            solver=pybamm.IDAKLUSolver(rtol=1e-7, atol=1e-9))
    sol = sim.solve(initial_soc=soc)
    t = sol["Time [s]"].entries
    V = sol["Voltage [V]"].entries
    I = sol["Current [A]"].entries
    Tcell = sol["Volume-averaged cell temperature [K]"].entries - 273.15
    # end of rest: last point with t <= 600 and zero current; end of pulse: t = 610
    i_rest = int(np.max(np.where((t <= 600.0 + 1e-9) & (np.abs(I) < 1e-12))[0]))
    i_end = int(np.argmin(np.abs(t - 610.0)))
    return {"t_rest": float(t[i_rest]), "t_end": float(t[i_end]), "I_end": float(I[i_end]), "C_rate_current": cap,
            "V_rest": float(V[i_rest]), "V_end": float(V[i_end]), "R": float((V[i_rest] - V[i_end]) / I[i_end]),
            "T_cell_range": [float(Tcell.min()), float(Tcell.max())]}


def route_b(pset, T_C, soc=1.0):
    p = pv(pset, T_C)
    p["Current function [A]"] = lambda t: 5.0 * (t > 600.0)
    model = pybamm.lithium_ion.DFN()
    # termination events only: V(0) equals the 4.2 V cut-off exactly at 100 % SOC, which trips "Maximum voltage"
    model.events = [e for e in model.events if "voltage" not in e.name.lower()]
    sim = pybamm.Simulation(model, parameter_values=p, solver=pybamm.IDAKLUSolver(rtol=1e-7, atol=1e-9))
    t_eval = [0.0, 610.0]
    t_interp = np.concatenate([np.linspace(0, 600, 121), np.linspace(600, 610, 201)[1:]])
    sol = sim.solve(t_eval=t_eval, t_interp=t_interp, initial_soc=soc)
    t = sol["Time [s]"].entries
    V = sol["Voltage [V]"].entries
    I = sol["Current [A]"].entries
    i600 = int(np.max(np.where((t <= 600.0 + 1e-9) & (np.abs(I) < 1e-12))[0]))   # last zero-current point
    i610 = int(np.argmin(np.abs(t - 610.0)))
    return {"t_rest": float(t[i600]), "I_rest": float(I[i600]), "t_end": float(t[i610]), "I_end": float(I[i610]),
            "V_rest": float(V[i600]), "V_end": float(V[i610]), "R": float((V[i600] - V[i610]) / 5.0)}


def main():
    table = {(r["set"], float(r["soc"]), float(r["T_C"])): r for r in csv.DictReader(open(os.path.join(RES, "stage4_RT.csv")))}
    jobs = [("ORegan2022", -5.0), ("ORegan2022", 25.0), ("ORegan2022", 0.0), ("Chen2020", -5.0), ("ORegan2022", 1.25)]
    if len(sys.argv) > 1:
        jobs = jobs[: int(sys.argv[1])]
    out = {"pybamm": pybamm.__version__, "results": {}}
    for pset, T_C in jobs:
        t0 = time.time()
        rec = {}
        try:
            rec["A"] = route_a(pset, T_C)
        except Exception as e:  # noqa: BLE001
            rec["A"] = {"error": repr(e)}
        try:
            rec["B"] = route_b(pset, T_C)
        except Exception as e:  # noqa: BLE001
            rec["B"] = {"error": repr(e)}
        key = (pset, 1.0, T_C)
        if key in table:
            tr = table[key]
            rec["table"] = {"V_rest": float(tr["V_rest_V"]), "V_end": float(tr["V_10s_V"]), "R": float(tr["R_ohm"])}
        else:
            # off-grid temperature: the table's ln-linear interpolation
            lo, hi = table[(pset, 1.0, np.floor(T_C * 2) / 2)], table[(pset, 1.0, np.ceil(T_C * 2) / 2)]
            f = (T_C - float(lo["T_C"])) / 0.5
            rec["table_interp"] = float(np.exp((1 - f) * np.log(float(lo["R_ohm"])) + f * np.log(float(hi["R_ohm"]))))
        for r_ in ("A", "B"):
            if "R" in rec[r_]:
                ref = rec.get("table", {}).get("R", rec.get("table_interp"))
                rec[r_]["rel_diff_vs_table"] = rec[r_]["R"] / ref - 1
        rec["wall_s"] = time.time() - t0
        out["results"][f"{pset}|{T_C:g}C"] = rec
        print(pset, T_C, json.dumps(rec), flush=True)
        json.dump(out, open(os.path.join(OUT, "out_f.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
