#!/usr/bin/env python3
"""Independent read, items 2 to 5: every reading of results/stage5_discharge.csv, stage5_shares.csv,
stage5_charge.csv and stage5_limit.csv recomputed from the run histories and the search records; C3's proxy; P6;
and the scorecard against the rules of predictions_stage5.md. Also, for every stored run, the coupling rule of D30
(the temperature held over each step from the convolution of the heat recorded at the earlier steps, or from the
registered heat) and the current balance (V3's first part).
-> out/readings.json (and out/readings_mismatches.json, the list of stored values not reproduced)"""
import glob
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402

T0 = time.time()
RTOL_MATCH = 2e-7          # the CSVs are written with 9 significant digits
MISMATCH = []
_KCACHE = {}


def kernel(path):
    if path not in _KCACHE:
        if len(_KCACHE) > 6:
            _KCACHE.clear()
        _KCACHE[path] = L.load_kernel(path, keys=("S_group", "S_inf_group", "S_unit_uniform", "S_inf_unit_uniform"))
    return _KCACHE[path]


def same(a, b, rtol=RTOL_MATCH, atol=1e-12):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, str) or isinstance(b, str):
        return str(a) == str(b)
    return abs(a - b) <= rtol * max(abs(a), abs(b)) + atol


def compare_row(table, key, mine, stored, skip=()):
    """Compare my values with the stored CSV row; return the number of columns compared."""
    if stored is None:
        MISMATCH.append({"table": table, "key": key, "column": "(row)", "mine": "present", "stored": "missing"})
        return 0
    n = 0
    for c, v in mine.items():
        if c in skip:
            continue
        if c not in stored:
            MISMATCH.append({"table": table, "key": key, "column": c, "mine": v, "stored": "(no column)"})
            continue
        s = L.fnum(stored[c])
        if isinstance(v, (bool, np.bool_)):
            ok = (s is True or s == "True" or s == 1.0) == bool(v)
        elif isinstance(v, str):
            ok = str(stored[c]) == v
        elif isinstance(v, int) and not isinstance(v, bool):
            ok = s is not None and abs(float(s) - v) < 1e-9
        else:
            ok = same(None if v is None else float(v), None if s is None else float(s))
        n += 1
        if not ok:
            MISMATCH.append({"table": table, "key": key, "column": c, "mine": v, "stored": stored[c]})
    return n


def find(rows, **kw):
    out = [r for r in rows if all(str(r.get(k)) == str(v) for k, v in kw.items())]
    return out[0] if out else None


def findnum(rows, **kw):
    """find with numeric fields compared as numbers"""
    for r in rows:
        ok = True
        for k, v in kw.items():
            x = r.get(k)
            if isinstance(v, float):
                if x in (None, "") or abs(float(x) - v) > 1e-9:
                    ok = False
                    break
            elif str(x) != str(v):
                ok = False
                break
        if ok:
            return r
    return None


# ----------------------------------------------------------------------------------------------------------------
# readings of one run (D31, D32)
# ----------------------------------------------------------------------------------------------------------------
def energy_capacity(run):
    I = abs(run["meta"]["I_app_A"])
    t, V = run["t"].astype(float), run["V"].astype(float)
    return L.trap(V * I, t) / 3600.0, I * float(t[-1]) / 3600.0


def reversal(t, s1, tol):
    up = np.where(s1 > 1.0 + tol)[0]
    if len(up) == 0:
        return None
    i0 = int(up[0])
    dn = np.where(s1[i0 + 1:] < 1.0)[0]
    if len(dn) == 0:
        return None
    j = i0 + 1 + int(dn[0])
    return float(t[j - 1] + (1.0 - s1[j - 1]) * (t[j] - t[j - 1]) / (s1[j] - s1[j - 1]))


def share_readings(run, W):
    t = run["t"].astype(float)
    Iapp = run["meta"]["I_app_A"]
    s = run["I"].astype(float) / Iapp
    spread = s.max(axis=1) - s.min(axis=1)
    sd = np.sqrt((W[None, :] * (s - 1.0) ** 2).sum(axis=1))
    te = float(t[-1])
    s1 = s[:, 0]
    rev12, rev0, rev9 = reversal(t, s1, 1e-12), reversal(t, s1, 0.0), reversal(t, s1, 1e-9)
    imax = int(np.argmax(s1))
    return {"spread_tavg": L.trap(spread, t) / te, "sd_tavg": L.trap(sd, t) / te, "inner_tavg": L.trap(s1, t) / te,
            "outer_tavg": L.trap(s[:, -1], t) / te, "inner_max": float(s1.max()), "t_inner_max_s": float(t[imax]),
            "reversal_s": rev12, "spread_end": float(spread[-1]), "inner_end": float(s1[-1]),
            "outer_end": float(s[-1, -1]),
            "max_current_balance_residual": float(np.abs(s @ W - 1.0).max()),
            "t_cut_s": te}, {"reversal_tol0": rev0, "reversal_tol1e-9": rev9,
                             "shares_at_t0_max_dev": float(np.abs(s[0] - 1).max()),
                             "group_rate_range": [float(s.min()), float(s.max())]}


