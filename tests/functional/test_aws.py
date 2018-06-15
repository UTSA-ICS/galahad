import time
import json
import sys
import os
import ast

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(os.path.dirname(file_path)) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)
from website.aws import AWS


# Name of the file storing the instance information
aws_instance_info = 'aws_instance_info.json'


class Test_AWS:


    def setup_class(self):
        self.instance_list = []

        file = open(aws_instance_info, "r")
        test_string = json.dumps(file.read())
        self.test_instance = ast.literal_eval(json.loads(test_string))



    def teardown_class(self):

        aws = AWS()

        abandoned_instances = 0
        for i in self.instance_list:
            i.reload()

            if(i.state['Name'] != 'terminated' and i.state['Name'] != 'shutting-down'):
                abandoned_instances = abandoned_instances + 1
                aws.instance_destroy(i.id)

        assert abandoned_instances == 0



    def create_test_instance(self, aws):
        instance = aws.instance_create(**self.test_instance)
        self.instance_list.append(instance)
        return instance



    def test_that_creating_an_instance_succeeds(self):

        aws = AWS()

        instance = self.create_test_instance(aws)

        assert instance.state['Name'] == 'running'
        assert instance.image_id == self.test_instance['image_id']
        assert instance.key_name == self.test_instance['key_name']
        assert instance.subnet_id == self.test_instance['subnet_id']
        assert instance.instance_type == self.test_instance['inst_type']

        aws.instance_destroy(instance.id, block=False)



    def test_that_stopping_an_instance_succeeds(self):

        aws = AWS()

        instance = self.create_test_instance(aws)

        instance2 = aws.instance_stop(instance.id)

        assert instance2.id == instance.id
        assert instance2.state['Name'] == 'stopped'

        aws.instance_launch(instance.id)

        instance3 = aws.instance_stop(instance.id, block=False)

        assert instance3.id == instance.id
        assert instance3.state['Name'] == 'stopping'

        aws.instance_destroy(instance.id, block=False)



    def test_that_starting_an_instance_succeeds(self):

        aws = AWS()

        instance = self.create_test_instance(aws)

        aws.instance_stop(instance.id)

        instance2 = aws.instance_launch(instance.id)

        assert instance2.id == instance.id
        assert instance2.state['Name'] == 'running'

        aws.instance_stop(instance.id)

        instance3 = aws.instance_launch(instance.id, block=False)

        assert instance3.id == instance.id
        assert instance3.state['Name'] == 'pending'

        instance3.wait_until_running()

        aws.instance_destroy(instance.id, block=False)



    def test_that_destroying_an_instance_succeeds(self):

        aws = AWS()

        instance = self.create_test_instance(aws)

        instance2 = aws.instance_destroy(instance.id)

        assert instance2.id == instance.id
        assert instance2.state['Name'] == 'terminated'

        instance3 = self.create_test_instance(aws)

        instance4 = aws.instance_destroy(instance3.id, block=False)

        assert instance4.id == instance3.id
        assert instance4.state['Name'] == 'shutting-down'
