# Temporary file

import os

from assembler.assembler import Assembler

env = 'aws'

if (env == 'aws'):
    build_opts = {'env': 'aws',
        'aws_image_id': 'ami-759bc50a',
        'aws_instance_type': 't2.micro',
        'aws_security_group': 'sg-00701349e8e18c5eb',
        'aws_subnet_id': 'subnet-05034ec1f99d009b9',
        'aws_disk_size': 8,
        'create_ami': False
    }
else:
    build_opts = {
        'env': 'xen',
        'base_img': os.environ['HOME'] + '/galahad/assembler/base_ubuntu.img',
        'output_dir': os.environ['HOME'] + '/galahad/assembler/output'
    }

assembler = Assembler()
assembler.construct_unity(build_opts)
