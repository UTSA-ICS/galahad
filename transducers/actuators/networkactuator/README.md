# **Network Actuator - Version 0.1**

Network actuator for blocking ports and IP addresses. Implemented using the netfilter framework: https://www.netfilter.org/documentation/HOWTO/netfilter-hacking-HOWTO-3.html


### To test within the Excalibur CLI:

transducer_enable **block_net** virtue_66bf0dfb573c42f7ae8435f1cf702438 **{"rules":["block_incoming_src_udp_53","block_outgoing_src_tcp_80"]}**

* Currently, the ruleset is provided via a JSON object **{}**. The current implementation of the Excalibur CLI does not yet allow spaces, so underscores can be used instead. This will be changed once Excalibur allows spaces. 
* Each time a new JSON configuration object is passed to this *transducer_enable block_net* command, the existing ruleset is wiped and replaced with the new JSON configuration object. This prevents us from having to keep a list of rules in Merlin, but we may change it later. 


#### Notes
* **incoming/outgoing** refer to the hook you would like to filter on i.e. *incoming* or *outgoing* traffic from the host.

### To install on a local VM for testing:
**./setup.sh** 

This will install the network actuator and allow you to run sample commands with the **netblock** command. Some sample commands are listed below.

##### Supported netblock Commands
* block [incoming/outgoing] [src/dst] ipv4 **IPv4 address**
* unblock [incoming/outgoing] [src/dst] ipv4 **IPv4 address**
* block [incoming/outgoing] [src/dst] ipv6 **IPv6 address**
* unblock [incoming/outgoing] [src/dst] ipv6 **IPv6 address**
* block [incoming/outgoing] [src/dst] tcp **port**
* unblock [incoming/outgoing] [src/dst] tcp **port**
* block [incoming/outgoing] [src/dst] udp **port**
* unblock [incoming/outgoing] [src/dst] udp **port**
* block [incoming/outgoing] [src/dst] ipport **IP:Port**
* unblock [incoming/outgoing] [src/dst] ipport **IP:Port**
* ls

##### **Example commands:**
* netblock block incoming ipv4 127.0.0.1
* netblock unblock outgoing udp 53
* netblock block outgoing src ipport 8.8.8.8:53
* netblock ls


Note: **src** and **dst** are meaningless for the **ipport** protocol. For instance, if you want to block all outgoing DNS traffic to Google's DNS servers you would use: **block outgoing [src/dst] ipport 8.8.8.8:53** OR if you want to block the reverse traffic: **block incoming [src/dst] ipport 8.8.8.8:53**


### Installing via the Debian Package File (galahad/assembler/payload/actuators)

Note that this is not necessary, but is documented for integration with the assembler. This part of the document also describes how new rules can be added to the system from Merlin or other VirtUE components. 

**dpkg -i netblock_actuator.deb**

**sudo insmod /lib/modules/4.13.0-38-generic/updates/dkms/actuator_network.ko**


A program can add new rules by writing to the character device at */dev/netblockchar*

Writing **unblock outgoing ipv4 127.0.0.1** to the file */dev/netblockchar* will unblock all outgoing IPv4 traffic from the localhost.

###### **Example of writing rules to the character device:**
*\#!/usr/bin/python*

*import os*

*fd = os.open("/dev/netblockchar", os.O_RDWR)*

*os.write(fd, "block incoming tcp 80")*

*os.close(fd)*


This will block all incoming traffic to port 80 on the host. Note that the python program should run with the correct permissions in order to work correctly. 