#!/usr/bin/env bash

if [ "$#" -ne 2 ]; then
    echo "Usage: install_rethinkdb.sh path/to/rethinkdb.pem path/to/rethinkdb.conf"
    exit 1
fi

# Set hostname
echo "127.0.0.1 rethinkdb.galahad.lab" >> /etc/hosts

# Install rethinkdb
source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list
wget -qO- https://download.rethinkdb.com/apt/pubkey.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install rethinkdb

# Generate cert for this host and put in correct place
openssl req -new -x509 -key rethinkdb.pem -out rethinkdb_cert.pem -days 3650 -subj "/CN=rethinkdb.galahad.lab"
sudo mkdir -p /var/private/ssl/
sudo cp rethinkdb.pem /var/private/ssl/
sudo cp rethinkdb_cert.pem /var/private/ssl/
sudo chown rethinkdb:rethinkdb /var/private/ssl/*.pem
sudo chmod 600 /var/private/ssl/*.pem

# Put conf file in right place
sudo cp rethinkdb.conf /etc/rethinkdb/instances.d/

# Enable autostart and actually start rethinkdb
sudo systemctl enable rethinkdb@rethinkdb
sudo systemctl start rethinkdb@rethinkdb
