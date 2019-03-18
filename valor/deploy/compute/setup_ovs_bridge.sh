#!/usr/bin/env bash

GUESTNET_IP="${1}"
ROUTER_IP="${2}"

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
# Configure a port in the ovs switch with Router's remote IP
#
while read line; do
	IFS='.' read -r -a array <<< "$line"
	port="vxlan"${array[3]}
	ovs-vsctl add-port hello-br0 $port -- set interface $port type=vxlan options:remote_ip=$line
done <<< $ROUTER_IP
