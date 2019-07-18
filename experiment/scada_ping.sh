#!/bin/sh
#wpa_cli -atst.sh
IFNAME=$1
CMD=$2

if [ "$CMD" = "CONNECTED" ]; then
    echo "$IFNAME Pinging..."
    ping -c 1 10.0.0.4
fi

if [ "$CMD" = "DISCONNECTED" ]; then
    echo "$IFNAME Disconnected..."
fi
