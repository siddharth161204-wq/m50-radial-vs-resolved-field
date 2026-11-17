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

## Stage 2 (after v1.0.1): which of conductivity or heat makes the gap, and a one-term end correction

D17. Part A, written after reading ref. 33 (inputs/ref33_values.md) and before any Stage 2 computation.
- Ref. 33's thermal model is the radial model Stage 1 assumed (D2), so Stage 2 proceeds. Its thermal values are fitted to one 1C discharge, not measured: lambda = 0.62 W/(m K) and rho c = 3.444e6 J/(m3 K) (lambda over its fitted diffusivity). Its fitted h (29.56 W/(m2 K)) belongs to its experiment; the multi-unit paper's h = 400 is kept.
- A2, the property part. Stage 1's radial model (src/radial1d.py, unchanged) with lambda = 0.62 W/(m K) across the layers and rho c = 3.444e6 J/(m3 K), the can and h = 400 unchanged, and the registered Chen2020 heat unchanged. The comparison conditions are V4's: 1.25C and 2C at 25 C at the end of discharge; 2C at minus 5 C at the paper's own end of discharge, 482.4 and 540.0 s (D15); and the 4680 at 2C and minus 5 C at the end of discharge. The factor is the paper's innermost-unit difference (V4: 2.88, 5.94, 11.54 and 37.53 K) over this model's innermost-minus-outermost unit difference.
- A3, the heat part. The ref. 33 set is PyBaMM's ORegan2022 with two changes: each exchange-current density is F k0 c_s,max (c_e xi (1 - xi))^(1/2) times O'Regan's Arrhenius factor (40.0 and 24.01 kJ/mol), and each particle diffusivity is ref. 33's constant value times O'Regan's Arrhenius factor (17.39 and 12.05 kJ/mol). Every other value is ORegan2022's, and the values Table 1 lists are checked against it. The DFN runs as in Stage 1 (lumped thermal model, h = 400 on the side, 1 s output, cut-off 2.5 V with the time at 2.6 V recorded), from Table 1's initial concentrations, with the roll's heat capacity at ref. 33's rho c plus the can. Its heat is compared with Chen2020's over 0 to 482.4 s and 0 to 540.0 s at minus 5 C and over the whole discharge at 25 C, and the radial model is rerun with that heat and ref. 33's properties.
- A4, the split. At each condition the factor is the product of the property ratio (this model's unit difference with ref. 33's properties over that with O'Regan's, both with the Chen2020 heat), the heat ratio (with ref. 33's heat over with the Chen2020 heat, both with ref. 33's properties) and the remainder (the paper's value over this model with ref. 33's properties and heat).
- The heat of mixing stays a declared secondary input, as in Stage 1. Stage 1's code and results are not edited; Stage 2 writes new files only.