def margin_readings(run):
    mn = run["margin_nodes_min"].astype(float)
    mi = run["margin_interface"].astype(float)
    both = np.minimum(mn, mi)
    k, g = np.unravel_index(int(np.argmin(both)), both.shape)
    I = abs(run["meta"]["I_app_A"])
    return {"margin_V": float(both[k, g]), "group": int(g) + 1, "t_min_s": float(run["t"][k]),
            "at_interface": bool(mi[k, g] <= mn[k, g]), "t_end_s": float(run["t"][-1]),
            "charge_Ah": I * float(run["t"][-1]) / 3600.0, "status": run["meta"]["status"]}


# ----------------------------------------------------------------------------------------------------------------
# the coupling rule of D30 in a stored run
# ----------------------------------------------------------------------------------------------------------------
def coupling_check(run, kern, Ta, heat, single, oneway_groups=None):
    """The temperature recorded at output k (k >= 1) is the one held over step k: the convolution of the heats
    recorded at the ends of steps 1..k-1 (two-way), or the registered heat's field at step k - 1, held past the
    archive's end (one-way). Returns the largest absolute difference in K and the held-step count."""
    T = run["T"].astype(float)
    n_out = T.shape[0]
    n_steps = n_out - 1
    G = kern["S_group"].shape[1]
    W = L.group_w(kern["meta"]["N"], G)
    if heat == "two-way":
        q = run["q"].astype(float)[1:n_steps]                 # heats at the ends of steps 1..n_steps-1
        if single:
            S = np.einsum("g,kgj->k", W, kern["S_group"].astype(float))
            S_inf = float(W @ kern["S_inf_group"].sum(axis=1))
            rise = L.conv(S, S_inf, q[:, 0]) if len(q) else np.zeros(0)
            mine = np.concatenate([[Ta], Ta + rise])[:, None]
        else:
            rise = L.conv(kern["S_group"], kern["S_inf_group"], q) if len(q) else np.zeros((0, G))
            mine = np.vstack([np.full((1, G), Ta), Ta + rise])
        held = 0
    else:
        n_arch = oneway_groups.shape[0] - 1
        idx = np.minimum(np.arange(0, n_steps), n_arch)
        mine = oneway_groups[idx]
        if single:
            mine = (mine @ W)[:, None]
        held = max(0, n_steps - 1 - n_arch)
    d = np.abs(T[1:] - mine)
    return float(d.max()) if d.size else 0.0, held, float(np.abs(T[0] - Ta).max())


def oneway_groups(kern, Ta, gridname):
    q = L.heat_on_grid(gridname)
    rise = L.conv(kern["S_group"].sum(axis=2), kern["S_inf_group"].sum(axis=1), q)
    return np.vstack([np.full((1, rise.shape[1]), Ta), Ta + rise])


# ----------------------------------------------------------------------------------------------------------------
# Stage 4's proxy (D23, D24) for C3
# ----------------------------------------------------------------------------------------------------------------
RT = L.read_csv(os.path.join(L.RES, "stage4_RT.csv"))
E4 = L.read_csv(os.path.join(L.RES, "stage4_errors.csv"))


def R_of(pset, soc=1.0):
    rows = sorted([r for r in RT if r["set"] == pset and abs(float(r["soc"]) - soc) < 1e-9], key=lambda r: float(r["T_C"]))
    T = np.array([float(r["T_C"]) for r in rows])
    lnR = np.log(np.array([float(r["R_ohm"]) for r in rows]))
    return lambda x: np.exp(np.interp(np.asarray(x, dtype=float), T, lnR)), (float(T.min()), float(T.max()))


def proxy(Tavg, w, Rf):
    g = 1.0 / Rf(Tavg)
    s = g / float(np.sum(w * g))
    return float(s.max() - s.min()), s


def stage4_row(case, field, pset):
    return find(E4, case=case, field=field, set=pset, soc="1", reading="time_average", weighting="area")


