#!/bin/bash

EFS_URL=$1
UBUNTU_MNT=~/ubuntu_mnt
mkdir $UBUNTU_MNT

# Wait for /var/lib/dpkg/lock rather than fail
DPKG_LOCK=1
while (( $DPKG_LOCK -nz )); do
    sleep 5
    sudo apt-get install -y nfs-common
    DPKG_LOCK=$?
done

sudo mkdir /mnt/efs
sudo mount -t nfs $EFS_URL:/ /mnt/efs

DPKG_LOCK=1
while (( $DPKG_LOCK -nz )); do
    sleep 5
    sudo apt-get install -y xen-tools
    DPKG_LOCK=$?
done

# Workaround 1:
sudo dpkg -r xen-util-4.6

# Workaround 2:
sudo cp xm.tmpl /etc/xen-tools

sudo xen-create-image --hostname=Unity8GB --dhcp --dir=$HOME --dist=xenial --vcpus=1 --memory=1024MB --genpass=0 --size=8GB --noswap
sudo xen-create-image --hostname=Unity4GB --dhcp --dir=$HOME --dist=xenial --vcpus=1 --memory=1024MB --genpass=0 --size=4GB --noswap

# Workaround 3:
sudo mount $HOME/domains/Unity8GB/disk.img $UBUNTU_MNT
sudo cp sources.list $UBUNTU_MNT/etc/apt
sudo umount $UBUNTU_MNT

# Workaround 3 again:
sudo mount $HOME/domains/Unity4GB/disk.img $UBUNTU_MNT
sudo cp sources.list $UBUNTU_MNT/etc/apt
sudo umount $UBUNTU_MNT

sudo mkdir -p /mnt/efs/images/base_ubuntu
sudo rsync $HOME/domains/Unity8GB/disk.img /mnt/efs/images/base_ubuntu/8GB.img
sudo rsync $HOME/domains/Unity4GB/disk.img /mnt/efs/images/base_ubuntu/4GB.img
