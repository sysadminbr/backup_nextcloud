#!/usr/bin/python3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(sender_email, sender_password, recipient_email, subject, message, file_path):
    # Set up the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Add the message body
    msg.attach(MIMEText(message, 'plain'))

    # Open and attach the file
    with open(file_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())

    # Encode the attachment and add a header
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename= {file_path}')
    msg.attach(part)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP('smtp.office365.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

# Usage
sender_email = 'notifica@empresa.com.br'
sender_password = 'SenhaTravessa'
recipient_email = 'avisos@empresa.com.br'
subject = '[NEXTCLOUD] Backup Nextcloud'
message = 'Detalhes do backup no arquivo Anexo.'
file_path = '/var/log/nextcloud_backup.log'

send_email(sender_email, sender_password, recipient_email, subject, message, file_path)
