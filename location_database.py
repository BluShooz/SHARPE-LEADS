"""
LeadForge AI - Top-Tier Location Database
Precise coordinates and demographic data for accurate lead generation
"""

# Comprehensive US city coordinates with precise lat/lng
CITY_COORDINATES = {
    # California
    "San Francisco": {"lat": 37.7749, "lng": -122.4194, "state": "CA", "county": "San Francisco County"},
    "Los Angeles": {"lat": 34.0522, "lng": -118.2437, "state": "CA", "county": "Los Angeles County"},
    "San Diego": {"lat": 32.7157, "lng": -117.1611, "state": "CA", "county": "San Diego County"},
    "San Jose": {"lat": 37.3382, "lng": -121.8863, "state": "CA", "county": "Santa Clara County"},
    "Sacramento": {"lat": 38.5816, "lng": -121.4944, "state": "CA", "county": "Sacramento County"},
    "Fresno": {"lat": 36.7468, "lng": -119.7721, "state": "CA", "county": "Fresno County"},
    "Oakland": {"lat": 37.8044, "lng": -122.2712, "state": "CA", "county": "Alameda County"},

    # New York
    "New York": {"lat": 40.7128, "lng": -74.0060, "state": "NY", "county": "New York County"},
    "Buffalo": {"lat": 42.8864, "lng": -78.8784, "state": "NY", "county": "Erie County"},
    "Rochester": {"lat": 43.1566, "lng": -77.6088, "state": "NY", "county": "Monroe County"},
    "Yonkers": {"lat": 40.9319, "lng": -73.8988, "state": "NY", "county": "Westchester County"},
    "Syracuse": {"lat": 43.0481, "lng": -76.1474, "state": "NY", "county": "Onondaga County"},
    "Albany": {"lat": 42.6526, "lng": -73.7562, "state": "NY", "county": "Albany County"},

    # Texas
    "Austin": {"lat": 30.2672, "lng": -97.7431, "state": "TX", "county": "Travis County"},
    "Dallas": {"lat": 32.7767, "lng": -96.7970, "state": "TX", "county": "Dallas County"},
    "Houston": {"lat": 29.7604, "lng": -95.3698, "state": "TX", "county": "Harris County"},
    "San Antonio": {"lat": 29.4241, "lng": -98.4936, "state": "TX", "county": "Bexar County"},
    "Fort Worth": {"lat": 32.7555, "lng": -97.3308, "state": "TX", "county": "Tarrant County"},
    "El Paso": {"lat": 31.7619, "lng": -106.4850, "state": "TX", "county": "El Paso County"},

    # Washington
    "Seattle": {"lat": 47.6062, "lng": -122.3321, "state": "WA", "county": "King County"},
    "Spokane": {"lat": 47.6588, "lng": -117.4260, "state": "WA", "county": "Spokane County"},
    "Tacoma": {"lat": 47.2529, "lng": -122.4443, "state": "WA", "county": "Pierce County"},
    "Vancouver": {"lat": 45.6387, "lng": -122.6615, "state": "WA", "county": "Clark County"},
    "Bellevue": {"lat": 47.6101, "lng": -122.2015, "state": "WA", "county": "King County"},

    # Colorado
    "Denver": {"lat": 39.7392, "lng": -104.9903, "state": "CO", "county": "Denver County"},
    "Colorado Springs": {"lat": 38.8339, "lng": -104.8214, "state": "CO", "county": "El Paso County"},
    "Aurora": {"lat": 39.7294, "lng": -104.8319, "state": "CO", "county": "Arapahoe County"},
    "Fort Collins": {"lat": 40.5853, "lng": -105.0844, "state": "CO", "county": "Larimer County"},
    "Boulder": {"lat": 40.0150, "lng": -105.2705, "state": "CO", "county": "Boulder County"},

    # Florida
    "Miami": {"lat": 25.7617, "lng": -80.1918, "state": "FL", "county": "Miami-Dade County"},
    "Tampa": {"lat": 27.9506, "lng": -82.4572, "state": "FL", "county": "Hillsborough County"},
    "Orlando": {"lat": 28.5383, "lng": -81.3792, "state": "FL", "county": "Orange County"},
    "Jacksonville": {"lat": 30.3322, "lng": -81.6557, "state": "FL", "county": "Duval County"},
    "Fort Lauderdale": {"lat": 26.1224, "lng": -80.1373, "state": "FL", "county": "Broward County"},

    # Illinois
    "Chicago": {"lat": 41.8781, "lng": -87.6298, "state": "IL", "county": "Cook County"},
    "Aurora": {"lat": 41.7606, "lng": -88.3201, "state": "IL", "county": "Kane County"},
    "Naperville": {"lat": 41.7503, "lng": -88.1539, "state": "IL", "county": "DuPage County"},
    "Springfield": {"lat": 39.7817, "lng": -89.6501, "state": "IL", "county": "Sangamon County"},

    # Massachusetts
    "Boston": {"lat": 42.3601, "lng": -71.0589, "state": "MA", "county": "Suffolk County"},
    "Worcester": {"lat": 42.2626, "lng": -71.8023, "state": "MA", "county": "Worcester County"},
    "Springfield": {"lat": 42.1015, "lng": -72.5898, "state": "MA", "county": "Hampden County"},
    "Cambridge": {"lat": 42.3601, "lng": -71.0942, "state": "MA", "county": "Middlesex County"},

    # Arizona
    "Phoenix": {"lat": 33.4484, "lng": -112.0740, "state": "AZ", "county": "Maricopa County"},
    "Tucson": {"lat": 32.2226, "lng": -110.9747, "state": "AZ", "county": "Pima County"},
    "Mesa": {"lat": 33.4152, "lng": -111.8315, "state": "AZ", "county": "Maricopa County"},
    "Scottsdale": {"lat": 33.4354, "lng": -111.9263, "state": "AZ", "county": "Maricopa County"},

    # Georgia
    "Atlanta": {"lat": 33.7490, "lng": -84.3880, "state": "GA", "county": "Fulton County"},
    "Augusta": {"lat": 33.4735, "lng": -82.0105, "state": "GA", "county": "Richmond County"},
    "Columbus": {"lat": 32.4609, "lng": -84.9877, "state": "GA", "county": "Muscogee County"},
    "Savannah": {"lat": 32.0835, "lng": -81.0978, "state": "GA", "county": "Chatham County"},

    # Oregon
    "Portland": {"lat": 45.5152, "lng": -122.6784, "state": "OR", "county": "Multnomah County"},
    "Eugene": {"lat": 44.0521, "lng": -123.0868, "state": "OR", "county": "Lane County"},
    "Salem": {"lat": 44.9429, "lng": -123.0351, "state": "OR", "county": "Marion County"},

    # Tennessee
    "Nashville": {"lat": 36.1627, "lng": -86.7816, "state": "TN", "county": "Davidson County"},
    "Memphis": {"lat": 35.1495, "lng": -90.0490, "state": "TN", "county": "Shelby County"},
    "Knoxville": {"lat": 35.9606, "lng": -83.9207, "state": "TN", "county": "Knox County"},

    # North Carolina
    "Raleigh": {"lat": 35.7796, "lng": -78.6382, "state": "NC", "county": "Wake County"},
    "Charlotte": {"lat": 35.2271, "lng": -80.8431, "state": "NC", "county": "Mecklenburg County"},
    "Greensboro": {"lat": 36.0726, "lng": -79.7920, "state": "NC", "county": "Guilford County"},

    # Michigan
    "Detroit": {"lat": 42.3314, "lng": -83.0458, "state": "MI", "county": "Wayne County"},
    "Grand Rapids": {"lat": 42.9634, "lng": -85.6681, "state": "MI", "county": "Kent County"},

    # Minnesota
    "Minneapolis": {"lat": 44.9778, "lng": -93.2650, "state": "MN", "county": "Hennepin County"},
    "Saint Paul": {"lat": 44.9537, "lng": -93.0900, "state": "MN", "county": "Ramsey County"},

    # Ohio
    "Columbus": {"lat": 39.9612, "lng": -82.9988, "state": "OH", "county": "Franklin County"},
    "Cleveland": {"lat": 41.4993, "lng": -81.6944, "state": "OH", "county": "Cuyahoga County"},
    "Cincinnati": {"lat": 39.1031, "lng": -84.5120, "state": "OH", "county": "Hamilton County"},

    # Pennsylvania
    "Philadelphia": {"lat": 39.9526, "lng": -75.1652, "state": "PA", "county": "Philadelphia County"},
    "Pittsburgh": {"lat": 40.4406, "lng": -79.9959, "state": "PA", "county": "Allegheny County"},

    # Missouri
    "Kansas City": {"lat": 39.0997, "lng": -94.5786, "state": "MO", "county": "Jackson County"},
    "St. Louis": {"lat": 38.6270, "lng": -90.1994, "state": "MO", "county": "St. Louis City"},

    # Nevada
    "Las Vegas": {"lat": 36.1699, "lng": -115.1398, "state": "NV", "county": "Clark County"},
    "Reno": {"lat": 39.5296, "lng": -119.8138, "state": "NV", "county": "Washoe County"},

    # Utah
    "Salt Lake City": {"lat": 40.7608, "lng": -111.8910, "state": "UT", "county": "Salt Lake County"},

    # Indiana
    "Indianapolis": {"lat": 39.7684, "lng": -86.1581, "state": "IN", "county": "Marion County"},

    # Wisconsin
    "Milwaukee": {"lat": 43.0389, "lng": -87.9065, "state": "WI", "county": "Milwaukee County"},

    # Maryland
    "Baltimore": {"lat": 39.2904, "lng": -76.6122, "state": "MD", "county": "Baltimore City"},

    # District of Columbia
    "Washington": {"lat": 38.9072, "lng": -77.0369, "state": "DC", "county": "District of Columbia"},
}

