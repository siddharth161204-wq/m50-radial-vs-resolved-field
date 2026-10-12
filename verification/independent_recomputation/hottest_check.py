"""Location and value of the hottest roll point at end of discharge (scheme V, 180 x 264), and a
bottom/top symmetry check. Extra diagnostic, written after my main numbers."""
import json
import numpy as np
from params import *
from discretise import VertexGrid2D
from network import integrate
src = HeatSource()
R = GEOMS["21700"]["R"]; H = GEOMS["21700"]["H"]
out = {}
for case in ("a", "b"):
    cf = CASES[case]
    g = VertexGrid2D(R, H, 180, 264, cf["h"], cf["ends_convect"])
    res = integrate(g.net, src, dt=1.0)
    T = res["th"].reshape(g.Nz + 1, g.Nr + 1) + T_AMB
    j, i = np.unravel_index(np.argmax(T), T.shape)
    out[case] = dict(grid="180x264", hottest_T_C=float(T[j, i]), hottest_r_mm=float(g.r[i] * 1e3), hottest_z_mm=float(g.z[j] * 1e3),
                     max_abs_T_minus_mirror_K=float(np.max(np.abs(T - T[::-1, :]))))
    print(case, out[case], flush=True)
json.dump(out, open("hottest_check.json", "w"), indent=1)
