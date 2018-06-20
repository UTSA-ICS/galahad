obj-m := port_block_module.o
port_block_module-y := map.o
KDIR :=/lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)
default:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules
clean:
	rm *.o *.mod.o *.mod.c *.symvers *.order *.ko