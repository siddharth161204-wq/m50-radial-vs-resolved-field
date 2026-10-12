import time
import numpy as np
from params import *
from discretise import VertexGrid2D
from network import integrate
src = HeatSource()
R = GEOMS["21700"]["R"]; H = GEOMS["21700"]["H"]
for (Nr, Nz) in [(45, 66), (90, 132), (180, 264)]:
    t0 = time.time()
    g = VertexGrid2D(R, H, Nr, Nz, 400.0, ends_convect=False)
    tb = time.time() - t0
    res = integrate(g.net, src, dt=1.0, verbose=True)
    p = g.probes(); th = res["th"]
    print(f"(a) Nr={Nr} Nz={Nz} n={g.net.n}: build {tb:.2f}s, integrate {res['wall_s']:.1f}s; "
          f"dT_cs={th[p['core_mid']]-th[p['surf_mid']]:.6f} dT_ax={th[p['core_mid']]-th[p['core_bot']]:.6f} "
          f"bal={res['balance_rel']:.2e}", flush=True)
