#!/usr/bin/env python3
"""Independent read, phase 2: every number in results/stage5_summary.md (the tables the README and note quote) and in
results/stage5_paper_numbers.json against my own recomputed readings (out/readings.json; run ir_readings.py first).
A displayed number agrees when my value, rounded to the displayed decimals, lies within half a unit of the last digit.
-> out/summary_check.json"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ir_lib as L  # noqa: E402

CASE = {"M50, 2C, -5 C, cooled": "21700_b_m5C_2C", "M50, 2C, 25 C, cooled": "21700_b_p25C_2C",
        "M50, 1.25C, 25 C, cooled": "21700_b_p25C_1.25C", "M50, 2C, -5 C, insul.": "21700_a_m5C_2C",
        "4680, 2C, -5 C, cooled": "4680_b_m5C_2C", "M50, 3C, 25 C, cooled": "21700_b_p25C_3C"}
KERN = {"radial model": "radial", "resolved cell": "resolved", "end-corrected": "corrected"}
NUM = re.compile(r"[-+]?\d+(?:\.\d+)?")
CHECKS, BAD, HALFWAY = [], [], []


def agree(shown, mine, where):
    """shown: the displayed string (a number); mine: my value in the same units"""
    if mine is None:
        ok = shown.strip() == ""
        CHECKS.append(where)
        if not ok:
            BAD.append({"at": where, "shown": shown, "mine": None})
        return
    m = NUM.search(shown)
    if not m:
        BAD.append({"at": where, "shown": shown, "mine": mine})
        return
    s = m.group(0)
    dec = len(s.split(".")[1]) if "." in s else 0
    x = float(s)
    CHECKS.append(where)
    half = 0.5 * 10 ** (-dec)
    if abs(mine - x) > half * (1 + 1e-9):
        BAD.append({"at": where, "shown": s, "mine": mine})
    elif abs(abs(mine - x) - half) < 1e-9 * max(1.0, abs(mine)):
        HALFWAY.append({"at": where, "shown": s, "mine": mine, "note": "my value lies halfway between two displayed values"})


def tables(md):
    out, cur = [], None
    for line in md.splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cur is None:
                cur = {"header": cells, "rows": []}
                out.append(cur)
            else:
                cur["rows"].append(cells)
        elif not line.startswith("|"):
            cur = None
    return out


def main():
    rd = json.load(open(os.path.join(L.OUT, "readings.json")))
    D = {r["key"]: r for r in rd["discharge"]}
    S = {r["key"]: r for r in rd["shares"]}
    C = {r["key"]: r for r in rd["charge"]}
    Lm = {r["key"]: r for r in rd["limit_rows"]}
    md = open(os.path.join(L.RES, "stage5_summary.md")).read()
    T = tables(md)
    assert len(T) == 4, len(T)
    # 1: discharge, two-way heat
    for row in T[0]["rows"]:
        case, k = CASE[row[0]], KERN[row[1]]
        for j, pset in ((2, "ORegan2022"), (6, "Chen2020")):
            key = f"{case}|{pset}|two-way|{k}"
            if row[j] == "":
                continue
            agree(row[j], 100 * D[key]["penalty_energy"], f"T1|{key}|penalty")
            agree(row[j + 1], D[key]["t_cut_coupled_s"], f"T1|{key}|cut-off")
            agree(row[j + 2], 100 * S[key]["spread_tavg"], f"T1|{key}|spread")
            if k != "resolved":
                agree(row[j + 3], 100 * S[key]["spread_rel_error"], f"T1|{key}|against resolved")
        rev = S[f"{case}|Chen2020|two-way|{k}"]["reversal_s"]
        agree(row[10], rev, f"T1|{case}|Chen2020|{k}|reversal")
    # 2: C3, one-way heat
    for row in T[1]["rows"]:
        case, k = CASE[row[0]], KERN[row[1]]
        for j, pset in ((2, "ORegan2022"), (5, "Chen2020")):
            key = f"{case}|{pset}|one-way|{k}"
            if row[j] == "":
                continue
            agree(row[j], 100 * S[key]["spread_tavg"], f"T2|{key}|coupled")
            p4 = S[key].get("proxy_stage4_spread")
            agree(row[j + 1], None if p4 is None else 100 * p4, f"T2|{key}|stage4")
            u, g = row[j + 2].split(";")
            agree(u, 100 * S[key]["proxy_window_unit_spread"], f"T2|{key}|window units")
            agree(g, 100 * S[key]["proxy_window_group_spread"], f"T2|{key}|window groups")
    # 3: charge
    for row in T[2]["rows"]:
        cell = "21700" if row[0] == "M50" else "4680"
        m = re.match(r"([\d.]+)C at ([\d.]+) C", row[1])
        case = f"{float(m.group(1)):g}C_{float(m.group(2)):g}C"
        k = KERN[row[2]]
        for j, pset in ((3, "ORegan2022"), (5, "Chen2020")):
            for jj, model in ((j, "coupled"), (j + 1, "single")):
                key = f"{cell}|{case}|{pset}|{k}|{model}"
                if row[jj] == "":
                    continue
                agree(row[jj], 1e3 * C[key]["margin_V"], f"T3|{key}|margin")
                if model == "coupled":
                    g = int(re.search(r"group (\d+)", row[jj]).group(1))
                    CHECKS.append(f"T3|{key}|group")
                    if g != C[key]["group"]:
                        BAD.append({"at": f"T3|{key}|group", "shown": g, "mine": C[key]["group"]})
    # 4: plating-limited rates
    for row in T[3]["rows"]:
        cell = "21700" if row[0] == "M50" else "4680"
        Ta = float(row[1])
        k = KERN[row[2]]
        for j, (pset, model) in enumerate((("ORegan2022", "single"), ("ORegan2022", "coupled"), ("Chen2020", "single"), ("Chen2020", "coupled"))):
            r = Lm[f"{cell}|{pset}|{Ta:g}|{k}|{model}"]
            v = r["fine_rate_spec_C"] or r["rate_spec_C"]
            agree(row[3 + j], v, f"T4|{cell}|{pset}|{Ta:g}|{k}|{model}|rate")
    # the paper-numbers file
    pn = json.load(open(os.path.join(L.RES, "stage5_paper_numbers.json")))
    nbad, n = [], 0
    for key, v in pn["this_study"].items():
        d, s = D[key], S[key]
        run_lab = "radial" if d["identical_to_radial"] else key.split("|")[3]
        case, pset, heat, _ = key.split("|")
        r = L.load_run(L.run_file("C", case, run_lab, pset, heat, False))
        sh = r["I"] / r["meta"]["I_app_A"]
        rate = d["rate_C"]
        mine = {"penalty_energy": d["penalty_energy"], "penalty_capacity": d["penalty_capacity"], "Q_coupled_Ah": d["Q_coupled_Ah"],
                "Q_single_Ah": d["Q_single_Ah"], "t_cut_coupled_s": d["t_cut_coupled_s"], "spread_tavg": s["spread_tavg"],
                "group_rate_range_C": [rate * float(sh.min()), rate * float(sh.max())], "reversal_s": s["reversal_s"]}
        for kk, mv in mine.items():
            sv = v.get(kk)
            n += 1
            if isinstance(mv, list):
                if any(abs(a - b) > 1e-9 * max(1, abs(b)) for a, b in zip(mv, sv)):
                    nbad.append({"key": key, "field": kk, "mine": mv, "stored": sv})
            elif (mv is None) != (sv is None) or (mv is not None and abs(mv - sv) > 1e-9 * max(1e-12, abs(sv))):
                nbad.append({"key": key, "field": kk, "mine": mv, "stored": sv})
    for key, sv in pn["plating_limited_rate_spec_C"].items():
        cell, pset, T_, k, model = key.split("|")
        mv = Lm[f"{cell}|{pset}|{float(T_[:-1]):g}|{k}|{model}"]["rate_spec_C"]
        n += 1
        if (mv is None) != (sv is None) or (mv is not None and abs(mv - sv) > 1e-9):
            nbad.append({"key": key, "field": "rate", "mine": mv, "stored": sv})
    for key, sv in pn["margin_V"].items():
        n += 1
        if abs(C[key]["margin_V"] - sv) > 1e-9 * max(1e-12, abs(sv)) + 1e-12:
            nbad.append({"key": key, "field": "margin", "mine": C[key]["margin_V"], "stored": sv})
    paper_ok = (pn["paper"]["energy_overestimate_3C_25C"] == 0.0345 and pn["paper"]["overestimate_2C_m5C"] == 0.1132
                and pn["paper"]["energy_overestimate_4680_2C_m5C"] == 0.1145 and pn["paper"]["4680_unit_rates_C"] == [1.25, 2.75])
    res = {"summary_numbers_checked": len(CHECKS), "summary_not_reproduced": BAD, "summary_halfway_cases": HALFWAY,
           "paper_numbers_checked": n, "paper_numbers_not_reproduced": nbad,
           "paper_values_as_D27_quotes_them": paper_ok,
           "note_on_the_rate_table": "the coarse rates are multiples of 0.00625C; at four decimals a halfway value is shown "
                                     "rounded by its binary representation (0.36875 as 0.3688, 0.54375 as 0.5437)"}
    L.dump("summary_check.json", res)
    print(json.dumps({k: (v if not isinstance(v, list) else (len(v), v[:12])) for k, v in res.items()}, indent=1, default=str))


if __name__ == "__main__":
    main()
