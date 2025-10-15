import sys
import os
import json
import csv
import io
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.contact import Contact
from models.campaign import Campaign
from models.outreach import Outreach

class CampaignService:
    
    @staticmethod
    def create_campaign(name, subject_lines, email_body, target_industries, target_tiers, target_sources, daily_limit):
        """Create a new email campaign"""
        session = get_session()
        try:
            campaign = Campaign(
                name=name,
                subject_lines=json.dumps(subject_lines),
                email_body=email_body,
                target_industries=json.dumps(target_industries),
                target_tiers=json.dumps(target_tiers),
                target_sources=json.dumps(target_sources),
                daily_limit=daily_limit
            )
            session.add(campaign)
            session.commit()
            return {'success': True, 'campaign': campaign.to_dict()}
        except Exception as e:
            session.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            session.close()
    
    @staticmethod
    def get_campaign_recipients(campaign_id):
        """Get list of contacts that match campaign criteria"""
        session = get_session()
        try:
            campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                return {'success': False, 'error': 'Campaign not found'}
            
            # Parse targeting criteria
            target_industries = json.loads(campaign.target_industries) if campaign.target_industries else []
            target_tiers = json.loads(campaign.target_tiers) if campaign.target_tiers else []
            target_sources = json.loads(campaign.target_sources) if campaign.target_sources else []
            
            # Build query
            query = session.query(Contact).filter(
                Contact.email.isnot(None),
                Contact.email != ''
            )
            
            # Apply filters
            if target_industries:
                query = query.filter(Contact.industry.in_(target_industries))
            
            if target_tiers:
                query = query.filter(Contact.tier.in_(target_tiers))
            
            if target_sources:
                query = query.filter(Contact.source.in_(target_sources))
            
            # Exclude already contacted in this campaign
            # (For now, exclude anyone contacted in last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(
                (Contact.last_contacted.is_(None)) | 
                (Contact.last_contacted < seven_days_ago)
            )
            
            contacts = query.all()
            
            return {
                'success': True,
                'recipients': [c.to_dict() for c in contacts],
                'count': len(contacts)
            }
            
        finally:
            session.close()
    
    @staticmethod
    def generate_preview_csv(campaign_id):
        """Generate preview CSV of campaign recipients and emails"""
        session = get_session()
        try:
            campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                return {'success': False, 'error': 'Campaign not found'}
            
            recipients_result = CampaignService.get_campaign_recipients(campaign_id)
            if not recipients_result['success']:
                return recipients_result
            
            recipients = recipients_result['recipients']
            subject_lines = json.loads(campaign.subject_lines)
            
            # Generate CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'contact_id', 'name', 'email', 'company', 'industry', 'tier', 
                'website', 'subject', 'preview'
            ])
            writer.writeheader()
            
            for i, contact in enumerate(recipients):
                # Rotate subject lines
                subject = subject_lines[i % len(subject_lines)]
                
                # Personalize email
                personalized_subject = CampaignService.personalize_email(subject, contact)
                personalized_body = CampaignService.personalize_email(campaign.email_body, contact)
                
                writer.writerow({
                    'contact_id': contact['id'],
                    'name': contact['name'],
                    'email': contact['email'],
                    'company': contact['company'],
                    'industry': contact['industry'],
                    'tier': contact['tier'],
                    'website': contact['website_url'],
                    'subject': personalized_subject,
                    'preview': personalized_body[:100] + '...'
                })
            
            csv_content = output.getvalue()
            output.close()
            
            return {
                'success': True,
                'csv_content': csv_content,
                'total_recipients': len(recipients)
            }
            
        finally:
            session.close()
    
    @staticmethod
    def personalize_email(template, contact):
        """Replace placeholders in email template with contact data"""
        replacements = {
            '{{Business}}': contact.get('name', 'your business'),
            '{{Name}}': contact.get('name', 'there'),
            '{{Company}}': contact.get('company', 'your company'),
            '{{Industry}}': contact.get('industry', 'your industry'),
        }
        
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result
    
    @staticmethod
    def send_campaign_batch(campaign_id, batch_size=None, preview_mode=True):
        """Send a batch of campaign emails"""
        session = get_session()
        try:
            campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                return {'success': False, 'error': 'Campaign not found'}
            
            # Get recipients
            recipients_result = CampaignService.get_campaign_recipients(campaign_id)
            if not recipients_result['success']:
                return recipients_result
            
            recipients = recipients_result['recipients']
            subject_lines = json.loads(campaign.subject_lines)
            
            # Limit batch size
            batch_limit = batch_size or campaign.daily_limit
            batch = recipients[:batch_limit]
            
            if preview_mode:
                return {
                    'success': True,
                    'preview_mode': True,
                    'message': 'Preview mode: emails not sent',
                    'would_send_to': len(batch)
                }
            
            # Actually send emails
            sent_count = 0
            for i, contact_data in enumerate(batch):
                contact = session.query(Contact).filter(Contact.id == contact_data['id']).first()
                if not contact:
                    continue
                
                # Rotate subject lines
                subject = subject_lines[i % len(subject_lines)]
                
                # Personalize
                personalized_subject = CampaignService.personalize_email(subject, contact_data)
                personalized_body = CampaignService.personalize_email(campaign.email_body, contact_data)
                
                # Log outreach
                outreach = Outreach(
                    contact_id=contact.id,
                    outreach_type='Email',
                    subject=personalized_subject,
                    message=personalized_body,
                    sent_at=datetime.utcnow()
                )
                session.add(outreach)
                
                # Update contact
                contact.total_touches += 1
                contact.last_contacted = datetime.utcnow()
                
                sent_count += 1
            
            # Update campaign stats
            campaign.total_sent += sent_count
            if not campaign.started_at:
                campaign.started_at = datetime.utcnow()
            
            session.commit()
            
            return {
                'success': True,
                'sent': sent_count,
                'message': f'Sent {sent_count} emails'
            }
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'error': str(e)}
        
        finally:
            session.close()
