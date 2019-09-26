# Copyright (c) 2019 by Star Lab Corp.

from boto.utils import get_instance_metadata
import boto3
import botocore
import copy
import json
import time


class AWS:

    aws_state_to_virtue_state = {
        'pending': 'CREATING',
        'running': 'RUNNING',
        'shutting-down': 'DELETING',
        'terminated': 'STOPPED',
        'stopping': 'STOPPING',
        'stopped': 'STOPPED'
    }

    def __init__(self):
        self.ec2 = boto3.resource('ec2')

        self.id = ''
        self.username = ''
        self.roleId = ''
        self.applicationIds = []
        self.resourceIds = []
        self.transducerIds = []
        self.state = ''
        self.ipAddress = ''

    def get_json(self):
        return json.dumps({
            'id': self.id,
            'username': self.username,
            'roleId': self.roleId,
            'applicationIds': self.applicationIds,
            'resourceIds': self.resourceIds,
            'transducerIds': self.transducerIds,
            'state': self.state,
            'ipAddress': self.ipAddress
        })

    def __repr__(self):
        return self.get_json()

    def __str__(self):
        return self.get_json()

    @staticmethod
    def get_instance_info():
        return get_instance_metadata(timeout=0.5, num_retries=2)

    def get_private_ip(self):
        info = self.get_instance_info()

        instance = self.ec2.Instance(info['instance-id'])
        return instance.private_ip_address

    def get_subnet_id(self):
        info = self.get_instance_info()

        instance = self.ec2.Instance(info['instance-id'])
        return instance.subnet.id

    def get_sec_group(self):
        info = self.get_instance_info()

        sg_id = self.ec2.Instance(
            info['instance-id']).security_groups[0]['GroupId']

        return self.ec2.SecurityGroup(sg_id)

    def populate_virtue_dict(self, virtue):
        instance = self.ec2.Instance(virtue['awsInstanceId'])

        virtue = copy.deepcopy(virtue)
        try:
            virtue['state'] = \
                self.aws_state_to_virtue_state[instance.state['Name']]
            virtue['ipAddress'] = str(instance.private_ip_address)
        except (botocore.exceptions.ClientError, AttributeError):
            virtue['state'] = 'NULL'
            virtue['ipAddress'] = 'NULL'

        return virtue

    @staticmethod
    def get_id_from_ip(ip_address):
        ec2 = boto3.client('ec2')

        res = ec2.describe_instances(Filters=[{
            'Name': 'ip-address',
            'Values': [ip_address]
        }])
        if (len(res['Reservations'][0]['Instances']) == 0):
            return None

        return res['Reservations'][0]['Instances'][0]['InstanceId']


    def instance_create(self, image_id,
                        inst_type,
                        subnet_id,
                        key_name,
                        tag_key,
                        tag_value,
                        sec_group,
                        inst_profile_name,
                        inst_profile_arn,
                        user_data='',
                        block=True):
        """Create a new AWS instance - a virtue
        This will create a AWS instance based on a
        given AMI ID.
        Ref: http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances
        """

        ec2 = boto3.resource('ec2', region_name='us-east-1')

        res = ec2.create_instances(
            ImageId=image_id,
            InstanceType=inst_type,
            KeyName=key_name,
            MinCount=1,
            MaxCount=1,
            Monitoring={'Enabled': False},
            SecurityGroupIds=[sec_group],
            SubnetId=subnet_id,
            BlockDeviceMappings=[{
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'DeleteOnTermination': True,
                 }
            }],
            IamInstanceProfile={
                'Name': inst_profile_name,
            },
            UserData=user_data,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': tag_key,
                            'Value': tag_value
                        },
                    ]
                },
                {
                    'ResourceType': 'volume',
                    'Tags': [
                        {
                            'Key': tag_key,
                            'Value': tag_value
                        },
                    ]
                },
            ])

        instance = res[0]
        self.id = instance.id

        time.sleep(0.5)
        if (block):
            instance.wait_until_running()

        instance.reload()

        self.ipAddress = instance.private_ip_address
        self.state = instance.state['Name']

        return instance

    def instance_launch(self, instId, block=True):
        """Start the specified AWS instance
        This will use the instance ID specifed as the AWS instance ID and start the
        instance.
        Ref: http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.start_instances
        """

        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(instId)

        instance.start()

        time.sleep(0.5)
        if (block):
            instance.wait_until_running()

        instance.reload()

        return instance

    def instance_stop(self, instId, block=True):
        """Stop the specified AWS instance
        Stop the specified AWS instance
        Ref: http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.stop_instances
        """

        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(instId)

        instance.stop()

        time.sleep(0.5)
        if (block):
            instance.wait_until_stopped()

        instance.reload()

        return instance

    def instance_destroy(self, instId, block=True):
        """Terminate the AWS instance
        Terminate the specified AWS instance.
        Ref: http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.terminate_instances
        """

        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(instId)

        instance.terminate()

        time.sleep(0.5)
        if (block):
            instance.wait_until_terminated()

        instance.reload()

        return instance
