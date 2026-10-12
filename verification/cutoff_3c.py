#!/usr/bin/env python3
"""Why the Chen2020 discharge stops at about 2.3 A h at 3C (README, heat generation): the state of the particles at the
2.5 V cut-off. Re-runs the registered 3C discharges (same settings as src/heat_generation.py) and records, at the
cut-off, the positive and negative particle surface and volume-averaged stoichiometries and the electrolyte
concentration range. Writes verification/cutoff_3c.json."""
import json, os, sys
import numpy as np
import pybamm
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import common as C

out = {}
for Ta in (-5.0, 25.0):
    cc = C.cell_constants("21700")
    p = pybamm.ParameterValues("Chen2020")
    p.update({"Ambient temperature [K]": Ta + 273.15, "Initial temperature [K]": Ta + 273.15,
              "Total heat transfer coefficient [W.m-2.K-1]": C.H_PAPER, "Cell volume [m3]": cc["V"],
              "Cell cooling surface area [m2]": cc["A_lateral"], "Cell heat capacity [J.K-1.m-3]": cc["C_total"] / cc["V"]},
             check_already_exists=False)
    m = pybamm.lithium_ion.DFN({"thermal": "lumped", "use lumped thermal capacity": "true"})
    exp = pybamm.Experiment([f"Discharge at {3 * C.NOMINAL_AH} A until 2.5 V"], period="1 second")
    sol = pybamm.Simulation(m, parameter_values=p, experiment=exp,
                            solver=pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8)).solve(initial_soc=1.0)
    g = lambda n: np.asarray(sol[n].entries)
    pos_surf = g("Positive particle surface stoichiometry")[:, -1]
    pos_avg = g("Average positive particle stoichiometry")[-1]
    neg_surf = g("Negative particle surface stoichiometry")[:, -1]
    neg_avg = g("Average negative particle stoichiometry")[-1]
    ce = g("Electrolyte concentration [mol.m-3]")[:, -1]
    out[f"{Ta:+.0f} C"] = {"t_end_s": float(g("Time [s]")[-1]), "capacity_Ah": float(g("Discharge capacity [A.h]")[-1]),
        "positive_surface_stoichiometry_min_max": [float(pos_surf.min()), float(pos_surf.max())],
        "positive_average_stoichiometry": float(pos_avg),
        "negative_surface_stoichiometry_min_max": [float(neg_surf.min()), float(neg_surf.max())],
        "negative_average_stoichiometry": float(neg_avg),
        "electrolyte_concentration_min_max_mol_m3": [float(ce.min()), float(ce.max())]}
    print(Ta, json.dumps(out[f"{Ta:+.0f} C"]))
json.dump(out, open(os.path.join(ROOT, "verification", "cutoff_3c.json"), "w"), indent=2)
