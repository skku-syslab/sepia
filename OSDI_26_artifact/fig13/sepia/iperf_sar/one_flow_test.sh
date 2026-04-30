#!/bin/bash

SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"

taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &


ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &


sleep 2
sar -P 0 1 27 > receiver_util.log &


sleep 27
wait


sleep 0.5
mkdir -p one_flow_${TEST_NUM:-1}
mv *.log one_flow_${TEST_NUM:-1}/

echo "All tests completed"