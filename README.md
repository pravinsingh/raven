# raven
Raven is a notification framework that aims to optimize and standardize various notifications coming in from cloud infrastructure. For any SRE team, part of the job is to monitor the cloud environments and notify about any suspicious activities or report progress of scheduled activities. Teams try to automate this by writing several small, independent AWS Lambda functions (or Azure functions) that get triggered by different events and send notifications in the form of emails, Slack messages, OpsGenie alerts or something similar. There are a few problems with this approach, however:
- Every engineer composes the notification in his/her own style, so there's no uniformity.
- Every Lambda/Azure function has the code to send emails, Slack messages etc. That's a lot of duplicate code that can be avoided.
- Since there is no agreement on the message format or the severity level of notifications, some relatively minor notifications may be tagged as important while actually important notifications might get buried.
- If too many notifications arrive, it is difficult to know at a glance which notifications require immediate attention and which ones can wait.
- The scattered Lambda/Azure functions become difficult to manage.
- If there are too many functions, sometimes it is hard to know where a particular notification is coming from.

Raven addresses these concerns by creating a consolidated notification framework that centralizes common code in a library which can be accessed by all
the functions. The framework also:
- Standardizes the alert subject and allows different standardized alert body templates for different content (e.g. JSON, HTML, Markdown, plain text
*etc.*)
- Makes it easy to identify the type and priority of the alert.
- Makes the content more readable, so that the recipient can get the gist of the alert by just a quick glance.
- Identifies the source of the alert (i.e. where the alert is coming from).
- Provides integration points with different alerting systems (e.g. Email, OpsGenie, Slack *etc.*)

---

**What's in the name**

*The name 'Raven' is an obvious reference to the hit HBO series 'Game of Thrones'. The framework also has a class called 'Scroll' which is like an envelop for the actual message, containing other details, like where this message is coming from, what the importance level is etc. Just like in the TV series where ravens were used to send messages written on scrolls (rolled up paper), you write your 'message' on a 'scroll' and send it through 'raven'.*
