# Assembler Notes

Basic notes for the VirtUE project's assembler.

Make sure you review the Cloud-Init reference materials:
  - [Cloud-Init site](http://cloudinit.readthedocs.io/en/latest)
  - [AWS CLI and Cloud-Init](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html#user-data-cloud-init)


## Requirements

Expected configuration of a development system:

  - Ubuntu or Debian, best with 64-bit Ubuntu 16.04.X LTS
  - there is a KVM-compatible IMG file that is the working copy of a golden / base image of the Unity VM
  - Dependencies: kvm, genisoimage

Make sure there are saved copies of your Unity golden / base image just in case something unexpected happens to it while doing Cloud-Init / Assembler development.


## Setup

First, make sure your development system has the requisite dependencies.

```
sudo apt install genisoimage qemu-kvm
```

Create a working directory (e.e., `~/virtue`) to store the relevant ISO and IMG files needed to test in KVM. The contained assembler scripts expect to find this directory using the variable `ISO_IMG_DIR` you find in each script. As a staring point, this directory must contain the golden / base image file for the Unity VM.

```
mkdir ~/virtue
cp <PATH_TO_GOLDEN_IMG_DIR>/unity-base.img ~/virtue/unity-base.img
```

Once the IMG and ISO working directory is set and it contains a copy of the Unity golden / base image, make a copy of the base image with the included script `./rebase-img.sh`. No input arguments are expected.

```
cd <DIR_FOR_THIS_GIT_REPO>/assembler
./rebase-img.sh
```

Now one must create the Cloud-Init ISO file that will configure the Unity base image. The file `user-data` contains the details for setting up the image. Make changes as you see fit. The `meta-data` file currently sets the instance and hostname for the system. These are placeholders for what will likely be replaced by more complex management software / scripts in the final architecture (see AWS CLI link from introduction section).

Note, there are two users created by default with Cloud-Init: 1) username: `ubuntu`, password: whatever is in the `password:` directive atop the file, and 2) username: `virtue`, password: `virtue`. These can be changed, removed, or replaced as necessary. Furthermore, it is possible to switch to SSH based authentication (see Cloud-Init references materials).

```
./make-cloud-init-iso.sh
```

Assuming the Cloud-Init ISO creation script returned with error, there will be a new ISO file in the directory `ISO_IMG_DIR` (`~/virtue` in our example here). With that created and the clean Unity image file from the re-basing step, you are now ready to spin-up the KVM guest.

```
./spin-up-kvm-img.sh
```

You should see a QEMU / KVM window appear with boot output. Depending on how the original image was generated, you may need to hit the keyboard to get the boot started.

Once the image is fully booted, you can log in with the credentials listed above or with the SSH keys you provision. Note. the `spin-up-kvm-img.sh` script initially sets up port forwarding on localhost port 5555 to ssh port 22 on the guest. Use or change as you see fit.

```
ssh ubuntu@127.0.0.1 -p 5555
```

Once booted and logged into the Unity VM, you should be able to monitor the Cloud-Init provisioning process using its provided mechanisms or using the output logging file that is setup in the `user-data` script. Initially the file is located at `/var/log/cloud-init-output.log`. If left in place, it will log the output of the Cloud-Init script.

```
tail -n 100 /var/log/cloud-init-output.log
```

## Cleaning an Image

Whenever you need to make changes to the Cloud-Init script and start afresh, you can re-run the re-basing script to start over with a newly cleaned Unity base image.

```
cd <DIR_FOR_THIS_GIT_REPO>/assembler
./rebase-img.sh
```
