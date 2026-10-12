"""Convergence of the one-dimensional model in time step and in elements per unit (registered 2C, minus 5 C case).
Writes verification/check_1d_steps.json."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import radial1d as R1
out = {}
for cell in ("21700", "4680"):
    q, t_end, _ = R1.load_heat("Chen2020_m5C_2C")
    base = None
    for dt, sub in ((1.0, 20), (0.25, 20), (1.0, 5), (1.0, 40)):
        r = R1.Radial1D(cell, sub=sub).run(q, t_end, -5.0, dt_target=dt)
        e = r["end"]
        rec = {"dT_core_surface_K": e["dT_core_surface"], "unit_spread_K": e["unit_spread"], "T_mean_C": e["T_mean"],
               "energy_residual_rel": r["energy_per_m"]["residual_rel"]}
        if base is None:
            base = rec
        rec["change_dT_rel"] = rec["dT_core_surface_K"] / base["dT_core_surface_K"] - 1
        out[f"{cell} dt {dt} s, {sub} elements per unit"] = rec
        print(cell, dt, sub, json.dumps(rec))
json.dump(out, open(os.path.join(ROOT, "verification", "check_1d_steps.json"), "w"), indent=2)
