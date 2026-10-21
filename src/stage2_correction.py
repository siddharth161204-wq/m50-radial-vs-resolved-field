#!/usr/bin/env python3
"""Stage 2, Part B: the one-term end correction of D18 for the radial model, its checks (V1 to V3) and its comparison
with the resolved cell (B2). Stage 1's model (src/radial1d.py) is subclassed, not edited.
Writes results/stage2_correction.json and results/stage2_correction.csv."""
import csv
import json
import math
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.special import i0, i1

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402


def end_beta(h, L, k_z):
    """D18: h_e = 1 / (1/h + L/(6 k_z)), beta = 2 h_e / L."""
    h_e = 1.0 / (1.0 / h + L / (6.0 * k_z))
    return 2.0 * h_e / L, h_e


class Corrected(R1.Radial1D):
    def __init__(self, cell, props=None, h=C.H_PAPER, ends=True, beta=None, k_z=None):
        super().__init__(cell, props=props, h=h)
        self.L = self.cc["H"]
        self.k_z = k_z if k_z is not None else self.cc["k_along"]
        if beta is None:
            beta = end_beta(h, self.L, self.k_z)[0] if ends else 0.0
        self.beta = beta
        self.d_sink = beta * self.w_vol

    def axial_core(self, T, Ta):
        return self.beta * (T[0] - Ta) * self.L ** 2 / (8.0 * self.k_z)

    def run(self, q_of_t, t_end, T_amb_C, dt_target=1.0, snap_times=()):
        n, dt = R1.time_grid(t_end, dt_target)
        snap_steps = {int(round(ts / dt)): ts for ts in snap_times}
        lu = spla.splu((self.K + sp.diags(self.C / dt + self.d_conv + self.d_sink)).tocsc())
        Ta = T_amb_C
        T = np.full(self.N + 1, Ta)
        E0 = self.C @ T
        E_gen = E_side = E_end = 0.0
        snaps = {}
        for k in range(n):
            t = (k + 1) * dt
            q = q_of_t(t)
            T = lu.solve(self.C / dt * T + (self.d_conv + self.d_sink) * Ta + self.w_vol * q)
            E_gen += dt * q * self.w_vol.sum()
            E_side += dt * float(self.d_conv @ (T - Ta))
            E_end += dt * float(self.d_sink @ (T - Ta))
            if (k + 1) in snap_steps:
                s = self._snap(T, self.U @ T, t, every=1)
                s["dT_axial_core"] = self.axial_core(T, Ta)
                snaps[snap_steps[k + 1]] = s
        stored = self.C @ T - E0
        end = self._snap(T, self.U @ T, t_end, every=1)
        end["dT_axial_core"] = self.axial_core(T, Ta)
        return {"cell": self.cell, "beta": self.beta, "n_steps": n, "dt": dt, "end": end, "snaps": snaps,
                "energy_per_m": {"generated": E_gen, "side": E_side, "ends": E_end, "stored": stored,
                                 "residual_rel": (stored + E_side + E_end - E_gen) / E_gen},
                "ends_share": E_end / (E_side + E_end)}

    def steady(self, q, Ta):
        T = spla.spsolve((self.K + sp.diags(self.d_conv + self.d_sink)).tocsc(),
                         (self.d_conv + self.d_sink) * Ta + self.w_vol * q)
        return T


def analytic_steady(r, q, beta, k, h, R):
    m = math.sqrt(beta / k)
    return q / beta * (1.0 - h * i0(m * r) / (k * m * i1(m * R) + h * i0(m * R)))


def compare(units_1d, units_3d):
    u1, u3 = np.array(units_1d), np.array(units_3d)
    off = u1 - u3
    s1, s3 = u1.max() - u1.min(), u3.max() - u3.min()
    return {"mean_abs_offset_K": float(np.abs(off).mean()), "max_abs_offset_K": float(np.abs(off).max()),
            "mean_offset_K": float(off.mean()), "spread_1d_K": float(s1), "spread_3d_K": float(s3),
            "spread_overstatement": float(s1 / s3 - 1)}


