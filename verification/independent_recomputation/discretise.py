"""Spatial discretisations of the axisymmetric (r, z) problem and of the 1D radial model.

Scheme V (primary): vertex-centred finite volumes on a uniform (r, z) grid with nodes on
r = 0, r = R, z = 0 and z = H. Boundary nodes carry the shell: its heat capacity
(C_SHELL times the outer area belonging to the node), its in-plane conduction as extra
links between neighbouring boundary nodes (lateral: k t 2 pi R / dz; end faces:
k t 2 pi r_face / dr) and convection. The rim nodes (r = R, z = 0 and z = H) belong to
both the lateral and the end-face shell, so the shell is continuous around the rim.

Scheme C (cross-check): cell-centred finite volumes for the roll plus separate
zero-volume shell surface nodes (one per lateral segment and one per end-face annulus)
joined to the adjacent roll cell through a half-cell conductance; the lateral and
end-face shell segments next to the rim are joined by a corner link (half a lateral
segment in series with half an end-face annulus).
"""
import numpy as np
from network import Network
from params import RHOCP, K_R, K_Z, KT_SHELL, C_SHELL

TWO_PI = 2.0 * np.pi


# ----------------------------------------------------------------------------------
# Scheme V: vertex-centred
# ----------------------------------------------------------------------------------
class VertexGrid2D:
    def __init__(self, R, H, Nr, Nz, h, ends_convect, rhocp=RHOCP, kr=K_R, kz=K_Z,
                 kt=KT_SHELL, cs=C_SHELL, end_shell=True, lat_shell_cond=True):
        assert Nz % 2 == 0, "Nz must be even so that z = H/2 is a node"
        self.R, self.H, self.Nr, self.Nz = R, H, Nr, Nz
        self.r = np.linspace(0.0, R, Nr + 1)
        self.z = np.linspace(0.0, H, Nz + 1)
        dr = R / Nr; dz = H / Nz
        self.dr, self.dz = dr, dz
        a = np.maximum(self.r - dr / 2, 0.0); b = np.minimum(self.r + dr / 2, R)
        A = np.pi * (b ** 2 - a ** 2)                      # annular CV area at each r node
        c = np.maximum(self.z - dz / 2, 0.0); d = np.minimum(self.z + dz / 2, H)
        L = d - c                                          # CV height at each z node
        self.A, self.L = A, L
        nr1, nz1 = Nr + 1, Nz + 1
        n = nr1 * nz1
        idx = np.arange(n).reshape(nz1, nr1)               # idx[j, i]
        self.idx = idx
        net = Network(n)
        V = np.outer(L, A)                                 # V[j, i]
        net.C += rhocp * V.ravel()
        net.v += V.ravel()
        # roll: radial links (i, j)-(i+1, j)
        rf = self.r[:-1] + dr / 2
        G = kr * TWO_PI * rf[None, :] * L[:, None] / dr    # shape (nz1, Nr)
        net.link(idx[:, :-1].ravel(), idx[:, 1:].ravel(), G.ravel())
        # roll: axial links (i, j)-(i, j+1)
        G = np.broadcast_to(kz * A[None, :] / dz, (Nz, nr1))
        net.link(idx[:-1, :].ravel(), idx[1:, :].ravel(), G.ravel())
        # shell, lateral surface (i = Nr)
        lat = idx[:, Nr]
        S_lat = TWO_PI * R * L
        net.C[lat] += cs * S_lat
        net.Gh[lat] += h * S_lat
        if lat_shell_cond and kt > 0:
            net.link(lat[:-1], lat[1:], kt * TWO_PI * R / dz)
        # shell, end faces (j = 0 and j = Nz)
        for j in (0, Nz):
            row = idx[j, :]
            if end_shell:
                net.C[row] += cs * A
                if kt > 0:
                    net.link(row[:-1], row[1:], kt * TWO_PI * rf / dr)
            if ends_convect:
                net.Gh[row] += h * A
        self.net = net
        # unit-average operators are built on demand
        self.V = V

    def probes(self):
        Nr, Nz = self.Nr, self.Nz
        jm = Nz // 2
        return dict(core_mid=self.idx[jm, 0], surf_mid=self.idx[jm, Nr],
                    core_bot=self.idx[0, 0], core_top=self.idx[Nz, 0])

    def radial_unit_weights(self, n_units):
        """W[k, i] = integral over unit k of hat_i(r) * r dr (piecewise-linear interpolant)."""
        Nr = self.Nr
        assert Nr % n_units == 0
        m = Nr // n_units
        r, dr = self.r, self.dr
        W = np.zeros((n_units, Nr + 1))
        for i in range(Nr):
            k = i // m
            W[k, i] += r[i] * dr / 2 + dr ** 2 / 6
            W[k, i + 1] += r[i] * dr / 2 + dr ** 2 / 3
        edges = np.linspace(0, self.R, n_units + 1)
        area_half = (edges[1:] ** 2 - edges[:-1] ** 2) / 2  # integral of r dr over unit
        assert np.allclose(W.sum(axis=1), area_half, rtol=1e-12)
        return W, edges

    def unit_averages(self, th, n_units):
        W, edges = self.radial_unit_weights(n_units)
        T = th.reshape(self.Nz + 1, self.Nr + 1)
        zint = self.L @ T                          # trapezoid in z (exact for the Q1 field)
        num = W @ zint                             # integral of T r dr dz over each unit
        den = (edges[1:] ** 2 - edges[:-1] ** 2) / 2 * self.H
        return num / den, edges

    def volume_mean(self, th):
        V = self.V.ravel()
        return float(V @ th / V.sum())


