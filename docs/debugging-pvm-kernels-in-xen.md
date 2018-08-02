# Debugging a PVM's kernel in Xen

To debug the kernel running in a Xen domU:

1. Obtain `gdbsx` (which isn't packaged in `xen-tools` anymore, for some reason): 

        git clone git://xenbits.xen.org/xen.git
        cd xen
        git checkout stable-4.6
        sudo apt-get build-dep xen
        ./configure
        cd tools/gdbsx
        make
        sudo make install
  See also: https://wiki.xenproject.org/wiki/Compiling_Xen_From_Source

2. Get a copy of the Linux kernel you're running:

        sudo mount -o loop /path/to/disk.img /mnt
        cp /mnt/vmliunz .
        sudo umount /mnt

3. Start the domU and get its ID:

        xl create /etc/xen/Unity2     # make sure /etc/xen/Unity2.cfg points to the right disk image
        xl list              # check the ID field for Unity2

4. Run the `gdbsx` GDB stub:

        gdb ./vmlinuz                       # this is the one you copied up there
        (gdb) target remote dom0:9999       # do this in the GDB terminal
        (gdb) continue                      # let domU keep running
  See also: https://github.com/mirage/xen/tree/master/tools/debugger/gdbsx

5. Do something on the host

6. To break in, run `xl pause Unity2` - this will trap to the debugger, where you can use the normal kernel debugging kung fu.

---

Note: to figure out what IP address the Unity has (from https://wiki.xenproject.org/wiki/Xen_FAQ_Networking)

> I want to know the IP of a running VM in XEN. Is there any way to have this without login to that VM?
>
> Yes. First, you need to find the MAC address of the domU. This can be done by running:
> 
> `xl network-list <domU name>`
>
> which should produce an output similar to:
> 
> ```
> Idx BE MAC Addr.         handle state evt-ch   tx-/rx-ring-ref BE-path
> 0   0  00:16:3E:F7:D6:E7 0      4     6      16238/16237       /local/domain/0/backend/vif/163/0
> ```
>
> The domU's MAC address is 00:16:3E:F7:D6:E7
> 
> You now need to snoop the bridge for domU's MAC. For example:
> 
> ```
> $ sudo tcpdump -n -i eno1 ether src 00:16:3e:f7:d6:e7 
> tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
> listening on eth0, link-type EN10MB (Ethernet), capture size 96 bytes
> 15:54:56.419482 IP 10.0.0.10 > 10.0.0.1: ICMP echo reply, id 5443, seq 1, length 64 15:54:57.422349
> IP 10.0.0.10 > 10.0.0.1: ICMP echo reply, id 5443, seq 2, length 64
> ```
> 
> Then you know that domU has IP address 10.0.0.10.