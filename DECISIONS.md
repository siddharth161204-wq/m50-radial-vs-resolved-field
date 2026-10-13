# Decisions

Every choice that the brief does not fix is recorded here in full sentences with its reason. "The brief" is the author's written plan for this study: its question, inputs, design, checks, predictions and rules. Each choice is recorded before the runs it affects, except those under the last heading, which came after the predictions were public and say so. Values come with their sources, and nothing is fitted.

## The paper and its thermal model

D1. The study compares a one-dimensional radial cell model with a resolved three-dimensional cell. Both models get the same heat, and the comparison is made under the boundary data of the paper the model comes from. The study computes temperature fields only and does not rerun any electrochemistry.

D2. The paper is Yang, X., Cui, Y. and Tartakovsky, D. M., Electrochemical Models of Multi-Unit Lithium Batteries Under Thermal Gradient, J. Electrochem. Soc. 173 (2026) 050520, doi:10.1149/1945-7111/ae4b6d. Its thermal submodel is transient radial conduction, Eq. 2 on p. 2: rho c dT/dt = (1/r) d/dr (lambda r dT/dr) + Q on 0 < r < R_b. The volume-averaged density, specific heat and conductivity of the five layers of a unit come from Eq. 3 on p. 3, and the conductivity is the series mean across the layers. Eq. 4 on p. 3 sets zero flux at r = 0 and convection with coefficient h to the ambient at R_b. Each discretised point is one unit (p. 2). The 21700 holds 45 units (p. 3). The 4680, 46 mm by 80 mm, holds about 111 units, with the 21700's unit parameters and the same hollow core, contact layer and casing (p. 3). The paper uses h = 400 W/(m^2 K) and ambient temperatures of minus 5 C and 25 C (p. 3). It names a hollow core but gives no radius, and Eq. 4 puts the zero-flux condition at r = 0, so the one-dimensional domain here is the solid cylinder, as the brief allows. On the thermal properties the paper says this (p. 3): "Its thermal properties are reported in Ref. 33." Ref. 33 is Yang, X. and Tartakovsky, D. M., Estimation of battery core temperature from indirect observations and models with error, J. Power Sources 664 (2026) 238948, doi:10.1016/j.jpowsour.2025.238948 (the DOI comes from Crossref). Its full text could not be obtained for this study, so the difference between its properties and the ones used here is not stated. D16 records what its available parts say.

## Heat generation

D3. The heat comes from PyBaMM 26.9.0.0, Doyle-Fuller-Newman model, with the parameter set Chen2020 as the brief names it (Chen et al., J. Electrochem. Soc. 167 (2020) 080534, doi:10.1149/1945-7111/ab9050).
- Options: "thermal": "lumped" and "use lumped thermal capacity": "true". The lumped capacity is the total heat capacity of this study's 21700 (65.18 J/K, D4), so the DFN's cell warms with the same thermal mass as the cells it feeds.
- Cooling: h = 400 W/(m^2 K) on the lateral area only (4.647e-3 m^2), the paper's boundary condition.
- Temperatures: the initial temperature equals the ambient.
- Discharge: at 1.25C, 2C and 3C of the set's nominal 5 A h (6.25, 10 and 15 A), from initial_soc = 1 (the 4.2 V upper cut-off) to the set's lower cut-off of 2.5 V, with output every second.
- Solver: IDAKLU with rtol 1e-6 and atol 1e-8.
- What is recorded: the heat is PyBaMM's "Total heating [W]", the heat per unit electrode-pair area times the electrode area of 0.1027 m^2. Recorded with it are the duration, the capacity, the lumped temperature, and the first time the voltage reaches 2.6 V, the cut-off the paper uses for its training data (p. 2).
- How Chen2020 behaves: its entropic coefficients are zero, so there is no reversible heat. Its only temperature dependence is in the two exchange-current densities (Arrhenius, 35 and 17.8 kJ/mol). Its diffusivities and its electrolyte conductivity do not depend on temperature.
- The brief describes the Chen 2020 set this way: "the one already used here". The author's preceding study, the thermal lever (github.com/siddharth161204-wq/thermal-lever-duplicate-floor), in fact used ORegan2022, which is Chen 2020's electrochemistry plus the temperature dependence of diffusion, conduction and kinetics measured by O'Regan et al. (2022), and their entropic heat. Chen2020 is registered because the brief names it. ORegan2022 is run with identical settings as a declared secondary input and is reported but never scored.
- The registered heat is PyBaMM's default "Total heating [W]": Ohmic, irreversible reaction and reversible heat. It leaves out the heat of mixing, which PyBaMM includes only on request. The paper computes its heat as its ref. 24 does, and this study did not read which terms that includes.
- For Chen2020 the heat of mixing is large. Switched on, it adds 1,600 to 2,540 J to a discharge, 36 to 54 % of the registered heat (38 % at 2C and minus 5 C), because the set's slow diffusion in the positive particles holds steep concentration gradients. It is run as a declared secondary input, since the fields scale nearly in proportion to the heat.
- Checks of the registered heat: in every run the Ohmic plus irreversible heat equals I (U_p,w - U_n,w - V) within 0.12 %. That is the model's power identity, with the open-circuit potentials at the particle surfaces weighted by the local reaction current. With the heat of mixing on, the heat reaches 98 to 99 % of I (U_bulk - V) at 1.25C and 2C, and the rest remains in the gradients at cut-off.
- Before this file was written, a quick test of both sets ran with these settings, together with one run with the heat of mixing at 2C and minus 5 C. No thermal model was run. In that test ORegan2022 at minus 5 C ended after 166 s at 2C and 61 s at 3C.

