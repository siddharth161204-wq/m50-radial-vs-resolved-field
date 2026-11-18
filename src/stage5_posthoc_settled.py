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
   python3 src/stage5_posthoc_settled.py runs --points N --job charge:21700:resolved        (both limits)
   python3 src/stage5_posthoc_settled.py runs --points N --job charge:21700:resolved:0.3C_0C (one of them)
   python3 src/stage5_posthoc_settled.py runs --points N --job p9:21700        (single-unit then coupled, refined)

3. The readings (`report`), by the registered report's functions, each beside its registered value at 20 points;
   nothing is scored and nothing registered is replaced.

   python3 src/stage5_posthoc_settled.py report --points N
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


READINGS = {"discharge_2C_25C": ("discharge_2C_25C", "t_cut_s"), "charge_1455mA_0C": ("charge_1455mA_0C", "margin_min_V"),
            "charge_3395mA_25C": ("charge_3395mA_25C", "margin_min_V"), "rate_0C": ("rate_0C", "rate_spec_C"),
            "rate_10C": ("rate_10C", "rate_spec_C"), "rate_25C": ("rate_25C", "rate_spec_C")}
BESIDE = {"discharge_2C_m5C": ("discharge_2C_m5C", "t_cut_s")}


def mesh_summary():
    """The six readings (and the 2C discharge at minus 5 C beside them) against the points per particle radius, from
    D35's check (20 to 320 points) and this one, the change of each from N to 2N points, and the coarsest N at which
    each changes by less than 1 % on doubling. -> results/stage5_posthoc_settled/mesh_summary.json"""
    d35 = load(os.path.join(C.RESULTS, "stage5_posthoc_mesh.json")).get("results", {}).get("ORegan2022", {})
    d36 = load(MESH_JSON)
    table, agree = {}, []
    for name, (key, field) in {**READINGS, **BESIDE}.items():
        vals = {}
        for n, e in d35.items():
            if key.startswith("rate_"):
                v = e.get("plating_limited_rate_at_ambient", {}).get(key[5:-1])
                v = v.get("rate_spec_C") if isinstance(v, dict) else v
            else:
                v = e.get(key, {}).get(field)
            if v is not None:
                vals[int(n)] = (float(v), "D35")
        for n, e in d36.items():
            v = e.get(key, {}).get(field)
            if v is not None:
                if int(n) in vals:
                    agree.append({"reading": name, "points": int(n), "D35": vals[int(n)][0], "D36": float(v)})
                vals[int(n)] = (float(v), "D36")
        pts = sorted(vals)
        changes = {n: vals[2 * n][0] / vals[n][0] - 1 for n in pts if 2 * n in vals}
        settled = [n for n in sorted(changes) if abs(changes[n]) < 0.01]
        table[name] = {"values": {str(n): vals[n][0] for n in pts}, "source": {str(n): vals[n][1] for n in pts},
                       "change_on_doubling": {f"{n} to {2 * n}": changes[n] for n in sorted(changes)},
                       "coarsest_settled_points": settled[0] if settled else None,
                       "every_later_doubling_below_1_percent": bool(settled) and all(
                           abs(changes[n]) < 0.01 for n in changes if n >= settled[0])}
    six = [table[k]["coarsest_settled_points"] for k in READINGS]
    out = {"what": ("Post hoc (D36): one DFN held at the ambient (ORegan2022, D23's window), as in D35, against the "
                    "points per particle radius (uniform, both particles). Readings: the 2C discharge's cut-off time at "
                    "25 C; the smallest margin at the specification's two charge limits (1.455 A at 0 C, 3.395 A at 25 C); "
                    "the plating-limited rate at 0, 10 and 25 C (the largest rate whose margin stays at or above zero to "
                    "4.2 V, by bisection to 0.001C). Recorded beside them: the 2C discharge at minus 5 C. The settled mesh "
                    "is the coarsest N at which a reading changes by less than 1 % from N to 2N points."),
           "readings": table, "settled_mesh_for_all_six": None if None in six else max(six),
           "same_point_count_in_both_checks": agree}
    with open(os.path.join(OUT, "mesh_summary.json"), "w") as f:
        json.dump(out, f, indent=1)
    return out


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
    os.environ["D36_POINTS"] = str(n)                     # part of a checkpoint's name (resumable_run)
    S5.RUNDIR = os.path.join(OUT, f"runs_r{n}")
    os.makedirs(S5.RUNDIR, exist_ok=True)
    # the registered runs' stored trials are not this mesh's; a store of this mesh's own trials may be given
    os.environ.pop("STAGE5_TRIAL_CACHE", None)
    if os.environ.get("D36_TRIAL_CACHE"):
        os.environ["STAGE5_TRIAL_CACHE"] = os.path.join(os.environ["D36_TRIAL_CACHE"], f"r{n}")


