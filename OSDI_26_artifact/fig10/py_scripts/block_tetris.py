"""Construct "tetris" page sequences for a single page group.

Usage:
     python3 py_scripts/block_tetris.py <page_group_index>

High-level flow:
1) Load `page_index_table.pkl` and the list of per-page "patterns" for this
    page group.
2) Search for a set of `TARGET_UNIT_PAGES` patterns that minimizes an estimated
    LLC "miss/violation" rate (a simple occupancy model).
3) Materialize concrete page indices for the chosen patterns and write
    per-group sequences under:
    - data/tetris_data-<START_ADDRESS_HEX>-<TARGET_UNIT_PAGES>/base_blocks/
    - .../pattern_sequence/
    - .../page_index_sequence/

This script intentionally runs at top-level (no main()), because it is used as
an entrypoint from the accompanying shell scripts.
"""

import sys
import os
import numpy as np
import pickle
from multiprocessing import Pool, cpu_count
from queue import Queue
from scipy.spatial.distance import cosine
import config

page_group_index = int(sys.argv[1])

N_SETS              = config.N_SETS
N_SLICES            = config.N_SLICES
TARGET_UNIT_PAGES   = config.TARGET_UNIT_PAGES

TOTAL_ACCESS  = N_SETS * TARGET_UNIT_PAGES
N             = 2000  # number of samples
ELITE_PERCENT = 0.01  # top p% kept as elites

output_dir = f"data/tetris_data-{config.START_ADDRESS_HEX}-{config.TARGET_UNIT_PAGES}"
os.makedirs(output_dir, exist_ok=True)

try:
    table_dir = f"{output_dir}"
    with open(f"{table_dir}/page_index_table.pkl", "rb") as file:
        page_index_table = dict(pickle.load(file)[page_group_index])
        pattern_list     = list(page_index_table.keys())

except Exception as e:
    print(e.with_traceback(None))
    print("There is no table.")
    exit(-1)

for key, values in page_index_table.items():
    # Convert each list of page indices into a FIFO queue so we can consume
    # page indices without duplicates when building sequences later.
    page_index_table[key] = Queue()
    for value in values:
        page_index_table[key].put(value)

def calculate_miss_rate(patterns):
    """Estimate miss/violation rate for a set of page patterns.

    `patterns` is a list of length P (= number of pages) where each element is a
    length-N_SETS vector. Each entry indicates which slice a cache line maps to
    for the corresponding set, so we can count occupancy per (set, slice).
    """
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

max_iterations = 500
save_point     = 100
done           = False
best_sample    = None

base_block_dir = f"{output_dir}/base_blocks"
os.makedirs(base_block_dir, exist_ok=True)
try:
    with open(f"{base_block_dir}/page_group_index-{page_group_index}.pkl", "rb") as file:
        prev_best_sample = pickle.load(file)
except Exception as e:
    prev_best_sample = None
    print(e.with_traceback(None))

while not done:
    length            = len(pattern_list)
    slice_frequencies = np.zeros(length)
    best_miss_rate    = float("inf")

    for i in range(length):
        unique, counts = np.unique(pattern_list[i], return_counts=True)
        slice_frequencies[i] = counts.sum()
    prob_dist = slice_frequencies / slice_frequencies.sum()

    samples = [np.random.choice(length, TARGET_UNIT_PAGES, replace=length==TARGET_UNIT_PAGES, p=prob_dist) for _ in range(N)]

    if prev_best_sample is not None:
        samples = [prev_best_sample] + samples
        prev_best_sample = None
    for iteration in range(max_iterations):
        print(f"[{page_group_index:2d}]iteration {iteration}")

        with Pool(cpu_count()) as pool:
            miss_rates = pool.map(calculate_miss_rate, [[pattern_list[i] for i in sample] for sample in samples])

        elite_count = int(N * ELITE_PERCENT)
        elite_indices = np.argsort(miss_rates)[:elite_count]
        elite_samples = [samples[i] for i in elite_indices]

        current_best_rate = min(miss_rates)
        if current_best_rate < best_miss_rate:
            best_miss_rate = current_best_rate
            best_sample = samples[np.argmin(miss_rates)]

        print(f"Best miss rate so far: {best_miss_rate*100:.3f}%")

        prob_dist.fill(1e-8) 
        for sample in elite_samples:
            for index in sample:
                prob_dist[index] += 1
        noise = np.random.uniform(0, 0.01, size=prob_dist.shape)
        prob_dist = prob_dist + noise
        prob_dist /= prob_dist.sum()

        if iteration >= save_point:
            done = True
            break
        samples = [np.random.choice(length, TARGET_UNIT_PAGES, replace=length==TARGET_UNIT_PAGES, p=prob_dist) for _ in range(N)]
        
