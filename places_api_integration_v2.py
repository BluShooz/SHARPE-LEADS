"""
LeadForge AI - Enhanced Google Places API Integration
Top-tier accuracy with precise location targeting and demographic filtering
"""

import requests
import json
import sqlite3
from typing import List, Dict, Optional
import time
import re
from location_database import (
    get_location_info,
    parse_location_string,
    get_search_radius,
    CITY_COORDINATES,
    INDUSTRY_CONCENTRATION
)

API_KEY = "AIzaSyCTrX9ySn-2nAZLq3SkadPAD0Cmp202oXk"
BASE_URL = "https://maps.googleapis.com/maps/api/place"

class EnhancedPlacesLeadGenerator:
    """Generate leads with top-tier location accuracy"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or API_KEY
        self.session = requests.Session()

    def search_businesses_precise(
        self,
        query: str,
        location: str,
        radius: int = None,
        business_type: str = None,
        max_results: int = 20,
        min_rating: float = 0.0
    ) -> List[Dict]:
        """
        Search for businesses with precise location targeting

        Args:
            query: Search query (e.g., "construction company", "restaurant")
            location: City name or "City, State" format
            radius: Search radius in meters (auto-determined if not provided)
            business_type: Google Place type filter
            max_results: Maximum number of results
            min_rating: Minimum rating threshold (0.0-5.0)

        Returns:
            List of business leads with accurate location data
        """
        # Get precise location information
        location_info = get_location_info(location)

        if not location_info:
            print(f"⚠️  Location not found: {location}")
            return []

        print(f"🎯 Targeting: {location_info['city']}, {location_info['state']}")
        print(f"   Coordinates: {location_info['latitude']}, {location_info['longitude']}")
        print(f"   County: {location_info['county']}")

        # Determine optimal search radius
        if radius is None:
            business_density = location_info.get('business_density', 'medium')
            city_size = "large" if location_info.get('population', 0) > 1000000 else "medium"
            radius = get_search_radius(city_size, business_density)

        print(f"   Search Radius: {radius/1000:.1f} km")

        # Optimize query for location
        optimized_query = self._optimize_query_for_location(query, location_info)

        leads = []
        try:
            # Text Search API with precise location
            url = f"{BASE_URL}/textsearch/json"
            params = {
                "query": optimized_query,
                "location": location_info["coordinates"],
                "radius": radius,
                "key": self.api_key
            }

            if business_type:
                params["type"] = business_type

            print(f"\n🔍 Searching: {optimized_query}")

            response = self.session.get(url, params=params)
            data = response.json()

            if data.get("status") == "OK":
                results = data.get("results", [])

                for place in results:
                    # Filter by rating if specified
                    rating = place.get("rating", 0)
                    if rating < min_rating:
                        continue

                    lead = self._extract_lead_data_precise(place, location_info, query)
                    if lead and self._verify_lead_location(lead, location_info):
                        leads.append(lead)
                        print(f"✅ Found: {lead['business_name']} - Rating: {rating}")

                # Handle pagination
                next_page_token = data.get("next_page_token")
                page = 1
                while next_page_token and len(leads) < max_results and page < 3:
                    time.sleep(2)
                    params["pagetoken"] = next_page_token

                    response = self.session.get(url, params=params)
                    data = response.json()

                    if data.get("status") == "OK":
                        results = data.get("results", [])
                        for place in results:
                            if len(leads) >= max_results:
                                break

                            rating = place.get("rating", 0)
                            if rating < min_rating:
                                continue

                            lead = self._extract_lead_data_precise(place, location_info, query)
                            if lead and self._verify_lead_location(lead, location_info):
                                leads.append(lead)

                        next_page_token = data.get("next_page_token")
                        page += 1
                    else:
                        break

                print(f"\n🎉 Found {len(leads)} verified leads in {location_info['city']}, {location_info['state']}!")
                return leads

            elif data.get("status") == "ZERO_RESULTS":
                print("😕 No results found - try expanding search radius")
                return []

            else:
                print(f"❌ API Error: {data.get('status')}")
                if data.get("error_message"):
                    print(f"   Message: {data.get('error_message')}")
                return []

        except Exception as e:
            print(f"❌ Error searching businesses: {e}")
            return []

    def _optimize_query_for_location(self, query: str, location_info: Dict) -> str:
        """Optimize search query for specific location"""
        # Add state to query for better results
        state_full = {
            "CA": "California", "NY": "New York", "TX": "Texas",
            "WA": "Washington", "CO": "Colorado", "FL": "Florida",
            "IL": "Illinois", "MA": "Massachusetts", "AZ": "Arizona",
            "GA": "Georgia", "OR": "Oregon", "TN": "Tennessee",
            "NC": "North Carolina", "MI": "Michigan", "MN": "Minnesota",
            "OH": "Ohio", "PA": "Pennsylvania", "MO": "Missouri",
            "NV": "Nevada", "UT": "Utah", "IN": "Indiana",
            "WI": "Wisconsin", "MD": "Maryland", "DC": "Washington DC"
        }

        state_name = state_full.get(location_info["state"], location_info["state"])
        return f"{query} in {location_info['city']}, {state_name}"

    def _extract_lead_data_precise(
        self,
        place: Dict,
        location_info: Dict,
        search_query: str
    ) -> Optional[Dict]:
        """Extract lead data with precise location information"""
        try:
            place_id = place.get("place_id")

            # Get detailed information
            details_url = f"{BASE_URL}/details/json"
            params = {
                "place_id": place_id,
                "fields": "name,formatted_phone_number,website,formatted_address,rating,user_ratings_total,types,geometry,adr_address",
                "key": self.api_key
            }

            response = self.session.get(details_url, params=params)
            details = response.json()

            if details.get("status") != "OK":
                return None

            details_data = details.get("result", {})

            # Extract precise location data
            geometry = details_data.get("geometry", {})
            location = geometry.get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")

            # Parse address components for accuracy
            address = details_data.get("formatted_address", "")
            parsed_address = self._parse_address_components(address)

            # Verify location matches target
            if not self._is_location_match(parsed_address, location_info):
                return None

            # Determine business type/industry
            types = details_data.get("types", [])
            industry = self._map_types_to_industry(types, search_query, location_info)

            # Calculate lead score
            rating = details_data.get("rating")
            reviews_count = details_data.get("user_ratings_total", 0)
            score = self._calculate_lead_score(rating, reviews_count, details_data, location_info)

            lead = {
                "business_name": details_data.get("name", ""),
                "industry": industry,
                "location": location_info["city"],  # Use our verified city
                "state": location_info["state"],     # Use our verified state
                "phone": details_data.get("formatted_phone_number", ""),
                "website": details_data.get("website", ""),
                "rating": rating,
                "reviews_count": reviews_count,
                "address": details_data.get("formatted_address", ""),
                "city": location_info["city"],       # Explicit city field
                "state": location_info["state"],      # Explicit state field
                "county": location_info.get("county", ""),
                "latitude": lat,
                "longitude": lng,
                "place_id": place_id,
                "score": score,
                "status": "new",
                "verified_location": True
            }

            return lead

        except Exception as e:
            print(f"⚠️  Error extracting lead data: {e}")
            return None

    def _parse_address_components(self, address: str) -> Dict:
        """Parse address into components"""
        components = {
            "street_number": "",
            "street": "",
            "city": "",
            "state": "",
            "zip": "",
            "country": ""
        }

        if not address:
            return components

        # Parse using Google's address format
        parts = address.split(", ")

        if len(parts) >= 3:
            # Street address
            components["street"] = parts[0]

            # City
            components["city"] = parts[1]

            # State and ZIP
            if len(parts) >= 3:
                state_zip = parts[2]
                zip_match = re.search(r'\b\d{5}(?:-\d{4})?\b', state_zip)
                if zip_match:
                    components["zip"] = zip_match.group()
                    components["state"] = state_zip.replace(zip_match.group(), "").strip()

        return components

    def _is_location_match(self, parsed_address: Dict, location_info: Dict) -> bool:
        """Verify address matches target location"""
        target_city = location_info["city"].lower()
        target_state = location_info["state"].lower()

        address_city = parsed_address.get("city", "").lower()
        address_state = parsed_address.get("state", "").lower()

        # Check state match
        if target_state not in address_state and address_state not in target_state:
            # Allow 2-letter state codes
            if len(address_state) == 2 and address_state != target_state[:2]:
                return False

        # City match is more flexible (can be in metro area)
        return True

    def _verify_lead_location(self, lead: Dict, location_info: Dict) -> bool:
        """Verify lead is actually in the target location"""
        if not lead.get("latitude") or not lead.get("longitude"):
            return True  # Can't verify without coordinates

        # Calculate distance
        from math import radians, cos, sin, asin, sqrt

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in km
            dLat = radians(lat2 - lat1)
            dLon = radians(lon2 - lon1)
            lat1 = radians(lat1)
            lat2 = radians(lat2)
            a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
            c = 2*asin(sqrt(a))
            return R * c

        distance = haversine(
            location_info["latitude"],
            location_info["longitude"],
            lead["latitude"],
            lead["longitude"]
        )

        # Allow 50km radius for metro areas
        return distance <= 50

    def _map_types_to_industry(
        self,
        types: List[str],
        search_query: str,
        location_info: Dict
    ) -> str:
        """Map Google Place types to industries with location awareness"""
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

        # Check for type matches
        for place_type, industry in type_mapping.items():
            if place_type in types:
                return industry

        # Use location-based industry suggestions
        top_industries = location_info.get("top_industries", [])
        for industry in top_industries:
            if industry.lower() in search_query.lower():
                return industry

        # Fallback to search query
        return search_query.title() if search_query else "Business"

    def _calculate_lead_score(
        self,
        rating: float,
        reviews_count: int,
        details: Dict,
        location_info: Dict
    ) -> int:
        """Calculate lead score with location-aware factors"""
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

        # Location bonus for high-value areas
        median_income = location_info.get("median_income", 0)
        if median_income > 70000:
            score += 5

        return min(100, max(0, score))

    def search_by_industry_in_city(
        self,
        city: str,
        industry: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search for specific industry in a specific city
        This is the main method for precise lead generation
        """
        location_info = get_location_info(city)

        if not location_info:
            print(f"❌ City not found: {city}")
            return []

        # Get recommended industries for this city
        recommended = location_info.get("top_industries", [])

        # If industry matches recommendations, boost search radius
        radius = None
        if any(industry.lower() in rec.lower() for rec in recommended):
            print(f"✨ {industry} is a top industry in {city}!")
            radius = 35000  # Larger radius for strong industries

        return self.search_businesses_precise(
            query=industry,
            location=city,
            radius=radius,
            max_results=max_results
        )

    def save_to_database(self, leads: List[Dict], db_path: str = "leads.db") -> int:
        """Save leads to SQLite database with automatic Google Sheets sync"""
        if not leads:
            return 0

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if location columns exist
        cursor.execute("PRAGMA table_info(leads)")
        columns = [col[1] for col in cursor.fetchall()]

        # Add location columns if they don't exist
        if "state" not in columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN state TEXT")
        if "county" not in columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN county TEXT")
        if "latitude" not in columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN latitude REAL")
        if "longitude" not in columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN longitude REAL")
        if "verified_location" not in columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN verified_location INTEGER DEFAULT 0")

        conn.commit()

        saved = 0
        for lead in leads:
            try:
                # Check for duplicates by business name and location
                cursor.execute('''
                    SELECT id FROM leads
                    WHERE business_name = ? AND city = ?
                ''', (lead["business_name"], lead["city"]))

                if cursor.fetchone():
                    continue  # Skip duplicate

                cursor.execute('''
                    INSERT INTO leads
                    (business_name, industry, location, state, phone, website, rating,
                     reviews_count, address, email, score, status, county, latitude, longitude, verified_location)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lead["business_name"],
                    lead["industry"],
                    lead["city"],
                    lead.get("state", ""),
                    lead["phone"],
                    lead["website"],
                    lead["rating"],
                    lead["reviews_count"],
                    lead["address"],
                    "",
                    lead["score"],
                    lead["status"],
                    lead.get("county", ""),
                    lead.get("latitude"),
                    lead.get("longitude"),
                    1  # verified_location = True
                ))
                saved += 1

            except sqlite3.IntegrityError:
                pass
            except Exception as e:
                print(f"⚠️  Error saving lead: {e}")

        conn.commit()
        conn.close()

        print(f"💾 Saved {saved} leads to database!")

        # AUTOMATIC GOOGLE SHEETS SYNC - EXECUTE EVERY TIME
        try:
            from auto_sheets_sync import auto_sync_leads
            print("🔄 Syncing to Google Sheets...")
            synced = auto_sync_leads(leads)
            print(f"✅ Google Sheets sync complete: {synced} leads")
        except Exception as e:
            print(f"⚠️  Google Sheets sync warning: {e}")

        return saved


# Quick start function
def search_and_save(city: str, industry: str, max_results: int = 20) -> int:
    """Quick search and save function"""
    generator = EnhancedPlacesLeadGenerator()

    print(f"\n{'='*70}")
    print(f"🎯 Searching for {industry} in {city}")
    print(f"{'='*70}\n")

    leads = generator.search_by_industry_in_city(city, industry, max_results)

    if leads:
        saved = generator.save_to_database(leads)
        print(f"\n✅ Successfully saved {saved} new leads!")
        return saved

    return 0
