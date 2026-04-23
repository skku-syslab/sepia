#!/bin/bash


if [ -z "$1" ]; then
    echo "Usage: $0 <result_directory>"
    echo "Example: $0 ./spdk_results_20251201_023254"
    exit 1
fi

result_dir="$1"

if [ ! -d "$result_dir" ]; then
    echo "Error: Directory '$result_dir' not found"
    exit 1
fi

output_avg="${result_dir}/summary_avg.csv"
output_raw="${result_dir}/raw_details.csv"

echo "Parsing results from: $result_dir"
echo "1. Summary (Strict Avg): $output_avg"
echo "2. Raw Details         : $output_raw"


echo "BlockSize(B),QueueDepth,FlowCount,ValidCleanTrials,AvgTotalIOPS,AvgLatency(us),AvgThroughput(MiB/s),AvgCPUUtil(%),AvgCacheMissRate(%),Status" > "$output_avg"
echo "BlockSize(B),QueueDepth,FlowCount,ActualFlows,TrialID,TotalIOPS,AvgLatency(us),Throughput(MiB/s),CPUUtil(%),CacheMissRate(%)" > "$output_raw"


configs=$(ls "$result_dir"/perf_*_trial*_flow0.txt 2>/dev/null | sed 's/.*perf_\([0-9]*\)B_qd\([0-9]*\)_flows\([0-9]*\)_trial.*_flow0.txt/\1,\2,\3/' | sort -u -t',' -k1,1n -k2,2n -k3,3n)

if [ -z "$configs" ]; then
    echo "Error: No result files found in $result_dir."
    exit 1
fi

