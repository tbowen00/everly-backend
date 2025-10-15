import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import traceback

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'mail.privateemail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Everly Studio')
        
        # Log configuration (without exposing password)
        print(f"📧 Email Service Initialized:", flush=True)
        print(f"  SMTP Host: {self.smtp_host}", flush=True)
        print(f"  SMTP Port: {self.smtp_port}", flush=True)
        print(f"  Username: {self.smtp_username}", flush=True)
        print(f"  From Email: {self.from_email}", flush=True)
        print(f"  Password Configured: {'Yes' if self.smtp_password else 'No'}", flush=True)
        
    def send_email(self, to_email, subject, body_html, body_text=None):
        """Send a single email"""
        try:
            # Validate configuration
            if not all([self.smtp_username, self.smtp_password, self.from_email]):
                error_msg = "SMTP credentials not fully configured"
                print(f"❌ {error_msg}", flush=True)
                return {'success': False, 'error': error_msg}
            
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
            
            print(f"📤 Attempting to send email to {to_email}...", flush=True)
            print(f"  Connecting to {self.smtp_host}:{self.smtp_port}", flush=True)
            
            # Use SSL for port 465, STARTTLS for port 587
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    print(f"  Using SSL connection...", flush=True)
                    print(f"  Logging in as {self.smtp_username}...", flush=True)
                    server.login(self.smtp_username, self.smtp_password)
                    print(f"  Sending message...", flush=True)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    print("  Starting TLS...", flush=True)
                    server.starttls()
                    print(f"  Logging in as {self.smtp_username}...", flush=True)
                    server.login(self.smtp_username, self.smtp_password)
                    print(f"  Sending message...", flush=True)
                    server.send_message(msg)
            
            print(f"✅ Email sent successfully to {to_email}", flush=True)
            return {'success': True}
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication failed: {str(e)}"
            print(f"❌ {error_msg}", flush=True)
            return {'success': False, 'error': error_msg}
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            print(f"❌ {error_msg}", flush=True)
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            print(f"❌ {error_msg}", flush=True)
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
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
            if not all([self.smtp_username, self.smtp_password]):
                return {
                    'success': False, 
                    'error': 'SMTP username or password not configured'
                }
                
            print(f"Testing SMTP connection to {self.smtp_host}:{self.smtp_port}...", flush=True)
            
            # Use SSL for port 465, STARTTLS for port 587
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.login(self.smtp_username, self.smtp_password)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                
            print("✅ SMTP connection successful", flush=True)
            return {'success': True, 'message': 'SMTP connection successful'}
            
        except Exception as e:
            error_msg = f"SMTP connection failed: {str(e)}"
            print(f"❌ {error_msg}", flush=True)
            traceback.print_exc()
            return {'success': False, 'error': error_msg}