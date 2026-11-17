#!/usr/bin/env python3
"""Independent read, phase 2: each statement and count of DECISIONS.md D35 against the files, with my own code.
Reads results/ and my own outputs out/readings.json and out/v2_v4.json (run ir_readings.py and ir_v2_v4.py first).
Each item records D35's words or numbers, the value from the files, and whether they agree at D35's precision.
-> out/d35.json"""
import glob
import json
import math
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402

ITEMS = []


def item(topic, claim, value, ok, note=None, borderline=False):
    """borderline: true at D35's stated figure (one significant figure) but over it as a strict bound"""
    ITEMS.append({"topic": topic, "claim": claim, "files": value, "agrees": bool(ok), "borderline": bool(borderline),
                  **({"note": note} if note else {})})


def r_ok(x, quoted, decimals):
    """x rounded to `decimals` equals the quoted figure"""
    return round(x, decimals) == round(quoted, decimals) and abs(round(x, decimals) - quoted) < 10 ** (-decimals) / 2


def d35_text():
    s = open(os.path.join(L.ROOT, "DECISIONS.md")).read()
    i = s.index("D35.")
    return s[i:]


# ------------------------------------------------------------------------------------------------------------
def mesh():
    R = json.load(open(os.path.join(L.RES, "stage5_posthoc_mesh.json")))["results"]
    O, Ch = R["ORegan2022"], R["Chen2020"]
    # discharges
    quoted = {"20": 978, "40": 1282, "80": 1456, "160": 1469}
    for n, q in quoted.items():
        x = O[n]["discharge_2C_25C"]["t_cut_s"]
        item("mesh", f"ORegan2022 2C, 25 C ends at {q:,} s with {n} points", round(x, 4), round(x) == q,
             None if round(x) == q else f"{x:.4f} s rounds to {round(x):,} s")
    for n, q in {"20": 126, "40": 121, "80": 141, "160": 186, "320": 247}.items():
        x = O[n]["discharge_2C_m5C"]["t_cut_s"]
        item("mesh", f"ORegan2022 2C, -5 C ends at {q} s with {n} points", round(x, 4), round(x) == q)
    # margins and charges at 20 points
    for key, q, qQ in (("charge_1455mA_0C", -193.6, 3.14), ("charge_3395mA_25C", -237.3, 2.84)):
        m, Q = 1e3 * O["20"][key]["margin_min_V"], O["20"][key]["charge_Ah"]
        item("mesh", f"20 points, {key}: margin {q} mV, charge stops at {qQ} A h", [round(m, 4), round(Q, 4)],
             r_ok(m, q, 1) and r_ok(Q, qQ, 2))
    # 40 points or more
    for key, lo, hi in (("charge_1455mA_0C", 19.1, 19.7), ("charge_3395mA_25C", 27.4, 28.6)):
        ms = [1e3 * O[n][key]["margin_min_V"] for n in ("40", "80", "160")]
        item("mesh", f"40+ points, {key}: margin +{lo} to +{hi} mV", [round(v, 4) for v in ms],
             r_ok(min(ms), lo, 1) and r_ok(max(ms), hi, 1))
    Qs = {f"{key}|{n}": O[n][key]["charge_Ah"] for key in ("charge_1455mA_0C", "charge_3395mA_25C") for n in ("40", "80", "160")}
    okQ = all(r_ok(v, 4.30, 2) for v in Qs.values())
    item("mesh", "40+ points: 4.30 A h charged", {k: round(v, 4) for k, v in Qs.items()}, okQ,
         None if okQ else "the 0.7C, 25 C charge with 40 points stores {:.4f} A h, which rounds to {:.2f}".format(
             Qs["charge_3395mA_25C|40"], Qs["charge_3395mA_25C|40"]))
    for n, qs in (("20", (0.280, 0.369, 0.536)), ("40", (0.405, 0.618, 1.024)), ("80", (0.430, 0.670, 1.228))):
        xs = [O[n]["plating_limited_rate_at_ambient"][T]["rate_spec_C"] for T in ("0", "10", "25")]
        item("mesh", f"ORegan2022 rates at the ambient with {n} points: {qs}", [round(v, 5) for v in xs],
             all(r_ok(x, q, 3) for x, q in zip(xs, qs)))
    # Chen2020 settles
    for key in ("discharge_2C_m5C", "discharge_2C_25C"):
        ts = {n: Ch[n][key]["t_cut_s"] for n in Ch if key in Ch[n]}
        spread = max(ts.values()) - min(ts.values())
        item("mesh", f"Chen2020 {key} within 0.2 s over the meshes", {"spread_s": round(spread, 4), **{n: round(v, 4) for n, v in ts.items()}},
             round(spread, 1) <= 0.2, None if spread <= 0.2 else f"the spread is {spread:.4f} s (20 against the finest mesh), 0.2 s to one figure",
             borderline=spread > 0.2)
    for key, q in (("charge_1455mA_0C", -1.51), ("charge_3395mA_25C", 0.48)):
        ms = {n: 1e3 * Ch[n][key]["margin_min_V"] for n in Ch if key in Ch[n]}
        spread = max(ms.values()) - min(ms.values())
        item("mesh", f"Chen2020 {key}: {q:+.2f} mV at 20 points, within 0.01 mV over the meshes",
             {"spread_mV": round(spread, 5), **{n: round(v, 5) for n, v in ms.items()}},
             r_ok(ms["20"], q, 2) and round(spread, 2) <= 0.01,
             None if spread <= 0.01 else f"the spread is {spread:.4f} mV (20 against 160 points), 0.01 mV to one figure",
             borderline=spread > 0.01)
    rates = {n: [Ch[n]["plating_limited_rate_at_ambient"][T]["rate_spec_C"] for T in ("0", "10", "25")]
             for n in Ch if "plating_limited_rate_at_ambient" in Ch[n]}
    spread = max(max(v[i] for v in rates.values()) - min(v[i] for v in rates.values()) for i in range(3))
    item("mesh", "Chen2020 rates within 0.001C over the meshes: 0.288, 0.431, 0.706 at 20 points",
         {"largest_spread_C": round(spread, 6), **{n: [round(x, 5) for x in v] for n, v in rates.items()}},
         spread <= 0.001 and all(r_ok(x, q, 3) for x, q in zip(rates["20"], (0.288, 0.431, 0.706))))
    # pulse resistances
    ch = {}
    for ps in ("ORegan2022", "Chen2020"):
        for T in ("-5", "0", "25"):
            ch[f"{ps}|{T}"] = R[ps]["160"]["pulse_R_ohm"][T] / R[ps]["20"]["pulse_R_ohm"][T] - 1
    lo, hi = min(ch.values()), max(ch.values())
    item("mesh", "pulse resistances move by 3 to 5 % between 20 and 160 points", {k: round(100 * v, 3) for k, v in ch.items()},
         round(100 * lo) >= 3 and round(100 * hi) <= 5,
         None if 100 * hi <= 5.0 else f"the range is {100 * lo:.2f} to {100 * hi:.2f} % (Chen2020 at 25 C moves by {100 * ch['Chen2020|25']:.2f} %)",
         borderline=100 * hi > 5.0)
    for ps, q20, q160, qch in (("ORegan2022", 0.02423, 0.02427, 0.2), ("Chen2020", 0.01121, 0.01072, 4.0)):
        a = math.log(R[ps]["20"]["pulse_R_ohm"]["-5"] / R[ps]["20"]["pulse_R_ohm"]["25"]) / 30.0
        b = math.log(R[ps]["160"]["pulse_R_ohm"]["-5"] / R[ps]["160"]["pulse_R_ohm"]["25"]) / 30.0
        c = 100 * abs(b / a - 1)
        item("mesh", f"{ps}: |d ln R/dT| between -5 and 25 C {q20} (20 points) and {q160} (160), a {qch:g} % move",
             [round(a, 8), round(b, 8), round(c, 3)], r_ok(a, q20, 5) and r_ok(b, q160, 5) and round(c) == round(qch),
             f"|d ln R/dT| = {a:.8f} and {b:.8f} per K, which round to {a:.5f} and {b:.5f}; the move is {c:.2f} %; "
             "d ln R/dT itself is negative (R falls as T rises), and D35 quotes its magnitude")


