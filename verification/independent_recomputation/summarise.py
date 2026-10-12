"""Assemble final numbers, convergence evidence and unit offsets from runs.jsonl.

Writes results.json, results.csv, units_end.csv, convergence.csv. Uses only my own runs.
"""
import json, csv, math
import numpy as np
from params import GEOMS, T_AMB

runs = [json.loads(l) for l in open("runs.jsonl")]


def pick(**kw):
    out = [r for r in runs if all(r.get(k) == v for k, v in kw.items())]
    return out


def analytic(cell, case="1D"):
    rr = [r for r in runs if r["scheme"] == "1D-analytic" and r["cell"] == cell and r["case"] == case]
    return max(rr, key=lambda r: r["n_modes"]) if rr else None


def ladder(cell, case, scheme="V", study="space"):
    rr = [r for r in runs if r["scheme"] == scheme and r["cell"] == cell and r["case"] == case
          and r.get("study") == study and r.get("dt") == 1.0]
    return sorted(rr, key=lambda r: r["Nr"])


def offsets(u1d, u3d):
    d = np.asarray(u1d) - np.asarray(u3d)
    near = np.where(np.abs(np.abs(d) - 1.0) < 0.05)[0]
    return dict(mean=float(d.mean()), min=float(d.min()), max=float(d.max()),
                n_over_1K=int(np.sum(np.abs(d) > 1.0)),
                max_abs=float(np.max(np.abs(d))),
                closest_to_1K=float(d[np.argmin(np.abs(np.abs(d) - 1.0))]),
                n_over_0p95K=int(np.sum(np.abs(d) > 0.95)), n_over_1p05K=int(np.sum(np.abs(d) > 1.05)),
                units_within_0p05K_of_1K=[[int(i + 1), float(d[i])] for i in near]), d


def richardson(vals):
    """vals ordered coarse to fine (refinement ratio 2). Returns observed order and error estimate."""
    if len(vals) < 2:
        return None, None
    e_last = vals[-1] - vals[-2]
    if len(vals) >= 3:
        e_prev = vals[-2] - vals[-3]
        if e_last != 0 and e_prev != 0 and np.sign(e_last) == np.sign(e_prev):
            p = math.log2(abs(e_prev / e_last))
        else:
            p = float("nan")
    else:
        p = float("nan")
    pe = p if (p == p and 0.5 < p < 6) else 2.0
    err = abs(e_last) / (2 ** pe - 1)
    return p, err


METRICS = ["dT_core_surface_K", "dT_axial_bot_K", "dT_axial_top_K", "units_spread_K", "vol_mean_C",
           "T_core_mid_C", "T_surf_mid_C"]

final = {}
conv_rows = []
units_table = {}
CONFIGS = [("21700", "1D"), ("21700", "a"), ("21700", "b"), ("21700", "d"),
           ("4680", "1D"), ("4680", "a"), ("4680", "b")]

