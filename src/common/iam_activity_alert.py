""" Alert for any IAM activities like creating/deleting a user/role/access keys etc.
"""
__version__ = '1.0.0'
__author__ = 'Pravin Singh'

import raven
import os

def handler(event, context):
    fromEmail = os.environ['fromEmail']
    toEmails = os.environ['toEmails']
    subject = event["detail"]["eventName"]
    event_summary = {
        "IAM Activity": {
            "Action": event["detail"]["eventName"],
            "Action Input": event["detail"]["requestParameters"],
            "Action Output": event["detail"]["responseElements"],
            "Region": event["region"],
            "Created time": event["time"],
            "Done by": event["detail"]["userIdentity"]["arn"].split(':')[5]
        }
    }
    scroll = raven.Scroll(raven.Severity.Alert)
    return scroll.send_email(
        email_from = fromEmail,
        emails_to = [toEmails],
        subject = subject,
        message_type = raven.MessageType.Json,
        message = event_summary
    )

if (__name__ == "__main__"):
    handler(None, None)