def diffusivity():
    import pybamm
    p = pybamm.ParameterValues("ORegan2022")
    D = p["Negative particle diffusivity [m2.s-1]"]
    ev = lambda s, T=298.15: float(D(pybamm.Scalar(s), pybamm.Scalar(T)).evaluate())
    d98, d80, d9842 = ev(0.98), ev(0.80), ev(0.9841951106298638)
    item("diffusivity", "ORegan2022 graphite diffusivity at 25 C: 1.4e-13 m2/s at a stoichiometry of 0.98", f"{d98:.4e}",
         r_ok(d98 * 1e13, 1.4, 1), f"1.4e-13 is the value at 0.9842 (the 100 % stoichiometry of D27): {d9842:.4e}")
    item("diffusivity", "2.8e-16 m2/s at 0.80", f"{d80:.4e}", r_ok(d80 * 1e16, 2.8, 1))
    s = np.linspace(0.02956238686388328, 0.9841951106298638, 4001)
    v = np.array([ev(x) for x in s])
    item("diffusivity", "varies about 500-fold with stoichiometry at 25 C",
         {"ratio_0.98_to_0.80": round(d98 / d80, 1), "ratio_0.9842_to_0.80": round(d9842 / d80, 1),
          "max_over_min_on_the_window_0.0296_to_0.9842": round(float(v.max() / v.min()), 1)},
         400 <= v.max() / v.min() <= 650, "about 500-fold holds on the window and for 0.9842 against 0.80; 0.98 against 0.80 gives 354")
    c = pybamm.ParameterValues("Chen2020")["Negative particle diffusivity [m2.s-1]"]
    item("diffusivity", "Chen2020's diffusivity is constant", repr(c), isinstance(c, (int, float)))


