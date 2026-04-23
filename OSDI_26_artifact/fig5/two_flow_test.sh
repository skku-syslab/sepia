#!/bin/bash

SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"

sysctl -w net.ipv4.tcp_rmem="4096 131072 3145728"

# 1. Tracepoint disable (prevent new events)
echo 0 > /sys/kernel/debug/tracing/events/mlx5_rx/mlx5_mpwqe_page_alloc/enable
# 2. Buffer initialize
echo > /sys/kernel/debug/tracing/trace
# 3. Tracepoint enable
echo 262144 > /sys/kernel/debug/tracing/buffer_size_kb # buffer size 256MB
echo 1 > /sys/kernel/debug/tracing/events/mlx5_rx/mlx5_mpwqe_page_alloc/enable
cat /sys/kernel/debug/tracing/trace_pipe > mlx5_trace.log &
TRACE_PID=$!


# iperf3 server start
taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &
taskset -c 2 iperf3 -s --one-off -p 5203 > receiver_iperf_2.log &


# iperf3 client execute
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 5 -P 1 -p 5202 -Z" > sender_iperf_1.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 5 -P 1 -p 5203 -Z" > sender_iperf_2.log &


# performance measurement
sleep 1
sar -P 0,2 1 4 > receiver_util.log &

perf stat -a -C 0 -o 0_cache_miss.log -e LLC-loads,LLC-load-misses -- sleep 4 &
perf stat -a -C 2 -o 2_cache_miss.log -e LLC-loads,LLC-load-misses -- sleep 4 &

sleep 4
kill $TRACE_PID
wait

sleep 0.5
cat /sys/kernel/debug/tracing/trace >> mlx5_trace.log

sleep 0.5
mkdir -p two_flow_1
mv *.log two_flow_1
echo "All tests completed"
