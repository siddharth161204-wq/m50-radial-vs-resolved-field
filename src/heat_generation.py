#!/usr/bin/env python3
"""Heat generation of the LG M50 with PyBaMM's DFN and lumped thermal model (input 1 of the brief; D3).

Registered: parameter set Chen2020, as the brief names it, with PyBaMM's default heat (Ohmic, irreversible reaction
and reversible terms; no heat of mixing). Secondary (reported, never scored): Chen2020 with the heat of mixing
switched on, and ORegan2022 with the same thermal settings. Each run discharges at 1.25C, 2C or 3C of the 5 A h nominal capacity from 100 % state of
charge (initial_soc = 1, the 4.2 V upper cut-off) to the set's lower cut-off of 2.5 V, with the lumped thermal
model at h = 400 W/(m2 K) on the lateral area only (the paper's boundary condition), an initial temperature equal
to the ambient, and the cell heat capacity of the thermal models of this study (65.18 J/K for the 21700, D4).

Recorded every second: current, terminal voltage, the total heat generation rate "Total heating [W]" (PyBaMM: the
heat per unit electrode-pair area times the electrode area), its Ohmic, irreversible and reversible parts, and
the volume-averaged (lumped) temperature. Also recorded: the duration, the capacity and energy delivered, the
first time the voltage reaches 2.6 V (the paper's cut-off for its training data, p. 2), and two energy checks: the
Ohmic plus irreversible heat against I (U_p,w - U_n,w - V), with the electrode potentials at the particle surfaces
weighted by the local reaction current, an identity of the model that it must match; and the heat against
I (U_bulk - V), which it falls short of by the energy that goes into concentration gradients (the heat of mixing).

Usage: python3 src/heat_generation.py [--sets Chen2020,ORegan2022]
"""
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

OUT = os.path.join(C.RESULTS, "heat")