# ------------------------------------------------------------------------------------------------------------
def storage_machine():
    p1 = json.load(open(os.path.join(L.OUT, "p1_v1.json")))["P1"]
    item("storage", "the kernels agree with Stage 4's histories within 9.5e-7 K (P1)", p1["max_abs_K"], r_ok(p1["max_abs_K"] * 1e7, 9.5, 1))
    lim = None
    for f in glob.glob("/sys/fs/cgroup/memory/process_api/*/claude-code-bash/memory.limit_in_bytes"):
        lim = int(open(f).read())
    item("machine", "a memory limit of 6.27 GB shared by all jobs, two cores", {"limit_bytes": lim, "cores": os.cpu_count()},
         lim is not None and round(lim / 1e9, 2) == 6.27 and os.cpu_count() == 2,
         "read from this machine's cgroup now; the two-hour job limit is not in any file")
    rec = {}
    for f in sorted(glob.glob(os.path.join(L.KDIR, "resolved_*4680*.json")) + glob.glob(os.path.join(L.KDIR, "resolved_b_21700_*G30.json"))):
        m = json.load(open(f))
        rec[os.path.basename(f)[:-5]] = {"resumed_from_checkpoint": m.get("resumed_from_checkpoint"), "peak_memory_GB": m.get("peak_memory_GB")}
    item("machine", "the 4680's main-grid resolved kernel resumed from its saved state (at step 1,600); its factorisation needs about 5.5 GB (D28)",
         rec, rec.get("resolved_b_4680_m5C_2C_G15", {}).get("resumed_from_checkpoint") is True,
         "the files record the resume but not its step; the 4680 kernel jobs record a peak of {:.2f} GB, below D28's 5.5 GB".format(
             rec.get("resolved_b_4680_m5C_2C_G15", {}).get("peak_memory_GB") or float("nan")))


def store():
    tot = cache = 0
    srch = []
    for p in sorted(glob.glob(os.path.join(L.RDIR, "limit_*C.json"))):
        d = json.load(open(p))
        for k, v in d.items():
            c = sum(1 for t in v["trials"] if t.get("from_cache"))
            tot += len(v["trials"])
            cache += c
            if c:
                srch.append(f"{os.path.basename(p)[6:-5]}|{k}: {c} of {len(v['trials'])}")
    item("store", "the searches record which trials came from the store: 17 of 700", {"stored": cache, "trials": tot}, cache == 17 and tot == 700)
    item("store", "three of the four jobs run again were searches that resumed from their stored trials", srch, len(srch) == 3,
         "the files show which searches hold stored trials; the restarts themselves are not recorded")


