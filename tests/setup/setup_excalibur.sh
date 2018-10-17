#!/bin/bash

# Install everything required for testing, except the openldap server
BASE_DIR="galahad/tests/setup"

#
# Setup Routes to be able to get to the guestnet network for access to virtues
#
echo "  #" >> /etc/network/interfaces.d/50-cloud-init.cfg
echo "  # Routes to be able to reach the virtue guestnet subnet" >> /etc/network/interfaces.d/50-cloud-init.cfg
echo "  #" >> /etc/network/interfaces.d/50-cloud-init.cfg
echo "  post-up route add -net 10.91.0.0/16 gw 172.30.1.53" >> /etc/network/interfaces.d/50-cloud-init.cfg

sudo apt-get update
# Cannot yet automate responses to three-way merge prompts
#sudo apt-get upgrade -y
sudo apt-get install -y virtualenv python-pip libldap2-dev libsasl2-dev python-logilab-common nfs-common
sudo apt-get autoremove -y
sudo pip install --upgrade -r $HOME/$BASE_DIR/requirements.txt
