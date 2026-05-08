#!/bin/sh

# Network interface
IFACE="${IFACE:-ens2np0}"

# Experiment machine IP addresses and SSH user
SSH_USER="${SSH_USER:-changwoo}"
CLIENT_IP="${CLIENT_IP:-192.168.10.211}"
SERVER_IP="${SERVER_IP:-192.168.10.213}"
export IFACE
export SSH_USER
export CLIENT_IP
export SERVER_IP
