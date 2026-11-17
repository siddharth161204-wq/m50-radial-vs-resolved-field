"""Independent read of Stage 5: definitions written from DECISIONS.md D5, D6, D24, D28 to D33 and
predictions_stage5.md, without importing anything from src/.

Run every script of this folder from this folder with `python3 -I -B <script>` (through ./memgate.sh, which waits
for memory and sets one thread and nice 10). Outputs go to ./out/.
"""
import csv
import json
import math
import os
from fractions import Fraction

import numpy as np
from scipy.signal import fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RES = os.path.join(ROOT, "results")
KDIR = os.path.join(RES, "stage5_kernels")
RDIR = os.path.join(RES, "stage5_runs")
OUT = os.path.join(HERE, "out")

# D5: the two cylinders; D6: heat per unit volume of the 21700 cylinder in both cells
CELL = {"21700": {"R": 21.1e-3 / 2, "H": 70.1e-3, "N": 45}, "4680": {"R": 46.0e-3 / 2, "H": 80.0e-3, "N": 111}}
V21700 = math.pi * CELL["21700"]["R"] ** 2 * CELL["21700"]["H"]
C_SPEC = 4.85            # D27, D32: the specification's 1C in A (its 0.3C is 1,455 mA)
C_STUDY = 5.0            # the sets' nominal 5 A h (Stages 1 to 4)
H_CONV = 400.0           # W/(m2 K), the paper's h (D2)

# D31 cases: key -> (cell, ends, ambient, I_app in A, the registered heat that fixes the grid)
DISCHARGE = {"21700_b_m5C_2C": ("21700", "b", -5.0, 10.0, "m5C_2C"),
             "21700_b_p25C_2C": ("21700", "b", 25.0, 10.0, "p25C_2C"),
             "21700_b_p25C_1.25C": ("21700", "b", 25.0, 6.25, "p25C_1.25C"),
             "21700_a_m5C_2C": ("21700", "a", -5.0, 10.0, "m5C_2C"),
             "4680_b_m5C_2C": ("4680", "b", -5.0, 10.0, "m5C_2C"),
             "21700_b_p25C_3C": ("21700", "b", 25.0, 15.0, "p25C_3C")}
HEAT_FILE = {"m5C_2C": "Chen2020_m5C_2C", "p25C_2C": "Chen2020_p25C_2C", "p25C_1.25C": "Chen2020_p25C_1.25C",
             "p25C_3C": "Chen2020_p25C_3C"}
# D32 cases: key -> (rate in the specification's C, ambient, within the specification)
CHARGE = {"0.3C_0C": (0.3, 0.0, True), "0.7C_25C": (0.7, 25.0, True), "0.7C_0C": (0.7, 0.0, False),
          "1C_25C": (1.0, 25.0, False), "2C_25C": (2.0, 25.0, False)}
LABELS = ("radial", "resolved", "corrected")
SETS = ("ORegan2022", "Chen2020")
HEATS = ("two-way", "one-way")


def kernel_file(label, ends, cell, grid, G=15):
    """D29: radial = Stage 1's radial model (side convection only); resolved = the 3D cell with the ends insulated
    (a) or cooled (b); end-corrected = the radial model plus D18's sink, which with insulated ends is the radial."""
    if label == "radial" or (label == "corrected" and ends == "a"):
        stem = f"radial_lat_{cell}_{grid}"
    elif label == "resolved":
        stem = f"resolved_{ends}_{cell}_{grid}"
    else:
        stem = f"corrected_b_{cell}_{grid}"
    return os.path.join(KDIR, f"{stem}_G{G}.npz")


def run_file(part, case, label, pset, heat, single, G=15):
    return os.path.join(RDIR, f"{part}_{case}_{label}_{pset}_{heat}_{'single' if single else 'coupled'}_G{G}.npz")


# ------------------------------------------------------------------------------------------------------------
# units and groups (D24, D28, D29)
# ------------------------------------------------------------------------------------------------------------
def unit_w(N):
    """Area weights of equal-thickness annuli: ((i)^2 - (i-1)^2) / N^2."""
    i = np.arange(1, N + 1, dtype=float)
    return (i ** 2 - (i - 1) ** 2) / N ** 2


def edges(N, G):
    """Group edges: the integer nearest k N / G (exact rational arithmetic; a tie, which D28 does not meet, is
    reported by the caller, here resolved upwards)."""
    out = []
    for k in range(G + 1):
        x = Fraction(k * N, G)
        out.append(int(math.floor(x + Fraction(1, 2))))
    return out


def has_tie(N, G):
    return any(Fraction(k * N, G).denominator == 2 for k in range(G + 1))


def group_w(N, G):
    w, e = unit_w(N), edges(N, G)
    return np.array([w[e[k]:e[k + 1]].sum() for k in range(G)])


def unit_to_group(N, G):
    w, e = unit_w(N), edges(N, G)
    A = np.zeros((G, N))
    for k in range(G):
        A[k, e[k]:e[k + 1]] = w[e[k]:e[k + 1]] / w[e[k]:e[k + 1]].sum()
    return A


# ------------------------------------------------------------------------------------------------------------
# the registered heat and its grid (D6, D28)
# ------------------------------------------------------------------------------------------------------------
def heat(gridbase):
    with open(os.path.join(RES, "heat", HEAT_FILE[gridbase] + ".csv")) as f:
        rows = list(csv.reader(f))
    hdr = rows[0]
    it, iq = hdr.index("t_s"), hdr.index("heat_total_W")
    t = np.array([float(r[it]) for r in rows[1:]])
    q = np.array([float(r[iq]) for r in rows[1:]]) / V21700
    return t, q


