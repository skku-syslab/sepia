// Sliding-window cache-occupancy analysis for Figure 5.
//
// This program reads per-CPU page-start physical addresses extracted from NIC
// trace logs (see `py_script/process_trace.py`) and models LLC occupancy by
// counting accesses per (set, slice). A "violation" is recorded when the
// occupancy exceeds NUM_WAYS.
//
// Usage:
//   ./bin/analyze_by_sliding.bin <subfigure_name>
//
// Inputs:
//   data/subfig_<name>/page_start_address.<cpu_id>.txt
//
// Outputs (written under data/subfig_<name>/):
//   - violation_ratio.bin   (double per step)
//   - hist.bin              (uint16 histogram per step)
//   - violation_summary.txt (average + count)

#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <map>
#include <cstdint>
#include <numeric> // std::accumulate
#include "common/hash_mask.h"

// ==========================================
// 1. Constants & Config
// ==========================================
constexpr int NUM_SETS = 2048;
constexpr int NUM_SLICES = 26;
constexpr int NUM_WAYS = 12;
constexpr int OFFSET_BITS = 6;
constexpr int HISTOGRAM_BINS = 40;
uint64_t MASK_INDEX = 0;

std::vector<int> BASE_SEQUENCE;

std::map<int, std::vector<int>> get_cpu_ids_table() {
    // CPUs to track per subplot (one entry per flow)
    return {
        {'a', {0}},      // 1 flow
        {'b', {0, 2}},   // 2 flows
    };
}

std::map<int, int> get_num_pages_per_flow_table() {
    // Total expected memory / 4 kB per page / number of flows
    return {
        {'a', 5632/1},  // ~22 MB (16 MB feeding + 6 MB throttling), 1 flow
        {'b', 9728/2},  // ~38 MB (32 MB feeding + 3 MB throttling * 2), 2 flows
    };
}

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
}

