#!/bin/bash

ethtool -G ens2np0 rx 256 tx 256
sleep 1

/home/changwoo/enable_arfs_2.sh
sleep 0.5

echo 1 > /proc/sys/my_page_pool/test_create_flag_numa0

ethtool -G ens2np0 rx 1024 tx 1024


echo 'complete changing descriptor'
sleep 3

