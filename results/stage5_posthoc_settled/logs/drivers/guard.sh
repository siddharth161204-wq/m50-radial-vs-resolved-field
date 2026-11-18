#!/bin/bash
# D36's memory guard: a run process above GUARD MB is stopped and its job recorded as stalled (a step whose solver
# took so many internal steps that their stored states outgrew the memory); this keeps one stalled run from taking
# the memory limit, and the other runs, with it.
SP=/tmp/claude-0/-home-claude/a52839dc-9584-53cc-a238-428518c66a3f/scratchpad
G=${1:-2600}; END=$(( $(date +%s) + ${2:-7000} ))
while [ $(date +%s) -lt $END ]; do
  ps -eo pid=,rss=,args= | grep "stage5_posthoc_settled.py runs" | grep -v -E "timeout |grep " | while read -r pid rss rest; do
    mb=$((rss / 1024))
    if [ $mb -gt $G ]; then
      job=$(echo "$rest" | sed -n 's/.*--job \([^ ]*\).*/\1/p')
      echo "$job" >> $SP/d36_stalled
      echo "### $(date -u +%H:%M:%S) guard: stopped $job (pid $pid) at $mb MB" >> $SP/logs36/guard.log
      kill -TERM $pid
    fi
  done
  sleep 3
done
