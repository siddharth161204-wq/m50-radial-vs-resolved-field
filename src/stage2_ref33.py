#!/usr/bin/env python3
"""Stage 2, Part A (D17): the paper's factor split into a property part (ref. 33's fitted thermal values in place of
O'Regan's), a heat part (ref. 33's electrochemical set run in PyBaMM at the paper's conditions) and a remainder; and B3,
the end-corrected model with ref. 33's properties. Writes results/heat/Ref33_*.csv, results/stage2_ref33.json/.csv."""
import csv
import json
import os
import sys
import time

import numpy as np
import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402
from stage2_correction import Corrected  # noqa: E402

F, RG = 96485.33212, pybamm.constants.R
# ref. 33, Table 1 (p. 4): fitted values at 25 C
K0N, K0P, DN, DP = 1.15e-11, 6.70e-11, 6.50e-14, 5.17e-15
LAMBDA33, DIFF33 = 0.62, 1.80e-7
# Table 1 untuned values ("from [46]") checked against ORegan2022
TABLE1 = {"Negative current collector thickness [m]": 1.2e-5, "Negative electrode thickness [m]": 8.52e-5,
          "Positive electrode thickness [m]": 7.56e-5, "Separator thickness [m]": 1.2e-5,
          "Positive current collector thickness [m]": 1.6e-5, "Negative particle radius [m]": 5.86e-6,
          "Positive particle radius [m]": 5.22e-6, "Negative current collector density [kg.m-3]": 8933.0,
          "Positive current collector density [kg.m-3]": 2702.0, "Negative electrode density [kg.m-3]": 2060.0,
          "Positive electrode density [kg.m-3]": 3699.0, "Separator density [kg.m-3]": 1548.0,
          "Negative electrode porosity": 0.25, "Positive electrode porosity": 0.335,
          "Maximum concentration in negative electrode [mol.m-3]": 29583.0,
          "Maximum concentration in positive electrode [mol.m-3]": 51765.0,
          "Initial concentration in negative electrode [mol.m-3]": 28866.0,
          "Initial concentration in positive electrode [mol.m-3]": 13975.0,
          "Initial concentration in electrolyte [mol.m-3]": 1000.0, "Negative electrode conductivity [S.m-1]": 215.0}
LAYERS = [(1.2e-5, 8933.0), (8.52e-5, 2060.0), (1.2e-5, 1548.0), (7.56e-5, 3699.0), (1.6e-5, 2702.0)]
RHO33 = sum(l * r for l, r in LAYERS) / sum(l for l, _ in LAYERS)          # Eq. B.3
RHOC33 = LAMBDA33 / DIFF33
PAPER = {"1.25C 25 C": 2.878081797006585, "2C 25 C": 5.9398380346298225, "2C minus 5 C": 11.539778811249276,
         "4680 2C minus 5 C": 37.528607054525295}                               # V4 (verification/v4.json)
CONDS = [("1.25C 25 C", "p25C_1.25C", "21700", None), ("2C 25 C", "p25C_2C", "21700", None),
         ("2C minus 5 C", "m5C_2C", "21700", (482.4, 540.0)), ("4680 2C minus 5 C", "m5C_2C", "4680", None)]


def arr(E):
    return lambda T: pybamm.exp(E / RG * (1 / 298.15 - 1 / T))


def ref33_parameters():
    p = pybamm.ParameterValues("ORegan2022")
    checks = {k: (float(p[k]), v) for k, v in TABLE1.items() if isinstance(p[k], (int, float))}
    an, ap, dn, dp = arr(4.0e4), arr(2.401e4), arr(2092 * RG), arr(1449 * RG)
    p.update({
        "Negative electrode exchange-current density [A.m-2]":
            lambda c_e, c_s, c_max, T: F * K0N * c_max * pybamm.sqrt(c_e * (c_s / c_max) * (1 - c_s / c_max)) * an(T),
        "Positive electrode exchange-current density [A.m-2]":
            lambda c_e, c_s, c_max, T: F * K0P * c_max * pybamm.sqrt(c_e * (c_s / c_max) * (1 - c_s / c_max)) * ap(T),
        "Negative particle diffusivity [m2.s-1]": lambda sto, T: DN * dn(T),
        "Positive particle diffusivity [m2.s-1]": lambda sto, T: DP * dp(T)})
    return p, checks


def run_ref33(T_amb_C, crate):
    cc = C.cell_constants("21700")
    c_can = cc["C_total"] - cc["rho_cp"] * cc["V"]
    p, _ = ref33_parameters()
    p.update({"Ambient temperature [K]": T_amb_C + 273.15, "Initial temperature [K]": T_amb_C + 273.15,
              "Total heat transfer coefficient [W.m-2.K-1]": C.H_PAPER, "Cell volume [m3]": cc["V"],
              "Cell cooling surface area [m2]": cc["A_lateral"],
              "Cell heat capacity [J.K-1.m-3]": (RHOC33 * cc["V"] + c_can) / cc["V"]}, check_already_exists=False)
    model = pybamm.lithium_ion.DFN({"thermal": "lumped", "use lumped thermal capacity": "true"})
    I = crate * C.NOMINAL_AH
    exp = pybamm.Experiment([f"Discharge at {I} A until 2.5 V"], period="1 second")
    t0 = time.time()
    sol = pybamm.Simulation(model, parameter_values=p, experiment=exp,
                            solver=pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8)).solve()
    g = lambda n: np.asarray(sol[n].entries, dtype=float)
    t, V, Q = g("Time [s]"), g("Terminal voltage [V]"), g("Total heating [W]")
    cols = [t, g("Current [A]"), V, Q, g("Ohmic heating [W]"), g("Irreversible electrochemical heating [W]"),
            g("Reversible heating [W]"), np.zeros_like(t), g("Volume-averaged cell temperature [K]") - 273.15,
            g("Discharge capacity [A.h]")]
    name = f"Ref33_{'m5C' if T_amb_C < 0 else 'p25C'}_{crate:g}C"
    with open(os.path.join(C.RESULTS, "heat", name + ".csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "current_A", "voltage_V", "heat_total_W", "heat_ohmic_W", "heat_irreversible_W",
                    "heat_reversible_W", "heat_of_mixing_W", "T_lumped_C", "capacity_Ah"])
        for r in np.column_stack(cols):
            w.writerow([f"{x:.9g}" for x in r])
    k = np.where(V <= 2.6)[0]
    return name, {"duration_s": float(t[-1]), "capacity_Ah": float(cols[-1][-1]), "heat_J": float(np.trapezoid(Q, t)),
                  "heat_mean_W": float(np.trapezoid(Q, t) / t[-1]), "T_lumped_end_C": float(cols[8][-1]),
                  "t_at_2p6V_s": float(t[k[0]]) if len(k) else None, "wall_s": time.time() - t0}


