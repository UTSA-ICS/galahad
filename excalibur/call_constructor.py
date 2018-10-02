# Temporary file

import os

from assembler.assembler import Assembler

env = 'aws'

if (env == 'aws'):
    build_opts = {'env': 'aws',
        'docker_login': '$DOCKER_LOGIN',
        'aws_image_id': 'ami-759bc50a',
        'aws_instance_type': 't2.medium',
        'aws_security_group': 'sg-01a26770c93daf2cc',
        'aws_subnet_id': 'subnet-0b9daec6ff026a935',
        'aws_disk_size': 8,
        'create_ami': False,
        'containers': ['terminal', 'firefox']
    }

else:
    build_opts = {
        'env': 'xen',
        'base_img': os.environ['HOME'] + '/galahad/assembler/base_ubuntu.img',
        'output_dir': os.environ['HOME'] + '/galahad/assembler/output'
    }

assembler = Assembler()
assembler.construct_unity(build_opts)
