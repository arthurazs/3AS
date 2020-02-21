clear

NUM_EV=300      # Number of Electric Vehicles
EV_BY_SW=22     # Number of Electric Vehicles by Switch
EXT_MACH=4      # Number of Extra Machines, other than the main one

echo ">>> Cleaning logs"
sudo rm -r logs/*

echo ">>> Cleaning mininet"
mkdir -p logs/pre
sudo mn -c > logs/pre/mn_clean.log 2>&1

echo ">>> Running ryu"
ryu-manager --user-flags experiment/sdn-controller/flags.py experiment/sdn-controller/ares_ev.py --num_ev $NUM_EV --ev_by_sw $EV_BY_SW --verbose > logs/ares.log 2>&1 &
echo ">>> Running mininet"
sudo python experiment/network_ev.py $NUM_EV $EV_BY_SW $EXT_MACH > logs/network.log 2>&1

echo ">>> Killing ryu"
pkill ryu-manager
