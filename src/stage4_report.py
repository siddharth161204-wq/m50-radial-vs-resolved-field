#!/usr/bin/env python3
"""Stage 4, Part C (D24): the unit's resistance and current share under the radial, resolved and end-corrected
fields, the errors against the resolved field, the scorecard, the paper numbers and the figure.
Reads results/stage4_unit_temps.json (Part A) and results/stage4_RT.csv, stage4_RT.json (Part B).
Writes results/stage4_units.csv, stage4_errors.csv, stage4_scorecard.json, stage4_paper_numbers.json and
stage4_figure.png/.pdf."""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

R = C.RESULTS
SETS = ("ORegan2022", "Chen2020")
SOCS = (1.0, 0.5)
READINGS = ("time_average", "end")
WEIGHTINGS = ("area", "unweighted")
FIELDS = ("radial", "corrected", "resolved")
MAIN = "21700_b_m5C_2C"
REG = {"set": "ORegan2022", "soc": 1.0, "reading": "time_average", "weighting": "area"}
LABEL = {"21700_b_m5C_2C": "M50, 2C, minus 5 C, ends cooled", "21700_b_p25C_2C": "M50, 2C, 25 C, ends cooled",
         "21700_b_p25C_1.25C": "M50, 1.25C, 25 C, ends cooled", "21700_a_m5C_2C": "M50, 2C, minus 5 C, ends insulated",
         "4680_b_m5C_2C": "4680, 2C, minus 5 C, ends cooled"}


def rt_table():
    rows = list(csv.DictReader(open(os.path.join(R, "stage4_RT.csv"))))
    tab = {}
    for s in SETS:
        for soc in SOCS:
            sel = sorted([r for r in rows if r["set"] == s and float(r["soc"]) == soc], key=lambda r: float(r["T_C"]))
            tab[(s, soc)] = (np.array([float(r["T_C"]) for r in sel]), np.log([float(r["R_ohm"]) for r in sel]))
    return tab


def weights(cell, n):
    Rc = C.cell_constants(cell)["R"]
    e = np.linspace(0.0, Rc, n + 1)
    return np.diff(e ** 2) / Rc ** 2, 0.5 * (e[1:] + e[:-1])


def metrics(Ts, w, tab, s, soc):
    Tg, lnR = tab[(s, soc)]
    assert Ts.min() >= Tg[0] and Ts.max() <= Tg[-1], (Ts.min(), Ts.max())
    Ru = np.exp(np.interp(Ts, Tg, lnR))
    g = 1.0 / Ru
    sh = g / np.sum(w * g)
    hot, cold = int(np.argmax(Ts)), int(np.argmin(Ts))
    return {"R": Ru, "share": sh, "R_mean": float(np.sum(w * Ru)), "spread": float(sh.max() - sh.min()),
            "sd": float(np.sqrt(np.sum(w * (sh - 1.0) ** 2))), "inner": float(sh[0]), "outer": float(sh[-1]),
            "hottest_unit": hot + 1, "hottest_share": float(sh[hot]), "coldest_unit": cold + 1, "coldest_share": float(sh[cold])}


