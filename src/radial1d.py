#!/usr/bin/env python3
"""The paper's one-dimensional radial thermal model (its Eq. 2 and Eq. 4), with the units as annuli (D5, D7).

    rho_cp dT/dt = (1/r) d/dr (k_across r dT/dr) + q(t),   0 < r < R
    dT/dr = 0 at r = 0;   -k_across dT/dr = h (T - T_amb) + c_can dT/dt at r = R  (c_can = 0 in the paper's form)

P1 finite elements in r with the weight 2 pi r (per unit height), `sub` elements per unit, a lumped (row-sum)
capacity and backward Euler on steps of t_end / ceil(t_end / dt_target), the steps of the three-dimensional model.
Each unit's temperature is the annulus average of the field, integrated exactly.

Usage: python3 src/radial1d.py      (runs every registered and secondary case; writes results/radial1d*.json, .csv)
"""
import csv
import json
import math
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def load_heat(name):
    """q(t) in W/m3 of the 21700 cylinder from the DFN run `name`, as a function, and the end of discharge."""
    d = np.loadtxt(os.path.join(C.RESULTS, "heat", name + ".csv"), delimiter=",", skiprows=1)
    t, Q = d[:, 0], d[:, 3]
    V21700 = C.cell_constants("21700")["V"]
    q = Q / V21700

    def q_of_t(tt):
        return float(np.interp(tt, t, q))
    return q_of_t, float(t[-1]), (t, q)


def time_grid(t_end, dt_target=1.0):
    n = int(math.ceil(t_end / dt_target - 1e-9))
    return n, t_end / n


class Radial1D:
    def __init__(self, cell, props=None, can=True, sub=20, h=C.H_PAPER, r_in=0.0):
        """r_in > 0 gives the annulus outside a hollow core (zero flux at r_in), a secondary geometry only."""
        cc = C.cell_constants(cell, props)
        self.cc, self.cell = cc, cell
        self.R, self.n_units, self.sub = cc["R"], cc["n_units"], sub
        N = self.n_units * sub
        self.N = N
        self.r_in = r_in
        self.r = np.linspace(r_in, self.R, N + 1)
        dr = (self.R - r_in) / N
        a, b = self.r[:-1], self.r[1:]
        tp = 2 * math.pi
        # element integrals of phi_i r dr (exact) give the lumped volume weights per unit height
        wa, wb = tp * dr * (2 * a + b) / 6, tp * dr * (a + 2 * b) / 6
        w = np.zeros(N + 1)
        np.add.at(w, np.arange(N), wa)
        np.add.at(w, np.arange(1, N + 1), wb)
        self.w_vol = w                                   # m2 (volume per unit height); sums to pi R^2
        kmid = tp * cc["k_across"] * (a + b) / 2 / dr      # 2 pi k int r dr / dr^2
        rows = np.concatenate([np.arange(N), np.arange(1, N + 1), np.arange(N), np.arange(1, N + 1)])
        cols = np.concatenate([np.arange(N), np.arange(1, N + 1), np.arange(1, N + 1), np.arange(N)])
        vals = np.concatenate([kmid, kmid, -kmid, -kmid])
        self.K = sp.csr_matrix((vals, (rows, cols)), shape=(N + 1, N + 1))
        self.C = cc["rho_cp"] * w
        if can:
            self.C[-1] += cc["c_can_per_area"] * tp * self.R
        self.d_conv = np.zeros(N + 1)
        self.d_conv[-1] = h * tp * self.R
        self.h = h
        # unit-average operator: exact integral of the linear field times r over each element
        U = np.zeros((self.n_units, N + 1))
        for i in range(self.n_units):
            for e in range(i * sub, (i + 1) * sub):
                U[i, e] += wa[e]
                U[i, e + 1] += wb[e]
            U[i] /= U[i].sum()
        self.U = U
        self.unit_edges = np.linspace(r_in, self.R, self.n_units + 1)

    def run(self, q_of_t, t_end, T_amb_C, dt_target=1.0, snap_times=()):
        n, dt = time_grid(t_end, dt_target)
        snap_steps = {int(round(ts / dt)): ts for ts in snap_times}
        snaps = {}
        A = (self.K + sp.diags(self.C / dt + self.d_conv)).tocsc()
        lu = spla.splu(A)
        Ta = T_amb_C
        T = np.full(self.N + 1, Ta)
        best = {"dT": -np.inf}
        series = np.zeros((n + 1, 5))
        series[0] = [0.0, Ta, Ta, Ta, 0.0]
        E_gen = E_out = 0.0
        E0 = self.C @ T
        for k in range(n):
            t = (k + 1) * dt
            q = q_of_t(t)
            rhs = self.C / dt * T + self.d_conv * Ta + self.w_vol * q
            T = lu.solve(rhs)
            E_gen += dt * q * self.w_vol.sum()
            E_out += dt * float(self.d_conv @ (T - Ta))
            dT = T[0] - T[-1]
            series[k + 1] = [t, T[0], T[-1], float(self.w_vol @ T / self.w_vol.sum()), dT]
            if dT > best["dT"]:
                best = {"dT": dT, "t": t, "T": T.copy()}
            if (k + 1) in snap_steps:
                snaps[snap_steps[k + 1]] = self._snap(T, self.U @ T, t, every=1)
        stored = self.C @ T - E0
        units_end = self.U @ T
        units_max = self.U @ best["T"]
        res = {
            "cell": self.cell, "n_steps": n, "dt": dt, "t_end": t_end,
            "end": self._snap(T, units_end, t_end), "max_dT": self._snap(best["T"], units_max, best["t"]),
            "energy_per_m": {"generated": E_gen, "lost": E_out, "stored": stored,
                             "residual_rel": (stored + E_out - E_gen) / E_gen},
            "series": series, "snaps": snaps,
        }
        return res

    def _snap(self, T, units, t, every=5):
        rnd = lambda a: [round(float(v), 7) for v in a]
        return {"t": t, "T_core": float(T[0]), "T_surface": float(T[-1]), "dT_core_surface": float(T[0] - T[-1]),
                "units": rnd(units), "unit_spread": float(units.max() - units.min()),
                "T_mean": float(self.w_vol @ T / self.w_vol.sum()), "profile_r": rnd(self.r[::every]),
                "profile_T": rnd(T[::every])}


