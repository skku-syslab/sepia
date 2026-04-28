"""Plot Figure 10 results from `count_violation.py` outputs.

Inputs:
- data/counter/<pattern>_<workingset_kb>.txt

Outputs:
- plots/subfigure_a.png
- plots/subfigure_b.png
"""

import matplotlib.pyplot as plt
import config
import numpy as np

# subfigure (a)
target_access_pattern_type = "stride1"
workingset_size_kb_list = [4096, 5120, 6656] #4MB, 5MB, 6.5MB
result_dict = {}
for workingset_size_kb in workingset_size_kb_list:
    file_name = f"data/counter/{target_access_pattern_type}_{workingset_size_kb}.txt"
    with open(file_name, "r") as f:
        lines = f.read().strip().split("\n")
    
    result_dict[workingset_size_kb] = {}
    sum_ratio = 0
    total_ratio = 100
    for line in lines:
        access_count, ratio = line.split(":")
        ratio = round(float(ratio), 4)
        sum_ratio += ratio

        result_dict[workingset_size_kb][access_count] = ratio
    
    result_dict[workingset_size_kb][f">{int(access_count)+1}"] = round(total_ratio - sum_ratio, 4)

for key, value in result_dict.items():
    print(key)
    print(value)

labels = ['0', '1', '2', '>3']
colors = ['#4472C4', '#70AD47', '#ED7D31']  # blue, green, orange
legend_labels = ['4MB', '5MB', '6.5MB']

x = np.arange(len(labels))
width = 0.25

fig, ax = plt.subplots(figsize=(5, 4))

for i, (workingset_size_kb, color, legend_label) in enumerate(zip(workingset_size_kb_list, colors, legend_labels)):
    values = [result_dict[workingset_size_kb].get(k, 0.0) for k in labels]
    ax.bar(x + i * width, values, width, label=legend_label, color=color)

ax.set_xlabel('Per-slice/set access count')
ax.set_ylabel('Slice/set Ratio (%)')
ax.set_ylim(0, 100)
ax.set_xticks(x + width)
ax.set_xticklabels(labels)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig("plots/subfigure_a.png")
plt.clf()

# subfigure (b)
target_access_pattern_type_list = ["tetris", "stride1"]
workingset_size_kb = 5632 #5.5MB
result_dict = {}

for target_access_pattern_type in target_access_pattern_type_list:
    file_name = f"data/counter/{target_access_pattern_type}_{workingset_size_kb}.txt"
    with open(file_name, "r") as f:
        lines = f.read().strip().split("\n")
    
    result_dict[target_access_pattern_type] = {}
    sum_ratio = 0
    total_ratio = 100
    for line in lines:
        access_count, ratio = line.split(":")
        ratio = round(float(ratio), 4)
        sum_ratio += ratio

        result_dict[target_access_pattern_type][access_count] = ratio
    
    result_dict[target_access_pattern_type][f">{int(access_count)+1}"] = round(total_ratio - sum_ratio, 4)

for key, value in result_dict.items():
    print(key)
    print(value)

labels = ['0', '1', '2', '>3']
colors = ['#4472C4', '#70AD47']  # blue, green
legend_labels = ['Tetris', 'Stride-1']

x = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(5, 4))

for i, (pattern_type, color, legend_label) in enumerate(zip(target_access_pattern_type_list, colors, legend_labels)):
    values = [result_dict[pattern_type].get(k, 0.0) for k in labels]
    ax.bar(x + i * width, values, width, label=legend_label, color=color)

ax.set_xlabel('Per-slice/set access count')
ax.set_ylabel('Slice/set Ratio (%)')
ax.set_ylim(0, 100)
ax.set_xticks(x + width / 2)
ax.set_xticklabels(labels)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig("plots/subfigure_b.png")