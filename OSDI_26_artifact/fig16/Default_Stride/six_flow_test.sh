#!/bin/bash


. /usr/src/sepia/OSDI_26_artifact/scripts/common_env.sh

taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &
taskset -c 2 iperf3 -s --one-off -p 5203 > receiver_iperf_2.log &
taskset -c 4 iperf3 -s --one-off -p 5204 > receiver_iperf_3.log &
taskset -c 6 iperf3 -s --one-off -p 5205 > receiver_iperf_4.log &
taskset -c 8 iperf3 -s --one-off -p 5206 > receiver_iperf_5.log &
taskset -c 10 iperf3 -s --one-off -p 5207 > receiver_iperf_6.log &

ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5203 -Z" > sender_iperf_2.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5204 -Z" > sender_iperf_3.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5205 -Z" > sender_iperf_4.log &
sleep 0.2
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5206 -Z" > sender_iperf_5.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5207 -Z" > sender_iperf_6.log &

sleep 2
sar -P 0,2,4,6,8,10 1 27 > receiver_util.log &

sleep 27
wait


sleep 0.5
mkdir -p six_flow_${TEST_NUM:-1}
mv *.log six_flow_${TEST_NUM:-1}/