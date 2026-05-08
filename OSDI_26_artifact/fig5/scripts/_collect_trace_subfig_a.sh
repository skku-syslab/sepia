#!/bin/bash

mkdir -p temp
rm -rf temp/*

echo 0 > /sys/kernel/debug/tracing/events/mlx5_rx/mlx5_mpwqe_page_alloc/enable
echo > /sys/kernel/debug/tracing/trace
echo 262144 > /sys/kernel/debug/tracing/buffer_size_kb
echo 1 > /sys/kernel/debug/tracing/events/mlx5_rx/mlx5_mpwqe_page_alloc/enable
sleep 1
cat /sys/kernel/debug/tracing/trace_pipe > temp/mlx5_trace.log &
TRACE_PID=$!

. /usr/src/sepia/OSDI_26_artifact/scripts/common_env.sh

taskset -c 0 iperf3 -s --one-off -p 5202 > temp/receiver_iperf_1.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 5 -P 1 -p 5202 -Z" > temp/sender_iperf_1.log &

sleep 1
sar -P 0 1 4 > temp/receiver_util.log &

perf stat -a -C 0 -o temp/0_cache_miss.log -e LLC-loads,LLC-load-misses -- sleep 4 &

sleep 4
kill $TRACE_PID
wait

sleep 0.5
cat /sys/kernel/debug/tracing/trace >> temp/mlx5_trace.log

sleep 0.5
mkdir -p traces/subfig_a
mv temp/*.log traces/subfig_a
rm -rf temp
echo "All tests completed"
