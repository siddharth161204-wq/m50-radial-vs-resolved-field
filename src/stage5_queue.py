#!/usr/bin/env python3
"""Runs a list of Stage 5 jobs in order, waiting for each job's kernel files to exist (they are computed by
src/stage5_kernels.py in another process). Used to drive the registered runs; it adds nothing to the procedure.

python3 src/stage5_queue.py <queue name> [--claims DIR] [--reverse]
With --claims, several processes can work through the same jobs: each job is claimed before it is run."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage5_common as S5  # noqa: E402
import stage5_runs as RN  # noqa: E402


def need(cell, ends, grids, G=S5.G_REG):
    out = []
    for label, (mdl, bc) in RN.models_for(ends).items():
        for g in grids:
            out.append(S5.kernel_path(mdl, bc, cell, g, G))
    return out


def wait_for(paths):
    while not all(os.path.exists(p) for p in paths):
        time.sleep(60)


QUEUES = {
    "coupled_limits_21700_ORegan2022": [("limit_coupled", "21700", "ORegan2022", T) for T in (0.0, 25.0, 10.0)],
    "coupled_limits_4680_ORegan2022": [("limit_coupled", "4680", "ORegan2022", T) for T in (0.0, 25.0, 10.0)],
    "coupled_limits_21700_Chen2020": [("limit_coupled", "21700", "Chen2020", T) for T in (0.0, 25.0, 10.0)],
    "coupled_limits_4680_Chen2020": [("limit_coupled", "4680", "Chen2020", T) for T in (0.0, 25.0, 10.0)],
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

QUEUES["P1"] = (QUEUES["coupled_limits_21700_ORegan2022"] + QUEUES["registered_21700"]
                + QUEUES["bracket_21700"])
QUEUES["P2"] = QUEUES["registered_4680"] + QUEUES["bracket_4680"]


LABELS = ("radial", "resolved", "corrected")


def segment(cell, pset):
    """All registered runs of one cell under one parameter set, one job per kernel, so that two processes can share
    them (one going forward through the list, the other backward). One process per segment keeps the number of
    built models in a process at four."""
    jobs = [("limit_coupled", cell, pset, T, lab) for T in (0.0, 25.0, 10.0) for lab in LABELS]
    jobs += [("discharge", case, pset, lab) for case in RN.DISCHARGE_CASES if case.startswith(cell + "_")
             for lab in LABELS]
    jobs += [("charge", cell, pset, lab) for lab in LABELS]
    return jobs


SEGMENTS = {f"seg_{cell}_{pset}": segment(cell, pset) for cell in ("21700", "4680") for pset in ("ORegan2022", "Chen2020")}
# the extra runs of checks V2 to V4 (D33), split so that a process holds one coupled model
SEGMENTS["checks_d15"] = [("v2",)] + [("v_discharge", "m5C_2C_half", 15, lab) for lab in LABELS]
SEGMENTS["checks_c15"] = [("v_charge", "charge10_half", 15, lab) for lab in LABELS]
SEGMENTS["checks_d30"] = [("v_discharge", "m5C_2C", 30, lab) for lab in LABELS]
SEGMENTS["checks_c30"] = [("v_charge", "charge10", 30, lab) for lab in LABELS]
QUEUES.update(SEGMENTS)


def claim_name(job):
    """One claim per piece of work: a search started as 'limit' and as 'limit_coupled' is the same work."""
    kind = job[0]
    if kind in ("limit", "limit_coupled") and len(job) == 5:
        kind = "limit_coupled"
    return "__".join([kind] + [f"{x:g}" if isinstance(x, float) else str(x) for x in job[1:]])


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def claim(job, cdir):
    """Atomically claim a job; a claim left by a process that no longer exists is taken over."""
    p = os.path.join(cdir, claim_name(job))
    for _ in range(2):
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()} {time.time():.0f}\n".encode())
            os.close(fd)
            return p
        except FileExistsError:
            txt = open(p).read().split()
            if "done" in txt:
                return None
            if txt and pid_alive(int(txt[0])):
                return None
            os.remove(p)                               # stale: its process was stopped before the job finished
    return None


def do(job):
    kind = job[0]
    print(f"=== {time.strftime('%H:%M:%S', time.gmtime())} {job}", flush=True)
    if kind == "discharge" and len(job) == 4:
        case, pset, lab = job[1], job[2], job[3]
        cell, ends, _, _, g = RN.DISCHARGE_CASES[case]
        wait_for(need(cell, ends, [g]))
        RN.discharge(case, pset, models=(lab,))
    elif kind == "charge" and len(job) == 4:
        cell, pset, lab = job[1], job[2], job[3]
        wait_for(need(cell, "b", ["charge10"]))
        pot = ("0.3C_0C", "resolved", False) if (cell == "21700" and pset == "ORegan2022") else None
        RN.charge(cell, pset, models=(lab,), store_potentials_for=pot)
    elif kind == "limit_coupled" and len(job) == 5:
        cell, pset, T, lab = job[1], job[2], job[3], job[4]
        wait_for(need(cell, "b", ["charge10"]))
        RN.limit(cell, pset, T, models=(lab,), fine_resolved=(T == 0.0 and pset == "ORegan2022"), which=("coupled",))
    elif kind == "v2":
        import stage5_checks as CK
        if not os.path.exists(os.path.join(S5.RUNDIR, "V2_uniform_temperature_coupled.npz")):
            CK.v2_run()
    elif kind == "v_discharge":
        import stage5_checks as CK
        grid, G, lab = job[1], job[2], job[3]
        wait_for(need("21700", "b", [grid], G=G))
        RN.discharge(CK.MAIN, CK.PSET, models=(lab,), gridname=grid, G=G, part="V")
    elif kind == "v_charge":
        import stage5_checks as CK
        grid, G, lab = job[1], job[2], job[3]
        wait_for(need("21700", "b", [grid], G=G))
        RN.charge("21700", CK.PSET, cases=(CK.CHG,), models=(lab,), gridname=grid, G=G, part="V")
    elif kind == "discharge":
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
    elif kind == "limit_coupled":
        cell, pset, T = job[1], job[2], job[3]
        wait_for(need(cell, "b", ["charge10"]))
        RN.limit(cell, pset, T, fine_resolved=(T == 0.0 and pset == "ORegan2022"), which=("coupled",))
    elif kind == "limit":
        cell, pset, T = job[1], job[2], job[3]
        wait_for(need(cell, "b", ["charge10"]))
        RN.limit(cell, pset, T, fine_resolved=(T == 0.0 and pset == "ORegan2022"))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("queue")
    ap.add_argument("--claims", help="a directory of claims shared by the processes working through the same jobs")
    ap.add_argument("--reverse", action="store_true")
    a = ap.parse_args()
    jobs = list(QUEUES[a.queue])
    if a.reverse:
        jobs.reverse()
    for job in jobs:
        if a.claims:
            os.makedirs(a.claims, exist_ok=True)
            p = claim(job, a.claims)
            if p is None:
                continue
            do(job)
            with open(p, "a") as f:
                f.write("done\n")
        else:
            do(job)
    print(f"=== {time.strftime('%H:%M:%S', time.gmtime())} queue {a.queue} done", flush=True)
