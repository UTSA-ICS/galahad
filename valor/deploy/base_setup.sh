#!/usr/bin/env bash


GUESTNET_IP="${1}"

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
