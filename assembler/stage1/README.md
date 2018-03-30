# Virtue Assembler Stage 1

## Constructive stage

This assembler stage adds data to the VM. Nothing is cleaned

### Call ./run.sh image_file container_name "docker login from aws cli"

The script does the following

- Generates key-pair on host
-  Using cloud-init
    - Create user on vm
    - Write user authorized key
	- Run remote_script
	    - checks out docker container
		- runs the container with appropriate apparmor/seccomp stuff
