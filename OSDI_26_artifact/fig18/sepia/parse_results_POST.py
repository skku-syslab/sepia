import os
import glob
import re
import csv
import sys

def parse_latency(latency_str):
    latency_str = latency_str.strip()
    if latency_str.endswith("us"):
        return float(latency_str[:-2]) / 1000.0
    elif latency_str.endswith("ms"):
        return float(latency_str[:-2])
    elif latency_str.endswith("s"):
        return float(latency_str[:-1]) * 1000.0
    return 0.0

def parse_wrk_files(target_dir):
    results = []
    
    filename_pattern = re.compile(r"(\d+)B_t(\d+)_cTotal(\d+)_trial(\d+)\.txt")
    req_pattern = re.compile(r"Requests/sec:\s+([\d\.]+)")
    lat_pattern = re.compile(r"Latency\s+([\d\.]+[a-z]+)")

    files = glob.glob(os.path.join(target_dir, "*.txt"))
    print(f"Found {len(files)} files in {target_dir}...")

    for filepath in files:
        filename = os.path.basename(filepath)
        match = filename_pattern.match(filename)
        
        if not match:
            continue

        payload_size = int(match.group(1))
        threads = int(match.group(2))
        conns = int(match.group(3))
        trial = int(match.group(4))

        with open(filepath, 'r') as f:
            content = f.read()
            
        req_match = req_pattern.search(content)
        lat_match = lat_pattern.search(content)

        if req_match:
            req_sec = float(req_match.group(1))
            upload_gbps = (req_sec * payload_size * 8) / 1_000_000_000
        else:
            req_sec = 0.0
            upload_gbps = 0.0

        latency_ms = parse_latency(lat_match.group(1)) if lat_match else 0.0

        results.append({
            "Payload(B)": payload_size,
            "Threads": threads,
            "Connections": conns,
            "Trial": trial,
            "Req/sec": req_sec,
            "Latency(ms)": latency_ms,
            "Upload(Gbps)": round(upload_gbps, 4)
        })

    results.sort(key=lambda x: (x["Payload(B)"], x["Threads"], x["Connections"], x["Trial"]))
    return results

def calculate_averages(raw_data):
    grouped = {}

    for row in raw_data:
        key = (row["Payload(B)"], row["Threads"], row["Connections"])
        
        if key not in grouped:
            grouped[key] = {
                "req_list": [],
                "lat_list": [],
                "gbps_list": []
            }
        
        grouped[key]["req_list"].append(row["Req/sec"])
        grouped[key]["lat_list"].append(row["Latency(ms)"])
        grouped[key]["gbps_list"].append(row["Upload(Gbps)"])

    avg_results = []
    for key, values in grouped.items():
        payload, threads, conns = key
        count = len(values["req_list"])
        
        if count == 0: continue

        avg_req = sum(values["req_list"]) / count
        avg_lat = sum(values["lat_list"]) / count
        avg_gbps = sum(values["gbps_list"]) / count

        avg_results.append({
            "Payload(B)": payload,
            "Threads": threads,
            "Connections": conns,
            "Trials_Count": count,
            "Avg_Req/sec": round(avg_req, 2),
            "Avg_Latency(ms)": round(avg_lat, 3),
            "Avg_Upload(Gbps)": round(avg_gbps, 4)
        })

    avg_results.sort(key=lambda x: (x["Payload(B)"], x["Threads"], x["Connections"]))
    return avg_results

def save_csv(filename, data):
    if not data:
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"Saved: {filename}")

def main():
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        dirs = sorted(glob.glob("./nginx_result_*"), reverse=True)
        if not dirs:
            print("Error: No result directory found.")
            return
        target_dir = dirs[0]

    print(f"Processing directory: {target_dir}\n")
    
    raw_data = parse_wrk_files(target_dir)
    if not raw_data:
        print("No data found.")
        return

    avg_data = calculate_averages(raw_data)

    print("-" * 95)
    print(f"{'Size(B)':<10} | {'Thr':<3} | {'Con':<5} | {'Count':<5} | {'Avg Req/sec':<12} | {'Avg Lat(ms)':<12} | {'Avg Gbps':<10}")
    print("-" * 95)
    for row in avg_data:
        print(f"{row['Payload(B)']:<10} | {row['Threads']:<3} | {row['Connections']:<5} | {row['Trials_Count']:<5} | {row['Avg_Req/sec']:<12.2f} | {row['Avg_Latency(ms)']:<12.3f} | {row['Avg_Upload(Gbps)']:<10.2f}")
    print("-" * 95)

    raw_csv_path = os.path.join(target_dir, "raw_data.csv")
    avg_csv_path = os.path.join(target_dir, "summary_avg.csv")

    save_csv(raw_csv_path, raw_data)
    save_csv(avg_csv_path, avg_data)

if __name__ == "__main__":
    main()