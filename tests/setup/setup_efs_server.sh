#!/bin/bash

# Install and configure EFS file server on EFS server node
EFS_ID="${1}"
NFS_IP="${2}"

sudo apt-get update
sudo apt install --assume-yes nfs-common
sudo mkdir /mnt/efs
sudo mount -t nfs $EFS_ID:/ /mnt/efs
sudo mkdir /mnt/nfs
sudo mount -t nfs $NFS_IP:/ /mnt/nfs
sudo cp /mnt/nfs/export/vms/images/centos7.img /mnt/efs
