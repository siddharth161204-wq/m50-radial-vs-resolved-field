"""Second pass: (1) P5 and P7 from the per-reading series; (2) the relabel against b7af681, the CSV and the scorecard.
Independent of the repository's code; reads files only. Usage: python3 -I check_pass2.py"""
import os
import csv
import io
import json
import subprocess

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R = REPO + "/results/"
SIG_REF = 12377.70179
disc = []


def git_show(path):
    return subprocess.run(["git", "-C", REPO, "show", "b7af681:" + path], capture_output=True, check=True).stdout


def lvl(r):
    if r["method"] == "forecast":
        return "none" if r["sigma_eps"] == 0.0 else "?forecast with sigma_eps"
    q = r["sigma_eps"] / SIG_REF
    for k, v in ((0.1, "0.1x"), (1.0, "1x"), (10.0, "10x")):
        if abs(q / k - 1) < 1e-8:
            return v
    return "?%r" % r["sigma_eps"]


def close(a, b, rel=1e-12):
    return abs(a - b) <= rel * max(1.0, abs(a), abs(b))


runs = json.load(open(R + "stage3_runs_21700.json")) + json.load(open(R + "stage3_runs_4680.json"))
sens = json.load(open(R + "stage3_sensitivity.json"))
ser = json.load(open(R + "stage3_series.json"))
score = json.load(open(R + "stage3_scorecard.json"))

# ------------------------------------------------------------------ Task 1 ---------------------------------------
print("== Task 1: P5 and P7 from the series ==")
# D18 beta for the 21700 at h = 400: h_e = 1/(1/h + L/(6 k_z)), beta = 2 h_e / L
h, L, kz = 400.0, 0.0701, 25.092
he = 1.0 / (1.0 / h + L / (6 * kz))
beta = 2 * he / L
print("D18 beta (21700, h = 400): h_e = %.2f, beta = %.1f W/(m3 K)" % (he, beta))

res = {}
for s in ser:
    t = np.asarray(s["t"])
    tr, es = np.asarray(s["core_true"]), np.asarray(s["core_est"])
    half = t[-1] / 2
    lt = np.array([p[0] for p in s["learned_series"]])
    lv = np.array([p[1] for p in s["learned_series"]])
    st = np.array([p[0] for p in s["sink_series"]])
    sv = np.array([p[1] for p in s["sink_series"]])
    # readings: every second archived time from index 1 (20 s), as D20
    step = int(round(s["dt_obs"] / (t[1] - t[0])))
    t_read = t[np.arange(step - 1, len(t), step)]
    if not (len(lt) == len(t_read) and np.allclose(lt, t_read, atol=1e-9, rtol=0) and np.array_equal(lt, st)):
        disc.append(("series " + s["cond"] + s["level"], "reading times", "t[1::2]", (len(lt), len(t_read))))
    lm = float(np.mean(lv[lt >= half]))
    sm = float(np.mean(sv[st >= half]))
    mae = float(np.mean(np.abs(es - tr)))
    end = float(es[-1] - tr[-1])
    key = (s["cond"], lvl(s), s["sigma_T"])
    res[key] = dict(lm=lm, sm=sm, ratio=lm / sm, mae=mae, end=end, n2=int(np.sum(lt >= half)), n=len(lt))
    # against the series file's own scalars
    for nm, mine, stored in (("learned", lm, s["learned_mean_second_half_W_m3"]),
                             ("sink", sm, s["sink_mean_second_half_W_m3"]), ("mae", mae, s["mae_K"]),
                             ("end", end, s["end_error_K"])):
        if not close(mine, stored):
            disc.append(("stage3_series.json " + str(key), nm, mine, stored))
    if not close(s["beta_sink"], beta, 1e-4):
        disc.append(("stage3_series.json " + str(key), "beta_sink", beta, s["beta_sink"]))
    # against the stored runs / sensitivity
    if s["sigma_T"] == 0.1:
        o = [r for r in runs if (r["cell"], r["cond"], r["bc"], r["method"]) == (s["cell"], s["cond"], s["bc"], s["method"])
             and r["sigma_eps"] == s["sigma_eps"]]
        src = "stage3_runs_21700.json"
    else:
        o = [r for r in sens if (r["cell"], r["cond"], r["bc"], r["method"]) == (s["cell"], s["cond"], s["bc"], s["method"])
             and r["sigma_eps"] == s["sigma_eps"] and r["sigma_T"] == s["sigma_T"] and r["dt_obs"] == s["dt_obs"]
             and "props" not in r]
        src = "stage3_sensitivity.json"
    assert len(o) == 1, (key, len(o))
    o = o[0]
    for nm, mine, stored in (("learned", lm, o["learned_mean_second_half_W_m3"]),
                             ("sink", sm, o["sink_mean_second_half_W_m3"]), ("mae", mae, o["mae_K"]),
                             ("end", end, o["end_error_K"])):
        if not close(mine, stored):
            disc.append((src + " " + str(key), nm, mine, stored))
    same_series = ""
    if "core_est" in o:
        same_series = " core_est identical to stored run: %s" % (o["core_est"] == s["core_est"] and o["core_true"] == s["core_true"] and o["t"] == s["t"])
    print("  %-11s %-4s sigT=%.1f  learned %.6g  sink %.6g  ratio %.5f  (n2=%d of %d)  mae %.6f  end %.6f%s" % (
        key[0], key[1], key[2], lm, sm, lm / sm, res[key]["n2"], res[key]["n"], mae, end, same_series))

