"""Production runs for the independent check. Appends one JSON record per run to runs.jsonl.

Usage: python3 run_all.py [part ...]   parts: analytic fv1d timestep v21700 v4680 cell sens
"""
import json, sys, time
import numpy as np
from params import *
from discretise import VertexGrid1D, VertexGrid2D, CellGrid2D
from network import integrate
import analytic_1d

OUT = "runs.jsonl"
src = HeatSource()


def emit(rec):
    rec["stamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(OUT, "a") as f:
        f.write(json.dumps(rec) + "\n")
    short = {k: v for k, v in rec.items() if k not in ("units_C", "hist")}
    print(json.dumps(short), flush=True)


def record_2d(scheme, cell, case, g, res, extra=None):
    th = res["th"]
    if scheme == "V":
        p = g.probes()
        vals = {k: float(th[v]) for k, v in p.items()}
    else:
        vals = {k: float(v) for k, v in g.extract(th).items()}
    nu = GEOMS[cell]["n_units"]
    units, edges = g.unit_averages(th, nu)
    vol_units = np.pi * (edges[1:] ** 2 - edges[:-1] ** 2)
    rec = dict(
        scheme=scheme, cell=cell, case=case, Nr=g.Nr, Nz=g.Nz, n=g.net.n,
        T_core_mid_C=T_AMB + vals["core_mid"], T_surf_mid_C=T_AMB + vals["surf_mid"],
        T_core_bot_C=T_AMB + vals["core_bot"], T_core_top_C=T_AMB + vals["core_top"],
        dT_core_surface_K=vals["core_mid"] - vals["surf_mid"],
        dT_axial_bot_K=vals["core_mid"] - vals["core_bot"],
        dT_axial_top_K=vals["core_mid"] - vals["core_top"],
        units_C=list(T_AMB + units), units_spread_K=float(units.max() - units.min()),
        vol_mean_C=T_AMB + g.volume_mean(th),
        vol_mean_from_units_C=float(T_AMB + vol_units @ units / vol_units.sum()),
        E_gen_J=res["E_gen_exact"], E_lost_J=res["E_lost"], E_stored_J=res["E_stored"],
        balance_rel=res["balance_rel"], wall_s=res["wall_s"], n_steps=res["n_steps"],
    )
    if extra:
        rec.update(extra)
    return rec


def part_analytic():
    for cell, h in (("21700", H_1D), ("4680", H_1D), ("21700", 25.0)):
        R = GEOMS[cell]["R"]; H = GEOMS[cell]["H"]; nu = GEOMS[cell]["n_units"]
        edges = np.linspace(0, R, nu + 1)
        for nm in (10000, 40000):
            t0 = time.time()
            an = analytic_1d.solve(R, h, RHOCP, K_R, C_SHELL, src.t, src.q, src.t_end,
                                   n_modes=nm, unit_edges=edges)
            u = an["units"]
            emit(dict(scheme="1D-analytic", cell=cell, case="1D" if h == H_1D else f"1D_h{h:g}",
                      h=h, n_modes=nm, x1=float(an["x"][0]),
                      T_core_mid_C=T_AMB + an["core"], T_surf_mid_C=T_AMB + an["surf"],
                      dT_core_surface_K=an["core"] - an["surf"],
                      units_C=list(T_AMB + u), units_spread_K=float(u.max() - u.min()),
                      vol_mean_C=T_AMB + an["vol_mean"],
                      E_gen_J=an["E_gen"] * H, E_lost_J=an["E_lost"] * H, E_stored_J=an["E_stored"] * H,
                      balance_rel=an["balance_rel"], wall_s=time.time() - t0,
                      note="energies per unit height times H"))


def part_fv1d():
    for cell, mult in (("21700", (1, 2, 4, 8)), ("4680", (1, 2, 4))):
        R = GEOMS[cell]["R"]; H = GEOMS[cell]["H"]; nu = GEOMS[cell]["n_units"]
        for m in mult:
            g = VertexGrid1D(R, nu * m, H_1D)
            res = integrate(g.net, src, dt=1.0)
            th = res["th"]
            u, edges = g.unit_averages(th, nu)
            emit(dict(scheme="1D-FV", cell=cell, case="1D", Nr=g.Nr, dt=1.0,
                      T_core_mid_C=T_AMB + th[0], T_surf_mid_C=T_AMB + th[-1],
                      dT_core_surface_K=float(th[0] - th[-1]),
                      units_C=list(T_AMB + u), units_spread_K=float(u.max() - u.min()),
                      vol_mean_C=T_AMB + g.volume_mean(th),
                      E_gen_J=res["E_gen_exact"] * H, E_lost_J=res["E_lost"] * H,
                      E_stored_J=res["E_stored"] * H, balance_rel=res["balance_rel"],
                      wall_s=res["wall_s"]))


def part_timestep():
    R = GEOMS["21700"]["R"]; H = GEOMS["21700"]["H"]
    for case in ("a", "b", "d"):
        cf = CASES[case]
        g = VertexGrid2D(R, H, 90, 132, cf["h"], cf["ends_convect"])
        for dt, ran in ((4.0, True), (2.0, True), (1.0, True), (0.5, True), (0.25, True), (1.0, False)):
            res = integrate(g.net, src, dt=dt, rannacher=ran)
            emit(record_2d("V", "21700", case, g, res,
                           dict(dt=dt, rannacher=ran, study="timestep")))


def ladder(cell, levels, cases, scheme="V", dt=1.0, study="space"):
    R = GEOMS[cell]["R"]; H = GEOMS[cell]["H"]
    for case in cases:
        cf = CASES[case]
        for (Nr, Nz) in levels:
            if scheme == "V":
                g = VertexGrid2D(R, H, Nr, Nz, cf["h"], cf["ends_convect"])
            else:
                g = CellGrid2D(R, H, Nr, Nz, cf["h"], cf["ends_convect"])
            res = integrate(g.net, src, dt=dt)
            emit(record_2d(scheme, cell, case, g, res, dict(dt=dt, rannacher=True, study=study)))


def part_v21700():
    ladder("21700", [(45, 66), (90, 132), (180, 264), (360, 528)], ("a", "b", "d"))


def part_v4680():
    ladder("4680", [(111, 86), (222, 172), (444, 344)], ("a", "b"))


def part_cell():
    ladder("21700", [(90, 133), (180, 265)], ("a", "b", "d"), scheme="C", study="crosscheck")
    ladder("4680", [(222, 173), (444, 345)], ("a", "b"), scheme="C", study="crosscheck")


def part_sens():
    """rho*cp as quoted in the task text (2475540) instead of the product 2938.7*842.4."""
    for cell, (Nr, Nz) in (("21700", (180, 264)),):
        R = GEOMS[cell]["R"]; H = GEOMS[cell]["H"]
        for case in ("a", "b"):
            cf = CASES[case]
            g = VertexGrid2D(R, H, Nr, Nz, cf["h"], cf["ends_convect"], rhocp=RHOCP_TASK_TEXT)
            res = integrate(g.net, src, dt=1.0)
            emit(record_2d("V", cell, case, g, res, dict(dt=1.0, rannacher=True, study="rhocp_task_text",
                                                          rhocp=RHOCP_TASK_TEXT)))


PARTS = dict(analytic=part_analytic, fv1d=part_fv1d, timestep=part_timestep,
             v21700=part_v21700, v4680=part_v4680, cell=part_cell, sens=part_sens)

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(f"=== part {p} ===", flush=True)
        PARTS[p]()
    print("=== done ===", flush=True)
