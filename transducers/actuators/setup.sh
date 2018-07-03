#!/bin/bash

make
sudo insmod actuator_network.ko
sudo cp netblock /usr/bin
echo "Setup complete. Run sudo netblock to add firewall rules"

