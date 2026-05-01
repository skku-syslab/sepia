#!/bin/bash


echo 1 > /proc/sys/sepia_page_pool/sepia_init_flag_numa0

ethtool -G ens2np0 rx 256 tx 256

echo 'complete changing descriptor'
sleep 3
