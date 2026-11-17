#!/usr/bin/env python3
"""Independent read, item 1: P1 and V1 from the stored kernels, and a re-solve of the one-dimensional models'
step responses with my own finite-element code.

P1 (predictions_stage5.md): the units' uniform-heat response convolved with the registered heat on the archive's
grid, against Stage 4's stored unit histories at every archived time, five cases, three kernels; holds if the
largest absolute difference is below 0.01 K.
V1 (D33): reciprocity of the load-weighted group means (V_i S_ij = V_j S_ji), the load-weighted against the sampled
group means, and the internal consistency of each kernel file.
-> out/p1_v1.json"""
import glob
import json
import math
import os
import sys
import time

import numpy as np
from scipy.linalg import solve_banded

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402

T0 = time.time()
STAGE4_CASES = ("21700_b_m5C_2C", "21700_b_p25C_2C", "21700_b_p25C_1.25C", "21700_a_m5C_2C", "4680_b_m5C_2C")


def p1():
    h1 = json.load(open(os.path.join(L.RES, "stage4_hist_1d.json")))
    h3 = json.load(open(os.path.join(L.RES, "stage4_hist_3d_21700.json")))
    h3.update(json.load(open(os.path.join(L.RES, "stage4_hist_3d_4680.json"))))
    stored = json.load(open(os.path.join(L.RES, "stage5_p1.json")))
    out, worst = {}, 0.0
    for case in STAGE4_CASES:
        cell, ends, Ta, I, g = L.DISCHARGE[case]
        dt, n, te = L.grid(g)
        q = L.heat_on_grid(g)
        for label in L.LABELS:
            kp = L.kernel_file(label, ends, cell, g)
            k = L.load_kernel(kp, keys=("S_unit_uniform", "S_inf_unit_uniform"))
            assert abs(k["meta"]["dt"] - dt) < 1e-12 and k["meta"]["n_archive"] == n, (kp, k["meta"]["dt"], dt)
            rise = L.conv(k["S_unit_uniform"], k["S_inf_unit_uniform"], q)            # (n, N)
            if label == "resolved":
                rec = h3[case]
                arch = np.array(rec["resolved"], dtype=float)
            else:
                rec = h1[case]
                use_radial = label == "radial" or ends == "a"
                arch = np.array(rec["radial" if use_radial else "corrected"], dtype=float)
            times = np.array(rec["times"], dtype=float)
            steps = np.rint(times / dt).astype(int)
            off = float(np.abs(steps * dt - times).max())
            T = Ta + rise[steps - 1]
            d = np.abs(T - arch)
            i_t, i_u = np.unravel_index(int(np.argmax(d)), d.shape)
            # one row recomputed by the direct step-response sum (cross-check of the FFT evaluation)
            j = int(steps[-1])
            direct = Ta + L.conv_direct_last(k["S_unit_uniform"].astype(float), k["S_inf_unit_uniform"], q[:j])
            key = f"{case}|{label}"
            out[key] = {"kernel": os.path.basename(kp), "n_times": int(len(times)), "n_units": int(d.shape[1]),
                        "max_abs_K": float(d.max()), "at_time_s": float(times[i_t]), "at_unit": int(i_u) + 1,
                        "grid_time_offset_max_s": off, "fft_vs_direct_last_row_max_abs_K": float(np.abs(direct - T[-1]).max()),
                        "stored_max_abs_K": stored["cases"][key]["max_abs_K"],
                        "end_rise_K_max_unit": float((T[-1] - Ta).max())}
            worst = max(worst, float(d.max()))
    return {"cases": out, "max_abs_K": worst, "held": bool(worst < 0.01), "stored_max_abs_K": stored["max_abs_K"],
            "stored_held": stored["held"]}


