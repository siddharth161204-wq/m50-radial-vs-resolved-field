#!/usr/bin/env python3
"""Post-hoc analysis (D15), not pre-registered: the 2C, minus 5 C case at the paper's own end of discharge, and where
the heat leaves the cell.

The paper's Fig. 4d (p. 5) ends its 2C, minus 5 C discharge near 1.34 A h (multi-unit) and 1.50 A h (single-unit),
read from the figure; at 10 A that is 482.4 and 540.0 s. The registered DFN run continues to 4.74 A h (1706.7 s). This
script re-solves the registered cases on the registered step grid, records snapshots at those two times, and
records the heat each surface removes:
  21700 and 4680, boundary conditions (a) and (b), heat Chen2020_m5C_2C.
(b) runs to the end of discharge (for the split over the whole discharge); (a) stops after 540 s.
Writes results/posthoc_matched_time.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402
from cell3d import Cell3D  # noqa: E402

HEAT = "Chen2020_m5C_2C"
I_A = 10.0
T_PAPER = {"1.34 A h": 1.34 * 3600 / I_A, "1.50 A h": 1.50 * 3600 / I_A}


def compare(s3, s1):
    u3, u1 = np.array(s3["units"]), np.array(s1["units"])
    off = u1 - u3
    return {"t_s": s3["t"], "dT_cs_3d_K": s3["dT_core_surface"], "dT_cs_1d_K": s1["dT_core_surface"],
            "dT_axial_K": s3["dT_axial"], "axial_over_radial": s3["dT_axial"] / s3["dT_core_surface"],
            "mean_offset_K": float(off.mean()), "min_offset_K": float(off.min()), "max_offset_K": float(off.max()),
            "n_units_over_1K": int((np.abs(off) > 1).sum()), "spread_1d_K": float(u1.max() - u1.min()),
            "spread_3d_K": float(u3.max() - u3.min()),
            "spread_overstatement": float((u1.max() - u1.min()) / (u3.max() - u3.min()) - 1)}


def main():
    q, t_end, _ = R1.load_heat(HEAT)
    out = {"heat": HEAT, "paper_end_times_s": T_PAPER, "cases": {}}
    times = list(T_PAPER.values())
    for cell in ("21700", "4680"):
        m1 = R1.Radial1D(cell)
        r1 = m1.run(q, t_end, -5.0, snap_times=times)
        for bc in ("b", "a"):
            model = Cell3D(cell, bc)
            res, _T = model.run(q, t_end, -5.0, snap_times=times, stop_after=None if bc == "b" else max(times))
            rec = {"stopped_at_s": res["stopped_at_s"], "heat_lost_by_surface_J": res["heat_lost_by_surface_J"],
                   "energy_residual_rel": res["energy_J"]["residual_rel"]}
            lost = res["heat_lost_by_surface_J"]
            tot = sum(lost.values())
            rec["ends_share_of_heat_lost"] = (lost.get("top", 0.0) + lost.get("bottom", 0.0)) / tot if tot else None
            for lab, ts in T_PAPER.items():
                rec[lab] = compare(res["snaps"][ts], r1["snaps"][ts])
            if bc == "b":
                rec["end_of_discharge"] = compare(res["end"], R1.Radial1D(cell).run(q, t_end, -5.0, snap_times=[t_end])["snaps"][t_end])
                ser = np.array(res["series"])
                ok = ser[:, 0] >= 100.0
                ratio = np.maximum(ser[ok, 4], ser[ok, 5]) / ser[ok, 3]
                rec["axial_over_radial_from_100s"] = {"min": float(ratio.min()), "max": float(ratio.max())}
            out["cases"][f"{cell}_{bc}"] = rec
            print(cell, bc, json.dumps({k: v for k, v in rec.items() if k != "heat_lost_by_surface_J"}), flush=True)
    with open(os.path.join(C.RESULTS, "posthoc_matched_time.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
