#!/usr/bin/env python3
"""Stage 5, Parts C and D (D31 to D33): the registered runs of the coupled and single-unit models.

python3 src/stage5_runs.py discharge --cell 21700 --case b_m5C_2C --set ORegan2022 [--models radial,resolved,corrected]
python3 src/stage5_runs.py charge --cell 21700 --set ORegan2022           (the specification's limits and brackets)
python3 src/stage5_runs.py limit --cell 21700 --set ORegan2022 --T 0      (plating-limited rates at one ambient)
Each run is stored in results/stage5_runs/<name>.npz (src/stage5_coupled.py save_run); the limit searches in
results/stage5_runs/limit_<cell>_<set>_<T>C.json."""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage5_common as S5  # noqa: E402
import stage5_coupled as SC  # noqa: E402

# Part C cases (D31): key -> (cell, ends, ambient C, current A of the 5 A h model, grid)
DISCHARGE_CASES = {
    "21700_b_m5C_2C": ("21700", "b", -5.0, 10.0, "m5C_2C"),
    "21700_b_p25C_2C": ("21700", "b", 25.0, 10.0, "p25C_2C"),
    "21700_b_p25C_1.25C": ("21700", "b", 25.0, 6.25, "p25C_1.25C"),
    "21700_a_m5C_2C": ("21700", "a", -5.0, 10.0, "m5C_2C"),
    "4680_b_m5C_2C": ("4680", "b", -5.0, 10.0, "m5C_2C"),
    "21700_b_p25C_3C": ("21700", "b", 25.0, 15.0, "p25C_3C"),
}
# Part D cases (D32): key -> (rate in the specification's C, ambient C, registered?)
CHARGE_CASES = {"0.3C_0C": (0.3, 0.0, True), "0.7C_25C": (0.7, 25.0, True),
                "0.7C_0C": (0.7, 0.0, False), "1C_25C": (1.0, 25.0, False), "2C_25C": (2.0, 25.0, False)}


def models_for(ends):
    """The three kernels (D29): with the ends insulated the end-corrected model is the radial model (beta = 0)."""
    if ends == "a":
        return {"radial": ("radial", "lat"), "resolved": ("resolved", "a"), "corrected": ("radial", "lat")}
    return {"radial": ("radial", "lat"), "resolved": ("resolved", "b"), "corrected": ("corrected", "b")}


def run_name(part, case, kernel_label, pset, heat, single, G):
    return f"{part}_{case}_{kernel_label}_{pset}_{heat}_{'single' if single else 'coupled'}_G{G}"


def oneway_group_temps(kern, Ta, gridname):
    """Group temperatures under the registered heat at steps 0..n (D30, one-way heat)."""
    q = S5.registered_heat_on_grid(gridname)
    rise = S5.conv_series(kern.S_group.sum(axis=2)[:, :, None], kern.S_inf_group.sum(axis=1)[:, None], q)
    return np.vstack([np.full(kern.G, Ta), Ta + rise])


_BUILT = {}


def built_for(pset, soc, W, single):
    key = (pset, soc, tuple(np.round(W, 15)), single)
    if key not in _BUILT:
        _BUILT[key] = SC.make(pset, soc, W, single)
    return _BUILT[key]


