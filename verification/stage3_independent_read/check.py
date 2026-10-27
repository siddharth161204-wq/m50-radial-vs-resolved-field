"""Independent check of Stage 3 Part B outputs (written from predictions_stage3.md, D19, D20).
Does not import anything from the repository."""
import os
import csv
import json
import math
import sys
from collections import Counter, defaultdict

import numpy as np

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "results") + "/"
SIG_REF = 12377.70179  # registered level, W/m3 (task statement); exact value cross-checked below
LEVELS = {0.1: "0.1x", 1.0: "1x", 10.0: "10x"}

runs = json.load(open(R + "stage3_runs_21700.json")) + json.load(open(R + "stage3_runs_4680.json"))
sens = json.load(open(R + "stage3_sensitivity.json"))
score = json.load(open(R + "stage3_scorecard.json"))
checks = json.load(open(R + "stage3_checks.json"))

disc = []  # discrepancies


def lvl(sig):
    if sig == 0.0:
        return "none"
    r = sig / SIG_REF
    for k, v in LEVELS.items():
        if abs(r / k - 1) < 1e-8:
            return v
    return "?%r" % sig


# ---------------- Task 1: recompute MAE and end error from the time series -------------
print("== Task 1: recompute mae_K, end_error_K from series ==")
idx = {}
maxd_mae = maxd_end = 0.0
label_wrong = 0
for r in runs:
    t = np.asarray(r["t"], float)
    tr = np.asarray(r["core_true"], float)
    es = np.asarray(r["core_est"], float)
    assert len(t) == len(tr) == len(es), "length mismatch"
    assert np.all(np.diff(t) > 0), "time not increasing"
    e = es - tr
    mae = float(np.mean(np.abs(e)))
    end = float(e[-1])
    L = lvl(r["sigma_eps"])
    if L.startswith("?"):
        disc.append(("runs", "sigma_eps", "0, 0.1x, 1x or 10x", r["sigma_eps"]))
    if r.get("level") != L:
        label_wrong += 1
    key = (r["cell"], r["cond"], r["bc"], r["method"], L)
    if key in idx:
        disc.append(("runs", "duplicate key", "unique", key))
    rec = dict(r)
    rec.update(mae=mae, end=end, maxabs=float(np.max(np.abs(e))), argmax_t=float(t[np.argmax(np.abs(e))]),
               t_end=float(t[-1]), n=len(t), level_derived=L)
    idx[key] = rec
    dm, de = abs(mae - r["mae_K"]), abs(end - r["end_error_K"])
    maxd_mae, maxd_end = max(maxd_mae, dm), max(maxd_end, de)
    if dm > 1e-12 or de > 1e-12:
        disc.append(("runs " + str(key), "mae_K/end_error_K", (mae, end), (r["mae_K"], r["end_error_K"])))
    # other run fields
    if r["dt_obs"] != 20.0 or r["sigma_T"] != 0.1:
        disc.append(("runs " + str(key), "dt_obs/sigma_T", (20.0, 0.1), (r["dt_obs"], r["sigma_T"])))
    if r["method"] == "forecast":
        if r["learned_mean_second_half_W_m3"] is not None or r["sink_mean_second_half_W_m3"] is not None:
            disc.append(("runs " + str(key), "learned/sink", None, "not None"))
print("runs:", len(runs), " max |mae diff| = %.3e, max |end diff| = %.3e" % (maxd_mae, maxd_end))
print("runs whose 'level' label differs from sigma_eps-derived level:", label_wrong)

# completeness of the run set
cases = sorted(set((k[0], k[1], k[2]) for k in idx))
print("cases:", cases)
for c in cases:
    meths = sorted((k[3], k[4]) for k in idx if k[:3] == c)
    exp = [("estimator", l) for l in ("0.1x", "10x", "1x")] + [("forecast", "none")]
    if c[2] == "b":
        exp += [("corrected", l) for l in ("0.1x", "10x", "1x")]
    if sorted(meths) != sorted(exp):
        disc.append(("runs " + str(c), "method/level set", sorted(exp), sorted(meths)))

# truth and time identical across methods within a case; info on series
for c in cases:
    ks = [k for k in idx if k[:3] == c]
    t0 = np.asarray(idx[ks[0]]["t"])
    tr0 = np.asarray(idx[ks[0]]["core_true"])
    for k in ks[1:]:
        if not (np.array_equal(t0, idx[k]["t"]) and np.array_equal(tr0, idx[k]["core_true"])):
            disc.append(("runs " + str(k), "t/core_true", "identical within case", "differs"))
    print("  %s n=%d t0=%.4f t_end=%.4f  true_end=%.4f" % (c, len(t0), t0[0], t0[-1], tr0[-1]))

# ---------------- Task 2: score P1 to P7 -------------------------------------------------
print("\n== Task 2: scoring ==")
C3 = ["p25C_1.25C", "p25C_2C", "m5C_2C"]


