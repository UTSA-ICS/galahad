#!/bin/bash

EFS_URL=$1
UBUNTU_MNT=~/ubuntu_mnt
mkdir $UBUNTU_MNT

sudo apt-get install -y nfs-common
sudo mkdir /mnt/efs
sudo mount -t nfs $EFS_URL:/ /mnt/efs

sudo apt-get install -y xen-tools

# Workaround 1:
sudo dpkg -r xen-util-4.6

# Workaround 2:
sudo cp xm.tmpl /etc/xen-tools

sudo xen-create-image --hostname=Unity8GB --dhcp --dir=/mnt/efs/images --dist=xenial --vcpus=1 --memory=1024MB --genpass=0 --size=8GB --noswap

# Workaround 3:
sudo mount /mnt/efs/images/domains/Unity8GB/disk.img $UBUNTU_MNT
sudo cp sources.list $UBUNTU_MNT/etc/apt
sudo umount $UBUNTU_MNT
