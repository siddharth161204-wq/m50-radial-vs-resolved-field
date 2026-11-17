# Logs of the Stage 5 runs

These are the console logs of the processes that made Stage 5's kernels and runs, kept as the record behind DECISIONS.md D35 (the machine's limits, the jobs that were stopped and run again, the stored trials). Local paths are replaced by `<scratch>`. Times are UTC.

- `kq_*.log`: the resolved kernels (`src/stage5_kernels.py`). `kq_4680b.log` ends where the two-hour limit stopped the 4680's main-grid kernel; `kq_4680c.log` shows its second run, stopped at step 1,600 and resumed from its saved state. `kq_21700c.log` shows the M50's 30-group kernels stopped by the memory guard (`watchdog.log`), and `kq_21700d.log` their later run.
- `q_reg21700.log`, `q_singles.log`, `q_cl_21700_reg.log`: the first runs, before the runs were split into one job per kernel (the single-unit searches are in `q_singles.log`).
- `wA.log`, `wB.log`: the two processes that worked through the jobs of `src/stage5_queue.py`, one job per process. Each `===` line starts a job; each search prints its trials and its reading. A line `time budget used` ends a round before the two-hour limit.
- `wC.log`: the 30-group runs of check V4, run alone. `mem30.log`: their memory.
- `v5.log`: check V5's second route. `posthoc_mesh.log`: the post hoc particle-mesh check of D35.
