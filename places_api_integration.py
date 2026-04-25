"""
LeadForge AI - Google Places API Integration
Generate real business leads using Google Places API
"""

import requests
import json
import sqlite3
from typing import List, Dict, Optional
import time

API_KEY = "AIzaSyCTrX9ySn-2nAZLq3SkadPAD0Cmp202oXk"  # Google Places API Key
BASE_URL = "https://maps.googleapis.com/maps/api/place"

class PlacesLeadGenerator:
    """Generate leads using Google Places API"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or API_KEY
        self.session = requests.Session()

    def search_businesses(
        self,
        query: str,
        location: str = "37.7749,-122.4194",  # San Francisco default
        radius: int = 50000,  # 50km in meters
        business_type: str = None,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search for businesses using Places API

        Args:
            query: Search query (e.g., "construction company", "restaurant")
            location: Lat,lng coordinates
            radius: Search radius in meters (max 50000)
            business_type: Place type (e.g., 'restaurant', 'store', 'establishment')
            max_results: Maximum number of results

        Returns:
            List of business leads
        """
        if not self.api_key or self.api_key == "YOUR_GOOGLE_PLACES_API_KEY":
            print("❌ Please set your Google Places API key")
            return []

        leads = []

        try:
            # Text Search API
            url = f"{BASE_URL}/textsearch/json"
            params = {
                "query": query,
                "location": location,
                "radius": radius,
                "key": self.api_key
            }

            if business_type:
                params["type"] = business_type

            print(f"🔍 Searching for: {query} in {location}")

            response = self.session.get(url, params=params)
            data = response.json()

            if data.get("status") == "OK":
                results = data.get("results", [])

                for place in results[:max_results]:
                    lead = self._extract_lead_data(place, query)
                    if lead:
                        leads.append(lead)
                        print(f"✅ Found: {lead['business_name']} - {lead.get('phone', 'N/A')}")

                # Handle pagination (next_page_token)
                next_page_token = data.get("next_page_token")
                while next_page_token and len(leads) < max_results:
                    time.sleep(2)  # Required delay for next_page_token
                    params["pagetoken"] = next_page_token

                    response = self.session.get(url, params=params)
                    data = response.json()

                    if data.get("status") == "OK":
                        results = data.get("results", [])
                        for place in results:
                            if len(leads) >= max_results:
                                break
                            lead = self._extract_lead_data(place, query)
                            if lead:
                                leads.append(lead)
                                print(f"✅ Found: {lead['business_name']}")

                        next_page_token = data.get("next_page_token")
                    else:
                        break

                print(f"\n🎉 Found {len(leads)} leads!")
                return leads

            elif data.get("status") == "ZERO_RESULTS":
                print("😕 No results found")
                return []

            else:
                print(f"❌ API Error: {data.get('status')}")
                print(f"Message: {data.get('error_message', 'Unknown error')}")
                return []

        except Exception as e:
            print(f"❌ Error searching businesses: {e}")
            return []

    def _extract_lead_data(self, place: Dict, search_query: str) -> Optional[Dict]:
        """Extract lead data from Places API response"""
        try:
            place_id = place.get("place_id")

            # Get detailed information
            details_url = f"{BASE_URL}/details/json"
            params = {
                "place_id": place_id,
                "fields": "name,formatted_phone_number,website,formatted_address,rating,user_ratings_total,types,geometry",
                "key": self.api_key
            }

            response = self.session.get(details_url, params=params)
            details = response.json()

            if details.get("status") != "OK":
                print(f"⚠️  Details API error: {details.get('status')}")
                if details.get("error_message"):
                    print(f"   Error: {details.get('error_message')}")
                return None

            details_data = details.get("result", {})

            # Extract location data
            geometry = details_data.get("geometry", {})
            location = geometry.get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")

            # Determine business type/industry
            types = details_data.get("types", [])
            industry = self._map_types_to_industry(types, search_query)

            # Calculate lead score
            rating = details_data.get("rating")
            reviews_count = details_data.get("user_ratings_total", 0)
            score = self._calculate_lead_score(rating, reviews_count, details_data)

            lead = {
                "business_name": details_data.get("name", ""),
                "industry": industry,
                "location": self._extract_city(details_data.get("formatted_address", "")),
                "phone": details_data.get("formatted_phone_number", ""),
                "website": details_data.get("website", ""),
                "rating": rating,
                "reviews_count": reviews_count,
                "address": details_data.get("formatted_address", ""),
                "latitude": lat,
                "longitude": lng,
                "place_id": place_id,
                "score": score,
                "status": "new"
            }

            return lead

        except Exception as e:
            print(f"⚠️  Error extracting lead data: {e}")
            return None

    def _map_types_to_industry(self, types: List[str], search_query: str) -> str:
        """Map Google Place types to LeadForge industries"""
        type_mapping = {
            "restaurant": "Restaurant",
            "cafe": "Food & Beverage",
            "bakery": "Food & Beverage",
            "store": "Retail",
            "shopping": "Retail",
            "health": "Healthcare",
            "hospital": "Healthcare",
            "doctor": "Healthcare",
            "lawyer": "Legal",
            "finance": "Finance",
            "bank": "Finance",
            "insurance": "Insurance",
            "construction": "Construction",
            "real_estate": "Real Estate",
            "school": "Education",
            "university": "Education",
            "gym": "Fitness",
            "beauty_salon": "Beauty & Wellness",
            "hair_care": "Beauty & Wellness",
        }

        for place_type, industry in type_mapping.items():
            if place_type in types:
                return industry

        # Fallback to search query or default
        return search_query.title() if search_query else "Business"

    def _extract_city(self, address: str) -> str:
        """Extract city from formatted address"""
        if not address:
            return "Unknown"

        parts = address.split(", ")
        if len(parts) >= 2:
            # Usually: "street, city, state, country"
            city_part = parts[-3] if len(parts) >= 3 else parts[-2]
            return city_part.strip()

        return "Unknown"

    def _calculate_lead_score(self, rating: float, reviews_count: int, details: Dict) -> int:
        """Calculate lead score based on various factors"""
        score = 50  # Base score

        # Rating impact (up to +20 points)
        if rating:
            score += min(20, (rating - 3) * 10)

        # Review count impact (up to +15 points)
        if reviews_count:
            score += min(15, min(reviews_count // 10, 15))

        # Has website (+10 points)
        if details.get("website"):
            score += 10

        # Has phone number (+5 points)
        if details.get("formatted_phone_number"):
            score += 5

        return min(100, max(0, score))

    def search_by_location(
        self,
        location: str,
        business_type: str,
        radius: int = 50000,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search for businesses near a specific location

        Args:
            location: City name or lat,lng coordinates
            business_type: Type of business (e.g., 'restaurant', 'store')
            radius: Search radius in meters
            max_results: Maximum results

        Returns:
            List of leads
        """
        # Convert city name to coordinates if needed
        if "," not in location:
            location = self._geocode_city(location)

        return self.search_businesses(
            query=business_type,
            location=location,
            business_type=business_type,
            max_results=max_results,
            radius=radius
        )

    def _geocode_city(self, city: str) -> str:
        """Convert city name to lat,lng coordinates"""
        try:
            url = f"{BASE_URL}/geocode/json"
            params = {
                "address": city,
                "key": self.api_key
            }

            response = self.session.get(url, params=params)
            data = response.json()

            if data.get("status") == "OK":
                location = data["results"][0]["geometry"]["location"]
                return f"{location['lat']},{location['lng']}"

        except Exception as e:
            print(f"⚠️  Error geocoding city: {e}")

        # Default to San Francisco
        return "37.7749,-122.4194"

    def save_to_database(self, leads: List[Dict], db_path: str = "leads.db") -> int:
        """Save leads to SQLite database"""
        if not leads:
            return 0

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        saved = 0
        for lead in leads:
            try:
                cursor.execute('''
                    INSERT INTO leads
                    (business_name, industry, location, phone, website, rating,
                     reviews_count, address, email, score, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lead["business_name"],
                    lead["industry"],
                    lead["location"],
                    lead["phone"],
                    lead["website"],
                    lead["rating"],
                    lead["reviews_count"],
                    lead["address"],
                    "",  # Email - not provided by Places API
                    lead["score"],
                    lead["status"]
                ))
                saved += 1

            except sqlite3.IntegrityError:
                # Lead already exists
                pass
            except Exception as e:
                print(f"⚠️  Error saving lead: {e}")

        conn.commit()
        conn.close()

        print(f"💾 Saved {saved} leads to database!")
        return saved


# Quick start examples
def quick_search_example():
    """Example: Search for construction companies in San Francisco"""
    generator = PlacesLeadGenerator()

    print("🏗️  Searching for construction companies...")
    leads = generator.search_businesses(
        query="construction company",
        location="37.7749,-122.4194",  # San Francisco
        radius=50000,
        max_results=20
    )

    if leads:
        generator.save_to_database(leads)
        print(f"\n✅ Found and saved {len(leads)} leads!")


def search_by_city_example():
    """Example: Search for restaurants in a specific city"""
    generator = PlacesLeadGenerator()

    cities = ["Austin, TX", "Seattle, WA", "Denver, CO"]
    business_types = ["restaurant", "coffee shop", "gym"]

    for city in cities:
        for business_type in business_types:
            print(f"\n🔍 Searching {business_type}s in {city}...")
            leads = generator.search_by_location(
                location=city,
                business_type=business_type,
                max_results=10
            )

            if leads:
                generator.save_to_database(leads)
                print(f"✅ Saved {len(leads)} leads from {city}")

            time.sleep(1)  # Rate limiting


if __name__ == "__main__":
    print("=" * 70)
    print("🎯 LeadForge AI - Google Places API Integration")
    print("=" * 70)
    print()
    print("📋 To get started:")
    print("1. Get a free API key from: https://console.cloud.google.com/apis/credentials")
    print("2. Enable the Places API for your project")
    print("3. Set your API_KEY in this file")
    print()
    print("💰 Pricing:")
    print("   - $200/month free credit")
    print("   - Text Search: $5 per 1,000 requests")
    print("   - Place Details: $15 per 1,000 requests")
    print()
    print("📚 Documentation: https://developers.google.com/maps/documentation/places/web-service/overview")
    print()

    # Uncomment to run examples
    # quick_search_example()
    # search_by_city_example()
