#!/usr/bin/env python3
"""Stage 5, a post hoc bracket (D35), not part of the registered procedure: chosen runs of Part D repeated with more
points along each particle's radius than PyBaMM's default of 20 (D30), with everything else as registered. The
registered modules are used unchanged: this script only sets the particle mesh of PyBaMM's DFN for its own process
and writes to results/stage5_posthoc_r<N>/ instead of results/stage5_runs/.

python3 src/stage5_posthoc_r40.py charge --cell 21700 --set ORegan2022 [--points 40] [--models resolved]
python3 src/stage5_posthoc_r40.py limit --cell 21700 --set ORegan2022 --T 0 [--points 40] [--models resolved]
                                       [--which single,coupled] [--fine]"""
import argparse
import os
import sys

import pybamm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import stage5_common as S5  # noqa: E402


def set_particle_points(n):
    """Every DFN built in this process gets n points along each particle's radius (PyBaMM's default is 20)."""
    base = pybamm.lithium_ion.BaseModel.default_var_pts.fget

    def var_pts(self):
        v = dict(base(self))
        v["r_n"] = v["r_p"] = n
        return v
    pybamm.lithium_ion.DFN.default_var_pts = property(var_pts)
    S5.RUNDIR = os.path.join(C.RESULTS, f"stage5_posthoc_r{n}")
    os.makedirs(S5.RUNDIR, exist_ok=True)
    os.environ.pop("STAGE5_TRIAL_CACHE", None)        # the registered runs' stored trials are not this mesh's


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["charge", "limit"])
    ap.add_argument("--cell", default="21700")
    ap.add_argument("--set", default="ORegan2022")
    ap.add_argument("--points", type=int, default=40)
    ap.add_argument("--models", default="resolved")
    ap.add_argument("--cases", default="0.3C_0C,0.7C_25C")
    ap.add_argument("--T", type=float)
    ap.add_argument("--which", default="single,coupled")
    ap.add_argument("--fine", action="store_true")
    a = ap.parse_args()
    set_particle_points(a.points)
    import stage5_runs as RN  # noqa: E402  (imported after the mesh is set)
    models = tuple(a.models.split(","))
    if a.what == "charge":
        RN.charge(a.cell, a.set, cases=tuple(a.cases.split(",")), models=models)
    else:
        RN.limit(a.cell, a.set, a.T, models=models, fine_resolved=a.fine, which=tuple(a.which.split(",")))
