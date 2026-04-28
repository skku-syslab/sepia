"""Generate the "tetris" cache-line address list.

Usage:
    python3 py_scripts/gen_tetris_address_list.py <workingset_size_mb>

This script loads per-page-group page-index sequences produced by
`create_page_index_sequence.py`, then interleaves them round-robin across
`config.NUM_PAGE_GROUPS` to generate a stream of page indices. For each page,
it outputs 64B-stepped physical addresses (one per cache line), relative to the
user-chosen base `config.START_ADDRESS_INT`.
"""

import config
import pickle
import sys
import hash_function
import numpy as np

workingset_size_mb = int(sys.argv[1])
workingset_size_byte = workingset_size_mb << 20

output_dir = f"data/tetris_data-{config.START_ADDRESS_HEX}-{config.TARGET_UNIT_PAGES}"
page_sequence_dict = {}

for i in range(config.NUM_PAGE_GROUPS):
    file_name = f"{output_dir}/tetris_page_index_sequence/page_group_index_{i}.pkl"
    with open(file_name, "rb") as f:
        page_sequence_dict[i] = list(pickle.load(f))

def generate(output_file):
    want_num_cachelines = workingset_size_byte >> 6
    curr_num_cachelines = 0
    page_group_index = 0

    while True:
        # Interleave page groups: group cycles fastest, sequence index advances
        # once per full round over all groups.
        page_group = page_group_index % config.NUM_PAGE_GROUPS
        sequence_index = page_group_index // config.NUM_PAGE_GROUPS
        print(page_group, sequence_index)
        page_index = page_sequence_dict[page_group][sequence_index]

        for offset in range(page_index*4096, (page_index+1)*4096, 64):
            address = config.START_ADDRESS_INT + offset
            print(f"{hex(address)}", file=output_file)
        
            curr_num_cachelines += 1
            if curr_num_cachelines >= want_num_cachelines:
                return
        page_group_index += 1

output_file_name = f"data/address_list-tetris/address_list.{workingset_size_mb}.csv"
with open(output_file_name, "w") as output_file:
    generate(output_file)