# ----------------------------------------------------------------------------------------------------------------
def discharge_part():
    stored_d = L.read_csv(os.path.join(L.RES, "stage5_discharge.csv"))
    stored_s = L.read_csv(os.path.join(L.RES, "stage5_shares.csv"))
    mine_d, mine_s, extra, missing = [], [], {}, []
    for case, (cell, ends, Ta, I, g0) in L.DISCHARGE.items():
        dt, n_arch, t_arch = L.grid(g0)
        N = L.CELL[cell]["N"]
        W = L.group_w(N, 15)
        for pset in L.SETS:
            for heat in L.HEATS:
                per = {}
                for label in L.LABELS:
                    lab_run = "radial" if (ends == "a" and label == "corrected") else label
                    fc = L.run_file("C", case, lab_run, pset, heat, False)
                    fs = L.run_file("C", case, lab_run, pset, heat, True)
                    if not (os.path.exists(fc) and os.path.exists(fs)):
                        missing.append(f"{case}|{pset}|{heat}|{label}")
                        continue
                    rc, rs = L.load_run(fc), L.load_run(fs)
                    kp = L.kernel_file(label, ends, cell, g0)
                    kern = kernel(kp)
                    assert os.path.basename(kp) == rc["meta"]["kernel"] == rs["meta"]["kernel"], (kp, rc["meta"]["kernel"])
                    og = oneway_groups(kern, Ta, g0) if heat == "one-way" else None
                    cc = coupling_check(rc, kern, Ta, heat, False, og)
                    cs = coupling_check(rs, kern, Ta, heat, True, og)
                    Ec, Qc = energy_capacity(rc)
                    Es, Qs = energy_capacity(rs)
                    d = {"E_single_Wh": Es, "E_coupled_Wh": Ec, "penalty_energy": Es / Ec - 1, "Q_single_Ah": Qs,
                         "Q_coupled_Ah": Qc, "penalty_capacity": Qs / Qc - 1, "t_cut_single_s": float(rs["t"][-1]),
                         "t_cut_coupled_s": float(rc["t"][-1]), "held_steps_coupled": cc[1], "held_steps_single": cs[1],
                         "archive_t_end_s": t_arch, "rate_C": I / L.C_STUDY, "T_amb_C": Ta,
                         "identical_to_radial": bool(ends == "a" and label == "corrected")}
                    sh, sx = share_readings(rc, W)
                    if heat == "one-way":
                        f4 = "corrected" if label == "corrected" else "radial"
                        p4 = stage4_row(case, f4, pset)
                        if p4 is not None:
                            sh["proxy_stage4_spread"] = float(p4["share_spread_resolved"] if label == "resolved" else p4["share_spread"])
                        ku = L.load_kernel(kp, keys=("S_unit_uniform", "S_inf_unit_uniform"))
                        q = L.heat_on_grid(g0)
                        Tu = np.vstack([np.full((1, N), Ta), Ta + L.conv(ku["S_unit_uniform"], ku["S_inf_unit_uniform"], q)])
                        Tg = Tu @ L.unit_to_group(N, 15).T
                        times = dt * np.arange(Tu.shape[0])
                        tc = float(rc["t"][-1])
                        Tu_avg = L.pwl_average(times, Tu, tc)
                        Tg_avg = L.pwl_average(times, Tg, tc)
                        Rf, rng = R_of(pset)
                        sh["proxy_window_unit_spread"] = proxy(Tu_avg, L.unit_w(N), Rf)[0]
                        sh["proxy_window_group_spread"] = proxy(Tg_avg, W, Rf)[0]
                        sh["T_mean_window_C"] = float(L.unit_w(N) @ Tu_avg)
                        sh["T_spread_units_window_K"] = float(Tu_avg.max() - Tu_avg.min())
                        sx["proxy_window_with_ORegan2022_RT"] = {"unit": proxy(Tu_avg, L.unit_w(N), R_of("ORegan2022")[0])[0],
                                                                 "group": proxy(Tg_avg, W, R_of("ORegan2022")[0])[0]}
                        sx["window_T_range_C"] = [float(Tu_avg.min()), float(Tu_avg.max())]
                        sx["RT_table_range_C"] = rng
                    # run-level checks beyond the CSVs
                    sx.update({"coupled_T_rule_max_abs_K": cc[0], "single_T_rule_max_abs_K": cs[0],
                               "coupled_T0_dev": cc[2], "status_coupled": rc["meta"]["status"],
                               "status_single": rs["meta"]["status"],
                               "V_end_coupled": float(rc["V"][-1]), "V_end_single": float(rs["V"][-1]),
                               "grid_ok_coupled": bool(np.abs(rc["t"][:-1] - dt * np.arange(len(rc["t"]) - 1)).max() < 1e-9
                                                       and rc["t"][-1] <= dt * (len(rc["t"]) - 1) + 1e-9),
                               "grid_ok_single": bool(np.abs(rs["t"][:-1] - dt * np.arange(len(rs["t"]) - 1)).max() < 1e-9),
                               "meta_held_coupled": rc["meta"]["held_steps_past_archive"],
                               "meta_held_single": rs["meta"]["held_steps_past_archive"],
                               "W_meta_ok": bool(np.abs(np.array(rc["meta"]["W"]) - W).max() < 1e-15)})
                    per[label] = (d, sh, sx)
                ref = per.get("resolved")
                for label, (d, sh, sx) in per.items():
                    if ref:
                        d0, s0, _ = ref
                        d["penalty_energy_minus_resolved_pp"] = 100 * (d["penalty_energy"] - d0["penalty_energy"])
                        d["penalty_energy_rel_error"] = d["penalty_energy"] / d0["penalty_energy"] - 1 if d0["penalty_energy"] else None
                        sh["spread_rel_error"] = sh["spread_tavg"] / s0["spread_tavg"] - 1
                        sh["inner_error_pp"] = 100 * (sh["inner_tavg"] - s0["inner_tavg"])
                        sh["outer_error_pp"] = 100 * (sh["outer_tavg"] - s0["outer_tavg"])
                        sh["reversal_error_s"] = (sh["reversal_s"] - s0["reversal_s"]) if (sh["reversal_s"] is not None and s0["reversal_s"] is not None) else None
                    key = f"{case}|{pset}|{heat}|{label}"
                    rowd = find(stored_d, case=case, set=pset, heat=heat, kernel=label)
                    rows = find(stored_s, case=case, set=pset, heat=heat, kernel=label)
                    nd = compare_row("stage5_discharge.csv", key, d, rowd)
                    ns = compare_row("stage5_shares.csv", key, sh, rows)
                    mine_d.append({"key": key, **d})
                    mine_s.append({"key": key, **sh})
                    extra[key] = {**sx, "columns_compared": nd + ns}
    # stored rows that I did not produce
    keys_mine = {r["key"] for r in mine_d}
    for r in stored_d:
        k = f"{r['case']}|{r['set']}|{r['heat']}|{r['kernel']}"
        if k not in keys_mine:
            MISMATCH.append({"table": "stage5_discharge.csv", "key": k, "column": "(row)", "mine": "missing", "stored": "present"})
    return mine_d, mine_s, extra, missing


