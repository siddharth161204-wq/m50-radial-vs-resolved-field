#!/usr/bin/env python3
"""Stage 5, a post hoc bracket (D36), not part of the registered procedure and not scored: the registered set,
ORegan2022, at a particle mesh that has settled, against D30's registered mesh (PyBaMM's default, 20 points along
each particle's radius, uniform). Everything else is as registered; the registered modules are used unchanged.

1. The mesh (`mesh`). One DFN held at the ambient temperature, as in D35's check (src/stage5_posthoc_mesh.py, whose
   functions are used here unchanged): the 2C discharge time at 25 C (and at minus 5 C, recorded beside it), the
   smallest margin at the specification's two charge limits, and the plating-limited rate at 0, 10 and 25 C, found
   by bisection to 0.001C from a bracket checked at both ends. The settled mesh is the coarsest uniform mesh N at
   which each of these six readings changes by less than 1 % from N to 2N points.

   python3 src/stage5_posthoc_settled.py mesh --points 160 --what rates_0,rates_10,rates_25,charges,discharges

2. The runs (`runs`). The coupled and single-unit models at the settled mesh with two-way heat, under the three
   kernels: the six discharges of Part C and the charge readings behind P7 to P9 (the specification's two limits in
   both cells, and the four searches of P9 at 0 C under the resolved kernel). Every DFN built in the process gets N
   points along each particle's radius; the runs are written to results/stage5_posthoc_settled/ in the registered
   format, so that the registered runs in results/stage5_runs/ are untouched.

   python3 src/stage5_posthoc_settled.py runs --points N --job discharge:21700_b_m5C_2C:resolved
   python3 src/stage5_posthoc_settled.py runs --points N --job charge:21700:resolved
   python3 src/stage5_posthoc_settled.py runs --points N --job p9:21700        (single-unit then coupled, refined)
"""
import argparse
import fcntl
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

OUT = os.path.join(C.RESULTS, "stage5_posthoc_settled")
MESH_JSON = os.path.join(OUT, "mesh.json")