## Properties and geometry

D4. One property table serves every thermal model. It is the jelly roll of O'Regan et al., Electrochim. Acta 425 (2022) 140700, doi:10.1016/j.electacta.2022.140700, through PyBaMM's ORegan2022 set, computed as in the two-cell study (Satte 2026, doi:10.5281/zenodo.23253738, its inputs/oregan2022_properties.py, copied unchanged as inputs/twocell_oregan2022_properties.py). The values are evaluated at 25 C, the set's reference temperature, and held constant (inputs/properties.py, inputs/properties.json):
- density 2938.7 kg/m^3
- specific heat 842.4 J/(kg K)
- conductivity across the layers 1.2251 W/(m K)
- conductivity along the layers 25.092 W/(m K)

The same computation gives 1.1711 W/(m K) and 707.0 J/(kg K) at minus 5 C (4.4 % and 16 % lower). The polynomial fits carry no stated range of validity in the set, so minus 5 C may lie outside the measurements. Constant properties match the paper's constant unit properties (Eq. 3). Because the cells stay within a few kelvin of ambient at h = 400, one table keeps the study to one cell. The one-dimensional model is rerun with the minus 5 C row for the minus 5 C runs to show how much the table matters.

The can is the two-cell study's (its D10): a 0.25 mm steel shell on every outer surface, with in-plane conductivity 15 W/(m K) and 9 g at 500 J/(kg K) spread over the 21700's outer area (841.7 J/(m^2 K)). The two-cell study states these values without a primary source. The 4680 takes the same shell per unit area, as the paper sets its casing to the 21700's. The roll fills the cylinder, as in the two-cell cell (its D9: no hollow core, headspace or cap assembly resolved). The 21700 therefore holds 60.68 J/K in the roll and 4.50 J/K in the can (65.18 J/K in all), and the 4680 holds 329.13 and 12.53 J/K. The two-cell study used 1.3 W/(m K) and 61.75 J/K, values chosen for its thermal-runaway range. This study runs near 25 C and minus 5 C, so the 25 C values are used.

D5. The 21700 is the two-cell study's cylinder, 21.1 mm by 70.1 mm (R = 10.55 mm). The 4680 is 46 mm by 80 mm (R = 23 mm, the paper's form factor). The units are equal-thickness annuli over 0 < r < R: 45 of 0.2344 mm in the 21700 and 111 of 0.2072 mm in the 4680. The paper's one-dimensional model spans 0 < r < R_b with one point per unit, and the brief asks for equal-thickness annuli.

D6. The heat is applied uniformly per unit volume of the cylinder, q(t) = Q(t) / (pi R^2 H), and it is the same in the one- and three-dimensional models. Between the one-second DFN outputs it is interpolated linearly. The 4680 takes the 21700's q(t) at the same rate and ambient. The same C-rate means the same current per unit electrode area, and the paper gives the 4680 the 21700's units. Its total heat is therefore 5.42 times the 21700's, the ratio of the volumes, and its discharge lasts as long.

## The models

D7. The one-dimensional model solves the paper's Eq. 2 and Eq. 4 with the properties of D4:
- Discretisation: P1 finite elements in r with the weight 2 pi r, 20 elements per unit, a lumped (row-sum) capacity, and backward Euler on the same time steps as the three-dimensional model.
- Boundary conditions: zero flux at r = 0 and convection at R.
- Unit temperature: the annulus average of the field, integrated exactly.
- The can: the lateral share of its heat capacity is carried as a surface capacity at R (841.7 J/(m^2 K)), so the one-dimensional model and the three-dimensional cell hold the same materials at mid-height. This is the "one-dimensional model" of every comparison.
- The paper's form without the can is also run, and its difference is reported.

