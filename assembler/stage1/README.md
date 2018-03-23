# Virtue Assembler Stage 1

## Constructive stage

This assembler stage adds data to the VM. Nothing is cleaned

### Call ./run.sh path_to_qemu_image

The script does the following

- Generates key-pair on host
-  Using cloud-init
    - Create user on vm
    - Write user authorized key
	- Run remote_script
	    - checks out docker container
		- git clones starlab's docker-virtue
		- runs virtue start with appropriate docker image
