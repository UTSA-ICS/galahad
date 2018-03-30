#!/bin/bash

IMG_FILE=$1
CONTAINER_NAME=$2
DOCKER_LOGIN=$3

ISO_FILE=virtue.cloudinit.iso
LOG_FILE=SERIAL.log
SSH_NAT_PORT=5555

IMG_SIZE=$(qemu-img info $IMG_FILE  | grep "virtual size" | cut -d' ' -f4 | sed 's/(//g')
if [ "$IMG_SIZE" -lt 3000000000 ]; then
	echo "VM Image size is less than required. Resizing..."
	qemu-img resize $IMG_FILE +3G
fi

echo "Generating new keypair"
ssh-keygen -N "" -f id_rsa

echo "Generating cloud-init scripts"
./cloud-init-generator.py -d ../../../docker-virtue/virtue -l "$DOCKER_LOGIN"  $CONTAINER_NAME
mkisofs -output $ISO_FILE  -volid cidata -joliet -rock meta-data user-data

echo "Starting VM with cloud-init data..."
qemu-system-x86_64 --enable-kvm -m 1024 -smp 1 -cdrom $ISO_FILE -device e1000,netdev=user.0 -netdev user,id=user.0,hostfwd=tcp::$SSH_NAT_PORT-:22 -drive file=$IMG_FILE,if=virtio,cache=writeback,index=0 -serial file:$LOG_FILE

