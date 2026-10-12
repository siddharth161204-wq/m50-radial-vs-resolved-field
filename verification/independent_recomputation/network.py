"""Generic conservative thermal network: C dth/dt = -K th + q(t) v, th = T - T_amb.

K = (graph Laplacian of the conductance links) + diag(h*A at convective nodes).
Time integration: Crank-Nicolson, with a Rannacher start (the first two CN steps are
replaced by four backward-Euler half steps) to damp the stiff start-up transient.
Energy bookkeeping uses the same quadrature as the scheme, so the discrete balance
closes to round-off; the reported balance also compares with the exact integral of q(t).
"""
import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


class Network:
    def __init__(self, n):
        self.n = n
        self.C = np.zeros(n)     # J/K
        self.v = np.zeros(n)     # m3 of roll that receives q(t)
        self.Gh = np.zeros(n)    # W/K convective conductance to ambient
        self._p, self._q, self._g = [], [], []

    def link(self, p, q, g):
        p = np.atleast_1d(np.asarray(p, dtype=np.int64))
        q = np.atleast_1d(np.asarray(q, dtype=np.int64))
        g = np.broadcast_to(np.asarray(g, dtype=float), p.shape).copy()
        assert p.shape == q.shape
        assert np.all(g > 0)
        self._p.append(p); self._q.append(q); self._g.append(g)

    def K(self):
        p = np.concatenate(self._p); q = np.concatenate(self._q); g = np.concatenate(self._g)
        n = self.n
        rows = np.concatenate([p, q, p, q])
        cols = np.concatenate([p, q, q, p])
        vals = np.concatenate([g, g, -g, -g])
        K = sp.coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsc()
        K = K + sp.diags(self.Gh, 0, format="csc")
        return K.tocsc()

    def check(self):
        K = self.K()
        # Conductance-only part must have zero row sums
        rs = np.asarray((K - sp.diags(self.Gh)).sum(axis=1)).ravel()
        assert np.max(np.abs(rs)) < 1e-12 * max(1.0, np.max(np.abs(K.diagonal()))), rs
        assert np.all(self.C > 0)
        return K


def time_grid(t_end, dt):
    """Uniform steps of dt from 0, last step shortened to land exactly on t_end."""
    n_full = int(np.floor(t_end / dt + 1e-9))
    t = dt * np.arange(n_full + 1)
    if t_end - t[-1] > 1e-9 * dt:
        t = np.concatenate([t, [t_end]])
    else:
        t[-1] = t_end
    return t


def integrate(net, src, dt, t_end=None, rannacher=True, probes=None, record_every=None,
              verbose=False):
    """Integrate from th = 0 to t_end. src(t) gives q in W/m3.

    Returns dict with final th, energy terms, optional probe histories.
    """
    if t_end is None:
        t_end = src.t_end
    K = net.check()
    C = net.C; v = net.v; Gh = net.Gh
    Vtot = v.sum()
    tg = time_grid(t_end, dt)
    # Build the list of (kind, t0, t1)
    steps = []
    k0 = 0
    if rannacher and len(tg) >= 3:
        t_r = tg[2]
        for m in range(4):
            steps.append(("BE", t_r * m / 4.0, t_r * (m + 1) / 4.0))
        k0 = 2
    for k in range(k0, len(tg) - 1):
        steps.append(("CN", tg[k], tg[k + 1]))

    facs = {}
    Cd = sp.diags(C, 0, format="csc")

    def get_fac(kind, h):
        key = (kind, round(h, 12))
        if key not in facs:
            tt = time.time()
            if kind == "BE":
                A = (Cd / h + K).tocsc()
            else:
                A = (Cd / h + 0.5 * K).tocsc()
            facs[key] = spla.splu(A, permc_spec="MMD_AT_PLUS_A")
            if verbose:
                print(f"    factorised {kind} dt={h:.6g} n={net.n} in {time.time()-tt:.2f}s", flush=True)
        return facs[key]

    th = np.zeros(net.n)
    E_gen = 0.0; E_lost = 0.0
    L_old = 0.0
    hist_t = [0.0]; hist = [th[probes].copy()] if probes is not None else None
    t_start = time.time()
    for (kind, t0, t1) in steps:
        h = t1 - t0
        # exact mean of the piecewise-linear q(t) over the step (equals (q0+q1)/2 when the
        # step does not straddle a sample of the heat file); keeps generated heat exact
        qbar = src.average(t0, t1)
        fac = get_fac(kind, h)
        if kind == "BE":
            rhs = C / h * th + qbar * v
            th = fac.solve(rhs)
            L_new = float(Gh @ th)
            E_lost += h * L_new
        else:
            rhs = C / h * th - 0.5 * (K @ th) + qbar * v
            th = fac.solve(rhs)
            L_new = float(Gh @ th)
            E_lost += h * 0.5 * (L_old + L_new)
        E_gen += h * qbar * Vtot
        L_old = L_new
        if probes is not None:
            hist_t.append(t1); hist.append(th[probes].copy())
    E_stored = float(C @ th)
    E_gen_exact = src.integral(t_end) * Vtot
    out = dict(
        th=th, t_end=t_end, n_steps=len(steps), wall_s=time.time() - t_start,
        E_gen_scheme=E_gen, E_gen_exact=E_gen_exact, E_lost=E_lost, E_stored=E_stored,
        balance_rel=(E_gen_exact - E_lost - E_stored) / E_gen_exact,
        balance_rel_scheme=(E_gen - E_lost - E_stored) / E_gen,
    )
    if probes is not None:
        out["hist_t"] = np.array(hist_t); out["hist"] = np.array(hist)
    return out
