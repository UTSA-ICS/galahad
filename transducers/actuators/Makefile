KDIR :=/lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

obj-m := actuator_network.o
actuator_network-objs := map.o port_block_module.o

default:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules
clean:
	make -C $(KDIR) M=$(PWD) clean