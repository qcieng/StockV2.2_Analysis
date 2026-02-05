import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

def send_email(subject, body):
    if not config.EMAIL_USER or not config.EMAIL_PASS:
        print("Email not configured.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = config.EMAIL_USER
        msg['To'] = config.EMAIL_TO
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain')) # Or 'html'
        
        server = smtplib.SMTP_SSL(config.EMAIL_HOST, config.EMAIL_PORT)
        server.login(config.EMAIL_USER, config.EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
