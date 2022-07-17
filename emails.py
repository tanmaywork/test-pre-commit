import re
from app import app
from flask import g
import boto3, os, sys, logging, traceback
from botocore.exceptions import ClientError
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

SENDER = app.config['SMTP_FROM_ADDRESS']
#CONFIGURATION_SET = "ConfigSet"
AWS_REGION = "us-west-2"
CHARSET = "UTF-8"
# Create a new SES resource and specify a region.
client = boto3.client('ses',
            region_name=AWS_REGION)

logger = logging.getLogger("root")

def send_email(to_address, subject, message, envelope_from=None, reply_to=None, cc_address=None, bcc_address=None, 
    attachments=None, mime_type='plain', sender_name=None):
    if not envelope_from:
        envelope_from = SENDER

    # Try to send the email.
    try:
        logging.error(f"{os.environ.get('PAYFERENCE_ENV')} Trying to send email -> to_address: {to_address}, subject: {subject}, message-len: {len(message)}, envelope_from: {envelope_from}, reply_to: {reply_to}, cc_address: {cc_address}, bcc_address: {bcc_address}")

        from_header = "<" + envelope_from + ">"
        if sender_name:
            sender_name = re.sub("[^0-9a-zA-Z]+", " ", sender_name)
            from_header = sender_name + from_header

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = from_header
        msg['To'] = ', '.join([to_address])
        if reply_to:
            msg['reply-to'] = reply_to
        if cc_address:
            msg['Cc'] = ', '.join([cc_address])
        if bcc_address:
            msg['Bcc'] = bcc_address
        # message body
        part = MIMEText(message, mime_type)
        msg.attach(part)
        # attachments
        if attachments:
            for attachment in attachments:
                msg.attach(attachment)

        response = client.send_raw_email(
            Source=envelope_from,
            Destinations=[],
            RawMessage={
                'Data': msg.as_string()
            }
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        logging.critical(e.response['Error']['Message'])
        raise
    except:
        e = sys.exc_info()
        logging.critical(e)
        raise
    else:

        user = None
        try:
            user = g.user
        except:
            pass

        if user:
            logging.error("%s: Email sent by user %s! Message ID: %s", os.environ.get('PAYFERENCE_ENV'), user.name, response['MessageId'])
        else:
            logging.error("%s: Email sent! Message ID: %s", os.environ.get('PAYFERENCE_ENV'), response['MessageId'])
        return response