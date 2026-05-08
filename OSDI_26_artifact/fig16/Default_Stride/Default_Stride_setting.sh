#!/bin/bash

. /usr/src/sepia/OSDI_26_artifact/scripts/common_env.sh
ethtool -G $IFACE rx 256 tx 256
sleep 1

echo 1 > /proc/sys/sepia_page_pool/sepia_init_flag_numa0

ethtool -G $IFACE rx 1024 tx 1024

echo 'complete changing descriptor'
sleep 3