# State demographic data (median income, population, etc.)
STATE_DEMOGRAPHICS = {
    "CA": {"median_income": 80440, "population": 39538223, "business_density": "high"},
    "NY": {"median_income": 72607, "population": 20201249, "business_density": "high"},
    "TX": {"median_income": 63827, "population": 29145505, "business_density": "high"},
    "WA": {"median_income": 77006, "population": 7705281, "business_density": "high"},
    "CO": {"median_income": 75231, "population": 5773714, "business_density": "medium"},
    "FL": {"median_income": 59533, "population": 21538187, "business_density": "high"},
    "IL": {"median_income": 68428, "population": 12812508, "business_density": "high"},
    "MA": {"median_income": 85743, "population": 7029917, "business_density": "high"},
    "AZ": {"median_income": 62583, "population": 7151502, "business_density": "medium"},
    "GA": {"median_income": 61227, "population": 10711908, "business_density": "high"},
    "OR": {"median_income": 67081, "population": 4237256, "business_density": "medium"},
    "TN": {"median_income": 56541, "population": 6910840, "business_density": "medium"},
    "NC": {"median_income": 60516, "population": 10439388, "business_density": "high"},
    "MI": {"median_income": 59426, "population": 10077331, "business_density": "high"},
    "MN": {"median_income": 73833, "population": 5706494, "business_density": "medium"},
    "OH": {"median_income": 61458, "population": 11799448, "business_density": "high"},
    "PA": {"median_income": 64902, "population": 13002700, "business_density": "high"},
    "MO": {"median_income": 57840, "population": 6154913, "business_density": "medium"},
    "NV": {"median_income": 61682, "population": 3104614, "business_density": "medium"},
    "UT": {"median_income": 71997, "population": 3271616, "business_density": "medium"},
    "IN": {"median_income": 58235, "population": 6785528, "business_density": "medium"},
    "WI": {"median_income": 63849, "population": 5893718, "business_density": "medium"},
    "MD": {"median_income": 86867, "population": 6177224, "business_density": "high"},
    "DC": {"median_income": 92663, "population": 689545, "business_density": "high"},
}

