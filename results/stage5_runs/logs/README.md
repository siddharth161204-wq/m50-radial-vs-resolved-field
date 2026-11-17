# Logs of the Stage 5 runs

These are the console logs of the processes that made Stage 5's kernels and runs, kept as the record behind DECISIONS.md D35 (the machine's limits, the jobs that were stopped and run again, the stored trials). Local paths are replaced by `<scratch>`. Times are UTC.

- `kq_*.log`: the resolved kernels (`src/stage5_kernels.py`). `kq_4680b.log` ends at step 2,000 of the 4680's main-grid kernel, where the two-hour limit stopped it. `kq_4680c.log` shows its second run, stopped after step 1,600 (its loop ends at 04:42:39) and resumed from the state saved at step 1,600. `kq_21700c.log` shows the M50's 30-group kernels stopped by the memory guard (`watchdog.log`), and `kq_21700d.log` their later run.
- `q_reg21700.log`, `q_singles.log`, `q_cl_21700_reg.log`: the first runs, before the runs were split into one job per kernel. `q_singles.log` holds every single-unit search; `q_reg21700.log` stops part way through the M50's ORegan2022 charges, and `q_cl_21700_reg.log` before the first trial of a coupled search; both were run again in the split jobs.
- `memtest_job*.log`, `memtest_rss*.log`: three jobs run one per process while their memory was measured (the resident memory in MB every 2 s), before the queue was changed to run one job per process: the 4680's ORegan2022 discharge under one-way heat and the end-corrected kernel, and its ORegan2022 charges under the radial and resolved kernels.
- `wA.log`, `wB.log`: the two processes that worked through the jobs of `src/stage5_queue.py`, one job per process. Each `===` line starts a job; each search prints its trials and its reading. A line `time budget used` ends a round before the two-hour limit.
- `wC.log`: the 30-group runs of check V4, run alone. `mem30.log`: their memory.
- `v5.log`: check V5's second route. `posthoc_mesh.log`: the post hoc particle-mesh check of D35.
