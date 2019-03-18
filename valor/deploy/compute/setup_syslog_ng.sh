#!/bin/bash
# Copyright (c) 2018 Raytheon BBN Technologies Corp.

# Base directory for the script to operate from
cd /mnt/efs/valor/deploy/compute

# install latest syslog-ng
wget -qO - http://download.opensuse.org/repositories/home:/laszlo_budai:/syslog-ng/xUbuntu_16.04/Release.key | apt-key add -
echo deb http://download.opensuse.org/repositories/home:/laszlo_budai:/syslog-ng/xUbuntu_16.04 ./ >> /etc/apt/sources.list.d/syslog-ng-obs.list
apt-get update
apt-get install syslog-ng-core=3.14.1-3 curl git -y

# Install syslog modules and dependencies
add-apt-repository -y ppa:eugenesan/ppa
apt-get install syslog-ng-mod-elastic=3.14.1-3 syslog-ng-mod-elastic=3.14.1-3 syslog-ng-mod-java=3.14.1-3 syslog-ng-mod-java-common-lib=3.14.1-3 openjdk-8-jdk -y
echo /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/amd64/server >> /etc/ld.so.conf.d/java.conf
ldconfig

# Install elasticsearch searchguard dependencies
curl -L -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.6.3.tar.gz
tar -xzvf elasticsearch-5.6.3.tar.gz
cd elasticsearch-5.6.3/
./bin/elasticsearch-plugin install --batch com.floragunn:search-guard-5:5.6.3-16
mkdir /etc/syslog-ng/jars/
cp plugins/search-guard-5/*.jar /etc/syslog-ng/jars/
cd ..
rm -rf elasticsearch-5.6.3/
rm elasticsearch-5.6.3.tar.gz

# write config files and keystores
cp syslog-ng/syslog-ng.conf /etc/syslog-ng/
cp syslog-ng/elasticsearch.yml /etc/syslog-ng/

cp syslog-ng/kirk-keystore.jks /etc/syslog-ng/
cp syslog-ng/truststore.jks /etc/syslog-ng/

chmod 644 syslog-ng/syslog-ng.service
cp syslog-ng/syslog-ng.service /lib/systemd/system/
systemctl daemon-reload
systemctl enable syslog-ng
