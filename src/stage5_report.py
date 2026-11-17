#!/usr/bin/env python3
"""Stage 5, the readings (D31, D32), the scorecard (predictions_stage5.md) and the figure, from the stored kernels and
runs. Nothing here solves a model.

python3 src/stage5_report.py
-> results/stage5_discharge.csv, stage5_shares.csv, stage5_charge.csv, stage5_limit.csv, stage5_p1.json,
   stage5_scorecard.json, stage5_paper_numbers.json, stage5_figure.png/.pdf"""
import csv
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import stage5_common as S5  # noqa: E402
import stage5_coupled as SC  # noqa: E402
import stage5_runs as RN  # noqa: E402

R = C.RESULTS
SETS = ("ORegan2022", "Chen2020")
LABELS = ("radial", "resolved", "corrected")
HEATS = ("two-way", "one-way")
PROXY_MAIN = 0.0554168        # Stage 4's registered proxy spread, main case (results/stage4_errors.csv)
PROXY_MAIN_CHEN = 0.0253836   # its Chen2020 bracket


def exists(name):
    return os.path.exists(os.path.join(S5.RUNDIR, name + ".npz"))


# ---------------------------------------------------------------------------------------------------------------
# readings of one run
# ---------------------------------------------------------------------------------------------------------------
def energy_capacity(run):
    t, V = run["t"], run["V"]
    I = run["meta"]["I_app_A"]
    return float(np.trapezoid(V * abs(I), t) / 3600.0), float(abs(I) * t[-1] / 3600.0)


def tavg(t, y):
    return float(np.trapezoid(y, t) / t[-1])


def shares_reading(run):
    t = run["t"]
    s = run["I"] / run["meta"]["I_app_A"]
    W = np.asarray(run["meta"]["W"])
    spread = s.max(axis=1) - s.min(axis=1)
    sd = np.sqrt(((s - 1.0) ** 2 * W[None, :]).sum(axis=1))
    s1 = s[:, 0]
    rev = None
    above = np.where(s1 > 1.0 + 1e-12)[0]
    if len(above):
        after = np.where(s1[above[0]:] < 1.0)[0]
        if len(after):
            j = above[0] + after[0]
            rev = float(np.interp(1.0, [s1[j], s1[j - 1]], [t[j], t[j - 1]]))
    return {"spread_tavg": tavg(t, spread), "sd_tavg": tavg(t, sd), "inner_tavg": tavg(t, s1), "outer_tavg": tavg(t, s[:, -1]),
            "inner_max": float(s1.max()), "t_inner_max_s": float(t[int(np.argmax(s1))]), "reversal_s": rev,
            "spread_end": float(spread[-1]), "inner_end": float(s1[-1]), "outer_end": float(s[-1, -1]),
            "max_current_balance_residual": float(run["resid"].max())}


def margin_reading(run):
    mn, mi = run["margin_nodes_min"].astype(float), run["margin_interface"].astype(float)
    both = np.minimum(mn, mi)
    k, g = np.unravel_index(int(np.argmin(both)), both.shape)
    return {"margin_V": float(both[k, g]), "group": int(g) + 1, "t_min_s": float(run["t"][k]),
            "at_interface": bool(mi[k, g] <= mn[k, g]), "t_end_s": float(run["t"][-1]),
            "charge_Ah": energy_capacity(run)[1], "status": run["meta"]["status"],
            "max_current_balance_residual": float(run["resid"].max())}


# ---------------------------------------------------------------------------------------------------------------
# the proxy of Stage 4 (D23, D24), for C3
# ---------------------------------------------------------------------------------------------------------------
def rt_table(pset="ORegan2022", soc=1.0):
    rows = [r for r in csv.DictReader(open(os.path.join(R, "stage4_RT.csv"))) if r["set"] == pset and float(r["soc"]) == soc]
    T = np.array([float(r["T_C"]) for r in rows])
    lnR = np.log(np.array([float(r["R_ohm"]) for r in rows]))
    return lambda x: np.exp(np.interp(x, T, lnR))


def proxy_spread(T, w, Rof):
    g = 1.0 / Rof(np.asarray(T))
    s = g / (np.asarray(w) * g).sum()
    return float(s.max() - s.min()), s


def stage4_proxy(case, field, pset):
    for r in csv.DictReader(open(os.path.join(R, "stage4_errors.csv"))):
        if (r["case"] == case and r["field"] == field and r["set"] == pset and float(r["soc"]) == 1.0
                and r["reading"] == "time_average" and r["weighting"] == "area"):
            return {"spread": float(r["share_spread"]), "spread_resolved": float(r["share_spread_resolved"]),
                    "spread_rel_error": float(r["share_spread_rel_error"]), "inner": float(r["inner_share"]),
                    "inner_resolved": float(r["inner_share_resolved"]), "outer": float(r["outer_share"]),
                    "outer_resolved": float(r["outer_share_resolved"])}
    return None


