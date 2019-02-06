#!/bin/bash

# Install everything required for testing, except the openldap server
BASE_DIR="galahad/deploy/setup"

#
# Setup Routes to be able to get to the guestnet network for access to virtues
#
sudo su - root -c "echo \"  #\"                                                                        >> /etc/network/interfaces.d/50-cloud-init.cfg"
sudo su - root -c "echo \"  # Routes to be able to reach the virtue guestnet subnet (virtue network)\" >> /etc/network/interfaces.d/50-cloud-init.cfg"
sudo su - root -c "echo \"  #\"                                                                        >> /etc/network/interfaces.d/50-cloud-init.cfg"
sudo su - root -c "echo \"  post-up route add -net 10.91.0.0/16 gw 172.30.1.53\"                       >> /etc/network/interfaces.d/50-cloud-init.cfg"
# Added the routes temporarily so to take affect without a reboot
sudo route add -net 10.91.0.0/16 gw 172.30.1.53 dev eth0

sudo apt-get update
# Cannot yet automate responses to three-way merge prompts
#sudo apt-get upgrade -y
sudo apt-get install -y virtualenv python-pip libldap2-dev libsasl2-dev python-logilab-common nfs-common
sudo DEBIAN_FRONTEND=noninteractive apt-get install krb5-user
sudo apt-get autoremove -y
sudo pip install --upgrade -r $HOME/$BASE_DIR/requirements.txt
sudo rm /etc/krb5.conf
sudo cp $HOME/$BASE_DIR/krb5.conf /etc