def hold_rule():
    rd = json.load(open(os.path.join(L.OUT, "readings.json")))
    runs = {}
    for r in rd["discharge"]:
        case, pset, heat, label = r["key"].split("|")
        if heat != "one-way":
            continue
        lab_run = "radial" if (case == "21700_a_m5C_2C" and label == "corrected") else label
        for model, k in (("coupled", "held_steps_coupled"), ("single", "held_steps_single")):
            if r[k] > 0:
                runs[f"{case}|{pset}|{lab_run}|{model}"] = r[k]
    chen = {k: v for k, v in runs.items() if "Chen2020" in k}
    ore = {k: v for k, v in runs.items() if "ORegan2022" in k}
    item("hold rule", "acted in 15 runs: 12 Chen2020 for 1 to 7 steps, 3 ORegan2022 at 3C, 25 C for 47 to 59 steps", runs,
         len(runs) == 15 and len(chen) == 12 and min(chen.values()) == 1 and max(chen.values()) == 7 and len(ore) == 3
         and min(ore.values()) == 47 and max(ore.values()) == 59 and all("p25C_3C" in k for k in ore))
    expect = {"21700_b_m5C_2C|radial", "21700_a_m5C_2C|radial", "21700_a_m5C_2C|resolved", "4680_b_m5C_2C|radial",
              "4680_b_m5C_2C|resolved", "4680_b_m5C_2C|corrected"}
    got = {"|".join([k.split("|")[0], k.split("|")[2]]) for k in chen}
    item("hold rule", "Chen2020: the M50's main case (radial), its insulated case (radial, resolved), the 4680 (all three)",
         sorted(got), got == expect)
    got_o = sorted(k for k in ore)
    item("hold rule", "ORegan2022 at 3C, 25 C: coupled and single-unit under the radial kernel, coupled under the end-corrected",
         got_o, set(got_o) == {"21700_b_p25C_3C|ORegan2022|radial|coupled", "21700_b_p25C_3C|ORegan2022|radial|single",
                               "21700_b_p25C_3C|ORegan2022|corrected|coupled"})
    te = L.grid("p25C_3C")[2]
    item("hold rule", "those discharges ran past the 558 s of the registered heat", round(te, 3), round(te) == 558)
    # each one-way run is also checked for one-step-of-about-1-s
    dt = L.grid("m5C_2C")[0]
    item("hold rule", "steps of about 1 s", round(dt, 6), abs(dt - 1) < 0.01)


def balance_and_checks():
    rd = json.load(open(os.path.join(L.OUT, "readings.json")))
    v3 = rd["V3_current_balance"]
    item("current balance", "across every stored coupled run the largest residual is 5.7e-10 of I_app", v3,
         r_ok(v3["max_rel_residual"] * 1e10, 5.7, 1))
    v = json.load(open(os.path.join(L.OUT, "v2_v4.json")))
    h = v["V3"]["halved_step_discharge"]["readings"]
    fails = {k: round(100 * r["rel_change"], 3) for k, r in h.items() if not r["within"]}
    item("checks", "V3: the halved step moves the main case's penalties under the radial and end-corrected kernels by 1.1 to 1.3 %",
         fails, set(fails) == {"penalty_energy|radial", "penalty_capacity|radial", "penalty_energy|corrected", "penalty_capacity|corrected"}
         and round(min(abs(x) for x in fails.values()), 1) >= 1.1 and round(max(abs(x) for x in fails.values()), 1) <= 1.3)
    en = v["V3"].get("energies_halved_step", {})
    worst_e = max([abs(d["energy"]) for d in en.values()] or [float("nan")])
    worst_q = max([abs(d["capacity"]) for d in en.values()] or [float("nan")])
    item("checks", "the energies behind them move by at most 0.13 %", en, round(100 * worst_e, 2) <= 0.13,
         f"largest move of an energy {100 * worst_e:.4f} %; the capacities behind the two capacity penalties move by up to "
         f"{100 * worst_q:.4f} %")
    g = v["V4"]["doubled_groups_discharge"]["readings"]
    sp = {k: round(100 * r["rel_change"], 3) for k, r in g.items() if k.startswith("spread")}
    fails = {k: x for k, x in sp.items() if abs(x) >= 5}
    item("checks", "V4: 30 groups move five of the six spreads by 5.1 to 5.4 %, the sixth by 4.8 %", sp,
         len(fails) == 5 and round(min(fails.values()), 1) >= 5.1 and round(max(fails.values()), 1) <= 5.4
         and any(round(x, 1) == 4.8 for x in sp.values()) and all(r["within"] for k, r in g.items() if not k.startswith("spread")))
    item("checks", "close to the 4.8 % that D28 found for the group-level proxy", round(100 * (5.535 / 5.279 - 1), 2),
         round(100 * (5.535 / 5.279 - 1), 1) == 4.8, "from D28's spreads, 5.279 % with 15 groups and 5.535 % with 30")


