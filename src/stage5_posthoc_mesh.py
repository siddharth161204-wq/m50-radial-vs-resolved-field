#!/usr/bin/env python3
"""Stage 5, a post hoc check (D35), not part of the registered procedure: how one cell's DFN depends on the number of
points per particle radius. D30 registered PyBaMM's default mesh (20 points per particle radius, uniform). One
DFN, held at the ambient temperature, as in D27's single-cell runs and Stage 4's R(T), on the 2.5 to 4.2 V window:
- a 2C (10 A) discharge from 100 % to 2.5 V at minus 5 C and at 25 C;
- a constant-current charge from 0 % to 4.2 V at the specification's two limits (1,455 mA at 0 C and 3,395 mA at
  25 C), with the margin of D32 (phi_s,n - phi_e over the negative electrode's nodes and at the separator
  interface): its smallest value, when it first falls below zero, and the charge at 4.2 V;
- the largest charge rate (specification's C, 4.85 A) whose margin stays at or above zero to 4.2 V, at 0, 10 and
  25 C, by bisection to 0.001C (the cell at the ambient, not D32's two-way heat);
- Stage 4's pulse resistance (src/stage4_RT.py's procedure: 600 s rest, then 5 A for 10 s) at 100 %.
Both sets, with 20, 40, 80 and 160 points (and 320 for the minus 5 C discharge).

python3 src/stage5_posthoc_mesh.py -> results/stage5_posthoc_mesh.json"""
import json
import os
import sys
import time

import numpy as np
import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

C_SPEC = 4.85
WINDOW = {"Upper voltage cut-off [V]": 4.2, "Open-circuit voltage at 100% SOC [V]": 4.2,
          "Lower voltage cut-off [V]": 2.5, "Open-circuit voltage at 0% SOC [V]": 2.5}
MARGIN = ["Negative electrode surface potential difference [V]",
          "Negative electrode surface potential difference at separator interface [V]"]


def sim_for(pset, T_C, n, outputs, current_input=True):
    p = pybamm.ParameterValues(pset)
    T = 273.15 + T_C
    p.update({"Ambient temperature [K]": T, "Initial temperature [K]": T, **WINDOW})
    if current_input:
        p.update({"Current function [A]": pybamm.InputParameter("I")})
    m = pybamm.lithium_ion.DFN({"calculate heat source for isothermal models": "true"})
    vp = dict(m.default_var_pts)
    vp["r_n"] = vp["r_p"] = n
    solver = pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8, output_variables=outputs)
    return pybamm.Simulation(m, parameter_values=p, var_pts=vp, solver=solver)


def discharge(pset, T_C, n):
    I = 10.0
    sol = sim_for(pset, T_C, n, ["Voltage [V]"]).solve(np.arange(0, 20000.0, 1.0), initial_soc=1.0, inputs={"I": I})
    t = sol["Time [s]"].entries
    V = sol["Voltage [V]"].entries
    return {"t_cut_s": float(t[-1]), "capacity_Ah": I * float(t[-1]) / 3600,
            "energy_Wh": float(np.trapezoid(V * I, t) / 3600)}


def charge_margin(sim, I):
    sol = sim.solve(np.arange(0, 100000.0, 10.0), initial_soc=0.0, inputs={"I": -I})
    t = sol["Time [s]"].entries
    both = np.minimum(np.asarray(sol[MARGIN[0]].entries).min(axis=0), np.asarray(sol[MARGIN[1]].entries))
    neg = np.where(both < 0)[0]
    return {"margin_min_V": float(both.min()), "t_min_s": float(t[int(np.argmin(both))]),
            "t_first_negative_s": float(t[neg[0]]) if len(neg) else None, "t_end_s": float(t[-1]),
            "charge_Ah": I * float(t[-1]) / 3600}


def rate_limit(pset, T_C, n):
    sim = sim_for(pset, T_C, n, ["Voltage [V]"] + MARGIN)
    lo, hi = 0.05, 1.5
    if charge_margin(sim, lo * C_SPEC)["margin_min_V"] < 0:
        return {"rate_spec_C": None, "below": lo}
    while hi - lo > 0.001:
        mid = 0.5 * (lo + hi)
        if charge_margin(sim, mid * C_SPEC)["margin_min_V"] >= 0:
            lo = mid
        else:
            hi = mid
    return {"rate_spec_C": lo, "fails_at_spec_C": hi}


def pulse_R(pset, T_C, n):
    p = pybamm.ParameterValues(pset)
    p.update({"Ambient temperature [K]": T_C + 273.15, "Initial temperature [K]": T_C + 273.15, **WINDOW})
    m = pybamm.lithium_ion.DFN()
    vp = dict(m.default_var_pts)
    vp["r_n"] = vp["r_p"] = n
    exp = pybamm.Experiment(["Rest for 600 seconds (10 second period)",
                             "Discharge at 5.0 A for 10 seconds (0.1 second period)"])
    sol = pybamm.Simulation(m, parameter_values=p, experiment=exp, var_pts=vp,
                            solver=pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8)).solve(initial_soc=1.0)
    return (float(sol.cycles[0]["Voltage [V]"].entries[-1]) - float(sol.cycles[1]["Voltage [V]"].entries[-1])) / 5.0


def main():
    out = {"what": "post hoc (D35): one DFN at the ambient temperature against the particle mesh; not a registered reading",
           "pybamm": pybamm.__version__, "registered_points_per_particle_radius": 20, "results": {}}
    path = os.path.join(C.RESULTS, "stage5_posthoc_mesh.json")
    if os.path.exists(path):
        out["results"] = json.load(open(path)).get("results", {})     # resume: keep the meshes already done
    for pset in ("ORegan2022", "Chen2020"):
        res = out["results"].setdefault(pset, {})
        for n in (20, 40, 80, 160, 320):
            if str(n) in res:
                continue
            t0 = time.time()
            r = {}
            r["discharge_2C_m5C"] = discharge(pset, -5.0, n)
            if n <= 160:
                r["discharge_2C_25C"] = discharge(pset, 25.0, n)
                r["charge_1455mA_0C"] = charge_margin(sim_for(pset, 0.0, n, ["Voltage [V]"] + MARGIN), 1.455)
                r["charge_3395mA_25C"] = charge_margin(sim_for(pset, 25.0, n, ["Voltage [V]"] + MARGIN), 3.395)
                r["pulse_R_ohm"] = {f"{T:g}": pulse_R(pset, T, n) for T in (-5.0, 0.0, 25.0)}
            if n <= 80:
                r["plating_limited_rate_at_ambient"] = {f"{T:g}": rate_limit(pset, T, n) for T in (0.0, 10.0, 25.0)}
            r["wall_s"] = time.time() - t0
            res[str(n)] = r
            print(pset, n, json.dumps(r), flush=True)
            json.dump(out, open(path, "w"), indent=1)


if __name__ == "__main__":
    main()
