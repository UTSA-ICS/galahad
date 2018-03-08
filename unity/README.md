Building a Unity VM
====================

The first step to building the Unity VM is to build up a new kernel for the base image.
The kernel will have multiple security options applied along with the Galahad LSM.
The Galahad LSM is brought into the project as a submodule, so you need to make sure
that you have initialized the submodules with:
```
git submodule update --init --recursive
```

Then, you must have your cloud image initialized and running so that you can retrieve the kernel version information from it.
The password for the default server cloudimg account is 'password', so you will need to enter that when asked.
With the cloud image running, you can run the `build-kernel` script which will connect to 'localhost:5555' by default.
To build up the kernel image, you must have docker installed and running on your system.
The build of the kernel takes place inside of a docker container.
