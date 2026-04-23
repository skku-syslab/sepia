#!/usr/bin/env python3
import os
import re
import glob
import sys
import csv

def get_flow_base_name(dir_name):
    if '_' in dir_name and dir_name.split('_')[-1].isdigit():
        return '_'.join(dir_name.split('_')[:-1])
    return dir_name

FLOW_ORDER = {
    'single_flow': 1,
    'one_flow': 1,
    'two_flow': 2,
    'three_flow': 3,
    'four_flow': 4,
    'five_flow': 5,
    'six_flow': 6,
    'seven_flow': 7,
    'eight_flow': 8,
}

SKMEM_REGEX = re.compile(r"skmem:\(r(\d+),rb(\d+),")
MB = 1024 * 1024

def extract_bitrate(iperf_file):
    try:
        with open(iperf_file, 'r') as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "receiver" in line:
                    match = re.search(r'(\d+\.?\d*)\s+Gbits/sec', line)
                    if match:
                        return float(match.group(1))
    except Exception as e:
        print(f"iperf file processing error: {e}")
    return None

def extract_cpu_usage(util_file):
    try:
        with open(util_file, 'r') as f:
            lines = f.readlines()
            cpu_usage = {}
            for line in lines:
                if line.startswith("Average:") and not "CPU" in line:
                    parts = line.split()
                    if len(parts) >= 8:
                        cpu_num = parts[1]
                        idle_percent = float(parts[-1])
                        cpu_usage[cpu_num] = round(100.0 - idle_percent, 2)
            return cpu_usage
    except Exception as e:
        print(f"util file processing error: {e}")
    return {}

def parse_socket_memory_log(log_path):
    recv_vals = []
    skmem_vals = []
    block_entries = []
    current_entry = None

    def flush_block():
        nonlocal block_entries
        if not block_entries:
            return
        valid_entries = [e for e in block_entries if e.get("skmem_r", 0) > 0]
        if not valid_entries:
            block_entries = []
            return
        best = max(valid_entries, key=lambda e: (e.get("rb", 0), e.get("recv", 0)))
        recv_vals.append(best.get("recv", 0))
        skmem_vals.append(best.get("skmem_r", 0))
        block_entries = []

    try:
        with open(log_path, 'r') as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                if line.startswith("=== Sample"):
                    flush_block()
                    current_entry = None
                    continue

                if line.startswith("ESTAB"):
                    parts = line.split()
                    try:
                        recv = int(parts[1])
                    except (IndexError, ValueError):
                        recv = 0
                    current_entry = {"recv": recv, "skmem_r": 0, "rb": 0}
                    block_entries.append(current_entry)
                    continue

                if "skmem:" in line and current_entry is not None:
                    match = SKMEM_REGEX.search(line)
                    if match:
                        current_entry["skmem_r"] = int(match.group(1))
                        current_entry["rb"] = int(match.group(2))
                    current_entry = None

        flush_block()
    except Exception as e:
        print(f"socket memory log {log_path} processing error: {e}")
        return [], []

    return recv_vals, skmem_vals