class VertexGrid1D:
    """1D radial model, per unit height (no axial dimension)."""

    def __init__(self, R, Nr, h, rhocp=RHOCP, kr=K_R, cs=C_SHELL):
        self.R, self.Nr = R, Nr
        self.r = np.linspace(0.0, R, Nr + 1)
        dr = R / Nr; self.dr = dr
        a = np.maximum(self.r - dr / 2, 0.0); b = np.minimum(self.r + dr / 2, R)
        A = np.pi * (b ** 2 - a ** 2)
        self.A = A
        net = Network(Nr + 1)
        net.C += rhocp * A
        net.v += A
        rf = self.r[:-1] + dr / 2
        net.link(np.arange(Nr), np.arange(1, Nr + 1), kr * TWO_PI * rf / dr)
        net.C[Nr] += cs * TWO_PI * R
        net.Gh[Nr] += h * TWO_PI * R
        self.net = net

    def probes(self):
        return dict(core_mid=0, surf_mid=self.Nr)

    def unit_averages(self, th, n_units):
        Nr = self.Nr
        assert Nr % n_units == 0
        m = Nr // n_units
        r, dr = self.r, self.dr
        num = np.zeros(n_units)
        for i in range(Nr):
            k = i // m
            num[k] += th[i] * (r[i] * dr / 2 + dr ** 2 / 6) + th[i + 1] * (r[i] * dr / 2 + dr ** 2 / 3)
        edges = np.linspace(0, self.R, n_units + 1)
        den = (edges[1:] ** 2 - edges[:-1] ** 2) / 2
        return num / den, edges

    def volume_mean(self, th):
        return float(self.A @ th / self.A.sum())


