#!/bin/bash


GUESTNET_IP="${1}"
ROUTER_IP="${2}"

#
# Call the base setup script
#
/bin/bash ../base_setup.sh "${GUESTNET_IP}"

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
    apt --assume-yes install libaio-dev libpixman-1-dev libyajl-dev libjpeg-dev libsdl-dev libcurl4-openssl-dev
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
# Configure ssh keys - TODO - configure dynamic keys
# Currently these keys do not exist
#
#cp docs/id_rsa /root/.ssh/
#cp docs/id_rsa.pub /root/.ssh/
#cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