def main():
    ut = json.load(open(os.path.join(R, "stage4_unit_temps.json")))["cases"]
    rtj = json.load(open(os.path.join(R, "stage4_RT.json")))
    tab = rt_table()
    M = {}                     # (case, field, set, soc, reading, weighting) -> metrics
    unit_rows = []
    for case, rec in ut.items():
        n = len(rec["resolved"]["time_average"])
        wa, rmid = weights(rec["cell"], n)
        for field in FIELDS:
            for reading in READINGS:
                Ts = np.array(rec[field][reading])
                for s in SETS:
                    for soc in SOCS:
                        ma = metrics(Ts, wa, tab, s, soc)
                        mu = metrics(Ts, np.full(n, 1.0 / n), tab, s, soc)
                        M[(case, field, s, soc, reading, "area")] = ma
                        M[(case, field, s, soc, reading, "unweighted")] = mu
                        for i in range(n):
                            unit_rows.append([case, field, s, f"{soc:g}", reading, i + 1, f"{1e3 * rmid[i]:.4f}",
                                              f"{wa[i]:.6e}", f"{Ts[i]:.6f}", f"{1e3 * ma['R'][i]:.6f}",
                                              f"{ma['share'][i]:.6f}", f"{mu['share'][i]:.6f}"])
    with open(os.path.join(R, "stage4_units.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "field", "set", "soc", "reading", "unit", "r_mid_mm", "area_weight", "T_C", "R_mOhm",
                    "share_area_weighted", "share_unweighted"])
        w.writerows(unit_rows)
    E = {}
    err_rows = []
    for (case, field, s, soc, reading, wt), m in M.items():
        if field == "resolved":
            continue
        ref = M[(case, "resolved", s, soc, reading, wt)]
        e = {"R_mean_rel": m["R_mean"] / ref["R_mean"] - 1, "spread_rel": m["spread"] / ref["spread"] - 1,
             "sd_rel": m["sd"] / ref["sd"] - 1, "inner_pp": 100 * (m["inner"] - ref["inner"]),
             "outer_pp": 100 * (m["outer"] - ref["outer"]),
             "R_mean_mOhm": 1e3 * m["R_mean"], "R_mean_resolved_mOhm": 1e3 * ref["R_mean"],
             "spread": m["spread"], "spread_resolved": ref["spread"], "inner": m["inner"], "inner_resolved": ref["inner"],
             "outer": m["outer"], "outer_resolved": ref["outer"]}
        E[(case, field, s, soc, reading, wt)] = e
        err_rows.append([case, field, s, f"{soc:g}", reading, wt] + [f"{e[k]:.6g}" for k in (
            "R_mean_mOhm", "R_mean_resolved_mOhm", "R_mean_rel", "spread", "spread_resolved", "spread_rel", "sd_rel",
            "inner", "inner_resolved", "inner_pp", "outer", "outer_resolved", "outer_pp")])
    with open(os.path.join(R, "stage4_errors.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "field", "set", "soc", "reading", "weighting", "R_mean_mOhm", "R_mean_resolved_mOhm",
                    "R_mean_rel_error", "share_spread", "share_spread_resolved", "share_spread_rel_error",
                    "share_sd_rel_error", "inner_share", "inner_share_resolved", "inner_share_error_pp",
                    "outer_share", "outer_share_resolved", "outer_share_error_pp"])
        w.writerows(err_rows)

    def score(s="ORegan2022", soc=1.0, reading="time_average", wt="area"):
        g = lambda case, field, set_=None: E[(case, field, set_ or s, soc, reading, wt)]
        q = {"P1": g(MAIN, "radial")["spread_rel"], "P2": g(MAIN, "corrected")["spread_rel"],
             "P3": g(MAIN, "radial")["R_mean_rel"], "P4": g("21700_b_p25C_2C", "radial")["R_mean_rel"],
             "P5": g("4680_b_m5C_2C", "radial")["spread_rel"]}
        out = {"P1": {"radial_spread_rel": q["P1"], "held": q["P1"] >= 0.30},
               "P2": {"corrected_spread_rel": q["P2"], "held": abs(q["P2"]) < 0.08},
               "P3": {"radial_R_mean_rel": q["P3"], "held": q["P3"] < -0.04},
               "P4": {"radial_R_mean_rel_2C_25C": q["P4"], "held": abs(q["P4"]) < 0.03},
               "P5": {"radial_spread_rel_4680": q["P5"], "radial_spread_rel_M50": q["P1"], "ratio": q["P5"] / q["P1"],
                      "held": q["P5"] >= 3 * q["P1"]}}
        if s == "ORegan2022":
            gc = lambda case, field: E[(case, field, "Chen2020", soc, reading, wt)]
            qc = {"P1": gc(MAIN, "radial")["spread_rel"], "P2": gc(MAIN, "corrected")["spread_rel"],
                  "P3": gc(MAIN, "radial")["R_mean_rel"], "P4": gc("21700_b_p25C_2C", "radial")["R_mean_rel"],
                  "P5": gc("4680_b_m5C_2C", "radial")["spread_rel"]}
            each = {k: {"ORegan2022": q[k], "Chen2020": qc[k], "ratio": qc[k] / q[k], "held": abs(qc[k]) < 0.5 * abs(q[k])}
                    for k in q}
            out["P6"] = {"quantities": each, "held": all(v["held"] for v in each.values())}
        a = g("21700_a_m5C_2C", "radial")
        out["P7"] = {"R_mean_rel": a["R_mean_rel"], "spread_rel": a["spread_rel"], "inner_pp": a["inner_pp"],
                     "outer_pp": a["outer_pp"],
                     "held": abs(a["R_mean_rel"]) < 0.01 and abs(a["spread_rel"]) < 0.01 and abs(a["inner_pp"]) < 1
                     and abs(a["outer_pp"]) < 1}
        return out

    sc = {"registered": score(), "brackets": {
        "Chen2020": score(s="Chen2020"), "soc_50": score(soc=0.5), "end_of_discharge": score(reading="end"),
        "unweighted": score(wt="unweighted")}}
    sc["verdicts"] = {p: v["held"] for p, v in sc["registered"].items()}
    json.dump(sc, open(os.path.join(R, "stage4_scorecard.json"), "w"), indent=1)
    print("registered", sc["verdicts"])
    for b, v in sc["brackets"].items():
        print(b, {p: x["held"] for p, x in v.items()})
    # C3: the errors across cases at the registered choices, and how much the end correction removes
    c3 = {}
    for case in ut:
        er, ec = E[(case, "radial", *REG.values())], E[(case, "corrected", *REG.values())]
        c3[case] = {"radial": {k: er[k] for k in ("R_mean_rel", "spread_rel", "inner_pp", "outer_pp")},
                    "corrected": {k: ec[k] for k in ("R_mean_rel", "spread_rel", "inner_pp", "outer_pp")},
                    "removed_by_correction": {k: (1 - abs(ec[k]) / abs(er[k])) if er[k] != 0 else None
                                              for k in ("R_mean_rel", "spread_rel", "inner_pp", "outer_pp")}}
    paper = {
        "procedure": rtj,
        "sets": {
            "ORegan2022": {"source": "O'Regan et al. 2022, Electrochim. Acta 425, 140700; read in the ChemRxiv preprint of "
                                     "17 January 2022, doi:10.26434/chemrxiv-2022-d2q4n, with its supplementary information",
                           "measured_ranges_C": {"exchange-current density and activation energy (impedance)": [15, 45],
                                                 "particle diffusivity and activation energy (GITT)": [5, 45],
                                                 "electronic conductivity": [15, 35], "entropic term": [-5, 25],
                                                 "thermal diffusivity": [-5, 55]},
                           "where": "preprint Table 2, p. 5; GITT p. 6; impedance p. 7; 0 C outside the measured range, p. 31",
                           "electrolyte": "Landesfeind and Gasteiger 2019, minus 10 to 50 C (abstract)",
                           "minus_5C": "below the measured range of the kinetics (15 C) and of solid diffusion (5 C): an extrapolation of the set"},
            "Chen2020": {"source": "Chen et al. 2020, J. Electrochem. Soc. 167, 080534 (Warwick repository copy)",
                         "temperature_dependence": "Arrhenius exchange-current densities only, 35.0 and 17.8 kJ/mol, from "
                                                   "impedance at room temperature and at 30, 40, 50 and 60 C",
                         "minus_5C": "an extrapolation of the set"}},
        "registered": REG, "C3_registered": c3,
        "unit_temperature_summary": {case: {f: {r: {"mean_area_weighted_C": float(np.sum(weights(rec["cell"], len(rec[f][r]))[0] * np.array(rec[f][r]))),
                                                    "spread_K": float(max(rec[f][r]) - min(rec[f][r]))} for r in READINGS}
                                            for f in FIELDS} for case, rec in ut.items()},
    }
    json.dump(paper, open(os.path.join(R, "stage4_paper_numbers.json"), "w"), indent=1)
    figure(M, E, ut)