D18. Part B, the end correction, derived before any code. In case (b) the roll's end faces lose heat to the ambient through h. Take one radius r, the roll height L (70.1 mm in the 21700, 80 mm in the 4680), the along-layer conductivity k_z (25.092 W/(m K)) and two assumptions: the heat generated is uniform along the height, and the axial temperature profile at each radius is therefore parabolic and symmetric about mid-height. With z measured from mid-height, T(z) = T_c - Delta (2z/L)^2, so the axial mean is T_bar = T_c - Delta/3, the end-face temperature is T_c - Delta, and the conductive flux through each end face is 4 k_z Delta / L = 6 k_z (T_bar - T_face) / L. In series with h at the face, each end conducts h_e (T_bar - T_amb) per unit area, with h_e = 1 / (1/h + L / (6 k_z)). Two ends over the height L remove beta (T_bar - T_amb) per unit volume, with beta = 2 h_e / L. The one-dimensional radial equation for the axially averaged temperature gains the sink -beta (T - T_amb); nothing is fitted. The axial difference at radius r, centre to end face, follows as Delta = h_e (T - T_amb) L / (4 k_z) = beta (T(r) - T_amb) L^2 / (8 k_z).
- h is applied as case (b) applies it: the roll's end faces touch the can's end caps, with no headspace. The caps' normal resistance, 0.25 mm over 15 W/(m K) = 1.7e-5 m2 K/W, is 0.7 % of 1/h at h = 400 and is neglected. The caps' in-plane conduction and their heat capacity are not represented.
- Values: in case (b), h = 400 gives h_e = 337.2 W/(m2 K) and beta = 9620 W/(m3 K) in the 21700, and 329.9 W/(m2 K) and 8247 W/(m3 K) in the 4680. In case (d), h = 25 gives 24.71 W/(m2 K) and 705 W/(m3 K) in the 21700.
- Implementation (src/stage2_correction.py, a subclass of Stage 1's model, which is not edited): the sink is lumped on the same nodal volumes as the source and treated implicitly, like the lateral convection. The unit temperatures are annulus averages of the axially averaged field, which is what the resolved annulus averages over the full height measure. Same properties, heat, can and time grid as Stage 1.
- Checks: V1, beta = 0 reproduces Stage 1's radial results exactly; V2, generation equals lateral loss plus end sink plus storage within 1e-9 of the generation; V3, the steady solution of the code matches the analytical one, theta(r) = q/beta (1 - h I0(m r) / (k m I1(m R) + h I0(m R))) with m = (beta/k)^(1/2), at h = 400 for one case; V4, the resolved cell's share of heat through the ends comes from the heat removed through each surface (D15 and src/stage2_split.py), not from the correction.
- B2 compares the corrected model with the resolved cell in case (b) (both cells, h = 400) and case (d) (21700, h = 25) at the six registered heats. B3 runs it with ref. 33's properties at the paper's comparison conditions (D17).

## Stage 3 (after v1.1.0): the core-temperature estimator of ref. 33 against the resolved cell

D19. A1, the estimator as ref. 33 states it (Yang and Tartakovsky, J. Power Sources 664 (2026) 238948; the PDF of Stage 2, SHA-256 7a18214f...), recorded before any Stage 3 code.
- Forecast model (Eqs. 3 to 6, pp. 2 and 3): the P2D electrochemical model coupled with the radial thermal model of Appendix B, discretised by finite volumes (one element per layer, N + 3 thermal elements), advanced by an implicit flow map u_k+1 = f(u_k, eps_k; p).
- Error model (Eq. 4 and Section 3, p. 3): a model error eps added to the right-hand side of each PDE, the thermal one included, so for temperature it is a heat source per element. eps_k = b_k + omega_k with omega_k ~ N(0, sigma_eps,k^2); the bias b_k is the posterior mean of eps_k and the next step's prior mean is zero ("we set b_k+1 = 0 as the initial guess"). Augmented state s = (u, eps).
- Forecast step (Eq. 7) and observation (Eq. 8): H extracts the terminal voltage and the surface temperature T^(N+2); observation noise sigma_T = 0.1 C and sigma_V = 0.001 V (Section 2, p. 2).
- Analysis (Eqs. 9a to 9c): ensemble Kalman gain from the ensemble covariance, mean update with observations averaged over N_ens realisations of the observation error, that is, perturbed observations. Algorithm 1 (p. 3): deterministic initial state (Table 1), initial errors eps_0 ~ N(0, sigma_eps^2).
- Values the paper gives: N_ens = 3000 (Section 4.2, p. 4), sigma_T = 0.1 C, sigma_V = 0.001 V.
- Values the paper does not give: sigma_eps (initial or per step), the time step, the observation interval, a learning window. Its accuracy for the core temperature is shown only in Figs. 3 and 5 (0.3C and 0.7C, against Sarmadian et al.'s measured core temperature), with no number in the text.
- Eq. 7 as printed draws eps_k+1 as fresh noise after the forecast that used eps_k, so eps_k+1 never correlates with the surface reading and nothing is learned. With the author's agreement (27 October), it is read as the error drawn for the interval being assimilated: drawn with zero mean at the start of the interval, applied as a heat source over the interval, updated with the state at the reading that ends it (its posterior mean is the learned error b_k), and drawn afresh with zero mean for the next interval.

D20. A2 and A3, the implementation and its open choices (src/stage3_enkf.py), recorded before the predictions; the author chose O'Regan's properties and the brackets below (27 October).
- Forecast: Stage 1's radial model with O'Regan's properties, the can, h = 400 on the side and the registered Chen2020 heat, the heat the resolved cell received, so its only error is what the radial model leaves out. Ref. 33's properties are run once as a recorded bracket (2C, minus 5 C, cooled ends, M50). The terminal voltage is not observed: neither the resolved cell nor this forecast has electrochemistry, and the heat is known exactly. The paper's per-layer error maps to one source per unit (45 in the 21700, 111 in the 4680), uniform over the unit's annulus.
- Observation: the resolved cell's mid-length surface temperature from Stage 1's archived field series (one value every 10 s, no re-solve), every 20 s registered (10 and 40 s as the interval sensitivity), plus Gaussian noise of 0.1 K, seed 20261027. The plain forecast's surface node is compared with it. For the end-corrected forecast of Stage 2, whose temperature is the axial average, the mid-length values are reconstructed with D18's parabolic profile, T_mid = T + gamma (T - T_amb) with gamma = beta L^2 / (24 k_z) (0.0785 in the 21700, 0.0877 in the 4680 at h = 400), at the surface for the observation and at the core for the estimate.
- sigma_eps, bracketed: sigma_ref = rho c sigma_T / Delta t_obs, the source that moves a unit by the paper's 0.1 K over one 20 s interval (1.238e4 W/m3), registered; 0.1 and 10 times it bracket it. The ensemble size is the paper's 3000; the initial state is the ambient temperature in every member.
- Cases: 1.25C and 2C at 25 C and 2C at minus 5 C, ends insulated (a) and cooled (b), in the 21700; 2C at minus 5 C, cooled ends, in the 4680. Methods: the forecast alone; the estimator; the estimator with Stage 2's end-corrected forecast (identical to the estimator in case (a), where beta = 0). No learning window. Errors are the ensemble-mean mid-length core against the resolved centre node at mid-length at every archived time (mean absolute error) and at the end of discharge.
- The learned error is reported as the volume-mean posterior source per interval (W/m3), beside the end sink -beta (T_mean - T_amb) of D18 evaluated on the same estimator's ensemble-mean history; both averaged over the second half of the discharge.
- Checks: V1, a truth made by the radial model itself recovered (the paper gives no number, so the number is recorded against sigma_T = 0.1 K); V2, the forecast alone equals Stage 1's radial model exactly; V3, the archived truth read by two separate routines, identical; V4, the same seed gives identical output, and sigma_eps = 0 reduces the estimator to the forecast exactly.

D21. After the Part B runs, prompted by the independent read, which found no registered value or verdict wrong; no registered number or verdict changes.
- Two fields in the stored runs were wrong and are corrected without re-running them (src/stage3_relabel.py); src/stage3_enkf.py now writes both correctly. The level label: run() overwrote it with "none" in 14 of the 40 runs; the tables and the scorecard always took the level from sigma_eps. The end sink beside the learned error in the nine insulated-ends estimator runs: model_beta evaluated it at h = 400, although beta = 0 with the ends insulated (D20), so it is 0. No prediction uses it.
- In results/stage3_errors.csv the nine insulated-ends rows of the end-corrected estimator have no run of their own: with beta = 0 that estimator is the estimator, and the rows now say so.
- "Exactly" in V2 and V4 holds to round-off: 5.6e-15 K and 8.9e-16 K.
- The sensitivities hold sigma_eps at the registered 1.238e4 W/m3 while the reading's noise or interval changes.
- The runs behind P5 (the three cooled-ends M50 cases at the registered level and at ten times it) and P7 (0.2 K noise) were run again keeping the learned error and the end sink at every reading (src/stage3_enkf.py series; results/stage3_series.json), so that their second-half means could be recomputed independently. With one BLAS thread the seven runs reproduce the stored values bit for bit; with two, a repeat of one run differs by at most 2.2e-16 K in its core history and no reported number changes.
- The removal of the end-of-discharge miss comes from the state update at each reading: the posterior error is redrawn with zero mean after each reading (D19), so the learned error is reported beside the sink, not as the correction itself.

D22. Stage 4, Part A, the unit temperatures: what the archive holds, the re-solve and the two readings. Recorded before any Stage 4 computation; the author chose the re-solve (29 October).
- Cases: (1) 21700, 2C, minus 5 C, ends cooled at h = 400 (case (b), the main case); (2) 21700, 2C, 25 C, case (b); (3) 21700, 1.25C, 25 C, case (b); (4) 21700, 2C, minus 5 C, ends insulated (case (a), the control); (5) 4680, 2C, minus 5 C, case (b). Each has the registered Chen2020 heat of its condition (results/heat/), as in Stages 1 to 3.
- Fields and archived files. The radial field T_1d: src/radial1d.py; end-of-discharge units in results/radial1d.json (registered, "Chen2020_<condition>|<cell>", end.units). The resolved field T_3d: src/cell3d.py with the settings of src/run3d.py (registered properties, refine 1, circumferential conductivity across the layers); end units in results/fields/<cell>_<case>_Chen2020_<condition>.json (end.units), the 2C, minus 5 C ones also in results/units_<cell>_<case>_2C_minus5C_end.csv. The end-corrected field: src/stage2_correction.py (Corrected, h = 400); end units in results/stage2_correction.json (B2, "<cell>_b_Chen2020_<condition>", units_corrected). With the ends insulated beta = 0, so the end-corrected field is the radial field (D18).
- What the archive lacks: every file above holds the unit temperatures at the end of discharge only (and at the largest core-to-surface difference, which is the end in these cases); none holds them over time. The brief's main reading, the time average over the discharge, therefore needs the three models run again, which the brief had ruled out. The author chose the re-solve over taking the end of discharge as the only reading. The runs (src/stage4_units.py) import Stage 1 and 2 code unchanged and use the same heat, properties, meshes and time grids, with a snapshot of every unit at the archived series times (every 10 s and the end of discharge).
- V1: the end-of-discharge units of every re-solve equal the archived ones: exactly for the direct solvers; for the 4680, whose resolved run uses Stage 1's conjugate-gradient solver (relative residual 1e-12), to that tolerance. The unit-mean offsets and the spreads, computed as Stages 1 and 2 report them (unweighted mean over units of the absolute offset from the resolved field; spread = largest minus smallest unit temperature), reproduce their registered values (results/stage2_correction.csv; Stage 1's results).
- Readings: the time average of each unit's temperature over the discharge, by the trapezoidal rule over t = 0 (the ambient temperature) and the snapshot times (registered); and the end of discharge (bracket).

D23. Stage 4, Part B, the resistance of a unit at its temperature. Fixed before the predictions.
- Model: PyBaMM 26.9.0.0, the Doyle-Fuller-Newman model with its default options, which are isothermal (the cell is held at "Ambient temperature [K]"). "Ambient temperature [K]" and "Initial temperature [K]" are both set to T. IDAKLU solver, rtol 1e-6, atol 1e-8 (as Stage 1's heat runs).
- Sets: ORegan2022 (main) and Chen2020 (bracket), both on the cell's rated 2.5 to 4.2 V window (Chen et al. 2020: "The rated capacity of the LGM50 cell between 2.5-4.2 V is cited to be 5 Ah"; O'Regan et al. 2022, supplementary Table S1: maximum charge voltage 4.2 V, cut-off voltage 2.5 V). Chen2020 already has these limits. PyBaMM's ORegan2022 places 100 % state of charge at 4.4 V, so its "Upper voltage cut-off [V]" and "Open-circuit voltage at 100% SOC [V]" are set to 4.2 V, as in the lever study (its D8 and src/lgm50_resistance.py). Stage 1's D3 describes initial_soc = 1 as the 4.2 V cut-off; for the secondary ORegan2022 heat runs PyBaMM placed it at 4.4 V. The registered Chen2020 heat is not affected; this is recorded here, and Stage 1's text is left as it is.
- State of charge: initial_soc = 1.0 (registered) and 0.5 (bracket). PyBaMM places the stoichiometries with the open-circuit voltages at the set's reference temperature (25 C), so a given state of charge is the same lithium content at every T.
- Pulse: rest for 600 s, then discharge at 1C (5 A, the nominal 5 A h of both sets) for 10 s, with output every 0.1 s in the pulse. R(T) = (V at the end of the rest minus V at the end of the pulse) / 5 A. This is the lever study's pulse procedure (its src/lgm50_resistance.py) at 1C.
- Grid: T from minus 10 C to 35 C in steps of 0.5 K (91 temperatures) for each set and state of charge. The brief's range of minus 10 to 30 C is extended to 35 C because the radial units reach 30.73 C at the end of the 2C, 25 C discharge (results/radial1d.json).
- Sensitivity: d ln R / dT at minus 5 C, 0 C and 25 C, by the central difference over plus and minus 0.5 K.
- A unit's resistance: ln R interpolated linearly between the grid points at the unit's temperature.
- ORegan2022's temperature dependence: Arrhenius terms in both exchange-current densities (40.0 and 24.01 kJ/mol, graphite and NMC), both particle diffusivities (E/R = 2092 and 1449 K, that is 17.4 and 12.0 kJ/mol) and the positive electrode's electronic conductivity (3.5 kJ/mol); the electrolyte's conductivity, diffusivity, thermodynamic factor and transference number of Landesfeind and Gasteiger 2019; and the entropic terms of both open-circuit potentials.
- Where those values were measured. O'Regan et al. 2022 was read in its ChemRxiv preprint of 17 January 2022 (doi:10.26434/chemrxiv-2022-d2q4n; the published version was not read), with its supplementary information. Its Table 2 (p. 5) gives these ranges:
  - diffusivity and its activation energy by GITT, 5 to 45 C (also p. 6);
  - exchange-current density and its activation energy by impedance, 15 to 45 C (also p. 7);
  - electronic conductivity, 15 to 35 C;
  - entropic term, minus 5 to 25 C;
  - thermal diffusivity, minus 5 to 55 C.
- Landesfeind and Gasteiger 2019 report the electrolyte functions for minus 10 to 50 C (abstract). O'Regan et al. validate the set at 0, 10 and 25 C, and write that the agreement "is worse at 0 °C, this is due to this temperature being outside the range for measured parameter values" (p. 31).
- What that means here. Minus 5 C lies below the measured range of the kinetics (15 C) and of solid diffusion (5 C). The minus 5 C cases therefore use the set's Arrhenius fits outside their data: an extrapolation of the set, not of the thermal model. The 25 C cases, with units between 25 and 31 C, lie inside every range.
- Chen2020's temperature dependence: Arrhenius terms in the two exchange-current densities only (35.0 and 17.8 kJ/mol); constant particle diffusivities; Nyman et al. 2008's electrolyte with no temperature dependence. Chen et al. 2020 (J. Electrochem. Soc. 167, 080534; the Warwick repository copy) derive the two activation energies from impedance at room temperature and at 30, 40, 50 and 60 C (section "Exchange current density"), and validate at 25 C. Minus 5 C is an extrapolation for this set as well.

D24. Stage 4, the share and the errors (Parts B2 and C). Fixed before the predictions; the author chose area weights (29 October).
- The units are equal-thickness annuli (D5). A jelly roll's electrode area per unit volume is uniform, so unit i's electrode area is proportional to its annulus's cross-section: w_i = (r_(i+1)^2 - r_i^2) / R^2, which sums to 1. The brief's statement that the areas are equal by construction does not hold for equal-thickness annuli: the outermost unit has 89 times the innermost's area in the 21700 and 221 times in the 4680. The author chose area weights over the brief's unweighted mean.
- The proxy. At a common voltage each unit's current density is proportional to 1 / R(T_i). Unit i's share, its current density over the cell's mean current density, is s_i = (1 / R(T_i)) / sum_j w_j (1 / R(T_j)), so that sum_i w_i s_i = 1. This is the instantaneous share at the field's temperatures. It leaves out the redistribution over time that the paper's multi-unit model carries: units that draw more current deplete faster and their share falls.
- Per case, field and set:
  - the unit-mean resistance R_mean = sum_i w_i R(T_i);
  - the share spread, max_i s_i minus min_i s_i;
  - the area-weighted standard deviation of the shares, sqrt(sum_i w_i (s_i - 1)^2);
  - the shares of the hottest and coldest units, and of the innermost (unit 1) and outermost (unit N) units.
- Errors of the radial and the end-corrected fields against the resolved field:
  - relative, (X_field - X_resolved) / X_resolved, in R_mean and in the share spread;
  - absolute, s_field - s_resolved in percent of the mean current density, in the innermost and outermost shares.
- Registered: ORegan2022, 100 % state of charge, time-averaged temperatures, area weights. Brackets, recorded for every case: Chen2020; 50 % state of charge; end-of-discharge temperatures; unweighted means (the brief's formula, with 1/N in place of w_i).

D25. Stage 4 predictions and checks.
- The predictions are the brief's P1 to P7, in predictions_stage4.md with their scoring rules, committed and pushed before any Stage 4 computation.
- P6 is registered word for word. Its expectation was changed from "likely" to "unlikely" by the author's choice (29 October), after this observation. To first order a unit's share is 1 + a (T_i - T_mean), with a = -d ln R / dT. The relative share-spread error is therefore close to the relative temperature-spread error, whatever a is. Under Chen2020 the spread errors of P1, P2 and P5 should be about those under ORegan2022; only the resistance errors of P3 and P4 scale with a.
- V1: as in D22.
- V2: R(T) at minus 5, 0 and 25 C for both sets at 100 % state of charge, re-derived by separate code (src/stage4_v2.py) within 0.1 %. That code applies the current as a current function rather than an experiment, and takes V before the pulse from the open-circuit potentials at the initial stoichiometries rather than from a rest.
- V3: the main case's shares and spread recomputed by a separate routine with explicit loops from the R(T) table.
- V4: both state-of-charge brackets and both temperature readings recorded for every case; the registered numbers are the main choices.
- Then an independent read of every registered number and verdict, before the note is written.

D26. After the Stage 4 runs, prompted by the independent read (verification/stage4_independent_read), which found no registered number, verdict or definition wrong. Nothing is changed.
- In every case, field and reading the hottest unit is unit 1 (the innermost) and the coldest is unit N (the outermost). The shares of the hottest and coldest units that D24 lists are therefore the innermost and outermost shares in results/stage4_errors.csv.
- The case (a) check in results/stage4_unit_temps.json compares the offset and the spread with Stage 1's three-decimal table. The full-precision values in results/results_3d.csv also match.

## Stage 5 (after v1.3.0): the multi-unit model with a resolved thermal field

D27. Part A0, recorded before the predictions: what the paper and the cell's specification say, the linearity of the thermal models, and two facts found in single-cell runs.
- The paper (Yang, Cui and Tartakovsky, J. Electrochem. Soc. 173 (2026) 050520; page numbers of its eight pages):
  - p. 3: "At 3C (Fig. 4b), the single-unit model overestimates the total discharge energy by approximately 3.45%, while it overpredicts by 11.32% at –5°C." p. 4 places the second number at 2C ("the capacity loss (3.45%) is smaller than at 2C under –5°C (11.32%)") and calls both a capacity loss. For the 4680 at 2C and minus 5 C, p. 4 says the single-unit model overestimates the discharge energy "by about 11.45% (Fig. 7b)", with unit currents "varying from approximately 1.25C to 2.75C (Fig. 8)".
  - p. 1, on the direct approach: "coupling the P2D models for multiple units through such an optimization at each time step would render this approach impractical for real-time control and other applications". On coupling a thermal model: "Doing so would further exacerbate the computational cost."
  - p. 1, abstract: single-unit approximations "fail to capture the battery performance, especially at high charge/discharge rates and/or low temperatures". Introduction: low temperatures (below 0 C) slow the kinetics and transport and "can induce lithium plating". p. 6, conclusion: "stronger current localization and uneven utilization intensify local electrochemical stress and accelerate potential degradation". Every simulation the paper shows (Figs. 3 to 8) is a discharge.
  - The single-unit model (p. 3) "assumes that all units behave identically under an averaged temperature": "the P2D equations are solved under the volume-averaged temperature", T_ave = (2 / R_b^2) times the integral of T r_b dr_b from 0 to R_b. Both models "are coupled with the one-dimensional thermal model". The units' areas (Eq. 5c, p. 3): A_n / A_m = r_b(n) / r_b(m), summing to the battery's electrode area. The currents satisfy Eq. 5a (the area-weighted sum of the unit current densities is the applied current) and Eq. 5b (every unit at the battery voltage). Here a unit's area is its annulus's cross-section (D24), which is proportional to its mean radius, as Eq. 5c has it.
  - The figures. Fig. 4 (p. 5): lithiation curves of the M50 at 1.25C, 2C and 3C at minus 5 C and 25 C, with the multi-unit model at T_ave drawn dashed. The text places 1.25C and 25 C in panel (a), 3C in (b), the higher rates in (b) and (c), and minus 5 C in (d), which p. 4 gives as 2C. Fig. 5 (p. 5): each unit's temperature less the outermost unit's at the end of the 1.25C, 2C and 3C discharges at 25 C and minus 5 C. Fig. 6 (p. 5): the M50's unit current densities at 2C and minus 5 C. Fig. 7 (p. 6): the 4680 at 2C and minus 5 C, its unit temperature differences at the end of discharge (a) and its lithiation curves (b). Fig. 8 (p. 6): the 4680's unit current densities at 2C and minus 5 C, where the core's current rises and later falls below the outer units' (p. 5). The coefficient is h = 400 W/(m^2 K) (p. 3). The paper's training data run to 2.6 V (p. 2); the cut-off of Figs. 4 and 7 is not stated.
- The specification: LG Chem, Lithium Ion INR21700 M50T 18.2Wh, document LRB-PS-CY18.2Wh-M50T, revision 0, 2018-07-16, 13 pages, read on 16 November 2026 in the copy hosted by Robu.in (aws.robu.in/wp-content/uploads/2021/11/DATASHEET-LGM50T.pdf).
  - Standard charge (section 2.4 on p. 4; section 4.1.1 on p. 6): constant current 0.3C (1,455 mA), constant voltage 4.2 V, end current 50 mA.
  - Maximum continuous charge current (section 4.2.3, p. 7): 0.3C (1,455 mA) from 0 to 25 C; 0.7C (3,395 mA) from 25 to 45 C.
  - Operating temperature (section 5.1, p. 9): charge from 0 to 45 C; discharge from minus 20 to 55 C. Maximum charge voltage 4.20 V and minimum discharge voltage 2.50 V (sections 2.5, 2.7 and 2.9, p. 4).
  - The specification's 1C is 4,850 mA, since its 0.3C is 1,455 mA. This study's 1C is the parameter sets' nominal 5 A h, which is 1.031 times larger.
- Which cell. The paper names the LG Chem INR21700 M50 (p. 3). Chen et al. 2020 (the Warwick repository copy) calls its cell "LG M50 21700 (LGM50)", and O'Regan et al. 2022 (the ChemRxiv preprint) calls it "a 5 Ah M50 21700 cylindrical cell manufactured by LG Chem". Neither names the M50T. The brief's statement that Chen et al. 2020 identifies the cell as the M50T is therefore not borne out by its text. The M50T is named by the paper's ref. 34, Kirkaldy et al., ACS Appl. Energy Mater. 5 (2022) 13367 (the abstract of its ChemRxiv record: "a commercial cylindrical cell with a Si-Gr electrode (LG M50T)"). The paper validated its parametrisation against that study's discharge data at 0.1C and 0.5C (p. 3, footnote b). The charging limits used here are the M50T's. Whether the M50's own document states the same limits was not checked.
- Linearity (A0.3), read from the code.
  - src/radial1d.py, src/cell3d.py (ends insulated and ends cooled) and src/stage2_correction.py assemble constant matrices. These hold D4's constant density, specific heat and two conductivities, the can's constant shell conductance and capacity, a constant h and, in the corrected model, a constant end sink beta. Every exchange term is taken relative to a fixed ambient, and the source enters linearly.
  - There is no radiation, no temperature-dependent property and no other term in T. Each model advances by backward Euler with one matrix per time step.
  - The temperature rise is therefore linear in the heat history, and the kernels below are exact up to the linear solver's tolerance. Stage 1's conjugate-gradient solves of the 4680 are linear to their relative residual of 1e-12.
- Two facts found in single-cell runs during the cost test. No coupled solve and no kernel was used.
  1. Under ORegan2022 the discharges end long before the registered heat does.
     - In the main case, a DFN held at Stage 4's area-weighted mean temperature of the resolved field reaches 2.5 V at 147.2 s (0.409 A h). The registered Chen2020 heat lasts 1,706.7 s. With its own heat in PyBaMM's lumped thermal model (D3's settings), the cut-off comes at 155.5 s.
     - At 25 C it comes at 775.0 s at 2C and 2,258.1 s at 1.25C (both at Stage 4's mean temperatures), and at about 275 s at 3C (lumped).
     - Chen2020 ends within 1 s of its heat's duration in each of these cases.
  2. With D23's 2.5 to 4.2 V window, PyBaMM places 100 % state of charge at a negative-electrode stoichiometry of 0.9842 in ORegan2022 and 0.9106 in Chen2020. Both sets use Chen et al.'s graphite potential, which is flat at 0.092 V above 0.9.
     - In a constant-current charge of one cell held at the ambient temperature, the particle surface next to the separator reaches the stoichiometric limit before 4.2 V at both of the specification's limits. The margin of D32 is then minus 192 mV (1,455 mA at 0 C) and minus 235 mV (3,395 mA at 25 C).
     - PyBaMM 26.9 adds to each open-circuit potential a barrier of 1 mV at a stoichiometry 0.001 from its limit and 1,000 mV at the limit (pybamm/parameters/lithium_ion_parameters.py, U_asymptotes). These margins are that barrier, not an overpotential.
     - Between 0.05C and 2C of the specification's C, the margin lies between plus 33 and plus 84 mV below some rate and between minus 192 and minus 272 mV above it. The change happens between 0.2C and 0.3C at 0 C, between 0.3C and 0.5C at 10 C, and between 0.5C and 0.7C at 25 C.
     - Chen2020 gives minus 0.9 and plus 1.9 mV at the two limits, and its margin changes sign smoothly near 0.30C (0 C), 0.45C (10 C) and 0.72C (25 C).
  - The author chose on 16 November, after reading these facts, to keep ORegan2022 registered and Chen2020 as the bracket, as the brief has it. Every reading is reported under both sets.

D28. A0.4, the cost test, and what it fixes.
- Timings on this machine (two cores, 7 GB of memory):
  - Resolved step responses for nine groups' loads:
    - 21700: SuperLU factorises in 7.1 s, then takes 0.23 s per step (25 ms per load).
    - 4680: Stage 1's conjugate gradients take 1.0 s per load and step (27 iterations). SuperLU on the same matrix factorises in 122 s and then takes 1.6 s per step for nine loads (0.18 s per load), with a peak memory of 5.5 GB.
  - The coupled solve of D30 with 15 groups and the temperature inputs changed at every step:
    - a 2C, 25 C discharge in 1 s steps: 769 steps in 110 s (ORegan2022);
    - a 2C, minus 5 C discharge: 1,709 steps in 104 s (Chen2020);
    - a 1,455 mA charge from 0 % at 0 C in 10 s steps: 152 s (ORegan2022) and 75 s (Chen2020).
  - One DFN alone takes 4 to 13 ms per step.
  - The full case set below comes to about 15 hours of computing, which this machine can run, so no reduced set is proposed.
- Groups: G = 15 in both cells. The 21700's 45 units form 15 groups of 3. The 4680's 111 units form groups whose edges are the integers nearest 111 k / 15, that is, groups of 7 or 8 units. The brief's minimum is 9 groups. 15 was chosen with V4 in view.
  - Stage 4's proxy evaluated at group level from its stored time-averaged temperatures (main case, resolved field) gives a share spread of 5.020 % with 9 groups, 5.279 % with 15, 5.402 % with 18, 5.535 % with 30 and 5.542 % with 45, the unit level.
  - Doubling 9 groups therefore changes the spread by 7.6 %, more than V4 allows. Doubling 15 changes it by 4.8 %.
  - The radial field's relative spread error and the area-weighted standard deviation of the shares change by less than 1 % between 9 and 45 groups.
- Time steps:
  - Each discharge case runs on the time grid of its registered heat (t_end / ceil(t_end / 1 s), the grid of Stages 1 to 4), so that its one-way temperatures are Stage 4's at every step.
  - Charges run in steps of 10 s, and every kernel is computed again on that grid.
  - V3 halves both.
- Linear solvers: Stage 1's SuperLU for the 21700 and for the one-dimensional models. For the 4680's resolved cell, SuperLU on Stage 1's matrices, where Stage 1 used conjugate gradients to a relative residual of 1e-12. It is the same discrete system, solved directly, and P1 measures the difference.

D29. Part A, the groups and the kernels (src/stage5_kernels.py).
- Group g holds its units' electrode area: W_g = sum of w_i over its units (D24), and the W_g sum to 1. A group's temperature is the area-weighted mean of its units' temperatures, the units as Stage 1 defines them: the exact annulus average in the one-dimensional models (D7), and Stage 1's sampled annulus average in the resolved cell (D10).
- A group's heat is uniform over its annulus and over the full height. A real roll's heat varies along the height, with the tabs; that variation is left out here and stated as a limit.
  - In the one-dimensional models the load of group j is the exact annulus integral of the basis functions, which is the unnormalised rows of Stage 1's unit operator.
  - In the resolved cell it is the exact integral of the basis functions over the part of each prism of the mesh inside the annulus. Integrated over the height of a prism, the six basis functions of its vertex-order split are quadratics in the triangle's barycentric coordinates. They are integrated exactly over each sub-triangle wholly inside one group (a three-point rule exact for quadratics). The triangles cut by a group's boundary are subdivided adaptively to 12 levels, and at the last level each quadrature point counts towards the group it lies in.
  - The group loads sum to Stage 1's uniform load to round-off, and each is scaled as Stage 1's source is (the exact volume over the mesh volume). Each group's mesh volume is reported against its exact annulus.
- The step response S_ij(k) is the rise of unit i's temperature at step k when group j is heated at 1 W/m^3 from step 1 on, starting from the ambient. It is computed with the same matrices, the same backward Euler steps and the same time step as the model's own runs. The group responses are S_gj(k), the area-weighted means over group g's units. The response to uniform heat is the sum over j.
- Each response is stepped until max |S(k) - S_inf| <= 1e-8 max |S_inf|, where S_inf is the model's exact discrete steady state, and at least to the longest archived discharge on that grid. Past that step it is held at S_inf, and the truncation is reported.
- The convolution: T_i(k) = T_amb + sum over m from 1 to k and over j of S_ij(k - m + 1) (q_j(m) - q_j(m - 1)), with q_j(0) = 0. Here q_j(m) is group j's heat per unit volume (W/m^3) at the end of step m. It is the same sum the backward Euler steps make, so it reproduces each solver step by step.
- Kernels are computed for the radial model, for the resolved cell with the ends insulated and with them cooled, and for the end-corrected model (beta of D18 with the ends cooled; with the ends insulated beta = 0, so it is the radial model).
  - Grids: the 21700's four registered discharge grids (2C at minus 5 C, 2C and 1.25C at 25 C, 3C at 25 C), with the ends insulated on the first only. The 4680's grid for 2C at minus 5 C. The 10 s charge grid for both cells. The grids V3 and V4 need.
  - The kernels are stored in results/stage5_kernels in single precision, as group responses, the units' uniform-heat response and, for the main case's grid, every unit's response to every group. The computations use double precision.

D30. Part B, the coupled solve (src/stage5_coupled.py).
- Each group is PyBaMM 26.9.0.0's Doyle-Fuller-Newman model with D23's default isothermal options, plus "calculate heat source for isothermal models": "true", which adds the heat without changing the electrochemistry.
  - "Ambient temperature [K]" and "Initial temperature [K]" are the group's temperature, an input updated at every step.
  - The model uses PyBaMM's default mesh (20 points in each electrode, in the separator and in each particle radius) and the IDAKLU solver with rtol 1e-6 and atol 1e-8.
  - Both sets run on the 2.5 to 4.2 V window of D23. The initial concentrations are the stoichiometries PyBaMM gives for 100 % (discharge) or 0 % (charge) state of charge. As D23 notes, these are placed at the reference temperature. They are written into the parameter set, so that the temperature can be an input.
- Each group's model is the full cell run at that group's current density: its current I_g is what the whole electrode area would carry at that density. The cell's current is I_app = sum of W_g I_g, and group g's share is I_g / I_app. The 4680 uses the same model at the same current per unit area, with its own weights and kernels.
- All groups share one terminal voltage. The G currents and the voltage V are unknowns of one differential-algebraic system, alongside every group's own states. Its equations are the groups' models, V_g = V for each group, and the sum of W_g I_g = I_app.
  - IDAKLU's Newton iteration solves these at every internal step. That is the root search for the voltage, done at every step of the solver rather than once per thermal step.
  - The system is built from G copies of PyBaMM's model with every state variable renamed.
  - V5 checks it against the literal route, in which separate models are stepped and the voltage is found by a root search at each step.
- Stepping: the system advances one thermal step at a time. Each group's temperature is held over the step at its value at the step's start, the latest the convolution gives, and the heat at the step's end enters the convolution for the next temperature. This operator splitting puts the temperature one step behind the electrochemistry. V3 tests it.
- Heat, two ways:
  - Two-way (registered): q_g = group g's "Total heating [W]" divided by the 21700's volume (Stage 1's normalisation, D6, for both cells).
  - One-way (the link to Stage 4): the registered Chen2020 heat q(t) of Stages 1 to 4 in every group, on the archive's grid, so that the group temperatures are Stage 4's at every step.
  - The rule the brief fixes for one-way heat: past the archive's end, the temperatures are held at their last values. The number of runs and the seconds for which it acts are reported.
- The single-unit model (B3) is one such DFN at T_ave(k) = sum of w_i T_i(k) = sum of W_g T_g(k), the area-weighted mean of the units, which is the paper's volume-averaged temperature. It sees the same thermal model and the same heat rule. Under one-way heat that is the field of the registered heat. Under two-way heat it is the field its own heat makes when applied uniformly. It is run once under each kernel.
- A discharge ends when the common voltage reaches 2.5 V, and a charge when it reaches 4.2 V (solver events).
- Sets: ORegan2022 is registered and Chen2020 is the bracket (D27).

D31. Part C, the discharge readings.
- Cases: Stage 4's five (D22) and the M50 at 3C and 25 C with the ends cooled, the condition of the paper's 3.45 %. Each runs under the radial, resolved and end-corrected kernels, with two-way heat (registered) and one-way heat, and under both sets.
- C1, the penalty: the single-unit model's discharge energy to 2.5 V over the coupled model's, less one. Each energy is the integral of V I_app by the trapezoidal rule over the step outputs through the cut-off. The same is done for capacity, I_app t_cut / 3600.
- C2, the shares:
  - s_g(t) = I_g / I_app at every step output.
  - The spread at each output is the largest share minus the smallest; its time average is by the trapezoidal rule over [0, t_cut], starting at t = 0 where every share is 1.
  - The area-weighted standard deviation of the shares, the time-averaged innermost and outermost shares, and the innermost group's share over time are reported beside it.
  - The reversal time is the first time at which the innermost share, having risen above 1, falls below 1, interpolated linearly between outputs. A run without one is reported as having none.
- C3: Stage 4's proxy (its share spread, 5.54 % in the main case, and its spread errors) beside the coupled time-averaged spreads under one-way heat, and the coupled spread errors.
  - Because the coupled discharge can end long before the archive's (D27), the proxy is also evaluated like for like: Stage 4's R(T) procedure (D23 and D24, ORegan2022 at 100 %) at the temperatures time-averaged over the coupled run's own window [0, t_cut], both at the unit level and at the group level.
- C4: the radial and end-corrected kernels' errors against the resolved kernel:
  - in the penalty, relative and in percentage points;
  - in the time-averaged spread, relative;
  - in the time-averaged innermost and outermost shares, in percentage points;
  - in the reversal time, in seconds.
- Ranges: minus 5 C lies outside both sets' measured ranges (D23). Every minus 5 C number is an extrapolation of the set, not of the thermal model, and is reported as such.

D32. Part D, the charge readings.
- Cases: a constant-current charge from 0 % state of charge at rest, with every group at the ambient, to a common voltage of 4.2 V, with the ends cooled, in the M50 and the 4680.
  - Rates are in the specification's C (1C = 4.85 A in the M50; the 4680 at the same current per unit area).
  - The specification's two limits: 0.3C (1,455 mA) at 0 C and 0.7C (3,395 mA) at 25 C.
  - Brackets outside the specification's charging limits: 0.7C at 0 C, and 1C (4,850 mA) and 2C (9,700 mA) at 25 C.
  - No case runs below 0 C. 0 C lies below ORegan2022's measured ranges for the kinetics (15 C) and solid diffusion (5 C) (D23), and every 0 C and 10 C number says so.
- D1, the margin: the smallest value of phi_s,n minus phi_e, the negative electrode's solid potential less the electrolyte's. The minimum is taken over the charge (every step output and the cut-off), over the negative electrode's 20 nodes and its separator-interface value (PyBaMM's "Negative electrode surface potential difference [V]" and "... at separator interface [V]"), and over the groups.
  - The group that holds it, the time and the place are recorded.
  - It is the model's own variable, and no plating reaction is added. A negative margin means lithium deposition is thermodynamically possible there; it is not an amount of plated lithium.
  - Under ORegan2022 a margin of minus 0.1 V or less reflects the barrier at the stoichiometric limit (D27).
- D2: the margin for the single-unit model and for the coupled model under each kernel, with two-way heat, under both sets.
- D3, the plating-limited rate: at ambients of 0, 10 and 25 C, in both cells, for the single-unit model and the coupled model under each kernel, with two-way heat, under both sets.
  - A trial passes if the margin stays at or above zero until 4.2 V. A trial stops as soon as the margin falls below zero, which fails it.
  - Single-unit model: trials at 0.05C, 0.10C, 0.15C and so on upward until the first failure. Coupled model: the scan starts at the single-unit model's rate under the same kernel less 0.10C, rounded down to 0.01C (at least 0.05C); if that start fails, it steps down by 0.05C until a trial passes. In both, the scan then steps up by 0.05C to the first failure.
  - That 0.05C bracket is halved three times, to 0.00625C. The reading is the largest passing rate, with the smallest failing rate beside it.
  - For P9's four rates (0 C, resolved kernel, single-unit and coupled, both cells, ORegan2022), the halving continues to 0.001C, and P9 is scored on those values.
  - Below the first failure the margin is taken to rise with falling rate. This was seen in the single-cell scans of D27 and is not tested for each coupled model.
  - The rates describe this parameter set, an energy cell, and the 4680 inherits it as the paper assumes. They do not describe a fast-charging cell.

D33. Checks, fixed before the predictions:
- V1:
  - P1's comparison.
  - Reciprocity: with each group's mean taken with its own load as the weight, the group volume times S_ij(k) equals the transpose at every step within 1e-9 of the largest value.
  - The difference between that mean and the sampled group mean of D29.
- V2: every group's temperature set to the single-unit model's T_ave in the main case (one-way heat, resolved kernel, ORegan2022). The coupled solve matches the single-unit model within 1 mV in voltage at every step and within 0.1 % in capacity.
- V3:
  - In every coupled run, |sum of W_g I_g - I_app| below 1e-6 I_app at every step output.
  - The time step halved, with every kernel recomputed on the halved grid, in the main case and in one charge case (the M50 at 1,455 mA and 0 C). Each registered reading changes by less than 1 %.
- V4: G doubled to 30 (groups of 1 or 2 units in the M50) in the same two cases. Each registered reading changes by less than 5 %.
  - The registered readings for V3 and V4 are:
    - in the main case, the energy and capacity penalties under each kernel with two-way heat, the time-averaged spread under each kernel with both heat rules, and the reversal time where there is one;
    - in the charge case, the margin under each kernel and the charge capacity at 4.2 V.
- V5, the second route, in the main case (two-way heat, resolved kernel, ORegan2022):
  - G separate DFNs in PyBaMM's voltage mode, each with its voltage linear in time over each step.
  - The step's end voltage is found by a secant search on the current balance at the end of the step, to 1e-8 of I_app. Every group model is stepped from its state at the start of the step for each trial voltage.
  - The temperature and heat rules are the same.
  - Every group's share at every step agrees with the stepwise route within 0.5 % of its value.
- V6: for the coupled M50 at 1,455 mA and 0 C (resolved kernel, ORegan2022), phi_s,n and phi_e at the negative electrode's nodes are stored for every group and step. Separate code, using no PyBaMM variable, recomputes the margin from them: the node minimum, and the interface value by linear extrapolation from the two nodes next to the separator.
- Then an independent read of every registered number and verdict by a separate agent that did not see the runs being made.

D34. The predictions are the brief's P1 to P9, in predictions_stage5.md with their expectations and scoring rules. They are committed and pushed after Part A0 (D27 and D28) and before any kernel is computed or any coupled solve is run. Stage 1 to 4 code and results are not edited; Stage 5 adds new files only.

D35. Notes made after the predictions. None changes the procedure of D27 to D33, and every reading and verdict reported is the registered one.
- The particle mesh, found after the predictions and checked post hoc (src/stage5_posthoc_mesh.py, results/stage5_posthoc_mesh.json). D30 registered PyBaMM's default mesh, 20 points along each particle's radius. The check runs one DFN held at the ambient temperature on D23's window, as D27's single-cell runs and Stage 4's R(T) do, with 20, 40, 80, 160 and 320 points.
  - Under ORegan2022 the results at 20 points are not settled:
    - The 2C discharge at 25 C ends at 978 s with 20 points, 1,282 s with 40, 1,456 s with 80 and 1,468 s with 160.
    - The 2C discharge at minus 5 C ends at 126, 121, 141, 186 and 247 s with 20 to 320 points, and has not settled at 320.
    - At the specification's two charge limits the smallest margin is minus 193.6 mV (0.3C, 0 C) and minus 237.3 mV (0.7C, 25 C) with 20 points: the negative surface next to the separator reaches its stoichiometric limit, and the charge stops at 3.14 and 2.84 A h. With 40 points or more the margin stays positive to 4.2 V: plus 19.1 to 19.7 mV and plus 27.4 to 28.6 mV, with 4.29 to 4.30 A h charged.
    - The largest charge rate whose margin stays at or above zero, for the cell at the ambient, is 0.280C, 0.369C and 0.536C at 0, 10 and 25 C with 20 points, 0.405C, 0.618C and 1.024C with 40, and 0.430C, 0.670C and 1.228C with 80.
  - Under Chen2020 every one of these settles at 20 points: the discharges within 0.21 s, the margins within 0.011 mV (minus 1.51 and plus 0.48 mV) and the rates within 0.001C (0.288C, 0.431C and 0.706C).
  - The cause is ORegan2022's graphite diffusivity, a fit that varies about 500-fold with stoichiometry at 25 C (1.4e-13 m^2/s at a stoichiometry of 0.9842, the 100 % point of D27, and 2.8e-16 m^2/s at 0.80). Twenty points along the radius do not resolve the steep concentration profiles it produces. Chen2020's diffusivity is constant.
  - Consequences:
    - The second fact of D27 (at both of the specification's limits the negative surface next to the separator reaches its stoichiometric limit before 4.2 V) belongs to the 20-point mesh.
    - The first fact (the ORegan2022 discharges end long before the registered heat does) holds in direction with the finer meshes, but its times depend on the mesh.
    - Every ORegan2022 reading in Parts C and D (penalties, shares, margins, plating-limited rates) is therefore a reading of the 20-point discretisation, and is reported as registered with this said beside it. The Chen2020 bracket is settled at 20 points in every quantity checked. The coupled model under ORegan2022 with a finer mesh was not run.
    - Under ORegan2022 at 20 points, whether a discharge gets past its early end can turn on a fraction of a kelvin. At 3C and 25 C the end-corrected field's innermost group is 0.2 K warmer than the resolved field's at 270 s; the coupled discharge under the end-corrected kernel runs to 604 s, while its single-unit model and both models under the resolved kernel stop near 280 s.
    - Under ORegan2022 the smallest margin of a passing charge is not always monotonic in the rate: in the 4680's single-unit search at 25 C under the radial kernel it is plus 37.97 mV at 0.500C and plus 38.37 mV at 0.525C, and two more such pairs occur. D32 took monotonicity as given. In every one of the 72 searches the trials' pass or fail is monotonic in the rate, so each reading is what D32's rules give from its trials.
  - Stage 4's pulse resistances (D23) move by 3.0 to 5.3 % between 20 and 160 points. Their temperature sensitivity, which sets the shares, moves by 0.2 % under ORegan2022 (d ln R/dT between minus 5 and 25 C: 0.02423 and 0.02427 per K) and by 4 % under Chen2020 (0.01120 and 0.01072 per K). Stage 4's files are not edited.
- Storage. The kernels are stored in single precision (D29). The runs read the stored values and do all arithmetic in double precision, so the stored kernels are the ones used. Against Stage 4's stored histories, which are rounded to 1e-7 K, the kernels agree within 9.5e-7 K (P1).
- The machine's limits: a memory limit of 6.27 GB shared by all jobs, two cores, and two hours per background job.
  - The 4680's resolved factorisation needs about 5 GB (its kernel jobs recorded 4.8 GB, and D28's cost test 5.5 GB), so its kernels ran with only small jobs beside them. Its first run on the main discharge grid was stopped by the two-hour limit 2,000 steps in. It was run again from the start, saving its state every 200 steps. That run was stopped 1,600 steps in, when a side check run beside it exceeded the memory limit, and it resumed from its saved state at step 1,600. The M50's 30-group kernels of V4 were stopped twice by a memory guard while it ran, and were computed after it.
  - A coupled process with 15 groups needs about 2 GB while it runs, and one with 30 groups about 4.1 GB. The registered runs were split into one job per kernel, and two processes worked through them, each claiming a job before running it and starting it only when the memory in use left room (src/stage5_queue.py). Each job runs in its own process, and freed memory is returned to the system after every run. The 30-group runs of V4 ran alone.
  - The processes ran in rounds that end before the two-hour limit. The trials of the limit searches were stored as they finished, so that a search stopped by the machine resumed where it stopped. A stored trial is the same computation's result, and the search records which trials came from the store (17 of 700). Runs and kernels are written to a temporary file and renamed, so a stopped job leaves no partial file.
  - Four jobs were stopped part way and run again: two when the processes were restarted to run one job each (one of them twice), and two by the two-hour limit. Three were searches, which resumed from their stored trials; the fourth, a discharge, was run again whole.
- One-way heat past the archive's end (D30). The hold rule acted in 15 runs, the coupled and single-unit models counted apart. In 12 Chen2020 runs it acted for 1 to 7 steps of about 1 s: the M50's main case under the radial kernel, its insulated case under the radial and resolved kernels, and the 4680 under all three. In 3 ORegan2022 runs at 3C and 25 C it acted for 47 to 59 steps (the coupled and single-unit models under the radial kernel, and the coupled model under the end-corrected kernel): those discharges ran past the 558 s of the registered heat.
- The current balance (V3). Across every stored coupled run the largest residual is 5.7e-10 of I_app. The searches' trials store their margins and not their step outputs, so V3's residual is read on the stored runs.
- Checks that failed. V3's halved step moves the main case's penalties under the radial and end-corrected kernels by 1.1 to 1.3 % of their values (the limit is 1 %; the energies and capacities behind them move by at most 0.15 %). V4's 30 groups move five of the six time-averaged spreads by 5.1 to 5.4 % (the limit is 5 %; the sixth moves by 4.8 %), close to the 4.8 % that D28 found for the group-level proxy. Both checks are reported as failed, and no registered reading is replaced.
- A ripple. Under ORegan2022 the shares and the terminal voltage ripple in every discharge, with a period of about 11 s at 2C and minus 5 C and of about 7 to 19 s in the other cases. The single-unit model's voltage ripples alike and Chen2020's does not, so the ripple belongs to the DFN under this set at the registered mesh, not to the coupling. The time averages of D31 smooth it.
- Readings, as the code computes them where D31 to D33 leave a detail open:
  - The like-for-like proxy of C3 uses the run's own set's R(T): ORegan2022's for the registered rows, as D31 says, and Chen2020's for the bracket's rows, as P3's bracket does.
  - The reversal's "having risen above 1" is read as above 1 + 1e-12, so that round-off in the shares (about 2e-16) does not count.
  - With 30 groups (V4) the edges 45 k / 30 fall halfway between integers for odd k; they are rounded up.
  - V5's two routes agree within 0.037 % in every share; their voltages differ by up to 6.5 mV at the last full step. V5's criterion is on the shares.
  - In 25 failed trials the margin first goes below zero at the 4.2 V cut-off itself; by D32's rule these are failures. 20 are ORegan2022 trials at the barrier of D27, and in the 5 Chen2020 trials the margin there is between minus 0.1 mV and zero. Some passing Chen2020 trials clear zero by a few microvolts.
  - P9's Chen2020 bracket is read at the searches' 0.00625C, since D32 refines only the registered set's four rates.
  - Figure panel (b) shows the main case's shares under Chen2020, whose readings are settled at the registered mesh.
