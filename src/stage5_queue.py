#!/usr/bin/env python3
"""Runs a list of Stage 5 jobs in order, waiting for each job's kernel files to exist (they are computed by
src/stage5_kernels.py in another process). Used to drive the registered runs; it adds nothing to the procedure.

python3 src/stage5_queue.py <queue name>"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage5_common as S5  # noqa: E402
import stage5_runs as RN  # noqa: E402


def need(cell, ends, grids):
    out = []
    for label, (mdl, bc) in RN.models_for(ends).items():
        for g in grids:
            out.append(S5.kernel_path(mdl, bc, cell, g))
    return out


def wait_for(paths):
    while not all(os.path.exists(p) for p in paths):
        time.sleep(60)


QUEUES = {
    "singles": [("limit_single", cell, pset, T, models)
                for pset in ("ORegan2022", "Chen2020")
                for cell, models in (("21700", ("radial", "resolved", "corrected")), ("4680", ("radial", "resolved", "corrected")))
                for T in (0.0, 25.0, 10.0)],
    "registered_21700": [
        ("discharge", "21700_b_m5C_2C", "ORegan2022"),
        ("charge", "21700", "ORegan2022"),
        ("discharge", "21700_a_m5C_2C", "ORegan2022"),
        ("discharge", "21700_b_p25C_3C", "ORegan2022"),
        ("discharge", "21700_b_p25C_2C", "ORegan2022"),
        ("discharge", "21700_b_p25C_1.25C", "ORegan2022"),
        ("limit", "21700", "ORegan2022", 0.0),
        ("limit", "21700", "ORegan2022", 25.0),
        ("limit", "21700", "ORegan2022", 10.0),
    ],
    "bracket_21700": [
        ("discharge", "21700_b_m5C_2C", "Chen2020"),
        ("charge", "21700", "Chen2020"),
        ("discharge", "21700_a_m5C_2C", "Chen2020"),
        ("discharge", "21700_b_p25C_3C", "Chen2020"),
        ("discharge", "21700_b_p25C_2C", "Chen2020"),
        ("discharge", "21700_b_p25C_1.25C", "Chen2020"),
        ("limit", "21700", "Chen2020", 0.0),
        ("limit", "21700", "Chen2020", 25.0),
        ("limit", "21700", "Chen2020", 10.0),
    ],
    "registered_4680": [
        ("discharge", "4680_b_m5C_2C", "ORegan2022"),
        ("charge", "4680", "ORegan2022"),
        ("limit", "4680", "ORegan2022", 0.0),
        ("limit", "4680", "ORegan2022", 25.0),
        ("limit", "4680", "ORegan2022", 10.0),
    ],
    "bracket_4680": [
        ("discharge", "4680_b_m5C_2C", "Chen2020"),
        ("charge", "4680", "Chen2020"),
        ("limit", "4680", "Chen2020", 0.0),
        ("limit", "4680", "Chen2020", 25.0),
        ("limit", "4680", "Chen2020", 10.0),
    ],
}


def do(job):
    kind = job[0]
    print(f"=== {time.strftime('%H:%M:%S', time.gmtime())} {job}", flush=True)
    if kind == "discharge":
        case, pset = job[1], job[2]
        cell, ends, _, _, g = RN.DISCHARGE_CASES[case]
        wait_for(need(cell, ends, [g]))
        RN.discharge(case, pset)
    elif kind == "charge":
        cell, pset = job[1], job[2]
        wait_for(need(cell, "b", ["charge10"]))
        pot = ("0.3C_0C", "resolved", False) if (cell == "21700" and pset == "ORegan2022") else None
        RN.charge(cell, pset, store_potentials_for=pot)
    elif kind == "limit_single":
        cell, pset, T, models = job[1], job[2], job[3], job[4]
        wait_for(need(cell, "b", ["charge10"]))
        RN.limit(cell, pset, T, models=models, fine_resolved=(T == 0.0 and pset == "ORegan2022"), which=("single",))
    elif kind == "limit":
        cell, pset, T = job[1], job[2], job[3]
        wait_for(need(cell, "b", ["charge10"]))
        RN.limit(cell, pset, T, fine_resolved=(T == 0.0 and pset == "ORegan2022"))


if __name__ == "__main__":
    for job in QUEUES[sys.argv[1]]:
        do(job)
    print(f"=== {time.strftime('%H:%M:%S', time.gmtime())} queue done", flush=True)
