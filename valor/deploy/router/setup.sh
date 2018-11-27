#!/bin/bash

set -eu

GUESTNET_IP="10.91.0.254"

#
# Call the base setup script
#
/bin/bash ../base_setup.sh "${GUESTNET_IP}"

#
# Set the IP Tables rules
#
# Allow traffic destined for 10.91.0.0/16 network to be masqueraded using hello-br0 bridge.
iptables --table nat -A POSTROUTING -d 10.91.0.0/16 -o hello-br0 -j MASQUERADE
# Now save the iptables rules by installing the persistent package
DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install iptables-persistent

#
# Add Router entry to rethinkDB
#
python update_rethinkdb_with_router.py