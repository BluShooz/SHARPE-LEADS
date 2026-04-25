"""
LeadForge AI - Gmail Integration Module
Send outreach emails using SMTP (simpler, no additional dependencies)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import sqlite3


class GmailClient:
    def __init__(self, email_address=None, app_password=None):
        """
        Initialize Gmail client using SMTP

        Args:
            email_address: Your Gmail address
            app_password: Gmail app password (not your regular password)
                           Get one at: https://myaccount.google.com/apppasswords
        """
        self.email = email_address or "3lueshooz@gmail.com"
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

        if self.app_password:
            print(f"✅ Gmail client initialized for {self.email}")
        else:
            print(f"⚠️  Gmail client ready (app password needed to send emails)")

    def send_email(self, to, subject, body, html_body=None, from_name=None):
        """
        Send an email via Gmail SMTP

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            from_name: Sender name (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.app_password:
            print("❌ App password not set. Cannot send email.")
            print("📋 Get an app password at: https://myaccount.google.com/apppasswords")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((from_name or 'LeadForge AI', self.email))
            msg['To'] = to

            # Add plain text version
            part1 = MIMEText(body, 'plain')
            msg.attach(part1)

            # Add HTML version if provided
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)

            # Connect to Gmail SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.app_password)

            # Send email
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent to {to}")
            return True

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def send_outreach_email(self, lead, template_type='initial'):
        """
        Send personalized outreach email to a lead

        Args:
            lead: Lead dictionary with business details
            template_type: Type of email template ('initial', 'followup', etc.)

        Returns:
            True if successful, False otherwise
        """
        if not lead.get('email') or lead.get('email') == 'N/A':
            print(f"⚠️  No valid email for lead: {lead.get('business_name', 'Unknown')}")
            return False

        to = lead['email']
        business_name = lead.get('business_name', 'your business')
        website = lead.get('website', '')
        phone = lead.get('phone', 'N/A')
        location = lead.get('location', '')

        # Select template
        if template_type == 'initial':
            subject = f"Quick Question About {business_name}"
            body = f"""Hi there,

I hope this email finds you well. I came across {business_name} and was impressed by what you're building.

I'd love to learn more about your current operations and see if there might be opportunities for us to work together.

Would you be open to a brief 15-minute call this week?

Best regards,
LeadForge AI
{self.email}

---
Business Details:
• Business: {business_name}
• Website: {website}
• Phone: {phone}
• Location: {location}
"""

        elif template_type == 'followup':
            subject = f"Re: Quick Question About {business_name}"
            body = f"""Hi there,

I wanted to follow up on my previous email regarding {business_name}.

I understand you're busy, but I believe there could be some great synergies between our companies.

Would you have 5 minutes just to explore if this makes sense?

Best regards,
LeadForge AI
{self.email}
"""
        else:
            subject = f"Hello from LeadForge AI"
            body = f"Hi,\n\nI'd love to connect regarding {business_name}.\n\nBest regards,\nLeadForge AI"

        # Create HTML version
        html_body = f"""
        <html>
        <body>
            <p>Hi there,</p>
            <p>I hope this email finds you well. I came across <strong>{business_name}</strong> and was impressed by what you're building.</p>
            <p>I'd love to learn more about your current operations and see if there might be opportunities for us to work together.</p>
            <p>Would you be open to a brief 15-minute call this week?</p>
            <p>Best regards,<br><strong>LeadForge AI</strong><br>{self.email}</p>
            <hr>
            <p><small>Business Details:</small></p>
            <ul>
                <li>Business: {business_name}</li>
                <li>Website: {website}</li>
                <li>Phone: {phone}</li>
                <li>Location: {location}</li>
            </ul>
        </body>
        </html>
        """

        return self.send_email(to, subject, body, html_body)

    def send_bulk_outreach(self, leads, template_type='initial', delay=2, max_emails=None):
        """
        Send outreach emails to multiple leads

        Args:
            leads: List of lead dictionaries
            template_type: Type of email template
            delay: Delay between emails (seconds)
            max_emails: Maximum number of emails to send (None = all)

        Returns:
            Tuple of (successful_count, failed_count)
        """
        import time

        if max_emails:
            leads = leads[:max_emails]

        successful = 0
        failed = 0

        for i, lead in enumerate(leads, 1):
            print(f"\n[{i}/{len(leads)}] Sending to {lead.get('business_name', 'Unknown')} ({lead.get('email', 'no email')})...")

            if self.send_outreach_email(lead, template_type):
                successful += 1
                # Update lead status in database
                if lead.get('id'):
                    self._update_lead_status(lead['id'], 'contacted')
            else:
                failed += 1

            # Delay between emails
            if i < len(leads):
                print(f"⏳ Waiting {delay} seconds...")
                time.sleep(delay)

        print(f"\n📊 Email Campaign Complete:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        if successful + failed > 0:
            print(f"   📈 Success Rate: {successful/(successful+failed)*100:.1f}%")

        return successful, failed

    def _update_lead_status(self, lead_id, status):
        """Update lead status in database"""
        try:
            conn = sqlite3.connect('leads.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE leads SET status = ? WHERE id = ?', (status, lead_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️  Could not update lead status: {e}")


def send_test_email(app_password):
    """Send a test email to verify Gmail integration"""
    print("=" * 70)
    print("🧪 Gmail Integration Test")
    print("=" * 70)
    print()

    client = GmailClient(app_password=app_password)

    print("📧 Sending test email...")

    result = client.send_email(
        to='3lueshooz@gmail.com',
        subject='🎉 LeadForge AI - Gmail Integration Test!',
        body='Congratulations!\n\nYour Gmail integration is working perfectly.\n\nYou can now send outreach emails directly from LeadForge AI.\n\nBest regards,\nLeadForge AI Team',
        html_body='<h2>Congratulations!</h2><p>Your Gmail integration is working perfectly.</p><p>You can now send outreach emails directly from LeadForge AI.</p><br><p>Best regards,<br><strong>LeadForge AI Team</strong></p>',
        from_name='LeadForge AI'
    )

    if result:
        print("\n" + "=" * 70)
        print("✅ Test email sent successfully!")
        print("=" * 70)
        print("\n💡 Check your inbox (and spam folder) for the test email.")
        print("\n🚀 You're now ready to send outreach emails!")
        return True
    else:
        print("\n❌ Failed to send test email")
        print("\n📋 Make sure you:")
        print("1. Created an app password at: https://myaccount.google.com/apppasswords")
        print("2. Used the app password (not your regular password)")
        return False


if __name__ == "__main__":
    print("\n📧 LeadForge AI - Gmail Integration")
    print("\nTo send emails, you need a Gmail App Password:")
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Create a new app password")
    print("3. Use it when sending emails")
    print()
    print("Example usage:")
    print("  client = GmailClient(app_password='your-app-password')")
    print("  client.send_outreach_email(lead, template_type='initial')")
