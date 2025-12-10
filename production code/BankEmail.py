import smtplib
import os
from email.mime.text import MIMEText

# Read environment variables. Make sure to enter these in your system before hand.
SENDER_EMAIL = os.environ.get("EMAIL_USER")
SENDER_PASSWORD = os.environ.get("EMAIL_PASS")

#this function will be sending an verificaiton email to the users email address.
def send_verification_email(to_email, verificationToken):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ EMAIL_USER or EMAIL_PASS environment variable is missing.")
        return False
    
    verificationURL = f"http://localhost:3000/verify?token={verificationToken}"

    emailBody = f"""
    <html>
    <body>
        <h2>Verify Your Budget App Account</h2>
        <p>Thank you for registering with Budget App!</p>
        <p>Please click the link below to verify your email address:</p>
        <p><a href="{verificationURL}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
        <p>Or copy and paste this link in your browser:</p>
        <p>{verificationURL}</p>
        <p>This link will expire in 24 hours.</p>
        <br>
        <p>If you didn't create an account, please ignore this email.</p>
    </body>
    </html>
    """

    msg = MIMEText(emailBody, 'html')
    msg['Subject'] = "Verify Your Budget App Account"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Verification email sent!")
        return True

    except Exception as e:
        print("Email sending failed:", e)
        return False
    
#Function to send an alert email to the user.
def send_alert_email(to_email, subject, body):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Missing email environment variables.")
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Alert email sent!")
        return True

    except Exception as e:
        print("Email sending failed:", e)
        return False
    
#making sure the email and app password are set.
if __name__ == "__main__":
    print("EMAIL_USER =", SENDER_EMAIL)
    print("EMAIL_PASS =", "SET" if SENDER_PASSWORD else "NOT SET")
    