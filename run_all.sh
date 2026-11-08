#!/usr/bin/env bash
# run_all.sh - Linux/Git-Bash version of run_all.bat (needs vlog/vsim on PATH)
set -u
mkdir -p logs; [ -d work ] || vlib work >/dev/null
fail=0; count=0
for tb in tb/tb_*.v; do
  name=$(basename "$tb" .v); [ "$name" = "tb_template" ] && continue
  count=$((count+1))
  if ! vlog -quiet -lint src/*.v "$tb" > "logs/${name}_compile.log" 2>&1; then
    echo "  $name   COMPILE ERROR"; fail=1; continue; fi
  vsim -c "$name" -do "run -all; quit -f" > "logs/$name.log" 2>&1
  if grep -q "ALL PASS" "logs/$name.log"; then echo "  $name   ALL PASS"; else echo "  $name   FAILED"; fail=1; fi
done
[ $fail -eq 0 ] && { echo "ALL $count TESTBENCHES PASSED"; exit 0; } || { echo "SOME TESTBENCHES FAILED"; exit 1; }
