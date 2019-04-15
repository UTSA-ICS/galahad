#!/bin/bash

# Base directory for Valor related files
VALOR_DIR="galahad/valor"

GALAHAD_CONFIG_DIR="galahad-config"

#
# Copy over relevant directories from git repo into EFS
#
# Copy over valor related files to EFS
sudo cp -Rp $HOME/$VALOR_DIR /mnt/efs

sudo mkdir -p /mnt/efs/galahad-keys
sudo chown --reference=$HOME/$GALAHAD_CONFIG_DIR /mnt/efs/galahad-keys
sudo chmod --reference=$HOME/$GALAHAD_CONFIG_DIR /mnt/efs/galahad-keys
cp -p $HOME/$GALAHAD_CONFIG_DIR/excalibur_pub.pem /mnt/efs/galahad-keys
cp -p $HOME/$GALAHAD_CONFIG_DIR/rethinkdb_keys/rethinkdb_cert.pem /mnt/efs/galahad-keys
cp -p $HOME/$GALAHAD_CONFIG_DIR/elasticsearch_keys/kirk-keystore.jks /mnt/efs/galahad-keys
cp -p $HOME/$GALAHAD_CONFIG_DIR/elasticsearch_keys/truststore.jks /mnt/efs/galahad-keys

# Create necessary directories for construction, assembly and provisioning.
sudo mkdir -p /mnt/efs/images/base_ubuntu
sudo mkdir -p /mnt/efs/images/unities
sudo mkdir -p /mnt/efs/images/non_provisioned_virtues
sudo mkdir -p /mnt/efs/images/provisioned_virtues
