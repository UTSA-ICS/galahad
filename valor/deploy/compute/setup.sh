#!/bin/bash -xe

# Install Packages required for AWS EFS mount helper
apt-get update
apt-get -y install binutils

# Install the AWS EFS mount helper
git clone https://github.com/aws/efs-utils
cd efs-utils/
./build-deb.sh
apt-get -y install ./build/amazon-efs-utils*deb

# Create the base mount directory
mkdir -p /mnt/efs

# Mount the EFS file system
echo "${1}:/ /mnt/efs efs defaults,_netdev 0 0" >> /etc/fstab
mount -a

# Install System packages
apt-get -y install python-pip openvswitch-common openvswitch-switch bridge-utils

# Install pip packages
pip install rethinkdb==2.3.0.post6

# Base directory for the script to operate from
cd /mnt/efs/valor/deploy/compute

# Directory for storage of Galahad keys
GALAHAD_KEY_DIR="/mnt/efs/galahad-keys"

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
# Set the Network System Variables
#
sed -i 's/#net.ipv4.ip_forward/net.ipv4.ip_forward/' /etc/sysctl.conf
echo "#" >> /etc/sysctl.conf
echo "# Network variables for Valor Network" >> /etc/sysctl.conf
echo "net.ipv4.conf.all.rp_filter=0" >> /etc/sysctl.conf
echo "net.ipv4.conf.gre0.rp_filter=0" >> /etc/sysctl.conf

#
# Create User Groups for Syslog-Ng unix socket
#
addgroup camelot
adduser root camelot

#
# Install necessary System packages
#
# Xen Blanket and Introspection related Debian packages
apt --assume-yes install ./xen-upstream-4.8.2-16.04.deb ./libvmi_0.13-1.deb ./introspection-monitor_0.2-1.deb

# System packages
apt --assume-yes install libaio-dev libpixman-1-dev libyajl-dev libjpeg-dev libsdl-dev libcurl4-openssl-dev

#
# Set the IP Tables rules
#
iptables -A FORWARD --in-interface br0 -j ACCEPT
iptables --table nat -A POSTROUTING --out-interface br0 -j MASQUERADE
# Now save the iptables rules by installing the persistent package
DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install iptables-persistent

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

# Configure introspection files
cp config/libvmi/libvmi.conf /etc/libvmi.conf
mkdir -p /usr/share/libvmi/kernel-data
cp config/libvmi/kernel-data/System.map-4.13.0-46-generic /usr/share/libvmi/kernel-data/System.map-4.13.0-46-generic

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
