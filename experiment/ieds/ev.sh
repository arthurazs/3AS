#!/bin/sh
IFNAME=$1
CMD=$2

if [ "$CMD" = "CONNECTED" ]; then
    echo "$IFNAME Starting MMS Server..."
    python3 /home/arthurazs/git/3AS/experiment/ieds/ev.py
fi

if [ "$CMD" = "DISCONNECTED" ]; then
    echo "$IFNAME Disconnected..."
fi