C3 = ["p25C_1.25C", "p25C_2C", "m5C_2C"]
for L_ in ("1x", "10x"):
    ok = all(abs(res[(c, L_, 0.1)]["lm"] - res[(c, L_, 0.1)]["sm"]) <= 0.3 * abs(res[(c, L_, 0.1)]["sm"]) for c in C3)
    rats = [res[(c, L_, 0.1)]["ratio"] for c in C3]
    print("  P5 %s: ratios %s -> %s" % (L_, ["%.4f" % x for x in rats], "held" if ok else "failed"))
    for i, c in enumerate(C3):
        if not close(rats[i], score[L_]["P5"]["learned_over_sink"][i], 1e-10):
            disc.append(("stage3_scorecard.json", L_ + " P5 ratio " + c, rats[i], score[L_]["P5"]["learned_over_sink"][i]))
    if ok != score[L_]["P5"]["held"]:
        disc.append(("stage3_scorecard.json", L_ + " P5 held", ok, score[L_]["P5"]["held"]))
base_run = [r for r in runs if (r["cell"], r["cond"], r["bc"], r["method"]) == ("21700", "m5C_2C", "b", "estimator")
            and lvl(r) == "1x"][0]
mae1 = float(np.mean(np.abs(np.asarray(base_run["core_est"]) - np.asarray(base_run["core_true"]))))
mae2 = res[("m5C_2C", "1x", 0.2)]["mae"]
print("  P7: mae 0.1 K (runs file series) %.6f, mae 0.2 K (series) %.6f, increase %.6f -> %s" % (
    mae1, mae2, mae2 - mae1, "held" if mae2 - mae1 < 0.1 else "failed"))
for nm, mine in (("mae_noise_0.1_K", mae1), ("mae_noise_0.2_K", mae2), ("increase_K", mae2 - mae1)):
    if not close(mine, score["1x"]["P7"][nm], 1e-10):
        disc.append(("stage3_scorecard.json", "P7 " + nm, mine, score["1x"]["P7"][nm]))

# ------------------------------------------------------------------ Task 2 ---------------------------------------
print("\n== Task 2: relabel against b7af681 ==")
changes = {}
for cell in ("21700", "4680"):
    old = json.loads(git_show("results/stage3_runs_%s.json" % cell))
    new = json.load(open(R + "stage3_runs_%s.json" % cell))
    if len(old) != len(new):
        disc.append(("stage3_runs_%s.json" % cell, "run count", len(old), len(new)))
    for i, (a, b) in enumerate(zip(old, new)):
        if set(a) != set(b):
            disc.append(("stage3_runs_%s.json" % cell, "keys run %d" % i, sorted(a), sorted(b)))
        for k in a:
            if a[k] != b.get(k):
                tag = (k, b["bc"], b["method"])
                changes[tag] = changes.get(tag, 0) + 1
                if k not in ("level", "sink_mean_second_half_W_m3") or (k == "sink_mean_second_half_W_m3" and b["bc"] != "a"):
                    disc.append(("stage3_runs_%s.json" % cell, "unexpected change run %d %s" % (i, k), a[k], b.get(k)))
        if lvl(b) != b["level"]:
            disc.append(("stage3_runs_%s.json" % cell, "level run %d" % i, lvl(b), b["level"]))
        if b["bc"] == "a" and b["method"] == "estimator" and b["sink_mean_second_half_W_m3"] != 0.0:
            disc.append(("stage3_runs_%s.json" % cell, "bc a estimator sink run %d" % i, 0.0, b["sink_mean_second_half_W_m3"]))
        if b["method"] == "forecast" and (b["sink_mean_second_half_W_m3"] is not None or b["learned_mean_second_half_W_m3"] is not None):
            disc.append(("stage3_runs_%s.json" % cell, "forecast learned/sink run %d" % i, None, "set"))
