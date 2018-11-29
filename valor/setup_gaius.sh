#!/usr/bin/env bash

#
# Copy Gaius Code to appropriate location
#
cp -R ../valor /usr/share/valor
mkdir /usr/share/valor/gaius/cfg
chmod 755 /usr/share/valor/gaius/*
pip install /usr/share/valor

#
# Copy over service definition file
#
cp gaius.service /etc/systemd/system/

#
# Now install the service and then start it
#
systemctl daemon-reload
systemctl enable gaius.service
systemctl start gaius.service
