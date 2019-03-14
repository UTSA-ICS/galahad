#!/usr/bin/env bash

# Base directory for the script to operate from
cd /mnt/efs/valor

#
# Copy Gaius Code to appropriate location
#
cp -R /mnt/efs/valor /usr/share/valor
mkdir /usr/share/valor/gaius/cfg
chmod 755 /usr/share/valor/gaius/*
pip install /usr/share/valor

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
