#!/bin/bash
#
wget -qO - http://download.opensuse.org/repositories/home:/laszlo_budai:/syslog-ng/xUbuntu_16.04/Release.key | apt-key add -
echo deb http://download.opensuse.org/repositories/home:/laszlo_budai:/syslog-ng/xUbuntu_16.04 ./ >> /etc/apt/sources.list.d/syslog-ng-obs.list
apt update && apt install syslog-ng-core curl git -y

# Install modules and dependencies
add-apt-repository ppa:eugenesan/ppa
apt install syslog-ng-dev syslog-ng-mod-elastic python flex bison glib2.0 autoconf-archive openjdk-8-jdk libssl-dev libtool -y
echo export LD_LIBRARY_PATH=/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/amd64/server/ >> /home/virtue/.bashrc

# Build and install transducer module
export PKG_CONFIG_PATH=/usr/lib/pkgconfig/
git clone https://github.com/starlab-io/galahad.git
cd galahad/
git checkout transducers
cd transducers/transducer-module/
autoreconf -i
./configure && make && make install
cd

# Install elasticsearch searchguard dependencies
curl -L -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.6.3.tar.gz
tar -xzvf elasticsearch-5.6.3.tar.gz
cd elasticsearch-5.6.3/
./bin/elasticsearch-plugin install --batch com.floragunn:search-guard-5:5.6.3-16
mkdir /etc/syslog-ng/jars/
cp plugins/search-guard-5/*.jar /etc/syslog-ng/jars/
cd

# Copy over certs and config
cp galahad/transducers/syslog-ng-config/syslog-ng-virtue-node.conf /etc/syslog-ng/syslog-ng.conf
cp galahad/transducers/syslog-ng-config/elasticsearch.yml /etc/syslog-ng/
cp galahad/transducers/syslog-ng-config/certs/kirk-keystore.jks /etc/syslog-ng/
cp galahad/transducers/syslog-ng-config/certs/truststore.jks /etc/syslog-ng/

