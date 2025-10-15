import requests
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class GooglePlacesScraper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        
    def search_nearby(self, location, radius_miles=10, industry_keywords=None):
        """
        Search for businesses near a location
        """
        results = []
        radius_meters = radius_miles * 1609.34
        
        # Geocode location first
        if isinstance(location, str):
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {'address': location, 'key': self.api_key}
            
            print(f"Geocoding location: {location}")
            response = requests.get(geocode_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    location_data = data['results'][0]['geometry']['location']
                    location = f"{location_data['lat']},{location_data['lng']}"
                    print(f"Geocoded to: {location}")
                else:
                    print(f"Geocoding failed: {data}")
                    return []
            else:
                print(f"Geocoding error: {response.status_code}")
                return []
        
        # Search for each industry keyword
        keywords = industry_keywords or ['business']
        print(f"Searching for keywords: {keywords}")
        
        for keyword in keywords:
            print(f"\nSearching for: {keyword}")
            places = self._nearby_search(location, radius_meters, keyword)
            print(f"Found {len(places)} places for {keyword}")
            results.extend(places)
            time.sleep(2)  # Rate limiting
        
        # Remove duplicates by place_id
        unique_results = {p['place_id']: p for p in results}.values()
        print(f"Total unique places: {len(unique_results)}")
        return list(unique_results)
    
    def _nearby_search(self, location, radius, keyword):
        """Perform nearby search with better error handling"""
        url = f"{self.base_url}/nearbysearch/json"
        params = {
            'location': location,
            'radius': radius,
            'keyword': keyword,
            'key': self.api_key
        }
        
        all_results = []
        page_count = 0
        max_pages = 3  # Limit to avoid too many API calls
        
        while page_count < max_pages:
            print(f"  Fetching page {page_count + 1}...")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"  Error {response.status_code}: {response.text}")
                break
            
            data = response.json()
            
            if data.get('status') != 'OK' and data.get('status') != 'ZERO_RESULTS':
                print(f"  API Status: {data.get('status')}")
                if data.get('error_message'):
                    print(f"  Error: {data.get('error_message')}")
                break
            
            if data.get('results'):
                all_results.extend(data['results'])
                print(f"  Added {len(data['results'])} results")
            else:
                print(f"  No results on this page")
            
            # Check for next page
            if 'next_page_token' in data:
                time.sleep(3)  # Required delay for next_page_token
                url = f"{self.base_url}/nearbysearch/json"
                params = {'pagetoken': data['next_page_token'], 'key': self.api_key}
                page_count += 1
            else:
                break
        
        return all_results
    
    def get_place_details(self, place_id):
        """Get detailed information about a place"""
        url = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,types,business_status',
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('result', {})
        
        return {}
    
    def format_lead(self, place_data, details=None):
        """Format place data into lead structure"""
        if not details:
            details = self.get_place_details(place_data['place_id'])
        
        # Skip if business is permanently closed
        if details.get('business_status') == 'CLOSED_PERMANENTLY':
            return None
        
        # Parse address
        address_parts = details.get('formatted_address', '').split(',')
        city = address_parts[1].strip() if len(address_parts) > 1 else ''
        state_zip = address_parts[2].strip() if len(address_parts) > 2 else ''
        state = state_zip.split()[0] if state_zip else ''
        
        return {
            'name': place_data.get('name'),
            'company': place_data.get('name'),
            'address': address_parts[0] if address_parts else '',
            'city': city,
            'state': state,
            'phone': details.get('formatted_phone_number'),
            'website_url': details.get('website'),
            'source': 'google',
            'industry': self._categorize_industry(details.get('types', [])),
            'rating': details.get('rating')
        }
    
    def _categorize_industry(self, types):
        """Map Google place types to our industries"""
        types_str = ' '.join(types).lower()
        
        industry_mapping = {
            'healthcare': ['doctor', 'physician', 'hospital', 'health', 'medical'],
            'dental': ['dentist', 'dental'],
            'veterinary': ['veterinary'],
            'home_services': ['plumber', 'electrician', 'roofing', 'contractor', 'hvac', 'general_contractor'],
            'food': ['restaurant', 'cafe', 'bakery', 'food', 'meal_takeaway'],
            'legal': ['lawyer', 'attorney', 'legal'],
            'accounting': ['accountant', 'accounting'],
            'wellness': ['spa', 'gym', 'fitness', 'physiotherapist'],
            'beauty': ['beauty', 'salon', 'hair'],
            'retail': ['store', 'shopping', 'clothing'],
            'real_estate': ['real_estate'],
            'auto': ['car_repair', 'car_dealer', 'auto'],
            'pet_services': ['pet', 'grooming'],
            'cleaning': ['cleaning'],
            'landscaping': ['landscaping', 'lawn'],
            'photography': ['photographer'],
        }
        
        for industry, keywords in industry_mapping.items():
            if any(keyword in types_str for keyword in keywords):
                return industry
        
        return 'other'
