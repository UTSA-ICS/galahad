#!/usr/bin/env bash


GUESTNET_IP="${1}"

#
# Install necessary System packages
#
apt-get update

DPKG_LOCK=1
while (( $DPKG_LOCK -nz )); do
    sleep 5
    apt --assume-yes install python-pip openvswitch-common openvswitch-switch bridge-utils
    DPKG_LOCK=$?
done

#
# Install rethinkdb python package
#
pip install rethinkdb

#
# Create a openvswitch bridge - hello-br0
#
ovs-vsctl add-br hello-br0

#
# Disable cloud init networking which sets eth0 to default settings.
#
echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
rm -f /etc/network/interfaces.d/50-cloud-init.cfg

#
# Setup and configure bridge br0 with interface eth0
#
echo "" >> /etc/network/interfaces
echo "#" >> /etc/network/interfaces
echo "# Bridge br0 for eth0" >> /etc/network/interfaces
echo "#" >> /etc/network/interfaces
echo "auto br0" >> /etc/network/interfaces
echo "iface br0 inet dhcp" >> /etc/network/interfaces
echo "  bridge_ports br0 eth0" >> /etc/network/interfaces
echo "  bridge_stp off" >> /etc/network/interfaces
echo "  bridge_fd 0" >> /etc/network/interfaces
echo "  bridge_maxwait 0" >> /etc/network/interfaces

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
# Set the IP Tables rules
#
iptables -A FORWARD --in-interface br0 -j ACCEPT
iptables --table nat -A POSTROUTING --out-interface br0 -j MASQUERADE
# Now save the iptables rules by installing the persistent package
DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install iptables-persistent

#
# Update rc.local for system commands
#
sed -i '/^exit 0/i \
\
#\
# Add ip_gre module\
#\
modprobe ip_gre\
' /etc/rc.local
