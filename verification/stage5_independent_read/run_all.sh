#!/bin/bash
# Independent read of Stage 5: rerun every check on the files as they stand. Each step waits for memory
# (./memgate.sh: at or below 4.6e9 bytes in use), runs with one thread at nice 10, and writes to ./out/.
# Usage (from this folder): ./run_all.sh            all checks
#                           ./run_all.sh quick      without the PyBaMM runs (mesh check and single-unit re-runs)
set -u
cd "$(dirname "$0")"
mkdir -p out
run() { echo "=== $(date -u +%H:%M:%S) $*"; ./memgate.sh python3 -I -B "$@" > "out/log_$(echo "$*" | tr ' /' '__').txt" 2>&1; echo "    exit $?"; }
run ir_inventory.py
run ir_p1_v1.py
run ir_readings.py
run ir_v5_v6.py
run ir_v2_v4.py
if [ "${1:-}" != "quick" ]; then
  run ir_single_rerun.py both
  run ir_single_rerun.py p9
  run ir_mesh.py 20
  run ir_mesh.py 80
  run ir_mesh.py 20 explicit
fi
echo "=== $(date -u +%H:%M:%S) done"
