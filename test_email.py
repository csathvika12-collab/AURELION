import os
import resend
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("RESEND_API_KEY")
print(f"Loaded API Key: {api_key}")

if not api_key:
    print("Error: RESEND_API_KEY is missing in .env")
    exit(1)

resend.api_key = api_key

try:
    print("Attempting to send email...")
    r = resend.Emails.send({
        "from": "aurelion@resend.dev",
        "to": "csathvika10@gmail.com", 
        "subject": "Test Email from Gemini CLI",
        "html": "<p>If you see this, the email configuration is working!</p>"
    })
    print(f"Success! Response: {r}")
except Exception as e:
    print(f"Failed to send email: {e}")