def process_experiment_directory(directory):
    results = {}
    
    iperf_files = glob.glob(os.path.join(directory, "receiver_iperf_*.log"))
    bitrates = []
    for iperf_file in iperf_files:
        bitrate = extract_bitrate(iperf_file)
        if bitrate:
            bitrates.append(bitrate)
    results['bitrate_gbps'] = bitrates
    
    util_file = os.path.join(directory, "receiver_util.log")
    if os.path.exists(util_file):
        cpu_usages = extract_cpu_usage(util_file)
        cpu_nums = sorted(cpu_usages.keys(), key=int)
        cpu_usage_list = [cpu_usages[num] for num in cpu_nums]
        results['cpu_usage_percent'] = cpu_usage_list
    
    socket_memory_files = glob.glob(os.path.join(directory, "socket_memory_*.log"))
    port_recv_averages = []
    port_skmem_averages = []
    port_recv_maxes = []
    port_skmem_maxes = []
    
    for socket_file in socket_memory_files:
        recv_vals, skmem_vals = parse_socket_memory_log(socket_file)
        if recv_vals:
            port_recv_avg = sum(recv_vals) / len(recv_vals) / MB
            port_recv_averages.append(port_recv_avg)
            port_recv_max = max(recv_vals) / MB
            port_recv_maxes.append(port_recv_max)
        if skmem_vals:
            port_skmem_avg = sum(skmem_vals) / len(skmem_vals) / MB
            port_skmem_averages.append(port_skmem_avg)
            port_skmem_max = max(skmem_vals) / MB
            port_skmem_maxes.append(port_skmem_max)
    
    if port_recv_averages:
        recv_sum_mb = sum(port_recv_averages)
    else:
        recv_sum_mb = 0.0
    
    if port_skmem_averages:
        skmem_sum_mb = sum(port_skmem_averages)
    else:
        skmem_sum_mb = 0.0
    
    if port_recv_maxes:
        recv_max_sum_mb = sum(port_recv_maxes)
    else:
        recv_max_sum_mb = 0.0
    
    if port_skmem_maxes:
        skmem_max_sum_mb = sum(port_skmem_maxes)
    else:
        skmem_max_sum_mb = 0.0
    
    results['recv_q_total_mb'] = recv_sum_mb
    results['skmem_r_total_mb'] = skmem_sum_mb
    results['recv_q_max_sum_mb'] = recv_max_sum_mb
    results['skmem_r_max_sum_mb'] = skmem_max_sum_mb
    
    return results

