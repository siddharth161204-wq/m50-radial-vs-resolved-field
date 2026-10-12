"""Constants and heat-source handling for the independent radial-vs-3D check.

Everything here is typed in from the task statement; nothing is imported from the study.
"""
import numpy as np

HEAT_CSV = "/home/claude/m50-radial-vs-resolved-field/results/heat/Chen2020_m5C_2C.csv"

# Jelly roll
RHO = 2938.7            # kg/m3
CP = 842.4              # J/(kg K)
RHOCP = RHO * CP        # = 2475560.88 J/(m3 K); the task text quotes 2475540 (8.5 ppm lower)
RHOCP_TASK_TEXT = 2475540.0
K_R = 1.2251            # W/(m K), across the layers (radial)
K_Z = 25.092            # W/(m K), along the layers (axial)

# Can (thin steel shell, modelled as a surface layer in perfect contact)
KT_SHELL = 15.0 * 0.25e-3   # W/K, in-plane conductance k*t
C_SHELL = 841.7358          # J/(m2 K), heat capacity per unit outer area

T_INIT = -5.0           # C
T_AMB = -5.0            # C

GEOMS = {
    "21700": dict(R=10.55e-3, H=70.1e-3, n_units=45),
    "4680": dict(R=23.0e-3, H=80.0e-3, n_units=111),
}
# Reference volume used to turn Q(t) [W] into q(t) [W/m3] for BOTH cells
V_REF = np.pi * 0.01055 ** 2 * 0.0701

# Boundary-condition cases for the 3D (r, z) model
CASES = {
    "a": dict(h=400.0, ends_convect=False),
    "b": dict(h=400.0, ends_convect=True),
    "d": dict(h=25.0, ends_convect=True),
}
H_1D = 400.0


def load_heat(path=HEAT_CSV):
    d = np.genfromtxt(path, delimiter=",", names=True)
    t = np.asarray(d["t_s"], dtype=float)
    Q = np.asarray(d["heat_total_W"], dtype=float)
    assert np.all(np.diff(t) > 0)
    return t, Q


class HeatSource:
    """q(t) in W/m3, piecewise linear in time between the samples of the heat file."""

    def __init__(self, path=HEAT_CSV):
        self.t, self.Q = load_heat(path)
        self.q = self.Q / V_REF
        self.t_end = float(self.t[-1])

    def __call__(self, tt):
        return np.interp(tt, self.t, self.q)

    def integral(self, t_end=None):
        """Exact integral of the piecewise-linear q(t) from 0 to t_end, J/m3."""
        if t_end is None:
            t_end = self.t_end
        m = self.t < t_end
        tt = np.concatenate([self.t[m], [t_end]])
        return float(np.trapezoid(self(tt), tt))

    def cumulative(self, tt):
        """F(t) = exact integral of q from 0 to t (vectorised)."""
        if not hasattr(self, "_F"):
            self._F = np.concatenate([[0.0], np.cumsum(np.diff(self.t) * 0.5 * (self.q[1:] + self.q[:-1]))])
        tt = np.atleast_1d(np.asarray(tt, dtype=float))
        k = np.clip(np.searchsorted(self.t, tt, side="right") - 1, 0, len(self.t) - 2)
        return self._F[k] + (tt - self.t[k]) * 0.5 * (self.q[k] + self(tt))

    def average(self, t0, t1):
        """Exact mean of q over [t0, t1]."""
        F = self.cumulative([t0, t1])
        return float((F[1] - F[0]) / (t1 - t0))
