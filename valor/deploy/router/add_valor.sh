#!/usr/bin/env bash

VALOR_IP="${1}"

#
# Add a port in the ovs switch with Valor's remote IP
#
while read line; do
	IFS='.' read -r -a array <<< "$line"
	port="vxlan"${array[2]}${array[3]}
	ovs-vsctl add-port hello-br0 $port -- set interface $port type=vxlan options:remote_ip=$line
done <<< $VALOR_IP
