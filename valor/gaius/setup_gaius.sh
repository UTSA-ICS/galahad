#!/usr/bin/env bash

#
# Copy Gaius Code to appropriate location
#
cp -R gaius /usr/share/
chmod 755 /usr/share/gaius/*

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
