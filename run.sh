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

echo ">>> Running ryu"
ryu-manager experiment/sdn-controller/ares.py --verbose > logs/ares.log 2>&1 &
echo ">>> Running mininet"
sudo python experiment/network_abac.py > logs/network.log 2>&1

# kill pox
echo ">>> Killing ryu"
pkill ryu-manager
