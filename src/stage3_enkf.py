#!/usr/bin/env python3
"""Stage 3: the ensemble Kalman filter of ref. 33 (D19) on Stage 1's radial model (D20), against the resolved cell.
python3 src/stage3_enkf.py checks   -> V1 to V4, results/stage3_checks.json (before the predictions)
python3 src/stage3_enkf.py run      -> Part B: results/stage3_runs_{cell}.json, stage3_sensitivity.json (tables: stage3_report.py)
python3 src/stage3_enkf.py series   -> D21: the P5 and P7 runs again with their per-reading series, results/stage3_series.json"""
import csv
import json
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402
from stage2_correction import Corrected, end_beta  # noqa: E402

N_ENS, SIG_T, SEED, DT_OBS = 3000, 0.1, 20261027, 20.0      # ref. 33: N_ens, sigma_T; D20: seed, interval
RHOC = C.cell_constants("21700")["rho_cp"]
SIG_REF = RHOC * SIG_T / DT_OBS                              # D20: 1.238e4 W/m3
CASES = [("21700", "p25C_1.25C", "a"), ("21700", "p25C_1.25C", "b"), ("21700", "p25C_2C", "a"), ("21700", "p25C_2C", "b"),
         ("21700", "m5C_2C", "a"), ("21700", "m5C_2C", "b"), ("4680", "m5C_2C", "b")]


def truth(cell, cond, bc):
    """Resolved core and mid-length surface temperatures at the archived times (Stage 1 field series)."""
    d = json.load(open(os.path.join(C.RESULTS, "fields", f"{cell}_{bc}_Chen2020_{cond}.json")))
    s, cols = np.array(d["series"]), d["series_columns"]
    return s[:, cols.index("t_s")], s[:, cols.index("T_core_mid")], s[:, cols.index("T_surface_mid")]


def truth_check(cell, cond, bc):
    """V3: the same archive read by a separate routine (row by row, columns by position from the header)."""
    d = json.load(open(os.path.join(C.RESULTS, "fields", f"{cell}_{bc}_Chen2020_{cond}.json")))
    i0, i1, i2 = (d["series_columns"].index(k) for k in ("t_s", "T_core_mid", "T_surface_mid"))
    rows = [(r[i0], r[i1], r[i2]) for r in d["series"]]
    return tuple(np.array([r[j] for r in rows]) for j in range(3))


def enkf(model, heat, Ta, t_obs, y_obs, t_rec, sig_eps, sig_T=SIG_T, n_ens=N_ENS, seed=SEED, assimilate=True, beta_sink=None):
    """Stochastic EnKF with the per-interval error of D19/D20. Returns the ensemble-mean mid-length core at t_rec,
    the learned error per reading (volume-mean posterior source, W/m3) and the end sink on the same history.
    beta_sink: the end sink's beta for that diagnostic (default D18's at h = 400; 0 with the ends insulated, D21)."""
    q, t_end, _ = R1.load_heat(heat)
    n, dt = R1.time_grid(t_end, 1.0)
    N1 = model.N + 1
    d_sink = getattr(model, "d_sink", np.zeros(N1))
    beta = getattr(model, "beta", 0.0)
    gam = beta * model.L ** 2 / (24 * model.k_z) if beta > 0 else 0.0
    lu = spla.splu((model.K + sp.diags(model.C / dt + model.d_conv + d_sink)).tocsc())
    vol_u = np.array([model.U[i] @ np.ones(N1) for i in range(model.n_units)])  # rows of U are normalised
    w_u = np.diff(np.pi * model.unit_edges ** 2)                                # unit volume per unit height
    G = (model.U / vol_u[:, None]).T * w_u                                      # node source per unit source
    rng = np.random.default_rng(seed)
    T = np.full((N1, n_ens), Ta)
    const = (model.d_conv + d_sink) * Ta
    obs_step = {int(round(t / dt)): y for t, y in zip(t_obs, y_obs)}
    rec_step = {int(round(t / dt)): i for i, t in enumerate(t_rec)}
    core = np.full(len(t_rec), np.nan)
    learned, sink = [], []
    draw = lambda: rng.normal(0.0, sig_eps, (model.n_units, n_ens)) if sig_eps > 0 else np.zeros((model.n_units, n_ens))
    eps = draw()
    S = G @ eps
    for k in range(1, n + 1):
        T = lu.solve(model.C[:, None] / dt * T + (const + model.w_vol * q(k * dt))[:, None] + S)
        if assimilate and k in obs_step:
            h = T[-1] + gam * (T[-1] - Ta)
            dh = h - h.mean()
            var = dh @ dh / (n_ens - 1) + sig_T ** 2
            innov = obs_step[k] + sig_T * rng.normal(size=n_ens) - h
            T += np.outer((T - T.mean(1, keepdims=True)) @ dh / (n_ens - 1) / var, innov)
            eps = eps + np.outer((eps - eps.mean(1, keepdims=True)) @ dh / (n_ens - 1) / var, innov)
            Tm = T.mean(1)
            learned.append((k * dt, float(w_u @ eps.mean(1) / w_u.sum())))
            b_sink = model_beta(model) if beta_sink is None else beta_sink
            sink.append((k * dt, float(-b_sink * (model.w_vol @ Tm / model.w_vol.sum() - Ta))))
            eps = draw()
            S = G @ eps
        if k in rec_step:
            c0 = T[0].mean()
            core[rec_step[k]] = c0 + gam * (c0 - Ta)
    return core, learned, sink


