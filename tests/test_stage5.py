"""Tests of the Stage 5 machinery (python3 -m pytest tests/test_stage5.py, or python3 tests/test_stage5.py).

They check the identities the procedure rests on (DECISIONS.md D29, D30), not the registered results."""
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
import radial1d as R1  # noqa: E402
import stage5_common as S5  # noqa: E402
import stage5_kernels as K5  # noqa: E402


def test_groups():
    for N, G in ((45, 15), (111, 15), (45, 30)):
        e = S5.group_edges(N, G)
        assert e[0] == 0 and e[-1] == N and all(b > a for a, b in zip(e, e[1:]))
        assert abs(S5.group_weights(N, G).sum() - 1) < 1e-14
        A = S5.unit_to_group_matrix(N, G)
        assert np.allclose(A.sum(axis=1), 1)


def test_convolution_reproduces_the_solver_1d():
    """A heat history that differs from group to group, stepped directly with Stage 1's matrices, equals the
    convolution of its increments with the step responses (D29)."""
    m = R1.Radial1D("21700")
    G, dt, n = 5, 1.0, 400
    mm = {"m": m, "kind": "1d"}
    L, b, _ = K5.loads(mm, G)
    A = (m.K + sp.diags(m.C / dt + m.d_conv)).tocsc()
    lu = spla.splu(A)
    rng = np.random.default_rng(1)
    q = np.cumsum(rng.normal(0, 2e3, (n, G)), axis=0) + 1e5
    T = np.zeros(m.N + 1)
    direct = []
    for k in range(n):
        T = lu.solve(m.C / dt * T + L @ q[k])
        direct.append(S5.unit_to_group_matrix(m.n_units, G) @ (m.U @ T))
    th = np.zeros((m.N + 1, G))
    S = []
    for k in range(n):
        th = lu.solve((m.C / dt)[:, None] * th + L)
        S.append(S5.unit_to_group_matrix(m.n_units, G) @ (m.U @ th))
    S = np.array(S)
    conv = S5.conv_series(S, S[-1], q)
    assert np.abs(conv - np.array(direct)).max() < 1e-9 * np.abs(direct).max()
    inc = S5.Convolver(S, S[-1])
    for k in range(n):
        v = inc.push(q[k])
    assert np.abs(v - conv[-1]).max() < 1e-12 * np.abs(conv).max()


def test_cut_integrals_partition():
    """The adaptive integration over a triangle split by circles sums to the whole triangle's integrals."""
    pts = np.array([[0.0, 0.0], [1.0, 0.1], [0.3, 0.9]])
    tris = np.array([[0, 1, 2]])
    I, info = K5.cut_integrals(pts, tris, np.array([0.0, 0.35, 0.7, np.inf]), depth=8)
    area = 0.5 * abs(1.0 * 0.9 - 0.1 * 0.3)
    assert np.abs(I.sum(axis=1)[0] - area * K5.QUAD).max() < 1e-13
    assert (I[0].sum(axis=1) > 0).all()


if __name__ == "__main__":
    for name, f in list(globals().items()):
        if name.startswith("test_"):
            f()
            print(name, "passed")
