import time
import json
import sys
import os
import ast

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(os.path.dirname(file_path)) + '/flask-authlib'
sys.path.insert(0, base_excalibur_dir)
from website.routes.aws import AWS

# Name of the file storing the instance information
aws_instance_info = 'aws_instance_info.json'

class Test_AWS:

    def __init__(self):
        file = open(aws_instance_info, "r")
        test_string = json.dumps(file.read())
        self.test_instance = ast.literal_eval(json.loads(test_string))


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

        instance2 = aws.instance_stop(instance.id)

        assert instance2.id == instance.id
        assert instance2.state['Name'] == 'stopped'

        aws.instance_launch(instance.id)

        instance3 = aws.instance_stop(instance.id, block=False)

        assert instance3.id == instance.id
        assert instance3.state['Name'] == 'stopping'

        aws.instance_destroy(instance.id)



    def test_that_starting_an_instance_succeeds(self):

        aws = AWS()

        instance = aws.instance_create(**self.test_instance)

        aws.instance_stop(instance.id)

        instance2 = aws.instance_launch(instance.id)

        assert instance2.id == instance.id
        assert instance2.state['Name'] == 'running'

        aws.instance_stop(instance.id)

        instance3 = aws.instance_launch(instance.id, block=False)

        assert instance3.id == instance.id
        assert instance3.state['Name'] == 'pending'

        aws.instance_stop(instance.id)

        aws.instance_destroy(instance.id)



    def test_that_destroying_an_instance_succeeds(self):

        aws = AWS()

        instance = aws.instance_create(**self.test_instance)

        aws.instance_stop(instance.id)

        instance2 = aws.instance_destroy(instance.id)

        assert instance2.id == instance.id
        assert instance2.state['Name'] == 'terminated'

        instance3 = aws.instance_create(**self.test_instance)

        aws.instance_stop(instance3.id)

        instance4 = aws.instance_destroy(instance3.id, block=False)

        assert instance4.id == instance3.id
        assert instance4.state['Name'] == 'shutting-down'
