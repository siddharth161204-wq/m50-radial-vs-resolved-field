Filed by the author with this header. The text below is the checker's report as it returned it. It audited commit ed0fdd8 together with the note, CITATION.cff and .zenodo.json as they then stood, uncommitted; the paths in it refer to the checker's workspace, and its scripts and logs are in audit_evidence/. Every finding was taken up in the README, the note, DECISIONS.md (D14, D15) or the metadata, except these: L13 (predictions.md is frozen, so the README states the value of q instead); N3's single licence in .zenodo.json (that file takes one licence; the README, the licence files and the Zenodo record carry both); N5 (the copy stays unchanged for provenance, and the README says it is not imported). The split of the heat between the ends and the side, and the radial model at the paper's end of discharge, which it computed with its own scripts, are recomputed with the study's code in D15 (results/posthoc_matched_time.json).

# Audit of m50-radial-vs-resolved-field before it goes to the paper's author

**Status: 10 errors and 23 imprecisions** (2 high, 5 medium, 26 low), plus 5 notes that need no change to the text. The table values in the README match the result files, and so do the scorecard verdicts. The main problems are interpretive. The V4 comparison is not made at the same state of discharge as the paper's figures, so the "correspondingly larger" kelvin values do not follow from it. The rendered note PDF is out of date and still holds a "[V3]" placeholder. Four claims overstate the results: the fractions being the same at every heat level, the end path being the stronger one, the stated cause of P5's failure, and the boundary condition "the paper states". The note's Limits also give the wrong direction for the conductivity.

Scope: README.md, note/radial_vs_resolved_note.md (plus its rendered HTML and PDF), DECISIONS.md, predictions.md, .zenodo.json and CITATION.cff. These were checked against results/, verification/, src/, inputs/, the paper's PDF (pdftotext, page by page, and its embedded figures), PyBaMM 26.9.0.0's CITATIONS.bib, the git history, GitHub's push record, Crossref, the two-cell study at /home/claude/ext/m50-two-cell-pilot and the thermal-lever study at /home/claude/tl. Nothing in /home/claude/m50-radial-vs-resolved-field was edited: `git status` and the `__pycache__` timestamps are unchanged. Two findings rest on the auditor's own calculations. Their scripts and logs are in /home/claude/audit_radial/evidence/.

Classes used: **Error** means wrong as stated (a value outside what the files give, a wrong direction, an unsupported cause, or a stale deliverable). **Imprecision** means true but loose, incomplete, ambiguous or inconsistent. Each finding names its category from the brief: (2) number, (3) overstatement, (4) inconsistency, (5) attribution to the paper, (6) style.

---

## High severity

### H1. Error (3, 5). The V4 comparison and the "correspondingly larger" kelvin values compare different states of discharge, and the text never says so
Quoted text:
- README, Result: "The paper's own Fig. 5 shows unit differences 1.7 to 2.8 times this study's radial model, and its Fig. 7a shows the 4680 at 2.0 times. So the paper's heat or conductivity differs (check V4 below), and its kelvin values would be correspondingly larger."
- README, V4: "The reading error is 0.09 K, so they do not agree: the paper's heat or its conductivity differs from Chen2020 with O'Regan's properties."
- Note, Limits 2: "The paper's Fig. 5 unit differences are 1.7 to 2.8 times this radial model's".
- .zenodo.json: "The paper's own unit differences are 1.7 to 2.8 times this study's radial model, so its kelvin values would be larger".

Evidence:
1. The paper's Fig. 5 shows profiles "at the end of" each discharge (caption, p. 5). The paper's Fig. 4 (p. 5, verification/v4/jes-000.jpg) shows where those discharges end.
   - At 2C and minus 5 C (Fig. 4d), the paper's discharge ends near 1.34 A h (multi-unit) and 1.50 A h (single-unit). This study's discharge reaches 4.741 A h at 1706.7 s (results/heat_summary.csv).
   - At 3C and 25 C (Fig. 4b), the paper's discharge ends near 4.2 to 4.4 A h. This study's stops at 2.326 A h at 558.3 s.
   - These are the two conditions of the paper's 11.32 % and 3.45 %.
