import pickle
import numpy as np
import re

with open('common/base_sequence.pkl', 'rb') as f:
    BASE_SEQUENCE = np.array(pickle.load(f))

BASE_SEQ_LEN = int(BASE_SEQUENCE.shape[0])
MASK_INDEX = MASK_INDEX = np.uint64(BASE_SEQ_LEN - 1)
OFFSET_BITS = 6
NUM_SETS = 2048
NUM_SLICES = 26
NUM_WAYS = 12

def load_masks_from_header(path="common/hash_mask.h"):
    with open(path, "r") as f:
        content = f.read()
    hex_values = re.findall(r'0x[0-9A-Fa-f]+', content)
    return np.array([int(v, 16) for v in hex_values], dtype=np.uint64)

MASK = load_masks_from_header()

def popcount_u64(x: np.ndarray) -> np.ndarray:
    if hasattr(np, "bit_count"):
        return np.bit_count(x)
    x = x.astype(np.uint64, copy=False)
    x = x - ((x >> 1) & np.uint64(0x5555555555555555))
    x = (x & np.uint64(0x3333333333333333)) + ((x >> 2) & np.uint64(0x3333333333333333))
    x = (x + (x >> 4)) & np.uint64(0x0F0F0F0F0F0F0F0F)
    x = (x * np.uint64(0x0101010101010101)) >> np.uint64(56)
    return x.astype(np.uint64) % 2

def build_perm_bits(addresses_u64: np.ndarray) -> np.ndarray:
    n_masks = MASK.shape[0]
    weights = np.left_shift(np.uint64(1), np.arange(n_masks - 1, -1, -1, dtype=np.uint64))
    perm_bits = np.zeros(addresses_u64.shape[0], dtype=np.uint64)
    for m, w in zip(MASK[::-1], weights):
        parity = (popcount_u64(addresses_u64 & m) & np.uint64(1)).astype(np.uint64)
        perm_bits += parity * w
    return perm_bits

def get_slice_nums(addresses_u64: np.ndarray) -> np.ndarray:
    indices = ((addresses_u64 >> np.uint64(OFFSET_BITS)) & MASK_INDEX).astype(np.uint64)
    perm_bits = build_perm_bits(addresses_u64)
    permuted = (indices ^ perm_bits).astype(np.uint64)
    return list(BASE_SEQUENCE[permuted.astype(np.int64)])


if __name__ == "__main__":
    print(MASK)