for cell, case in CONFIGS:
    key = f"{case}_{cell}"
    nu = GEOMS[cell]["n_units"]
    an = analytic(cell)
    if case == "1D":
        if an is None:
            continue
        u = np.asarray(an["units_C"])
        fv = [r for r in runs if r["scheme"] == "1D-FV" and r["cell"] == cell]
        fv = sorted(fv, key=lambda r: r["Nr"])
        final[key] = dict(
            model="1D radial, semi-analytical Bessel series (%d modes); FV ladder agrees" % an["n_modes"],
            T_core_mid_C=an["T_core_mid_C"], T_surf_mid_C=an["T_surf_mid_C"],
            dT_core_surface_K=an["dT_core_surface_K"],
            dT_axial_bot_K=None, dT_axial_top_K=None,
            units_spread_K=an["units_spread_K"], vol_mean_C=an["vol_mean_C"],
            E_gen_J=an["E_gen_J"], E_lost_J=an["E_lost_J"], E_stored_J=an["E_stored_J"],
            balance_rel=an["balance_rel"],
            fv_finest=dict(Nr=fv[-1]["Nr"], dT_core_surface_K=fv[-1]["dT_core_surface_K"],
                           units_spread_K=fv[-1]["units_spread_K"], vol_mean_C=fv[-1]["vol_mean_C"],
                           balance_rel=fv[-1]["balance_rel"]) if fv else None,
            fv_ladder=[dict(Nr=r["Nr"], dT_core_surface_K=r["dT_core_surface_K"],
                            err_vs_analytic_K=r["dT_core_surface_K"] - an["dT_core_surface_K"],
                            units_max_abs_err_K=float(np.max(np.abs(np.asarray(r["units_C"]) - u))))
                       for r in fv],
        )
        units_table[key] = u
        continue
    lad = ladder(cell, case)
    if not lad:
        continue
    fin = lad[-1]
    u3 = np.asarray(fin["units_C"])
    rec = dict(model="3D (r,z) vertex-centred FV, Nr=%d Nz=%d, dt=1 s CN" % (fin["Nr"], fin["Nz"]),
               Nr=fin["Nr"], Nz=fin["Nz"])
    for m in METRICS:
        rec[m] = fin[m]
    for m in ("E_gen_J", "E_lost_J", "E_stored_J", "balance_rel"):
        rec[m] = fin[m]
    rec["vol_mean_from_units_C"] = fin["vol_mean_from_units_C"]
    if an is not None:
        o, d = offsets(an["units_C"], u3)
        rec["offsets_1d_minus_3d"] = o
        rec["dT_core_surface_1d_K"] = an["dT_core_surface_K"]
        rec["units_spread_1d_K"] = an["units_spread_K"]
        units_table[key + "_offset"] = d
    if case == "d":
        an25 = analytic(cell, "1D_h25")
        if an25 is not None:
            o25, d25 = offsets(an25["units_C"], u3)
            rec["extra_offsets_vs_1d_h25"] = o25
            rec["extra_1d_h25"] = dict(dT_core_surface_K=an25["dT_core_surface_K"],
                                       units_spread_K=an25["units_spread_K"],
                                       vol_mean_C=an25["vol_mean_C"],
                                       T_core_mid_C=an25["T_core_mid_C"], T_surf_mid_C=an25["T_surf_mid_C"])
    units_table[key] = u3
    # convergence on the ladder, including offset statistics per level
    lv_stats = []
    for r in lad:
        st = dict(Nr=r["Nr"], Nz=r["Nz"])
        for m in METRICS:
            st[m] = r[m]
        if an is not None:
            o, _ = offsets(an["units_C"], r["units_C"])
            st["off_mean"] = o["mean"]; st["off_min"] = o["min"]; st["off_max"] = o["max"]
            st["off_n_over_1K"] = o["n_over_1K"]
        lv_stats.append(st)
    conv = {}
    for m in METRICS + (["off_mean", "off_min", "off_max"] if an is not None else []):
        vals = [s[m] for s in lv_stats]
        p, err = richardson(vals)
        conv[m] = dict(values=vals, observed_order=p, richardson_err_finest=err,
                       err_rel_to_dTcs=(err / fin["dT_core_surface_K"]) if err is not None else None)
        for s in lv_stats:
            pass
    rec["convergence"] = conv
    rec["ladder"] = lv_stats
    # cross-check with scheme C at its finest level
    cc = sorted([r for r in runs if r["scheme"] == "C" and r["cell"] == cell and r["case"] == case],
                key=lambda r: r["Nr"])
    if cc:
        c = cc[-1]
        cmp = dict(Nr=c["Nr"], Nz=c["Nz"])
        for m in METRICS:
            cmp[m] = c[m]
            cmp["diff_" + m] = c[m] - fin[m]
        cmp["units_max_abs_diff_K"] = float(np.max(np.abs(np.asarray(c["units_C"]) - u3)))
        if an is not None:
            o, _ = offsets(an["units_C"], c["units_C"])
            cmp["offsets"] = o
        cmp["ladder"] = [dict(Nr=r["Nr"], Nz=r["Nz"], dT_core_surface_K=r["dT_core_surface_K"],
                              dT_axial_bot_K=r["dT_axial_bot_K"], units_spread_K=r["units_spread_K"],
                              vol_mean_C=r["vol_mean_C"]) for r in cc]
        rec["crosscheck_scheme_C"] = cmp
    final[key] = rec
    for s in lv_stats:
        row = dict(config=key)
        row.update(s)
        conv_rows.append(row)

