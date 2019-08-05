if [ -z "$1" ]; then
    echo "Usage: sh run.sh <interface>"
    exit 0
else

    clear

    echo ">>> Killing ryu and mininet"
    pkill ryu-manager
    pkill mn

    echo ">>> Cleaning logs"
    sudo rm -r logs/*

    echo ">>> Cleaning mininet"
    mkdir -p logs/pre
    sudo mn -c > logs/pre/mn_clean.log 2>&1

    echo ">>> Removing DNS"
    # sudo dpkg --remove whoopsie  # ubuntu only
    sudo systemctl disable avahi-daemon > logs/pre/avahi_disable.log 2>&1
    sudo service avahi-daemon stop > logs/pre/avahi_stop.log 2>&1

    echo ">>> Fix IP address"
    # sudo service NetworkManager restart
    MAC=$(sudo cat /sys/class/net/$1/address)
    sudo ifconfig $1 10.0.0.1 netmask 255.0.0.0
    # sudo arp -s 10.0.0.2 00:00:00:00:00:02

    echo ">>> Running ryu"
    ryu-manager --user-flags experiment/sdn-controller/flags.py experiment/sdn-controller/ares.py --mac_address $MAC --verbose > logs/ares.log 2>&1 &
    echo ">>> Running mininet"
    sudo python experiment/network_abac.py $MAC $1 > logs/network.log 2>&1

    # kill pox
    echo ">>> Killing ryu"
    pkill ryu-manager

    echo ">>> Restarting network interface"
    sudo service NetworkManager restart
fi
