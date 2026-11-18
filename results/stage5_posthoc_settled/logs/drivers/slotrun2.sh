#!/bin/bash
# A D36 slot: works through d36_queue in order, one job per process, claiming each job first so that two slots
# never run the same one. Every run saves its state every 20 steps (resumable_run in src/stage5_posthoc_settled.py),
# so a job stopped at the slot's time limit resumes where it stopped in the next round. Started as a background
# task; stops CAP minutes after its start (the limit of a task is two hours). Each job touches a heartbeat file
# after every step, which guard2.sh reads. A job written retry:<job> runs <job> again under its own name.
SP=/tmp/claude-0/-home-claude/a52839dc-9584-53cc-a238-428518c66a3f/scratchpad
cd /home/claude/m50-radial-vs-resolved-field
export OMP_NUM_THREADS=1 D36_TRIAL_CACHE=$SP/trial_cache36 D36_CHECKPOINTS=$SP/ckpt36
echo 500 > /proc/self/oom_score_adj
SLOT=$1; CAP=${2:-113}
START=$(date +%s)
QUEUE=$SP/d36_queue; FIN=$SP/d36_finished; FAIL=$SP/d36_failed; CL=$SP/d36_claims
mkdir -p $CL; touch $FIN $FAIL
key() { echo "$1" | tr ':/' '__'; }
claim() {
  local d=$CL/$(key "$1")
  if mkdir "$d" 2>/dev/null; then echo $$ > "$d/pid"; return 0; fi
  local p; p=$(cat "$d/pid" 2>/dev/null)
  if [ -n "$p" ] && kill -0 "$p" 2>/dev/null; then return 1; fi
  echo $$ > "$d/pid"; return 0                     # a claim left by a slot that has stopped
}
release() { rm -rf "$CL/$(key "$1")"; }
mapfile -t JOBS < <(grep -v '^#' $QUEUE | grep -v '^$')
for job in "${JOBS[@]}"; do
  grep -qxF "$job" $FIN && continue
  [ "$(grep -cxF "$job" $FAIL)" -ge 2 ] && continue          # two failed attempts: left for the report
  grep -qxF "$job" $SP/d36_stalled 2>/dev/null && continue    # stopped by the guard: left for the report
  el=$(( ($(date +%s) - START) / 60 )); left=$((CAP - el))
  if [ $left -lt 6 ]; then echo "### $(date -u +%H:%M:%S) slot $SLOT: time up"; exit 0; fi
  claim "$job" || continue
  stalled_before=$(grep -cxF "${job#retry:}" $SP/d36_stalled 2>/dev/null)
  export D36_HEARTBEAT=$SP/heartbeat/$(key "${job#retry:}"); mkdir -p $SP/heartbeat
  echo "### $(date -u +%H:%M:%S) slot $SLOT start $job ($left min left)"
  t0=$(date +%s)
  timeout $((left * 60)) python3 -u src/stage5_posthoc_settled.py runs --points 160 --job "${job#retry:}" < /dev/null 2>&1 | grep --line-buffered -v C_CONTIG
  rc=${PIPESTATUS[0]}; mins=$(( ($(date +%s) - t0) / 60 ))
  release "$job"
  if [ $rc -eq 0 ]; then echo "$job" >> $FIN; echo "### $(date -u +%H:%M:%S) slot $SLOT done $job ($mins min)"
  elif [ $rc -eq 124 ]; then echo "### $(date -u +%H:%M:%S) slot $SLOT stopped $job at its time limit ($mins min); it resumes"; exit 0
  elif grep -qxF "${job#retry:}" $SP/d36_stalled 2>/dev/null && [ "$(grep -cxF "${job#retry:}" $SP/d36_stalled)" -gt "$stalled_before" ]; then [ "$job" != "${job#retry:}" ] && echo "$job" >> $SP/d36_stalled; echo "### $(date -u +%H:%M:%S) slot $SLOT: $job stopped by the guard ($mins min)"
  else echo "$job" >> $FAIL; echo "### $(date -u +%H:%M:%S) slot $SLOT exit $rc $job ($mins min)"; fi
done
echo "### $(date -u +%H:%M:%S) slot $SLOT: no job left for it"
