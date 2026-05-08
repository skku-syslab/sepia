#!/bin/bash

/usr/src/sepia/OSDI_26_artifact/scripts/enable_arfs_2.sh
sleep 0.5

echo 1 > /proc/sys/sepia_page_pool/sepia_init_flag_numa0

. /usr/src/sepia/OSDI_26_artifact/scripts/common_env.sh
ethtool -G $IFACE rx 256 tx 256


echo 'complete changing descriptor'
sleep 3