# Industry concentration by city (which industries are most common)
INDUSTRY_CONCENTRATION = {
    "San Francisco": ["Technology", "Software", "Biotech", "Finance"],
    "New York": ["Finance", "Legal", "Media", "Consulting"],
    "Austin": ["Technology", "Software", "Healthcare", "Education"],
    "Seattle": ["Technology", "E-commerce", "Aerospace", "Healthcare"],
    "Denver": ["Technology", "Aerospace", "Telecommunications", "Energy"],
    "Miami": ["Tourism", "Real Estate", "International Trade", "Healthcare"],
    "Chicago": ["Finance", "Manufacturing", "Healthcare", "Technology"],
    "Boston": ["Technology", "Biotech", "Education", "Healthcare"],
    "Los Angeles": ["Entertainment", "Media", "Fashion", "Technology"],
    "Phoenix": ["Healthcare", "Real Estate", "Manufacturing", "Technology"],
    "Dallas": ["Technology", "Finance", "Telecommunications", "Healthcare"],
    "Atlanta": ["Technology", "Media", "Logistics", "Healthcare"],
    "Portland": ["Technology", "Manufacturing", "Sustainability", "Healthcare"],
    "Nashville": ["Healthcare", "Music", "Publishing", "Technology"],
    "Raleigh": ["Technology", "Biotech", "Education", "Healthcare"],
}