2. Matched to the paper's end state at 2C and minus 5 C (about 482 to 540 s at 10 A), the study's own radial model gives an innermost-minus-outermost difference of 3.23 to 3.26 K, not 4.17 K. At that state the paper's 11.54 K is 3.5 to 3.6 times larger, not 2.8 times (evidence/radial_at_paper_end_time.log, which runs src/radial1d.py on the registered heat). The 3C, 25 C ratio cannot be matched at all, because the study's heat series stops at 558 s.
3. The ratio is not uniform along the radius. verification/v4.json gives, on the digitised grid, a minimum of 0.68 and 0.67 (2C and 1.25C at 25 C, near the surface, where the paper's differences are smaller than this model's: 0.19 against 0.27 K at r = 0.95 R, 2C 25 C) and a maximum of 2.94. A uniform change of heat or conductivity cannot produce that shape.

Consequences:
- The 1.7 to 2.8 ratios mix the heat rate, the properties, the discharge duration and the paper's unit-resolved heat. They do not show that the paper's kelvin values would be "correspondingly larger".
- README "The DFN does not fail at minus 5 C and 2C: it reaches 4.74 A h" should add that the paper's own discharge at this condition ends near 1.3 to 1.5 A h (Fig. 4d). The two parameter sets bracket the paper's end point: the registered Chen2020 run goes on to 4.74 A h, and the secondary ORegan2022 run stops after 166 s at 0.46 A h.

What survives: the headline fractions do not depend on the time. From the series in results/fields, the axial-to-radial ratio in (b) is 0.372 at 480 s against 0.371 at 1706.7 s in the 21700, and 0.324 at both times in the 4680.

### H2. Error (4). The rendered note (PDF and HTML) is stale and contains an unfilled placeholder
note/radial_vs_resolved_note.pdf and .html were written at 12:55 UTC. The .md was last changed at 14:15 UTC. The note/ folder is untracked in git.
- The PDF and HTML, Method 6, read: "A refined mesh changes the core-to-surface difference by [V3]." The .md reads: "A mesh with every spacing halved changes the core-to-surface difference by 0.09 %."
- Their last section is an older, three-sentence version: "...are too warm and too widely spread: by a third in the M50 and by a factor of two in the 4680. The 3.45 % and 11.32 % energy overestimates, and the 30 C difference across the 4680, would then be expected to shrink, by an amount this study does not compute." The brief asks for two sentences, and the .md has two.

Fix: correct the .md (see the findings below), then rerun note/render_note.sh before anything is sent.

---

## Medium severity

### M1. Error (3, 2). "The same at every heat level" is contradicted by the study's own tables for two of the four fractions
Quoted text:
- README: "The fractions above (37 %, 32 %, 36 %, 98 %) are properties of the geometry, the conductivities and the cooling, and they are the same at every heat level."
- Note, Limits 1: "The fractions hold at any heat level".
- .zenodo.json: "the fractions are independent of the heat level".

Evidence (results_3d.csv, case (b), at the six registered heats: 1.25C, 2C, 3C at minus 5 C, then the same at 25 C):
- 4680 spread overstatement (radial spread divided by resolved spread, minus 1): 100.9, 98.3, 79.1, 99.6, 96.3 and 77.8 %. The README's own 4680 table shows "31.81 against 17.76 K" at 3C, which is 79 %.
- M50 spread overstatement: 36.2, 36.2, 34.8, 35.9, 35.9 and 34.3 %.
- Only the axial-to-radial ratios stay constant: 0.370 to 0.371 in the M50 and 0.324 to 0.325 in the 4680.

The fractions also depend on the time history. The 3C discharge ends at 558 s, about half the 4680's radial diffusion time R^2 rho c / k_across, which is about 1070 s. They are not set by the geometry, conductivities and cooling alone. The claim is exact only for a pure rescaling of the same q(t).

Correct: "The axial-to-radial fractions (37 %, 32 %) are the same at every rate and ambient. The spread overstatement is 34 to 36 % in the M50 and 78 to 101 % in the 4680."

### M2. Error (2, 5). The note gives the wrong direction for the conductivity
Note, Limits 2: "...so its heat or conductivity is larger."

