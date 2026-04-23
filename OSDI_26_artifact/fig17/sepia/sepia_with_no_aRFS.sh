#!/bin/bash

echo 'NO aRFS'

echo 1 > /proc/sys/my_page_pool/test_create_flag_numa0
sleep 0.5

ethtool -G ens2np0 rx 256 tx 256

echo 'complete changing descriptor'
sleep 3
