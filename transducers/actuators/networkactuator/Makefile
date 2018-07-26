
# This directory is different on a Virtue
#KDIR :=/lib/modules/$(shell uname -r)/build

KDIR :=/usr/src/linux-headers-$(shell uname -r)
PWD := $(shell pwd)

obj-m := actuator_network.o
actuator_network-objs := include/kmap.o netblock_module.o

all:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules
clean:
	make -C $(KDIR) M=$(PWD) clean
