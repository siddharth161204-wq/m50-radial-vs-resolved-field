#!/usr/bin/env python3
"""Independent read, item 7: the post hoc mesh check (D35; src/stage5_posthoc_mesh.py, results/stage5_posthoc_mesh.json)
reproduced with my own PyBaMM script, for one set at a given number of points per particle radius.

One DFN (PyBaMM 26.9.0.0, default isothermal options plus the isothermal heat source, as D30), held at the ambient
("Ambient temperature [K]" = "Initial temperature [K]" = T), on D23's 2.5 to 4.2 V window, IDAKLU rtol 1e-6,
atol 1e-8, outputs requested on a 1 s (discharge) or 10 s (charge) grid with the solver's own steps kept. Items:
  c0   the 1,455 mA charge from 0 % at 0 C to 4.2 V: the smallest margin phi_s,n - phi_e over the negative
       electrode's nodes and its separator-interface value, over the outputs, from PyBaMM's two variables and,
       separately, from the raw potentials (interface by linear extrapolation from the two nodes next to the separator)
  c25  the same at 3,395 mA and 25 C
  d25  the 2C (10 A) discharge from 100 % at 25 C to 2.5 V: the cut-off time
  dm5  the same at minus 5 C
The initial stoichiometries are set by passing initial_soc to the solve, as the stored script does ("explicit": written
into the set instead, as the coupled models do, D30).
python3 -I -B ir_mesh.py <points> [explicit] [set=ORegan2022] [items=c0,d25]  -> out/mesh_<set>_n<points>[_explicit].json"""
import json
import os
import sys
import time

import numpy as np
import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402

N_R = int(sys.argv[1])
EXPLICIT = "explicit" in sys.argv[2:]
OPTS = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
PSET = OPTS.get("set", "ORegan2022")
ITEMS = OPTS.get("items", "c0,d25").split(",")
WINDOW = {"Upper voltage cut-off [V]": 4.2, "Open-circuit voltage at 100% SOC [V]": 4.2,
          "Lower voltage cut-off [V]": 2.5, "Open-circuit voltage at 0% SOC [V]": 2.5}
MARG = ["Negative electrode surface potential difference [V]",
        "Negative electrode surface potential difference at separator interface [V]"]
POT = ["Negative electrode potential [V]", "Negative electrolyte potential [V]"]
STORED_KEY = {"c0": "charge_1455mA_0C", "c25": "charge_3395mA_25C", "d25": "discharge_2C_25C", "dm5": "discharge_2C_m5C"}


def simulation(T_C, outputs, soc):
    pv = pybamm.ParameterValues(PSET)
    pv.update(WINDOW)
    if EXPLICIT:
        x, y = pybamm.lithium_ion.get_initial_stoichiometries(soc, pv)
        pv.update({"Initial concentration in negative electrode [mol.m-3]": x * pv["Maximum concentration in negative electrode [mol.m-3]"],
                   "Initial concentration in positive electrode [mol.m-3]": y * pv["Maximum concentration in positive electrode [mol.m-3]"]})
    pv.update({"Ambient temperature [K]": 273.15 + T_C, "Initial temperature [K]": 273.15 + T_C,
               "Current function [A]": pybamm.InputParameter("I_A")})
    model = pybamm.lithium_ion.DFN({"calculate heat source for isothermal models": "true"})
    pts = dict(model.default_var_pts)
    pts["r_n"] = N_R
    pts["r_p"] = N_R
    solver = pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8, output_variables=outputs)
    return pybamm.Simulation(model, parameter_values=pv, var_pts=pts, solver=solver)