def window_average(series, dt, t_cut, Ta):
    """Time average over [0, t_cut] of a step series series[k] (k = 0 is the ambient) by the trapezoidal rule,
    with the end value interpolated linearly in time (D31)."""
    n = series.shape[0] - 1
    kf = min(int(math.floor(t_cut / dt + 1e-9)), n)
    t = dt * np.arange(kf + 1)
    y = series[:kf + 1]
    if t_cut > t[-1] + 1e-9:
        if kf + 1 <= n:
            y_end = y[-1] + (series[kf + 1] - y[-1]) * (t_cut - t[-1]) / dt
        else:
            y_end = y[-1]                                # held past the archive's end (D30)
        t = np.append(t, t_cut)
        y = np.vstack([y, y_end[None, :]])
    return np.trapezoid(y, t, axis=0) / t_cut


# ---------------------------------------------------------------------------------------------------------------
def kernel_for(case, label, gridname=None, G=S5.G_REG):
    cell, ends, Ta, I, g0 = RN.DISCHARGE_CASES[case]
    mdl, bc = RN.models_for(ends)[label]
    return S5.Kernel(S5.kernel_path(mdl, bc, cell, gridname or g0, G))


def discharge_tables():
    rows_d, rows_s = [], []
    for case, (cell, ends, Ta, I, g0) in RN.DISCHARGE_CASES.items():
        for pset in SETS:
            for heat in HEATS:
                per = {}
                for label in LABELS:
                    lab_run = "radial" if (ends == "a" and label == "corrected") else label
                    nc = RN.run_name("C", case, lab_run, pset, heat, False, S5.G_REG)
                    ns = RN.run_name("C", case, lab_run, pset, heat, True, S5.G_REG)
                    if not (exists(nc) and exists(ns)):
                        continue
                    rc, rs = SC.load_run(nc), SC.load_run(ns)
                    Ec, Qc = energy_capacity(rc)
                    Es, Qs = energy_capacity(rs)
                    d = {"case": case, "cell": cell, "ends": "insulated" if ends == "a" else "cooled", "T_amb_C": Ta,
                         "rate_C": I / S5.C_STUDY_A, "set": pset, "heat": heat, "kernel": label,
                         "identical_to_radial": ends == "a" and label == "corrected",
                         "E_single_Wh": Es, "E_coupled_Wh": Ec, "penalty_energy": Es / Ec - 1,
                         "Q_single_Ah": Qs, "Q_coupled_Ah": Qc, "penalty_capacity": Qs / Qc - 1,
                         "t_cut_single_s": float(rs["t"][-1]), "t_cut_coupled_s": float(rc["t"][-1]),
                         "held_steps_coupled": rc["meta"]["held_steps_past_archive"],
                         "held_steps_single": rs["meta"]["held_steps_past_archive"],
                         "archive_t_end_s": S5.grid(g0)[2]}
                    sr = shares_reading(rc)
                    sh = {"case": case, "set": pset, "heat": heat, "kernel": label, **sr, "t_cut_s": float(rc["t"][-1])}
                    if heat == "one-way":
                        # C3: Stage 4's proxy, and the proxy over the coupled run's own window
                        f4 = {"radial": "radial", "corrected": "corrected", "resolved": "radial"}[label]
                        p4 = stage4_proxy(case, f4, pset)
                        if p4:
                            sh["proxy_stage4_spread"] = p4["spread_resolved"] if label == "resolved" else p4["spread"]
                        k = kernel_for(case, lab_run)
                        q = S5.registered_heat_on_grid(g0)
                        Tu = np.vstack([np.full(k.N, Ta), Ta + S5.conv_series(k.S_unit_uniform[:, :, None],
                                                                                k.S_inf_unit_uniform[:, None], q)])
                        Tg = Tu @ S5.unit_to_group_matrix(k.N, k.G).T
                        Rof = rt_table(pset)
                        Tu_avg = window_average(Tu, k.dt, float(rc["t"][-1]), Ta)
                        Tg_avg = window_average(Tg, k.dt, float(rc["t"][-1]), Ta)
                        sh["proxy_window_unit_spread"] = proxy_spread(Tu_avg, S5.unit_weights(k.N), Rof)[0]
                        sh["proxy_window_group_spread"] = proxy_spread(Tg_avg, k.W, Rof)[0]
                        sh["T_mean_window_C"] = float(S5.unit_weights(k.N) @ Tu_avg)
                        sh["T_spread_units_window_K"] = float(Tu_avg.max() - Tu_avg.min())
                    per[label] = (d, sh)
                res = per.get("resolved")
                for label, (d, sh) in per.items():
                    if res:
                        d0, s0 = res
                        d["penalty_energy_minus_resolved_pp"] = 100 * (d["penalty_energy"] - d0["penalty_energy"])
                        d["penalty_energy_rel_error"] = (d["penalty_energy"] / d0["penalty_energy"] - 1) if d0["penalty_energy"] else None
                        sh["spread_rel_error"] = sh["spread_tavg"] / s0["spread_tavg"] - 1
                        sh["inner_error_pp"] = 100 * (sh["inner_tavg"] - s0["inner_tavg"])
                        sh["outer_error_pp"] = 100 * (sh["outer_tavg"] - s0["outer_tavg"])
                        sh["reversal_error_s"] = (sh["reversal_s"] - s0["reversal_s"]) if (sh["reversal_s"] is not None and s0["reversal_s"] is not None) else None
                    rows_d.append(d)
                    rows_s.append(sh)
    return rows_d, rows_s


