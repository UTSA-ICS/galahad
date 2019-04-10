#!/bin/bash

# Base directory for Valor related files
VALOR_DIR="galahad/valor"

#
# Copy over relevant directories from git repo into EFS
#
# Copy over valor related files to EFS
sudo cp -Rp $HOME/$VALOR_DIR /mnt/efs

sudo mkdir -p /mnt/efs/galahad-keys

# Create necessary directories for construction, assembly and provisioning.
sudo mkdir -p /mnt/efs/images/base_ubuntu
sudo mkdir -p /mnt/efs/images/unities
sudo mkdir -p /mnt/efs/images/non_provisioned_virtues
sudo mkdir -p /mnt/efs/images/provisioned_virtues