def ripple():
    """Detrend by a local cubic over +-15 outputs; the period is the median spacing of the upward zero crossings of the
    detrended signal between 60 and 140 s (the regular part of the ripple; it lengthens near the cut-off)."""
    def period(t, y):
        t = np.asarray(t, float)
        y = np.asarray(y, float)
        n, h = len(y), 15
        r = np.full(n, np.nan)
        for i in range(h, n - h):
            a, b = i - h, i + h + 1
            r[i] = y[i] - np.polyfit(t[a:b] - t[i], y[a:b], 3)[-1]
        sel = (t >= 60) & (t <= 140) & np.isfinite(r)
        tt, rr = t[sel], r[sel]
        up = [tt[i] - rr[i] * (tt[i + 1] - tt[i]) / (rr[i + 1] - rr[i]) for i in range(len(rr) - 1) if rr[i] < 0 <= rr[i + 1]]
        per = np.diff(up)
        return (round(float(np.median(per)), 1) if len(per) else None), (len(per)), float(np.nanstd(rr)) if len(rr) else None
    out = {}
    for pset in ("ORegan2022", "Chen2020"):
        for heat in ("two-way", "one-way"):
            for model in ("coupled", "single"):
                r = L.load_run(L.run_file("C", "21700_b_m5C_2C", "resolved", pset, heat, model == "single"))
                t, V = r["t"][:-1], r["V"][:-1]
                pv, nv, sv = period(t, V)
                rec = {"V_period_s": pv, "V_cycles": nv, "V_rms_mV_60_140s": None if sv is None else round(1e3 * sv, 4)}
                if model == "coupled":
                    ps_, ns_, ss = period(t, r["I"][:-1, 0] / r["meta"]["I_app_A"])
                    rec.update({"inner_share_period_s": ps_, "inner_share_rms_60_140s": ss})
                out[f"{pset}|{heat}|{model}"] = rec
    o = {k: v for k, v in out.items() if k.startswith("ORegan")}
    periods = [v[x] for v in o.values() for x in ("V_period_s", "inner_share_period_s") if v.get(x)]
    ok = (len(periods) == 6 and all(9.5 <= p_ <= 12.5 for p_ in periods)
          and all(out[f"Chen2020|{h}|{m}"]["V_rms_mV_60_140s"] < 0.05 * o[f"ORegan2022|{h}|{m}"]["V_rms_mV_60_140s"]
                  for h in ("two-way", "one-way") for m in ("coupled", "single")))
    item("ripple", "under ORegan2022 at -5 C the shares and the voltage ripple with a period of about 11 s; the single-unit "
         "model's voltage shows the same ripple", out, ok,
         "main case, resolved kernel; median spacing of upward zero crossings of the detrended signal between 60 and 140 s; "
         "the ripple lengthens to about 14 s near the cut-off; Chen2020 shows none")


def three_c():
    out = {}
    for heat in ("two-way", "one-way"):
        for lab in ("radial", "resolved", "corrected"):
            for model in ("coupled", "single"):
                r = L.load_run(L.run_file("C", "21700_b_p25C_3C", lab, "ORegan2022", heat, model == "single"))
                k = int(round(270.0 / r["meta"]["dt"]))
                out[f"{heat}|{lab}|{model}"] = {"t_cut_s": round(float(r["t"][-1]), 2),
                                                "T_g1_at_270s_C": round(float(r["T"][k, 0]), 4) if k < len(r["t"]) else None}
    d2 = out["two-way|corrected|coupled"]["T_g1_at_270s_C"] - out["two-way|resolved|coupled"]["T_g1_at_270s_C"]
    # the fields of the registered heat (one-way) at 270 s, from my own convolution
    q = L.heat_on_grid("p25C_3C")
    dtg = L.grid("p25C_3C")[0]
    k = int(round(270.0 / dtg))
    T = {}
    for lab in ("resolved", "corrected"):
        kk = L.load_kernel(L.kernel_file(lab, "b", "21700", "p25C_3C"), keys=("S_group", "S_inf_group"))
        rise = L.conv(kk["S_group"].sum(axis=2), kk["S_inf_group"].sum(axis=1), q[:k])
        T[lab] = 25.0 + rise[-1, 0]
    d1 = T["corrected"] - T["resolved"]
    item("3C at 25 C", "the end-corrected field's innermost group is 0.2 K warmer than the resolved field's at 270 s",
         {"registered_heat_field_K": round(d1, 4), "two-way_coupled_runs_K": round(d2, 4)}, round(d1, 1) == 0.2 and round(d2, 1) == 0.2)
    item("3C at 25 C", "the coupled discharge under the end-corrected kernel runs to 604 s; its single-unit model and both models "
         "under the resolved kernel stop near 280 s", out,
         round(out["two-way|corrected|coupled"]["t_cut_s"]) == 604 and all(abs(out[f"two-way|{a}"]["t_cut_s"] - 280) < 5 for a in
                                                                           ("corrected|single", "resolved|coupled", "resolved|single")),
         "two-way heat (registered); under one-way heat the same split, the end-corrected coupled run to 605 s")


