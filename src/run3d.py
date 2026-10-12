#!/usr/bin/env python3
"""Run the resolved cell for a set of boundary conditions and heat inputs (D8 to D11).

Each run writes results/fields/<cell>_<bc>[_refine2][_<props>]_<heat>.json with the snapshots at the end of discharge
and at the time of the largest mid-height core-to-surface difference, a series every 10 s, the energy account and
the timings. A run whose file exists is skipped, so the sweep can be resumed.

Usage examples:
  python3 src/run3d.py --cell 21700 --bcs a_eq,a,b,c,d --heats registered
  python3 src/run3d.py --cell 4680 --bcs b,a --heats Chen2020_m5C_2C
  python3 src/run3d.py --cell 21700 --bcs a,b --heats Chen2020_m5C_2C --refine 2
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402
from cell3d import Cell3D  # noqa: E402

FIELDS = os.path.join(C.RESULTS, "fields")


def heat_list(spec):
    if spec == "registered":
        order = ["Chen2020_m5C_2C", "Chen2020_p25C_2C", "Chen2020_m5C_1.25C", "Chen2020_m5C_3C",
                 "Chen2020_p25C_1.25C", "Chen2020_p25C_3C"]
        return order
    return spec.split(",")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    ap.add_argument("--bcs", required=True)
    ap.add_argument("--heats", default="registered")
    ap.add_argument("--refine", type=float, default=1.0)
    ap.add_argument("--props", default="registered", choices=["registered", "cold"])
    ap.add_argument("--k-theta", default="across", choices=["across", "along"],
                    help="circumferential conductivity of the roll (D13): the across-layer value (default) or the "
                         "along-layer value of the two-cell study")
    a = ap.parse_args()
    os.makedirs(FIELDS, exist_ok=True)
    allp = C.roll_properties()
    props = allp["registered"] if a.props == "registered" else next(r for r in allp["table"] if r["T_C"] == -5.0)
    for bc in a.bcs.split(","):
        model = None
        for heat in heat_list(a.heats):
            tag = (f"{a.cell}_{bc}" + ("_refine2" if a.refine != 1.0 else "") + ("_cold" if a.props == "cold" else "")
                   + ("_ktheta-along" if a.k_theta == "along" else ""))
            path = os.path.join(FIELDS, f"{tag}_{heat}.json")
            if os.path.exists(path):
                print("skip", path, flush=True)
                continue
            if model is None:
                model = Cell3D(a.cell, bc, props=props, refine=a.refine, k_theta=a.k_theta)
            q_of_t, t_end, _ = R1.load_heat(heat)
            T_amb = R1.amb_of(heat)
            t0 = time.time()
            res, _T = model.run(q_of_t, t_end, T_amb)
            res.update({"heat": heat, "T_amb_C": T_amb, "props": a.props, "refine": a.refine, "k_theta": a.k_theta,
                        "props_values": props, "wall_s": time.time() - t0})
            with open(path, "w") as f:
                json.dump(res, f)
            e = res["end"]
            print(f"{tag} {heat}: end dT_cs {e['dT_core_surface']:.4f} K, axial {e['dT_axial']:.4f} K, spread "
                  f"{e['unit_spread']:.4f} K, energy residual {res['energy_J']['residual_rel']:.2e}, "
                  f"{res['wall_s']:.0f} s", flush=True)


if __name__ == "__main__":
    main()
