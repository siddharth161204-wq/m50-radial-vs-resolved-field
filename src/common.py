"""Constants shared by every model in this study. Each value is traced in DECISIONS.md.

Geometry, boundary data and properties are read here once, so the one-dimensional model, the three-dimensional
cell and the DFN heat runs cannot drift apart.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUTS = os.path.join(ROOT, "inputs")
RESULTS = os.path.join(ROOT, "results")

# ---- boundary data from Yang, Cui and Tartakovsky (2026), J. Electrochem. Soc. 173, 050520, p. 3 (D2) ----
H_PAPER = 400.0                     # W/(m2 K), the paper's convection coefficient
H_AIR = 25.0                        # W/(m2 K), boundary condition (d) of the brief, an air-cooled module
AMBIENTS_C = (-5.0, 25.0)           # C, the paper's two ambient temperatures (initial temperature equal to ambient)
C_RATES = (1.25, 2.0, 3.0)          # the brief's three discharge rates (the paper's Fig. 4 and Fig. 5 rates)
NOMINAL_AH = 5.0                    # A h, Chen2020 "Nominal cell capacity [A.h]"

# ---- geometry (D5) ----
CELLS = {
    # the two-cell study's cylinder (its D9): 21.1 mm by 70.1 mm, the paper's 45 units
    "21700": {"R": 21.1e-3 / 2, "H": 70.1e-3, "n_units": 45},
    # the paper's 4680 form factor (46 mm by 80 mm) and its "approximately N_unit = 111" (p. 3)
    "4680": {"R": 46.0e-3 / 2, "H": 80.0e-3, "n_units": 111},
}

# ---- the can (D4): the two-cell study's 0.25 mm steel shell, its D10 ----
T_CAN = 0.25e-3                     # m
K_CAN = 15.0                        # W/(m K), in-plane
C_CAN_21700 = 9e-3 * 500.0          # J/K, 9 g at 500 J/(kg K), spread over the 21700's whole outer area


def outer_area(R, H):
    return 2 * math.pi * R * H + 2 * math.pi * R ** 2


def lateral_area(R, H):
    return 2 * math.pi * R * H


def end_area(R):
    return math.pi * R ** 2


def volume(R, H):
    return math.pi * R ** 2 * H


C_CAN_PER_AREA = C_CAN_21700 / outer_area(CELLS["21700"]["R"], CELLS["21700"]["H"])   # J/(m2 K), same for the 4680

# ---- tabs for boundary condition (c) (D9): the two-cell study's patches (its D7) and per-strip nickel value (D24) ----
R_TAB_DISC = 4.0e-3                 # m, positive strip: disc of 8 mm diameter at the centre of the cap
R_TAB_ANN_IN = 7.5e-3               # m, negative strip: annulus from 15 mm diameter to the rim of the base
G_STRIP = 90.0 * (0.2e-3 * 8e-3) / 23.1e-3   # W/K per strip: nickel 0.2 mm by 8 mm over the 23.1 mm pitch


def roll_properties():
    """The registered roll properties (D4), computed by inputs/properties.py from PyBaMM's ORegan2022 set."""
    with open(os.path.join(INPUTS, "properties.json")) as f:
        p = json.load(f)
    return p


def cell_constants(cell, props=None):
    """Derived constants of one geometry: volumes, areas and heat capacities."""
    props = props or roll_properties()["registered"]
    g = CELLS[cell]
    R, H = g["R"], g["H"]
    rho_cp = props["rho"] * props["cp"]
    V = volume(R, H)
    A_out = outer_area(R, H)
    c = {
        "R": R, "H": H, "n_units": g["n_units"], "V": V, "A_outer": A_out, "A_lateral": lateral_area(R, H),
        "A_end": end_area(R), "rho_cp": rho_cp, "k_across": props["k_across"], "k_along": props["k_along"],
        "C_roll": rho_cp * V, "C_can": C_CAN_PER_AREA * A_out, "C_can_lateral": C_CAN_PER_AREA * lateral_area(R, H),
        "c_can_per_area": C_CAN_PER_AREA, "k_can_t": K_CAN * T_CAN,
    }
    c["C_total"] = c["C_roll"] + c["C_can"]
    return c
