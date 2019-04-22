#!/bin/bash

set -e
set -u

# Parameters
SOURCE_MATERIAL="valor-sources"
KERNEL_VERSION="4.15.5-xenblanket"
KERNEL_VERSION="4.15.5-xenblanket"
XEN_VERSION="blanket-4.8.2-irq-vcpu0"
DOM0_MEMORY="2048M"
DISK_SIZE_IN_BYTES="5368709120"


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
# Install standard packages

sudo apt update
# The below packages are newer than required.
sudo apt -y remove grub-pc grub-common
sudo DEBIAN_FRONTEND=noninteractive \
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
    sudo cp --preserve=mode,timestamps "${SOURCE_MATERIAL}/${BINARY}" /boot/
done

# Install Linux kernel modules for the XenBlanket kernel
sudo tar zxf "${SOURCE_MATERIAL}/modules-${KERNEL_VERSION}.tgz" -C /lib/modules

#---------------
# Image customization here


#-------------
# Create a device map for GRUB
echo "(hd0) /dev/xvda" | sudo tee "/boot/grub/device.map"

# Write the Valor GRUB partial config entry
sudo tee /etc/grub.d/45_valor <<EOF
#!/bin/sh
exec tail -n +3 \$0

menuentry 'Valor' --class ubuntu --class gnu-linux --class gnu --class os \$menuentry_id_option 'gnulinux-4.15.0+-advanced-f86631b2-7777-8888-9999-ac111cb77e4b' {
        recordfail
        load_video
        gfxmode \$linux_gfx_mode
        insmod gzio
        insmod part_msdos
        insmod ext2
        set root='hd0,msdos1'
        search --no-floppy --label --set=root valor-rootfs
        echo    'Loading Valor ...'
        multiboot /boot/xen-${XEN_VERSION}.gz apic_verbosity=verbose sched=credit tdt=0 com1=115200,8n1 console=com1 dom0_mem=${DOM0_MEMORY},max:${DOM0_MEMORY} loglvl=all guest_loglvl=all
        module /boot/vmlinuz-${KERNEL_VERSION} root=/dev/xvda1 ro LANG=en_US.UTF-8 highres=off acpi=off console=hvc0 console=ttyS0,115200n8 console=tty0 selinux=0 noexec=off noexec32=off sysrq_always_enabled
        module /boot/initrd.img-${KERNEL_VERSION}
}
EOF
sudo chmod 755 /etc/grub.d/45_valor

# Make Valor the default boot entry
sudo sed -i 's/^\(GRUB_DEFAULT=\).*$/\1"Valor"/' -i "/etc/default/grub"
sudo update-grub

# Write fstab
sudo tee <<EOF "/etc/fstab"
LABEL=cloudimg-rootfs / ext4 defaults,discard 0 0
none /proc/xen xenfs defaults 0 0
EOF

# Xen Blanket and Introspection related Debian packages
sudo apt --assume-yes install ./xen-upstream-4.8.2-16.04.deb ./libvmi_0.13-1.deb ./introspection-monitor_0.2-1.deb
sudo ldconfig /usr/local/lib

# System packages
sudo apt --assume-yes install libaio-dev libpixman-1-dev libyajl-dev libjpeg-dev libsdl-dev libcurl4-openssl-dev

########################################################
# Workaround for vm not being able to find boot device
# This needs to be fixed!
# During the installation of xen-tools the boot loader
# is updated somehow without which the VM will not boot
# The packages installed by xen-tools are not really
# needed and can be removed.
# Need to figure out what is configured/updated during
# the installation of xen-tools packages.
########################################################
# Remove the xen package for version 4.8
sudo apt -y purge xen-upstream

# Install xen-tools which will install
# xen packages for version 4.6
sudo apt -y install xen-tools
# Following xen related packages will be installed
#---------------------------
# grub-xen-bin
# grub-xen-host
# libxen-4.6:amd64
# libxenstore3.0:amd64
# xen-hypervisor-4.6-amd64
# xen-tools
# xen-utils-4.6
# xen-utils-common
# xenstore-utils
#---------------------------
# Now go ahead and remove the packages as they are not needed.
sudo apt -y purge \
     grub-xen-bin \
     grub-xen-host \
     libxen-4.6:amd64 \
     libxenstore3.0:amd64 \
     xen-hypervisor-4.6-amd64 \
     xen-tools \
     xenstore-utils \
     xen-utils-4.6 \
     xen-utils-common
# Remove packages not being used (stale)
sudo apt -y autoremove

# Install back the xenblanket version 4.8 based xen packages.
sudo apt -y install ./xen-upstream-4.8.2-16.04.deb
