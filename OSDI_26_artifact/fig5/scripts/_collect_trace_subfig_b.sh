#!/bin/bash

mkdir -p temp
rm -rf temp/*

sysctl -w net.ipv4.tcp_rmem="4096 131072 3145728"

# 1. Tracepoint 비활성화 (새 이벤트 방지)
echo 0 > /sys/kernel/debug/tracing/events/mlx5_rx/mlx5_mpwqe_page_alloc/enable
# 2. 버퍼 초기화
echo > /sys/kernel/debug/tracing/trace
# 3. Tracepoint 활성화
echo 262144 > /sys/kernel/debug/tracing/buffer_size_kb # buffer size 256MB
echo 1 > /sys/kernel/debug/tracing/events/mlx5_rx/mlx5_mpwqe_page_alloc/enable
sleep 1
cat /sys/kernel/debug/tracing/trace_pipe > temp/mlx5_trace.log &
TRACE_PID=$!


# iperf3 서버 시작
taskset -c 0 iperf3 -s --one-off -p 5202 > temp/receiver_iperf_1.log &
taskset -c 2 iperf3 -s --one-off -p 5203 > temp/receiver_iperf_2.log &


# iperf3 클라이언트 실행
ssh changwoo@192.168.10.211 -tt "iperf3 -c 192.168.10.213 -t 5 -P 1 -p 5202 -Z" > temp/sender_iperf_1.log &
ssh changwoo@192.168.10.211 -tt "iperf3 -c 192.168.10.213 -t 5 -P 1 -p 5203 -Z" > temp/sender_iperf_2.log &


# 성능 측정
sleep 1
sar -P 0,2 1 4 > temp/receiver_util.log &

perf stat -a -C 0 -o temp/0_cache_miss.log -e LLC-loads,LLC-load-misses -- sleep 4 &
perf stat -a -C 2 -o temp/2_cache_miss.log -e LLC-loads,LLC-load-misses -- sleep 4 &

sleep 4
kill $TRACE_PID
wait

sleep 0.5
cat /sys/kernel/debug/tracing/trace >> temp/mlx5_trace.log

sleep 0.5
mkdir -p traces/subfig_b
mv temp/*.log traces/subfig_b
echo "All tests completed"
