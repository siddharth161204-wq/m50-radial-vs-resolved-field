#!/usr/bin/env python3
"""The study's figure (brief step 6), at 2C and minus 5 C, end of discharge, registered inputs.

left: the mid-height radial profile above the surface temperature, one-dimensional model against the resolved cell
    under the four boundary conditions (21700, the M50);
second: the temperature along the axis relative to mid-height (M50);
right, two panels: unit temperatures above ambient, one-dimensional against the resolved annulus averages, for the
    M50 and the 4680, each on its own scale.
The panels carry no letters, because (a) to (d) name the boundary conditions.
Usage: python3 src/make_figure.py   (writes results/figure.png and results/figure.pdf)
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import radial1d as R1  # noqa: E402

HEAT = "Chen2020_m5C_2C"
T_AMB = -5.0
COL = {"1d": "#52514e", "a": "#2a78d6", "b": "#eb6834", "c": "#1baf7a", "d": "#6250d6"}
LAB = {"1d": "radial model", "a": "(a) side cooled", "b": "(b) side and ends", "c": "(c) as (b) + tabs",
       "d": "(d) as (b), h = 25"}
STY = {"1d": dict(ls="--", lw=1.4), "a": dict(ls="-", lw=1.4), "b": dict(ls="-", lw=1.4),
       "c": dict(ls=":", lw=1.6), "d": dict(ls="-.", lw=1.4)}


def field(cell, bc):
    return json.load(open(os.path.join(C.RESULTS, "fields", f"{cell}_{bc}_{HEAT}.json")))


def one_d(cell, t):
    q, t_end, _ = R1.load_heat(HEAT)
    m = R1.Radial1D(cell)
    r = m.run(q, t_end, T_AMB, snap_times=[t])
    return r["snaps"][t], m


def main():
    plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "legend.fontsize": 6.2,
                         "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                         "ytick.major.width": 0.6})
    fig, ax = plt.subplots(1, 4, figsize=(7.4, 2.45), gridspec_kw=dict(width_ratios=[1.05, 1.0, 1.0, 1.0]))
    f21 = {bc: field("21700", bc) for bc in ("a", "b", "c", "d")}
    t_end = f21["a"]["end"]["t"]
    s1, m1 = one_d("21700", t_end)
    R21 = C.CELLS["21700"]["R"] * 1e3
    # (a) mid-height profile above the surface
    r1 = np.array(s1["profile_r"]) * 1e3
    T1 = np.array(s1["profile_T"])
    ax[0].plot(r1, T1 - T1[-1], color=COL["1d"], label=LAB["1d"], **STY["1d"])
    for bc in ("a", "b", "c", "d"):
        e = f21[bc]["end"]
        r = np.array(e["profile_r"]) * 1e3
        T = np.array(e["profile_T"])
        ax[0].plot(r, T - e["T_surface_mid"], color=COL[bc], label=LAB[bc], **STY[bc])
    ax[0].set_xlim(0, R21)
    ax[0].set_ylim(bottom=0)
    ax[0].set_xlabel("radius (mm)")
    ax[0].set_ylabel("T minus surface T at mid-height (K)")
    ax[0].set_title("Radial profile at mid-height, M50", loc="left")

    # (b) along the axis, relative to mid-height
    ax[1].axhline(0.0, color=COL["1d"], label=LAB["1d"], **STY["1d"])
    for bc in ("a", "b", "c", "d"):
        e = f21[bc]["end"]
        z = np.array(e["core_z"]) * 1e3
        T = np.array(e["core_T"])
        ax[1].plot(z, T - e["T_core_mid"], color=COL[bc], label=LAB[bc], **STY[bc])
    ax[1].legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.0), handlelength=2.4, borderaxespad=0.2)
    ax[1].set_xlim(0, C.CELLS["21700"]["H"] * 1e3)
    ax[1].set_xlabel("height (mm), base to cap")
    ax[1].set_ylabel("axis T minus mid-height axis T (K)")
    ax[1].set_title("Along the axis, M50", loc="left")
    # (c) unit temperatures above ambient, 21700 and 4680
    for k, cell in enumerate(("21700", "4680")):
        a_ = ax[2 + k]
        fa = field(cell, "a")
        fb = field(cell, "b")
        s, m = one_d(cell, fa["end"]["t"])
        n = m.n_units
        x = np.arange(1, n + 1)
        a_.plot(x, np.array(s["units"]) - T_AMB, color=COL["1d"], label=LAB["1d"], **STY["1d"])
        a_.plot(x, np.array(fa["end"]["units"]) - T_AMB, color=COL["a"], label=LAB["a"], **STY["a"])
        a_.plot(x, np.array(fb["end"]["units"]) - T_AMB, color=COL["b"], label=LAB["b"], **STY["b"])
        a_.set_xlim(1, n)
        a_.set_ylim(bottom=0)
        a_.set_xlabel("unit, core to surface")
        a_.set_title(f"Units, {'M50' if cell == '21700' else cell}", loc="left")
        if k == 0:
            a_.set_ylabel("unit T above ambient (K)")
    for a_ in ax:
        a_.grid(True, color="#e6e5e1", lw=0.5)
        a_.set_axisbelow(True)
    fig.tight_layout(pad=0.3, w_pad=0.8)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(C.RESULTS, f"figure.{ext}"), dpi=300)
    print("figure written")


if __name__ == "__main__":
    main()
