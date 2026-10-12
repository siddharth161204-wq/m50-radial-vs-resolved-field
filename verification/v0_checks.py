"""V0: checks of the three-dimensional cell that carry no information about the study's fields (run before the
predictions are public). For every boundary condition and both geometries:
  1. conduction and shell operators annihilate a uniform field (row sums zero);
  2. the model's heat capacity, convective conductance, strip conductance and source weights reproduce the exact
     totals of the cylinder;
  3. a pure-conduction relaxation from a random initial field, with every loss switched off and no source,
     conserves energy to round-off and tends to the uniform mean; it also times the solvers.
Writes verification/v0_checks.json.
"""
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import common as C
from cell3d import Cell3D, BCS, _Direct, _AMGCG

out = {}
for cell, refine in (("21700", 1.0), ("4680", 1.0), ("21700", 2.0)):
    bcs = BCS.keys() if (cell == "21700" and refine == 1.0) else ("b",)
    for bc in bcs:
        m = Cell3D(cell, bc, refine=refine)
        cc = m.cc
        one = np.ones(m.K.shape[0])
        rec = {"n_nodes": m.mesh_info["n_nodes"], "build_s": round(m.build_s, 1)}
        rec["K_uniform_max_abs_rowsum_rel"] = float(np.abs(m.K @ one).max() / np.abs(m.K).max())
        rec["C_total_model"] = 2 * m.Cap.sum(); rec["C_total_expected"] = m.geom["C_total_expected"]
        rec["conv_total_model"] = 2 * m.d_conv.sum()
        rec["conv_total_expected"] = sum(BCS[bc]["h"] * m.A_exact[s] for s in BCS[bc]["conv"])
        rec["tab_total_model"] = 2 * float(np.sum(m.d_tab)); rec["tab_total_expected"] = 2 * C.G_STRIP if BCS[bc]["tabs"] else 0.0
        rec["source_weights_sum"] = float(2 * m.w_src.sum())
        rec["volume_mesh_over_exact"] = m.geom["volume_mesh"] / m.geom["volume_exact"]
        ok = (rec["K_uniform_max_abs_rowsum_rel"] < 1e-10 and abs(rec["C_total_model"] / rec["C_total_expected"] - 1) < 1e-12
              and abs(rec["conv_total_model"] / rec["conv_total_expected"] - 1) < 1e-12
              and abs(rec["tab_total_model"] - rec["tab_total_expected"]) < 1e-15 and abs(rec["source_weights_sum"] - 1) < 1e-12)
        rec["totals_pass"] = bool(ok)
        if bc == "b":
            # pure conduction relaxation, everything else off: (C/dt + K) T+ = C/dt T
            dt, nsteps = 1.0, 30
            A = (m.K + sp.diags(m.Cap / dt)).tocsr()
            t0 = time.time()
            solv = _Direct(A) if A.shape[0] < 100000 else _AMGCG(A)
            tf = time.time() - t0
            rng = np.random.default_rng(7)
            T = 20.0 + 5.0 * rng.random(A.shape[0])
            E0 = float(m.Cap @ T); mean0 = E0 / m.Cap.sum(); spread0 = T.max() - T.min()
            t0 = time.time()
            for k in range(nsteps):
                T = solv.solve(m.Cap / dt * T, x0=T)
            per_step = (time.time() - t0) / nsteps
            rec["relax"] = {"solver": solv.kind, "factorise_s": round(tf, 2), "s_per_step": round(per_step, 4),
                            "energy_drift_rel": float((m.Cap @ T - E0) / E0), "spread_before_K": float(spread0),
                            "spread_after_30_s_K": float(T.max() - T.min()),
                            "cg_iter_mean": float(np.mean(solv.iters)) if solv.iters else None}
        out[f"{cell} refine {refine:g} bc {bc}"] = rec
        print(f"{cell} refine {refine:g} bc {bc}: {json.dumps(rec)}", flush=True)
assert all(v["totals_pass"] for v in out.values())
assert all(abs(v["relax"]["energy_drift_rel"]) < 1e-9 for v in out.values() if "relax" in v)
json.dump(out, open(os.path.join(ROOT, "verification", "v0_checks.json"), "w"), indent=2)
print("PASS")
