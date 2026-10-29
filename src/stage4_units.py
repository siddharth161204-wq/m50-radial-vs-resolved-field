#!/usr/bin/env python3
"""Stage 4, Part A (D22): every unit's temperature over the discharge in the five cases, under the radial, resolved
and end-corrected fields, from Stage 1 and 2 code imported unchanged.

The archive holds the unit temperatures at the end of discharge only, so the three models are run again with a
snapshot of every unit at the archived series times (every 10 s and the end). V1: the end-of-discharge units equal
the archived ones (exactly for the direct solvers; the 4680's resolved run uses Stage 1's conjugate-gradient solver,
relative residual 1e-12).

python3 src/stage4_units.py --fields 1d          -> results/stage4_hist_1d.json   (radial and end-corrected, seconds)
python3 src/stage4_units.py --fields 3d --cell 21700  -> results/stage4_hist_3d_21700.json
python3 src/stage4_units.py --fields 3d --cell 4680   -> results/stage4_hist_3d_4680.json
python3 src/stage4_units.py --collect             -> results/stage4_unit_temps.json (readings and V1)
Histories are stored rounded to 1e-7 K (as Stage 1 stores the radial snapshots); the readings are computed from the
stored values."""
import argparse
import csv
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402

# (key, cell, case, heat): D22
CASES = [("21700_b_m5C_2C", "21700", "b", "Chen2020_m5C_2C"),
         ("21700_b_p25C_2C", "21700", "b", "Chen2020_p25C_2C"),
         ("21700_b_p25C_1.25C", "21700", "b", "Chen2020_p25C_1.25C"),
         ("21700_a_m5C_2C", "21700", "a", "Chen2020_m5C_2C"),
         ("4680_b_m5C_2C", "4680", "b", "Chen2020_m5C_2C")]
R = C.RESULTS
rnd = lambda a: [round(float(v), 7) for v in a]


def archived(cell, bc, heat):
    f3 = json.load(open(os.path.join(R, "fields", f"{cell}_{bc}_{heat}.json")))
    times = [row[0] for row in f3["series"]]
    end3 = f3["end"]["units"]
    end1 = json.load(open(os.path.join(R, "radial1d.json")))["registered"][f"{heat}|{cell}"]["end"]["units"]
    endc = None
    if bc == "b":
        endc = json.load(open(os.path.join(R, "stage2_correction.json")))["B2"][f"{cell}_b_{heat}"]["units_corrected"]
    return times, f3["t_end"], end3, end1, endc


def history(snaps, times, end_units):
    """Units at the snapshot times; the last series time is the end of discharge."""
    rows = []
    for t in times:
        if t in snaps:
            rows.append(rnd(snaps[t]["units"]))
        else:
            raise KeyError(f"no snapshot at {t}")
    return rows


def run_1d():
    from stage2_correction import Corrected
    out = {}
    for key, cell, bc, heat in CASES:
        times, t_end, _, end1, endc = archived(cell, bc, heat)
        q, t_end_h, _ = R1.load_heat(heat)
        Ta = R1.amb_of(heat)
        r0 = R1.Radial1D(cell).run(q, t_end_h, Ta, snap_times=times)
        rec = {"times": times, "t_end": t_end_h, "T_amb_C": Ta,
               "radial": history(r0["snaps"], times, r0["end"]["units"]), "radial_end": r0["end"]["units"]}
        if bc == "b":
            rc = Corrected(cell).run(q, t_end_h, Ta, snap_times=times)
            rec["corrected"] = history(rc["snaps"], times, rc["end"]["units"])
            rec["corrected_end"] = rc["end"]["units"]
            rec["beta"] = rc["beta"]
        else:
            rec["corrected_is_radial"] = True       # beta = 0 with the ends insulated (D18, D22)
        out[key] = rec
        print(key, "1d done", flush=True)
    json.dump(out, open(os.path.join(R, "stage4_hist_1d.json"), "w"))


def run_3d(only_cell):
    from cell3d import Cell3D
    props = C.roll_properties()["registered"]
    out = {}
    for key, cell, bc, heat in CASES:
        if cell != only_cell:
            continue
        times, t_end, end3, _, _ = archived(cell, bc, heat)
        q, t_end_h, _ = R1.load_heat(heat)
        Ta = R1.amb_of(heat)
        t0 = time.time()
        model = Cell3D(cell, bc, props=props, refine=1.0, k_theta="across")
        res, _T = model.run(q, t_end_h, Ta, snap_times=times)
        out[key] = {"times": times, "t_end": t_end_h, "T_amb_C": Ta, "solver": res["solver"],
                    "resolved": history(res["snaps"], times, res["end"]["units"]),
                    "resolved_end_full": res["end"]["units"], "wall_s": time.time() - t0}
        d = float(np.max(np.abs(np.array(res["end"]["units"]) - np.array(end3))))
        print(key, f"3d done in {time.time() - t0:.0f} s, end units max |diff| vs archive {d:.3e}", flush=True)
        json.dump(out, open(os.path.join(R, f"stage4_hist_3d_{only_cell}.json"), "w"))


