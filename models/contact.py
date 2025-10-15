from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import Base

class Contact(Base):
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic Info
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    
    # Location
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    
    # Website & Analysis
    website_url = Column(String(500), nullable=True)
    website_health_score = Column(Float, nullable=True)  # 0-100
    has_mobile_optimization = Column(Integer, default=0)  # 0 = No, 1 = Yes
    has_https = Column(Integer, default=0)
    page_load_speed = Column(Float, nullable=True)  # seconds
    
    # Lead Generation Fields
    source = Column(String(50), nullable=True)  # google, yelp, manual
    industry = Column(String(100), nullable=True)
    job_category = Column(String(100), nullable=True)
    tier = Column(String(20), nullable=True)  # High, Medium, Low
    tags = Column(Text, nullable=True)  # JSON array of tags
    
    # AI Opportunity Signals
    has_forms = Column(Integer, default=0)
    has_appointments = Column(Integer, default=0)
    has_faq = Column(Integer, default=0)
    ai_opportunity_score = Column(Float, nullable=True)  # 0-100
    
    # Status & Tracking
    status = Column(String(50), default='Lead')
    total_touches = Column(Integer, default=0)
    last_contacted = Column(DateTime, nullable=True)
    last_reply_date = Column(DateTime, nullable=True)
    has_replied = Column(Integer, default=0)
    
    # Enrichment Status
    is_enriched = Column(Integer, default=0)
    enriched_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert contact to dictionary"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'job_title': self.job_title,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'website_url': self.website_url,
            'website_health_score': self.website_health_score,
            'has_mobile_optimization': bool(self.has_mobile_optimization),
            'has_https': bool(self.has_https),
            'page_load_speed': self.page_load_speed,
            'source': self.source,
            'industry': self.industry,
            'job_category': self.job_category,
            'tier': self.tier,
            'tags': json.loads(self.tags) if self.tags else [],
            'has_forms': bool(self.has_forms),
            'has_appointments': bool(self.has_appointments),
            'has_faq': bool(self.has_faq),
            'ai_opportunity_score': self.ai_opportunity_score,
            'status': self.status,
            'total_touches': self.total_touches,
            'last_contacted': self.last_contacted.isoformat() if self.last_contacted else None,
            'last_reply_date': self.last_reply_date.isoformat() if self.last_reply_date else None,
            'has_replied': bool(self.has_replied),
            'is_enriched': bool(self.is_enriched),
            'enriched_at': self.enriched_at.isoformat() if self.enriched_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
