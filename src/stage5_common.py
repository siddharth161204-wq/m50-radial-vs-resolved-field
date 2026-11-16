"""Stage 5: definitions shared by the kernels, the coupled solve and the report (DECISIONS.md D27 to D33).

Groups of neighbouring units (D28, D29), the time grids (D28), the kernel files and the convolution (D29):
    T(k) - T_amb = sum over m = 1..k of S(k - m + 1) (q(m) - q(m - 1)),   q(0) = 0,
with S the step response on the solver's own grid, held at its steady value S_inf past the stored steps.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

G_REG = 15                                  # D28: groups in both cells
KDIR = os.path.join(C.RESULTS, "stage5_kernels")
RUNDIR = os.path.join(C.RESULTS, "stage5_runs")
V21700 = C.cell_constants("21700")["V"]     # D6, D30: heat per unit volume of the 21700 cylinder in both cells
C_SPEC_A = 4.85                             # D27, D32: the specification's 1C (its 0.3C is 1,455 mA)
C_STUDY_A = C.NOMINAL_AH                    # the sets' nominal 5 A h: the C of Part C and of Stages 1 to 4

# registered heats and the grids they fix (D28): t_end / ceil(t_end / 1 s)
DISCHARGE_HEATS = {"m5C_2C": "Chen2020_m5C_2C", "p25C_2C": "Chen2020_p25C_2C",
                   "p25C_1.25C": "Chen2020_p25C_1.25C", "p25C_3C": "Chen2020_p25C_3C"}


def unit_weights(N):
    """D24: w_i = (r_(i+1)^2 - r_i^2) / R^2 for equal-thickness annuli."""
    i = np.arange(1, N + 1)
    return (2 * i - 1) / N ** 2


def group_edges(N, G):
    """D28: group k holds units edges[k] + 1 .. edges[k + 1] (1-based); edges at the nearest integer to k N / G."""
    return [int(math.floor(k * N / G + 0.5)) for k in range(G + 1)]


def group_weights(N, G):
    w = unit_weights(N)
    e = group_edges(N, G)
    return np.array([w[e[k]:e[k + 1]].sum() for k in range(G)])


def unit_to_group_matrix(N, G):
    """A (G x N) with T_g = A T_units: the area-weighted mean of each group's units (D29)."""
    w = unit_weights(N)
    e = group_edges(N, G)
    A = np.zeros((G, N))
    for k in range(G):
        A[k, e[k]:e[k + 1]] = w[e[k]:e[k + 1]] / w[e[k]:e[k + 1]].sum()
    return A


def heat_series(heat):
    """The registered heat as Stage 1 reads it (radial1d.load_heat): q(t) in W/m3 of the 21700 cylinder."""
    d = np.loadtxt(os.path.join(C.RESULTS, "heat", heat + ".csv"), delimiter=",", skiprows=1)
    return d[:, 0], d[:, 3] / V21700


def grid(name):
    """(dt, n_archive, t_end). Discharge grids are the registered heats' (D28); 'charge10' is the 10 s charge
    grid. A suffix '_half' halves the step (V3)."""
    half = name.endswith("_half")
    base = name[:-5] if half else name
    if base in DISCHARGE_HEATS:
        t, _ = heat_series(DISCHARGE_HEATS[base])
        t_end = float(t[-1])
        n = int(math.ceil(t_end / 1.0 - 1e-9))
        dt = t_end / n
    elif base == "charge10":
        dt, n, t_end = 10.0, 0, 0.0
    else:
        raise KeyError(name)
    if half:
        dt, n = dt / 2, 2 * n
    return dt, n, t_end


def registered_heat_on_grid(gridname):
    """q at the end of each step of the grid, as Stage 1's solvers sample it (np.interp at t = k dt)."""
    base = gridname[:-5] if gridname.endswith("_half") else gridname
    t, q = heat_series(DISCHARGE_HEATS[base])
    dt, n, _ = grid(gridname)
    tk = dt * np.arange(1, n + 1)
    return np.interp(tk, t, q)


