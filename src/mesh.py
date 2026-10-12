"""Half-cylinder tetrahedral meshes of the 21700 and the 4680 (D8).

The construction is the two-cell study's (inputs/twocell_mesh_cell2.py, copied unchanged): the cross-section is
triangulated ring by ring, extruded through graded axial layers into prisms, and each prism is split into three
tetrahedra by the vertex-order rule, so neighbouring prisms conform. For the 21700 the rings, segments and layers
are exactly the two-cell study's (checked in verification/test_mesh.py). For the 4680 the same rules are applied
with the interior rings spaced evenly at about 0.68 mm and the rings near the wall at the 21700's distances from the
wall; the 21700's outer zone (radius 8.9 mm and above, where the segments align) becomes the outer 1.65 mm.

This module also returns the extrusion data (the 2D nodes and triangles and the layer heights), which the field
sampler uses to evaluate the finite-element field at any point exactly.
"""
import math
import os
import sys

import numpy as np
from skfem import MeshTet

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "inputs"))
import twocell_mesh_cell2 as TC  # noqa: E402  (the two-cell study's generator, unchanged)

WALL_MM = [2.5, 2.0, 1.55, 1.15, 0.82, 0.55, 0.35, 0.2, 0.09, 0.0]    # the 21700's rings, as distances from the wall


def radial_rings(R, refine=1.0):
    if abs(R - 0.01055) < 1e-12:
        return TC.radial_rings(R, refine)
    if refine != 1.0:
        raise ValueError("only the 21700 mesh is refined (V3)")
    r_in = R - 3.05e-3                       # the 21700's interior zone ends 3.05 mm inside the wall (at 7.5 mm)
    n_in = int(round(r_in / 0.68e-3))
    interior = [r_in * k / n_in for k in range(1, n_in + 1)]
    wall = [R - d * 1e-3 for d in WALL_MM]
    return np.array(interior + wall)


def n_segments(r, R, refine=1.0):
    outer_zone = R - 1.65e-3
    ds = 0.5e-3 / refine if r >= outer_zone else 0.55e-3 / refine
    n = 4 * int(math.ceil(math.pi * r / (4 * ds)))
    if r >= outer_zone:
        n = 4 * int(math.ceil(math.pi * R / (4 * 0.5e-3 / refine)))
    return max(4, n)


def build_mesh(R, Lz, refine=1.0):
    rings = radial_rings(R, refine)
    pts2 = [(0.0, 0.0)]
    ring_nodes = []
    for r in rings:
        n = n_segments(r, R, refine)
        th = np.linspace(0.0, math.pi, n + 1)
        idx = list(range(len(pts2), len(pts2) + n + 1))
        pts2 += [(r * math.cos(t), r * math.sin(t)) for t in th]
        ring_nodes.append((idx, th))
    pts2 = np.array(pts2)
    tris = []
    idx0, _ = ring_nodes[0]
    for j in range(len(idx0) - 1):
        tris.append((0, idx0[j], idx0[j + 1]))
    for (ia, ta), (ib, tb) in zip(ring_nodes[:-1], ring_nodes[1:]):
        i = j = 0
        m, n = len(ia) - 1, len(ib) - 1
        while i < m or j < n:
            if i == m:
                tris.append((ia[i], ib[j], ib[j + 1])); j += 1
            elif j == n:
                tris.append((ia[i], ib[j], ia[i + 1])); i += 1
            elif ta[i + 1] < tb[j + 1] - 1e-12:
                tris.append((ia[i], ib[j], ia[i + 1])); i += 1
            else:
                tris.append((ia[i], ib[j], ib[j + 1])); j += 1
    tris = np.array(tris)
    z = TC.axial_layers(Lz, refine)
    n2, nz = len(pts2), len(z)
    p = np.zeros((3, n2 * nz))
    for k in range(nz):
        p[0, k * n2:(k + 1) * n2] = pts2[:, 0]
        p[1, k * n2:(k + 1) * n2] = pts2[:, 1]
        p[2, k * n2:(k + 1) * n2] = z[k]
    tets = []
    for tri in tris:
        a, b, c = sorted(tri)
        for k in range(nz - 1):
            A0, B0, C0 = a + k * n2, b + k * n2, c + k * n2
            A1, B1, C1 = A0 + n2, B0 + n2, C0 + n2
            tets += [(A0, B0, C0, C1), (A0, B0, B1, C1), (A0, A1, B1, C1)]
    t = np.array(tets).T
    P = p[:, t]
    vol = np.einsum("ij,ij->j", np.cross((P[:, 1] - P[:, 0]).T, (P[:, 2] - P[:, 0]).T).T, P[:, 3] - P[:, 0])
    neg = vol < 0
    t[[1, 2]] = np.where(neg, t[[2, 1]], t[[1, 2]])
    mesh = MeshTet(p, t)
    info = {"n_rings": len(rings), "n_layers": nz, "n_nodes_2d": n2, "n_tris_2d": len(tris),
            "n_nodes": int(p.shape[1]), "n_tets": int(t.shape[1]), "min_abs_vol": float(np.abs(vol).min())}
    extr = {"pts2": pts2, "tris": tris, "z": np.asarray(z), "n2": n2, "rings": np.asarray(rings), "R": R,
            "n_outer": len(ring_nodes[-1][0]) - 1}
    return mesh, info, extr


