import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.email_template import EmailTemplate

def fix():
    session = get_session()
    try:
        # Update all templates
        templates = session.query(EmailTemplate).all()
        for t in templates:
            t.body = t.body.replace('Brooklyn Lanning', 'Tyler Bowen')
            t.is_default = False  # Make them editable
        session.commit()
        print(f"✓ Fixed {len(templates)} templates - now editable")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    fix()