print("  fields changed (field, bc, method): count ->", changes)
print("  levels now:", sorted({(r["method"], r["level"]) for r in runs}))
print("  bc a estimator sinks:", sorted({r["sink_mean_second_half_W_m3"] for r in runs if r["bc"] == "a" and r["method"] == "estimator"}))

# the CSV, against the runs (values, formats and the note column)
rows = list(csv.DictReader(open(R + "stage3_errors.csv")))
idx = {(r["cell"], r["cond"], r["bc"], r["method"], r["level"]): r for r in runs}
NOTE_CORR = "no separate run: with the ends insulated beta = 0, so this is the estimator (D20)"
NOTE_EST = "end sink 0: beta = 0 with the ends insulated (D21)"
seen = set()
for row in rows:
    bc = {"insulated": "a", "cooled": "b"}[row["ends"]]
    key = (row["cell"], row["condition"], bc, row["method"], row["sigma_eps_level"])
    seen.add(key)
    src = idx.get(key)
    exp_note = ""
    if src is None and bc == "a" and row["method"] == "corrected":
        src = idx.get((row["cell"], row["condition"], "a", "estimator", row["sigma_eps_level"]))
        exp_note = NOTE_CORR
    elif bc == "a" and row["method"] == "estimator":
        exp_note = NOTE_EST
    if src is None:
        disc.append(("stage3_errors.csv", str(key), "a run", "none"))
        continue
    mae = float(np.mean(np.abs(np.asarray(src["core_est"]) - np.asarray(src["core_true"]))))
    end = src["core_est"][-1] - src["core_true"][-1]
    exp = [f"{mae:.5f}", f"{end:.5f}",
           "" if src["learned_mean_second_half_W_m3"] is None else f"{src['learned_mean_second_half_W_m3']:.6g}",
           "" if src["sink_mean_second_half_W_m3"] is None else f"{src['sink_mean_second_half_W_m3']:.6g}", exp_note]
    got = [row["mean_abs_error_K"], row["end_error_K"], row["learned_error_mean_second_half_W_m3"],
           row["end_sink_mean_second_half_W_m3"], row["note"]]
    for nm, e_, g_ in zip(("mae", "end", "learned", "sink", "note"), exp, got):
        if e_ != g_:
            # allow a last-digit formatting tie only if numerically within half a unit
            disc.append(("stage3_errors.csv", str(key) + " " + nm, e_, g_))
missing = [k for k in idx if k not in seen]
if missing:
    disc.append(("stage3_errors.csv", "runs missing", [], missing))
print("  CSV rows %d, header %s" % (len(rows), list(rows[0].keys())))
print("  notes used:", sorted({r["note"] for r in rows}))

# CSV diff against b7af681: only the insulated sinks and the note column should change
old_rows = list(csv.DictReader(io.StringIO(git_show("results/stage3_errors.csv").decode())))
okey = lambda r: (r["cell"], r["condition"], r["ends"], r["method"], r["sigma_eps_level"])
om = {okey(r): r for r in old_rows}
chg = {}
for r in rows:
    o = om.get(okey(r))
    if o is None:
        disc.append(("stage3_errors.csv vs b7af681", "new row", "", okey(r)))
        continue
    for k in o:
        if o[k] != r[k]:
            chg[(k, r["ends"], r["method"])] = chg.get((k, r["ends"], r["method"]), 0) + 1
print("  CSV changes vs b7af681 (field, ends, method): count ->", chg, "; rows old/new", len(old_rows), len(rows))

# scorecard unchanged
same = git_show("results/stage3_scorecard.json") == open(R + "stage3_scorecard.json", "rb").read()
print("  scorecard byte-identical to b7af681:", same)
if not same:
    disc.append(("stage3_scorecard.json", "vs b7af681", "identical", "differs"))

print("\n== DISCREPANCIES (%d) ==" % len(disc))
for d in disc:
    print(" ", d)
