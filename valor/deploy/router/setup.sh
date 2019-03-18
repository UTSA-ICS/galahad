#!/bin/bash

set -eu

GUESTNET_IP="10.91.0.254"

#
# Create a openvswitch bridge - hello-br0
#
ovs-vsctl add-br hello-br0

#
# Configure bridge hello-br0
#
echo "" >> /etc/network/interfaces
echo "#" >> /etc/network/interfaces
echo "# Bridge hello-br0 for ovs bridge hello-br0" >> /etc/network/interfaces
echo "#" >> /etc/network/interfaces
echo "auto hello-br0" >> /etc/network/interfaces
echo "iface hello-br0 inet static" >> /etc/network/interfaces
echo "  address ${GUESTNET_IP}/24" >> /etc/network/interfaces

#
# Set the Network System Variables
#
sed -i 's/#net.ipv4.ip_forward/net.ipv4.ip_forward/' /etc/sysctl.conf
echo "#" >> /etc/sysctl.conf
echo "# Network variables for Valor Network" >> /etc/sysctl.conf
echo "net.ipv4.conf.all.rp_filter=0" >> /etc/sysctl.conf
echo "net.ipv4.conf.gre0.rp_filter=0" >> /etc/sysctl.conf

#
# Set the IP Tables rules
#
# Allow traffic destined for 10.91.0.0/16 network to be masqueraded using hello-br0 bridge.
iptables --table nat -A POSTROUTING -d 10.91.0.0/16 -o hello-br0 -j MASQUERADE
# Now save the iptables rules by installing the persistent package
DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install iptables-persistent

#
# Add Router entry to rethinkDB
#
python update_rethinkdb_with_router.py