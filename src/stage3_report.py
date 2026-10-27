#!/usr/bin/env python3
"""Stage 3: tables, scorecard and figure from the Part B runs.
Writes results/stage3_errors.csv, stage3_scorecard.json, stage3_paper_numbers.json and stage3_figure.png/.pdf."""
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
from stage3_enkf import SIG_REF  # noqa: E402

R = C.RESULTS


def level(r):
    if r["method"] == "forecast":
        return "none"
    return {0.1: "0.1x", 1.0: "1x", 10.0: "10x"}[round(r["sigma_eps"] / SIG_REF, 1)]


def main():
    runs = json.load(open(os.path.join(R, "stage3_runs_21700.json"))) + json.load(open(os.path.join(R, "stage3_runs_4680.json")))
    for r in runs:
        r["level"] = level(r)
    # case (a): the end-corrected estimator is the estimator itself (beta = 0, D20)
    for r in [x for x in runs if x["bc"] == "a" and x["method"] == "estimator"]:
        runs.append(dict(r, method="corrected", note="no separate run: with the ends insulated beta = 0, so this is the estimator (D20)"))
    get = lambda cell, cond, bc, meth, lv: next(x for x in runs if (x["cell"], x["cond"], x["bc"], x["method"], x["level"]) ==
                                               (cell, cond, bc, meth, "none" if meth == "forecast" else lv))
    with open(os.path.join(R, "stage3_errors.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell", "condition", "ends", "method", "sigma_eps_level", "mean_abs_error_K", "end_error_K",
                    "learned_error_mean_second_half_W_m3", "end_sink_mean_second_half_W_m3", "note"])
        for r in sorted(runs, key=lambda x: (x["cell"], x["cond"], x["bc"], x["method"], x["level"])):
            w.writerow([r["cell"], r["cond"], "insulated" if r["bc"] == "a" else "cooled", r["method"], r["level"],
                        f"{r['mae_K']:.5f}", f"{r['end_error_K']:.5f}",
                        "" if r["learned_mean_second_half_W_m3"] is None else f"{r['learned_mean_second_half_W_m3']:.6g}",
                        "" if r["sink_mean_second_half_W_m3"] is None else f"{r['sink_mean_second_half_W_m3']:.6g}",
                        r.get("note", "end sink 0: beta = 0 with the ends insulated (D21)" if r["bc"] == "a" and r["method"] != "forecast" else "")])
    sens = json.load(open(os.path.join(R, "stage3_sensitivity.json")))
    conds = ("p25C_1.25C", "p25C_2C", "m5C_2C")
    sc = {}
    for lv in ("1x", "0.1x", "10x"):
        g = lambda *a: get(*a, lv)
        fa = [max(abs(e - t) for e, t in zip(g("21700", c, "a", "forecast")["core_est"], g("21700", c, "a", "forecast")["core_true"])) for c in conds]
        ea = [g("21700", c, "a", "estimator")["mae_K"] for c in conds]
        f2 = abs(g("21700", "m5C_2C", "b", "forecast")["end_error_K"])
        e2 = abs(g("21700", "m5C_2C", "b", "estimator")["end_error_K"])
        cb = [("21700", c) for c in conds] + [("4680", "m5C_2C")]
        p4 = [(g(cl, c, "b", "corrected")["mae_K"], g(cl, c, "b", "estimator")["mae_K"]) for cl, c in cb]
        p5 = [g("21700", c, "b", "estimator")["learned_mean_second_half_W_m3"] / g("21700", c, "b", "estimator")["sink_mean_second_half_W_m3"] for c in conds]
        f6, e6 = abs(g("4680", "m5C_2C", "b", "forecast")["end_error_K"]), abs(g("4680", "m5C_2C", "b", "estimator")["end_error_K"])
        s = {"P1": {"forecast_max_abs_K": fa, "estimator_mae_K": ea, "held": max(fa) <= 0.3 and max(ea) < 0.3},
             "P2": {"forecast_end_abs_K": f2, "held": f2 > 0.8},
             "P3": {"estimator_end_abs_K": e2, "ratio": e2 / f2, "held": e2 <= 0.5 * f2},
             "P4": {"corrected_vs_estimator_mae_K": p4, "held": all(a < b for a, b in p4)},
             "P5": {"learned_over_sink": p5, "held": all(abs(x - 1) <= 0.30 for x in p5)},
             "P6": {"forecast_end_abs_K": f6, "estimator_end_abs_K": e6, "held": f6 > 5 and e6 > 1}}
        if lv == "1x":
            base = g("21700", "m5C_2C", "b", "estimator")["mae_K"]
            n2 = next(x for x in sens if x.get("sigma_T") == 0.2 and x["dt_obs"] == 20.0 and "props" not in x)["mae_K"]
            s["P7"] = {"mae_noise_0.1_K": base, "mae_noise_0.2_K": n2, "increase_K": n2 - base, "held": n2 - base < 0.1}
        sc[lv] = s
    json.dump(sc, open(os.path.join(R, "stage3_scorecard.json"), "w"), indent=1)
    print({lv: {p: v["held"] for p, v in s.items()} for lv, s in sc.items()})
    paper = {"source": "Yang and Tartakovsky, J. Power Sources 664 (2026) 238948",
             "given": {"N_ens": [3000, "Section 4.2, p. 4"], "sigma_T_C": [0.1, "Section 2, p. 2"], "sigma_V_V": [0.001, "Section 2, p. 2"],
                       "observations": ["terminal voltage and surface temperature T^(N+2)", "Eq. 8, p. 3"],
                       "error_model": ["eps_k = b_k + omega_k, omega ~ N(0, sigma_eps^2), next prior mean zero", "Section 3 and Algorithm 1, p. 3"],
                       "core_temperature_accuracy": ["shown only in Figs. 3 and 5 (0.3C and 0.7C); no number in the text", "pp. 4 and 5"]},
             "not_given": ["sigma_eps (initial and per step)", "time step", "observation interval", "learning window"],
             "used_here": {"sigma_ref_W_m3": SIG_REF, "bracket": [0.1, 1, 10], "dt_obs_s": 20.0, "seed": 20261027}}
    json.dump(paper, open(os.path.join(R, "stage3_paper_numbers.json"), "w"), indent=1)
    plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "legend.fontsize": 6.2, "xtick.labelsize": 6.5,
                         "ytick.labelsize": 6.5, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6})
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.5), gridspec_kw=dict(width_ratios=[1, 1.25]))
    ref = get("21700", "m5C_2C", "b", "forecast", "1x")
    t = np.array(ref["t"])
    ax[0].plot(t, np.array(ref["core_true"]) + 5, color="#eb6834", lw=1.6, label="resolved cell")
    for meth, col, ls, lab in (("forecast", "#52514e", "--", "radial forecast"), ("estimator", "#2a78d6", "-", "estimator"),
                               ("corrected", "#6250d6", ":", "estimator, end-corrected forecast")):
        ax[0].plot(t, np.array(get("21700", "m5C_2C", "b", meth, "1x")["core_est"]) + 5, color=col, ls=ls, lw=1.3, label=lab)
    ax[0].set_xlabel("time (s)")
    ax[0].set_ylabel("core T above ambient (K)")
    ax[0].set_title("Core, M50, 2C, minus 5 C, ends cooled", loc="left")
    ax[0].legend(frameon=False, loc="lower right")
    cases = [("21700", "p25C_1.25C", "a", "1.25C\n25 C\ninsul."), ("21700", "p25C_1.25C", "b", "1.25C\n25 C\ncooled"),
             ("21700", "p25C_2C", "a", "2C\n25 C\ninsul."), ("21700", "p25C_2C", "b", "2C\n25 C\ncooled"),
             ("21700", "m5C_2C", "a", "2C\n-5 C\ninsul."), ("21700", "m5C_2C", "b", "2C\n-5 C\ncooled"),
             ("4680", "m5C_2C", "b", "4680\n2C, -5 C\ncooled")]
    x = np.arange(len(cases))
    for i, (meth, col, lab) in enumerate((("forecast", "#52514e", "radial forecast"), ("estimator", "#2a78d6", "estimator"),
                                          ("corrected", "#6250d6", "estimator, end-corrected"))):
        ax[1].bar(x + (i - 1) * 0.27, [get(cl, c, bc, meth, "1x")["end_error_K"] for cl, c, bc, _ in cases], 0.25, color=col, label=lab)
    ax[1].axhline(0, color="#0b0b0b", lw=0.6)
    ax[1].set_xticks(x, [c[3] for c in cases])
    ax[1].set_ylabel("core error at end of discharge (K)")
    ax[1].set_title("End-of-discharge error, estimate minus resolved", loc="left")
    ax[1].legend(frameon=False, loc="upper left")
    for a in ax:
        a.grid(True, color="#e6e5e1", lw=0.5)
        a.set_axisbelow(True)
    fig.tight_layout(pad=0.3, w_pad=0.8)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(R, f"stage3_figure.{ext}"), dpi=300)


if __name__ == "__main__":
    main()
