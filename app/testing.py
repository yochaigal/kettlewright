# # Python program to explain os.environ object

# # importing os module
# import os
# import pprint

# # Get the list of user's
# # environment variables
# env_var = os.environ

# # Print the list of user's
# # environment variables
# print("User's Environment variable:")
# pprint.pprint(dict(env_var), width=1)

from __init__ import application
from flask_mail import Mail, Message
import os
mail = Mail(application)

sender = os.environ.get('MAIL_USERNAME')

msg = Message('test email', sender=sender, recipients=['dstearns77@gmail.com'])
msg.body = 'test body'
msg.html = '<b>testing</b>'
with application.app_context():
    mail.send(msg)
