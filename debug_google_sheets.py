#!/usr/bin/env python3
"""
Debug Google Sheets connection and check column names
"""

import gspread
from google.oauth2.service_account import Credentials
import sys

SHEET_ID = "1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo"
WORKSHEET_NAME = "All Leads"
SERVICE_ACCOUNT_FILE = 'service_account.json'

try:
    # Connect to Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(WORKSHEET_NAME)

    print("✅ Connected to Google Sheets successfully!")

    # Get the first row (headers)
    headers = worksheet.row_values(1)

    print(f"\n📋 Found {len(headers)} columns in the sheet:")
    print("=" * 60)
    for i, header in enumerate(headers[:50], 1):
        print(f"{i:3d}. {header}")

    if len(headers) > 50:
        print(f"\n... and {len(headers) - 50} more columns")

    print("=" * 60)

    # Count total rows
    total_rows = len(worksheet.get_all_values())
    print(f"\n📊 Total rows (including header): {total_rows}")
    print(f"📊 Total leads (excluding header): {total_rows - 1}")

    # Check for email-related columns
    email_columns = [h for h in headers if 'email' in h.lower() or 'mail' in h.lower()]
    phone_columns = [h for h in headers if 'phone' in h.lower()]

    print(f"\n📧 Email-related columns: {email_columns}")
    print(f"📞 Phone-related columns: {phone_columns}")

    # Get sample data from first few rows
    print("\n📝 Sample data (first 3 leads):")
    print("=" * 60)
    sample_data = worksheet.get_all_values()[:4]  # Header + 3 rows
    for row in sample_data:
        # Show first 10 columns
        print(" | ".join(row[:10]))

    print("=" * 60)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
