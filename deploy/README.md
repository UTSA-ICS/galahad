# Galahad Deployment

The Galahad deployment is driven by the `deploy.py` script, which will setup and configure a complete galahad production environment. This environment includes the following componenets:
- a VPC cloudformation stack
     
   This stack contains a new VPC, subnet, IGW, routing table and deployment node. The galahad stack will deploy resources that uses this VPC.
   - deployment node
   
     This is the node from where the galahad stack will be deployed. The purpose of this node is to act as the entry host for network access to the VPC.
     All galahad nodes, for the final eval, will only have private IPs are not have public access from outside of the VPC.
     `*** For development purposes only, the galahad nodes will have public IPs assigned for developers to be able to access them,
     but they will not be used by galahad for any sort of network communication ***`
     
- a galahad cloudformation stack

  This is the stack that contains the rest of the galahad resources - ec2 instances, dns records, EFS filesystem.
  Currently there are the following nodes deployed as part of the galahad infrastructure:
      
     - excalibur node
     - rethinkdb node
     - aggregator node
     - valor-router node
     - Active Directory node
     - XenPVMBuilder node
     - sample canvas node
     - deployment node

## deploy.py
`deploy.py` script which will start the deployment process and perform the following tasks:
- create a stack in AWS using the cloudformation file `deploy/setup/galahad-vpc-stack.yaml` which will create a VPC
  and associated network resources and a deployment node with a public IP.
- The script will then SSH into the deployment node and install required packages and setup appropriate keys.
- After setup of the deployment node is complete the `deploy-galahad.py` script will be automaticaly run with the appropriate options.

Usage:
```
usage: deploy.py [-h] -k PATH_TO_KEY -g GITHUB_REPO_KEY -n STACK_NAME -s
                 STACK_SUFFIX [-b BRANCH_NAME] [--aws_config AWS_CONFIG]
                 --aws_keys AWS_KEYS [--setup] [--setup_stack] [--list_stacks]
                 [--delete_stack] --default_user_key DEFAULT_USER_KEY

optional arguments:
  -h, --help            show this help message and exit
  -k PATH_TO_KEY, --path_to_key PATH_TO_KEY
                        The path to the public key used for the ec2 instances
  -g GITHUB_REPO_KEY, --github_repo_key GITHUB_REPO_KEY
                        The path to the key to be able to access github repos
  -n STACK_NAME, --stack_name STACK_NAME
                        The name of the cloudformation stack for the virtue
                        environment
  -s STACK_SUFFIX, --stack_suffix STACK_SUFFIX
                        The suffix used by the cloudformation stack to append
                        to resource names
  -b BRANCH_NAME, --branch_name BRANCH_NAME
                        The branch name to be used for galahad repo
  --aws_config AWS_CONFIG
                        AWS config to be used to communicate with AWS
  --aws_keys AWS_KEYS   AWS keys to be used for AWS communication
  --setup               setup the galahad/virtue test environment
  --setup_stack         setup the galahad/virtue stack only
  --list_stacks         List all the available stacks
  --delete_stack        delete the specified stack
  --default_user_key DEFAULT_USER_KEY
                        Default private key for users to get (Will be replaced
                        with generated keys)
```
Example:
```
python3 deploy.py 
        -k ../../starlab-virtue-te.pem                 - private key corresponding to public key provisioned in AWS
        -g ../../github_key.private                    - github access key required to access the repo
        --aws_config "setup/aws_config"                - aws setup config
        --aws_keys ~/.aws/credentials                  - aws credentials – access key and access key ID
        --default_user_key ../../starlab-virtue-te.pem - can be same as private key corresponding to public key provisioned in AWS
        -b JHUAPL_Deployment_rework                    - branch in github which will be used as the code base
        -n STARLAB-JHUAPL                              - name of new stack going to be deployed
        -s ST1                                         - tag name for aws resources to have as a identifier in their name
        --setup                                        - directive to setup
 ```

## deploy-galahad.py
The `deploy-galahad.py` script will perform the following tasks:
- create a stack in AWS using the cloudformation file `deploy/setup.galahad-stack.yaml` which will create the ec2 instances to host all the galahad infrastructure components.
- The script will then proceed to setup and configure the software components and start all the required galahad processes.
- After completing the installation, the script will call the constructor to create the base unity image (default 4GB image) which will be used for all the roles and appropriate virtues. A `--image_size` option can be specified to change this default size.
- This script can be run again with `--build_image_only` option specified to build additional base ubuntu and unity images for a different `--image_size`. This option assumes that the stack has already been setup and only works on a completed galahad deployment.

Usage:
```
usage: deploy_galahad.py [-h] -k PATH_TO_KEY -g GITHUB_REPO_KEY -n STACK_NAME
                         -s STACK_SUFFIX [--import_stack IMPORT_STACK]
                         [-b BRANCH_NAME] [--aws_config AWS_CONFIG] --aws_keys
                         AWS_KEYS [--setup] [--setup_stack] [--list_stacks]
                         [--delete_stack] [--image_size {4GB,8GB,16GB}]
                         [--build_image_only] --default_user_key
                         DEFAULT_USER_KEY

optional arguments:
  -h, --help            show this help message and exit
  -k PATH_TO_KEY, --path_to_key PATH_TO_KEY
                        The path to the public key used for the ec2 instances
  -g GITHUB_REPO_KEY, --github_repo_key GITHUB_REPO_KEY
                        The path to the key to be able to access github repos
  -n STACK_NAME, --stack_name STACK_NAME
                        The name of the cloudformation stack for the virtue
                        environment
  -s STACK_SUFFIX, --stack_suffix STACK_SUFFIX
                        The suffix used by the cloudformation stack to append
                        to resource names
  --import_stack IMPORT_STACK
                        The Name of the Stack containing resources that will
                        be imported for use in this stack
  -b BRANCH_NAME, --branch_name BRANCH_NAME
                        The branch name to be used for excalibur repo
  --aws_config AWS_CONFIG
                        AWS config to be used to communicate with AWS
  --aws_keys AWS_KEYS   AWS keys to be used for AWS communication
  --setup               setup the galahad/virtue test environment
  --setup_stack         setup the galahad/virtue stack only
  --list_stacks         List all the available stacks
  --delete_stack        delete the specified stack
  --image_size {4GB,8GB,16GB}
                        Indicate size of initial ubuntu image to be created
                        (default: 4GB)
  --build_image_only    Build the ubuntu and unity image only - Assume an
                        existing stack
  --default_user_key DEFAULT_USER_KEY
                        Default private key for users to get (Will be replaced
                        with generated keys)
```
Example:
```
python3 deploy-galahad.py 
        -k ../../starlab-virtue-te.pem                 -  private key corresponding to public key provisioned in AWS
        -g ../../github_key.private                    -  github access key required to access the repo
        --aws_config "setup/aws_config"                - aws setup config
        --aws_keys ~/.aws/credentials                  - aws credentials – access key and access key ID
        --default_user_key ../../starlab-virtue-te.pem - can be same as private key corresponding to public key provisioned in AWS
        -b JHUAPL_Deployment_rework                    - branch in github which will be used as the code base
        -n STARLAB-JHUAPL                              - name of new stack going to be deployed
        -s ST1                                         - tag name for aws resources to have as a identifier in their name
        --import_stack STARLAB-JHUAPL-VPC              - name of CF stack that was deployed to AWS that has VPC and subnet resources
        --setup                                        - directive to setup
 ```
