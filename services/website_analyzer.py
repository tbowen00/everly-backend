import requests
from bs4 import BeautifulSoup
import time
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WebsiteAnalyzer:
    def __init__(self):
        self.timeout = 10
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; EverlyStudio/1.0; +https://everlystudio.com)'
        }
    
    def analyze_website(self, url):
        """
        Analyze a website and return health metrics + AI opportunities
        """
        if not url:
            return None
        
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = f'https://{url}'
        
        result = {
            'url': url,
            'health_score': 0,
            'has_https': False,
            'has_mobile_optimization': False,
            'page_load_speed': None,
            'has_forms': False,
            'has_appointments': False,
            'has_faq': False,
            'ai_opportunity_score': 0,
            'emails_found': []
        }
        
        try:
            # Time the request
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            load_time = time.time() - start_time
            
            result['page_load_speed'] = round(load_time, 2)
            
            # Check HTTPS
            result['has_https'] = response.url.startswith('https://')
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check mobile optimization
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            result['has_mobile_optimization'] = viewport is not None
            
            # Check for forms
            forms = soup.find_all('form')
            result['has_forms'] = len(forms) > 0
            
            # Check for appointment/booking keywords
            text_content = soup.get_text().lower()
            appointment_keywords = ['appointment', 'schedule', 'book', 'booking', 'calendar']
            result['has_appointments'] = any(keyword in text_content for keyword in appointment_keywords)
            
            # Check for FAQ
            faq_keywords = ['faq', 'frequently asked', 'questions']
            result['has_faq'] = any(keyword in text_content for keyword in faq_keywords)
            
            # Find emails
            result['emails_found'] = self._extract_emails(soup, response.text)
            
            # Calculate health score
            result['health_score'] = self._calculate_health_score(result, load_time)
            
            # Calculate AI opportunity score
            result['ai_opportunity_score'] = self._calculate_ai_score(result)
            
            return result
            
        except Exception as e:
            print(f"Error analyzing {url}: {str(e)}")
            return result
    
    def _extract_emails(self, soup, html_text):
        """Extract email addresses from page"""
        emails = set()
        
        # Find emails in mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            email = link['href'].replace('mailto:', '').split('?')[0]
            if self._is_valid_email(email):
                emails.add(email.lower())
        
        # Find emails in text with regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        found_emails = re.findall(email_pattern, html_text)
        for email in found_emails:
            if self._is_valid_email(email):
                emails.add(email.lower())
        
        return list(emails)[:3]  # Return max 3 emails
    
    def _is_valid_email(self, email):
        """Basic email validation"""
        if not email or '@' not in email:
            return False
        
        # Filter out common false positives
        bad_patterns = ['.png', '.jpg', '.jpeg', '.gif', '.css', '.js']
        return not any(pattern in email.lower() for pattern in bad_patterns)
    
    def _calculate_health_score(self, result, load_time):
        """Calculate website health score (0-100)"""
        score = 0
        
        # HTTPS (25 points)
        if result['has_https']:
            score += 25
        
        # Mobile optimization (25 points)
        if result['has_mobile_optimization']:
            score += 25
        
        # Load speed (25 points)
        if load_time < 2:
            score += 25
        elif load_time < 4:
            score += 15
        elif load_time < 6:
            score += 10
        
        # Has forms (15 points)
        if result['has_forms']:
            score += 15
        
        # Email found (10 points)
        if result['emails_found']:
            score += 10
        
        return min(score, 100)
    
    def _calculate_ai_score(self, result):
        """Calculate AI opportunity score (0-100)"""
        score = 0
        
        # Has forms (40 points)
        if result['has_forms']:
            score += 40
        
        # Has appointment/scheduling (40 points)
        if result['has_appointments']:
            score += 40
        
        # Has FAQ (20 points)
        if result['has_faq']:
            score += 20
        
        return min(score, 100)
    
    def check_contact_page(self, base_url):
        """Try to find and scrape contact page for additional emails"""
        contact_paths = ['/contact', '/contact-us', '/about', '/about-us']
        
        for path in contact_paths:
            try:
                url = base_url.rstrip('/') + path
                response = requests.get(url, headers=self.headers, timeout=5)
                
                if response.status_code == 200:
                    emails = self._extract_emails(BeautifulSoup(response.content, 'html.parser'), response.text)
                    if emails:
                        return emails
                        
            except:
                continue
        
        return []
