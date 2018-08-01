# Debugging a PVM's kernel in Xen

To debug the kernel running in a Xen domU:

1. Obtain `gdbsx` (which isn't packaged in `xen-tools` anymore, for some reason): 

```
git clone git://xenbits.xen.org/xen.git
cd xen
git checkout stable-4.6
sudo apt-get build-dep xen
./configure
cd tools/gdbsx
make
sudo make install
```

See also: https://wiki.xenproject.org/wiki/Compiling_Xen_From_Source

2. Get a copy of the Linux kernel you're running:

```
sudo mount -o loop /path/to/disk.img /mnt
cp /mnt/vmliunz .
sudo umount /mnt
```

3. Start the domU and get its ID:

```
xl create Unity2     # make sure /etc/xen/Unity2.cfg points to the right disk image
xl list              # check the ID field for Unity2
```

4. Run the `gdbsx` GDB stub:

```
gdb ./vmlinuz                       # this is the one you copied up there
(gdb) target remote dom0:9999       # do this in the GDB terminal
(gdb) continue                      # let domU keep running
```

See also: https://github.com/mirage/xen/tree/master/tools/debugger/gdbsx

5. Do something on the host

6. To break in, run `xl pause Unity2` - this will trap to the debugger, where you can use the normal kernel debugging kung fu.