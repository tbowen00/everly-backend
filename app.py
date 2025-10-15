from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Disable output buffering
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.contacts import contacts_bp
from api.analytics import analytics_bp
from api.email import email_bp
from api.filters import filters_bp
from api.lead_discovery import lead_discovery_bp
from api.campaigns import campaigns_bp
from api.email_templates import templates_bp
from config import DEBUG, HOST, PORT
from database.connection import get_session
from models.contact import Contact
from models.outreach import Outreach
from services.email_service import EmailService

app = Flask(__name__)
CORS(app, origins=["*"])

# Register all blueprints
app.register_blueprint(contacts_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(email_bp, url_prefix='/api')
app.register_blueprint(filters_bp, url_prefix='/api')
app.register_blueprint(lead_discovery_bp, url_prefix='/api')
app.register_blueprint(campaigns_bp, url_prefix='/api')
app.register_blueprint(templates_bp, url_prefix='/api')

email_service = EmailService()

@app.route('/')
def index():
    return jsonify({
        'message': 'Everly Studio Lead Generation Engine API',
        'version': '2.0',
        'endpoints': {
            'contacts': '/api/contacts',
            'analytics': '/api/analytics/dashboard',
            'campaigns': '/api/campaigns',
            'lead_discovery': '/api/lead-discovery/jobs',
            'filters': '/api/filters/options',
            'email_templates': '/api/email-templates'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/email/test', methods=['GET'])
def test_email_connection():
    """Test email SMTP connection"""
    result = email_service.test_connection()
    return jsonify(result)

@app.route('/api/email/send', methods=['POST'])
def send_email():
    """Send email to contacts"""
    data = request.json
    
    contact_ids = data.get('contact_ids', [])
    subject = data.get('subject')
    body_html = data.get('body_html')
    body_text = data.get('body_text')
    
    if not contact_ids or not subject or not body_html:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Get contacts
    session = get_session()
    try:
        contacts = session.query(Contact).filter(Contact.id.in_(contact_ids)).all()
        
        # Filter contacts with valid emails
        recipients = []
        for contact in contacts:
            if contact.email and '@' in contact.email:
                recipients.append({
                    'email': contact.email,
                    'name': contact.name,
                    'company': contact.company
                })
        
        if not recipients:
            return jsonify({'success': False, 'error': 'No valid email addresses found'}), 400
        
        # Send emails
        results = email_service.send_bulk_emails(recipients, subject, body_html, body_text)
        
        # Record outreach for sent emails
        for recipient in recipients:
            contact = next((c for c in contacts if c.email == recipient['email']), None)
            if contact:
                outreach = Outreach(
                    contact_id=contact.id,
                    outreach_type='email',
                    subject=subject,
                    message=body_html
                )
                session.add(outreach)
                
                contact.total_touches = (contact.total_touches or 0) + 1
                if contact.status == 'Lead':
                    contact.status = 'Contacted'
        
        session.commit()
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        session.rollback()
        print(f"Error sending emails: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    print("=" * 60, flush=True)
    print("🚀 Everly Studio Lead Generation Engine", flush=True)
    print("=" * 60, flush=True)
    print(f"Server running on: http://{HOST}:{PORT}", flush=True)
    print("Press CTRL+C to stop", flush=True)
    print("=" * 60, flush=True)
    app.run(host=HOST, port=PORT, debug=DEBUG)
