#!/bin/bash
# Wait until the memory in use by the shared cgroup is at or below 4.6e9 bytes, then run the given command
# with one thread and lowered priority (the brief's rules for this machine).
MEMF=$(ls -d /sys/fs/cgroup/memory/process_api/*/claude-code-bash | head -1)/memory.usage_in_bytes
while [ "$(cat $MEMF)" -gt 4600000000 ]; do sleep 20; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec nice -n 10 "$@"