# ----------------------------------------------------------------------------------------------------------------
def kernel_checks():
    rows = {}
    for kp in sorted(glob.glob(os.path.join(L.KDIR, "*.npz"))):
        k = L.load_kernel(kp)
        m = k["meta"]
        N, G = m["N"], m["G"]
        r = {"model": m["model"], "bc": m["bc"], "cell": m["cell"], "grid": m["grid"], "G": G, "K_stored": m["K_stored"]}
        # grid
        dt, n, _ = L.grid(m["grid"])
        r["dt_matches"] = bool(abs(m["dt"] - dt) < 1e-12)
        r["n_archive_matches"] = bool(m["n_archive"] == n)
        r["K_at_least_archive"] = bool(m["K_stored"] >= n)
        # groups
        r["edges_match"] = m["group_edges"] == L.edges(N, G)
        r["edges_tie_in_rule"] = L.has_tie(N, G)
        r["W_max_abs_diff"] = float(np.abs(np.array(m["W"]) - L.group_w(N, G)).max())
        # reciprocity from the stored (single precision) load-weighted means
        Vb = np.array(m["group_volume_half_mesh_m3"], dtype=float)
        S_lc = k["S_lc"].astype(float)
        VS = Vb[None, :, None] * S_lc
        D = np.abs(VS - np.transpose(VS, (0, 2, 1)))
        r["reciprocity_stored_f32_max_rel"] = float(D.max() / np.abs(VS).max())
        # bound from rounding each stored S_lc entry to single precision: |dV S| <= (V_i|S_ij| + V_j|S_ji|) 2^-24
        bound = (np.abs(VS) + np.abs(np.transpose(VS, (0, 2, 1)))) * 2.0 ** -24 * 1.01 + 1e-300
        r["reciprocity_within_f32_rounding_everywhere"] = bool((D <= bound).all())
        r["reciprocity_worst_over_f32_bound"] = float((D / bound).max())
        VSi = Vb[:, None] * k["S_inf_lc"]
        r["reciprocity_steady_f64_max_rel"] = float(np.abs(VSi - VSi.T).max() / np.abs(VSi).max())
        r["meta_reciprocity_load_weighted_max_rel"] = m["reciprocity_load_weighted_max_rel"]
        # load-weighted against sampled group means
        Sg = k["S_group"].astype(float)
        r["lc_vs_sampled_max_rel_recomputed"] = float(np.abs(S_lc - Sg).max() / np.abs(Sg).max())
        r["meta_lc_vs_sampled_max_rel"] = m["load_weighted_vs_sampled_group_mean_max_rel"]
        # group volumes against the exact annuli
        R, H = L.CELL[m["cell"]]["R"], L.CELL[m["cell"]]["H"]
        e = L.edges(N, G)
        rr = R * np.array(e, dtype=float) / N
        area = math.pi * (rr[1:] ** 2 - rr[:-1] ** 2)
        if m["model"] in ("radial", "corrected"):
            r["group_area_max_rel_diff_vs_exact"] = float(np.abs(Vb / area - 1).max())
        else:
            ratio = 2 * Vb / (area * H) - 1
            r["group_volume_mesh_over_exact_minus_1_recomputed_max_abs"] = float(np.abs(ratio).max())
            r["group_volume_meta_vs_recomputed_max_abs"] = float(np.abs(ratio - np.array(m["loads"]["group_volume_mesh_over_exact_minus_1"])).max())
        # internal consistency: uniform = sum over groups; group means = area-weighted unit means
        A = L.unit_to_group(N, G)
        Su = k["S_unit_uniform"].astype(float)
        r["S_inf_group_rowsum_vs_A_unit_uniform_max_rel"] = float(np.abs(k["S_inf_group"].sum(axis=1) - A @ k["S_inf_unit_uniform"]).max()
                                                                 / np.abs(k["S_inf_unit_uniform"]).max())
        r["S_group_rowsum_vs_A_unit_uniform_max_rel"] = float(np.abs(Sg.sum(axis=2) - Su @ A.T).max() / np.abs(Su).max())
        if "S_unit" in k:
            Sn = k["S_unit"].astype(float)
            r["S_unit_sum_vs_uniform_max_rel"] = float(np.abs(Sn.sum(axis=2) - Su).max() / np.abs(Su).max())
            r["S_group_vs_A_S_unit_max_rel"] = float(np.abs(np.einsum("gn,knj->kgj", A, Sn) - Sg).max() / np.abs(Sg).max())
            r["S_inf_unit_sum_vs_uniform_max_rel"] = float(np.abs(k["S_inf_unit"].sum(axis=1) - k["S_inf_unit_uniform"]).max()
                                                           / np.abs(k["S_inf_unit_uniform"]).max())
        # convergence to the steady state at the last stored step (single-precision storage limits this to ~6e-8)
        r["last_step_rel_distance_to_steady_f32"] = float(np.abs(Su[-1] - k["S_inf_unit_uniform"]).max()
                                                         / np.abs(k["S_inf_unit_uniform"]).max())
        r["meta_final_rel_distance_to_steady"] = m["final_rel_distance_to_steady"]
        r["monotone_nondecreasing_uniform"] = bool((np.diff(Su, axis=0) >= -1e-6 * np.abs(Su).max()).all())
        rows[os.path.basename(kp)[:-4]] = r
    worst_f32 = max(v["reciprocity_stored_f32_max_rel"] for v in rows.values())
    worst_steady = max(v["reciprocity_steady_f64_max_rel"] for v in rows.values())
    return {"kernels": rows, "reciprocity_stored_f32_worst": worst_f32,
            "reciprocity_all_within_f32_rounding": bool(all(v["reciprocity_within_f32_rounding_everywhere"] for v in rows.values())),
            "reciprocity_steady_f64_worst": worst_steady, "reciprocity_steady_held_1e-9": bool(worst_steady < 1e-9)}


