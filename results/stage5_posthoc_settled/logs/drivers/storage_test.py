"""Does the solver's output storage change a step? A stored registered run (20 points) made again with the solver
told to keep only each step's first and last states (store_first_last), compared with the stored run."""
import json, os, sys
import numpy as np
sys.path.insert(0, "/home/claude/m50-radial-vs-resolved-field/src")
os.environ["OMP_NUM_THREADS"] = "1"
import pybamm
import stage5_common as S5, stage5_coupled as SC, stage5_runs as RN
import common as C
S5.RUNDIR = os.path.join(C.RESULTS, "stage5_runs")
name = sys.argv[1]; mode = sys.argv[2]
ref = SC.load_run(name); m = ref["meta"]
cell, ends, Ta, I, g0 = RN.DISCHARGE_CASES[m["case"]]
mdl, bc = RN.models_for(ends)[m["kernel_label"]]
kern = S5.Kernel(S5.kernel_path(mdl, bc, cell, g0))
b = SC.make(m["set"], 1.0, kern.W, m["single"])
if mode == "first_last":
    b["stepper"].solver = pybamm.IDAKLUSolver(rtol=SC.RTOL, atol=SC.ATOL, store_first_last=True)
elif mode == "no_hermite":
    b["stepper"].solver = pybamm.IDAKLUSolver(rtol=SC.RTOL, atol=SC.ATOL, options={"hermite_interpolation": False})
out = SC.run("discharge", cell, m["set"], Ta, I, kern, heat="two-way", single=m["single"], built=b, label=name)
w = {k: float(np.max(np.abs(np.asarray(ref[k], dtype=float) - np.asarray(out[k], dtype=float).astype(np.float32 if k in ("T", "q") else np.float64)))) for k in ("t", "V", "I", "T", "q")}
print(mode, out["meta"]["n_steps"], out["meta"]["status"], round(out["meta"]["wall_s"], 1), "s", w)
