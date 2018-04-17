#!/bin/bash

## Install syslog-ng
wget -qO - http://download.opensuse.org/repositories/home:/laszlo_budai:/syslog-ng/xUbuntu_16.04/Release.key | apt-key add -
echo deb http://download.opensuse.org/repositories/home:/laszlo_budai:/syslog-ng/xUbuntu_16.04 ./ >> /etc/apt/sources.list.d/syslog-ng-obs.list
apt update
apt install syslog-ng-core -y

## Copy over config
git clone https://github.com/starlab-io/galahad.git
cd galahad/
git checkout transducers
cp transducers/syslog-ng-config/syslog-ng-server.conf /etc/syslog-ng/syslog-ng.conf


