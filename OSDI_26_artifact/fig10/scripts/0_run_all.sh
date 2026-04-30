#!/bin/bash
set -e

# Figure 10 driver.
#
# Runs the numbered step scripts (1_* .. 5_*) in order and stops on the first
# failure. Run this from the Figure 10 directory so relative paths resolve:
#   bash scripts/0_run_all.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find and sort all step scripts matching [1-9]_*.sh.
scripts=$(ls "$SCRIPT_DIR"/[1-9]_*.sh 2>/dev/null | sort)

if [ -z "$scripts" ]; then
    echo "No scripts found."
    exit 1
fi

for script in $scripts; do
    echo "================================================"
    echo "Running: $(basename $script)"
    echo "================================================"
    
    if ! bash "$script"; then
        echo ""
        echo "ERROR: Failed at $(basename $script)" >&2
        exit 1
    fi
done

echo "================================================"
echo "All scripts completed successfully."
echo "================================================"