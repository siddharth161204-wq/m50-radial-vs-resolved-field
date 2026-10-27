#!/usr/bin/env python3
"""D21: two labels in the stored Stage 3 runs corrected without re-running them (no error, history or learned value
changes). The level field, which run() overwrote with "none" for 14 of the 40 runs, is set from sigma_eps. The end
sink beside the learned error in the insulated-ends runs, which model_beta evaluated at h = 400 although beta = 0
with the ends insulated (D20), is set to 0. src/stage3_enkf.py now writes both as corrected here.
python3 src/stage3_relabel.py   (then python3 src/stage3_report.py)"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from stage3_enkf import SIG_REF  # noqa: E402


def level(r):
    if r["method"] == "forecast":
        return "none"
    return {0.1: "0.1x", 1.0: "1x", 10.0: "10x"}[round(r["sigma_eps"] / SIG_REF, 1)]


def main():
    for cell in ("21700", "4680"):
        p = os.path.join(C.RESULTS, f"stage3_runs_{cell}.json")
        runs = json.load(open(p))
        n_level = n_sink = 0
        for r in runs:
            lv = level(r)
            n_level += r.get("level") != lv
            r["level"] = lv
            if r["bc"] == "a" and r["sink_mean_second_half_W_m3"] is not None:
                n_sink += r["sink_mean_second_half_W_m3"] != 0.0
                r["sink_mean_second_half_W_m3"] = 0.0
        json.dump(runs, open(p, "w"))
        print(cell, f"{len(runs)} runs, level corrected in {n_level}, insulated-ends sink set to 0 in {n_sink}")


if __name__ == "__main__":
    main()
