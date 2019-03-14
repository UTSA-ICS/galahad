#!/usr/bin/env bash

# Base directory for the script to operate from
cd /mnt/efs/valor/deploy/compute

#
# Copy Gaius Code to appropriate location
#
mkdir -p /usr/share/valor/
cp -R /mnt/efs/valor/gaius /usr/share/valor/gaius
mkdir /usr/share/valor/gaius/cfg
chmod 755 /usr/share/valor/gaius/*

#
# Copy over service definition file
#
cp gaius.service /etc/systemd/system/
cp introspect.service /etc/systemd/system/

#
# Now install the service and then start it
#
systemctl daemon-reload
systemctl enable gaius.service
systemctl start gaius.service
systemctl enable introspect.service
systemctl start introspect.service