def searches():
    cut, tiny = [], []
    for p in sorted(glob.glob(os.path.join(L.RDIR, "limit_*C.json"))):
        d = json.load(open(p))
        base = os.path.basename(p)[6:-5]
        for k, v in d.items():
            for t in v["trials"]:
                if not t["passed"] and str(t["status"]).startswith("event"):
                    cut.append({"search": f"{base}|{k}", "rate": t["rate"], "margin_mV": 1e3 * t["min_margin_V"],
                                "at_cut_off": t["t_min_s"] == t["t_end_s"]})
                if t["passed"] and "Chen2020" in base and t["min_margin_V"] < 1e-4:
                    tiny.append({"search": f"{base}|{k}", "rate": t["rate"], "margin_uV": round(1e6 * t["min_margin_V"], 2)})
    o = [c for c in cut if "ORegan2022" in c["search"]]
    c = [c for c in cut if "Chen2020" in c["search"]]
    item("searches", "in 25 failed trials the margin first goes below zero at the 4.2 V cut-off: 20 ORegan2022 at the barrier, "
         "5 Chen2020 between -0.1 mV and zero", {"n": len(cut), "ORegan2022": len(o), "Chen2020": len(c),
                                                "ORegan2022_margin_mV_range": [round(min(x["margin_mV"] for x in o), 2), round(max(x["margin_mV"] for x in o), 2)],
                                                "Chen2020_margins_mV": sorted(round(x["margin_mV"], 4) for x in c)},
         len(cut) == 25 and len(o) == 20 and len(c) == 5 and all(-0.1 < x["margin_mV"] < 0 for x in c) and all(x["at_cut_off"] for x in cut))
    tiny.sort(key=lambda x: x["margin_uV"])
    few = [x for x in tiny if x["margin_uV"] < 10]
    item("searches", "some passing Chen2020 trials clear zero by a few microvolts", tiny, len(few) >= 1,
         f"{len(few)} passing trial clears zero by under 10 microvolts ({few[0]['margin_uV'] if few else None}); the next "
         f"smallest clear it by {tiny[len(few)]['margin_uV'] if len(tiny) > len(few) else None} microvolts or more")
    # the non-monotonic example
    d = json.load(open(os.path.join(L.RDIR, "limit_21700_ORegan2022_0C.json")))["resolved|coupled"]
    pick = {f"{t['rate']:.6f}": {"margin_mV": 1e3 * t["min_margin_V"], "status": t["status"], "t_min_s": t["t_min_s"],
                                 "t_end_s": t["t_end_s"], "group": t["group"]} for t in d["trials"] if abs(t["rate"] - 0.28625) < 1e-6 or abs(t["rate"] - 0.283125) < 2e-6}
    inv = []
    for p in sorted(glob.glob(os.path.join(L.RDIR, "limit_*C.json"))):
        for k, v in json.load(open(p)).items():
            P = [t["rate"] for t in v["trials"] if t["passed"]]
            F = [t["rate"] for t in v["trials"] if not t["passed"]]
            if P and F and min(F) < max(P):
                inv.append(f"{os.path.basename(p)}|{k}")
    vals_ok = (round(pick.get("0.286250", {}).get("margin_mV", 9), 2) == -0.03
               and round(pick.get("0.283125", pick.get("0.283130", {})).get("margin_mV", 9), 2) == -3.66)
    # like-for-like evidence: passing trials run to 4.2 V, so their recorded margin is the smallest over the charge
    rises = []
    for p in sorted(glob.glob(os.path.join(L.RDIR, "limit_*C.json"))):
        for k, v in json.load(open(p)).items():
            P = sorted((t["rate"], t["min_margin_V"]) for t in v["trials"] if t["passed"])
            rises += [{"search": f"{os.path.basename(p)[6:-5]}|{k}", "rates": [a[0], b[0]],
                       "margins_mV": [round(1e3 * a[1], 4), round(1e3 * b[1], 4)]} for a, b in zip(P, P[1:]) if b[1] > a[1] + 1e-9]
    scanf = os.path.join(L.OUT, "single_rerun_scan.json")
    scan = json.load(open(scanf))["single_unit_margin_scan"] if os.path.exists(scanf) else None
    item("searches", "under ORegan2022 near the plating-limited rate the margin is not monotonic in the rate; D32 took "
         "monotonicity as given", {"passing_trials_whose_margin_rises_with_rate": rises,
                                   "my_single_unit_scan_rises": None if scan is None else scan["rises"],
                                   "searches_with_a_failing_rate_below_a_passing_one": inv},
         bool(rises) or bool(scan and scan["rises"]),
         "holds: the smallest margin over a full charge rises with rate in two stored searches and in my scan of the M50's "
         "single-unit model at 0 C; the pass or fail outcome stays monotonic in every search")
    item("searches", "D35's example: at 0 C in the M50's coupled search, minus 0.03 mV at 0.28625C and minus 3.66 mV at 0.283125C",
         {"trials": pick}, False,
         "the two values are as stored, but each is the first output below zero of a trial that D32's rule stopped there; its "
         "depth depends on where the crossing falls within the 10 s step and it is not the trial's smallest margin over a "
         "charge, so the pair does not show the non-monotonicity" if vals_ok else "the values differ from D35")
    sc = json.load(open(os.path.join(L.RES, "stage5_scorecard.json")))["brackets_Chen2020"]["P9"]
    item("scorecard", "P9's Chen2020 bracket is read at the searches' 0.00625C", sc,
         all(sc[c]["resolution"] == "0.00625C" for c in ("21700", "4680")) and "condition_met" in sc)


