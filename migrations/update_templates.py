import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.email_template import EmailTemplate

def update():
    session = get_session()
    try:
        templates = session.query(EmailTemplate).all()
        for template in templates:
            template.body = template.body.replace('Brooklyn Lanning', 'Tyler Bowen')
        session.commit()
        print(f"✓ Updated {len(templates)} templates")
    finally:
        session.close()

if __name__ == '__main__':
    update()