def charge_part():
    stored = L.read_csv(os.path.join(L.RES, "stage5_charge.csv"))
    mine, extra, missing = [], {}, []
    for cell in ("21700", "4680"):
        N = L.CELL[cell]["N"]
        W = L.group_w(N, 15)
        for pset in L.SETS:
            for case, (rate, Ta, reg) in L.CHARGE.items():
                per = {}
                for label in L.LABELS:
                    kp = L.kernel_file(label, "b", cell, "charge10")
                    for single in (False, True):
                        f = L.run_file("D", f"{cell}_{case}", label, pset, "two-way", single)
                        if not os.path.exists(f):
                            missing.append(f"{cell}|{case}|{pset}|{label}|{'single' if single else 'coupled'}")
                            continue
                        r = L.load_run(f)
                        kern = kernel(kp)
                        assert os.path.basename(kp) == r["meta"]["kernel"]
                        cr = coupling_check(r, kern, Ta, "two-way", single)
                        m = margin_readings(r)
                        Ws = np.array([1.0]) if single else W
                        res = float(np.abs((r["I"].astype(float) @ Ws) / r["meta"]["I_app_A"] - 1).max())
                        row = {**m, "max_current_balance_residual": res, "rate_spec_C": rate,
                               "current_A_M50": rate * L.C_SPEC, "T_amb_C": Ta, "within_specification": reg}
                        ok_I = abs(r["meta"]["I_app_A"] + rate * L.C_SPEC) < 1e-12
                        per[(label, single)] = row
                        extra[f"{cell}|{case}|{pset}|{label}|{'single' if single else 'coupled'}"] = {
                            "T_rule_max_abs_K": cr[0], "I_app_is_minus_rate_times_4.85A": bool(ok_I),
                            "V_end": float(r["V"][-1]), "status": r["meta"]["status"],
                            "n_outputs": int(len(r["t"]))}
                for (label, single), row in per.items():
                    ref = per.get(("resolved", single))
                    if ref:
                        row["margin_minus_resolved_mV"] = 1e3 * (row["margin_V"] - ref["margin_V"])
                    model = "single" if single else "coupled"
                    key = f"{cell}|{case}|{pset}|{label}|{model}"
                    st = find(stored, cell=cell, case=case, set=pset, kernel=label, model=model)
                    compare_row("stage5_charge.csv", key, row, st)
                    mine.append({"key": key, **row})
    keys_mine = {r["key"] for r in mine}
    for r in stored:
        k = f"{r['cell']}|{r['case']}|{r['set']}|{r['kernel']}|{r['model']}"
        if k not in keys_mine:
            MISMATCH.append({"table": "stage5_charge.csv", "key": k, "column": "(row)", "mine": "missing", "stored": "present"})
    return mine, extra, missing