Larger unit differences need more heat or a lower conductivity. A larger conductivity would make them smaller. The README has this right ("differs").

Correct: "so its heat is larger or its conductivity smaller". Add the duration difference from H1.

### M3. Error (3). "In the 4680 the end path is the stronger one" is not supported, and the side still carries most of the heat
README, Result: "In the 4680 the end path is the stronger one: the roll conducts heat to an end 40 mm away more easily than to the side 23 mm away."

The deposited files record no split of the heat lost between the ends and the side. The auditor re-solved case (b) axisymmetrically (evidence/end_side_split.py and its log). The re-solve reproduces the study's 4680 (b) core-to-surface difference: 10.610 to 10.611 K, against the study's 10.613 K and the independent recomputation's 10.611 K.
- In the 4680, the ends remove 37.8 % of the heat (time-integrated) and 37.9 % at the end of discharge. The side removes 62 %.
- In the M50, the ends remove 18.6 %.

Only the narrower clause after the colon holds: inside the roll, the conduction resistance to the ends, H/(12 k_along pi R^2) = 0.16 K/W, is below the resistance to the side, 1/(8 pi k_across H) = 0.41 K/W.

Suggested: "In the 4680 the roll conducts heat to an end 40 mm away more easily than to the side 23 mm away, so the ends take about 38 % of the heat, against about 19 % in the M50."

### M4. Error (5). The insulated-end condition is attributed to the paper, which states no condition at the ends
Quoted text:
- README, first sentence: "The paper's own boundary condition keeps the cell's ends insulated."
- Note, What it means: "Under the boundary condition the paper states, the resolved field supports its radial model."
- .zenodo.json: "With the paper's own boundary condition (ends insulated)".

The paper (p. 3, Eq. 4) states only zero flux at r_b = 0 and convection to the ambient at R_b. It describes the temperature "in the through-battery direction" (p. 2) and never mentions the ends. Insulated ends are the three-dimensional reading of its one-dimensional model, which is how the brief puts it ("his boundary condition in three dimensions").

Suggested: "The paper's one-dimensional model carries no heat along the axis, which in three dimensions means insulated ends." The note's headline wording, "a radial model with the cell's ends insulated", is acceptable.

### M5. Error (3). The stated cause of P5's failure is not supported by the results
README: "P5 fails because the heat is held at the DFN's h = 400 value, as the brief requires."

No heat consistent with h = 25 was computed, and the results argue against this cause:
- At 25 C ambient, the heat is 20 % below the minus 5 C one (3.040 against 3.812 W mean), yet (d) still gives a radial difference of 2.62 K.
- At 1.25C, with a mean heat of only 1.19 to 1.67 W, (d) still gives 1.05 to 1.43 K (results_3d.csv).
- To bring the 2C, minus 5 C radial difference below 1 K, the heat would have to fall below about a third (3.18 K to 1 K). Chen2020's only temperature dependence is in the two exchange currents (D3), so about 30 K of warming cannot do that.

The README's next clause is the real mechanism: "the radial difference grows with the heat the surface has to carry away". With a time constant C/(h A) = 65.18/(25 x 5.346e-3) = 488 s against a discharge of 1706.7 s, the h = 25 cell is near quasi-steady at the end of discharge. The side then has to carry almost all of the heat, and the radial difference stays near q R^2/(4 k_across).

---

## Low severity: errors

### L1. Error (2). The V2 energy closure is misquoted
- README, V2: "closes within 4.6e-13".
- Note, Method 6: "Energy closes to 5e-13."

results/verification.json gives V2_max_abs = 2.02e-12, for 4680 (b) at 1.25C and 25 C. 4680 (a) at the same condition gives -1.59e-12. The 4.6e-13 figure is the 21700 maximum only (21700 a_eq, 1.25C, 25 C).

Correct: "within 2.0e-12 (4.6e-13 in the 21700)". This is still far inside the D11 criterion of 1e-9.

### L2. Error (2). One bound of the 4680 offset range is misrounded
README, 4680 bullets: "Its largest unit offset is 0.39 to 1.63 K".

results_3d.csv (4680, a, units_max_abs_diff_K) gives 0.38989 to 1.62456 K.

