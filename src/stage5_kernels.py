#!/usr/bin/env python3
"""Stage 5, Part A (D29): the step responses of the three thermal models for heat in each group of units.

For each model, cell and time grid, group j is heated at 1 W/m3 from step 1 on, starting from the ambient, and every
unit's temperature rise is recorded at every step. The steps are the model's own: Stage 1's and Stage 2's matrices,
backward Euler, the grid's step. The responses are stepped until they lie within 1e-8 (relative) of the model's
exact discrete steady state, and at least to the grid's archived discharge; past that they are held at the steady
state (src/stage5_common.py).

Models and their boundary data (D29):
    radial    (bc "lat")   Stage 1's radial model, convection on the side only (src/radial1d.py)
    corrected (bc "b")     Stage 2's end-corrected model, beta of D18 at h = 400 (src/stage2_correction.py)
    resolved  (bc "a"/"b") Stage 1's resolved cell, ends insulated / ends cooled (src/cell3d.py), refine 1,
                           circumferential conductivity across the layers, registered properties
Group loads: in one dimension the exact annulus integrals of the basis functions; in the resolved cell the exact
integrals over each prism's part inside the annulus (adaptive subdivision of the cut triangles, D29).

python3 src/stage5_kernels.py --model resolved --bc b --cell 21700 --grid m5C_2C [--G 15] [--units]
python3 src/stage5_kernels.py --all1d            (every one-dimensional kernel of D29)
Writes results/stage5_kernels/<model>_<bc>_<cell>_<grid>_G<G>.npz (single precision, D29) and a .json summary."""
import argparse
import gc
import json
import math
import os
import resource
import sys
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402
import stage5_common as S5  # noqa: E402

TOL_CONV = 1e-8
MAX_STEPS = 60000
CKPT_DIR = os.path.join(S5.KDIR, "checkpoints")      # not part of the results (.gitignore)
CKPT_EVERY = 200
QUAD = np.array([1 / 4, 1 / 12, 1 / 6, 1 / 6, 1 / 12, 1 / 4])   # A0 A1 B0 B1 C0 C1 over a whole prism, per area x height


# ----------------------------------------------------------------------------------------------------------------
# group loads in the resolved cell: exact integrals over the part of each prism inside a group's annulus
# ----------------------------------------------------------------------------------------------------------------
def prism_basis(la, lb, lc):
    """The six basis functions of a prism's vertex-order split (sorted vertices a < b < c, D8 and src/mesh.py),
    integrated over the prism's height per unit height: quadratics in the triangle's barycentric coordinates.
    Order: A0, A1, B0, B1, C0, C1 (0 = bottom layer, 1 = top layer)."""
    return np.stack([la - la ** 2 / 2, la ** 2 / 2, lb * lc + lb ** 2 / 2, lb ** 2 / 2 + la * lb,
                     lc ** 2 / 2, lc - lc ** 2 / 2], axis=-1)


def rminmax(P0, P1, P2):
    """Smallest and largest distance from the axis over each triangle (arrays of points, shape (M, 2))."""
    rmax = np.maximum(np.maximum(np.hypot(*P0.T), np.hypot(*P1.T)), np.hypot(*P2.T))

    def segd(P, Q):
        d = Q - P
        t = np.clip(-(P * d).sum(axis=1) / np.maximum((d * d).sum(axis=1), 1e-300), 0.0, 1.0)
        X = P + t[:, None] * d
        return np.hypot(*X.T)
    rmin = np.minimum(np.minimum(segd(P0, P1), segd(P1, P2)), segd(P2, P0))
    # origin inside the triangle -> 0
    cr = lambda A, B: A[:, 0] * B[:, 1] - A[:, 1] * B[:, 0]
    s0, s1, s2 = cr(P0, P1), cr(P1, P2), cr(P2, P0)
    inside = ((s0 >= 0) & (s1 >= 0) & (s2 >= 0)) | ((s0 <= 0) & (s1 <= 0) & (s2 <= 0))
    rmin = np.where(inside, 0.0, rmin)
    return rmin, rmax


