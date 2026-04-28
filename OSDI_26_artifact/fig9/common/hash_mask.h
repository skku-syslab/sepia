// Precomputed bit masks used by the LLC slice-hash implementation.
//
// The Python helper `py_scripts/hash_function.py` parses this file and treats
// each hex literal as a mask. For a given physical address, it computes the
// parity (popcount % 2) of (address & mask) for each mask and combines those
// parity bits into a permutation index.
//
// Keep this file in a simple, parseable format (hex literals only), because it
// is intentionally read as plain text.
const std::vector<uint64_t> MASKS = {
0x5DD00000,
0x90100000,
0x63B00000,
0x1F500000,
0xF8500000,
0x8000000,
0x4D200000,
0x77700000,
0x3500000,
0x7B100000,
0xDD100000,
0x69B00000,
0x0,
0x48300000,
};
