# Stage 4 predictions

Written by the author in the Stage 4 brief and committed here as written, each with its expectation, before any Stage 4 computation. The procedure they are scored on is fixed in DECISIONS.md D22 to D25. One thing differs from the brief: P6's expectation. The author changed it from "likely" to "unlikely" on 29 October, before this commit (D25); the wording of P6 is unchanged.

P1. In the main case under ORegan2022, the radial field overstates the share spread relative to the resolved field by at least 30 %. Expectation: likely (the temperature spread is overstated by 36 % and the resistance is monotone in temperature).

P2. In the main case under ORegan2022, the end-corrected field's share-spread error is below 8 %. Expectation: likely (the end correction brings the spread overstatement to 5 %).

P3. In the main case under ORegan2022, the radial field underestimates the unit-mean resistance by more than 4 %. Expectation: uncertain (1.19 K times the sensitivity at minus 5 C, which the table will give).

P4. At 25 C and 2C with the ends cooled, the same error is below 3 %. Expectation: likely.

P5. In the 4680 main case the share-spread error of the radial field is at least three times the M50's. Expectation: likely.

P6. Under Chen2020 every error in P1 to P5 is less than half its ORegan2022 value, because that set's temperature dependence sits only in the exchange-current densities. Expectation: unlikely. The author changed this from "likely" before this commit, for the following reason. To first order the relative share-spread error follows the relative temperature-spread error, whatever the resistance's sensitivity to temperature. So the spread errors of P1, P2 and P5 should not shrink under Chen2020; only the resistance errors of P3 and P4 should.

P7. With the ends insulated, every error is below 1 %. Expectation: likely.

## Scoring rules

**Registered choices** (D22 to D24): ORegan2022; 100 % state of charge; time-averaged unit temperatures; area weights.

**Terms used below:**
- The main case is the 21700 at 2C and minus 5 C with the ends cooled at h = 400 (case (b)). The 4680 main case is the same condition in the 4680.
- The share spread is the largest share minus the smallest.
- Errors are the field's value minus the resolved field's. They are relative for the unit-mean resistance and the share spread. For the innermost and outermost shares they are in percentage points of the mean current density.

**Brackets.** Each prediction is also evaluated at Chen2020 (where Chen2020 is not its subject), at 50 % state of charge, at end-of-discharge temperatures and with unweighted means, and read against those brackets. The verdict is taken at the registered choices.

**Rules:**
- P1: main case. The radial field's relative share-spread error is at least +0.30.
- P2: main case. The end-corrected field's relative share-spread error is below 0.08 in absolute value.
- P3: main case. The radial field's relative error in the unit-mean resistance is below -0.04.
- P4: 21700, 2C, 25 C, case (b). The radial field's relative error in the unit-mean resistance is below 0.03 in absolute value.
- P5: 4680 main case. The radial field's relative share-spread error is at least three times the main case's.
- P6: P6 holds only if all five of the quantities scored in P1 to P5 meet its condition: under Chen2020, each one's absolute value is below half its absolute value under ORegan2022. The five quantities are:
  - the radial spread error in the main case;
  - the end-corrected spread error in the main case;
  - the radial resistance error in the main case;
  - the radial resistance error at 2C and 25 C;
  - the radial spread error in the 4680 main case.
- P7: 21700, 2C, minus 5 C, case (a). This is scored for the radial field and the end-corrected field, which are identical here (beta = 0). The relative errors in the unit-mean resistance and in the share spread are below 0.01 in absolute value. The errors in the innermost and outermost shares are below 1 percentage point in absolute value.
