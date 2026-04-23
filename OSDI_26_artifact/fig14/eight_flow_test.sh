#!/bin/bash


SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"

taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &
taskset -c 2 iperf3 -s --one-off -p 5203 > receiver_iperf_2.log &
taskset -c 4 iperf3 -s --one-off -p 5204 > receiver_iperf_3.log &
taskset -c 6 iperf3 -s --one-off -p 5205 > receiver_iperf_4.log &
taskset -c 8 iperf3 -s --one-off -p 5206 > receiver_iperf_5.log &
taskset -c 10 iperf3 -s --one-off -p 5207 > receiver_iperf_6.log &
taskset -c 12 iperf3 -s --one-off -p 5208 > receiver_iperf_7.log &
taskset -c 14 iperf3 -s --one-off -p 5209 > receiver_iperf_8.log &

ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5203 -Z" > sender_iperf_2.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5204 -Z" > sender_iperf_3.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5205 -Z" > sender_iperf_4.log &
sleep 0.2
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5206 -Z" > sender_iperf_5.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5207 -Z" > sender_iperf_6.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5208 -Z" > sender_iperf_7.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5209 -Z" > sender_iperf_8.log &

sleep 2
sar -P 0,2,4,6,8,10,12,14 1 27 > receiver_util.log &

ports=(5202 5203 5204 5205 5206 5207 5208 5209)
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
mkdir -p eight_flow_${TEST_NUM:-1}
mv *.log eight_flow_${TEST_NUM:-1}/
echo "All tests completed"