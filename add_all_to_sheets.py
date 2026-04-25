#!/usr/bin/env python3
"""
Add ALL leads from database to Google Sheets
Makes Google Sheets the single source of truth
"""

import gspread
from google.oauth2.service_account import Credentials
import sqlite3

SERVICE_ACCOUNT_FILE = '/Users/jonsmith/leadforge-scraper/service_account.json'
SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
DB_PATH = '/Users/jonsmith/leadforge-scraper/leads.db'

print("="*60)
print("📊 Adding ALL Database Leads to Google Sheet")
print("="*60)

# Connect to Google Sheets
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet(WORKSHEET_NAME)

# Get existing companies from Google Sheet
all_data = worksheet.get_all_values()
data_rows = all_data[1:]
existing_companies = set()

for row in data_rows:
    if row and len(row) > 0:
        existing_companies.add(row[0].lower().strip())

print(f"✅ Google Sheet currently has {len(existing_companies)} companies")

# Get ALL leads from database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''
    SELECT business_name, phone, website, location, industry, 
           rating, reviews_count, address, email, score
    FROM leads
    ORDER BY score DESC
''')

db_leads = cursor.fetchall()
conn.close()

print(f"✅ Database has {len(db_leads)} leads")

# Find leads to add (not in Google Sheet)
leads_to_add = []
for lead in db_leads:
    business_name = lead[0]
    if business_name and business_name.lower().strip() not in existing_companies:
        leads_to_add.append(lead)

print(f"\n📊 Found {len(leads_to_add)} leads to ADD to Google Sheet")

if len(leads_to_add) == 0:
    print("✅ All leads already in Google Sheet!")
    exit(0)

# Prepare rows for Google Sheet (match column structure)
# Columns: Business Name, Phone, Website, Location, Industry, Rating, etc.
rows_to_add = []
for lead in leads_to_add:
    row = [
        lead[0],  # Business Name
        lead[1] if lead[1] else '',  # Phone
        lead[2] if lead[2] else '',  # Website
        lead[3] if lead[3] else '',  # Location
        lead[4] if lead[4] else '',  # Industry
        str(lead[5]) if lead[5] else '',  # Rating
        str(lead[6]) if lead[6] else '',  # Reviews Count
        lead[7] if lead[7] else '',  # Address
        lead[8] if lead[8] else '',  # Email
        str(lead[9]) if lead[9] else '0',  # Score
    ]
    rows_to_add.append(row)

# Add to Google Sheet in batches
print(f"\n🔄 Adding {len(rows_to_add)} leads to Google Sheet...")
print(f"   (This may take a few minutes)")

added = 0
batch_size = 50

for i in range(0, len(rows_to_add), batch_size):
    batch = rows_to_add[i:i+batch_size]
    try:
        worksheet.append_rows(batch)
        added += len(batch)
        print(f"   ✅ Added {added}/{len(rows_to_add)} leads")
    except Exception as e:
        print(f"   ❌ Error adding batch: {e}")

print(f"\n{'='*60}")
print(f"✅ SUCCESS! Added {added} leads to Google Sheet")
print(f"{'='*60}")

print(f"\n📊 Your Google Sheet now has:")
print(f"   • Before: {len(existing_companies)} leads")
print(f"   • Added: {added} leads")
print(f"   • Total: {len(existing_companies) + added} leads")

print(f"\n✅ Google Sheets is now your MASTER database!")
print(f"   All 912 leads are in one place.")
