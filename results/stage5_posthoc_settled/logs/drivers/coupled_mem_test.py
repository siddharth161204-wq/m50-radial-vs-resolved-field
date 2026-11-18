"""Memory of the coupled model at n points per particle radius, step by step (a test, nothing saved)."""
import gc
import sys
import time

sys.path.insert(0, "/home/claude/m50-radial-vs-resolved-field/src")
n = int(sys.argv[1])
steps = int(sys.argv[2])
import stage5_posthoc_settled as P  # noqa: E402

P.set_particle_points(n)
import numpy as np  # noqa: E402
import stage5_common as S5  # noqa: E402
import stage5_coupled as SC  # noqa: E402


def rss():
    for line in open("/proc/self/status"):
        if line.startswith(("VmRSS", "VmHWM")):
            yield line.split()[1]


kern = S5.Kernel(S5.kernel_path("resolved", "b", "21700", "m5C_2C"))
b = SC.make("ORegan2022", 1.0, kern.W, False)
st = b["stepper"]
print("built", list(rss()), flush=True)
conv = kern.group_convolver()
T = np.full(15, -5.0)
t0 = time.time()
for k in range(steps):
    inp = {"I_app": 10.0, **{f"T{g + 1}": float(T[g]) + 273.15 for g in range(15)}}
    sol = st.step(1.0, inp)
    o = st.evaluate(inp)
    T = -5.0 + conv.push(o["Q"] / S5.V21700)
    if k < 5 or k % 10 == 0:
        gc.collect()
        print(f"step {k + 1} t {o['t']:.0f} V {o['V']:.4f} rss/hwm kB {list(rss())} {time.time() - t0:.0f} s", flush=True)
    if sol.termination != "final time":
        print("end", sol.termination)
        break
