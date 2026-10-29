#!/usr/bin/env python3
"""Independent check of Stage 4 Part C (c) and the scorecard (d).

Inputs: results/stage4_RT.csv (the R(T) table) and MY readings (check4/my_readings.json, from check_ab.py, computed
from the history files). Nothing is imported from the repository. Interpolation of ln R is my own bisection code.
Compares every row of results/stage4_errors.csv and every share column of results/stage4_units.csv, then scores
P1 to P7 by the written rules at the registered choices and at each bracket, and compares with stage4_scorecard.json.
Writes check4/out_cd.json and check4/my_scorecard.json."""
import bisect
import csv
import json
import math
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RES = os.path.join(REPO, "results")
OUT = os.path.dirname(os.path.abspath(__file__))
RCELL = {"21700": 21.1e-3 / 2, "4680": 46.0e-3 / 2}
SETS = ("ORegan2022", "Chen2020")
SOCS = (1.0, 0.5)
READINGS = ("time_average", "end")
WEIGHTINGS = ("area", "unweighted")
FIELDS = ("radial", "corrected", "resolved")
MAIN, P4CASE, CASE4680, CASEA = "21700_b_m5C_2C", "21700_b_p25C_2C", "4680_b_m5C_2C", "21700_a_m5C_2C"


def rt_table():
    tab = {}
    with open(os.path.join(RES, "stage4_RT.csv")) as f:
        for r in csv.DictReader(f):
            tab.setdefault((r["set"], float(r["soc"])), []).append((float(r["T_C"]), float(r["R_ohm"])))
    out = {}
    for k, rows in tab.items():
        rows.sort()
        Ts = [t for t, _ in rows]
        assert len(Ts) == len(set(Ts)) == 91, (k, len(Ts))
        out[k] = (Ts, [math.log(R) for _, R in rows])
    return out


def R_of(T, grid):
    Ts, lnR = grid
    if not (Ts[0] <= T <= Ts[-1]):
        raise ValueError(f"T = {T} outside the grid")
    j = bisect.bisect_right(Ts, T) - 1
    if j == len(Ts) - 1:
        j -= 1
    f = (T - Ts[j]) / (Ts[j + 1] - Ts[j])
    return math.exp(lnR[j] + f * (lnR[j + 1] - lnR[j]))


def area_weights(n, R=None):
    """w_i = (r_(i+1)^2 - r_i^2) / R^2 on equal-thickness edges; algebraically (2i - 1) / n^2."""
    if R is None:
        return [(2 * i - 1) / n ** 2 for i in range(1, n + 1)]
    e = [R * i / n for i in range(n + 1)]
    return [(e[i + 1] ** 2 - e[i] ** 2) / R ** 2 for i in range(n)]


def metrics(Ts, w, grid):
    Rs = [R_of(T, grid) for T in Ts]
    norm = sum(wi / Ri for wi, Ri in zip(w, Rs))
    sh = [(1.0 / Ri) / norm for Ri in Rs]
    return {"R": Rs, "share": sh, "R_mean": sum(wi * Ri for wi, Ri in zip(w, Rs)), "spread": max(sh) - min(sh),
            "sd": math.sqrt(sum(wi * (s - 1.0) ** 2 for wi, s in zip(w, sh))), "inner": sh[0], "outer": sh[-1],
            "wsum_share": sum(wi * s for wi, s in zip(w, sh))}


def g6(x):
    return f"{x:.6g}"


