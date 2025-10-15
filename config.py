import os
from dotenv import load_dotenv

load_dotenv()

# Server config
DEBUG = os.getenv('DEBUG', 'True') == 'True'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5001))

# Database - use PostgreSQL in production, SQLite locally
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Email config
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL')
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'Everly Studio')

# Job categories for lead discovery
JOB_CATEGORIES = [
    'healthcare', 'home_services', 'food', 'legal', 
    'wellness', 'retail', 'construction', 'automotive'
]

# Contact statuses
CONTACT_STATUSES = [
    'Lead', 'Contacted', 'Replied', 'Qualified', 
    'Converted', 'Not Interested'
]

# API Keys for lead discovery
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
YELP_API_KEY = os.getenv('YELP_API_KEY', '')
