import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class YelpScraper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.yelp.com/v3"
        self.headers = {'Authorization': f'Bearer {api_key}'}
    
    def search_businesses(self, location, radius_miles=10, categories=None, limit=50):
        """
        Search for businesses on Yelp
        location: "Oklahoma City, OK"
        radius_miles: search radius (max 25 miles)
        categories: list of category aliases
        """
        url = f"{self.base_url}/businesses/search"
        
        # Convert miles to meters (Yelp uses meters, max 40000)
        radius_meters = min(int(radius_miles * 1609.34), 40000)
        
        params = {
            'location': location,
            'radius': radius_meters,
            'limit': min(limit, 50),  # Yelp max is 50 per request
            'sort_by': 'best_match'
        }
        
        if categories:
            params['categories'] = ','.join(categories)
        
        all_results = []
        offset = 0
        
        while offset < limit:
            params['offset'] = offset
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                break
            
            data = response.json()
            businesses = data.get('businesses', [])
            
            if not businesses:
                break
            
            all_results.extend(businesses)
            offset += len(businesses)
            
            if len(businesses) < 50:  # No more results
                break
        
        return all_results
    
    def get_business_details(self, business_id):
        """Get detailed info about a business"""
        url = f"{self.base_url}/businesses/{business_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        
        return {}
    
    def format_lead(self, business_data):
        """Format Yelp data into lead structure"""
        location = business_data.get('location', {})
        
        return {
            'name': business_data.get('name'),
            'address': location.get('address1'),
            'city': location.get('city'),
            'state': location.get('state'),
            'zip_code': location.get('zip_code'),
            'phone': business_data.get('phone'),
            'website': business_data.get('url'),  # This is Yelp URL, not actual website
            'source': 'yelp',
            'industry': self._categorize_industry(business_data.get('categories', [])),
            'rating': business_data.get('rating')
        }
    
    def _categorize_industry(self, categories):
        """Map Yelp categories to our industries"""
        industry_mapping = {
            'healthcare': ['physicians', 'dentists', 'veterinarians', 'health'],
            'home_services': ['plumbing', 'electricians', 'roofing', 'contractors'],
            'food': ['restaurants', 'cafes', 'bakeries', 'food'],
            'legal': ['lawyers', 'accountants'],
            'wellness': ['spas', 'gyms', 'beautysvc'],
            'retail': ['shopping'],
        }
        
        category_titles = [cat.get('alias', '').lower() for cat in categories]
        
        for industry, keywords in industry_mapping.items():
            if any(keyword in title for title in category_titles for keyword in keywords):
                return industry
        
        return 'other'
