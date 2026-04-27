import sys
import config
import re
import os

subfigure_name = sys.argv[1]
cpu_ids = config.cpu_ids_table[subfigure_name]
file_name = f"traces/subfig_{subfigure_name}/mlx5_trace.log"

output_dir = f"data/subfig_{subfigure_name}"
os.makedirs(output_dir, exist_ok=True)

pattern = re.compile(
    r"""
    ^.*?                               # 앞부분 전부 스킵
    (?P<timestamp>\d+\.\d+):\s+        # timestamp (예: 86.592561)
    \S+:\s+                            # 이벤트명 (mlx5_mpwqe_page_alloc) 후 콜론
    cpu=(?P<cpu>\d+)\s+                # cpu=숫자
    wqe_idx=(?P<wqe_idx>\d+)\s+        # wqe_idx=숫자
    page_idx=(?P<page_idx>\d+)\s+      # page_idx=숫자
    phys_addr=(?P<phys_addr>0x[0-9a-fA-F]+) # phys_addr=0x...
    """,
    re.VERBOSE,
)


with open(file_name, "r") as f:
    lines = f.readlines()

output_files = dict()
for cpu_id in cpu_ids:
    output_file = f"{output_dir}/page_start_address.{cpu_id}.txt"
    File = open(output_file, "w")
    output_files[cpu_id] = File

for line in lines:
    match = pattern.match(line)
    if match:
        cpu_id = int(match.group("cpu"))
        if cpu_id not in cpu_ids:
            continue
        phys_addr = int(match.group("phys_addr"), 16)
        output_files[cpu_id].write(f"{phys_addr}\n")

for cpu_id in cpu_ids:
    output_files[cpu_id].close()