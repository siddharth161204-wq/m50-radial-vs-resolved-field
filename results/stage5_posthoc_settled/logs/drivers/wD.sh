#!/bin/bash
# Worker D: D36's coupled and single-unit runs at a uniform 160 points per particle radius, one job per process, in
# the order Sid set (the M50's main case, the 4680, the M50's two charges first). A job starts only if its expected
# time fits before the two-hour limit of a background job; a search keeps its finished trials in a store.
SP=/tmp/claude-0/-home-claude/a52839dc-9584-53cc-a238-428518c66a3f/scratchpad
cd /home/claude/m50-radial-vs-resolved-field
export OMP_NUM_THREADS=1 D36_TRIAL_CACHE=$SP/trial_cache36
echo 500 > /proc/self/oom_score_adj
N=160
START=$(date +%s)
CAP=${1:-112}          # minutes after which no job may still be running
# job and its expected minutes
JOBS=(
  "discharge:21700_b_m5C_2C:resolved 15" "discharge:21700_b_m5C_2C:radial 15" "discharge:21700_b_m5C_2C:corrected 15"
  "discharge:4680_b_m5C_2C:resolved 20" "discharge:4680_b_m5C_2C:radial 25" "discharge:4680_b_m5C_2C:corrected 20"
  "charge:21700:resolved 80" "charge:21700:radial 80" "charge:21700:corrected 80"
  "discharge:21700_b_p25C_3C:resolved 45" "discharge:21700_b_p25C_3C:radial 45" "discharge:21700_b_p25C_3C:corrected 45"
  "discharge:21700_b_p25C_2C:resolved 80" "discharge:21700_b_p25C_2C:radial 80" "discharge:21700_b_p25C_2C:corrected 80"
  "charge:4680:resolved 80" "charge:4680:radial 80" "charge:4680:corrected 80"
  "p9:21700 0" "p9:4680 0"
  "discharge:21700_a_m5C_2C:resolved 15" "discharge:21700_a_m5C_2C:radial 15"
  "discharge:21700_b_p25C_1.25C:resolved 110" "discharge:21700_b_p25C_1.25C:radial 110" "discharge:21700_b_p25C_1.25C:corrected 110"
)
DONE=$SP/d36_done
touch $DONE
for je in "${JOBS[@]}"; do
  job=${je% *}; est=${je##* }
  grep -qx "$job" $DONE && continue
  el=$(( ($(date +%s) - START) / 60 ))
  if [ "$est" -gt 0 ] && [ $((el + est)) -gt $CAP ]; then echo "### $(date -u +%H:%M:%S) $job needs about $est min, $el min used: stopping"; exit 0; fi
  if [ "$est" -eq 0 ] && [ $el -gt $((CAP - 20)) ]; then echo "### $(date -u +%H:%M:%S) no time left for $job: stopping"; exit 0; fi
  echo "### $(date -u +%H:%M:%S) start $job"
  if [ "$est" -eq 0 ]; then
    # a search: stopped by the time limit it resumes from its stored trials in the next round
    timeout $(( (CAP - el - 2) * 60 )) python3 -u src/stage5_posthoc_settled.py runs --points $N --job $job 2>&1 | grep --line-buffered -v C_CONTIG
  else
    python3 -u src/stage5_posthoc_settled.py runs --points $N --job $job 2>&1 | grep --line-buffered -v C_CONTIG
  fi
  rc=${PIPESTATUS[0]}
  if [ $rc -eq 0 ]; then echo "$job" >> $DONE; echo "### $(date -u +%H:%M:%S) done $job"
  else echo "### $(date -u +%H:%M:%S) exit $rc $job"; [ $rc -eq 124 ] && exit 0; fi
done
echo "### $(date -u +%H:%M:%S) worker D: every job done"
