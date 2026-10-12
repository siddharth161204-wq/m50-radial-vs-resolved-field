#!/usr/bin/env python3
"""V4: digitise Fig. 5 (p. 5) and Fig. 7a (p. 6) of Yang, Cui and Tartakovsky (2026) and compare them with the
one-dimensional model of this study.

The figures are the paper's own embedded JPEG images (extracted with `pdfimages -f 5 -l 6 -j`, unchanged). The axes
are calibrated from the tick marks, found as dark minima just outside the frame. Each curve is isolated by its colour
(Fig. 5: black solid 1.25C 25 C, green dashed 2C 25 C, red dotted 3C 25 C, blue dash-dot 2C minus 5 C; Fig. 7a: black
2C minus 5 C), and its height is the median row of its pixels in each column. The reading error is taken as half a
line width plus one pixel of tick calibration, converted to kelvin.

The paper plots T_loc - T_Nunit (each unit against the outermost unit) at the end of discharge against r = r_b / R_b.
The one-dimensional model is compared in the same form: unit temperature minus the outermost unit's, at the unit's
mid-radius over R.
Writes verification/v4_digitised.csv and verification/v4.json.
"""
import csv
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
import radial1d as R1  # noqa: E402


def ticks(gray, frame_bottom, frame_left, x_rows, y_cols):
    band = gray[x_rows[0]:x_rows[1], frame_left:].min(axis=0)
    xs = [j + frame_left for j in range(1, len(band) - 1) if band[j] < 140 and band[j] <= band[j - 1] and band[j] <= band[j + 1]]
    band = gray[:frame_bottom, y_cols[0]:y_cols[1]].min(axis=1)
    ys = [i for i in range(1, len(band) - 1) if band[i] < 140 and band[i] <= band[i - 1] and band[i] <= band[i + 1]]
    return xs, ys


def curve(mask, x_of_col, y_of_row, cols):
    out = []
    for c in cols:
        rows = np.where(mask[:, c])[0]
        if len(rows):
            out.append((x_of_col(c), y_of_row(np.median(rows)), len(rows)))
    return np.array(out)


def fig5():
    im = np.asarray(Image.open(os.path.join(HERE, "v4", "jes-001.jpg")).convert("RGB")).astype(int)
    g = im.mean(axis=2)
    top, bottom, left, right = 6, 641, 123, 975
    xs, ys = ticks(g, bottom, left, (648, 656), (114, 122))
    assert len(xs) == 5 and len(ys) == 7, (xs, ys)
    px = np.polyfit(xs, [0.2, 0.4, 0.6, 0.8, 1.0], 1)
    py = np.polyfit(ys, [12, 10, 8, 6, 4, 2, 0], 1)     # rows run downward: the top tick is 12 K
    xo = lambda c: float(np.polyval(px, c))
    yo = lambda r: float(np.polyval(py, r))
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    inner = np.zeros(g.shape, bool)
    inner[top + 4:bottom - 3, left + 4:right - 3] = True
    legend = np.zeros(g.shape, bool)
    legend[15:250, 590:975] = True
    masks = {
        "3C 25 C": (R > 170) & (G < 110) & (B < 110),
        "2C minus 5 C": (B > 150) & (R < 110) & (G < 140),
        "2C 25 C": (G > 80) & (R < 90) & (B < 90) & (G > R + 30),
        "1.25C 25 C": (g < 90) & (np.abs(R - G) < 30) & (np.abs(G - B) < 30),
    }
    cols = range(left + 5, right - 4)
    out = {}
    for k, m in masks.items():
        m = m & inner & ~legend
        if k == "1.25C 25 C":
            m &= np.arange(g.shape[0])[:, None] > np.polyval(np.polyfit([12, 10, 8, 6, 4, 2, 0], ys, 1), 4.0)
        out[k] = curve(m, xo, yo, cols)
    lw_px = 6.0
    err = abs(py[0]) * (lw_px / 2 + 1)
    return out, {"x_ticks_px": xs, "y_ticks_px": ys, "K_per_px": abs(py[0]), "reading_error_K": err}


def fig7a():
    """Fig. 7a: the 4680 at 2C and minus 5 C (black solid line), left panel of the image."""
    im = np.asarray(Image.open(os.path.join(HERE, "v4", "jes-003.jpg")).convert("RGB")).astype(int)
    g = im.mean(axis=2)
    top, bottom, left, right = 5, 582, 111, 884
    xs, ys = ticks(g[:, :right + 2], bottom, left, (586, 592), (101, 109))
    assert len(xs) == 5 and len(ys) == 4, (xs, ys)
    px = np.polyfit(xs, [0.2, 0.4, 0.6, 0.8, 1.0], 1)
    py = np.polyfit(ys, [30, 20, 10, 0], 1)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    m = (g < 90) & (np.abs(R - G) < 30) & (np.abs(G - B) < 30)
    inner = np.zeros(g.shape, bool)
    inner[top + 4:bottom - 3, left + 4:right - 3] = True
    excl = np.zeros(g.shape, bool)
    excl[15:80, 540:840] = True          # legend
    excl[520:580, 115:190] = True        # panel label "(a)"
    d = curve(m & inner & ~excl, lambda c: float(np.polyval(px, c)), lambda r: float(np.polyval(py, r)),
              range(left + 5, right - 4))
    return d, {"x_ticks_px": xs, "y_ticks_px": ys, "K_per_px": abs(py[0]), "reading_error_K": abs(py[0]) * 4}


