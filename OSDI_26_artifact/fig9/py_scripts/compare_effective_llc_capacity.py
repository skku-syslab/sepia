"""Compare effective LLC capacity across access patterns.

This script loads pre-generated physical address lists (default / stride1 /
tetris), computes the LLC slice number for each address, and estimates a miss
rate using a simple occupancy model: any (set, slice) counter that exceeds
`config.N_WAYS` contributes to the miss ratio.

Outputs:
    data/effective_llc_size_test/{default|stride1|tetris}.txt
"""

import config
import numpy as np
import hash_function
import os

access_pattern_types = ["default", "stride1", "tetris"]
workingset_size_mb_list = [16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36]

def calculate_miss_rate(address_list, slice_nums):
    # Model the LLC as (TOTAL_SETS x N_SLICES) bins.
    TOTAL_SETS      = config.N_SETS * config.NUM_PAGE_GROUPS
    cache_struct    = np.zeros(TOTAL_SETS * config.N_SLICES, dtype=int)

    for address, slice_num in zip(address_list, slice_nums):
        # Set index uses cache-line granularity (>> 6) and wraps by TOTAL_SETS.
        set_index = int((address >> 6) & (TOTAL_SETS-1))
        cache_struct[TOTAL_SETS*slice_num + set_index] += 1
    
    miss_rate = np.sum(cache_struct[cache_struct > config.N_WAYS]) / len(address_list)

    return miss_rate

results = {access_pattern_type: {} for access_pattern_type in access_pattern_types}
for workingset_size_mb in workingset_size_mb_list:
    print(f"==={workingset_size_mb}===")
    for access_pattern_type in access_pattern_types:
        file_name = f"data/address_list-{access_pattern_type}/address_list.{workingset_size_mb}.csv"
        with open(file_name, "r") as f:
            address_list = np.array(list(map(lambda x: int(x, 16), f.read().strip().split('\n'))), dtype=np.uint64)
        slice_nums = hash_function.get_slice_nums(address_list)

        miss_rate = calculate_miss_rate(address_list, slice_nums)
        print(f"{access_pattern_type}: {miss_rate*100:.1f}%")
        results[access_pattern_type][workingset_size_mb] = miss_rate*100

output_dir = f"data/effective_llc_size_test"
os.makedirs(output_dir, exist_ok=True)

for access_pattern_type, result in results.items():
    file_name = f"{output_dir}/{access_pattern_type}.txt"
    with open(file_name, "w") as f:
        for workingset_size_mb, miss_rate in result.items():
            print(f"{workingset_size_mb}:{miss_rate:.1f}", file=f)
