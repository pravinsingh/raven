# raven
Raven is a notification framework that aims to optimize and standardize various notifications coming in from cloud infrastructure. For any SRE team, part of the job is to monitor the cloud environments and notify about any suspicious activities or report progress of scheduled activities. Teams try to automate this by writing several small, independent AWS Lambda functions (or Azure functions) that get triggered by different events and send notifications in the form of emails, Slack messages, OpsGenie alerts or something similar. There are a few problems with this approach, however:
- Every engineer composes the notification in his/her own style, so there's no uniformity.
- Every Lambda/Azure function has the code to send emails, Slack messages *etc*. That's a lot of duplicate code that can be avoided.
- Since there is no agreement on the message format or the severity level of notifications, some relatively minor notifications may be tagged as important while actually important notifications might get buried.
- If too many notifications arrive, it is difficult to know at a glance which notifications require immediate attention and which ones can wait.
- The scattered Lambda/Azure functions become difficult to manage.
- If there are too many functions, sometimes it is hard to know where a particular notification is coming from.

Raven addresses these concerns by creating a consolidated notification framework that centralizes common code in a library which can be accessed by all
the functions. The framework also:
- Standardizes the alert subject and allows different standardized alert body templates for different content (*e.g.* JSON, HTML, Markdown, plain text
*etc.*)
- Makes it easy to identify the type and priority of the alert.
- Makes the content more readable, so that the recipient can get the gist of the alert by just a quick glance.
- Identifies the source of the alert (*i.e.* where the alert is coming from).
- Provides integration points with different alerting systems (*e.g.* Email, OpsGenie, Slack *etc.*)

