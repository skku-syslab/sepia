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
taskset -c 16 iperf3 -s --one-off -p 5210 > receiver_iperf_9.log &
taskset -c 18 iperf3 -s --one-off -p 5211 > receiver_iperf_10.log &
taskset -c 20 iperf3 -s --one-off -p 5212 > receiver_iperf_11.log &
taskset -c 22 iperf3 -s --one-off -p 5213 > receiver_iperf_12.log &
taskset -c 24 iperf3 -s --one-off -p 5214 > receiver_iperf_13.log &
taskset -c 26 iperf3 -s --one-off -p 5215 > receiver_iperf_14.log &
taskset -c 28 iperf3 -s --one-off -p 5216 > receiver_iperf_15.log &
taskset -c 30 iperf3 -s --one-off -p 5217 > receiver_iperf_16.log &


ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5203 -Z" > sender_iperf_2.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5204 -Z" > sender_iperf_3.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5205 -Z" > sender_iperf_4.log &
sleep 0.2
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5206 -Z" > sender_iperf_5.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5207 -Z" > sender_iperf_6.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5208 -Z" > sender_iperf_7.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5209 -Z" > sender_iperf_8.log &
sleep 0.2
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5210 -Z" > sender_iperf_9.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5211 -Z" > sender_iperf_10.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5212 -Z" > sender_iperf_11.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5213 -Z" > sender_iperf_12.log &
sleep 0.2
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5214 -Z" > sender_iperf_13.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5215 -Z" > sender_iperf_14.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5216 -Z" > sender_iperf_15.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5217 -Z" > sender_iperf_16.log &

sleep 2
sar -P 0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30 1 27 > receiver_util.log &


sleep 27
wait


sleep 0.5
mkdir -p sixteen_flow_${TEST_NUM:-1}
mv *.log sixteen_flow_${TEST_NUM:-1}/
echo "All tests completed"