def tavg(times, rows, Ta):
    t = np.concatenate([[0.0], np.asarray(times, float)])
    U = np.vstack([np.full(len(rows[0]), Ta), np.asarray(rows, float)])
    return np.trapezoid(U, t, axis=0) / t[-1]


def collect():
    h1 = json.load(open(os.path.join(R, "stage4_hist_1d.json")))
    h3 = {**json.load(open(os.path.join(R, "stage4_hist_3d_21700.json"))),
          **json.load(open(os.path.join(R, "stage4_hist_3d_4680.json")))}
    s2 = json.load(open(os.path.join(R, "stage2_correction.json")))["B2"]
    out, v1 = {}, {}
    for key, cell, bc, heat in CASES:
        times, t_end, end3, end1, endc = archived(cell, bc, heat)
        a, b = h1[key], h3[key]
        Ta = a["T_amb_C"]
        rad, res = a["radial"], b["resolved"]
        cor = a["corrected"] if bc == "b" else rad
        fields = {"radial": rad, "resolved": res, "corrected": cor}
        rec = {"cell": cell, "case": bc, "heat": heat, "T_amb_C": Ta, "t_end": a["t_end"], "n_snapshots": len(times)}
        for f, rows in fields.items():
            rec[f] = {"time_average": tavg(times, rows, Ta).tolist(), "end": list(rows[-1])}
        # V1: end units against the archive, and the registered offsets and spreads (unweighted, as Stages 1 and 2)
        e3 = np.array(b["resolved_end_full"])
        chk = {"resolved_end_max_abs_diff_K": float(np.max(np.abs(e3 - np.array(end3)))),
               "resolved_solver": b["solver"],
               "radial_end_max_abs_diff_K": float(np.max(np.abs(np.array(a["radial_end"]) - np.array(end1))))}
        if bc == "b":
            chk["corrected_end_max_abs_diff_K"] = float(np.max(np.abs(np.array(a["corrected_end"]) - np.array(endc))))
        E1, E3 = np.array(end1), np.array(end3)
        chk["mean_abs_offset_radial_K"] = float(np.mean(np.abs(E1 - E3)))
        chk["max_abs_offset_radial_K"] = float(np.max(np.abs(E1 - E3)))
        chk["spread_radial_K"] = float(E1.max() - E1.min())
        chk["spread_resolved_K"] = float(E3.max() - E3.min())
        chk["spread_overstatement_radial"] = chk["spread_radial_K"] / chk["spread_resolved_K"] - 1
        if bc == "b":
            Ec = np.array(endc)
            chk["mean_abs_offset_corrected_K"] = float(np.mean(np.abs(Ec - E3)))
            chk["spread_overstatement_corrected"] = float((Ec.max() - Ec.min()) / chk["spread_resolved_K"] - 1)
            reg = s2[f"{cell}_b_{heat}"]
            chk["registered_stage2"] = {"mean_abs_offset_uncorrected_K": reg["uncorrected"]["mean_abs_offset_K"],
                                        "spread_overstatement_uncorrected": reg["uncorrected"]["spread_overstatement"],
                                        "mean_abs_offset_corrected_K": reg["corrected"]["mean_abs_offset_K"],
                                        "spread_overstatement_corrected": reg["corrected"]["spread_overstatement"]}
            pairs = (("mean_abs_offset_radial_K", "mean_abs_offset_uncorrected_K"),
                     ("spread_overstatement_radial", "spread_overstatement_uncorrected"),
                     ("mean_abs_offset_corrected_K", "mean_abs_offset_corrected_K"),
                     ("spread_overstatement_corrected", "spread_overstatement_corrected"))
            chk["matches_stage2"] = all(chk[k1] == chk["registered_stage2"][k2] for k1, k2 in pairs)
        else:
            # Stage 1's table for case (a) at 2C and minus 5 C (README): unit offsets 0.004 to 0.290 K, resolved spread 3.886 K
            chk["registered_stage1"] = {"max_abs_offset_K": 0.290, "spread_resolved_K": 3.886}
            chk["matches_stage1"] = (round(chk["max_abs_offset_radial_K"], 3) == 0.290 and round(chk["spread_resolved_K"], 3) == 3.886)
        v1[key] = chk
        out[key] = rec
    json.dump({"cases": out, "V1": v1}, open(os.path.join(R, "stage4_unit_temps.json"), "w"), indent=1)
    print(json.dumps(v1, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields", choices=["1d", "3d"])
    ap.add_argument("--cell")
    ap.add_argument("--collect", action="store_true")
    a = ap.parse_args()
    if a.collect:
        collect()
    elif a.fields == "1d":
        run_1d()
    else:
        run_3d(a.cell)
