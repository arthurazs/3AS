clear

NUM_EV=300
EV_BY_SW=75

# echo ">>> Killing ryu and mininet"
# pkill ryu-manager
# pkill mn

echo ">>> Cleaning logs"
sudo rm -r logs/*

echo ">>> Cleaning mininet"
mkdir -p logs/pre
sudo mn -c > logs/pre/mn_clean.log 2>&1

# echo ">>> Removing DNS"
# sudo dpkg --remove whoopsie  # ubuntu only
# sudo systemctl disable avahi-daemon > logs/pre/avahi_disable.log 2>&1
# sudo service avahi-daemon stop > logs/pre/avahi_stop.log 2>&1

echo ">>> Running ryu"
ryu-manager --user-flags experiment/sdn-controller/flags.py experiment/sdn-controller/ares_ev.py --num_ev $NUM_EV --ev_by_sw $EV_BY_SW --verbose > logs/ares.log 2>&1 &
echo ">>> Running mininet"
# sudo python experiment/network_ev.py
sudo python experiment/network_ev.py $NUM_EV $EV_BY_SW > logs/network.log 2>&1
echo ">>> Restarting Interfaces"
# sudo service NetworkManager restart

# kill pox
echo ">>> Killing ryu"
pkill ryu-manager
