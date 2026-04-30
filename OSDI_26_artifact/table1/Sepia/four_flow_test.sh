#!/bin/bash

SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"

taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &
taskset -c 2 iperf3 -s --one-off -p 5203 > receiver_iperf_2.log &
taskset -c 4 iperf3 -s --one-off -p 5204 > receiver_iperf_3.log &
taskset -c 6 iperf3 -s --one-off -p 5205 > receiver_iperf_4.log &

ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5203 -Z" > sender_iperf_2.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5204 -Z" > sender_iperf_3.log &
ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5205 -Z" > sender_iperf_4.log &

sleep 2
sar -P 0,2,4,6 1 27 > receiver_util.log &

timeout -s SIGINT 25s /home/sanghyun/WorkSpace/imc_read_test/cha_read_test_nic_to_llc.exe > imc_read_test.log &

sleep 27
wait


sleep 0.5
mkdir -p four_flow_${TEST_NUM:-1}
mv *.log four_flow_${TEST_NUM:-1}/
