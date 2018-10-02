#!/bin/bash

set -e

GALAHAD_CONFIG_HOME=~/galahad-config
TRANSDUCERS_HOME=~/galahad/transducers
MERLIN_KEY_DIR=~/galahad/transducers/merlin/var/private/ssl
cd $TRANSDUCERS_HOME

# Copy keys and Certs from galahad-config repo
if [ ! -d "$MERLIN_KEY_DIR" ]; then
  mkdir -p $MERLIN_KEY_DIR
  # This is the root dir where the config repo should be
  if [ ! -d "$GALAHAD_CONFIG_HOME" ]; then
    echo "#########################################################################################"
    echo "ERROR: Config directory $GALAHAD_CONFIG_HOME does not exist"
    echo "Please ensure that the following dirs and files exist in [$GALAHAD_CONFIG_HOME]"
    echo "$GALAHAD_CONFIG_HOME/excalibur_pub.pem"
    echo "$GALAHAD_CONFIG_HOME/rethinkdb_keys"
    echo "$GALAHAD_CONFIG_HOME/virtue_instance_keys"
    echo "#########################################################################################"
    exit
  fi
  cp $GALAHAD_CONFIG_HOME/excalibur_pub.pem $MERLIN_KEY_DIR/.
  cp $GALAHAD_CONFIG_HOME/rethinkdb_keys/rethinkdb_cert.pem $MERLIN_KEY_DIR/.
  cp $GALAHAD_CONFIG_HOME/virtue_instance_keys/virtue_1_key.pem $MERLIN_KEY_DIR/.
  cp $GALAHAD_CONFIG_HOME/elasticsearch_keys/ca.pem $MERLIN_KEY_DIR/
  cp $GALAHAD_CONFIG_HOME/elasticsearch_keys/kirk.crtfull.pem $MERLIN_KEY_DIR/
  cp $GALAHAD_CONFIG_HOME/elasticsearch_keys/kirk.key.pem $MERLIN_KEY_DIR/
fi

cd $TRANSDUCERS_HOME
./build_deb.sh merlin
