#!/bin/bash

# Install and configure EFS file server on EFS server node
EFS_ID="${1}"

sudo apt-get update
sudo apt install --assume-yes nfs-common
sudo mkdir /mnt/efs
sudo mount -t nfs $EFS_ID:/ /mnt/efs
