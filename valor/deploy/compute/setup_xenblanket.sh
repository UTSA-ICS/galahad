#!/bin/bash

set -e # fail on any error
set -u # error on unbounded variables

#
# Parameters
#
SOURCE_MATERIAL="boot"
KERNEL_VERSION="4.15.5-xenblanket"
XEN_VERSION="blanket-4.8.2-irq-vcpu0"
DOM0_MEMORY="2048M"
DISK_SIZE_IN_BYTES="5368709120"

#
# Base directory for the script to operate from
#
cd /mnt/efs/valor/deploy/compute

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
sudo apt -yq install ${PACKAGES}

#
# Install XenBlanket and Introspection related packages
#
XEN_PACKAGES=" \
    ./xen-upstream-4.8.2-16.04.deb \
    ./libvmi_0.13-1.deb \
    ./introspection-monitor_0.2-1.deb \
"
sudo apt-get -yq install ${XEN_PACKAGES}
sudo ldconfig /usr/local/lib

#
# Install XenBlanket Kernel and binaries
#
for BINARY in \
    "xen-${XEN_VERSION}.gz" \
    "vmlinuz-${KERNEL_VERSION}" \
    "System.map-${KERNEL_VERSION}" \
    "initrd.img-${KERNEL_VERSION}" \
    "config-${KERNEL_VERSION}"
do
    sudo cp --preserve=mode,timestamps "${SOURCE_MATERIAL}/${BINARY}" /boot/
done

#
# Install Linux kernel modules for the XenBlanket kernel
#
sudo tar zxf "${SOURCE_MATERIAL}/modules-${KERNEL_VERSION}.tgz" -C /lib/modules

#
# Create a device map for GRUB
#
echo "(hd0) /dev/xvda" | sudo tee "/boot/grub/device.map"

#
# Write the Valor GRUB partial config entry
#
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
        search --no-floppy --label --set=root cloudimg-rootfs
        echo    'Loading Valor ...'
        multiboot /boot/xen-${XEN_VERSION}.gz apic_verbosity=verbose sched=credit tdt=0 com1=115200,8n1 console=com1 dom0_mem=${DOM0_MEMORY},max:${DOM0_MEMORY} loglvl=all guest_loglvl=all
        module /boot/vmlinuz-${KERNEL_VERSION} root=/dev/xvda1 ro LANG=en_US.UTF-8 highres=off acpi=off console=hvc0 console=ttyS0,115200n8 console=tty0 selinux=0 noexec=off noexec32=off sysrq_always_enabled
        module /boot/initrd.img-${KERNEL_VERSION}
}
EOF
sudo chmod 755 /etc/grub.d/45_valor

#
# Make Valor the default boot entry
#
sudo sed -i 's/^\(GRUB_DEFAULT=\).*$/\1"Valor"/' -i "/etc/default/grub"
sudo update-grub

#
# Write fstab
#
sudo tee <<EOF "/etc/fstab"
LABEL=cloudimg-rootfs / ext4 defaults,discard 0 0
none /proc/xen xenfs defaults 0 0
EOF

#
# Configure XEN system files
#
cp config/vif-bridge /etc/xen/scripts/vif-bridge
cp config/xen-network-common.sh /etc/xen/scripts/xen-network-common.sh
cp config/xl.conf /etc/xen/xl.conf
systemctl restart xencommons

#
# Install introspection packages and files
#
cp config/libvmi/libvmi.conf /etc/libvmi.conf
mkdir -p /usr/share/libvmi/kernel-data
cp config/libvmi/kernel-data/System.map-4.13.0-46-generic /usr/share/libvmi/kernel-data/System.map-4.13.0-46-generic

#
# Configure tty
#
cp config/hvc0.conf /etc/init/
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
' /etc/rc.local
