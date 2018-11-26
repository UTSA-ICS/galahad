#!/bin/bash


GUESTNET_IP="${1}"
ROUTER_IP="${2}"

# Directory for storage of Galahad keys
GALAHAD_KEY_DIR="/mnt/efs/galahad-keys"

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
# Install necessary System packages
#
DPKG_LOCK=1
while (( $DPKG_LOCK -nz )); do
    sleep 1
    apt --assume-yes install ./xen-upstream-4.8.2-16.04.deb
    DPKG_LOCK=$?
done
DPKG_LOCK=1
while (( $DPKG_LOCK -nz )); do
    sleep 1
    apt --assume-yes install -f
    DPKG_LOCK=$?
done

#
# Set the IP Tables rules
#
iptables -A FORWARD --in-interface br0 -j ACCEPT
iptables --table nat -A POSTROUTING --out-interface br0 -j MASQUERADE
# Now save the iptables rules by installing the persistent package
DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install iptables-persistent

#
# Configure a port in the ovs switch with Router's remote IP
#
while read line; do
	IFS='.' read -r -a array <<< "$line"
	port="vxlan"${array[3]}
	ovs-vsctl add-port hello-br0 $port -- set interface $port type=vxlan options:remote_ip=$line
done <<< $ROUTER_IP

#
# Set the MTU of eth0 to 9001 (Jumbo Frames) to ensure
# proper network connectivity with external nodes e.g excalibur
# Without this MTU increase (from 1500) SSH connections from excalibur to valor will hang.
#
echo "" >> /etc/network/interfaces
echo "#" >> /etc/network/interfaces
echo "# Increase MTU from 1500 to 9001 to ensure proper network connectivity" >> /etc/network/interfaces
echo "# with external nodes wjthn a higher MTU" >> /etc/network/interfaces
echo "#" >> /etc/network/interfaces
echo "post-up ip link set dev eth0 mtu 9001" >> /etc/network/interfaces

#
# Append entry in fstab for xen file system
#
echo "none /proc/xen xenfs defaults 0 0" >> /etc/fstab

#
# Configure XEN system files
#
cp config/vif-bridge /etc/xen/scripts/vif-bridge
cp config/xen-network-common.sh /etc/xen/scripts/xen-network-common.sh
cp config/xl.conf /etc/xen/xl.conf
systemctl restart xencommons

#
# Configure tty
#
cp config/hvc0.conf /etc/init/
rm -f /etc/init/ttyS0.conf

#
# Update rc.local for system commands
#
sed -i '/^exit 0/i \
\
#\
# Restart xencommons service\
#\
systemctl restart xencommons\
' /etc/rc.local

#
# Configure ssh keys for valor nodes to be able to access each other
#
cp $GALAHAD_KEY_DIR/valor-key /root/.ssh/id_rsa
cat $GALAHAD_KEY_DIR/valor-key.pub >> /root/.ssh/authorized_keys
