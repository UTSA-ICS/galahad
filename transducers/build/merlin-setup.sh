#!/bin/sh

# Create merlin user
groupadd transducer
useradd -G transducer -m merlin
echo "merlin:virtue" | chpasswd

# Install merlin-related files and keys
apt update
apt install -qy python python-pip
dpkg -i merlin.deb
chown -R merlin:transducer /opt/merlin

# Give merlin user permission to use the keys
chown -R merlin:transducer /var/private/ssl