# ----------------------------------------------------------------------------------------------------------------
# D32's search, replayed on the stored trials
# ----------------------------------------------------------------------------------------------------------------
def replay(trials, start, fine):
    """Follow D32's rules, asking the stored trials for each outcome. Returns the sequence of rates the rules ask
    for, the readings, and any rate the rules ask for that the record lacks."""
    tab = [(float(t["rate"]), bool(t["passed"])) for t in trials]

    def outcome(r):
        for x, p in tab:
            if abs(x - r) < 2e-6:
                return p
        raise KeyError(r)
    seq = []

    def T(r):
        seq.append(r)
        return outcome(r)
    try:
        r = max(0.05, start)
        if not T(r):
            while True:
                r = r - 0.05
                if r < 0.05 - 1e-12:
                    return {"sequence": seq, "rate": None}
                if T(r):
                    break
        lo = r
        while True:
            hi = lo + 0.05
            if not T(hi):
                break
            lo = hi
        res = {}
        nh = 0
        while True:
            if nh == 3:
                res.update({"rate": lo, "fail_above": hi, "width": hi - lo})
                if not fine:
                    break
            if hi - lo <= 0.001 + 1e-12:
                break
            mid = 0.5 * (lo + hi)
            if T(mid):
                lo = mid
            else:
                hi = mid
            nh += 1
        if fine:
            res.update({"fine_rate": lo, "fine_fail_above": hi, "fine_width": hi - lo})
        res["sequence"] = seq
        return res
    except KeyError as e:
        return {"sequence": seq, "missing_trial_rate": float(e.args[0])}


def limit_part():
    stored = L.read_csv(os.path.join(L.RES, "stage5_limit.csv"))
    out, mine = {}, []
    for path in sorted(glob.glob(os.path.join(L.RDIR, "limit_*_*C.json"))):
        base = os.path.basename(path)[len("limit_"):-len(".json")]
        cell, pset, Tstr = base.split("_")
        Ta = float(Tstr[:-1])
        d = json.load(open(path))
        for key, v in d.items():
            label, model = key.split("|")
            fine_rule = (Ta == 0.0 and pset == "ORegan2022" and label == "resolved")
            if model == "single":
                start = 0.05
                start_note = "0.05C (D32)"
            else:
                s = d.get(f"{label}|single")
                if s is None:
                    start, start_note = None, "single-unit search absent"
                else:
                    sr = s.get("rate")
                    start = max(0.05, math.floor(round((sr - 0.10) * 100, 9)) / 100) if sr else 0.05
                    start_note = f"single-unit rate {sr} less 0.10C, rounded down to 0.01C, at least 0.05C"
            trials = v["trials"]
            # each trial's verdict from its own record: passes when it reached 4.2 V with the margin never below 0
            trial_ok = all(bool(t["passed"]) == (str(t["status"]).startswith("event") and t["min_margin_V"] >= 0.0) for t in trials)
            neg_stop = all((t["status"] == "negative margin") == (t["min_margin_V"] < 0 and not t["passed"]) for t in trials if not t["passed"])
            rp = replay(trials, start, fine_rule) if start is not None else {"sequence": []}
            seq_stored = [float(t["rate"]) for t in trials]
            seq_ok = len(rp["sequence"]) == len(seq_stored) and all(abs(a - b) < 2e-6 for a, b in zip(rp["sequence"], seq_stored))
            rec = {"cell": cell, "set": pset, "T_amb_C": Ta, "kernel": label, "model": model, "start_rule": start,
                   "start_stored": v.get("start"), "start_note": start_note, "fine_by_rule": fine_rule,
                   "fine_stored": v.get("fine"), "n_trials": len(trials), "sequence_follows_rules": bool(seq_ok),
                   "trial_verdicts_consistent": bool(trial_ok), "failed_trials_stopped_on_negative_margin": bool(neg_stop),
                   "replay": {k: rp.get(k) for k in ("rate", "fail_above", "width", "fine_rate", "fine_fail_above", "missing_trial_rate")},
                   "stored": {k: v.get(k) for k in ("rate", "fail_above", "width", "fine_rate", "fine_fail_above")},
                   "from_cache_trials": int(sum(1 for t in trials if t.get("from_cache"))),
                   "kernel_file": v.get("kernel")}
            ok = seq_ok and all(same(rp.get(k), v.get(k), rtol=1e-9, atol=1e-9) for k in ("rate", "fail_above", "width"))
            if fine_rule:
                ok = ok and all(same(rp.get(k), v.get(k), rtol=1e-9, atol=1e-9) for k in ("fine_rate", "fine_fail_above"))
            ok = ok and same(start, v.get("start"), rtol=1e-12, atol=1e-12) and bool(v.get("fine")) == fine_rule
            rec["all_consistent"] = bool(ok and trial_ok)
            if not rec["all_consistent"]:
                MISMATCH.append({"table": "limit json", "key": f"{cell}|{pset}|{Ta:g}|{key}", "column": "search",
                                 "mine": rec["replay"], "stored": rec["stored"]})
            # the CSV row
            row = {"rate_spec_C": rp.get("rate"), "fails_at_spec_C": rp.get("fail_above"),
                   "bracket_width_C": rp.get("width"), "fine_rate_spec_C": rp.get("fine_rate"),
                   "fine_fails_at_spec_C": rp.get("fine_fail_above"), "n_trials": len(trials), "start_spec_C": start,
                   "rate_A_M50": rp["rate"] * L.C_SPEC if rp.get("rate") else None}
            st = findnum(stored, cell=cell, set=pset, T_amb_C=Ta, kernel=label, model=model)
            ck = f"{cell}|{pset}|{Ta:g}|{label}|{model}"
            compare_row("stage5_limit.csv", ck, row, st)
            out[ck] = rec
            mine.append({"key": ck, **row})
    keys_mine = {r["key"] for r in mine}
    for r in stored:
        k = f"{r['cell']}|{r['set']}|{float(r['T_amb_C']):g}|{r['kernel']}|{r['model']}"
        if k not in keys_mine:
            MISMATCH.append({"table": "stage5_limit.csv", "key": k, "column": "(row)", "mine": "missing", "stored": "present"})
    return out, mine


