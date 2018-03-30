
How to spin up Amazon VM for a given ROLE

## Prerequisites

- Linux instance with cloud-init installed
	- `sudo apt-get install cloud-init`

- docker-virtue repository checked out on the local file system.
- You have access to aws cli to get docker login password


## Find Unity VM Image

- Two options:
	- Follow instruction in https://github.com/starlab-io/galahad/tree/build-unity/unity
	- Download https://cloud-images.ubuntu.com/artful/current/artful-server-cloudimg-amd64.img

You will want to copy this file before the last step as the last step modifies the file in-place rather than creating a new one.

## Get docker login password

Once you have aws cli configured, run

```
DOCKER_LOGIN=`aws ecr get-login --no-include-email --region us-east-1`
```

This will store "docker login ..." command with password into $DOCKER_LOGIN variable.

## Generate the image

In the future there will be one file that runs every stage. For now only Stage1 is available. To run it

```
cd stage1
./run.sh <unity_img> <docker-virtue-container-name> $DOCKER_LOGIN
```

This will spin up a QEMU VM that will prep itself to run the specified container and then run it.