# ----------------------------------------------------------------------------------------------------------------
# my own finite elements for the one-dimensional models (D7, D18): P1 in r with the weight 2 pi r, the capacity
# lumped by row sums, the can's capacity at r = R, side convection h at r = R, the end sink beta per unit volume
# (lumped like the capacity), backward Euler on the grid's step. Units: exact annulus averages.
# ----------------------------------------------------------------------------------------------------------------
def props():
    p = json.load(open(os.path.join(L.ROOT, "inputs", "properties.json")))["registered"]
    return p


def fe_1d(cell, sub=20, corrected=False, consistent=False):
    p = props()
    R, H, N = L.CELL[cell]["R"], L.CELL[cell]["H"], L.CELL[cell]["N"]
    ne = N * sub
    r = np.linspace(0.0, R, ne + 1)
    a, b = r[:-1], r[1:]
    dr = R / ne
    tp = 2 * math.pi
    rho_cp = p["rho"] * p["cp"]
    k = p["k_across"]
    # element matrices
    ke = tp * k * (a + b) / 2 / dr                                  # stiffness: [[1,-1],[-1,1]] * ke
    # mass integrals of phi_i phi_j r over [a, b]
    m_aa = tp * dr * (3 * a + b) / 12
    m_bb = tp * dr * (a + 3 * b) / 12
    m_ab = tp * dr * (a + b) / 12
    load_a = tp * dr * (2 * a + b) / 6                              # integral of phi_a r
    load_b = tp * dr * (a + 2 * b) / 6
    nn = ne + 1
    diag_K = np.zeros(nn)
    np.add.at(diag_K, np.arange(ne), ke)
    np.add.at(diag_K, np.arange(1, nn), ke)
    off_K = -ke                                                     # (i, i+1)
    w = np.zeros(nn)
    np.add.at(w, np.arange(ne), load_a)
    np.add.at(w, np.arange(1, nn), load_b)
    # can capacity per unit height, spread over the 21700's outer area (D4, the two-cell study's 9 g at 500 J/(kg K))
    R21, H21 = L.CELL["21700"]["R"], L.CELL["21700"]["H"]
    c_can_area = 9e-3 * 500.0 / (2 * math.pi * R21 * H21 + 2 * math.pi * R21 ** 2)
    if consistent:
        diag_C = np.zeros(nn)
        np.add.at(diag_C, np.arange(ne), rho_cp * m_aa)
        np.add.at(diag_C, np.arange(1, nn), rho_cp * m_bb)
        off_C = rho_cp * m_ab
    else:
        diag_C = rho_cp * w.copy()
        off_C = np.zeros(ne)
    diag_C[-1] += c_can_area * tp * R
    D = np.zeros(nn)
    D[-1] = L.H_CONV * tp * R
    beta = 0.0
    if corrected:
        Lz, kz = H, p["k_along"]
        h_e = 1.0 / (1.0 / L.H_CONV + Lz / (6.0 * kz))
        beta = 2.0 * h_e / Lz
        if consistent:
            diag_D = D.copy()
            np.add.at(diag_D, np.arange(ne), beta * m_aa)
            np.add.at(diag_D, np.arange(1, nn), beta * m_bb)
            off_D = beta * m_ab
        else:
            diag_D = D + beta * w
            off_D = np.zeros(ne)
    else:
        diag_D, off_D = D.copy(), np.zeros(ne)
    # unit averages: exact integral of the linear field times r over each element, over the unit's area
    U = np.zeros((N, nn))
    for i in range(N):
        el = np.arange(i * sub, (i + 1) * sub)
        np.add.at(U[i], el, load_a[el])
        np.add.at(U[i], el + 1, load_b[el])
    area_u = U.sum(axis=1)
    U = U / area_u[:, None]
    return {"diag_K": diag_K, "off_K": off_K, "diag_C": diag_C, "off_C": off_C, "diag_D": diag_D, "off_D": off_D,
            "U": U, "load_a": load_a, "load_b": load_b, "sub": sub, "N": N, "nn": nn, "beta": beta, "w": w}


