import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings


def send_email_notification(to_email: str, subject: str, message: str):
    try:
        # Object of the email
        msg = MIMEMultipart()
        msg['From'] = settings.MAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject

        # email text
        msg.attach(MIMEText(message, 'plain'))

        # Connect to server
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
        server.starttls()  # enable security
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)

        # send email
        text = msg.as_string()
        server.sendmail(settings.MAIL_FROM, to_email, text)
        server.quit()

        print(f"--- [EMAIL SENT SUCCESSFULLY] To: {to_email} ---")

    except Exception as e:
        print(f"!!! [EMAIL FAILED] Error: {e} !!!")