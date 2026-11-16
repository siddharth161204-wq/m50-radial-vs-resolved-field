#!/usr/bin/env python3
"""Stage 5, V5 (D33): the coupled solve by a second route, in the main case (two-way heat, resolved kernel,
ORegan2022).

G separate PyBaMM DFNs in voltage mode. Over each step the voltage is linear in time from the step's start value
V_k to its end value V_k+1, and V_k+1 is found by a secant search so that the area-weighted sum of the group
currents at the step's end equals the applied current, to 1e-8 of it. For every trial voltage each group model is
stepped from its state at the step's start. The temperature and heat rules are those of the stepwise route
(src/stage5_coupled.py): each group's temperature held over the step at its value at the start, the heat at the
end entering the convolution. The shares are compared with the stepwise route's run at every common step.

python3 src/stage5_v5.py      -> results/stage5_v5.json, results/stage5_runs/V5_route2.npz"""
import json
import os
import sys
import time

import numpy as np
import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import stage5_common as S5  # noqa: E402
import stage5_coupled as SC  # noqa: E402
import stage5_runs as RN  # noqa: E402

TOL = 1e-8


def build_voltage_model(pset):
    m = pybamm.lithium_ion.DFN({**SC.OPTIONS, "operating mode": "voltage"})
    p, _, _ = SC.base_values(pset, 1.0)
    T = pybamm.InputParameter("T")
    V0, V1, t0, dts = (pybamm.InputParameter(n) for n in ("V0", "V1", "t0", "dts"))
    p.update({"Ambient temperature [K]": T, "Initial temperature [K]": T,
              "Voltage function [V]": lambda t: V0 + (V1 - V0) * (t - t0) / dts, "Current function [A]": 10.0},
             check_already_exists=False)
    sim = pybamm.Simulation(m, parameter_values=p)
    sim.build()
    bm = sim.built_model
    bm.events = []
    return bm, sim


def main():
    case, pset, label = "21700_b_m5C_2C", "ORegan2022", "resolved"
    cell, ends, Ta, I_app, gridname = RN.DISCHARGE_CASES[case]
    mdl, bc = RN.models_for(ends)[label]
    kern = S5.Kernel(S5.kernel_path(mdl, bc, cell, gridname))
    ref = SC.load_run(RN.run_name("C", case, label, pset, "two-way", False, kern.G))
    G, W, dt = kern.G, kern.W, kern.dt
    model, sim = build_voltage_model(pset)
    solver = pybamm.IDAKLUSolver(rtol=SC.RTOL, atol=SC.ATOL)
    names = ["Current [A]", "Total heating [W]"]
    get = lambda sol, n: float(np.asarray(sol[n].entries).ravel()[-1])
    conv = kern.group_convolver()
    T_now = np.full(G, Ta)
    V_prev = float(ref["V"][0])                  # V at t = 0: every group identical, the stepwise route's value
    sols = [None] * G
    t0 = time.time()
    rec_t, rec_V, rec_I, rec_res, n_iter = [0.0], [V_prev], [np.full(G, I_app)], [0.0], []
    V_hist = [V_prev, V_prev]
    k = 0
    while True:
        tk = k * dt

        def F(V1):
            out, cur = [], []
            for g in range(G):
                inp = {"T": float(T_now[g]) + 273.15, "V0": V_prev, "V1": V1, "t0": tk, "dts": dt}
                s = solver.step(sols[g], model, dt, inputs=inp, save=False)
                out.append(s)
                cur.append(get(s, "Current [A]"))
            cur = np.array(cur)
            return float(W @ cur) - I_app, out, cur

        # secant search from the extrapolated voltage
        Va = V_prev + (V_hist[-1] - V_hist[-2]) if k > 0 else V_prev - 0.01
        Vb = Va - 1e-3
        fa, sa, ca = F(Va)
        fb, sb, cb = F(Vb)
        it = 2
        while abs(fb) > TOL * abs(I_app) and it < 30:
            Vc = Vb - fb * (Vb - Va) / (fb - fa)
            Va, fa, sa, ca = Vb, fb, sb, cb
            Vb = Vc
            fb, sb, cb = F(Vb)
            it += 1
        n_iter.append(it)
        if Vb < SC.V_MIN:
            break
        k += 1
        sols = sb
        q = np.array([get(s, "Total heating [W]") for s in sols]) / S5.V21700
        rec_t.append(k * dt)
        rec_V.append(Vb)
        rec_I.append(cb)
        rec_res.append(abs(fb) / abs(I_app))
        V_hist.append(Vb)
        V_prev = Vb
        T_now = Ta + conv.push(q)
        if k % 20 == 0:
            print(f"  step {k} t {k * dt:.0f} s V {Vb:.4f} iterations {it} ({time.time() - t0:.0f} s)", flush=True)
    t = np.array(rec_t)
    I = np.array(rec_I)
    s2 = I / I_app
    # the stepwise route at the same step indices (both routes record step k at t = k dt)
    n = min(len(t), len(ref["t"]) - 1)        # the stepwise route's last record may be the partial cut-off step
    s1 = ref["I"][:n] / I_app
    rel = np.abs(s2[:n] / s1 - 1)
    res = {"case": case, "set": pset, "kernel": label, "G": G, "steps_compared": int(n), "dt": dt,
           "max_rel_share_difference": float(rel.max()),
           "step_of_max": int(np.argmax(rel.max(axis=1))), "group_of_max": int(np.argmax(rel.max(axis=0))) + 1,
           "max_abs_voltage_difference_V": float(np.abs(np.array(rec_V)[:n] - ref["V"][:n]).max()),
           "max_current_balance_residual": float(max(rec_res)), "secant_iterations_max": int(max(n_iter)),
           "secant_iterations_mean": float(np.mean(n_iter)), "route2_last_full_step_t_s": float(t[-1]),
           "route1_cutoff_t_s": float(ref["t"][-1]), "within_0.5_percent": bool(rel.max() < 0.005),
           "wall_s": time.time() - t0}
    json.dump(res, open(os.path.join(C.RESULTS, "stage5_v5.json"), "w"), indent=1)
    np.savez_compressed(os.path.join(S5.RUNDIR, "V5_route2.npz"), t=t, V=np.array(rec_V), I=I,
                        resid=np.array(rec_res))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
