#!/bin/bash

sudo systemctl stop memcached 2>/dev/null
sudo pkill memcached 2>/dev/null
sleep 1
echo "systemctl memcached stop"

MEM_MB=204800 # 200GB memory
LISTEN_IP="0.0.0.0"
PORT=11211
THREADS=4
CORE_MASK="0,2,4,6"
MAX_CONN=20000
MAX_REQ_PER_EVENT=100
MAX_ITEM_SIZE="2m"

taskset -c $CORE_MASK memcached -m $MEM_MB \
          -l $LISTEN_IP \
          -p $PORT \
          -t $THREADS \
          -c $MAX_CONN \
          -R $MAX_REQ_PER_EVENT \
          -I $MAX_ITEM_SIZE \
          -u nobody \
          -d

sleep 1
ss -tlnp | grep ":$PORT"

ps aux | grep memcached | grep -v "grep\|running_memcached"
