#!/bin/bash

#-------------
# Parameters
XEN_VERSION="blanket-4.8.2-irq-vcpu0"
LINUX_VERSION="4.15.5-xenblanket"
DOM0_MEMORY="2048M"
#DISK_SIZE_IN_BYTES="21474836480"
DISK_SIZE_IN_BYTES="5368709120"
PATH_TO_FILESYSTEM_DIR="build"
OVF_TEMPLATE="valor-template.ovf.in"
WORKDIR="workdir"

#-------------
mkdir -p "${WORKDIR}"

# Create a sparse disk image with a single bootable partition
truncate -s "${DISK_SIZE_IN_BYTES}" "${WORKDIR}/valor-disk.img"
printf '%b\n' 'n\n\n\n\n' a w q | fdisk "${WORKDIR}/valor-disk.img"

# Make the new partition within the disk image accessible
DISK_LOOPDEV=$(sudo losetup --show -Pf "${WORKDIR}/valor-disk.img")
PART_LOOPDEV="${DISK_LOOPDEV}p1"

# Create the ext4 filesystem on the partition in the disk image:
sudo mkfs.ext4 "${PART_LOOPDEV}"
sudo e2label "${PART_LOOPDEV}" "valor-rootfs"

# Mount the new filesystem so it can be populated
MOUNTPOINT="${WORKDIR}/mnt"
mkdir -p "${MOUNTPOINT}"
sudo mount -t ext4 "${PART_LOOPDEV}" "${MOUNTPOINT}"

# transfer the rootfs contents into the new filesystem
sudo tar cf - -C "${PATH_TO_FILESYSTEM_DIR}" . | sudo tar xf - -C "${MOUNTPOINT}"

# create a device node within the target filesystem that we can use for
# installation of the bootloader
TMPDEVDIR="tmpdev"
sudo mkdir "${MOUNTPOINT}/${TMPDEVDIR}"
sudo tar cf - -C "$(dirname ${DISK_LOOPDEV})" "$(basename ${DISK_LOOPDEV})" | \
    sudo tar xf - -C "${MOUNTPOINT}/${TMPDEVDIR}"
CHROOT_DISKDEV="/${TMPDEVDIR}/$(basename ${DISK_LOOPDEV})"

# Create a device map for GRUB
echo "(hd0) /dev/xvda" | sudo tee "${MOUNTPOINT}/boot/grub/device.map"

# Write the Valor GRUB partial config entry
sudo tee "${MOUNTPOINT}"/etc/grub.d/45_valor <<EOF
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
        module /boot/vmlinuz-${LINUX_VERSION} root=/dev/xvda1 ro LANG=en_US.UTF-8 highres=off acpi=off console=hvc0 console=ttyS0,115200n8 console=tty0 selinux=0 noexec=off noexec32=off sysrq_always_enabled
        module /boot/initrd.img-${LINUX_VERSION}
}
EOF
sudo chmod 755 "${MOUNTPOINT}"/etc/grub.d/45_valor

# Populate enough of the chroot to satisfy GRUB
sudo mount --bind /dev/ "${MOUNTPOINT}/dev"
sudo cp /proc/devices "${MOUNTPOINT}/proc/devices"

sudo chroot "${MOUNTPOINT}" \
    grub-install --no-floppy \
        --modules 'part_gpt part_msdos ext2' \
        --grub-mkdevicemap="/${TMPDEVDIR}/device.map" "${CHROOT_DISKDEV}"

# Make Valor the default boot entry
sudo sed -i 's/^\(GRUB_DEFAULT=\).*$/\1"Valor"/' -i "${MOUNTPOINT}/etc/default/grub"
sudo chroot "${MOUNTPOINT}" update-grub

# Done with devds for GRUB
sudo umount "${MOUNTPOINT}/dev"

# Tidying up
sudo rm "${MOUNTPOINT}/proc/devices"
sudo rm "${MOUNTPOINT}${CHROOT_DISKDEV}"
sudo rmdir "${MOUNTPOINT}/${TMPDEVDIR}"

# Write fstab
sudo tee <<EOF "${MOUNTPOINT}/etc/fstab"
LABEL=valor-rootfs / ext4 defaults,discard 0 0
none /proc/xen xenfs defaults 0 0
EOF

sudo umount "${MOUNTPOINT}"
rmdir "${MOUNTPOINT}"
sudo losetup -d "${DISK_LOOPDEV}"
# End of disk image creation
#-------------

#-------------
# Convert the raw disk image into a destination VM disk image format
# 'vpc' is what qemu-img people have (unhelpfully) decided to call 'vhd'.
qemu-img convert -f raw -O vpc "${WORKDIR}/valor-disk.img" "${WORKDIR}/valor-disk.vhd"

# OVF file is XML.  The template needs the following data:
# - size of the VHD file
# - capacity of the disk that the VHD file represents

VHD_FILE_SIZE=$(stat -c '%s' "${WORKDIR}/valor-disk.vhd")

sed <"${OVF_TEMPLATE}" >"${WORKDIR}/valor.ovf" \
    -e "s/%VHD_FILE_SIZE%/${VHD_FILE_SIZE}/g" \
    -e "s/%DISK_CAPACITY%/${DISK_SIZE_IN_BYTES}/g"

# Manifest file is a simple list of sha1sums of named files
OVF_SHA1SUM=$(sha1sum "${WORKDIR}/valor.ovf" | cut -f1 -d' ')
VHD_SHA1SUM=$(sha1sum "${WORKDIR}/valor-disk.vhd" | cut -f1 -d' ')
cat >"${WORKDIR}/valor.mf" <<EOF
SHA1(valor.ovf)= ${OVF_SHA1SUM}
SHA1(valor-disk.vhd)= ${VHD_SHA1SUM}
EOF

# The OVA file is a tar archive of manifest, OVF and disk(s).
tar cf "${WORKDIR}/valor.ova" -C "${WORKDIR}" valor.mf valor.ovf valor-disk.vhd

# End of virtual appliance generation
# ------
