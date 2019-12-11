""" Base module for project Raven that contains the implementations of Scroll and other 
    related classes.
"""

__version__ = '0.8.1'
__author__ = 'Bhupender Kumar, Ruby Zhao'

import os
import boto3
import datetime
import raven

def handler(event, context):
    fromEmail = 'tibco-mdm-noreply@tibco.com' #os.environ['fromEmail']
    toEmail = 'hzhao@tibco.com' #os.environ['toEmail']
    subject = 'Broker and Storage EBS daily snapshot update' #os.environ['subject']
    message = """
                    <table>
                        <tr style="background-color: lightgray;">
                        <th>Instance</th>
                        <th>Instance ID</th>
                        <th>Volume ID</th>
                        <th>Snapshot Created</th>
                        <th>Snapshot Deleted</th></tr>"""
    # Variables used in output message
    ins_id = "InstanceID:"
    snap_cre = "Snapshot Created:"
    snap_del = "Snapshot Deleted:"
    vol_id = "VolumeID:"
    
    # Looping through all regions
    ec2_client = boto3.client('ec2')
    for region in ec2_client.describe_regions()['Regions']:
        #print('region', region['RegionName'])
        ec2_1 = boto3.client('ec2', region_name=region['RegionName'])
        res = ec2_1.describe_instances() # Describing EC2 instances in current region
        for r1 in res['Reservations']:
            for r2 in r1['Instances']:
                for r3 in r2['Tags']:
                    if r3['Value'].find("MDM") != -1 and (r3['Value'].find("roker") != -1 or r3['Value'].find("torage") != -1): # Filtering EC2 instances having a tag containing MDM and any one of Broker and Storage
                        #print('instance id is: ', r2['InstanceId'])
                        for v1 in r2['BlockDeviceMappings']:
                            #print(v1['Ebs']['VolumeId'],r2['InstanceId'],r3['Value'])
                            # Taking snapshot of Broker and Storage EBS volumes
                            snap = ec2_1.create_snapshot(Description='Snapshot for EBS Volume of' + ' ' + r3['Value']+ ' ' + 'taken on'+ ' ' + datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')  , VolumeId=v1['Ebs']['VolumeId'],DryRun=False)
                            #message += r3['Value'] + ' ' + ins_id + ' ' + r2['InstanceId'] + ' ' + vol_id + ' ' + v1['Ebs']['VolumeId'] + ' ' + snap_cre + ' ' + snap['SnapshotId']+ ' ''\n'
                            desc_snap = ec2_1.describe_snapshots(Filters=[{'Name':'volume-id','Values': [v1['Ebs']['VolumeId']]}])
                            comp_date = datetime.datetime.now() - datetime.timedelta(days=2)
                            for s1 in desc_snap['Snapshots']:
                                #print(s1['SnapshotId'], s1['StartTime'])
                                if s1['StartTime'].replace(tzinfo=None) < comp_date.replace(tzinfo=None):
                                    #print(r3['Value'], s1['SnapshotId'], s1['StartTime'])
                                    del_snap = ec2_1.delete_snapshot(SnapshotId=s1['SnapshotId'], DryRun=False) # Deleting snapshots older than specified date(comp_date)
                                    # Output message to be displayed and mailed to CloudOps
                                    #message += ' ' + snap_del + ' ' + s1['SnapshotId']+ ' ''\n'
                                    message += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %(r3['Value'], r2['InstanceId'], v1['Ebs']['VolumeId'], snap['SnapshotId'], s1['SnapshotId'])
                                 
    message +=  """</table>
                       
                    """  

    scroll = raven.Scroll(raven.Severity.Report)
    return scroll.send_email(
            email_from = fromEmail,
            emails_to = [toEmail],
            subject = subject, 
            message_type = raven.MessageType.Html, 
            message = message            
    )

if (__name__ == "__main__"):
    handler(None, None)

