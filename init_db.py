"""Initialize database tables"""
from database.connection import Base, engine
from models.contact import Contact
from models.campaign import Campaign
from models.outreach import Outreach

print("Creating database tables...")
Base.metadata.create_all(engine)
print("✓ Database tables created successfully!")