D8. The three-dimensional cell is the two-cell study's scikit-fem cell. Its mesh generator is copied unchanged as inputs/twocell_mesh_cell2.py, and its solver is inputs/twocell_resolved_cell2.py, of which src/cell3d.py keeps the construction:
- a half cylinder with zero flux on the plane of symmetry, made of P1 tetrahedra
- the roll's conductivity tensor k_along I + (k_across - k_along) e_r e_r^T, so that conduction along the layers acts axially and around the circumference (replaced by D13 after V1: around the circumference the across-layer value is used)
- the can as a shell on every outer surface, carrying in-plane conduction k t and its heat capacity
- a lumped capacity and backward Euler time stepping

What changes:
- the properties of D4
- a uniform volumetric source, distributed by nodal volume
- the boundary conditions of D9, with no neighbour, air gap or radiation, because the paper's h is its total coefficient
- a step of t_end / ceil(t_end / 1 s), so the last step lands on the end of discharge

The 21700 mesh is the two-cell mesh at refine 1 (39,990 nodes). The 4680 mesh follows the same rules. Its interior rings are spaced about 0.68 mm apart, its rings near the wall sit at the 21700's distances from the wall (2.5, 2.0, 1.55, 1.15, 0.82, 0.55, 0.35, 0.2, 0.09 and 0 mm), and its segments and axial layers follow the same rules. SuperLU solves the 21700. Preconditioned conjugate gradients with smoothed-aggregation AMG (pyamg), to a relative residual of 1e-12 and starting from a linear extrapolation of the two previous steps, solve the larger meshes.

D9. Boundary conditions:
- (a) Convection h = 400 on the lateral surface; the end faces adiabatic; the can on every surface.
- (b) Convection h = 400 on every outer surface.
- (c) As (b), plus two strips to busbars held at the ambient temperature. They sit on the two-cell study's patches (its D7): the positive strip on the 8 mm disc at the centre of the cap (z = H), the negative strip on the base annulus from 15 mm diameter to the rim (z = 0). Each strip is a conductance of 6.23 mW/K, the two-cell study's per-strip nickel value (its D24: 90 W/(m K) times 0.2 mm by 8 mm over the 23.1 mm pitch), applied as a Robin condition with coefficient G divided by the patch area. The patches keep their convection.
- (d) As (b) with h = 25 W/(m^2 K).

The 4680 runs (a) and (b). Every case runs at all six heat inputs, and the heat is the DFN's at h = 400 in every case, as the brief holds it equal.

The roll's end faces touch the can's end caps directly, because the two-cell cell has no insulating discs or headspace. The path to the ends is therefore as conductive as this cell allows: the end cooling of (b) is an upper bound, and so is the end caps' effect in (a).

