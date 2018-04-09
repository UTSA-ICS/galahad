Building a Unity VM
====================

Requirements
------------

Basic requirements include:
1. Being able to run `sudo`
2. Being able to kick off a virtual machine with `kvm`
3. Being able to create and execute `docker` containers.

Rough Build Instructions
------------------------

1. Make sure you have a base cloud image downloaded. By default, it should be named `artful-server-cloudimg-amd64.img` in this directory.
2. In a terminal, execute `sudo ./start-unity start`. This will show you the serial console of the VM.
3. In a separate terminal, execute the `./build-kernel` script. It will download the LSM from Github for you.
4. Wait for a while.
5. Eventually, the build will finish, copy the kernel debs to the image, install them, and reboot.

Further Build Details
---------------------

You need to have a base image running somewhere. If you download [https://cloud-images.ubuntu.com/artful/current/artful-server-cloudimg-amd64.img](https://cloud-images.ubuntu.com/artful/current/artful-server-cloudimg-amd64.img) into the current directory, you can just run:
`sudo ./start-unity start` to kick off the Unity base image.
You can pass the absolute path of the base image file (this will be modified by the build process) as a secondary argument to the `start-unity` script.
You must have your cloud image initialized and running so that you can retrieve the kernel version information from it and apply the new kernel to the image.

The first step to building the Unity VM is to build up a new kernel for the base image.
The kernel will have multiple security options applied along with the Galahad LSM.
By default, the `build-kernel` script will look for the LSM in the `$(pwd)/lsm` directory, but it can be overridden by setting the `LSM` environment variable to the directory.
If the `${LSM}` directory does not exist, the `build-kernel` script will attempt to clone it from `LSM_REPO`, which defaults to the GitHub repo.

The password for the default server cloudimg account is 'password', so you will need to enter that when asked.
With the cloud image running, you can run the `build-kernel` script which will connect to 'localhost:5555' by default.
To build up the kernel image, you must have docker installed and running on your system.
The build of the kernel takes place inside of a docker container.
During the build process, all of the patches found inside of the `${LSM}` directory will be applied to the `kernel-source` in-order.
Then, the security-related config options will be applied to the kernel config.
Finally, if there is an `lsm.config` file in the root of the `${LSM}` directory, those config options will be applied to the kernel config.
During initial testing, nothing is setting the `SECURITY_VIRTUE` flag that gets introduced with the LSM patches, so you have to manually set that.
Additing an `lsm.config` with the following contents will alleviate the need to do that:
```
SECURITY_VIRTUE=y
```
