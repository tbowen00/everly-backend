import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.contact import Contact
from sqlalchemy import func

class DuplicateChecker:
    
    @staticmethod
    def check_email(email):
        """Check if email already exists in database"""
        session = get_session()
        try:
            contact = session.query(Contact).filter(
                func.lower(Contact.email) == func.lower(email)
            ).first()
            
            if contact:
                return {
                    'exists': True,
                    'contact': contact.to_dict()
                }
            return {'exists': False}
        finally:
            session.close()
    
    @staticmethod
    def check_similar_name(name):
        """Check for contacts with similar names"""
        session = get_session()
        try:
            # Simple similarity check - you can enhance this
            contacts = session.query(Contact).filter(
                func.lower(Contact.name).contains(func.lower(name))
            ).all()
            
            if contacts:
                return {
                    'found': True,
                    'contacts': [c.to_dict() for c in contacts]
                }
            return {'found': False}
        finally:
            session.close()
