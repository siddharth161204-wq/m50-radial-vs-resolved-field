#!/usr/bin/env python3
"""Independent check (g): stage4_paper_numbers.json (C3 at the registered choices, removed_by_correction, the unit
temperature summary), stage4_checks_v3.json, and claims of D22 to D24 that can be tested from stored files.
Self-contained (no repository imports). Writes check4/out_g.json."""
import bisect
import csv
import json
import math
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RES = os.path.join(REPO, "results")
OUT = os.path.dirname(os.path.abspath(__file__))


def rt(set_, soc):
    rows = sorted((float(r["T_C"]), float(r["R_ohm"])) for r in csv.DictReader(open(os.path.join(RES, "stage4_RT.csv")))
                  if r["set"] == set_ and float(r["soc"]) == soc)
    return [t for t, _ in rows], [math.log(R) for _, R in rows]


def R_of(T, g):
    Ts, l = g
    j = min(bisect.bisect_right(Ts, T) - 1, len(Ts) - 2)
    f = (T - Ts[j]) / (Ts[j + 1] - Ts[j])
    return math.exp(l[j] + f * (l[j + 1] - l[j]))


def metr(Ts, w, g):
    Rs = [R_of(T, g) for T in Ts]
    nrm = sum(wi / Ri for wi, Ri in zip(w, Rs))
    sh = [1 / Ri / nrm for Ri in Rs]
    return {"R_mean": sum(wi * Ri for wi, Ri in zip(w, Rs)), "spread": max(sh) - min(sh), "inner": sh[0], "outer": sh[-1],
            "shares": sh}


