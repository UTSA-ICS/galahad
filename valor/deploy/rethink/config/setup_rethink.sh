#!/bin/bash
source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | tee /etc/apt/sources.list.d/rethinkdb.list
wget -qO- https://download.rethinkdb.com/apt/pubkey.gpg | apt-key add -
apt-get update
apt-get --assume-yes install rethinkdb
cp /etc/rethinkdb/default.conf.sample /etc/rethinkdb/instances.d/instance1.conf
service rethinkdb restart
apt-get --assume-yes install python2.7 python-pip
pip install rethinkdb
