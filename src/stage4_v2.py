#!/usr/bin/env python3
"""Stage 4, V2 (D25): R(T) at minus 5, 0 and 25 C for both sets at 100 % state of charge, re-derived by code that
shares nothing with src/stage4_RT.py but the parameter sets and the window. The initial stoichiometries come from
PyBaMM's get_initial_stoichiometries and are written into the initial concentrations; the current is a constant
"Current function [A]" (no experiment, no rest); the voltage before the pulse is the open-circuit voltage
U_p(y0, T) - U_n(x0, T) evaluated from the electrode potentials; the solver tolerance is 100 times tighter.
python3 src/stage4_v2.py -> results/stage4_checks_v2.json"""
import csv
import json
import os
import sys

import numpy as np
import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def r_separate(pset, T_C):
    p = pybamm.ParameterValues(pset)
    T = T_C + 273.15
    p.update({"Upper voltage cut-off [V]": 4.2, "Open-circuit voltage at 100% SOC [V]": 4.2,
              "Lower voltage cut-off [V]": 2.5, "Open-circuit voltage at 0% SOC [V]": 2.5,
              "Ambient temperature [K]": T, "Initial temperature [K]": T, "Current function [A]": 5.0})
    x0, y0 = pybamm.lithium_ion.get_initial_stoichiometries(1.0, p)
    p.update({"Initial concentration in negative electrode [mol.m-3]": x0 * p["Maximum concentration in negative electrode [mol.m-3]"],
              "Initial concentration in positive electrode [mol.m-3]": y0 * p["Maximum concentration in positive electrode [mol.m-3]"]})
    prm = pybamm.LithiumIonParameters()
    Tsym = pybamm.Scalar(T)
    ocv = float(p.evaluate(prm.p.prim.U(pybamm.Scalar(y0), Tsym)) - p.evaluate(prm.n.prim.U(pybamm.Scalar(x0), Tsym)))
    sim = pybamm.Simulation(pybamm.lithium_ion.DFN(), parameter_values=p, solver=pybamm.IDAKLUSolver(rtol=1e-8, atol=1e-10))
    sol = sim.solve([0, 10.0], t_interp=np.linspace(0.0, 10.0, 201))
    v10 = float(sol["Voltage [V]"].entries[-1])
    return {"x0": float(x0), "y0": float(y0), "OCV_V": ocv, "V_10s_V": v10, "R_ohm": (ocv - v10) / 5.0}


def main():
    table = {(r["set"], float(r["soc"]), float(r["T_C"])): r for r in csv.DictReader(open(os.path.join(C.RESULTS, "stage4_RT.csv")))}
    out = {}
    for pset in ("ORegan2022", "Chen2020"):
        for T_C in (-5.0, 0.0, 25.0):
            v = r_separate(pset, T_C)
            t = table[(pset, 1.0, T_C)]
            v["R_table_ohm"] = float(t["R_ohm"])
            v["V_rest_table_V"] = float(t["V_rest_V"])
            v["rel_diff"] = v["R_ohm"] / v["R_table_ohm"] - 1
            v["within_0.1_percent"] = abs(v["rel_diff"]) < 1e-3
            out[f"{pset}|{T_C:g}C"] = v
            print(pset, T_C, f"{1e3 * v['R_ohm']:.5f} vs {1e3 * v['R_table_ohm']:.5f} mOhm, {100 * v['rel_diff']:+.4f} %", flush=True)
    out["all_within_0.1_percent"] = all(v["within_0.1_percent"] for k, v in out.items() if isinstance(v, dict))
    json.dump(out, open(os.path.join(C.RESULTS, "stage4_checks_v2.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
