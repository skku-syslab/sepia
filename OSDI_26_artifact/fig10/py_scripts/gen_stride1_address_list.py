"""Generate a simple stride-1 (contiguous) address list (Figure 10).

Usage:
    python3 py_scripts/gen_stride1_address_list.py <workingset_size_kb>

Output:
- data/address_list-stride1/address_list.<workingset_size_kb>.csv

Each output line is a hex address. The list spans the requested working-set
size with a 64-byte stride (one cache line).
"""

import sys
import config

workingset_size_kb = int(sys.argv[1])
workingset_size_byte = workingset_size_kb << 10

output_file_name = f"data/address_list-stride1/address_list.{workingset_size_kb}.csv"
with open(output_file_name, "w") as f:
    # Emit one cache-line address per line.
    for offset in range(0, workingset_size_byte, 64):
        address = config.START_ADDRESS_INT + offset
        print(f"{hex(address)}", file=f)

