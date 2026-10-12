"""Time-step sensitivity on the (Nr, Nz) = (90, 132) grid, 21700 cases (a) and (b)."""
import json, time
import numpy as np
from params import *
from discretise import VertexGrid2D
from network import integrate
src = HeatSource()
# check the cumulative integral
F = src.cumulative([0.0, 0.5, 1.0, 1706.0, src.t_end])
print("F(t_end) vs integral:", F[-1], src.integral(), " avg q over [0,2] check:",
      src.average(0, 2), 0.5*(0.5*(src.q[0]+src.q[1]) + 0.5*(src.q[1]+src.q[2])))
R = GEOMS["21700"]["R"]; H = GEOMS["21700"]["H"]
rows = []
for case in ("a", "b"):
    cf = CASES[case]
    g = VertexGrid2D(R, H, 90, 132, cf["h"], cf["ends_convect"])
    p = g.probes()
    for dt, ran in [(4.0, True), (2.0, True), (1.0, True), (0.5, True), (0.25, True), (1.0, False)]:
        res = integrate(g.net, src, dt=dt, rannacher=ran)
        th = res["th"]
        row = dict(case=case, Nr=90, Nz=132, dt=dt, rannacher=ran,
                   core=th[p["core_mid"]], surf=th[p["surf_mid"]],
                   dT_cs=th[p["core_mid"]] - th[p["surf_mid"]],
                   dT_ax=th[p["core_mid"]] - th[p["core_bot"]],
                   bal=res["balance_rel"], wall=res["wall_s"])
        rows.append(row)
        print(json.dumps({k: (round(v, 9) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
json.dump(rows, open("timestep_study_raw.json", "w"), indent=1)
