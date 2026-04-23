#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import glob
import sys

def extract_llc_miss_rate(directory):
    cache_files = glob.glob(os.path.join(directory, "*_cache_miss.log"))
    
    for cache_file in cache_files:
        try:
            with open(cache_file, 'r') as f:
                for line in f:
                    if 'LLC-load-misses' in line or 'llc-load-misses' in line.lower():
                        match = re.search(r'#\s*(\d+\.?\d*)%', line)
                        if match:
                            return float(match.group(1))
        except Exception as e:
            print(f"Error processing cache file {cache_file}: {e}", file=sys.stderr)
    
    return None

def main():
    if len(sys.argv) > 1:
        base_dir = os.path.join(os.getcwd(), sys.argv[1])
    else:
        base_dir = os.getcwd()
    
    experiment_dirs = glob.glob(os.path.join(base_dir, "default_kernel_*_one_flow"))
    
    if not experiment_dirs:
        print(f"Warning: No experiment directories found in {base_dir}")
        return
    
    results = []
    for exp_dir in experiment_dirs:
        dir_name = os.path.basename(exp_dir)
        miss_rate = extract_llc_miss_rate(exp_dir)
        if miss_rate is not None:
            bit_name = dir_name.replace("default_kernel_", "").replace("_one_flow", "")
            results.append((bit_name, miss_rate, dir_name))
    
    def sort_key(item):
        bit_str = item[0].replace("bit", "")
        try:
            return int(bit_str)
        except ValueError:
            return 999
    
    results.sort(key=sort_key)
    
    print("Bit Setting,LLC Miss Rate (%),Directory")
    for bit_name, miss_rate, dir_name in results:
        print(f"{bit_name},{miss_rate:.2f},{dir_name}")

if __name__ == "__main__":
    main()
