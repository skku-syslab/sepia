#!/bin/bash

server_ip="192.168.10.211"
test_duration=30
output_dir="./memcached_set_results_$(date +%Y%m%d_%H%M%S)"

TRIALS=1

FIXED_CORE_MASK="0-35"

value_sizes=(524288 1048576)

thread_configs=(2 4 6 8 16)
connection_configs=(1) 
pipeline_configs=(4)

mem_budget_bytes=$((120 * 1024 * 1024 * 1024))
default_keys=1000000 

total_cases=$((${#value_sizes[@]} * ${#thread_configs[@]} * ${#connection_configs[@]} * ${#pipeline_configs[@]} * TRIALS))
warmup_time_min=2

test_time_min=$(( (total_cases * test_duration) / 60 ))
total_time_min=$(( warmup_time_min + test_time_min + 5 ))
total_time_hour=$(( total_time_min / 60 ))
total_time_min_remainder=$(( total_time_min % 60 ))

echo "Total Test Cases (with Trials): ${total_cases}"
echo "Estimated Test Time: ~${test_time_min}m"
echo "Estimated Total Time: ~${total_time_hour}h ${total_time_min_remainder}m"
echo "Taskset & SAR Range: ${FIXED_CORE_MASK}" 
echo ""

mkdir -p ${output_dir}

for value_size in "${value_sizes[@]}"; do
    echo ""
    echo "========================================"
    echo "=== VALUE SIZE: ${value_size}B ==="
    
    timeout 2 bash -c "echo 'flush_all' | nc -w 1 ${server_ip} 11211" 2>/dev/null
    sleep 10

    keys_for_this_run=${default_keys}
    required_wss=$((value_size * keys_for_this_run))
    
    if (( required_wss > mem_budget_bytes )); then
        keys_for_this_run=$((mem_budget_bytes / value_size))
    fi
    
    warmup_output="${output_dir}/warmup_${value_size}B.txt"
    echo "[Warmup] Loading ${keys_for_this_run} keys..."
    
    memtier_benchmark -s ${server_ip} -p 11211 --protocol=memcache_text \
    -c 1 -t 1 \
    --ratio=1:0 \
    --key-minimum=1 \
    --key-maximum=${keys_for_this_run} \
    --key-pattern=S:S \
    --data-size=${value_size} \
    --requests=${keys_for_this_run} \
    --print-percentiles="50,95,99,99.9" \
    > ${warmup_output} 2>&1
    
    echo "[Warmup] Done → ${warmup_output}"
    echo ""
    echo "[SET Tests] (Key Range: 1-${keys_for_this_run})"
    
    for threads in "${thread_configs[@]}"; do
        for connections in "${connection_configs[@]}"; do
            for pipeline in "${pipeline_configs[@]}"; do
                
                for ((t=1; t<=TRIALS; t++)); do
                    prefix="${value_size}B_t${threads}_c${connections}_p${pipeline}_trial${t}"
                    
                    echo "  [Trial ${t}/${TRIALS}] t=${threads} c=${connections} p=${pipeline}"
                    
                    taskset -c ${FIXED_CORE_MASK} memtier_benchmark -s ${server_ip} -p 11211 --protocol=memcache_text \
                    -c ${connections} -t ${threads} \
                    --pipeline=${pipeline} \
                    --ratio=1:0 \
                    --key-minimum=1 \
                    --key-maximum=${keys_for_this_run} \
                    --data-size=${value_size} \
                    --key-pattern=G:G \
                    --test-time=${test_duration} \
                    --print-percentiles="50,95,99,99.9" \
                    > "${output_dir}/set_${prefix}.txt" 2>&1 &
                    memtier_pid=$!
                    
                    timeout=$((test_duration + 10))
                    if ! timeout ${timeout} bash -c "while kill -0 $memtier_pid 2>/dev/null; do sleep 1; done"; then
                        echo "    ⚠ Warning: memtier timeout, killing..."
                        kill $memtier_pid 2>/dev/null
                    fi
                    wait $memtier_pid 2>/dev/null
                    
                    if [ -f "${output_dir}/set_${prefix}.txt" ]; then
                        ops=$(grep "^Sets" "${output_dir}/set_${prefix}.txt" | awk '{print $2}')
                        latency=$(grep "^Sets" "${output_dir}/set_${prefix}.txt" | awk '{print $6}')
                        echo "    → Result: ${ops} ops/sec, ${latency}ms"
                    fi

                    sleep 2

                done
            
            done
        done
    done
done

echo ""
echo "Experiment Completed! Results: ${output_dir}"