def model_beta(model):
    """D18's end sink for the cell at h = 400, the term the end correction carries (used for the comparison)."""
    return end_beta(C.H_PAPER, model.cc["H"], model.cc["k_along"])[0]


def plain(cell, props=None):
    m = R1.Radial1D(cell, props=props)
    m.L, m.k_z = m.cc["H"], m.cc["k_along"]
    return m


def checks():
    out = {}
    heat = "Chen2020_m5C_2C"
    # V2: forecast alone against Stage 1's radial model
    t_rec, _, _ = truth("21700", "m5C_2C", "b")
    r1 = R1.Radial1D("21700").run(*R1.load_heat(heat)[:2], -5.0, snap_times=list(t_rec))
    core_f, _, _ = enkf(plain("21700"), heat, -5.0, [], [], t_rec, 0.0, n_ens=1, assimilate=False)
    ref = np.array([r1["snaps"][t]["T_core"] for t in t_rec])
    out["V2_max_abs_diff_K"] = float(np.max(np.abs(core_f - ref)))
    # V1: truth from the radial model itself, its surface plus noise, estimator with the registered settings
    surf = np.array([r1["snaps"][t]["T_surface"] for t in t_rec])
    rng = np.random.default_rng(SEED)
    sel = np.arange(1, len(t_rec), 2)
    y = surf[sel] + SIG_T * rng.normal(size=len(sel))
    core_e, _, _ = enkf(plain("21700"), heat, -5.0, t_rec[sel], y, t_rec, SIG_REF)
    out["V1_mean_abs_error_K"] = float(np.mean(np.abs(core_e - ref)))
    out["V1_end_error_K"] = float(core_e[-1] - ref[-1])
    # V3: the archive read twice
    a, b = truth("21700", "m5C_2C", "b"), truth_check("21700", "m5C_2C", "b")
    out["V3_identical"] = all(np.array_equal(x, z) for x, z in zip(a, b))
    # V4: same seed twice; sigma_eps = 0 reduces to the forecast
    t_r, c_r, s_r = a
    yb = s_r[sel] + SIG_T * np.random.default_rng(SEED).normal(size=len(sel))
    e1, _, _ = enkf(plain("21700"), heat, -5.0, t_r[sel], yb, t_r, SIG_REF, n_ens=300)
    e2, _, _ = enkf(plain("21700"), heat, -5.0, t_r[sel], yb, t_r, SIG_REF, n_ens=300)
    e0, _, _ = enkf(plain("21700"), heat, -5.0, t_r[sel], yb, t_r, 0.0, n_ens=50)
    out["V4_same_seed_identical"] = bool(np.array_equal(e1, e2))
    out["V4_sigma0_max_abs_diff_from_forecast_K"] = float(np.max(np.abs(e0 - core_f)))
    out["settings"] = {"N_ens": N_ENS, "sigma_T_K": SIG_T, "seed": SEED, "dt_obs_s": DT_OBS, "sigma_ref_W_m3": SIG_REF}
    json.dump(out, open(os.path.join(C.RESULTS, "stage3_checks.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


def one(cell, cond, bc, method, sig_eps, dt_obs=DT_OBS, sig_T=SIG_T, props=None, keep=False):
    t, core_true, surf = truth(cell, cond, bc)
    heat, Ta = f"Chen2020_{cond}", (-5.0 if cond.startswith("m5C") else 25.0)
    step = int(round(dt_obs / (t[1] - t[0])))
    sel = np.arange(step - 1, len(t), step)
    y = surf[sel] + sig_T * np.random.default_rng(SEED).normal(size=len(sel))
    if method == "corrected":
        m = Corrected(cell, props=props)
    else:
        m = plain(cell, props)
    est, learned, sink = enkf(m, heat, Ta, t[sel], y, t, sig_eps if method != "forecast" else 0.0, sig_T=sig_T,
                              n_ens=N_ENS if method != "forecast" else 1, assimilate=method != "forecast",
                              beta_sink=0.0 if bc == "a" else None)
    err = est - core_true
    half = t[-1] / 2
    lm = [v for tt, v in learned if tt >= half]
    sm = [v for tt, v in sink if tt >= half]
    r = {"cell": cell, "cond": cond, "bc": bc, "method": method, "sigma_eps": sig_eps, "dt_obs": dt_obs, "sigma_T": sig_T,
         "mae_K": float(np.mean(np.abs(err))), "end_error_K": float(err[-1]),
         "learned_mean_second_half_W_m3": float(np.mean(lm)) if lm else None,
         "sink_mean_second_half_W_m3": float(np.mean(sm)) if sm else None,
         "t": t.tolist(), "core_true": core_true.tolist(), "core_est": est.tolist()}
    if keep:
        r.update(learned_series=learned, sink_series=sink, Ta=Ta,
                 beta_sink=0.0 if bc == "a" else model_beta(m))
    return r


def run():
    out = []
    lv = {"0.1x": 0.1 * SIG_REF, "1x": SIG_REF, "10x": 10 * SIG_REF}
    only = os.environ.get("STAGE3_CELL")
    for cell, cond, bc in CASES:
        if only and cell != only:
            continue
        out.append(dict(one(cell, cond, bc, "forecast", 0.0), level="none"))
        for name, s in lv.items():
            out.append(dict(one(cell, cond, bc, "estimator", s), level=name))
            if bc == "b":
                out.append(dict(one(cell, cond, bc, "corrected", s), level=name))
            print(cell, cond, bc, name, {k: round(v, 4) for k, v in out[-1].items() if k in ("mae_K", "end_error_K")}, flush=True)
    sens = []
    if only in (None, "21700"):
        for kw in ({"sig_T": 0.05}, {"sig_T": 0.2}, {"dt_obs": 10.0}, {"dt_obs": 40.0}):
            r = one("21700", "m5C_2C", "b", "estimator", SIG_REF, **kw)
            sens.append({k: v for k, v in r.items() if k not in ("t", "core_true", "core_est")})
        p33 = dict(C.roll_properties()["registered"], rho=3108.4, cp=3.444444e6 / 3108.4, k_across=0.62)
        for meth in ("forecast", "estimator"):
            r = one("21700", "m5C_2C", "b", meth, SIG_REF if meth == "estimator" else 0.0, props=p33)
            sens.append(dict({k: v for k, v in r.items() if k not in ("t", "core_true", "core_est")}, props="ref. 33"))
        json.dump(sens, open(os.path.join(C.RESULTS, "stage3_sensitivity.json"), "w"), indent=1)
    tag = f"_{only}" if only else ""
    json.dump(out, open(os.path.join(C.RESULTS, f"stage3_runs{tag}.json"), "w"))


def series():
    """D21: the runs behind P5 (cooled-ends M50, registered and ten times) and P7 (0.2 K noise) again, keeping the
    learned error and end sink per reading, so their second-half means can be recomputed independently."""
    jobs = [("21700", c, "b", "estimator", s, n, {}) for c in ("p25C_1.25C", "p25C_2C", "m5C_2C")
            for n, s in (("1x", SIG_REF), ("10x", 10 * SIG_REF))]
    jobs.append(("21700", "m5C_2C", "b", "estimator", SIG_REF, "1x", {"sig_T": 0.2}))
    part = os.environ.get("STAGE3_PART")
    out = []
    for i, (cell, cond, bc, meth, s, n, kw) in enumerate(jobs):
        if part is not None and i % 2 != int(part):
            continue
        out.append(dict(one(cell, cond, bc, meth, s, keep=True, **kw), level=n))
        print(cell, cond, bc, n, kw, round(out[-1]["mae_K"], 6), flush=True)
    tag = f"_part{part}" if part is not None else ""
    json.dump(out, open(os.path.join(C.RESULTS, f"stage3_series{tag}.json"), "w"))


if __name__ == "__main__":
    {"checks": checks, "run": run, "series": series}[sys.argv[1]]()