def collect_garbage_while_stepping(every=1):
    """At 160 points each step's solution holds large arrays (the solver's internal steps) in reference cycles, which
    Python's collector frees too late: memory then grows with the steps past the machine's limit. Collecting after
    every step keeps no more than two steps' solutions in memory. (Every five steps, as first tried, kept one run
    within the limit but not two side by side.) The computation is unchanged."""
    import gc
    import stage5_coupled as SC
    step = SC.Stepper.step

    beat = os.environ.get("D36_HEARTBEAT")

    def step_and_collect(self, dt, inputs):
        self._steps_since_gc = getattr(self, "_steps_since_gc", 0) + 1
        if self._steps_since_gc >= every:
            gc.collect()
            self._steps_since_gc = 0
        out = step(self, dt, inputs)
        if beat:                                          # a step has ended (read by the slots' guard)
            with open(beat, "a"):
                os.utime(beat)
        return out
    SC.Stepper.step = step_and_collect


def keep_first_last_states():
    """The solver keeps only the first and last states of each thermal step, not every internal step of it (PyBaMM's
    store_first_last). The run reads only the last state of each step, and a step's states are the same either way
    (checked on a stored registered run, and on 40 steps at 160 points, D36); a step that needs very many internal
    steps then no longer fills the memory with them."""
    import pybamm
    import stage5_coupled as SC
    init = SC.Stepper.__init__

    def init_first_last(self, *a, **k):
        init(self, *a, **k)
        self.solver = pybamm.IDAKLUSolver(rtol=SC.RTOL, atol=SC.ATOL, store_first_last=True)
    SC.Stepper.__init__ = init_first_last