# ----------------------------------------------------------------------------------
# Scheme C: cell-centred roll + shell surface nodes
# ----------------------------------------------------------------------------------
class CellGrid2D:
    def __init__(self, R, H, Nr, Nz, h, ends_convect, rhocp=RHOCP, kr=K_R, kz=K_Z,
                 kt=KT_SHELL, cs=C_SHELL):
        assert Nz % 2 == 1, "Nz must be odd so that z = H/2 is a cell centre"
        self.R, self.H, self.Nr, self.Nz = R, H, Nr, Nz
        dr = R / Nr; dz = H / Nz
        self.dr, self.dz = dr, dz
        rf = np.linspace(0, R, Nr + 1)                      # radial faces
        self.rc = 0.5 * (rf[1:] + rf[:-1])
        A = np.pi * (rf[1:] ** 2 - rf[:-1] ** 2)
        self.A = A
        ncell = Nr * Nz
        cell = np.arange(ncell).reshape(Nz, Nr)             # cell[j, i]
        lat = ncell + np.arange(Nz)
        bot = ncell + Nz + np.arange(Nr)
        top = ncell + Nz + Nr + np.arange(Nr)
        n = ncell + Nz + 2 * Nr
        self.cell, self.lat, self.bot, self.top = cell, lat, bot, top
        net = Network(n)
        V = np.broadcast_to(A[None, :] * dz, (Nz, Nr))
        self.V = np.array(V)
        net.C[cell.ravel()] += rhocp * V.ravel()
        net.v[cell.ravel()] += V.ravel()
        # roll radial links
        G = np.broadcast_to(kr * TWO_PI * rf[1:-1] * dz / dr, (Nz, Nr - 1))
        net.link(cell[:, :-1].ravel(), cell[:, 1:].ravel(), G.ravel())
        # roll axial links
        G = np.broadcast_to(kz * A / dz, (Nz - 1, Nr))
        net.link(cell[:-1, :].ravel(), cell[1:, :].ravel(), G.ravel())
        # roll to lateral shell: half cell, exact cylindrical resistance
        g_half_r = TWO_PI * kr * dz / np.log(R / (R - dr / 2))
        net.link(cell[:, -1], lat, g_half_r)
        # roll to end shells: half cell
        net.link(cell[0, :], bot, kz * A / (dz / 2))
        net.link(cell[-1, :], top, kz * A / (dz / 2))
        # lateral shell
        S = TWO_PI * R * dz
        net.C[lat] += cs * S
        net.Gh[lat] += h * S
        net.link(lat[:-1], lat[1:], kt * TWO_PI * R / dz)
        # end shells
        for e in (bot, top):
            net.C[e] += cs * A
            if ends_convect:
                net.Gh[e] += h * A
            net.link(e[:-1], e[1:], kt * TWO_PI * rf[1:-1] / dr)
        # corner links around the rim: half lateral segment + half end annulus in series
        res = (dz / 2) / (kt * TWO_PI * R) + np.log(R / (R - dr / 2)) / (kt * TWO_PI)
        net.link([lat[0], lat[-1]], [bot[-1], top[-1]], 1.0 / res)
        self.net = net

    def extract(self, th):
        jm = (self.Nz - 1) // 2
        c = self.cell
        core_mid = (9 * th[c[jm, 0]] - th[c[jm, 1]]) / 8
        surf_mid = th[self.lat[jm]]
        core_bot = (9 * th[self.bot[0]] - th[self.bot[1]]) / 8
        core_top = (9 * th[self.top[0]] - th[self.top[1]]) / 8
        return dict(core_mid=core_mid, surf_mid=surf_mid, core_bot=core_bot, core_top=core_top)

    def unit_averages(self, th, n_units):
        Nr = self.Nr
        assert Nr % n_units == 0
        m = Nr // n_units
        T = th[self.cell.ravel()].reshape(self.Nz, Nr)
        num = (self.V * T).sum(axis=0)          # per radial cell, J-like sums over height
        vol = self.V.sum(axis=0)
        num_u = num.reshape(n_units, m).sum(axis=1)
        vol_u = vol.reshape(n_units, m).sum(axis=1)
        return num_u / vol_u, np.linspace(0, self.R, n_units + 1)

    def volume_mean(self, th):
        T = th[self.cell.ravel()]
        V = self.V.ravel()
        return float(V @ T / V.sum())
