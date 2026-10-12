"""Auditor's own axisymmetric check: share of heat leaving through the ends vs the side in case (b).
Vertex-centred finite volumes on a uniform (r, z) grid, anisotropic roll, can as boundary capacity and in-plane
conduction, convection h on side and ends, backward Euler at ~1 s, heat q(t) from the study's DFN series."""
import sys, math, numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
heat_csv, R, H, Nr, Nz, ends_cooled = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6] == "1"
cap_ends, cond_ends = sys.argv[7] == "1", sys.argv[8] == "1"
rho_cp = 2938.6852248394002 * 842.3972520912723
kr, kz = 1.225063080816923, 25.091576331499663
c_can = 4.5 / (2 * math.pi * 0.01055 * 0.0701 + 2 * math.pi * 0.01055 ** 2)
kt = 15.0 * 0.25e-3
h = 400.0
Tamb = -5.0 if "m5C" in heat_csv else 25.0
d = np.loadtxt(heat_csv, delimiter=",", skiprows=1)
t_s, Q21 = d[:, 0], d[:, 3]
V21 = math.pi * 0.01055 ** 2 * 0.0701
q_of = lambda t: np.interp(t, t_s, Q21 / V21)
r = np.linspace(0, R, Nr + 1); z = np.linspace(0, H, Nz + 1)
dr, dz = R / Nr, H / Nz
rf = np.concatenate([[0.0], 0.5 * (r[:-1] + r[1:]), [R]])          # cell faces in r
Ar = math.pi * (rf[1:] ** 2 - rf[:-1] ** 2)                         # annular area of node i
hz = np.full(Nz + 1, dz); hz[0] = hz[-1] = dz / 2                   # node extent in z
idx = lambda i, j: j * (Nr + 1) + i
N = (Nr + 1) * (Nz + 1)
rows, cols, vals = [], [], []
def link(a, b, g):
    rows.extend([a, b, a, b]); cols.extend([a, b, b, a]); vals.extend([g, g, -g, -g])
for j in range(Nz + 1):
    for i in range(Nr):
        link(idx(i, j), idx(i + 1, j), kr * 2 * math.pi * rf[i + 1] * hz[j] / dr)
for j in range(Nz):
    for i in range(Nr + 1):
        link(idx(i, j), idx(i, j + 1), kz * Ar[i] / dz)
# can: in-plane conduction along the side and across the end discs
for j in range(Nz):
    link(idx(Nr, j), idx(Nr, j + 1), kt * 2 * math.pi * R / dz)
for jj in ((0, Nz) if cond_ends else ()):
    for i in range(Nr):
        link(idx(i, jj), idx(i + 1, jj), kt * 2 * math.pi * rf[i + 1] / dr)
K = sp.csr_matrix((vals, (rows, cols)), shape=(N, N))
Cap = np.zeros(N); Vn = np.zeros(N); Aside = np.zeros(N); Aend = np.zeros(N)
for j in range(Nz + 1):
    for i in range(Nr + 1):
        n = idx(i, j); Vn[n] = Ar[i] * hz[j]
        if i == Nr: Aside[n] = 2 * math.pi * R * hz[j]
        if j in (0, Nz): Aend[n] = Ar[i]
Cap = rho_cp * Vn + c_can * (Aside + (Aend if cap_ends else 0 * Aend))
G_side = h * Aside; G_end = h * Aend if ends_cooled else 0 * Aend
t_end = t_s[-1]; nst = int(math.ceil(t_end - 1e-9)); dt = t_end / nst
A = (K + sp.diags(Cap / dt + G_side + G_end)).tocsc(); lu = spla.splu(A)
T = np.full(N, Tamb); Eside = Eend = Egen = 0.0
for k in range(nst):
    t = (k + 1) * dt
    T = lu.solve(Cap / dt * T + (G_side + G_end) * Tamb + Vn * q_of(t))
    Eside += dt * G_side @ (T - Tamb); Eend += dt * G_end @ (T - Tamb); Egen += dt * q_of(t) * Vn.sum()
fs = G_side @ (T - Tamb); fe = G_end @ (T - Tamb)
Tc = T[idx(0, Nz // 2)]; Ts = T[idx(Nr, Nz // 2)]; Tb = T[idx(0, 0)]
print(f"R {R*1e3:.2f} mm H {H*1e3:.1f} mm grid {Nr}x{Nz} ends_cooled {ends_cooled}: core-surface {Tc-Ts:.3f} K, axial {Tc-Tb:.3f} K;"
      f" time-integrated loss: side {Eside:.0f} J, ends {Eend:.0f} J (ends {100*Eend/(Eside+Eend):.1f} %);"
      f" at end of discharge: side {fs:.3f} W, ends {fe:.3f} W (ends {100*fe/(fs+fe):.1f} %); gen {Egen:.0f} J")
