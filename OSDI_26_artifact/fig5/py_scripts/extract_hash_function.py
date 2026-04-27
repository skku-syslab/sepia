"""
LLC slice hash function reverse engineering.
Converted from hash_reversing.ipynb.

Usage:
    python hash_reversing.py
"""

import struct
import glob
import math
import pickle
import os
import pandas as pd
from collections import defaultdict
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

offset_bits = 6
index_bits  = 14
LIST_SIZE   = 1 << index_bits   # 16384

# ---------------------------------------------------------------------------
# Step 1. Load mapping files and build mapping_table
# ---------------------------------------------------------------------------

def create_mapping_table():
    df = pd.read_csv("outputs/slice_mapping.csv")
    return dict(zip(df["pa"].apply(lambda x: int(x, 16)), df["slice"]))

print("Loading mapping files...")
mapping_table = create_mapping_table()
print(f"Loaded {len(mapping_table)} entries.")

addr, slice_num = next(iter(mapping_table.items()))
minimum_sequence_number = sequence = (addr >> (offset_bits + index_bits)) + 1

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def join_bits(seq, index):
    return (seq << (index_bits + offset_bits)) | (index << offset_bits)


def xor_reduction(a, b):
    """Bitwise AND then XOR-reduce all bits (inner product over GF(2))."""
    res = 0
    temp = a & b
    while temp:
        res ^= (temp & 1)
        temp >>= 1
    return res


def get_sparse_sequence_list(seq_num):
    """Return {index: slice} for all entries that exist in mapping_table."""
    result = {}
    for i in range(LIST_SIZE):
        addr = join_bits(seq_num, i)
        if addr in mapping_table:
            result[i] = mapping_table[addr]
    return result


# ---------------------------------------------------------------------------
# Step 2. Reverse-engineer perm_j table and derive masks
# ---------------------------------------------------------------------------

perm_j_table = {}

print("\nFinding all available sequence numbers...")
all_seq_nums = set(addr >> (index_bits + offset_bits) for addr in mapping_table.keys())
print(f"Found {len(all_seq_nums)} unique sequence numbers.")

seq_bit_offset = index_bits + offset_bits

for j_bit in range(seq_bit_offset, 48):
    j = j_bit - seq_bit_offset
    print(f"\n--- Analyzing Address Bit {j_bit} (j_offset={j}) ---")

    List_1 = List_2 = common_keys = None

    print("  Searching for a *valid* (sparse) sequence pair...")
    for seq_num in all_seq_nums:
        target_seq_num = seq_num ^ (1 << j)
        if target_seq_num not in all_seq_nums:
            continue

        List_1_candidate = get_sparse_sequence_list(seq_num)
        List_2_candidate = get_sparse_sequence_list(target_seq_num)
        common_keys_candidate = List_1_candidate.keys() & List_2_candidate.keys()

        if len(common_keys_candidate) > 100:
            List_1      = List_1_candidate
            List_2      = List_2_candidate
            common_keys = common_keys_candidate
            print(f"  Found valid sparse pair! Base: {seq_num}, Target: {target_seq_num}")
            print(f"  Found {len(common_keys)} common indexes for filtering.")
            break

    if List_1 is None:
        print(f"  --- Error: No valid sequence pair found for j={j}! ---")
        continue

    # Intersect candidate sets across all common indexes to find perm_j
    main_candidates = None
    for index in tqdm(common_keys, desc=f"  Filtering j={j}", leave=False):
        slice_num = List_1[index]
        current = {index2 ^ index for index2 in common_keys if List_2[index2] == slice_num}

        if main_candidates is None:
            main_candidates = current
        else:
            main_candidates.intersection_update(current)

        if not main_candidates:
            break

    print(f"\r  Filtering complete. Candidates remaining: {len(main_candidates)}    ")

    if main_candidates:
        perm_j = min(main_candidates)
        print(f"  Selected perm_{j_bit} = {perm_j} (0x{perm_j:X}) [Candidates: {main_candidates}]")
        perm_j_table[j_bit] = perm_j
    else:
        print(f"  --- Error: Failed to find perm_{j_bit} (0 candidates) ---")

# Build mask array from perm_j_table
print("\n\n--- Generating Permutation Selector Masks (M_0 to M_13) ---")
masks = [0] * index_bits

for j_bit, perm_j in perm_j_table.items():
    for p_i in range(index_bits):
        if (perm_j >> p_i) & 1:
            masks[p_i] |= (1 << j_bit)

print("\n--- Final Permutation Selector Masks ---")
header_outputs = ["const std::vector<uint64_t> MASKS = {"]
for p_i, mask in enumerate(masks):
    print(f"  M_{p_i:>2} (p{p_i}): 0x{mask:X}")
    header_outputs.append(f"0x{mask:X},")
header_outputs.append("};")
with open("common/hash_mask.h", "w") as f:
    print("\n".join(header_outputs), file=f)

# ---------------------------------------------------------------------------
# Step 3. Verify masks: two sequences with the same physical set index
#         should map to the same slice after de-permutation.
# ---------------------------------------------------------------------------

print("\n--- Verification ---")

with open("outputs/hash_verification.txt", "w") as f:
    base   = minimum_sequence_number
    target = base ^ 1

    List_1 = {i: mapping_table[join_bits(base,   i)] for i in range(LIST_SIZE)}
    List_2 = {i: mapping_table[join_bits(target, i)] for i in range(LIST_SIZE)}

    list1 = {}
    list2 = {}
    for index in range(LIST_SIZE):
        bits1 = [xor_reduction(m, join_bits(base,   index)) for m in masks[::-1]]
        bits2 = [xor_reduction(m, join_bits(target, index)) for m in masks[::-1]]
        perm1 = int("0b" + "".join(map(str, bits1)), 2)
        perm2 = int("0b" + "".join(map(str, bits2)), 2)
        list1[index ^ perm1] = List_1[index]
        list2[index ^ perm2] = List_2[index]

    total_count  = 0
    total_passed = 0
    for index in range(LIST_SIZE):
        match = list1[index] == list2[index]
        print(f"{index:04X}: {list1[index]:02X} | {list2[index]:02X} [{match}]", file=f)
        total_count  += 1
        total_passed += int(match)

    print(
        f"Total Passed: {total_passed} [{total_passed/total_count:.2%}], "
        f"Total Failed: {total_count - total_passed} [{(total_count - total_passed)/total_count:.2%}]"
    )

# ---------------------------------------------------------------------------
# Step 4. Save base_sequence
# ---------------------------------------------------------------------------

base_sequence = [list1[i] for i in range(LIST_SIZE)]
os.makedirs("common", exist_ok=True)
with open("common/base_sequence.pkl", "wb") as f:
    pickle.dump(base_sequence, f)
print("\nSaved common/base_sequence.pkl")

with open("common/base_sequence.txt", "w") as f:
    for slice_num in base_sequence:
        print(slice_num, file=f)
print("\nSaved common/base_sequence.txt")
