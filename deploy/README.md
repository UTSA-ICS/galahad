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
python3 deploy.py 
        -k ../../starlab-virtue-te.pem                 -  private key corresponding to public key provisioned in AWS
        -g ../../github_key.private                    -  github access key required to access the repo
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
- After completing the installation, the script will call the constructor to create the base unity image (a 4GB and 8GB image) which will be used for all the roles and appropriate virtues.

Usage:
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
        --import_stack                                 - name of CF stack that was deployed to AWS that has VPC and subnet resources
        --setup                                        - directive to setup
 ```
