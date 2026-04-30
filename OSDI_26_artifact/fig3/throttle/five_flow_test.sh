#!/bin/bash

# sysctl -w net.ipv4.tcp_rmem="4096 131072 6291456"
# sysctl -w net.ipv4.tcp_rmem="4096 131072 3145728"
# sysctl -w net.ipv4.tcp_rmem="4096 131072 2097152"
# sysctl -w net.ipv4.tcp_rmem="4096 131072 1572864"
sysctl -w net.ipv4.tcp_rmem="4096 131072 1258291"
# sysctl -w net.ipv4.tcp_rmem="4096 131072 1048576"
sleep 1


SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"

taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &
taskset -c 2 iperf3 -s --one-off -p 5203 > receiver_iperf_2.log &
taskset -c 4 iperf3 -s --one-off -p 5204 > receiver_iperf_3.log &
taskset -c 6 iperf3 -s --one-off -p 5205 > receiver_iperf_4.log &
taskset -c 8 iperf3 -s --one-off -p 5206 > receiver_iperf_5.log &

ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5203 -Z" > sender_iperf_2.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5204 -Z" > sender_iperf_3.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5205 -Z" > sender_iperf_4.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5206 -Z" > sender_iperf_5.log &
sleep 2
sar -P 0,2,4,6,8 1 27 > receiver_util.log &

perf stat -a -C 0 -o 0_cache_miss.log -e "r02d1,r10d1,LLC-loads,LLC-load-misses" -- sleep 27 &
perf stat -a -C 2 -o 2_cache_miss.log -e "r02d1,r10d1,LLC-loads,LLC-load-misses" -- sleep 27 &
perf stat -a -C 4 -o 4_cache_miss.log -e "r02d1,r10d1,LLC-loads,LLC-load-misses" -- sleep 27 &
perf stat -a -C 6 -o 6_cache_miss.log -e "r02d1,r10d1,LLC-loads,LLC-load-misses" -- sleep 27 &
perf stat -a -C 8 -o 8_cache_miss.log -e "r02d1,r10d1,LLC-loads,LLC-load-misses" -- sleep 27 &

ports=(5202 5203 5204 5205 5206)
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
mkdir -p five_flow_${TEST_NUM:-1}
mv *.log five_flow_${TEST_NUM:-1}/
echo "All tests completed"