#!/bin/bash
# Copyright (c) 2018 Raytheon BBN Technologies Corp.

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

# Install pre-build module (taken from make install step of the transducer script)
tar xzf transducer-module.tar.gz
cd transducer-module
mkdir -p /usr/lib/syslog-ng/3.14
/bin/bash ./libtool   --mode=install /usr/bin/install -c   modules/transducer-controller/libtransducer-controller.la '/usr/lib/syslog-ng/3.14'
cd ..
rm -rf transducer-module/
rm transducer-module.tar.gz

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
mv syslog-ng.conf /etc/syslog-ng/
mv elasticsearch.yml /etc/syslog-ng/
mv kirk-keystore.jks /etc/syslog-ng/
mv truststore.jks /etc/syslog-ng/
mv sshd_config /etc/ssh/
systemctl enable syslog-ng
#systemctl start syslog-ng

echo 172.30.128.130 rethinkdb.galahad.com >> /etc/hosts
rm runme.sh