def get_city_coordinates(city_name):
    """Get precise coordinates for a city"""
    # Remove state abbreviation if present
    city = city_name.split(",")[0].strip()

    # Direct match
    if city in CITY_COORDINATES:
        return CITY_COORDINATES[city]

    # Case-insensitive search
    for name, data in CITY_COORDINATES.items():
        if name.lower() == city.lower():
            return data

    # Try to find partial match
    for name, data in CITY_COORDINATES.items():
        if city.lower() in name.lower() or name.lower() in city.lower():
            return data

    return None

def get_location_info(city_name, state_code=None):
    """Get comprehensive location information"""
    city_data = get_city_coordinates(city_name)

    if not city_data:
        return None

    # Verify state matches if provided
    if state_code and city_data["state"] != state_code.upper():
        # Try to find city in specified state
        for name, data in CITY_COORDINATES.items():
            if (name.lower() == city_name.lower() or city_name.lower() in name.lower()) and \
               data["state"] == state_code.upper():
                city_data = data
                break

    state_data = STATE_DEMOGRAPHICS.get(city_data["state"], {})
    industries = INDUSTRY_CONCENTRATION.get(city_name.split(",")[0].strip(), [])

    return {
        "city": city_name.split(",")[0].strip(),
        "state": city_data["state"],
        "county": city_data.get("county", ""),
        "latitude": city_data["lat"],
        "longitude": city_data["lng"],
        "coordinates": f"{city_data['lat']},{city_data['lng']}",
        "median_income": state_data.get("median_income", 0),
        "population": state_data.get("population", 0),
        "business_density": state_data.get("business_density", "medium"),
        "top_industries": industries
    }

def parse_location_string(location):
    """Parse location string into city and state"""
    if not location:
        return None, None

    # Split by comma
    parts = [p.strip() for p in location.split(",")]

    if len(parts) >= 2:
        city = parts[0]
        state = parts[1].upper()
        return city, state

    # If only city provided
    city_data = get_city_coordinates(location)
    if city_data:
        return location, city_data["state"]

    return location, None

def format_location_display(city, state):
    """Format location for display"""
    if state:
        return f"{city}, {state}"
    return city

def get_search_radius(city_size, business_density):
    """Determine optimal search radius based on city characteristics"""
    base_radius = 25000  # 25km base

    # Adjust for city size
    if city_size == "large":
        base_radius = 50000  # 50km
    elif city_size == "medium":
        base_radius = 30000  # 30km

    # Adjust for business density
    if business_density == "high":
        base_radius = int(base_radius * 0.8)  # Smaller radius for dense areas

    return base_radius

def get_all_cities():
    """Get list of all available cities"""
    cities = []
    for city_name, data in CITY_COORDINATES.items():
        cities.append({
            "name": city_name,
            "state": data["state"],
            "display": f"{city_name}, {data['state']}"
        })
    return sorted(cities, key=lambda x: x["display"])

def get_cities_by_state(state_code):
    """Get all cities in a specific state"""
    cities = []
    for city_name, data in CITY_COORDINATES.items():
        if data["state"] == state_code.upper():
            cities.append({
                "name": city_name,
                "display": f"{city_name}, {data['state']}"
            })
    return sorted(cities, key=lambda x: x["display"])
