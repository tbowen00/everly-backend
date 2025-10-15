import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.contact import Contact
from models.outreach import Outreach
from models.campaign import Campaign
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import json

class AnalyticsService:
    
    @staticmethod
    def get_dashboard_stats():
        """Get overall dashboard statistics for lead gen"""
        session = get_session()
        try:
            # Total contacts
            total_contacts = session.query(func.count(Contact.id)).scalar()
            
            # By tier
            tier_breakdown = session.query(
                Contact.tier,
                func.count(Contact.id)
            ).group_by(Contact.tier).all()
            
            # By industry
            industry_breakdown = session.query(
                Contact.industry,
                func.count(Contact.id)
            ).group_by(Contact.industry).all()
            
            # By source
            source_breakdown = session.query(
                Contact.source,
                func.count(Contact.id)
            ).group_by(Contact.source).all()
            
            # Email availability
            with_email = session.query(func.count(Contact.id)).filter(
                Contact.email.isnot(None),
                Contact.email != ''
            ).scalar()
            
            # Contacted stats
            total_contacted = session.query(func.count(Contact.id)).filter(
                Contact.total_touches > 0
            ).scalar()
            
            total_replied = session.query(func.count(Contact.id)).filter(
                Contact.has_replied == 1
            ).scalar()
            
            total_converted = session.query(func.count(Contact.id)).filter(
                Contact.status == 'Converted'
            ).scalar()
            
            # Calculate rates
            reply_rate = (total_replied / total_contacted * 100) if total_contacted > 0 else 0
            conversion_rate = (total_converted / total_contacted * 100) if total_contacted > 0 else 0
            
            # Average website health by tier
            avg_health_by_tier = session.query(
                Contact.tier,
                func.avg(Contact.website_health_score)
            ).filter(Contact.website_health_score.isnot(None)).group_by(Contact.tier).all()
            
            # AI opportunity counts
            high_ai_opportunity = session.query(func.count(Contact.id)).filter(
                Contact.ai_opportunity_score > 60
            ).scalar()
            
            # Campaign stats
            active_campaigns = session.query(func.count(Campaign.id)).filter(
                Campaign.is_active == 1
            ).scalar()
            
            total_campaign_sends = session.query(func.sum(Campaign.total_sent)).scalar() or 0
            
            return {
                'total_contacts': total_contacts,
                'with_email': with_email,
                'email_percentage': round((with_email / total_contacts * 100) if total_contacts > 0 else 0, 1),
                'total_contacted': total_contacted,
                'total_replied': total_replied,
                'total_converted': total_converted,
                'reply_rate': round(reply_rate, 2),
                'conversion_rate': round(conversion_rate, 2),
                'tier_breakdown': dict(tier_breakdown),
                'industry_breakdown': dict(industry_breakdown),
                'source_breakdown': dict(source_breakdown),
                'avg_health_by_tier': dict(avg_health_by_tier),
                'high_ai_opportunity': high_ai_opportunity,
                'active_campaigns': active_campaigns,
                'total_campaign_sends': total_campaign_sends
            }
        finally:
            session.close()
    
    @staticmethod
    def get_industry_performance():
        """Get performance metrics by industry"""
        session = get_session()
        try:
            industries = session.query(Contact.industry).distinct().all()
            
            results = []
            for (industry,) in industries:
                if not industry:
                    continue
                
                total = session.query(func.count(Contact.id)).filter(
                    Contact.industry == industry
                ).scalar()
                
                contacted = session.query(func.count(Contact.id)).filter(
                    and_(Contact.industry == industry, Contact.total_touches > 0)
                ).scalar()
                
                replied = session.query(func.count(Contact.id)).filter(
                    and_(Contact.industry == industry, Contact.has_replied == 1)
                ).scalar()
                
                converted = session.query(func.count(Contact.id)).filter(
                    and_(Contact.industry == industry, Contact.status == 'Converted')
                ).scalar()
                
                reply_rate = (replied / contacted * 100) if contacted > 0 else 0
                conversion_rate = (converted / contacted * 100) if contacted > 0 else 0
                
                results.append({
                    'industry': industry,
                    'total': total,
                    'contacted': contacted,
                    'replied': replied,
                    'converted': converted,
                    'reply_rate': round(reply_rate, 2),
                    'conversion_rate': round(conversion_rate, 2)
                })
            
            # Sort by conversion rate
            results.sort(key=lambda x: x['conversion_rate'], reverse=True)
            
            return results
            
        finally:
            session.close()
    
    @staticmethod
    def get_source_performance():
        """Compare Google vs Yelp lead quality"""
        session = get_session()
        try:
            sources = ['google', 'yelp', 'manual']
            
            results = []
            for source in sources:
                total = session.query(func.count(Contact.id)).filter(
                    Contact.source == source
                ).scalar()
                
                if total == 0:
                    continue
                
                with_email = session.query(func.count(Contact.id)).filter(
                    and_(Contact.source == source, Contact.email.isnot(None), Contact.email != '')
                ).scalar()
                
                contacted = session.query(func.count(Contact.id)).filter(
                    and_(Contact.source == source, Contact.total_touches > 0)
                ).scalar()
                
                replied = session.query(func.count(Contact.id)).filter(
                    and_(Contact.source == source, Contact.has_replied == 1)
                ).scalar()
                
                avg_health = session.query(func.avg(Contact.website_health_score)).filter(
                    and_(Contact.source == source, Contact.website_health_score.isnot(None))
                ).scalar()
                
                results.append({
                    'source': source,
                    'total': total,
                    'with_email': with_email,
                    'email_rate': round((with_email / total * 100), 2),
                    'contacted': contacted,
                    'replied': replied,
                    'reply_rate': round((replied / contacted * 100) if contacted > 0 else 0, 2),
                    'avg_health_score': round(avg_health, 2) if avg_health else None
                })
            
            return results
            
        finally:
            session.close()
