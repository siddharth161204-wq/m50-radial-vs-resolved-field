#!/usr/bin/env python3
"""Independent check of Stage 4 Part A readings (a) and V1 (b).

Reads only stored files of the repository; imports nothing from it. Pure-Python trapezoid (explicit loop).
Writes check4/out_ab.json and check4/my_readings.json (my own readings, used by check_cd.py).
"""
import csv
import json
import math
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RES = os.path.join(REPO, "results")
OUT = os.path.dirname(os.path.abspath(__file__))

CASES = {  # key -> (cell, bc, condition)
    "21700_b_m5C_2C": ("21700", "b", "m5C_2C"),
    "21700_b_p25C_2C": ("21700", "b", "p25C_2C"),
    "21700_b_p25C_1.25C": ("21700", "b", "p25C_1.25C"),
    "21700_a_m5C_2C": ("21700", "a", "m5C_2C"),
    "4680_b_m5C_2C": ("4680", "b", "m5C_2C"),
}
NUNITS = {"21700": 45, "4680": 111}
TAMB = {"m5C_2C": -5.0, "p25C_2C": 25.0, "p25C_1.25C": 25.0}


def load(p):
    with open(p) as f:
        return json.load(f)


def trap_avg(times, rows, Ta, t_end):
    """Time average of each unit by the trapezoid rule over t = 0 (T = Ta) and the snapshot times, / t_end."""
    n = len(rows[0])
    acc = [0.0] * n
    t_prev, row_prev = 0.0, [Ta] * n
    for t, row in zip(times, rows):
        dt = t - t_prev
        for i in range(n):
            acc[i] += 0.5 * dt * (row_prev[i] + row[i])
        t_prev, row_prev = t, row
    return [a / t_end for a in acc]


def maxabs(a, b):
    assert len(a) == len(b), (len(a), len(b))
    return max(abs(x - y) for x, y in zip(a, b))