def figure_and_readings():
    src = open(os.path.join(L.ROOT, "src", "stage5_report.py")).read()
    m = re.search(r'pset_b = "(\w+)"', src)
    item("figure", "panel (b) shows the main case's shares under Chen2020", m.group(1) if m else None, bool(m and m.group(1) == "Chen2020"),
         "from the figure code's set for panel (b); the image is checked by eye in the README")
    rd = json.load(open(os.path.join(L.OUT, "readings.json")))
    ok_rt = rd["n_mismatches"] == 0
    item("readings", "C3's like-for-like proxy uses the run's own set's R(T)", "my recomputation with each run's own set reproduces "
         "every proxy column of results/stage5_shares.csv", ok_rt)
    revs = [v for v in rd["discharge_run_checks"].values()]
    same9 = all(v["reversal_tol1e-9"] == next(r for r in rd["shares"] if r["key"] == k)["reversal_s"]
                for k, v in rd["discharge_run_checks"].items())
    spurious = sorted(k for k, v in rd["discharge_run_checks"].items() if v["reversal_tol0"] is not None and v["reversal_tol0"] < 1.0)
    item("readings", "the reversal's 'having risen above 1' is read as above 1 + 1e-12, so that round-off (about 2e-16) does not count",
         {"tolerance_1e-9_gives_the_same_reading_everywhere": same9, "runs_with_a_false_reversal_at_zero_tolerance": spurious,
          "largest_deviation_of_the_shares_from_1_at_t0": max(v["shares_at_t0_max_dev"] for v in revs)}, same9)
    p1 = json.load(open(os.path.join(L.OUT, "p1_v1.json")))
    g30 = {k: v["edges_match"] for k, v in p1["V1_kernel_files"]["kernels"].items() if k.endswith("G30")}
    item("readings", "with 30 groups the edges 45 k / 30 fall halfway for odd k and are rounded up", g30, all(g30.values()))
    v5 = json.load(open(os.path.join(L.OUT, "v5_v6.json")))["V5"]
    item("readings", "V5: shares within 0.037 %, voltages up to 6.5 mV apart at the last full step",
         {"max_rel_share_difference": v5["max_rel_share_difference"], "max_abs_dV_V": v5["max_abs_voltage_difference_V"],
          "t_of_max_s": v5["t_of_max_voltage_difference_s"]},
         r_ok(100 * v5["max_rel_share_difference"], 0.037, 3) and r_ok(1e3 * v5["max_abs_voltage_difference_V"], 6.5, 1))


