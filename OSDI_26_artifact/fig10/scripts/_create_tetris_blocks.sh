#!/bin/bash

# Generate per-page-group "base blocks" via `py_scripts/block_tetris.py`.
#
# Usage:
#   bash scripts/_create_tetris_blocks.sh <start_group> <end_group>
#
# This spawns one Python process per page group in the requested range.
# The Python code is CPU-heavy and uses multiprocessing.

# Load config from config.py
eval $(cd py_scripts && python3 -c "
import config
print(f'page_unit={config.TARGET_UNIT_PAGES}')
print(f'start_address={config.START_ADDRESS_HEX}')
print(f'start=0')
print(f'end={config.NUM_PAGE_GROUPS - 1}')
")

cleanup() {
    echo "SIGINT received. Terminating all child processes..."
    pkill -P $$  # Kill all child processes of the current script
    wait         # Wait for all child processes to terminate
    echo "All child processes terminated."
    exit 1       # Exit with a non-zero status to indicate interruption
}

# Set up the trap for SIGINT (Ctrl+C)
trap cleanup SIGINT

start=$1
end=$2

for page_index in $(seq $start 1 $end); do
    python3 py_scripts/block_tetris.py $page_index $page_unit $start_address &
done

wait
echo Done