def discharge(case, pset, models=("radial", "resolved", "corrected"), heats=("two-way", "one-way"), G=S5.G_REG,
              gridname=None, part="C", force=False):
    cell, ends, Ta, I, grid0 = DISCHARGE_CASES[case]
    gridname = gridname or grid0
    mfor = models_for(ends)
    for label in models:
        mdl, bc = mfor[label]
        if ends == "a" and label == "corrected":
            continue                                   # identical to the radial runs (D29)
        kern = S5.Kernel(S5.kernel_path(mdl, bc, cell, gridname, G))
        for heat in heats:
            Tg = oneway_group_temps(kern, Ta, gridname) if heat == "one-way" else None
            for single in (False, True):
                name = run_name(part, f"{case}" + ("" if gridname == grid0 else f"_{gridname}"), label, pset, heat, single, G)
                if not force and os.path.exists(os.path.join(S5.RUNDIR, name + ".npz")):
                    continue
                W = np.array([1.0]) if single else kern.W
                b = built_for(pset, 1.0, W, single)
                oneway = None
                if heat == "one-way":
                    oneway = (Tg @ kern.W)[:, None] if single else Tg
                out = SC.run("discharge", cell, pset, Ta, I, kern, heat=heat, single=single, oneway_T=oneway,
                             built=b, label=name)
                out["meta"].update({"case": case, "kernel_label": label, "grid": gridname, "ends": ends})
                SC.save_run(out, name)
                m = out["meta"]
                print(f"{name}: {m['status']} at {m['t_end']:.1f} s ({m['n_steps']} steps), held {m['held_steps_past_archive']}, "
                      f"max resid {out['resid'].max():.1e}, {m['wall_s']:.0f} s", flush=True)


def charge_current(rate):
    return -rate * S5.C_SPEC_A


def charge(cell, pset, cases=tuple(CHARGE_CASES), models=("radial", "resolved", "corrected"), G=S5.G_REG,
           gridname="charge10", part="D", force=False, store_potentials_for=None):
    mfor = models_for("b")
    for label in models:
        mdl, bc = mfor[label]
        kern = S5.Kernel(S5.kernel_path(mdl, bc, cell, gridname, G))
        for case in cases:
            rate, Ta, _ = CHARGE_CASES[case]
            for single in (False, True):
                name = run_name(part, f"{cell}_{case}" + ("" if gridname == "charge10" else f"_{gridname}"), label, pset,
                                "two-way", single, G)
                if not force and os.path.exists(os.path.join(S5.RUNDIR, name + ".npz")):
                    continue
                W = np.array([1.0]) if single else kern.W
                b = built_for(pset, 0.0, W, single)
                pots = store_potentials_for is not None and (case, label, single) == store_potentials_for
                out = SC.run("charge", cell, pset, Ta, charge_current(rate), kern, heat="two-way", single=single,
                             built=b, label=name, store_potentials=pots)
                out["meta"].update({"case": case, "rate_spec_C": rate, "kernel_label": label, "grid": gridname})
                SC.save_run(out, name)
                mm = min(out["margin_nodes_min"].min(), out["margin_interface"].min())
                m = out["meta"]
                print(f"{name}: {m['status']} at {m['t_end']:.0f} s, margin {1e3 * mm:+.2f} mV, max resid "
                      f"{out['resid'].max():.1e}, {m['wall_s']:.0f} s", flush=True)


# ----------------------------------------------------------------------------------------------------------------
# D3: the plating-limited rate
# ----------------------------------------------------------------------------------------------------------------
def trial(cell, pset, Ta, rate, kern, single):
    W = np.array([1.0]) if single else kern.W
    b = built_for(pset, 0.0, W, single)
    out = SC.run("charge", cell, pset, Ta, charge_current(rate), kern, heat="two-way", single=single, built=b,
                 stop_on_negative_margin=True)
    mn = out["margin_nodes_min"]
    mi = out["margin_interface"]
    both = np.minimum(mn, mi)
    k, g = np.unravel_index(int(np.argmin(both)), both.shape)
    passed = out["meta"]["status"].startswith("event") and float(both.min()) >= 0.0
    return {"rate": round(rate, 6), "passed": bool(passed), "status": out["meta"]["status"],
            "min_margin_V": float(both.min()), "group": int(g) + 1, "t_min_s": float(out["t"][k]),
            "at_interface": bool(mi[k, g] <= mn[k, g]), "t_end_s": float(out["t"][-1]),
            "charge_Ah": float(-charge_current(rate) * out["t"][-1] / 3600), "steps": int(out["meta"]["n_steps"]),
            "wall_s": float(out["meta"]["wall_s"])}


