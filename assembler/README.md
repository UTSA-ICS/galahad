
How to spin up VM for a given ROLE

## Prerequisites

- Linux instance with ssh and python3

- AWS Constructor dependency: pyyaml
- Xen Constructor requires sudo permissions to mount and edit the image

- Assembler dependencies:
	- You have access to aws cli to get docker login password
	- Follow this URL to configure aws cli interface: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

## Get Ubuntu 16.04 VM Image

- Two options:
	- AWS: Find recent Ubuntu 16.04 AMI
	- Xen: Create a base Ubuntu 16.04 PVM image with the following command and take note of where disk.img is saved, usually `<dir>/domains/Unity/disk.img`:
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

Unity construction is done with `Assembler.construct_unity(build_options, clean=False)`.

`build_options` is a dict containing environment-specific construction arguments. Options are described later in the README.

`clean` is a boolean determining whether the work directory is deleted after construction is done.

While creating the Assembler object, `__init__` takes four optional arguments:
```
es_node # The Elastic Search Node for storing logs. Defaults to 'https://aggregator.galahad.com:9200'
syslog_server # The IP address for the Syslog Server. Defaults to '172.30.128.131'
rethinkdb_host # The IP address for RethinkDB. Defaults to 'rethinkdb.galahad.com'
work_dir # The work directory
```

### Option 1: Constructing a Xen PVM disk image

To run the constructor on a PVM image file, the running application will require root privelages so it can mount and modify the image. `build_options` must have 'env' set to 'xen' and include these keys:
```
base_img
output_dir
```

This will copy the `base_img` to `self.work_dir/disk.img` and mount it at `/tmp/img_mount`. Then, modified code from the ssh stages will run to write files to the image in-place. This process does not require a hypervisor to be installed, nor does it require access to AWS. The new modified image will be copied to `output_dir/disk.img` and can be launched as a Xen or Xenblanket PVM.

Here is an example of how to create a unity from a base Ubuntu 16.04 image:
```
import os

from assembler.assembler import Assembler

build_opts = {
    'env': 'xen',
    'base_img': os.environ['HOME'] + '/galahad/assembler/base_ubuntu.img',
    'output_dir': os.environ['HOME'] + '/galahad/assembler/output',
}

assembler = Assembler(work_dir='/tmp/work_dir')
assembler.construct_unity(build_opts)
```

### Option 2: Constructing on AWS

To run the constructor with AWS, `build_options` must have 'env' set to 'aws' and include these keys:
```
aws_image_id # The base 16.04 image mentioned above
aws_instance_type
aws_security_group
aws_subnet_id
aws_disk_size # Disk size in gigabytes
create_ami
```

This will first generate the cloud-init config file in `keys-unity/user-data` The script will launch a VM based on `aws_image_id` in `build_options` and wait until it finishes launching. Once it is up, the SSH stages will run, and finally the machine will be shut-down and the construction process will be complete. After this point, your AWS will contain a stopped Unity instance with the type, security group, subnet ID, and disk size (In gigabytes) specified in `build_options`.

An AMI of the Unity will be created if `create_ami` is set to True.

Here is an example of how to create a unity in the starlab-virtue AWS account:
```
from assembler.assembler import Assembler

build_opts = {
    'env': 'aws',
    'aws_image_id': 'ami-759bc50a',
    'aws_instance_type': 't2.micro',
    'aws_security_group': 'sg-00701349e8e18c5eb',
    'aws_subnet_id': 'subnet-05034ec1f99d009b9',
    'aws_disk_size': 8,
    'create_ami': True
}

assembler = Assembler()
assembler.construct_unity(build_opts)
```

Office applications are very large and require a larger disk size and more RAM:
```
build_opts = {
    'env': 'aws',
    'aws_image_id': 'ami-759bc50a',
    'aws_instance_type': 't2.xlarge',
    'aws_security_group': 'sg-00701349e8e18c5eb',
    'aws_subnet_id': 'subnet-05034ec1f99d009b9',
    'aws_disk_size': 12,
    'create_ami': True
}
```

## Get docker login command

Once you have aws cli configured, run `./get_docker_login_command.sh` and follow the on-screen prompts for the MFA token. If you don't have MFA enabled, press Enter without putting the token into the prompt. Once complete, the last output of that script will provide a `docker login ...` command. Store it in a bash variable or somewhere accessible from your script.

## Assemble a role

Currently, the only way to assemble a role is to launch a Unity VM and call `Assembler.assemble_running_vm(containers, docker_login, key_path, ssh_host, ssh_port='22')`.

`containers` is a list of the docker containers to setup.

`docker_login` is the string printed by `get_docker_login_command.sh`.

`key_path` is the path to the private key to ssh into the Unity with.

`ssh_host` is the IP address of the running Unity.

`ssh_port` is the port to use while ssh'ing into the Unity.

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
