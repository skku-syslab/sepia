import numpy as np
import os
import sys
import config
import hash_function
import matplotlib.pyplot as plt
from collections import defaultdict

subfigure_name = sys.argv[1]
cpu_ids = config.cpu_ids_table[subfigure_name]

bin_file_name = f"data/subfig_{subfigure_name}/violation_ratio.bin"
violation_ratios = np.fromfile(bin_file_name, dtype=np.float64())
avg_violation_ratio = np.mean(violation_ratios)
print(f"Result {subfigure_name}, Average Violation Ratio: {avg_violation_ratio:.6f}[{len(violation_ratios)} samples]")

#######################################################

HISTOGRAM_BINS = 40
cache_struct_size = hash_function.NUM_SETS * hash_function.NUM_SLICES

hist_file_name = f"data/subfig_{subfigure_name}/hist.bin"
raw_data = np.fromfile(hist_file_name, dtype=np.uint16)
hist_data = raw_data.reshape((-1, HISTOGRAM_BINS))
print(f"Shape: {hist_data.shape}")
print(f"Data type: {hist_data.dtype}") # uint8 이어야 함

ratio_list = hist_data / cache_struct_size

mean_ratios = np.mean(ratio_list, axis=0) # 막대 높이
std_ratios = np.std(ratio_list, axis=0)   # 에러바 길이
plt.figure(figsize=(12, 6))

threshold = hash_function.NUM_WAYS
good_x_pos = np.arange(0, threshold + 1)
bad_x_pos = np.arange(threshold+1, HISTOGRAM_BINS)

good_mean_ratios = mean_ratios[0:threshold + 1]
bad_mean_ratios = mean_ratios[threshold + 1:HISTOGRAM_BINS]

good_std_ratios = std_ratios[0:threshold + 1]
bad_std_ratios = std_ratios[threshold + 1:HISTOGRAM_BINS]
plt.bar(good_x_pos, good_mean_ratios, yerr=good_std_ratios, 
        align='center', alpha=0.7, ecolor='black', capsize=3, label='safe access', color='blue')
plt.bar(bad_x_pos, bad_mean_ratios, yerr=bad_std_ratios, 
        align='center', alpha=0.7, ecolor='black', capsize=3, label='violation access', color='orange')
plt.axvline(x=threshold+0.5, color='gray', linestyle='--', label='violation threshold') 

total = 0
violation_ratio = 0
for hist_idx in range(HISTOGRAM_BINS):
    count = mean_ratios[hist_idx] * cache_struct_size
    total += mean_ratios[hist_idx]
    if hist_idx > threshold:
        violation_ratio += mean_ratios[hist_idx]
print(f"Violation Ratio: {violation_ratio:.6f}")
print(f"Total: {total:.6f}")

plt.xlabel('Access Count')
plt.ylabel('Ratio (Count / Cache Size)')
plt.ylim(0, 0.20)
plt.title(f"Cache Access Distribution {len(cpu_ids)} Flows  - {violation_ratio*100:.2f}% Violation Ratio")
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend()

plt.savefig(f"plots/subfig_{subfigure_name}.png", dpi=500)
plt.clf()