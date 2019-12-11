""" Storage Common Dir, Local Postgres and recent logs backup.
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
    subject = 'Backup - Broker, Storage and Logs' #os.environ['subject']  
    message = """    
                                   <br><b style="font-size:18px">Storage Common Dir and Local postgrebackup update</b><br>
                                        <table >
                                            <col style="width:25%" span="2" />
                                        <tr style="background-color: lightgray"><th>Bucket Name</th><th>Job Update</th></tr>"""

    ssm_obj = boto3.client('ssm', region_name='us-east-1')
    resp_broker = ssm_obj.get_parameter(Name='broker-backup-buckets')
    broker_buckets = resp_broker['Parameter']['Value'].split(",")
    resp_storage = ssm_obj.get_parameter(Name='storage-backup-buckets')
    storage_buckets = resp_storage['Parameter']['Value'].split(",")
    resp_logs = ssm_obj.get_parameter(Name='logs-backup-buckets')
    logs_buckets = resp_logs['Parameter']['Value'].split(",")
    
    message_1 = "Bucket Name: "
    message_2 = " file was not uploaded."
    message_4 = "All files were uploaded successfully"   
    message_b = "Broker Console DB backup update"
    message_l = "Most recent Log backups"
    alert = False
    
    s3_client = boto3.client('s3')
    storage_files = ['dynservices.zip', 'commondir.zip', 'config.zip', 'dbexportfile.zip', 'backuptool.properties.zip']
    broker_files = ['mdmconsole.zip', 'dbexportfile.zip', 'brokerbackuptool.properties.zip']
    comp_date = datetime.datetime.now() - datetime.timedelta(days=1)
    
    temp_list = []
    mid_list = []
    not_present = []          
    for s1 in storage_buckets:
        resp = s3_client.list_objects(Bucket=s1)
        for s2 in resp['Contents']:
            if s2['LastModified'].replace(tzinfo=None) > comp_date.replace(tzinfo=None):
                temp_list.append(s2['Key'])
        for s3 in storage_files:
            
            if any(s3 in s for s in temp_list):
                continue
            else:
                mid_list.append(s3)

        if len(mid_list) == 0:
            message += "<tr><td>%s</td><td style=\"color:green\">%s</td></tr>" %(s1, message_4)
        else:
            for s4 in mid_list:
                temp_msg += s4 + message_2 + "<br>"
                alert = True
            message += "<tr><td>%s</td><td style=\"color:red\">%s</td></tr>" %(s1, temp_msg)
        temp_list = []
        mid_list = []
        temp_msg = ""

    message +=  """</table><br>""" 
    message += """<br><b style="font-size:18px">Broker Console DB backup update</b><br>"""
    message +=""" <table>
                    <col style="width:25%" span="2" />
                    <tr style="background-color: lightgray;"><th>Bucket Name</th><th>Job Update</th></tr>"""
    for b1 in broker_buckets:
        resp = s3_client.list_objects(Bucket=b1)
        for b2 in resp['Contents']:
            if b2['LastModified'].replace(tzinfo=None) > comp_date.replace(tzinfo=None):
                temp_list.append(b2['Key'])
        for b3 in broker_files:
            if any(b3 in s for s in temp_list):
                continue
            else:
                mid_list.append(b3)
        if len(mid_list) == 0:
            message += "<tr><td>%s</td><td style=\"color:green\">%s</td></tr>" %(b1, message_4 )
        else:
            for b4 in mid_list:
                temp_msg += b4 + message_2 + "<br>"
                alert = True
            message += "<tr><td>%s</td><td style=\"color:red\">%s</td></tr>" %(b1, temp_msg)
                
        temp_list = []
        mid_list = []
        temp_msg = ""
    message +=  """</table><br>"""
    message += """<br><b style="font-size:20px">Most recent Log backups</b><br>"""
    message +=""" <table>
                        <col style="width:25%" span="2" />
                        <tr style="background-color: lightgray;"><th>Bucket Name</th><th>Logs</th></tr>"""

    dict1 = {}
    for l1 in logs_buckets:
        resp = s3_client.list_objects(Bucket=l1)
        
        for l2 in resp['Contents']:
            if l2['LastModified'].replace(tzinfo=None) > comp_date.replace(tzinfo=None):
                key1 = l2['Key']
                value1 = l2['LastModified'].strftime('%m/%d/%Y %H:%M:%S')
                dict1[key1] = value1
        temp_msg = ""
        for k, v in dict1.items():
            temp_msg += k + " " + v + "<br>"
        message += "<tr><td>%s</td><td>%s</td></tr>" %(l1, temp_msg)
        
    message +=  """</table>
                                """          
    
    if alert:
        scroll = raven.Scroll(raven.Severity.Alert)
    else:
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