#!/bin/sh
#wpa_cli -atst.sh
IFNAME=$1
CMD=$2

if [ "$CMD" = "CONNECTED" ]; then
    echo "$IFNAME Starting MMS Server..."
    sudo experiment/ieds/./server_ied $IFNAME
fi

if [ "$CMD" = "DISCONNECTED" ]; then
    echo "$IFNAME Disconnected..."
fi
