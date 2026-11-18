"""One cell's 2C discharge at minus 5 C (ORegan2022, the cell at the ambient, as in D35) on particle meshes other than
uniform: the positive particle kept at 20 points, and meshes graded toward the particle surface. A test."""
import sys
import time

import numpy as np
import pybamm

sys.path.insert(0, "/home/claude/m50-radial-vs-resolved-field/src")
import stage5_posthoc_mesh as PM  # noqa: E402


def sim(T_C, rn, rp, graded=None, outputs=("Voltage [V]",)):
    p = pybamm.ParameterValues("ORegan2022")
    T = 273.15 + T_C
    p.update({"Ambient temperature [K]": T, "Initial temperature [K]": T, **PM.WINDOW,
              "Current function [A]": pybamm.InputParameter("I")})
    m = pybamm.lithium_ion.DFN({"calculate heat source for isothermal models": "true"})
    vp = dict(m.default_var_pts)
    vp["r_n"], vp["r_p"] = rn, rp
    sub = dict(m.default_submesh_types)
    if graded:
        for dom in ("negative particle", "positive particle"):
            sub[dom] = pybamm.MeshGenerator(pybamm.Exponential1DSubMesh, submesh_params={"side": "right", "stretch": graded})
    solver = pybamm.IDAKLUSolver(rtol=1e-6, atol=1e-8, output_variables=list(outputs))
    return pybamm.Simulation(m, parameter_values=p, var_pts=vp, submesh_types=sub, solver=solver)


for spec in sys.argv[1:]:
    rn, rp, g, T = spec.split(":")
    t0 = time.time()
    s = sim(float(T), int(rn), int(rp), float(g) if g != "u" else None)
    sol = s.solve(np.arange(0, 20000.0, 1.0), initial_soc=1.0, inputs={"I": 10.0})
    print(f"r_n {rn} r_p {rp} graded {g} at {T} C: 2C discharge ends at {sol['Time [s]'].entries[-1]:.2f} s "
          f"({time.time() - t0:.0f} s)", flush=True)