CASES_REGISTERED = [f"Chen2020_{('m5C' if Ta < 0 else 'p25C')}_{cr:g}C" for Ta in C.AMBIENTS_C for cr in C.C_RATES]


def amb_of(name):
    return -5.0 if "_m5C_" in name else 25.0


def main():
    props_all = C.roll_properties()
    reg_props = props_all["registered"]
    cold_props = next(r for r in props_all["table"] if r["T_C"] == -5.0)
    out = {"registered": {}, "secondary": {}}
    runs = []
    for name in CASES_REGISTERED:
        for cell in ("21700", "4680"):
            runs.append(("registered", name, cell, reg_props, True, f"{name}|{cell}"))
            runs.append(("secondary", name, cell, reg_props, False, f"{name}|{cell}|paper form without the can"))
            if amb_of(name) < 0:
                runs.append(("secondary", name, cell, cold_props, True, f"{name}|{cell}|properties at -5 C"))
        for var in ("_mixing",):
            runs.append(("secondary", name + var, "21700", reg_props, True, f"{name + var}|21700"))
            runs.append(("secondary", name + var, "4680", reg_props, True, f"{name + var}|4680"))
        alt = name.replace("Chen2020", "ORegan2022")
        runs.append(("secondary", alt, "21700", reg_props, True, f"{alt}|21700"))
        runs.append(("secondary", alt, "4680", reg_props, True, f"{alt}|4680"))
    rows = []
    for kind, name, cell, props, can, key in runs:
        q_of_t, t_end, _ = load_heat(name)
        m = Radial1D(cell, props=props, can=can)
        r = m.run(q_of_t, t_end, amb_of(name))
        r.pop("series")
        r.pop("snaps")
        out[kind][key] = r
        e, mx = r["end"], r["max_dT"]
        rows.append([kind, key, cell, t_end, e["dT_core_surface"], e["unit_spread"], e["T_core"], e["T_surface"],
                     e["T_mean"], mx["t"], mx["dT_core_surface"], mx["unit_spread"], r["energy_per_m"]["residual_rel"]])
        print(f"{kind:10s} {key:58s} end {t_end:7.1f} s  dT_cs {e['dT_core_surface']:7.4f} K  spread {e['unit_spread']:7.4f} K"
              f"  mean {e['T_mean']:7.3f} C  max dT_cs {mx['dT_core_surface']:7.4f} K at {mx['t']:7.1f} s", flush=True)
    with open(os.path.join(C.RESULTS, "radial1d.json"), "w") as f:
        json.dump(out, f)
    with open(os.path.join(C.RESULTS, "radial1d_summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "case", "cell", "t_end_s", "dT_core_surface_end_K", "unit_spread_end_K", "T_core_end_C",
                    "T_surface_end_C", "T_mean_end_C", "t_max_dT_s", "dT_core_surface_max_K", "unit_spread_at_max_K",
                    "energy_residual_rel"])
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    main()