def banded(diag, off):
    ab = np.zeros((3, len(diag)))
    ab[0, 1:] = off
    ab[1] = diag
    ab[2, :-1] = off
    return ab


def fe_group_loads(fe, G):
    N, sub, nn = fe["N"], fe["sub"], fe["nn"]
    e = L.edges(N, G)
    B = np.zeros((nn, G))
    for g in range(G):
        el = np.arange(e[g] * sub, e[g + 1] * sub)
        np.add.at(B[:, g], el, fe["load_a"][el])
        np.add.at(B[:, g], el + 1, fe["load_b"][el])
    return B


def fe_step_responses(fe, G, dt, K):
    B = fe_group_loads(fe, G)
    A_ss = banded(fe["diag_K"] + fe["diag_D"], fe["off_K"] + fe["off_D"])
    th_inf = solve_banded((1, 1), A_ss, B)
    A = banded(fe["diag_C"] / dt + fe["diag_K"] + fe["diag_D"], fe["off_C"] / dt + fe["off_K"] + fe["off_D"])
    th = np.zeros_like(B)
    S = np.zeros((K, fe["N"], G))
    for k in range(K):
        rhs = fe["diag_C"][:, None] * th / dt
        rhs[:-1] += (fe["off_C"] / dt)[:, None] * th[1:]
        rhs[1:] += (fe["off_C"] / dt)[:, None] * th[:-1]
        th = solve_banded((1, 1), A, rhs + B)
        S[k] = fe["U"] @ th
    return S, fe["U"] @ th_inf