def g(cell, cond, bc, method, L):
    return idx[(cell, cond, bc, method, L if method != "forecast" else "none")]


mine = {}
for L in ("1x", "0.1x", "10x"):
    s = {}
    fmax = [g("21700", c, "a", "forecast", L)["maxabs"] for c in C3]
    emae = [g("21700", c, "a", "estimator", L)["mae"] for c in C3]
    s["P1"] = dict(forecast_max_abs_K=fmax, estimator_mae_K=emae,
                   held=all(x <= 0.3 for x in fmax) and all(x < 0.3 for x in emae))
    f_end = abs(g("21700", "m5C_2C", "b", "forecast", L)["end"])
    s["P2"] = dict(forecast_end_abs_K=f_end, held=f_end > 0.8)
    e_end = abs(g("21700", "m5C_2C", "b", "estimator", L)["end"])
    s["P3"] = dict(estimator_end_abs_K=e_end, ratio=e_end / f_end, held=e_end <= 0.5 * f_end)
    pairs = [(g(cell, cond, "b", "corrected", L)["mae"], g(cell, cond, "b", "estimator", L)["mae"])
             for cell, cond in [("21700", c) for c in C3] + [("4680", "m5C_2C")]]
    s["P4"] = dict(corrected_vs_estimator_mae_K=pairs, held=all(a < b for a, b in pairs))
    rat = []
    for c in C3:
        rr = g("21700", c, "b", "estimator", L)
        rat.append(rr["learned_mean_second_half_W_m3"] / rr["sink_mean_second_half_W_m3"])
    # within 30 % of the sink: |learned - sink| <= 0.3 |sink|
    held5 = True
    for c in C3:
        rr = g("21700", c, "b", "estimator", L)
        lm, sk = rr["learned_mean_second_half_W_m3"], rr["sink_mean_second_half_W_m3"]
        held5 &= abs(lm - sk) <= 0.3 * abs(sk)
    s["P5"] = dict(learned_over_sink=rat, held=held5)
    f4 = abs(g("4680", "m5C_2C", "b", "forecast", L)["end"])
    e4 = abs(g("4680", "m5C_2C", "b", "estimator", L)["end"])
    s["P6"] = dict(forecast_end_abs_K=f4, estimator_end_abs_K=e4, held=f4 > 5.0 and e4 > 1.0)
    if L == "1x":
        base = g("21700", "m5C_2C", "b", "estimator", "1x")["mae"]
        n2 = [x for x in sens if x["cell"] == "21700" and x["cond"] == "m5C_2C" and x["bc"] == "b"
              and x["method"] == "estimator" and x["sigma_T"] == 0.2 and x["dt_obs"] == 20.0
              and lvl(x["sigma_eps"]) == "1x" and "props" not in x]
        assert len(n2) == 1, n2
        inc = n2[0]["mae_K"] - base
        s["P7"] = dict(**{"mae_noise_0.1_K": base, "mae_noise_0.2_K": n2[0]["mae_K"]}, increase_K=inc,
                       held=inc < 0.1)
    mine[L] = s


def flat(x, pre=""):
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            out.update(flat(v, pre + "." + k if pre else k))
        return out
    if isinstance(x, (list, tuple)):
        out = {}
        for i, v in enumerate(x):
            out.update(flat(v, pre + "[%d]" % i))
        return out
    return {pre: x}


fm, fs = flat(mine), flat(score)
for k in sorted(set(fm) | set(fs)):
    a, b = fm.get(k, "MISSING"), fs.get(k, "MISSING")
    if isinstance(a, bool) or isinstance(b, bool) or isinstance(a, str) or isinstance(b, str):
        ok = a == b
    else:
        ok = abs(a - b) <= 1e-12 * max(1.0, abs(a))
    if not ok:
        disc.append(("stage3_scorecard.json", k, a, b))
for L in ("1x", "0.1x", "10x"):
    print(L, {p: mine[L][p]["held"] for p in mine[L]})
s1 = mine["1x"]
print("P1 forecast max|err| (a):", ["%.4f@t=%.0f" % (g("21700", c, "a", "forecast", "1x")["maxabs"],
                                                       g("21700", c, "a", "forecast", "1x")["argmax_t"]) for c in C3],
      " end:", ["%.4f" % g("21700", c, "a", "forecast", "1x")["end"] for c in C3])
