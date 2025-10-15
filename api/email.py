from flask import Blueprint, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.email_service import EmailService
from database.connection import get_session
from models.contact import Contact
from models.outreach import Outreach

email_bp = Blueprint('email', __name__)
email_service = EmailService()

@email_bp.route('/email/send', methods=['POST'])
def send_email():
    """Send email to contacts"""
    data = request.json
    
    contact_ids = data.get('contact_ids', [])
    subject = data.get('subject')
    body_html = data.get('body_html')
    body_text = data.get('body_text')
    
    if not contact_ids or not subject or not body_html:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
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
        
        # Record outreach
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

@email_bp.route('/email/log-touch', methods=['POST'])
def log_touch():
    """Manually log an outreach touch"""
    data = request.json
    
    contact_id = data.get('contact_id')
    outreach_type = data.get('outreach_type', 'call')
    notes = data.get('notes', '')
    
    if not contact_id:
        return jsonify({'success': False, 'error': 'Contact ID required'}), 400
    
    session = get_session()
    try:
        outreach = Outreach(
            contact_id=contact_id,
            outreach_type=outreach_type,
            message=notes
        )
        session.add(outreach)
        
        # Update contact touches
        contact = session.query(Contact).filter(Contact.id == contact_id).first()
        if contact:
            contact.total_touches = (contact.total_touches or 0) + 1
        
        session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
