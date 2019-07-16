clear

echo ">>> Killing ryu and mininet"
pkill ryu-manager
pkill mn

echo ">>> Cleaning mininet"
sudo mn -c

echo ">>> Removing DNS"
sudo systemctl disable avahi-daemon
sudo service avahi-daemon stop

# run experiment
echo ">>> Cleaning logs"
sudo rm -r logs/*

#
echo ">>> Fix IP address"
MAC=$(sudo cat /sys/class/net/$1/address)
sudo ifconfig $1 10.0.0.1 netmask 255.0.0.0

echo ">>> Running ryu"
# TODO add MAC as param here
ryu-manager controller.py --verbose > logs/ryu.log 2>&1 &
echo ">>> Running mininet"
sudo python scenario.py $MAC > logs/mininet.log 2>&1

# kill pox
echo ">>> Killing ryu"
pkill ryu-manager

echo ">>> Restarting network interface"
sudo service NetworkManager restart