def heat_upto(name, t_lim):
    d = np.loadtxt(os.path.join(C.RESULTS, "heat", name + ".csv"), delimiter=",", skiprows=1)
    t, Q = d[:, 0], d[:, 3]
    if t[-1] < t_lim:
        return None
    m = t <= t_lim
    tt, QQ = np.append(t[m], t_lim), np.append(Q[m], np.interp(t_lim, t, Q))
    return float(np.trapezoid(QQ, tt))


def spread(model_cls, cell, props, heat, times):
    q, t_end, _ = R1.load_heat(heat)
    m = model_cls(cell, props=props)
    if times:
        ok = [ts for ts in times if ts <= t_end]
        r = m.run(q, t_end, R1.amb_of(heat), snap_times=ok)
        return {ts: (r["snaps"][ts]["unit_spread"] if ts in r["snaps"] else None) for ts in times}, t_end
    return {"end": m.run(q, t_end, R1.amb_of(heat))["end"]["unit_spread"]}, t_end


def main():
    reg = C.roll_properties()["registered"]
    p33 = dict(reg, rho=RHO33, cp=RHOC33 / RHO33, k_across=LAMBDA33)
    _, checks = ref33_parameters()
    out = {"ref33": {"lambda": LAMBDA33, "diffusivity": DIFF33, "rho_c": RHOC33, "rho_eq_B3": RHO33,
                     "k_z_used_for_correction": reg["k_along"], "table1_vs_ORegan2022": checks,
                     "table1_all_equal": all(abs(a - b) <= 1e-9 * max(1, abs(b)) for a, b in checks.values())},
           "runs": {}, "heat_window": {}, "conditions": {}}
    for Ta, cr in ((-5.0, 2.0), (25.0, 1.25), (25.0, 2.0)):
        name, s = run_ref33(Ta, cr)
        out["runs"][name] = s
        print(name, json.dumps(s), flush=True)
    for tl in (482.4, 540.0):
        a, b = heat_upto("Ref33_m5C_2C", tl), heat_upto("Chen2020_m5C_2C", tl)
        out["heat_window"][f"{tl:g}"] = {"ref33_J": a, "chen2020_J": b, "ratio": (a / b) if a else None}
    rows = []
    for label, cond, cell, times in CONDS:
        so, _ = spread(R1.Radial1D, cell, reg, f"Chen2020_{cond}", times)
        s3, _ = spread(R1.Radial1D, cell, p33, f"Chen2020_{cond}", times)
        sh, t_end33 = spread(R1.Radial1D, cell, p33, f"Ref33_{cond}", times)
        co, _ = spread(Corrected, cell, p33, f"Chen2020_{cond}", times)
        ch, _ = spread(Corrected, cell, p33, f"Ref33_{cond}", times)
        rec = {}
        for key in so:
            o, a3, h3 = so[key], s3[key], sh.get(key)
            f_o, f_3 = PAPER[label] / o, PAPER[label] / a3
            rec[str(key)] = {"spread_oregan_chen_K": o, "spread_ref33props_chen_K": a3, "spread_ref33props_ref33heat_K": h3,
                             "factor_oregan": f_o, "factor_ref33props": f_3, "property_ratio": a3 / o,
                             "heat_ratio": (h3 / a3) if h3 else None, "remainder": (PAPER[label] / h3) if h3 else None,
                             "corrected_spread_ref33props_chen_K": co[key], "corrected_spread_ref33props_ref33heat_K": ch.get(key),
                             "ref33_discharge_end_s": t_end33}
            r = rec[str(key)]
            rows.append([label, key, PAPER[label], o, a3, h3, f_o, f_3, r["property_ratio"], r["heat_ratio"],
                         r["remainder"], co[key], ch.get(key)])
            print(label, key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
        out["conditions"][label] = rec
    json.dump(out, open(os.path.join(C.RESULTS, "stage2_ref33.json"), "w"), indent=1)
    with open(os.path.join(C.RESULTS, "stage2_ref33.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["condition", "time", "paper_K", "model_oregan_chen2020_K", "model_ref33props_chen2020_K",
                    "model_ref33props_ref33heat_K", "factor_oregan", "factor_ref33props", "property_ratio",
                    "heat_ratio", "remainder", "corrected_ref33props_chen2020_K", "corrected_ref33props_ref33heat_K"])
        for r in rows:
            w.writerow([f"{x:.6g}" if isinstance(x, float) else ("" if x is None else x) for x in r])


if __name__ == "__main__":
    main()
