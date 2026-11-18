"""Test of D36's resumable run at the registered mesh (20 points): a stored registered run is made again (a) by the
registered run function and (b) by the resumable one, stopped by os._exit after a given number of steps and resumed
in a new process, possibly several times. Both must give the stored run.

python3 resume_test.py plain <name>          the registered function, compared with the stored run
python3 resume_test.py resume <name> <stop>   the resumable function; stop after <stop> steps (0: run to the end)
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, "/home/claude/m50-radial-vs-resolved-field/src")
os.environ["OMP_NUM_THREADS"] = "1"
mode, name = sys.argv[1], sys.argv[2]
stop = int(sys.argv[3]) if len(sys.argv) > 3 else 0
os.environ["D36_CHECKPOINTS"] = "/tmp/claude-0/-home-claude/a52839dc-9584-53cc-a238-428518c66a3f/scratchpad/ckpt_test"
os.environ["D36_POINTS"] = "20"
import stage5_posthoc_settled as P  # noqa: E402
import stage5_common as S5  # noqa: E402
import stage5_coupled as SC  # noqa: E402
import stage5_runs as RN  # noqa: E402

S5.RUNDIR = os.path.join(P.C.RESULTS, "stage5_runs")
ref = SC.load_run(name)
m = ref["meta"]
case = m.get("case")
lab = m["kernel_label"]
if name.startswith("C_"):
    cell, ends, Ta, I, g0 = RN.DISCHARGE_CASES[case]
    mdl, bc = RN.models_for(ends)[lab]
    kern = S5.Kernel(S5.kernel_path(mdl, bc, cell, g0))
    kind, soc = "discharge", 1.0
else:
    cell = m["cell"]
    mdl, bc = RN.models_for("b")[lab]
    kern = S5.Kernel(S5.kernel_path(mdl, bc, cell, "charge10"))
    kind, soc, Ta, I = "charge", 0.0, m["T_amb_C"], m["I_app_A"]
single = m["single"]
W = np.array([1.0]) if single else kern.W
b = SC.make(m["set"], soc, W, single)
if mode == "plain":
    out = SC.run(kind, cell, m["set"], Ta, I, kern, heat="two-way", single=single, built=b, label=name)
else:
    if stop:
        step = SC.Stepper.step
        calls = {"n": 0}

        def step_and_stop(self, dt, inputs):
            calls["n"] += 1
            if calls["n"] > stop:
                print(f"stopping after {stop} steps of this process", flush=True)
                os._exit(3)
            return step(self, dt, inputs)
        SC.Stepper.step = step_and_stop
    out = P.resumable_run(kind, cell, m["set"], Ta, I, kern, heat="two-way", single=single, built=b, label=name, every=20)
worst = {}
for key in ref:
    if key == "meta":
        continue
    a = np.asarray(ref[key], dtype=np.float64)
    bb = np.asarray(out[key])
    if key in ("T", "q", "margin_nodes_min", "margin_interface"):
        bb = bb.astype(np.float32)
    elif key == "margin_nodes_argmin":
        bb = bb.astype(np.int16)
    bb = bb.astype(np.float64)
    if a.shape != bb.shape:
        worst[key] = f"shape {a.shape} against {bb.shape}"
        continue
    worst[key] = float(np.max(np.abs(a - bb))) if a.size else 0.0
print(json.dumps({"mode": mode, "name": name, "steps": out["meta"]["n_steps"], "status": out["meta"]["status"],
                  "resumed_at": out["meta"].get("resumed_at_steps"), "max_abs_difference": worst}))