def merge_save(path, key, value):
    """Add one entry to a JSON file shared by several processes."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        d = json.load(open(path)) if os.path.exists(path) else {}
        node = d
        for k in key[:-1]:
            node = node.setdefault(k, {})
        node[key[-1]] = value
        tmp = path + f".tmp{os.getpid()}"
        json.dump(d, open(tmp, "w"), indent=1)
        os.replace(tmp, path)


def load(path):
    return json.load(open(path)) if os.path.exists(path) else {}


# ---------------------------------------------------------------- 1. the mesh
def rate_bisect(PM, T_C, n, guess, log):
    """The largest rate (specification's C) whose margin stays at or above zero to 4.2 V, one DFN at the ambient, by
    bisection to 0.001C from a bracket around a guess, both ends checked (widened if needed)."""
    sim = PM.sim_for("ORegan2022", T_C, n, ["Voltage [V]"] + PM.MARGIN)
    trials = []

    def ok(r):
        m = PM.charge_margin(sim, r * PM.C_SPEC)["margin_min_V"]
        trials.append({"rate": r, "margin_min_V": m, "passed": m >= 0})
        log(f"      {T_C:g} C, {n} points: {r:.5f}C margin {1e3 * m:+.3f} mV")
        return m >= 0
    lo, hi = 0.85 * guess, 1.25 * guess
    while not ok(lo):
        hi, lo = lo, 0.8 * lo
    while ok(hi):
        lo, hi = hi, 1.25 * hi
    while hi - lo > 0.001:
        mid = 0.5 * (lo + hi)
        if ok(mid):
            lo = mid
        else:
            hi = mid
    return {"rate_spec_C": lo, "fails_at_spec_C": hi, "trials": trials}


def mesh(points, what):
    import stage5_posthoc_mesh as PM
    d35 = load(os.path.join(C.RESULTS, "stage5_posthoc_mesh.json")).get("results", {}).get("ORegan2022", {})
    log = lambda s: print(s, flush=True)
    for n in points:
        have = load(MESH_JSON).get(str(n), {})
        prev = {}                                  # the nearest coarser mesh's rates, for the bracket
        for m in sorted([int(k) for k in load(MESH_JSON)] + [int(k) for k in d35], reverse=True):
            if m < n:
                src = load(MESH_JSON).get(str(m), {}) or {}
                for T in ("0", "10", "25"):
                    r = src.get(f"rate_{T}C") or d35.get(str(m), {}).get("plating_limited_rate_at_ambient", {}).get(T)
                    if r and T not in prev:
                        prev[T] = r["rate_spec_C"]
        for w in what:
            t0 = time.time()
            if w == "discharges":
                for key, T in (("discharge_2C_25C", 25.0), ("discharge_2C_m5C", -5.0)):
                    if key not in have:
                        r = PM.discharge("ORegan2022", T, n)
                        r["wall_s"] = time.time() - t0
                        merge_save(MESH_JSON, [str(n), key], r)
                        log(f"{n} points {key}: {r}")
            elif w == "discharge_m5":
                if "discharge_2C_m5C" not in have:
                    r = PM.discharge("ORegan2022", -5.0, n)
                    r["wall_s"] = time.time() - t0
                    merge_save(MESH_JSON, [str(n), "discharge_2C_m5C"], r)
                    log(f"{n} points discharge_2C_m5C: {r}")
            elif w == "charges":
                for key, T, I in (("charge_1455mA_0C", 0.0, 1.455), ("charge_3395mA_25C", 25.0, 3.395)):
                    if key not in have:
                        r = PM.charge_margin(PM.sim_for("ORegan2022", T, n, ["Voltage [V]"] + PM.MARGIN), I)
                        r["wall_s"] = time.time() - t0
                        merge_save(MESH_JSON, [str(n), key], r)
                        log(f"{n} points {key}: {r}")
            elif w.startswith("rates_"):
                T = w.split("_")[1]
                key = f"rate_{T}C"
                if key not in have:
                    r = rate_bisect(PM, float(T), n, prev.get(T, 0.5), log)
                    r["wall_s"] = time.time() - t0
                    merge_save(MESH_JSON, [str(n), key], r)
                    log(f"{n} points {key}: {r['rate_spec_C']:.5f} to {r['fails_at_spec_C']:.5f}C, {len(r['trials'])} trials")


# ---------------------------------------------------------------- 2. the runs at the settled mesh
def set_particle_points(n):
    """Every DFN built in this process gets n points along each particle's radius (PyBaMM's default is 20)."""
    import pybamm
    import stage5_common as S5
    base = pybamm.lithium_ion.BaseModel.default_var_pts.fget

    def var_pts(self):
        v = dict(base(self))
        v["r_n"] = v["r_p"] = n
        return v
    pybamm.lithium_ion.DFN.default_var_pts = property(var_pts)
    S5.RUNDIR = os.path.join(OUT, f"runs_r{n}")
    os.makedirs(S5.RUNDIR, exist_ok=True)
    # the registered runs' stored trials are not this mesh's; a store of this mesh's own trials may be given
    os.environ.pop("STAGE5_TRIAL_CACHE", None)
    if os.environ.get("D36_TRIAL_CACHE"):
        os.environ["STAGE5_TRIAL_CACHE"] = os.path.join(os.environ["D36_TRIAL_CACHE"], f"r{n}")


def collect_garbage_while_stepping(every=5):
    """At 160 points each step's solution holds large arrays in reference cycles, which Python's collector frees too
    late: memory then grows with the steps past the machine's limit. Collecting every few steps keeps it bounded.
    The computation is unchanged."""
    import gc
    import stage5_coupled as SC
    step = SC.Stepper.step

    def step_and_collect(self, dt, inputs):
        self._steps_since_gc = getattr(self, "_steps_since_gc", 0) + 1
        if self._steps_since_gc >= every:
            gc.collect()
            self._steps_since_gc = 0
        return step(self, dt, inputs)
    SC.Stepper.step = step_and_collect


def runs(n, jobs):
    set_particle_points(n)
    collect_garbage_while_stepping()
    import stage5_runs as RN                              # imported after the mesh is set
    import stage5_queue as Q                              # returns freed memory after every run (no reading changes)
    assert Q is not None
    for job in jobs:
        kind, *rest = job.split(":")
        print(f"=== {time.strftime('%H:%M:%S', time.gmtime())} {n} points {job}", flush=True)
        if kind == "discharge":
            case, lab = rest
            RN.discharge(case, "ORegan2022", models=(lab,), heats=("two-way",))
        elif kind == "charge":
            cell, lab = rest
            RN.charge(cell, "ORegan2022", cases=("0.3C_0C", "0.7C_25C"), models=(lab,))
        elif kind == "p9":
            cell, = rest
            RN.limit(cell, "ORegan2022", 0.0, models=("resolved",), fine_resolved=True, which=("single",))
            RN.limit(cell, "ORegan2022", 0.0, models=("resolved",), fine_resolved=True, which=("coupled",))
        else:
            raise SystemExit(f"unknown job {job}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["mesh", "runs"])
    ap.add_argument("--points", required=True, help="comma-separated points per particle radius")
    ap.add_argument("--what", dest="items", default="discharges,charges,rates_0,rates_10,rates_25")
    ap.add_argument("--job", action="append", default=[])
    a = ap.parse_args()
    pts = [int(x) for x in a.points.split(",")]
    if a.what == "mesh":
        mesh(pts, a.items.split(","))
    else:
        runs(pts[0], a.job)