# ----------------------------------------------------------------------------------------------------------------
# P6 (predictions_stage5.md)
# ----------------------------------------------------------------------------------------------------------------
def p6(pset):
    case = "21700_b_m5C_2C"
    cell, ends, Ta, I, g0 = L.DISCHARGE[case]
    f = L.run_file("C", case, "resolved", pset, "two-way", False)
    if not os.path.exists(f):
        return None
    run = L.load_run(f)
    k = L.load_kernel(L.kernel_file("resolved", "b", cell, g0), keys=("S_unit", "S_inf_unit", "S_unit_uniform", "S_inf_unit_uniform"))
    dt = k["meta"]["dt"]
    N = k["meta"]["N"]
    W = L.group_w(N, 15)
    t = run["t"].astype(float)
    nfull = len(t) - 1 if abs(t[-1] - dt * (len(t) - 1)) < 1e-9 else len(t) - 2      # complete steps
    q = run["q"].astype(float)[1:nfull + 1]                    # heats at the ends of the complete steps
    T_own = np.vstack([np.full((1, N), Ta), Ta + L.conv(k["S_unit"], k["S_inf_unit"], q)])
    T_uni = np.vstack([np.full((1, N), Ta), Ta + L.conv(k["S_unit_uniform"], k["S_inf_unit_uniform"], q @ W)])
    times = dt * np.arange(nfull + 1)
    sp_own = T_own.max(axis=1) - T_own.min(axis=1)
    sp_uni = T_uni.max(axis=1) - T_uni.min(axis=1)
    te = float(t[-1])
    # over the run's discharge [0, t_cut]; the field at t_cut (inside the last, partial step) taken as its value at
    # the last complete step (the heat of the partial step is not in the convolution) -- and, as a sensitivity,
    # the time average over the complete steps only
    a = L.pwl_average(times, sp_own, te) if te > times[-1] + 1e-9 else L.trap(sp_own, times) / te
    b = L.pwl_average(times, sp_uni, te) if te > times[-1] + 1e-9 else L.trap(sp_uni, times) / te
    a2, b2 = L.trap(sp_own, times) / times[-1], L.trap(sp_uni, times) / times[-1]
    return {"spread_per_group_heat_K": a, "spread_uniform_heat_K": b, "ratio_minus_1": a / b - 1,
            "held": bool(abs(a / b - 1) < 0.10), "steps": int(nfull), "t_cut_s": te,
            "sensitivity_complete_steps_only_ratio_minus_1": a2 / b2 - 1}


