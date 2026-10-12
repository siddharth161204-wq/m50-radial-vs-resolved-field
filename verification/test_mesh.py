"""The 21700 mesh is the two-cell study's mesh, node for node, and the field sampler reproduces P1 fields exactly.

Run: python3 verification/test_mesh.py
"""
import os, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.join(ROOT, "inputs"))
import mesh as M
import twocell_mesh_cell2 as TC
from skfem import Basis, ElementTetP1

out = {}
for ref in (1.0, 2.0):
    m_new, info, extr = M.build_mesh(0.01055, 0.0701, ref)
    m_old, info_old = TC.build_mesh(0.01055, 0.0701, ref)
    same = (m_new.p.shape == m_old.p.shape and np.array_equal(m_new.p, m_old.p) and np.array_equal(m_new.t, m_old.t))
    out[f"21700 refine {ref}: identical to the two-cell mesh"] = bool(same)
    print(f"21700 refine {ref}: {info['n_nodes']} nodes, identical to two-cell mesh: {same}")
m4, info4, extr4 = M.build_mesh(0.023, 0.08, 1.0)
print("4680:", info4)
# sampler: a field linear on every tetrahedron is reproduced exactly at random interior points
for name, (mm, ex, R, H) in {"21700": (m_new, extr, 0.01055, 0.0701), "4680": (m4, extr4, 0.023, 0.08)}.items():
    if name == "21700":
        mm, _, ex = M.build_mesh(R, H, 1.0)
    rng = np.random.default_rng(1)
    n = 20000
    r = R * np.sqrt(rng.random(n)) * 0.999; th = np.pi * rng.random(n); z = H * rng.random(n)
    x, y = r * np.cos(th), r * np.sin(th)
    S = M.FieldSampler(ex).matrix(x, y, z)
    lin = lambda X, Y, Z: 3.0 + 2e3 * X - 1e3 * Y + 5e2 * Z
    err_lin = np.abs(S @ lin(*mm.p) - lin(x, y, z)).max()
    # against scikit-fem's own interpolation for a nonlinear nodal field, on a few points
    T = np.sin(300 * mm.p[0]) + mm.p[1] ** 2 * 1e4 + np.cos(80 * mm.p[2])
    b = Basis(mm, ElementTetP1())
    k = 200 if name == "21700" else 10
    P = b.probes(np.vstack([x[:k], y[:k], z[:k]]))
    err_sk = np.abs(S[:k] @ T - P @ T).max()
    rowsum = np.abs(np.asarray(S.sum(axis=1)).ravel() - 1).max()
    print(f"{name}: linear field max error {err_lin:.2e}; against scikit-fem probes {err_sk:.2e}; row sums - 1 {rowsum:.1e}")
    out[f"{name} sampler linear error"] = float(err_lin); out[f"{name} sampler vs skfem"] = float(err_sk)
assert all(v for k, v in out.items() if "identical" in k)
assert max(v for k, v in out.items() if "sampler" in k) < 1e-9
print("PASS")