def kernel_path(model, bc, cell, gridname, G=G_REG):
    return os.path.join(KDIR, f"{model}_{bc}_{cell}_{gridname}_G{G}.npz")


def conv_series(S, S_inf, q):
    """Full-history convolution. S (K, O, J) step responses, S_inf (O, J), q (n, J) heats at steps 1..n.
    Returns the rises (n, O) at steps 1..n."""
    S = np.asarray(S, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    if q.ndim == 1:
        q = q[:, None]
    n, J = q.shape
    K = S.shape[0]
    dq = np.diff(np.concatenate([np.zeros((1, J)), q]), axis=0)
    out = np.zeros((n, S.shape[1]))
    for k in range(1, n + 1):
        lo = max(1, k - K + 1)
        lags = k - np.arange(lo, k + 1) + 1               # lags of m = lo..k, each in 1..K
        out[k - 1] = np.einsum("loj,lj->o", S[lags - 1], dq[lo - 1:k])
        if lo > 1:                                        # sum_{m < lo} S_inf dq(m) = S_inf q(lo - 1)
            out[k - 1] += S_inf @ q[lo - 2]
    return out


class Convolver:
    """Incremental convolution for the stepwise coupled solve: push the heat of step k (J values), get the rise at
    step k (O values)."""

    def __init__(self, S, S_inf, nmax=200000):
        self.S = np.asarray(S, dtype=np.float64)
        self.S_inf = np.asarray(S_inf, dtype=np.float64)
        self.K, self.O, self.J = self.S.shape
        self.q = np.zeros((nmax + 1, self.J))     # q[0] = 0, q[m] = heat of step m
        self.k = 0

    def push(self, q_k):
        self.k += 1
        k = self.k
        self.q[k] = np.atleast_1d(np.asarray(q_k, dtype=np.float64))
        lo = max(1, k - self.K + 1)
        lags = k - np.arange(lo, k + 1) + 1
        dq = self.q[lo:k + 1] - self.q[lo - 1:k]
        v = np.einsum("loj,lj->o", self.S[lags - 1], dq)
        if lo > 1:
            v = v + self.S_inf @ self.q[lo - 1]
        return v


class Kernel:
    """Step responses of one thermal model on one grid (D29), as stored in results/stage5_kernels.
    S_group[k - 1] is the (G x G) rise of the group means at step k for 1 W/m3 in each group from step 1 on."""

    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.path = path
        self.meta = json.loads(str(z["meta"]))
        self.dt = float(self.meta["dt"])
        self.G = int(self.meta["G"])
        self.N = int(self.meta["N"])
        self.S_group = z["S_group"].astype(np.float64)                  # (K, G, G)
        self.S_inf_group = z["S_inf_group"].astype(np.float64)          # (G, G)
        self.S_unit_uniform = z["S_unit_uniform"].astype(np.float64)    # (K, N)
        self.S_inf_unit_uniform = z["S_inf_unit_uniform"].astype(np.float64)
        self.S_unit = z["S_unit"].astype(np.float64) if "S_unit" in z.files else None        # (K, N, G)
        self.S_inf_unit = z["S_inf_unit"].astype(np.float64) if "S_inf_unit" in z.files else None
        self.K = self.S_group.shape[0]
        self.W = group_weights(self.N, self.G)
        # the volume-averaged (area-weighted) temperature's response to uniform heat (D30)
        self.S_ave = np.einsum("g,kgj->k", self.W, self.S_group)
        self.S_inf_ave = float(self.W @ self.S_inf_group.sum(axis=1))

    def group_convolver(self):
        return Convolver(self.S_group, self.S_inf_group)

    def ave_convolver(self):
        return Convolver(self.S_ave[:, None, None], np.array([[self.S_inf_ave]]))

    def uniform_group_convolver(self):
        """Every group heated at one rate: response of the group means."""
        return Convolver(self.S_group.sum(axis=2)[:, :, None], self.S_inf_group.sum(axis=1)[:, None])
