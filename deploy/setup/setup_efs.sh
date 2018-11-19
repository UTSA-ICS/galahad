#!/bin/bash

# Install and configure EFS file server on EFS server node
EFS_ID="${1}"

# Base directory for Valor related files
VALOR_DIR="galahad/valor"

sudo apt-get update
sudo apt-get install --assume-yes nfs-common
sudo mkdir -p /mnt/efs
sudo su - root -c "echo \"${EFS_ID}:/ /mnt/efs nfs defaults 0 0\" >> /etc/fstab"
sudo mount -a

#
# Copy over relevant directories from git repo into EFS
#
# Copy over valor related files to EFS
sudo cp -Rp $HOME/$VALOR_DIR /mnt/efs

# Copy over the galahad-keys to EFS mount
sudo cp -Rp $HOME/galahad-keys /mnt/efs

# Create necessary directories for construction, assembly and provisioning.
sudo mkdir -p /mnt/efs/images/base_ubuntu
sudo mkdir -p /mnt/efs/images/unities
sudo mkdir -p /mnt/efs/images/non_provisioned_virtues
sudo mkdir -p /mnt/efs/images/provisioned_virtues