def main():
    out = {"beta": {}, "checks": {}, "B2": {}}
    split = json.load(open(os.path.join(C.RESULTS, "stage2_split.json"))) \
        if os.path.exists(os.path.join(C.RESULTS, "stage2_split.json")) else {}
    post = json.load(open(os.path.join(C.RESULTS, "posthoc_matched_time.json")))["cases"]
    for cell, h in (("21700", 400.0), ("4680", 400.0), ("21700", 25.0)):
        cc = C.cell_constants(cell)
        b, he = end_beta(h, cc["H"], cc["k_along"])
        out["beta"][f"{cell}|h={h:g}"] = {"h_e": he, "beta": b, "L": cc["H"], "k_z": cc["k_along"]}
    # V1: beta = 0 reproduces Stage 1's radial model; V3: steady solution against the modified Bessel profile
    for cell in ("21700", "4680"):
        q, t_end, _ = R1.load_heat("Chen2020_m5C_2C")
        r0 = R1.Radial1D(cell).run(q, t_end, -5.0)
        rc = Corrected(cell, ends=False).run(q, t_end, -5.0)
        out["checks"][f"V1|{cell}"] = {"units_max_abs_diff_K": float(np.max(np.abs(
            np.array(r0["end"]["units"]) - np.array(rc["end"]["units"])))),
            "dT_cs_diff_K": abs(r0["end"]["dT_core_surface"] - rc["end"]["dT_core_surface"])}
        m = Corrected(cell)
        qs = 1.5e5
        Tn = m.steady(qs, 0.0)
        Ta_ = analytic_steady(m.r, qs, m.beta, m.cc["k_across"], m.h, m.R)
        out["checks"][f"V3|{cell}"] = {"q_W_m3": qs, "max_abs_diff_K": float(np.max(np.abs(Tn - Ta_))),
                                       "dT_cs_code_K": float(Tn[0] - Tn[-1]), "dT_cs_analytic_K": float(Ta_[0] - Ta_[-1]),
                                       "ends_share_steady": float(m.beta * (m.w_vol @ Tn) /
                                                                  (m.beta * (m.w_vol @ Tn) + m.h * 2 * math.pi * m.R * Tn[-1]))}
    rows = []
    for cell, bc, h in (("21700", "b", 400.0), ("4680", "b", 400.0), ("21700", "d", 25.0)):
        for heat in R1.CASES_REGISTERED:
            q, t_end, _ = R1.load_heat(heat)
            Ta = R1.amb_of(heat)
            rc = Corrected(cell, h=h).run(q, t_end, Ta)
            r0 = R1.Radial1D(cell, h=h).run(q, t_end, Ta)
            f3 = json.load(open(os.path.join(C.RESULTS, "fields", f"{cell}_{bc}_{heat}.json")))["end"]
            key = f"{cell}_{bc}_{heat}"
            res_share = split.get(key, {}).get("ends_share")
            if res_share is None and key in ("21700_b_Chen2020_m5C_2C", "4680_b_Chen2020_m5C_2C"):
                res_share = post[f"{cell}_b"]["ends_share_of_heat_lost"]
            cmp_c, cmp_0 = compare(rc["end"]["units"], f3["units"]), compare(r0["end"]["units"], f3["units"])
            rec = {"corrected": cmp_c, "uncorrected": cmp_0, "ends_share_corrected": rc["ends_share"],
                   "ends_share_resolved": res_share, "dT_axial_core_corrected_K": rc["end"]["dT_axial_core"],
                   "dT_axial_core_resolved_K": f3["dT_axial_bottom"],
                   "axial_ratio_corrected_over_resolved": rc["end"]["dT_axial_core"] / f3["dT_axial_bottom"],
                   "dT_cs_corrected_K": rc["end"]["dT_core_surface"], "dT_cs_uncorrected_K": r0["end"]["dT_core_surface"],
                   "dT_cs_resolved_K": f3["dT_core_surface"], "energy_residual_rel": rc["energy_per_m"]["residual_rel"],
                   "units_corrected": rc["end"]["units"], "units_uncorrected": r0["end"]["units"], "units_resolved": f3["units"]}
            out["B2"][key] = rec
            rows.append([cell, bc, h, heat, rc["ends_share"], res_share, cmp_c["mean_abs_offset_K"], cmp_c["max_abs_offset_K"],
                         cmp_0["mean_abs_offset_K"], cmp_c["spread_overstatement"], cmp_0["spread_overstatement"],
                         rc["end"]["dT_axial_core"], f3["dT_axial_bottom"], rec["axial_ratio_corrected_over_resolved"],
                         rc["end"]["dT_core_surface"], r0["end"]["dT_core_surface"], f3["dT_core_surface"],
                         rc["energy_per_m"]["residual_rel"]])
            print(key, f"share {rc['ends_share']:.4f}/{res_share}", f"off {cmp_c['mean_abs_offset_K']:.3f} (was {cmp_0['mean_abs_offset_K']:.3f})",
                  f"spread {cmp_c['spread_overstatement']:+.3f} (was {cmp_0['spread_overstatement']:+.3f})",
                  f"axial {rec['axial_ratio_corrected_over_resolved']:.3f}", flush=True)
    out["checks"]["V2_max_abs_residual"] = max(abs(v["energy_residual_rel"]) for v in out["B2"].values())
    json.dump(out, open(os.path.join(C.RESULTS, "stage2_correction.json"), "w"), indent=1)
    with open(os.path.join(C.RESULTS, "stage2_correction.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell", "case", "h_W_m2K", "heat", "ends_share_corrected", "ends_share_resolved",
                    "mean_abs_offset_corrected_K", "max_abs_offset_corrected_K", "mean_abs_offset_uncorrected_K",
                    "spread_overstatement_corrected", "spread_overstatement_uncorrected", "dT_axial_core_corrected_K",
                    "dT_axial_core_resolved_K", "axial_corrected_over_resolved", "dT_cs_corrected_K",
                    "dT_cs_uncorrected_K", "dT_cs_resolved_K", "energy_residual_rel"])
        for r in rows:
            w.writerow([f"{x:.6g}" if isinstance(x, float) else ("" if x is None else x) for x in r])
    print(json.dumps(out["checks"], indent=1))


if __name__ == "__main__":
    main()