def resumable_run(kind, cell, pset, T_amb_C, I_app, kern, heat="two-way", single=False, G=None, oneway_T=None,
                  fixed_T=None, max_steps=200000, store_potentials=False, stop_on_negative_margin=False, verbose=False,
                  built=None, label="", every=20):
    """src/stage5_coupled.py's run, line for line, with its state saved every `every` steps to a checkpoint
    (directory D36_CHECKPOINTS) and resumed from it when the same run is started again. At 160 points a run can
    outlast the machine's two-hour limit on a job. The state carried from one thermal step to the next is the
    solver's last time and state vector, the convolution's heat history and the records, so a resumed run takes
    the same steps as one that was never stopped (checked against a stored registered run, D36)."""
    import hashlib
    import numpy as np
    import pybamm
    import stage5_common as S5
    import stage5_coupled as SC
    t_wall = time.time()
    soc = 1.0 if kind == "discharge" else 0.0
    N = kern.N
    G = kern.G
    W = S5.group_weights(N, G) if not single else np.array([1.0])
    Gm = 1 if single else G
    if built is None:
        built = SC.make(pset, soc, W, single)
    st = built["stepper"]
    st.sol = None
    names = st.inputs
    dt = kern.dt
    Ta = T_amb_C
    if heat == "two-way":
        conv = kern.ave_convolver() if single else kern.group_convolver()
    T_now = np.full(Gm, Ta)
    rec = {k: [] for k in ("t", "V", "I", "T", "q", "resid", "mn_min", "mn_arg", "mi")}
    pots = {"phi_s_n": [], "phi_e_n": []}
    held_steps = 0
    margin = kind == "charge"
    k = 0
    status = "max_steps"
    W_arr = np.asarray(W, dtype=float)

    def inputs_now(T):
        return {"I_app": I_app, **{f"T{g + 1}": float(T[g]) + 273.15 for g in range(Gm)}}

    def record(o, T_held):
        rec["t"].append(o["t"])
        rec["V"].append(o["V"])
        rec["I"].append(o["I"])
        rec["T"].append(np.asarray(T_held, dtype=float).copy())
        rec["q"].append(o["Q"] / S5.V21700)
        rec["resid"].append(abs(float(W_arr @ o["I"]) - I_app) / abs(I_app))
        if margin:
            rec["mn_min"].append(o["margin_nodes_min"])
            rec["mn_arg"].append(o["margin_nodes_argmin"])
            rec["mi"].append(o["margin_interface"])
        if store_potentials:
            pots["phi_s_n"].append(o["phi_s_n"])
            pots["phi_e_n"].append(o["phi_e_n"])

    # the checkpoint: one file per run, named by everything that defines the run
    ident = json.dumps([kind, cell, pset, repr(float(T_amb_C)), repr(float(I_app)), os.path.basename(kern.path), heat,
                        bool(single), G, max_steps, bool(store_potentials), bool(stop_on_negative_margin), label,
                        None if oneway_T is None else hashlib.sha1(np.ascontiguousarray(oneway_T)).hexdigest(),
                        os.environ.get("D36_POINTS")])
    ck_dir = os.environ.get("D36_CHECKPOINTS")
    ck = None
    if ck_dir and heat in ("two-way", "one-way"):
        os.makedirs(ck_dir, exist_ok=True)
        ck = os.path.join(ck_dir, (label or f"{kind}_{cell}_{pset}_{T_amb_C:g}C_{abs(I_app):.6f}A_{'single' if single else 'coupled'}")
                          + "_" + hashlib.sha1(ident.encode()).hexdigest()[:12] + ".npz")
    wall_before, resumed_at = 0.0, []
    if ck and os.path.exists(ck):
        z = np.load(ck, allow_pickle=False)
        assert str(z["ident"]) == ident
        k = int(z["k"])
        held_steps = int(z["held_steps"])
        T_now = z["T_now"].astype(np.float64)
        for key in rec:
            if f"rec_{key}" in z.files:
                arr = z[f"rec_{key}"]
                rec[key] = [float(x) for x in arr] if arr.ndim == 1 else [row.copy() for row in arr]
        for key in pots:
            if f"pots_{key}" in z.files:
                pots[key] = [row.copy() for row in z[f"pots_{key}"]]
        if heat == "two-way":
            conv.k = int(z["conv_k"])
            conv.q[:conv.k + 1] = z["conv_q"]
        inp_last = inputs_now(z["T_last"].astype(np.float64))
        st.sol = pybamm.Solution(np.array([float(z["sol_t"])]), z["sol_y"].astype(np.float64).reshape(-1, 1), st.model,
                                 inp_last)
        wall_before = float(z["wall_s"])
        resumed_at = [int(x) for x in z["resumed_at"]] + [k]
        print(f"   {label or os.path.basename(ck)}: resumed at step {k}", flush=True)

    def save_checkpoint():
        arrs = {"ident": np.array(ident), "k": np.array(k), "held_steps": np.array(held_steps),
                "T_now": np.asarray(T_now, dtype=np.float64), "T_last": np.asarray(rec["T"][-1], dtype=np.float64),
                "sol_t": np.array(float(st.sol.t[-1])), "sol_y": np.asarray(st.sol.y)[:, -1].astype(np.float64),
                "wall_s": np.array(wall_before + time.time() - t_wall), "resumed_at": np.array(resumed_at, dtype=np.int64)}
        for key, v in rec.items():
            if v:
                arrs[f"rec_{key}"] = np.array(v)
        for key, v in pots.items():
            if v:
                arrs[f"pots_{key}"] = np.array(v)
        if heat == "two-way":
            arrs["conv_k"] = np.array(conv.k)
            arrs["conv_q"] = conv.q[:conv.k + 1]
        tmp = ck + f".tmp{os.getpid()}"
        with open(tmp, "wb") as f:
            np.savez(f, **arrs)
        os.replace(tmp, ck)

    n_arch = None if oneway_T is None else oneway_T.shape[0] - 1
    while k < max_steps:
        inp = inputs_now(T_now)
        sol = st.step(dt, inp)
        if k == 0:
            record(st.evaluate_at(0, inp, margin=margin, potentials=store_potentials), T_now)
        k += 1
        o = st.evaluate(inp, margin=margin, potentials=store_potentials)
        record(o, T_now)                        # the temperature held over the step that ends here
        if sol.termination != "final time":
            status = sol.termination
            break
        if margin and stop_on_negative_margin and min(o["margin_nodes_min"].min(), o["margin_interface"].min()) < 0.0:
            status = "negative margin"
            break
        # the temperature for the next step
        q = o["Q"] / S5.V21700
        if heat == "two-way":
            T_now = Ta + conv.push(q)
        elif heat == "one-way":
            if k > n_arch:
                held_steps += 1
            T_now = np.asarray(oneway_T[min(k, n_arch)], dtype=float)
        elif heat == "fixed":
            T_now = np.asarray(fixed_T(k), dtype=float)
        if verbose and k % 200 == 0:
            print(f"   {label} step {k} t {o['t']:.0f} s V {o['V']:.4f}", flush=True)
        if ck and k % every == 0:
            save_checkpoint()
    out = {"t": np.array(rec["t"]), "V": np.array(rec["V"]), "I": np.array(rec["I"]), "T": np.array(rec["T"]),
           "q": np.array(rec["q"]), "resid": np.array(rec["resid"])}
    if margin:
        out.update({"margin_nodes_min": np.array(rec["mn_min"]), "margin_nodes_argmin": np.array(rec["mn_arg"]),
                    "margin_interface": np.array(rec["mi"])})
    if store_potentials:
        out.update({k: np.array(v) for k, v in pots.items()})
    out["meta"] = {"kind": kind, "cell": cell, "set": pset, "T_amb_C": Ta, "I_app_A": I_app, "heat": heat,
                   "single": single, "G": Gm, "N": N, "W": list(map(float, W)), "dt": dt, "kernel": os.path.basename(kern.path),
                   "status": status, "n_steps": k, "t_end": float(out["t"][-1]), "held_steps_past_archive": held_steps,
                   "wall_s": wall_before + time.time() - t_wall, "label": label}
    if resumed_at:
        out["meta"]["resumed_at_steps"] = resumed_at
    if ck and os.path.exists(ck):
        os.remove(ck)
    return out


