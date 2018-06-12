import time
import boto3

def create_aws_inst( ami, subnet, iam, name, key_name ):

    if( subnet == None ):
        print( 'Need subnet value -s' )
        exit()

    # Create AWS inst
    ec2 = boto3.resource('ec2', region_name='us-east-1')

    res = ec2.create_instances( ImageId=ami,
                                InstanceType='t2.micro',
                                KeyName=key_name,
                                MinCount=1,
                                MaxCount=1,
                                Monitoring={'Enabled': False},
                                SubnetId=subnet,
                                IamInstanceProfile={
                                    'Name': iam
                                },
                                TagSpecifications=[
                                    {
                                        'ResourceType': 'instance',
                                        'Tags': [{
                                            'Key': 'Project',
                                            'Value': 'Virtue'
                                        },
                                        {
                                            'Key': 'Name',
                                            'Value': name
                                        }]
                                    },
                                    {
                                        'ResourceType': 'volume',
                                        'Tags': [{
                                            'Key': 'Project',
                                            'Value': 'Virtue'
                                        }]
                                    }
                                ] )

    instance = res[0]

    print( instance.id )

    instance.wait_until_running()
    time.sleep(5)
    instance.reload()

    return instance.public_ip_address


def setup_aws_inst( ssh_inst, github_key, awskeys ):

    # Clone the galahad repository to the instance
    ssh_inst.scp_to( github_key, '~/id_rsa' )
    ssh_inst.ssh( 'mv ~/id_rsa ~/.ssh/id_rsa' )
    ssh_inst.ssh( 'rm -f ~/.ssh/id_rsa.pub' )
    ssh_inst.ssh( 'chmod 600 ~/.ssh/id_rsa' )

    ssh_inst.ssh( 'ssh -o StrictHostKeyChecking=no git@github.com', test=False )

    ssh_inst.ssh( 'rm -rf ~/galahad' )
    ssh_inst.ssh( 'git clone -b 110.refactor_excalibur git@github.com:starlab-io/galahad.git ~/galahad' )
    ssh_inst.ssh( 'rm -rf ~/galahad-config' )
    ssh_inst.ssh( 'git clone git@github.com:starlab-io/galahad-config.git ~/galahad-config' )

    # Very temporary
    #ssh_inst.ssh( 'rm -rf ~/galahad/tests' )
    #ssh_inst.scp_to( '/home/jeffrey/galahad/tests', '~/galahad' )

    # Install dependencies
    ssh_inst.ssh( '~/galahad/tests/setup_excalibur.sh' )

    # Install and configure slapd
    ssh_inst.ssh( '~/galahad/tests/setup_ldap.sh' )
    ssh_inst.ssh( 'echo \'export LDAPSEARCH="ldapsearch -H ldap://localhost -D cn=admin,dc=canvas,dc=virtue,dc=com -W -b dc=canvas,dc=virtue,dc=com"\' >> ~/.bashrc' )

    # Setup AWS client on AWS inst
    ssh_inst.ssh( 'sudo apt-get install -y awscli' )
    ssh_inst.ssh( 'mkdir .aws', test=False )
    ssh_inst.ssh( 'cp ~/galahad/tests/aws_config ~/.aws/config' )
    ssh_inst.scp_to( awskeys, '~/.aws/credentials' )

    # Start Excalibur
    ssh_inst.ssh( 'cd galahad/excalibur && ./start-screen.sh' )
