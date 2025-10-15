import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, Base
from models.contact import Contact
from models.outreach import Outreach
from models.note import Note
from models.campaign import Campaign
from models.lead_discovery import LeadDiscovery
from config import DATABASE_PATH

def init_database():
    """Initialize the database and create all tables"""
    data_dir = Path(DATABASE_PATH).parent
    data_dir.mkdir(exist_ok=True)
    
    Base.metadata.create_all(engine)
    print(f"Database initialized at: {DATABASE_PATH}")
    print("Tables created successfully!")
    print("- contacts")
    print("- outreach")
    print("- notes")
    print("- campaigns")
    print("- lead_discoveries")

if __name__ == "__main__":
    init_database()
