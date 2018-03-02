#!/bin/bash

ISO_IMG_DIR="~/virtue"
TEST_ISO_FILENAME="unity-base.img"
CLOUD_INIT_ISO_FILENAME="cloud-init-assembler.iso"

# test if executable / command is present
command_exists() {
    command -v "$@" > /dev/null 2>&1
}

# expand ISO_IMG_DIR path in case of ~/
ISO_IMG_DIR="${ISO_IMG_DIR/#\~/$HOME}"
if [ ! -d "${ISO_IMG_DIR}" ]; then
    echo "Error: missing ISO directory: ${ISO_IMG_DIR}"
    exit 1
fi

# install curl if not present
if ! command_exists kvm; then
    echo "Error: need to install kvm"
    exit 1
fi

if [ ! -f "${ISO_IMG_DIR}/${TEST_ISO_FILENAME}" ]; then
    echo "Error: failed to find base ISO file ${ISO_IMG_DIR}/${TEST_ISO_FILENAME}"
    exit 1
fi

if [ ! -f "${ISO_IMG_DIR}/${CLOUD_INIT_ISO_FILENAME}" ]; then
    echo "Error: failed to Cloud Init ISO file ${ISO_IMG_DIR}/${CLOUD_INIT_ISO_FILENAME}"
    exit 1
fi

echo
echo "... Attempting to start KVM ..."
echo
set -x
kvm -m 1024 \
    -smp 1 \
    -cdrom "${ISO_IMG_DIR}/${CLOUD_INIT_ISO_FILENAME}" \
    -device e1000,netdev=user.0 \
    -netdev user,id=user.0,hostfwd=tcp::5555-:22 \
    -drive file="${ISO_IMG_DIR}/${TEST_ISO_FILENAME}",if=virtio,cache=writeback,index=0
