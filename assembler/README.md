
How to spin up Amazon VM for a given ROLE(s)

## Prerequisites

- Linux instance with ssh, python3, and py-yaml library
	- `pip3 install pyyaml`
	- Optional dependency: qemu-kvm 

- You have access to aws cli to get docker login password
	- Follow this URL to configure aws cli interface: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html


## Find Unity VM Image

- Two options:
	- Follow instruction in https://github.com/starlab-io/galahad/tree/build-unity/unity
	- Download https://cloud-images.ubuntu.com/artful/current/artful-server-cloudimg-amd64.img

You will want to copy this file before the last step as the last step modifies the file in-place rather than creating a new one.

## Get docker login password

Once you have aws cli configured, run `./get_docker_login_command.sh` and follow the on-screen prompts for the MFA token. Once complete the last output of that script will provide a `docker login ...` command. Store it in a bash variable or copy-paste it as an argument to the assemble.py. This readme will use `$DOCKER_LOGIN` in place of that command.

## Generate the image

`./assemble.py -h` will print a list of all options. 

### Option 1: Running on QEMU
If you have qemu-kvm installed, simply run

```
./assemble.py --docker-login "$DOCKER_LOGIN" --start-vm <path_to_Unity_image> -r +3G virtue_container [virtue_container ...]
```

This will generate proper cloud-init config and start a qemu vm with that config. Once the cloud-init finishes, the SSH stages will run, and finally the machine will be shut-down and the assembly process will be complete. After this point `<path_to_Unity_image>` will contain an updated image that launches specified virtues on boot.

### Option 2: Running on AWS

To run the assembler on AWS instead of local QEMU build, run

```
./asseble.py --docker-login "$DOCKER_LOGIN" --ssh-host <vm_host> --ssh-port <vm_port> virtue_container [virtue_container ... ]
```

This will first generated the cloud-init config file in `tmp/user-data` You can provide this file to AWS in order to configure an instance properly. The script will wait until the VM comes up on the provided ssh host and ports. Once it is up, the SSH stages will run, and finally the machine will be shut-down and the assebly process will be complete. After this point your AWS will contain a stopped instance that launches specified virtues on boot.