Correct: "0.39 to 1.62 K".

### L3. Error (2). The 3C capacity is misrounded at 25 C
README: "At 3C it stops at 2.32 A h at both ambients".

heat_summary.csv gives 2.3240 A h at minus 5 C and 2.3262 A h at 25 C. The README's own heat table shows 2.324 and 2.326.

Correct: "at 2.32 and 2.33 A h".

---

## Low severity: imprecisions

### L4. (2) Range lower bound
README, 21700: "The spread in (b) is 25 to 27 % below the radial model's." The data give 25.54 to 26.60 %, so the rounded range is "26 to 27 %".

### L5. (2) Range wider than the data
README, 4680: "The axial-to-radial ratio of (b) stays at 0.32 to 0.33." The six values run from 0.32406 to 0.32473, and every one rounds to 0.32. Correct: "stays at 0.32 (0.324 to 0.325)".

### L6. (2) Single 4680 value where the 21700 gets a range
README, V1 (a) row: "...4.3 to 4.5 % below the radial model in the 21700 and 5.6 % in the 4680."
- The 21700 figure spans the six heats (verification.json: 4.27 to 4.50 %).
- The 4680 figure, 5.59 %, is the 2C, minus 5 C value only. Over the six heats the 4680 runs from 4.30 % (3C, 25 C) to 5.73 % (1.25C, minus 5 C).

Correct: "4.3 to 5.7 % in the 4680".

### L7. (2) Hottest point offset
README: "...within 1.5 mm in (a)". The hottest node in (a) is at z = 36.576 mm, which is 1.526 mm above mid-height (one mesh layer). It is 5.9e-5 K hotter than the mid-height axis node. Correct: "1.53 mm (one mesh layer) above mid-height in (a)".

### L8. (2) Two maxima merged into one
README: "In the symmetric cases the two ends differ by at most 0.024 K (2.5 % of the axial difference)".
- The largest absolute gap is 0.0244 K, in 4680 (b) at 3C and minus 5 C. That is 0.38 % of that case's axial difference.
- The largest relative gap is 2.51 %, in 21700 (a), where the gap is 0.008 K.

Correct: "by at most 0.024 K, and by at most 2.5 % of the axial difference".

### L9. (2) Reading error of Fig. 7a
README, V4: "The reading error is 0.09 K". That is Fig. 5's value (0.091 K). Fig. 7a's is 0.287 K (v4.json). The conclusion is unaffected.

### L10. (2) Independent recomputation figures, and its verdict line
- README: "The core-to-surface differences agree within 0.14 %". The (a) value is 0.143 % (comparison.md).
- Note: "An independent axisymmetric solver agrees within 0.14 %". Across all compared quantities the largest difference is 0.149 % (T_core_mid in (a)). The filed REPORT.md itself says "within 0.15 %".
- README: "Its own grid error is below 1e-4 K". That holds for the core-to-surface difference. The largest grid-error estimate is 1.3e-4 K (4680 (a) volume mean, REPORT.md).
- comparison.md's verdict line reads "DISAGREEMENT" because the 4680 (a) count differs (45 against 44). The README reports this in its table notes but not under Verification.

### L11. (2) "Warms the cell by about 27 K"
README, P5 paragraph: "At h = 25 that heat warms the cell by about 27 K". In (d) at 2C and minus 5 C the roll mean ends at 26.40 C, which is 31.4 K above ambient. The 26.9 K figure is the excess over case (a). The table note has it right ("27 K warmer than (a)").

### L12. (2) Hollow core
README, V4: "its innermost unit at 0.165 R, a hollow core of about 1.74 mm". The Fig. 5 curves start at 0.165 to 0.169 R (v4.json paper_x_range). That gives a core radius of 1.74 to 1.78 mm, and three of the four curves give 1.78 mm. The text should also say this is a radius.

### L13. (4) q differs between predictions.md and the README
- predictions.md: "q = 1.55e5 W/m³".
- README: "q = 1.56e5 W/m^3".
- heat_summary.csv gives q_vol_mean = 155,527 W/m^3, which rounds to 1.56e5. predictions.md truncates.