def fe_compare():
    out = {}
    jobs = [("radial", "21700", "m5C_2C"), ("corrected", "21700", "m5C_2C"), ("radial", "4680", "m5C_2C"),
            ("corrected", "4680", "m5C_2C"), ("radial", "21700", "charge10"), ("corrected", "21700", "charge10")]
    for model, cell, g in jobs:
        bc = "lat" if model == "radial" else "b"
        kp = os.path.join(L.KDIR, f"{model}_{bc}_{cell}_{g}_G15.npz")
        if not os.path.exists(kp):
            continue
        k = L.load_kernel(kp)
        K, dt = k["meta"]["K_stored"], k["meta"]["dt"]
        fe = fe_1d(cell, corrected=(model == "corrected"))
        S, S_inf = fe_step_responses(fe, 15, dt, K)
        r = {"kernel": os.path.basename(kp), "steps": K, "beta": fe["beta"]}
        if "S_unit" in k:
            ref = k["S_unit"].astype(float)
            r["S_unit_max_rel_diff"] = float(np.abs(S - ref).max() / np.abs(ref).max())
            r["S_inf_unit_max_rel_diff"] = float(np.abs(S_inf - k["S_inf_unit"]).max() / np.abs(k["S_inf_unit"]).max())
            r["what"] = "every unit's response to every one of the 15 groups"
        Su = S.sum(axis=2)
        r["S_unit_uniform_max_rel_diff"] = float(np.abs(Su - k["S_unit_uniform"]).max() / np.abs(k["S_unit_uniform"]).max())
        A = L.unit_to_group(fe["N"], 15)
        Sg = np.einsum("gn,knj->kgj", A, S)
        r["S_group_max_rel_diff"] = float(np.abs(Sg - k["S_group"]).max() / np.abs(k["S_group"]).max())
        r["S_inf_group_max_rel_diff"] = float(np.abs(A @ S_inf - k["S_inf_group"]).max() / np.abs(k["S_inf_group"]).max())
        out[f"{model}|{cell}|{g}"] = r
    # discretisation context (not a registered check): 4x finer mesh with the consistent capacity, same steps
    k = L.load_kernel(os.path.join(L.KDIR, "radial_lat_21700_m5C_2C_G15.npz"), keys=("S_unit_uniform",))
    K, dt = k["meta"]["K_stored"], k["meta"]["dt"]
    fe = fe_1d("21700", sub=80, consistent=True)
    S, _ = fe_step_responses(fe, 15, dt, K)
    Su = S.sum(axis=2)
    q = L.heat_on_grid("m5C_2C")
    T_reg = L.conv(k["S_unit_uniform"], k["S_unit_uniform"][-1], q)[-1]
    T_fine = L.conv(Su, Su[-1], q)[-1]
    out["context_finer_mesh_consistent_capacity_21700_radial"] = {
        "uniform_response_max_rel_diff": float(np.abs(Su - k["S_unit_uniform"]).max() / np.abs(k["S_unit_uniform"]).max()),
        "end_of_discharge_unit_rise_max_abs_diff_K": float(np.abs(T_fine - T_reg).max()),
        "note": "80 elements per unit and the consistent capacity against the registered 20 and lumped; a size of the "
                "spatial discretisation error, not a check of the registered kernel"}
    return out


if __name__ == "__main__":
    res = {"P1": p1()}
    print("P1 done", f"{time.time() - T0:.0f} s", res["P1"]["max_abs_K"], flush=True)
    res["V1_kernel_files"] = kernel_checks()
    print("kernel checks done", f"{time.time() - T0:.0f} s", flush=True)
    res["fe_1d_resolve"] = fe_compare()
    res["wall_s"] = time.time() - T0
    res["peak_memory"] = L.mem_note()
    L.dump("p1_v1.json", res)
    print(json.dumps({"P1_max_abs_K": res["P1"]["max_abs_K"], "P1_held": res["P1"]["held"],
                      "reciprocity_f32_worst": res["V1_kernel_files"]["reciprocity_stored_f32_worst"],
                      "reciprocity_within_f32": res["V1_kernel_files"]["reciprocity_all_within_f32_rounding"],
                      "reciprocity_steady_worst": res["V1_kernel_files"]["reciprocity_steady_f64_worst"],
                      "fe": res["fe_1d_resolve"], "wall_s": res["wall_s"], "peak": res["peak_memory"]}, indent=1))
