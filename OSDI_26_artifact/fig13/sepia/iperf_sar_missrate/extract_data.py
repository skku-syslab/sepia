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
    'one_flow': 1,
    'two_flow': 2,
    'three_flow': 3,
    'four_flow': 4,
    'five_flow': 5,
    'six_flow': 6,
}

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
        print(f"iperf error: {e}")
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
        print(f"util error: {e}")
    return {}

def extract_l3_miss_rate(cache_file):
    try:
        with open(cache_file, 'r') as f:
            for line in f:
                if 'LLC-load-misses' in line or 'llc-load-misses' in line.lower():
                    match = re.search(r'#\s*(\d+\.?\d*)%', line)
                    if match:
                        return float(match.group(1))
    except Exception as e:
        print(f"cache error {cache_file}: {e}")
    return None

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
    
    cache_files = glob.glob(os.path.join(directory, "*_cache_miss.log"))
    l3_miss_rates = []
    
    for cache_file in cache_files:
        miss_rate = extract_l3_miss_rate(cache_file)
        if miss_rate is not None:
            l3_miss_rates.append(miss_rate)
    
    if l3_miss_rates:
        results['l3_miss_rate'] = sum(l3_miss_rates) / len(l3_miss_rates)
    else:
        results['l3_miss_rate'] = 0.0
    
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
        "Directory,Bitrate (Gbps),CPU0 (%),CPU1 (%),CPU2 (%),CPU3 (%),CPU4 (%),CPU5 (%),"
        "Total CPU Usage (%)", "Per-Core Throughput (Gbps/100%)",
        "L3 Miss Rate (%)"
    )
    
    print(header)
    
    for dir_name, results in sorted_results:
        if 'bitrate_gbps' in results and results['bitrate_gbps']:
            run_bitrate = sum(results['bitrate_gbps'])
        else:
            run_bitrate = 0.0
        
        cpu_usages = [0.0] * 6
        total_cpu_usage = 0.0
        if 'cpu_usage_percent' in results and results['cpu_usage_percent']:
            cpu_usage_list = results['cpu_usage_percent']
            for i, usage in enumerate(cpu_usage_list):
                if i < 6:
                    cpu_usages[i] = usage
                    total_cpu_usage += usage
        
        if total_cpu_usage > 0:
            per_core_throughput = (run_bitrate / total_cpu_usage) * 100
        else:
            per_core_throughput = 0.0
        
        l3_miss_rate = results.get('l3_miss_rate', 0.0)
        
        cpu_str = ",".join([f"{usage:.2f}" for usage in cpu_usages])
        
        result_line = (
            f"{dir_name},{run_bitrate:.2f},{cpu_str},{total_cpu_usage:.2f},{per_core_throughput:.2f},"
            f"{l3_miss_rate:.2f}"
        )
        
        print(result_line)

if __name__ == "__main__":
    main()
