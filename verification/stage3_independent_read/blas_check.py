"""Repeat the 21700, 2C, minus 5 C, cooled-ends estimator run at the registered level and compare it with the stored run.
Writes blas_<label>.json beside this script. Usage: python3 -I -B blas_check.py <label>"""
import os
import json
import sys
import time

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, REPO + "/src")
import stage3_enkf as S  # noqa: E402

label = sys.argv[1]
try:
    import threadpoolctl
    info = [(x.get("internal_api"), x.get("num_threads")) for x in threadpoolctl.threadpool_info()]
except Exception as e:  # pragma: no cover
    info = repr(e)

t0 = time.time()
r = S.one("21700", "m5C_2C", "b", "estimator", S.SIG_REF)
secs = time.time() - t0
runs = json.load(open(REPO + "/results/stage3_runs_21700.json"))
ref = [x for x in runs if (x["cond"], x["bc"], x["method"]) == ("m5C_2C", "b", "estimator")
       and abs(x["sigma_eps"] / S.SIG_REF - 1) < 1e-9]
assert len(ref) == 1
ref = ref[0]
a, b = np.array(r["core_est"]), np.array(ref["core_est"])
d = np.abs(a - b)
out = dict(label=label, blas_threads=info, seconds=round(secs, 1), n=len(d), n_differ=int(np.sum(d > 0)),
           max_abs_diff_K=float(d.max()), t_same=r["t"] == ref["t"], true_same=r["core_true"] == ref["core_true"],
           bit_identical=bool(np.array_equal(a, b)))
for k in ("mae_K", "end_error_K", "learned_mean_second_half_W_m3", "sink_mean_second_half_W_m3"):
    out[k] = (r[k], ref[k], r[k] - ref[k])
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"blas_{label}.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
