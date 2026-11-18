# Logs of the post hoc bracket at a settled particle mesh (DECISIONS.md D36)

The runs were made on a machine with a memory limit of 6.27 GB shared by all jobs, two cores, and two hours per background job. These files record how they ran. They add nothing to the procedure: every reading is in `../readings_r160.json` and `../mesh_summary.json`, and every run in `../runs_r160/`.

- `meshA.log`, `meshB.log`, `mesh640.log`: the mesh study (`src/stage5_posthoc_settled.py mesh`). It covers one DFN held at the ambient at 160 to 1,280 points along each particle's radius, with each trial of the rate searches.
- `wD.log`: the first worker of the coupled runs. Its first run, the main case under the resolved kernel without garbage collection, was stopped by the memory limit (exit 137, 09:37 UTC). It was run again after collection was added and finished.
- `slot1.log`, `slot2.log`: the two processes that worked through `queue.txt` in rounds that end before the two-hour limit. Each claimed a job before running it, ran it in its own process, and resumed a stopped run from its saved state. A line `exit 137` is a stop by the memory limit. A line `stopped by the memory guard` or `stopped by the guard` is a stop by `guard.log`'s guard. A line `at its time limit` is the end of a round.
- `guard.log`: runs stopped by the guard, which stops a process above 3 GB (2.6 GB before 11:42 UTC) or one in which no thermal step has ended for 30 minutes.
- `mem36.log`: the memory of the job group and of the run processes, every 10 s.
- `events.log`: what each stop was and how the run went on.
- `queue.txt`, `finished.txt`, `failed.txt`, `stalled.txt`: the job list, the jobs finished, each failed attempt (a job with two is not started again), and the jobs stopped by the guard. `retry:<job>` is a further run of a job that had failed twice, made after the cause was fixed (D36).
- `drivers/`: the scripts that ran the jobs and the tests named in D36:
  - `wD.sh`, `runjob.sh`, `slot.sh`, `slotrun.sh`, `slotrun2.sh`: the job drivers, in the order they were used.
  - `guard.sh`, `guard2.sh`: the guards.
  - `resume_test.py`: a stored registered run, stopped twice and resumed, against the stored run.
  - `storage_test.py`, `storage_test160.py`: the solver keeping only each step's first and last states, against a stored registered run and at 160 points.
  - `stall_diag.py`: the groups' stoichiometries at the last saved state of the stopped main case under the radial kernel.
  - `coupled_cost_test.py`, `coupled_mem_test.py`: the coupled model's cost and memory at 160 points.
  - `mesh_variants.py`: the meshes graded toward the surface.
