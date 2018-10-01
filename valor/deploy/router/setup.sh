#!/bin/bash

set -eu

#
# Setup rehthink DB
#
/bin/bash setup_rethink.sh

#
# # Add Router entry to rethinkDB
#
pip install boto
python update_rethinkdb_with_router.py

# Install necessary System packages
#
apt --assume-yes install ./xen-upstream-4.8.2.deb
apt --assume-yes install openvswitch-common
apt --assume-yes install openvswitch-switch
apt --assume-yes install bridge-utils

#
# Configure scripts using information from rethinkDB
#
python generate_config.py

#
# Setup and configure a openvswitch bridge - hello-br0
#
ovs-vsctl add-br hello-br0
while read line; do
        echo $line
	IFS='.' read -r -a array <<< "$line"
	port="vxlan"${array[2]}${array[3]}
	ovs-vsctl add-port hello-br0 $port -- set interface $port type=vxlan options:remote_ip=$line
done < virtue-galahad.cfg

#
# Add routing for hello-br0 device and bring it up
#
ip address add "$(cat me.cfg)/24" dev hello-br0
ifconfig hello-br0 up

#
# Setup and configure bridge br0 with interface eth0
#
echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
rm -f /etc/network/interfaces.d/50-cloud-init.cfg
echo "auto br0" >> /etc/network/interfaces
echo "iface br0 inet dhcp" >> /etc/network/interfaces
echo "  bridge_ports br0 eth0" >> /etc/network/interfaces
echo "  bridge_stp off" >> /etc/network/interfaces
echo "  bridge_fd 0" >> /etc/network/interfaces
echo "  bridge_maxwait 0" >> /etc/network/interfaces

#
# Set the IP Tables rules
#
iptables -A FORWARD --in-interface br0 -j ACCEPT
iptables --table nat -A POSTROUTING --out-interface br0 -j MASQUERADE
# Now save the iptables rules by installing the persistent package
DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install iptables-persistent

#
# Update rc.local
#
#
# Update rc.local for hello-br0 routing and system commands
#
sed -i '/exit 0/i \
#\
# Add routing for hello-br0 device and bring it up\
#\
ip address add \"$(cat /home/ubuntu/router/me.cfg)/24\" dev hello-br0\
ifconfig hello-br0 up\
\
#\
# Add ip_gre module and start xencommons service\
#\
modprobe ip_gre\
systemctl start xencommons\
' /etc/rc.local
