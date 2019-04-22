#!/bin/bash

#
#     *** IMPORTANT NOTE ***
# Please ensure that any setup related commands that do not require
# information from github repo or mounted file system should be issued
# in cloud-init for the server specified in the Cloud Formation YAML file
#     galahad/deploy/setup/galahad-stack.yaml
# This specially applies to installation of system packages using apt and pip.


# Base directory for Canvas related files
CANVAS_DIR="galahad/canvas"

# Galahad key dir
GALAHAD_KEY_DIR="/mnt/efs/galahad-keys"

#
# Setup Routes to be able to get to the guestnet network for access to virtues
#
sudo su - root -c "echo \"  #\"                                                                        >> /etc/network/interfaces.d/50-cloud-init.cfg"
sudo su - root -c "echo \"  # Routes to be able to reach the virtue guestnet subnet (virtue network)\" >> /etc/network/interfaces.d/50-cloud-init.cfg"
sudo su - root -c "echo \"  #\"                                                                        >> /etc/network/interfaces.d/50-cloud-init.cfg"
sudo su - root -c "echo \"  post-up route add -net 10.91.0.0/16 gw 172.30.1.53\"                       >> /etc/network/interfaces.d/50-cloud-init.cfg"
# Added the routes temporarily so to take affect without a reboot
sudo route add -net 10.91.0.0/16 gw 172.30.1.53 dev eth0
