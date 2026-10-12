"""The resolved cell: the two-cell study's scikit-fem cell with a uniform volumetric source (D8, D9).

Field equation in the roll (half cylinder, zero flux on the plane of symmetry):
    rho_cp dT/dt = div(K grad T) + q(t),   K = k_across e_r e_r^T + k_theta e_t e_t^T + k_along e_z e_z^T
The two-cell study had k_theta = k_along. Every field here is axisymmetric, so k_theta cannot change the exact
solution, and it is set to k_across (D13): with k_along, the coarse triangles near the axis, which are not aligned
with the radius, let a twenty-fold circumferential conductivity carry heat across them, and V1 failed by 1.7 %.
The can is a 0.25 mm steel shell carrying in-plane conduction k t and its heat capacity, on every outer surface
(on the lateral surface only in the V1 equivalence run). Convection h (T_amb - T) acts on the surfaces named by the
boundary condition; in (c) two strips connect the cap disc and the base annulus to busbars at the ambient. Capacity
is lumped (row sums), time stepping is backward Euler on t_end / ceil(t_end / 1 s), and every boundary and capacity
weight is normalised so that a uniform field reproduces the exact totals of the cylinder (V0, verification/).

Boundary conditions:
    a_eq : convection on the lateral surface, ends adiabatic, can on the lateral surface only (V1)
    a    : convection on the lateral surface, ends adiabatic, can on every surface
    b    : convection on every outer surface
    c    : as b, plus the two strips (G_STRIP each) to busbars at the ambient
    d    : as b with h = 25 W/(m2 K)
"""
import math
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from skfem import Basis, FacetBasis, ElementTetP1, BilinearForm, LinearForm, asm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import mesh as M  # noqa: E402

BCS = {
    "a_eq": {"conv": ("lateral",), "shell": ("lateral",), "h": C.H_PAPER, "tabs": False},
    "a": {"conv": ("lateral",), "shell": ("lateral", "top", "bottom"), "h": C.H_PAPER, "tabs": False},
    "b": {"conv": ("lateral", "top", "bottom"), "shell": ("lateral", "top", "bottom"), "h": C.H_PAPER, "tabs": False},
    "c": {"conv": ("lateral", "top", "bottom"), "shell": ("lateral", "top", "bottom"), "h": C.H_PAPER, "tabs": True},
    "d": {"conv": ("lateral", "top", "bottom"), "shell": ("lateral", "top", "bottom"), "h": C.H_AIR, "tabs": False},
}


class _Direct:
    def __init__(self, A):
        self.lu = spla.splu(A.tocsc(), permc_spec="MMD_AT_PLUS_A", diag_pivot_thresh=0.0,
                            options=dict(SymmetricMode=True))
        self.kind = "SuperLU"
        self.iters = []

    def solve(self, b, x0=None):
        return self.lu.solve(b)


class _AMGCG:
    def __init__(self, A, tol=1e-12):
        import pyamg
        self.A = A.tocsr()
        self.ml = pyamg.smoothed_aggregation_solver(self.A, symmetry="symmetric", max_coarse=500)
        self.M = self.ml.aspreconditioner(cycle="V")
        self.tol = tol
        self.kind = f"PCG with smoothed-aggregation AMG (pyamg), relative residual {tol:g}"
        self.iters = []

    def solve(self, b, x0=None):
        it = [0]

        def cb(xk):
            it[0] += 1
        x, info = spla.cg(self.A, b, x0=x0, rtol=self.tol, atol=0.0, M=self.M, maxiter=2000, callback=cb)
        if info != 0:
            raise RuntimeError(f"CG did not converge (info {info})")
        self.iters.append(it[0])
        return x