def aggregate_flow_results(result_dirs, output_path=None):
    from collections import defaultdict

    flow_totals = defaultdict(lambda: defaultdict(list))
    flow_counts = defaultdict(int)
    numeric_columns = []
    header_initialized = False

    for result_dir in result_dirs:
        csv_path = os.path.join(result_dir, "experiment_results.csv")
        if not os.path.exists(csv_path):
            print(f"[Warning] {csv_path} file not found. Skipping.")
            continue

        with open(csv_path, newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            if not header_initialized:
                numeric_columns = [col for col in reader.fieldnames if col != "Directory"]
                header_initialized = True

            for row in reader:
                flow_name = get_flow_base_name(row["Directory"])
                flow_counts[flow_name] += 1
                for col in numeric_columns:
                    value_str = row.get(col, "").strip()
                    if not value_str:
                        continue
                    try:
                        value = float(value_str)
                    except ValueError:
                        continue
                    flow_totals[flow_name][col].append(value)

    if not flow_totals:
        print("No data to aggregate. Check RESULT directory.")
        return

    def format_value(column, value):
        if "Counter" in column:
            return f"{value:.0f}"
        return f"{value:.1f}"

    if output_path is None:
        output_path = os.path.join(os.getcwd(), "flow_averages.csv")

    def sort_key(item):
        flow_name = item[0]
        priority = FLOW_ORDER.get(flow_name, 999)
        return (priority, flow_name)

    sorted_flows = sorted(flow_totals.items(), key=sort_key)

    with open(output_path, 'w', newline='', encoding='utf-8') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(["Flow", "Sample Count", *numeric_columns])

        for flow_name, col_values in sorted_flows:
            count = flow_counts[flow_name]
            row = [flow_name, count]
            for col in numeric_columns:
                values = col_values.get(col)
                if values:
                    avg = sum(values) / len(values)
                    row.append(format_value(col, avg))
                else:
                    row.append("")
            writer.writerow(row)

    print(f"Flow average results saved to {output_path}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--aggregate":
        output_path = None
        result_dirs = []
        for arg in sys.argv[2:]:
            if arg.startswith("--output="):
                output_path = os.path.abspath(arg.split("=", 1)[1])
            else:
                if os.path.isabs(arg):
                    result_dirs.append(arg)
                else:
                    result_dirs.append(os.path.join(os.getcwd(), arg))
        if not result_dirs:
            print("Usage: python extract_data.py --aggregate RESULT_3 RESULT_4 [--output=flow_averages.csv]")
            return
        aggregate_flow_results(result_dirs, output_path)
        return

    if len(sys.argv) > 1:
        base_dir = os.path.join(os.getcwd(), sys.argv[1])
    else:
        base_dir = os.getcwd()
    
    experiment_dirs = []
    
    if os.path.exists(base_dir):
        test_dirs = glob.glob(os.path.join(base_dir, "*_flow_test"))
        experiment_dirs.extend(test_dirs)
        
        numbered_test_dirs = glob.glob(os.path.join(base_dir, "*_flow_test_*"))
        experiment_dirs.extend(numbered_test_dirs)
        
        flow_dirs = glob.glob(os.path.join(base_dir, "*_flow_*"))
        for flow_dir in flow_dirs:
            if os.path.isdir(flow_dir) and flow_dir not in experiment_dirs:
                experiment_dirs.append(flow_dir)
        
        if os.path.exists(os.path.join(base_dir, "receiver_iperf_1.log")):
            if base_dir not in experiment_dirs:
                experiment_dirs.append(base_dir)
    
    if not experiment_dirs:
        print(f"Warning: Experiment data directory not found in specified path ({base_dir}).")
        print("The following files must exist: receiver_iperf_1.log, receiver_util.log")
        
        all_files = glob.glob(os.path.join(base_dir, "*"))
        print(f"Actual existing files: {[f for f in all_files if os.path.isfile(f)]}")
        return
    
    all_results = {}
    for directory in experiment_dirs:
        dir_name = os.path.basename(directory)
        all_results[dir_name] = process_experiment_directory(directory)
    
    def sort_key(item):
        dir_name = item[0]
        
        if '_' in dir_name and dir_name.split('_')[-1].isdigit():
            base_name = '_'.join(dir_name.split('_')[:-1])
            number = int(dir_name.split('_')[-1])
        else:
            base_name = dir_name
            number = 0
        
        flow_type = 'unknown'
        for flow_name in FLOW_ORDER.keys():
            if flow_name in base_name.lower():
                flow_type = flow_name
                break
        
        flow_priority = FLOW_ORDER.get(flow_type, 999)
        return (flow_priority, base_name, number)
    
    sorted_results = sorted(all_results.items(), key=sort_key)
    
    header = (
        "Directory,Bitrate (Gbps),"
        "CPU0 (%),CPU1 (%),CPU2 (%),CPU3 (%),CPU4 (%),CPU5 (%),CPU6 (%),CPU7 (%),"
        "Total CPU Usage (%)", "Per-Core Throughput (Gbps/100%),"
        "Recv-Q Average Total (MB),skmem r Average Total (MB),"
        "Recv-Q Maximum Total (MB),skmem r Maximum Total (MB)"
    )
    
    print(header)
    
    for dir_name, results in sorted_results:
        if 'bitrate_gbps' in results and results['bitrate_gbps']:
            run_bitrate = sum(results['bitrate_gbps'])
        else:
            run_bitrate = 0.0
        
        cpu_usages = [0.0] * 8
        total_cpu_usage = 0.0
        if 'cpu_usage_percent' in results and results['cpu_usage_percent']:
            cpu_usage_list = results['cpu_usage_percent']
            for i, usage in enumerate(cpu_usage_list):
                if i < 8:
                    cpu_usages[i] = usage
                    total_cpu_usage += usage
        
        if total_cpu_usage > 0:
            per_core_throughput = (run_bitrate / total_cpu_usage) * 100
        else:
            per_core_throughput = 0.0
        
        recv_q_total_mb = results.get('recv_q_total_mb', 0.0)
        skmem_r_total_mb = results.get('skmem_r_total_mb', 0.0)
        recv_q_max_sum_mb = results.get('recv_q_max_sum_mb', 0.0)
        skmem_r_max_sum_mb = results.get('skmem_r_max_sum_mb', 0.0)
        
        cpu_str = ",".join([f"{usage:.2f}" for usage in cpu_usages])
        
        result_line = (
            f"{dir_name},{run_bitrate:.2f},{cpu_str},{total_cpu_usage:.2f},{per_core_throughput:.2f},"
            f"{recv_q_total_mb:.1f},{skmem_r_total_mb:.1f},"
            f"{recv_q_max_sum_mb:.1f},{skmem_r_max_sum_mb:.1f}"
        )
        
        print(result_line)

if __name__ == "__main__":
    main()
