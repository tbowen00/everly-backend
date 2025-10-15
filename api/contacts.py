from flask import Blueprint, request, jsonify
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.contact import Contact
from models.outreach import Outreach
from models.note import Note
from sqlalchemy import or_, func

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts with optional filters"""
    session = get_session()
    
    try:
        query = session.query(Contact)
        
        # Apply filters
        if request.args.get('status'):
            query = query.filter(Contact.status == request.args.get('status'))
        
        if request.args.get('industry'):
            query = query.filter(Contact.industry == request.args.get('industry'))
        
        if request.args.get('tier'):
            query = query.filter(Contact.tier == request.args.get('tier'))
        
        if request.args.get('source'):
            query = query.filter(Contact.source == request.args.get('source'))
        
        if request.args.get('search'):
            search = f"%{request.args.get('search')}%"
            query = query.filter(or_(
                Contact.name.like(search),
                Contact.company.like(search),
                Contact.email.like(search)
            ))
        
        contacts = query.order_by(Contact.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'contacts': [contact.to_dict() for contact in contacts],
            'count': len(contacts)
        })
    finally:
        session.close()

@contacts_bp.route('/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get a single contact with full details"""
    session = get_session()
    
    try:
        contact = session.query(Contact).filter(Contact.id == contact_id).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        outreach_history = session.query(Outreach).filter(
            Outreach.contact_id == contact_id
        ).order_by(Outreach.sent_at.desc()).all()
        
        notes = session.query(Note).filter(
            Note.contact_id == contact_id
        ).order_by(Note.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict(),
            'outreach_history': [o.to_dict() for o in outreach_history],
            'notes': [n.to_dict() for n in notes]
        })
    finally:
        session.close()

@contacts_bp.route('/contacts', methods=['POST'])
def create_contact():
    """Create a new contact"""
    session = get_session()
    
    try:
        data = request.json
        
        contact = Contact(
            name=data.get('name'),
            company=data.get('company'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            website_url=data.get('website_url'),
            industry=data.get('industry'),
            status=data.get('status', 'Lead'),
            source=data.get('source', 'manual')
        )
        
        session.add(contact)
        session.commit()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict()
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@contacts_bp.route('/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Update a contact"""
    session = get_session()
    
    try:
        contact = session.query(Contact).filter(Contact.id == contact_id).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        data = request.json
        
        for key, value in data.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict()
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@contacts_bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete a contact"""
    session = get_session()
    
    try:
        contact = session.query(Contact).filter(Contact.id == contact_id).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Delete associated records
        session.query(Outreach).filter(Outreach.contact_id == contact_id).delete()
        session.query(Note).filter(Note.contact_id == contact_id).delete()
        
        session.delete(contact)
        session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@contacts_bp.route('/contacts/<int:contact_id>/notes', methods=['POST'])
def add_note(contact_id):
    """Add a note to a contact"""
    session = get_session()
    
    try:
        data = request.json
        
        note = Note(
            contact_id=contact_id,
            content=data.get('content')
        )
        
        session.add(note)
        session.commit()
        
        return jsonify({
            'success': True,
            'note': note.to_dict()
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@contacts_bp.route('/contacts/bulk-delete', methods=['POST'])
def bulk_delete_contacts():
    """Delete multiple contacts"""
    session = get_session()
    
    try:
        data = request.json
        contact_ids = data.get('contact_ids', [])
        
        if not contact_ids:
            return jsonify({'success': False, 'error': 'No contacts specified'}), 400
        
        # Delete associated records
        session.query(Outreach).filter(Outreach.contact_id.in_(contact_ids)).delete(synchronize_session=False)
        session.query(Note).filter(Note.contact_id.in_(contact_ids)).delete(synchronize_session=False)
        
        # Delete contacts
        deleted = session.query(Contact).filter(Contact.id.in_(contact_ids)).delete(synchronize_session=False)
        session.commit()
        
        return jsonify({
            'success': True,
            'deleted': deleted
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@contacts_bp.route('/contacts/delete-all', methods=['DELETE'])
def delete_all_contacts():
    """Delete ALL contacts"""
    session = get_session()
    
    try:
        # Delete all associated records
        session.query(Outreach).delete()
        session.query(Note).delete()
        
        # Delete all contacts
        deleted = session.query(Contact).delete()
        session.commit()
        
        print(f"⚠️  Deleted ALL contacts: {deleted} total", flush=True)
        
        return jsonify({
            'success': True,
            'deleted': deleted
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@contacts_bp.route('/contacts/check-duplicate', methods=['POST'])
def check_duplicate():
    """Check if contact with email already exists"""
    session = get_session()
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'is_duplicate': False})
        
        existing = session.query(Contact).filter(Contact.email == email).first()
        
        if existing:
            return jsonify({
                'is_duplicate': True,
                'contact': existing.to_dict()
            })
        
        return jsonify({'is_duplicate': False})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