# ----------------------------------------------------------------------------------------------------------------
def scorecard(md, ms, mc, ml, P1):
    get = lambda rows, key: next((r for r in rows if r["key"] == key), None)
    sc = {}
    for pset in L.SETS:
        o = {}
        if pset == "ORegan2022" and P1 is not None:
            o["P1"] = {"max_abs_K": P1["max_abs_K"], "held": P1["held"]}
        a = get(ms, f"21700_b_m5C_2C|{pset}|one-way|radial")
        b = get(ms, f"21700_b_m5C_2C|{pset}|one-way|resolved")
        if a and b:
            x = a["spread_tavg"] / b["spread_tavg"] - 1
            o["P2"] = {"radial_over_resolved_minus_1": x, "held": bool(0.25 <= x <= 0.45)}
            # Stage 4's registered proxy spread of the main case (resolved field), from results/stage4_errors.csv;
            # predictions_stage5.md names 0.0554168 (ORegan2022) and 2.538 % (Chen2020)
            ref = float(stage4_row("21700_b_m5C_2C", "radial", pset)["share_spread_resolved"])
            named = 0.0554168 if pset == "ORegan2022" else 0.02538
            y = b["spread_tavg"] / ref - 1
            o["P3"] = {"coupled_spread": b["spread_tavg"], "proxy": ref, "ratio_minus_1": y, "held": bool(-0.20 <= y <= 0.20),
                       "proxy_equals_value_named_in_predictions": bool(abs(ref - named) < (5e-8 if pset == "ORegan2022" else 5e-6))}
        a = get(md, f"21700_b_m5C_2C|{pset}|two-way|radial")
        b = get(md, f"21700_b_m5C_2C|{pset}|two-way|resolved")
        if a and b:
            o["P4"] = {"penalty_radial": a["penalty_energy"], "penalty_resolved": b["penalty_energy"],
                       "held": bool(a["penalty_energy"] > 0 and b["penalty_energy"] <= 0.8 * a["penalty_energy"])}
        a = get(md, f"4680_b_m5C_2C|{pset}|two-way|radial")
        b = get(md, f"4680_b_m5C_2C|{pset}|two-way|resolved")
        if a and b:
            o["P5"] = {"penalty_radial": a["penalty_energy"], "penalty_resolved": b["penalty_energy"],
                       "ratio": a["penalty_energy"] / b["penalty_energy"] if b["penalty_energy"] else None,
                       "held": bool(a["penalty_energy"] > 0 and a["penalty_energy"] >= 1.5 * b["penalty_energy"])}
        r6 = p6(pset)
        if r6:
            o["P6"] = r6
        diffs = []
        for case in ("0.3C_0C", "0.7C_25C"):
            a = get(mc, f"21700|{case}|{pset}|radial|coupled")
            b = get(mc, f"21700|{case}|{pset}|resolved|coupled")
            if a and b:
                diffs.append(1e3 * (a["margin_V"] - b["margin_V"]))
        if len(diffs) == 2:
            o["P7"] = {"radial_minus_resolved_mV": diffs, "held": bool(all(abs(x) < 2.0 for x in diffs))}
        holders = {}
        for cell in ("21700", "4680"):
            for case in ("0.3C_0C", "0.7C_25C"):
                for lab in L.LABELS:
                    r = get(mc, f"{cell}|{case}|{pset}|{lab}|coupled")
                    if r:
                        holders[f"{cell}|{case}|{lab}"] = r["group"]
        if len(holders) == 12:
            o["P8"] = {"group_holding_minimum": holders, "held": bool(all(v == 15 for v in holders.values()))}
        e = {}
        for cell in ("21700", "4680"):
            s_ = get(ml, f"{cell}|{pset}|0|resolved|single")
            c_ = get(ml, f"{cell}|{pset}|0|resolved|coupled")
            if s_ and c_ and s_["rate_spec_C"] and c_["rate_spec_C"]:
                rs = s_["fine_rate_spec_C"] or s_["rate_spec_C"]
                rc = c_["fine_rate_spec_C"] or c_["rate_spec_C"]
                # the bracket of e from the two searches' brackets
                hs = s_["fine_fails_at_spec_C"] or s_["fails_at_spec_C"]
                hc = c_["fine_fails_at_spec_C"] or c_["fails_at_spec_C"]
                e[cell] = {"single": rs, "coupled": rc, "e": rs / rc - 1, "e_range_from_brackets": [rs / hc - 1, hs / rc - 1]}
        if len(e) == 2:
            o["P9"] = {**e, "held": bool(e["21700"]["e"] < 0.05 and e["4680"]["e"] > 0.05),
                       "verdict_robust_to_bracket": bool((e["21700"]["e_range_from_brackets"][1] < 0.05) ==
                                                         (e["21700"]["e_range_from_brackets"][0] < 0.05) and
                                                         (e["4680"]["e_range_from_brackets"][1] > 0.05) ==
                                                         (e["4680"]["e_range_from_brackets"][0] > 0.05))}
        sc[pset] = o
    # against the stored scorecard
    st = json.load(open(os.path.join(L.RES, "stage5_scorecard.json")))
    comp = {}
    for pset, skey in (("ORegan2022", "registered"), ("Chen2020", "brackets_Chen2020")):
        for P, v in sc[pset].items():
            s = st[skey].get(P)
            vk = "held" if pset == "ORegan2022" else ("condition_met" if "condition_met" in (s or {}) else "held")
            key_note = None if pset == "ORegan2022" else ("bracket recorded as condition_met" if vk == "condition_met"
                                                          else "bracket recorded with a 'held' key (a verdict), not condition_met")
            if s is None:
                comp[f"{pset}|{P}"] = {"mine": v.get("held"), "stored": "absent"}
                continue
            num = {}
            for kk, vv in v.items():
                if isinstance(vv, float) and kk in s:
                    tol = 1e-7 if P == "P1" else 1e-9          # P1: FFT against direct summation of float32 kernels
                    num[kk] = {"mine": vv, "stored": s[kk], "match": same(vv, s[kk], rtol=tol, atol=1e-15)}
            comp[f"{pset}|{P}"] = {"verdict_mine": v.get("held"), "verdict_stored": s.get(vk), "verdict_match": v.get("held") == s.get(vk),
                                   "numbers": num, "stored_key": vk, "key_note": key_note}
            if v.get("held") != s.get(vk) or not all(x["match"] for x in num.values()):
                MISMATCH.append({"table": "stage5_scorecard.json", "key": f"{skey}|{P}", "column": vk, "mine": v, "stored": s})
        for P in st[skey]:
            if P not in sc[pset] and P != "note":
                comp[f"{pset}|{P}"] = {"mine": "not computable from the files present", "stored": st[skey][P]}
    return sc, comp


