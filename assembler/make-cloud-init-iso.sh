#!/bin/bash

ISO_IMG_DIR="~/virtue"
CLOUD_INIT_ISO_FILENAME="cloud-init-assembler.iso"
CLOUD_INIT_METADATA="meta-data"
CLOUD_INIT_USERDATA="user-data"

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
if ! command_exists genisoimage; then
    echo "Error: need to install genisoimage"
    exit 1
fi

# generate cloud-init iso
genisoimage -output "${ISO_IMG_DIR}/${CLOUD_INIT_ISO_FILENAME}" \
            -volid cidata \
            -joliet \
            -rock "${CLOUD_INIT_USERDATA}" "${CLOUD_INIT_METADATA}"

if [ $? -ne 0 ]; then
    echo "Error: genisoimage failed"
    exit 1
fi

if [ ! -f "${ISO_IMG_DIR}/${CLOUD_INIT_ISO_FILENAME}" ]; then
    echo "Error: failed to create Cloud Init ISO file: ${ISO_IMG_DIR}/${CLOUD_INIT_ISO_FILENAME}"
    exit 1
else
    echo "Success: created Cloud Init ISO file: ${ISO_IMG_DIR}/${CLOUD_INIT_ISO_FILENAME}"
fi

exit 0
