#!/bin/bash

EFS_ID="${1}"

sudo mkdir -p /mnt/efs
sudo su - root -c "echo \"${EFS_ID}:/ /mnt/efs nfs defaults 0 0\" >> /etc/fstab"
sudo mount -a
sudo cp -R /mnt/efs/deploy/router /home/ubuntu
cd /home/ubuntu/router
sudo /bin/bash setup.sh
sudo shutdown -r