predictions.md is frozen, so the README could add a short note.

### L14. (5) The 4680 difference in the note
Note, What it means: "its 30 C difference across the 4680". The paper (p. 4) says "a temperature difference exceeding 30°C", and its Fig. 7a peaks at 37.5 K (v4.json). The README has it right ("more than 30 C"). Correct: "its difference of more than 30 C".

### L15. (3) What V4 can quantify
README, What differs: "...so the property difference is quantified only through V4." V4 cannot separate the property difference from differences in heat and duration (H1). It quantifies only their combined effect on the unit differences.

### L16. (3) The 3C cut-off mechanism
README: "...because Chen2020's slow diffusion in the positive particles saturates their surfaces." No deposited file records particle-surface concentrations. The heat CSVs hold current, voltage, the heat terms, the lumped temperature and the capacity. The explanation is plausible (positive diffusivity 4e-15 m^2/s), but it should be marked as an interpretation or backed with saved output.

### L17. (4) P3 scorecard wording
- README: "Mean offset 1.19 K and every offset positive, but the offsets run from 0.48 to 1.59 K and the spread falls 27 % (4.17 to 3.06 K)".
- Note: "Mean 1.19 K, but 0.48 to 1.59 K, and the spread falls 27 %".

predictions.md lists the offset range as "Also reported, without being scored". Clauses 1 and 2 held (scorecard.json), and P3 failed on clause 3 alone: the spread changes by -26.6 % against a 20 % limit. The "but" presents an unscored item as a reason for the failure.

All five verdicts follow predictions.md, and src/analyse.py implements the rules exactly (inclusive bounds for P1 and P3 clause 1, strict ones elsewhere).

### L18. (4) D8 describes a conductivity tensor the code no longer uses
DECISIONS D8: "the roll's conductivity tensor k_along I + (k_across - k_along) e_r e_r^T, so that conduction along the layers acts axially and around the circumference".

src/cell3d.py (k_theta="across" by default; every file in results/fields has k_theta "across") applies k_across around the circumference, as D13 records. D8's "What changes" list does not mention this and does not point to D13.

### L19. (4) D12 omits the heat of mixing
D12: "The secondary results use the ORegan2022 heat and the minus 5 C properties for the minus 5 C runs". D3, predictions.md and the README also count the heat of mixing as a secondary input.

### L20. (4) "How to run" does not reproduce all reported results
It has no command for the 10 secondary resolved runs whose results the README reports ("The resolved cell with these inputs, at 2C"). Those runs are 21700 (a) and (b) with the mixing, ORegan2022 and minus 5 C property inputs. They need, for example:
- `python3 src/run3d.py --cell 21700 --bcs a,b --heats Chen2020_m5C_2C_mixing,Chen2020_p25C_2C_mixing,ORegan2022_m5C_2C,ORegan2022_p25C_2C`
- `python3 src/run3d.py --cell 21700 --bcs a,b --props cold --heats Chen2020_m5C_2C`

It also omits verification/v0_checks.py, check_1d_steps.py and test_mesh.py.

### L21. (4) The same phrase is used for two different metrics
- README, 21700 bullets: "(a) lies 3.2 to 3.3 % below the radial model". This is the core-to-surface difference.
- README, V1: "the mid-height profile lies 4.3 to 4.5 % below the radial model". This is the largest profile deviation divided by the one-dimensional core-to-surface difference.

Both are correct, but read side by side they look contradictory. Name the metric in each.

### L22. (4) Figure 1 caption (note)
- Panels (a) and (b) show all four boundary conditions against the radial model.
- Panel (c) has two sub-panels, the M50 and the 4680.
- The caption mentions neither, and the panel letters (a) to (c) reuse the boundary-condition letters.

### L23. (4) Software list
The README's software list omits matplotlib (3.11.2 installed). Every unit average and profile is computed through src/mesh.py's FieldSampler, which uses matplotlib.tri, and src/make_figure.py uses it too.

### L24. (4) A second post-registration code change goes unmentioned
README: "One decision came after the predictions (DECISIONS.md D13)." The D13 commit (214ba46) also changed how the field sampler handles points just outside the inscribed outer polygon (src/mesh.py).
- The change is a fix that let sampling run; the earlier nudge would have raised an error.
- No field had been sampled before it.
- It does not change the physics, but it is a post-registration code change the text does not mention.

