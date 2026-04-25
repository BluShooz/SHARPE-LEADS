#!/usr/bin/env python3
"""
Add missing leads from local database to Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
import sqlite3

SERVICE_ACCOUNT_FILE = '/Users/jonsmith/leadforge-scraper/service_account.json'
SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
DB_PATH = '/Users/jonsmith/leadforge-scraper/leads.db'

print("="*60)
print("🔍 Finding leads NOT in Google Sheet")
print("="*60)

# Connect to Google Sheets
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet(WORKSHEET_NAME)

# Get all companies from Google Sheet
all_data = worksheet.get_all_values()
data_rows = all_data[1:]

sheet_companies = set()
for row in data_rows:
    if row and len(row) > 0:
        sheet_companies.add(row[0].lower().strip())

print(f"✅ Google Sheet has {len(sheet_companies)} unique companies")

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('SELECT business_name, phone, website, location, industry, rating, reviews_count, address, email, score FROM leads')
db_leads = cursor.fetchall()
conn.close()

print(f"✅ Database has {len(db_leads)} leads")

# Find leads NOT in Google Sheet
missing_leads = []
for lead in db_leads:
    business_name = lead[0]
    if business_name and business_name.lower().strip() not in sheet_companies:
        missing_leads.append(lead)

print(f"\n📊 Found {len(missing_leads)} leads NOT in Google Sheet")
print(f"   These need to be added to your Google Sheet")

if len(missing_leads) > 0:
    print(f"\n📋 Sample of missing leads:")
    for i, lead in enumerate(missing_leads[:10], 1):
        print(f"   {i}. {lead[0]} - {lead[3]}")
    
    if len(missing_leads) > 10:
        print(f"   ... and {len(missing_leads) - 10} more")

print(f"\n💡 To add these to Google Sheet:")
print(f"   1. Export them: ~/Desktop/missing_google_sheets_leads.csv")
print(f"   2. Open your Google Sheet")
print(f"   3. File → Import → Upload the CSV")
print(f"   4. Choose 'Replace spreadsheet' or 'Append to sheet'")

print(f"\n{'='*60}")