def charge_tables():
    rows = []
    for cell in ("21700", "4680"):
        for pset in SETS:
            for case, (rate, Ta, reg) in RN.CHARGE_CASES.items():
                per = {}
                for label in LABELS:
                    for single in (False, True):
                        n = RN.run_name("D", f"{cell}_{case}", label, pset, "two-way", single, S5.G_REG)
                        if not exists(n):
                            continue
                        r = margin_reading(SC.load_run(n))
                        row = {"cell": cell, "case": case, "rate_spec_C": rate, "current_A_M50": rate * S5.C_SPEC_A,
                               "T_amb_C": Ta, "within_specification": reg, "set": pset, "kernel": label,
                               "model": "single" if single else "coupled", **r}
                        per[(label, single)] = row
                        rows.append(row)
                for (label, single), row in per.items():
                    ref = per.get(("resolved", single))
                    if ref:
                        row["margin_minus_resolved_mV"] = 1e3 * (row["margin_V"] - ref["margin_V"])
    return rows


def limit_table():
    rows = []
    for cell in ("21700", "4680"):
        for pset in SETS:
            for Ta in (0.0, 10.0, 25.0):
                p = os.path.join(S5.RUNDIR, f"limit_{cell}_{pset}_{Ta:g}C.json")
                if not os.path.exists(p):
                    continue
                d = json.load(open(p))
                for key, v in d.items():
                    label, model = key.split("|")
                    rows.append({"cell": cell, "set": pset, "T_amb_C": Ta, "kernel": label, "model": model,
                                 "rate_spec_C": v.get("rate"), "fails_at_spec_C": v.get("fail_above"),
                                 "bracket_width_C": v.get("width"), "fine_rate_spec_C": v.get("fine_rate"),
                                 "fine_fails_at_spec_C": v.get("fine_fail_above"), "n_trials": len(v["trials"]),
                                 "start_spec_C": v.get("start"),
                                 "rate_A_M50": v["rate"] * S5.C_SPEC_A if v.get("rate") else None})
    return rows


# ---------------------------------------------------------------------------------------------------------------
# P1: the kernels against Stage 4's stored histories
# ---------------------------------------------------------------------------------------------------------------
def p1():
    h1 = json.load(open(os.path.join(R, "stage4_hist_1d.json")))
    h3 = {**json.load(open(os.path.join(R, "stage4_hist_3d_21700.json"))),
          **json.load(open(os.path.join(R, "stage4_hist_3d_4680.json")))}
    out = {}
    for case in ("21700_b_m5C_2C", "21700_b_p25C_2C", "21700_b_p25C_1.25C", "21700_a_m5C_2C", "4680_b_m5C_2C"):
        cell, ends, Ta, I, g0 = RN.DISCHARGE_CASES[case]
        q = S5.registered_heat_on_grid(g0)
        for label in LABELS:
            k = kernel_for(case, label)
            rise = S5.conv_series(k.S_unit_uniform[:, :, None], k.S_inf_unit_uniform[:, None], q)
            if label == "resolved":
                arch = h3[case]["resolved"]
                times = h3[case]["times"]
            else:
                hh = h1[case]
                arch = hh["radial"] if (label == "radial" or ends == "a") else hh["corrected"]
                times = hh["times"]
            steps = np.rint(np.array(times) / k.dt).astype(int)
            assert np.abs(steps * k.dt - np.array(times)).max() < 1e-6
            T = Ta + rise[steps - 1]
            d = np.abs(T - np.array(arch))
            out[f"{case}|{label}"] = {"max_abs_K": float(d.max()), "n_times": len(times), "n_units": int(d.shape[1]),
                                      "kernel": os.path.basename(k.path), "kernel_steps": k.K}
    worst = max(v["max_abs_K"] for v in out.values())
    return {"cases": out, "max_abs_K": worst, "held": bool(worst < 0.01)}


# ---------------------------------------------------------------------------------------------------------------
def write_csv(path, rows):
    if not rows:
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.9g}" if isinstance(v, float) else ("" if v is None else v)) for k, v in r.items()})


def find(rows, **kw):
    out = [r for r in rows if all(r.get(k) == v for k, v in kw.items())]
    return out[0] if out else None


