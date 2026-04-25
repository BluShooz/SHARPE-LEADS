#!/usr/bin/env python3
"""
Test script to verify API keys are working
"""

import requests
import sys

# API Keys
HUNTER_API_KEY = "17aaebe1a4244027b283e2c40c2c3dd2f9b9b10c"
ABSTRACT_API_KEY = "84bf85fe34254c0780c9440187aeab12"

print("=" * 60)
print("🔑 Testing API Keys")
print("=" * 60)

# Test 1: Hunter.io Account Info
print("\n1️⃣ Testing Hunter.io API Key...")
try:
    url = "https://api.hunter.io/v2/account"
    params = {"api_key": HUNTER_API_KEY}
    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Hunter.io API key is VALID!")
        print(f"   Plan: {data.get('data', {}).get('plan', {}).get('name', 'Unknown')}")
        credits = data.get('data', {}).get('plan', {}).get('credits', {})
        print(f"   Search credits: {credits.get('search', {}).get('remaining', 'N/A')}")
        print(f"   Verifier credits: {credits.get('verifier', {}).get('remaining', 'N/A')}")
    elif response.status_code == 401:
        print(f"❌ Hunter.io API key is INVALID or unauthorized")
        print(f"   Status: {response.status_code}")
    else:
        print(f"⚠️  Hunter.io API returned error: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Hunter.io API test failed: {e}")

# Test 2: Abstract API
print("\n2️⃣ Testing Abstract API Key...")
try:
    url = "https://emailvalidation.abstractapi.com/v1/"
    params = {
        "api_key": ABSTRACT_API_KEY,
        "email": "test@example.com"
    }
    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Abstract API key is VALID!")
        print(f"   Email validated: test@example.com")
        print(f"   Quality score: {data.get('quality_score', 'N/A')}")
    elif response.status_code == 401:
        print(f"❌ Abstract API key is INVALID or unauthorized")
        print(f"   Status: {response.status_code}")
    elif response.status_code == 404:
        print(f"⚠️  Abstract API endpoint not found (404)")
        print(f"   This might mean the API URL has changed")
        print(f"   Response: {response.text[:200]}")
    else:
        print(f"⚠️  Abstract API returned error: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Abstract API test failed: {e}")

# Test 3: Alternative Abstract API endpoint
print("\n3️⃣ Testing Alternative Abstract API Endpoint...")
try:
    url = "https://emailvalidation.abstractapi.com/v1/validate"
    params = {
        "api_key": ABSTRACT_API_KEY,
        "email": "test@example.com"
    }
    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Abstract API key is VALID! (using /validate endpoint)")
        print(f"   Quality score: {data.get('quality_score', 'N/A')}")
    else:
        print(f"⚠️  Abstract API returned: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Alternative endpoint test failed: {e}")

print("\n" + "=" * 60)
print("✅ API Key Testing Complete!")
print("=" * 60)
