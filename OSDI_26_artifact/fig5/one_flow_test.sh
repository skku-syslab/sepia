#!/bin/bash

SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"

# 1. Tracepoint disable (prevent new events)
echo 0 > /sys/kernel/debug/tracing/events/mlx5_rx/mlx5_mpwqe_page_alloc/enable
# 2. Buffer initialize
echo > /sys/kernel/debug/tracing/trace
# 3. Tracepoint enable
echo 262144 > /sys/kernel/debug/tracing/buffer_size_kb
echo 1 > /sys/kernel/debug/tracing/events/mlx5_rx/mlx5_mpwqe_page_alloc/enable
cat /sys/kernel/debug/tracing/trace_pipe > mlx5_trace.log &
TRACE_PID=$!


# iperf3 server start
taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &


# iperf3 client execute
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 5 -P 1 -p 5202 -Z" > sender_iperf_1.log &


# performance measurement
sleep 1
sar -P 0 1 4 > receiver_util.log &

perf stat -a -C 0 -o 0_cache_miss.log -e LLC-loads,LLC-load-misses -- sleep 4 &


sleep 4
kill $TRACE_PID
wait

sleep 0.5
cat /sys/kernel/debug/tracing/trace >> mlx5_trace.log


sleep 0.5
mkdir -p one_flow_1
mv *.log one_flow_1
echo "All tests completed"
