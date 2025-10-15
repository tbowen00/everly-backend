from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URI

# Create engine
engine = create_engine(DATABASE_URI, echo=False)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Base class for models
Base = declarative_base()

def get_session():
    """Get a new database session"""
    return Session()

def close_session():
    """Close the current session"""
    Session.remove()