def main():
    rd = json.load(open(os.path.join(OUT, "my_readings.json")))
    tab = rt_table()
    M = {}
    wcheck = {}
    for case, rec in rd.items():
        cell = rec["cell"]
        n = len(rec["resolved"]["time_average"])
        wa = area_weights(n)
        wa_edges = area_weights(n, RCELL[cell])
        wcheck[case] = {"n": n, "sum_w": sum(wa), "max_diff_formula_vs_edges": max(abs(x - y) for x, y in zip(wa, wa_edges)),
                        "outer_over_inner": wa[-1] / wa[0]}
        wu = [1.0 / n] * n
        for fld in FIELDS:
            for reading in READINGS:
                Ts = rec[fld][reading]
                for s in SETS:
                    for soc in SOCS:
                        M[(case, fld, s, soc, reading, "area")] = metrics(Ts, wa, tab[(s, soc)])
                        M[(case, fld, s, soc, reading, "unweighted")] = metrics(Ts, wu, tab[(s, soc)])
    E = {}
    for (case, fld, s, soc, reading, wt), m in M.items():
        if fld == "resolved":
            continue
        ref = M[(case, "resolved", s, soc, reading, wt)]
        E[(case, fld, s, soc, reading, wt)] = {
            "R_mean_mOhm": 1e3 * m["R_mean"], "R_mean_resolved_mOhm": 1e3 * ref["R_mean"],
            "R_mean_rel_error": (m["R_mean"] - ref["R_mean"]) / ref["R_mean"],
            "share_spread": m["spread"], "share_spread_resolved": ref["spread"],
            "share_spread_rel_error": (m["spread"] - ref["spread"]) / ref["spread"],
            "share_sd_rel_error": (m["sd"] - ref["sd"]) / ref["sd"],
            "inner_share": m["inner"], "inner_share_resolved": ref["inner"], "inner_share_error_pp": 100.0 * (m["inner"] - ref["inner"]),
            "outer_share": m["outer"], "outer_share_resolved": ref["outer"], "outer_share_error_pp": 100.0 * (m["outer"] - ref["outer"])}

    # ---- compare stage4_errors.csv ----
    cols = ["R_mean_mOhm", "R_mean_resolved_mOhm", "R_mean_rel_error", "share_spread", "share_spread_resolved",
            "share_spread_rel_error", "share_sd_rel_error", "inner_share", "inner_share_resolved", "inner_share_error_pp",
            "outer_share", "outer_share_resolved", "outer_share_error_pp"]
    stored_rows = list(csv.DictReader(open(os.path.join(RES, "stage4_errors.csv"))))
    seen = set()
    err_cmp = {"n_rows": len(stored_rows), "string_mismatches": [], "max_abs_diff": {c: 0.0 for c in cols},
               "max_rel_diff": {c: 0.0 for c in cols}}
    for r in stored_rows:
        key = (r["case"], r["field"], r["set"], float(r["soc"]), r["reading"], r["weighting"])
        assert key not in seen, key
        seen.add(key)
        e = E[key]
        for c in cols:
            sv = float(r[c])
            d = abs(e[c] - sv)
            err_cmp["max_abs_diff"][c] = max(err_cmp["max_abs_diff"][c], d)
            if sv != 0:
                err_cmp["max_rel_diff"][c] = max(err_cmp["max_rel_diff"][c], d / abs(sv))
            if g6(e[c]) != r[c]:
                err_cmp["string_mismatches"].append({"row": list(map(str, key)), "col": c, "stored": r[c], "mine": repr(e[c])})
    err_cmp["missing_rows"] = [list(map(str, k)) for k in E if k not in seen]
    err_cmp["n_expected_rows"] = len(E)

    # ---- compare stage4_units.csv ----
    ucols = ["T_C", "R_mOhm", "share_area_weighted", "share_unweighted", "area_weight", "r_mid_mm"]
    u_cmp = {"n_rows": 0, "max_abs_diff": {c: 0.0 for c in ucols}, "string_mismatches": {c: 0 for c in ucols},
             "examples": []}
    useen = set()
    with open(os.path.join(RES, "stage4_units.csv")) as f:
        for r in csv.DictReader(f):
            u_cmp["n_rows"] += 1
            case, fld, s, soc, reading, i = r["case"], r["field"], r["set"], float(r["soc"]), r["reading"], int(r["unit"]) - 1
            key = (case, fld, s, soc, reading, i)
            assert key not in useen
            useen.add(key)
            rec = rd[case]
            n = len(rec["resolved"]["time_average"])
            Rc = RCELL[rec["cell"]]
            ma, mu = M[(case, fld, s, soc, reading, "area")], M[(case, fld, s, soc, reading, "unweighted")]
            mine = {"T_C": rec[fld][reading][i], "R_mOhm": 1e3 * ma["R"][i], "share_area_weighted": ma["share"][i],
                    "share_unweighted": mu["share"][i], "area_weight": (2 * (i + 1) - 1) / n ** 2,
                    "r_mid_mm": 1e3 * Rc * (i + 0.5) / n}
            fmt = {"T_C": "{:.6f}", "R_mOhm": "{:.6f}", "share_area_weighted": "{:.6f}", "share_unweighted": "{:.6f}",
                   "area_weight": "{:.6e}", "r_mid_mm": "{:.4f}"}
            for c in ucols:
                d = abs(mine[c] - float(r[c]))
                u_cmp["max_abs_diff"][c] = max(u_cmp["max_abs_diff"][c], d)
                if fmt[c].format(mine[c]) != r[c]:
                    u_cmp["string_mismatches"][c] += 1
                    if len(u_cmp["examples"]) < 20:
                        u_cmp["examples"].append({"key": list(map(str, key)), "col": c, "stored": r[c], "mine": repr(mine[c])})
    u_cmp["n_expected_rows"] = sum(len(rd[c]["resolved"]["time_average"]) for c in rd) * len(FIELDS) * len(READINGS) * len(SETS) * len(SOCS)

    # ---- scorecard ----
    def q(case, fld, s, soc, reading, wt, col):
        return E[(case, fld, s, soc, reading, wt)][col]

    def score(s="ORegan2022", soc=1.0, reading="time_average", wt="area", with_p6=True):
        sc = {}
        p1 = q(MAIN, "radial", s, soc, reading, wt, "share_spread_rel_error")
        p2 = q(MAIN, "corrected", s, soc, reading, wt, "share_spread_rel_error")
        p3 = q(MAIN, "radial", s, soc, reading, wt, "R_mean_rel_error")
        p4 = q(P4CASE, "radial", s, soc, reading, wt, "R_mean_rel_error")
        p5 = q(CASE4680, "radial", s, soc, reading, wt, "share_spread_rel_error")
        sc["P1"] = {"value": p1, "held": p1 >= 0.30}
        sc["P2"] = {"value": p2, "held": abs(p2) < 0.08}
        sc["P3"] = {"value": p3, "held": p3 < -0.04}
        sc["P4"] = {"value": p4, "held": abs(p4) < 0.03}
        sc["P5"] = {"value": p5, "main": p1, "ratio": p5 / p1, "held": p5 >= 3.0 * p1}
        if with_p6:
            quant = {"P1": ("radial", MAIN, "share_spread_rel_error"), "P2": ("corrected", MAIN, "share_spread_rel_error"),
                     "P3": ("radial", MAIN, "R_mean_rel_error"), "P4": ("radial", P4CASE, "R_mean_rel_error"),
                     "P5": ("radial", CASE4680, "share_spread_rel_error")}
            each = {}
            for k, (fld, case, col) in quant.items():
                o = q(case, fld, "ORegan2022", soc, reading, wt, col)
                c = q(case, fld, "Chen2020", soc, reading, wt, col)
                each[k] = {"ORegan2022": o, "Chen2020": c, "ratio": c / o, "held": abs(c) < 0.5 * abs(o)}
            sc["P6"] = {"quantities": each, "held": all(v["held"] for v in each.values())}
        p7 = {}
        for fld in ("radial", "corrected"):
            p7[fld] = {"R_mean_rel": q(CASEA, fld, s, soc, reading, wt, "R_mean_rel_error"),
                       "spread_rel": q(CASEA, fld, s, soc, reading, wt, "share_spread_rel_error"),
                       "inner_pp": q(CASEA, fld, s, soc, reading, wt, "inner_share_error_pp"),
                       "outer_pp": q(CASEA, fld, s, soc, reading, wt, "outer_share_error_pp")}
            p7[fld]["held"] = (abs(p7[fld]["R_mean_rel"]) < 0.01 and abs(p7[fld]["spread_rel"]) < 0.01
                               and abs(p7[fld]["inner_pp"]) < 1.0 and abs(p7[fld]["outer_pp"]) < 1.0)
        p7["held"] = p7["radial"]["held"] and p7["corrected"]["held"]
        p7["radial_equals_corrected"] = all(p7["radial"][k] == p7["corrected"][k] for k in ("R_mean_rel", "spread_rel", "inner_pp", "outer_pp"))
        sc["P7"] = p7
        return sc

    mysc = {"registered": score(), "brackets": {"Chen2020": score(s="Chen2020", with_p6=False), "soc_50": score(soc=0.5),
                                               "end_of_discharge": score(reading="end"), "unweighted": score(wt="unweighted")}}
    mysc["verdicts"] = {p: v["held"] for p, v in mysc["registered"].items()}
    json.dump(mysc, open(os.path.join(OUT, "my_scorecard.json"), "w"), indent=1)

    # compare with stored scorecard
    st = json.load(open(os.path.join(RES, "stage4_scorecard.json")))
    sc_cmp = {"verdicts_stored": st["verdicts"], "verdicts_mine": mysc["verdicts"],
              "verdicts_agree": st["verdicts"] == mysc["verdicts"], "per_bracket": {}, "max_abs_value_diff": 0.0}
    vmap = {"P1": "radial_spread_rel", "P2": "corrected_spread_rel", "P3": "radial_R_mean_rel", "P4": "radial_R_mean_rel_2C_25C",
            "P5": "radial_spread_rel_4680"}
    def cmp_block(mine, stored):
        res = {"held_agree": {}, "value_diffs": {}}
        for p in stored:
            res["held_agree"][p] = (stored[p]["held"] == mine[p]["held"])
            if p in vmap:
                res["value_diffs"][p] = mine[p]["value"] - stored[p][vmap[p]]
                if p == "P5":
                    res["value_diffs"]["P5_ratio"] = mine[p]["ratio"] - stored[p]["ratio"]
            elif p == "P6":
                for k, v in stored[p]["quantities"].items():
                    for kk in ("ORegan2022", "Chen2020", "ratio"):
                        res["value_diffs"][f"P6_{k}_{kk}"] = mine[p]["quantities"][k][kk] - v[kk]
                    res["held_agree"][f"P6_{k}"] = (mine[p]["quantities"][k]["held"] == v["held"])
            elif p == "P7":
                for kk in ("R_mean_rel", "spread_rel", "inner_pp", "outer_pp"):
                    res["value_diffs"][f"P7_{kk}"] = mine[p]["radial"][kk] - stored[p][kk]
        res["missing_in_stored"] = [p for p in mine if p not in stored]
        return res
    sc_cmp["per_bracket"]["registered"] = cmp_block(mysc["registered"], st["registered"])
    for b in st["brackets"]:
        sc_cmp["per_bracket"][b] = cmp_block(mysc["brackets"][b], st["brackets"][b])
    sc_cmp["max_abs_value_diff"] = max(abs(v) for blk in sc_cmp["per_bracket"].values() for v in blk["value_diffs"].values())
    sc_cmp["all_held_agree"] = all(all(blk["held_agree"].values()) for blk in sc_cmp["per_bracket"].values())

    out = {"weights": wcheck, "errors_csv": err_cmp, "units_csv": u_cmp, "scorecard": sc_cmp,
           "share_normalisation_max_dev": max(abs(m["wsum_share"] - 1) for m in M.values())}
    json.dump(out, open(os.path.join(OUT, "out_cd.json"), "w"), indent=1)

    print("weights:", wcheck)
    print("share normalisation max |sum w s - 1|:", out["share_normalisation_max_dev"])
    print("errors.csv rows", err_cmp["n_rows"], "expected", err_cmp["n_expected_rows"], "missing", len(err_cmp["missing_rows"]),
          "string mismatches (%.6g):", len(err_cmp["string_mismatches"]))
    for c in cols:
        print(f"  {c:26s} max abs diff {err_cmp['max_abs_diff'][c]:.3e}  max rel diff {err_cmp['max_rel_diff'][c]:.3e}")
    for m_ in err_cmp["string_mismatches"][:20]:
        print("  mismatch", m_)
    print("units.csv rows", u_cmp["n_rows"], "expected", u_cmp["n_expected_rows"])
    for c in ucols:
        print(f"  {c:22s} max abs diff {u_cmp['max_abs_diff'][c]:.3e}  string mismatches {u_cmp['string_mismatches'][c]}")
    for ex in u_cmp["examples"][:10]:
        print("  example", ex)
    print("scorecard: verdicts agree", sc_cmp["verdicts_agree"], "all held agree", sc_cmp["all_held_agree"],
          "max |value diff|", sc_cmp["max_abs_value_diff"])
    print("my registered verdicts", mysc["verdicts"])
    for b, blk in mysc["brackets"].items():
        print("bracket", b, {p: v["held"] for p, v in blk.items()})
    r = mysc["registered"]
    print("registered numbers: P1 %.6f P2 %.6f P3 %.6f P4 %.6f P5 %.6f (ratio %.4f)" % (
        r["P1"]["value"], r["P2"]["value"], r["P3"]["value"], r["P4"]["value"], r["P5"]["value"], r["P5"]["ratio"]))
    for k, v in r["P6"]["quantities"].items():
        print("  P6", k, "O %.6f C %.6f ratio %.4f held %s" % (v["ORegan2022"], v["Chen2020"], v["ratio"], v["held"]))
    print("  P7 radial", r["P7"]["radial"], "corrected==radial", r["P7"]["radial_equals_corrected"])


if __name__ == "__main__":
    main()