def main():
    curves, cal = fig5()
    rows = []
    import hashlib
    pdf = os.environ.get("PAPER_PDF", "")
    res = {"fig5_calibration": cal, "fig5": {}, "fig7a": {},
           "source_pdf_sha256": "c75f54d772ee62b0c2cf7a24332f2f0f51bc0772c5c50494d3a788f4ce0a3c37",
           "source_pdf_note": "Yang, Cui and Tartakovsky (2026), J. Electrochem. Soc. 173, 050520, publisher PDF; images "
                              "extracted with pdfimages -f 5 -l 6 -j (jes-001.jpg is Fig. 5, jes-003.jpg is Fig. 7)"}
    if pdf and os.path.exists(pdf):
        res["source_pdf_sha256"] = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
    cases = {"1.25C 25 C": "Chen2020_p25C_1.25C", "2C 25 C": "Chen2020_p25C_2C", "3C 25 C": "Chen2020_p25C_3C",
             "2C minus 5 C": "Chen2020_m5C_2C"}
    for k, d in curves.items():
        x, y = d[:, 0], d[:, 1]
        order = np.argsort(x)
        x, y = x[order], y[order]
        heat = cases[k]
        q, t_end, _ = R1.load_heat(heat)
        m = R1.Radial1D("21700")
        r = m.run(q, t_end, R1.amb_of(heat))
        u = np.array(r["end"]["units"])
        rm = 0.5 * (m.unit_edges[:-1] + m.unit_edges[1:]) / m.R
        du = u - u[-1]
        # compare where the paper has units: its innermost to its outermost unit
        grid = np.linspace(max(x.min(), 0.2), min(x.max(), 0.95), 16)
        his = np.interp(grid, x, y)
        ours = np.interp(grid, rm, du)
        res["fig5"][k] = {"heat": heat, "paper_x_range": [float(x.min()), float(x.max())],
                          "paper_dT_innermost_K": float(y[np.argmin(x)]), "ours_dT_innermost_unit_K": float(du[0]),
                          "ratio_paper_over_ours_on_grid_mean": float(np.mean(his / ours)),
                          "ratio_paper_over_ours_at_0.2": float(np.interp(0.2, x, y) / np.interp(0.2, rm, du)),
                          "ratio_paper_over_ours_on_grid_min": float(np.min(his / ours)),
                          "ratio_paper_over_ours_on_grid_max": float(np.max(his / ours)),
                          "max_abs_diff_K": float(np.max(np.abs(his - ours))),
                          "within_reading_error": bool(np.max(np.abs(his - ours)) <= cal["reading_error_K"])}
        for gx, h, o in zip(grid, his, ours):
            rows.append([k, f"{gx:.4f}", f"{h:.4f}", f"{o:.4f}"])
    # the paper's figures put its innermost unit at r/R = 0.165 (21700) and 0.0715 (4680): a hollow core of about
    # 1.74 and 1.64 mm. The same comparison with the one-dimensional model on that annulus (secondary geometry; the
    # registered model is the solid cylinder of the paper's Eq. 4), same total heat:
    core = {}
    for k, heat in cases.items():
        q, t_end, _ = R1.load_heat(heat)
        x0 = res["fig5"][k]["paper_x_range"][0]
        r_in = x0 * R1.Radial1D("21700").R
        m = R1.Radial1D("21700", r_in=r_in)
        Vr = np.pi * m.R ** 2 / (np.pi * (m.R ** 2 - r_in ** 2))
        rr = m.run(lambda t, q=q: q(t) * Vr, t_end, R1.amb_of(heat))
        u = np.array(rr["end"]["units"])
        core[k] = {"r_in_mm": 1e3 * r_in, "dT_innermost_unit_K": float(u[0] - u[-1]),
                   "registered_dT_innermost_unit_K": res["fig5"][k]["ours_dT_innermost_unit_K"],
                   "paper_over_hollow_core_model": res["fig5"][k]["paper_dT_innermost_K"] / float(u[0] - u[-1])}
    res["fig5_hollow_core_secondary"] = core
    d7, cal7 = fig7a()
    x, y = d7[:, 0], d7[:, 1]
    o = np.argsort(x)
    x, y = x[o], y[o]
    q, t_end, _ = R1.load_heat("Chen2020_m5C_2C")
    m = R1.Radial1D("4680")
    r = m.run(q, t_end, -5.0)
    u = np.array(r["end"]["units"])
    rm = 0.5 * (m.unit_edges[:-1] + m.unit_edges[1:]) / m.R
    du = u - u[-1]
    grid = np.linspace(max(x.min(), 0.1), min(x.max(), 0.95), 18)
    his, ours = np.interp(grid, x, y), np.interp(grid, rm, du)
    res["fig7a"] = {"calibration": cal7, "paper_x_range": [float(x.min()), float(x.max())],
                    "paper_dT_innermost_K": float(y[0]), "ours_dT_innermost_unit_K": float(du[0]),
                    "ratio_paper_over_ours_on_grid_mean": float(np.mean(his / ours)),
                    "ratio_paper_over_ours_at_0.2": float(np.interp(0.2, x, y) / np.interp(0.2, rm, du)),
                    "max_abs_diff_K": float(np.max(np.abs(his - ours)))}
    for gx, h, o_ in zip(grid, his, ours):
        rows.append(["4680 2C minus 5 C (Fig. 7a)", f"{gx:.4f}", f"{h:.4f}", f"{o_:.4f}"])
    with open(os.path.join(HERE, "v4_digitised.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "r_over_R", "paper_dT_K", "this_study_1d_dT_K"])
        for r_ in rows:
            w.writerow(r_)
    with open(os.path.join(HERE, "v4.json"), "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
