#! /bin/sh

. /usr/src/sepia/OSDI_26_artifact/scripts/common_env.sh

intf=${1:-$IFACE}

ethtool -K $intf ntuple on

if [ $? -gt 0 ]; then

        echo "ERROR to enble ntuple"

        # exit

fi

echo 32768 > /proc/sys/net/core/rps_sock_flow_entries

for f in /sys/class/net/$intf/queues/rx-*/rps_flow_cnt; do echo 32768 > $f; done

/usr/src/sepia/OSDI_26_artifact/scripts/set_irq_affinity.sh $intf
service irqbalance stop