def p6_reading(pset="ORegan2022", case="21700_b_m5C_2C"):
    """P6: the time-averaged spread of the unit temperatures under each group's own heat and under the same total
    heat applied uniformly, from the run's stored heat history (predictions_stage5.md)."""
    cell, ends, Ta, I, g0 = RN.DISCHARGE_CASES[case]
    k = kernel_for(case, "resolved")
    run = SC.load_run(RN.run_name("C", case, "resolved", pset, "two-way", False, S5.G_REG))
    t = run["t"]
    n_full = int(math.floor(t[-1] / k.dt + 1e-9))
    if abs(t[min(n_full, len(t) - 1)] - n_full * k.dt) > 1e-6:
        n_full = min(n_full, len(t) - 1)
    q = run["q"][1:n_full + 1].astype(np.float64)           # heats at the end of steps 1..n_full
    Tg_unit = np.vstack([np.full(k.N, Ta), Ta + S5.conv_series(k.S_unit, k.S_inf_unit, q)])
    qu = q @ k.W
    Tu_unit = np.vstack([np.full(k.N, Ta), Ta + S5.conv_series(k.S_unit_uniform[:, :, None], k.S_inf_unit_uniform[:, None], qu)])
    tt = np.append(k.dt * np.arange(n_full + 1), t[-1]) if t[-1] > n_full * k.dt + 1e-9 else k.dt * np.arange(n_full + 1)

    def spread_avg(Tun):
        sp = Tun.max(axis=1) - Tun.min(axis=1)
        if len(tt) > len(sp):
            sp = np.append(sp, sp[-1])
        return float(np.trapezoid(sp, tt) / tt[-1])
    a, b = spread_avg(Tg_unit), spread_avg(Tu_unit)
    return {"spread_per_group_heat_K": a, "spread_uniform_heat_K": b, "ratio_minus_1": a / b - 1,
            "held": bool(abs(a / b - 1) < 0.10), "steps": n_full}


def scorecard(rows_d, rows_s, rows_c, rows_l, P1):
    sc = {"registered": {}, "brackets_Chen2020": {}}
    for pset, key in (("ORegan2022", "registered"), ("Chen2020", "brackets_Chen2020")):
        out = {}
        if pset == "ORegan2022":
            out["P1"] = {"max_abs_K": P1["max_abs_K"], "held": P1["held"]}
        g = lambda kern, heat, case="21700_b_m5C_2C": find(rows_s, case=case, set=pset, heat=heat, kernel=kern)
        d = lambda kern, heat, case="21700_b_m5C_2C": find(rows_d, case=case, set=pset, heat=heat, kernel=kern)
        a, b = g("radial", "one-way"), g("resolved", "one-way")
        if a and b:
            x = a["spread_tavg"] / b["spread_tavg"] - 1
            out["P2"] = {"radial_over_resolved_minus_1": x, "held": bool(0.25 <= x <= 0.45)}
            ref = PROXY_MAIN if pset == "ORegan2022" else PROXY_MAIN_CHEN
            y = b["spread_tavg"] / ref - 1
            out["P3"] = {"coupled_spread": b["spread_tavg"], "proxy": ref, "ratio_minus_1": y, "held": bool(-0.20 <= y <= 0.20)}
        a, b = d("radial", "two-way"), d("resolved", "two-way")
        if a and b:
            out["P4"] = {"penalty_radial": a["penalty_energy"], "penalty_resolved": b["penalty_energy"],
                         "held": bool(a["penalty_energy"] > 0 and b["penalty_energy"] <= 0.8 * a["penalty_energy"])}
        a, b = d("radial", "two-way", "4680_b_m5C_2C"), d("resolved", "two-way", "4680_b_m5C_2C")
        if a and b:
            out["P5"] = {"penalty_radial": a["penalty_energy"], "penalty_resolved": b["penalty_energy"],
                         "ratio": (a["penalty_energy"] / b["penalty_energy"]) if b["penalty_energy"] else None,
                         "held": bool(a["penalty_energy"] > 0 and a["penalty_energy"] >= 1.5 * b["penalty_energy"])}
        try:
            out["P6"] = p6_reading(pset)
        except FileNotFoundError:
            pass
        m = lambda cell, case, kern: find(rows_c, cell=cell, case=case, set=pset, kernel=kern, model="coupled")
        diffs = []
        for case in ("0.3C_0C", "0.7C_25C"):
            a, b = m("21700", case, "radial"), m("21700", case, "resolved")
            if a and b:
                diffs.append(1e3 * (a["margin_V"] - b["margin_V"]))
        if len(diffs) == 2:
            out["P7"] = {"radial_minus_resolved_mV": diffs, "held": bool(all(abs(x) < 2.0 for x in diffs))}
        holders = {}
        for cell in ("21700", "4680"):
            for case in ("0.3C_0C", "0.7C_25C"):
                for kern in LABELS:
                    r = m(cell, case, kern)
                    if r:
                        holders[f"{cell}|{case}|{kern}"] = r["group"]
        if len(holders) == 12:
            out["P8"] = {"group_holding_minimum": holders, "outermost": S5.G_REG,
                         "held": bool(all(v == S5.G_REG for v in holders.values()))}
        lim = lambda cell, model: find(rows_l, cell=cell, set=pset, T_amb_C=0.0, kernel="resolved", model=model)
        e = {}
        for cell in ("21700", "4680"):
            s_, c_ = lim(cell, "single"), lim(cell, "coupled")
            if s_ and c_:
                rs = s_["fine_rate_spec_C"] or s_["rate_spec_C"]
                rc = c_["fine_rate_spec_C"] or c_["rate_spec_C"]
                e[cell] = {"single": rs, "coupled": rc, "e": rs / rc - 1,
                           "resolution": "0.001C" if s_["fine_rate_spec_C"] else "0.00625C"}
        if len(e) == 2:
            out["P9"] = {**e, "held": bool(e["21700"]["e"] < 0.05 and e["4680"]["e"] > 0.05)}
        if pset != "ORegan2022":
            # a bracket has no verdict of its own (predictions_stage5.md): record whether the rule's condition is met
            for v in out.values():
                if "held" in v:
                    v["condition_met"] = v.pop("held")
        sc[key] = out
    sc["note"] = ("Verdicts are under the registered choices (ORegan2022, PyBaMM's default mesh of 20 points along each "
                  "particle's radius). After the predictions it was found that this mesh does not resolve ORegan2022's "
                  "solid diffusion, so every ORegan2022 reading belongs to that mesh; Chen2020 settles at it (DECISIONS.md "
                  "D35, results/stage5_posthoc_mesh.json). The Chen2020 brackets carry no verdict of their own: "
                  "condition_met records whether the rule's condition holds under Chen2020.")
    return sc


