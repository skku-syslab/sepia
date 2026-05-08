#! /bin/sh

/usr/src/sepia/OSDI_26_artifact/scripts/enable_arfs_2.sh

sleep 1

. /usr/src/sepia/OSDI_26_artifact/scripts/common_env.sh

taskset -c 0 iperf3 -s --one-off -p 5202 > receiver_iperf_1.log &


ssh "${SSH_USER}@${CLIENT_IP}" -tt "iperf3 -c ${SERVER_IP} -t 30 -P 1 -p 5202 -Z" > sender_iperf_1.log &


sleep 2
sar -P 0 1 27 > receiver_util.log &

perf stat -a -C 0 -o 0_cache_miss.log -e "LLC-loads,LLC-load-misses" -- sleep 27 &


sleep 28
wait

echo "Toy experiment ended"
