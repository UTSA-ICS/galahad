
How to spin up VM for a given ROLE

## Prerequisites

- Linux instance with ssh and python3

- Constructor dependencies:
	- sudo permissions to mount and edit the image

- Assembler dependencies:
	- You have access to aws cli to get docker login password
	- Follow this URL to configure aws cli interface: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

## Get Ubuntu 16.04 VM Image

- Create a base Ubuntu 16.04 PVM image with the following command and take note of where disk.img is saved, usually `<dir>/domains/Unity/disk.img`:
`sudo xen-create-image \
    --hostname=Unity \
    --dhcp \
    --dir=<dir> \
    --dist=xenial \
    --vcpus=1 \
    --memory=1024MB \
    --genpass=0 \
    --size=<size>GB`

## Construct the Unity

Unity construction is done with `Assembler.construct_unity(base_img, output_path, ssh_key=None, clean=False)`.

`base_img` is a string path to the base image, usually Ubuntu, to construct.

`output_path` is the path where the constructor will leave the finished Unity.

`ssh_key` is the path to a public key for the Unity to accept SSH sessions. If left at `None`, a key pair will be generated.

`clean` is a boolean determining whether the work directory is deleted after construction is done.

While creating the Assembler object, `__init__` takes four optional arguments:
```
es_node # The Elastic Search Node for storing logs. Defaults to 'https://aggregator.galahad.com:9200'
syslog_server # The IP address for the Syslog Server. Defaults to '192.168.4.10'
rethinkdb_host # The IP address for RethinkDB. Defaults to 'rethinkdb.galahad.com'
work_dir # The work directory
```

To run the constructor on a PVM image file, the running application will require root privelages so it can mount and modify the image.

This will copy the `base_img` to `self.work_dir/disk.img` and mount it at `/tmp/img_mount`. Then, modified code from the ssh stages will run to write files to the image in-place. This process does not require a hypervisor to be installed, nor does it require access to AWS. The new modified image will be copied to `output_dir/disk.img` and can be launched as a Xen or Xenblanket PVM.

Here is an example of how to create a unity from a base Ubuntu 16.04 image:
```
import os

from assembler.assembler import Assembler

assembler = Assembler(work_dir='/tmp/work_dir')
assembler.construct_unity(os.environ['HOME'] + '/galahad/assembler/base_ubuntu.img',
                          os.environ['HOME'] + '/galahad/assembler/output')
```

## Get docker login command

Once you have aws cli configured, run `./get_docker_login_command.sh` and follow the on-screen prompts for the MFA token. If you don't have MFA enabled, press Enter without putting the token into the prompt. Once complete, the last output of that script will provide a `docker login ...` command. Store it in a bash variable or somewhere accessible from your script.

## Assemble a role

Currently, the only way to assemble a role is to launch a Unity VM and call `Assembler.assemble_running_vm(containers, docker_login, key_path, ssh_host)`.

`containers` is a list of the docker containers to setup.

`docker_login` is the string printed by `get_docker_login_command.sh`.

`key_path` is the path to the private key to ssh into the Unity with.

`ssh_host` is the IP address of the running Unity.

This will ssh into the Unity with the key in `key_path` and install all of the specified docker containers.

Here is an example:
```
from assembler.assembler import Assembler

docker_login = 'docker login very_long_string'

assembler = Assembler(work_dir='/path/to/work/dir')
assembler.assemble_running_vm(['firefox', 'xterm'],
                              docker_login,
                              '/path/to/key',
                              '10.30.30.118')
```
