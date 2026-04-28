"""Generate a stride-1 (sequential) cache-line address list.

Usage:
    python3 py_scripts/gen_stride1_address_list.py <workingset_size_mb>

The output contains one hex address per line, stepping by 64 bytes (one cache
line) from `config.START_ADDRESS_INT` (a user-chosen physical base address).
"""

import sys
import config

workingset_size_mb = int(sys.argv[1])
workingset_size_byte = workingset_size_mb << 20

output_file_name = f"data/address_list-stride1/address_list.{workingset_size_mb}.csv"
with open(output_file_name, "w") as f:
    # Step through the working set in 64B increments.
    for offset in range(0, workingset_size_byte, 64):
        address = config.START_ADDRESS_INT + offset
        print(f"{hex(address)}", file=f)

