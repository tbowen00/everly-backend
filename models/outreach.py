from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import Base

class Outreach(Base):
    __tablename__ = 'outreach'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    
    outreach_type = Column(String(50), default='Email')  # Email, Call, Meeting, etc.
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=True)
    
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert outreach to dictionary"""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'outreach_type': self.outreach_type,
            'subject': self.subject,
            'message': self.message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }
