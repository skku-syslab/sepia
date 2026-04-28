// Generate a synthetic (dummy) slice mapping CSV.
//
// This is used in the artifact path to avoid running the real perf-based slice
// extractor (which is slow and system-dependent). Instead, it uses the already
// recovered masks + base sequence to compute a slice number for each address.
//
// Output:
//   outputs/slice_mapping.csv

#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <map>
#include <cstdint>
#include <numeric> // std::accumulate

// ==========================================
// 1. Constants & Config
// ==========================================
constexpr int NUM_SETS = 2048;
constexpr int NUM_SLICES = 26;
constexpr int NUM_WAYS = 12;
constexpr int OFFSET_BITS = 6;
constexpr int HISTOGRAM_BINS = 40;
uint64_t MASK_INDEX = 0;

// LLC slice hash function masks, reverse-engineered for this system.
// Methodology based on: https://github.com/jdmccalpin/Intel_Address_Hash
const std::vector<uint64_t> MASKS = {
    0x5DD00000, 0x90100000, 0x63B00000, 0x1F500000,
    0xF8500000, 0x8000000,  0x4D200000, 0x77700000,
    0x3500000,  0x7B100000, 0xDD100000, 0x69B00000,
    0x0,        0x48300000
};

std::vector<int> BASE_SEQUENCE;

// ==========================================
// 2. Helper Functions
// ==========================================

void load_base_sequence(const std::string& filename) {
    std::ifstream infile(filename);
    if (!infile.is_open()) {
        std::cerr << "Error: Could not open " << filename << ". Run export_base_sequence.py first." << std::endl;
        exit(1);
    }
    int val;
    while (infile >> val) {
        BASE_SEQUENCE.push_back(val);
    }
    MASK_INDEX = BASE_SEQUENCE.size() - 1;
    fprintf(stderr, "len_base_seq: %ld\n", BASE_SEQUENCE.size());
}

inline int popcount_u64(uint64_t x) {
    return __builtin_popcountll(x);
}

inline int get_slice_num_single(uint64_t address_u64) {
    int n_masks = MASKS.size();
    uint64_t perm_bits = 0;

    for (int i = 0; i < n_masks; ++i) {
        uint64_t m = MASKS[n_masks - 1 - i]; 
        uint64_t w = (1ULL << (n_masks - 1 - i));
        
        if (popcount_u64(address_u64 & m) % 2 == 1) {
            perm_bits += w;
        }
    }

    uint64_t indices = (address_u64 >> OFFSET_BITS) & MASK_INDEX;
    uint64_t permuted = indices ^ perm_bits;
    
    if (permuted >= BASE_SEQUENCE.size()) return 0; 
    return BASE_SEQUENCE[permuted];
}

// ==========================================
// 3. Main Logic
// ==========================================

int main(int argc, char* argv[]) {
    // Dummy physical base address; only used as an address generator seed.
    const uint64_t start_address = 0x101500000;
    const uint64_t size_working_set = 4*(1LL<<30); //4GB

    load_base_sequence("common/base_sequence_for_gen_dummy.txt");
    FILE *output_fp = fopen("outputs/slice_mapping.csv", "w");
    fprintf(output_fp, "va,pa,slice\n");
    uint64_t idx= 0;
    uint64_t n_probes = size_working_set / 64;
    for(uint64_t offset=0; offset < size_working_set; offset += 64) {
        uint64_t pa = start_address + offset;
        int slice_num = get_slice_num_single(pa);
        // Use dummy addresses: the synthetic VA equals PA in the CSV.
        fprintf(output_fp, "0x%012lx,0x%012lx,%d\n", pa, pa, slice_num);
        
        if ((idx + 1) % 1000 == 0)
            fprintf(stderr, "\r%zu / %zu (%.2f%%)", idx + 1, n_probes, ((double)(idx + 1) / n_probes)*100);
        
        idx++;
    }

    fclose(output_fp);
    printf("\n");

    return 0;
}
