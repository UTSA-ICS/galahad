import time
import sys

sys.path.insert( 0, '/home/ubuntu/galahad/flask-authlib' )
from website.routes.aws import AWS

class Test_AWS:

    test_instance = {
        'image_id': 'ami-36a8754c',
        'inst_type': 't2.small',
        'subnet_id': 'subnet-00664ce7230870c66',
        'key_name': 'starlab-virtue-te',
        'tag_key': 'Project',
        'tag_value': 'Virtue',
        'sec_group': 'sg-0e125c01c684e7f6c',
        'inst_profile_name': '',
        'inst_profile_arn': ''
    }



    def test_that_creating_an_instance_succeeds(self):

        aws = AWS()

        instance = aws.instance_create(**self.test_instance)

        assert instance.state['Name'] == 'running'
        assert instance.image_id == self.test_instance['image_id']
        assert instance.key_name == self.test_instance['key_name']
        assert instance.subnet_id == self.test_instance['subnet_id']
        assert instance.instance_type == self.test_instance['inst_type']

        aws.instance_stop(instance.id)

        aws.instance_destroy(instance.id)



    def test_that_stopping_an_instance_succeeds(self):

        aws = AWS()

        instance = aws.instance_create(**self.test_instance)

        response = aws.instance_stop(instance.id)

        assert response['StoppingInstances'][0]['InstanceId'] == instance.id

        aws.instance_destroy(instance.id)



    def test_that_starting_an_instance_succeeds(self):

        aws = AWS()

        instance = aws.instance_create(**self.test_instance)

        response = aws.instance_stop(instance.id)

        time.sleep(60)

        response = aws.instance_launch(instance.id)

        assert response['StartingInstances'][0]['InstanceId'] == instance.id

        aws.instance_stop(instance.id)

        aws.instance_destroy(instance.id)



    def test_that_destroying_an_instance_succeeds(self):

        aws = AWS()

        instance = aws.instance_create(**self.test_instance)

        aws.instance_stop(instance.id)

        response = aws.instance_destroy(instance.id)

        assert response['TerminatingInstances'][0]['InstanceId'] == instance.id
