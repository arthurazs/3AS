#!/bin/sh
IFNAME=$1
CMD=$2

if [ "$CMD" = "CONNECTED" ]; then
    echo "$IFNAME Starting MMS Server..."
    echo "$IFNAME Subscribing GOOSE..."
    sudo experiment/ieds/./server_ied_sub $IFNAME
fi

if [ "$CMD" = "DISCONNECTED" ]; then
    echo "$IFNAME Disconnected..."
fi
