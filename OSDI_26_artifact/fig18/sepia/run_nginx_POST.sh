#!/bin/bash


server_ip="192.168.10.211"
test_duration=30
output_dir="./nginx_result_$(date +%Y%m%d_%H%M%S)"

# number of trials
TRIALS=1

# client core mask
CLIENT_CORE_MASK="0-35"

# payload sizes
value_sizes=(2097152 4194304)

# number of threads
thread_configs=(2 4 6 8 16)

# number of connections per thread
conns_per_thread_configs=(1) 


echo "Target: http://${server_ip}/"
echo "Output: ${output_dir}"
mkdir -p ${output_dir}


for size in "${value_sizes[@]}"; do
    lua_file="${size}B.lua"
    
    if [ ! -f "${lua_file}" ]; then
        echo "Error: ${lua_file} not found! Please create it first."
        exit 1
    fi

    echo ""
    echo "=== Testing Payload: ${size} Bytes ==="

    for threads in "${thread_configs[@]}"; do
        for cpt in "${conns_per_thread_configs[@]}"; do
            
            # total connections is calculated by the number of threads and the number of connections per thread
            total_connections=$((threads * cpt))

            for ((t=1; t<=TRIALS; t++)); do
                prefix="${size}B_t${threads}_cTotal${total_connections}_trial${t}"
                output_file="${output_dir}/${prefix}.txt"
                
                echo -n "  [Trial ${t}/${TRIALS}] Threads: ${threads}, Total Conns: ${total_connections} ... "

             
                taskset -c ${CLIENT_CORE_MASK} wrk \
                    -t${threads} \
                    -c${total_connections} \
                    -d${test_duration}s \
                    -s ${lua_file} \
                    http://${server_ip}/ \
                    > "${output_file}" 2>&1

                if [ -f "${output_file}" ]; then
                    bw=$(grep "Transfer/sec" "${output_file}" | awk '{print $2}')
                    req=$(grep "Requests/sec" "${output_file}" | awk '{print $2}')
                    
                    if [ -z "$bw" ]; then
                         echo "Fail (Socket Error or Timeout)"
                    else
                         echo "Done! (BW: ${bw}, Req: ${req})"
                    fi
                fi
                sleep 2
            done
        done
    done
done

echo ""
echo "All tests completed."