### L25. (4) An attribution in D4 cannot be traced
DECISIONS D4: "The thermal-lever study recorded that the two-cell study gives no primary table for these values." No such statement appears in that study's README.md or DECISIONS.md (/home/claude/tl). The fact itself holds: the two-cell study's D10 gives 9 g and 500 J/kgK without a source.

### L26. (6) Internal labels and references an outside reader cannot resolve
- "The thermal-lever study" is cited nowhere (README, What differs; DECISIONS D3, D4).
- "The brief" is not in the deposit; it appears about 20 times across the README, DECISIONS and predictions.md.
- "In this session" is process language (README, What differs; DECISIONS D2).

There is no "Pilot A" or "Pilot B" style label anywhere. The only "pilot" is in the two-cell study's published title (README source 5), and that is a citation.

---

## Notes (no change to the text needed, or outside the audited files)

- N1. V4 ran after the predictions: images were extracted at 11:42 and v4.json was written at 12:54. The brief places V4 before the predictions "if the PDF is available". D11's wording ("if the paper's PDF becomes available") implies it was not available then. One sentence in "What differs from the brief" would close this.
- N2. The same pair of numbers is quoted against two bases: "overstates the unit-to-unit spread by 36 % (4.17 against 3.06 K)" and "the spread falls 27 % (4.17 to 3.06 K)". Both are right.
- N3. Metadata.
  - .zenodo.json "license" is MIT only, while its description puts the results under CC BY 4.0. Zenodo takes one licence field, so this is acceptable.
  - CITATION.cff's keywords lack "4680".
  - There is no CC BY 4.0 licence file.
