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

echo ">>> Running ryu"
ryu-manager example_switch_13.py --verbose > logs/ryu.log 2>&1 &
echo ">>> Running mininet"
sudo python topo.py > logs/mininet.log 2>&1

# kill pox
echo ">>> Killing ryu"
pkill ryu-manager
