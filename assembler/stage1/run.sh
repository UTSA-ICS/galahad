#!/bin/bash

IMG_FILE=$1

cp ../../../../artful-server-cloudimg-amd64.img ../unity-base.img

qemu-img resize $IMG_FILE +10G

ISO_FILE=virtue.cloudinit.iso
LOG_FILE=SERIAL.log

ssh-keygen -N "" -f id_rsa

./cloud-init-generator.py

mkisofs -output $ISO_FILE  -volid cidata -joliet -rock meta-data user-data

LOCAL_PORT=5555
qemu-system-x86_64 --enable-kvm -m 1024 -smp 1 -cdrom $ISO_FILE -device e1000,netdev=user.0 -netdev user,id=user.0,hostfwd=tcp::$LOCAL_PORT-:22 -drive file=$IMG_FILE,if=virtio,cache=writeback,index=0 -serial file:$LOG_FILE

