#!/bin/bash

headers="linux-headers-$(uname -r)"
yes | sudo apt-get install $headers
make
sudo insmod actuator_network.ko
sudo cp netblock /usr/bin/
sudo chmod +x /usr/bin/netblock
yes | sudo apt-get install sipcalc
yes | sudo apt-get install sed
sudo touch "/tmp/netblock.dat"
sudo chmod +x netblock
echo "Setup complete. Run sudo netblock to add firewall rules"
