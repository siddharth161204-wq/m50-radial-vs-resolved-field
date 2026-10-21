#!/usr/bin/env python3
"""Stage 2: scores P1 to P10 by the rules of predictions_stage2.md and draws the Stage 2 figure.
Writes results/stage2_scorecard.json, results/stage2_figure.png and results/stage2_figure.pdf."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

J = lambda n: json.load(open(os.path.join(C.RESULTS, n)))


def main():
    corr, ref = J("stage2_correction.json"), J("stage2_ref33.json")
    post = J("posthoc_matched_time.json")["cases"]
    B = corr["B2"]
    k = "Chen2020_m5C_2C"
    m, f = B[f"21700_b_{k}"], B[f"4680_b_{k}"]
    d = B[f"21700_d_{k}"]
    c = ref["conditions"]
    sc = {}
    r1 = C.roll_properties()["registered"]["k_across"] / ref["ref33"]["lambda"]
    sc["P1"] = {"value": r1, "held": 1.0 <= r1 <= 2.5}
    f2 = [c["2C minus 5 C"][t]["factor_ref33props"] for t in ("482.4", "540.0")]
    sc["P2"] = {"value": f2, "held": all(x > 1.5 for x in f2)}
    ch = []
    for t in ("482.4", "540.0"):
        ro = c["2C minus 5 C"][t]["factor_oregan"] / c["2C 25 C"]["end"]["factor_oregan"]
        r3 = c["2C minus 5 C"][t]["factor_ref33props"] / c["2C 25 C"]["end"]["factor_ref33props"]
        ch.append({"R_oregan": ro, "R_ref33": r3, "change": r3 / ro - 1})
    sc["P3"] = {"value": ch, "held": all(abs(x["change"]) <= 0.10 for x in ch)}
    hw = [ref["heat_window"][t]["ratio"] for t in ("482.4", "540")]
    sc["P4"] = {"value": hw, "held": all(x is not None and 1.5 <= x <= 4 for x in hw)}
    sh = {"21700": (m["ends_share_corrected"], post["21700_b"]["ends_share_of_heat_lost"]),
          "4680": (f["ends_share_corrected"], post["4680_b"]["ends_share_of_heat_lost"])}
    sc["P5"] = {"value": sh, "held": all(abs(a - b) <= 0.02 for a, b in sh.values())}
    o6 = [m["corrected"]["mean_abs_offset_K"], f["corrected"]["mean_abs_offset_K"]]
    sc["P6"] = {"value": o6, "held": o6[0] < 0.3 and o6[1] < 1.0}
    s7 = [m["corrected"]["spread_overstatement"], f["corrected"]["spread_overstatement"]]
    sc["P7"] = {"value": s7, "held": all(abs(x) < 0.10 for x in s7)}
    a8 = [m["axial_ratio_corrected_over_resolved"], f["axial_ratio_corrected_over_resolved"]]
    sc["P8"] = {"value": a8, "held": all(abs(x - 1) <= 0.15 for x in a8)}
    sc["P9"] = {"value": d["corrected"]["mean_abs_offset_K"], "held": d["corrected"]["mean_abs_offset_K"] < 0.5}
    a10 = d["axial_ratio_corrected_over_resolved"]
    sc["P10"] = {"value": a10, "held": abs(a10 - 1) > 0.15}
    json.dump(sc, open(os.path.join(C.RESULTS, "stage2_scorecard.json"), "w"), indent=1)
    print({p: v["held"] for p, v in sc.items()})

    plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "legend.fontsize": 6.2, "xtick.labelsize": 6.5,
                         "ytick.labelsize": 6.5, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.linewidth": 0.6})
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.35), gridspec_kw=dict(width_ratios=[1.35, 1, 1]))
    labs = [("1.25C 25 C", "end", "1.25C, 25 C"), ("2C 25 C", "end", "2C, 25 C"),
            ("2C minus 5 C", "482.4", "2C, minus 5 C\n(482 s)"), ("4680 2C minus 5 C", "end", "4680, 2C,\nminus 5 C")]
    x = np.arange(len(labs))
    series = [("factor_oregan", "O'Regan properties (Stage 1)", "#52514e"),
              ("factor_ref33props", "ref. 33 properties", "#2a78d6"),
              ("remainder", "ref. 33 properties and heat", "#1baf7a")]
    for i, (key, lab, col) in enumerate(series):
        vals = [c[a][b][key] for a, b, _ in labs]
        ax[0].bar(x + (i - 1) * 0.26, vals, 0.24, color=col, label=lab)
    ax[0].axhline(1.0, color="#0b0b0b", lw=0.7)
    ax[0].set_xticks(x, [l for _, _, l in labs])
    ax[0].set_ylabel("paper's unit difference / model's")
    ax[0].set_title("Factor to the paper", loc="left")
    ax[0].set_ylim(0, 4.9)
    ax[0].legend(frameon=False, loc="upper left")
    for j, (cell, rec) in enumerate((("M50", m), ("4680", f))):
        a = ax[1 + j]
        n = len(rec["units_resolved"])
        u = np.arange(1, n + 1)
        a.plot(u, np.array(rec["units_resolved"]) + 5, color="#eb6834", lw=1.4, label="resolved, ends cooled")
        a.plot(u, np.array(rec["units_uncorrected"]) + 5, color="#52514e", ls="--", lw=1.4, label="radial model")
        a.plot(u, np.array(rec["units_corrected"]) + 5, color="#6250d6", ls=":", lw=1.8, label="radial, end-corrected")
        a.set_xlim(1, n)
        a.set_ylim(bottom=0)
        a.set_xlabel("unit, core to surface")
        a.set_title(f"Units, {cell}, case (b)", loc="left")
        if j == 0:
            a.set_ylabel("unit T above ambient (K)")
            a.legend(frameon=False, loc="lower left")
    for a in ax:
        a.grid(True, color="#e6e5e1", lw=0.5)
        a.set_axisbelow(True)
    fig.tight_layout(pad=0.3, w_pad=0.8)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(C.RESULTS, f"stage2_figure.{ext}"), dpi=300)


if __name__ == "__main__":
    main()
