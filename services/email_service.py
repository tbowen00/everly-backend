import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'mail.privateemail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Everly Studio')
        
    def send_email(self, to_email, subject, body_html, body_text=None):
        """Send a single email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text version (fallback)
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"✓ Email sent to {to_email}", flush=True)
            return {'success': True}
            
        except Exception as e:
            print(f"✗ Failed to send email to {to_email}: {str(e)}", flush=True)
            return {'success': False, 'error': str(e)}
    
    def send_bulk_emails(self, recipients, subject, body_html, body_text=None):
        """Send emails to multiple recipients"""
        results = {
            'total': len(recipients),
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for recipient in recipients:
            result = self.send_email(recipient['email'], subject, body_html, body_text)
            
            if result['success']:
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'email': recipient['email'],
                    'error': result.get('error')
                })
        
        return results
    
    def test_connection(self):
        """Test SMTP connection"""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            return {'success': True, 'message': 'SMTP connection successful'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
