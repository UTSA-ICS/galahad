#!/bin/bash

ISO_IMG_DIR="~/virtue"
GOLDEN_ISO_FILENAME="unity-base-gold.img"
TEST_ISO_FILENAME="unity-base.img"

# expand ISO_IMG_DIR path in case of ~/
ISO_IMG_DIR="${ISO_IMG_DIR/#\~/$HOME}"
if [ ! -d "${ISO_IMG_DIR}" ]; then
    echo "Error: missing ISO directory: ${ISO_IMG_DIR}"
    exit 1
fi

if [ ! -f "${ISO_IMG_DIR}/${GOLDEN_ISO_FILENAME}" ]; then
    echo "Error: missing golden ISO file: ${ISO_IMG_DIR}/${GOLDEN_ISO_FILENAME}"
    exit 1
fi

if [ -f "${ISO_IMG_DIR}/${TEST_ISO_FILENAME}" ]; then
    rm ${ISO_IMG_DIR}/${TEST_ISO_FILENAME}
fi

cp "${ISO_IMG_DIR}/${GOLDEN_ISO_FILENAME}" "${ISO_IMG_DIR}/${TEST_ISO_FILENAME}"

if [ ! -f "${ISO_IMG_DIR}/${TEST_ISO_FILENAME}" ]; then
    echo "Error: failed to create test ISO file: ${ISO_IMG_DIR}/${TEST_ISO_FILENAME}"
    exit 1
fi

exit 0
