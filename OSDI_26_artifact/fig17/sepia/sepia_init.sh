#!/bin/bash


./enable_arfs_2.sh
sleep 0.5

echo 1 > /proc/sys/my_page_pool/test_create_flag_numa0
sleep 0.5

ethtool -G ens2np0 rx 256 tx 256

echo 'complete changing descriptor'
sleep 3
