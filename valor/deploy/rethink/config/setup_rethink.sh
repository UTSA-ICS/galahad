#!/bin/bash

# bbn - Install rethinkdb
source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | tee /etc/apt/sources.list.d/rethinkdb.list
wget -qO- https://download.rethinkdb.com/apt/pubkey.gpg | apt-key add -
apt-get update
apt-get --assume-yes install rethinkdb

# bbn - Generate cert for this host and put in correct place
openssl req -new -x509 -key rethinkdb.pem -out rethinkdb_cert.pem -days 3650 -subj "/CN=rethinkdb.galahad.lab"
sudo mkdir -p /var/private/ssl/
sudo cp rethinkdb.pem /var/private/ssl/
sudo cp rethinkdb_cert.pem /var/private/ssl/
sudo chown rethinkdb:rethinkdb /var/private/ssl/*.pem
sudo chmod 600 /var/private/ssl/*.pem

# bbn - Put conf file in right place
sudo cp rethinkdb.conf /etc/rethinkdb/instances.d/

# bbn - Enable autostart and actually start rethinkdb
sudo systemctl enable rethinkdb@rethinkdb
sudo systemctl start rethinkdb@rethinkdb


# idk
# kelli - cp /etc/rethinkdb/default.conf.sample /etc/rethinkdb/instances.d/instance1.conf
# kelli - service rethinkdb restart

apt-get --assume-yes install python2.7 python-pip
pip install rethinkdb

python setup_rethinkdb.py