D10. Outputs. Each run is evaluated at the end of discharge (the DFN's cut-off time) and at the time of the largest mid-height core-to-surface difference, found from that difference recorded at every step. At each time:
- Core-to-surface difference: T(r = 0, z = H/2) minus the mean temperature of the surface ring at z = H/2.
- Axial difference: T(0, H/2) minus T(0, 0), and T(0, H/2) minus T(0, H), with z = 0 at the base. The larger is "the axial difference".
- Hottest point: its radius and height.
- Unit averages: each unit's average temperature over its annulus and the full height. It is sampled from the finite-element field on 10 Gauss radii per unit, every 0.1 mm in height and at 4 angles, with the weight r.
- Comparison with the one-dimensional model: the largest absolute difference between the two unit temperatures, the number of units that differ by more than 1 K, and the unit-to-unit spread (hottest minus coldest unit) in both models.

## Verification

D11. The checks:
- V1, the bug check, compares like with like. With boundary condition (a), the three-dimensional field is exactly one-dimensional only if the can's end caps neither conduct nor store heat. V1 therefore runs the cell with the can on the lateral surface only. Its mid-height radial profile must match the one-dimensional model, at the same time and the same radii, within 1 % of the one-dimensional core-to-surface difference, at both output times and for all six heat inputs.
- (a) with the full can is then compared with the one-dimensional model as the brief's verification row. Any excess over 1 % there is reported as the end caps' effect, not treated as a bug, because the equivalence run has already tested the solver.
- V2: the energy account of every three-dimensional run (heat stored plus heat lost minus heat generated) closes to round-off, within 1e-9 of the heat generated.
- V3: one mesh refinement (every spacing halved, 297,057 nodes) changes the core-to-surface difference by less than 5 % for (a) and (b) at 2C and minus 5 C. The axial difference and the unit averages are reported alongside.
- V4: if the paper's PDF becomes available, its Fig. 5 (p. 5) is digitised and compared with the one-dimensional model.

## Registration

D12. The predictions are the brief's P1 to P5. Each has a scoring rule in predictions.md, committed and pushed to the public repository before any three-dimensional field is computed. The registered results use the Chen2020 heat (without the heat of mixing) and the 25 C properties. The secondary results use the Chen2020 heat with the heat of mixing, the ORegan2022 heat, and the minus 5 C properties for the minus 5 C runs. They are reported beside the registered ones without being scored.

## Added after the predictions were public

D13. V1 failed as first run and was fixed before any other case ran. The equivalence run at 2C and minus 5 C (the two-cell study's conductivity tensor, in which the along-layer value also acts around the circumference) gave a mid-height core-to-surface difference 1.7 % below the one-dimensional model's (4.192 against 4.264 K). The deficit was largest at the axis and fell to zero at the surface.

The cause is a discretisation error, not physics. Near the axis the two-cell mesh has few, wide triangles that are not aligned with the radius: the first ring carries 4 segments over half a circle. On those triangles the finite-element gradient of a radial field has a spurious circumferential part, and a circumferential conductivity twenty times the radial one turns that part into heat flow, which makes the roll look more conductive than it is. With the circumferential conductivity set to the across-layer value, the same run matches the one-dimensional model within 0.15 % (4.270 against 4.264 K). A diagnostic run, made after the registered results and not used in them, repeats the first equivalence run with the original tensor on the mesh with every spacing halved: the deficit falls from 1.70 % to 0.51 % (4.242 K; results/fields/21700_a_eq_refine2_ktheta-along_Chen2020_m5C_2C.json, summarised in results/verification.json), as a discretisation error should.

Every field in this study is axisymmetric: a uniform source, and convection and strips that do not vary around the circumference. The circumferential conductivity therefore cannot change the exact solution, and every run uses the across-layer value for it. The conductivities that carry heat here, 1.2251 W/(m K) across the layers (radial) and 25.092 W/(m K) along them (axial), are unchanged. The first equivalence run is kept in results/fields_superseded/ for the record.

D14. Also after the predictions, in the same commit as D13, the field sampler was fixed (src/mesh.py). The outer ring of the mesh is a polygon inscribed in the circle r = R, so sample points on that circle can lie up to 2.8 micrometres outside it, and the first equivalence run stopped with an error when it sampled them. Such points are now moved along their radius onto the polygon's edge, where the finite-element field takes its boundary value. No field had been sampled before the fix, and it changes no physics.

D15. Post-hoc, not pre-registered, and prompted by an independent audit of the text: the 2C, minus 5 C case at the paper's own end of discharge, and where the heat leaves. The paper's Fig. 4d ends that discharge near 1.34 A h (multi-unit) and 1.50 A h (single-unit), read from the figure, which is 482 and 540 s at 10 A. The registered DFN run continues to 4.74 A h (1706.7 s). src/posthoc_matched_time.py re-solves (a) and (b) for both cells on the registered step grid, records the fields at those two times, and records the heat removed through each surface. It writes results/posthoc_matched_time.json. The registered results are unchanged.

D16. After the predictions and after v1.0.0, the author supplied the parts of the paper's ref. 33 that its publisher's page shows without a subscription: the abstract, the introduction and the opening lines of each section (Yang, X. and Tartakovsky, D. M., Estimation of battery core temperature from indirect observations and models with error, J. Power Sources 664 (2026) 238948). They say this:
- It estimates the core temperature of a cylindrical cell from its surface temperature and terminal voltage with an ensemble Kalman filter that also learns the forecast model's bias.
- The forecast model couples a pseudo-two-dimensional electrochemical model with a one-dimensional thermal model, and its introduction says that the model is "parameterized by fitting the model prediction to 1-C discharge data".
- The cell is the same as here: the 5 Ah LG INR 21700 M50, NMC811 against graphite-SiOx.
- Its estimates are compared with published core-temperature measurements at several discharge rates.

The thermal property values, and which parameters the fit sets, are in the body of the paper, which was not available. The difference from this study is therefore stated in kind: the paper's properties come from a model of the same cell fitted to discharge data, and this study's from O'Regan et al.'s measurements of that cell (D4). Whether the properties account for the factor of 1.7 to 3.6 between the paper's unit differences and this study's (V4) cannot be told from these parts. No input, code or result changed. The note's second limit, README and this log say this from v1.0.1.
