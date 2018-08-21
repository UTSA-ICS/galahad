#!/bin/bash

EFS_ID="${1}"

sudo apt --assume-yes install nfs-common
sudo mkdir -p /mnt/efs
sudo su - root -c "echo \"${EFS_ID}:/ /mnt/efs nfs defaults 0 0\" >> /etc/fstab"
sudo mount -a
sudo cp -R /mnt/efs/deploy/rethink/config /home/ubuntu
cd /home/ubuntu/config
sudo /bin/bash setup.sh
