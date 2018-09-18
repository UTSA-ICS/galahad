#!/bin/bash

# Retrieve keys and put them in their appropriate location
sudo mkdir -p /var/private/ssl/
git clone git@github.com:starlab-io/galahad-config.git

sudo cp galahad-config/rethinkdb_keys/rethinkdb.pem      /var/private/ssl/
sudo cp galahad-config/rethinkdb_keys/rethinkdb_cert.pem /var/private/ssl/
sudo cp galahad-config/excalibur_private_key.pem         /var/private/ssl/excalibur_key.pem

sudo chown rethinkdb:rethinkdb /var/private/ssl/*.pem
sudo chmod 600 /var/private/ssl/*.pem


# Set the hostname
sudo echo "127.0.0.1 rethinkdb.galahad.lab" >> /etc/hosts


# Add RethinkDB repository and install
sudo source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list
sudo wget -qO- https://download.rethinkdb.com/apt/pubkey.gpg | apt-key add -
sudo apt-get update
sudo apt-get --assume-yes install rethinkdb


# Put RethinkDB configuration file in its appropriate location
sudo cp rethinkdb.conf /etc/rethinkdb/instances.d/


# Restart RethinkDB with its new configuration file
sudo service rethinkdb restart


# Install python libraries for rethinkdb and configure the database
sudo apt-get --assume-yes install python2.7 python-pip
pip install rethinkdb
sudo python configure_rethinkdb.py
