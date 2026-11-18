#!/bin/bash
# One D36 job at 160 points per particle radius, in its own process and its own background task (so that each job
# has the whole two-hour limit of a task). A finished job is recorded in d36_done. A second argument (minutes) stops
# the job by then: a search resumes from its stored trials when it is started again.
SP=/tmp/claude-0/-home-claude/a52839dc-9584-53cc-a238-428518c66a3f/scratchpad
cd /home/claude/m50-radial-vs-resolved-field
export OMP_NUM_THREADS=1 D36_TRIAL_CACHE=$SP/trial_cache36
echo 500 > /proc/self/oom_score_adj
job=$1; tmo=${2:-0}
if grep -qx "$job" $SP/d36_done 2>/dev/null; then echo "### $(date -u +%H:%M:%S) already done $job"; exit 0; fi
echo "### $(date -u +%H:%M:%S) start $job"
t0=$(date +%s)
if [ "$tmo" -gt 0 ]; then
  timeout $((tmo * 60)) python3 -u src/stage5_posthoc_settled.py runs --points 160 --job "$job" 2>&1 | grep --line-buffered -v C_CONTIG
else
  python3 -u src/stage5_posthoc_settled.py runs --points 160 --job "$job" 2>&1 | grep --line-buffered -v C_CONTIG
fi
rc=${PIPESTATUS[0]}
mins=$(( ($(date +%s) - t0) / 60 ))
if [ $rc -eq 0 ]; then echo "$job" >> $SP/d36_done; echo "### $(date -u +%H:%M:%S) done $job ($mins min)"
else echo "### $(date -u +%H:%M:%S) exit $rc $job ($mins min)"; fi