print("P1 est mae (a):", ["%.4f" % x for x in s1["P1"]["estimator_mae_K"]])
print("P2 forecast |end|: %.4f" % s1["P2"]["forecast_end_abs_K"])
print("P3 est |end|: %.4f ratio %.4f" % (s1["P3"]["estimator_end_abs_K"], s1["P3"]["ratio"]))
print("P4 pairs:", [("%.4f" % a, "%.4f" % b) for a, b in s1["P4"]["corrected_vs_estimator_mae_K"]])
print("P5 ratios:", ["%.4f" % x for x in s1["P5"]["learned_over_sink"]])
print("P6: %.4f %.4f" % (s1["P6"]["forecast_end_abs_K"], s1["P6"]["estimator_end_abs_K"]))
print("P7:", s1["P7"])
for L in ("0.1x", "10x"):
    m = mine[L]
    print(L, "P1 est mae", ["%.4f" % x for x in m["P1"]["estimator_mae_K"]], "P3 ratio %.4f" % m["P3"]["ratio"],
          "P5", ["%.4f" % x for x in m["P5"]["learned_over_sink"]], "P6 est end %.4f" % m["P6"]["estimator_end_abs_K"])

# ---------------- Task 3: stage3_errors.csv ---------------------------------------------
print("\n== Task 3: stage3_errors.csv ==")
rows = list(csv.DictReader(open(R + "stage3_errors.csv")))
print("rows:", len(rows), "header:", list(rows[0].keys()))
seen = Counter()
ends_map = {"insulated": "a", "cooled": "b"}
nocase = []
for row in rows:
    bc = ends_map.get(row["ends"])
    L = row["sigma_eps_level"]
    key = (row["cell"], row["condition"], bc, row["method"], L)
    seen[key] += 1
    src = idx.get(key)
    note = ""
    if src is None:
        if bc == "a" and row["method"] == "corrected":
            src = idx.get((row["cell"], row["condition"], "a", "estimator", L))
            nocase.append(key)
            note = " (no run; compared with estimator)"
        if src is None:
            disc.append(("stage3_errors.csv", str(key), "a matching run", "none"))
            continue

    def chk(field, val, ndp=None, sig=None):
        txt = row[field]
        if val is None:
            if txt != "":
                disc.append(("stage3_errors.csv", str(key) + " " + field, "blank", txt))
            return
        if txt == "":
            disc.append(("stage3_errors.csv", str(key) + " " + field, val, "blank"))
            return
        x = float(txt)
        if ndp is not None:
            tol = 0.5 * 10 ** (-ndp) + 1e-12
        else:
            mag = math.floor(math.log10(abs(val))) if val != 0 else 0
            tol = 0.5 * 10 ** (mag - sig + 1) * (1 + 1e-9)
        if abs(x - val) > tol:
            disc.append(("stage3_errors.csv", str(key) + " " + field + note, val, txt))

    chk("mean_abs_error_K", src["mae"], ndp=5)
    chk("end_error_K", src["end"], ndp=5)
    chk("learned_error_mean_second_half_W_m3", src["learned_mean_second_half_W_m3"], sig=6)
    chk("end_sink_mean_second_half_W_m3", src["sink_mean_second_half_W_m3"], sig=6)
dups = [k for k, v in seen.items() if v > 1]
if dups:
    disc.append(("stage3_errors.csv", "duplicate rows", "none", dups))
missing = [k for k in idx if k not in seen]
if missing:
    disc.append(("stage3_errors.csv", "runs absent from CSV", "none", missing))
print("CSV rows with no run behind them:", nocase)

# ---------------- Task 4: stage3_checks.json --------------------------------------------
print("\n== Task 4: stage3_checks.json ==")
print(json.dumps(checks, indent=1))
st = checks["settings"]
exp_settings = dict(N_ens=3000, sigma_T_K=0.1, seed=20261027, dt_obs_s=20.0)
for k, v in exp_settings.items():
    if st.get(k) != v:
        disc.append(("stage3_checks.json", "settings." + k, v, st.get(k)))
if abs(st["sigma_ref_W_m3"] - SIG_REF) > 1e-5:
    disc.append(("stage3_checks.json", "settings.sigma_ref_W_m3", SIG_REF, st["sigma_ref_W_m3"]))
print("V1 mae < 0.1 K:", checks["V1_mean_abs_error_K"] < 0.1, " |end| < 0.1 K:", abs(checks["V1_end_error_K"]) < 0.1)
print("V2 max diff:", checks["V2_max_abs_diff_K"], " bit-exact:", checks["V2_max_abs_diff_K"] == 0.0)
print("V3:", checks["V3_identical"])
print("V4 same seed:", checks["V4_same_seed_identical"], " sigma0 diff:", checks["V4_sigma0_max_abs_diff_from_forecast_K"])

# ---------------- sensitivity file sanity -------------------------------------------------
print("\n== sensitivity ==")
for x in sens:
    print(" ", x["method"], x.get("props", "O'Regan"), "sigma_eps=%s" % lvl(x["sigma_eps"]), "dt=%g" % x["dt_obs"],
          "sigT=%g" % x["sigma_T"], "mae=%.5f end=%.5f" % (x["mae_K"], x["end_error_K"]))

print("\n== DISCREPANCIES (%d) ==" % len(disc))
for d in disc:
    print(" ", d)
