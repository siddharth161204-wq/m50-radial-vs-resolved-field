"""Compare run truth series with Stage 1's archived resolved fields, and the forecast with Stage 1's radial output."""
import os
import json

import numpy as np

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "results") + "/"
runs = json.load(open(R + "stage3_runs_21700.json")) + json.load(open(R + "stage3_runs_4680.json"))
rad = json.load(open(R + "radial1d.json"))["registered"]

seen = set()
fc = {}
for r in runs:
    key = (r["cell"], r["cond"], r["bc"])
    if r["method"] == "forecast":
        fc[key] = r
    if key in seen:
        continue
    seen.add(key)
    f = json.load(open(R + "fields/%s_%s_Chen2020_%s.json" % (r["cell"], r["bc"], r["cond"])))
    cols = f["series_columns"]
    S = np.asarray(f["series"], float)
    t_a, core_a = S[:, cols.index("t_s")], S[:, cols.index("T_core_mid")]
    t, tr = np.asarray(r["t"]), np.asarray(r["core_true"])
    same_len = len(t_a) == len(t)
    dt = np.max(np.abs(t_a - t)) if same_len else None
    dc = np.max(np.abs(core_a - tr)) if same_len else None
    print(key, "archive n=%d run n=%d" % (len(t_a), len(t)), "max|dt|=", dt, "max|dcore|=", dc,
          "archive end t=%.4f T_core_mid=%.6f, field 'end' T_core_mid=%.6f" % (t_a[-1], core_a[-1], f["end"]["T_core_mid"]),
          "bc", f["bc"], "props", f["props"], "heat", f["heat"], "Tamb", f["T_amb_C"])
print("series columns:", cols)

# forecast: (a) and (b) should be the same radial model (no ends), equal to Stage 1's radial end core
for cell, cond in [("21700", "p25C_1.25C"), ("21700", "p25C_2C"), ("21700", "m5C_2C"), ("4680", "m5C_2C")]:
    fa, fb = fc.get((cell, cond, "a")), fc.get((cell, cond, "b"))
    e = rad["Chen2020_%s|%s" % (cond, cell)]["end"]
    msg = "%s %s radial1d end t=%.4f T_core=%.12f" % (cell, cond, e["t"], e["T_core"])
    for nm, x in (("a", fa), ("b", fb)):
        if x is not None:
            msg += " | fc(%s) end=%.12f diff=%.2e" % (nm, x["core_est"][-1], x["core_est"][-1] - e["T_core"])
    if fa is not None and fb is not None:
        msg += " | a==b series: %s" % np.array_equal(fa["core_est"], fb["core_est"])
    print(msg)
