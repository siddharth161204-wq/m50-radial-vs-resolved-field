#!/usr/bin/env python3
"""Stage 2, V4: the resolved cell's share of the heat leaving through the ends, from the heat removed through each
surface (as D15), for cases (b) and (d) in the 21700 at the six registered heats. The 4680's share is D15's at 2C and
minus 5 C; its six re-solves (about 15 minutes each here) were not run. SPLIT_ONLY=4680 runs them. Re-solves Stage 1's
registered cases with src/cell3d.py on the registered step grid and checks the end-of-discharge field against the
registered field file. Writes results/stage2_split.json (updated after every case)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402
from cell3d import Cell3D  # noqa: E402

OUT = os.path.join(C.RESULTS, os.environ.get("SPLIT_OUT", "stage2_split.json"))


def main():
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}
    cases = [("21700", "b"), ("21700", "d")] + ([("4680", "b")] if os.environ.get("SPLIT_ONLY", "").startswith("4680") else [])
    only = os.environ.get("SPLIT_ONLY")          # e.g. "4680_b_Chen2020_m5C_2C" to run one case
    for cell, bc in cases:
        for heat in R1.CASES_REGISTERED:
            if only and not f"{cell}_{bc}_{heat}".startswith(only):
                continue
            key = f"{cell}_{bc}_{heat}"
            if key in out:
                continue
            q, t_end, _ = R1.load_heat(heat)
            res, _T = Cell3D(cell, bc).run(q, t_end, R1.amb_of(heat))
            lost = res["heat_lost_by_surface_J"]
            tot = sum(lost.values())
            reg = json.load(open(os.path.join(C.RESULTS, "fields", f"{key}.json")))["end"]
            out[key] = {"heat_lost_by_surface_J": lost,
                        "ends_share": (lost.get("top", 0.0) + lost.get("bottom", 0.0)) / tot,
                        "energy_residual_rel": res["energy_J"]["residual_rel"],
                        "check_units_max_abs_diff_vs_registered_K":
                            float(np.max(np.abs(np.array(res["end"]["units"]) - np.array(reg["units"]))))}
            json.dump(out, open(OUT, "w"), indent=2)
            print(key, round(out[key]["ends_share"], 4), out[key]["check_units_max_abs_diff_vs_registered_K"], flush=True)


def merge():
    """Merge results/stage2_split_*.json (one case each) into results/stage2_split.json."""
    import glob
    out = json.load(open(os.path.join(C.RESULTS, "stage2_split.json")))
    for p in sorted(glob.glob(os.path.join(C.RESULTS, "stage2_split_*.json"))):
        out.update(json.load(open(p)))
        os.remove(p)
    json.dump(out, open(os.path.join(C.RESULTS, "stage2_split.json"), "w"), indent=2)


if __name__ == "__main__":
    merge() if "--merge" in sys.argv else main()
