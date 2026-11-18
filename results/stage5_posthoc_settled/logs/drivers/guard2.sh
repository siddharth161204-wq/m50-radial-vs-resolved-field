#!/bin/bash
# D36's guard: a run process above G MB, or one in which no thermal step has ended for STALL seconds (its heartbeat
# file, touched after every step), is stopped and its job recorded as stalled.
SP=/tmp/claude-0/-home-claude/a52839dc-9584-53cc-a238-428518c66a3f/scratchpad
G=${1:-3000}; STALL=${2:-1800}; END=$(( $(date +%s) + ${3:-7000} ))
while [ $(date +%s) -lt $END ]; do
  now=$(date +%s)
  ps -eo pid=,etimes=,rss=,args= | grep "stage5_posthoc_settled.py runs" | grep -v -E "timeout |grep " | while read -r pid et rss rest; do
    mb=$((rss / 1024))
    job=$(echo "$rest" | sed -n 's/.*--job \([^ ]*\).*/\1/p')
    hb=$SP/heartbeat/$(echo "$job" | tr ':/' '__')
    why=""
    [ $mb -gt $G ] && why="at $mb MB"
    if [ -z "$why" ] && [ -f "$hb" ] && [ "$et" -gt "$STALL" ]; then
      age=$(( now - $(stat -c %Y "$hb") ))
      [ $age -gt $STALL ] && why="no step ended for $age s"
    fi
    if [ -n "$why" ]; then
      echo "$job" >> $SP/d36_stalled
      echo "### $(date -u +%H:%M:%S) guard: stopped $job (pid $pid), $why" >> $SP/logs36/guard.log
      kill -TERM $pid
    fi
  done
  sleep 5
done