class Cell3D:
    def __init__(self, cell, bc, props=None, refine=1.0, solver="auto", k_theta="across"):
        self.cell, self.bc_name = cell, bc
        bcd = BCS[bc]
        self.bcd = bcd
        cc = C.cell_constants(cell, props)
        self.cc = cc
        R, H = cc["R"], cc["H"]
        self.R, self.H = R, H
        t0 = time.time()
        self.mesh, self.mesh_info, self.extr = M.build_mesh(R, H, refine)
        m = self.mesh
        e = ElementTetP1()
        self.vb = Basis(m, e)
        g = M.classify_facets(m, R, H)
        self.groups = g
        surf = {"lateral": g["lateral"], "top": g["top"], "bottom": g["bottom"], "top_disc": g["top_disc"],
                "bottom_annulus": g["bottom_annulus"]}
        fb = {k: FacetBasis(m, e, facets=v) for k, v in surf.items()}
        kr, kz = cc["k_across"], cc["k_along"]
        kth = kz if k_theta == "along" else kr
        self.k_theta = k_theta

        @BilinearForm
        def conduction(u, v, w):
            x, y = w.x[0], w.x[1]
            r = np.sqrt(x ** 2 + y ** 2) + 1e-15
            ex, ey = x / r, y / r
            gu, gv = u.grad, v.grad
            ur = ex * gu[0] + ey * gu[1]
            vr = ex * gv[0] + ey * gv[1]
            ut = -ey * gu[0] + ex * gu[1]
            vt = -ey * gv[0] + ex * gv[1]
            return kz * gu[2] * gv[2] + kr * ur * vr + kth * ut * vt

        kt = cc["k_can_t"]

        @BilinearForm
        def shell(u, v, w):
            n = w.n
            gu, gv = u.grad, v.grad
            un = gu[0] * n[0] + gu[1] * n[1] + gu[2] * n[2]
            vn = gv[0] * n[0] + gv[1] * n[1] + gv[2] * n[2]
            return kt * sum((gu[i] - un * n[i]) * (gv[i] - vn * n[i]) for i in range(3))

        @LinearForm
        def one(v, w):
            return v

        self.K_roll = asm(conduction, self.vb).tocsr()
        shell_facets = np.concatenate([surf[s] for s in bcd["shell"]])
        self.K_shell = asm(shell, FacetBasis(m, e, facets=shell_facets)).tocsr()
        self.K = (self.K_roll + self.K_shell).tocsr()
        self.w_vol = asm(one, self.vb)
        self.w = {k: asm(one, b) for k, b in fb.items()}
        A_exact = {"lateral": cc["A_lateral"], "top": cc["A_end"], "bottom": cc["A_end"],
                   "top_disc": math.pi * C.R_TAB_DISC ** 2, "bottom_annulus": math.pi * (R ** 2 - C.R_TAB_ANN_IN ** 2)}
        self.A_exact = A_exact
        half = lambda k: self.w[k] / (2 * self.w[k].sum())        # sums to 1/2: the half model's share
        self.V_exact = cc["V"]
        self.w_src = self.w_vol / (2 * self.w_vol.sum())           # times Q in W (full cell)
        cap = cc["rho_cp"] * self.V_exact * self.w_src * 1.0
        for s in bcd["shell"]:
            cap = cap + cc["c_can_per_area"] * A_exact[s] * half(s)
        self.Cap = cap
        d = np.zeros_like(self.w_vol)
        for s in bcd["conv"]:
            d = d + bcd["h"] * A_exact[s] * half(s)
        self.d_conv = d
        self.d_tab = (C.G_STRIP * (half("top_disc") + half("bottom_annulus"))) if bcd["tabs"] else 0.0 * d
        self.geom = {"volume_mesh": 2 * self.w_vol.sum(), "volume_exact": self.V_exact,
                     **{f"A_{k}_mesh": 2 * self.w[k].sum() for k in surf}, **{f"A_{k}_exact": v for k, v in A_exact.items()},
                     "C_total_model": 2 * self.Cap.sum(),
                     "C_total_expected": cc["C_roll"] + sum(cc["c_can_per_area"] * A_exact[s] for s in bcd["shell"])}
        p = m.p
        self.r_node = np.hypot(p[0], p[1])
        self.z_node = p[2]
        n2, zl = self.extr["n2"], self.extr["z"]
        self.n2, self.zl = n2, zl
        self.k_mid = int(np.argmin(np.abs(zl - H / 2)))
        assert abs(zl[self.k_mid] - H / 2) < 1e-12
        self.i_core_mid = self.k_mid * n2
        self.i_core_bottom = 0
        self.i_core_top = (len(zl) - 1) * n2
        lay = np.arange(self.k_mid * n2, (self.k_mid + 1) * n2)
        self.i_surf_mid = lay[np.abs(self.r_node[lay] - R) < 1e-12]
        self.solver_pref = solver
        self.build_s = time.time() - t0
        self._samplers = None

    # ---------------------------------------------------------------------------------------------------------
    def samplers(self, n_units=None, ng=10, dz=0.1e-3, angles=4, r_profile=None):
        """Sparse operators: unit (annulus, full height) averages, the mid-height radial profile, the core line."""
        if self._samplers is not None:
            return self._samplers
        R, H = self.R, self.H
        n_units = n_units or self.cc["n_units"]
        S = M.FieldSampler(self.extr)
        th = (np.arange(angles) + 0.5) * math.pi / angles
        gx, gw = np.polynomial.legendre.leggauss(ng)
        nz = int(round(H / dz)) + 1
        zs = np.linspace(0.0, H, nz)
        wz = np.full(nz, 1.0)
        wz[0] = wz[-1] = 0.5
        edges = np.linspace(0.0, R, n_units + 1)
        rows = []
        for i in range(n_units):
            a, b = edges[i], edges[i + 1]
            rr = 0.5 * (a + b) + 0.5 * (b - a) * gx
            wr = gw * rr
            Rg, Tg, Zg = np.meshgrid(rr, th, zs, indexing="ij")
            W = (wr[:, None, None] * np.ones_like(Tg) * wz[None, None, :]).ravel()
            Mi = S.matrix((Rg * np.cos(Tg)).ravel(), (Rg * np.sin(Tg)).ravel(), Zg.ravel())
            rows.append(sp.csr_matrix((W / W.sum()) @ Mi))
        U = sp.vstack(rows).tocsr()
        if r_profile is None:
            r_profile = np.linspace(0.0, R, 211 if self.cell == "21700" else 461)
        Rg, Tg = np.meshgrid(r_profile, th, indexing="ij")
        Pm = S.matrix((Rg * np.cos(Tg)).ravel(), (Rg * np.sin(Tg)).ravel(), np.full(Rg.size, H / 2))
        avg = sp.kron(sp.eye(len(r_profile)), np.full((1, angles), 1.0 / angles))
        Prof = (avg @ Pm).tocsr()
        rings = np.concatenate([[0.0], self.extr["rings"]])
        Rg2, Tg2 = np.meshgrid(rings, th, indexing="ij")
        Pr = S.matrix((Rg2 * np.cos(Tg2)).ravel(), (Rg2 * np.sin(Tg2)).ravel(), np.full(Rg2.size, H / 2))
        avg2 = sp.kron(sp.eye(len(rings)), np.full((1, angles), 1.0 / angles))
        ProfRings = (avg2 @ Pr).tocsr()
        core_idx = np.arange(len(self.zl)) * self.n2
        self._samplers = {"U": U, "unit_edges": edges, "Prof": Prof, "r_profile": r_profile,
                          "ProfRings": ProfRings, "r_rings": rings, "core_idx": core_idx, "z_core": self.zl.copy()}
        return self._samplers

    def snapshot(self, T, t):
        s = self.samplers()
        units = s["U"] @ T
        core = T[s["core_idx"]]
        imax = int(np.argmax(T))
        T_surf = float(T[self.i_surf_mid].mean())
        out = {
            "t": t, "T_core_mid": float(T[self.i_core_mid]), "T_surface_mid": T_surf,
            "dT_core_surface": float(T[self.i_core_mid] - T_surf),
            "dT_axial_bottom": float(T[self.i_core_mid] - T[self.i_core_bottom]),
            "dT_axial_top": float(T[self.i_core_mid] - T[self.i_core_top]),
            "hottest": {"T": float(T[imax]), "r_mm": float(1e3 * self.r_node[imax]), "z_mm": float(1e3 * self.z_node[imax])},
            "T_mean": float(self.Cap @ T / self.Cap.sum()), "T_roll_mean": float(self.w_vol @ T / self.w_vol.sum()),
            "units": units.tolist(), "unit_spread": float(units.max() - units.min()),
            "profile_r": s["r_profile"].tolist(), "profile_T": (s["Prof"] @ T).tolist(),
            "rings_r": s["r_rings"].tolist(), "rings_T": (s["ProfRings"] @ T).tolist(),
            "core_z": s["z_core"].tolist(), "core_T": core.tolist(),
        }
        out["dT_axial"] = max(out["dT_axial_bottom"], out["dT_axial_top"])
        return out

    def run(self, q_of_t, t_end, T_amb_C, dt_target=1.0, series_every=10.0, verbose=False):
        n = int(math.ceil(t_end / dt_target - 1e-9))
        dt = t_end / n
        d_out = self.d_conv + self.d_tab
        A = (self.K + sp.diags(self.Cap / dt + d_out)).tocsr()
        t0 = time.time()
        pref = self.solver_pref
        if pref == "direct" or (pref == "auto" and A.shape[0] < 100000):
            solver = _Direct(A)
        else:
            solver = _AMGCG(A)
        t_fact = time.time() - t0
        Ta = T_amb_C
        T = np.full(A.shape[0], Ta)
        E0 = float(self.Cap @ T)
        E_gen = E_out = 0.0
        best = {"dT": -np.inf}
        series = []
        every = max(1, int(round(series_every / dt)))
        t1 = time.time()
        T_prev = T.copy()
        for k in range(n):
            t = (k + 1) * dt
            Q = q_of_t(t) * self.V_exact
            rhs = self.Cap / dt * T + d_out * Ta + self.w_src * Q
            x0 = 2 * T - T_prev                      # linear extrapolation as the iterative solver's first guess
            T_prev = T
            T = solver.solve(rhs, x0=x0)
            E_gen += dt * Q / 2
            E_out += dt * float(d_out @ (T - Ta))
            Ts = T[self.i_surf_mid].mean()
            dT = T[self.i_core_mid] - Ts
            if dT > best["dT"]:
                best = {"dT": dT, "t": t, "T": T.copy()}
            if (k + 1) % every == 0 or k == n - 1:
                series.append([t, T[self.i_core_mid], Ts, dT, T[self.i_core_mid] - T[self.i_core_bottom],
                               T[self.i_core_mid] - T[self.i_core_top], T.max(), float(self.Cap @ T / self.Cap.sum())])
            if verbose and (k + 1) % 200 == 0:
                print(f"  step {k+1}/{n} t {t:.0f} s dT_cs {dT:.4f} K", flush=True)
        t_loop = time.time() - t1
        stored = float(self.Cap @ T) - E0
        res = {
            "cell": self.cell, "bc": self.bc_name, "n_nodes": int(A.shape[0]), "mesh": self.mesh_info,
            "geom": self.geom, "solver": solver.kind, "n_steps": n, "dt": dt, "t_end": t_end,
            "timing_s": {"build": self.build_s, "factorise": t_fact, "loop": t_loop},
            "cg_iterations_mean": float(np.mean(solver.iters)) if solver.iters else None,
            "energy_J": {"generated": 2 * E_gen, "lost": 2 * E_out, "stored": 2 * stored,
                         "residual_rel": (stored + E_out - E_gen) / E_gen if E_gen else None},
            "end": self.snapshot(T, t_end), "max_dT": self.snapshot(best["T"], best["t"]),
            "series_columns": ["t_s", "T_core_mid", "T_surface_mid", "dT_core_surface", "dT_axial_bottom",
                               "dT_axial_top", "T_max", "T_mean"],
            "series": np.array(series).tolist(),
        }
        return res, T
