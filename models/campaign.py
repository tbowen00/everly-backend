from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import Base

class Campaign(Base):
    __tablename__ = 'campaigns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    
    # Campaign Settings
    subject_lines = Column(Text, nullable=True)  # JSON array
    email_body = Column(Text, nullable=True)
    
    # Targeting
    target_industries = Column(Text, nullable=True)  # JSON array
    target_tiers = Column(Text, nullable=True)  # JSON array
    target_sources = Column(Text, nullable=True)  # JSON array
    
    # Schedule
    daily_limit = Column(Integer, default=30)
    is_active = Column(Integer, default=0)
    
    # Stats
    total_sent = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_replied = Column(Integer, default=0)
    total_converted = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'subject_lines': json.loads(self.subject_lines) if self.subject_lines else [],
            'email_body': self.email_body,
            'target_industries': json.loads(self.target_industries) if self.target_industries else [],
            'target_tiers': json.loads(self.target_tiers) if self.target_tiers else [],
            'target_sources': json.loads(self.target_sources) if self.target_sources else [],
            'daily_limit': self.daily_limit,
            'is_active': bool(self.is_active),
            'total_sent': self.total_sent,
            'total_opened': self.total_opened,
            'total_replied': self.total_replied,
            'total_converted': self.total_converted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
