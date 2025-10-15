import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, Base
from models.email_template import EmailTemplate

def migrate():
    print("Creating email_templates table...")
    Base.metadata.create_all(engine, tables=[EmailTemplate.__table__])
    print("✓ email_templates table created")

if __name__ == '__main__':
    migrate()
