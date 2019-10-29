""" Base module for project Raven that contains the implementations of Scroll and other 
    related classes.
"""
__version__ = '0.8.1'
__author__ = 'Pravin Singh, Govarthanan Rajappan'

import boto3
import os
import json
from json2html import json2html
from markdown2 import markdown
import inspect
import logging
import requests
from enum import Enum, unique

@unique
class Severity(Enum):
    """ Severity level of the message.
    """
    Report = u"\U0001F4CB" #'📋'
    Info = u"\U00002139\U0000FE0F" #'ℹ️'
    Alert = u"\U000026A0\U0000FE0F" #'⚠️'
    Critical = u"\U0001F525" #'🔥'

@unique
class MessageType(Enum):
    """ Type of message. The message gets formatted according to its type:
        - A JSON message becomes a table (or nested tables). If it has only one key, the top level
          key becomes the table heading. The message can also be a list of multiple JSONs.
        - A text message is placed inside a text box and the message subject becomes the heading.
        - An HTML message is added to the notification body 'as-is'.
        - A markdown message is converted to HTML.
    """
    Json = 'JSON'
    Text = 'TEXT'
    Html = 'HTML'
    Markdown = 'MARKDOWN'

class Scroll:
    """ Scroll is what Raven carries. It's an envelop for the actual message, containing other
        details, like where this message is coming from, what the severity level is etc.
    """
    def __init__(self, severity, region=''):
        if (not isinstance(severity, Severity)):
            raise TypeError('%s is not of type Severity' %severity)
        self.raven_bucket = "https://raven-framework.s3.amazonaws.com"
        self.logger = get_logger('Scroll')
        self.severity = severity
        self.account_id = self._get_account_id()
        self.account_alias = str(self._get_account_alias()).title().replace('_','').replace('-','')
        if (region == ''):
            self.region = self._get_current_region()
        else:
            self.region = region
        try:
            self.source = inspect.currentframe().f_back.f_code.co_filename
        except:
            self.source = ''
    
    def _get_account_id(self):
        try:
            sts_client = boto3.client('sts')
            return sts_client.get_caller_identity()["Account"]
        except Exception as e:
            self.logger.exception(e)
            return ''

    def _get_account_alias(self):
        try:
            iam_client = boto3.client('iam')
            response = iam_client.list_account_aliases()
            # Since accounts can have only one alias, it's okay to return the first response
            return response['AccountAliases'][0]
        except Exception as e:
            self.logger.exception(e)
            return ''

    def _get_current_region(self):
        try:
            return os.environ['AWS_REGION']
        except KeyError as e:
            self.logger.error(e)
            return ''

    def _add_json_body(self, message):
        body = ''
        if (isinstance(message, dict)):
            if (len(message) == 1):
                for item in message:
                    body += ("<h3>" + item + "</h3>\n" 
                            + json2html.convert(json=message[item], escape=False))
            else:
                body += ("<br>\n" + json2html.convert(json=message, escape=False))
        # Just in case the message is a list of multiple jsons
        elif (isinstance(message, list)):
            for item in message:
                if (len(item) == 1):
                    for i in item:
                        body += ("<h3>" + i + "</h3>\n" 
                                + json2html.convert(json=item[i], escape=False))
                else:
                    body += ("<br>\n" + json2html.convert(json=item, escape=False))
        return body

    def _add_markdown_body(self, message):
        body = markdown(message)
        return body

    def _add_text_body(self, message, subject):
        body = '<h3>' + subject + '</h3>\n<div class="message-area">'
        for line in str(message).splitlines():
            body += line + '<br>'
        body += '</div>'
        return body

    def send_email(self, email_from, emails_to, subject, message_type, message):
        """ Composes a notification email and sends it using AWS SES service
        """
        if (type(message_type) != MessageType):
            raise TypeError('%s is not of type MessageType' %message_type)
        # Create email subject
        email_subject = (self.severity.value + '[' + self.severity.name.upper() + '] ' 
                        + self.account_alias + ': ' + subject)
        # Create email body
        email_body = \
        """<!DOCTYPE html><html><head>
            <style>
            table {border: 1px solid papayawhip; width: 100%; border-collapse: collapse;}
            th {text-align: left; padding-left: 5px; background-color: navajowhite;}
            td {padding-left: 5px; background-color: floralwhite}
            .banner {
                border: none;
                background: papayawhip url('""" + self.raven_bucket + """/res/scroll-banner.png') no-repeat;
                background-size: cover;
                font-size: x-large;
                overflow: auto;
                text-shadow: 0 0 10px white, 0 0 10px white;
            }
            .raven-icon {width: 60px; float: right;}
            .scroll-icon {width: 60px; float: left;}
            .scroll-type {color: white; font-size: smaller;}
            .account-name {font-weight: bold; font-size: smaller;}
            .account-id {color: dimgray; font-style: italic; float: left;}
            .region {color: dimgray; font-size: smaller;}
            .cloud-logo {width: 25px; float: left; margin-right: 10px;}
            .source {color: dimgray; font-style: italic; text-align: right; float: right;}
            .message-area {
                background: floralwhite; 
                border: navajowhite; 
                border-style: solid; 
                border-width: 1px; 
                padding: 15px;}
            </style></head><body>
        """
        # Add the banner
        email_body += ('<div class="banner"><img src="' + self.raven_bucket + '/res/'
                        + self.severity.name + '.png" class="scroll-icon"><img src="'
                        + self.raven_bucket + '/res/raven-logo.png" class="raven-icon">'
                        + '<div class="scroll-type">' + self.severity.name
                        + '</div><span class="account-name">' + self.account_alias + '</span>')
        if (self.region != ''):
            email_body += '<span class="region""> | ' + self.region + '</span>'
        email_body += '</div>\n'
        # Add the message body
        if message_type is MessageType.Json:
            email_body += self._add_json_body(message)
        elif message_type is MessageType.Markdown:
            email_body += self._add_markdown_body(message)
        elif message_type is MessageType.Text:
            email_body += self._add_text_body(message, subject)
        elif message_type is MessageType.Html:
            email_body += message
        # Add the footer: cloud type logo, account id, and source (caller)
        email_body += '<hr>'
        email_body += '<img src="' + self.raven_bucket + '/res/aws-logo.png" class="cloud-logo">\n'
        if (self.account_id != ''):
            email_body += '<div class="account-id">Account Id: ' + self.account_id + '</div>\n'
        if (self.source != ''):
            email_body += '<div class="source">Notification Source: ' + self.source + '</div>\n'
        email_body += '</body>\n</html>'
        
        # Send
        try:
            ses_client = boto3.client('ses')
            response = ses_client.send_email(
                        Source=email_from,
                        Destination={'ToAddresses': emails_to,
                        },
                        Message={
                            'Subject': {
                                'Data': email_subject,
                                'Charset': 'UTF-8'
                            },
                            'Body': {
                                'Html': {
                                    'Data': email_body,
                                    'Charset': 'UTF-8'
                                },
                                'Text': {
                                    'Data': json.dumps(message),
                                    'Charset': 'UTF-8'
                                }
                            }
                        })

            return response
        except Exception as e:
            self.logger.exception(e)

    def send_slack_message(self, channel, alertmsg, service, tenant):
        if self.scroll_type.name == 'Critical':
            alertmsg = ':fire:' + alertmsg
            color = 'danger'
        elif self.scroll_type.name == 'Info':
            alertmsg = ':white_check_mark:' + alertmsg
            color = 'good'
        elif self.scroll_type.name == 'Alert':
            alertmsg = ':heavy_exclamation_mark:' + alertmsg
            color = 'warning'
        elif self.scroll_type.name == 'Report':
            alertmsg = ':bar_chart:' + alertmsg
            color = '#439FE0'
        else: 
            color = '#FFFF00'

        #url="https://hooks.slack.com/services/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"
        url = "https://hooks.slack.com/services/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"
        
        payload={
            "channel": channel, 
            "username": "SRE Alerts", 
            "attachments": [{
                "color":color, 
                "pretext":"<!here>", 
                "title": alertmsg,
                "fields": [{
                    "title": "Service", 
                    "value" : service, 
                    "short": True
                },
                {
                    "title": "Tenant",
                    "value": tenant,
                    "short": True
                },
                {
                    "title":"Region", 
                    "value":self.region, 
                    "short":True
                },
                {
                    "title":"Source",
                    "value":self.source,
                    "short":True
                }],
                "footer": "Connected Intelligence Cloud",
                "footer_icon":"https://raven-framework.s3.amazonaws.com/aws-logo.png"#,
                #"ts":calendar.timegm(time.gmtime())
            }]
        }
        r = requests.post(url=url, data=json.dumps(payload))


def get_logger(name='', level='DEBUG'):
    """ Get the Python logger. By default, the level is set to DEBUG but can be changed as needed.\n
    ``name``: Set it to the filename you are calling it from\n
    ``level``: Text logging level for the message ('DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL')
    """
    #logging.basicConfig(format='%(asctime)s - %(name)s: %(levelname)s - %(message)s')
    logging.basicConfig(format='File %(filename)s, Function %(funcName)s, Line %(lineno)d: [%(levelname)s] %(message)s')
    logger = logging.getLogger(name)
    levelname = logging.getLevelName(level)
    logger.setLevel(levelname)
    return logger