with open(f"{base_block_dir}/page_group_index-{page_group_index}.pkl", "wb") as file:
    pickle.dump(best_sample, file)
print(list(map(int, best_sample)))

pattern_sequence_dir = f"{output_dir}/pattern_sequence"
page_index_sequence_dir = f"{output_dir}/page_index_sequence"

os.makedirs(pattern_sequence_dir, exist_ok=True)
os.makedirs(page_index_sequence_dir, exist_ok=True)

try:
    with open(f"{page_index_sequence_dir}/page_group_index-{page_group_index}.pkl", "rb") as file:
        pass
    print("detect previous result")
    exit(0)
except Exception as e:
    print(e.with_traceback(None))
    pass

# Target sequence length (in pages) for this page group.
# We intentionally build a longer sequence than the final block so that
# `create_page_index_sequence.py` can later select the best contiguous block
# (e.g., for wrap-around repetition).
WANT_NUM_PAGES       = 2500
TOTAL_N_PAGES        = ((WANT_NUM_PAGES // TARGET_UNIT_PAGES) + 1) * TARGET_UNIT_PAGES
pattern_sequence     = [None for _ in range(TOTAL_N_PAGES)]
page_index_sequence  = [None for _ in range(TOTAL_N_PAGES)]

for i, pattern_index in enumerate(best_sample):
    pattern    = pattern_list[pattern_index]
    page_index = page_index_table[pattern].get()

    pattern_sequence[i]     = pattern
    page_index_sequence[i]  = page_index

def weighted_miss_rate(argv):
    patterns, prev_pattern, len_queue = argv
    new_pattern = patterns[-1]

    miss_rate = calculate_miss_rate(patterns)
    cosine_similarity = 0
    cosine_similarity = 1 - cosine(new_pattern, prev_pattern)

    # Return a tuple used for ranking candidates.
    return (miss_rate, cosine_similarity, len_queue)

for insert_index in range(TARGET_UNIT_PAGES, TOTAL_N_PAGES):
    start_index = insert_index - TARGET_UNIT_PAGES + 1

    valid_patterns = [(pattern, page_index_table[pattern].qsize()) for pattern in page_index_table.keys() if not page_index_table[pattern].empty()]
    
    test_groups = [(pattern_sequence[start_index:insert_index] + [pattern], pattern_sequence[start_index-1], len_queue) for pattern, len_queue in valid_patterns]
    
    with Pool(cpu_count()) as pool:
        results = pool.map(weighted_miss_rate, test_groups)

    # Sort primarily by lower miss rate, then higher cosine similarity, then a
    # larger remaining queue (more available pages for that pattern).
    sorted_results = sorted(enumerate(results), key=lambda x: (x[1][0], -x[1][1], -x[1][2]))
    
    best_result_index = sorted_results[0][0]  # index of the best candidate
    best_result = test_groups[best_result_index][0]

    pattern = best_result[-1]
    page_index = page_index_table[pattern].get_nowait()

    pattern_sequence[insert_index] = pattern
    page_index_sequence[insert_index] = page_index

    print(f"[{page_group_index:2d}]index: {insert_index:4d} | miss_rate: {results[best_result_index][0]*100:.3f}% | page_index: {page_index}")

print(TOTAL_N_PAGES, len(pattern_sequence))
print(TOTAL_N_PAGES, len(page_index_sequence))

with open(f"{pattern_sequence_dir}/page_group_index_{page_group_index}.pkl", "wb") as file:
    pickle.dump(pattern_sequence, file)
with open(f"{page_index_sequence_dir}/page_group_index_{page_group_index}.pkl", "wb") as file:
    pickle.dump(page_index_sequence, file)