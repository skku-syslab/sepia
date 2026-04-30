#!/bin/bash

./enable_arfs_2.sh
sleep 0.5

echo 1 > /proc/sys/sepia_page_pool/test_create_flag_numa0

ethtool -G ens2np0 rx 256 tx 256


echo 'complete changing descriptor'
sleep 3


SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"

taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &


ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &


sleep 2
sar -P 0 1 27 > receiver_util.log &

perf stat -a -C 0 -o 0_cache_miss.log -e "LLC-loads,LLC-load-misses" -- sleep 27 &


sleep 28
wait

echo "Toy experiment ended"
