#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <result_directory>"
    echo "Example: $0 ./memcached_results_20251204"
    exit 1
fi

result_dir="$1"

if [ ! -d "$result_dir" ]; then
    echo "Error: Directory '$result_dir' not found"
    exit 1
fi

output_avg="${result_dir}/summary_memcached.csv"
output_raw="${result_dir}/raw_details_memcached.csv"

echo "Parsing results from: $result_dir"

echo "ValueSize(B),Threads,Connections,Pipeline,SuccessRate,AvgOPS,AvgLatency(ms),AvgBandwidth(KB/s),Status" > "$output_avg"
echo "ValueSize(B),Threads,Connections,Pipeline,TrialID,OPS,Latency(ms),Bandwidth(KB/s)" > "$output_raw"

configs=$(ls "$result_dir"/set_*_trial1.txt 2>/dev/null | sed 's/.*set_\([0-9]*\)B_t\([0-9]*\)_c\([0-9]*\)_p\([0-9]*\)_trial1.txt/\1,\2,\3,\4/' | sort -u -t',' -k1,1n -k2,2n -k3,3n -k4,4n)

if [ -z "$configs" ]; then
    echo "Error: No result files found."
    exit 1
fi

echo "$configs" | while IFS=',' read -r vs threads conn pipe; do
    
    sum_ops=0
    sum_lat=0
    sum_bw=0
    
    valid_trials=0
    total_trials=0
    
    for ((t=1; t<=20; t++)); do
        prefix="${vs}B_t${threads}_c${conn}_p${pipe}_trial${t}"
        result_file="${result_dir}/set_${prefix}.txt"
        
        if [ ! -f "$result_file" ]; then
            continue
        fi

        total_trials=$((total_trials + 1))

        line=$(grep "^Totals" "$result_file")
        if [ -z "$line" ]; then
             line=$(grep "^Sets" "$result_file")
        fi

        ops=$(echo "$line" | awk '{print $2}')
        lat=$(echo "$line" | awk '{print $5}')
        bw=$(echo "$line" | awk '{print $10}')
        
        if [ -z "$bw" ]; then bw="0"; fi

        if [ -z "$ops" ] || [ "$ops" == "0.00" ]; then
            echo "${vs},${threads},${conn},${pipe},${t},0,0,0" >> "$output_raw"
            continue 
        fi

        echo "${vs},${threads},${conn},${pipe},${t},${ops},${lat},${bw}" >> "$output_raw"

        sum_ops=$(echo "$sum_ops + $ops" | bc)
        sum_lat=$(echo "$sum_lat + $lat" | bc)
        sum_bw=$(echo "$sum_bw + $bw" | bc)
        
        valid_trials=$((valid_trials + 1))
        
    done

    final_ops=0; final_lat=0; final_bw=0
    status="NO_DATA"

    if [ $valid_trials -gt 0 ]; then
        final_ops=$(printf "%.2f" $(echo "scale=2; $sum_ops / $valid_trials" | bc))
        final_lat=$(printf "%.2f" $(echo "scale=2; $sum_lat / $valid_trials" | bc))
        final_bw=$(printf "%.2f" $(echo "scale=2; $sum_bw / $valid_trials" | bc))
        status="OK"
    fi

    success_rate="${valid_trials}/${total_trials}"
    if [ "$valid_trials" -ne "$total_trials" ] && [ "$total_trials" -gt 0 ]; then
        percent=$(echo "scale=0; ($valid_trials * 100) / $total_trials" | bc)
        status="UNSTABLE (${percent}%)"
    fi

    echo "${vs},${threads},${conn},${pipe},${success_rate},${final_ops},${final_lat},${final_bw},${status}" >> "$output_avg"
    
    if [ "$status" == "OK" ]; then
        echo "  ✓ Size=${vs}, T=${threads}, C=${conn}, P=${pipe} -> [OK] AvgOPS: ${final_ops}"
    else
        echo "  ⚠ Size=${vs}, T=${threads}, C=${conn}, P=${pipe} -> [${status}] Valid: ${success_rate}"
    fi
    
done

echo ""
echo "Parsing completed!"
echo "1. Summary CSV : $output_avg"
echo "2. Raw Details : $output_raw"