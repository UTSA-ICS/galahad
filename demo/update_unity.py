import argparse
import logging
import os
import sys
import time

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(os.path.dirname(file_path)) + '/deploy'
sys.path.insert(0, base_excalibur_dir)
from deploy_galahad import EFS


# Configure the Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Node addresses
EXCALIBUR_HOSTNAME = 'excalibur.galahad.com'


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-k",
        "--path_to_key",
        type=str,
        required=True,
        help="The path to the public key used for the ec2 instances")
    parser.add_argument(
        "-n",
        "--stack_name",
        type=str,
        required=True,
        help="The name of the cloudformation stack for the virtue environment")
    parser.add_argument(
        "--image_size",
        default="8GB",
        choices=["4GB", "8GB", "16GB"],
        help="Indicate size of initial ubuntu image to be created (default: %(default)s)")

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()

    # Build a base ubuntu and unity image only - Assume that the stack is already deployed.
    efs = EFS(args.stack_name, args.path_to_key)

    start_ubuntu_img_time = time.time()

    efs.setup_ubuntu_img(args.image_size)

    logger.info('\n*** Time taken for {0} ubuntu img is [{1}] ***\n'.format(args.image_size,
                                                                            (time.time() - start_ubuntu_img_time) / 60))
    start_unity_time = time.time()

    efs.setup_unity_img(EXCALIBUR_HOSTNAME, args.image_size + '.img')

    logger.info('\n*** Time taken for {0} unity is [{1}] ***\n'.format(args.image_size,
                                                                       (time.time() - start_unity_time) / 60))
