#!/usr/bin/env python3
"""
Test Hunter.io API endpoints
"""

import requests
import json

HUNTER_API_KEY = "17aaebe1a4244027b283e2c40c2c3dd2f9b9b10c"

print("=" * 60)
print("🔍 Testing Hunter.io API Endpoints")
print("=" * 60)

# Test 1: Domain Search (all emails at a domain)
print("\n1️⃣ Testing Domain Search...")
try:
    url = "https://api.hunter.io/v2/domain-search"
    params = {
        "domain": "apple.com",
        "api_key": HUNTER_API_KEY
    }
    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Domain search successful!")
        emails = data.get('data', {}).get('emails', [])
        print(f"   Found {len(emails)} emails")
        if emails:
            for email in emails[:3]:  # Show first 3
                print(f"   - {email.get('value')} (confidence: {email.get('confidence', 'N/A')})")
    else:
        print(f"⚠️  Domain search failed: {response.status_code}")
        print(f"   Response: {response.text[:300]}")
except Exception as e:
    print(f"❌ Domain search error: {e}")

# Test 2: Email Finder (specific email pattern)
print("\n2️⃣ Testing Email Finder...")
try:
    url = "https://api.hunter.io/v2/email-finder"
    params = {
        "domain": "asana.com",
        "api_key": HUNTER_API_KEY
    }
    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Email finder successful!")
        email_data = data.get('data', {})
        print(f"   Email: {email_data.get('email', 'N/A')}")
        print(f"   Confidence: {email_data.get('confidence', 'N/A')}")
    else:
        print(f"⚠️  Email finder failed: {response.status_code}")
        print(f"   Response: {response.text[:300]}")
except Exception as e:
    print(f"❌ Email finder error: {e}")

# Test 3: Email Verifier
print("\n3️⃣ Testing Email Verifier...")
try:
    url = "https://api.hunter.io/v2/email-verifier"
    params = {
        "email": "test@asana.com",
        "api_key": HUNTER_API_KEY
    }
    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Email verifier successful!")
        email_data = data.get('data', {})
        print(f"   Status: {email_data.get('status', 'N/A')}")
        print(f"   Score: {email_data.get('score', 'N/A')}")
    else:
        print(f"⚠️  Email verifier failed: {response.status_code}")
        print(f"   Response: {response.text[:300]}")
except Exception as e:
    print(f"❌ Email verifier error: {e}")

print("\n" + "=" * 60)
print("✅ Hunter.io API Testing Complete!")
print("=" * 60)
