""" Create Broker and Storage snapshots every day
"""

__version__ = '1.1.0'
__author__ = 'Bhupender Kumar, Ruby Zhao'

import os
import boto3
import datetime
import raven

def handler(event, context):
    fromEmail = 'tibco-mdm-noreply@tibco.com' 
    toEmail = 'alerts-cloudops@tibco.com'
    subject = 'Snapshots - Broker and Storage' 
    message = ('| Instance | Instance ID | Volume ID | Snapshot Created | Snapshot Deleted |\n'
            + '| --------- | ----------- | --------- | ---------------- | ---------------- |\n')
    
    # Looping through all regions
    ec2 = boto3.client('ec2')
    for region in ec2.describe_regions()['Regions']:
        
        ec2_client = boto3.client('ec2', region_name=region['RegionName'])
        res = ec2_client.describe_instances() # Describing EC2 instances in current region
        for r1 in res['Reservations']:
            for r2 in r1['Instances']:
                for r3 in r2['Tags']:
                    if r3['Value'].find("MDM") != -1 and (r3['Value'].find("roker") != -1 or r3['Value'].find("torage") != -1): # Filtering EC2 instances having a tag containing MDM and any one of Broker and Storage
                        for v1 in r2['BlockDeviceMappings']:
                            # Taking snapshot of Broker and Storage EBS volumes
                            snap = ec2_client.create_snapshot(Description='Snapshot for EBS Volume of' + ' ' + r3['Value']+ ' ' + 'taken on'+ ' ' + datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')  , VolumeId=v1['Ebs']['VolumeId'],DryRun=False)
                            desc_snap = ec2_client.describe_snapshots(Filters=[{'Name':'volume-id','Values': [v1['Ebs']['VolumeId']]}])
                            comp_date = datetime.datetime.now() - datetime.timedelta(days=2)
                            for s1 in desc_snap['Snapshots']:
                                if s1['StartTime'].replace(tzinfo=None) < comp_date.replace(tzinfo=None):
                                    ec2_client.delete_snapshot(SnapshotId=s1['SnapshotId'], DryRun=False) # Deleting snapshots older than specified date(comp_date)
                                    # Output message to be displayed and mailed to CloudOps
                                    message += "| %s | %s | %s | %s | %s |\n" %(r3['Value'], r2['InstanceId'], v1['Ebs']['VolumeId'], snap['SnapshotId'], s1['SnapshotId']) 

    scroll = raven.Scroll(raven.Severity.Report)
    return scroll.send_email(
            email_from = fromEmail,
            emails_to = [toEmail],
            subject = subject, 
            message_type = raven.MessageType.Markdown, 
            message = message            
    )

if (__name__ == "__main__"):
    handler(None, None)