def figure(M, E, ut):
    plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "legend.fontsize": 6.2, "xtick.labelsize": 6.5,
                         "ytick.labelsize": 6.5, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6})
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.6), gridspec_kw=dict(width_ratios=[1, 1.25]))
    rec = ut[MAIN]
    _, rmid = weights(rec["cell"], len(rec["resolved"]["time_average"]))
    for field, col, ls, lab in (("resolved", "#eb6834", "-", "resolved cell"), ("radial", "#52514e", "--", "radial model"),
                                ("corrected", "#6250d6", ":", "radial model, end-corrected")):
        sh = M[(MAIN, field, *REG.values())]["share"]
        ax[0].plot(1e3 * rmid, 100 * sh, color=col, ls=ls, lw=1.5 if field == "resolved" else 1.3, label=lab)
    ax[0].axhline(100, color="#0b0b0b", lw=0.5)
    ax[0].set_xlabel("unit mid-radius (mm)")
    ax[0].set_ylabel("current density, % of the cell mean")
    ax[0].set_title("Unit shares, M50, 2C, minus 5 C, ends cooled", loc="left")
    ax[0].legend(frameon=False, loc="upper right")
    cases = list(LABEL)
    ticks = ["M50\n2C, -5 C\ncooled", "M50\n2C, 25 C\ncooled", "M50\n1.25C, 25 C\ncooled", "M50\n2C, -5 C\ninsul.",
             "4680\n2C, -5 C\ncooled"]
    x = np.arange(len(cases))
    spec = (("radial", "ORegan2022", "#52514e", "radial, ORegan2022"), ("radial", "Chen2020", "#a9a8a3", "radial, Chen2020"),
            ("corrected", "ORegan2022", "#6250d6", "end-corrected, ORegan2022"),
            ("corrected", "Chen2020", "#b3aaee", "end-corrected, Chen2020"))
    for i, (field, s, col, lab) in enumerate(spec):
        vals = [100 * E[(c, field, s, 1.0, "time_average", "area")]["spread_rel"] for c in cases]
        ax[1].bar(x + (i - 1.5) * 0.2, vals, 0.18, color=col, label=lab)
    ax[1].axhline(0, color="#0b0b0b", lw=0.6)
    ax[1].set_xticks(x, ticks)
    ax[1].set_ylabel("share-spread error against the resolved cell (%)")
    ax[1].set_title("Share-spread error by case and set", loc="left")
    ax[1].legend(frameon=False, loc="upper left")
    for a in ax:
        a.grid(True, color="#e6e5e1", lw=0.5)
        a.set_axisbelow(True)
    fig.tight_layout(pad=0.3, w_pad=0.8)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(R, f"stage4_figure.{ext}"), dpi=300)


if __name__ == "__main__":
    main()
