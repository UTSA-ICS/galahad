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

sudo xen-create-image --hostname=Unity8GB --dhcp --dir=/mnt/efs/images --dist=xenial --vcpus=1 --memory=1024MB --genpass=0 --size=8GB --noswap

# Workaround 3:
sudo mount /mnt/efs/images/domains/Unity8GB/disk.img $UBUNTU_MNT
sudo cp sources.list $UBUNTU_MNT/etc/apt
sudo umount $UBUNTU_MNT
