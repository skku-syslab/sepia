"""Build a page-index lookup table keyed by per-page slice patterns.

For each 4KiB page in the configured (modeled) physical address range, we
compute a "page pattern":
the length-64 sequence of LLC slice IDs for the 64 cache lines within the page.

The physical base address (`config.START_ADDRESS_HEX`) is user-chosen and is
used only as a reference when generating these synthetic physical addresses.

We then group pages by `page_group_index = page_index % NUM_PAGE_GROUPS` and
build a mapping:

    page_group_index -> { page_pattern(tuple) -> (page_index, ...) }

The result is written to:
    data/tetris_data-<START_ADDRESS_HEX>-<TARGET_UNIT_PAGES>/page_index_table.pkl
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

# Compute slice IDs for every cache line in the configured address range.
print("Generate the slice_index_sequence. - Start", end = "", flush=True)
page_index_table = defaultdict()
address_list = np.array([config.START_ADDRESS_INT + offset for offset in range(0, config.ADDRESS_RANGE, 64)], dtype=np.uint64)
slice_index_sequence = hash_function.get_slice_nums(address_list)
print("\rGenerate the slice_index_sequence. - End   ", flush=True)

for page_group_index in range(config.NUM_PAGE_GROUPS):
    page_index_table[page_group_index] = defaultdict(list)

for page_index in range(N_TOTAL_PAGES):
    print(f"\r {page_index+1} / {N_TOTAL_PAGES} ({(page_index+1) / N_TOTAL_PAGES * 100:.2f}%)   ", end="", flush=True)
    page_group_index = (page_index%config.NUM_PAGE_GROUPS)
    start, end = page_index*64, (page_index+1)*64
    # The pattern is the 64-length slice sequence for this 4KiB page.
    page_pattern = tuple(slice_index_sequence[start:end])

    page_index_table[page_group_index][page_pattern].append(page_index)
print()

for page_group_index in range(config.NUM_PAGE_GROUPS):
    for key, value in tuple(page_index_table[page_group_index].items()):
        page_index_table[page_group_index][key] = tuple(value)

with open(f"{output_dir}/page_index_table.pkl", "wb") as file:
    pickle.dump(page_index_table, file)