The screenshot below shows subject lines for different notification types, and the preview pane shows how JSON data is shown in a tabular format in the
email body:
![image](https://user-images.githubusercontent.com/8378748/227669616-27254a44-2656-41f2-8520-48c76429350e.png)

---

**What's in the name**

*The name 'Raven' is an obvious reference to the hit HBO series 'Game of Thrones'. The framework also has a class called 'Scroll' which is like an envelop for the actual message, containing other details, like where this message is coming from, what the importance level is etc. Just like in the TV series where ravens were used to send messages written on scrolls (rolled up paper), you write your 'message' on a 'scroll' and send it through 'raven'.*

---

## Using Raven Module
Raven can be used in two ways:
- As a Python module in your Lambda functions, or
- As a REST API that can be called from anywhere
### Using Raven in Lambda functions
Raven Python module (raven.py) can be hosted as a Lambda layer in an account. Please note that since it needs the ability to send emails using 
Amazon SES service, it can be used only in the regions which support SES (currently N. Virginia, Oregon, and Ireland). To use this module in your 
Lambda code, follow these steps (the steps are shown for N. Virginia region, change the region as appropriate for other regions).

#### Make Raven accessible to your account
These steps are needed only once and only if you are hosting the layer in a different account.

- Get the latest version of ‘raven’ layer. To do this, connect to the account hosting the layer using AWS CLI and use this command:
`aws lambda list-layer-versions --layer-name raven`
This should show all the versions of ‘raven’ layer. Make a note of the latest version number and its ARN. You’d need the ARN later.

![Screenshot 2023-03-24 at 4 24 52 PM](https://user-images.githubusercontent.com/8378748/227661039-b41d231a-7112-48ad-9889-6ee7cca55aa0.png)

- Grant access on the latest ‘raven’ layer to your account. To do this, use this command:
`aws lambda add-layer-version-permission --layer-name raven --statement-id <your-account-alias> --
action lambda:GetLayerVersion \
--principal <your-account-id> --version-number <latest-layer-version-number> --output text`

If successful, this will show the json policy which was added to the layer version.

![image](https://user-images.githubusercontent.com/8378748/227671082-f27476a6-7175-4681-8ee2-0505a483c267.png)

#### Create your Lambda function
- Log into AWS console of your account, go to Lambda service, and create your function. Use the runtime as Python 3.7 or Python 3.6.
- Make sure that the execution role you chose, has the following permissions:
    - `iam:ListAccountAliases`
    - `ses:SendEmail`
- On the function configuration page, click on ‘Layers’, and then on ‘Add a layer’.
- On the Layer selection page, select ‘Provide a layer version ARN’ and provide the layer ARN that you noted down in an earlier step.
- Click ‘Add’. The layer should now show up in the list of layers.
- In the Lambda ‘Designer’ section, click on the function name to go back to code editor window.
- In your code you can now import the raven module as any other Python module. Here is a sample code that uses raven to send a notification email:
```python
import raven
import os

json_message = {
  "IAM Activity": {
    "Action": "CreateAccessKey",
    "Action Input": {
      "userName": "user1@example.com"
    },
    "Action Output": {
      "accessKey": {
        "accessKeyId": "ABCDE12MT3UKHTPQXYZ7",
        "status": "Active",
        "userName": "user1@example.com",
        "createDate": "May 21, 2022 6:45:11 PM"
      }
    },
    "Time": "2022-05-21T18:45:11Z",
    "Region": "us-east-1",
    "Done by": "user/user1@example.com"
  }
}

markdown_message = """> A list within a blockquote:
>
> * Item 1
> * Item 2
> * Item 3
####Sample Table
|Heading 1| Heading 2 |\n| ----- | ----- |\n| 11111 | 22222 |\n| 1110000 | 2220000 |\n
"""

text_message = "Something somewhere failed.\nSome random one-liner text from somewhere."

html_message = """
<br><b style="font-size:18px">Database backup update</b><br>
<table>
<col style="width:25%" span="2" />
<tr style="background-color: lightgray;"><th>Bucket Name</th><th>Job Update</th></tr>
<tr><td>database-1</td><td style="color:green">All files were uploaded successfully</td></tr>
<tr><td>database-2</td><td style="color:green">All files were uploaded successfully</td></tr>
<tr><td>database-3</td><td style="color:red">Some files did not upload</td></tr>
<tr><td>database-4</td><td style="color:green">All files were uploaded successfully</td></tr>
</table>
"""

def handler(event, context):
  scroll = raven.Scroll(raven.Severity.Info)
  return scroll.send_email(
      email_from = 'noreply@example.com',
      emails_to = ['user2@example.com', 'group1@example.com'],
      subject = "Sample email from Raven",
      message_type = raven.MessageType.Text,
      message = text_message
  )
  
if (__name__ == "__main__"):
handler(None, None)
```

### Using Raven as a REST API
If you want to use Raven at a place other than Lambda functions (*e.g.* from Azure, or from a custom app), you can put a Lambda function
(providing a wrapper around the Raven module) behind an API Gateway and expose it as a REST API. The API can accept all the details of the 
email as a json object in the message body, *e.g.*:
```json
{
  "sender" : "noreply@example.com",
  "receivers" : "['user2@example.com', 'group1@example.com']",
  "severity" : "Info",
  "message_type" : "Html",
  "subject" : "API Gateway Test",
  "message" : "<strong>Hello from Raven!</strong>"
}
```

## Raven Classes

Raven module has 3 classes:
### Severity
This shows the severity level of the message. It can have one of the four values:
- **Critical**: Should be used when we are *sure* that this message is *actionable* and needs human intervention.
- **Info**: Should be used when we are *sure* that this message is *not actionable* and provides only information.
- **Alert**: Should be used when we are *not sure* whether or not this message is actionable.
- **Report**: Should be used for providing reporting outputs, *e.g.* from Lambda functions that run periodically to check for something.

### MessageType
This shows the type of message content. The message gets formatted according to its type:
- A JSON message becomes a table (or nested tables). If it has only one key, the top level key becomes the table heading. The message can also be a 
list of multiple JSONs.
- A text message is placed inside a text box and the message subject becomes the heading.
- An HTML message is added to the notification body 'as-is'. Should be used when you want to have your own custom formatting, *e.g.* using
different colored text. When creating the HTML message, just create what should go inside the &lt;body&gt; tags. Outer tags like &lt;html&gt;, &lt;head&gt;,
&lt;body&gt; *etc.* are automatically added.
- A markdown message is converted to HTML.

### Scroll
Scroll is what Raven carries. It's an envelop for the actual message, containing other details, like where this message is coming from, what the 
severity level is *etc.* It is the main class in Raven and has the following exposed functions:
- `send_email(email_from, emails_to, subject, message_type, message) // Composes a notification email and sends it using AWS SES service:`
    - **email_from**: email address of the sender. It should be a verified email address (or a verified domain) in SES service in the region.
    - **emails_to**: email addresses of the receivers. It should be a list, even if it has a single address inside the list.
    - **subject**: subject line of the email
    - **message_type**: the type of message content, should be of type MessageType
    - **message**: the actual message
- `send_slack_message(channel, alertmsg, service, tenant) // Still under development, do not use`
- `send_opsgenie_alert() // Still under development, do not use`