def charge(T_C, I):
    sim = simulation(T_C, ["Voltage [V]"] + MARG + POT, 0.0)
    t0 = time.time()
    kw = {} if EXPLICIT else {"initial_soc": 0.0}
    sol = sim.solve(np.arange(0.0, 100000.0, 10.0), inputs={"I_A": -I}, **kw)
    t = np.asarray(sol["Time [s]"].entries)
    V = np.asarray(sol["Voltage [V]"].entries)
    nodes = np.asarray(sol[MARG[0]].entries)                    # (nodes, times)
    iface = np.asarray(sol[MARG[1]].entries)
    both = np.minimum(nodes.min(axis=0), iface)
    k = int(np.argmin(both))
    d = np.asarray(sol[POT[0]].entries) - np.asarray(sol[POT[1]].entries)
    my_iface = d[-1] + 0.5 * (d[-1] - d[-2])
    my_both = np.minimum(d.min(axis=0), my_iface)
    neg = np.where(both < 0)[0]
    return {"I_A": I, "margin_min_V": float(both[k]), "t_min_s": float(t[k]), "t_end_s": float(t[-1]),
            "t_first_negative_s": float(t[neg[0]]) if len(neg) else None, "V_end": float(V[-1]),
            "charge_Ah": I * float(t[-1]) / 3600.0, "n_outputs": int(len(t)),
            "margin_min_from_raw_potentials_V": float(my_both.min()),
            "raw_vs_pybamm_node_margin_max_abs_V": float(np.abs(d - nodes).max()),
            "raw_vs_pybamm_interface_max_abs_V": float(np.abs(my_iface - iface).max()),
            "termination": str(sol.termination), "wall_s": time.time() - t0}


def discharge(T_C):
    sim = simulation(T_C, ["Voltage [V]"], 1.0)
    I = 10.0
    t0 = time.time()
    kw = {} if EXPLICIT else {"initial_soc": 1.0}
    sol = sim.solve(np.arange(0.0, 20000.0, 1.0), inputs={"I_A": I}, **kw)
    t = np.asarray(sol["Time [s]"].entries)
    V = np.asarray(sol["Voltage [V]"].entries)
    return {"I_A": I, "t_cut_s": float(t[-1]), "V_end": float(V[-1]), "capacity_Ah": I * float(t[-1]) / 3600.0,
            "energy_Wh": float(np.sum(0.5 * (V[1:] + V[:-1]) * I * np.diff(t)) / 3600.0),
            "termination": str(sol.termination), "wall_s": time.time() - t0, "n_outputs": int(len(t))}


def initial_stoichiometries():
    pv = pybamm.ParameterValues(PSET)
    pv.update(WINDOW)
    return {f"{soc:g}": [float(v) for v in pybamm.lithium_ion.get_initial_stoichiometries(soc, pv)] for soc in (0.0, 1.0)}


if __name__ == "__main__":
    stored = json.load(open(os.path.join(L.RES, "stage5_posthoc_mesh.json")))["results"].get(PSET, {}).get(str(N_R), {})
    res = {"set": PSET, "points_per_particle_radius": N_R, "pybamm": pybamm.__version__,
           "initial_state": "stoichiometries written into the set (D30's way)" if EXPLICIT else "initial_soc passed to the solve (the stored script's way)",
           "initial_stoichiometries_x_n_y_p": initial_stoichiometries(), "items": {}, "stored": {}, "diff": {}}
    run = {"c0": lambda: charge(0.0, 1.455), "c25": lambda: charge(25.0, 3.395), "d25": lambda: discharge(25.0),
           "dm5": lambda: discharge(-5.0)}
    for it in ITEMS:
        key = STORED_KEY[it]
        r = run[it]()
        res["items"][key] = r
        s = stored.get(key)
        res["stored"][key] = s
        if s:
            if it.startswith("c"):
                res["diff"][key] = {"margin_min_V": r["margin_min_V"] - s["margin_min_V"], "t_end_s": r["t_end_s"] - s["t_end_s"],
                                    "charge_Ah": r["charge_Ah"] - s["charge_Ah"]}
            else:
                res["diff"][key] = {"t_cut_s": r["t_cut_s"] - s["t_cut_s"], "energy_Wh": r["energy_Wh"] - s["energy_Wh"]}
        print(key, json.dumps({k: v for k, v in r.items() if k != "points"}), flush=True)
    res["peak_memory"] = L.mem_note()
    L.dump(f"mesh_{PSET}_n{N_R}{'_explicit' if EXPLICIT else ''}.json", res)
    print(json.dumps(res["diff"], indent=1), res["peak_memory"])
