#!/usr/bin/env python3
"""Stage 4, Part B (D23): the LG M50's resistance against temperature, R(T), from a 1C discharge pulse of 10 s in
PyBaMM's isothermal Doyle-Fuller-Newman model, for ORegan2022 (main) and Chen2020 (bracket), at 100 % (registered)
and 50 % state of charge, from minus 10 C to 35 C in steps of 0.5 K.

R(T) = (V at the end of a 600 s rest minus V at the end of the 10 s pulse at 5 A) / 5 A, both sets on the rated
2.5 to 4.2 V window. Sensitivity d ln R / dT at minus 5, 0 and 25 C by the central difference over +-0.5 K.
python3 src/stage4_RT.py [--part 0|1]  -> results/stage4_RT.csv, results/stage4_RT.json"""
import argparse
import csv
import json
import os
import sys
import time

import numpy as np
import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SETS = ("ORegan2022", "Chen2020")
SOCS = (1.0, 0.5)
T_GRID = [round(-10.0 + 0.5 * k, 1) for k in range(91)]          # minus 10 C to 35 C
I_PULSE = 5.0                                                     # 1C of the 5 A h nominal capacity (both sets)
WINDOW = {"Upper voltage cut-off [V]": 4.2, "Open-circuit voltage at 100% SOC [V]": 4.2,
          "Lower voltage cut-off [V]": 2.5, "Open-circuit voltage at 0% SOC [V]": 2.5}


def params(pset, T_C):
    p = pybamm.ParameterValues(pset)
    p.update({"Ambient temperature [K]": T_C + 273.15, "Initial temperature [K]": T_C + 273.15, **WINDOW})
    return p


def pulse(pset, T_C, soc):
    p = params(pset, T_C)
    assert abs(p["Nominal cell capacity [A.h]"] - 5.0) < 1e-12
    exp = pybamm.Experiment(["Rest for 600 seconds (10 second period)",
                             f"Discharge at {I_PULSE} A for 10 seconds (0.1 second period)"])
    sim = pybamm.Simulation(pybamm.lithium_ion.DFN(), parameter_values=p, experiment=exp,
                            solver=pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8))
    sol = sim.solve(initial_soc=soc)
    rest, pul = sol.cycles[0], sol.cycles[1]
    v_rest = float(rest["Voltage [V]"].entries[-1])
    t_p = pul["Time [s]"].entries
    v_end = float(pul["Voltage [V]"].entries[-1])
    i_end = float(pul["Current [A]"].entries[-1])
    T_cell = float(pul["Volume-averaged cell temperature [K]"].entries[-1]) - 273.15
    assert abs(t_p[-1] - t_p[0] - 10.0) < 1e-9 and abs(i_end - I_PULSE) < 1e-9 and abs(T_cell - T_C) < 1e-9
    return {"set": pset, "soc": soc, "T_C": T_C, "V_rest_V": v_rest, "V_10s_V": v_end,
            "R_ohm": (v_rest - v_end) / I_PULSE}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int)                  # optional split across two processes
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()
    out = os.path.join(C.RESULTS, "stage4_RT.csv")
    if a.merge:
        rows = []
        for k in (0, 1):
            rows += list(csv.DictReader(open(os.path.join(C.RESULTS, f"stage4_RT_part{k}.csv"))))
            os.remove(os.path.join(C.RESULTS, f"stage4_RT_part{k}.csv"))
        rows.sort(key=lambda r: (SETS.index(r["set"]), -float(r["soc"]), float(r["T_C"])))
        write(rows, out)
        summarise(rows)
        return
    jobs = [(s, soc, T) for s in SETS for soc in SOCS for T in T_GRID]
    if a.part is not None:
        jobs = jobs[a.part::2]
    rows = []
    t0 = time.time()
    for i, (s, soc, T) in enumerate(jobs):
        r = pulse(s, T, soc)
        rows.append({k: (f"{v:.10g}" if isinstance(v, float) else v) for k, v in r.items()})
        if i % 20 == 0:
            print(i, len(jobs), s, soc, T, f"{r['R_ohm'] * 1e3:.4f} mOhm", f"{time.time() - t0:.0f} s", flush=True)
    if a.part is not None:
        write(rows, os.path.join(C.RESULTS, f"stage4_RT_part{a.part}.csv"))
    else:
        write(rows, out)
        summarise(rows)


def write(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["set", "soc", "T_C", "V_rest_V", "V_10s_V", "R_ohm"])
        w.writeheader()
        w.writerows(rows)


def summarise(rows):
    res = {"pybamm": pybamm.__version__, "model": "DFN, default options (isothermal at the ambient temperature)",
           "solver": "IDAKLUSolver(rtol=1e-6, atol=1e-8)", "window_V": [2.5, 4.2], "pulse": "rest 600 s, then 5 A for 10 s",
           "grid_C": [T_GRID[0], T_GRID[-1], 0.5], "sensitivity": {}}
    for s in SETS:
        for soc in SOCS:
            sel = sorted([r for r in rows if r["set"] == s and float(r["soc"]) == soc], key=lambda r: float(r["T_C"]))
            T = np.array([float(r["T_C"]) for r in sel])
            lnR = np.log([float(r["R_ohm"]) for r in sel])
            key = f"{s}|soc={soc:g}"
            res["sensitivity"][key] = {}
            for Tc in (-5.0, 0.0, 25.0):
                i = int(np.argmin(np.abs(T - Tc)))
                res["sensitivity"][key][f"{Tc:g}"] = {"dlnR_dT_per_K": float((lnR[i + 1] - lnR[i - 1]) / (T[i + 1] - T[i - 1])),
                                                      "R_mOhm": float(np.exp(lnR[i]) * 1e3)}
    json.dump(res, open(os.path.join(C.RESULTS, "stage4_RT.json"), "w"), indent=1)
    print(json.dumps(res["sensitivity"], indent=1))


if __name__ == "__main__":
    main()
