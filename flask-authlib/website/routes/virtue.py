from flask import request, Response

from flask import Blueprint, url_for
from flask import abort, redirect, render_template
from ..auth import require_login, current_user
from ..models import OAuth2Client, User
from ..forms.client import (
    Client2Form, OAuth2ClientWrapper
)
import json
import boto3.ec2
import time
from ..vars import LDAP_DATABASE_URI, AD_DATABASE_URI, LDAP_PROTOCOL_VERSION
from ..ldaplookup import LDAP

bp = Blueprint('virtue', __name__)

import boto3
#import logging
#boto3.set_stream_logger('botocore.credentials', logging.DEBUG)
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

aws_state_to_virtue_state = {
        'pending': 'CREATING',
        'running': 'RUNNING',
        'shutting-down': 'DELETING',
        'terminated': 'STOPPED',
        'stopping': 'STOPPING',
        'stopped': 'STOPPED'
}

## TRANSFER TO NEW MODELS/VIRTUE FILE FOR ORGANIZATION
class Virtue:
        id = ''
        username = ''
        roleId = ''
        applicationIds = []
        resourceIds = []
        transducerIds = []
        state = ''
        ipAddress = ''

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

@bp.route('/user/application/get', methods=['GET'])
@require_login
def application_get():
    print request.args['appId']
    user = User.query.filter_by(email=current_user.email).first()
    print current_user.conn
    print user.conn
    return 'The Application with the given ID. Type: Application.'

@bp.route('/user/role/get', methods=['GET'])
@require_login
def role_get():
    print request.args['roleId']
    print('WAT    : request = %s' % request)
    #return 'Information about the indicated Role. Type: Role'

    js = json.dumps({'status':'success'})
    resp = Response(js, status=200, mimetype='application/json')
    #resp = make_response()
    resp.headers['status'] = 'success'
    print('WAT    : response = %s' % resp)
    return resp

# TODO
# user login (username, password)
# user logout

@bp.route('/user/user/rolelist', methods=['GET'])
@require_login
def user_role_list():
    return 'A set of Roles available to the given User. Type: set of Role'

@bp.route('/user/user/virtuelist', methods=['GET'])
@require_login
def user_virtue_list():
    return 'A set of Virtues for the given User. Type: set of Virtue.'

@bp.route('/user/virtue/get', methods=['GET'])
@require_login
def virtue_get():
    print request.args['virtId']
    return 'Information about the indicated Virtue. Type: Virtue.'

@bp.route('/user/virtue/create', methods=['GET'])
@require_login
def virtue_create():
    if 'roleId' not in request.args:
        return 'Missing argument: roleId'

    print request.args['roleId']
    virtue = Virtue()
    virtue.roleId = request.args['roleId']

    #print 'AWS ACCESS KEY' + boto3.Session().get_credentials().access_key
    #print 'AWS SECRET KEY' + boto3.Session().get_credentials().secret_key
    ec2 = boto3.resource('ec2',region_name='us-east-1')
    
    res = ec2.create_instances(ImageId=aws_image_id,
                             InstanceType=aws_instance_type,
                             KeyName=aws_key_name,
                             MinCount=1,
                             MaxCount=1,
                             Monitoring={'Enabled':False},
                             SecurityGroupIds=[aws_security_group],
                             SubnetId=aws_subnet_id,
                             IamInstanceProfile={
                                                 'Name':aws_instance_profile_name
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
    virtue.id = instance.id

    instance.wait_until_running()

    virtue.ipAddress = instance.ip_address
    virtue.state = aws_state_to_virtue_state.get(instance.state,
            'UNKNOWN')

    return virtue.get_json()

@bp.route('/user/virtue/launch', methods=['GET'])
@require_login
def virtue_launch():
    print request.args['virtId']
    return 'Information about the launched Virtue. Type: Virtue'

@bp.route('/user/virtue/stop', methods=['GET'])
@require_login
def virtue_stop():
    print request.args['virtId']
    return 'Information about the stopped Virtue. Type: Virtue'

@bp.route('/user/virtue/destroy', methods=['GET'])
@require_login
def virtue_destroy():
    print request.args['virtId']
    return '0'

@bp.route('/user/virtue/applicationlaunch', methods=['GET'])
@require_login
def virtue_application_launch():
    print request.args['virtId']
    print request.args['appId']
    return 'Information about the launched Application. Format is implementation-specific. Type: object'

@bp.route('/user/virtue/applicationstop', methods=['GET'])
@require_login
def virtue_application_stop():
    print request.args['virtId']
    print request.args['appId']
    return '0'

@bp.route('/test', methods=['GET'])
@require_login
def virtue_test():
    test = ''
    for arg in request.args:
        test += arg + ':' + request.args[arg] + '&'
    return test

@bp.route('/connect/excalibur', methods=['GET'])
@require_login
def virtue_connect():
    test = ''
    for arg in request.args:
        test += arg + ':' + request.args[arg] + '&'
    return test
