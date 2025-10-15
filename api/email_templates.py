from flask import Blueprint, request, jsonify
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.email_template import EmailTemplate

templates_bp = Blueprint('email_templates', __name__)

@templates_bp.route('/email-templates', methods=['GET'])
def get_templates():
    """Get all email templates"""
    session = get_session()
    try:
        templates = session.query(EmailTemplate).order_by(EmailTemplate.is_default.desc(), EmailTemplate.name).all()
        return jsonify({
            'success': True,
            'templates': [t.to_dict() for t in templates]
        })
    finally:
        session.close()

@templates_bp.route('/email-templates', methods=['POST'])
def create_template():
    """Create new email template"""
    session = get_session()
    try:
        data = request.json
        
        template = EmailTemplate(
            name=data['name'],
            subject_line=data['subject_line'],
            body=data['body'],
            is_default=data.get('is_default', False),
            category=data.get('category', 'custom')
        )
        
        session.add(template)
        session.commit()
        
        return jsonify({
            'success': True,
            'template': template.to_dict()
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@templates_bp.route('/email-templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """Update email template"""
    session = get_session()
    try:
        template = session.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        data = request.json
        template.name = data.get('name', template.name)
        template.subject_line = data.get('subject_line', template.subject_line)
        template.body = data.get('body', template.body)
        template.category = data.get('category', template.category)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'template': template.to_dict()
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@templates_bp.route('/email-templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete email template"""
    session = get_session()
    try:
        template = session.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        if template.is_default:
            return jsonify({'success': False, 'error': 'Cannot delete default templates'}), 400
        
        session.delete(template)
        session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@templates_bp.route('/email-templates/seed', methods=['POST'])
def seed_default_templates():
    """Seed default templates"""
    session = get_session()
    try:
        # Check if defaults already exist
        existing = session.query(EmailTemplate).filter(EmailTemplate.is_default == True).count()
        if existing > 0:
            return jsonify({'success': True, 'message': 'Default templates already exist'})
        
        defaults = [
            {
                'name': 'AI Services - Cold Outreach',
                'subject_line': 'Transform {{company}} with AI',
                'body': '''Hi {{name}},

I noticed {{company}} and wanted to reach out with a quick opportunity.

We're Everly Studio, and we specialize in AI-powered solutions for businesses in the {{industry}} industry. We help companies like yours:

- Automate repetitive tasks
- Improve customer experience with AI chatbots
- Modernize websites with intelligent features

Would you be open to a quick 15-minute call this week to discuss how AI could benefit {{company}}?

Best regards,
Brooklyn Lanning
Everly Studio
hello@everlystudio.co''',
                'is_default': True,
                'category': 'ai_services'
            },
            {
                'name': 'Website Redesign Offer',
                'subject_line': 'Free Website Analysis for {{company}}',
                'body': '''Hi {{name}},

I came across {{company}} and wanted to reach out about your online presence.

As a web design agency, we're offering FREE website analysis for local {{industry}} businesses. We'll review:

✓ Mobile responsiveness
✓ Page speed & SEO
✓ User experience
✓ Conversion optimization

No strings attached - just want to help {{company}} succeed online.

Interested in a free 20-minute review?

Best,
Brooklyn Lanning
Everly Studio
hello@everlystudio.co''',
                'is_default': True,
                'category': 'web_design'
            },
            {
                'name': 'Free Consultation',
                'subject_line': 'Quick question about {{company}}',
                'body': '''Hi {{name}},

Hope you're doing well! I wanted to reach out because I think {{company}} could benefit from some digital upgrades.

We're offering free 30-minute consultations where we:

- Review your current online presence
- Identify growth opportunities
- Share actionable recommendations (no pitch!)

Would next week work for a quick call?

Cheers,
Brooklyn Lanning
Everly Studio
hello@everlystudio.co''',
                'is_default': True,
                'category': 'consultation'
            }
        ]
        
        for template_data in defaults:
            template = EmailTemplate(**template_data)
            session.add(template)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Created {len(defaults)} default templates'
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
