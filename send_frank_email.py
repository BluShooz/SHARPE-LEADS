#!/usr/bin/env python3
"""
Send email to Frank
"""

import os
import sys
from send_email import GmailClient

# Email details
recipient = "Franksharpe008@gmail.com"
subject = "We Found You!"
body = """Hi Frank,

Great news! We found you and wanted to reach out.

We'd love to connect and discuss potential opportunities.

Best regards,
LeadForge AI
"""

html_body = """
<html>
<body>
    <h2>Hi Frank,</h2>
    <p>Great news! <strong>We found you</strong> and wanted to reach out.</p>
    <p>We'd love to connect and discuss potential opportunities.</p>
    <br>
    <p>Best regards,<br>
    <strong>LeadForge AI</strong></p>
</body>
</html>
"""

print("=" * 70)
print("📧 Sending Email to Frank")
print("=" * 70)
print()
print(f"To: {recipient}")
print(f"Subject: {subject}")
print()

# Get app password from environment variable or argument
app_password = os.environ.get('GMAIL_APP_PASSWORD')

if not app_password and len(sys.argv) > 1:
    app_password = sys.argv[1]

if not app_password:
    print("❌ Gmail App Password not provided!")
    print()
    print("📋 To send this email:")
    print("   Option 1: Set environment variable:")
    print("      export GMAIL_APP_PASSWORD='your-app-password'")
    print("      python3 send_frank_email.py")
    print()
    print("   Option 2: Pass as argument:")
    print("      python3 send_frank_email.py 'your-app-password'")
    print()
    print("💡 Get an app password at: https://myaccount.google.com/apppasswords")
    sys.exit(1)

# Initialize client
client = GmailClient(app_password=app_password)

# Send email
print("Sending...")
result = client.send_email(
    to=recipient,
    subject=subject,
    body=body,
    html_body=html_body,
    from_name="LeadForge AI"
)

if result:
    print()
    print("=" * 70)
    print("✅ Email sent successfully to Frank!")
    print("=" * 70)
else:
    print()
    print("❌ Failed to send email")
    print()
    print("💡 Make sure you:")
    print("1. Created an app password at: https://myaccount.google.com/apppasswords")
    print("2. Used the app password (not your regular password)")
