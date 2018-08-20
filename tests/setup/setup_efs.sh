#!/bin/bash

# Install and configure EFS file server on EFS server node
EFS_ID="${1}"

# Base directory for Valor related files
BASE_DIR="galahad/valor"

sudo apt-get update
sudo apt install --assume-yes nfs-common
sudo mkdir /mnt/efs
sudo mount -t nfs $EFS_ID:/ /mnt/efs
sudo cp -R $HOME/$BASE_DIR/deploy /mnt/efs
