"""Semi-analytical solution of the 1D radial model.

rho cp th_t = k (1/r)(r th_r)_r + q(t),  0 < r < R,  th = T - T_amb, th(r, 0) = 0
at r = R:  -k th_r = h th + C_s th_t   (convection plus shell heat capacity)

Eigenfunctions J0(beta_n r), x_n = beta_n R roots of x J1(x) = (Bi - sigma x^2) J0(x),
Bi = h R / k, sigma = C_s / (rho cp R); exactly one root in each (j0_{n-1}, j0_n).
They are orthogonal in <u, w> = int rho cp u w r dr + C_s R u(R) w(R), so
th = sum a_n(t) J0(beta_n r) with a_n' = -lambda_n a_n + q(t) P_n / N_n,
lambda_n = k beta_n^2 / (rho cp), P_n = R^2 J1(x_n)/x_n,
N_n = rho cp R^2 (J0^2 + J1^2)/2 + C_s R J0^2.
The convolution with the piecewise-linear q(t) is done exactly segment by segment.
"""
import numpy as np
from scipy.special import j0, j1, jn_zeros


def roots(Bi, sigma, n_modes):
    z0 = np.concatenate([[0.0], jn_zeros(0, n_modes)])
    lo = z0[:-1].copy(); hi = z0[1:].copy()
    lo[0] = 1e-14

    def f(x):
        return x * j1(x) - (Bi - sigma * x * x) * j0(x)

    flo = f(lo); fhi = f(hi)
    assert np.all(np.sign(flo) != np.sign(fhi)), "bracket failure"
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        left = np.sign(fm) == np.sign(flo)
        lo = np.where(left, mid, lo); flo = np.where(left, fm, flo)
        hi = np.where(left, hi, mid)
        if np.max(hi - lo) < 4e-16 * np.max(hi):
            break
    return 0.5 * (lo + hi)


def solve(R, h, rhocp, k, cs, t_data, q_data, t_end, n_modes=20000, unit_edges=None):
    Bi = h * R / k
    sigma = cs / (rhocp * R)
    x = roots(Bi, sigma, n_modes)
    beta = x / R
    lam = k * beta ** 2 / rhocp
    J0x = j0(x); J1x = j1(x)
    P = R ** 2 * J1x / x
    N = rhocp * R ** 2 * (J0x ** 2 + J1x ** 2) / 2 + cs * R * J0x ** 2
    c = P / N
    # exact convolution of piecewise-linear q
    m = t_data < t_end
    tt = np.concatenate([t_data[m], [t_end]])
    qq = np.interp(tt, t_data, q_data)
    a = np.zeros_like(x)
    for kk in range(len(tt) - 1):
        D = tt[kk + 1] - tt[kk]
        zz = lam * D
        e = np.exp(-zz)
        phi1 = -np.expm1(-zz) / zz
        psi = (-np.expm1(-zz) - zz * e) / zz ** 2
        small = zz < 1e-4
        if np.any(small):
            zs = zz[small]
            phi1[small] = 1 - zs / 2 + zs ** 2 / 6
            psi[small] = 0.5 - zs / 3 + zs ** 2 / 8
        a = e * a + c * D * (qq[kk + 1] * phi1 - (qq[kk + 1] - qq[kk]) * psi)
    Iq = float(np.trapezoid(qq, tt))
    out = {}
    out["x"] = x
    out["core"] = float(np.sum(a))
    out["surf"] = float(np.sum(a * J0x))
    out["vol_mean"] = float(np.sum(a * 2 * J1x / x))
    # energy per unit height
    stored = rhocp * 2 * np.pi * np.sum(a * R * J1x / beta) + cs * 2 * np.pi * R * out["surf"]
    int_a = (c * Iq - a) / lam
    lost = h * 2 * np.pi * R * np.sum(J0x * int_a)
    gen = Iq * np.pi * R ** 2
    out.update(E_gen=gen, E_lost=float(lost), E_stored=float(stored),
               balance_rel=float((gen - lost - stored) / gen))
    if unit_edges is not None:
        ra = unit_edges[:-1]; rb = unit_edges[1:]
        Fb = (rb[:, None] * j1(beta[None, :] * rb[:, None])) / beta[None, :]
        Fa = (ra[:, None] * j1(beta[None, :] * ra[:, None])) / beta[None, :]
        num = (Fb - Fa) @ a
        out["units"] = num / ((rb ** 2 - ra ** 2) / 2)
    return out