# time-step study
ts = {}
for case in ("a", "b", "d"):
    rr = [r for r in runs if r.get("study") == "timestep" and r["case"] == case]
    if not rr:
        continue
    ran = sorted([r for r in rr if r["rannacher"]], key=lambda r: -r["dt"])
    nor = [r for r in rr if not r["rannacher"]]
    vals = [r["dT_core_surface_K"] for r in ran]
    p, err = richardson(vals)
    ts[case] = dict(grid="Nr=90 Nz=132",
                    dt=[r["dt"] for r in ran], dT_core_surface_K=vals,
                    dT_axial_bot_K=[r["dT_axial_bot_K"] for r in ran],
                    vol_mean_C=[r["vol_mean_C"] for r in ran],
                    observed_order=p,
                    err_dt1_vs_finest_dt_K=(vals[[r["dt"] for r in ran].index(1.0)] - vals[-1]) if 1.0 in [r["dt"] for r in ran] else None,
                    no_rannacher_dt1_dT_core_surface_K=nor[0]["dT_core_surface_K"] if nor else None)

sens = [r for r in runs if r.get("study") == "rhocp_task_text"]
sens_out = []
for r in sens:
    base = [x for x in ladder(r["cell"], r["case"]) if x["Nr"] == r["Nr"]]
    if base:
        sens_out.append(dict(cell=r["cell"], case=r["case"], Nr=r["Nr"], rhocp=r["rhocp"],
                             d_dT_core_surface_K=r["dT_core_surface_K"] - base[0]["dT_core_surface_K"],
                             d_vol_mean_K=r["vol_mean_C"] - base[0]["vol_mean_C"]))

out = dict(final=final, timestep=ts, rhocp_sensitivity=sens_out)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, float) and (o != o):
        return None
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


json.dump(clean(out), open("results.json", "w"), indent=1)

# flat CSV of the headline numbers
cols = ["config", "model", "T_core_mid_C", "T_surf_mid_C", "dT_core_surface_K", "dT_axial_bot_K",
        "dT_axial_top_K", "units_spread_K", "off_mean_K", "off_min_K", "off_max_K", "off_n_over_1K",
        "vol_mean_C", "E_gen_J", "E_lost_J", "E_stored_J", "balance_rel", "disc_err_dTcs_K"]
with open("results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(cols)
    for cell, case in CONFIGS:
        key = f"{case}_{cell}"
        if key not in final:
            continue
        r = final[key]
        o = r.get("offsets_1d_minus_3d", {})
        de = r.get("convergence", {}).get("dT_core_surface_K", {}).get("richardson_err_finest")
        w.writerow([key, r["model"], r["T_core_mid_C"], r["T_surf_mid_C"], r["dT_core_surface_K"],
                    r.get("dT_axial_bot_K"), r.get("dT_axial_top_K"), r["units_spread_K"],
                    o.get("mean"), o.get("min"), o.get("max"), o.get("n_over_1K"),
                    r["vol_mean_C"], r["E_gen_J"], r["E_lost_J"], r["E_stored_J"], r["balance_rel"], de])

with open("convergence.csv", "w", newline="") as f:
    if conv_rows:
        keys = list(conv_rows[0].keys())
        for r in conv_rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in conv_rows:
            w.writerow(r)

for cell in ("21700", "4680"):
    nu = GEOMS[cell]["n_units"]; R = GEOMS[cell]["R"]
    edges = np.linspace(0, R, nu + 1)
    keys = [k for k in units_table if k.endswith(cell) or k.endswith(cell + "_offset")]
    if not keys:
        continue
    with open(f"units_end_{cell}.csv", "w", newline="") as f:
        w = csv.writer(f)
        hdr = ["unit", "r_in_mm", "r_out_mm"] + [k + ("_K" if k.endswith("offset") else "_C") for k in keys]
        w.writerow(hdr)
        for i in range(nu):
            w.writerow([i + 1, edges[i] * 1e3, edges[i + 1] * 1e3] + [float(units_table[k][i]) for k in keys])

print(json.dumps({k: {m: v.get(m) for m in ("dT_core_surface_K", "dT_axial_bot_K", "units_spread_K", "vol_mean_C", "balance_rel")}
                  for k, v in final.items()}, indent=1))
for k, v in final.items():
    if "offsets_1d_minus_3d" in v:
        print(k, "offsets", v["offsets_1d_minus_3d"])
    if "convergence" in v:
        c = v["convergence"]["dT_core_surface_K"]
        print(k, "dTcs ladder", ["%.7f" % x for x in c["values"]], "p=", c["observed_order"], "err=", c["richardson_err_finest"])
print("timestep", json.dumps(ts, indent=0))
