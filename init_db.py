"""Initialize database tables"""
from database.connection import Base, engine
from models.contact import Contact
from models.campaign import Campaign
from models.outreach import Outreach
from models.lead_discovery import LeadDiscovery
from models.email_template import EmailTemplate
from models.note import Note

print("Creating database tables...")
Base.metadata.create_all(engine)
print("✓ Database tables created successfully!")