classify_facets = TC.classify_facets


class FieldSampler:
    """Exact evaluation of the P1 field at arbitrary points of the extruded mesh.

    A point is located in its triangle of the cross-section and its axial layer; within the prism, the three
    tetrahedra of the vertex-order split (sorted vertices a < b < c) are T1 = {A0 B0 C0 C1} where zeta <= lambda_c,
    T2 = {A0 B0 B1 C1} where lambda_c < zeta <= lambda_b + lambda_c, and T3 = {A0 A1 B1 C1} above, with lambda the
    barycentric coordinates in the triangle and zeta the fraction of the layer height. In each the P1 interpolant is
    written in those coordinates, so the sampled value is the finite-element value itself.
    """

    def __init__(self, extr):
        import matplotlib.tri as mtri
        self.e = extr
        self.tris = np.sort(extr["tris"], axis=1)       # a < b < c, the order used by the split (same row order)
        pts2 = extr["pts2"]
        self.tri = mtri.Triangulation(pts2[:, 0], pts2[:, 1], extr["tris"])
        self.finder = self.tri.get_trifinder()

    def matrix(self, x, y, z):
        import scipy.sparse as sp
        x, y, z = (np.asarray(v, dtype=float).ravel() for v in (x, y, z))
        it = self.finder(x, y)
        bad = it < 0
        if bad.any():
            # The outer ring is a polygon inscribed in the circle r = R, so a point on (or within a few micrometres
            # inside) the circle can lie just outside it. Such a point is moved along its radius onto the polygon's
            # edge, where the finite-element field takes its boundary value.
            n = self.e["n_outer"]
            R = self.e["R"]
            th = np.arctan2(y[bad], x[bad])
            j = np.clip(np.floor(th / (np.pi / n)), 0, n - 1)
            th_mid = (j + 0.5) * np.pi / n
            r_chord = R * np.cos(np.pi / (2 * n)) / np.cos(th - th_mid)
            r = np.minimum(np.hypot(x[bad], y[bad]), r_chord * (1 - 1e-10))
            x[bad], y[bad] = r * np.cos(th), r * np.sin(th)
            it[bad] = self.finder(x[bad], y[bad])
            if (it < 0).any():
                raise ValueError(f"{int((it < 0).sum())} points outside the mesh")
        pts2 = self.e["pts2"]
        a, b, c = self.tris[it].T
        xa, ya = pts2[a, 0], pts2[a, 1]
        xb, yb = pts2[b, 0], pts2[b, 1]
        xc, yc = pts2[c, 0], pts2[c, 1]
        det = (yb - yc) * (xa - xc) + (xc - xb) * (ya - yc)
        la = ((yb - yc) * (x - xc) + (xc - xb) * (y - yc)) / det
        lb = ((yc - ya) * (x - xc) + (xa - xc) * (y - yc)) / det
        lc = 1.0 - la - lb
        zl = self.e["z"]
        k = np.clip(np.searchsorted(zl, z, side="right") - 1, 0, len(zl) - 2)
        zeta = (z - zl[k]) / (zl[k + 1] - zl[k])
        n2 = self.e["n2"]
        A0, B0, C0 = a + k * n2, b + k * n2, c + k * n2
        A1, B1, C1 = A0 + n2, B0 + n2, C0 + n2
        t1 = zeta <= lc
        t3 = zeta > lb + lc
        t2 = ~t1 & ~t3
        n = len(x)
        rows = np.repeat(np.arange(n), 4)
        cols = np.empty((n, 4), dtype=np.int64)
        vals = np.empty((n, 4))
        cols[t1] = np.column_stack([A0, B0, C0, C1])[t1]
        vals[t1] = np.column_stack([la, lb, lc - zeta, zeta])[t1]
        cols[t2] = np.column_stack([A0, B0, B1, C1])[t2]
        vals[t2] = np.column_stack([la, lb + lc - zeta, zeta - lc, lc])[t2]
        cols[t3] = np.column_stack([A0, A1, B1, C1])[t3]
        vals[t3] = np.column_stack([1 - zeta, zeta - lb - lc, lb, lc])[t3]
        return sp.csr_matrix((vals.ravel(), (rows, cols.ravel())), shape=(n, n2 * len(zl)))
