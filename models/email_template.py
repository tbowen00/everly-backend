from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from database.connection import Base

class EmailTemplate(Base):
    __tablename__ = 'email_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    subject_line = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    category = Column(String(100))  # 'ai_services', 'web_design', 'consultation', etc.
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject_line': self.subject_line,
            'body': self.body,
            'is_default': self.is_default,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
