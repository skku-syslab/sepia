"""Build a per-page-group index table for Tetris pattern generation (Figure 10).

This script enumerates a 4GiB address range (cache-line granularity), computes
the LLC slice number for each cache line, and groups 4KiB pages by:
- page_group_index = page_index % NUM_PAGE_GROUPS
- page_pattern     = tuple(slice_ids_for_64_cache_lines_in_page)

The resulting table maps:
    (page_group_index, page_pattern) -> tuple/list of page_index values

Output:
- data/tetris_data-<START_ADDRESS_HEX>-<TARGET_UNIT_PAGES>/page_index_table.pkl

Note: this can be CPU/memory heavy; the artifact may ship pre-generated data.
"""

import json
import os
import pickle
import sys
from collections import defaultdict
import config
import hash_function
import numpy as np

output_dir = f"data/tetris_data-{config.START_ADDRESS_HEX}-{config.TARGET_UNIT_PAGES}"
os.system(f"mkdir -p {output_dir}")

N_TOTAL_PAGES = config.ADDRESS_RANGE >> 12

print("Generate the slice_index_sequence. - Start", end = "", flush=True)
page_index_table = defaultdict()
# Build addresses for every cache line in the 4GiB range.
address_list = np.array([config.START_ADDRESS_INT + offset for offset in range(0, config.ADDRESS_RANGE, 64)], dtype=np.uint64)
slice_index_sequence = hash_function.get_slice_nums(address_list)
print("\rGenerate the slice_index_sequence. - End   ", flush=True)

for page_group_index in range(config.NUM_PAGE_GROUPS):
    page_index_table[page_group_index] = defaultdict(list)

for page_index in range(N_TOTAL_PAGES):
    print(f"\r {page_index+1} / {N_TOTAL_PAGES} ({(page_index+1) / N_TOTAL_PAGES * 100:.2f}%)   ", end="", flush=True)
    page_group_index = (page_index%config.NUM_PAGE_GROUPS)
    start, end = page_index*64, (page_index+1)*64
    # Slice pattern for the 64 cache lines within this 4KiB page.
    page_pattern = tuple(slice_index_sequence[start:end])

    page_index_table[page_group_index][page_pattern].append(page_index)
print()

for page_group_index in range(config.NUM_PAGE_GROUPS):
    for key, value in tuple(page_index_table[page_group_index].items()):
        page_index_table[page_group_index][key] = tuple(value)

with open(f"{output_dir}/page_index_table.pkl", "wb") as file:
    pickle.dump(page_index_table, file)
