# Predictions

These five predictions are the brief's, committed and pushed to the public repository before any three-dimensional field of the study was computed. Before this commit the following had already run: the DFN heat runs (`results/heat_summary.csv`), the one-dimensional model (`results/radial1d_summary.csv`), and the three-dimensional checks that carry no information about the fields (`verification/v0_checks.json`: uniform-field totals and a pure-conduction relaxation from a random field). That is the order the brief sets. The one-dimensional model is the paper's model, and the predictions concern what the three-dimensional cell adds to it.

Every prediction is scored on the registered inputs: the Chen2020 heat and the 25 C properties. The case is the end of discharge (the DFN cut-off at 2.5 V) unless a prediction names another. The secondary inputs (the heat of mixing, ORegan2022, the minus 5 C properties) are reported beside them but never scored. The definitions are those of DECISIONS.md D10:
- the core-to-surface difference is T(r = 0, z = H/2) minus the mean of the surface ring at z = H/2;
- the axial difference is the larger of T(0, H/2) minus T(0, 0) and T(0, H/2) minus T(0, H);
- a unit temperature in three dimensions is the annulus average over the full height.

## P1
At 2C and minus 5 C with h = 400, lateral cooling only, the core-to-surface difference at mid-height at the end of discharge is between 3 and 10 K (central 6 K).

Scored on boundary condition (a), the can on every surface, at the end of discharge (1706.7 s). P1 holds if the difference lies between 3 and 10 K inclusive.

## P2
Adding end cooling at the same h changes the mid-height core-to-surface difference by less than 30 % (central 15 %) but creates a difference along the core, mid-height to end, of more than a third of the radial difference (central 50 %).

Scored on (b) against (a), at 2C and minus 5 C at the end of discharge. P2 holds if both clauses hold:
- the magnitude of [the core-to-surface difference in (b) divided by that in (a), minus 1] is below 0.30;
- the axial difference in (b), divided by the core-to-surface difference in (b), exceeds 1/3.

## P3
With end cooling, the one-dimensional unit temperatures exceed the three-dimensional unit averages by 1 to 3 K (central 1.5 K), by about the same amount for every unit, so the unit-to-unit spread changes by less than 20 % while every unit's temperature moves.

Scored on (b) against the one-dimensional model, at 2C and minus 5 C at the end of discharge, over the 45 units of the 21700. The offset of a unit is its one-dimensional temperature minus its three-dimensional average. P3 holds if all three of these hold:
- the mean offset lies between 1 and 3 K inclusive;
- every unit's offset is positive;
- the three-dimensional spread (hottest unit minus coldest unit) differs from the one-dimensional spread by less than 20 % of the latter.

Also reported, without being scored: the smallest and largest offsets, and whether every offset lies between 1 and 3 K.

## P4
In the 4680 the ratio of the axial difference to the radial difference is smaller than in the 21700 (central 0.3 against 0.5).

Scored on (b) at 2C and minus 5 C at the end of discharge. The ratio is the axial difference divided by the core-to-surface difference. P4 holds if the 4680's ratio is smaller than the 21700's.

## P5
At h = 25 both differences are below 1 K at 2C.

Scored on (d) at 2C at the end of discharge, at both ambients. P5 holds only if the core-to-surface difference and the axial difference are each below 1 K at minus 5 C and at 25 C.

## The brief's reason, without data
The brief gives this reason: "with q about 4e5 W/m³ the radial drop scales as qR²/(4k_across) and the axial drop as qL²/(8k_along); the two are within a factor of two for the M50, but the end area is an eighth of the lateral area, so end cooling removes a small share of the heat and lowers the whole field more than it reshapes the radial profile."

## Values at the time of this commit

The registered one-dimensional core-to-surface differences at the end of discharge, 21700 (4680 in brackets):
- 1.25C: 1.81 K (8.23 K) at minus 5 C; 1.36 K (6.12 K) at 25 C
- 2C: 4.26 K (19.11 K) at minus 5 C; 3.62 K (15.89 K) at 25 C
- 3C: 8.31 K (32.12 K) at minus 5 C; 7.38 K (27.96 K) at 25 C

The registered DFN heat at 2C and minus 5 C averages 3.81 W over 1706.7 s, which is q = 1.55e5 W/m³ in the 21700.
