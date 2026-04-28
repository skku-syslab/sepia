"""Plot the effective-LLC-size experiment results.

Reads text outputs produced by `compare_effective_llc_capacity.py` under:
    data/effective_llc_size_test/

and saves a bar chart to:
    plots/figure.png
"""

import matplotlib.pyplot as plt
import numpy as np

target_access_pattern_type_list = ["tetris", "stride1", "default"]
result_dict = {}

for target_access_pattern_type in target_access_pattern_type_list:
    file_name = f"data/effective_llc_size_test/{target_access_pattern_type}.txt"
    with open(file_name, "r") as f:
        lines = f.read().strip().split("\n")
    
    result_dict[target_access_pattern_type] = {}
    for line in lines:
        workingset_size_mb, miss_rate = line.split(":")
        workingset_size_mb = int(workingset_size_mb)
        miss_rate = float(miss_rate)

        result_dict[target_access_pattern_type][workingset_size_mb] = miss_rate

labels = list(result_dict[target_access_pattern_type_list[0]].keys())
colors = ['#4472C4', '#70AD47', '#ED7D31']  # blue, green, orange
legend_labels = ["tetris", "stride1", "default"]

x = np.arange(len(labels))
width = 0.2

fig, ax = plt.subplots(figsize=(12, 4))

for i, (pattern_type, color, legend_label) in enumerate(zip(target_access_pattern_type_list, colors, legend_labels)):
    values = [result_dict[pattern_type].get(k, 0.0) for k in labels]
    ax.bar(x + i * width, values, width, label=legend_label, color=color)

ax.set_xlabel('Working set size (MB)')
ax.set_ylabel('Violation Ratio (%)')
ax.set_ylim(0, 50)
ax.set_xticks(x + width / 3)
ax.set_xticklabels(labels)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig("plots/figure.png")