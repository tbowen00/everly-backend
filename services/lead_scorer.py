import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LeadScorer:
    
    @staticmethod
    def score_lead(contact_data):
        """
        Score a lead and assign tier (High/Medium/Low)
        Returns: tier (str) and tags (list)
        """
        score = 0
        tags = []
        
        # Website analysis
        if not contact_data.get('website_url'):
            score += 30
            tags.append('no-website')
        else:
            health_score = contact_data.get('website_health_score', 0)
            
            if health_score < 40:
                score += 25
                tags.append('poor-website')
            elif health_score < 70:
                score += 15
                tags.append('needs-improvement')
            
            if not contact_data.get('has_https'):
                score += 10
                tags.append('no-https')
            
            if not contact_data.get('has_mobile_optimization'):
                score += 10
                tags.append('no-mobile')
            
            if contact_data.get('page_load_speed', 0) > 4:
                score += 10
                tags.append('slow-site')
        
        # AI opportunity signals
        ai_score = contact_data.get('ai_opportunity_score', 0)
        if ai_score > 60:
            score += 20
            tags.append('ai-opportunity')
        elif ai_score > 30:
            score += 10
            tags.append('ai-potential')
        
        # Email availability
        if contact_data.get('email'):
            score += 15
            tags.append('has-email')
        else:
            tags.append('no-email')
        
        # Add source tag
        if contact_data.get('source'):
            tags.append(f"source:{contact_data['source']}")
        
        # Add industry tag
        if contact_data.get('industry'):
            tags.append(f"industry:{contact_data['industry']}")
        
        # Always add local-smb tag
        tags.append('local-smb')
        
        # Determine tier
        if score >= 60:
            tier = 'High'
        elif score >= 30:
            tier = 'Medium'
        else:
            tier = 'Low'
        
        return tier, tags
    
    @staticmethod
    def normalize_industry(raw_industry, source):
        """
        Normalize industry names across sources
        """
        industry_map = {
            'healthcare': ['healthcare', 'health', 'medical', 'dental', 'dentist', 'doctor', 'physician', 'vet', 'veterinary'],
            'home_services': ['home_services', 'contractor', 'construction', 'plumbing', 'roofing', 'electrician', 'hvac'],
            'food': ['food', 'restaurant', 'cafe', 'bakery', 'catering'],
            'legal': ['legal', 'lawyer', 'attorney', 'law', 'accounting'],
            'wellness': ['wellness', 'spa', 'gym', 'fitness', 'salon', 'beauty'],
            'retail': ['retail', 'store', 'shop', 'boutique'],
        }
        
        if not raw_industry:
            return 'other'
        
        raw_lower = raw_industry.lower()
        
        for normalized, keywords in industry_map.items():
            if any(keyword in raw_lower for keyword in keywords):
                return normalized
        
        return 'other'
