#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find and sort all scripts matching the pattern [0-9]_*.sh, excluding 0_run_all.sh
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