def paper_numbers(rows_d, rows_s, rows_c, rows_l):
    """The paper's statements (D27) beside this study's numbers, for the note and README (context only: the paper's
    numbers come from its own parameters and properties)."""
    out = {"paper": {"energy_overestimate_3C_25C": 0.0345, "overestimate_2C_m5C": 0.1132,
                     "energy_overestimate_4680_2C_m5C": 0.1145, "4680_unit_rates_C": [1.25, 2.75],
                     "m5C_2C_end_Ah_multi_single_read_from_Fig4d": [1.34, 1.50],
                     "source": "Yang, Cui and Tartakovsky, J. Electrochem. Soc. 173 (2026) 050520, pp. 3 and 4"},
           "this_study": {}}
    for case in RN.DISCHARGE_CASES:
        for pset in SETS:
            for heat in HEATS:
                for label in LABELS:
                    d = find(rows_d, case=case, set=pset, heat=heat, kernel=label)
                    sh = find(rows_s, case=case, set=pset, heat=heat, kernel=label)
                    if not d:
                        continue
                    key = f"{case}|{pset}|{heat}|{label}"
                    run = SC.load_run(RN.run_name("C", case, "radial" if d["identical_to_radial"] else label, pset, heat,
                                                  False, S5.G_REG))
                    sha = run["I"] / run["meta"]["I_app_A"]
                    rate = d["rate_C"]
                    out["this_study"][key] = {
                        "penalty_energy": d["penalty_energy"], "penalty_capacity": d["penalty_capacity"],
                        "Q_coupled_Ah": d["Q_coupled_Ah"], "Q_single_Ah": d["Q_single_Ah"],
                        "t_cut_coupled_s": d["t_cut_coupled_s"], "spread_tavg": sh["spread_tavg"] if sh else None,
                        "group_rate_range_C": [float(rate * sha.min()), float(rate * sha.max())],
                        "reversal_s": sh["reversal_s"] if sh else None}
    lim = {}
    for r in rows_l:
        lim[f"{r['cell']}|{r['set']}|{r['T_amb_C']:g}C|{r['kernel']}|{r['model']}"] = r["rate_spec_C"]
    out["plating_limited_rate_spec_C"] = lim
    out["specification_limits_spec_C"] = {"0 to 25 C": 0.3, "25 to 45 C": 0.7}
    mar = {}
    for r in rows_c:
        mar[f"{r['cell']}|{r['case']}|{r['set']}|{r['kernel']}|{r['model']}"] = r["margin_V"]
    out["margin_V"] = mar
    return out


