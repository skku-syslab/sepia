"""Pick a contiguous page-index block with a good wrap-around property.

Given the long per-group sequences produced by `block_tetris.py`, this script
selects a contiguous block of length `TOTAL_N_PAGES` such that the transition
from the tail back to the head (when repeating the block) yields a low estimated
miss/violation rate.

It writes the chosen block to:
    data/tetris_data-<START_ADDRESS_HEX>-<TARGET_UNIT_PAGES>/tetris_page_index_sequence/
"""

import pickle
import sys
import numpy as np
import matplotlib.pyplot as plt
import os
import config

page_group_index = int(sys.argv[1])

N_SETS              = config.N_SETS
N_SLICES            = config.N_SLICES
TARGET_UNIT_PAGES   = config.TARGET_UNIT_PAGES
TOTAL_ACCESS        = N_SETS * TARGET_UNIT_PAGES

output_dir = f"data/tetris_data-{config.START_ADDRESS_HEX}-{config.TARGET_UNIT_PAGES}"
pattern_sequence_dir    = f"{output_dir}/pattern_sequence"
page_index_sequence_dir = f"{output_dir}/page_index_sequence"
try:
    with open(f"{output_dir}/page_index_table.pkl", "rb") as file:
        page_index_table = dict(pickle.load(file)[page_group_index])
        pattern_list     = list(page_index_table.keys())

    with open(f"{pattern_sequence_dir}/page_group_index_{page_group_index}.pkl", "rb") as file:
        pattern_sequence = list(pickle.load(file))
    with open(f"{page_index_sequence_dir}/page_group_index_{page_group_index}.pkl", "rb") as file:
        page_index_sequence = pickle.load(file)

except Exception as e:
    print(e.with_traceback(None))
    print("There is no sequence.")
    exit(-1)


def calculate_miss_rate(patterns):
    """Same occupancy-based estimator used by `block_tetris.py`."""
    # Create a counter array
    counter = np.zeros(N_SETS * N_SLICES, dtype=int)

    # Convert patterns to a NumPy array for efficient indexing
    patterns = np.array(patterns)

    # Compute indices in a vectorized manner
    indices = N_SETS * patterns + np.arange(N_SETS)

    # Use NumPy's add.at() to efficiently increment the counter
    np.add.at(counter, indices.ravel(), 1)

    # Calculate the miss rate
    miss_rate = np.sum(counter[counter > config.THRESHOLD]) / TOTAL_ACCESS
    return round(miss_rate, 6)


# NOTE: 512 is an intentionally arbitrary target length (in pages) used to make
# the candidate block "long enough" for evaluation. It has no special meaning.
# We round it up to a multiple of TARGET_UNIT_PAGES so the block aligns with the
# unit size used elsewhere.
TOTAL_N_PAGES = ((512 // TARGET_UNIT_PAGES) + 1) * TARGET_UNIT_PAGES
half_size = TARGET_UNIT_PAGES // 2

x_values = []
y_values = []
for start_index, end_index in enumerate(range(TOTAL_N_PAGES-half_size, len(pattern_sequence)-half_size)):
    # Evaluate a wrap-around window: first half of the candidate block + last
    # half of the same block.
    test_target = pattern_sequence[start_index:start_index+half_size] + pattern_sequence[end_index:end_index+half_size]

    miss_rate = calculate_miss_rate(test_target) * 100
    x_values.append(start_index)
    y_values.append(miss_rate)

good_block_index = np.argmin(y_values)
good_start_index = x_values[good_block_index]
good_miss_rate   = y_values[good_block_index]
good_block = page_index_sequence[good_start_index:good_start_index+TOTAL_N_PAGES]

tetris_page_index_sequence_dir = f"{output_dir}/tetris_page_index_sequence"
os.makedirs(tetris_page_index_sequence_dir, exist_ok=True)
with open(f"{tetris_page_index_sequence_dir}/page_group_index_{page_group_index}.pkl", "wb") as file:
    pickle.dump(good_block, file)
print(f"{page_group_index:2d}: {good_miss_rate:.2f}%")