def cut_integrals(pts2, tris, edges_r, depth=10):
    """I[t, g, :]: integrals over (triangle t) intersected with (group g's annulus) of the six prism functions."""
    T = np.sort(np.asarray(tris), axis=1)
    Pa, Pb, Pc = pts2[T[:, 0]], pts2[T[:, 1]], pts2[T[:, 2]]
    area = 0.5 * np.abs((Pb[:, 0] - Pa[:, 0]) * (Pc[:, 1] - Pa[:, 1]) - (Pb[:, 1] - Pa[:, 1]) * (Pc[:, 0] - Pa[:, 0]))
    G = len(edges_r) - 1
    nt = len(T)
    gof = lambda r: np.clip(np.searchsorted(edges_r, r, side="right") - 1, 0, G - 1)
    I = np.zeros((nt, G, 6))
    rmin, rmax = rminmax(Pa, Pb, Pc)
    ga, gb = gof(rmin), gof(rmax)
    whole = ga == gb
    I[np.where(whole)[0], ga[whole], :] = area[whole, None] * QUAD
    cut = np.where(~whole)[0]
    # adaptive subdivision in barycentric coordinates of the parent triangle
    par = cut.copy()
    L = np.tile(np.eye(3), (len(cut), 1, 1))           # (M, vertex, (la, lb, lc))
    n_last = 0
    for level in range(depth + 1):
        if len(par) == 0:
            break
        X = np.einsum("mvk,mkd->mvd", L, np.stack([Pa[par], Pb[par], Pc[par]], axis=1))
        r0, r1 = rminmax(X[:, 0], X[:, 1], X[:, 2])
        g0, g1 = gof(r0), gof(r1)
        res = g0 == g1
        A_sub = area[par] / 4.0 ** level
        mids = np.stack([(L[:, 0] + L[:, 1]) / 2, (L[:, 1] + L[:, 2]) / 2, (L[:, 2] + L[:, 0]) / 2], axis=1)
        f = prism_basis(mids[..., 0], mids[..., 1], mids[..., 2])          # (M, 3, 6)
        if res.any():
            contrib = (A_sub[res, None] / 3.0) * f[res].sum(axis=1)
            np.add.at(I, (par[res], g0[res]), contrib)
        un = ~res
        if level == depth:
            # last level: each of the three quadrature points counts towards the group it lies in
            Xm = np.einsum("mqk,mkd->mqd", mids[un], np.stack([Pa[par[un]], Pb[par[un]], Pc[par[un]]], axis=1))
            gq = gof(np.hypot(Xm[..., 0], Xm[..., 1]))                       # (M, 3)
            for q in range(3):
                np.add.at(I, (par[un], gq[:, q]), (A_sub[un, None] / 3.0) * f[un, q])
            n_last = int(un.sum())
            break
        Lu = L[un]
        v0, v1, v2 = Lu[:, 0], Lu[:, 1], Lu[:, 2]
        m01, m12, m20 = (v0 + v1) / 2, (v1 + v2) / 2, (v2 + v0) / 2
        kids = [np.stack(c, axis=1) for c in ((v0, m01, m20), (m01, v1, m12), (m20, m12, v2), (m01, m12, m20))]
        L = np.concatenate(kids, axis=0)
        par = np.tile(par[un], 4)
    check = np.abs(I.sum(axis=1) - area[:, None] * QUAD).max() / area.max()
    return I, {"n_tris": nt, "n_cut": int(len(cut)), "depth": depth, "n_unresolved_last": n_last,
               "partition_max_rel": float(check)}


