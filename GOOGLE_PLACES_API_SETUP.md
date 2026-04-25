# Google Places API Setup Guide

## 🚀 Quick Setup (5 minutes)

### 1. Get Your API Key
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click **"Create Credentials"** → **"API Key"**
3. Copy your API key (looks like: `AIzaSy...`)

### 2. Enable Places API
1. Go to: https://console.cloud.google.com/apis/library
2. Search for **"Places API"**
3. Click **"Enable"**

### 3. Add Your API Key
Edit `/Users/jonsmith/leadforge-scraper/places_api_integration.py`:
```python
API_KEY = "your-api-key-here"
```

## 💰 Pricing
- **$200/month free credit** (generous!)
- After free credit:
  - Text Search: $5 per 1,000 requests
  - Place Details: $15 per 1,000 requests
  - With $200 credit: ~40,000 business searches per month!

## 🎯 Usage Examples

### Example 1: Search by Industry & Location
```python
from places_api_integration import PlacesLeadGenerator

generator = PlacesLeadGenerator()

leads = generator.search_businesses(
    query="construction company",  # Any business type
    location="37.7749,-122.4194",  # San Francisco
    radius=50000,                  # 50km radius
    max_results=50
)

generator.save_to_database(leads)
```

### Example 2: Search Multiple Cities
```python
cities = ["Austin, TX", "Seattle, WA", "Denver, CO"]

for city in cities:
    leads = generator.search_by_location(
        location=city,
        business_type="restaurant",
        max_results=20
    )
    generator.save_to_database(leads)
```

### Example 3: Generate 1000+ Leads
```python
# Search multiple industries in multiple cities
industries = ["restaurant", "gym", "lawyer", "dentist"]
cities = ["New York, NY", "Los Angeles, CA", "Chicago, IL"]

for city in cities:
    for industry in industries:
        leads = generator.search_by_location(city, industry, max_results=50)
        generator.save_to_database(leads)
        print(f"✅ {len(leads)} {industry}s in {city}")
```

## 📊 What Data You Get

For each lead:
- ✅ Business name
- ✅ Phone number
- ✅ Website URL
- ✅ Full address
- ✅ Rating (1-5 stars)
- ✅ Review count
- ✅ Business category/industry
- ✅ GPS coordinates
- ✅ AI-calculated lead score

## 🔗 Integration with LeadForge

The integration automatically saves to your existing SQLite database at `/Users/jonsmith/leadforge-scraper/leads.db`

## 🎉 Benefits vs Scraping

| Feature | Places API | Web Scraping |
|---------|------------|--------------|
| **Speed** | Instant | Slow |
| **Reliability** | 99.9% uptime | Often blocked |
| **Data Quality** | Verified, accurate | Inconsistent |
| **Legal** | ✅ Official API | ⚠️ Gray area |
| **Cost** | Free $200/mo | Server costs |
| **Rate Limits** | High | Low (blocked) |

## 🚨 Rate Limits

- **Free tier**: Up to ~40,000 searches/month
- **Paid tier**: Unlimited with billing
- Built-in rate limiting handled automatically

## 🔐 Security Tips

1. **Never commit API keys to git**
2. **Set up API key restrictions** in Google Console:
   - Application restrictions: IP addresses or referrer
   - API restrictions: Only Places API

## 📚 Official Documentation

https://developers.google.com/maps/documentation/places/web-service/overview
