"""Cost of the coupled model at n points per particle radius: build time, time per step and peak memory (a test,
nothing is saved)."""
import os
import resource
import sys
import time

sys.path.insert(0, "/home/claude/m50-radial-vs-resolved-field/src")
n = int(sys.argv[1])
steps = int(sys.argv[2]) if len(sys.argv) > 2 else 30
import stage5_posthoc_settled as P  # noqa: E402

P.set_particle_points(n)
import stage5_common as S5  # noqa: E402
import stage5_coupled as SC  # noqa: E402

S5.RUNDIR = "/tmp/claude-0/-home-claude/a52839dc-9584-53cc-a238-428518c66a3f/scratchpad/costtest"
kern = S5.Kernel(S5.kernel_path("resolved", "b", "21700", "m5C_2C"))
t0 = time.time()
b = SC.make("ORegan2022", 1.0, kern.W, False)
t1 = time.time()
rss1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
out = SC.run("discharge", "21700", "ORegan2022", -5.0, 10.0, kern, heat="two-way", built=b, max_steps=steps)
t2 = time.time()
rss2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"n {n}: build {t1 - t0:.0f} s, peak after build {rss1:.0f} MB; {out['meta']['n_steps']} steps in {t2 - t1:.0f} s "
      f"({(t2 - t1) / max(1, out['meta']['n_steps']):.2f} s/step), peak {rss2:.0f} MB, V {out['V'][-1]:.4f}", flush=True)