def main():
    rd = json.load(open(os.path.join(OUT, "my_readings.json")))
    pn = json.load(open(os.path.join(RES, "stage4_paper_numbers.json")))
    g = rt("ORegan2022", 1.0)
    out = {"C3": {}, "temp_summary": {}, "max_abs_diff_C3": 0.0, "max_abs_diff_temp_summary": 0.0}
    for case, rec in rd.items():
        n = len(rec["resolved"]["time_average"])
        w = [(2 * i - 1) / n ** 2 for i in range(1, n + 1)]
        m = {f: metr(rec[f]["time_average"], w, g) for f in ("radial", "corrected", "resolved")}
        ref = m["resolved"]
        e = {}
        for f in ("radial", "corrected"):
            e[f] = {"R_mean_rel": m[f]["R_mean"] / ref["R_mean"] - 1, "spread_rel": m[f]["spread"] / ref["spread"] - 1,
                    "inner_pp": 100 * (m[f]["inner"] - ref["inner"]), "outer_pp": 100 * (m[f]["outer"] - ref["outer"])}
        e["removed_by_correction"] = {k: (1 - abs(e["corrected"][k]) / abs(e["radial"][k])) if e["radial"][k] != 0 else None
                                      for k in e["radial"]}
        st = pn["C3_registered"][case]
        diffs = {}
        for blk in ("radial", "corrected", "removed_by_correction"):
            for k in ("R_mean_rel", "spread_rel", "inner_pp", "outer_pp"):
                a, b = e[blk][k], st[blk][k]
                diffs[f"{blk}.{k}"] = (a - b) if (a is not None and b is not None) else None
                if diffs[f"{blk}.{k}"] is not None:
                    out["max_abs_diff_C3"] = max(out["max_abs_diff_C3"], abs(diffs[f"{blk}.{k}"]))
        out["C3"][case] = {"mine": e, "diffs": diffs}
        # temperature summary
        ts = {}
        for f in ("radial", "corrected", "resolved"):
            for r in ("time_average", "end"):
                v = rec[f][r]
                mean = sum(wi * x for wi, x in zip(w, v))
                sp = max(v) - min(v)
                s = pn["unit_temperature_summary"][case][f][r]
                ts[f"{f}.{r}"] = {"mean_mine": mean, "mean_stored": s["mean_area_weighted_C"], "spread_mine": sp,
                                  "spread_stored": s["spread_K"]}
                out["max_abs_diff_temp_summary"] = max(out["max_abs_diff_temp_summary"], abs(mean - s["mean_area_weighted_C"]),
                                                       abs(sp - s["spread_K"]))
        # time-averaged temperature spread overstatement vs the share-spread error (D25's first-order argument)
        ts["temp_spread_overstatement_time_avg"] = {f: (max(rec[f]["time_average"]) - min(rec[f]["time_average"])) /
                                                    (max(rec["resolved"]["time_average"]) - min(rec["resolved"]["time_average"])) - 1
                                                    for f in ("radial", "corrected")}
        ts["share_spread_error_registered"] = {f: e[f]["spread_rel"] for f in ("radial", "corrected")}
        # is unit 1 the hottest and unit N the coldest in every field and reading (inner/outer = hottest/coldest)?
        ts["unit1_hottest_unitN_coldest"] = {f"{f}.{r}": (rec[f][r][0] == max(rec[f][r]) and rec[f][r][-1] == min(rec[f][r]))
                                             for f in ("radial", "corrected", "resolved") for r in ("time_average", "end")}
        ts["argmax_argmin_units_1based"] = {f"{f}.{r}": [rec[f][r].index(max(rec[f][r])) + 1, rec[f][r].index(min(rec[f][r])) + 1]
                                            for f in ("radial", "corrected", "resolved") for r in ("time_average", "end")}
        out["temp_summary"][case] = ts
    # V3 file vs mine
    v3 = json.load(open(os.path.join(RES, "stage4_checks_v3.json")))
    rec = rd["21700_b_m5C_2C"]
    w = [(2 * i - 1) / 45 ** 2 for i in range(1, 46)]
    mm = {f: metr(rec[f]["time_average"], w, g) for f in ("radial", "corrected", "resolved")}
    out["V3_file_vs_mine"] = {f: {"R_mean_mOhm": mm[f]["R_mean"] * 1e3 - v3["hand"][f]["R_mean_mOhm"],
                                  "spread": mm[f]["spread"] - v3["hand"][f]["spread"],
                                  "inner": mm[f]["inner"] - v3["hand"][f]["inner"],
                                  "outer": mm[f]["outer"] - v3["hand"][f]["outer"]} for f in mm}
    # D22: the time of the largest core-to-surface difference is the end in these cases
    ends = {}
    for case, rec in rd.items():
        cell, bc = rec["cell"], rec["case"]
        cond = case.split("_", 2)[2]
        f3 = json.load(open(os.path.join(RES, "fields", f"{cell}_{bc}_Chen2020_{cond}.json")))
        ends[case] = {"max_dT_t": f3["max_dT"]["t"], "end_t": f3["end"]["t"], "same": f3["max_dT"]["t"] == f3["end"]["t"],
                      "max_dT_units_equal_end_units": f3["max_dT"]["units"] == f3["end"]["units"]}
    out["D22_maxdT_is_end"] = ends
    # D24: hottest/coldest shares listed as per-case outputs; are they written anywhere?
    found = {}
    for fn in os.listdir(RES):
        if fn.startswith("stage4_") and (fn.endswith(".json") or fn.endswith(".csv")):
            with open(os.path.join(RES, fn)) as f:
                txt = f.read()
            found[fn] = ("hottest" in txt) or ("coldest" in txt)
    out["D24_hottest_coldest_written_in"] = found
    json.dump(out, open(os.path.join(OUT, "out_g.json"), "w"), indent=1)
    print("max |C3 diff|", out["max_abs_diff_C3"], " max |temp summary diff|", out["max_abs_diff_temp_summary"])
    for c, v in out["temp_summary"].items():
        print(c, "Tspread overst (time avg)", {k: round(x, 5) for k, x in v["temp_spread_overstatement_time_avg"].items()},
              "share spread err", {k: round(x, 5) for k, x in v["share_spread_error_registered"].items()})
        print("   unit1 hottest & unitN coldest:", v["unit1_hottest_unitN_coldest"])
        print("   argmax/argmin:", v["argmax_argmin_units_1based"])
    print("V3 file vs mine", out["V3_file_vs_mine"])
    print("D22 max_dT is end", out["D22_maxdT_is_end"])
    print("hottest/coldest written in", out["D24_hottest_coldest_written_in"])


if __name__ == "__main__":
    main()