def run(pset, T_amb_C, crate, cell="21700", mixing=False):
    cc = C.cell_constants(cell)
    p = pybamm.ParameterValues(pset)
    p.update({
        "Ambient temperature [K]": T_amb_C + 273.15,
        "Initial temperature [K]": T_amb_C + 273.15,
        "Total heat transfer coefficient [W.m-2.K-1]": C.H_PAPER,
        "Cell volume [m3]": cc["V"],
        "Cell cooling surface area [m2]": cc["A_lateral"],
        "Cell heat capacity [J.K-1.m-3]": cc["C_total"] / cc["V"],
    }, check_already_exists=False)
    opts = {"thermal": "lumped", "use lumped thermal capacity": "true"}
    if mixing:
        opts["heat of mixing"] = "true"
    model = pybamm.lithium_ion.DFN(opts)
    I = crate * C.NOMINAL_AH
    v_cut = p["Lower voltage cut-off [V]"]
    exp = pybamm.Experiment([f"Discharge at {I} A until {v_cut} V"], period="1 second")
    solver = pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8)
    sim = pybamm.Simulation(model, parameter_values=p, experiment=exp, solver=solver)
    t0 = time.time()
    sol = sim.solve(initial_soc=1.0)
    wall = time.time() - t0
    g = lambda name: np.asarray(sol[name].entries, dtype=float)
    t = g("Time [s]")
    V = g("Terminal voltage [V]")
    Iarr = g("Current [A]")
    Q = g("Total heating [W]")
    Q_ohm = g("Ohmic heating [W]")
    Q_irr = g("Irreversible electrochemical heating [W]")
    Q_rev = g("Reversible heating [W]")
    T = g("Volume-averaged cell temperature [K]") - 273.15
    cap = g("Discharge capacity [A.h]")
    U_bulk = g("Bulk open-circuit voltage [V]")
    U_surf = g("Surface open-circuit voltage [V]")
    Q_mix = g("Heat of mixing [W]") if mixing else np.zeros_like(t)
    # exact power identity of the DFN: Ohmic plus irreversible heat equals I (U_p,w - U_n,w - V), where U_k,w is the
    # open-circuit potential at the particle surfaces weighted by the local reaction current (uniform x mesh)
    aj_n = np.asarray(sol["Negative electrode volumetric interfacial current density [A.m-3]"].entries)
    aj_p = np.asarray(sol["Positive electrode volumetric interfacial current density [A.m-3]"].entries)
    U_n = np.asarray(sol["Negative electrode open-circuit potential [V]"].entries)
    U_p = np.asarray(sol["Positive electrode open-circuit potential [V]"].entries)
    U_w = (aj_p * U_p).sum(axis=0) / aj_p.sum(axis=0) - (aj_n * U_n).sum(axis=0) / aj_n.sum(axis=0)
    # first time the voltage reaches 2.6 V
    t26 = None
    below = np.where(V <= 2.6)[0]
    if len(below):
        k = below[0]
        t26 = float(np.interp(2.6, [V[k], V[k - 1]], [t[k], t[k - 1]])) if k > 0 else float(t[k])
    E_heat = float(np.trapezoid(Q, t))
    E_surf = float(np.trapezoid(Iarr * (U_surf - V), t))
    E_w = float(np.trapezoid(Iarr * (U_w - V), t))
    E_ohm_irr = float(np.trapezoid(Q_ohm + Q_irr, t))
    E_bulk = float(np.trapezoid(Iarr * (U_bulk - V), t))
    rows = np.column_stack([t, Iarr, V, Q, Q_ohm, Q_irr, Q_rev, Q_mix, T, cap])
    name = f"{pset}_{T_amb_C:+.0f}C_{crate:g}C".replace("+", "p").replace("-", "m") + ("_mixing" if mixing else "")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "current_A", "voltage_V", "heat_total_W", "heat_ohmic_W", "heat_irreversible_W",
                    "heat_reversible_W", "heat_of_mixing_W", "T_lumped_C", "capacity_Ah"])
        for r in rows:
            w.writerow([f"{x:.9g}" for x in r])
    summ = {
        "name": name, "parameter_set": pset, "heat_of_mixing": mixing, "registered": pset == "Chen2020" and not mixing,
        "T_amb_C": T_amb_C, "c_rate": crate,
        "current_A": I, "cut_off_V": v_cut, "duration_s": float(t[-1]), "capacity_Ah": float(cap[-1]),
        "energy_Wh": float(np.trapezoid(Iarr * V, t) / 3600), "heat_J": E_heat,
        "heat_mean_W": E_heat / float(t[-1]), "heat_max_W": float(Q.max()), "heat_end_W": float(Q[-1]),
        "T_lumped_end_C": float(T[-1]), "T_lumped_max_C": float(T.max()),
        "T_lumped_mean_C": float(np.trapezoid(T, t) / t[-1]),
        "t_at_2p6V_s": t26, "heat_of_mixing_J": float(np.trapezoid(Q_mix, t)),
        "ohmic_plus_irreversible_J": E_ohm_irr, "reversible_J": float(np.trapezoid(Q_rev, t)),
        "check_I_times_Uweighted_minus_V_J": E_w, "ohmic_irreversible_over_weighted_check": E_ohm_irr / E_w,
        "check_I_times_Usurface_minus_V_J": E_surf, "heat_over_surface_check": E_heat / E_surf,
        "check_I_times_Ubulk_minus_V_J": E_bulk, "heat_over_bulk_check": E_heat / E_bulk, "wall_s": wall,
        "q_vol_mean_W_m3": E_heat / float(t[-1]) / C.cell_constants(cell)["V"],
    }
    return summ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", default="Chen2020,Chen2020+mixing,ORegan2022")
    a = ap.parse_args()
    out = []
    for spec in a.sets.split(","):
        pset, mixing = spec.replace("+mixing", ""), spec.endswith("+mixing")
        for Ta in C.AMBIENTS_C:
            for cr in C.C_RATES:
                s = run(pset, Ta, cr, mixing=mixing)
                out.append(s)
                print(f"{s['name']:30s} {s['duration_s']:8.1f} s {s['capacity_Ah']:6.3f} Ah  Q mean {s['heat_mean_W']:6.3f} W "
                      f"max {s['heat_max_W']:6.3f} W  T_end {s['T_lumped_end_C']:6.2f} C  t(2.6 V) {s['t_at_2p6V_s']:.1f}  "
                      f"(Qohm+Qirr)/weighted {s['ohmic_irreversible_over_weighted_check']:.5f}  Q/bulk {s['heat_over_bulk_check']:.4f}  "
                      f"mixing {s['heat_of_mixing_J']:.0f} J", flush=True)
    meta = {"pybamm_version": pybamm.__version__, "model": "DFN", "options": {"thermal": "lumped",
            "use lumped thermal capacity": "true"}, "solver": "IDAKLUSolver(rtol=1e-6, atol=1e-8)",
            "initial_soc": 1.0, "period_s": 1.0, "h_W_m2K": C.H_PAPER, "cooling_area": "lateral, 2 pi R H",
            "cell": C.cell_constants("21700"), "runs": out}
    with open(os.path.join(C.RESULTS, "heat_summary.json"), "w") as f:
        json.dump(meta, f, indent=2)
    keys = ["name", "parameter_set", "heat_of_mixing", "registered", "T_amb_C", "c_rate", "current_A", "duration_s",
            "capacity_Ah", "energy_Wh", "heat_J", "heat_mean_W", "heat_max_W", "heat_end_W", "T_lumped_mean_C",
            "T_lumped_end_C", "t_at_2p6V_s", "q_vol_mean_W_m3", "heat_of_mixing_J", "reversible_J",
            "ohmic_irreversible_over_weighted_check", "heat_over_bulk_check"]
    with open(os.path.join(C.RESULTS, "heat_summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keys)
        for s in out:
            w.writerow([s[k] for k in keys])


if __name__ == "__main__":
    main()
