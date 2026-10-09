#!/bin/sh
# Runs every browser suite and prints one line per suite. Usage: sh tests/run_all_e2e.sh
cd "$(dirname "$0")/.." || exit 1
for t in e2e_browser e2e_prompt e2e_forge e2e_shell e2e_pages; do
  printf "%s " "$t"
  python "tests/$t.py" 2>&1 | grep -a -E "^FAIL|checks passed|Error" | head -5
done
