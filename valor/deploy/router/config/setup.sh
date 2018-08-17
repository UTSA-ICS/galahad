#!/bin/bash
/bin/bash setup_rethink.sh
apt --assume-yes install ./xen-upstream-4.8.2.deb
apt --assume-yes install openvswitch-common
apt --assume-yes install openvswitch-switch
apt --assume-yes install bridge-utils
ovs-vsctl add-br hello-br0
if [ -f virtue-galahad.cfg ]; then
	rm virtue-galahad.cfg
fi
if [ -f me.cfg ]; then
	rm me.cfg
fi
python generate_config.py
while read line; do
        echo $line
	IFS='.' read -r -a array <<< "$line"
	port="vxlan"${array[2]}${array[3]}
	ovs-vsctl add-port hello-br0 $port -- set interface $port type=vxlan options:remote_ip=$line
done < virtue-galahad.cfg
tmp=$(cat me.cfg) && sudo sed -i "s/\$ME/$tmp/g" rc.local
mv /etc/rc.local /etc/rc.local.bak
cp rc.local /etc/rc.local
chmod 755 /etc/rc.local
