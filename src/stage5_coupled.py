#!/usr/bin/env python3
"""Stage 5, Part B (D30): the multi-unit model. Each group of units is PyBaMM's Doyle-Fuller-Newman model, isothermal
at its own temperature; all groups share one terminal voltage and the area-weighted sum of their currents is the
applied current. The temperatures come from the kernels of Part A (src/stage5_kernels.py) by convolution of the
heat history (two-way heat) or of the registered heat (one-way heat).

The coupled system: G copies of PyBaMM's DFN, every state variable renamed per group, each copy's current a new
algebraic variable I_g with the equation V_g = V, and the common voltage V with the equation sum W_g I_g = I_app.
IDAKLU's Newton iteration solves the voltage and the currents at every internal step (D30).
"""
import json
import math
import os
import sys
import time

import casadi
import numpy as np
import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import stage5_common as S5  # noqa: E402

WINDOW = {"Upper voltage cut-off [V]": 4.2, "Open-circuit voltage at 100% SOC [V]": 4.2,
          "Lower voltage cut-off [V]": 2.5, "Open-circuit voltage at 0% SOC [V]": 2.5}   # D23
RTOL, ATOL = 1e-6, 1e-8                                                                  # D23, D30
OPTIONS = {"calculate heat source for isothermal models": "true"}                        # D30
V_MIN, V_MAX = 2.5, 4.2


def base_values(pset, soc):
    """D23's window; the initial stoichiometries PyBaMM places for this state of charge (at the reference
    temperature) written into the initial concentrations, so that the temperature can be an input (D30)."""
    p = pybamm.ParameterValues(pset)
    p.update(WINDOW)
    x, y = pybamm.lithium_ion.get_initial_stoichiometries(soc, p)
    p.update({"Initial concentration in negative electrode [mol.m-3]": x * p["Maximum concentration in negative electrode [mol.m-3]"],
              "Initial concentration in positive electrode [mol.m-3]": y * p["Maximum concentration in positive electrode [mol.m-3]"]})
    return p, float(x), float(y)


def _renamed(v, tag):
    return pybamm.Variable(f"{v.name} {tag}", domains=v.domains, bounds=v.bounds, scale=v.scale, reference=v.reference)


OUT_NAMES = ["Voltage [V]", "Total heating [W]", "Negative electrode surface potential difference [V]",
             "Negative electrode surface potential difference at separator interface [V]",
             "Negative electrode potential [V]", "Negative electrolyte potential [V]"]


def build_coupled(pset, soc, W):
    """The coupled system for groups with area weights W (summing to 1). Returns (model, outputs) where outputs
    maps names to discretised expressions."""
    G = len(W)
    V = pybamm.Variable("Common voltage [V]")
    I_app = pybamm.InputParameter("I_app")
    comb = pybamm.BaseModel("stage5 coupled")
    Ivars, outs = [], {}
    geometry = submesh = var_pts = spatial = None
    for g in range(G):
        tag = f"g{g + 1}"
        m = pybamm.lithium_ion.DFN(OPTIONS)
        Ig = pybamm.Variable(f"Group current [A] {tag}")
        p, _, _ = base_values(pset, soc)
        Tg = pybamm.InputParameter(f"T{g + 1}")
        p.update({"Current function [A]": Ig, "Ambient temperature [K]": Tg, "Initial temperature [K]": Tg})
        pm = p.process_model(m, inplace=False)
        mapping = {}
        for s in list(pm.rhs.keys()) + list(pm.algebraic.keys()):
            for c in (s.children if isinstance(s, pybamm.ConcatenationVariable) else [s]):
                mapping[c] = _renamed(c, tag)
        cache = {}
        R = lambda e: pybamm.replace(e, mapping, cache)
        for k, e in pm.rhs.items():
            comb.rhs[R(k)] = R(e)
        for k, e in pm.algebraic.items():
            comb.algebraic[R(k)] = R(e)
        for k, e in pm.initial_conditions.items():
            comb.initial_conditions[R(k)] = R(e)
        for k, bc in pm.boundary_conditions.items():
            comb.boundary_conditions[R(k)] = {side: (R(ex), typ) for side, (ex, typ) in bc.items()}
        vg = R(p.process_symbol(m.variables["Voltage [V]"]))
        comb.algebraic[Ig] = vg - V
        comb.initial_conditions[Ig] = I_app
        for name in OUT_NAMES:
            outs[(name, g)] = R(p.process_symbol(m.variables[name]))
        Ivars.append(Ig)
        if g == 0:
            geometry = m.default_geometry
            p.process_geometry(geometry)
            submesh, var_pts, spatial = m.default_submesh_types, m.default_var_pts, m.default_spatial_methods
    comb.algebraic[V] = sum(float(w) * I for w, I in zip(W, Ivars)) - I_app
    comb.initial_conditions[V] = pybamm.Scalar(3.7)
    comb.variables["Common voltage [V]"] = V
    comb.events = [pybamm.Event("Minimum voltage", V - V_MIN), pybamm.Event("Maximum voltage", V_MAX - V)]
    mesh = pybamm.Mesh(geometry, submesh, var_pts)
    disc = pybamm.Discretisation(mesh, spatial)
    disc.process_model(comb)
    douts = {"V": disc.process_symbol(V)}
    for g, Ig in enumerate(Ivars):
        douts[("I", g)] = disc.process_symbol(Ig)
    for (name, g), e in outs.items():
        douts[(name, g)] = disc.process_symbol(e)
    return comb, douts