def grid(name):
    """(dt, n, t_end): discharge grids t_end / ceil(t_end / 1 s) from the registered heat; charge grid 10 s;
    '_half' halves the step (V3)."""
    half = name.endswith("_half")
    base = name[:-5] if half else name
    if base == "charge10":
        dt, n, te = 10.0, 0, 0.0
    else:
        t, _ = heat(base)
        te = float(t[-1])
        n = int(math.ceil(te - 1e-9))
        dt = te / n
    if half:
        dt, n = dt / 2.0, 2 * n
    return dt, n, te


def heat_on_grid(name):
    """The registered heat at the end of each step k = 1..n (linear interpolation of the 1 s DFN outputs, as the
    Stage 1 solvers sample q(t) at t = k dt)."""
    base = name[:-5] if name.endswith("_half") else name
    t, q = heat(base)
    dt, n, _ = grid(name)
    return np.interp(dt * np.arange(1, n + 1), t, q)


# ------------------------------------------------------------------------------------------------------------
# kernels and the convolution (D29)
# ------------------------------------------------------------------------------------------------------------
def load_kernel(path, keys=None):
    z = np.load(path, allow_pickle=False)
    out = {"meta": json.loads(str(z["meta"])), "path": path}
    for k in z.files:
        if k != "meta" and (keys is None or k in keys):
            out[k] = z[k]
    return out


def conv(S, S_inf, q):
    """Rise at steps 1..n for heat q at steps 1..n (q(0) = 0), by the impulse form
        T(k) = sum_{m=1..k} h(k - m + 1) q(m),   h(l) = S(l) - S(l - 1),  S(0) = 0,  S(l > K) = S_inf,
    which is the step-response sum of D29 summed by parts; evaluated by FFT along time.
    S: (K, ...) step responses, S_inf: (...), q: (n,) or (n, J) where S is (K, O, J)."""
    S = np.asarray(S, dtype=np.float64)
    S_inf = np.asarray(S_inf, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    h = np.concatenate([S[:1], np.diff(S, axis=0), (S_inf - S[-1])[None]], axis=0)       # lags 1..K+1
    n = q.shape[0]
    if S.ndim == 2:                                  # (K, O), q (n,)
        c = fftconvolve(h, q[:, None], axes=0)
        return c[:n]
    if S.ndim == 3:                                  # (K, O, J), q (n, J)
        c = fftconvolve(h, q[:, None, :], axes=0)
        return c[:n].sum(axis=2)
    if S.ndim == 1:
        c = fftconvolve(h, q)
        return c[:n]
    raise ValueError(S.shape)


def conv_direct_last(S, S_inf, q):
    """Direct step-response form at the last step only (a cross-check of conv on one row)."""
    S = np.asarray(S, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    n, K = len(q), S.shape[0]
    dq = np.diff(np.concatenate([[0.0], q]))
    tot = 0.0
    for m in range(1, n + 1):
        lag = n - m + 1
        tot = tot + (S[lag - 1] if lag <= K else S_inf) * dq[m - 1]
    return tot


# ------------------------------------------------------------------------------------------------------------
# runs
# ------------------------------------------------------------------------------------------------------------
def load_run(path):
    z = np.load(path, allow_pickle=False)
    out = {k: z[k] for k in z.files if k != "meta"}
    out["meta"] = json.loads(str(z["meta"])) if "meta" in z.files else {}
    return out


def trap(y, t):
    y = np.asarray(y, dtype=float)
    t = np.asarray(t, dtype=float)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(t)))


def pwl_average(times, values, t_end):
    """Average over [0, t_end] of the piecewise-linear function through (times, values), times starting at 0;
    past the last time it is held at the last value. values may be 2-D (time first)."""
    times = np.asarray(times, dtype=float)
    values = np.asarray(values, dtype=float)
    if t_end <= times[-1]:
        j = int(np.searchsorted(times, t_end, side="left"))       # times[j-1] < t_end <= times[j]
        if j < len(times) and abs(times[j] - t_end) < 1e-12:
            tt, vv = times[:j + 1], values[:j + 1]
        else:
            frac = (t_end - times[j - 1]) / (times[j] - times[j - 1])
            v_end = values[j - 1] + frac * (values[j] - values[j - 1])
            tt = np.append(times[:j], t_end)
            vv = np.concatenate([values[:j], v_end[None] if values.ndim > 1 else [v_end]], axis=0)
    else:
        tt = np.append(times, t_end)
        vv = np.concatenate([values, values[-1:]], axis=0)
    d = np.diff(tt)
    if vv.ndim == 1:
        return float(np.sum(0.5 * (vv[1:] + vv[:-1]) * d) / t_end)
    return (0.5 * (vv[1:] + vv[:-1]) * d[:, None]).sum(axis=0) / t_end


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def fnum(x):
    if x is None or x == "":
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if x in ("True", "False"):
        return x == "True"
    try:
        return float(x)
    except ValueError:
        return x


def rel(a, b):
    """Relative difference of a (mine) from b (stored), or the absolute one when b is zero."""
    if a is None or b is None:
        return None
    return abs(a - b) / abs(b) if b != 0 else abs(a - b)


def dump(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))


def mem_note():
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmHWM"):
                    return line.split(":")[1].strip()
    except OSError:
        pass
    return "?"
