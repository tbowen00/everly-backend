from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment (Railway sets this automatically)
DATABASE_URL = os.getenv('DATABASE_URL')

# Railway provides DATABASE_URL starting with postgres://
# But SQLAlchemy 1.4+ requires postgresql://
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Use PostgreSQL in production, SQLite locally
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///leads.db'

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_session():
    return SessionLocal()