def build_single(pset, soc):
    """The single-unit model (B3): one plain PyBaMM DFN with the current and the temperature as inputs, built and
    discretised as the copies of the coupled system are."""
    m = pybamm.lithium_ion.DFN(OPTIONS)
    p, _, _ = base_values(pset, soc)
    T1 = pybamm.InputParameter("T1")
    p.update({"Current function [A]": pybamm.InputParameter("I_app"), "Ambient temperature [K]": T1,
              "Initial temperature [K]": T1})
    pm = p.process_model(m, inplace=False)
    pm.events = [e for e in pm.events if e.name in ("Minimum voltage [V]", "Maximum voltage [V]")]
    geometry = m.default_geometry
    p.process_geometry(geometry)
    mesh = pybamm.Mesh(geometry, m.default_submesh_types, m.default_var_pts)
    disc = pybamm.Discretisation(mesh, m.default_spatial_methods)
    disc.process_model(pm)
    douts = {"V": disc.process_symbol(p.process_symbol(m.variables["Voltage [V]"])),
             ("I", 0): pybamm.InputParameter("I_app")}
    for name in OUT_NAMES:
        douts[(name, 0)] = disc.process_symbol(p.process_symbol(m.variables[name]))
    return pm, douts


class Stepper:
    """Steps a built model with IDAKLU (D23's tolerances) and evaluates the outputs at the end of each step."""

    def __init__(self, model, douts, G, input_names):
        self.model, self.G = model, G
        self.inputs = list(input_names)
        self.solver = pybamm.IDAKLUSolver(rtol=RTOL, atol=ATOL)
        n = model.len_rhs_and_alg
        t = casadi.MX.sym("t")
        y = casadi.MX.sym("y", n)
        ps = {k: casadi.MX.sym(k) for k in self.inputs}
        cs = lambda e: e.to_casadi(t, y, inputs=ps)
        self.f_scalar = casadi.Function("fs", [t, y] + [ps[k] for k in self.inputs],
                                        [casadi.vertcat(cs(douts["V"]), *[cs(douts[("I", g)]) for g in range(G)],
                                                        *[cs(douts[("Total heating [W]", g)]) for g in range(G)])])
        self._sym = (t, y, ps, cs, douts)
        self._f_margin = self._f_pot = None       # built when first needed (memory)
        self.sol = None

    @property
    def f_margin(self):
        if self._f_margin is None:
            t, y, ps, cs, douts = self._sym
            G = self.G
            self._f_margin = casadi.Function("fm", [t, y] + [ps[k] for k in self.inputs],
                                             [casadi.vertcat(*[cs(douts[("Negative electrode surface potential difference [V]", g)]) for g in range(G)],
                                                             *[cs(douts[("Negative electrode surface potential difference at separator interface [V]", g)]) for g in range(G)])])
        return self._f_margin

    @property
    def f_pot(self):
        if self._f_pot is None:
            t, y, ps, cs, douts = self._sym
            G = self.G
            self._f_pot = casadi.Function("fp", [t, y] + [ps[k] for k in self.inputs],
                                          [casadi.vertcat(*[cs(douts[("Negative electrode potential [V]", g)]) for g in range(G)],
                                                          *[cs(douts[("Negative electrolyte potential [V]", g)]) for g in range(G)])])
        return self._f_pot

    def step(self, dt, inputs):
        self.sol = self.solver.step(self.sol, self.model, dt, inputs=inputs, save=False)
        return self.sol

    def state(self):
        return float(self.sol.t[-1]), np.asarray(self.sol.y)[:, -1]

    def evaluate_at(self, i, inputs, margin=False, potentials=False):
        return self.evaluate(inputs, margin, potentials, ty=(float(self.sol.t[i]), np.asarray(self.sol.y)[:, i]))

    def evaluate(self, inputs, margin=False, potentials=False, ty=None):
        t, y = self.state() if ty is None else ty
        args = [t, y] + [inputs[k] for k in self.inputs]
        v = np.asarray(self.f_scalar(*args)).ravel()
        G = self.G
        out = {"t": t, "V": v[0], "I": v[1:1 + G], "Q": v[1 + G:1 + 2 * G]}
        if margin:
            mv = np.asarray(self.f_margin(*args)).ravel()
            nodes = mv[:-G].reshape(G, -1)
            out["margin_nodes_min"] = nodes.min(axis=1)
            out["margin_nodes_argmin"] = nodes.argmin(axis=1)
            out["margin_interface"] = mv[-G:]
        if potentials:
            pv = np.asarray(self.f_pot(*args)).ravel()
            half = len(pv) // 2
            out["phi_s_n"] = pv[:half].reshape(G, -1)
            out["phi_e_n"] = pv[half:].reshape(G, -1)
        return out