def consequences_and_records():
    import subprocess
    R = json.load(open(os.path.join(L.RES, "stage5_posthoc_mesh.json")))["results"]["ORegan2022"]
    heat_end = {"25": L.grid("p25C_2C")[2], "-5": L.grid("m5C_2C")[2]}
    ts = {f"{T} C|{n}": R[n][f"discharge_2C_{'25C' if T == '25' else 'm5C'}"]["t_cut_s"] for T in ("25", "-5") for n in R
          if f"discharge_2C_{'25C' if T == '25' else 'm5C'}" in R[n]}
    item("consequences", "the first fact of D27 (ORegan2022 discharges end long before the registered heat) holds in direction "
         "with the finer meshes", {"cut_offs_s": {k: round(v, 1) for k, v in ts.items()}, "registered_heat_ends_s":
                                   {k: round(v, 1) for k, v in heat_end.items()}},
         all(v < heat_end[k.split(" ")[0]] for k, v in ts.items()))
    m = {n: R[n]["charge_1455mA_0C"]["margin_min_V"] for n in ("20", "40", "80", "160")}
    item("consequences", "the second fact of D27 (the surface reaches its limit before 4.2 V at the specification's limits) "
         "belongs to the 20-point mesh", {n: round(1e3 * v, 3) for n, v in m.items()},
         m["20"] < 0 and all(v > 0 for n, v in m.items() if n != "20"))
    log = subprocess.run(["git", "-C", L.ROOT, "log", "-1", "--format=%h %ad", "--date=iso-strict", "--",
                          "results/stage4_hist_1d.json", "results/stage4_hist_3d_21700.json", "results/stage4_hist_3d_4680.json",
                          "results/stage4_errors.csv", "results/stage4_RT.csv", "results/stage4_unit_temps.json"],
                         capture_output=True, text=True).stdout.strip()
    item("records", "Stage 4's files are not edited", log, log.endswith("2026-10-29T04:26:21+00:00") or "2026-10-29" in log,
         "the last commit touching Stage 4's results")
    keys = set()
    for p in glob.glob(os.path.join(L.RDIR, "limit_*C.json")):
        for v in json.load(open(p)).values():
            for t in v["trials"]:
                keys |= set(t)
    item("records", "the searches' trials store their margins and not their step outputs", sorted(keys),
         "min_margin_V" in keys and not ({"V", "I", "t", "resid"} & keys))
    src = open(os.path.join(L.ROOT, "src", "stage5_common.py")).read()
    item("records", "the runs read the stored (single-precision) kernels and do all arithmetic in double precision",
         "Kernel loads S_group, S_unit_uniform and S_unit with .astype(np.float64)",
         'z["S_group"].astype(np.float64)' in src and 'z["S_unit_uniform"].astype(np.float64)' in src, "from the code")
    srcs = open(os.path.join(L.ROOT, "src", "stage5_coupled.py")).read() + open(os.path.join(L.ROOT, "src", "stage5_kernels.py")).read()
    item("records", "runs and kernels are written to a temporary file and renamed", "save_run and the kernel writer use a .tmp "
         "file and os.replace", srcs.count("os.replace(tmp, path)") >= 2, "from the code")
    cp = open(os.path.join(L.ROOT, "src", "stage5_coupled.py")).read()
    item("records", "the coupled model under ORegan2022 with a finer mesh was not run", "the coupled and single-unit models are "
         "built on PyBaMM's default mesh only", "default_var_pts" in cp and "r_n" not in cp, "from the code: no other mesh is built")


if __name__ == "__main__":
    for f in (mesh, diffusivity, storage_machine, store, hold_rule, balance_and_checks, ripple, three_c, searches, figure_and_readings,
              consequences_and_records):
        try:
            f()
        except Exception as e:                                   # a failure of my own check is recorded, not hidden
            item(f.__name__, "(check could not run)", repr(e), False)
    res = {"items": ITEMS, "n": len(ITEMS), "n_agree": sum(1 for i in ITEMS if i["agrees"]),
           "borderline": [i for i in ITEMS if i["borderline"]],
           "disagree": [i for i in ITEMS if not i["agrees"]], "peak_memory": L.mem_note()}
    L.dump("d35.json", res)
    for i in ITEMS:
        tag = "DIFF " if not i["agrees"] else ("EDGE " if i["borderline"] else "ok   ")
        print(tag + f"[{i['topic']}] {i['claim'][:110]}" + (f"\n        note: {i['note'][:300]}" if i.get("note") and (not i["agrees"] or i["borderline"]) else ""))
    print(f"{res['n_agree']} of {res['n']} agree")
