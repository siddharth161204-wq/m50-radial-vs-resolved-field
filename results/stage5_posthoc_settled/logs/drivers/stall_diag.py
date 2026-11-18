"""Diagnostic of the stalled run (D36): each group's extreme surface stoichiometries and current at the last saved
state of the main case under the radial kernel at 160 points (step 360), from the run's checkpoint. Nothing is
stepped; the coupled model is built with extra outputs and evaluated at the saved state."""
import glob
import sys

import casadi
import numpy as np

sys.path.insert(0, "/home/claude/m50-radial-vs-resolved-field/src")
import stage5_posthoc_settled as P  # noqa: E402

P.set_particle_points(160)
import stage5_common as S5  # noqa: E402
import stage5_coupled as SC  # noqa: E402

EXTRA = ["Minimum negative particle surface stoichiometry", "Maximum negative particle surface stoichiometry",
         "Minimum positive particle surface stoichiometry", "Maximum positive particle surface stoichiometry",
         "Minimum negative particle stoichiometry", "X-averaged negative particle stoichiometry"]
SC.OUT_NAMES = SC.OUT_NAMES + EXTRA
f = sorted(glob.glob(sys.argv[1]))[0]
z = np.load(f)
kern = S5.Kernel(S5.kernel_path("radial", "lat", "21700", "m5C_2C"))
model, douts = SC.build_coupled("ORegan2022", 1.0, kern.W)
G = 15
t = casadi.MX.sym("t")
y = casadi.MX.sym("y", model.len_rhs_and_alg)
names = ["I_app"] + [f"T{g + 1}" for g in range(G)]
ps = {k: casadi.MX.sym(k) for k in names}
T_last = z["T_last"]
args = [float(z["sol_t"]), z["sol_y"], 10.0] + [float(T) + 273.15 for T in T_last]
np.set_printoptions(linewidth=220, precision=4, suppress=True)
print(f"step {int(z['k'])}, t {float(z['sol_t']):.2f} s, V {z['rec_V'][-1]:.4f}")
print("group current / mean:", z["rec_I"][-1] / 10.0)
print("group T (C):", T_last)
for name in EXTRA:
    out = []
    for g in range(G):
        fn = casadi.Function("f", [t, y] + [ps[k] for k in names], [douts[(name, g)].to_casadi(t, y, inputs=ps)])
        v = np.asarray(fn(*args)).ravel()
        out.append(v)
    if len(out[0]) == 1:
        print(f"{name}: {np.array([o[0] for o in out])}")
    else:
        print(f"{name} (centre, middle, surface): " + " | ".join(f"{o[0]:.3f} {o[len(o)//2]:.3f} {o[-1]:.3f}" for o in out))