- N4. verification/v4/jes-000.jpg to jes-004.jpg (the paper's figures) sit in the working tree. They are git-ignored, so the README's "They are not redistributed here" holds for a release made from git. A deposit made by zipping the folder would include them.
- N5. inputs/twocell_resolved_cell2.py imports lumped_two_cell and mesh_cell2, which are not in inputs/. It is a faithful copy (byte-identical to the two-cell study at 2b35ac7), but it cannot be imported here. Only src/cell3d.py is used.

---

## Checked and found correct

- **Every value in the README's three results tables and the heat table**, against results_3d.csv, comparison_vs_a.csv, the units_*.csv files and heat_summary.csv. This covers all six heats in both cells: core-to-surface and axial differences, ratios, mean, minimum and maximum offsets, counts over 1 K and spreads. Full precision was checked where the rounding was borderline (6.742, 0.377, 1.001, 1.283, 1.458, 3.439, 2.890).
- **The figures in the README's Result, notes and secondary bullets.** These include:
  - 0.29 K, 7 % and 1.2 K, 6 %; 37 % (1.28 of 3.45 K); 32 % (3.44 of 10.61 K); 43 % with tabs.
  - 0.48 to 1.59 K (mean 1.19 K, 31 of 45); 1.95 to 11.34 K (mean 7.96 K); 36 % and 98 % at 2C, minus 5 C.
  - 16 %, 1.00 K and 25 units; 42 % and 7.18 K; 27 K warmer than (a); 4.08 K and 45 units.
  - The 4680 (a) unit at 1.00 K (1.00283 K).
  - 3.2 to 3.3 %; 15 to 16 %; 0.27 to 0.28; 3.8 to 5.1 %; 38 to 45 %; 44 to 50 %.
  - The secondary results: 38 %, 6.19 and 26.47 K, 166 s and 0.46 A h, 5.13 K, 4.9 and 5.7 %, 0.01 %, 0.371, 0.367, 0.372 and 0.370, 20 to 27 %, 1.68 K with 39 units, 1.25 K with 32 units, and 0.41 K.
  - The heat of mixing adding 36 to 54 %.
  - Every difference peaking at the end of discharge, in all 54 runs.
- **The cause of the (a) deviations.** "These small differences come from the can's end caps, which carry heat from the ends of the roll to the side" is confirmed. In the auditor's re-solve, end-cap conduction alone gives 4.117 K, and end-cap capacity alone gives 4.263 K against the radial model's 4.264 K (evidence/end_side_split.log).
- **The verification records.**
  - V0: the relaxation conserves energy to 3.6e-14. The sampler was re-run with test_mesh.py and is exact to 2.8e-14, with the mesh identical to the two-cell study's at refine 1 and 2.
  - V1: 0.147 %. D13: 4.192 and 4.270 K, 1.7 %, the deficit largest at the axis and zero at the surface, and the first ring carrying 4 segments.
  - V3: -0.09 % and -0.08 %, -0.9 % and -0.3 %, 0.004 K, 297,057 nodes.
  - V4: the digitised values and ratios 2.2, 1.7, 1.8, 2.8 and 2.0, and the 10 % hollow-core reduction (9.6 to 10.2 %). Fig. 5 has exactly the four curves used.
  - Independent recomputation: 3.176, 18.166 and 10.611 K; counts 0 and 31; 44 in the 4680 (a).
- **The pre-registration record.**
  - Commit b92f9a8 dates from 11:11:54 UTC. The remote-ref log shows the push at 11:12:48, and GitHub's activity record shows 11:12:47.
  - The repository is public.
  - The heat runs, the one-dimensional runs and V0 predate the commit. The first field file (the superseded V1 run) was written at 11:19:26.
- **DECISIONS against the code** (except L18 and L19). This covers D3, D4 (60.68, 4.50, 65.18, 329.13 and 12.53 J/K; 841.7 J/(m^2 K); 4.4 % and 16 %), D5 (0.2344 and 0.2072 mm), D6 (the volume ratio of 5.42), D7, D9 (6.23 mW/K applied as a Robin condition over the patch, which keeps its convection) and D10. D10's definitions match src/:
  - the axial difference is the larger of the two ends;
  - the core-to-surface difference is the axis node minus the mean of the surface-ring nodes at z = H/2;
  - the offset is the one-dimensional temperature minus the three-dimensional one;
  - unit averages use 10 Gauss radii, a 0.1 mm step in height, 4 angles and the weight r;
  - both models step at t_end / ceil(t_end / 1 s).
- **The two-cell study.** The four `twocell_*` files are byte-identical copies. Its D7, D9, D10, D11 and D24 say what the text cites.
- **Every statement attributed to the paper, except M4 and L14:**
  - 3.45 % at 3C and 25 C, and 11.32 % at 2C and minus 5 C (p. 3, restated on p. 4);
  - "exceeding 30°C" at 2C and minus 5 C (p. 4);
  - 45 units, about 111 units, 46 mm by 80 mm, h = 400, and minus 5 C and 25 C (all p. 3);
  - Eq. 2 on p. 2, Eq. 3 and 4 on p. 3, Fig. 5 on p. 5, Fig. 7 on p. 6, and the 2.6 V cut-off on p. 2;
  - ref. 33 as Yang and Tartakovsky, J. Power Sources 664, 238948 (2026), with DOI 10.1016/j.jpowsour.2025.238948 confirmed on Crossref;
  - the quotation "Its thermal properties are reported in Ref. 33.", which is exact (the source's footnote marker "b)" is omitted).
- **Citations.** Chen et al. 2020 (J. Electrochem. Soc. 167, 080534, doi 10.1149/1945-7111/ab9050), O'Regan et al. 2022 (Electrochim. Acta 425, 140700, doi 10.1016/j.electacta.2022.140700) and Sulzer et al. 2021 (J. Open Res. Softw. 9, 14, doi 10.5334/jors.309) match PyBaMM's CITATIONS.bib in authors, title, journal, volume, article number, year and DOI.
- **Software versions.** PyBaMM 26.9.0.0, scikit-fem 12.0.2, pyamg 5.3.0, NumPy 2.5.3 and SciPy 1.18.1 match the installed packages.
- **Style.**
  - There are no em dashes, en dashes or dash entities in any audited file, the note HTML or the note PDF.
  - All four quotations are introduced after a colon with their original capitalisation: README and D3, "the one already used here", matching the brief; D2, the ref. 33 sentence; predictions.md, the brief's reason, which matches the brief word for word.
