# **Network Actuator**

Network actuator for blocking ports, IP addresses, etc. 
Must have root permissions to run.

##### To install:
**./setup.sh** 

##### Installing via Debian Package File (galahad/assembler/payload/)
**dpkg -i netblock_actuator.deb**
**sudo insmod /lib/modules/4.13.0-38-generic/updates/dkms/actuator_network.ko**

A user can add new rules by running the **netblock** command.

Example: **sudo netblock block incoming tcp 80**
- this blocks all incoming TCP traffic on port 80


A program can add new rules by writing to the character device at */dev/netblockchar*

Writing **unblock outgoing ipv4 127.0.0.1** to the file */dev/netblockchar* will unblock all outgoing IPv4 traffic from the localhost.


##### Supported Network Commands
* block incoming ipv4 **IPv4 address**
* block outgoing ipv4 **IPv4 address**
* block incoming ipv6 **IPv6 address**
* block outgoing ipv6 **IPv6 address**
* block incoming tcp **port**
* block outgoing tcp **port**
* block incoming udp **port**
* block outgoing udp **port**

*As well as all the corresponding **unblock** commands*

###### Listing all existing rules
* ls

For example, running **netblock ls** will list all the existing firewill rules.
