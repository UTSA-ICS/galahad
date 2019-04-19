#!/bin/bash

# Parameters
ROOTFS_DIR="build"
SOURCE_MATERIAL="valor-sources"
KERNEL_VERSION="4.15.5-xenblanket"
XEN_VERSION="blanket-4.8.2-irq-vcpu0"

UBUNTU_RELEASE_NAME="xenial"
UBUNTU_APT_SOURCE="http://us.archive.ubuntu.com/ubuntu/"

PACKAGES=" \
    nfs-common \
    openvswitch-common \
    openvswitch-switch \
    bridge-utils \
    python2.7 \
    python-pip \
    grub2 \
"

#---------------
# Obtain and install host prerequisitites

HOST_TOOLS_NEEDED=
if ! which wget ; then HOST_TOOLS_NEEDED="${HOST_TOOLS_NEEDED} wget"; fi
if ! which debootstrap ; then HOST_TOOLS_NEEDED="${HOST_TOOLS_NEEDED} debootstrap"; fi
if ! which qemu-img ; then HOST_TOOLS_NEEDED="${HOST_TOOLS_NEEDED} qemu-utils"; fi

[ -z ${HOST_TOOLS_NEEDED} ] || sudo apt install ${HOST_TOOLS_NEEDED}

#---------------
# Install base distro into build directory

if [ -e "${ROOTFS_DIR}" ] ; then
    echo >&2 "Aborting: ${ROOTFS_DIR} already exists."
    exit 1
fi

sudo debootstrap --arch=amd64 \
    "${UBUNTU_RELEASE_NAME}" "${ROOTFS_DIR}" "${UBUNTU_APT_SOURCE}"

# Generate and configure the default locale to: en_US.UTF-8
# This suppresses error messages that would otherwise occur.
sudo chroot build locale-gen "en_US.UTF-8"
sudo chroot build update-locale "LANG=en_US.UTF-8"

#---------------
# Enable package sources: main and universe

echo -e "deb ${UBUNTU_APT_SOURCE} ${UBUNTU_RELEASE_NAME} main\ndeb"\
        "${UBUNTU_APT_SOURCE} ${UBUNTU_RELEASE_NAME} universe" | \
    sudo tee "${ROOTFS_DIR}"/etc/apt/sources.list

#---------------
# Install standard packages

sudo chroot "${ROOTFS_DIR}" apt update
sudo DEBIAN_FRONTEND=noninteractive chroot "${ROOTFS_DIR}" \
    apt-get -yq install ${PACKAGES}

#---------------
# Install XenBlanket packages and binaries

for BINARY in \
    "xen-${XEN_VERSION}.gz" \
    "vmlinuz-${KERNEL_VERSION}" \
    "System.map-${KERNEL_VERSION}" \
    "initrd.img-${KERNEL_VERSION}" \
    "config-${KERNEL_VERSION}"
do
    sudo cp --preserve=mode,timestamps "${SOURCE_MATERIAL}/${BINARY}" "${ROOTFS_DIR}"/boot/
done

# Install Linux kernel modules for the XenBlanket kernel
sudo mkdir -p "${ROOTFS_DIR}"/lib/modules
sudo tar zxf "${SOURCE_MATERIAL}/modules-${KERNEL_VERSION}.tgz" -C "${ROOTFS_DIR}"/lib/modules

#---------------
# Image customization here

# Set a default root password
echo "root:root" | sudo chroot "${ROOTFS_DIR}" chpasswd
# Set hostname
echo "valor" | sudo tee "${ROOTFS_DIR}"/etc/hostname
