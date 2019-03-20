# Copyright (c) 2019 by Star Lab Corp.

import os
import sys
import boto3

def delete_orphaned_snapshots():
   # Get the Account number which is the ownerId
   sts_client = boto3.client('sts')
   owner_id = sts_client.get_caller_identity()['Account']

   ec2 = boto3.client('ec2')

    
   # Get All private images - AMIs
   private_images = ec2.describe_images(Owners=[owner_id])

   # Get All private snapshots with description specifying image creation
   private_snapshots = ec2.describe_snapshots(
                           OwnerIds=[owner_id], 
                           Filters=[{ 'Name':'description', 'Values': ['Created by CreateImage*ami-*'] }]
                       )

   # Check orphaned snapshots
   for snapshot in private_snapshots['Snapshots']:
       ami_id = snapshot['Description'].split(' ')[4] 
       if ami_id not in str(private_images):
           # The AMI specified in this snapshot does not exist
           # This is a orphaned snapshot so delete it
           print('Deleting orphaned snapshot -> [{}]'.format(snapshot['SnapshotId']))
           ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'])

delete_orphaned_snapshots()
