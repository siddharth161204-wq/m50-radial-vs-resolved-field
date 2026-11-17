"""Tests of the Stage 5 machinery (python3 -m pytest tests/test_stage5.py, or python3 tests/test_stage5.py).

They check the identities and rules the procedure rests on (DECISIONS.md D29, D30, D32), not the registered results."""
import math
import os
import sys
import types

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


def test_search_follows_d32():
    """The plating-limited rate search (D32) on a synthetic margin that stays at or above zero up to 0.3137C: the
    scan by 0.05C, three halvings to 0.00625C, the refinement to 0.001C, and the coupled scan's start."""
    os.environ.pop("STAGE5_TRIAL_CACHE", None)
    import stage5_runs as RN
    edge = 0.3137
    seen = []

    def fake_trial(cell, pset, Ta, rate, kern, single):
        seen.append(round(rate, 6))
        ok = rate <= edge
        return {"rate": round(rate, 6), "passed": ok, "status": "event" if ok else "negative margin",
                "min_margin_V": 0.01 if ok else -0.01, "group": 1, "t_min_s": 0.0, "wall_s": 0.0}
    real = RN.trial
    RN.trial = fake_trial
    try:
        s = RN.search("21700", "Chen2020", 0.0, None, True, 0.05, fine=True)
        assert np.allclose(seen, [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.325, 0.3125, 0.31875, 0.315625, 0.3140625,
                                  0.31328125], rtol=0, atol=1e-6)
        assert math.isclose(s["rate"], 0.3125) and math.isclose(s["fail_above"], 0.31875)
        assert math.isclose(s["fine_rate"], 0.31328125) and s["fine_width"] <= 0.001
        start = max(0.05, math.floor((s["rate"] - 0.10) * 100 + 1e-9) / 100)      # the coupled scan's start
        assert math.isclose(start, 0.21)
        seen.clear()
        c = RN.search("21700", "Chen2020", 0.0, None, False, start)
        assert seen == [0.21, 0.26, 0.31, 0.36, 0.335, 0.3225, 0.31625]
        assert math.isclose(c["rate"], 0.31) and math.isclose(c["fail_above"], 0.31625)
        seen.clear()
        d = RN.search("21700", "Chen2020", 0.0, None, False, 0.40)                  # a start that fails steps down
        assert seen[:3] == [0.4, 0.35, 0.3] and math.isclose(d["rate"], 0.3125)
    finally:
        RN.trial = real


def test_coupled_equals_single_at_one_temperature():
    """With every group at one temperature the coupled system draws the same current in every group and follows the
    single DFN (V2 in small: two groups, Chen2020, 1C discharge for 60 s at 25 C)."""
    import stage5_coupled as SC
    kern = types.SimpleNamespace(N=45, G=2, dt=1.0, path="test")
    I = 5.0
    c = SC.run("discharge", "21700", "Chen2020", 25.0, I, kern, heat="fixed", fixed_T=lambda k: np.full(2, 25.0),
               max_steps=60)
    s = SC.run("discharge", "21700", "Chen2020", 25.0, I, kern, heat="fixed", fixed_T=lambda k: np.full(1, 25.0),
               single=True, max_steps=60)
    assert len(c["t"]) == len(s["t"]) == 61
    assert np.abs(c["V"] - s["V"]).max() < 1e-5
    assert np.abs(c["I"] / I - 1).max() < 1e-6
    assert c["resid"].max() < 1e-9


if __name__ == "__main__":
    for name, f in list(globals().items()):
        if name.startswith("test_"):
            f()
            print(name, "passed")
