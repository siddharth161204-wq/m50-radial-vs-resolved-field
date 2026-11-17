#!/usr/bin/env python3
"""Independent read, item 7: the post hoc mesh check (D35's note; src/stage5_posthoc_mesh.py), reproduced with my
own PyBaMM script for ORegan2022 at a given number of points per particle radius.

One DFN (PyBaMM 26.9.0.0, default isothermal options plus the isothermal heat source, as D30), held at the ambient
("Ambient temperature [K]" = "Initial temperature [K]" = T), on D23's 2.5 to 4.2 V window, IDAKLU rtol 1e-6,
atol 1e-8, outputs requested on a 1 s (discharge) or 10 s (charge) grid with the solver's own steps kept:
  - the 1,455 mA charge from 0 % at 0 C to 4.2 V: the smallest margin phi_s,n - phi_e over the negative electrode's
    nodes and its separator-interface value, over the outputs, from PyBaMM's two variables and, separately, from
    the raw potentials (interface by linear extrapolation from the two nodes next to the separator);
  - the 2C (10 A) discharge from 100 % at 25 C to 2.5 V: the cut-off time.
The initial stoichiometries are set by passing initial_soc to the solve, as the stored script does, and the values
PyBaMM uses are recorded.
python3 -I -B ir_mesh.py <points per particle radius>   -> out/mesh_n<points>.json"""
import json
import os
import sys
import time

import numpy as np
import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402

N_R = int(sys.argv[1])
EXPLICIT = len(sys.argv) > 2 and sys.argv[2] == "explicit"      # initial stoichiometries written into the set (D30)
PSET = "ORegan2022"
WINDOW = {"Upper voltage cut-off [V]": 4.2, "Open-circuit voltage at 100% SOC [V]": 4.2,
          "Lower voltage cut-off [V]": 2.5, "Open-circuit voltage at 0% SOC [V]": 2.5}
MARG = ["Negative electrode surface potential difference [V]",
        "Negative electrode surface potential difference at separator interface [V]"]
POT = ["Negative electrode potential [V]", "Negative electrolyte potential [V]"]


def simulation(T_C, outputs, soc=None):
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
    return pybamm.Simulation(model, parameter_values=pv, var_pts=pts, solver=solver), pts


def charge_0C():
    sim, pts = simulation(0.0, ["Voltage [V]"] + MARG + POT, soc=0.0)
    I = 1.455
    t0 = time.time()
    kw = {} if EXPLICIT else {"initial_soc": 0.0}
    sol = sim.solve(np.arange(0.0, 100000.0, 10.0), inputs={"I_A": -I}, **kw)
    t = np.asarray(sol["Time [s]"].entries)
    V = np.asarray(sol["Voltage [V]"].entries)
    nodes = np.asarray(sol[MARG[0]].entries)                    # (nodes, times)
    iface = np.asarray(sol[MARG[1]].entries)
    both = np.minimum(nodes.min(axis=0), iface)
    k = int(np.argmin(both))
    ps = np.asarray(sol[POT[0]].entries)
    pe = np.asarray(sol[POT[1]].entries)
    d = ps - pe
    my_iface = 1.5 * d[-1] - 0.5 * d[-2]
    my_both = np.minimum(d.min(axis=0), my_iface)
    neg = np.where(both < 0)[0]
    return {"I_A": I, "margin_min_V": float(both[k]), "t_min_s": float(t[k]), "t_end_s": float(t[-1]),
            "t_first_negative_s": float(t[neg[0]]) if len(neg) else None, "V_end": float(V[-1]),
            "charge_Ah": I * float(t[-1]) / 3600.0, "n_outputs": int(len(t)),
            "margin_min_from_raw_potentials_V": float(my_both.min()),
            "raw_vs_pybamm_node_margin_max_abs_V": float(np.abs(d - nodes).max()),
            "raw_vs_pybamm_interface_max_abs_V": float(np.abs(my_iface - iface).max()),
            "margin_min_on_10s_grid_only_V": float(both[np.isclose(np.mod(t, 10.0), 0.0, atol=1e-6) |
                                                        np.isclose(np.mod(t, 10.0), 10.0, atol=1e-6)].min()),
            "termination": str(sol.termination), "wall_s": time.time() - t0,
            "points": {k_: int(v) for k_, v in pts.items()}}


def discharge_25C():
    sim, pts = simulation(25.0, ["Voltage [V]"], soc=1.0)
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
    out = {}
    for soc in (0.0, 1.0):
        x, y = pybamm.lithium_ion.get_initial_stoichiometries(soc, pv)
        out[f"{soc:g}"] = [float(x), float(y)]
    return out


if __name__ == "__main__":
    stored = json.load(open(os.path.join(L.RES, "stage5_posthoc_mesh.json")))["results"][PSET].get(str(N_R), {})
    res = {"points_per_particle_radius": N_R, "pybamm": pybamm.__version__,
           "initial_stoichiometries_x_n_y_p": initial_stoichiometries()}
    res["charge_1455mA_0C"] = charge_0C()
    print("charge done", json.dumps(res["charge_1455mA_0C"]), flush=True)
    res["discharge_2C_25C"] = discharge_25C()
    res["stored"] = {"charge_1455mA_0C": stored.get("charge_1455mA_0C"), "discharge_2C_25C": stored.get("discharge_2C_25C")}
    if stored:
        res["diff"] = {"margin_min_V": res["charge_1455mA_0C"]["margin_min_V"] - stored["charge_1455mA_0C"]["margin_min_V"],
                       "charge_t_end_s": res["charge_1455mA_0C"]["t_end_s"] - stored["charge_1455mA_0C"]["t_end_s"],
                       "discharge_t_cut_s": res["discharge_2C_25C"]["t_cut_s"] - stored["discharge_2C_25C"]["t_cut_s"]}
    res["peak_memory"] = L.mem_note()
    res["initial_state"] = "stoichiometries written into the set (D30's way)" if EXPLICIT else "initial_soc passed to the solve (the stored script's way)"
    L.dump(f"mesh_n{N_R}{'_explicit' if EXPLICIT else ''}.json", res)
    print(json.dumps(res, indent=1))
