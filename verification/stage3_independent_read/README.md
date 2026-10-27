# Stage 3: the independent read

A separate checking agent did this read before the note's Stage 3 section was written. It was given the files and the rules (predictions_stage3.md, D19 and D20), not the author's working. It reads files only, and its numerical scripts import nothing from `src/` except `blas_check.py`, which repeats one run.

## First pass (on commit b7af681)

**What it did.** It recomputed from the stored histories:
- every mean and end-of-discharge error in all 40 runs;
- the scorecard at 0.1x, 1x and 10x;
- all 49 rows of `results/stage3_errors.csv`;
- the checks file.

It also compared the truth series with Stage 1's archived fields, and the forecast with Stage 1's radial output (`check.py`, `check_truth.py`).

**Result.** No value or verdict was wrong. It found:
- the `level` label wrong in 14 stored runs;
- the end sink of the insulated-ends runs evaluated at h = 400 instead of 0;
- the nine insulated-ends rows of the end-corrected estimator copied from the estimator without saying so;
- "exactly" in V2 and V4 holding to round-off.

It also noted that P5 and P7 rested on stored means. Their series had not been kept.

**Corrections.** All of these are corrected or recorded under D21. The runs behind P5 and P7 were repeated with their series kept (`results/stage3_series.json`).

## Second pass

**What it did** (`check_pass2.py`):
- recomputed P5 and P7 from the series;
- compared the relabelled runs, the regenerated table and the scorecard with b7af681;
- read every number in the README section, D21, the archive description and the draft note against the files.

**Result.** All recomputations matched, and the six repeated runs that have stored histories match them bit for bit. In the texts it found:
- one wrong number, a sensitivity value of 0.875 K that is 0.874 K;
- three ranges that did not match the cases their sentences name;
- three claims the files could not support.

**Corrections.** All of them were corrected before the note was written.

## Third pass

**What it did.** It read the corrected texts, including the note's Stage 3 section and the release text. It also checked the D21 statement on BLAS threads by repeating one run (`blas_check.py`; `blas_one.json` with one thread, `blas_default.json` with two).

**Result.** Nothing was wrong. One sentence in the README claimed bit-for-bit reproduction for all Stage 3 runs and was narrowed to the seven runs repeated.

## How to run

```
python3 check.py
python3 check_truth.py
python3 check_pass2.py
OMP_NUM_THREADS=1 python3 blas_check.py one
```

- `check_pass2.py` reads commit b7af681 through git, so it needs the repository's history.
- The `*_output.txt` files are the outputs on the final commit, after the corrections.
