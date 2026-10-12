"""Auditor's check for finding H1: the study's own radial model (src/radial1d.py, imported read-only) evaluated at the
time the paper's 2C, minus 5 C discharge ends (Fig. 4d: about 1.34 A h multi-unit, 1.50 A h single-unit, i.e. about
482 s and 540 s at 10 A), against the study's end of discharge. Run with: python3 -B radial_at_paper_end_time.py"""
import sys
sys.path.insert(0, "/home/claude/m50-radial-vs-resolved-field/src")
sys.dont_write_bytecode = True
import radial1d as R1
for name, times in [("Chen2020_m5C_2C", [482.0, 540.0, 1706.7446])]:
    q, t_end, _ = R1.load_heat(name)
    m = R1.Radial1D("21700")
    r = m.run(q, t_end, R1.amb_of(name), snap_times=times)
    for t in times:
        k = min(r["snaps"].keys(), key=lambda x: abs(x - t))
        s = r["snaps"][k]
        print(f"{name} t = {t:7.1f} s: innermost minus outermost unit {s['unit_spread']:.3f} K, "
              f"core-to-surface {s['dT_core_surface']:.3f} K; paper Fig. 5 innermost 11.54 K is {11.54 / s['unit_spread']:.2f} times")
