"""At 160 points: 40 steps of the main case (resolved kernel, two-way heat) with the solver's default storage and
with first and last states only; are the steps the same, and how does memory grow without collection?"""
import gc, os, sys, time
import numpy as np
sys.path.insert(0, "/home/claude/m50-radial-vs-resolved-field/src")
os.environ["OMP_NUM_THREADS"] = "1"
import stage5_posthoc_settled as P
P.set_particle_points(160)
import pybamm
import stage5_common as S5, stage5_coupled as SC
mode = sys.argv[1]; steps = int(sys.argv[2])
kern = S5.Kernel(S5.kernel_path("resolved", "b", "21700", "m5C_2C"))
b = SC.make("ORegan2022", 1.0, kern.W, False)
if mode == "first_last":
    b["stepper"].solver = pybamm.IDAKLUSolver(rtol=SC.RTOL, atol=SC.ATOL, store_first_last=True)
import stage5_posthoc_settled as PP; PP.collect_garbage_while_stepping()
rss = lambda: int(open("/proc/self/statm").read().split()[1]) * 4096 // 2**20
r0 = rss(); t0 = time.time()
out = SC.run("discharge", "21700", "ORegan2022", -5.0, 10.0, kern, heat="two-way", built=b, max_steps=steps)
print(mode, "steps", out["meta"]["n_steps"], "wall", round(time.time() - t0), "s, rss growth without collection", rss() - r0, "MB")
np.savez(f"storage160_{mode}.npz", t=out["t"], V=out["V"], I=out["I"], T=out["T"], q=out["q"], y=np.asarray(b["stepper"].sol.y)[:, -1])
