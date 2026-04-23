#!/bin/bash

SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"

LLC_MASKS=(
  "0xFFF"  # 12bit
  "0x3FF"  # 10bit
  "0x0FF"   # 8bit
  "0x03F"   # 6bit
  "0x00F"   # 4bit
  "0x003"   # 2bit
)

BIT_NAMES=(
  "12bit"
  "10bit"
  "8bit"
  "6bit"
  "4bit"
  "2bit"
)

for i in "${!LLC_MASKS[@]}"; do
  echo "=========================================="
  echo "Running: ${BIT_NAMES[$i]} (Mask: ${LLC_MASKS[$i]})"
  echo "=========================================="
  
  pqos -R
  sleep 0.5
  
  pqos -a "llc:1=0"
  pqos -e "llc:1=${LLC_MASKS[$i]}"
  sleep 0.5
  

  taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &

  ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &
  

  sleep 2
  sar -P 0 1 27 > receiver_util.log &

  perf stat -a -C 0 -o 0_cache_miss.log -e LLC-loads,LLC-load-misses -- sleep 27 &
 
  
  sleep 27
  wait
  sleep 0.5
  
  DIR_NAME="default_kernel_${BIT_NAMES[$i]}_one_flow"
  mkdir -p $DIR_NAME
  mv *.log $DIR_NAME
  
done

pqos -R
sleep 0.5