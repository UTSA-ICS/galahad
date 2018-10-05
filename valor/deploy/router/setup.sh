#!/bin/bash

set -eu

GUESTNET_IP = "10.91.0.254"

#
# Call the base setuo script
#
/bin/bash ../base_setup.sh "${GUESTNET_IP}"

#
# Add Router entry to rethinkDB
#
pip install boto
python update_rethinkdb_with_router.py