void save_results(char subfigure_name, const std::vector<double>& ratios, const std::vector<std::vector<uint16_t>>& histograms) {
    std::ostringstream path_ss;
    path_ss << "data/subfig_" << subfigure_name << "/";
    std::string base_path = path_ss.str();
    
    // ---------------------------------------------------------
    // 1. Save to binary
    // ---------------------------------------------------------
    std::string bin_filename = base_path + "violation_ratio.bin";
    std::ofstream bin_file(bin_filename, std::ios::out | std::ios::binary);

    if (bin_file.is_open()) {
        if (!ratios.empty()) {
            bin_file.write(reinterpret_cast<const char*>(ratios.data()), ratios.size() * sizeof(double));
        }
        bin_file.close();
    } else {
        std::cerr << "Error: Could not write to " << bin_filename << std::endl;
    }

    std::string hist_filename = base_path + "hist.bin";
    std::ofstream hist_file(hist_filename, std::ios::out | std::ios::binary);

    if (hist_file.is_open()) {
        if (!histograms.empty()) {
            for (const auto& h : histograms) {
                hist_file.write(reinterpret_cast<const char*>(h.data()), h.size() * sizeof(uint16_t));
            }
        }
        hist_file.close();
    } else {
        std::cerr << "Error: Could not write to " << hist_filename << std::endl;
    }

    // ---------------------------------------------------------
    // 2. Calculate the average value
    // ---------------------------------------------------------
    double sum = 0.0;
    for (double r : ratios) sum += r;
    double avg = ratios.empty() ? 0.0 : sum / ratios.size();

    // ---------------------------------------------------------
    // 3. Save the text file
    // ---------------------------------------------------------
    std::string txt_filename = base_path + "violation_summary.txt";
    std::ofstream txt_file(txt_filename);

    if (txt_file.is_open()) {
        txt_file << "Average Violation Ratio: " << avg << "\n";
        txt_file << "Total Steps: " << ratios.size() << "\n";
        txt_file.close();
        
        std::cout << "Saved binary: " << bin_filename << "\n"
                  << "Saved summary: " << txt_filename << " (Avg: " << avg << ")" << std::endl;
    } else {
        std::cerr << "Error: Could not write to " << txt_filename << std::endl;
    }
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

std::vector<uint32_t> cache_struct(NUM_SLICES * NUM_SETS, 0);

inline void update_cache(uint64_t page_start_address, int delta) {
    for (int offset = 0; offset < 4096; offset += 64) {
        uint64_t phys_addr = page_start_address + offset;
        int slice_num = get_slice_num_single(phys_addr);
        int set_num = (phys_addr >> OFFSET_BITS) & (NUM_SETS - 1);
        int idx = slice_num * NUM_SETS + set_num;
        
        if (delta < 0 && cache_struct[idx] == 0) continue; 
        cache_struct[idx] += delta;
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <subfigure_name>" << std::endl;
        return 1;
    }

    char subfigure_name = argv[1][0];
    
    auto cpu_ids_table = get_cpu_ids_table();
    auto num_pages_table = get_num_pages_per_flow_table();

    if (cpu_ids_table.find(subfigure_name) == cpu_ids_table.end()) {
        std::cerr << "Invalid Subfigure Name" << std::endl;
        return 1;
    }

    std::vector<int> cpu_ids = cpu_ids_table[subfigure_name];
    int num_pages_per_flow = num_pages_table[subfigure_name];

    load_base_sequence("common/base_sequence.txt");
    MASK_INDEX = static_cast<uint64_t>(BASE_SEQUENCE.size() - 1);
    if (MASK_INDEX == static_cast<uint64_t>(-1)) {
        std::cerr << "Error: BASE_SEQUENCE is empty." << std::endl;
        return 1;
    }

    std::vector<std::vector<uint16_t>> hist_record;
    std::vector<std::vector<uint64_t>> address_list_per_cpu;
    
    // Read per-CPU page-start-address traces.
    for (int cpu_id : cpu_ids) {
        std::ostringstream filename_ss;
        filename_ss << "data/subfig_" << subfigure_name 
                    << "/page_start_address." << cpu_id << ".txt";
        
        std::ifstream infile(filename_ss.str());
        if (!infile.is_open()) {
            std::cerr << "Skipping " << filename_ss.str() << " (Not Found)" << std::endl;
            continue;
        }

        std::vector<uint64_t> addresses;
        uint64_t addr;
        while (infile >> addr) {
            addresses.push_back(addr);
        }
        address_list_per_cpu.push_back(addresses);
        infile.close();
    }

    std::fill(cache_struct.begin(), cache_struct.end(), 0);
    std::vector<double> violation_ratio_list;
    double total_count = (double)(NUM_SETS * NUM_SLICES);

    // --- Init Phase ---
    for (int i = 0; i < num_pages_per_flow; ++i) {
        for (const auto& addr_list : address_list_per_cpu) {
            if (i < addr_list.size()) {
                update_cache(addr_list[i], 1);
            }
        }
    }
    
    // Initial Violation Check
    int violation_count = 0;
    std::vector<uint16_t> histogram(HISTOGRAM_BINS, 0);
    for (uint32_t val : cache_struct) {
        if (val > NUM_WAYS) violation_count++;
        histogram[val]++;
    }
    violation_ratio_list.push_back(violation_count / total_count);
    hist_record.push_back(histogram);

    // --- Sliding Window Phase ---
    size_t min_len = address_list_per_cpu[0].size();
    for (const auto& lst : address_list_per_cpu) {
        if (lst.size() < min_len) min_len = lst.size();
    }

    for (size_t i = num_pages_per_flow; i < min_len; ++i) {
        for (const auto& addr_list : address_list_per_cpu) {
            update_cache(addr_list[i - num_pages_per_flow], -1); // Remove
            update_cache(addr_list[i], 1);                       // Add
        }

        violation_count = 0;
        std::vector<uint16_t> histogram(HISTOGRAM_BINS, 0);
        for (uint32_t val : cache_struct) {
            if (val > NUM_WAYS) violation_count++;
            histogram[val]++;
        }
        violation_ratio_list.push_back(violation_count / total_count);
        hist_record.push_back(histogram);
    }

    // Save the results
    save_results(subfigure_name, violation_ratio_list, hist_record);
    

    return 0;
}
