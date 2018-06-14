#!/bin/bash

set -e

GALAHAD_CONFIG_HOME=~/galahad-config
HEARTBEAT_LISTENER_HOME=~/galahad/transducers/listener/opt/heartbeatlistener
cd $HEARTBEAT_LISTENER_HOME

# Copy keys and Certs from galahad-config repo
if [ ! -d "keys" ]; then
  mkdir -p keys
  # This is the root dir where the config repo should be
  if [ ! -d "$GALAHAD_CONFIG_HOME" ]; then
    echo "#########################################################################################"
    echo "ERROR: Config directory $GALAHAD_CONFIG_HOME does not exist"
    echo "Please ensure that the following dirs and files exist in [$GALAHAD_CONFIG_HOME]"
    echo "$GALAHAD_CONFIG_HOME/excalibur_private_key.pem"
    echo "$GALAHAD_CONFIG_HOME/rethinkdb_keys"
    echo "$GALAHAD_CONFIG_HOME/elasticsearch_keys"
    echo "$GALAHAD_CONFIG_HOME/virtue_instance_keys"
    echo "#########################################################################################"
    exit
  fi
  cp -R $GALAHAD_CONFIG_HOME/excalibur_private_key.pem keys/.
  cp -R $GALAHAD_CONFIG_HOME/rethinkdb_keys keys/.
  cp -R $GALAHAD_CONFIG_HOME/elasticsearch_keys keys/.
  cp -R $GALAHAD_CONFIG_HOME/virtue_instance_keys keys/.
fi

cd ~/galahad/transducers
./build_deb.sh listener
sudo dpkg -i listener.deb
sudo systemctl start heartbeatlistener.service