def make(pset, soc, W, single=False):
    """A built model with its stepper, reusable across runs with the same set, initial state and weights."""
    model, douts = build_single(pset, soc) if single else build_coupled(pset, soc, W)
    Gm = 1 if single else len(W)
    names = ["I_app"] + [f"T{g + 1}" for g in range(Gm)]
    return {"model": model, "douts": douts, "stepper": Stepper(model, douts, Gm, names), "set": pset, "soc": soc,
            "W": np.asarray(W, dtype=float), "single": single}


# ----------------------------------------------------------------------------------------------------------------
# the stepwise solve (D30): temperatures held over each step at the step's start, heat at its end
# ----------------------------------------------------------------------------------------------------------------
def run(kind, cell, pset, T_amb_C, I_app, kern, heat="two-way", single=False, G=None, oneway_T=None,
        fixed_T=None, max_steps=200000, store_potentials=False, stop_on_negative_margin=False, verbose=False,
        built=None, label=""):
    """kind: 'discharge' (from 100 %) or 'charge' (from 0 %). I_app in A of the 5 A h model, positive on discharge.
    kern: a stage5_common.Kernel on the run's grid (its dt is the step). heat: 'two-way', 'one-way' (oneway_T: the
    (n_archive + 1) x G group temperatures in C from step 0, held past the end) or 'fixed' (fixed_T: a function of the
    step index returning the G temperatures, for V2). single: the single-unit model at the area-weighted mean.
    Returns a dict of per-step arrays and run metadata."""
    t_wall = time.time()
    soc = 1.0 if kind == "discharge" else 0.0
    N = kern.N
    G = kern.G
    W = S5.group_weights(N, G) if not single else np.array([1.0])
    Gm = 1 if single else G
    if built is None:
        built = make(pset, soc, W, single)
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
                   "wall_s": time.time() - t_wall, "label": label}
    return out


def save_run(out, name):
    os.makedirs(S5.RUNDIR, exist_ok=True)
    arrs = {}
    for k, v in out.items():
        if k == "meta":
            continue
        if k in ("t",):
            arrs[k] = v.astype(np.float64)
        elif k in ("V", "I", "resid"):
            arrs[k] = v.astype(np.float64)
        elif k == "margin_nodes_argmin":
            arrs[k] = v.astype(np.int16)
        else:
            arrs[k] = v.astype(np.float32)
    path = os.path.join(S5.RUNDIR, name + ".npz")
    tmp = path + f".tmp{os.getpid()}"
    with open(tmp, "wb") as f:                        # written whole, then renamed, so a stopped job leaves no part file
        np.savez_compressed(f, meta=json.dumps(out["meta"]), **arrs)
    os.replace(tmp, path)


def load_run(name):
    z = np.load(os.path.join(S5.RUNDIR, name + ".npz"), allow_pickle=False)
    out = {k: z[k] for k in z.files if k != "meta"}
    out["meta"] = json.loads(str(z["meta"]))
    return out
