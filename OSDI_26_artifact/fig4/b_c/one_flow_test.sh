#!/bin/bash

SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"

taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &

ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &

sleep 2
sar -P 0 1 27 > receiver_util.log &

perf stat -a -C 0 -o 0_cache_miss.log -e "LLC-loads,LLC-load-misses" -- sleep 27 &


ports=(5202)
sample_interval=0.1
sample_count=200

for ((i=1; i<=sample_count; i++)); do
    for port in "${ports[@]}"; do
        log_file="socket_memory_${port}.log"
        echo "=== Sample ${i} ===" >> "${log_file}"
        ss -tm sport = :"${port}" >> "${log_file}" 2>&1
    done
    sleep "${sample_interval}"
done &


sleep 27
wait


sleep 0.5
mkdir -p one_flow_${TEST_NUM:-1}
mv *.log one_flow_${TEST_NUM:-1}/
echo "All tests completed"