def summary_md(rows_d, rows_s, rows_c, rows_l, sc):
    """Markdown tables of the readings under both sets, for the README (every number from the files above)."""
    pc = lambda v, d=2: "" if v is None else f"{100 * v:+.{d}f}"
    cname = lambda case: CASE_TICK[case].replace(chr(10), ", ")
    L = ["Discharge, two-way heat. Penalty: the single-unit model's energy to 2.5 V over the coupled model's, less one. "
         "Spread: the time-averaged share spread; against resolved: its relative error.", "",
         "| Case | Kernel | ORegan2022: penalty (%) | cut-off, coupled (s) | spread (%) | against resolved | "
         "Chen2020: penalty (%) | cut-off, coupled (s) | spread (%) | against resolved | innermost share below 1 from (s) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for case in RN.DISCHARGE_CASES:
        for label in LABELS:
            cells = []
            for pset, dp in (("ORegan2022", 2), ("Chen2020", 3)):
                d = find(rows_d, case=case, set=pset, heat="two-way", kernel=label)
                sh = find(rows_s, case=case, set=pset, heat="two-way", kernel=label)
                if not d:
                    cells += ["", "", "", ""]
                    continue
                err = sh.get("spread_rel_error") if sh else None
                cells += [pc(d["penalty_energy"], dp), f"{d['t_cut_coupled_s']:.0f}",
                          f"{100 * sh['spread_tavg']:.2f}" if sh else "",
                          "" if (err is None or label == "resolved") else f"{100 * err:+.1f} %"]
            shc = find(rows_s, case=case, set="Chen2020", heat="two-way", kernel=label)
            rev = "" if not shc or shc.get("reversal_s") is None else f"{shc['reversal_s']:.0f}"
            if any(cells):
                L.append(f"| {cname(case)} | {NAME[label]} | " + " | ".join(cells) + f" | {rev} |")
    L += ["", "Stage 4's proxy (C3), one-way heat: the coupled time-averaged spread beside Stage 4's proxy and the proxy "
          "over the coupled run's own window (units; groups).", "",
          "| Case | Kernel | ORegan2022: coupled (%) | Stage 4 proxy (%) | proxy, run's window (%) | "
          "Chen2020: coupled (%) | Stage 4 proxy (%) | proxy, run's window (%) |", "|---|---|---|---|---|---|---|---|"]
    for case in RN.DISCHARGE_CASES:
        for label in LABELS:
            cells = []
            for pset in SETS:
                sh = find(rows_s, case=case, set=pset, heat="one-way", kernel=label)
                if not sh or "proxy_window_group_spread" not in sh:
                    cells += ["", "", ""]
                    continue
                p4 = sh.get("proxy_stage4_spread")
                cells += [f"{100 * sh['spread_tavg']:.2f}", "" if p4 is None else f"{100 * p4:.2f}",
                          f"{100 * sh['proxy_window_unit_spread']:.2f}; {100 * sh['proxy_window_group_spread']:.2f}"]
            if any(cells):
                L.append(f"| {cname(case)} | {NAME[label]} | " + " | ".join(cells) + " |")
    L += ["", "Charge, two-way heat: the smallest margin (mV) and the group that holds it (1 innermost, 15 outermost).", "",
          "| Cell | Charge | Kernel | ORegan2022: coupled | single-unit | Chen2020: coupled | single-unit |",
          "|---|---|---|---|---|---|---|"]
    for cell in ("21700", "4680"):
        for case, (rate, Ta, reg) in RN.CHARGE_CASES.items():
            for label in LABELS:
                cells = []
                for pset in SETS:
                    a = find(rows_c, cell=cell, case=case, set=pset, kernel=label, model="coupled")
                    b = find(rows_c, cell=cell, case=case, set=pset, kernel=label, model="single")
                    cells += ["" if not a else f"{1e3 * a['margin_V']:+.2f} (group {a['group']})",
                              "" if not b else f"{1e3 * b['margin_V']:+.2f}"]
                if any(cells):
                    lab = f"{rate:g}C at {Ta:g} C" + ("" if reg else ", outside the specification")
                    L.append(f"| {'M50' if cell == '21700' else '4680'} | {lab} | {NAME[label]} | " + " | ".join(cells) + " |")
    L += ["", "Plating-limited rate (specification's C, 4.85 A in the M50), two-way heat: the largest passing rate "
          "(the fine search's where there is one).", "",
          "| Cell | Ambient (C) | Kernel | ORegan2022: single-unit | coupled | Chen2020: single-unit | coupled |",
          "|---|---|---|---|---|---|---|"]
    for cell in ("21700", "4680"):
        for Ta in (0.0, 10.0, 25.0):
            for label in LABELS:
                v = [find(rows_l, cell=cell, set=ps, T_amb_C=Ta, kernel=label, model=m)
                     for ps in SETS for m in ("single", "coupled")]
                f = lambda r: "" if not r or r["rate_spec_C"] is None else (
                    f"{r['fine_rate_spec_C']:.4f}" if r.get("fine_rate_spec_C") else f"{r['rate_spec_C']:.4f}")
                L.append(f"| {'M50' if cell == '21700' else '4680'} | {Ta:g} | {NAME[label]} | " +
                         " | ".join(f(x) for x in v) + " |")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------------------------
# the figure
# ---------------------------------------------------------------------------------------------------------------
COL = {"resolved": "#eb6834", "radial": "#52514e", "corrected": "#6250d6"}      # Stage 4's colours
NAME = {"resolved": "resolved cell", "radial": "radial model", "corrected": "end-corrected"}
CASE_TICK = {"21700_b_m5C_2C": "M50\n2C, -5 C\ncooled", "21700_b_p25C_2C": "M50\n2C, 25 C\ncooled",
             "21700_b_p25C_1.25C": "M50\n1.25C, 25 C\ncooled", "21700_a_m5C_2C": "M50\n2C, -5 C\ninsul.",
             "4680_b_m5C_2C": "4680\n2C, -5 C\ncooled", "21700_b_p25C_3C": "M50\n3C, 25 C\ncooled"}


PAPER_PENALTY = {"21700_b_p25C_3C": 3.45, "21700_b_m5C_2C": 11.32, "4680_b_m5C_2C": 11.45}   # % (D27; context)


def posthoc_rates():
    """The post hoc single-cell rates with 80 points per particle radius under ORegan2022 (D35), if present."""
    p = os.path.join(R, "stage5_posthoc_mesh.json")
    if not os.path.exists(p):
        return None
    r = json.load(open(p))["results"].get("ORegan2022", {}).get("80", {}).get("plating_limited_rate_at_ambient")
    return None if not r else [(float(T), v["rate_spec_C"]) for T, v in r.items() if v.get("rate_spec_C")]


def figure(rows_d, rows_s, rows_l):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "legend.fontsize": 6.0, "xtick.labelsize": 6.5,
                         "ytick.labelsize": 6.5, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.linewidth": 0.6})
    fig, ax = plt.subplots(2, 2, figsize=(7.4, 6.0))
    # (a) the kernels: uniform-heat step response of the innermost and outermost groups, main grid
    a = ax[0, 0]
    for label in ("resolved", "radial"):
        k = kernel_for("21700_b_m5C_2C", label)
        t = k.dt * np.arange(1, k.K + 1)
        S = k.S_group.sum(axis=2) * 1e5                       # K per 100 kW/m3
        a.plot(t, S[:, 0], color=COL[label], lw=1.4, label=f"{NAME[label]}, innermost group")
        a.plot(t, S[:, -1], color=COL[label], lw=1.1, ls="--", label=f"{NAME[label]}, outermost group")
    a.set_xlim(0, 1200)
    a.set_xlabel("time since the heat was switched on (s)")
    a.set_ylabel("temperature rise (K per 100 kW/m$^3$)")
    a.set_title("(a) Kernel, M50, ends cooled: rise under uniform heat", loc="left")
    a.legend(frameon=False, loc="lower right")
    # (b) the shares over time in the main case, one-way heat (the proxy's heat), under Chen2020, which settles at the
    # registered mesh (D35); the proxy's group-level shares (Stage 4's procedure, temperatures averaged over the run)
    b = ax[0, 1]
    pset_b = "Chen2020"
    for label in LABELS:
        n = RN.run_name("C", "21700_b_m5C_2C", label, pset_b, "one-way", False, S5.G_REG)
        if not exists(n):
            continue
        r = SC.load_run(n)
        sh = r["I"] / r["meta"]["I_app_A"]
        b.plot(r["t"], 100 * sh[:, 0], color=COL[label], lw=1.3, label=NAME[label])
        b.plot(r["t"], 100 * sh[:, -1], color=COL[label], lw=1.1, ls="--")
    n = RN.run_name("C", "21700_b_m5C_2C", "resolved", pset_b, "one-way", False, S5.G_REG)
    if exists(n):
        r = SC.load_run(n)
        k = kernel_for("21700_b_m5C_2C", "resolved")
        q = S5.registered_heat_on_grid("m5C_2C")
        Tu = np.vstack([np.full(k.N, -5.0), -5.0 + S5.conv_series(k.S_unit_uniform[:, :, None],
                                                                  k.S_inf_unit_uniform[:, None], q)])
        Tg = Tu @ S5.unit_to_group_matrix(k.N, k.G).T
        _, sp_ = proxy_spread(window_average(Tg, k.dt, float(r["t"][-1]), -5.0), k.W, rt_table(pset_b))
        tl = float(r["t"][-1])
        for j, v in enumerate((sp_[0], sp_[-1])):
            b.plot([0.0, tl], [100 * v] * 2, color="#0b0b0b", lw=0.8, ls=":",
                   label="proxy (Stage 4), resolved cell" if j == 0 else None)
    b.axhline(100, color="#0b0b0b", lw=0.5)
    lo_, hi_ = b.get_ylim()
    b.set_ylim(lo_ - 1.6 * (hi_ - lo_) / 3.0, hi_ + 0.1 * (hi_ - lo_))
    b.text(0.02, 0.97, "innermost group (solid)", transform=b.transAxes, fontsize=5.6, va="top")
    b.text(0.02, 0.385, "outermost group (dashed)", transform=b.transAxes, fontsize=5.6, va="top")
    b.set_xlabel("time (s)")
    b.set_ylabel("group current density, % of the cell mean")
    b.set_title("(b) Shares, M50, 2C, -5 C, one-way heat, Chen2020", loc="left")
    b.legend(frameon=False, loc="lower left", ncol=1, fontsize=5.4)
    # (c) the size of the penalty by case, kernel and set, two-way heat, on a log scale: filled where the single-unit
    # model gives more energy (the paper's direction), open where it gives less; the paper's values as ticks
    c = ax[1, 0]
    cases = list(RN.DISCHARGE_CASES)
    x = np.arange(len(cases))
    for i, label in enumerate(LABELS):
        for pset, mk, dx in (("ORegan2022", "o", -0.12), ("Chen2020", "D", 0.12)):
            for j, cs in enumerate(cases):
                r = find(rows_d, case=cs, set=pset, heat="two-way", kernel=label)
                if not r or r.get("identical_to_radial"):
                    continue
                v = 100 * r["penalty_energy"]
                c.plot(x[j] + dx + (i - 1) * 0.07, max(abs(v), 1e-4), ls="none", marker=mk, ms=3.6, mec=COL[label],
                       mew=0.9, mfc=COL[label] if v > 0 else "white")
    for j, cs in enumerate(cases):
        if cs in PAPER_PENALTY:
            c.plot([x[j] - 0.3, x[j] + 0.3], [PAPER_PENALTY[cs]] * 2, color="#0b0b0b", lw=1.2)
    c.set_yscale("log")
    c.set_ylim(5e-5, 5e3)                              # the top two decades hold the legend, above every value
    c.set_xticks(x, [CASE_TICK[k] for k in cases])
    c.set_ylabel("|single-unit energy over coupled, less one| (%)")
    c.set_title("(c) Multi-unit penalty, two-way heat", loc="left")
    hc1 = [Line2D([], [], color=COL[lb], marker="o", ls="none", ms=3.6, label=NAME[lb]) for lb in LABELS]
    hc2 = [Line2D([], [], color="#52514e", marker="o", ls="none", ms=3.6, mfc="white", label="ORegan2022 (registered)"),
           Line2D([], [], color="#52514e", marker="o", ls="none", ms=3.6, label="filled: single-unit gives more"),
           Line2D([], [], color="#52514e", marker="D", ls="none", ms=3.4, mfc="white", label="Chen2020"),
           Line2D([], [], color="#0b0b0b", lw=1.2, label="the paper's values")]
    lg = c.legend(handles=hc1, frameon=False, loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=3, fontsize=5.2,
                  handletextpad=0.2, columnspacing=1.0)
    c.add_artist(lg)
    c.legend(handles=hc2, frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.925), ncol=2, fontsize=5.2,
             handletextpad=0.2, columnspacing=1.0)
    # (d) the plating-limited rate against ambient, both cells and sets
    d = ax[1, 1]
    for pset, ls_c in (("Chen2020", "-"), ("ORegan2022", "--")):
        for cell, mk in (("21700", "o"), ("4680", "s")):
            for label in LABELS:
                for model in ("coupled", "single"):
                    pts = []
                    for Ta in (0.0, 10.0, 25.0):
                        r = find(rows_l, cell=cell, set=pset, T_amb_C=Ta, kernel=label, model=model)
                        if r and r["rate_spec_C"] is not None:
                            pts.append((Ta, r["fine_rate_spec_C"] or r["rate_spec_C"]))
                    if pts:
                        xs, ys = zip(*pts)
                        d.plot(xs, ys, color=COL[label], ls=ls_c, marker=mk, ms=3.0 if model == "coupled" else 3.4,
                               mfc=COL[label] if model == "coupled" else "white", lw=1.1 if model == "coupled" else 0.6)
    ph = posthoc_rates()
    if ph:
        xs, ys = zip(*sorted(ph))
        d.plot(xs, ys, color="#0b0b0b", ls="none", marker="^", ms=4.0, mfc="white", mew=0.9)
    d.step([0, 25, 45], [0.3, 0.7, 0.7], where="post", color="#0b0b0b", lw=0.8)
    d.annotate("specification's maximum continuous charge", (5.0, 0.29), fontsize=5.5, va="top")
    d.set_xlim(-1, 27)
    d.set_ylim(0.2, 1.3)
    d.set_xlabel("ambient temperature (C)")
    d.set_ylabel("plating-limited rate (specification's C, 4.85 A)")
    d.set_title("(d) Plating-limited rate, two-way heat", loc="left")
    hd = [Line2D([], [], color=COL[lb], lw=1.2, label=NAME[lb]) for lb in LABELS]
    hd += [Line2D([], [], color="#52514e", ls="-", lw=1.0, label="Chen2020"),
           Line2D([], [], color="#52514e", ls="--", lw=1.0, label="ORegan2022 (registered, 20 points)"),
           Line2D([], [], color="#52514e", ls="-", marker="o", lw=1.1, ms=3.0, label="coupled (filled)"),
           Line2D([], [], color="#52514e", ls="-", marker="o", mfc="white", lw=0.6, ms=3.4, label="single-unit (open)"),
           Line2D([], [], color="#52514e", marker="o", ls="none", ms=3.0, label="M50"),
           Line2D([], [], color="#52514e", marker="s", ls="none", ms=3.0, label="4680"),
           Line2D([], [], color="#0b0b0b", marker="^", ls="none", ms=4.0, mfc="white",
                  label="ORegan2022, 80 points, one cell\nat the ambient (post hoc)")]
    d.legend(handles=hd, frameon=False, loc="upper left", ncol=2, fontsize=5.0)
    for a_ in ax.ravel():
        a_.grid(True, color="#e6e5e1", lw=0.5)
        a_.set_axisbelow(True)
    fig.tight_layout(pad=0.4, w_pad=0.9, h_pad=1.0)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(R, f"stage5_figure.{ext}"), dpi=300)
    plt.close(fig)


def main():
    P1 = p1()
    json.dump(P1, open(os.path.join(R, "stage5_p1.json"), "w"), indent=1)
    rows_d, rows_s = discharge_tables()
    rows_c = charge_tables()
    rows_l = limit_table()
    write_csv(os.path.join(R, "stage5_discharge.csv"), rows_d)
    write_csv(os.path.join(R, "stage5_shares.csv"), rows_s)
    write_csv(os.path.join(R, "stage5_charge.csv"), rows_c)
    write_csv(os.path.join(R, "stage5_limit.csv"), rows_l)
    sc = scorecard(rows_d, rows_s, rows_c, rows_l, P1)
    json.dump(sc, open(os.path.join(R, "stage5_scorecard.json"), "w"), indent=1)
    json.dump(paper_numbers(rows_d, rows_s, rows_c, rows_l), open(os.path.join(R, "stage5_paper_numbers.json"), "w"),
              indent=1)
    figure(rows_d, rows_s, rows_l)
    with open(os.path.join(R, "stage5_summary.md"), "w") as f:
        f.write(summary_md(rows_d, rows_s, rows_c, rows_l, sc))
    print(json.dumps(sc, indent=1))


if __name__ == "__main__":
    main()
