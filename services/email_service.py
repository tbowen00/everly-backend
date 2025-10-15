import os
import resend
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', 'hello@everlystudio.co')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Everly Studio')
        
        if self.api_key:
            resend.api_key = self.api_key
        
        # Log configuration
        print(f"📧 Email Service Initialized (Resend):", flush=True)
        print(f"  From Email: {self.from_email}", flush=True)
        print(f"  API Key Configured: {'Yes' if self.api_key else 'No'}", flush=True)
        
    def send_email(self, to_email, subject, body_html, body_text=None):
        """Send a single email using Resend"""
        try:
            if not self.api_key:
                error_msg = "Resend API key not configured"
                print(f"❌ {error_msg}", flush=True)
                return {'success': False, 'error': error_msg}
            
            print(f"📤 Sending email to {to_email} via Resend...", flush=True)
            
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": body_html,
            }
            
            if body_text:
                params["text"] = body_text
            
            email = resend.Emails.send(params)
            
            print(f"✅ Email sent successfully to {to_email} (ID: {email['id']})", flush=True)
            return {'success': True}
            
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            print(f"❌ {error_msg}", flush=True)
            import traceback
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
        """Test Resend API connection"""
        try:
            if not self.api_key:
                return {
                    'success': False, 
                    'error': 'Resend API key not configured'
                }
            
            print("Testing Resend API connection...", flush=True)
            
            # Try sending a test email to verify the API key works
            # Note: This will actually send an email
            test_result = self.send_email(
                to_email=self.from_email,  # Send test to yourself
                subject="Test Email from Everly Studio",
                body_html="<p>This is a test email to verify your Resend integration is working!</p>"
            )
            
            if test_result['success']:
                print("✅ Resend API connection successful", flush=True)
                return {'success': True, 'message': 'Resend API connection successful'}
            else:
                return {'success': False, 'error': test_result.get('error')}
            
        except Exception as e:
            error_msg = f"Resend API test failed: {str(e)}"
            print(f"❌ {error_msg}", flush=True)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}