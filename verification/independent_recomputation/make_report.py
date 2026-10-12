"""Write the numeric sections of REPORT.md from results.json (my own numbers only).

The prose sections (status, method, problems, comparison) live in report_text.py so that
numbers in tables are never transcribed by hand.
"""
import json
import numpy as np

R = json.load(open("results.json"))
F = R["final"]
ORDER = ["1D_21700", "a_21700", "b_21700", "d_21700", "1D_4680", "a_4680", "b_4680"]
LABEL = {"1D_21700": "1D 21700", "a_21700": "(a) 21700", "b_21700": "(b) 21700", "d_21700": "(d) 21700",
         "1D_4680": "1D 4680", "a_4680": "(a) 4680", "b_4680": "(b) 4680"}


def f(x, n=4):
    if x is None:
        return "n/a"
    if isinstance(x, int):
        return str(x)
    return f"{x:.{n}f}"


def e(x, n=1):
    return "n/a" if x is None else f"{x:.{n}e}"


def table_main():
    L = []
    L.append("| Case | T core mid (C) | T surface mid (C) | Core-to-surface (K) | Axial T(0,H/2)-T(0,0) (K) | Axial T(0,H/2)-T(0,H) (K) | Unit spread (K) | Volume-mean T (C) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for k in ORDER:
        if k not in F:
            continue
        r = F[k]
        L.append(f"| {LABEL[k]} | {f(r['T_core_mid_C'], 5)} | {f(r['T_surf_mid_C'], 5)} | {f(r['dT_core_surface_K'], 5)} | "
                 f"{f(r.get('dT_axial_bot_K'), 5)} | {f(r.get('dT_axial_top_K'), 5)} | {f(r['units_spread_K'], 5)} | {f(r['vol_mean_C'], 5)} |")
    return "\n".join(L)


def table_offsets():
    L = []
    L.append("| 3D case | 1D used | Mean offset (K) | Min offset (K) | Max offset (K) | Units with abs offset > 1 K | Largest abs offset (K) |")
    L.append("|---|---|---|---|---|---|---|")
    for k in ORDER:
        if k not in F or "offsets_1d_minus_3d" not in F[k]:
            continue
        o = F[k]["offsets_1d_minus_3d"]
        cell = k.split("_")[1]
        n_units = 45 if cell == "21700" else 111
        L.append(f"| {LABEL[k]} | 1D {cell}, h = 400 | {f(o['mean'], 5)} | {f(o['min'], 5)} | {f(o['max'], 5)} | {o['n_over_1K']} of {n_units} | {f(o['max_abs'], 5)} |")
        if "extra_offsets_vs_1d_h25" in F[k]:
            o = F[k]["extra_offsets_vs_1d_h25"]
            L.append(f"| {LABEL[k]} (extra) | 1D {cell}, h = 25 | {f(o['mean'], 5)} | {f(o['min'], 5)} | {f(o['max'], 5)} | {o['n_over_1K']} of {n_units} | {f(o['max_abs'], 5)} |")
    return "\n".join(L)


def table_energy():
    L = []
    L.append("| Case | Heat generated (J) | Heat lost by convection (J) | Heat stored, roll + shell (J) | (gen - lost - stored)/gen |")
    L.append("|---|---|---|---|---|")
    for k in ORDER:
        if k not in F:
            continue
        r = F[k]
        L.append(f"| {LABEL[k]} | {f(r['E_gen_J'], 3)} | {f(r['E_lost_J'], 3)} | {f(r['E_stored_J'], 3)} | {e(r['balance_rel'])} |")
    return "\n".join(L)


def table_ladders():
    out = []
    for k in ORDER:
        if k not in F or "ladder" not in F[k]:
            continue
        r = F[k]
        c = r["convergence"]
        L = [f"**{LABEL[k]}** (vertex-centred scheme, dt = 1 s)", "",
             "| Nr x Nz | Core-to-surface (K) | Axial bot (K) | Unit spread (K) | Volume mean (C) | Mean offset (K) | Min offset (K) | Max offset (K) | n > 1 K |",
             "|---|---|---|---|---|---|---|---|---|"]
        for s in r["ladder"]:
            L.append(f"| {s['Nr']} x {s['Nz']} | {f(s['dT_core_surface_K'], 7)} | {f(s['dT_axial_bot_K'], 7)} | {f(s['units_spread_K'], 7)} | "
                     f"{f(s['vol_mean_C'], 7)} | {f(s.get('off_mean'), 6)} | {f(s.get('off_min'), 6)} | {f(s.get('off_max'), 6)} | {s.get('off_n_over_1K', 'n/a')} |")
        cs = c["dT_core_surface_K"]
        L.append("")
        L.append(f"Core-to-surface: observed order {f(cs['observed_order'], 2)}, Richardson error estimate of the finest grid "
                 f"{e(cs['richardson_err_finest'], 2)} K = {e(cs['err_rel_to_dTcs'], 2)} of the core-to-surface difference "
                 f"({f(100 * cs['err_rel_to_dTcs'], 5)} %). Largest Richardson error estimate over all listed quantities: "
                 f"{e(max(v['richardson_err_finest'] for v in c.values() if v['richardson_err_finest'] is not None), 2)} K.")
        out.append("\n".join(L))
    return "\n\n".join(out)


def table_timestep():
    ts = R["timestep"]
    L = ["| Case (grid 90 x 132) | dt (s) | Core-to-surface (K) | Axial bot (K) | Volume mean (C) |", "|---|---|---|---|---|"]
    for case, d in ts.items():
        for i, dt in enumerate(d["dt"]):
            L.append(f"| ({case}) 21700 | {dt:g} | {f(d['dT_core_surface_K'][i], 9)} | {f(d['dT_axial_bot_K'][i], 9)} | {f(d['vol_mean_C'][i], 9)} |")
    L.append("")
    for case, d in ts.items():
        L.append(f"- ({case}): observed temporal order {f(d['observed_order'], 2)}; core-to-surface at dt = 1 s differs from dt = 0.25 s by "
                 f"{e(d['err_dt1_vs_finest_dt_K'], 2)} K; plain Crank-Nicolson without the Rannacher start gives "
                 f"{f(d['no_rannacher_dt1_dT_core_surface_K'], 9)} K at dt = 1 s.")
    return "\n".join(L)


def table_1d():
    L = ["| Case | Nr | Core-to-surface (K) | Error vs Bessel series (K) | Max abs unit error vs series (K) |", "|---|---|---|---|---|"]
    for k in ("1D_21700", "1D_4680"):
        if k not in F:
            continue
        for s in F[k]["fv_ladder"]:
            L.append(f"| {LABEL[k]} | {s['Nr']} | {f(s['dT_core_surface_K'], 7)} | {e(s['err_vs_analytic_K'], 2)} | {e(s['units_max_abs_err_K'], 2)} |")
    return "\n".join(L)


def table_cross():
    L = ["| Case | Scheme C grid | Core-to-surface C minus V (K) | Axial C minus V (K) | Unit spread C minus V (K) | Volume mean C minus V (K) | Max abs unit diff (K) |",
         "|---|---|---|---|---|---|---|"]
    for k in ORDER:
        if k not in F or "crosscheck_scheme_C" not in F[k]:
            continue
        c = F[k]["crosscheck_scheme_C"]
        L.append(f"| {LABEL[k]} | {c['Nr']} x {c['Nz']} | {e(c['diff_dT_core_surface_K'], 2)} | {e(c['diff_dT_axial_bot_K'], 2)} | "
                 f"{e(c['diff_units_spread_K'], 2)} | {e(c['diff_vol_mean_C'], 2)} | {e(c['units_max_abs_diff_K'], 2)} |")
    return "\n".join(L)


if __name__ == "__main__":
    sections = dict(main=table_main(), offsets=table_offsets(), energy=table_energy(), ladders=table_ladders(),
                    timestep=table_timestep(), oned=table_1d(), cross=table_cross())
    json.dump(sections, open("report_tables.json", "w"), indent=1)
    for k, v in sections.items():
        print(f"===== {k}\n{v}\n")
