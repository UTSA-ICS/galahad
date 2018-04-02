import boto3
import json

class AWS:
    aws_image_id = 'ami-36a8754c' # see https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#LaunchInstanceWizard:
    aws_instance_type = 't2.small'
    aws_subnet_id='subnet-0b97b651'
    aws_key_name = 'valor-dev'
    aws_tag_key = 'Project'
    aws_tag_value = 'Virtue'
    aws_security_group = 'sg-3c8ccf4f'
    aws_vpc = 'vpc-5fcac526'
    aws_instance_profile_name = 'Virtue-Tester'
    aws_instance_profile_arn = 'arn:aws:iam::602130734730:instance-profile/Virtue-Tester'

    def __init__(self):
        self.id = ''
        self.username = ''
        self.roleId = ''
        self.applicationIds = []
        self.resourceIds = []
        self.transducerIds = []
        self.state = ''
        self.ipAddress = ''

    def get_json(self):
        return json.dumps({'id': self.id,
            'username': self.username,
            'roleId': self.roleId,
            'applicationIds': self.applicationIds,
            'resourceIds': self.resourceIds,
            'transducerIds': self.transducerIds,
            'state': self.state,
            'ipAddress': self.ipAddress})

    def __repr__(self):
        return self.get_json()

    def __str__(self):
        return self.get_json()

    def instance_create(self):
        """Create a new AWS instance - a virtue
        This will create a AWS instance based on a
        given AMI ID.
        Ref: http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances
        """
        ec2 = boto3.resource('ec2',region_name='us-east-1')
    
        res = ec2.create_instances(ImageId=self.aws_image_id,
            InstanceType=self.aws_instance_type,
            KeyName=self.aws_key_name,
            MinCount=1,
            MaxCount=1,
            Monitoring={'Enabled':False},
            SecurityGroupIds=[self.aws_security_group],
            SubnetId=self.aws_subnet_id,
            IamInstanceProfile={
                                    'Name':self.aws_instance_profile_name
                                },
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Project',
                            'Value': 'Virtue'
                        },
                    ]
                },
                {
                    'ResourceType': 'volume',
                    'Tags': [
                        {
                            'Key': 'Project',
                            'Value': 'Virtue'
                        },
                    ]
                },
            ]
        )

        instance = res[0]
        self.id = instance.id

        instance.wait_until_running()

        self.ipAddress = instance.private_ip_address
        self.state = instance.state['Name']

        return instance


    def instance_launch(self, virtueId):
        """Start the specified AWS instance
        This will use the virtue ID specifed as the AWS instance ID and start the
        instance.
        Ref: http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.start_instances
        """
        client = boto3.client('ec2')

        response = client.start_instances(
            InstanceIds=[
                virtueId,
            ]
        )
        return response


    def instance_stop(self, virtueId):
        """Stop the specified AWS instance
        Stop the specified AWS instance
        Ref: http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.stop_instances
        """
        client = boto3.client('ec2', 'us-east-1')

        # Specify the InstanceId of the spcific instance.
        response = client.stop_instances(
            InstanceIds=[
                virtueId,
            ]
        )
        return response


    def instance_destroy(self, virtueId):
        """Terminate the AWS instance
        Terminate the specified AWS instance.
        Ref: http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.terminate_instances
        """
        client = boto3.client('ec2')

        # Specify the InstanceId of the spcific instance.
        response = client.terminate_instances(
            InstanceIds=[
                virtueId,
            ]
        )
        return response
