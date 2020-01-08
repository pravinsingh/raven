""" Checks if all the ISO jobs run successfully.
"""
__version__ = '1.2.0'
__author__ = 'Bhupender Kumar, Ruby Zhao'

import os
import boto3
import datetime
import raven

def handler(event, context):
    fromEmail = 'tibco-mdm-noreply@tibco.com' 
    toEmail = 'alerts-cloudops@tibco.com' 
    subject = 'ISO jobs status'  
    message = ''
    
    str_mgs = "ISO job did not execute properly this week."  # Message Body
    fine_msg = "All ISO jobs executed successfully this week"
    ssm_obj = boto3.client('ssm', region_name='us-east-1') 
    resp_par = ssm_obj.get_parameter(Name='iso-jobs-param-store')
    iso_jobs = ['base-package', 'change-package', 'clam-scan']
    file_name = []
    alert=False

    par_vals = resp_par['Parameter']['Value'].split(",") # Importing parameter value defined in parameter store.
    
    for x1 in iso_jobs:
        file_name.append([s + x1 for s in par_vals])
    
    file_list = [item for sublist in file_name for item in sublist] # Final list of files expected every week.
    queue_messages = []
    
    try:
        sqs_obj = boto3.client('sqs', region_name='us-east-1')
        res = sqs_obj.get_queue_attributes(QueueUrl='https://sqs.us-east-1.amazonaws.com/013185853748/iso-mdm-job-queue', AttributeNames=['All']) 
    
        while(1):
            msgs = sqs_obj.receive_message(QueueUrl='https://sqs.us-east-1.amazonaws.com/013185853748/iso-mdm-job-queue', AttributeNames=['All']) # Importing SQS message
            for m1 in msgs['Messages']:
                if m1['Body'] not in queue_messages:
                    queue_messages.append(m1['Body']) # Appending message body to a list.
                else:
                    continue
            dmsg = sqs_obj.delete_message(QueueUrl='https://sqs.us-east-1.amazonaws.com/013185853748/iso-mdm-job-queue', ReceiptHandle=m1['ReceiptHandle']) # Deleting the message from the queue.
                
        num_of_msgs = int(res['Attributes']['ApproximateNumberOfMessages'])
        print(num_of_msgs)
        
    except KeyError:
        print("Queue is now empty")
        #print(queue_messages)
    not_present = []
    
    for r1 in file_list:
        if any(r1 in s for s in queue_messages):    #Comparing message body with parameter value defined in parameter store.
            continue
        else:
            not_present.append(r1)
            message += ' ' + r1 + ' ' + str_mgs + ' ''\n'
            alert=True
    #print(not_present)
    
    if message == '':
        message += ' ' + fine_msg
    if alert:
            scroll = raven.Scroll(raven.Severity.Alert)
    else:
        scroll = raven.Scroll(raven.Severity.Info)
    return scroll.send_email(
            email_from = fromEmail,
            emails_to = [toEmail],
            subject = subject, 
            message_type = raven.MessageType.Text,
            message = message         
    )
if (__name__ == "__main__"):
    handler(None, None)