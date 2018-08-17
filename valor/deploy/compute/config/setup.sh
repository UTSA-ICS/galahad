#!/bin/bash
/bin/bash setup_rethink.sh
apt --assume-yes install ./xen-upstream-4.8.2-16.04.deb
apt --assume-yes install libaio-dev libpixman-1-dev libyajl-dev libjpeg-dev libsdl-dev
apt --assume-yes install openvswitch-common
apt --assume-yes install openvswitch-switch
apt --assume-yes install bridge-utils
apt --assume-yes install -f
systemctl restart xencommons
ovs-vsctl add-br hello-br0
if [ -f virtue-galahad.cfg ]; then
	rm virtue-galahad.cfg
fi
if [ -f domus.cfg ]; then
	rm domus.cfg
fi
if [ -f me.cfg ]; then
	rm me.cfg
fi
python generate_config.py
while read line; do
        echo $line
	IFS='.' read -r -a array <<< "$line"
	port="vxlan"${array[3]}
	ovs-vsctl add-port hello-br0 $port -- set interface $port type=vxlan options:remote_ip=$line
done < virtue-galahad.cfg
tmp=$(cat me.cfg) && sudo sed -i "s/\$ME/$tmp/g" docs/rc.local
mv /etc/rc.local /etc/rc.local.bak
cp docs/rc.local /etc/rc.local
chmod 755 /etc/rc.local
mv /etc/fstab /etc/fstab.bak
cp docs/fstab /etc/
cp docs/hvc0.conf /etc/init/
mv /etc/xen/scripts/vif-bridge /etc/xen/scripts/vif-bridge.bak
cp docs/vif-bridge /etc/xen/scripts/vif-bridge
mv /etc/xen/scripts/xen-network-common.sh /etc/xen/scripts/xen-network-common.sh.bak
cp docs/xen-network-common.sh /etc/xen/scripts/xen-network-common.sh
mv /etc/xen/xl.conf /etc/xen/xl.conf.bak
cp docs/xl.conf /etc/xen/xl.conf
rm -f /etc/init/ttyS0.conf
cp docs/id_rsa /root/.ssh/
cp docs/id_rsa.pub /root/.ssh/
cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
