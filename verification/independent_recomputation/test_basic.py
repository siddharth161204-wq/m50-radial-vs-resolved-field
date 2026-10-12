"""Basic verification tests (written before any comparison with the study)."""
import time, json
import numpy as np
from params import *
from discretise import VertexGrid1D, VertexGrid2D, CellGrid2D
from network import integrate
import analytic_1d

src = HeatSource()
R = GEOMS["21700"]["R"]; H = GEOMS["21700"]["H"]; NU = GEOMS["21700"]["n_units"]
edges = np.linspace(0, R, NU + 1)

# 1) analytic 1D, mode-count convergence
for nm in (5000, 10000, 20000, 40000):
    t0 = time.time()
    an = analytic_1d.solve(R, H_1D, RHOCP, K_R, C_SHELL, src.t, src.q, src.t_end, n_modes=nm, unit_edges=edges)
    print(f"analytic n_modes={nm}: core={an['core']:.9f} surf={an['surf']:.9f} dT={an['core']-an['surf']:.9f} "
          f"vmean={an['vol_mean']:.9f} bal={an['balance_rel']:.3e} ({time.time()-t0:.1f}s)")

# 2) 1D FV convergence vs analytic
for Nr in (45, 90, 180, 360):
    g = VertexGrid1D(R, Nr, H_1D)
    res = integrate(g.net, src, dt=0.5)
    th = res["th"]
    u, _ = g.unit_averages(th, NU)
    print(f"1D FV Nr={Nr}: core={th[0]:.6f} surf={th[-1]:.6f} dT={th[0]-th[-1]:.6f} "
          f"units max|diff vs analytic|={np.max(np.abs(u-an['units'])):.2e} bal={res['balance_rel']:.2e} schemebal={res['balance_rel_scheme']:.1e}")

# 3) 3D code with shell in-plane conduction off and no end shell, adiabatic ends == 1D
g1 = VertexGrid1D(R, 90, H_1D); r1 = integrate(g1.net, src, dt=1.0)
g3 = VertexGrid2D(R, H, 90, 20, H_1D, ends_convect=False, kt=0.0, end_shell=False)
r3 = integrate(g3.net, src, dt=1.0)
T3 = r3["th"].reshape(21, 91)
print("3D-reduces-to-1D max |T3D(r,z) - T1D(r)| =", np.max(np.abs(T3 - r1["th"][None, :])))