def use_resumable_runs():
    import stage5_coupled as SC
    SC.run = resumable_run


def runs(n, jobs):
    set_particle_points(n)
    collect_garbage_while_stepping()
    keep_first_last_states()
    use_resumable_runs()                                  # before stage5_queue wraps the run
    if os.environ.get("D36_HEARTBEAT"):
        with open(os.environ["D36_HEARTBEAT"], "a"):
            os.utime(os.environ["D36_HEARTBEAT"])
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
            cell, lab, *case = rest                       # one case, or both of the specification's limits
            RN.charge(cell, "ORegan2022", cases=tuple(case) or ("0.3C_0C", "0.7C_25C"), models=(lab,))
        elif kind == "p9":
            cell, = rest
            RN.limit(cell, "ORegan2022", 0.0, models=("resolved",), fine_resolved=True, which=("single",))
            RN.limit(cell, "ORegan2022", 0.0, models=("resolved",), fine_resolved=True, which=("coupled",))
        else:
            raise SystemExit(f"unknown job {job}")


# ---------------------------------------------------------------- 3. the readings, beside the registered ones
def report(n, rundir=None, outdir=OUT):
    """The readings of the runs at n points, by the registered report's own functions (src/stage5_report.py), each
    beside its registered value at 20 points (results/stage5_*.csv). Post hoc: nothing is scored and nothing in
    the registered results is replaced. -> results/stage5_posthoc_settled/readings_r<n>.json and .csv"""
    import csv
    import stage5_common as S5
    S5.RUNDIR = rundir or os.path.join(OUT, f"runs_r{n}")
    import stage5_report as REP
    rows_d, rows_s = REP.discharge_tables()
    rows_c = REP.charge_tables()
    rows_l = REP.limit_table()
    reg = lambda f: [r for r in csv.DictReader(open(os.path.join(C.RESULTS, f))) if r["set"] == "ORegan2022"]
    reg_d = {(r["case"], r["kernel"]): r for r in reg("stage5_discharge.csv") if r["heat"] == "two-way"}
    reg_s = {(r["case"], r["kernel"]): r for r in reg("stage5_shares.csv") if r["heat"] == "two-way"}
    reg_c = {(r["cell"], r["case"], r["kernel"], r["model"]): r for r in reg("stage5_charge.csv")}
    reg_l = {(r["cell"], float(r["T_amb_C"]), r["kernel"], r["model"]): r for r in reg("stage5_limit.csv")}
    num = lambda v: None if v in (None, "") else float(v)
    out = {"what": (f"Post hoc (D36), not scored: ORegan2022, the coupled and single-unit models with two-way heat, "
                    f"{n} points along each particle's radius (uniform, both particles), beside the registered "
                    f"readings at PyBaMM's default 20 points (results/stage5_discharge.csv, stage5_shares.csv, "
                    f"stage5_charge.csv, stage5_limit.csv). Penalty = single-unit energy (capacity) to 2.5 V over the "
                    f"coupled model's, less one. Spread = time average of the largest minus the smallest group share; "
                    f"its error = the kernel's spread over the resolved kernel's, less one. Margin = minimum of the "
                    f"negative electrode's surface potential difference over the charge, the electrode and the groups."),
           "points": n, "discharge": {}, "charge": {}, "limit": {}}
    rows_csv = []
    for d in rows_d:
        if d["set"] != "ORegan2022" or d["heat"] != "two-way":
            continue
        key = (d["case"], d["kernel"])
        sh = next(s for s in rows_s if s["set"] == "ORegan2022" and s["heat"] == "two-way"
                  and (s["case"], s["kernel"]) == key)
        rd, rs = reg_d[key], reg_s[key]
        e = {"penalty_energy": [num(rd["penalty_energy"]), d["penalty_energy"]],
             "penalty_capacity": [num(rd["penalty_capacity"]), d["penalty_capacity"]],
             "t_cut_coupled_s": [num(rd["t_cut_coupled_s"]), d["t_cut_coupled_s"]],
             "t_cut_single_s": [num(rd["t_cut_single_s"]), d["t_cut_single_s"]],
             "Q_coupled_Ah": [num(rd["Q_coupled_Ah"]), d["Q_coupled_Ah"]],
             "E_coupled_Wh": [num(rd["E_coupled_Wh"]), d["E_coupled_Wh"]],
             "spread_tavg": [num(rs["spread_tavg"]), sh["spread_tavg"]],
             "spread_rel_error": [num(rs.get("spread_rel_error")), sh.get("spread_rel_error")],
             "inner_tavg": [num(rs["inner_tavg"]), sh["inner_tavg"]],
             "reversal_s": [num(rs["reversal_s"]), sh["reversal_s"]],
             "max_current_balance_residual": [num(rs["max_current_balance_residual"]), sh["max_current_balance_residual"]]}
        out["discharge"][f"{d['case']}|{d['kernel']}"] = e
        for q, (a, b) in e.items():
            rows_csv.append({"part": "discharge", "case": d["case"], "kernel": d["kernel"], "model": "", "reading": q,
                             "registered_20_points": a, f"post_hoc_{n}_points": b})
    for r in rows_c:
        if r["set"] != "ORegan2022":
            continue
        rr = reg_c[(r["cell"], r["case"], r["kernel"], r["model"])]
        e = {"margin_V": [num(rr["margin_V"]), r["margin_V"]], "group": [int(rr["group"]), r["group"]],
             "t_min_s": [num(rr["t_min_s"]), r["t_min_s"]], "t_end_s": [num(rr["t_end_s"]), r["t_end_s"]],
             "charge_Ah": [num(rr["charge_Ah"]), r["charge_Ah"]],
             "max_current_balance_residual": [num(rr["max_current_balance_residual"]), r["max_current_balance_residual"]]}
        out["charge"][f"{r['cell']}|{r['case']}|{r['kernel']}|{r['model']}"] = e
        for q, (a, b) in e.items():
            rows_csv.append({"part": "charge", "case": f"{r['cell']}_{r['case']}", "kernel": r["kernel"],
                             "model": r["model"], "reading": q, "registered_20_points": a, f"post_hoc_{n}_points": b})
    for r in rows_l:
        if r["set"] != "ORegan2022":
            continue
        rr = reg_l[(r["cell"], r["T_amb_C"], r["kernel"], r["model"])]
        e = {"rate_spec_C": [num(rr["fine_rate_spec_C"]) or num(rr["rate_spec_C"]), r["fine_rate_spec_C"] or r["rate_spec_C"]],
             "fails_at_spec_C": [num(rr["fine_fails_at_spec_C"]) or num(rr["fails_at_spec_C"]),
                                 r["fine_fails_at_spec_C"] or r["fails_at_spec_C"]],
             "n_trials": [int(rr["n_trials"]), r["n_trials"]]}
        out["limit"][f"{r['cell']}|{r['T_amb_C']:g}C|{r['kernel']}|{r['model']}"] = e
        for q, (a, b) in e.items():
            rows_csv.append({"part": "limit", "case": f"{r['cell']}_{r['T_amb_C']:g}C", "kernel": r["kernel"],
                             "model": r["model"], "reading": q, "registered_20_points": a, f"post_hoc_{n}_points": b})
    # the readings behind P7 to P9, as the registered scorecard reads them (src/stage5_report.py), without verdicts
    ch = out["charge"]
    p7 = {c: [1e3 * (ch[f"21700|{c}|radial|coupled"][k][i] - ch[f"21700|{c}|resolved|coupled"][k][i])
              for k, i in (("margin_V", 0), ("margin_V", 1))]
          for c in ("0.3C_0C", "0.7C_25C") if f"21700|{c}|radial|coupled" in ch and f"21700|{c}|resolved|coupled" in ch}
    p8 = {k.rsplit("|", 1)[0]: v["group"] for k, v in ch.items()
          if k.endswith("|coupled") and k.split("|")[1] in ("0.3C_0C", "0.7C_25C")}
    p9 = {}
    for cell in ("21700", "4680"):
        s_, c_ = out["limit"].get(f"{cell}|0C|resolved|single"), out["limit"].get(f"{cell}|0C|resolved|coupled")
        if s_ and c_ and c_["rate_spec_C"][1]:
            p9[cell] = {"single": s_["rate_spec_C"], "coupled": c_["rate_spec_C"],
                        "e": [s_["rate_spec_C"][i] / c_["rate_spec_C"][i] - 1 for i in (0, 1)]}
    out["readings_behind_P7_to_P9"] = {
        "note": "Each pair is [registered at 20 points, post hoc]. Not scored: the registered verdicts stand.",
        "P7_radial_minus_resolved_margin_mV_M50_coupled": p7, "P8_group_holding_the_minimum_coupled": p8,
        "P9_plating_limited_rate_0C_resolved_single_over_coupled_minus_1": p9}
    with open(os.path.join(outdir, f"readings_r{n}.json"), "w") as f:
        json.dump(out, f, indent=1)
    keys = ["part", "case", "kernel", "model", "reading", "registered_20_points", f"post_hoc_{n}_points"]
    with open(os.path.join(outdir, f"readings_r{n}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows_csv:
            w.writerow({k: (f"{v:.9g}" if isinstance(v, float) else ("" if v is None else v)) for k, v in r.items()})
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["mesh", "runs", "report"])
    ap.add_argument("--points", required=True, help="comma-separated points per particle radius")
    ap.add_argument("--what", dest="items", default="discharges,charges,rates_0,rates_10,rates_25")
    ap.add_argument("--job", action="append", default=[])
    a = ap.parse_args()
    pts = [int(x) for x in a.points.split(",")]
    if a.what == "mesh":
        mesh(pts, a.items.split(","))
    elif a.what == "runs":
        runs(pts[0], a.job)
    else:
        report(pts[0])