def group_loads_3d(model, G):
    """b (n_nodes x G): integral of each basis function over the half mesh inside group g's annulus."""
    extr = model.extr
    N = model.cc["n_units"]
    e = S5.group_edges(N, G)
    unit_r = np.linspace(0.0, model.R, N + 1)
    edges_r = unit_r[e]
    edges_r[-1] = np.inf                          # the outer polygon lies inside r = R
    I, info = cut_integrals(extr["pts2"], extr["tris"], edges_r)
    T = np.sort(np.asarray(extr["tris"]), axis=1)
    z = np.asarray(extr["z"])
    h = np.diff(z)
    n2 = extr["n2"]
    nn = n2 * len(z)
    b = np.zeros((nn, G))
    kk = np.arange(len(h))
    for role, (col, up) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))):
        nodes = T[:, col][:, None] + (kk[None, :] + up) * n2               # (nt, nl)
        w = I[:, None, :, role] * h[None, :, None]                          # (nt, nl, G)
        for g in range(G):
            np.add.at(b[:, g], nodes.ravel(), w[:, :, g].ravel())
    wv = np.asarray(model.w_vol)
    info["sum_of_loads_vs_w_vol_max_rel"] = float(np.abs(b.sum(axis=1) - wv).max() / wv.max())
    vol_mesh = 2 * b.sum(axis=0)
    r = np.linspace(0.0, model.R, N + 1)[e]
    vol_exact = math.pi * (r[1:] ** 2 - r[:-1] ** 2) * model.H
    info["group_volume_mesh_over_exact_minus_1"] = (vol_mesh / vol_exact - 1).tolist()
    info["group_volume_mesh_over_mesh_total_vs_W"] = (vol_mesh / vol_mesh.sum() - S5.group_weights(N, G)).tolist()
    return b, info


# ----------------------------------------------------------------------------------------------------------------
def build(model_name, bc, cell):
    """The model's matrices: capacity Cmat (vector), stiffness K, exchange diagonal D, unit sampler U (N x nodes),
    group loads L per 1 W/m3 (nodes x G) and their unscaled forms b (for the load-weighted means)."""
    props = C.roll_properties()["registered"]
    if model_name in ("radial", "corrected"):
        if model_name == "radial":
            assert bc == "lat"
            m = R1.Radial1D(cell, props=props)
            D = m.d_conv.copy()
        else:
            assert bc == "b"
            from stage2_correction import Corrected
            m = Corrected(cell, props=props)
            D = m.d_conv + m.d_sink
        return {"K": m.K.tocsr(), "Cap": m.C.copy(), "D": D, "U": sp.csr_matrix(m.U), "Uun": None, "m": m,
                "kind": "1d", "w_vol": m.w_vol}
    from cell3d import Cell3D
    m = Cell3D(cell, bc, props=props, refine=1.0, k_theta="across")
    s = m.samplers()
    return {"K": m.K.tocsr(), "Cap": np.asarray(m.Cap), "D": np.asarray(m.d_conv + m.d_tab), "U": s["U"].tocsr(),
            "m": m, "kind": "3d", "w_vol": np.asarray(m.w_vol)}


def loads(mm, G):
    m = mm["m"]
    N = m.n_units if mm["kind"] == "1d" else m.cc["n_units"]
    if mm["kind"] == "1d":
        area = math.pi * (m.unit_edges[1:] ** 2 - m.unit_edges[:-1] ** 2)
        Uun = m.U * area[:, None]                   # exact annulus integrals of the basis functions (per unit height)
        e = S5.group_edges(N, G)
        b = np.stack([Uun[e[k]:e[k + 1]].sum(axis=0) for k in range(G)], axis=1)
        info = {"sum_of_loads_vs_w_vol_max_rel": float(np.abs(b.sum(axis=1) - m.w_vol).max() / m.w_vol.max())}
        return b, b.copy(), info                   # the 1D source is w_vol q: no scaling
    b, info = group_loads_3d(m, G)
    scale = m.V_exact / (2 * m.w_vol.sum())         # Stage 1's source normalisation (w_src Q, Q = q V_exact)
    return b * scale, b, info


def solver_for(A):
    return spla.splu(A.tocsc(), permc_spec="MMD_AT_PLUS_A", diag_pivot_thresh=0.0, options=dict(SymmetricMode=True))


