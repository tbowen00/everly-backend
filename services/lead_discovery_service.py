import sys
import os
import json
import time
import re
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.contact import Contact
from models.lead_discovery import LeadDiscovery
from scraper.google_places import GooglePlacesScraper
from services.website_analyzer import WebsiteAnalyzer
from services.lead_scorer import LeadScorer

class LeadDiscoveryService:
    
    # Patterns for invalid/tracking emails
    INVALID_EMAIL_PATTERNS = [
        r'user@',
        r'email@',
        r'@domain\.com',
        r'@example\.com',
        r'@sentry\.io',
        r'@segment\.com',
        r'@amplitude\.com',
        r'@mixpanel\.com',
        r'noreply@',
        r'no-reply@',
        r'^[a-f0-9]{32}@',  # MD5 hashes
        r'^[a-f0-9]{40}@',  # SHA1 hashes
    ]
    
    def __init__(self, google_api_key=None, yelp_api_key=None, progress_callback=None):
        self.google_api_key = google_api_key
        self.yelp_api_key = yelp_api_key
        self.website_analyzer = WebsiteAnalyzer()
        self.lead_scorer = LeadScorer()
        self.progress_callback = progress_callback
        
        print(f"LeadDiscoveryService - Google Key: {'SET (' + google_api_key[:20] + '...)' if google_api_key else 'NOT SET'}", flush=True)
    
    def is_valid_email(self, email):
        """Check if email is valid and not a tracking/monitoring email"""
        if not email or '@' not in email:
            return False
        
        email_lower = email.lower()
        
        # Check against invalid patterns
        for pattern in self.INVALID_EMAIL_PATTERNS:
            if re.search(pattern, email_lower):
                return False
        
        return True
    
    def report_progress(self, message, step=None, total=None):
        """Report progress to callback and console"""
        print(message, flush=True)
        if self.progress_callback:
            self.progress_callback(message, step, total)
    
    def create_discovery_job(self, job_name, source, location, radius_miles, industries):
        """Create a new lead discovery job"""
        session = get_session()
        try:
            job = LeadDiscovery(
                job_name=job_name,
                source=source,
                location=location,
                radius_miles=radius_miles,
                industries=json.dumps(industries),
                status='pending'
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            job_dict = job.to_dict()
            print(f"✓ Created job: {job_name} (ID: {job.id})", flush=True)
            return job_dict
        finally:
            session.close()
    
    def run_discovery_job(self, job_id):
        """Execute a lead discovery job with automatic enrichment"""
        session = get_session()
        
        try:
            job = session.query(LeadDiscovery).filter(LeadDiscovery.id == job_id).first()
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            self.report_progress(f"Starting job: {job.job_name}")
            
            job.status = 'running'
            job.started_at = datetime.utcnow()
            session.commit()
            
            industries = json.loads(job.industries) if job.industries else []
            
            raw_leads = []
            
            if job.source == 'google':
                if not self.google_api_key:
                    error_msg = 'Google API key not configured'
                    self.report_progress(f"Error: {error_msg}")
                    job.status = 'failed'
                    job.error_message = error_msg
                    session.commit()
                    return {'success': False, 'error': error_msg}
                
                self.report_progress("Searching Google Places...")
                scraper = GooglePlacesScraper(self.google_api_key)
                
                results = scraper.search_nearby(
                    location=job.location,
                    radius_miles=job.radius_miles,
                    industry_keywords=industries
                )
                
                self.report_progress(f"Found {len(results)} businesses")
                
                for i, place in enumerate(results):
                    self.report_progress(f"Fetching details: {place.get('name', 'Unknown')}", i+1, len(results))
                    details = scraper.get_place_details(place['place_id'])
                    lead = scraper.format_lead(place, details)
                    if lead:
                        raw_leads.append(lead)
                    time.sleep(0.3)
            
            else:
                error_msg = 'Yelp not configured'
                job.status = 'failed'
                job.error_message = error_msg
                session.commit()
                return {'success': False, 'error': error_msg}
            
            job.total_found = len(raw_leads)
            
            imported = 0
            duplicates = 0
            
            self.report_progress(f"Importing and analyzing {len(raw_leads)} leads...")
            
            for i, lead_data in enumerate(raw_leads):
                self.report_progress(f"Processing: {lead_data.get('name')}", i+1, len(raw_leads))
                
                result = self.import_lead(lead_data)
                
                if result['imported']:
                    imported += 1
                    contact_id = result['contact_id']
                    
                    # Enrich immediately
                    enrich_result = self.enrich_lead(contact_id)
                    
                    if enrich_result['success']:
                        contact = enrich_result['contact']
                        tier = contact.get('tier', 'N/A')
                        email = contact.get('email', 'No email')
                        self.report_progress(f"✓ {lead_data.get('name')}: {tier} tier, {email}")
                else:
                    duplicates += 1
            
            # Update job with final stats
            job.total_imported = imported
            job.total_duplicates = duplicates
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            
            session.commit()
            session.close()
            
            # Get fresh job data
            fresh_session = get_session()
            try:
                final_job = fresh_session.query(LeadDiscovery).filter(LeadDiscovery.id == job_id).first()
                job_dict = final_job.to_dict()
                self.report_progress(f"Complete! Imported {imported} leads, {duplicates} duplicates")
                print(f"✅ Job completed: {job_dict['status']}", flush=True)
            finally:
                fresh_session.close()
            
            return {
                'success': True,
                'job': job_dict
            }
            
        except Exception as e:
            self.report_progress(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            try:
                job.status = 'failed'
                job.error_message = str(e)
                session.commit()
            except:
                pass
            
            return {'success': False, 'error': str(e)}
        
        finally:
            if session:
                session.close()
    
    def import_lead(self, lead_data):
        """Import a single lead"""
        session = get_session()
        
        try:
            existing = None
            if lead_data.get('email'):
                existing = session.query(Contact).filter(
                    Contact.email == lead_data['email']
                ).first()
            
            if not existing and lead_data.get('phone'):
                existing = session.query(Contact).filter(
                    Contact.phone == lead_data['phone']
                ).first()
            
            if existing:
                return {'imported': False, 'reason': 'duplicate', 'contact_id': existing.id}
            
            contact = Contact(
                name=lead_data.get('name'),
                company=lead_data.get('company'),
                email=lead_data.get('email'),
                phone=lead_data.get('phone'),
                address=lead_data.get('address'),
                city=lead_data.get('city'),
                state=lead_data.get('state'),
                zip_code=lead_data.get('zip_code'),
                website_url=lead_data.get('website_url'),
                source=lead_data.get('source'),
                industry=self.lead_scorer.normalize_industry(lead_data.get('industry'), lead_data.get('source')),
                status='Lead'
            )
            
            session.add(contact)
            session.commit()
            
            contact_id = contact.id
            
            return {'imported': True, 'contact_id': contact_id}
            
        except Exception as e:
            session.rollback()
            return {'imported': False, 'reason': str(e)}
        
        finally:
            session.close()
    
    def enrich_lead(self, contact_id):
        """Enrich a lead with website analysis"""
        session = get_session()
        
        try:
            contact = session.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                return {'success': False, 'error': 'Contact not found'}
            
            if contact.website_url:
                try:
                    analysis = self.website_analyzer.analyze_website(contact.website_url)
                    
                    if analysis:
                        contact.website_health_score = analysis['health_score']
                        contact.has_https = 1 if analysis['has_https'] else 0
                        contact.has_mobile_optimization = 1 if analysis['has_mobile_optimization'] else 0
                        contact.page_load_speed = analysis['page_load_speed']
                        contact.has_forms = 1 if analysis['has_forms'] else 0
                        contact.has_appointments = 1 if analysis['has_appointments'] else 0
                        contact.has_faq = 1 if analysis['has_faq'] else 0
                        contact.ai_opportunity_score = analysis['ai_opportunity_score']
                        
                        # Filter valid emails
                        if analysis['emails_found']:
                            valid_emails = [e for e in analysis['emails_found'] if self.is_valid_email(e)]
                            if valid_emails and not contact.email:
                                contact.email = valid_emails[0]
                        
                        if not contact.email:
                            contact_emails = self.website_analyzer.check_contact_page(contact.website_url)
                            if contact_emails:
                                valid_emails = [e for e in contact_emails if self.is_valid_email(e)]
                                if valid_emails:
                                    contact.email = valid_emails[0]
                except Exception as e:
                    pass  # Silent fail for enrichment errors
            
            # If email is still invalid, clear it
            if contact.email and not self.is_valid_email(contact.email):
                contact.email = None
            
            tier, tags = self.lead_scorer.score_lead(contact.to_dict())
            contact.tier = tier
            contact.tags = json.dumps(tags)
            
            contact.is_enriched = 1
            contact.enriched_at = datetime.utcnow()
            
            session.commit()
            session.refresh(contact)
            
            contact_dict = contact.to_dict()
            
            return {'success': True, 'contact': contact_dict}
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'error': str(e)}
        
        finally:
            session.close()
    
    def bulk_enrich(self, batch_size=10):
        """Enrich multiple unenriched leads"""
        session = get_session()
        
        try:
            unenriched = session.query(Contact).filter(
                Contact.is_enriched == 0
            ).limit(batch_size).all()
            
            if len(unenriched) == 0:
                return {
                    'success': True,
                    'enriched': 0,
                    'failed': 0
                }
            
            enriched_count = 0
            failed_count = 0
            
            for contact in unenriched:
                try:
                    result = self.enrich_lead(contact.id)
                    if result['success']:
                        enriched_count += 1
                    else:
                        failed_count += 1
                except:
                    failed_count += 1
            
            return {
                'success': True,
                'enriched': enriched_count,
                'failed': failed_count
            }
            
        finally:
            session.close()
