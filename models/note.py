from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import Base

class Note(Base):
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert note to dictionary"""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