def compute(model_name, bc, cell, gridname, G=S5.G_REG, keep_units=False, verbose=True):
    t0 = time.time()
    dt, n_arch, _ = S5.grid(gridname)
    mm = build(model_name, bc, cell)
    m = mm["m"]
    N = m.n_units if mm["kind"] == "1d" else m.cc["n_units"]
    L, b, linfo = loads(mm, G)
    Vb = b.sum(axis=0)
    K, Cap, D, U = mm["K"], mm["Cap"], mm["D"], mm["U"]
    A_ug = S5.unit_to_group_matrix(N, G)
    kind = mm["kind"]
    n_units_model = N
    del mm, m                                   # free the mesh and its bases before the factorisations (memory)
    gc.collect()
    rss = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
    if verbose:
        print(f"  built in {time.time() - t0:.0f} s, peak memory so far {rss():.2f} GB", flush=True)
    t_build = time.time() - t0
    # a checkpoint lets a long kernel resume after its process is stopped: the same matrices give the same
    # factors, so the resumed steps are the steps an uninterrupted run would make
    ck = os.path.join(CKPT_DIR, os.path.basename(S5.kernel_path(model_name, bc, cell, gridname, G)))
    resume = os.path.exists(ck)
    t1 = time.time()
    if resume:
        z = np.load(ck)
        S_inf_unit, S_inf_group, S_inf_lc = z["S_inf_unit"], z["S_inf_group"], z["S_inf_lc"]
        th = z["th"]
        S_unit, S_lc = list(z["S_unit"]), list(z["S_lc"])
        k = int(z["k"])
        if verbose:
            print(f"  resuming from step {k}", flush=True)
    else:
        # exact discrete steady state: (K + D) theta = L
        lu = solver_for(K + sp.diags(D))
        th_inf = lu.solve(L)
        del lu
        gc.collect()
        S_inf_unit = U @ th_inf                                  # (N, G)
        S_inf_group = A_ug @ S_inf_unit
        S_inf_lc = (b.T @ th_inf) / Vb[:, None]
        th = np.zeros_like(L)
        S_unit, S_lc = [], []
        k = 0
    t_steady = time.time() - t1
    t2 = time.time()
    lu = solver_for(K + sp.diags(Cap / dt + D))
    t_fact = time.time() - t2
    cdt = (Cap / dt)[:, None]
    scale_inf = np.abs(S_inf_unit).max()
    conv = None
    t3 = time.time()
    while k < MAX_STEPS:
        k += 1
        th = lu.solve(cdt * th + L)
        Su = U @ th
        S_unit.append(Su)
        S_lc.append((b.T @ th) / Vb[:, None])
        rel = float(np.abs(Su - S_inf_unit).max() / scale_inf)
        if verbose and k % 500 == 0:
            print(f"  {model_name} {bc} {cell} {gridname} step {k}: rel distance to steady {rel:.2e} "
                  f"({time.time() - t3:.0f} s)", flush=True)
        if k >= n_arch and rel <= TOL_CONV:
            conv = rel
            break
        if kind == "3d" and k % CKPT_EVERY == 0:
            os.makedirs(CKPT_DIR, exist_ok=True)
            tmp = ck + ".tmp.npz"
            np.savez(tmp, k=k, th=th, S_unit=np.array(S_unit), S_lc=np.array(S_lc), S_inf_unit=S_inf_unit,
                     S_inf_group=S_inf_group, S_inf_lc=S_inf_lc)
            os.replace(tmp, ck)
    if conv is None:
        raise RuntimeError("kernel did not converge")
    t_loop = time.time() - t3
    del lu
    gc.collect()
    S_unit = np.array(S_unit)                                # (K, N, G)
    S_lc = np.array(S_lc)                                    # (K, G, G)
    S_group = np.einsum("gn,knj->kgj", A_ug, S_unit)
    # V1, reciprocity on the load-weighted group means: V_i S_ij = V_j S_ji
    VS = Vb[None, :, None] * S_lc
    recip = float(np.abs(VS - np.transpose(VS, (0, 2, 1))).max() / np.abs(VS).max())
    VS_s = Vb[None, :, None] * S_group
    recip_sampled = float(np.abs(VS_s - np.transpose(VS_s, (0, 2, 1))).max() / np.abs(VS_s).max())
    lc_vs_sampled = float(np.abs(S_lc - S_group).max() / np.abs(S_group).max())
    meta = {"model": model_name, "bc": bc, "cell": cell, "grid": gridname, "dt": dt, "n_archive": n_arch,
            "G": G, "N": int(N), "group_edges": S5.group_edges(N, G), "W": S5.group_weights(N, G).tolist(),
            "K_stored": int(k), "final_rel_distance_to_steady": conv, "tolerance": TOL_CONV,
            "loads": linfo, "group_volume_half_mesh_m3": Vb.tolist(),
            "reciprocity_load_weighted_max_rel": recip, "reciprocity_sampled_max_rel": recip_sampled,
            "load_weighted_vs_sampled_group_mean_max_rel": lc_vs_sampled,
            "solver": "SuperLU (MMD_AT_PLUS_A, symmetric mode), as src/cell3d.py's direct solver",
            "timing_s": {"build": t_build, "steady": t_steady, "factorise": t_fact, "loop": t_loop},
            "peak_memory_GB": rss(),
            "n_nodes": int(K.shape[0]), "units": "K per (W/m3)", "storage": "float32 responses, float64 steady states"}
    os.makedirs(S5.KDIR, exist_ok=True)
    out = {"meta": json.dumps(meta), "S_group": S_group.astype(np.float32), "S_inf_group": S_inf_group,
           "S_unit_uniform": S_unit.sum(axis=2).astype(np.float32), "S_inf_unit_uniform": S_inf_unit.sum(axis=1),
           "S_lc": S_lc.astype(np.float32), "S_inf_lc": S_inf_lc}
    if keep_units:
        out["S_unit"] = S_unit.astype(np.float32)
        out["S_inf_unit"] = S_inf_unit
    meta["resumed_from_checkpoint"] = bool(resume)
    out["meta"] = json.dumps(meta)
    path = S5.kernel_path(model_name, bc, cell, gridname, G)
    tmp = path + f".tmp{os.getpid()}"
    with open(tmp, "wb") as f:                        # written whole, then renamed, so a stopped job leaves no part file
        np.savez_compressed(f, **out)
    os.replace(tmp, path)
    with open(path.replace(".npz", ".json"), "w") as f:
        json.dump(meta, f, indent=1)
    if os.path.exists(ck):
        os.remove(ck)
    if verbose:
        print(f"{os.path.basename(path)}: {k} steps (archive {n_arch}), distance {conv:.1e}, reciprocity {recip:.1e} "
              f"(sampled {recip_sampled:.1e}), loads partition {linfo.get('partition_max_rel', 0):.1e}, "
              f"sum vs w_vol {linfo['sum_of_loads_vs_w_vol_max_rel']:.1e}, {time.time() - t0:.0f} s", flush=True)
    return path


JOBS_1D = [(mdl, bc, cell, g, G, units)
           for cell, grids in (("21700", ("m5C_2C", "p25C_2C", "p25C_1.25C", "p25C_3C", "charge10", "m5C_2C_half",
                                          "charge10_half")), ("4680", ("m5C_2C", "charge10")))
           for mdl, bc in (("radial", "lat"), ("corrected", "b"))
           for g in grids for G, units in ((S5.G_REG, g == "m5C_2C"),)] + \
          [(mdl, bc, "21700", g, 30, False) for mdl, bc in (("radial", "lat"), ("corrected", "b"))
           for g in ("m5C_2C", "charge10")]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--bc")
    ap.add_argument("--cell")
    ap.add_argument("--grid")
    ap.add_argument("--G", type=int, default=S5.G_REG)
    ap.add_argument("--units", action="store_true", help="also store every unit's response to every group")
    ap.add_argument("--all1d", action="store_true")
    a = ap.parse_args()
    if a.all1d:
        for job in JOBS_1D:
            compute(*job[:5], keep_units=job[5])
    else:
        compute(a.model, a.bc, a.cell, a.grid, a.G, keep_units=a.units)