def search(cell, pset, Ta, kern, single, start, fine=False, log=None):
    """D32: scan by 0.05C from a passing start up to the first failure, then halve the bracket three times (to
    0.00625C), or to 0.001C (fine, P9's four rates)."""
    trials = []

    def T(r):
        res = trial(cell, pset, Ta, r, kern, single)
        trials.append(res)
        if log:
            log(f"    rate {r:.5f}C: {'pass' if res['passed'] else 'fail'}  margin {1e3 * res['min_margin_V']:+.2f} mV "
                f"group {res['group']} at {res['t_min_s']:.0f} s ({res['status']}, {res['wall_s']:.0f} s)")
        return res["passed"]

    r = max(0.05, start)
    if not T(r):
        while True:
            r = round(r - 0.05, 10)
            if r < 0.05 - 1e-12:
                return {"rate": None, "below": 0.05, "trials": trials}
            if T(r):
                break
    lo = r
    while True:
        hi = round(lo + 0.05, 10)
        if not T(hi):
            break
        lo = hi
    coarse = None
    halvings = 0
    while True:
        if halvings == 3:
            coarse = {"rate": lo, "fail_above": hi, "width": hi - lo}
            if not fine:
                break
        if hi - lo <= 0.001:
            break
        mid = round((lo + hi) / 2, 10)
        if T(mid):
            lo = mid
        else:
            hi = mid
        halvings += 1
    out = dict(coarse)
    out["trials"] = trials
    if fine:
        out["fine_rate"], out["fine_fail_above"], out["fine_width"] = lo, hi, hi - lo
    return out


def limit(cell, pset, Ta, models=("radial", "resolved", "corrected"), fine_resolved=False, G=S5.G_REG,
          which=("single", "coupled")):
    path = os.path.join(S5.RUNDIR, f"limit_{cell}_{pset}_{Ta:g}C.json")
    res = json.load(open(path)) if os.path.exists(path) else {}
    mfor = models_for("b")
    log = lambda s: print(s, flush=True)
    for label in models:
        mdl, bc = mfor[label]
        kern = S5.Kernel(S5.kernel_path(mdl, bc, cell, "charge10", G))
        for single in (True, False):
            if ("single" if single else "coupled") not in which:
                continue
            key = f"{label}|{'single' if single else 'coupled'}"
            fine = fine_resolved and label == "resolved"
            if key in res and (not fine or res[key].get("fine")):
                continue
            if single:
                start = 0.05
            else:
                s_rate = res[f"{label}|single"]["rate"]
                start = max(0.05, math.floor((s_rate - 0.10) * 100 + 1e-9) / 100) if s_rate else 0.05
            log(f"  {cell} {pset} {Ta:g} C {key}: start {start:.2f}C")
            t0 = time.time()
            out = search(cell, pset, Ta, kern, single, start, fine=fine, log=log)
            out.update({"fine": fine, "start": start, "wall_s": time.time() - t0, "kernel": os.path.basename(kern.path)})
            res[key] = out
            json.dump(res, open(path, "w"), indent=1)
            log(f"  -> {key}: {out['rate']}C (fails at {out.get('fail_above')}C), {len(out['trials'])} trials, "
                f"{out['wall_s']:.0f} s")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["discharge", "charge", "limit"])
    ap.add_argument("--cell", default="21700")
    ap.add_argument("--case")
    ap.add_argument("--set", default="ORegan2022")
    ap.add_argument("--models", default="radial,resolved,corrected")
    ap.add_argument("--heats", default="two-way,one-way")
    ap.add_argument("--T", type=float)
    ap.add_argument("--fine", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--which", default="single,coupled")
    a = ap.parse_args()
    models = tuple(a.models.split(","))
    if a.what == "discharge":
        cases = [a.case] if a.case else [k for k in DISCHARGE_CASES if k.startswith(a.cell)]
        for c in cases:
            discharge(c, a.set, models=models, heats=tuple(a.heats.split(",")), force=a.force)
    elif a.what == "charge":
        charge(a.cell, a.set, models=models, force=a.force)
    else:
        limit(a.cell, a.set, a.T, models=models, fine_resolved=a.fine, which=tuple(a.which.split(",")))
