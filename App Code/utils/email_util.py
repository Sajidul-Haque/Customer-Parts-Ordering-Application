# utils/email_util.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def send_email(to_email, subject, body):
    """
    Send an email using SMTP with provided subject and body.
    
    Parameters:
        to_email (str): The recipient's email address.
        subject (str): The subject line of the email.
        body (str): The body/content of the email.
    """
    from_email = os.getenv('FROM_EMAIL')
    password = os.getenv('EMAIL_PASSWORD')

    if not from_email or not password:
        print("Email credentials are not set. Please check your .env file.")
        return

    try:
        # Setup the email message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Use TLS for security
            server.login(from_email, password)
            server.send_message(msg)
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