def main():
    h1 = load(os.path.join(RES, "stage4_hist_1d.json"))
    h3 = {}
    h3.update(load(os.path.join(RES, "stage4_hist_3d_21700.json")))
    h3.update(load(os.path.join(RES, "stage4_hist_3d_4680.json")))
    ut = load(os.path.join(RES, "stage4_unit_temps.json"))
    r1d = load(os.path.join(RES, "radial1d.json"))["registered"]
    s2 = load(os.path.join(RES, "stage2_correction.json"))["B2"]

    report = {"a_readings": {}, "b_V1": {}, "structure": {}, "stored_V1_block_check": {}}
    mine = {}
    overall_a = 0.0
    for key, (cell, bc, cond) in CASES.items():
        a, b = h1[key], h3[key]
        st = {}
        # ---- structure checks ----
        n = NUNITS[cell]
        st["times_equal_1d_3d"] = a["times"] == b["times"]
        st["t_end_equal"] = (a["t_end"] == b["t_end"])
        st["last_time_is_t_end"] = (a["times"][-1] == a["t_end"])
        st["times_strictly_increasing"] = all(t2 > t1 for t1, t2 in zip(a["times"], a["times"][1:]))
        st["first_time"] = a["times"][0]
        st["n_snapshots"] = len(a["times"])
        st["T_amb_1d"], st["T_amb_3d"] = a["T_amb_C"], b["T_amb_C"]
        st["T_amb_matches_condition"] = (a["T_amb_C"] == TAMB[cond] == b["T_amb_C"])
        st["n_units_all_rows"] = sorted({len(r) for r in a["radial"]} | {len(r) for r in b["resolved"]}
                                        | ({len(r) for r in a["corrected"]} if "corrected" in a else set()))
        st["n_units_expected"] = n
        # archived field file and its series times
        f3 = load(os.path.join(RES, "fields", f"{cell}_{bc}_Chen2020_{cond}.json"))
        st["archive_field_cell_bc_heat"] = [f3["cell"], f3["bc"], f3["heat"], f3["T_amb_C"], f3["refine"], f3["k_theta"], f3["props"]]
        ser_t = [row[0] for row in f3["series"]]
        st["hist_times_equal_archive_series_times"] = (ser_t == a["times"])
        st["archive_t_end_equal"] = (f3["t_end"] == a["t_end"])
        # the rounded last row vs the full-precision end
        st["resolved_lastrow_vs_full_end_maxabs"] = maxabs(b["resolved"][-1], b["resolved_end_full"])
        st["radial_lastrow_vs_full_end_maxabs"] = maxabs(a["radial"][-1], a["radial_end"])
        if "corrected" in a:
            st["corrected_lastrow_vs_full_end_maxabs"] = maxabs(a["corrected"][-1], a["corrected_end"])
            st["beta"] = a["beta"]
        else:
            st["corrected_is_radial_flag"] = a.get("corrected_is_radial")
        # are stored values rounded to 1e-7?
        def max_round_resid(rows):
            m = 0.0
            for r in rows:
                for v in r:
                    m = max(m, abs(v * 1e7 - round(v * 1e7)))
            return m
        st["max_rounding_residual_1e-7_units"] = {"radial": max_round_resid(a["radial"]),
                                                   "resolved": max_round_resid(b["resolved"])}
        # min / max temperatures over the history (to check R(T) grid coverage)
        allv = [v for r in a["radial"] for v in r] + [v for r in b["resolved"] for v in r]
        if "corrected" in a:
            allv += [v for r in a["corrected"] for v in r]
        st["T_min_max_over_history"] = [min(allv), max(allv)]
        report["structure"][key] = st

        # ---- (a) readings ----
        fields = {"radial": a["radial"], "resolved": b["resolved"],
                  "corrected": a["corrected"] if bc == "b" else a["radial"]}
        stored = ut["cases"][key]
        ra = {}
        mine[key] = {"cell": cell, "case": bc, "T_amb_C": a["T_amb_C"], "t_end": a["t_end"]}
        for fld, rows in fields.items():
            tav = trap_avg(a["times"], rows, a["T_amb_C"], a["t_end"])
            end = list(rows[-1])
            mine[key][fld] = {"time_average": tav, "end": end}
            d_tav = maxabs(tav, stored[fld]["time_average"])
            d_end = maxabs(end, stored[fld]["end"])
            ra[fld] = {"time_average_maxabs_diff_K": d_tav, "end_maxabs_diff_K": d_end,
                       "n_units_stored": len(stored[fld]["time_average"])}
            overall_a = max(overall_a, d_tav, d_end)
        # stored metadata
        ra["stored_meta"] = {k: stored[k] for k in ("cell", "case", "heat", "T_amb_C", "t_end", "n_snapshots")}
        ra["stored_meta_ok"] = (stored["cell"] == cell and stored["case"] == bc and stored["heat"] == f"Chen2020_{cond}"
                                and stored["T_amb_C"] == a["T_amb_C"] and stored["t_end"] == a["t_end"]
                                and stored["n_snapshots"] == len(a["times"]))
        if bc == "a":
            ra["stored_corrected_equals_radial"] = (stored["corrected"] == stored["radial"])
        report["a_readings"][key] = ra

        # ---- (b) V1 ----
        v = {}
        end3_arch = f3["end"]["units"]
        end1_arch = r1d[f"Chen2020_{cond}|{cell}"]["end"]["units"]
        v["resolved_end_vs_fields_json_maxabs"] = maxabs(b["resolved_end_full"], end3_arch)
        v["radial_end_vs_radial1d_json_maxabs"] = maxabs(a["radial_end"], end1_arch)
        v["archive_end_t_fields"] = f3["end"]["t"]
        v["archive_end_t_radial1d"] = r1d[f"Chen2020_{cond}|{cell}"]["end"]["t"]
        if bc == "b":
            B = s2[f"{cell}_b_Chen2020_{cond}"]
            endc_arch = B["units_corrected"]
            v["corrected_end_vs_stage2_maxabs"] = maxabs(a["corrected_end"], endc_arch)
            # stage2's own archived resolved and uncorrected units vs the other archives
            v["stage2_units_resolved_vs_fields_maxabs"] = maxabs(B["units_resolved"], end3_arch)
            v["stage2_units_uncorrected_vs_radial1d_maxabs"] = maxabs(B["units_uncorrected"], end1_arch)
            # offsets and spreads, as Stage 2 reports them, from the ARCHIVED end values
            E1, E3, Ec = end1_arch, end3_arch, endc_arch
            n_ = len(E3)
            def stats(Ef):
                offs = [x - y for x, y in zip(Ef, E3)]
                sp_f = max(Ef) - min(Ef)
                sp_3 = max(E3) - min(E3)
                return {"mean_abs_offset_K": sum(abs(o) for o in offs) / n_,
                        "max_abs_offset_K": max(abs(o) for o in offs),
                        "mean_offset_K": sum(offs) / n_,
                        "spread_1d_K": sp_f, "spread_3d_K": sp_3,
                        "spread_overstatement": sp_f / sp_3 - 1}
            mu, mc = stats(E1), stats(Ec)
            cmp_ = {}
            for lab, mm, reg in (("uncorrected", mu, B["uncorrected"]), ("corrected", mc, B["corrected"])):
                cmp_[lab] = {k: {"mine": mm[k], "stage2": reg[k], "diff": mm[k] - reg[k]} for k in mm}
            v["vs_stage2_stored"] = cmp_
            v["max_abs_diff_vs_stage2"] = max(abs(c["diff"]) for lab in cmp_.values() for c in lab.values())
            # Stage 4's V1 block in stage4_unit_temps.json
            sv = ut["V1"][key]
            report["stored_V1_block_check"][key] = {
                "mean_abs_offset_radial": [mu["mean_abs_offset_K"], sv["mean_abs_offset_radial_K"]],
                "max_abs_offset_radial": [mu["max_abs_offset_K"], sv["max_abs_offset_radial_K"]],
                "spread_radial": [mu["spread_1d_K"], sv["spread_radial_K"]],
                "spread_resolved": [mu["spread_3d_K"], sv["spread_resolved_K"]],
                "spread_overstatement_radial": [mu["spread_overstatement"], sv["spread_overstatement_radial"]],
                "mean_abs_offset_corrected": [mc["mean_abs_offset_K"], sv["mean_abs_offset_corrected_K"]],
                "spread_overstatement_corrected": [mc["spread_overstatement"], sv["spread_overstatement_corrected"]],
                "stored_flags": {k: sv[k] for k in sv if k.endswith("diff_K") or k.startswith("matches")},
            }
        else:
            # Stage 1's stored values for case (a) are in results/results_3d.csv (full precision)
            rows = list(csv.DictReader(open(os.path.join(RES, "results_3d.csv"))))
            row = [r for r in rows if r["cell"] == cell and r["bc"] == "a" and r["refine"] == "1.0"
                   and r["props"] == "registered" and r["heat"] == f"Chen2020_{cond}" and r["when"] == "end"]
            assert len(row) == 1, len(row)
            row = row[0]
            E1, E3 = end1_arch, end3_arch
            offs = [x - y for x, y in zip(E1, E3)]
            mine_a = {"mean_offset": sum(offs) / len(offs), "mean_abs_offset": sum(abs(o) for o in offs) / len(offs),
                      "max_abs_offset": max(abs(o) for o in offs), "min_offset": min(offs), "max_offset": max(offs),
                      "spread_3d": max(E3) - min(E3), "spread_1d": max(E1) - min(E1)}
            mine_a["spread_change_rel_stage1_def"] = mine_a["spread_3d"] / mine_a["spread_1d"] - 1
            v["vs_stage1_results_3d_csv"] = {
                "mean_offset": [mine_a["mean_offset"], float(row["units_mean_offset_1d_minus_3d_K"])],
                "max_abs_diff": [mine_a["max_abs_offset"], float(row["units_max_abs_diff_K"])],
                "min_offset": [mine_a["min_offset"], float(row["units_min_offset_K"])],
                "max_offset": [mine_a["max_offset"], float(row["units_max_offset_K"])],
                "spread_3d": [mine_a["spread_3d"], float(row["units_spread_3d_K"])],
                "spread_1d": [mine_a["spread_1d"], float(row["units_spread_1d_K"])],
                "spread_change_rel": [mine_a["spread_change_rel_stage1_def"], float(row["units_spread_change_rel"])],
            }
            v["max_abs_diff_vs_stage1"] = max(abs(p[0] - p[1]) for p in v["vs_stage1_results_3d_csv"].values())
            v["mean_abs_offset_K"] = mine_a["mean_abs_offset"]
            v["spread_overstatement_radial"] = mine_a["spread_1d"] / mine_a["spread_3d"] - 1
            sv = ut["V1"][key]
            report["stored_V1_block_check"][key] = {
                "mean_abs_offset_radial": [mine_a["mean_abs_offset"], sv["mean_abs_offset_radial_K"]],
                "max_abs_offset_radial": [mine_a["max_abs_offset"], sv["max_abs_offset_radial_K"]],
                "spread_radial": [mine_a["spread_1d"], sv["spread_radial_K"]],
                "spread_resolved": [mine_a["spread_3d"], sv["spread_resolved_K"]],
                "spread_overstatement_radial": [v["spread_overstatement_radial"], sv["spread_overstatement_radial"]],
                "stored_flags": {k: sv[k] for k in sv if k.endswith("diff_K") or k.startswith("matches")},
            }
        # the 2C, minus 5 C per-unit CSVs (3 d.p. or 5 d.p.) vs the archive
        if cond == "m5C_2C":
            p = os.path.join(RES, f"units_{cell}_{bc}_2C_minus5C_end.csv")
            if os.path.exists(p):
                rows = list(csv.DictReader(open(p)))
                v["units_csv_T3d_vs_archive_maxabs"] = maxabs([float(r["T_3d_C"]) for r in rows], end3_arch)
                v["units_csv_T1d_vs_archive_maxabs"] = maxabs([float(r["T_1d_C"]) for r in rows], end1_arch)
        report["b_V1"][key] = v

    # radial field in case (a) and case (b) at 2C, minus 5 C must be identical (no end condition in the 1-D model)
    report["structure"]["radial_a_equals_radial_b_21700_m5C_2C"] = (h1["21700_a_m5C_2C"]["radial"] == h1["21700_b_m5C_2C"]["radial"])
    report["max_discrepancy_a_K"] = overall_a
    json.dump(report, open(os.path.join(OUT, "out_ab.json"), "w"), indent=1)
    json.dump(mine, open(os.path.join(OUT, "my_readings.json"), "w"))
    # concise print
    print("== (a) readings: max |mine - stored| over all cases/fields/units/readings:", overall_a)
    for k, v in report["a_readings"].items():
        print(k, {f: (v[f]["time_average_maxabs_diff_K"], v[f]["end_maxabs_diff_K"]) for f in ("radial", "resolved", "corrected")},
              "meta_ok", v["stored_meta_ok"], ("corr==rad " + str(v.get("stored_corrected_equals_radial"))) if "stored_corrected_equals_radial" in v else "")
    print("== structure")
    for k, v in report["structure"].items():
        print(k, v)
    print("== (b) V1")
    for k, v in report["b_V1"].items():
        print(k, {kk: vv for kk, vv in v.items() if not isinstance(vv, dict)})
    print("== stored V1 block vs mine")
    for k, v in report["stored_V1_block_check"].items():
        print(k, {kk: (vv if kk == "stored_flags" else (vv[0] - vv[1])) for kk, vv in v.items()})


if __name__ == "__main__":
    main()
