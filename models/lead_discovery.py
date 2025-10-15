from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import Base

class LeadDiscovery(Base):
    __tablename__ = 'lead_discoveries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Job Info
    job_name = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)  # google, yelp
    
    # Parameters
    location = Column(String(255), nullable=True)
    radius_miles = Column(Integer, nullable=True)
    industries = Column(Text, nullable=True)  # JSON array
    
    # Results
    total_found = Column(Integer, default=0)
    total_imported = Column(Integer, default=0)
    total_duplicates = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'job_name': self.job_name,
            'source': self.source,
            'location': self.location,
            'radius_miles': self.radius_miles,
            'industries': json.loads(self.industries) if self.industries else [],
            'total_found': self.total_found,
            'total_imported': self.total_imported,
            'total_duplicates': self.total_duplicates,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
