#!/usr/bin/env python3
"""Effective jelly-roll properties of the LG M50 from PyBaMM's "ORegan2022" parameter set (D4).

The computation is the two-cell study's (inputs/twocell_oregan2022_properties.py, copied unchanged from
github.com/siddharth161204-wq/m50-two-cell-pilot at v1.0.0): one electrode pair per unit area made of half the
copper foil, the negative electrode, the separator, the positive electrode and half the aluminium foil; density
and specific heat mass-weighted; conductivity across the layers the series (harmonic) mean and along the layers
the parallel (arithmetic) mean, both thickness-weighted. Here it is evaluated at 25 C, the parameter set's
reference temperature (registered), and at -5, 0 and 40 C for the sensitivity named in D4.

Usage: python3 inputs/properties.py   (writes inputs/properties.json and inputs/properties.txt)
"""
import json
import os

import pybamm

HERE = os.path.dirname(os.path.abspath(__file__))
p = pybamm.ParameterValues("ORegan2022")


def ev(name, T):
    v = p[name]
    if callable(v):
        return float(p.process_symbol(v(pybamm.Scalar(T))).evaluate())
    return float(v)


names = {"cn": "Negative current collector", "n": "Negative electrode", "s": "Separator",
         "p": "Positive electrode", "cp": "Positive current collector"}
L = {"cn": p["Negative current collector thickness [m]"] / 2, "n": p["Negative electrode thickness [m]"],
     "s": p["Separator thickness [m]"], "p": p["Positive electrode thickness [m]"],
     "cp": p["Positive current collector thickness [m]"] / 2}
Ltot = sum(L.values())


def at(TC):
    T = TC + 273.15
    rho = {k: ev(names[k] + " density [kg.m-3]", T) for k in L}
    cp = {k: ev(names[k] + " specific heat capacity [J.kg-1.K-1]", T) for k in L}
    kk = {k: ev(names[k] + " thermal conductivity [W.m-1.K-1]", T) for k in L}
    m = sum(rho[k] * L[k] for k in L)
    return {"T_C": TC, "rho": m / Ltot, "cp": sum(rho[k] * cp[k] * L[k] for k in L) / m,
            "k_across": Ltot / sum(L[k] / kk[k] for k in L), "k_along": sum(kk[k] * L[k] for k in L) / Ltot}


rows = [at(TC) for TC in (-5.0, 0.0, 25.0, 40.0)]
reg = dict(next(r for r in rows if r["T_C"] == 25.0))
reg["source"] = ("O'Regan et al. 2022 (Electrochim. Acta 425, 140700) through PyBaMM " + pybamm.__version__ +
                 " parameter set ORegan2022, effective roll values at 25 C (the set's reference temperature), "
                 "computed as in the two-cell study (doi:10.5281/zenodo.23253738, inputs/oregan2022_properties.py)")
out = {"pybamm_version": pybamm.__version__, "pair_thickness_m": Ltot, "registered": reg, "table": rows}
with open(os.path.join(HERE, "properties.json"), "w") as f:
    json.dump(out, f, indent=2)
with open(os.path.join(HERE, "properties.txt"), "w") as f:
    f.write(f"PyBaMM {pybamm.__version__}, parameter set ORegan2022, pair thickness {Ltot*1e6:.1f} um\n")
    f.write("T_C    rho_kg_m3  cp_J_kgK  k_across_W_mK  k_along_W_mK  rho_cp_MJ_m3K\n")
    for r in rows:
        f.write(f"{r['T_C']:5.1f}  {r['rho']:9.1f}  {r['cp']:8.1f}  {r['k_across']:13.4f}  {r['k_along']:12.3f}  "
                f"{r['rho']*r['cp']/1e6:13.4f}\n")
    f.write("Registered: the 25 C row. -5 C lies below the 0 C row of the two-cell table; the polynomial fits are\n"
            "evaluated there as written, without a stated range of validity in the parameter set.\n")
print(open(os.path.join(HERE, "properties.txt")).read())
