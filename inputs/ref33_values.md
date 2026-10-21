# The paper's ref. 33: what it gives (Stage 2, A1)

Source: Yang, X. and Tartakovsky, D. M. Estimation of battery core temperature from indirect observations and models with error. J. Power Sources 664 (2026) 238948. https://doi.org/10.1016/j.jpowsour.2025.238948. Read from the publisher's PDF supplied by the author (9 pages, SHA-256 7a18214ff2bb68cb36579130f48b23a9dfa96cffcf79225beefd3dade7636758; not redistributed). No supplementary file was supplied or is referred to for these values.

## The cell
The 5 Ah LG INR 21700 M50, NMC811 against graphite-SiOx (Section 4, p. 3). The roll has 23 revolutions, so the cell comprises 2 x 23 - 1 = 45 single layers in parallel (p. 3, citing its ref. 41). The same cell as Stage 1.

## The thermal model (Appendix B, p. 7)
- Eq. B.1: one-dimensional transient conduction in the radial coordinate r_b on (0, R_b): rho c dT/dt = (1/r_b) d/dr_b (lambda r_b dT/dr_b) + Q_tot. Each discretised point is one single layer.
- Eq. B.3: rho and c are thickness-weighted (c also density-weighted) over the five layer components, and lambda = L_cell / sum(L_i / lambda_i), the series mean across the layers.
- Eq. B.4: zero flux at r_b = 0 and convection with coefficient h to the ambient at R_b. No axial conduction, no end cooling, no tabs.
- This is the model Stage 1 assumed for the multi-unit paper (D2). The stop condition of the brief is not met.

## Heat generation (Eq. B.2, p. 7)
The layer average over the electrodes and separator of electrolyte Ohmic, solid Ohmic, entropic (reversible) and reaction (irreversible) heat. The current collectors' heat is neglected. There is no heat of mixing, as in Stage 1's registered heat.

## The thermal values (Table 1, p. 4)
| Quantity | Ref. 33 | Kind | Stage 1 (O'Regan et al. 2022) | Ratio |
|---|---|---|---|---|
| Volume-averaged thermal conductivity lambda | 0.62 W/(m K) | fitted | 1.2251 W/(m K) across the layers | O'Regan / ref. 33 = 1.98 |
| Volume-averaged thermal diffusivity | 1.80e-7 m2/s | fitted | 4.95e-7 m2/s (1.2251 / 2.476e6) | 2.75 |
| Volumetric heat capacity rho c | 3.444e6 J/(m3 K), computed here as lambda over the diffusivity | follows from the two fitted values | 2.476e6 J/(m3 K) | ref. 33 / O'Regan = 1.39 |
| Heat transfer coefficient h | 29.56 W/(m2 K) | fitted to its experiment | the multi-unit paper uses 400 | not used here |
| Conductivity along the layers | not given (the model has no axial direction) | | 25.092 W/(m K) | |

- Kind. Table 1 marks these three values as "tuned in Section 4.1 via model calibration". Section 4.1 (pp. 3 and 4) fits them, with four electrochemical values, by particle swarm optimisation (pymoo) to the 1C discharge data of its ref. 47 (Sarmadian et al.): terminal voltage, surface temperature and core temperature at 25 C. They are fitted values, not measurements.
- Density. Eq. B.3 with Table 1's thicknesses (12, 85.2, 12, 75.6 and 16 um for the negative collector, negative electrode, separator, positive electrode and positive collector) and densities (8933, 2060, 1548, 3699 and 2702 kg/m3) gives 3108 kg/m3 (computed here). The component specific heats are not listed: Table 1 refers its untuned values to its ref. 46, which is O'Regan et al. 2022.
- Temperature dependence. None for the thermal values; Table 1's caption gives Arrhenius dependence only to four electrochemical values.

## The electrochemical set (Table 1, p. 4; Appendix A, pp. 6 and 7)
- Untuned values, "from [46]", that is O'Regan et al. 2022: the five thicknesses, the particle radii (5.86 and 5.22 um), the densities, the porosities (0.25 and 0.335), the maximum concentrations (29 583 and 51 765 mol/m3), the initial concentrations (28 866 and 13 975 mol/m3; electrolyte 1000 mol/m3), the electrode conductivities (215 S/m; 0.85 S/m at 25 C) and the operating temperature 25 C. These are the values of PyBaMM's ORegan2022 set (checked by src/stage2_ref33.py).
- Fitted at 25 C: the reaction rate constants k0,neg = 1.15e-11 and k0,pos = 6.70e-11 m^2.5/(s mol^0.5), and the particle diffusivities D_s,neg = 6.50e-14 and D_s,pos = 5.17e-15 m2/s. They follow Arrhenius laws with the activation energies of its ref. 46 (Table 1 caption).
- Eq. A.3 gives the Butler-Volmer current as 2 F k0 c_s,max (c_e xi (1 - xi))^(1/2) sinh(...), with xi the surface stoichiometry; the square root is required by the units of k0. The exchange-current density is therefore F k0 c_s,max (c_e xi (1 - xi))^(1/2).
- Complete enough to run: yes, as PyBaMM's ORegan2022 set with the two exchange-current densities and the two particle diffusivities replaced by the forms above (D17). The open-circuit potentials, entropic coefficients and electrolyte properties are those of ref. 46, which ORegan2022 holds.
