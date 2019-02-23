#!/bin/bash

IMAGE_NAME=$1
UBUNTU_MNT=~/ubuntu_mnt
mkdir -p $UBUNTU_MNT

# Create the Image
sudo xen-create-image --hostname=Unity$IMAGE_NAME --dhcp --dir=$HOME --dist=xenial --vcpus=1 --memory=1024MB --genpass=0 --size=$IMAGE_NAME --noswap

# Workaround:
sudo mount $HOME/domains/Unity$IMAGE_NAME/disk.img $UBUNTU_MNT
sudo cp sources.list $UBUNTU_MNT/etc/apt
sudo umount $UBUNTU_MNT

# Copy over the image as the unity Size name over to EFS
sudo mkdir -p /mnt/efs/images/base_ubuntu
sudo rsync -W $HOME/domains/Unity$IMAGE_NAME/disk.img /mnt/efs/images/base_ubuntu/$IMAGE_NAME.img

# Cleanup the image file/directory
sudo rm -rf $HOME/domains/Unity$IMAGE_NAME
