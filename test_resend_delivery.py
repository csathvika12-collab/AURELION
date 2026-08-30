import os
import resend
from dotenv import load_dotenv

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

email_to_test = "csathvika10@gmail.com"

print(f"Attempting to send email to: {email_to_test}")

try:
    r = resend.Emails.send({
        "from": "aurelion@resend.dev",
        "to": email_to_test,
        "subject": "Verification Test",
        "html": "<p>This is a test to verify your Resend account is working for your email.</p>"
    })
    print(f"✓ Success! Email sent. ID: {r.get('id')}")
except Exception as e:
    print(f"❌ Failed: {e}")
