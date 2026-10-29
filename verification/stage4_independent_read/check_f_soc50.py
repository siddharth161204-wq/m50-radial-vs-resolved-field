#!/usr/bin/env python3
"""Spot check of the 50 % SOC bracket rows of results/stage4_RT.csv (route A of check_f.py, initial_soc = 0.5)."""
import csv, json, os
import numpy as np
import pybamm
RES = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")), "results")
OUT = os.path.dirname(os.path.abspath(__file__))
def run(pset, T_C, soc):
    p = pybamm.ParameterValues(pset)
    for k, v in {"Ambient temperature [K]": 273.15 + T_C, "Initial temperature [K]": 273.15 + T_C,
                 "Upper voltage cut-off [V]": 4.2, "Open-circuit voltage at 100% SOC [V]": 4.2,
                 "Lower voltage cut-off [V]": 2.5, "Open-circuit voltage at 0% SOC [V]": 2.5}.items():
        p[k] = v
    exp = pybamm.Experiment(["Rest for 600 seconds (5 second period)", "Discharge at 1C for 10 seconds (0.05 second period)"])
    sol = pybamm.Simulation(pybamm.lithium_ion.DFN(), parameter_values=p, experiment=exp,
                            solver=pybamm.IDAKLUSolver(rtol=1e-7, atol=1e-9)).solve(initial_soc=soc)
    t, V, I = sol["Time [s]"].entries, sol["Voltage [V]"].entries, sol["Current [A]"].entries
    i0 = int(np.max(np.where((t <= 600 + 1e-9) & (np.abs(I) < 1e-12))[0])); i1 = int(np.argmin(np.abs(t - 610)))
    return float(V[i0]), float(V[i1]), float((V[i0] - V[i1]) / I[i1])
tab = {(r["set"], float(r["soc"]), float(r["T_C"])): r for r in csv.DictReader(open(os.path.join(RES, "stage4_RT.csv")))}
out = {}
for pset, T_C in (("ORegan2022", -5.0), ("Chen2020", 25.0)):
    Vr, Ve, R = run(pset, T_C, 0.5)
    tr = tab[(pset, 0.5, T_C)]
    out[f"{pset}|soc=0.5|{T_C:g}C"] = {"V_rest": Vr, "V_rest_table": float(tr["V_rest_V"]), "R": R, "R_table": float(tr["R_ohm"]),
                                       "rel_diff": R / float(tr["R_ohm"]) - 1}
json.dump(out, open(os.path.join(OUT, "out_f_soc50.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
