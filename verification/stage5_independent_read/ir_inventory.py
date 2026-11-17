#!/usr/bin/env python3
"""Independent read: which of the runs and searches D31 to D33 call for are present in results/stage5_runs.
-> out/inventory.json"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402


def expected():
    out = []
    for case, (cell, ends, Ta, I, g) in L.DISCHARGE.items():                      # D31
        for pset in L.SETS:
            for heat in L.HEATS:
                for label in L.LABELS:
                    if ends == "a" and label == "corrected":
                        continue                                                    # the radial runs (D29)
                    for single in (False, True):
                        out.append(("D31 discharge", pset, L.run_file("C", case, label, pset, heat, single)))
    for cell in ("21700", "4680"):                                                  # D32 charges
        for pset in L.SETS:
            for case in L.CHARGE:
                for label in L.LABELS:
                    for single in (False, True):
                        out.append(("D32 charge", pset, L.run_file("D", f"{cell}_{case}", label, pset, "two-way", single)))
    MAIN, CHG, PSET = "21700_b_m5C_2C", "0.3C_0C", "ORegan2022"                     # D33
    out.append(("D33 V2", PSET, os.path.join(L.RDIR, "V2_uniform_temperature_coupled.npz")))
    for label in L.LABELS:
        for heat in L.HEATS:
            for single in (False, True):
                out.append(("D33 V3 discharge", PSET, L.run_file("V", f"{MAIN}_m5C_2C_half", label, PSET, heat, single, 15)))
                out.append(("D33 V4 discharge", PSET, L.run_file("V", MAIN, label, PSET, heat, single, 30)))
        for single in (False, True):
            out.append(("D33 V3 charge", PSET, L.run_file("V", f"21700_{CHG}_charge10_half", label, PSET, "two-way", single, 15)))
            out.append(("D33 V4 charge", PSET, L.run_file("V", f"21700_{CHG}", label, PSET, "two-way", single, 30)))
    out.append(("D33 V5", PSET, os.path.join(L.RDIR, "V5_route2.npz")))
    return out


def searches():
    rows = []
    for cell in ("21700", "4680"):
        for pset in L.SETS:
            for T in (0.0, 10.0, 25.0):
                p = os.path.join(L.RDIR, f"limit_{cell}_{pset}_{T:g}C.json")
                d = json.load(open(p)) if os.path.exists(p) else {}
                for label in L.LABELS:
                    for model in ("single", "coupled"):
                        k = f"{label}|{model}"
                        fine = T == 0.0 and pset == "ORegan2022" and label == "resolved"
                        ok = k in d and (not fine or d[k].get("fine"))
                        rows.append({"what": f"{cell}|{pset}|{T:g}C|{k}", "set": pset, "present": bool(ok)})
    return rows


if __name__ == "__main__":
    ex = expected()
    miss = [(w, s, os.path.basename(p)) for w, s, p in ex if not os.path.exists(p)]
    se = searches()
    res = {"runs_expected": len(ex), "runs_missing": len(miss),
           "runs_missing_ORegan2022": [m[2] for m in miss if m[1] == "ORegan2022"],
           "runs_missing_Chen2020": [m[2] for m in miss if m[1] == "Chen2020"],
           "searches_expected": len(se), "searches_missing": [r["what"] for r in se if not r["present"]],
           "check_files": {f: os.path.exists(os.path.join(L.RES, f)) for f in ("stage5_checks.json", "stage5_v5.json", "stage5_posthoc_mesh.json")}}
    by = {}
    for w, s, p in miss:
        by[f"{w}|{s}"] = by.get(f"{w}|{s}", 0) + 1
    res["missing_by_kind"] = by
    L.dump("inventory.json", res)
    print(json.dumps({k: v for k, v in res.items() if k != "runs_missing_Chen2020"}, indent=1))
    print("Chen2020 runs missing:", len(res["runs_missing_Chen2020"]))