echo "$configs" | while IFS=',' read -r bs qd flows; do
    

    sum_config_iops=0
    sum_config_lat=0
    sum_config_bw=0
    sum_config_cpu=0
    sum_config_miss=0
    
    valid_clean_trials=0
    partial_fail_trials=0
    
    for ((t=1; t<=100; t++)); do
        prefix="${bs}B_qd${qd}_flows${flows}_trial${t}"
        
        if [ ! -f "${result_dir}/perf_${prefix}_flow0.txt" ]; then
            if [ $t -eq 1 ]; then continue; fi
            break
        fi

        trial_total_iops=0
        trial_total_bw=0
        trial_sum_lat=0
        flow_count=0
        
        for ((i=0; i<flows; i++)); do
            perf_file="${result_dir}/perf_${prefix}_flow${i}.txt"
            if [ -f "$perf_file" ]; then
                iops=$(grep "^Total" "$perf_file" | awk '{print $3}' | tr -d ',')
                throughput=$(grep "^Total" "$perf_file" | awk '{print $4}' | tr -d ',')
                lat=$(grep "^Total" "$perf_file" | awk '{print $5}' | tr -d ',')
                
                if [ -n "$iops" ] && [ "$iops" != "0" ]; then
                    trial_total_iops=$(echo "$trial_total_iops + $iops" | bc)
                    trial_total_bw=$(echo "$trial_total_bw + $throughput" | bc)
                    trial_sum_lat=$(echo "$trial_sum_lat + $lat" | bc)
                    flow_count=$((flow_count + 1))
                fi
            fi
        done
        
        if [ $flow_count -gt 0 ]; then
            trial_avg_lat=$(echo "scale=2; $trial_sum_lat / $flow_count" | bc)
            
            trial_cpu_util=0
            cpu_file="${result_dir}/cpu_util_${prefix}.log"
            if [ -f "$cpu_file" ]; then
                idle_avg=$(grep "Average:" "$cpu_file" | grep -v "CPU" | awk '{sum+=$NF; count++} END {if(count>0) print sum/count; else print 0}')
                if [ -n "$idle_avg" ]; then trial_cpu_util=$(echo "scale=2; 100 - $idle_avg" | bc); fi
            fi

            trial_miss_rate=0
            total_loads=0; total_misses=0
            for cache_file in "${result_dir}"/cache_miss_${prefix}_c*.log; do
                if [ -f "$cache_file" ]; then
                    loads=$(grep "LLC-loads" "$cache_file" | awk '{gsub(/,/, "", $1); print $1}' | head -1)
                    misses=$(grep "LLC-load-misses" "$cache_file" | awk '{gsub(/,/, "", $1); print $1}' | head -1)
                    if [ -n "$loads" ] && [ -n "$misses" ] && [ "$loads" != "0" ]; then
                        total_loads=$(echo "$total_loads + $loads" | bc)
                        total_misses=$(echo "$total_misses + $misses" | bc)
                    fi
                fi
            done
            if [ "$total_loads" != "0" ]; then
                trial_miss_rate=$(printf "%.2f" $(echo "scale=10; ($total_misses / $total_loads) * 100" | bc))
            fi

            echo "${bs},${qd},${flows},${flow_count},${t},${trial_total_iops},${trial_avg_lat},${trial_total_bw},${trial_cpu_util},${trial_miss_rate}" >> "$output_raw"

            if [ $flow_count -eq $flows ]; then
                sum_config_iops=$(echo "$sum_config_iops + $trial_total_iops" | bc)
                sum_config_bw=$(echo "$sum_config_bw + $trial_total_bw" | bc)
                sum_config_lat=$(echo "$sum_config_lat + $trial_avg_lat" | bc)
                sum_config_cpu=$(echo "$sum_config_cpu + $trial_cpu_util" | bc)
                sum_config_miss=$(echo "$sum_config_miss + $trial_miss_rate" | bc)
                
                valid_clean_trials=$((valid_clean_trials + 1))
            else
                partial_fail_trials=$((partial_fail_trials + 1))
            fi
        fi
        
    done

    final_iops=0; final_lat=0; final_bw=0; final_cpu=0; final_miss=0
    status="ALL_FAILED"

    if [ $valid_clean_trials -gt 0 ]; then
        final_iops=$(printf "%.2f" $(echo "scale=2; $sum_config_iops / $valid_clean_trials" | bc))
        final_lat=$(printf "%.2f" $(echo "scale=2; $sum_config_lat / $valid_clean_trials" | bc))
        final_bw=$(printf "%.2f" $(echo "scale=2; $sum_config_bw / $valid_clean_trials" | bc))
        final_cpu=$(printf "%.2f" $(echo "scale=2; $sum_config_cpu / $valid_clean_trials" | bc))
        final_miss=$(printf "%.2f" $(echo "scale=2; $sum_config_miss / $valid_clean_trials" | bc))
        
        status="OK"
        if [ $partial_fail_trials -gt 0 ]; then
            status="OK_WITH_PARTIAL_FAILS"
        fi
    else
        if [ $partial_fail_trials -gt 0 ]; then
            status="ALL_PARTIAL_FAILED"
        else
            status="NO_DATA"
        fi
    fi


    echo "${bs},${qd},${flows},${valid_clean_trials},${final_iops},${final_lat},${final_bw},${final_cpu},${final_miss},${status}" >> "$output_avg"
    

    if [ "$status" == "OK" ]; then
        echo "  ✓ BS=${bs}, QD=${qd}, Flows=${flows} -> [OK] (Valid Trials: ${valid_clean_trials}, AvgIOPS: ${final_iops})"
    elif [ "$status" == "OK_WITH_PARTIAL_FAILS" ]; then
        echo "  ⚠ BS=${bs}, QD=${qd}, Flows=${flows} -> [OK but Unstable] (Valid: ${valid_clean_trials}, PartialFail: ${partial_fail_trials})"
    elif [ "$status" == "ALL_PARTIAL_FAILED" ]; then
        echo "  ✗ BS=${bs}, QD=${qd}, Flows=${flows} -> [FAILED] All ${partial_fail_trials} trials had missing flows. Result set to 0."
    else
        echo "  ✗ BS=${bs}, QD=${qd}, Flows=${flows} -> [NO DATA] No results found."
    fi
    
done

echo ""
echo "Parsing completed!"
echo "1. Summary CSV : $output_avg"
echo "2. Raw Data CSV: $output_raw"