def v3_residuals():
    worst, name, n = 0.0, None, 0
    for p in sorted(glob.glob(os.path.join(L.RDIR, "*_coupled_G*.npz"))):
        r = L.load_run(p)
        G = r["I"].shape[1]
        W = L.group_w(r["meta"]["N"], G)
        v = float(np.abs((r["I"].astype(float) @ W) / r["meta"]["I_app_A"] - 1).max())
        n += 1
        if v > worst:
            worst, name = v, os.path.basename(p)
    v2 = os.path.join(L.RDIR, "V2_uniform_temperature_coupled.npz")
    return {"coupled_runs_checked": n, "max_rel_residual": worst, "run_of_max": name, "held_1e-6": bool(worst < 1e-6)}


if __name__ == "__main__":
    md, ms, dx, dmiss = discharge_part()
    print("discharge done", f"{time.time() - T0:.0f} s", flush=True)
    mc, cx, cmiss = charge_part()
    print("charge done", f"{time.time() - T0:.0f} s", flush=True)
    lx, ml = limit_part()
    print("limits done", f"{time.time() - T0:.0f} s", flush=True)
    P1 = None
    p1f = os.path.join(L.OUT, "p1_v1.json")
    if os.path.exists(p1f):
        P1 = json.load(open(p1f))["P1"]
    sc, comp = scorecard(md, ms, mc, ml, P1)
    v3 = v3_residuals()
    res = {"discharge": md, "shares": ms, "discharge_run_checks": dx, "discharge_missing": dmiss,
           "charge": mc, "charge_run_checks": cx, "charge_missing": cmiss, "limits": lx, "limit_rows": ml,
           "scorecard_mine": sc, "scorecard_vs_stored": comp, "V3_current_balance": v3,
           "n_mismatches": len(MISMATCH), "wall_s": time.time() - T0, "peak_memory": L.mem_note()}
    L.dump("readings.json", res)
    csv_mtime = os.path.getmtime(os.path.join(L.RES, "stage5_discharge.csv"))
    for m in MISMATCH:
        if m["table"] == "stage5_scorecard.json":
            m["category"] = "scorecard verdict or number"
        elif m["column"] == "(row)":
            m["category"] = "row only in my recomputation (run file newer than the CSV)" if m["mine"] == "present" else "row only in the stored CSV"
        elif m["stored"] == "":
            m["category"] = "stored blank (a run it depends on is newer than the CSV)"
        else:
            m["category"] = "VALUE"
    res["mismatch_categories"] = {}
    for m in MISMATCH:
        res["mismatch_categories"][m["category"]] = res["mismatch_categories"].get(m["category"], 0) + 1
    res["csv_mtime_utc"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(csv_mtime))
    L.dump("readings.json", res)
    L.dump("readings_mismatches.json", MISMATCH)
    # summary
    worstT = max([v["coupled_T_rule_max_abs_K"] for v in dx.values()] + [v["single_T_rule_max_abs_K"] for v in dx.values()]
                 + [v["T_rule_max_abs_K"] for v in cx.values()] + [0.0])
    print(json.dumps({"discharge_rows": len(md), "charge_rows": len(mc), "limit_rows": len(ml),
                      "mismatches": len(MISMATCH), "worst_T_rule_K": worstT, "V3": v3,
                      "limits_all_consistent": all(v["all_consistent"] for v in lx.values()),
                      "scorecard_verdicts_match": {k: v.get("verdict_match") for k, v in comp.items()},
                      "wall_s": res["wall_s"], "peak": res["peak_memory"]}, indent=1, default=str))
    print("mismatch categories:", json.dumps(res["mismatch_categories"]))
    for m in MISMATCH:
        if m["category"] in ("VALUE", "scorecard verdict or number", "row only in the stored CSV"):
            print("MISMATCH", json.dumps(m, default=str)[:600])
