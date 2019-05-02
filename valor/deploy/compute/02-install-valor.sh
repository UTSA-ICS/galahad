#!/bin/bash

set -e # fail on any error
set -u # error on unbounded variables

#-------------
# Parameters
CONFIG_DIR="config"
PATH_TO_FILESYSTEM_DIR="build"

#
# Install standard system packages
#
PACKAGES=" \
    libaio1 \
    libcurl3 \
    libpixman-1-0 \
    libjpeg-turbo8 \
    libsdl1.2debian \
    libyajl2 \
"
sudo chroot "${PATH_TO_FILESYSTEM_DIR}" apt -yq install "${PACKAGES}"

#
# Install XenBlanket and Introspection related packages
#
XEN_PACKAGES=" \
    ./xen-upstream-4.8.2-16.04.deb \
    ./libvmi_0.13-1.deb \
    ./introspection-monitor_0.2-1.deb \
"
sudo chroot "${PATH_TO_FILESYSTEM_DIR}" apt-get -yq install "${XEN_PACKAGES}"
sudo chroot "${PATH_TO_FILESYSTEM_DIR}" ldconfig /usr/local/lib

#
# Configure XEN system files
#
cp "${CONFIG_DIR}"/vif-bridge "${PATH_TO_FILESYSTEM_DIR}"/etc/xen/scripts/vif-bridge
cp "${CONFIG_DIR}"/xen-network-common.sh "${PATH_TO_FILESYSTEM_DIR}"/etc/xen/scripts/xen-network-common.sh
cp "${CONFIG_DIR}"/xl.conf "${PATH_TO_FILESYSTEM_DIR}"/etc/xen/xl.conf
sudo chroot "${PATH_TO_FILESYSTEM_DIR}" systemctl enable xencommons

#
# Install introspection packages and files
#
cp "${CONFIG_DIR}"/libvmi/libvmi.conf "${PATH_TO_FILESYSTEM_DIR}"/etc/libvmi.conf
mkdir -p "${PATH_TO_FILESYSTEM_DIR}"/usr/share/libvmi/kernel-data
cp "${CONFIG_DIR}"/libvmi/kernel-data/System.map-4.13.0-46-generic "${PATH_TO_FILESYSTEM_DIR}"/usr/share/libvmi/kernel-data/System.map-4.13.0-46-generic

#
# Configure tty
#
cp "${CONFIG_DIR}"/hvc0.conf /etc/init/
rm -f /etc/init/ttyS0.conf

#
# Update rc.local to restart xencommons service
# which does not start by default
#
sed -i '/^exit 0/i \
\
#\
# Restart xencommons service\
#\
systemctl restart xencommons\
' "${PATH_TO_FILESYSTEM_DIR}"/etc/rc.local
